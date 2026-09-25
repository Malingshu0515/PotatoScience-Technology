# -*- coding: utf-8 -*-
u"""_zf103_api_probe.py —— 只读：把本轮（两套盔甲）要用的 API 签名从 jar 里当场抠出来

不靠记忆写原版/NeoForge 的 `ArmorMaterial` / `ArmorItem` / `ArmorItem.Type` /
`IItemExtension` / `LivingIncomingDamageEvent` / `ItemAttributeModifierEvent` 的形状。
输入：`build/neoForm/.../sources.jar`（打过补丁的原版源码）+ `neoforge-*-sources.jar`。

用法：
    $env:PYTHONIOENCODING='utf-8'; python build\zftools\_zf103_api_probe.py [filter]
"""
import glob
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
GRADLE = r"E:\gradle-home"

TARGETS = [
    (u"vanilla", u"net/minecraft/world/item/ArmorMaterial.java", None),
    (u"vanilla", u"net/minecraft/world/item/ArmorItem.java", None),
    (u"vanilla", u"net/minecraft/world/item/Item.java",
     [u"Properties", u"durability(", u"attributes(", u"rarity("],
     u"net/minecraft/world/item/Item.java"),
    (u"vanilla", u"net/minecraft/world/item/equipment/ArmorType.java", None),
    (u"neoforge", u"net/neoforged/neoforge/common/extensions/IItemExtension.java",
     [u"getDefaultAttributeModifiers", u"canWalkOnPowderedSnow", u"getArmorTexture",
      u"onArmorTick", u"isDamageable", u"damageItem", u"getMaxDamage"]),
    (u"neoforge", u"net/neoforged/neoforge/event/entity/living/LivingIncomingDamageEvent.java", None),
    (u"neoforge", u"net/neoforged/neoforge/event/entity/living/ArmorHurtEvent.java", None),
    (u"neoforge", u"net/neoforged/neoforge/event/entity/living/LivingDamageEvent.java", None),
    (u"vanilla", u"net/minecraft/world/entity/LivingEntity.java",
     [u"public boolean hurt", u"actuallyHurt", u"isDamageSourceBlocked",
      u"getArmorValue", u"onEquipItem", u"randomTeleport", u"teleportTo"]),
    (u"vanilla", u"net/minecraft/world/damagesource/DamageSource.java",
     [u"is(", u"getDirectEntity", u"getEntity", u"getMsgId"]),
    (u"vanilla", u"net/minecraft/world/damagesource/DamageSources.java",
     [u"fellOutOfWorld", u"generic", u"outOfWorld"]),
    (u"vanilla", u"net/minecraft/tags/DamageTypeTags.java", None),
    (u"vanilla", u"net/minecraft/world/effect/MobEffects.java", None),
    (u"vanilla", u"net/minecraft/world/effect/MobEffectInstance.java",
     [u"public MobEffectInstance", u"isAmbient", u"visible"]),
    (u"vanilla", u"net/minecraft/world/entity/ai/attributes/Attributes.java", None),
    (u"neoforge", u"net/neoforged/neoforge/event/entity/player/PlayerEvent.java",
     [u"class", u"Tick"]),
]


def find(patterns):
    hits = []
    for p in patterns:
        hits.extend(glob.glob(p, recursive=True))
    hits = [h for h in hits if os.path.isfile(h)]
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0] if hits else None


def main():
    needle_filter = sys.argv[1] if len(sys.argv) > 1 else None
    vanilla = find([os.path.join(PROJ, u"build", u"neoForm", u"**", u"sources.jar")])
    neoforge = find([os.path.join(GRADLE, u"**", u"neoforge-*-sources.jar")])
    print(u"vanilla sources : %s" % vanilla)
    print(u"neoforge sources: %s" % neoforge)
    jars = {u"vanilla": vanilla, u"neoforge": neoforge}

    for target in TARGETS:
        kind, entry = target[0], target[1]
        needles = target[2] if len(target) > 2 else None
        if needle_filter and needle_filter not in entry:
            continue
        path = jars.get(kind)
        print(u"\n================ %s (%s) ================" % (entry, kind))
        if not path:
            print(u"  (缺 jar)")
            continue
        with zipfile.ZipFile(path) as zf:
            try:
                text = zf.read(entry).decode("utf-8", "replace")
            except KeyError:
                print(u"  (jar 里没有这个条目)")
                continue
        lines = text.split(u"\n")
        printed = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(u"*") or stripped.startswith(u"//") \
                    or stripped.startswith(u"/*") or stripped.startswith(u"*/"):
                continue
            if needles is None or any(n in line for n in needles):
                print(u"  %4d| %s" % (i, stripped[:170]))
                printed += 1
                if printed >= 90:
                    print(u"  ... (截断)")
                    break
    return 0


if __name__ == "__main__":
    sys.exit(main())
