# -*- coding: utf-8 -*-
"""_zf136_look.py —— 看清 `星璨钢重置.png` 是什么（只读 + 写报告）

用户原话：「星璨钢换个材质 放素材里了」——"星璨钢"在工程里对应 **8 件东西**：
  6 件物品贴图（斧 / 头盔 / 胸甲 / 护腿 / 靴子 / 锭）
+ 2 张盔甲层贴图（`models/armor/star_steel_layer_1|2.png`）。
所以先要搞清这张新图是**单件**还是**图集**（含多件），再决定怎么落。
"""
import hashlib
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

SRC = r"E:\PotatoST\build\用户素材\星璨钢重置.png"
A = r"E:\PotatoST\src\main\resources\assets\potato_s_t"
OUT = r"E:\PotatoST\build\zftools\_zf136_look.txt"
RAMP = " .:-=+*#%@"

lines = []


def say(s=u""):
    lines.append(s)
    print(s)


blob = open(SRC, "rb").read()
say(u"文件 %s" % os.path.basename(SRC))
say(u"  %d B   sha1 %s" % (len(blob), hashlib.sha1(blob).hexdigest()))
say(u"  真 PNG = %s" % (blob[:8] == b"\x89PNG\r\n\x1a\n"))
w, h, rgba = read_png(SRC)
a = np.array(rgba, dtype=np.uint8).reshape(h, w, 4)
say(u"  %dx%d  位深 %d  色彩类型 %d" % (w, h, blob[24], blob[25]))
op = int((a[:, :, 3] == 255).sum())
tr = int((a[:, :, 3] == 0).sum())
say(u"  alpha：不透明 %d / 全透明 %d / 半透明 %d" % (op, tr, w * h - op - tr))
cols = {}
for y in range(h):
    for x in range(w):
        if a[y, x, 3] == 0:
            continue
        k = tuple(int(v) for v in a[y, x, :3])
        cols[k] = cols.get(k, 0) + 1
say(u"  颜色数 %d（不透明像素）" % len(cols))
say(u"  主色 top8: " + ", ".join("#%02x%02x%02x x%d" % (k[0], k[1], k[2], v)
                                 for k, v in sorted(cols.items(), key=lambda kv: -kv[1])[:8]))

say()
say(u"== 字符画（' .:-=+*#%@'，空格 = 全透明）==")
lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
for y in range(h):
    row = []
    for x in range(w):
        if a[y, x, 3] == 0:
            row.append(u" ")
        else:
            row.append(RAMP[min(len(RAMP) - 1, int(lum[y, x] / 255.0 * (len(RAMP) - 1)))])
    say(u"  |" + u"".join(row) + u"|")

say()
say(u"== alpha 分块：它是单件还是图集？==")
# 逐 16x16 分块统计不透明像素，看是不是规整的网格
if w % 16 == 0 and h % 16 == 0:
    say(u"  尺寸是 16 的整数倍（%dx%d = %d 个 16x16 格）" % (w, h, (w // 16) * (h // 16)))
    for by in range(h // 16):
        cells = []
        for bx in range(w // 16):
            blk = a[by * 16:(by + 1) * 16, bx * 16:(bx + 1) * 16, 3]
            cells.append(int((blk == 255).sum()))
        say(u"    第 %d 行分块不透明像素数: %s" % (by, cells))
else:
    say(u"  尺寸不是 16 的整数倍 ⇒ 不是规整图集")

say()
say(u"== 对照：工程里现有的 8 件星璨钢贴图 ==")
for rel in (r"textures\item\star_steel_ingot.png", r"textures\item\star_steel_helmet.png",
            r"textures\item\star_steel_chestplate.png", r"textures\item\star_steel_leggings.png",
            r"textures\item\star_steel_boots.png", r"textures\item\star_steel_axe.png",
            r"textures\models\armor\star_steel_layer_1.png",
            r"textures\models\armor\star_steel_layer_2.png"):
    p = os.path.join(A, rel)
    if os.path.exists(p):
        b = open(p, "rb").read()
        cw, ch, _ = read_png(p)
        say(u"  %-46s %6d B  %dx%d" % (rel.replace("\\", "/"), len(b), cw, ch))
    else:
        say(u"  %-46s （缺）" % rel.replace("\\", "/"))

open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print(u"\n[报告] %s" % OUT)
