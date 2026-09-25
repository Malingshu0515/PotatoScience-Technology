# -*- coding: utf-8 -*-
"""_zf45_textures.py —— ZF45 四个新物品的贴图生成（无第三方依赖）

用户原话：「新物品材质你简单画一下或者用原版相近的代替」。

**为什么自己画而不是借原版**：铁粉 / 磁铁 / 热力金属 / 光伏原件
在本项目里都是有明确形状的东西，借原版贴图（火药 / 铁粒 / 糖…）会**互相撞脸** ——
玩家分不清背包里哪个是铁粉哪个是碳粉。所以两张「有现成形状可复用」的用改色，
两张「没有相近原版」的手画。

**尺寸约定**：本项目自己的物品贴图是 **160×160**（= 16×16 像素画放大 10 倍，
见 carbon.png / silver_ingot.png 的 probe 结果）。所以这里也按 16×16 逻辑网格画，
再放大 10 倍写出 —— 跟着项目已有的美术规格走，不新造一套。

四张：
  ① iron_powder.png      铁粉   ← carbon.png 的粉尘形状改色（黑 → 灰）
  ② thermal_metal.png    热力金属 ← silver_ingot.png 的锭形改色（银 → 炽橙）
  ③ magnet.png           磁铁   ← 手画马蹄形磁铁（红身 + 灰磁极）
  ④ photovoltaic_component.png 光伏原件 ← 手画太阳能电池板（深蓝电池 + 灰框 + 触点）

跑法：
    python build/zftools/_zf45_textures.py --probe     # 只看，不写
    python build/zftools/_zf45_textures.py --write
"""
import argparse
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png, histogram      # noqa: E402

PROJ = "E:\\PotatoST"
TEX = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "textures", "item")
GRID = 16
SCALE = 10


def clamp255(v):
    return 0 if v < 0 else (255 if v > 255 else int(round(v)))


# ============================================================
#  ①② 改色（复用现成形状）
# ============================================================
def make_iron_powder(src_png):
    """碳粉的黑尘 → 铁粉的灰尘。

    carbon.png 的亮度全在 V=0.00~0.11（几乎纯黑）。铁粉要**看得出是铁**：
    把亮度线性抬到 0.30~0.80 的灰阶，并加一点点冷调（B 比 R 高 8），
    这样和碳粉放在一起是"深灰 vs 纯黑"，一眼能分。
    """
    w, h, rgba = read_png(src_png)
    out = bytearray(rgba)
    for i in range(w * h):
        a = rgba[i * 4 + 3]
        if a == 0:
            continue
        v = max(rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2]) / 255.0
        nv = 0.30 + v * 4.5                      # 0.00 → 0.30 ; 0.11 → 0.80
        if nv > 0.86:
            nv = 0.86
        g = clamp255(nv * 255)
        out[i * 4] = clamp255(g - 6)
        out[i * 4 + 1] = g
        out[i * 4 + 2] = clamp255(g + 8)
    return w, h, out


def make_thermal_metal(src_png):
    """银锭的锭形 → 热力金属（炽热的橙金色）。

    亮度保留（保住原来的高光/阴影关系），把色相按亮度往黄偏：
    暗部 30°（红橙）、亮部 44°（金黄）—— 这就是"烧红了"的读法。
    """
    import colorsys
    w, h, rgba = read_png(src_png)
    out = bytearray(rgba)
    for i in range(w * h):
        a = rgba[i * 4 + 3]
        if a == 0:
            continue
        r, g, b = rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2]
        _, _, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        hue = (28.0 + (v - 0.6) * 40.0) / 360.0  # v=0.6 → 28°（红橙）, v=0.9 → 40°（金黄）
        nr, ng, nb = colorsys.hsv_to_rgb(hue % 1.0, 0.82, min(1.0, v * 1.02))
        out[i * 4] = clamp255(nr * 255)
        out[i * 4 + 1] = clamp255(ng * 255)
        out[i * 4 + 2] = clamp255(nb * 255)
    return w, h, out


