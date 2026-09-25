# -*- coding: utf-8 -*-
r"""_zf91_check_rects.py —— 交叉核对：`.bbmodel` 里的 UV 矩形 vs「展开图」里的矩形，各自的透明像素数

两边的矩形据我所知只差 1 像素约定（工程里 max 是**开区间**，图里画到 max−1）。
但"压到透明像素"的数目必须一致 —— 不一致就说明有一边读错了，得当场查清。
只读。
"""
import io
import json
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
BB = r"C:\Users\Administrator\.dsh\attachments\v1\files\15\15028bf3d0dc6e7234ea03ec6a697b72858bc12ff7383c401b7c394fd2aab366\电力高炉.bbmodel"
IMG2 = r"C:\Users\Administrator\.dsh\attachments\v1\objects\0d\0da6ba4523aa4e72b040c78bd0bc7581323722f9ae8b124c5c9b7d9734e25210"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"

w, h, ct, tex = _zf66_png.read_png(TEX)


def trans(x0, y0, x1, y1):
    u"""闭区间 [x0,x1]×[y0,y1] 里的透明像素数（越界算坏）"""
    t = n = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            n += 1
            if not (0 <= x < w and 0 <= y < h) or tex[y * w + x][3] == 0:
                t += 1
    return t, n


d = json.loads(io.open(BB, encoding="utf-8").read())
eng = set()
for e in d.get("elements", []):
    for fid, fc in e.get("faces", {}).items():
        uvd = fc.get("uv", {})
        us = [uvd[k][0] for k in fc.get("vertices", []) if k in uvd]
        vs = [uvd[k][1] for k in fc.get("vertices", []) if k in uvd]
        if us:
            eng.add((int(min(us)), int(min(vs)), int(max(us)), int(max(vs))))
print(u"工程里的 UV 矩形：%d 个" % len(eng))

# 展开图里的矩形
w2, h2, _, p2 = _zf66_png.read_png(IMG2)
mask = [p[3] != 0 and not (p[0] > 245 and p[1] > 245 and p[2] > 245) for p in p2]
seen = bytearray(w2 * h2)
lay = set()
for y0 in range(h2):
    for x0 in range(w2):
        if seen[y0 * w2 + x0] or not mask[y0 * w2 + x0]:
            continue
        q = deque([(x0, y0)])
        seen[y0 * w2 + x0] = 1
        a = b = x0
        c = e2 = y0
        while q:
            x, y = q.popleft()
            a = min(a, x); b = max(b, x); c = min(c, y); e2 = max(e2, y)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w2 and 0 <= ny < h2 and not seen[ny * w2 + nx] and mask[ny * w2 + nx]:
                    seen[ny * w2 + nx] = 1
                    q.append((nx, ny))
        lay.add((a, c, b, e2))
print(u"展开图里的矩形：%d 个" % len(lay))

print(u"\n== 各自「压到透明像素」的统计（工程矩形按闭区间 [x0,x1−1]）==")
eng_bad = sorted([(trans(x0, y0, x1 - 1, y1 - 1), (x0, y0, x1, y1)) for (x0, y0, x1, y1) in eng],
                 key=lambda kv: -kv[0][0])
lay_bad = sorted([(trans(*r), r) for r in lay], key=lambda kv: -kv[0][0])
print(u"工程矩形里压到透明的：%d 个" % sum(1 for (t, n), _ in eng_bad if t))
for (t, n), r in eng_bad[:10]:
    if t:
        print(u"   %s  %d/%d" % (r, t, n))
print(u"展开图矩形里压到透明的：%d 个" % sum(1 for (t, n), _ in lay_bad if t))
for (t, n), r in lay_bad[:10]:
    if t:
        print(u"   %s  %d/%d" % (r, t, n))

print(u"\n== 工程矩形 − 展开图矩形（按 x0 排序，找 181 那一竖条）==")
e181 = sorted([r for r in eng if r[0] >= 176], key=lambda r: (r[0], r[1]))
l181 = sorted([r for r in lay if r[0] >= 176], key=lambda r: (r[0], r[1]))
print(u"  工程（x0≥176）：")
for r in e181:
    print(u"     %s  → 闭区间 (%d,%d)-(%d,%d)  透明 %d/%d"
          % (r, r[0], r[1], r[2] - 1, r[3] - 1, *trans(r[0], r[1], r[2] - 1, r[3] - 1)))
print(u"  展开图（x0≥176）：")
for r in l181:
    print(u"     %s  透明 %d/%d" % (r, *trans(*r)))
