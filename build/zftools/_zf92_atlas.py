# -*- coding: utf-8 -*-
r"""_zf92_atlas.py —— 把高炉贴图放大并叠上 16 像素网格（+ 可选高亮某些元素的 UV 矩形）

为什么要看这张图：用户报"某个小方块的顶面和正面贴图对调了"。贴图是用户手画的 UV 展开图，
瓦片是按 16 像素一格排的；把网格叠上去就能直接读出"艺术家把哪一格画成了顶面、哪一格画成了侧面"，
从而判断模型里哪个面拿错了格子。

用法:
    python _zf92_atlas.py <out.png> [scale] [高亮元素序号,逗号分隔]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BB = r"C:\PotatoST救援\zf91_pre\user\electric_blast_furnace.bbmodel"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"
COLORS = [(255, 60, 60), (60, 255, 60), (80, 160, 255), (255, 220, 40), (255, 80, 255), (60, 255, 255)]


def main(argv):
    out = argv[0]
    scale = int(argv[1]) if len(argv) > 1 else 4
    hi = [int(v) for v in argv[2].split(",")] if len(argv) > 2 else []
    tw, th, _, tex = P.read_png(TEX)
    W, H = tw * scale, th * scale
    buf = []
    for y in range(H):
        for x in range(W):
            r, g, b, a = tex[(y // scale) * tw + (x // scale)]
            buf.append((r, g, b, 255) if a else (40, 40, 44, 255))
    # 16 像素网格：浅灰；64 像素：更亮
    for gy in range(0, th + 1, 16):
        for x in range(W):
            c = (255, 255, 255, 255) if gy % 64 == 0 else (120, 120, 130, 255)
            buf[min(H - 1, gy * scale) * W + x] = c
    for gx in range(0, tw + 1, 16):
        for y in range(H):
            c = (255, 255, 255, 255) if gx % 64 == 0 else (120, 120, 130, 255)
            buf[y * W + min(W - 1, gx * scale)] = c
    if hi:
        d = json.loads(open(BB, encoding="utf-8").read())
        for n, ei in enumerate(hi):
            col = COLORS[n % len(COLORS)]
            e = d["elements"][ei]
            for fk, f in e["faces"].items():
                uu = [f["uv"][k][0] for k in f["vertices"]]
                vv = [f["uv"][k][1] for k in f["vertices"]]
                x0, x1 = min(uu) * scale, max(uu) * scale
                y0, y1 = min(vv) * scale, max(vv) * scale
                for x in range(int(x0), min(W, int(x1))):
                    for yy in (int(y0), min(H - 1, int(y1))):
                        buf[yy * W + x] = col
                for y in range(int(y0), min(H, int(y1))):
                    for xx in (int(x0), min(W - 1, int(x1))):
                        buf[y * W + xx] = col
    P.write_png(out, W, H, buf)
    print(u"→ %s（%dx%d，每 16 像素一格，白色粗线是 64 像素）" % (out, W, H))


if __name__ == "__main__":
    main(sys.argv[1:])
