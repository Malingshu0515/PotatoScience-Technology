# -*- coding: utf-8 -*-
"""ZF38：低级发电机的方块贴图（程序生成，16×16）。

**这是占位美术**（本项目除唱片外所有贴图都是程序生成的，见档案 §9），
你可以随时用 Blockbench 画一版替换掉，文件名不变即可。

设计：一台"廉价炉式发电机"——深色炉膛 + 底部琥珀色炉火格栅 + 顶部排气口。
配色沿用本项目机器家族的同一套金属灰（`hydraulic_press` / `salt_decomposer` 同款），
**强调色取琥珀黄（H≈42）**，与液压机的橙（H≈28）、盐分解构器的暗红（H≈14）、
它的青白溶液槽（H≈196）都拉开，避免几台机器在背包里看着像同一台。
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

FIREBOX = (28, 28, 32, 255)
EMBER_D = (168, 92, 18, 255)
EMBER = (232, 152, 42, 255)
EMBER_L = (252, 208, 104, 255)
VENT = (36, 36, 40, 255)


def blank():
    return [(0, 0, 0, 0)] * 256


def put(px, x, y, c):
    px[y * 16 + x] = c


def metal_body(px):
    """四台机器共用的"钢壳"底：填充 + 左上亮边 / 右下暗边。"""
    for y in range(16):
        for x in range(16):
            put(px, x, y, FRAME)
    for x in range(16):
        put(px, x, 0, FRAME_L)
        put(px, x, 15, FRAME_D)
    for y in range(16):
        put(px, 0, y, FRAME_L)
        put(px, 15, y, FRAME_D)


def side_texture():
    px = blank()
    metal_body(px)

    # 炉膛：中央凹陷的深色方口
    for y in range(4, 13):
        for x in range(3, 13):
            put(px, x, y, FIREBOX)
    for x in range(3, 13):
        put(px, x, 3, FRAME_L)      # 上沿受光
        put(px, x, 13, FRAME_D)     # 下沿背光
    for y in range(4, 13):
        put(px, 3, y, FRAME_L)
        put(px, 12, y, FRAME_D)

    # 炉膛上部的进气缝（三道横缝）
    for y in (5, 7, 9):
        for x in range(5, 11):
            put(px, x, y, VENT)

    # 底部炉火格栅：琥珀色，越靠下越亮（火在炉底）
    for x in range(4, 12):
        put(px, x, 11, EMBER)
    for x in range(4, 12):
        put(px, x, 12, EMBER_D)
    for x in (5, 7, 9, 11):
        put(px, x, 11, EMBER_L)
    put(px, 4, 11, EMBER_D)
    put(px, 11, 11, EMBER_D)

    # 侧面散热片（右侧一列竖纹）
    for y in range(5, 12):
        put(px, 14, y, FRAME_D)

    # 四角螺栓
    for (bx, by) in ((1, 1), (14, 1), (1, 14)):
        put(px, bx, by, BOLT)
    put(px, 2, 1, BOLT_D)
    put(px, 13, 14, BOLT_D)
    return px


def top_texture():
    px = blank()
    metal_body(px)

    # 中央排气口：圆形深孔 + 一圈受光边
    hole = [(6, 4), (7, 4), (8, 4), (9, 4),
            (4, 6), (5, 5), (10, 5), (11, 6),
            (4, 9), (5, 10), (10, 10), (11, 9),
            (6, 11), (7, 11), (8, 11), (9, 11)]
    for (x, y) in hole:
        put(px, x, y, VENT)
    for y in range(5, 11):
        for x in range(5, 11):
            put(px, x, y, FIREBOX)
    for x in range(5, 11):
        put(px, x, 5, VENT)
    # 排气口中心一点余温
    put(px, 7, 7, EMBER_D)
    put(px, 8, 8, EMBER_D)

    # 排气口外圈：一圈钢边
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


for name, px in (("low_generator_side.png", side_texture()),
                 ("low_generator_top.png", top_texture())):
    flat = bytearray()
    for c in px:
        flat += bytes(c)
    path = os.path.join(OUT, name)
    write_png(path, 16, 16, flat)
    print("%-28s 16x16  %d 字节" % (name, os.path.getsize(path)))
