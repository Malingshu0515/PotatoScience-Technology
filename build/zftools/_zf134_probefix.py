# -*- coding: utf-8 -*-
"""_zf134_probefix.py —— 两处跟着改动走的探针修正

## ① (j) 出手被拒：`耐久 0/0`
(g) 那场把斧子精确扣到 0 耐久（"正好扣光那 120"），(j) 排在它后面 ⇒ `use()` 走到
"耐久不够 120" 那一支直接回 FAIL。**修法**：`buildAngle()` 里先把耐久修好
（`axe.setDamageValue(0)`）并 `keepAlive()` —— 与其它场景开局的写法一致。

## ② `[DIRECT] 反射调用失败`
`ShockwaveManager$Wave` 的构造器签名从
`(ServerLevel, UUID, double, boolean, int, int)` 变成了
`(ServerLevel, UUID, double, double, double, int)`（方向由"主轴+正负"改成单位向量）。
探针里的 `getDeclaredConstructor(...)` 还写着旧的 ⇒ `NoSuchMethodException`。
**修法**：按新签名取构造器 —— 这也说明"探针是跟着产品结构走的"，产品结构一变它就该跟着变。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

FIXES = [
    # ① (j) 开局修耐久 + 保活
    ("""        say(TAG + "⑩ (j) 斜角 21°：斜线上的原木必须被拆、正东那一列必须没事");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        clearAbove();""",
     """        say(TAG + "⑩ (j) 斜角 21°：斜线上的原木必须被拆、正东那一列必须没事");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        // ⚠ (g) 那场把耐久精确扣到 0 了（"正好扣光那 120"），这里必须先修好，
        //   否则 use() 走到"耐久不够 120"那一支直接回 FAIL —— 上一跑就是这么假失败的。
        axe.setDamageValue(0);
        player.setItemInHand(InteractionHand.MAIN_HAND, axe);
        keepAlive();
        clearAbove();"""),

    # ② 反射构造器签名
    ("""            var ctor = waveClass.getDeclaredConstructor(
                    net.minecraft.server.level.ServerLevel.class, java.util.UUID.class,
                    double.class, boolean.class, int.class, int.class);
            ctor.setAccessible(true);
            Object wave = ctor.newInstance(end, owner.getUUID(),
                    ShockwaveManager.baseAttackDamage(owner), true, 1, pos.getY());""",
     """            // ⚠ ZF134：方向从"主轴 + 正负号"改成**单位向量** ⇒ 构造器签名跟着变了
            //   （ServerLevel, UUID, double, double dirX, double dirZ, int originY）。
            //   探针是跟着产品结构走的，产品一改它就该跟着改 —— 上一跑在这里报 NoSuchMethod。
            var ctor = waveClass.getDeclaredConstructor(
                    net.minecraft.server.level.ServerLevel.class, java.util.UUID.class,
                    double.class, double.class, double.class, int.class);
            ctor.setAccessible(true);
            Object wave = ctor.newInstance(end, owner.getUUID(),
                    ShockwaveManager.baseAttackDamage(owner), 1.0D, 0.0D, pos.getY());"""),
]

s = io.open(CHK, encoding="utf-8").read()
for i, (a, b) in enumerate(FIXES):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("探针已修")
