# -*- coding: utf-8 -*-
r"""_zf91_overlay.py —— 把「现在导出的 UV 展开图」的 114 个矩形套回「旧贴图」上，逐块数透明像素

这是判"到底对不对得上"的**决定性一测**：
  · 每一块矩形在旧贴图里如果**全是不透明像素** ⇒ 那一块的面采样落到画好的地方，没问题；
  · 只要有一块压到透明像素 ⇒ 那处在游戏里就是**洞/紫黑**，必须报出来。
顺带出一张对照图：旧贴图打底，矩形边框逐块描出来（**绿=全对上、红=有透明像素**），
再看一眼块与块之间的 1px 缝是不是也对得上（缝里有没有画）。
只读入参，只往 build/zftools 写预览图。
"""
import io
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _zf66_png  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

A = r"C:\Users\Administrator\.dsh\attachments\v1\objects\24\24a0dfc0dcfe98a1c736773ec5d1cd1017107712da8c78951e873f61ff5214ee"
B = r"C:\Users\Administrator\.dsh\attachments\v1\objects\0d\0da6ba4523aa4e72b040c78bd0bc7581323722f9ae8b124c5c9b7d9734e25210"
OUT = os.path.join(HERE, "_zf91_overlay.png")


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


def main():
    wa, ha, _, pa = _zf66_png.read_png(A)
    wb, hb, _, pb = _zf66_png.read_png(B)
    mask_b = [p[3] != 0 and not (p[0] > 245 and p[1] > 245 and p[2] > 245) for p in pb]
    rects = comps(wb, hb, mask_b)
    print(u"UV 展开图里的矩形：%d 个" % len(rects))

    ok, bad = [], []
    for (x0, y0, x1, y1) in sorted(rects, key=lambda t: (t[1], t[0])):
        n = t = 0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                n += 1
                if pa[y * wa + x][3] == 0:
                    t += 1
        (bad if t else ok).append(((x0, y0, x1, y1), t, n))
    print(u"  [OK]   完全落在画好的地方（无透明像素）：%d 块" % len(ok))
    print(u"  [BAD]  压到透明像素的：%d 块" % len(bad))
    for (r, t, n) in bad:
        print(u"       (%3d,%3d)-(%3d,%3d)  %3dx%-3d  %d/%d 像素透明"
              % (r[0], r[1], r[2], r[3], r[2] - r[0] + 1, r[3] - r[1] + 1, t, n))

    # 覆盖面：画好的地方有多少没被任何矩形用到（= 白画了）
    used = bytearray(wa * ha)
    for (x0, y0, x1, y1) in rects:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                used[y * wa + x] = 1
    painted = sum(1 for p in pa if p[3] != 0)
    unused = sum(1 for i, p in enumerate(pa) if p[3] != 0 and not used[i])
    print(u"\n  贴图不透明像素 %d 个；没被任何矩形用到的 %d 个（%.1f%%）"
          % (painted, unused, 100.0 * unused / max(1, painted)))

    # 出对照图：旧贴图打底 + 矩形边框（绿=对上 / 红=有透明像素）
    # ⚠ 边框颜色必须是**四元组** —— 第一版写成三元组，`_zf66_png.write_png` 照单全收，
    #    写出一个每像素只有 3 字节的"PNG"，读图工具直接报 malformed（写图器没有校验，是它的弱点）。
    px = [(p[0], p[1], p[2], 255) if p[3] else (45, 45, 45, 255) for p in pa]
    for (x0, y0, x1, y1), t, n in [(r, 0, 0) for r in [b[0] for b in ok]] + \
            [(r, t, n) for r, t, n in bad]:
        col = (255, 40, 40, 255) if t else (40, 255, 40, 255)
        for x in range(x0, x1 + 1):
            px[y0 * wa + x] = col
            px[y1 * wa + x] = col
        for y in range(y0, y1 + 1):
            px[y * wa + x0] = col
            px[y * wa + x1] = col
    _zf66_png.write_png(OUT, wa, ha, px)
    print(u"\n  对照图写到 %s" % os.path.basename(OUT))


main()
