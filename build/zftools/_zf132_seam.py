# -*- coding: utf-8 -*-
"""_zf132_seam.py —— 正确的环绕判据：**环绕处的跳变 vs 帧内相邻的平均跳变**

前两版我都量错了东西，记一笔：
  ① 第一版看平铺预览图里"有边界" —— 那是我自己在格子之间留的 6px 空隙；
  ② 第二版量"同一帧左右边缘列的像素值差" —— 图内容不是纯色，边缘本来就不同，
     这个数**天然就该很大**，跟"能不能环绕平铺"毫无关系（量出来 5~7/16 全是噪声）。

正确的判据是**比较**，不是绝对值：
  · 环绕跳变（第 15 行 ↔ 第 0 行、第 15 列 ↔ 第 0 列）
  · 帧内相邻行/列的平均跳变（把"这张图本来有多不平滑"当基准）
若**环绕跳变 ≤ 帧内平均跳变**，说明接缝不比图内任何一处更突兀 ⇒ 看不出接缝。
"""
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
NAMES = ["diesel_still", "diesel_flow", "gasoline_still",
         "gasoline_flow", "crude_oil_still", "crude_oil_flow"]

print(u"环绕跳变 对比 帧内平均跳变（越接近 1 越好；>2 就该怀疑接缝）")
print(u"  %-18s %8s %8s %6s   %8s %8s %6s" % ("贴图", "左右环绕", "列间均值", "比值",
                                              "上下环绕", "行间均值", "比值"))
bad = []
for n in NAMES:
    p = os.path.join(T, n + ".png")
    w, h, rgba = read_png(p)
    a = np.array(rgba, dtype=np.int16).reshape(h, w, 4)[:, :, :3]
    fh = 16
    nf = h // fh
    lr_ratios, tb_ratios = [], []
    for f in range(nf):
        fr = a[f * fh:(f + 1) * fh]
        # 左右环绕：第 15 列 ↔ 第 0 列
        wrap_lr = np.abs(fr[:, -1].astype(int) - fr[:, 0].astype(int)).mean()
        col_adj = np.abs(np.diff(fr.astype(int), axis=1)).mean()
        # 上下环绕：第 15 行 ↔ 第 0 行
        wrap_tb = np.abs(fr[-1].astype(int) - fr[0].astype(int)).mean()
        row_adj = np.abs(np.diff(fr.astype(int), axis=0)).mean()
        lr_ratios.append(wrap_lr / max(1e-6, col_adj))
        tb_ratios.append(wrap_tb / max(1e-6, row_adj))
    lr = float(np.mean(lr_ratios))
    tb = float(np.mean(tb_ratios))
    flag = u""
    if lr > 2.0:
        flag += u"  ← 左右可疑"
    if tb > 2.0:
        flag += u"  ← 上下可疑"
    if flag:
        bad.append((n, lr, tb))
    print(u"  %-18s %8.2f %8.2f %6.2f   %8.2f %8.2f %6.2f%s"
          % (n, 0, 0, lr, 0, 0, tb, flag))

print()
if bad:
    print(u"需要处理的：")
    for n, lr, tb in bad:
        print(u"  %s  左右 %.2f  上下 %.2f" % (n, lr, tb))
else:
    print(u"全部 ≤ 2.0：环绕处不比图内任何一处更突兀 ⇒ 看不出接缝")
