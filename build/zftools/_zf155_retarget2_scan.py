# -*- coding: utf-8 -*-
u"""_zf155_retarget2_scan.py —— 扫出**跟平后仍然残留**的 587 / 589（逐条给上下文，人判该不该改）。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
PAT = re.compile(r"^_zf\d+_(verify|guard|repro|audit|langaudit|tabaudit|recipe_guard|jar)\.py$")

for fn in sorted(os.listdir(ZT)):
    if not PAT.match(fn) or fn == u"_zf155_verify.py":
        continue
    lines = io.open(os.path.join(ZT, fn), encoding="utf-8", errors="replace").read().split("\n")
    for i, l in enumerate(lines):
        if re.search(r"(?<![0-9a-fA-F])(587|589)(?![0-9a-fA-F])", l):
            print(u"== %s:%d" % (fn, i + 1))
            for j in range(max(0, i - 2), min(len(lines), i + 3)):
                print(u"   %s%5d| %s" % (u">>" if j == i else u"  ", j + 1, lines[j].rstrip()[:150]))
