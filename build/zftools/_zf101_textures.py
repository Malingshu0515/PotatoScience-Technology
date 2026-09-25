# -*- coding: utf-8 -*-
u"""_zf101_textures.py —— ZF101 的 8 张占位贴图（程序生成，16×16，本工程自己的图）

  · `acidic_reaction_chamber_side.png` / `_top.png` —— 酸性反应室（灰钢壳 + 一排玻璃视窗）
  · `carbonic_acid_still.png` / `_flow.png`       —— 碳酸（淡青白）
  · `nitric_acid_still.png` / `_flow.png`         —— 硝酸（淡黄）
  · `sulfuric_acid_still.png` / `_flow.png`       —— 硫酸（琥珀，最"油"）

⚠ 六张流体贴图的 still 与 flow **逐字节相同** —— 这是本工程的老规矩
   （ZF100 的二氧化碳是唯一例外，那张画了单独的流动版）。这里**跟老规矩**，不搞第二个例外。

用法：
    python build/zftools/_zf101_textures.py            # 只打印，不写
    python build/zftools/_zf101_textures.py --write    # 真写
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png   # noqa: E402  （本工程自己的 PNG 读写工具）

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"

SHELL = (78, 80, 86, 255)
SHELL_D = (54, 56, 61, 255)
RIVET = (108, 110, 116, 255)
GLASS = (150, 196, 172, 255)      # 视窗玻璃（淡青绿）
GLASS_D = (104, 152, 128, 255)
ACID = (168, 214, 96, 255)        # 视窗里的酸液（黄绿）
PIPE = (120, 122, 128, 255)

CARBONIC = (206, 226, 224, 255)   # 碳酸：淡青白
CARBONIC_D = (172, 198, 198, 255)
CARBONIC_L = (232, 244, 242, 255)
NITRIC = (228, 216, 148, 255)     # 硝酸：淡黄
NITRIC_D = (196, 182, 112, 255)
NITRIC_L = (244, 236, 190, 255)
SULFURIC = (214, 176, 96, 255)    # 硫酸：琥珀
SULFURIC_D = (176, 138, 66, 255)
SULFURIC_L = (238, 208, 140, 255)


def blank(color=(0, 0, 0, 0)):
    return [[color for _ in range(16)] for _ in range(16)]


def px(g, x, y, color):
    g[y][x] = color


def rect(g, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(g, x, y, color)


def flatten(g):
    out = bytearray()
    for row in g:
        for (r, gg, b, a) in row:
            out += bytes((r, gg, b, a))
    return bytes(out)


def side_texture():
    u"""侧面：灰钢壳 + 两个竖向玻璃视窗（里面是酸液）+ 两根进出料管 + 铆钉。"""
    g = blank(SHELL)
    for i in range(0, 16, 4):
        for k in range(16):
            px(g, i, k, SHELL_D)
            px(g, k, i, SHELL_D)
    # 两个视窗
    for x0 in (3, 9):
        rect(g, x0, 5, x0 + 3, 11, GLASS)
        rect(g, x0, 8, x0 + 3, 11, ACID)      # 下半截是酸
        rect(g, x0, 5, x0 + 3, 5, GLASS_D)
        rect(g, x0, 11, x0 + 3, 11, GLASS_D)
    # 进出料管（顶面进来的两根）
    rect(g, 6, 0, 6, 3, PIPE)
    rect(g, 13, 0, 13, 3, PIPE)
    for (x, y) in ((1, 1), (14, 14), (1, 14), (14, 1)):
        px(g, x, y, RIVET)
    return g


def top_texture():
    u"""顶面：灰钢壳 + 中间一个圆形投料口（里面一点酸色）+ 四角铆钉。"""
    g = blank(SHELL)
    for i in range(0, 16, 4):
        for k in range(16):
            px(g, i, k, SHELL_D)
            px(g, k, i, SHELL_D)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 8, y - 8
            d2 = dx * dx + dy * dy
            if d2 <= 16:
                px(g, x, y, GLASS_D)
            elif d2 <= 25:
                px(g, x, y, PIPE)
    rect(g, 6, 7, 9, 8, ACID)
    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px(g, x, y, RIVET)
    return g


def acid_texture(base, dark, light):
    u"""一种酸的贴图：底色 + 细波纹（still 与 flow 逐字节相同 —— 本工程老规矩）。"""
    g = blank(base)
    for y in range(16):
        for x in range(16):
            v = (x * 3 + y * 5) % 9
            if v == 0:
                px(g, x, y, light)
            elif v in (4, 5):
                px(g, x, y, dark)
    for y in (4, 9, 14):
        for x in range(16):
            if (x + y) % 3:
                px(g, x, y, dark)
    return g


def same_pair(base, dark, light):
    u"""返回同一个生成函数的两次调用结果（写盘后两张逐字节相同）。"""
    return lambda: acid_texture(base, dark, light)


FILES = [
    ("acidic_reaction_chamber_side.png", side_texture),
    ("acidic_reaction_chamber_top.png", top_texture),
    ("carbonic_acid_still.png", same_pair(CARBONIC, CARBONIC_D, CARBONIC_L)),
    ("carbonic_acid_flow.png", same_pair(CARBONIC, CARBONIC_D, CARBONIC_L)),
    ("nitric_acid_still.png", same_pair(NITRIC, NITRIC_D, NITRIC_L)),
    ("nitric_acid_flow.png", same_pair(NITRIC, NITRIC_D, NITRIC_L)),
    ("sulfuric_acid_still.png", same_pair(SULFURIC, SULFURIC_D, SULFURIC_L)),
    ("sulfuric_acid_flow.png", same_pair(SULFURIC, SULFURIC_D, SULFURIC_L)),
]


def main():
    write = "--write" in sys.argv
    print(u"目标目录：%s" % OUT)
    for name, maker in FILES:
        path = os.path.join(OUT, name)
        old = os.path.getsize(path) if os.path.exists(path) else -1
        g = maker()
        if write:
            write_png(path, 16, 16, flatten(g))
            print(u"  [写出] %-34s 16×16  %d B" % (name, os.path.getsize(path)))
        else:
            print(u"  [只看] %-34s 16×16  （磁盘上原有 %d B）" % (name, old))
    if not write:
        print(u"\n（没写任何字节；加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
