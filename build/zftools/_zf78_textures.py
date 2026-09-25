# -*- coding: utf-8 -*-
"""ZF78 贴图（分馏塔三件套）。

① 用户给的四张 16x16 产品贴图（原件是 JPEG，由 PowerShell + System.Drawing 先转成
   build/zftools/_zf78_tmp/<name>.png）→ 写成本工程的 PNG（still + flow 同一张，
   与氧气/原油的老规矩一致：这两种流体贴图在本工程里逐字节相同）。

       diesel.png    → 柴油
       naphtha.png   → 石脑油
       gasoline.png  → 汽油
       lpg.png       → 液化石油气

② 分馏塔控制器 / 分馏塔操作器的**占位**方块贴图（顶 + 侧，程序生成，等美术 pass）：
   配色沿用本工程其它机器占位贴图那一套灰（74,74,82 / 88,88,94 / 58,58,62 +
   高光 154,162,172），控制器带琥珀色热带、操作器带青色屏。

③ 沥青贴图**不落文件**：按用户原话「沥青贴图暂时用火药占位」，item model 直接引用
   minecraft:item/gunpowder（与 capacitor 借 iron_nugget 同一套做法）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BLOCK_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "block")
TMP_DIR = os.path.join(ROOT, "build", "zftools", "_zf78_tmp")

FLUIDS = [
    ("diesel", "柴油"),
    ("naphtha", "石脑油"),
    ("gasoline", "汽油"),
    ("lpg", "液化石油气"),
]

# ---------- 占位方块贴图配色 ----------
STEEL = (74, 74, 82, 255)
STEEL_LIGHT = (110, 110, 120, 255)
STEEL_HI = (154, 162, 172, 255)
STEEL_DARK = (48, 48, 56, 255)
TOP_BASE = (92, 92, 102, 255)
TOP_DARK = (58, 58, 66, 255)
HEAT = (196, 106, 26, 255)
HEAT_DARK = (120, 60, 12, 255)
SCREEN_DARK = (24, 44, 52, 255)
SCREEN = (58, 150, 158, 255)
SCREEN_HI = (120, 208, 208, 255)


def blank(w=16, h=16, color=(0, 0, 0, 0)):
    px = bytearray()
    for _ in range(w * h):
        px += bytes(color)
    return px


def put(rgba, w, x, y, color):
    i = (y * w + x) * 4
    rgba[i:i + 4] = bytes(color)


def rect(rgba, w, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(rgba, w, x, y, color)


def outline(rgba, w, h, color=STEEL_DARK):
    rect(rgba, w, 0, 0, w - 1, 0, color)
    rect(rgba, w, 0, h - 1, w - 1, h - 1, color)
    rect(rgba, w, 0, 0, 0, h - 1, color)
    rect(rgba, w, w - 1, 0, w - 1, h - 1, color)


def rivets(rgba, w, h, color=STEEL_HI):
    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        put(rgba, w, x, y, color)


# ================= ① 产品流体贴图 =================

def convert_fluids():
    made = []
    for name, cn in FLUIDS:
        src = os.path.join(TMP_DIR, name + ".png")
        if not os.path.exists(src):
            print("MISS  {0}（缺 {1}，先跑 PowerShell 转换）".format(name, src))
            return None
        w, h, rgba = P.read_png(src)
        if (w, h) != (16, 16):
            print("FAIL  {0} 尺寸 {1}x{2}（要求 16x16）".format(name, w, h))
            return None
        # JPEG 转出来的是不透明图：统一把 alpha 钉成 255
        for i in range(3, len(rgba), 4):
            rgba[i] = 255
        for suffix in ("still", "flow"):
            dst = os.path.join(BLOCK_DIR, "{0}_{1}.png".format(name, suffix))
            P.write_png(dst, 16, 16, rgba)
            made.append((cn, name + "_" + suffix, os.path.getsize(dst)))
    return made


# ================= ② 占位方块贴图 =================

def controller_side():
    rgba = blank(color=STEEL)
    rect(rgba, 16, 1, 1, 14, 14, STEEL)
    # 两条竖管
    rect(rgba, 16, 3, 1, 4, 14, STEEL_LIGHT)
    rect(rgba, 16, 3, 1, 3, 14, STEEL_HI)
    rect(rgba, 16, 11, 1, 12, 14, STEEL_LIGHT)
    rect(rgba, 16, 12, 1, 12, 14, STEEL_HI)
    # 中间的热带（琥珀色，两段带暗缝）
    rect(rgba, 16, 1, 6, 14, 9, HEAT_DARK)
    rect(rgba, 16, 1, 7, 14, 8, HEAT)
    rect(rgba, 16, 7, 6, 8, 9, STEEL_DARK)
    outline(rgba, 16, 16)
    rivets(rgba, 16, 16)
    return rgba


def controller_top():
    rgba = blank(color=TOP_BASE)
    rect(rgba, 16, 1, 1, 14, 14, TOP_BASE)
    # 中央炉口
    rect(rgba, 16, 5, 5, 10, 10, TOP_DARK)
    rect(rgba, 16, 6, 6, 9, 9, HEAT_DARK)
    rect(rgba, 16, 7, 7, 8, 8, HEAT)
    outline(rgba, 16, 16)
    rivets(rgba, 16, 16)
    return rgba


def operator_side():
    rgba = blank(color=(88, 88, 94, 255))
    rect(rgba, 16, 1, 1, 14, 14, (88, 88, 94, 255))
    # 屏幕
    rect(rgba, 16, 2, 3, 13, 12, SCREEN_DARK)
    rect(rgba, 16, 3, 4, 12, 11, SCREEN)
    for y in (5, 7, 9):
        rect(rgba, 16, 3, y, 12, y, SCREEN_HI)
    rect(rgba, 16, 3, 4, 12, 4, (30, 96, 104, 255))
    outline(rgba, 16, 16)
    rivets(rgba, 16, 16)
    return rgba


def operator_top():
    rgba = blank(color=TOP_BASE)
    rect(rgba, 16, 1, 1, 14, 14, TOP_BASE)
    # 散热格栅
    for y in range(4, 12, 2):
        rect(rgba, 16, 3, y, 12, y, TOP_DARK)
        rect(rgba, 16, 3, y + 1, 12, y + 1, STEEL_LIGHT)
    outline(rgba, 16, 16)
    rivets(rgba, 16, 16)
    return rgba


BLOCKS = [
    ("distillation_controller_side", controller_side, "分馏塔控制器·侧"),
    ("distillation_controller_top", controller_top, "分馏塔控制器·顶"),
    ("distillation_operator_side", operator_side, "分馏塔操作器·侧"),
    ("distillation_operator_top", operator_top, "分馏塔操作器·顶"),
]


def make_blocks():
    made = []
    for name, fn, cn in BLOCKS:
        dst = os.path.join(BLOCK_DIR, name + ".png")
        P.write_png(dst, 16, 16, fn())
        made.append((cn, name, os.path.getsize(dst)))
    return made


def main():
    if not os.path.isdir(TMP_DIR):
        print("MISS  临时目录 {0}".format(TMP_DIR))
        return 1
    fluids = convert_fluids()
    if fluids is None:
        return 1
    blocks = make_blocks()
    print("== 产品流体贴图（8 个：4 种 x still/flow）==")
    for cn, name, size in fluids:
        print("  OK  {0:12s} {1:22s} {2} B".format(cn, name, size))
    print("== 占位方块贴图（4 个：2 方块 x 顶/侧）==")
    for cn, name, size in blocks:
        print("  OK  {0:16s} {1:32s} {2} B".format(cn, name, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
