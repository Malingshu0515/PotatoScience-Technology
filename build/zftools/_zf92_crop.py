# -*- coding: utf-8 -*-
"""_zf92_crop.py —— 从用户截图里裁一块放大存出来，用于肉眼比对贴图

本机没有 Pillow，只能用自己的 _zf66_png 读写。屏幕截图是 2560x1440。
用法:
    python _zf92_crop.py <in.png> <out.png> <x> <y> <w> <h> [scale] [--nearest|--box]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png as P


def crop(src, dst, x0, y0, cw, ch, scale, mode):
    w, h, ctype, px = P.read_png(src)
    ow, oh = cw * scale, ch * scale
    out = []
    for oy in range(oh):
        sy = y0 + oy // scale
        for ox in range(ow):
            sx = x0 + ox // scale
            if 0 <= sx < w and 0 <= sy < h:
                out.append(px[sy * w + sx])
            else:
                out.append((255, 0, 255, 255))
    P.write_png(dst, ow, oh, out)
    print(u"%s %dx%d 裁 (%d,%d)+%dx%d 放大 %dx -> %s %dx%d"
          % (os.path.basename(src), w, h, x0, y0, cw, ch, scale, os.path.basename(dst), ow, oh))


def main(argv):
    if len(argv) < 6:
        print(__doc__)
        return 2
    src, dst = argv[0], argv[1]
    x, y, cw, ch = (int(v) for v in argv[2:6])
    scale = int(argv[6]) if len(argv) > 6 and not argv[6].startswith("--") else 1
    crop(src, dst, x, y, cw, ch, scale, "nearest")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
