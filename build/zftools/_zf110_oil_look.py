# -*- coding: utf-8 -*-
"""_zf110_oil_look.py —— 把 _zf110_oil_pixels.json 的真实像素摊开看（只读）

背景色判定为什么错了？把 16x16 逐像素的 RGB 与"离四角中位色的距离"一起打出来，
同时给四角 / 四边 / 内部的统计，再按"暗/亮"分类画一张图。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = r"E:\PotatoST\build\zftools"
d = json.loads(io.open(os.path.join(TOOLS, "_zf110_oil_pixels.json"), encoding="utf-8").read())
px = [tuple(int(v) for v in s.split(",")) for s in d["px"]]
W = H = 16

print("== 四角 / 四边统计 ==")
corners = {"左上": px[0], "右上": px[15], "左下": px[240], "右下": px[255]}
for k, v in corners.items():
    print("  %s = RGB%s" % (k, v[:3]))
med = tuple(sorted(c[i] for c in corners.values())[1] for i in range(3))
print("  四角中位色 = RGB%s" % (med,))

print("\n== 逐像素 RGB（只打前 3 通道）==")
for y in range(H):
    row = []
    for x in range(W):
        r, g, b, _ = px[y * W + x]
        row.append("%3d,%3d,%3d" % (r, g, b))
    print("  y%02d " % y + " | ".join(row))

print("\n== 亮度字符画（同一张，便于对照）==")
ramp = " .:-=+*#%@"
for y in range(H):
    line = ""
    for x in range(W):
        r, g, b, _ = px[y * W + x]
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        line += ramp[min(len(ramp) - 1, int(lum * (len(ramp) - 1)))]
    print("  |" + line + "|")

print("\n== 按'是否接近四角中位色(TOL=26)'分类 ==")
TOL = 26
for y in range(H):
    line = ""
    for x in range(W):
        p = px[y * W + x]
        close = all(abs(p[c] - med[c]) <= TOL for c in range(3))
        line += "B" if close else "."
    print("  |" + line + "|")

print("\n== 亮度直方图 ==")
import collections
hist = collections.Counter()
for p in px:
    lum = int((0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]))
    hist[lum // 16] += 1
for k in sorted(hist):
    print("  %3d-%3d : %s (%d)" % (k * 16, k * 16 + 15, "#" * hist[k], hist[k]))

print("\n== 边框像素（最外圈）明细 ==")
border = []
for x in range(W):
    border.append((0, x, px[x]))
    border.append((H - 1, x, px[(H - 1) * W + x]))
for y in range(1, H - 1):
    border.append((y, 0, px[y * W]))
    border.append((y, W - 1, px[y * W + W - 1]))
bright = [b for b in border if 0.299 * b[2][0] + 0.587 * b[2][1] + 0.114 * b[2][2] > 128]
dark = [b for b in border if 0.299 * b[2][0] + 0.587 * b[2][1] + 0.114 * b[2][2] <= 128]
print("  边框共 %d 个像素：亮 %d，暗 %d" % (len(border), len(bright), len(dark)))
print("  最外圈里最亮的 8 个：")
for y, x, p in sorted(border, key=lambda t: -(0.299 * t[2][0] + 0.587 * t[2][1] + 0.114 * t[2][2]))[:8]:
    print("    (%2d,%2d) RGB%s" % (y, x, p[:3]))
