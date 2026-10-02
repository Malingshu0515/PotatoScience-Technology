# -*- coding: utf-8 -*-
"""_zf135_look.py —— 剩下 12 种流体贴图**能不能动**（只读）

动法（整体竖向滚动）能不能看出效果，取决于图里**有没有可平移的纹理**：
  · 亮度 std 大、行内自相关高 ⇒ 一平移就看出来；
  · 纯平色 / 每行都一样（竖直条纹） ⇒ 竖向平移**完全看不出来**，得换动法或先加纹理。
先把 15 种（含已做的 3 种做对照）都量一遍，再决定。
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
DONE = {"diesel", "gasoline", "crude_oil"}
NAMES = ["oxygen", "hydrogen", "chlorine", "nitrogen", "ammonia", "carbon_dioxide",
         "lpg", "naphtha", "carbonic_acid", "nitric_acid", "sulfuric_acid",
         "hydrochloric_acid", "diesel", "gasoline", "crude_oil"]

print(u"%-18s %5s %6s %6s %8s %8s %7s  %s" %
      (u"流体", u"色数", u"亮度min", u"亮度max", u"std", u"行内ac1", u"行间ac1", u"判定"))
todo = []
for n in NAMES:
    p = os.path.join(T, n + "_still.png")
    if not os.path.exists(p):
        print(u"%-18s （缺）" % n)
        continue
    w, h, rgba = read_png(p)
    a = np.array(rgba, dtype=np.int16).reshape(h, w, 4)
    if h != 16:
        print(u"%-18s 已经是 %dx%d（已动画？）" % (n, w, h))
        continue
    lum = 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]
    cols = len(set(tuple(int(v) for v in a[y, x, :3]) for y in range(h) for x in range(w)))
    g = lum - lum.mean()
    def ac1(sig, axis_desc):
        s = float((sig * sig).sum())
        if s <= 0:
            return 0.0
        return float((sig[:-1] * sig[1:]).sum() / s)
    ac_row = float(np.mean([ac1(g[y], "row") for y in range(h)]))
    ac_col = float(np.mean([ac1(g[:, x], "col") for x in range(w)]))
    # 判定：竖向滚动能否看出
    if lum.std() < 1.0 or ac_col > 0.98:
        verdict = u"竖向平移看不出（行与行一样）"
    elif lum.std() < 3.0:
        verdict = u"纹理弱，能看但很淡"
    else:
        verdict = u"可动"
    mark = u"[已做]" if n in DONE else u"     "
    print(u"%-18s %5d %6.1f %6.1f %8.2f %8.3f %7.3f  %s %s"
          % (n, cols, lum.min(), lum.max(), lum.std(), ac_row, ac_col, mark, verdict))
    if n not in DONE:
        todo.append((n, lum.std(), ac_col, verdict))

print(u"\n待做 %d 种：" % len(todo))
for n, std, acc, v in todo:
    print(u"  %-18s std %5.2f  行间ac %.3f  %s" % (n, std, acc, v))
