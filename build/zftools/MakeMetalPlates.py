# -*- coding: utf-8 -*-
"""ZF30 附带工具（**未运行，留给用户决定**）：把共用那张普通板按金属上色。

背景：用户这次给的三张素材是「铜板 / 普通板 / 钢板」，明确说第二张给"除了铜和钢板的板"用
⇒ 铁/镍/钴/银/铝**共用同一张灰板**，在背包里**彼此完全一样**。
这与 ZF16 时"6 种板共用一张"是同一个状况，用户当时也是这么指定的。

本脚本让它**变成可选**：按金属的固有色给"普通板"上色，各生成一张。
判据/做法：
  · 以铜板素材为**形体模板**（它的明暗关系就是板材的形体），
    取每个像素的 HSV，**保留明度 V**，只把色相 H / 饱和度 S 换成目标金属的；
  · 低饱和（描边、阴影）像素保持原样 ⇒ 轮廓不会花。
跑法：
    python build/zftools/MakeMetalPlates.py            # 只预览统计，不写盘
    python build/zftools/MakeMetalPlates.py --write    # 真的生成 5 张并打印要改的模型
生成后还需要**手动**把 models/item/<metal>_plate.json 的 layer0 指到新贴图（脚本会打印清单）。
"""
import colorsys
import io
import os
import sys

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png, write_png

TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"

# 目标金属：色相(度) / 饱和度倍率 / 明度倍率 —— 都是"看起来像那种金属"的经验值
METALS = [
    ("iron", 30, 0.06, 0.92),        # 铁：几乎无彩，稍暗
    ("nickel", 45, 0.10, 1.00),      # 镍：极淡的暖黄
    ("cobalt", 220, 0.45, 0.88),     # 钴：蓝
    ("silver", 210, 0.04, 1.10),     # 银：中性、最亮
    ("aluminum", 205, 0.07, 1.02),   # 铝：偏冷的浅灰
]

WRITE = "--write" in sys.argv

w, h, flat = read_png(os.path.join(TEX, "copper_plate.png"))
src = [tuple(flat[i:i + 4]) for i in range(0, len(flat), 4)]

for name, hue_deg, sat_mul, val_mul in METALS:
    out = []
    for r, g, b, a in src:
        if a == 0:
            out.append((0, 0, 0, 0))
            continue
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        if ss < 0.15:                      # 描边/阴影：保持中性
            nr, ng, nb = r, g, b
        else:
            nh = hue_deg / 360.0
            ns = min(1.0, ss * sat_mul)
            nv = min(1.0, vv * val_mul)
            fr, fg, fb = colorsys.hsv_to_rgb(nh, ns, nv)
            nr, ng, nb = int(fr * 255), int(fg * 255), int(fb * 255)
        out.append((nr, ng, nb, a))
    op = [p for p in out if p[3] > 0]
    r = sum(p[0] for p in op) / len(op)
    g = sum(p[1] for p in op) / len(op)
    b = sum(p[2] for p in op) / len(op)
    mark = ""
    if WRITE:
        path = os.path.join(TEX, "%s_plate.png" % name)
        buf = bytearray()
        for c in out:
            buf += bytes(c)
        write_png(path, 16, 16, buf)
        mark = "  -> 已写 %s_plate.png" % name
    print("%-9s 均色=(%3.0f,%3.0f,%3.0f)%s" % (name, r, g, b, mark))

if WRITE:
    print("\n还要手动改这些模型的 layer0 指向新贴图：")
    for name, *_ in METALS:
        print("   models/item/%s_plate.json  -> potato_s_t:item/%s_plate" % (name, name))
else:
    print("\n（这只是预览统计；加 --write 才真的生成贴图）")
