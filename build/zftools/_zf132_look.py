# -*- coding: utf-8 -*-
"""_zf132_look.py —— 看清三张流体贴图的画面结构（只读）

做动画之前必须知道"这张图有没有可动的纹理"：
  · 如果是**带噪点/斑纹**的（像原版水那种抖动），平移一像素就能看出流动；
  · 如果是**纯平色**，平移等于没动 —— 那就得**合成**波纹，不能硬平移。
顺便量：帧内不同色数、行/列自相关（判断有没有周期性纹理可循）。
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
RAMP = " .:-=+*#%@"
FILES = ["diesel_still.png", "gasoline_still.png", "crude_oil_still.png"]

for f in FILES:
    p = os.path.join(T, f)
    print("=" * 66)
    w, h, rgba = read_png(p)
    a = np.array(rgba, dtype=np.uint8).reshape(h, w, 4)
    rgb = a[:, :, :3].astype(np.int16)
    alpha = a[:, :, 3]
    print(u"%s  %dx%d" % (f, w, h))
    print(u"  alpha 取值: %s" % sorted(set(alpha.flatten().tolist()))[:6])
    cols = {}
    for y in range(h):
        for x in range(w):
            k = tuple(int(v) for v in a[y, x, :3])
            cols[k] = cols.get(k, 0) + 1
    print(u"  颜色数 %d   前 8 种: %s" % (len(cols), sorted(cols.items(), key=lambda kv: -kv[1])[:8]))
    lum = (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2])
    print(u"  亮度 min %.1f max %.1f std %.2f  -> %s"
          % (lum.min(), lum.max(), lum.std(),
             u"有明显纹理" if lum.std() > 3 else u"接近平色（平移看不出来！）"))
    print(u"  灰阶图:")
    for y in range(h):
        print(u"    |" + "".join(RAMP[min(len(RAMP) - 1, int(lum[y, x] / 255.0 * (len(RAMP) - 1)))]
                               for x in range(w)) + u"|")
    # 通道均值（判断色调）
    print(u"  RGB 均值 %s" % [round(float(a[:, :, c].mean()), 1) for c in range(3)])
    # 行/列自相关：看有没有可平移的周期结构
    g = lum - lum.mean()
    def ac(sig):
        s = float((sig * sig).sum())
        if s <= 0:
            return [0.0] * 5
        out = []
        for k in (0, 1, 2, 4, 8):
            if k == 0:
                out.append(1.0)
            elif len(sig) > k:
                out.append(round(float((sig[:-k] * sig[k:]).sum() / s), 3))
            else:
                out.append(0.0)
        return out
    print(u"  行内自相关(滞后0/1/2/4/8): %s" % ac(g[8]))
    print(u"  列内自相关(滞后0/1/2/4/8): %s" % ac(g[:, 8]))
