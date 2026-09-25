# -*- coding: utf-8 -*-
"""ZF33：把用户给的 6 张"金属块/装置"素材落成方块贴图。

用户原话：「发的这些图片 去掉001后缀 文件名即为id这几个先不加配方」
⇒ 文件名的中文就是 id（如 `高级金属块_001.png` → id/文件名 `高级金属块`），**本次不注册方块**。

尺寸处理：素材实测见打印（多为 160×160）。**160 不是 2 的幂**，直接当贴图用会被引擎缩放成糊的，
所以按 §6.8 的结论走**面积平均降采样到 16×16**（与板材同一套做法、同一个理由）。
若某张本来就是 16×16 或 32×32（2 的幂）则原样保留。

⚠ 通道顺序：WPF 的 `CopyPixels` 输出按 **BGRA32** 排（这一点在 ZF30 被文件名骗过一次，
   §4.23 记着）。所以这里读 `raw[i],raw[i+1],raw[i+2],raw[i+3]` = B,G,R,A，
   写 PNG 时**要换回 R,G,B**。本次不靠猜：脚本末尾会打印每张图的主色与冷暖统计，
   一眼能看出"橙色的是不是橙的"。
"""
import io
import os
import sys
import zipfile
from collections import Counter

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import write_png

SRC_DIR = r"E:\PotatoST\build\zftools\_block_imgs"
OUT = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"

NAMES = ["高级金属块", "加热装置", "耐热金属块", "散热装置", "稳定金属块", "一般金属块"]


def load_raw(path):
    """从 .webp 里直接解出裸像素：用 WPF 已导出的同名 .rgba（由 PowerShell 侧生成）。"""
    raw = io.open(path, "rb").read()
    n = len(raw) // 4
    side = int(n ** 0.5)
    if side * side != n:
        raise SystemExit("%s 不是正方形（%d 像素）" % (path, n))
    return side, raw


def average_downscale(raw, src_side, dst):
    """面积平均降采样；alpha 用 0..1 浮点累加后取整。"""
    step = src_side / float(dst)
    out = bytearray(dst * dst * 4)
    for ty in range(dst):
        y0, y1 = int(ty * step), max(int(ty * step) + 1, int((ty + 1) * step))
        for tx in range(dst):
            x0, x1 = int(tx * step), max(int(tx * step) + 1, int((tx + 1) * step))
            sr = sg = sb = sa = 0
            cnt = 0
            for y in range(y0, min(y1, src_side)):
                for x in range(x0, min(x1, src_side)):
                    i = (y * src_side + x) * 4
                    sb += raw[i]
                    sg += raw[i + 1]
                    sr += raw[i + 2]
                    sa += raw[i + 3]
                    cnt += 1
            o = (ty * dst + tx) * 4
            out[o] = sr // cnt
            out[o + 1] = sg // cnt
            out[o + 2] = sb // cnt
            out[o + 3] = sa // cnt
    return out


def stats(flat, label):
    px = [tuple(flat[i:i + 4]) for i in range(0, len(flat), 4)]
    op = [p for p in px if p[3] > 0]
    if not op:
        print("   %-14s 全透明？" % label)
        return
    r = sum(p[0] for p in op) / len(op)
    g = sum(p[1] for p in op) / len(op)
    b = sum(p[2] for p in op) / len(op)
    warm = sum(1 for p in op if p[0] > p[2] + 8)
    cool = sum(1 for p in op if p[2] > p[0] + 8)
    top = Counter(op).most_common(2)
    print("   %-14s 均色=(%3.0f,%3.0f,%3.0f) 暖=%3d 冷=%3d 主色=%s"
          % (label, r, g, b, warm, cool, top))


for name in NAMES:
    rgba_path = os.path.join(SRC_DIR, name + ".rgba")
    if not os.path.exists(rgba_path):
        print("[SKIP] %s：还没有导出 .rgba" % name)
        continue
    side, raw = load_raw(rgba_path)
    dst = 16 if side not in (16, 32) else side
    flat = average_downscale(raw, side, dst) if dst != side else bytearray(raw)
    out_path = os.path.join(OUT, name + ".png")
    write_png(out_path, dst, dst, flat)
    print("%-12s %3d→%-3d  %s  %d 字节" % (name, side, dst, out_path.split("\\")[-1], os.path.getsize(out_path)))
    stats(flat, "  落盘后")
