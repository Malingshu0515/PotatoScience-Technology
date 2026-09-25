# -*- coding: utf-8 -*-
r"""_zf96_preview.py —— 把本轮三张 16×16 贴图放大 8 倍拼成一张预览图，方便肉眼复核。

输出：build\zftools\_zf96_preview.png（左：机器侧面 / 中：机器顶面 / 右：硫）
底色画成中灰，免得透明区域看不出轮廓。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BLOCK_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "block")
ITEM_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "item")
OUT = os.path.join(ROOT, "build", "zftools", "_zf96_preview.png")

SCALE = 8
GAP = 8
BG = (96, 96, 96, 255)

SOURCES = [
    os.path.join(BLOCK_DIR, "hydrodesulfurization_chamber_side.png"),
    os.path.join(BLOCK_DIR, "hydrodesulfurization_chamber_top.png"),
    os.path.join(ITEM_DIR, "sulfur.png"),
]


def main():
    tiles = [P.read_png(p) for p in SOURCES]
    tw = sum(t[0] * SCALE for t in tiles)
    out_w = tw + GAP * (len(tiles) + 1)
    out_h = 16 * SCALE + GAP * 2
    canvas = bytearray()
    for _ in range(out_w * out_h):
        canvas += bytes(BG)
    x0 = GAP
    for (w, h, rgba) in tiles:
        for y in range(h):
            for x in range(w):
                i = (y * w + x) * 4
                px = rgba[i:i + 4]
                for dy in range(SCALE):
                    for dx in range(SCALE):
                        ox = x0 + x * SCALE + dx
                        oy = GAP + y * SCALE + dy
                        j = (oy * out_w + ox) * 4
                        if len(px) == 4 and px[3] == 0:
                            # 透明像素画成浅灰格，提示"这里是透明的"
                            canvas[j:j + 4] = bytes((180, 180, 180, 255))
                        else:
                            canvas[j:j + 4] = px
        x0 += w * SCALE + GAP
    P.write_png(OUT, out_w, out_h, canvas)
    print(u"写出 %s（%dx%d，放大 %d 倍）" % (OUT, out_w, out_h, SCALE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
