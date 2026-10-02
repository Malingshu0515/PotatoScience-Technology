# -*- coding: utf-8 -*-
"""_zf150_look.py —— 四种「粒」素材体检（只读 + 写报告）

用户原话：「嗯嗯放素材了几张图 其中四种粒你先注册一下 配方就是原版的
（对应锭合成9个粒 9个粒合成1个锭 记得加标签兼容别的mod）重复一遍！现在是0.12版本」
"""
import hashlib
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

U = r"E:\PotatoST\build\用户素材"
T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"
OUT = r"E:\PotatoST\build\zftools\_zf150_look.txt"
RAMP = " .:-=+*#%@"

# 素材 -> 物品 id -> 对应锭
JOBS = [(u"铝粒_001.png", "aluminum_nugget", "aluminum_ingot"),
        (u"银粒_001.png", "silver_nugget", "silver_ingot"),
        (u"钴粒_001.png", "cobalt_nugget", "cobalt_ingot"),
        (u"镍粒_001.png", "nickel_nugget", "nickel_ingot")]

lines = []


def say(s=u""):
    lines.append(s)
    print(s)


for src, item, ingot in JOBS:
    p = os.path.join(U, src)
    say(u"=" * 74)
    if not os.path.exists(p):
        say(u"  !! 找不到 %s" % src)
        continue
    blob = open(p, "rb").read()
    say(u"%s   →   textures/item/%s.png   （对应锭 %s）" % (src, item, ingot))
    say(u"  %d B   sha1 %s   真 PNG = %s"
        % (len(blob), hashlib.sha1(blob).hexdigest(), blob[:8] == b"\x89PNG\r\n\x1a\n"))
    w, h, rgba = read_png(p)
    a = np.array(rgba, dtype=np.uint8).reshape(h, w, 4)
    op = int((a[:, :, 3] == 255).sum())
    tr = int((a[:, :, 3] == 0).sum())
    cols = {}
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] == 0:
                continue
            k = tuple(int(v) for v in a[y, x, :3])
            cols[k] = cols.get(k, 0) + 1
    # ⚠ 用布尔掩码取出来是 (N, 4) 的二维数组 —— 第一版写成 [:, :, :3] 直接 IndexError
    mean = tuple(int(v) for v in a[a[:, :, 3] == 255][:, :3].mean(axis=0)) if op else (0, 0, 0)
    say(u"  %dx%d  位深 %d  色彩类型 %d" % (w, h, blob[24], blob[25]))
    say(u"  alpha：不透明 %d / 全透明 %d / 半透明 %d" % (op, tr, w * h - op - tr))
    say(u"  颜色数 %d   平均色 #%02x%02x%02x" % (len(cols), *mean))
    say(u"  主色 top5: " + ", ".join("#%02x%02x%02x x%d" % (k[0], k[1], k[2], v)
                                    for k, v in sorted(cols.items(), key=lambda kv: -kv[1])[:5]))
    say(u"  字符画：")
    lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    for y in range(h):
        row = []
        for x in range(w):
            row.append(u" " if a[y, x, 3] == 0 else
                       RAMP[min(len(RAMP) - 1, int(lum[y, x] / 255.0 * (len(RAMP) - 1)))])
        say(u"    |" + u"".join(row) + u"|")
    # 对照：对应锭的新图平均色（判断色调是否同族）
    q = os.path.join(T, ingot + ".png")
    if os.path.exists(q):
        w2, h2, r2 = read_png(q)
        a2 = np.array(r2, dtype=np.uint8).reshape(h2, w2, 4)
        m2 = a2[:, :, 3] == 255
        mean2 = tuple(int(v) for v in a2[m2][:, :3].mean(axis=0)) if m2.any() else (0, 0, 0)
        say(u"  ── 对应锭 %s：%dx%d  平均色 #%02x%02x%02x   （粒与锭色调同族？Δ=%d）"
            % (ingot, w2, h2, *mean2,
               int(sum((mean[i] - mean2[i]) ** 2 for i in range(3)) ** 0.5)))
    say()

say(u"=" * 74)
say(u"== 工程里是否已有这些物品/贴图 ==")
for src, item, ingot in JOBS:
    q = os.path.join(T, item + ".png")
    say(u"  %-18s 贴图：%s" % (item, u"已存在！" if os.path.exists(q) else u"（没有，要新建）"))

open(OUT, "w", encoding="utf-8").write(u"\n".join(lines))
print(u"\n[报告] %s" % OUT)
