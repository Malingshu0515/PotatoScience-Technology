# -*- coding: utf-8 -*-
u"""_zf96_textures.py —— ZF96 的三张**程序生成占位**贴图（等美术 pass 换掉）

用户这一轮没有给任何贴图（原话只有机器/配方与数值），所以三张都由本脚本生成 ——
与 ZF78 的分馏塔控制器/操作器、ZF82 的容器换流器同一套做法：

  ① `textures/block/hydrodesulfurization_chamber_side.png` —— 机器侧面：
     灰钢机身 + 左右两根**氢气竖管** + 中间一条**琥珀黄反应窗**（硫黄的颜色）
  ② `textures/block/hydrodesulfurization_chamber_top.png` —— 机器顶面：
     灰钢顶盖 + 中央圆形进气口（外圈深色法兰 + 内圈琥珀黄）
  ③ `textures/item/sulfur.png` —— **硫**（物品图）：透明底上一堆黄色粉末

配色沿用本工程占位贴图那一套灰（74,74,82 / 110,110,120 / 154,162,172 / 48,48,56），
再各加一样"这台机器的记号色"：琥珀黄 (222,186,42) —— 与分馏塔控制器的琥珀热带同一色系，
但**形状完全不同**（那台是横向热带、这台是竖管 + 方窗），一眼能分开。

⚠ 三张都写在**"我们自己的贴图"**这一栏里 ⇒ 英文公告里"还在借原版贴图的模型 = 5"**不变**。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BLOCK_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "block")
ITEM_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "item")

# ---------- 机身灰（与 ZF78 占位贴图同一套）----------
STEEL = (74, 74, 82, 255)
STEEL_LIGHT = (110, 110, 120, 255)
STEEL_HI = (154, 162, 172, 255)
STEEL_DARK = (48, 48, 56, 255)
TOP_BASE = (92, 92, 102, 255)
TOP_DARK = (58, 58, 66, 255)
# ---------- 记号色：琥珀黄（硫黄）----------
SULFUR = (222, 186, 42, 255)
SULFUR_DARK = (140, 112, 16, 255)
SULFUR_HI = (250, 226, 116, 255)
# ---------- 硫物品：粉末三色 ----------
DUST_HI = (250, 226, 116, 255)
DUST = (222, 186, 42, 255)
DUST_MID = (186, 150, 26, 255)
DUST_DARK = (140, 112, 16, 255)
CLEAR = (0, 0, 0, 0)


def blank(w=16, h=16, color=CLEAR):
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


def rivets(rgba, w, color=STEEL_HI):
    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        put(rgba, w, x, y, color)


# ================= ① 机器侧面 =================

def chamber_side():
    rgba = blank(color=STEEL)
    rect(rgba, 16, 1, 1, 14, 14, STEEL)
    # 左右两根氢气竖管（管身亮、左边缘高光 —— 与分馏塔控制器的管子同一画法）
    for x0 in (2, 11):
        rect(rgba, 16, x0, 1, x0 + 1, 14, STEEL_LIGHT)
        rect(rgba, 16, x0, 1, x0, 14, STEEL_HI)
    # 中间反应窗：外框深、内膛暗、中间一条琥珀黄
    rect(rgba, 16, 5, 3, 10, 12, STEEL_DARK)
    rect(rgba, 16, 6, 4, 9, 11, TOP_DARK)
    rect(rgba, 16, 6, 6, 9, 9, SULFUR_DARK)
    rect(rgba, 16, 6, 7, 9, 8, SULFUR)
    rect(rgba, 16, 6, 7, 6, 8, SULFUR_HI)
    outline(rgba, 16, 16)
    rivets(rgba, 16)
    return rgba


# ================= ② 机器顶面 =================

def chamber_top():
    rgba = blank(color=TOP_BASE)
    rect(rgba, 16, 1, 1, 14, 14, TOP_BASE)
    # 中央进气口：外圈法兰（亮边）+ 内圈暗膛 + 中心琥珀黄
    rect(rgba, 16, 4, 4, 11, 11, STEEL_DARK)
    rect(rgba, 16, 4, 4, 11, 4, STEEL_HI)
    rect(rgba, 16, 4, 4, 4, 11, STEEL_HI)
    rect(rgba, 16, 5, 5, 10, 10, TOP_DARK)
    rect(rgba, 16, 6, 6, 9, 9, SULFUR_DARK)
    rect(rgba, 16, 7, 7, 8, 8, SULFUR)
    outline(rgba, 16, 16)
    rivets(rgba, 16)
    return rgba


# ================= ③ 硫（物品） =================

def sulfur_item():
    rgba = blank(color=CLEAR)
    # 一堆粉末：从下往上逐行收窄（第 12 行最宽 12 px、第 5 行只剩 2 px）——
    # 形状固定、可复算，改配色不影响轮廓
    rows = [
        (13, 3, 12, DUST_DARK),   # 底边的阴影
        (12, 2, 13, DUST_MID),    # 最宽的那一层
        (11, 3, 12, DUST),
        (10, 3, 12, DUST),
        (9, 4, 11, DUST),
        (8, 4, 11, DUST_HI),      # 高光层
        (7, 5, 10, DUST),
        (6, 6, 9, DUST_HI),
        (5, 7, 8, DUST),          # 堆尖
    ]
    for (y, x0, x1, color) in rows:
        rect(rgba, 16, x0, y, x1, y, color)
    # 右侧一道暗边（光源在左上，让这堆粉不至于是一块平板）
    for (x, y) in ((12, 11), (11, 10), (11, 9), (10, 8), (9, 6)):
        put(rgba, 16, x, y, DUST_MID)
    put(rgba, 16, 5, 10, DUST_HI)
    put(rgba, 16, 5, 9, DUST_HI)
    return rgba


TEXTURES = [
    (BLOCK_DIR, "hydrodesulfurization_chamber_side", chamber_side, u"加氢脱硫反应仓·侧（占位）"),
    (BLOCK_DIR, "hydrodesulfurization_chamber_top", chamber_top, u"加氢脱硫反应仓·顶（占位）"),
    (ITEM_DIR, "sulfur", sulfur_item, u"硫（占位）"),
]


def main():
    force = "--force" in sys.argv
    ok = 0
    for (folder, name, fn, cn) in TEXTURES:
        dst = os.path.join(folder, name + ".png")
        if os.path.exists(dst) and not force:
            print(u"  [STOP] 已存在，不覆盖：%s（要重画加 --force）" % dst)
            return 1
        P.write_png(dst, 16, 16, fn())
        # 立刻读回来核一遍（写-读往返自证，§4.17：能失败的检查才算检查）
        w, h, back = P.read_png(dst)
        if (w, h) != (16, 16) or bytes(back) != bytes(fn()):
            print(u"  [FAIL] %s 写-读往返不一致" % name)
            return 1
        print(u"  OK  %-40s %5d B  %s" % (name + ".png", os.path.getsize(dst), cn))
        ok += 1
    print(u"生成 %d 张；失败项 = 0" % ok)
    return 0


if __name__ == "__main__":
    sys.exit(main())
