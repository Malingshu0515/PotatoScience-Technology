# -*- coding: utf-8 -*-
u"""_zf117_look.py —— 看清这两个方块"现在的侧面"长什么样（只读）

目的：确认「现有的 lithium_battery_plant.png / diesel_generator_controller.png 是不是侧面」
（用户这次给的是顶/底，那侧面必须来自某张已有图；不能猜）。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

TEXB = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
RAMP = " .:-=+*#%@"

FILES = ["lithium_battery_plant.png", "diesel_generator_controller.png",
         "lithium_battery_side.png", "low_generator_side.png"]


def art(w, h, rgba):
    rows = []
    for y in range(h):
        line = []
        for x in range(w):
            i = (y * w + x) * 4
            if rgba[i + 3] == 0:
                line.append(" ")
                continue
            lum = (0.299 * rgba[i] + 0.587 * rgba[i + 1] + 0.114 * rgba[i + 2]) / 255.0
            line.append(RAMP[min(len(RAMP) - 1, int(lum * (len(RAMP) - 1)))])
        rows.append("".join(line))
    return rows


for f in FILES:
    p = os.path.join(TEXB, f)
    print("=" * 60)
    if not os.path.exists(p):
        print(u"%s  不存在" % f)
        continue
    b = open(p, "rb").read()
    w, h, rgba = read_png(p)
    n = w * h
    op = sum(1 for i in range(n) if rgba[i * 4 + 3] == 255)
    cols = {}
    sr = sg = sb = 0
    for i in range(n):
        if rgba[i * 4 + 3] == 0:
            continue
        k = (rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2])
        cols[k] = cols.get(k, 0) + 1
        sr += k[0]; sg += k[1]; sb += k[2]
    c = max(1, sum(cols.values()))
    print(u"%s   %d B  %dx%d  位深%d 类型%d  不透明 %d/%d  颜色数 %d  平均色 #%02x%02x%02x"
          % (f, len(b), w, h, b[24], b[25], op, n, len(cols), sr // c, sg // c, sb // c))
    if w <= 32 and h <= 32:
        for r in art(w, h, rgba):
            print(u"    |" + r + u"|")
    else:
        print(u"    （%dx%d 太大，只打前 16x16 左上角）" % (w, h))
        for r in art(16, 16, rgba):
            print(u"    |" + r + u"|")
