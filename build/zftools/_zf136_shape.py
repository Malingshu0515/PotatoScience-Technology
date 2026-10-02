# -*- coding: utf-8 -*-
"""_zf136_shape.py —— 新图是"哪一件"？按**形状**和**配色**跟现有 6 件比对（只读）

判据不是感觉：
  · alpha 掩码相似度（形状像不像）—— IoU；
  · 不透明像素数（体量）；
  · 主色是否落在星璨钢那一族（紫蓝）。
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

SRC = r"E:\PotatoST\build\用户素材\星璨钢重置.png"
T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"

CAND = ["star_steel_ingot", "star_steel_helmet", "star_steel_chestplate",
        "star_steel_leggings", "star_steel_boots", "star_steel_axe"]


def load(p):
    w, h, rgba = read_png(p)
    a = np.array(rgba, dtype=np.uint8).reshape(h, w, 4)
    return a


def mask(a):
    return a[:, :, 3] == 255


def iou(m1, m2):
    inter = int((m1 & m2).sum())
    union = int((m1 | m2).sum())
    return inter / union if union else 0.0


def mean_color(a):
    m = mask(a)
    if m.sum() == 0:
        return (0, 0, 0)
    px = a[m][:, :3].astype(float)
    return tuple(int(v) for v in px.mean(axis=0))


new = load(SRC)
nm = mask(new)
print(u"新图 星璨钢重置.png：不透明 %d 像素，平均色 #%02x%02x%02x"
      % (nm.sum(), *mean_color(new)))
print()
print(u"%-26s %8s %8s %8s   %s" % (u"对照", u"不透明", u"IoU", u"平均色", u"色彩距离"))
rows = []
for n in CAND:
    p = os.path.join(T, n + ".png")
    if not os.path.exists(p):
        print(u"  %-26s （缺）" % n)
        continue
    a = load(p)
    m = mask(a)
    v = iou(nm, m)
    mc = mean_color(a)
    nc = mean_color(new)
    dist = sum((mc[i] - nc[i]) ** 2 for i in range(3)) ** 0.5
    rows.append((v, n, int(m.sum()), mc, dist))
    print(u"%-26s %8d %8.3f  #%02x%02x%02x   %6.1f" % (n, m.sum(), v, *mc, dist))

rows.sort(reverse=True)
print()
print(u"按形状相似度排：")
for v, n, cnt, mc, dist in rows:
    print(u"  %-26s IoU %.3f" % (n, v))
print()
best = rows[0]
print(u"==> 形状最像的是 **%s**（IoU %.3f）" % (best[1], best[0]))
print(u"    ⚠ IoU 只说明「轮廓像不像」，不说明「用户指的是哪一件」 —— 见汇报里的判断依据。")
