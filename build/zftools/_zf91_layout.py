# -*- coding: utf-8 -*-
r"""_zf91_layout.py —— 比对用户给的两张图：①旧的成品贴图 ②Blockbench 现在导出的 UV 展开图

回答的问题：
  · ②里的矩形（= 现在模型的面在贴图上的位置）与 ①里**画到的岛**（= 这张贴图当初是照着哪套 UV 画的）
    在**位置和尺寸**上对不对得上？对不上的具体是哪些？
  · 顺便数一数：②里有多少块矩形、①里有多少个岛 —— 数目本身就是信息。
只读，不改任何东西。
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
LIVE = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png"


def components(w, h, mask):
    seen = bytearray(w * h)
    out = []
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0 * w + x0] or not mask[y0 * w + x0]:
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
                            and mask[ny * w + nx]:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            out.append((minx, miny, maxx, maxy, n))
    return out


def islands_of(path, is_layout):
    w, h, ctype, px = _zf66_png.read_png(path)
    print(u"  %s：%dx%d ctype %s" % (os.path.basename(path), w, h, ctype))
    # 两张图都是 RGBA、背景全透明（`0da6ba45…` 有 33888 个 alpha=0 的像素）
    # ⇒ 判据统一用 **alpha**；不透明的近白像素当空（有的导出图会把底填白）
    mask = [p[3] != 0 and not (p[0] > 245 and p[1] > 245 and p[2] > 245) for p in px]
    comps = components(w, h, mask)
    # 每块的"主色"（面积最大的那个颜色）
    res = []
    for x0, y0, x1, y1, n in comps:
        cnt = {}
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if mask[y * w + x]:
                    c = px[y * w + x][:3]
                    cnt[c] = cnt.get(c, 0) + 1
        top = max(cnt.items(), key=lambda kv: kv[1])[0] if cnt else (0, 0, 0)
        res.append((x0, y0, x1, y1, n, top))
    return w, h, res, mask


def main():
    print(u"== ① 旧贴图（= 现在在用的那张）==")
    wa, ha, ia, ma = islands_of(A, False)
    print(u"  不透明岛：%d 个" % len(ia))
    print(u"  在用的那张与它是否同一份：%s"
          % (u"是" if open(A, "rb").read() == open(LIVE, "rb").read() else u"否"))
    print(u"\n== ② 现在导出的 UV 展开图 ==")
    wb, hb, ib, mb = islands_of(B, True)
    print(u"  矩形块：%d 个" % len(ib))

    print(u"\n== ③ 位置/尺寸对账 ==")
    seta = {}
    for x0, y0, x1, y1, n, c in ia:
        seta.setdefault((x0, y0, x1 - x0 + 1, y1 - y0 + 1), []).append(c)
    setb = {}
    for x0, y0, x1, y1, n, c in ib:
        setb.setdefault((x0, y0, x1 - x0 + 1, y1 - y0 + 1), []).append(c)
    only_a = sorted(k for k in seta if k not in setb)
    only_b = sorted(k for k in setb if k not in seta)
    both = sorted(k for k in seta if k in setb)
    print(u"  两边完全一致（位置+尺寸）的矩形：%d 个" % len(both))
    print(u"  只在①（旧贴图画到的位置）：%d 个" % len(only_a))
    for k in only_a[:14]:
        print(u"     %s" % (k,))
    print(u"  只在②（现在 UV 用的位置）：%d 个" % len(only_b))
    for k in only_b[:14]:
        print(u"     %s" % (k,))

    print(u"\n== ④ ②的全部矩形（按位置排序）==")
    for x0, y0, x1, y1, n, c in sorted(ib, key=lambda t: (t[1], t[0])):
        print(u"  (%3d,%3d)-(%3d,%3d)  %3dx%-3d  实心 %4d  主色 #%02X%02X%02X"
              % (x0, y0, x1, y1, x1 - x0 + 1, y1 - y0 + 1, n, c[0], c[1], c[2]))
    print(u"\n== ⑤ ①的全部岛（按位置排序）==")
    for x0, y0, x1, y1, n, c in sorted(ia, key=lambda t: (t[1], t[0])):
        print(u"  (%3d,%3d)-(%3d,%3d)  %3dx%-3d  实心 %4d  主色 #%02X%02X%02X"
              % (x0, y0, x1, y1, x1 - x0 + 1, y1 - y0 + 1, n, c[0], c[1], c[2]))


main()
