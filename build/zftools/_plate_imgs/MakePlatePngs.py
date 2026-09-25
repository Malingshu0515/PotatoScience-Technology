# -*- coding: utf-8 -*-
"""把用户这次给的三张板材素材（16×16 webp → BGRA）落成 PNG，并打印配色概览。

为什么这次不需要降采样：素材**本来就是 16×16**（实测），
与 ZF16 那次（160×160 抗锯齿图）不同，所以直接转格式即可，不跑 MakePlateTexture 的 box filter。
"""
import io
import os
import sys
from collections import Counter

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import write_png

DIR = r"E:\PotatoST\build\zftools\_plate_imgs"
JOBS = [("copper.bgra", "copper_16x16.png"),
        ("plain.bgra", "plain_16x16.png"),
        ("steel.bgra", "steel_16x16.png")]

for src, out in JOBS:
    raw = io.open(os.path.join(DIR, src), "rb").read()
    assert len(raw) == 16 * 16 * 4, "%s 不是 16x16 BGRA（%d 字节）" % (src, len(raw))
    # write_png 要的是**扁平 RGBA 字节流**（长度 w*h*4），不是 tuple 列表
    flat = bytearray(len(raw))
    for i in range(0, len(raw), 4):
        b, g, r, a = raw[i], raw[i + 1], raw[i + 2], raw[i + 3]
        flat[i], flat[i + 1], flat[i + 2], flat[i + 3] = r, g, b, a
    write_png(os.path.join(DIR, out), 16, 16, flat)
    px = [tuple(flat[i:i + 4]) for i in range(0, len(flat), 4)]
    cnt = Counter(px)
    opaque = sum(c for p, c in cnt.items() if p[3] > 0)
    print("%-14s -> %-18s 颜色种类=%3d  不透明像素=%d/256" % (src, out, len(cnt), opaque))
    for color, c in cnt.most_common(5):
        print("      RGBA%-22s x%d" % (str(color), c))
