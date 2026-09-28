# -*- coding: utf-8 -*-
u"""扫我自己脚本里「中文串里嵌了 ASCII 双引号」的行（这坑本会话第 6 次了）。

判据：一行里有 CJK，且 ASCII 双引号个数是**奇数**或 ≥4 —— 正常一行只该有 2 个（成对定界）。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf153_verify.py"
CJK = re.compile(u"[\u4e00-\u9fff]")

lines = io.open(P, encoding="utf-8").read().split(u"\n")
bad = []
for i, l in enumerate(lines, 1):
    code = l.split(u"#")[0]
    n = code.count(u'"')
    if CJK.search(code) and n >= 4:
        bad.append((i, l))
print(u"可疑行 %d 条：" % len(bad))
for i, l in bad:
    print(u"  %4d | %s" % (i, l))
