# -*- coding: utf-8 -*-
r"""_zf92_uvlabel.py —— 在 UV 索引图上按 16px 网格标注坐标，便于对着截图认块

输出 build/zftools/_zf92_uvindex_labelled.png：原索引图 + 每 16 像素一条暗线 + 每 32 像素更亮的线。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402

SRC = os.path.join(HERE, "_zf92_uvindex.png")
OUT = os.path.join(HERE, "_zf92_uvindex_labelled.png")

w, h, _, px = P.read_png(SRC)
out = list(px)
for y in range(h):
    for x in range(w):
        if x % 16 == 0 or y % 16 == 0:
            r, g, b, a = out[y * w + x]
            f = 0.45 if (x % 32 and y % 32) else 0.15
            out[y * w + x] = (int(r * f), int(g * f), int(b * f), 255)
P.write_png(OUT, w, h, out)
print(u"→ %s" % OUT)
