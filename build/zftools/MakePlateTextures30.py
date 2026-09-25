# -*- coding: utf-8 -*-
"""ZF30：把用户给的三张板材素材落成项目贴图。

素材链：webp →（WPF BitmapDecoder.CopyPixels）→ `*.rgba`（16×16×4 字节）→ 本脚本。

⚠ **踩过的坑：`.bgra` 这个扩展名是我自己起错的，它其实是 RGBA。**
   我第一次"验证通道顺序"时写了个脚本，脚本里**先对调再打印**，
   于是"对调后颜色正确"被当成了"必须对调"的证据 —— **循环论证**。
   真相只要看原始字节就清楚：
     铜的最饱和像素字节 = (255, 108, 1, 255) ⇒ 按 **R,G,B,A** 读正是铜橙 (255,108,1)；
     三张图按 RGBA 读的均色：copper (215,111,30) 暖 154/冷 0、steel (121,122,125) 冷 17/暖 0、
     plain (171,171,171) 中性 —— 与"铜是橙的、钢是冷灰的"完全吻合。
   ⇒ **结论：不做任何通道变换，原字节即 RGBA。**
   教训（写进档案）：**别拿"文件名/扩展名"当格式证据；也别在'验证'脚本里顺手做变换，
     那等于把假设当成了结论。** 先打印原始字节，再下判断。

产出：
  textures/item/copper_plate.png  ← 铜板（新文件）
  textures/item/plate.png         ← 覆盖：普通板（铁/镍/钴/银/铝，用户指定共用）
  textures/item/steel_plate.png   ← 钢板单独一张（用户指定）
"""
import io
import os
import sys
from collections import Counter

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import write_png

SRC_DIR = r"E:\PotatoST\build\zftools\_plate_imgs"
TEX_DIR = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"

JOBS = [
    ("copper.rgba", "copper_plate.png"),   # 铜板：新文件
    ("plain.rgba", "plate.png"),           # 普通板：覆盖 ZF16 那张（铁/镍/钴/银/铝共用）
    ("steel.rgba", "steel_plate.png"),     # 钢板：新文件
]

for src, out in JOBS:
    raw = io.open(os.path.join(SRC_DIR, src), "rb").read()
    assert len(raw) == 16 * 16 * 4, "%s 不是 16x16（%d 字节）" % (src, len(raw))
    dst = os.path.join(TEX_DIR, out)
    old = os.path.getsize(dst) if os.path.exists(dst) else None
    write_png(dst, 16, 16, raw)            # ← 原字节直传，不做任何通道变换(见文件头)
    px = [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)]
    op = [p for p in px if p[3] > 0]
    r = sum(p[0] for p in op) / len(op)
    g = sum(p[1] for p in op) / len(op)
    b = sum(p[2] for p in op) / len(op)
    warm = sum(1 for p in op if p[0] > p[2] + 8)
    cool = sum(1 for p in op if p[2] > p[0] + 8)
    print("%-13s -> %-18s 不透明=%3d 均色=(%3.0f,%3.0f,%3.0f) 暖=%3d 冷=%3d  %s"
          % (src, out, len(op), r, g, b, warm, cool,
             ("覆盖 %d→%d 字节" % (old, os.path.getsize(dst))) if old else
             ("新建 %d 字节" % os.path.getsize(dst))))
