# -*- coding: utf-8 -*-
u"""_zf155_gatelist.py —— 列出盘上全部常驻门，并与 ZF148 那份快照名单对差（只读）。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
PAT = re.compile(r"^_zf\d+_(verify|guard|repro|audit|langaudit|tabaudit|recipe_guard)\.py$")

t = io.open(os.path.join(ZT, u"_zf148_gatesnap.py"), encoding="utf-8").read()
old = set(re.findall(r'"(_zf\d+_[a-zA-Z_]+\.py)"', t))
allf = sorted(f for f in os.listdir(ZT) if PAT.match(f))

print(u"ZF148 名单 %d 个；盘上现在 %d 个" % (len(old), len(allf)))
print(u"\n盘上有、名单里没有（要补进本轮快照）：")
for f in allf:
    if f not in old:
        print(u"   + %s" % f)
print(u"\n名单里有、盘上不在（别人删了 / 改名了）：")
for f in sorted(old):
    if f not in allf:
        print(u"   - %s" % f)
