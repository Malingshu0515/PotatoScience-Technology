# -*- coding: utf-8 -*-
"""_zf60_bg.py —— 查这 7 张图的"背景"到底是什么

WPF 解出来是 Bgr32（**没有 alpha 通道**），所以：
  · 方块贴图（钛矿/深层钛矿）本来就该 100% 不透明 ⇒ 正常；
  · 物品贴图（磁铁/铁粉/粗钛/钛粉/钛锭）如果带白底，游戏里就是一个白方块套着图案 ⇒ 得处理。
先量事实：四角颜色、纯白像素数、外框一圈是不是白的、以及"从边缘漫水能吃掉多少白像素"。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf60_install import read_png  # noqa: E402  （复用同一个 PNG 解码器）

STAGE = r"E:\PotatoST\build\zftools\_zf60_png"
NAMES = ["magnet", "iron_powder", "titanium_ore", "deepslate_titanium_ore",
         "raw_titanium", "titanium_powder", "titanium_ingot"]


def main():
    out = []
    for name in NAMES:
        path = os.path.join(STAGE, name + ".png")
        w, h, depth, color, ch, px = read_png(path)

        def at(x, y):
            i = (y * w + x) * ch
            return px[i], px[i + 1], px[i + 2]

        corners = [at(0, 0), at(w - 1, 0), at(0, h - 1), at(w - 1, h - 1)]
        white = sum(1 for i in range(0, len(px), ch)
                    if px[i] >= 250 and px[i + 1] >= 250 and px[i + 2] >= 250)
        border = ([at(x, 0) for x in range(w)] + [at(x, h - 1) for x in range(w)]
                  + [at(0, y) for y in range(h)] + [at(w - 1, y) for y in range(h)])
        border_white = sum(1 for c in border if min(c) >= 245)

        # 从边缘漫水（容差 245）：能吃掉的白像素 = 背景
        seen = [[False] * w for _ in range(h)]
        stack = []
        for x in range(w):
            stack += [(x, 0), (x, h - 1)]
        for y in range(h):
            stack += [(0, y), (w - 1, y)]
        eaten = 0
        while stack:
            x, y = stack.pop()
            if x < 0 or y < 0 or x >= w or y >= h or seen[y][x]:
                continue
            c = at(x, y)
            if min(c) < 245:
                continue
            seen[y][x] = True
            eaten += 1
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

        out.append(u"%-24s %2dx%-2d 色型%d  四角=%s  纯白 %3d/%d  外框白 %d/%d  漫水吃掉 %3d (%.1f%%)"
                   % (name, w, h, color,
                      u"/".join(u"#%02X%02X%02X" % c for c in corners),
                      white, w * h, border_white, len(border), eaten, 100.0 * eaten / (w * h)))
    io.open(r"E:\PotatoST\build\zftools\_zf60_bg.txt", "w", encoding="utf-8").write(u"\n".join(out))
    print(u"写出 %d 行" % len(out))


if __name__ == "__main__":
    main()
