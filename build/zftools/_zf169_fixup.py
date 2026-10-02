# -*- coding: utf-8 -*-
u"""_zf169_fixup.py —— 把误写进 Java 的 Python 前缀 u" 去掉（第 11 次引号/转义类事故）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BAD = u'u' + u'"'
GOOD = u'"'
for p in (r"E:\PotatoST\src\main\java\com\potatost\mod\OreDetectorItem.java",
          r"E:\PotatoST\src\main\java\com\potatost\mod\GravityDeviceItem.java",
          r"E:\PotatoST\src\main\java\com\potatost\mod\BlackHoleManager.java"):
    t = io.open(p, encoding="utf-8").read()
    n = t.count(BAD)
    if n:
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(BAD, GOOD))
    print(u"%s：去掉 %d 处" % (p.split(u"\\")[-1], n))
