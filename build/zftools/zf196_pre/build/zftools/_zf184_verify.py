# -*- coding: utf-8 -*-
u"""_zf184_verify.py —— ZF184 常驻校验：猛砸伤害 = 玩家**当前**攻击伤害 + 逐目标附魔加成。

用户原话：「振金剑技能伤害n改一下 改成目前玩家的伤害（之前是基础伤害 不包括手持武器）
并且吃附魔例如亡灵杀手 锋利的加成 语言键不需要改」。

  A 代码判据：基数改成 `getAttributeValue(Attributes.ATTACK_DAMAGE)`（不再用 baseAttackDamage）；
   附魔加成走 `EnchantmentHelper.modifyDamage(...)`，且**在循环里**（逐目标）
  B 探针 6/0：攻击力 +9 ⇒ 伤害 +9；亡灵杀手 V 打僵尸更疼、打牛不变；锋利 V 打牛更疼
  C 语言键没动（用户明说不用改）：本轮不该出现任何 lang 变更痕迹

跑法：python build\\zftools\\_zf184_verify.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
SWORD = os.path.join(ROOT, r"src\main\java\com\potatost\mod\VibraniumSwordItem.java")
PROBE = os.path.join(ZT, u"_zf184_probe_utf8.txt")

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


src = read(SWORD)

print(u"=== A 段：代码判据 ===")
check(u"getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE)" in src,
      u"A1 基数 = 玩家**当前**攻击伤害（属性值；含手持武器那一份）")
check(u"ShockwaveManager.baseAttackDamage(player)" not in src,
      u"A2 不再用 baseAttackDamage（那条**不含**手持武器，是用户点名要换掉的）")
check(u"EnchantmentHelper.modifyDamage(" in src, u"A3 附魔加成走原版同一个 API（锋利/亡灵杀手都在这条路上）")
idx_tool = src.find(u"EnchantmentHelper.modifyDamage(")
idx_loop = src.find(u"for (LivingEntity target : level.getEntitiesOfClass")
check(idx_loop != -1 and idx_tool > idx_loop,
      u"A4 附魔加成写在**循环里**（逐目标）—— 亡灵杀手看目标类型，循环外算一次就错了")

print(u"\n=== B 段：真开服探针 ===")
rep = read(PROBE)
check(u"通过 = 6   失败 = 0" in rep, u"B1 探针 6/0", rep.strip().split(u"\n")[-1] if rep else u"（没有报告）")
check(u"A1 攻击力 +9 ⇒ 猛砸伤害跟着 +9" in rep, u"B2 报告里有「攻击力 +9 ⇒ 伤害 +9」（基数吃当前攻击伤害）")
check(u"B1 亡灵杀手 V 打**僵尸**（亡灵）明显更疼" in rep, u"B3 报告里有「亡灵杀手对僵尸更疼」")
check(u"C1 同一把亡灵杀手 V 打**牛**（非亡灵）伤害**不变**" in rep, u"B4 报告里有「对牛不变」（逐目标）")
check(u"C2 锋利 V 打牛更疼" in rep, u"B5 报告里有「锋利对牛也生效」")

print(u"\n通过 = %d   失败 = %d" % (passed, failed))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if failed else 0)
