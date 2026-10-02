# -*- coding: utf-8 -*-
"""_zf136_diff.py —— 新图 vs 现有锭：**差异到底在哪**（只读 + 写对照 PNG）

IoU 0.985 说明掩码几乎重合，但"重合"可能是"只差几个像素"也可能是"整体一样但换色"。
把两者的 alpha 掩码逐像素 XOR 出来，再并排放大，一眼看清。
"""
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

SRC = r"E:\PotatoST\build\用户素材\星璨钢重置.png"
# ⚠ 用 zf136_pre 里的**旧图**比：上线之后"在用"已经是新图，拿它当旧图就成了自己比自己
OLD = r"E:\PotatoST\build\zftools\zf136_pre\star_steel_ingot.png"
OUT = r"E:\PotatoST\build\zftools\_zf136_diff.png"
Z = 20
PAD = 10


def wpng(path, w, h, buf):
    raw = b"".join(b"\x00" + bytes(buf[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def ch(t, p):
        return struct.pack(">I", len(p)) + t + p + struct.pack(">I", zlib.crc32(t + p) & 0xFFFFFFFF)

    open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                           + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


nw, nh, nr = read_png(SRC)
ow, oh, orr = read_png(OLD)
print(u"新图 %dx%d   旧图 %dx%d" % (nw, nh, ow, oh))

# 掩码逐像素比
diff = 0
for y in range(16):
    for x in range(16):
        na = nr[(y * 16 + x) * 4 + 3]
        oa = orr[(y * 16 + x) * 4 + 3]
        if (na == 255) != (oa == 255):
            diff += 1
print(u"alpha 掩码不同的像素数 = %d / 256  ⇒ %s"
      % (diff, u"形状完全一致" if diff == 0 else u"形状有 %d 处差异" % diff))

# 只在两边都不透明处比颜色
same = 0
tot = 0
sr = sg = sb = 0
for y in range(16):
    for x in range(16):
        i = (y * 16 + x) * 4
        if nr[i + 3] == 255 and orr[i + 3] == 255:
            tot += 1
            if tuple(nr[i:i + 3]) == tuple(orr[i:i + 3]):
                same += 1
            sr += nr[i] - orr[i]; sg += nr[i + 1] - orr[i + 1]; sb += nr[i + 2] - orr[i + 2]
print(u"共有的 %d 个不透明像素里，颜色逐字节相同的 = %d" % (tot, same))
if tot:
    print(u"平均色差（新 − 旧）：R %+.1f  G %+.1f  B %+.1f" % (sr / tot, sg / tot, sb / tot))

# 并排放大：旧 / 新 / 掩码差异
W = PAD * 2 + 3 * (16 * Z + PAD)
H = PAD * 2 + 16 * Z
buf = bytearray(W * H * 4)
for i in range(W * H):
    x, y = i % W, i // W
    v = 44 if ((x // 7) + (y // 7)) % 2 == 0 else 62
    buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))

panels = [(u"旧", orr), (u"新", nr)]
for pi, (label, px) in enumerate(panels):
    ox = PAD + pi * (16 * Z + PAD)
    for y in range(16):
        for x in range(16):
            i = (y * 16 + x) * 4
            a = px[i + 3]
            if a == 0:
                continue
            for dy in range(Z):
                base = (PAD + y * Z + dy) * W
                for dx in range(Z):
                    di = (base + ox + x * Z + dx) * 4
                    buf[di:di + 3] = bytes(px[i:i + 3])
                    buf[di + 3] = 255

# 第三格：差异图（绿=只在旧里有，红=只在新里有，灰=都有）
ox = PAD + 2 * (16 * Z + PAD)
for y in range(16):
    for x in range(16):
        i = (y * 16 + x) * 4
        na = nr[i + 3] == 255
        oa = orr[i + 3] == 255
        col = (60, 60, 60)
        if na and oa:
            col = (110, 110, 120)
        elif na and not oa:
            col = (230, 70, 70)
        elif oa and not na:
            col = (70, 220, 90)
        for dy in range(Z):
            base = (PAD + y * Z + dy) * W
            for dx in range(Z):
                di = (base + ox + x * Z + dx) * 4
                buf[di:di + 3] = bytes(col)
                buf[di + 3] = 255

wpng(OUT, W, H, buf)
print(u"\n对照图（左=旧 / 中=新 / 右=掩码差异 灰=都有 红=只新有 绿=只旧有）")
print(u"  %s (%dx%d)" % (OUT, W, H))
