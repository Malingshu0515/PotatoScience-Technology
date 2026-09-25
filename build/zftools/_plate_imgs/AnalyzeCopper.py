# -*- coding: utf-8 -*-
"""ZF30：从用户给的**铜板**素材里抽隐藏色板，用于给其它金属上色。

为什么能这么做：那张 16×16 是"**同一张板材线稿 + 金属色**"的渲染图 ——
如果真是这样，那么把它的像素换成灰度再看，应该得到一张**中性灰**的板材线稿；
而原图每个像素的明度（value）就是要沿用的"形体明暗"。
于是给铁/镍/钴/银/铝生成新贴图 = **保留原始明度 + 套上各自的金属色相**。

判据（可失败）：如果铜板图**不是**"灰度线稿 × 单色"结构，
那 (R,G,B) 的色相分布会散开 —— 脚本会打印色相直方图并断言主色相占比。
"""
import colorsys
import io
import os
import sys
from collections import Counter

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png, write_png

DIR = r"E:\PotatoST\build\zftools\_plate_imgs"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"


def load(path):
    w, h, flat = read_png(path)
    return [tuple(flat[i:i + 4]) for i in range(0, len(flat), 4)]


px = load(os.path.join(DIR, "copper_plate.png"))
op = [p for p in px if p[3] > 0]

hues = Counter()
for r, g, b, a in op:
    hh, ss, vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    if ss < 0.15:
        hues["灰(低饱和)"] += 1
    else:
        hues[int(hh * 360 / 30) * 30] += 1
print("铜板素材的色相分布（30° 一档）：")
for k, v in hues.most_common():
    print("   %-10s %d" % (k, v))
print("不透明像素 %d" % len(op))

# 主色相占比（排除低饱和）
sat = [p for p in op if colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)[1] >= 0.15]
print("有饱和度的像素 = %d / %d（%.0f%%）" % (len(sat), len(op), 100.0 * len(sat) / len(op)))

# 明度直方图：看是不是"一张线稿的明暗范围"
vals = sorted(colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)[2] for p in op)
print("明度：min=%.2f  中位=%.2f  max=%.2f" % (vals[0], vals[len(vals) // 2], vals[-1]))
