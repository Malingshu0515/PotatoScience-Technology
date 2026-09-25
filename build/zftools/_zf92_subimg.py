# -*- coding: utf-8 -*-
r"""_zf92_subimg.py —— 在 A 图里找 B 图（整块或近似）出现的位置

用户提到"接线块"和"高炉贴图"可能有关联。最直接的判据：接线块那张 16x16 的图，
是不是就是从高炉贴图里抠出来的一块？整块找一遍就有答案。

用法:
    python _zf92_subimg.py <大图.png> <小图.png> [容差]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png as P  # noqa: E402


def main(argv):
    big, small = argv[0], argv[1]
    tol = int(argv[2]) if len(argv) > 2 else 0
    bw, bh, _, bp = P.read_png(big)
    sw, sh, _, sp = P.read_png(small)
    print(u"%s %dx%d  vs  %s %dx%d  容差 %d"
          % (os.path.basename(big), bw, bh, os.path.basename(small), sw, sh, tol))
    hits = 0
    for oy in range(bh - sh + 1):
        for ox in range(bw - sw + 1):
            bad = 0
            for y in range(sh):
                for x in range(sw):
                    a = bp[(oy + y) * bw + ox + x]
                    b = sp[y * sw + x]
                    if a[3] == 0 and b[3] == 0:
                        continue
                    if max(abs(a[i] - b[i]) for i in range(4)) > tol:
                        bad += 1
                        if bad > 0:
                            break
                if bad:
                    break
            if bad == 0:
                hits += 1
                print(u"  命中 (%d,%d)" % (ox, oy))
    if not hits:
        print(u"  没有整块命中")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
