# -*- coding: utf-8 -*-
"""_zf134_probefix3.py —— (j) 的冷却要在**重建斧子之后**再清一次

诊断打出来：`shift=false 冷却中=true`。
两个事实叠在一起：
  · `ItemCooldowns` 是按 **Item** 记的（不是 ItemStack）⇒ 哪一场设过冷却，之后都还在；
  · 那个假玩家不在 `PlayerList` 的 tick 循环里 ⇒ **冷却自己不会走**（除非我手动 tick，
    而 (f) 那场确实手动走完了它自己那一轮，但 (j) 之前 (g2)/(c)/(h) 又设过新的）。
修法：把 `removeCooldown` 挪到"重建斧子 + 拿在手上"**之后**，并把顺序写清楚。
（`shift=false` 是正常的 —— `useAxe()` 会自己按下 shift。）
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        // ⚠ (g2) 那场按设计把耐久"正好扣光"⇒ `hurtAndBreak` 的爆掉分支把**那个 ItemStack 实例**
        //   变成了空气（诊断实测：`静态 axe 空? true`）⇒ 后面每一场都用不了。
        //   所以这里**新建一把**，并把静态字段指过去（不是 setDamageValue —— 对空气无效）。
        axe = new ItemStack(ModItems.STAR_STEEL_AXE.get());
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);"""

NEW = """        ShockwaveManager.clearAll();
        // ⚠ (g2) 那场按设计把耐久"正好扣光"⇒ `hurtAndBreak` 的爆掉分支把**那个 ItemStack 实例**
        //   变成了空气（诊断实测：`静态 axe 空? true`）⇒ 后面每一场都用不了。
        //   所以这里**新建一把**，并把静态字段指过去（不是 setDamageValue —— 对空气无效）。
        axe = new ItemStack(ModItems.STAR_STEEL_AXE.get());
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
        // ⚠ 冷却要在重建之后再清：`ItemCooldowns` 按 **Item** 记（不是 ItemStack），
        //   而且这台假玩家不在 PlayerList 的 tick 循环里 ⇒ 冷却**不会自己走**
        //   （诊断实测：`冷却中=true` ⇒ `use()` 直接 PASS）。
        player.getCooldowns().removeCooldown(axe.getItem());"""

s = io.open(CHK, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] 冷却清理挪到重建之后")
