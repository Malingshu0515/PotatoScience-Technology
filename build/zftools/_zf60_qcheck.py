# -*- coding: utf-8 -*-
"""_zf60_qcheck.py —— 数一数 ps1 里每行的 ASCII 双引号是不是成对（解析报错时先查这个）"""
import io
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r"E:\PotatoST\build\zftools\_zf60_decode.ps1"
text = io.open(path, encoding="utf-8").read()
odd = 0
for i, line in enumerate(text.splitlines(), 1):
    n = line.count(u'"')
    if n % 2:
        odd += 1
        print(u"ODD(%d) line %d: %s" % (n, i, repr(line[:160])))
print(u"total lines = %d, odd-quote lines = %d" % (len(text.splitlines()), odd))
