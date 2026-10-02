# -*- coding: utf-8 -*-
u"""_zf178_textures.py —— ZF178：7 张方块贴图（6 个粗矿块 + 1 个磁铁块）

用户原话：
  「参考粗矿本来的风格和原版粗矿块的风格 可以自己画吧」
  「必须先把每张对应的粗矿物品贴图的配色采样出来（用 Python + Pillow/numpy 读 …），
    统计出主色/亮部/暗部，再用同一套色画方块上的矿斑 —— 这样方块的矿斑和物品是同一块料」

画出来的东西（一律 16×16 / 8 位 RGBA / 整张不透明 / color type 6）：

  textures/block/magnet_block.png        深灰铁底 + 红·灰磁极斑（配色取自 textures/item/magnet.png）
  textures/block/raw_aluminum_block.png  石头底 + 铝白矿斑（取自 textures/item/raw_aluminum.png）
  textures/block/raw_cobalt_block.png    石头底 + 钴紫矿斑（取自 textures/item/raw_cobalt.png）
  textures/block/raw_nickel_block.png    石头底 + 镍黄矿斑（取自 textures/item/raw_nickel.png）
  textures/block/raw_silver_block.png    石头底 + 银白矿斑（取自 textures/item/raw_silver.png）
  textures/block/raw_tungsten_block.png  石头底 + 钨蓝灰矿斑（取自 textures/item/raw_tungsten.png）
  textures/block/raw_uranium_block.png   石头底 + 铀绿矿斑（取自 textures/item/raw_uranium.png）

两条铁律：
  ① **矿斑的每一种颜色都来自对应的物品贴图**：要么是采样出来的原值（暗部/中部/亮部的主色），
     要么是这些原值的线性混合（往白/往黑混，比例会打印出来）——不凭空发明颜色。
     唯一的例外是磁铁块的红（`magnet.png` 里几乎没有红，见 `red_family()` 的分支打印）。
  ② 石头底**自己画**（不抄原版任何贴图文件）：16×16 灰石子噪点，明度落在 #6E~#8A，
     外加 2~3 处更暗/更亮的颗粒；色阶是**固定的 6 级梯子**（不是连续随机），
     这样一张图的总颜色数在 20 上下，不会糊成噪声（本工程好贴图的实测是 5~19 色）。

矿斑画法：6~10 坨，每坨 2~5 像素，**坨与坨之间至少隔 1 像素**（切比雪夫距离 ≥ 2，绝不粘连）；
每坨按「左上亮、右下暗」的对角线分级上色，≥4 像素的坨再补 1 个高光像素 + 1 个最暗描边像素。

自检（不加 --write 也全跑）：每张图 16×16 / RGBA / alpha 全 255 / 颜色数 / 平均色 /
矿斑坨数与每坨像素数 / 石头底明度区间 / 逐像素字符画预览。

跑法：
    python build\\zftools\\_zf178_textures.py                      # 采样 + 画 + 自检，只打印，不落盘
    python build\\zftools\\_zf178_textures.py --write              # 真写：7 张 PNG + 21 份 JSON
    python build\\zftools\\_zf178_textures.py --preview <出.png>    # 顺带写一张放大对比图（给自己眼睛看）
"""
import argparse
import json
import os
import random
import sys

import numpy as np
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ----------------------------------------------------------------- 路径
PROJ = r"E:\PotatoST"
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")
TEX_ITEM = os.path.join(ASSETS, "textures", "item")
TEX_BLOCK = os.path.join(ASSETS, "textures", "block")
DIR_BLOCKSTATE = os.path.join(ASSETS, "blockstates")
DIR_MODEL_BLOCK = os.path.join(ASSETS, "models", "block")
DIR_MODEL_ITEM = os.path.join(ASSETS, "models", "item")
NS = "potato_s_t"

