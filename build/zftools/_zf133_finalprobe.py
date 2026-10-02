# -*- coding: utf-8 -*-
"""_zf133_finalprobe.py —— 最后一次取证跑：把 (e)/(b) 的场景在**出手前**逐格读一遍

前面几轮一直在推"波为什么少拆一格"，但**从来没在出手那一刻把那一格读出来过**。
这次在 buildE / buildB 里，摆好之后、出手之前，把整排（6 列）的真实方块打出来 ——
要区分两件事：① 我压根没摆上（放置失败）；② 摆上了但波没拆（判据问题）。

同时把 (i) 的检查点从 490 再核一遍（出手 450 ⇒ 射程到 514）。

跑法：python build\\zftools\\_zf133_finalprobe.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# (e)：摆好那一格木头之后立刻读整排
A1 = "        level.setBlockAndUpdate(new BlockPos(X0 + 4, Y0, Z0), Blocks.OAK_LOG.defaultBlockState());"
B1 = A1 + """
        for (int lat = 0; lat < 6; lat++) {
            BlockPos q = new BlockPos(X0 + 4, Y0, Z0 - 3 + lat);
            say(TAG + "      [E] 出手前 x=104 第" + lat + "列 " + q.toShortString() + " = "
                    + level.getBlockState(q).getBlock().getName().getString());
        }
        say(TAG + "      [E] 玩家 " + player.blockPosition().toShortString()
                + " 手上 " + player.getMainHandItem().getItem());"""

# (b)：摆好那一排之后立刻读整排
A2 = "        firPos = player.blockPosition();"
B2 = """        for (int lat = -3; lat <= 2; lat++) {
            BlockPos q = new BlockPos(X0 + 1, Y0, Z0 + lat);
            BlockPos r = new BlockPos(X0 + 2, Y0 + 1, Z0 + lat);
            say(TAG + "      [B] 出手前 x=101 z=" + lat + " = "
                    + level.getBlockState(q).getBlock().getName().getString()
                    + " ／ x=102 y=161 = "
                    + level.getBlockState(r).getBlock().getName().getString());
        }
""" + A2

s = io.open(CHK, encoding="utf-8").read()
for i, (a, b) in enumerate([(A1, B1), (A2, B2)]):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("已加出手前读数")
