# -*- coding: utf-8 -*-
u"""_zf89_islands.py —— 把 256×256 贴图上的"岛"数出来，与模型的面尺寸对照

要回答的问题：用户这张 256×256 到底是
  (甲) 给**这个模型**展开的 UV 图集（岛数 ≈ 面数 114、岛尺寸 ≈ 面的像素尺寸），还是
  (乙) 一张"整张铺满每个面"的方块贴图。
只读。
"""
import os
import sys
from collections import deque

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
                if x < minx: minx = x
                if y < miny: miny = y
                if x > maxx: maxx = x
                if y > maxy: maxy = y
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] \
                            and px[ny * w + nx][3] != 0:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            out.append((minx, miny, maxx, maxy, n))
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
    return vs, quads


w, h, isl = islands()
print(u"贴图 %dx%d   不透明连通域（岛）: %d 个" % (w, h, len(isl)))
big = sorted(isl, key=lambda t: -(t[2] - t[0] + 1) * (t[3] - t[1] + 1))
print(u"最大的 12 个岛 (x0,y0)-(x1,y1) 尺寸 像素数:")
for x0, y0, x1, y1, n in big[:12]:
    print(u"  (%3d,%3d)-(%3d,%3d)  %3dx%-3d  n=%d" %
          (x0, y0, x1, y1, x1 - x0 + 1, y1 - y0 + 1, n))
sizes = sorted(set((x1 - x0 + 1, y1 - y0 + 1) for x0, y0, x1, y1, n in isl))
print(u"岛尺寸种类 (%d): %s" % (len(sizes), sizes))

vs, quads = faces()
print(u"")
print(u"OBJ: v=%d 面=%d" % (len(vs), len(quads)))
fsz = {}
for q in quads:
    xs = [p[0] for p in q]; ys = [p[1] for p in q]; zs = [p[2] for p in q]
    dims = sorted([round(max(xs) - min(xs), 4), round(max(ys) - min(ys), 4),
                   round(max(zs) - min(zs), 4)])
    a, b = [d for d in dims if d > 1e-6][:2]
    fsz[(a, b)] = fsz.get((a, b), 0) + 1
print(u"面的世界尺寸（块单位，两个非零边长）-> 个数，并按 16 px/块 折算像素:")
for k in sorted(fsz, key=lambda t: (-t[0] * t[1], t)):
    print(u"  %5.3f x %5.3f  块  = %3d x %-3d px   x%d 个面"
          % (k[0], k[1], round(k[0] * 16), round(k[1] * 16), fsz[k]))

# 每个盒子（6 个连续面）的尺寸，便于看 19 个盒子
print(u"")
print(u"按每 6 个面一组（= 一个长方体）:")
for i in range(0, len(quads), 6):
    grp = quads[i:i + 6]
    xs = [p[0] for q in grp for p in q]
    ys = [p[1] for q in grp for p in q]
    zs = [p[2] for q in grp for p in q]
    print(u"  #%02d  X %6.3f..%-6.3f Y %6.3f..%-6.3f Z %6.3f..%-6.3f  = %d x %d x %d px"
          % (i // 6 + 1, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs),
             round((max(xs) - min(xs)) * 16), round((max(ys) - min(ys)) * 16),
             round((max(zs) - min(zs)) * 16)))
