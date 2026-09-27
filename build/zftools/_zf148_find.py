# -*- coding: utf-8 -*-
u"""_zf148_find.py —— ZF148 侦察⑩：把「要跟平的活体数字」在全部常驻门里找出来。

本轮会动的两个数：
  · 语言键数 **508 → 579**（lzh 510 → 581）
  · 配方条数 **73 → 74**
另外模组依赖从「零 mod 依赖」变成「硬依赖帕秋莉」，凡写死这两件事的门都要看一眼。
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")
TOOLS = r"E:\PotatoST\build\zftools"

PATS = [
    (u"键数 508", re.compile(u"508")),
    (u"键数 510（lzh）", re.compile(u"510")),
    (u"配方 73", re.compile(u"\\b73\\b")),
    (u"mod_version 0.12", re.compile(u"0\\.12")),
    (u"依赖 / 前置", re.compile(u"无需其它前置|零依赖|prerequisite|前置")),
]

hits = {}
for fn in sorted(os.listdir(TOOLS)):
    if not fn.endswith(u".py"):
        continue
    if fn.startswith(u"_zf148_"):
        continue
    p = os.path.join(TOOLS, fn)
    text = io.open(p, encoding=u"utf-8", errors=u"replace").read()
    for label, pat in PATS:
        n = len(pat.findall(text))
        if n:
            hits.setdefault(label, []).append((fn, n))

for label, _ in PATS:
    lst = hits.get(label, [])
    print(u"================ %s：%d 份文件 ================" % (label, len(lst)))
    for fn, n in lst:
        print(u"   %-34s %d 处" % (fn, n))
