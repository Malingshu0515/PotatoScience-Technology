# -*- coding: utf-8 -*-
"""MakePlateTexture.py —— 把「平滑渲染图」降采样成 MC 用的物品贴图（0.10 ZF16）

**为什么不能"取块中心像素"**：那条无损还原法（§8「像素画还原」）只对**最近邻整数倍放大的像素画**成立。
本次素材实测：160×160、261 种颜色、**任何网格尺寸都不是单一色块**
（10×10 只有 26.2% 单一、连 2×2 也只有 83.1%）—— 它是**把方块旋转 45° 后抗锯齿渲染**出来的，
根本没有可还原的像素网格（边缘每 10 行正好推进 10 像素 = 完美 45°，这就是旋转的证据）。
强行按块取样只会得到错位的锯齿。

**正确做法**：抗锯齿图要**面积平均**（box filter）降采样，再对 alpha 做阈值得到干净边缘。

输入用 `_plate_raw.bgra`（由 PowerShell 的 WPF 解码器从 webp 导出，见 §8；
`System.Drawing` 解不了 webp，会报 Out of memory）。

跑法：
    python build/zftools/MakePlateTexture.py --size 16 --out 目标.png
    python build/zftools/MakePlateTexture.py --size 16 --quantize 6 --out 目标.png
    python build/zftools/MakePlateTexture.py --size 32 --out 目标.png
"""
import argparse
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import write_png   # 复用现成的零依赖 PNG 写出器


def load_bgra(path):
    raw = io.open(path, "rb").read()
    if len(raw) % 4 != 0:
        raise SystemExit("[FAIL] {0} 不是 4 字节对齐的 BGRA".format(path))
    return raw


def average_downscale(raw, src_w, src_h, size):
    """面积平均降采样 → [(r,g,b,a_float)] 长度 size*size（alpha 用 0..1 浮点，便于阈值）。"""
    step = src_w / float(size)
    out = []
    for ty in range(size):
        y0, y1 = int(ty * step), int((ty + 1) * step)
        for tx in range(size):
            x0, x1 = int(tx * step), int((tx + 1) * step)
            n = 0
            sr = sg = sb = sa = 0.0
            for y in range(y0, y1):
                base = y * src_w * 4
                for x in range(x0, x1):
                    i = base + x * 4
                    b, g, r, a = raw[i], raw[i + 1], raw[i + 2], raw[i + 3]
                    # 预乘 alpha 再平均，否则透明区的黑边会把边缘染脏
                    w = a / 255.0
                    sr += r * w
                    sg += g * w
                    sb += b * w
                    sa += w
                    n += 1
            if sa <= 0.0:
                out.append((0, 0, 0, 0.0))
            else:
                out.append((sr / sa, sg / sa, sb / sa, sa / n))
    return out


def palette_of(raw, src_w, src_h, top):
    """取不透明像素里出现次数最多的 top 个颜色作为调色板。"""
    counts = {}
    for i in range(0, len(raw), 4):
        b, g, r, a = raw[i], raw[i + 1], raw[i + 2], raw[i + 3]
        if a < 128:
            continue
        counts[(r, g, b)] = counts.get((r, g, b), 0) + 1
    return [c for c, _n in sorted(counts.items(), key=lambda kv: -kv[1])[:top]]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=r"E:\PotatoST\build\zftools\_plate_raw.bgra")
    ap.add_argument("--src-size", type=int, default=160)
    ap.add_argument("--size", type=int, required=True, help="输出边长（MC 建议 16 / 32 / 64）")
    ap.add_argument("--alpha-threshold", type=float, default=0.5,
                    help="alpha 覆盖率低于此值的像素直接透明（干净边缘）")
    ap.add_argument("--quantize", type=int, default=0,
                    help=">0 则把颜色吸附到原图出现最多的 N 种颜色（更像像素画）")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    raw = load_bgra(args.raw)
    src_w = src_h = args.src_size
    if len(raw) != src_w * src_h * 4:
        raise SystemExit("[FAIL] 原始数据 {0} 字节，与 {1}x{1} 对不上".format(len(raw), src_w))

    pal = palette_of(raw, src_w, src_h, args.quantize) if args.quantize > 0 else None
    px = average_downscale(raw, src_w, src_h, args.size)

    rgba = bytearray(args.size * args.size * 4)
    kept = 0
    for i, (r, g, b, a) in enumerate(px):
        if a < args.alpha_threshold:
            continue
        ri, gi, bi = int(round(r)), int(round(g)), int(round(b))
        if pal:
            # 吸附到最近的调色板颜色（欧氏距离，权重用眼睛敏感的 2/4/3 近似）
            best, bd = None, None
            for (pr, pg, pb) in pal:
                d = 2 * (ri - pr) ** 2 + 4 * (gi - pg) ** 2 + 3 * (bi - pb) ** 2
                if bd is None or d < bd:
                    best, bd = (pr, pg, pb), d
            ri, gi, bi = best
        o = i * 4
        rgba[o], rgba[o + 1], rgba[o + 2], rgba[o + 3] = ri, gi, bi, 255
        kept += 1

    write_png(args.out, args.size, args.size, rgba)
    print("  {0}  {1}x{1}  不透明像素 {2}/{3}   调色板 {4}".format(
        args.out, args.size, kept, args.size * args.size,
        "无（保留平均色）" if not pal else "{0} 色 {1}".format(len(pal), pal)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
