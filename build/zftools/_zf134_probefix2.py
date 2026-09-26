# -*- coding: utf-8 -*-
"""_zf134_probefix2.py —— (j) 要**重建**斧子（静态 axe 已经被上一场扣爆成空气了）

诊断打出来的事实：
```
[J] 手上=0 minecraft:air 空? true 耐久=0/0
[J] 静态 axe 空? true 耐久=0/0 同一实例? true
```
(g2) 那场"正好扣光那 120"按设计会触发 `hurtAndBreak` 的爆掉分支 ⇒
`onBroken` 把**那个 ItemStack 实例**改成空气 ⇒ 静态字段 `axe` 从此是空的
⇒ 后面任何一场都用不了（上一跑 (j) 就这么假失败）。

修法：`buildAngle()` 里**新建一把**（与开场同一句 `new ItemStack(ModItems.STAR_STEEL_AXE.get())`），
并把静态字段指过去 —— 这也顺带修正了"静态 axe 被扣爆"这件事本身。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """        // ⚠ (g) 那场把耐久精确扣到 0 了（"正好扣光那 120"），这里必须先修好，
        //   否则 use() 走到"耐久不够 120"那一支直接回 FAIL —— 上一跑就是这么假失败的。
        axe.setDamageValue(0);
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);"""

NEW = """        // ⚠ (g2) 那场按设计把耐久"正好扣光"⇒ `hurtAndBreak` 的爆掉分支把**那个 ItemStack 实例**
        //   变成了空气（诊断实测：`静态 axe 空? true`）⇒ 后面每一场都用不了。
        //   所以这里**新建一把**，并把静态字段指过去（不是 setDamageValue —— 对空气无效）。
        axe = new ItemStack(ModItems.STAR_STEEL_AXE.get());
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);"""

s = io.open(CHK, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
s = s.replace(OLD, NEW, 1)

# axe 字段必须是可重新赋值的（检查声明不是 final）
assert "private static ItemStack axe;" in s, "axe 字段声明变了？"
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] (j) 改成重建斧子")
