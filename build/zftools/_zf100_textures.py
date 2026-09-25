# -*- coding: utf-8 -*-
u"""_zf100_textures.py —— ZF100 的 4 张占位贴图（程序生成，16×16，本工程自己的图）

  · `combustion_chamber_side.png` / `combustion_chamber_top.png` —— 燃烧反应室（深灰金属壳 + 黑色炉膛）
  · `carbon_dioxide_still.png` / `carbon_dioxide_flow.png` —— 二氧化碳（淡灰白雾，与氮气/氨气的色调区分开）

⚠ 这四张都是**占位图**（用户没给素材）：形状与配色是我按"深灰铁壳 + 黑炉口 + 一点火色"定的，
   要换直接给图；`TextureCheck.py` 会把它们算进"本工程自己生成的占位"，不进"借原版"那一档。

用法：
    python build/zftools/_zf100_textures.py            # 只打印，不写
    python build/zftools/_zf100_textures.py --write    # 真写
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png   # noqa: E402  （本工程自己的 PNG 读写工具）

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"

# 调色板（RGBA）
SHELL = (74, 76, 82, 255)        # 深灰铁壳
SHELL_D = (52, 54, 59, 255)      # 壳上的暗格线
RIVET = (104, 106, 112, 255)     # 铆钉
GRATE = (26, 24, 24, 255)        # 炉膛（黑）
GRATE_H = (44, 40, 38, 255)      # 炉膛里的横档
FIRE = (196, 96, 34, 255)        # 一点火色
FIRE_H = (232, 152, 52, 255)
CO2 = (206, 210, 214, 255)       # 二氧化碳：淡灰白
CO2_D = (176, 182, 188, 255)
CO2_L = (232, 236, 240, 255)


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
    u"""侧面：深灰铁壳 + 正中一块竖长黑炉膛 + 炉膛里两道火色横档 + 6 颗铆钉。"""
    g = blank(SHELL)
    # 壳上的暗格线（每 4 格一条，看得出是拼装的铁壳）
    for i in range(0, 16, 4):
        for k in range(16):
            px(g, i, k, SHELL_D)
            px(g, k, i, SHELL_D)
    # 炉膛：x 5..10 / y 4..12
    rect(g, 5, 4, 10, 12, GRATE)
    for y in (6, 9, 12):
        rect(g, 5, y, 10, y, GRATE_H)
    # 炉膛里的火色（不对称，免得像贴图接缝）
    rect(g, 6, 10, 9, 10, FIRE)
    rect(g, 7, 11, 8, 11, FIRE_H)
    # 铆钉：四角 + 腰部两侧
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14), (1, 7), (14, 7)):
        px(g, x, y, RIVET)
    return g


def top_texture():
    u"""顶面：深灰铁壳 + 中间一个圆形排气口（黑），外圈一圈火色。"""
    g = blank(SHELL)
    for i in range(0, 16, 4):
        for k in range(16):
            px(g, i, k, SHELL_D)
            px(g, k, i, SHELL_D)
    # 圆心 (8,8) 半径 5 的排气口
    for y in range(16):
        for x in range(16):
            dx, dy = x - 8, y - 8
            d2 = dx * dx + dy * dy
            if d2 <= 16:
                px(g, x, y, GRATE)
            elif d2 <= 25:
                px(g, x, y, FIRE)
    px(g, 8, 3, GRATE_H)
    px(g, 8, 13, GRATE_H)
    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        px(g, x, y, RIVET)
    return g


def gas_texture(flowing):
    u"""二氧化碳：淡灰白雾。静止版是均匀的雾，流动版加上斜向条纹（与其它气体同一套约定）。"""
    g = blank(CO2)
    for y in range(16):
        for x in range(16):
            v = (x * 5 + y * 3) % 7
            if v == 0:
                px(g, x, y, CO2_L)
            elif v in (3, 4):
                px(g, x, y, CO2_D)
    if flowing:
        for y in range(16):
            for x in range(16):
                if (x + y) % 5 == 0:
                    px(g, x, y, CO2_L)
                if (x - y) % 7 == 0:
                    px(g, x, y, CO2_D)
    return g


FILES = [
    ("combustion_chamber_side.png", side_texture),
    ("combustion_chamber_top.png", top_texture),
    ("carbon_dioxide_still.png", lambda: gas_texture(False)),
    ("carbon_dioxide_flow.png", lambda: gas_texture(True)),
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
            print(u"  [写出] %-30s 16×16  %d B" % (name, os.path.getsize(path)))
        else:
            print(u"  [只看] %-30s 16×16  （磁盘上原有 %d B）" % (name, old))
    if not write:
        print(u"\n（没写任何字节；加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
