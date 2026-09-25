# -*- coding: utf-8 -*-
u"""_zf102_textures.py —— ZF102 的 2 张占位贴图：盐酸（still / flow，16×16，程序生成）

⚠ 跟本工程老规矩：still 与 flow **逐字节相同**（ZF100 的二氧化碳是唯一例外）。

用法：
    python build/zftools/_zf102_textures.py            # 只打印，不写
    python build/zftools/_zf102_textures.py --write    # 真写
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png   # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"

# 盐酸：淡黄绿（与碳酸的淡青白、硝酸的淡黄、硫酸的琥珀都区分得开）
BASE = (214, 226, 176, 255)
DARK = (176, 194, 130, 255)
LIGHT = (238, 246, 208, 255)


def blank(color):
    return [[color for _ in range(16)] for _ in range(16)]


def px(g, x, y, c):
    g[y][x] = c


def flatten(g):
    out = bytearray()
    for row in g:
        for (r, gg, b, a) in row:
            out += bytes((r, gg, b, a))
    return bytes(out)


def acid_texture():
    g = blank(BASE)
    for y in range(16):
        for x in range(16):
            v = (x * 3 + y * 5) % 9
            if v == 0:
                px(g, x, y, LIGHT)
            elif v in (4, 5):
                px(g, x, y, DARK)
    for y in (4, 9, 14):
        for x in range(16):
            if (x + y) % 3:
                px(g, x, y, DARK)
    return g


FILES = [("hydrochloric_acid_still.png", acid_texture),
         ("hydrochloric_acid_flow.png", acid_texture)]


def main():
    write = "--write" in sys.argv
    print(u"目标目录：%s" % OUT)
    for name, maker in FILES:
        path = os.path.join(OUT, name)
        old = os.path.getsize(path) if os.path.exists(path) else -1
        g = maker()
        if write:
            write_png(path, 16, 16, flatten(g))
            print(u"  [写出] %-32s 16×16  %d B" % (name, os.path.getsize(path)))
        else:
            print(u"  [只看] %-32s 16×16  （磁盘上原有 %d B）" % (name, old))
    if not write:
        print(u"\n（没写任何字节；加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