# ----------------------------------------------------------------- 要画的 7 张
# item：采样用的物品贴图；base：stone = 灰石子底，iron = 深灰铁底；seed：石头噪点的种子（定死，可复现）
BLOCKS = [
    dict(id="magnet_block", item="magnet.png", base="iron", seed=0x1781, poles=True),
    dict(id="raw_aluminum_block", item="raw_aluminum.png", base="stone", seed=0x1782, poles=False),
    dict(id="raw_cobalt_block", item="raw_cobalt.png", base="stone", seed=0x1783, poles=False),
    dict(id="raw_nickel_block", item="raw_nickel.png", base="stone", seed=0x1784, poles=False),
    dict(id="raw_silver_block", item="raw_silver.png", base="stone", seed=0x1785, poles=False),
    dict(id="raw_tungsten_block", item="raw_tungsten.png", base="stone", seed=0x1786, poles=False),
    dict(id="raw_uranium_block", item="raw_uranium.png", base="stone", seed=0x1787, poles=False),
]

# ----------------------------------------------------------------- 石头底 / 铁底
# 固定的 5 级灰梯子（微微偏冷，像原版石头）——**不是**连续随机，免得一张图几百种颜色。
# 步长 7：比连续噪声安静，又比"一整块死灰"有颗粒感（量过原版 iron_ore 的石头底：4 级灰、步长 11~16）。
STONE_LADDER = [(0x6E, 0x70, 0x72), (0x75, 0x77, 0x78), (0x7C, 0x7E, 0x7F),
                (0x83, 0x85, 0x86), (0x8A, 0x8C, 0x8D)]
STONE_W = [2, 3, 4, 3, 2]
STONE_DARK = (0x5A, 0x5C, 0x5E)      # 更暗的颗粒（在 #6E~#8A 之下，正好是"更暗"那一档）
STONE_LIGHT = (0x99, 0x9B, 0x9D)     # 更亮的颗粒

IRON_LADDER = [(0x44, 0x46, 0x4A), (0x4C, 0x4E, 0x52), (0x54, 0x56, 0x5A),
               (0x5C, 0x5E, 0x62), (0x64, 0x66, 0x6A)]
IRON_W = [2, 3, 4, 3, 2]
IRON_DARK = (0x30, 0x32, 0x36)
IRON_LIGHT = (0x76, 0x78, 0x7C)

# ----------------------------------------------------------------- 矿斑形状（2~5 像素）
SHAPES = [
    ((0, 0), (1, 0)),                                  # 2 横
    ((0, 0), (0, 1)),                                  # 2 竖
    ((0, 0), (1, 1)),                                  # 2 斜
    ((0, 0), (1, 0), (0, 1)),                          # 3 拐角
    ((0, 0), (1, 0), (2, 0)),                          # 3 横
    ((0, 0), (0, 1), (0, 2)),                          # 3 竖
    ((0, 0), (1, 0), (1, 1)),                          # 3 拐角（另一头）
    ((0, 0), (1, 0), (0, 1), (1, 1)),                  # 4 方块
    ((0, 0), (1, 0), (1, 1), (2, 1)),                  # 4 S
    ((0, 0), (0, 1), (0, 2), (1, 2)),                  # 4 L
    ((0, 0), (1, 0), (2, 0), (1, 1)),                  # 4 T
    ((0, 1), (1, 0), (1, 1), (1, 2)),                  # 4 T（竖）
    ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)),          # 5 十字
    ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1)),          # 5 P
    ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1)),          # 5 台阶
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),          # 5 W
]
# 形状权重：偏向大坨（2 像素的碎点只当点缀）。理由见下：
#   量过原版 iron_ore / gold_ore / copper_ore / diamond_ore（`client.jar` 现抠，只统计不复制）：
#   矿斑占 19.5%~24.6%，坨数 8~10，坨大小到 [15,13,9,6,6,6,4,2,2]。
#   本轮的约束是「6~10 坨、每坨 2~5 像素」⇒ 上限 50 像素（19.5%）——
#   所以选形状时偏向 4~5 像素，落在 8~10 坨 ≈ 34~44 像素（13%~17%），贴近原版那个密度。
SHAPE_W = [1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 5, 4, 4, 5]

# 字符画图例（给人眼看）
LEGEND = {
    ".": u"石头底", ":" : u"更暗的颗粒", "+": u"更亮的颗粒",
    "O": u"矿斑·中部（= 物品中部主色）", "o": u"矿斑·亮部", "#": u"矿斑·暗部/描边",
    "W": u"矿斑·高光（亮部往白混）", "@": u"矿斑·最深（暗部往黑混）",
    "X": u"磁极红·中部", "x": u"磁极红·亮部", "=": u"磁极红·暗部",
    "Y": u"磁极红·高光", "%": u"磁极红·最深",
}
PAL_ROLE = ["light", "body", "dark", "spec", "deep"]
ROLE_CHAR_A = dict(light="o", body="O", dark="#", spec="W", deep="@")
ROLE_CHAR_B = dict(light="x", body="X", dark="=", spec="Y", deep="%")


