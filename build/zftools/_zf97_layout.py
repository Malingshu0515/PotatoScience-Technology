# -*- coding: utf-8 -*-
r"""_zf97_layout.py —— 把两台新机器的界面**版面**画成一张示意图（放大 3 倍），交付前肉眼复核。

不是渲染器：只按 Screen/Menu 里的常量画矩形（面板 / 槽位 / 储罐 / 能量条 / 状态灯 / 文字长度），
目的只有一个 —— **看有没有压在一起**（文字盖住储罐、状态灯压住槽位之类）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_zf97_layout.png")
S = 3                      # 放大倍数
BG = (198, 198, 198, 255)
BORDER = (85, 85, 85, 255)
SLOT = (139, 139, 139, 255)
TANK = (30, 30, 30, 255)
TANK_FLUID = (120, 180, 220, 255)
ENERGY = (60, 60, 60, 255)
LAMP = (224, 192, 64, 255)
LABEL = (46, 125, 50, 255)


class Canvas(object):
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray()
        for _ in range(w * h):
            self.px += bytes(BG)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                i = (y * self.w + x) * 4
                self.px[i:i + 4] = bytes(color)

    def frame(self, x0, y0, w, h, color=BORDER, t=1):
        self.rect(x0, y0, x0 + w, y0 + t, color)
        self.rect(x0, y0 + h - t, x0 + w, y0 + h, color)
        self.rect(x0, y0, x0 + t, y0 + h, color)
        self.rect(x0 + w - t, y0, x0 + w, y0 + h, color)

    def blit(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                i = (y * other.w + x) * 4
                j = ((oy + y) * self.w + (ox + x)) * 4
                if 0 <= oy + y < self.h and 0 <= ox + x < self.w:
                    self.px[j:j + 4] = other.px[i:i + 4]


def panel(w, h):
    c = Canvas(w * S, h * S)
    c.frame(0, 0, w * S, h * S, BORDER, S)
    return c


def slot(c, x, y):
    c.rect(x * S, y * S, (x + 18) * S, (y + 18) * S, SLOT)
    c.frame(x * S, y * S, 18 * S, 18 * S, BORDER, 1)


def tank(c, x, y, w, h, fill_ratio=1.0):
    c.rect((x - 1) * S, (y - 1) * S, (x + w + 1) * S, (y + h + 1) * S, BORDER)
    c.rect(x * S, y * S, (x + w) * S, (y + h) * S, TANK)
    fh = int(h * fill_ratio)
    if fh > 0:
        c.rect(x * S, (y + h - fh) * S, (x + w) * S, (y + h) * S, TANK_FLUID)


def bar(c, x, y, w, h):
    c.rect((x - 1) * S, (y - 1) * S, (x + w + 1) * S, (y + h + 1) * S, BORDER)
    c.rect(x * S, y * S, (x + w) * S, (y + h) * S, ENERGY)


def lamp(c, x, y, size):
    c.rect((x - 1) * S, (y - 1) * S, (x + size + 1) * S, (y + size + 1) * S, BORDER)
    c.rect(x * S, y * S, (x + size) * S, (y + size) * S, LAMP)


def text_extent(c, x, y, cjk=5, ascii_=3, color=LABEL):
    """把一行字**按最宽的估法**画成实心块（CJK 每字 9px、ASCII 每字 6px；这里按 S 倍画）。
    只用来"看有没有压到别的东西"，不是真实字形。"""
    w = cjk * 9 + ascii_ * 6
    c.rect(x * S, y * S, (x + w) * S, (y + 9) * S, color)
    return w


def player_inv(c, top_y):
    for r in range(3):
        for col in range(9):
            slot(c, 8 + col * 18 - 1, top_y + r * 18 - 1)
    for col in range(9):
        slot(c, 8 + col * 18 - 1, top_y + 58 - 1)


def air_separator():
    w, h = 176, 166
    c = panel(w, h)
    tank(c, 46, 17, 18, 52, 0.6)
    tank(c, 78, 17, 18, 52, 0.25)
    lamp(c, 114, 38, 8)
    player_inv(c, 84)
    return c


def ammonia():
    w, h = 196, 202
    c = panel(w, h)
    tank(c, 26, 17, 18, 52, 0.5)       # 氮气
    tank(c, 48, 17, 18, 52, 0.5)       # 氢气
    tank(c, 152, 17, 18, 52, 0.3)      # 氨气
    slot(c, 78, 35)                    # 催化剂
    text_extent(c, 78, 20, cjk=5, ascii_=2)   # 「催化剂(铁粉)」
    slot(c, 26, 74)                    # 气罐槽
    slot(c, 48, 74)
    slot(c, 152, 74)
    bar(c, 176, 17, 10, 52)
    lamp(c, 176, 74, 8)
    player_inv(c, 118)
    return c


def main():
    a = air_separator()
    b = ammonia()
    gap = 12
    out_w = a.w + b.w + gap * 3
    out_h = max(a.h, b.h) + gap * 2
    out = Canvas(out_w, out_h)
    out.blit(a, gap, gap)
    out.blit(b, gap * 2 + a.w, gap)
    P.write_png(OUT, out_w, out_h, out.px)
    print(u"写出 %s（%dx%d；左=空气分离器 176×166，右=氨气组成室 196×202）"
          % (OUT, out_w, out_h))
    return 0


if __name__ == "__main__":
    sys.exit(main())
