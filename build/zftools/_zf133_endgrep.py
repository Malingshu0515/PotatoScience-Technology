# -*- coding: utf-8 -*-
"""_zf133_endgrep.py —— 在原始服务端日志里找"末地那一刀"的现场。

用法：
    python build\\zftools\\_zf133_endgrep.py
输出：把 _zf133_runSrv.log 里所有与 (h) 场景相关的行按行号打出来
（[DMG] / 末影人 / the_end / TRLOOP 里 dim=...the_end / TRENTRY / tick exception）。
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
LOG = os.path.join(ROOT, r"build\zftools\_zf133_runSrv.log")

PAT = re.compile(
    r"\[DMG\]|末影人|the_end|TRENTRY|tick exception|A133|TRLOOP"
)

body = io.open(LOG, encoding="utf-8", errors="replace").read().split("\n")
hits = 0
for i, line in enumerate(body, 1):
    if PAT.search(line):
        print("%6d| %s" % (i, line.rstrip()))
        hits += 1
print("---- 命中 %d 行 / 共 %d 行 ----" % (hits, len(body)))
