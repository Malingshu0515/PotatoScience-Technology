# -*- coding: utf-8 -*-
r"""_zf119_align.py —— 只读分析：10 个锭的**本体**与**闪光**各在哪几行

用户实测反馈：「最后一帧会猛地向下弹一下 锭本体保持一致 不要以闪光为基准」
⇒ 我上一版是"整天 24 行窗口"照搬，如果最后那个锭在它自己那 24 行里本来就画得偏下，
   那一帧就会看起来往下弹一截。先把 10 帧**分开**量一遍：本体（灰白，低饱和）与
   闪光（黄色，高饱和）各自的包围盒，看差在哪。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

SRC = r"E:\PotatoST\build\用户素材\振金锭.png"
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item\vibranium_ingot.png"
OUT = r"E:\PotatoST\build\zftools\_zf119_align.txt"
CONTENT = 24
lines = []


def say(s):
    print(s)
    lines.append(s)


def is_shine(px):
    r, g, b, a = px
    if a == 0:
        return False
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) >= 60 and r >= 120 and g >= 100 and b <= 160


def starts_of(w, h, buf):
    rows = [[buf[(y * w + x) * 4:(y * w + x) * 4 + 4] for x in range(w)] for y in range(h)]
    counts = [sum(1 for px in row if px[3] > 0) for row in rows]
    out = []
    for y in range(h):
        prev = counts[y - 1] if y > 0 else 0
        if counts[y] > 0 and prev <= 8:
            if out and y - out[-1] < CONTENT:
                continue
            if any(counts[min(h - 1, y + k)] >= 28 for k in range(0, 20)):
                out.append(y)
    return out, rows, counts


def boxes(w, rows_win):
    u"""窗口里：本体 / 闪光的 bbox（行范围 + 列范围）"""
    body, shine = [], []
    for i, row in enumerate(rows_win):
        for x, px in enumerate(row):
            if px[3] == 0:
                continue
            (shine if is_shine(px) else body).append((i, x))
    def bb(pts):
        if not pts:
            return None
        rs = [p[0] for p in pts]
        cs = [p[1] for p in pts]
        return (min(rs), max(rs), min(cs), max(cs), len(pts))
    return bb(body), bb(shine)


def main():
    w, h, buf = read_png(SRC)
    starts, rows, counts = starts_of(w, h, buf)
    say(u"源：%d×%d，检出 %d 个锭" % (w, h, len(starts)))
    say(u"")
    say(u"## 源图里每一帧（24 行窗口）的本体 / 闪光包围盒")
    say(u"")
    say(u"| 帧 | 窗口 y | 本体 y（相对窗口） | 本体列 | 闪光 y（相对窗口） | 闪光列 |")
    say(u"|---|---|---|---|---|---|")
    body_tops, shine_tops = [], []
    for k, s in enumerate(starts):
        win = rows[s:s + CONTENT]
        b, sh = boxes(w, win)
        say(u"| %d | %d..%d | %s | %s | %s | %s |"
            % (k, s, s + CONTENT - 1,
               (u"%d..%d（%d 像素）" % (b[0], b[1], b[4])) if b else u"—",
               (u"%d..%d" % (b[2], b[3])) if b else u"—",
               (u"%d..%d（%d 像素）" % (sh[0], sh[1], sh[4])) if sh else u"—",
               (u"%d..%d" % (sh[2], sh[3])) if sh else u"—"))
        if b:
            body_tops.append(b[0])
        if sh:
            shine_tops.append(sh[0])
    say(u"")
    say(u"本体顶行（相对窗口）：%s" % body_tops)
    say(u"⇒ 最大值 - 最小值 = **%d 行**" % (max(body_tops) - min(body_tops)))
    say(u"闪光顶行（相对窗口）：%s" % shine_tops)
    say(u"⇒ 闪光位移范围 = %d 行（它本来就该动）" % (max(shine_tops) - min(shine_tops)))
    say(u"")
    say(u"## 现在盘上那份重排结果（每帧 32×32）里，本体的位置")
    w2, h2, buf2 = read_png(TEX)
    r2 = [[buf2[(y * w2 + x) * 4:(y * w2 + x) * 4 + 4] for x in range(w2)] for y in range(h2)]
    say(u"")
    say(u"| 帧 | 本体 y | 本体列 | 闪光 y |")
    say(u"|---|---|---|---|")
    tops2 = []
    for k in range(h2 // 32):
        win = r2[k * 32:(k + 1) * 32]
        b, sh = boxes(w2, win)
        say(u"| %d | %s | %s | %s |" % (k,
                                      (u"%d..%d" % (b[0], b[1])) if b else u"—",
                                      (u"%d..%d" % (b[2], b[3])) if b else u"—",
                                      (u"%d..%d" % (sh[0], sh[1])) if sh else u"—"))
        if b:
            tops2.append(b[0])
    say(u"")
    say(u"⇒ 盘上本体顶行：%s（%d 帧之间差 **%d 行** ← 用户看到的「最后一帧向下弹」就是这个）"
        % (tops2, len(tops2), max(tops2) - min(tops2)))
    io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"报告 → %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