# ============================================================
#  ③④ 手画（16×16 逻辑网格 → 放大 10 倍）
# ============================================================
def paint(rows, palette):
    """字符画 → 160×160 RGBA。'.' = 全透明。"""
    assert len(rows) == GRID, "行数必须是 {0}".format(GRID)
    rgba = bytearray(GRID * SCALE * GRID * SCALE * 4)
    for y, row in enumerate(rows):
        assert len(row) == GRID, "第 {0} 行是 {1} 列，应为 {2}".format(y, len(row), GRID)
        for x, ch in enumerate(row):
            col = palette[ch]
            if col is None:
                continue
            for dy in range(SCALE):
                base = ((y * SCALE + dy) * GRID * SCALE + x * SCALE) * 4
                for dx in range(SCALE):
                    p = base + dx * 4
                    rgba[p:p + 4] = bytes(col)
    return GRID * SCALE, GRID * SCALE, rgba


# 马蹄形磁铁：U 口朝上，两极为浅灰，身体为红
MAGNET_ROWS = [
    "................",
    "................",
    "..#PPP#..#PPP#..",
    "..#PPP#..#PPP#..",
    "..#PPP#..#PPP#..",
    "..#RRR#..#RRR#..",
    "..#RRR#..#RRR#..",
    "..#RRR#..#RRR#..",
    "..#RRR#..#RRR#..",
    "..#RRR#..#RRR#..",
    "..#RRRRRRRRRR#..",
    "..#RRRRRRRRRR#..",
    "..#rrrrrrrrrr#..",
    "..############..",
    "................",
    "................",
]
MAGNET_PALETTE = {
    ".": None,
    "#": (0x4A, 0x1B, 0x14, 255),      # 深红描边
    "P": (0xD8, 0xD8, 0xD8, 255),      # 磁极（浅灰）
    "R": (0xC0, 0x39, 0x2B, 255),      # 磁体红
    "r": (0xE0, 0x5B, 0x4A, 255),      # 底缘高光
}

# 光伏原件：深蓝电池片 + 灰色边框 + 十字分割 + 底部两个触点
PV_ROWS = [
    "................",
    "................",
    ".FFFFFFFFFFFFFF.",
    ".FHHBBBLLBBBBBF.",
    ".FHHBBBLLBBBBBF.",
    ".FBBBBBLLBBBBBF.",
    ".FBBBBBLLBBBBBF.",
    ".FLLLLLLLLLLLLF.",
    ".FLLLLLLLLLLLLF.",
    ".FBBBBBLLBBBBBF.",
    ".FBBBBBLLBBBBBF.",
    ".FBBBBBLLBBBBBF.",
    ".FBBBBBLLBBBBBF.",
    ".FFFFFFFFFFFFFF.",
    "....FF....FF....",
    "................",
]
PV_PALETTE = {
    ".": None,
    "F": (0x8A, 0x8A, 0x8A, 255),      # 铝框
    "B": (0x1E, 0x3F, 0x73, 255),      # 电池片（深蓝）
    "L": (0x4E, 0x7F, 0xBF, 255),      # 电池片分割线（浅蓝）
    "H": (0x3E, 0x7F, 0xD0, 255),      # 左上角反光
}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args(argv)

    jobs = [
        ("iron_powder.png", lambda: make_iron_powder(os.path.join(TEX, "carbon.png"))),
        ("thermal_metal.png", lambda: make_thermal_metal(os.path.join(TEX, "silver_ingot.png"))),
        ("magnet.png", lambda: paint(MAGNET_ROWS, MAGNET_PALETTE)),
        ("photovoltaic_component.png", lambda: paint(PV_ROWS, PV_PALETTE)),
    ]
    for name, fn in jobs:
        w, h, rgba = fn()
        rows = histogram(rgba, w, h)
        opaque = sum(1 for i in range(w * h) if rgba[i * 4 + 3] != 0)
        print("== {0}  {1}x{2}  不透明像素 {3}/{4}  颜色 {5} 种".format(
            name, w, h, opaque, w * h, len(rows)))
        for n, r, g, b, hh, s, v in rows[:5]:
            print("     #{0:02X}{1:02X}{2:02X}  x{3:<6} H={4:5.1f} S={5:.2f} V={6:.2f}".format(r, g, b, n, hh, s, v))
        if args.write:
            dst = os.path.join(TEX, name)
            write_png(dst, w, h, rgba)
            print("     已写出 {0} ({1} 字节)".format(dst, os.path.getsize(dst)))
        print("")
    if not args.write and not args.probe:
        print("（什么都没写：加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
