# -*- coding: utf-8 -*-
"""MakeSolarTexture.py —— 生成太阳能板的 16×16 方块贴图（0.10 ZF23）

**为什么要自己画**：用户给的 64×64 素材其实是 **Blockbench 的 UV 展开模板**，不是成品方块贴图 ——
实测：真正的画面只占**左上 32×32**，右上是一片浅灰 UV 条，**y16-31 纯黑、y32-63 一片 #202020**
（下半张全是填充）。把整张贴到顶面 ⇒ 面板 3/4 是死色块。
与其去猜"哪块区域对应顶面"，不如按项目统一规格画一张 16×16（用户也说了"你能自己画嘛"）。

**画法**（全部是规则的网格，所以用代码生成比手点像素更靠谱、也能重跑）：
  1. 1 像素金属边框，左上偏亮、右下偏暗（做出倒角）
  2. 内部 14×14 切成 **3×3 个 4×4 电池片**，缝宽 1 像素
  3. 每片左上角两点提亮 = 玻璃反光；整体自上而下逐行压暗 = 天光衰减
  4. 四个角点再压暗一点 = 安装压块

跑法：
    python build/zftools/MakeSolarTexture.py --out <目标.png>
    python build/zftools/MakeSolarTexture.py --out <目标.png> --preview <预览.png> --scale 16
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png   # 复用零依赖 PNG 写出器

SIZE = 16

# 调色板
FRAME_LIGHT = (0x9B, 0xA1, 0xA9)   # 边框左上（受光）
FRAME_DARK = (0x5C, 0x61, 0x68)    # 边框右下（背光）
FRAME_EDGE = (0x44, 0x48, 0x4E)    # 四个角
GAP = (0x08, 0x0C, 0x18)           # 电池片之间的缝：**必须比电池片更暗**（第一版用了浅灰蓝，
                                   #   结果像瓷砖缝，不像光伏板 —— 缝隙是阴影不是勾缝）
CELL = (0x24, 0x33, 0x66)          # 电池片主体（深蓝）
SHINE = (0x5A, 0x72, 0xBC)         # 玻璃反光
SHINE2 = (0x3A, 0x4B, 0x8C)        # 反光的过渡

# 3×3 片电池：内部 14 像素切成 4+1+4+1+4
CELL_STARTS = (1, 6, 11)
GAP_POS = {5, 10}


def build_pixels():
    px = [[None] * SIZE for _ in range(SIZE)]
    for y in range(SIZE):
        for x in range(SIZE):
            # ① 边框
            if x == 0 or y == 0:
                px[y][x] = FRAME_LIGHT
                continue
            if x == SIZE - 1 or y == SIZE - 1:
                px[y][x] = FRAME_DARK
                continue
            if x in (1, SIZE - 2) and y in (1, SIZE - 2):
                px[y][x] = FRAME_EDGE      # 四角压块
                continue
            # ② 缝
            if x in GAP_POS or y in GAP_POS:
                px[y][x] = GAP
                continue

            # ③ 落在哪片电池里、片内坐标
            col = max(i for i, s in enumerate(CELL_STARTS) if x >= s)
            row = max(i for i, s in enumerate(CELL_STARTS) if y >= s)
            dx = x - CELL_STARTS[col]
            dy = y - CELL_STARTS[row]

            # 自上而下、自左而右压暗：模拟天光从左上打下来（幅度要小，否则右下角死黑）
            shade = (row + col) * 3 + row * 2
            base = tuple(max(0, c - shade) for c in CELL)
            # 玻璃反光：**沿左上→右下递减**，而不是每片都画个一模一样的 L
            # （第一版 9 片全同，看着很"机械"）
            lvl = row + col
            if (dx, dy) == (0, 0):
                base = SHINE if lvl <= 1 else SHINE2
            elif (dx, dy) in ((1, 0), (0, 1)) and lvl <= 1:
                base = SHINE2
            px[y][x] = base
    return px


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", default=None)
    ap.add_argument("--scale", type=int, default=16)
    args = ap.parse_args(argv)

    px = build_pixels()
    rgba = bytearray(SIZE * SIZE * 4)
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b = px[y][x]
            o = (y * SIZE + x) * 4
            rgba[o], rgba[o + 1], rgba[o + 2], rgba[o + 3] = r, g, b, 255
    write_png(args.out, SIZE, SIZE, rgba)
    print("  已写出 {0}  ({1}x{1})".format(args.out, SIZE))

    if args.preview:
        S = args.scale
        T = SIZE * S
        out = bytearray(T * T * 4)
        for y in range(T):
            for x in range(T):
                si = ((y // S) * SIZE + (x // S)) * 4
                o = (y * T + x) * 4
                out[o:o + 4] = rgba[si:si + 4]
        write_png(args.preview, T, T, out)
        print("  预览 {0}  ({1}x{1}，放大 {2} 倍)".format(args.preview, T, S))

    print("")
    print("  逐像素（越亮字符越靠后）：")
    ramp = " .:-=+*#%@"
    for y in range(SIZE):
        line = ""
        for x in range(SIZE):
            r, g, b = px[y][x]
            v = (r * 299 + g * 587 + b * 114) // 1000
            line += ramp[min(v * len(ramp) // 256, len(ramp) - 1)]
        print("    " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
