# -*- coding: utf-8 -*-
r"""ZF153 侦察③：最后三处"写错就悄悄错"的事实（只读）。

  ① `LivingEntity.addEffect` → `forceAddEffect` → `CommonHooks.canMobEffectBeApplied`
     这条链上 `MobEffectEvent.Applicable` 到底在哪一环触发 —— 决定"免疫"能不能真的拦住
     一次**新挂上**的效果（而不是只拦住"刷新时长"）。
  ② 附魔权重的链路：`Tier.getEnchantmentValue()` → `TieredItem` → `ItemStack`。
     用户给的「1附魔权重」必须落在这条链上，否则数值挂对了也没用。
  ③ `LivingEntity.hurt` 会不会**覆盖**速度 —— 击飞要在 hurt **之后**写速度（顺序写反就白推）。
     顺带确认 `SoundEvents.ANVIL_LAND` / 几个粒子常量真的存在（不凭记忆写常量名）。
"""

import io
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
ZFTOOLS = os.path.join(PROJ, "build", "zftools")
SOURCES_JAR = os.path.join(PROJ, "build", "neoForm",
                           "neoFormJoined1.21.1-20240808.144430", "sources.jar")

OUT = []


def w(line=u""):
    OUT.append(line)


def flush():
    text = u"\n".join(OUT) + u"\n"
    with io.open(os.path.join(ZFTOOLS, "_zf153_recon3.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.write(u"[zf153_recon3] 写出 %d 行 -> _zf153_recon3.txt\n" % len(OUT))


def src_of(zf, want):
    hit = [n for n in zf.namelist() if n.endswith(want)]
    return zf.read(hit[0]).decode("utf-8", "replace") if hit else None


def show(src, label, lo, hi):
    w(u"")
    w(u"---- %s（第 %d~%d 行）----" % (label, lo, hi))
    lines = src.split(u"\n")
    for i in range(lo, min(hi, len(lines)) + 1):
        w(u"  %5d | %s" % (i, lines[i - 1].rstrip()))


def find_all(src, needle, limit=14):
    return [i for i, line in enumerate(src.split(u"\n"), 1) if needle in line][:limit]


with zipfile.ZipFile(SOURCES_JAR) as zf:
    # ① 效果挂载链
    s = src_of(zf, u"net/minecraft/world/entity/LivingEntity.java")
    show(s, u"LivingEntity.addEffect", 971, 1000)
    show(s, u"LivingEntity.forceAddEffect", 1013, 1034)
    s = src_of(zf, u"net/neoforged/neoforge/common/CommonHooks.java")
    if s is None:
        w(u"!! 没有 CommonHooks.java")
    else:
        w(u"")
        w(u"---- CommonHooks.canMobEffectBeApplied ----")
        lo = find_all(s, u"canMobEffectBeApplied")
        w(u"  出现行号：%s" % lo)
        for i in lo[:1]:
            show(s, u"CommonHooks.java @%d" % i, i, i + 22)

    # ② 附魔权重链
    s = src_of(zf, u"net/minecraft/world/item/TieredItem.java")
    w(u"")
    w(u"---- TieredItem.java 全文（很短）----")
    if s is None:
        w(u"  !! 没有 TieredItem.java")
    else:
        for i, line in enumerate(s.split(u"\n"), 1):
            w(u"  %5d | %s" % (i, line.rstrip()))
    s = src_of(zf, u"net/minecraft/world/item/ItemStack.java")
    if s is not None:
        w(u"")
        w(u"---- ItemStack.java：getEnchantmentValue ----")
        for i in find_all(s, u"getEnchantmentValue"):
            show(s, u"ItemStack.java @%d" % i, i - 3, i + 6)
    s = src_of(zf, u"net/minecraft/world/item/Item.java")
    if s is not None:
        w(u"")
        w(u"---- Item.java：getEnchantmentValue 与 isValidRepairItem ----")
        for i in find_all(s, u"getEnchantmentValue") + find_all(s, u"isValidRepairItem"):
            show(s, u"Item.java @%d" % i, i - 2, i + 8)

    # ③ hurt 与速度
    s = src_of(zf, u"net/minecraft/world/entity/LivingEntity.java")
    w(u"")
    w(u"---- LivingEntity.hurt 里的 knockback / setDeltaMovement / hurtMarked 出现行号：%s"
      % (find_all(s, u"knockback") + find_all(s, u"setDeltaMovement") + find_all(s, u"hurtMarked")))
    for i in find_all(s, u"this.knockback") + find_all(s, u"markHurt"):
        show(s, u"LivingEntity.java @%d" % i, max(1, i - 8), i + 6)
    s = src_of(zf, u"net/minecraft/world/entity/Entity.java")
    if s is not None:
        w(u"")
        w(u"---- Entity.java：hasImpulse / hurtMarked / markHurt 的声明 ----")
        for i, line in enumerate(s.split(u"\n"), 1):
            t = line.strip()
            if t.startswith(u"public boolean hasImpulse") or t.startswith(u"public boolean hurtMarked") \
                    or t.startswith(u"public void markHurt") or t.startswith(u"public void setDeltaMovement"):
                w(u"  %5d | %s" % (i, t))

    # ④ 常量名核实（不凭记忆）
    s = src_of(zf, u"net/minecraft/sounds/SoundEvents.java")
    if s is not None:
        w(u"")
        w(u"---- SoundEvents：ANVIL_LAND / GENERIC_EXPLODE / TRIDENT_THROW ----")
        for i, line in enumerate(s.split(u"\n"), 1):
            if any(k in line for k in (u"ANVIL_LAND ", u"GENERIC_EXPLODE ", u"TRIDENT_THROW ",
                                       u"MACE_SMASH_GROUND ")):
                w(u"  %5d | %s" % (i, line.strip()))
    s = src_of(zf, u"net/minecraft/core/particles/ParticleTypes.java")
    if s is not None:
        w(u"")
        w(u"---- ParticleTypes：EXPLOSION / CLOUD / CRIT / SMOKE / END_ROD ----")
        for i, line in enumerate(s.split(u"\n"), 1):
            if any(u"= register(" in line and k in line
                   for k in (u"EXPLOSION", u"CLOUD", u"CRIT", u"SMOKE", u"END_ROD")):
                w(u"  %5d | %s" % (i, line.strip()))

flush()
