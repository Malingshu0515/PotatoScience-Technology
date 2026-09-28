# -*- coding: utf-8 -*-
u"""_zf155_countpeek.py —— 看那些写死 587 / 589 / 592 / 579 / 594 / 596 的门到底怎么用这些数（只读）。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
PAT = re.compile(r"^_zf\d+_(verify|guard|repro|audit|langaudit|tabaudit|recipe_guard|jar)\.py$")
NUMS = ["587", "589", "592", "579", "594", "596"]
KEYWORDS = (u"键", u"KEYS", u"KEY", u"key", u"lang", u"LANG")

for fn in sorted(os.listdir(ZT)):
    if not PAT.match(fn):
        continue
    lines = io.open(os.path.join(ZT, fn), encoding="utf-8", errors="replace").read().split("\n")
    out = []
    for i, l in enumerate(lines):
        if any(n in l for n in NUMS):
            tag = u"KEY?" if any(k in l for k in KEYWORDS) else u"---?"
            out.append(u"      %s %4d| %s" % (tag, i + 1, l.strip()[:150]))
    if out:
        print(u"== %s" % fn)
        print(u"\n".join(out))
