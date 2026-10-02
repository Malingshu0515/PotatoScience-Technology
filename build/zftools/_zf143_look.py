# -*- coding: utf-8 -*-
"""_zf143_look.py —— 四种锭的新图体检（只读 + 打报告）

用户原话：「把四种锭的图优化一下 我放用户素材里了」
四张：银锭 / 镍锭 / 铝锭 / 钴锭。
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
OUT = r"E:\PotatoST\build\zftools\_zf143_look.txt"
RAMP = " .:-=+*#%@"

JOBS = [(u"银锭.png", "silver_ingot"), (u"镍锭.png", "nickel_ingot"),
        (u"铝锭.png", "aluminum_ingot"), (u"钴锭.png", "cobalt_ingot")]

lines = []


def say(s=u""):
    lines.append(s)
    print(s)


for src, dst in JOBS:
    p = os.path.join(U, src)
    say(u"=" * 74)
    if not os.path.exists(p):
        say(u"  !! 找不到 %s" % src)
        continue
    blob = open(p, "rb").read()
    say(u"%s   →   textures/item/%s.png" % (src, dst))
    say(u"  %d B   sha1 %s   真 PNG = %s"
        % (len(blob), hashlib.sha1(blob).hexdigest(), blob[:8] == b"\x89PNG\r\n\x1a\n"))
    w, h, rgba = read_png(p)
    a = np.array(rgba, dtype=np.uint8).reshape(h, w, 4)
    op = int((a[:, :, 3] == 255).sum())
    tr = int((a[:, :, 3] == 0).sum())
    semi = w * h - op - tr
    cols = {}
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] == 0:
                continue
            k = tuple(int(v) for v in a[y, x, :3])
            cols[k] = cols.get(k, 0) + 1
    mean = tuple(int(v) for v in a[a[:, :, 3] == 255][:, :3].mean(axis=0)) if op else (0, 0, 0)
    say(u"  %dx%d  位深 %d  色彩类型 %d" % (w, h, blob[24], blob[25]))
    say(u"  alpha：不透明 %d / 全透明 %d / 半透明 %d" % (op, tr, semi))
    say(u"  颜色数 %d   平均色 #%02x%02x%02x" % (len(cols), *mean))
    say(u"  主色 top6: " + ", ".join("#%02x%02x%02x x%d" % (k[0], k[1], k[2], v)
                                    for k, v in sorted(cols.items(), key=lambda kv: -kv[1])[:6]))
    say(u"  字符画：")
    lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    for y in range(h):
        row = []
        for x in range(w):
            row.append(u" " if a[y, x, 3] == 0 else
                       RAMP[min(len(RAMP) - 1, int(lum[y, x] / 255.0 * (len(RAMP) - 1)))])
        say(u"    |" + u"".join(row) + u"|")
    # 现有那张
    q = os.path.join(T, dst + ".png")
    if os.path.exists(q):
        b2 = open(q, "rb").read()
        w2, h2, r2 = read_png(q)
        a2 = np.array(r2, dtype=np.uint8).reshape(h2, w2, 4)
        op2 = int((a2[:, :, 3] == 255).sum())
        cols2 = len(set(tuple(int(v) for v in a2[y, x, :3])
                        for y in range(h2) for x in range(w2) if a2[y, x, 3] == 255))
        say(u"  ── 现有 %s.png：%d B  %dx%d  不透明 %d  颜色数 %d  sha1 %s"
            % (dst, len(b2), w2, h2, op2, cols2, hashlib.sha1(b2).hexdigest()[:10]))
    else:
        say(u"  ── 现有 %s.png：（不存在）" % dst)
    say()

open(OUT, "w", encoding="utf-8").write(u"\n".join(lines))
print(u"\n[报告] %s" % OUT)
