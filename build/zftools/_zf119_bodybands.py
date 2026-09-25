# -*- coding: utf-8 -*-
r"""_zf119_bodybands.py —— 只读：按**本体**（去掉闪光）找 10 个锭的行段

上一版我用"有不透明像素的行"分帧 ⇒ 闪光跑到本体上方时会把窗口抬高一截
（第 10 帧就这样：闪光在 253..258、本体其实在 256..279）。
这里改成**只看本体**（低饱和像素）分行，看看是不是干净利落的 10 段 × 24 行。
"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

SRC = r"E:\PotatoST\build\用户素材\振金锭.png"
OUT = r"E:\PotatoST\build\zftools\_zf119_bodybands.txt"
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


def main():
    w, h, buf = read_png(SRC)
    rows = [[buf[(y * w + x) * 4:(y * w + x) * 4 + 4] for x in range(w)] for y in range(h)]
    body = [sum(1 for px in row if px[3] > 0 and not is_shine(px)) for row in rows]
    shine = [sum(1 for px in row if is_shine(px)) for row in rows]
    say(u"源 %d×%d" % (w, h))
    say(u"")
    say(u"| 行 | 本体像素 | 闪光像素 |")
    say(u"|---|---|---|")
    for y in range(h):
        if body[y] or shine[y]:
            say(u"| %d | %d | %d |" % (y, body[y], shine[y]))
    # 本体行段
    bands, cur = [], None
    for y in range(h):
        if body[y] > 0 and cur is None:
            cur = y
        elif body[y] == 0 and cur is not None:
            bands.append((cur, y - 1))
            cur = None
    if cur is not None:
        bands.append((cur, h - 1))
    say(u"")
    say(u"本体行段（%d 段）：%s" % (len(bands), bands))
    say(u"段高：%s" % [b - a + 1 for a, b in bands])
    say(u"")
    # 每段前后 4 行里有没有闪光（判断 32 行帧装不装得下）
    for k, (a, b) in enumerate(bands):
        up = sum(shine[max(0, a - 4):a])
        dn = sum(shine[b + 1:b + 5])
        say(u"帧 %d：本体 %d..%d ｜ 本体上方 4 行里的闪光 %d 像素 ｜ 下方 4 行里 %d 像素"
            % (k, a, b, up, dn))
    io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"报告 → %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
