# -*- coding: utf-8 -*-
"""_zf133_parentfix12.py —— 修那一行引号（我把 `"` 写进了 Java 字符串里）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

BAD = """        failed += check("事件监听确实抓不到（末地龙不调 super.hurt ⇒ 这条是"记录的坑"）",
                true);"""
GOOD = """        failed += check("（记录）事件监听抓不到这条伤害：末地龙不调 super.hurt", true);"""

s = io.open(CHK, encoding="utf-8").read()
n = s.count(BAD)
assert n == 1, "锚点 %d 次" % n
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(BAD, GOOD, 1))
print("[OK] 引号已修")
