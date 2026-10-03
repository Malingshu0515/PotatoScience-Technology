# -*- coding: utf-8 -*-
u"""_zf182_verify.py —— ZF182 常驻校验：振金剑「斩首」被动（口径 B = 只有猛砸技能击杀才算）。

用户原话：「给振金剑加个新被动buff 被振金剑技能击杀的生物掉落它的头颅 玩家掉落本人头颅
原版有头颅的掉落自己的头颅 没有的则不掉」，口径二选一里选了 **B（只有技能击杀）**。

  A 判据链：自定义伤害类型 JSON 在 + 常量在 + 猛砸用它 + 处理器只认它
  B 掉落表：6 种原版有头颅的生物都在表里；玩家走 player_head + 本人 profile；查表函数对牛这类返回空
  C 文案：tooltip 行数 4；五语两个键都在（tooltip.4 + death.attack...）
  D 探针报告 13/0（真服务端：真技能砸死三种生物掉自己的头 + 牛不掉 + 平砍不掉）

跑法：python build\\zftools\\_zf182_verify.py
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t")
LANGDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
PROBE = os.path.join(ZT, u"_zf182_probe_utf8.txt")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
TIP = u"tooltip.potato_s_t.vibranium_sword.4"
DEATH = u"death.attack.potato_s_t.vibranium_slam"

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else u""


sword = read(os.path.join(JAVA, u"VibraniumSwordItem.java"))
behead = read(os.path.join(JAVA, u"VibraniumBeheading.java"))

print(u"=== A 段：判据链（口径 B 靠伤害类型落地）===")
check(u"vibranium_slam" in read(os.path.join(DATA, u"damage_type", u"vibranium_slam.json")),
      u"A1 伤害类型 JSON 在（potato_s_t:vibranium_slam）")
check(u'ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "vibranium_slam")' in sword
      and u"public static DamageSource slamSource(ServerPlayer player)" in sword,
      u"A2 振金剑里有 VIBRANIUM_SLAM 常量与 slamSource()")
check(u"DamageSource source = slamSource(player);" in sword,
      u"A3 猛砸那一下的伤害**真的**换成了它（不是留着原版 player_attack）")
check(u"if (!event.getSource().is(VibraniumSwordItem.VIBRANIUM_SLAM)) {" in behead,
      u"A4 斩首处理器**只认**这个伤害类型 ⇒ 平砍自然不算（口径 B）")

print(u"\n=== B 段：掉落表 ===")
for mob, head in ((u"ZOMBIE", u"ZOMBIE_HEAD"), (u"SKELETON", u"SKELETON_SKULL"),
                  (u"WITHER_SKELETON", u"WITHER_SKELETON_SKULL"), (u"CREEPER", u"CREEPER_HEAD"),
                  (u"PIGLIN", u"PIGLIN_HEAD"), (u"ENDER_DRAGON", u"DRAGON_HEAD")):
    check(u"EntityType.%s, Items.%s" % (mob, head) in behead, u"B %s → %s" % (mob, head))
check(u"new ItemStack(Items.PLAYER_HEAD)" in behead
      and u"new ResolvableProfile(player.getGameProfile())" in behead,
      u"B7 玩家 → player_head + **被杀者本人**的 profile（1.21.1 是构造器，没有 createResolved）")
check(u"HEADS.get(victim.getType())" in behead and u"ItemStack.EMPTY" in behead,
      u"B8 查不到的类型返回空 ⇒ 牛/猪这些不掉（没有的则不掉）")
check(u"Items.HUSK_HEAD" not in behead and u"DROWNED" not in behead,
      u"B9 没给尸壳/溺尸这类**没有头颅物品**的生物编头颅")

print(u"\n=== C 段：文案 ===")
check(u"TOOLTIP_LINES = 4" in sword, u"C1 振金剑 tooltip 行数 3 → 4（多一行斩首说明）")
bad = []
for lg in LOCALES:
    obj = json.loads(io.open(os.path.join(LANGDIR, lg + u".json"), encoding="utf-8").read())
    for k in (TIP, DEATH):
        if not (obj.get(k) or u"").strip():
            bad.append(u"%s/%s" % (lg, k))
check(not bad, u"C2 五语都有 tooltip 第 4 行与死亡文案且非空", u"缺 %s" % bad[:4])

print(u"\n=== D 段：真开服探针 ===")
rep = read(PROBE)
check(u"通过 = 13   失败 = 0" in rep, u"D1 探针 13/0", rep.strip().split(u"\n")[-1] if rep else u"（没有报告）")
check(u"A zombie：掉落里有 minecraft:zombie_head" in rep, u"D2 报告里有「猛砸砸死僵尸掉僵尸头」")
check(u"C2 平砍**不掉**头颅" in rep, u"D3 报告里有「平砍不掉」这条负对照（B 口径成立）")
check(u"B2 牛**没有**掉任何头颅" in rep, u"D4 报告里有「牛不掉」这条负对照")

print(u"\n通过 = %d   失败 = %d" % (passed, failed))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if failed else 0)
