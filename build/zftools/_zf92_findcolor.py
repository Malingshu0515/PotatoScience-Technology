# -*- coding: utf-8 -*-
"""_zf92_findcolor.py —— 在贴图目录里按颜色找图（用来认"截图里那一小块用的是哪张图"）

用法:
    python _zf92_findcolor.py R G B [tol]     # 找含该颜色的贴图，列出文件名 + 该色在某张图里的坐标
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402

DIRS = [r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block",
        r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"]


def main(argv):
    r0, g0, b0 = (int(v) for v in argv[:3])
    tol = int(argv[3]) if len(argv) > 3 else 12
    for d in DIRS:
        for name in sorted(os.listdir(d)):
            if not name.endswith(".png"):
                continue
            path = os.path.join(d, name)
            try:
                w, h, _, px = P.read_png(path)
            except Exception as e:
                print(u"  !! %s 读不了: %s" % (name, e))
                continue
            hits = []
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[y * w + x]
                    if a and abs(r - r0) <= tol and abs(g - g0) <= tol and abs(b - b0) <= tol:
                        hits.append((x, y))
            if hits:
                print(u"%-34s %dx%d  命中 %4d  例: %s"
                      % (os.path.basename(d) + "/" + name, w, h, len(hits),
                         u" ".join(u"(%d,%d)#%02X%02X%02X" % (x, y, px[y * w + x][0], px[y * w + x][1], px[y * w + x][2])
                                   for x, y in hits[:6])))


if __name__ == "__main__":
    main(sys.argv[1:])
