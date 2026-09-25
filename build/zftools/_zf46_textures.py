# -*- coding: utf-8 -*-
"""_zf46_textures.py —— ZF46 黑钨矿 / 深层黑钨矿 / 粗钨 三张贴图

用户没给素材（「加入黑钨矿 和粗钨」），所以按项目既有做法：**拿现成贴图改色**（§6.7 的锂就是这么来的）。

**为什么是"黑灰"而不是棕色**：probe 过全部矿石的主色 ——
钴 307°(品红) / 锰 33°(棕) / 镍 38°(金棕) / 铀 92°(绿) / 锂 195°(青) / 铝与银无饱和像素(白)。
棕和金色**已经被锰和镍占了**，所以黑钨矿走"去饱和 + 压暗"的**冷灰黑**（H=220、S=0.14、V×0.45）：
在灰石头底上是一撮发黑的金属颗粒，和上面六种都不撞。

| 产物 | 素材 | 变换 |
|---|---|---|
| `wolframite_ore.png` | `manganese_ore.png`（16×16，矿石底 + 颗粒） | 只动 S>=0.25 的像素（石头底逐字节不动） |
| `deepslate_wolframite_ore.png` | `deepslate_manganese_ore.png`（16×16） | 同上 |
| `raw_tungsten.png` | `raw_lithium.png`（16×16，纯颗粒无底） | **全部不透明像素**都转灰（这张没有石头底要保） |

跑法：
    python build/zftools/_zf46_textures.py --probe
    python build/zftools/_zf46_textures.py --write
"""
import argparse
import colorsys
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png, histogram      # noqa: E402

PROJ = r"E:\PotatoST"
BLOCK = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "textures", "block")
ITEM = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "textures", "item")

HUE = 220.0 / 360.0     # 冷灰蓝
SAT = 0.14
VAL_MUL = 0.45          # 压暗 → "黑"
RAW_VAL_MUL = 0.62      # 粗钨是金属块状物，比矿石颗粒亮一点才看得出是"粗矿"


def clamp255(v):
    return 0 if v < 0 else (255 if v > 255 else int(round(v)))


def recolor(path, sat_min, sat, val_mul, hue=HUE):
    w, h, rgba = read_png(path)
    out = bytearray(rgba)
    touched = 0
    for i in range(w * h):
        if rgba[i * 4 + 3] == 0:
            continue
        r, g, b = rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2]
        _, s0, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        if s0 < sat_min:
            continue                     # 石头底/深板岩底原样保留
        nr, ng, nb = colorsys.hsv_to_rgb(hue, sat, min(1.0, v * val_mul))
        out[i * 4] = clamp255(nr * 255)
        out[i * 4 + 1] = clamp255(ng * 255)
        out[i * 4 + 2] = clamp255(nb * 255)
        touched += 1
    return w, h, out, touched


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args(argv)

    jobs = [
        # 矿石：石头底逐字节保留（sat_min=0.25 只放行矿物颗粒）
        (os.path.join(BLOCK, "wolframite_ore.png"),
         os.path.join(BLOCK, "manganese_ore.png"), 0.25, SAT, VAL_MUL, "黑钨矿"),
        (os.path.join(BLOCK, "deepslate_wolframite_ore.png"),
         os.path.join(BLOCK, "deepslate_manganese_ore.png"), 0.25, SAT, VAL_MUL, "深层黑钨矿"),
        # 粗钨：整张都是颗粒（没有底要保）⇒ sat_min=0.0 全改
        (os.path.join(ITEM, "raw_tungsten.png"),
         os.path.join(ITEM, "raw_lithium.png"), 0.0, SAT, RAW_VAL_MUL, "粗钨"),
    ]
    for dst, src, sat_min, sat, val_mul, label in jobs:
        w, h, rgba, touched = recolor(src, sat_min, sat, val_mul)
        rows = histogram(rgba, w, h)
        opaque = sum(1 for i in range(w * h) if rgba[i * 4 + 3] != 0)
        print(u"== {0}（{1}） {2}x{3}  改了 {4}/{5} 个不透明像素".format(label, os.path.basename(src), w, h, touched, opaque))
        for n, r, g, b, hh, s, v in rows[:5]:
            print(u"     #{0:02X}{1:02X}{2:02X}  x{3:<5} H={4:5.1f} S={5:.2f} V={6:.2f}".format(r, g, b, n, hh, s, v))
        if args.write:
            write_png(dst, w, h, rgba)
            print(u"     已写出 {0}（{1} 字节）".format(os.path.basename(dst), os.path.getsize(dst)))
        print(u"")
    if not args.write:
        print(u"（什么都没写：加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
