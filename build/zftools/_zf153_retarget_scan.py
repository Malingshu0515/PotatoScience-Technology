# -*- coding: utf-8 -*-
u"""_zf153_retarget_scan.py —— 扫出所有写死了语言键数的常驻脚本（**只读**）。

ZF153 加了 4 个键（物品名 + 三行说明）⇒ 四份语言 583 → **587**、lzh 585 → **589**。
凡是在代码里写死了 583 / 585 的地方都会红 —— 往轮（ZF119/125/150）的做法是
**一起重定靶**，但每一处都要先看清它是"键数断言"还是"碰巧长得像 583 的别的数"
（ZF150 那次就是无脑正则把跨行的 check() 改坏了，好在写盘前的 ast 自检挡住了）。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOLS = r"E:\PotatoST\build\zftools"
PAT = re.compile(r"\b(583|585)\b")

hits = []
for name in sorted(os.listdir(TOOLS)):
    if not name.endswith(".py"):
        continue
    if name.startswith("_zf153"):
        continue
    p = os.path.join(TOOLS, name)
    for i, line in enumerate(io.open(p, encoding="utf-8").read().split(u"\n"), 1):
        if PAT.search(line):
            hits.append((name, i, line.rstrip()))

print(u"命中 %d 行，分布在下列文件：" % len(hits))
byfile = {}
for name, i, line in hits:
    byfile.setdefault(name, []).append((i, line))
rep = []
rep.append(u"命中 %d 行，分布在下列文件：" % len(hits))
for name in sorted(byfile):
    rep.append(u"")
    rep.append(u"== %s（%d 处）==" % (name, len(byfile[name])))
    print(u"\n== %s（%d 处）==" % (name, len(byfile[name])))
    for i, line in byfile[name]:
        print(u"  %5d | %s" % (i, line.strip()[:200]))
        rep.append(u"  %5d | %s" % (i, line.strip()[:200]))
rep.append(u"")
rep.append(u"文件数 = %d" % len(byfile))
print(u"\n文件数 = %d" % len(byfile))
io.open(os.path.join(TOOLS, u"_zf153_retarget_scan.txt"), "w", encoding="utf-8",
        newline=u"\n").write(u"\n".join(rep) + u"\n")
