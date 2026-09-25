# -*- coding: utf-8 -*-
r"""_zf92_montage.py —— 把几张等大 PNG 拼成一张（横排/竖排/网格），省得一张张看

用法:
    python _zf92_montage.py <out.png> <列数> <a.png> <b.png> ...
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402


def main(argv):
    out = argv[0]
    cols = int(argv[1])
    srcs = argv[2:]
    imgs = [P.read_png(p) for p in srcs]
    cw = max(i[0] for i in imgs)
    ch = max(i[1] for i in imgs)
    rows = (len(imgs) + cols - 1) // cols
    W, H = cw * cols, ch * rows
    buf = [(16, 16, 20, 255)] * (W * H)
    for n, (w, h, _ct, px) in enumerate(imgs):
        ox, oy = (n % cols) * cw, (n // cols) * ch
        for y in range(h):
            for x in range(w):
                buf[(oy + y) * W + ox + x] = px[y * w + x]
    P.write_png(out, W, H, buf)
    print(u"→ %s %dx%d（%d 张，%d 列）" % (out, W, H, len(imgs), cols))


if __name__ == "__main__":
    main(sys.argv[1:])
