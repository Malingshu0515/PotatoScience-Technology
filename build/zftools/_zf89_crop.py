# -*- coding: utf-8 -*-
u"""_zf89_crop.py —— 把任意 PNG 裁一块 + NEAREST 放大，用来细看用户截图

用法: python _zf89_crop.py <in.png> <x0> <y0> <x1> <y1> <scale> <out.png>
只读入参，只写 out。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png  # noqa: E402


def main(argv):
    src, x0, y0, x1, y1, scale, dst = (argv[1], int(argv[2]), int(argv[3]),
                                       int(argv[4]), int(argv[5]), int(argv[6]),
                                       argv[7])
    w, h, ctype, px = _zf66_png.read_png(src)
    if x1 > w:
        x1 = w
    if y1 > h:
        y1 = h
    ow, oh = (x1 - x0) * scale, (y1 - y0) * scale
    out = []
    for y in range(oh):
        sy = y0 + y // scale
        for x in range(ow):
            sx = x0 + x // scale
            r, g, b, a = px[sy * w + sx]
            out.append((r, g, b, a))
    _zf66_png.write_png(dst, ow, oh, out)
    print(u"%s -> %s  (%d,%d)-(%d,%d) x%d = %dx%d" %
          (os.path.basename(src), os.path.basename(dst), x0, y0, x1, y1, scale,
           ow, oh))


main(sys.argv)
