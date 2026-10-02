# -*- coding: utf-8 -*-
"""_zf133_dbg9.py —— 摆完方块之后**立刻**读一遍（同 tick、出手之前）

trace 给出的硬事实：波在 t1 采样的 `100,160,97..102` 全是 air、t2 的 `101,...` 也全是 air，
只有 t4 才看到 x=103 的原木。可是 checkB（20 tick 后）又能读到"剩 5 根"。
⇒ 只在一种情况下自洽：**我在 buildB 里摆的方块根本没落下去**（或落到了别的地方），
  而"剩 5 根"其实数的是 x=103 那一根 + 邻居。

这一刀在**出手之前**把三代坐标都读出来：x=101 / x=102 的 7 个 z、以及玩家周围的状态。
跑法：python build\\zftools\\_zf133_dbg9.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

ANCHOR = "        firPos = player.blockPosition();"
INSERT = """        firPos = player.blockPosition();
        for (int z = -3; z <= 3; z++) {
            BlockPos l1 = new BlockPos(X0 + 1, Y0, Z0 + z);
            BlockPos l2 = new BlockPos(X0 + 2, Y0 + 1, Z0 + z);
            say(TAG + "      [D9] x=101 z=" + z + " -> "
                    + level.getBlockState(l1).getBlock().getName().getString()
                    + " | x=102 y=161 -> "
                    + level.getBlockState(l2).getBlock().getName().getString());
        }
        say(TAG + "      [D9] 手上是 " + player.getMainHandItem().getItem()
                + " 玩家 " + player.blockPosition().toShortString());"""

s = io.open(P, encoding="utf-8").read()
n = s.count(ANCHOR)
assert n == 1, "锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(ANCHOR, INSERT, 1))
print("[OK] 已插入同 tick 读数")
