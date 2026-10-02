# -*- coding: utf-8 -*-
u"""_zf184_slam_damage.py —— ZF184（0.14）：猛砸伤害改成「玩家当前攻击伤害 + 逐目标附魔加成」。

用户原话：「**振金剑技能伤害n改一下 改成目前玩家的伤害（之前是基础伤害 不包括手持武器）
并且吃附魔例如亡灵杀手 锋利的加成 语言键不需要改**」。

改前：`double n = ShockwaveManager.baseAttackDamage(player);`（属性基础值 + 玩家自身加成，
**不含手持武器**）→ `damage = n + SLAM_EXTRA_DAMAGE`，**循环外算一次**。

改后：
  ① 基数 `n = player.getAttributeValue(Attributes.ATTACK_DAMAGE)`（**含手持武器那一份**）；
  ② 附魔加成**逐目标**算一次：`EnchantmentHelper.modifyDamage(level, player.getMainHandItem(), target,
     source, baseDamage)` —— 这就是原版玩家攻击那条路用的同一个 API
     （`ServerPlayer.java:2163` 实测同一句），锋利/亡灵杀手这些 `EnchantmentEffectComponents.DAMAGE`
     效果都由它结算，**且亡灵杀手按目标类型生效** ⇒ 必须放在循环里（不能循环外算一次）。

跑法：python build\\zftools\\_zf184_slam_damage.py [--write]
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

P = r"E:\PotatoST\src\main\java\com\potatost\mod\VibraniumSwordItem.java"

NEW_BASE = u"""        // 0.14 ZF184（用户原话「改成目前玩家的伤害（之前是基础伤害 不包括手持武器）」）：
        // 基数改成**玩家当前攻击伤害** —— 属性值里已经把**手持武器那一份**算进去了
        // （原版 `baseAttackDamage` 只取属性基础值 + 玩家自身加成，故意不含武器）。
        double n = player.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE);
        float baseDamage = (float) (n + SLAM_EXTRA_DAMAGE);"""

OLD_BASE = (u"        double n = ShockwaveManager.baseAttackDamage(player);\n"
            u"        float damage = (float) (n + SLAM_EXTRA_DAMAGE);")

NEW_HIT = u"""            // 0.14 ZF184：**逐目标**吃一次附魔加成（锋利 / 亡灵杀手…）——
            // 用原版玩家攻击那条路同一个 API（ServerPlayer.java:2163 实测同一句）。
            // ⚠ 必须放在循环里：亡灵杀手看**目标类型**，对僵尸加、对牛不加。
            float damage = net.minecraft.world.item.enchantment.EnchantmentHelper.modifyDamage(
                    level, player.getMainHandItem(), target, source, baseDamage);
            if (launch(player, target, source, damage)) {"""

ARGS = [("OLD_BASE", OLD_BASE, NEW_BASE), ("NEW_HIT", None, NEW_HIT)]


def main(argv):
    write = u"--write" in argv
    text = io.open(P, encoding="utf-8", newline=u"").read()
    before = text
    fails = []
    if text.count(OLD_BASE) != 1:
        fails.append(u"基数那段出现 %d 次（应 1）" % text.count(OLD_BASE))
    else:
        text = text.replace(OLD_BASE, NEW_BASE, 1)
    old_hit = u"            if (launch(player, target, source, damage)) {"
    if text.count(old_hit) != 1:
        fails.append(u"launch 那一行出现 %d 次（应 1）" % text.count(old_hit))
    else:
        text = text.replace(old_hit, NEW_HIT, 1)
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1
    n = sum(1 for l1, l2 in zip(before.split(u"\n"), text.split(u"\n")) if l1 != l2)
    print(u"  VibraniumSwordItem.java 改 %d 行" % n)
    if write:
        io.open(P, "w", encoding="utf-8", newline=u"").write(text)
    print(u"模式：%s" % (u"落盘" if write else u"干跑"))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
