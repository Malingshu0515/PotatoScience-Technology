# -*- coding: utf-8 -*-
"""ZF30：液压机的方块贴图（程序生成，16×16，与项目其它机器同一套路）。

设计（侧视 = 一台立式压机）：
  · 外框：深灰机身 + 左上受光的立体边（沿用项目里机器贴图的明暗约定）
  · 中部：橙色液压缸体（横跨深色导轨之间）
  · 顶部：亮色压头，往下有一条活塞杆
  · 底部：底座 + 两侧螺栓
顶面单独一张：钢板 + 四角螺栓 + 中央圆孔（液压缸从上面穿下去）。
"""
import io
import os
import sys

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import write_png

OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"

FRAME_D = (58, 58, 62, 255)      # 机身暗部
FRAME = (88, 88, 94, 255)        # 机身
FRAME_L = (126, 126, 134, 255)   # 机身受光
BOLT = (176, 176, 184, 255)
BOLT_D = (70, 70, 76, 255)
RAIL = (34, 34, 38, 255)         # 导轨阴影
PISTON = (198, 198, 206, 255)    # 活塞杆
PISTON_D = (150, 150, 158, 255)
HEAD = (168, 168, 176, 255)      # 压头
CYL = (196, 106, 26, 255)        # 液压缸：橙
CYL_L = (231, 143, 52, 255)
CYL_D = (150, 74, 14, 255)


def blank():
    return [(0, 0, 0, 0)] * 256


def put(px, x, y, c):
    px[y * 16 + x] = c


def side_texture():
    px = blank()
    # 机身铺底
    for y in range(16):
        for x in range(16):
            put(px, x, y, FRAME)
    # 立体边：上/左受光，下/右压暗
    for x in range(16):
        put(px, x, 0, FRAME_L)
        put(px, x, 15, FRAME_D)
    for y in range(16):
        put(px, 0, y, FRAME_L)
        put(px, 15, y, FRAME_D)
    # 两侧立轨（深色）
    for y in range(2, 14):
        put(px, 3, y, RAIL)
        put(px, 12, y, RAIL)
    # 顶部横梁
    for x in range(2, 14):
        put(px, x, 2, FRAME_D)
    # 液压缸（橙色块，位于上部中央）
    for y in range(4, 7):
        for x in range(5, 11):
            put(px, x, y, CYL)
    for x in range(5, 11):
        put(px, x, 4, CYL_L)
        put(px, x, 6, CYL_D)
    # 活塞杆：从缸体往下
    for y in range(7, 11):
        put(px, 7, y, PISTON)
        put(px, 8, y, PISTON_D)
    # 压头（横跨导轨之间的亮块）
    for x in range(4, 12):
        put(px, x, 11, HEAD)
        put(px, x, 12, PISTON_D)
    # 底座
    for x in range(2, 14):
        put(px, x, 13, FRAME_D)
    # 四角螺栓
    for (bx, by) in ((1, 1), (14, 1), (1, 14), (14, 14)):
        put(px, bx, by, BOLT)
    for (bx, by) in ((2, 1), (14, 2), (1, 13), (13, 14)):
        put(px, bx, by, BOLT_D)
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
    # 中央圆孔：缸体从这里穿下去
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            d2 = dx * dx + dy * dy
            if d2 <= 6.5:
                put(px, x, y, CYL_D)
            elif d2 <= 12.5:
                put(px, x, y, CYL)
            elif d2 <= 16.5:
                put(px, x, y, CYL_L)
    for (bx, by) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        put(px, bx, by, BOLT)
        put(px, bx + 1, by, BOLT_D)
    return px


for name, px in (("hydraulic_press_side.png", side_texture()),
                 ("hydraulic_press_top.png", top_texture())):
    flat = bytearray()
    for c in px:
        flat += bytes(c)
    path = os.path.join(OUT, name)
    write_png(path, 16, 16, flat)
    opaque = sum(1 for c in px if c[3] > 0)
    print("%-28s 16x16  不透明=%3d  %d 字节" % (name, opaque, os.path.getsize(path)))
