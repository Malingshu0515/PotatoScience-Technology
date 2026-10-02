# -*- coding: utf-8 -*-
"""_zf132_preview2.py —— 两张更贴近实机的复核图（只读 + 写 PNG）

大图看单帧（放大 26 倍，逐像素清楚）；
平铺图把一帧复制成 3×3 再放大 —— 检查**左右/上下环绕接缝**有没有硬边
（剪切是环绕取样的，理论上无缝，但"理论上"不算验过）。
"""
import io
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
OUT = r"E:\PotatoST\build\zftools\_zf132_preview2.png"
NAMES = ["diesel_still", "diesel_flow", "gasoline_still",
         "gasoline_flow", "crude_oil_still", "crude_oil_flow"]
Z = 20
PAD = 8


def wpng(path, w, h, buf):
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(buf[y * w * 4:(y + 1) * w * 4])

    def ch(t, p):
        return struct.pack(">I", len(p)) + t + p + struct.pack(">I", zlib.crc32(t + p) & 0xFFFFFFFF)

    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                              + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                              + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def frame_px(rgba, fw, fh, f):
    return [tuple(rgba[((f * fh + y) * fw + x) * 4:((f * fh + y) * fw + x) * 4 + 4])
            for y in range(fh) for x in range(fw)]


def put(buf, W, ox, oy, px, fw, fh, z):
    for y in range(fh):
        for x in range(fw):
            r, g, b, a = px[y * fw + x]
            if a == 0:
                continue
            for dy in range(z):
                base = (oy + y * z + dy) * W
                for dx in range(z):
                    di = (base + ox + x * z + dx) * 4
                    buf[di:di + 3] = bytes((r, g, b))
                    buf[di + 3] = 255


# 布局：每个流体一行三格 —— 单帧(帧8) / **零间距**平铺 3x3 / 单帧(帧24)
# ⚠ 平铺那一格**必须零间距**：第一版每格之间留了 6px 空隙，露出的深色底被我
#    看成了"接缝"，差点去改一个根本不存在的问题（§4.113 那一族的"先怀疑探针"）。
CELLW = 16 * Z
TILEZ = 6                      # 平铺用的较小放大，3x3 才放得下
TILEW = 16 * 3 * TILEZ
ROWH = max(CELLW, TILEW)
W = PAD + CELLW + PAD + TILEW + PAD + CELLW + PAD
H = PAD + len(NAMES) * (ROWH + PAD)

buf = bytearray(W * H * 4)
for i in range(W * H):
    x, y = i % W, i // W
    v = 48 if ((x // 6) + (y // 6)) % 2 == 0 else 70
    buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))

print(u"逐行：流体；列：帧8（放大20） / 帧8 平铺 3x3（放大6） / 帧24（放大20）")
for ri, n in enumerate(NAMES):
    p = os.path.join(T, n + ".png")
    w, h, rgba = read_png(p)
    fh = 16
    oy = PAD + ri * (ROWH + PAD)
    # 左：帧 8
    px8 = frame_px(rgba, w, fh, 8)
    put(buf, W, PAD, oy, px8, w, fh, Z)
    # 中：帧 8 平铺 3x3（**格与格之间不留空隙**，这样看到的任何边界都是真接缝）
    ox = PAD + CELLW + PAD
    for ty in range(3):
        for tx in range(3):
            for y in range(fh):
                for x in range(w):
                    r, g, b, a = px8[y * w + x]
                    if a == 0:
                        continue
                    for dy in range(TILEZ):
                        base = (oy + (ty * fh + y) * TILEZ + dy) * W
                        for dx in range(TILEZ):
                            di = (base + ox + (tx * w + x) * TILEZ + dx) * 4
                            buf[di:di + 3] = bytes((r, g, b))
                            buf[di + 3] = 255

    # 上边/左边各留一条 1 像素标记线之外不加任何 padding —— 边界像素直接相邻
    # 逐帧接缝量：帧内左右边缘列之差、上下边缘行之差（真接缝的客观判据）
    def edge_stats(px, fw, fh):
        lr = sum(1 for y in range(fh)
                 if px[y * fw + fw - 1][:3] != px[y * fw][:3])
        tb = sum(1 for x in range(fw)
                 if px[(fh - 1) * fw + x][:3] != px[x][:3])
        return lr, tb
    lr, tb = edge_stats(px8, w, fh)
    print(u"  %-18s 已排（帧8：左右边缘列差 %d/16，上下边缘行差 %d/16 —— 0 = 环绕无缝）"
          % (n, lr, tb))

    # 右：帧 24
    px24 = frame_px(rgba, w, fh, 24)
    put(buf, W, PAD + CELLW + PAD + TILEW + PAD, oy, px24, w, fh, Z)

wpng(OUT, W, H, buf)
print(u"\n复核图: %s (%dx%d)" % (OUT, W, H))
