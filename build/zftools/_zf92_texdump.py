# -*- coding: utf-8 -*-
"""_zf92_texdump.py —— 把 16x16 方块贴图打成字符网格，用来跟游戏截图里的像素对认。

屏幕上一个方块面大约 250~400 px，每个 texel 约 16~25 px，肉眼能直接数格子；
把贴图打成同尺寸的字符网格就能一眼认出"这一面用的是哪张图"。

用法:
    python _zf92_texdump.py <file.png> [...]        # 一张图一种字符
字符表按亮度分档: 空格=透明 . =极暗 : =暗 - =中 + =亮 * =很亮 # =白
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf66_png as P

RAMP = u" .:-=+*#%@"


def dump(path, crop=None):
    w, h, ctype, px = P.read_png(path)
    name = os.path.basename(path)
    print(u"\n=== %s  %dx%d  colorType=%d" % (name, w, h, ctype))
    x0, y0, cw, ch = crop if crop else (0, 0, w, h)
    ch = min(ch, h - y0)
    cw = min(cw, w - x0)
    for y in range(y0, y0 + ch):
        row = []
        for x in range(x0, x0 + cw):
            r, g, b, a = px[y * w + x]
            if a == 0:
                row.append(u" ")
                continue
            lum = (r * 299 + g * 587 + b * 114) // 1000
            idx = 1 + (lum * (len(RAMP) - 2)) // 255
            row.append(RAMP[idx])
        print(u"%3d |%s|" % (y, u"".join(row)))
    # 附一张 16 进制色卡（只列前若干种颜色）
    cnt = {}
    for p in px:
        if p[3]:
            cnt[p[:3]] = cnt.get(p[:3], 0) + 1
    top = sorted(cnt.items(), key=lambda kv: -kv[1])[:8]
    print(u"    主色: " + u"  ".join(u"#%02X%02X%02X×%d" % (c[0], c[1], c[2], n) for c, n in top))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    for p in argv:
        dump(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
