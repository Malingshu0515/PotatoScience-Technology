# -*- coding: utf-8 -*-
u"""_zf155_countpeek2.py —— 公告里的键数提法 + `_zf150/_zf153` 两门怎么钉 587（只读）。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ANN = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"
ZT = r"E:\PotatoST\build\zftools"

ann = io.open(ANN, encoding="utf-8").read()
print(u"== 公告里所有 'keys each' 提法 ==")
for i, l in enumerate(ann.split("\n")):
    if u"keys each" in l or u"key" in l.lower() and u"each" in l:
        print(u"   %4d| %s" % (i + 1, l.strip()[:160]))

for fn in (u"_zf150_verify.py", u"_zf153_verify.py", u"_zf149_jar.py"):
    print(u"\n== %s" % fn)
    lines = io.open(ZT + "\\" + fn, encoding="utf-8", errors="replace").read().split("\n")
    for i, l in enumerate(lines):
        if re.search(u"\\b(587|589|583|585|579)\\b", l):
            print(u"   %4d| %s" % (i + 1, l.strip()[:170]))