# ================================================================= 采样
def _hsv(rgb):
    r, g, b = [v / 255.0 for v in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6.0, (0.0 if mx == 0 else d / mx), mx


def _from_hsv(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, min(max(s, 0.0), 1.0), min(max(v, 0.0), 1.0))
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def _lum(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def _mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _hexs(rgb):
    return u"#%02X%02X%02X" % tuple(rgb)


def _mode_of(band):
    """一段像素里出现次数最多的颜色（并列时取更亮的那个）。"""
    if len(band) == 0:
        return None, 0
    uniq, counts = np.unique(band, axis=0, return_counts=True)
    order = np.lexsort((uniq.sum(axis=1), counts))
    k = order[-1]
    return tuple(int(v) for v in uniq[k]), int(counts[k])


def sample_item(path):
    u"""真解码一张物品贴图，按亮度分三段统计（暗部 / 中部 / 亮部），外加红色像素统计。"""
    with Image.open(path) as im:
        size, mode = im.size, im.mode
        arr = np.asarray(im.convert("RGBA"), dtype=np.uint8)
    flat = arr.reshape(-1, 4)
    op = flat[flat[:, 3] >= 200][:, :3].astype(np.int32)
    n = len(op)
    lum = 0.299 * op[:, 0] + 0.587 * op[:, 1] + 0.114 * op[:, 2]
    order = np.argsort(lum, kind="stable")
    k = max(1, n // 8)
    bands = {
        "dark": op[order[:k]],
        "mid": op[order[n // 4: max(n // 4 + 1, (3 * n) // 4)]],
        "bright": op[order[-k:]],
    }
    out = {"path": path, "size": size, "mode": mode, "opaque": n,
           "colors": int(len(np.unique(op, axis=0))),
           "mean": tuple(int(round(v)) for v in op.mean(axis=0))}
    for name, band in bands.items():
        mode_c, cnt = _mode_of(band)
        out[name] = mode_c
        out[name + "_mean"] = tuple(int(round(v)) for v in band.mean(axis=0))
        out[name + "_n"] = cnt
    uniq, counts = np.unique(op, axis=0, return_counts=True)
    top = sorted(zip(counts.tolist(), uniq.tolist()), key=lambda t: (-t[0], -sum(t[1])))[:8]
    out["top"] = [(tuple(int(v) for v in c), int(cn)) for cn, c in top]
    red_mask = (op[:, 0] > op[:, 1] + 25) & (op[:, 0] > op[:, 2] + 25)
    reds = op[red_mask]
    out["red"] = {"count": int(len(reds)),
                  "mean": tuple(int(round(v)) for v in reds.mean(axis=0)) if len(reds) else None,
                  "bright": tuple(int(v) for v in reds[np.argmax(0.299 * reds[:, 0] + 0.587 * reds[:, 1] + 0.114 * reds[:, 2])]) if len(reds) else None}
    return out


def report_sample(smp):
    u"""把「统计出主色/亮部/暗部」这一步打印出来（这是用户明确要求的一步）。"""
    rel = os.path.relpath(smp["path"], PROJ)
    print(u"  == 采样 %s（%dx%d %s）==" % (rel, smp["size"][0], smp["size"][1], smp["mode"]))
    print(u"     不透明像素 %d；颜色数 %d；平均色 %s" % (smp["opaque"], smp["colors"], _hexs(smp["mean"])))
    for name, cn in ((u"暗部", "dark"), (u"中部", "mid"), (u"亮部", "bright")):
        print(u"     %s 主色 %s x%-4d 均值 %s" % (name, _hexs(smp[cn]), smp[cn + "_n"], _hexs(smp[cn + "_mean"])))
    print(u"     前 8 主色：%s" % u" / ".join(u"%s x%d" % (_hexs(c), cn) for c, cn in smp["top"]))


def ensure_sep(light, body, dark, min_sep=20.0, max_mix=0.40):
    u"""保证「亮 / 中 / 暗」在 16×16 上分得开：不够就往白/往黑混，混多少会打印出来。"""
    notes = []
    t = 0.0
    while _lum(light) - _lum(body) < min_sep and t < max_mix:
        t = round(t + 0.06, 2)
        light = _mix(light, (255, 255, 255), 0.06)
    if t > 0:
        notes.append(u"亮部往白混 %.0f%%（拉开与中部的亮度差）" % (t * 100))
    t = 0.0
    while _lum(body) - _lum(dark) < min_sep and t < max_mix:
        t = round(t + 0.06, 2)
        dark = _mix(dark, (0, 0, 0), 0.06)
    if t > 0:
        notes.append(u"暗部往黑混 %.0f%%（拉开与中部的亮度差）" % (t * 100))
    return light, body, dark, notes


def metal_palette(smp, stone_mid_lum):
    u"""由采样结果推出一支矿斑色：亮 / 中 / 暗 / 高光 / 最深。

    全部来自采样的三个主色（或它们的线性混合）。两条"看得见"的保底（都会打印）：
      · 亮/中/暗 之间亮度差不够 ⇒ 往白/往黑混到够；
      · **灰色金属**（铝/银/钨）的中部跟石头底明度挨得太近 ⇒ 往它自己采样到的亮端或暗端挪，
        挪 ≥22 才停（带色的金属不需要，色相本身就分得开）。
    """
    light, body, dark = smp["bright"], smp["mid"], smp["dark"]
    light, body, dark, notes = ensure_sep(light, body, dark)
    chroma = max(body) - min(body)
    if chroma < 40 and abs(_lum(body) - stone_mid_lum) < 22:
        toward_light = abs(_lum(light) - stone_mid_lum) >= abs(_lum(dark) - stone_mid_lum)
        goal = light if toward_light else dark
        t = 0.0
        while abs(_lum(body) - stone_mid_lum) < 22 and t < 0.54:
            t = round(t + 0.06, 2)
            body = _mix(body, goal, 0.06)
        notes.append(u"中部往%s混 %.0f%%（灰金属跟石头底明度只差 %.0f，挪开 ≥22 才看得见）"
                     % (u"亮部" if toward_light else u"暗部", t * 100,
                        abs(_lum(smp["mid"]) - stone_mid_lum)))
    if _lum(dark) > stone_mid_lum - 22:
        t = 0.0
        while _lum(dark) > stone_mid_lum - 22 and t < 0.45:
            t = round(t + 0.06, 2)
            dark = _mix(dark, (0, 0, 0), 0.06)
        notes.append(u"暗部再往黑混 %.0f%%（压到石头底明度以下，保证描边看得见）" % (t * 100))
    spec = _mix(light, (255, 255, 255), 0.22)
    deep = _mix(dark, (0, 0, 0), 0.18)
    for a, b, label in ((light, body, u"亮/中"), (body, dark, u"中/暗")):
        if _lum(a) - _lum(b) < 18:
            notes.append(u"[注意] %s 亮度差只剩 %.0f，可能发糊" % (label, _lum(a) - _lum(b)))
    pal = dict(light=light, body=body, dark=dark, spec=spec, deep=deep, notes=notes,
               src=(smp["bright"], smp["mid"], smp["dark"]))
    return pal


def red_family(smp):
    u"""磁铁块的「磁极红」。

    先看 `magnet.png` 里到底有没有**能用的**红（R > G+25 且 R > B+25 的像素 ≥12 个，且饱和度 ≥0.40）：
    有就用它的色；没有（实测 magnet.png 里只有 9 个发暗发灰的红像素 #6E4B4F，S=0.28，
    压在深灰铁底上根本看不出来）就按磁铁漆的常见红调制 ——
    **这一支是唯一不来自物品的颜色**，会在打印里明确标注。
    """
    reds = smp["red"]
    usable = reds["count"] >= 12 and reds["mean"] is not None \
        and _hsv(reds["mean"])[1] >= 0.40
    if usable:
        body = reds["mean"]
        src = u"取自 magnet.png 的红像素（%d 个，均值 %s，S=%.2f）" \
              % (reds["count"], _hexs(body), _hsv(body)[1])
    else:
        body = _from_hsv(0.998, 0.80, 0.62)
        why = (u"只有 %d 个红像素，均值 %s（S=%.2f）" % (reds["count"], _hexs(reds["mean"]), _hsv(reds["mean"])[1])
               if reds["mean"] is not None else u"一个红像素都没有")
        src = u"**不来自物品**：magnet.png 里%s，压不到深灰铁底上 ⇒ 按磁铁漆的红调制 H=0.998 S=0.80 V=0.62" % why
    h, s, v = _hsv(body)
    s = max(s, 0.55)
    light = _from_hsv(h, s * 0.86, min(1.0, v + 0.20))
    dark = _from_hsv(h, min(1.0, s * 1.06), max(0.0, v - 0.24))
    spec = _mix(light, (255, 255, 255), 0.30)
    deep = _mix(dark, (0, 0, 0), 0.30)
    return dict(light=light, body=body, dark=dark, spec=spec, deep=deep, notes=[], src=(light, body, dark),
                origin=src)


# ================================================================= 画
def _value_noise(rng, cell, size=16):
    u"""一张 16×16 的平滑随机场（格点随机 + smoothstep 双线性插值）。

    为什么要它：**逐像素独立随机会画成棋盘格**（第一版就是这样，24 倍放大下一眼是"西洋跳棋"）。
    原版的石头底是有"块"的（同一灰度会连着 2~4 个像素成一小片），所以这里先铺一层低频噪声。
    """
    n = size // cell + 1
    g = [[rng.random() for _ in range(n + 1)] for _ in range(n + 1)]
    out = [[0.0] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            gx, gy = x / float(cell), y / float(cell)
            x0, y0 = int(gx), int(gy)
            tx, ty = gx - x0, gy - y0
            sx = tx * tx * (3 - 2 * tx)
            sy = ty * ty * (3 - 2 * ty)
            a = g[y0][x0] * (1 - sx) + g[y0][x0 + 1] * sx
            b = g[y0 + 1][x0] * (1 - sx) + g[y0 + 1][x0 + 1] * sx
            out[y][x] = a * (1 - sy) + b * sy
    return out


def _quantize(v, weights):
    u"""把 0~1 的值按权重分档（每一档占多少像素由 weights 决定）。"""
    total = float(sum(weights))
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w / total
        if v <= acc:
            return i
    return len(weights) - 1


def make_base(rng, kind):
    u"""石头底 / 铁底：5 级灰梯子（低频噪声分片 + 一点逐像素抖动）+ 2~3 处更暗/更亮的颗粒。

    返回 (grid, roles, specks)。
    """
    if kind == "iron":
        ladder, weights, c_dark, c_light = IRON_LADDER, IRON_W, IRON_DARK, IRON_LIGHT
    else:
        ladder, weights, c_dark, c_light = STONE_LADDER, STONE_W, STONE_DARK, STONE_LIGHT
    big = _value_noise(rng, 4)
    small = _value_noise(rng, 2)
    grid = [[None] * 16 for _ in range(16)]
    roles = [["."] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            # 三个尺度叠加：细颗粒（逐像素）撑住"石子"的质感，两级低频只负责把同色像素连成 2~4 像素的小片。
            # 只放低频 ⇒ 会变成大块迷彩；只放逐像素 ⇒ 会变成棋盘格（两种都试过，24 倍放大下一眼能分出来）。
            v = 0.45 * rng.random() + 0.30 * small[y][x] + 0.25 * big[y][x]
            grid[y][x] = ladder[_quantize(v, weights)]
    specks = []
    for _ in range(rng.randint(2, 3)):
        x, y = rng.randrange(16), rng.randrange(16)
        size = rng.randint(1, 3)
        dark = rng.random() < 0.5
        cells = [(x, y)]
        for _ in range(size - 1):
            px, py = cells[-1]
            cells.append(((px + rng.choice((-1, 0, 1))) % 16, (py + rng.choice((0, 1))) % 16))
        for (cx, cy) in cells:
            grid[cy][cx] = c_dark if dark else c_light
            roles[cy][cx] = ":" if dark else "+"
        specks.append((len(cells), u"暗" if dark else u"亮"))
    return grid, roles, specks


def _xf(shape, rot, flip):
    pts = list(shape)
    if flip:
        pts = [(-x, y) for x, y in pts]
    for _ in range(rot):
        pts = [(y, -x) for x, y in pts]
    mx = min(x for x, y in pts)
    my = min(y for x, y in pts)
    return tuple(sorted((x - mx, y - my) for x, y in pts))


def _fits(occ, cells):
    cs = set(cells)
    for (x, y) in cells:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 16 and 0 <= ny < 16 and occ[ny, nx] and (nx, ny) not in cs:
                    return False
    return True


def place_blobs(rng, target):
    u"""把 target 坨矿斑撒到 16×16 上：4×4 个锚格各挑一坨（撒得开），
    坨与坨之间保持 ≥1 像素的空隙（不粘连）。"""
    occ = np.zeros((16, 16), dtype=bool)
    blobs = []
    anchors = [(cx, cy) for cy in range(4) for cx in range(4)]
    rng.shuffle(anchors)
    for (cx, cy) in anchors:
        if len(blobs) >= target:
            break
        ax = cx * 4 + rng.randint(1, 2)
        ay = cy * 4 + rng.randint(1, 2)
        cand = []
        for _ in range(14):
            pts = _xf(SHAPES[rng.choices(range(len(SHAPES)), weights=SHAPE_W)[0]],
                      rng.randrange(4), rng.random() < 0.5)
            w = max(p[0] for p in pts) + 1
            h = max(p[1] for p in pts) + 1
            ox = min(max(ax - w // 2 + rng.randint(-1, 1), 0), 16 - w)
            oy = min(max(ay - h // 2 + rng.randint(-1, 1), 0), 16 - h)
            cand.append([(x + ox, y + oy) for x, y in pts])
        rng.shuffle(cand)
        for cells in cand:
            if _fits(occ, cells):
                for (x, y) in cells:
                    occ[y, x] = True
                blobs.append(cells)
                break
    return blobs


def paint_blob(grid, roles, cells, pal, chars, want_spec=True):
    u"""一坨矿斑：按「(x-minx)+(y-miny)」的对角线分级 ⇒ 左上亮、右下暗，中间是主体。

    分级用得**很吝啬**（亮只占对角线上最靠左上那一小截、暗只占最靠右下那一小截，其余都是中部）：
    16×16 上高光像素一多就会像撒了白芝麻（第一版就是这么翻的，预览图里一目了然）。
    高光 / 最深只给 ≥5 像素的大坨补，2~4 像素的小坨只走「亮-中-暗」三档。
    """
    minx = min(x for x, y in cells)
    miny = min(y for x, y in cells)
    denom = max(1, (max(x for x, y in cells) - minx) + (max(y for x, y in cells) - miny))
    scored = sorted(((x - minx) + (y - miny), x, y) for x, y in cells)
    for s, x, y in scored:
        t = s / float(denom)
        role = "light" if t <= 0.26 else ("dark" if t >= 0.74 else "body")
        grid[y][x] = pal[role]
        roles[y][x] = chars[role]
    if want_spec and len(cells) >= 5:
        _, x, y = scored[0]
        grid[y][x] = pal["spec"]
        roles[y][x] = chars["spec"]
        _, x, y = scored[-1]
        grid[y][x] = pal["deep"]
        roles[y][x] = chars["deep"]


def build_block(spec, pal, pal2=None):
    u"""画一张 16×16 ⇒ 返回 (rgb 网格, 角色网格, 记账 dict)。"""
    rng = random.Random(spec["seed"])
    grid, roles, specks = make_base(rng, spec["base"])
    blobs = place_blobs(rng, rng.randint(8, 10))
    for i, cells in enumerate(blobs):
        if pal2 is not None and i % 2 == 1:
            paint_blob(grid, roles, cells, pal2, ROLE_CHAR_B)      # 磁极（红/灰交替）
        else:
            paint_blob(grid, roles, cells, pal, ROLE_CHAR_A)
    info = dict(base=spec["base"], specks=specks,
                blobs=[len(b) for b in blobs],
                blob_px=sum(len(b) for b in blobs),
                ladder=len(IRON_LADDER if spec["base"] == "iron" else STONE_LADDER),
                used=set())
    for y in range(16):
        for x in range(16):
            info["used"].add(grid[y][x])
    return grid, roles, info


def to_rgba(grid):
    arr = np.zeros((16, 16, 4), dtype=np.uint8)
    for y in range(16):
        for x in range(16):
            r, g, b = grid[y][x]
            arr[y, x] = (r, g, b, 255)
    return arr


# ================================================================= 自检
def png_head(path):
    with open(path, "rb") as fh:
        b = fh.read(33)
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(u"%s 不是 PNG" % path)
    w = int.from_bytes(b[16:20], "big")
    h = int.from_bytes(b[20:24], "big")
    return w, h, b[24], b[25], b[26], b[27], b[28]


def selfcheck(name, grid, roles, info):
    fails = []
    arr = to_rgba(grid)
    if arr.shape != (16, 16, 4):
        fails.append(u"尺寸/通道不对：%s" % (arr.shape,))
    if arr.dtype != np.uint8:
        fails.append(u"不是 8 位：%s" % arr.dtype)
    if int(arr[..., 3].min()) != 255 or int(arr[..., 3].max()) != 255:
        fails.append(u"alpha 不是全 255（min=%d max=%d）" % (arr[..., 3].min(), arr[..., 3].max()))
    n_blob = len(info["blobs"])
    if not (6 <= n_blob <= 10):
        fails.append(u"矿斑坨数 %d 不在 6~10" % n_blob)
    for i, n in enumerate(info["blobs"]):
        if not (2 <= n <= 5):
            fails.append(u"第 %d 坨是 %d 像素，不在 2~5" % (i + 1, n))
    px = arr[..., :3].reshape(-1, 3)
    uniq = np.unique(px, axis=0)
    print(u"  -- %s --" % name)
    print(u"     规格：%dx%d / 8 位 / RGBA / alpha 全 255 %s"
          % (arr.shape[1], arr.shape[0], u"OK" if not fails else u"FAIL"))
    print(u"     颜色数 %d；平均色 %s" % (len(uniq), _hexs(tuple(int(v) for v in px.mean(axis=0)))))
    print(u"     底：%s（%d 色阶 + %d 处颗粒：%s）；矿斑 %d 坨共 %d 像素（%s）"
          % (u"深灰铁底" if info["base"] == "iron" else u"石头底", info["ladder"], len(info["specks"]),
             u"、".join(u"%s%dpx" % (a, b) for b, a in info["specks"]),
             n_blob, info["blob_px"], u"+".join(str(v) for v in info["blobs"])))
    print(u"     目标颜色（%d 种，去重后）：%s"
          % (len(info["used"]), u" ".join(_hexs(c) for c in sorted(info["used"], key=_lum))))
    print(u"     字符画：")
    for row in roles:
        print(u"       " + u"".join(row))
    return fails


# ================================================================= 落盘
def write_json(path, obj):
    txt = json.dumps(obj, indent=2, ensure_ascii=False) + u"\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    return len(txt.encode("utf-8"))


def write_assets(bid, rgba):
    png = os.path.join(TEX_BLOCK, bid + u".png")
    Image.fromarray(rgba, mode="RGBA").save(png, format="PNG", optimize=False)
    made = [png]
    made.append(os.path.join(DIR_BLOCKSTATE, bid + u".json"))
    write_json(made[-1], {"variants": {"": {"model": u"%s:block/%s" % (NS, bid)}}})
    made.append(os.path.join(DIR_MODEL_BLOCK, bid + u".json"))
    write_json(made[-1], {"parent": "minecraft:block/cube_all",
                          "textures": {"all": u"%s:block/%s" % (NS, bid)}})
    made.append(os.path.join(DIR_MODEL_ITEM, bid + u".json"))
    write_json(made[-1], {"parent": u"%s:block/%s" % (NS, bid)})
    return made


def preview(images, path, scale=12, gap=4):
    w = len(images) * (16 * scale + gap) + gap
    h = 16 * scale + 2 * gap
    canvas = Image.new("RGBA", (w, h), (32, 34, 38, 255))
    for i, im in enumerate(images):
        big = im.resize((16 * scale, 16 * scale), Image.NEAREST)
        canvas.paste(big, (gap + i * (16 * scale + gap), gap))
    canvas.save(path)
    return path


# ================================================================= main
def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help=u"真写 PNG + JSON")
    ap.add_argument("--preview", default=None, help=u"额外写一张放大对比图（给人眼看）")
    args = ap.parse_args(argv)

    stone_mid_lum = _lum(STONE_LADDER[3])
    print(u"== ① 采样 7 张物品贴图（Pillow 真解码 + numpy 统计）==")
    samples = {}
    for spec in BLOCKS:
        p = os.path.join(TEX_ITEM, spec["item"])
        if not os.path.exists(p):
            raise SystemExit(u"采样源不存在：%s" % p)
        smp = sample_item(p)
        report_sample(smp)
        samples[spec["id"]] = smp

    print(u"")
    print(u"== ② 由采样结果推矿斑色（亮/中/暗 全部来自上面的采样值）==")
    pals = {}
    for spec in BLOCKS:
        bid, smp = spec["id"], samples[spec["id"]]
        pal = metal_palette(smp, stone_mid_lum)
        pals[bid] = pal
        print(u"  %s：" % bid)
        print(u"     采样 ⇒ 亮 %s / 中 %s / 暗 %s" % tuple(_hexs(c) for c in pal["src"]))
        print(u"     用色 ⇒ 亮 %s / 中 %s / 暗 %s / 高光 %s / 最深 %s"
              % (_hexs(pal["light"]), _hexs(pal["body"]), _hexs(pal["dark"]),
                 _hexs(pal["spec"]), _hexs(pal["deep"])))
        if pal["notes"]:
            print(u"     调整：%s" % u"；".join(pal["notes"]))
        else:
            print(u"     调整：无（采样值直接可用）")
        if spec["poles"]:
            red = red_family(smp)
            pals[bid + "#red"] = red
            print(u"     磁极红来源：%s" % red["origin"])
            print(u"     磁极红用色 ⇒ 亮 %s / 中 %s / 暗 %s / 高光 %s / 最深 %s"
                  % (_hexs(red["light"]), _hexs(red["body"]), _hexs(red["dark"]),
                     _hexs(red["spec"]), _hexs(red["deep"])))

    print(u"")
    print(u"== ③ 画 + 自检（不落盘也跑）==")
    print(u"   字符画图例：" + u"  ".join(u"%s=%s" % (k, v) for k, v in sorted(LEGEND.items())))
    fails = []
    images = []
    results = []
    for spec in BLOCKS:
        bid = spec["id"]
        grid, roles, info = build_block(spec, pals[bid], pals.get(bid + "#red"))
        fails += selfcheck(bid, grid, roles, info)
        images.append(Image.fromarray(to_rgba(grid), mode="RGBA"))
        results.append((bid, grid))

    print(u"")
    if fails:
        print(u"== ④ 自检：%d 条不过 ==" % len(fails))
        for f in fails:
            print(u"   FAIL %s" % f)
    else:
        print(u"== ④ 自检：全部通过（尺寸 16×16 / 8 位 / RGBA / alpha 全 255 / 坨数 6~10 / 每坨 2~5）==")

    if args.preview:
        preview(images, args.preview)
        print(u"预览图（放大 12 倍，7 张并排）：%s" % args.preview)

    if args.write:
        if fails:
            raise SystemExit(u"自检没过，不落盘")
        print(u"")
        print(u"== ⑤ 落盘 ==")
        for (bid, grid) in results:
            made = write_assets(bid, to_rgba(grid))
            for p in made:
                print(u"   %s" % os.path.relpath(p, PROJ))
        print(u"")
        print(u"  回读 PNG 头（宽/高/位深/色彩类型/压缩/过滤/隔行）：")
        for (bid, _g) in results:
            p = os.path.join(TEX_BLOCK, bid + u".png")
            w, h, depth, ctype, comp, filt, inter = png_head(p)
            with Image.open(p) as im:
                arr = np.asarray(im.convert("RGBA"))
            ok = (w, h, depth, ctype) == (16, 16, 8, 6) and int(arr[..., 3].min()) == 255
            print(u"   %-24s %dx%d d%d t%d c%d f%d i%d alpha_min=%d %s"
                  % (bid + u".png", w, h, depth, ctype, comp, filt, inter,
                     int(arr[..., 3].min()), u"OK" if ok else u"FAIL"))
        print(u"")
        print(u"  回读 JSON（3 份里挑 1 份逐字打印，证格式与模板一致）：")
        with open(os.path.join(DIR_MODEL_BLOCK, u"raw_silver_block.json"), encoding="utf-8") as fh:
            print(u"   " + fh.read().replace(u"\n", u"\n   ").rstrip())
    else:
        print(u"")
        print(u"（加 --write 才落盘；本轮只打印）")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
