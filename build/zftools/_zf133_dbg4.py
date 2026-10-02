# -*- coding: utf-8 -*-
"""_zf133_dbg4.py —— 在 (b) 场景里打印摆好之后玩家在哪（确认脚下那格已清空）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = "        level.setBlockAndUpdate(new BlockPos(X0 + 1, Y0, Z0), Blocks.AIR.defaultBlockState());"
NEW = OLD + """
        say(TAG + "      [DBG] 摆好之后玩家在哪：" + player.blockPosition().toShortString()
                + "（他脚下那格已清空 ⇒ 不会被卡住）");"""

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] 已加玩家位置打印")
