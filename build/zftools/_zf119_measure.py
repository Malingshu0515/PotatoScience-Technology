# -*- coding: utf-8 -*-
r"""_zf119_measure.py —— 量一下**盘上已有的锭/物品贴图**：尺寸 + 内容包围盒 + 纵向摆位

为什么要量：本轮这张 `振金锭.png` 是「宽 32、每帧内容 24 行」的一条竖直长条，
而 MC 的动画贴图**必须是方形帧**（宽 × 宽×帧数）⇒ 重建时"内容放在帧里的什么位置"
不能凭感觉 —— 拿盘上已有的物品贴图（尤其 ZF60 那批**用户自己画的 32×32**）当基准。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

TEXI = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"
WANT = ["titanium_ingot.png", "magnet.png", "titanium_powder.png", "raw_titanium.png",
        "star_steel_ingot.png", "iron_powder.png", "carbon.png", "aluminum_ingot.png",
        "silver_ingot.png", "nickel_ingot.png", "cobalt_ingot.png", "uranium_ingot.png",
        "toner.png", "lithium_carbonate.png", "sea_salt.png"]

lines = []


def say(s):
    print(s)
    lines.append(s)


def main():
    say(u"# 盘上物品贴图的尺寸与内容包围盒")
    say(u"")
    say(u"| 文件 | 尺寸 | 内容 bbox (x0..x1, y0..y1) | 内容宽×高 | 上留 / 下留 |")
    say(u"|---|---|---|---|---|")
    for name in WANT:
        p = os.path.join(TEXI, name)
        if not os.path.exists(p):
            say(u"| `%s` | （没有） | | | |" % name)
            continue
        w, h, rgba = read_png(p)
        xs, ys = [], []
        for y in range(h):
            for x in range(w):
                if rgba[y * w + x][3] > 0:
                    xs.append(x)
                    ys.append(y)
        if not xs:
            say(u"| `%s` | %d×%d | **全透明** | | |" % (name, w, h))
            continue
        bbox = (min(xs), max(xs), min(ys), max(ys))
        say(u"| `%s` | %d×%d | %d..%d, %d..%d | %d×%d | %d / %d |"
            % (name, w, h, bbox[0], bbox[1], bbox[2], bbox[3],
               bbox[1] - bbox[0] + 1, bbox[3] - bbox[2] + 1, bbox[2], h - 1 - bbox[3]))
    io.open(r"E:\PotatoST\build\zftools\_zf119_measure.txt", "w",
            encoding="utf-8", newline=u"\n").write(u"\n".join(lines) + u"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
