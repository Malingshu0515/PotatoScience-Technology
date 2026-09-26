# -*- coding: utf-8 -*-
u"""_zf140_intake.py —— ZF140 第一步：把用户给的黑洞 JPEG 收进来、量清楚

素材：用户 2026-xx 发在对话里的一张黑洞图（`build\\用户素材\\黑洞.jpg`，
690x1227 / 95484 B / sha256 c3466747…），原话：
「因为图片问题 天空盒一个点会看到明显的拉伸现象 解决不了 那正好在那个地方（四张星图都需要）
补个黑洞 图给你了 估计得抠一下 只剩黑洞本体 然后放到拉伸的地方」

这个脚本**只量不改**：报尺寸、亮度分布、黑洞本体的连通域与外接框、环半径、
并把原图缩一半出预览（档案 §6.8：先看图，再动手）。
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _zf140_img import write_rgb, read_png_np, flood, resize_bilinear  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RAW = os.path.join(ROOT, "build", "zftools", "_zf140_hole.bgra")
OUT = os.path.join(ROOT, "build", "zftools", "_zf140_out")
W, H, STRIDE = 690, 1227, 2760


def load_rgb():
    a = np.fromfile(RAW, dtype=np.uint8).reshape(H, STRIDE)[:, :W * 4].reshape(H, W, 4)
    return a[:, :, [2, 1, 0]].copy()          # BGRA -> RGB


def main():
    os.makedirs(OUT, exist_ok=True)
    rgb = load_rgb()
    lum = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2])
    print(u"素材 %dx%d" % (W, H))
    print(u"  亮度：min %.0f  p50 %.0f  p90 %.0f  p99 %.0f  p99.9 %.0f  max %.0f"
          % (lum.min(), np.percentile(lum, 50), np.percentile(lum, 90),
             np.percentile(lum, 99), np.percentile(lum, 99.9), lum.max()))
    for t in (8, 12, 16, 20, 25, 32, 40, 64):
        print(u"  亮度 > %-3d 的像素 %7d (%.2f%%)" % (t, int((lum > t).sum()),
                                                     100.0 * (lum > t).mean()))

    # 背景 = 从四条边上所有暗像素连出去的那一片；剩下的就是黑洞本体（含被环包住的阴影）
    dark = lum <= 20.0
    seeds = ([(0, x) for x in range(W)] + [(H - 1, x) for x in range(W)] +
             [(y, 0) for y in range(H)] + [(y, W - 1) for y in range(H)])
    outer = flood(dark, seeds)
    body = ~outer
    print(u"\n暗(<=20) 像素 %d，其中与边连通(外景) %d ⇒ 本体候选 %d (%.2f%%)"
          % (int(dark.sum()), int(outer.sum()), int(body.sum()), 100.0 * body.mean()))

    # 只留最大的连通域（星点会形成孤岛）
    lab = np.zeros((H, W), dtype=np.int32)
    sizes = []
    cur = 0
    ys, xs = np.nonzero(body)
    for i in range(len(ys)):
        y, x = int(ys[i]), int(xs[i])
        if lab[y, x]:
            continue
        cur += 1
        vis = flood(body & (lab == 0), [(y, x)])
        lab[vis] = cur
        sizes.append(int(vis.sum()))
    order = np.argsort(sizes)[::-1]
    print(u"本体候选连通域 %d 个，前 5 大：%s" % (len(sizes), [sizes[i] for i in order[:5]]))
    mainlab = order[0] + 1
    hole = lab == mainlab
    yy, xx = np.nonzero(hole)
    y0, y1, x0, x1 = yy.min(), yy.max(), xx.min(), xx.max()
    cy, cx = (y0 + y1) / 2.0, (x0 + x1) / 2.0
    print(u"最大连通域：bbox x[%d..%d] y[%d..%d]  尺寸 %dx%d  中心 (%.1f, %.1f)"
          % (x0, x1, y0, y1, x1 - x0 + 1, y1 - y0 + 1, cx, cy))
    print(u"   相对画布：中心 (%.3f, %.3f)，横向占 %.3f，纵向占 %.3f"
          % (cx / W, cy / H, (x1 - x0 + 1) / float(W), (y1 - y0 + 1) / float(H)))

    # 从中心往外扫，找"最亮的环"半径（光子环）
    gy, gx = np.mgrid[0:H, 0:W]
    r = np.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)
    for rr in range(0, 200, 10):
        m = (r >= rr) & (r < rr + 10)
        if m.sum() == 0:
            continue
        print(u"   环带 r=%3d..%3d  亮度均值 %6.2f  最大 %6.1f  亮(>60)占比 %.3f"
              % (rr, rr + 10, lum[m].mean(), lum[m].max(), (lum[m] > 60).mean()))

    meta = {"w": W, "h": H, "cx": cx, "cy": cy, "x0": int(x0), "x1": int(x1),
            "y0": int(y0), "y1": int(y1), "area": int(hole.sum())}
    with open(os.path.join(OUT, "intake.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    # 预览：一半尺寸 + 本体掩码（白=本体）
    half = resize_bilinear(rgb, W // 2, H // 2).astype(np.uint8)
    write_rgb(os.path.join(OUT, "src_half.png"), half)
    mk = np.zeros((H, W, 3), dtype=np.uint8)
    mk[hole] = (255, 255, 255)
    mk[~hole] = (rgb[~hole] * 0.25).astype(np.uint8)
    write_rgb(os.path.join(OUT, "mask_half.png"), resize_bilinear(mk, W // 2, H // 2).astype(np.uint8))
    print(u"\n预览 -> %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
