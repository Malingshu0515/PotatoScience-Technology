# -*- coding: utf-8 -*-
"""通道顺序甄别 + 修正。

现象：铜板解出来是**蓝**的（主色 RGBA(8,124,255)）—— 铜应该是橙铜色 (255,124,8)。
也就是说 R/B 被对调了（webp 容器/解码链按 BGRA 给，我按 RGBA 读）。
做法：三张图都以 R<->B 对调前的样子为准做判据 ——
  金属的"固有色调"是已知的：铜=橙、钢=偏冷的灰、普通板=中性灰。
  对调后 R>B 的像素（暖色）占比会明显上升。直接统计 R>B / R<B 的比例即可判定。
"""
import io
import os
import sys
from collections import Counter

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png

DIR = r"E:\PotatoST\build\zftools\_plate_imgs"


def load(name):
    w, h, flat = read_png(os.path.join(DIR, name))     # read_png 返回**扁平** RGBA 字节流
    px = [tuple(flat[i:i + 4]) for i in range(0, len(flat), 4)]
    return w, h, px


def stats(label, px):
    op = [p for p in px if p[3] > 0]
    warm = sum(1 for p in op if p[0] > p[2] + 8)
    cool = sum(1 for p in op if p[2] > p[0] + 8)
    r = sum(p[0] for p in op) / len(op)
    g = sum(p[1] for p in op) / len(op)
    b = sum(p[2] for p in op) / len(op)
    print("%-22s 不透明=%3d  均色=(%3.0f,%3.0f,%3.0f)  暖(R>B)=%3d  冷(B>R)=%3d"
          % (label, len(op), r, g, b, warm, cool))
    return warm, cool


print("== 现有（正确的）plate.png ==")
w, h, px = load(r"..\..\..\src\main\resources\assets\potato_s_t\textures\item\plate.png")
stats("plate.png", px)

print("\n== 这次三张：先看 原样读 的音调 ==")
res = {}
for name in ("copper_16x16.png", "plain_16x16.png", "steel_16x16.png"):
    _, _, px = load(name)
    res[name] = px
    stats(name + "（原样）", px)

print("\n== 若把 R/B 对调 ==")
for name, px in res.items():
    swapped = [(p[2], p[1], p[0], p[3]) for p in px]
    stats(name + "（对调后）", swapped)

