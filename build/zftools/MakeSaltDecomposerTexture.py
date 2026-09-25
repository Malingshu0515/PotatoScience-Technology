# -*- coding: utf-8 -*-
"""ZF32：盐分解构器的方块贴图（程序生成，16×16）。

设计：一台"分解槽"——顶部投料口、中部溶液槽（青白色 = 盐/卤水）、右侧一根加热柱。
与液压机（橙色液压缸）在色相上拉开距离，避免两台机器在背包里看着像同一台。
"""
import os
import sys

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import write_png

OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"

FRAME_D = (52, 54, 58, 255)
FRAME = (84, 86, 92, 255)
FRAME_L = (122, 124, 132, 255)
BOLT = (172, 174, 182, 255)
BOLT_D = (66, 68, 74, 255)
TANK = (206, 226, 232, 255)      # 卤水/盐溶液：淡青白
TANK_D = (150, 176, 186, 255)
TANK_L = (240, 250, 252, 255)
COIL = (196, 92, 60, 255)        # 加热柱：暗红
COIL_L = (232, 132, 92, 255)
PIPE = (108, 110, 118, 255)


def blank():
    return [(0, 0, 0, 0)] * 256


def put(px, x, y, c):
    px[y * 16 + x] = c


def side_texture():
    px = blank()
    for y in range(16):
        for x in range(16):
            put(px, x, y, FRAME)
    for x in range(16):
        put(px, x, 0, FRAME_L)
        put(px, x, 15, FRAME_D)
    for y in range(16):
        put(px, 0, y, FRAME_L)
        put(px, 15, y, FRAME_D)
    # 顶部投料斗
    for x in range(4, 12):
        put(px, x, 2, FRAME_D)
    for x in range(5, 11):
        put(px, x, 3, (30, 30, 34, 255))
    # 中部溶液槽（淡青白）
    for y in range(6, 12):
        for x in range(4, 12):
            put(px, x, y, TANK)
    for x in range(4, 12):
        put(px, x, 6, TANK_L)
        put(px, x, 11, TANK_D)
    for y in range(6, 12):
        put(px, 4, y, TANK_L)
        put(px, 11, y, TANK_D)
    # 槽内液面细节
    for x in range(6, 10):
        put(px, x, 8, TANK_D)
    # 右侧加热柱
    for y in range(4, 13):
        put(px, 13, y, COIL)
    put(px, 13, 4, COIL_L)
    # 底部管道 + 螺栓
    for x in range(3, 13):
        put(px, x, 13, PIPE)
    for (bx, by) in ((1, 1), (14, 14), (1, 14)):
        put(px, bx, by, BOLT)
    put(px, 2, 1, BOLT_D)
    put(px, 13, 14, BOLT_D)
    return px


def top_texture():
    px = blank()
    for y in range(16):
        for x in range(16):
            put(px, x, y, FRAME)
    for x in range(16):
        put(px, x, 0, FRAME_L)
        put(px, x, 15, FRAME_D)
    for y in range(16):
        put(px, 0, y, FRAME_L)
        put(px, 15, y, FRAME_D)
    # 中央投料口：深色方孔 + 亮边
    for y in range(5, 11):
        for x in range(5, 11):
            put(px, x, y, (28, 28, 32, 255))
    for x in range(4, 12):
        put(px, x, 4, FRAME_L)
        put(px, x, 11, FRAME_D)
    for y in range(4, 12):
        put(px, 4, y, FRAME_L)
        put(px, 11, y, FRAME_D)
    # 四角螺栓
    for (bx, by) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        put(px, bx, by, BOLT)
        put(px, bx + 1, by, BOLT_D)
    return px


for name, px in (("salt_decomposer_side.png", side_texture()),
                 ("salt_decomposer_top.png", top_texture())):
    flat = bytearray()
    for c in px:
        flat += bytes(c)
    path = os.path.join(OUT, name)
    write_png(path, 16, 16, flat)
    print("%-30s 16x16  %d 字节" % (name, os.path.getsize(path)))
