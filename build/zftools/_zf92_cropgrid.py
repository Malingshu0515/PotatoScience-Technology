# -*- coding: utf-8 -*-
r"""_zf92_cropgrid.py —— 裁一块放大并叠上"原图坐标"网格，用来读出角点像素坐标

用途：要把截图里某个面抠成 16x16 跟贴图比对，先得知道那个面的四个角在原图上的像素坐标。
     网格每 20 原图像素一条细线，每 100 像素一条亮线。

用法:
    python _zf92_cropgrid.py <in.png> <out.png> <x> <y> <w> <h> [scale]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402


def main(argv):
    src, dst = argv[0], argv[1]
    x0, y0, cw, ch = (int(v) for v in argv[2:6])
    scale = int(argv[6]) if len(argv) > 6 else 3
    w, h, _, px = P.read_png(src)
    W, H = cw * scale, ch * scale
    out = []
    for oy in range(H):
        sy = y0 + oy // scale
        for ox in range(W):
            sx = x0 + ox // scale
            out.append(px[sy * w + sx] if (0 <= sx < w and 0 <= sy < h) else (255, 0, 255, 255))
    # 叠网格（按原图坐标对齐）
    for gy in range((y0 // 20) * 20, y0 + ch + 1, 20):
        oy = (gy - y0) * scale
        if 0 <= oy < H:
            big = (gy % 100 == 0)
            for ox in range(W):
                if big or ox % 2 == 0:
                    out[oy * W + ox] = (0, 255, 0, 255) if big else (0, 140, 0, 255)
    for gx in range((x0 // 20) * 20, x0 + cw + 1, 20):
        ox = (gx - x0) * scale
        if 0 <= ox < W:
            big = (gx % 100 == 0)
            for oy in range(H):
                if big or oy % 2 == 0:
                    out[oy * W + ox] = (0, 255, 0, 255) if big else (0, 140, 0, 255)
    P.write_png(dst, W, H, out)
    print(u"→ %s  (%d,%d)+%dx%d ×%d；亮绿线 = 原图坐标 100 的倍数，暗绿 = 20 的倍数"
          % (dst, x0, y0, cw, ch, scale))


if __name__ == "__main__":
    main(sys.argv[1:])
