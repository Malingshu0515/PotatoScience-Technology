# -*- coding: utf-8 -*-
u"""_zf148_find2.py —— ZF148 侦察⑪：把所有常驻门里带 508 / 510 的**整行**列出来。

跟平脚本要按行点名排除「说的不是盘上现在键数」的那种行，所以先把清单看清。
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")
TOOLS = r"E:\PotatoST\build\zftools"

for tag in (u"508", u"510"):
    print(u"================ %s ================" % tag)
    for fn in sorted(os.listdir(TOOLS)):
        if not fn.endswith(u"_verify.py") or fn.startswith(u"_zf148_"):
            continue
        p = os.path.join(TOOLS, fn)
        for i, line in enumerate(io.open(p, encoding=u"utf-8", errors=u"replace").read().split(u"\n")):
            if tag in line:
                print(u"  %-22s %4d | %s" % (fn, i + 1, line.strip()[:150]))
