# -*- coding: utf-8 -*-
"""_zf133_dbg2.py —— 第二轮诊断：冷却门禁为什么没拦住？树叶为什么没被拆？

两个问题都靠打印事实来定位（不猜）：
  F) 在 `StarSteelAxeItem.use()` 的冷却判定前后，把 `isOnCooldown(axe 实例)`、
     `isOnCooldown(this)`、`percent`、以及玩家手上那把的 identity 打出来。
  B) 在 `checkB` 里把树叶那 6 格的**真实方块**逐个打出来（现在只统计"剩几格"）。

跑法：python build\\zftools\\_zf133_dbg2.py          插
      python build\\zftools\\_zf133_dbg2.py --off    撤
"""
import hashlib
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AXE = r"E:\PotatoST\src\main\java\com\potatost\mod\StarSteelAxeItem.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

AXE_OLD = """        if (player.getCooldowns().isOnCooldown(this)) {
            return InteractionResultHolder.pass(stack);
        }"""
AXE_NEW = """        if (com.potatost.mod.Zf133Check.DBG) {
            System.out.println("[A133DBG2] use(): this=" + System.identityHashCode(this)
                    + " stackItem=" + System.identityHashCode(stack.getItem())
                    + " onCooldown(this)=" + player.getCooldowns().isOnCooldown(this)
                    + " onCooldown(stack.getItem())=" + player.getCooldowns().isOnCooldown(stack.getItem())
                    + " removeCooldowns=" + player.getCooldowns());
        }
        if (player.getCooldowns().isOnCooldown(this)) {
            return InteractionResultHolder.pass(stack);
        }"""

CHK_OLD = """        int leavesLeft = 0;
        for (int z = -3; z <= 2; z++) {
            if (!level.getBlockState(new BlockPos(X0 + 2, Y0 + 1, Z0 + z)).isAir()) {
                leavesLeft++;
            }
        }"""
CHK_NEW = """        int leavesLeft = 0;
        for (int z = -3; z <= 2; z++) {
            BlockPos lp = new BlockPos(X0 + 2, Y0 + 1, Z0 + z);
            say(TAG + "      [DBG] 树叶位 " + lp.toShortString() + " = "
                    + level.getBlockState(lp).getBlock().getName().getString());
            if (!level.getBlockState(lp).isAir()) {
                leavesLeft++;
            }
        }"""

CHK_OLD2 = """public final class Zf133Check {

    private static final String TAG = "[A133] ";"""
CHK_NEW2 = """public final class Zf133Check {

    /** ⚠ 临时诊断开关（ZF133 查冷却门禁用），查完删。 */
    public static boolean DBG = false;

    private static final String TAG = "[A133] ";"""


def main():
    off = "--off" in sys.argv
    jobs = []
    for path, pairs in ((AXE, [(AXE_OLD, AXE_NEW)]),
                        (CHK, [(CHK_OLD, CHK_NEW), (CHK_OLD2, CHK_NEW2)])):
        s = io.open(path, encoding="utf-8").read()
        for a, b in ([(y, x) for x, y in pairs] if off else pairs):
            n = s.count(a)
            assert n == 1, "%s 锚点 %d 次：%r" % (path, n, a[:60])
            s = s.replace(a, b, 1)
        io.open(path, "w", encoding="utf-8", newline="\n").write(s)
        jobs.append(path)
    print("[OK] %s 完成：%s" % ("撤销" if off else "插入", jobs))
    if off:
        for path, needles in ((AXE, ["A133DBG2"]), (CHK, ["DBG"])):
            body = io.open(path, encoding="utf-8").read()
            for n in needles:
                print("  %s 残留 %s = %s" % (path, n, n in body))


main()
