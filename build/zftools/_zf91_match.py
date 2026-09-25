# -*- coding: utf-8 -*-
r"""_zf91_match.py —— 「用户导出的 UV 展开图」的 114 个矩形 vs「我们手里那份 OBJ」的 114 个面

判据（都是可复算的）：
  ① 数目：都必须是 114（展开图 114 块 = 模型 114 个面）；
  ② **尺寸多重集**必须完全相等 —— 每个面的像素尺寸（两个非零边长 ×16）应当一一对应；
  ③ 顺带把每块矩形的颜色列出来（Blockbench 按**长方体**上色 ⇒ 同色 = 同一个盒子，
     这是后面重建"哪个面用哪块"的关键线索）。
只读。
"""
import io
import os
import sys
from collections import Counter, deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

B = r"C:\Users\Administrator\.dsh\attachments\v1\objects\0d\0da6ba4523aa4e72b040c78bd0bc7581323722f9ae8b124c5c9b7d9734e25210"
OBJ = r"E:\PotatoST\src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.obj"


def comps(w, h, mask):
    seen = bytearray(w * h)
    out = []
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0 * w + x0] or not mask[y0 * w + x0]:
                continue
            q = deque([(x0, y0)])
            seen[y0 * w + x0] = 1
            minx, miny, maxx, maxy = x0, y0, x0, y0
            while q:
                x, y = q.popleft()
                minx = min(minx, x); miny = min(miny, y)
                maxx = max(maxx, x); maxy = max(maxy, y)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] \
                            and mask[ny * w + nx]:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            out.append((minx, miny, maxx, maxy))
    return out


def layout():
    w, h, _, px = _zf66_png.read_png(B)
    mask = [p[3] != 0 and not (p[0] > 245 and p[1] > 245 and p[2] > 245) for p in px]
    res = []
    for (x0, y0, x1, y1) in comps(w, h, mask):
        cnt = {}
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if mask[y * w + x]:
                    c = px[y * w + x][:3]
                    cnt[c] = cnt.get(c, 0) + 1
        top = max(cnt.items(), key=lambda kv: kv[1])[0]
        res.append(((x0, y0, x1 - x0 + 1, y1 - y0 + 1), top))
    return res


def faces():
    vs, quads = [], []
    for raw in io.open(OBJ, encoding="utf-8", errors="replace"):
        t = raw.split()
        if not t:
            continue
        if t[0] == "v":
            vs.append(tuple(float(x) for x in t[1:4]))
        elif t[0] == "f":
            quads.append([vs[int(a.split("/")[0]) - 1] for a in t[1:]])
    out = []
    for i, q in enumerate(quads):
        xs = [p[0] for p in q]; ys = [p[1] for p in q]; zs = [p[2] for p in q]
        dims = sorted(d for d in (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
                      if d > 1e-6)
        out.append((i, round(dims[0] * 16), round(dims[1] * 16)))
    return out


lay = layout()
print(u"展开图矩形 = %d 个" % len(lay))
fs = faces()
print(u"OBJ 的面    = %d 个" % len(fs))

lay_ms = Counter((r[2], r[3]) for r, _ in lay)
obj_ms = Counter((a, b) for _, a, b in fs)
print(u"\n== 尺寸多重集 ==")
keys = sorted(set(lay_ms) | set(obj_ms), key=lambda t: (-t[0] * t[1], t))
same = True
for k in keys:
    l, o = lay_ms.get(k, 0), obj_ms.get(k, 0)
    flag = u"" if l == o else u"   <<< 不一致"
    if l != o:
        same = False
    print(u"  %3d x %-3d   展开图 %2d   模型 %2d%s" % (k[0], k[1], l, o, flag))
print(u"\n尺寸多重集完全相等 = %s" % (u"是" if same else u"否"))

print(u"\n== 展开图每块的颜色分布（同色 = 同一个长方体）==")
byc = {}
for sz, c in lay:
    byc.setdefault(c, []).append(sz)
for c, lst in sorted(byc.items(), key=lambda kv: -len(kv[1])):
    print(u"  #%02X%02X%02X  %2d 块" % (c[0], c[1], c[2], len(lst)))
print(u"  颜色总数 = %d" % len(byc))

print(u"\n== 每个颜色的块尺寸（看出「一个盒子 6 个面」的分组规则）==")
for c, lst in sorted(byc.items(), key=lambda kv: -len(kv[1])):
    print(u"  #%02X%02X%02X: %s" % (c[0], c[1], c[2],
                                   u", ".join(u"%dx%d@(%d,%d)" % (s[2], s[3], s[0], s[1])
                                             for s in sorted(lst, key=lambda t: (t[1], t[0])))))
