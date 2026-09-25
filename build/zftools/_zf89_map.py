# -*- coding: utf-8 -*-
u"""_zf89_map.py —— 把 61 个岛与 114 个面摆在一起，找"这张图是不是本模型的展开图"

输出：
  ① 全部岛（按位置排序）；
  ② 全部 114 个面（按长方体分组，给出像素尺寸）；
  ③ 面积对账：不透明像素 vs 面面积之和（差值是不是"每岛 1px 出血"能解释的）。
只读。
"""
import os
import sys
from collections import Counter, deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png  # noqa: E402

TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"
OBJ = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.obj"


def islands():
    w, h, ctype, px = _zf66_png.read_png(TEX)
    seen = bytearray(w * h)
    out = []
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0 * w + x0] or px[y0 * w + x0][3] == 0:
                continue
            q = deque([(x0, y0)])
            seen[y0 * w + x0] = 1
            n = 0
            minx, miny, maxx, maxy = x0, y0, x0, y0
            while q:
                x, y = q.popleft()
                n += 1
                minx = min(minx, x); miny = min(miny, y)
                maxx = max(maxx, x); maxy = max(maxy, y)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] \
                            and px[ny * w + nx][3] != 0:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            out.append([minx, miny, maxx, maxy, n])
    return w, h, out


def faces():
    vs, quads = [], []
    for raw in open(OBJ, "r", encoding="utf-8", errors="replace"):
        t = raw.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "f":
            ids = [int(x.split("/")[0]) - 1 for x in t[1:]]
            quads.append([vs[i] for i in ids])
    return quads


w, h, isl = islands()
print(u"=== ① 全部 %d 个岛（按 y,x 排序）===" % len(isl))
for k, (x0, y0, x1, y1, n) in enumerate(sorted(isl, key=lambda t: (t[1], t[0])), 1):
    print(u"  #%02d (%3d,%3d)-(%3d,%3d)  %3dx%-3d  实心 %d" %
          (k, x0, y0, x1, y1, x1 - x0 + 1, y1 - y0 + 1, n))

quads = faces()
print(u"")
print(u"=== ② 114 个面（每 6 个一组 = 一个长方体）===")
flist = []
for i, q in enumerate(quads):
    xs = [p[0] for p in q]; ys = [p[1] for p in q]; zs = [p[2] for p in q]
    dims = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]
    nz = [d for d in dims if d > 1e-6]
    nz.sort()
    a, b = nz[0], nz[1]
    flist.append((round(a * 16), round(b * 16)))
    if i % 6 == 0:
        print(u"  --- 长方体 #%02d ---" % (i // 6 + 1))
    print(u"    面%03d  %3d x %-3d px" % (i + 1, flist[-1][0], flist[-1][1]))

opaque = sum(n for _, _, _, _, n in isl)
facearea = sum(a * b for a, b in flist)
print(u"")
print(u"=== ③ 面积对账 ===")
print(u"  不透明像素总数        = %d" % opaque)
print(u"  114 个面面积之和      = %d" % facearea)
print(u"  差（图比面多）        = %d" % (opaque - facearea))
print(u"  若每岛四周各画 1px 出血，需补 = %d"
      % sum(((x1 - x0 + 3) * (y1 - y0 + 3)) - n for x0, y0, x1, y1, n in isl))
print(u"")
print(u"  岛尺寸多重集（前 25）: %s"
      % Counter([(x1 - x0 + 1, y1 - y0 + 1) for x0, y0, x1, y1, n in isl]
                ).most_common(25))
print(u"  面尺寸多重集（前 25）: %s" % Counter(flist).most_common(25))
