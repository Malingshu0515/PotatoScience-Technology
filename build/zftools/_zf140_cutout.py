# -*- coding: utf-8 -*-
u"""_zf140_cutout.py —— ZF140 第二步：抠出黑洞本体，做成一张独立的天空贴图

用户原话：「估计得抠一下 只剩黑洞本体」。

做法（判据全部落在像素上，不靠"我觉得"）：
  1. **背景** = 亮度 <= 20 且**从画布四边连得出去**的那一片 ⇒ 剩下的就是本体
     （这个定义自带"填实"：被光环围住的阴影区连不到画布边，自动算本体 —— 正是我们要的，
     阴影必须是不透明的，否则极点会从黑洞里透出来）。
  2. 只留**最大连通域**（星点是孤岛，4238 个候选里第二大只有 765 px）。
  3. 边缘羽化：掩码做两次 3x3 箱型模糊再线性映射 -> 2~3 px 过渡（阈值处的辉光只有 ~8% 亮度，
     硬切本来也看不出来，羽化只是保险）。
  4. 以**阴影质心**为中心裁正方形（不是 bbox 中心：bbox 被横向拉长的吸积盘带偏，
     实测 (350.0,606.0) vs 阴影质心差 20+ px），边长取能装下本体还留余量。
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf140_img import blur3, crop_scale, write_rgb, write_rgba, flood, resize_bilinear  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RAW = os.path.join(ROOT, "build", "zftools", "_zf140_hole.bgra")
OUT = os.path.join(ROOT, "build", "zftools", "_zf140_out")
W, H, STRIDE = 690, 1227, 2760

DARK = 20.0          # "背景暗"的阈值（素材 p90=21，取 20 刚好把星云/星点挡在外面）
SIDE = 640           # 裁出来的正方形边长（源像素）

def load_rgb():
    a = np.fromfile(RAW, dtype=np.uint8).reshape(H, STRIDE)[:, :W * 4].reshape(H, W, 4)
    return a[:, :, [2, 1, 0]].copy()


def cutout(rgb, dark=DARK, smooth=0):
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    for _ in range(smooth):
        lum = blur3(lum)
    darkm = lum <= dark
    seeds = ([(0, x) for x in range(W)] + [(H - 1, x) for x in range(W)] +
             [(y, 0) for y in range(H)] + [(y, W - 1) for y in range(H)])
    outer = flood(darkm, seeds)
    cand = ~outer

    # 最大连通域
    lab = np.zeros((H, W), dtype=np.int32)
    sizes = []
    ys, xs = np.nonzero(cand)
    for i in range(len(ys)):
        y, x = int(ys[i]), int(xs[i])
        if lab[y, x]:
            continue
        vis = flood(cand & (lab == 0), [(y, x)])
        lab[vis] = len(sizes) + 1
        sizes.append(int(vis.sum()))
    body = lab == (int(np.argmax(sizes)) + 1)

    # 阴影质心 = 本体里"暗"的那一块（被环围住，连不到外面）=> 黑洞的光学中心
    shadow = body & darkm
    sy, sx = np.nonzero(shadow)
    cy, cx = float(sy.mean()), float(sx.mean())
    print(u"  本体 %d px，阴影 %d px，阴影质心 (%.1f, %.1f)" % (body.sum(), shadow.sum(), cx, cy))

    soft = blur3(blur3(body.astype(np.float32)))
    alpha = np.clip((soft - 0.35) / 0.30, 0.0, 1.0)
    return body, alpha, cx, cy


def main(argv):
    dark = DARK
    smooth = 0
    tag = ""
    if "--dark" in argv:
        dark = float(argv[argv.index("--dark") + 1])
        tag = "_d%d" % int(dark)
    if "--smooth" in argv:
        smooth = int(argv[argv.index("--smooth") + 1])
        tag += "_s%d" % smooth
    os.makedirs(OUT, exist_ok=True)
    rgb = load_rgb()
    print(u"阈值 dark=%g smooth=%d" % (dark, smooth))
    body, alpha, cx, cy = cutout(rgb, dark, smooth)

    half = SIDE / 2.0
    x0, y0 = cx - half, cy - half
    print(u"  裁剪：中心 (%.1f,%.1f) 半边长 %.0f -> 源框 [%.0f,%.0f]x[%.0f,%.0f]"
          % (cx, cy, half, x0, x0 + SIDE, y0, y0 + SIDE))
    assert 0 <= x0 and x0 + SIDE <= W and 0 <= y0 and y0 + SIDE <= H, u"裁剪框出界"

    yy, xx = np.nonzero(body)
    dx = np.maximum(np.abs(xx - cx), np.abs(yy - cy))       # 切比雪夫距离 = 正方形半径
    print(u"  本体最远角距 %.1f px（占半个裁剪框的 %.3f）" % (dx.max(), dx.max() / half))
    for name, q in (("上半", yy < cy), ("下半", yy >= cy), ("左半", xx < cx), ("右半", xx >= cx)):
        if q.any():
            print(u"    %s：最远 %.1f px（%.3f）" % (name, dx[q].max(), dx[q].max() / half))

    # 不缩放，直接原像素裁出来（SIDE x SIDE）—— 一个字节都不重采样
    rgba = np.zeros((SIDE, SIDE, 4), dtype=np.uint8)
    ix0, iy0 = int(round(x0)), int(round(y0))
    rgba[:, :, :3] = rgb[iy0:iy0 + SIDE, ix0:ix0 + SIDE]
    a = (alpha[iy0:iy0 + SIDE, ix0:ix0 + SIDE] * 255.0 + 0.5).astype(np.uint8)
    rgba[:, :, 3] = a
    # 全透明处的 RGB 清零（否则 PNG 里留着没用的彩色噪声，白占体积也容易误导）
    rgba[a == 0, :3] = 0

    op = int((a == 255).sum())
    print(u"\n  成品 %dx%d：不透明 %d (%.1f%%)，全透明 %d (%.1f%%)，半透明 %d"
          % (SIDE, SIDE, op, 100.0 * op / (SIDE * SIDE), int((a == 0).sum()),
             100.0 * (a == 0).mean(), int(((a > 0) & (a < 255)).sum())))
    print(u"  中心像素 alpha=%d（极点会被它挡住才算数）" % a[SIDE // 2, SIDE // 2])
    assert op > 20000, u"不透明像素太少，抠图等于没抠出来"

    # 预览：棋盘底上的成品 + 十字准星（看图确认中心对不对）
    prev = np.zeros((SIDE, SIDE, 3), dtype=np.uint8)
    chk = (((np.mgrid[0:SIDE, 0:SIDE][0] // 16) + (np.mgrid[0:SIDE, 0:SIDE][1] // 16)) % 2)
    prev[:, :, 0] = np.where(chk == 0, 40, 90)
    prev[:, :, 1] = prev[:, :, 0]
    prev[:, :, 2] = prev[:, :, 0]
    af = (a.astype(np.float32) / 255.0)[:, :, None]
    prev = (rgba[:, :, :3] * af + prev * (1 - af)).astype(np.uint8)
    prev[SIDE // 2 - 1:SIDE // 2 + 2, :] = (0, 255, 0)
    prev[:, SIDE // 2 - 1:SIDE // 2 + 2] = (0, 255, 0)
    write_rgb(os.path.join(OUT, "cutout_check%s.png" % tag), prev)
    write_rgba(os.path.join(OUT, "black_hole%s.png" % tag), rgba)

    meta = {"side": SIDE, "cx": cx, "cy": cy, "dark": dark, "smooth": smooth,
            "opaque": op, "alpha0": int((a == 0).sum())}
    with open(os.path.join(OUT, "cutout%s.json" % tag), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(u"  -> %s" % os.path.join(OUT, "black_hole%s.png" % tag))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
