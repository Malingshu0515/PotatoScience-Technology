# -*- coding: utf-8 -*-
"""_zf133_dbgprobe.py —— 临时：让探针 (b) 场景打开诊断开关并打印前一格的状态

查"波不拆方块"用，查完连同 ShockwaveManager 里的 trace 一起撤（`_zf133_dbgtrace.py --off`）。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """        firPos = player.blockPosition();
        int dmgBefore = axe.getDamageValue();"""
NEW = """        firPos = player.blockPosition();
        // ⚠ 临时诊断（ZF133）：打开波内部的逐格 trace，并把采样格直接读出来对照
        ShockwaveManager.DEBUG = true;
        for (int z = -3; z <= 3; z++) {
            BlockPos p = new BlockPos(X0 + 1, Y0, Z0 + z);
            say(TAG + "      [DBG] 放完后 " + p.toShortString() + " = "
                    + level.getBlockState(p).getBlock().getName().getString()
                    + "（可砍=" + (!level.getBlockState(p).isAir()) + "）");
        }
        say(TAG + "      [DBG] 玩家 " + player.blockPosition().toShortString()
                + " 视线 " + player.getLookAngle() + " 朝向 " + player.getDirection());
        int dmgBefore = axe.getDamageValue();"""


def main():
    s = io.open(P, encoding="utf-8").read()
    n = s.count(OLD)
    assert n == 1, "锚点 %d 次" % n
    io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
    print("[OK] 探针已加诊断输出")


main()
