# -*- coding: utf-8 -*-
r"""_zf97_preview.py —— 把本轮 8 张 16×16 贴图放大 6 倍拼成一张预览图（肉眼复核）。

输出：build\zftools\_zf97_preview.png
上排：氮气 / 氨气 / 空气分离器侧 / 空气分离器顶
下排：氨气组成室侧 / 氨气组成室顶 / （空两格）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BLOCK_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "block")
OUT = os.path.join(ROOT, "build", "zftools", "_zf97_preview.png")

SCALE = 6
GAP = 6
BG = (96, 96, 96, 255)
NAMES = [u"nitrogen_still", u"ammonia_still", u"air_separator_side", u"air_separator_top",
         u"ammonia_synthesis_chamber_side", u"ammonia_synthesis_chamber_top"]
COLS = 4


def main():
    tiles = [P.read_png(os.path.join(BLOCK_DIR, n + ".png")) for n in NAMES]
    cell = 16 * SCALE
    rows = (len(tiles) + COLS - 1) // COLS
    out_w = COLS * cell + GAP * (COLS + 1)
    out_h = rows * cell + GAP * (rows + 1)
    canvas = bytearray()
    for _ in range(out_w * out_h):
        canvas += bytes(BG)
    for idx, (w, h, rgba) in enumerate(tiles):
        cx = idx % COLS
        cy = idx // COLS
        x0 = GAP + cx * (cell + GAP)
        y0 = GAP + cy * (cell + GAP)
        for y in range(h):
            for x in range(w):
                i = (y * w + x) * 4
                px = rgba[i:i + 4]
                solid = len(px) == 4 and px[3] != 0
                use = px if solid else bytes((180, 180, 180, 255))
                for dy in range(SCALE):
                    for dx in range(SCALE):
                        j = ((y0 + y * SCALE + dy) * out_w + (x0 + x * SCALE + dx)) * 4
                        canvas[j:j + 4] = use
    P.write_png(OUT, out_w, out_h, canvas)
    print(u"写出 %s（%dx%d，%d 张）" % (OUT, out_w, out_h, len(tiles)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
