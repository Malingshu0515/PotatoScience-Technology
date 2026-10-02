# -*- coding: utf-8 -*-
"""_zf133_dbg3.py —— 第三轮诊断：把 (f) 段每一步的冷却状态打出来（精确到 tick）

`[A133DBG2]` 已经证明：注入点那一刻 `onCooldown(this) = false`（第一刀的检查确实过了），
但 10 tick 之后（`checkFMid`）再查又是 false —— 说明冷却"被加上了、又消失了"，
或者压根没加。第三种可能是**客户端那次调用**（探针直接调 `use` 两次？不，
探针只调一次）—— 所以只能靠逐步打印。

插 6 个打印点：buildF 加冷却前后、checkFMid 进入时、探针 mount 处。

跑法：python build\\zftools\\_zf133_dbg3.py      插
      python build\\zftools\\_zf133_dbg3.py --off 撤
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AXE = r"E:\PotatoST\src\main\java\com\potatost\mod\StarSteelAxeItem.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

AXE_OLD = """            player.getCooldowns().addCooldown(this, SHOCKWAVE_COOLDOWN_TICKS);
            player.swing(hand, true);"""
AXE_NEW = """            player.getCooldowns().addCooldown(this, SHOCKWAVE_COOLDOWN_TICKS);
            if (com.potatost.mod.Zf133Check.DBG) {
                System.out.println("[A133DBG3] addCooldown(" + SHOCKWAVE_COOLDOWN_TICKS + ") 之后 isOnCooldown="
                        + player.getCooldowns().isOnCooldown(this)
                        + " percent=" + player.getCooldowns().getCooldownPercent(this, 0.0F)
                        + " cd=" + player.getCooldowns());
            }
            player.swing(hand, true);"""

CHK_OLD = """    private static void checkFMid() {
        ShockwaveManager.clearAll();"""
CHK_NEW = """    private static void checkFMid() {
        say(TAG + "      [DBG] checkFMid 进入：isOnCooldown = "
                + player.getCooldowns().isOnCooldown(axe.getItem())
                + " percent = " + player.getCooldowns().getCooldownPercent(axe.getItem(), 0.0F)
                + " cd = " + player.getCooldowns()
                + " gameTime = " + level.getGameTime());
        ShockwaveManager.clearAll();"""

CHK_OLD2 = """        failed += check("出手后进入冷却（isOnCooldown = \""""
CHK_NEW2 = """        say(TAG + "      [DBG] buildF 出手之后立刻查：isOnCooldown = "
                + player.getCooldowns().isOnCooldown(axe.getItem())
                + " percent = " + player.getCooldowns().getCooldownPercent(axe.getItem(), 0.0F)
                + " cd = " + player.getCooldowns()
                + " gameTime = " + level.getGameTime());
        failed += check("出手后进入冷却（isOnCooldown = \""""


def main():
    off = "--off" in sys.argv
    for path, pairs in ((AXE, [(AXE_OLD, AXE_NEW)]),
                        (CHK, [(CHK_OLD, CHK_NEW), (CHK_OLD2, CHK_NEW2)])):
        s = io.open(path, encoding="utf-8").read()
        for a, b in ([(y, x) for x, y in pairs] if off else pairs):
            n = s.count(a)
            assert n == 1, "%s 锚点 %d 次：%r" % (path, n, a[:60])
            s = s.replace(a, b, 1)
        io.open(path, "w", encoding="utf-8", newline="\n").write(s)
        print("[OK] %s %s" % ("撤销" if off else "插入", path))


main()
