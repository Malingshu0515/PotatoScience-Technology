# -*- coding: utf-8 -*-
"""_zf133_cleanup4.py —— 撤掉最后两行 [DBG] 树叶位打印（行号定位，改完复核 scan）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """            say(TAG + "      [DBG] 树叶位 " + lp.toShortString() + " = "
                    + level.getBlockState(lp).getBlock().getName().getString());
"""

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(P, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, "", 1))
print("[OK] 已撤最后两行")
# BlockPos lp 这个局部变量还有用到（下面 if 里），别删
for needle in ("[DBG]", "A133DBG", "DEBUG"):
    print("  残留 %-10s = %s" % (needle, needle in io.open(P, encoding="utf-8").read()))
