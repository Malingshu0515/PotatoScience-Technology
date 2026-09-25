# -*- coding: utf-8 -*-
u"""_zf97_textures.py —— ZF97 的 **8 张程序生成占位贴图**

用户这一轮没给任何贴图（只有机器与数值），所以全部由本脚本生成 —— 与 ZF78/ZF82/ZF96 同一套做法：

**① 两种新流体的 still / flow（4 张）**
  `block/nitrogen_still.png` + `block/nitrogen_flow.png` —— 淡蓝灰（液氮色）
  `block/ammonia_still.png`  + `block/ammonia_flow.png`  —— 淡青绿
  老规矩（与氧气/氢气/氯气/四种产物一致）：**同一种流体的 still 与 flow 逐字节相同**。

**② 两台新机器的侧面 / 顶面（4 张）**
  `block/air_separator_side.png` / `_top.png`：
      灰钢机身 + 两根竖管 + 中间一条**淡蓝冷雾窗**（分离空气 = 低温）；顶面是进气格栅。
  `block/ammonia_synthesis_chamber_side.png` / `_top.png`：
      灰钢机身 + 左右两根进料管（氮/氢）+ 中间**青绿反应窗**（氨）；顶面是催化剂投料口。

配色沿用本工程占位贴图那一套灰（74,74,82 / 110,110,120 / 154,162,172 / 48,48,56）。
⚠ 八张都算**我们自己的贴图** ⇒ 英文公告里"还在借原版贴图的模型 = 5"**不变**。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BLOCK_DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "textures", "block")

# ---------- 机身灰 ----------
STEEL = (74, 74, 82, 255)
STEEL_LIGHT = (110, 110, 120, 255)
STEEL_HI = (154, 162, 172, 255)
STEEL_DARK = (48, 48, 56, 255)
TOP_BASE = (92, 92, 102, 255)
TOP_DARK = (58, 58, 66, 255)
# ---------- 氮气：淡蓝灰 ----------
N2 = (146, 176, 206, 255)
N2_HI = (198, 220, 240, 255)
N2_DARK = (92, 122, 156, 255)
# ---------- 氨气：淡青绿 ----------
NH3 = (142, 200, 178, 255)
NH3_HI = (196, 234, 216, 255)
NH3_DARK = (84, 142, 122, 255)
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


# ================= ① 流体（still / flow 同图）=================

def fluid(base, hi, dark):
    """16×16 的流体贴图：底色 + 两道横向波纹（与氧气/氢气那批占位同一路数）。"""
    rgba = blank(color=base)
    rect(rgba, 16, 0, 0, 15, 15, base)
    for y in range(0, 16, 4):
        rect(rgba, 16, 0, y, 15, y, dark)
        rect(rgba, 16, 0, y + 1, 15, y + 1, hi)
    # 几粒亮点，免得整张图是死板条纹
    for (x, y) in ((3, 9), (11, 3), (7, 13)):
        put(rgba, 16, x, y, hi)
    return rgba


# ================= ② 空气分离器 =================

def air_side():
    rgba = blank(color=STEEL)
    rect(rgba, 16, 1, 1, 14, 14, STEEL)
    # 左右两根竖管（冷媒）
    for x0 in (2, 11):
        rect(rgba, 16, x0, 1, x0 + 1, 14, STEEL_LIGHT)
        rect(rgba, 16, x0, 1, x0, 14, STEEL_HI)
    # 中间：冷雾窗（外框深、内膛暗、两道淡蓝冷气）
    rect(rgba, 16, 5, 3, 10, 12, STEEL_DARK)
    rect(rgba, 16, 6, 4, 9, 11, TOP_DARK)
    rect(rgba, 16, 6, 6, 9, 7, N2_DARK)
    rect(rgba, 16, 6, 7, 9, 8, N2)
    rect(rgba, 16, 6, 9, 9, 10, N2_HI)
    outline(rgba, 16, 16)
    rivets(rgba, 16)
    return rgba


def air_top():
    rgba = blank(color=TOP_BASE)
    rect(rgba, 16, 1, 1, 14, 14, TOP_BASE)
    # 顶面：进气格栅（横条），两侧各一个淡蓝小口
    for y in range(4, 11, 2):
        rect(rgba, 16, 4, y, 11, y, TOP_DARK)
        rect(rgba, 16, 4, y + 1, 11, y + 1, STEEL_LIGHT)
    put(rgba, 16, 3, 7, N2_HI)
    put(rgba, 16, 12, 7, N2_HI)
    outline(rgba, 16, 16)
    rivets(rgba, 16)
    return rgba


# ================= ③ 氨气组成室 =================

def ammonia_side():
    rgba = blank(color=STEEL)
    rect(rgba, 16, 1, 1, 14, 14, STEEL)
    # 左右两根进料管（氮 / 氢）
    for x0 in (2, 11):
        rect(rgba, 16, x0, 1, x0 + 1, 14, STEEL_LIGHT)
        rect(rgba, 16, x0, 1, x0, 14, STEEL_HI)
    # 中间：反应窗（青绿 = 氨）
    rect(rgba, 16, 5, 3, 10, 12, STEEL_DARK)
    rect(rgba, 16, 6, 4, 9, 11, TOP_DARK)
    rect(rgba, 16, 6, 6, 9, 9, NH3_DARK)
    rect(rgba, 16, 6, 7, 9, 8, NH3)
    rect(rgba, 16, 6, 7, 6, 8, NH3_HI)
    outline(rgba, 16, 16)
    rivets(rgba, 16)
    return rgba


def ammonia_top():
    rgba = blank(color=TOP_BASE)
    rect(rgba, 16, 1, 1, 14, 14, TOP_BASE)
    # 顶面：中央催化剂投料口（外圈法兰 + 内圈青绿）
    rect(rgba, 16, 4, 4, 11, 11, STEEL_DARK)
    rect(rgba, 16, 4, 4, 11, 4, STEEL_HI)
    rect(rgba, 16, 4, 4, 4, 11, STEEL_HI)
    rect(rgba, 16, 5, 5, 10, 10, TOP_DARK)
    rect(rgba, 16, 6, 6, 9, 9, NH3_DARK)
    rect(rgba, 16, 7, 7, 8, 8, NH3)
    outline(rgba, 16, 16)
    rivets(rgba, 16)
    return rgba


TEXTURES = [
    (u"nitrogen_still", lambda: fluid(N2, N2_HI, N2_DARK), u"氮气·静止（占位）"),
    (u"nitrogen_flow", lambda: fluid(N2, N2_HI, N2_DARK), u"氮气·流动（同上，逐字节相同）"),
    (u"ammonia_still", lambda: fluid(NH3, NH3_HI, NH3_DARK), u"氨气·静止（占位）"),
    (u"ammonia_flow", lambda: fluid(NH3, NH3_HI, NH3_DARK), u"氨气·流动（同上，逐字节相同）"),
    (u"air_separator_side", air_side, u"空气分离器·侧"),
    (u"air_separator_top", air_top, u"空气分离器·顶"),
    (u"ammonia_synthesis_chamber_side", ammonia_side, u"氨气组成室·侧"),
    (u"ammonia_synthesis_chamber_top", ammonia_top, u"氨气组成室·顶"),
]


def main():
    force = "--force" in sys.argv
    ok = 0
    for (name, fn, cn) in TEXTURES:
        dst = os.path.join(BLOCK_DIR, name + ".png")
        if os.path.exists(dst) and not force:
            print(u"  [STOP] 已存在，不覆盖：%s（要重画加 --force）" % dst)
            return 1
        data = fn()
        P.write_png(dst, 16, 16, data)
        # 写-读往返自证（§4.17：能失败的检查才算检查）
        w, h, back = P.read_png(dst)
        if (w, h) != (16, 16) or bytes(back) != bytes(data):
            print(u"  [FAIL] %s 写-读往返不一致" % name)
            return 1
        print(u"  OK  %-38s %5d B  %s" % (name + ".png", os.path.getsize(dst), cn))
        ok += 1
    # still 与 flow 必须逐字节相同（老规矩）
    for pair in ((u"nitrogen_still", u"nitrogen_flow"), (u"ammonia_still", u"ammonia_flow")):
        a = open(os.path.join(BLOCK_DIR, pair[0] + ".png"), "rb").read()
        b = open(os.path.join(BLOCK_DIR, pair[1] + ".png"), "rb").read()
        if a != b:
            print(u"  [FAIL] %s 与 %s 不是逐字节相同" % pair)
            return 1
        print(u"  OK  %s == %s（逐字节相同）" % pair)
    print(u"生成 %d 张；失败项 = 0" % ok)
    return 0


if __name__ == "__main__":
    sys.exit(main())
