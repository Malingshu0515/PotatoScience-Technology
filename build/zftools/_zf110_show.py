# -*- coding: utf-8 -*-
"""_zf110_show.py —— 直接读盘上成品出复核图（只读 + 写一张预览 PNG）

上排：这轮上线/改指向的四张
下排：油桶 —— 旧版（ZF87）/ 新版（ZF110，现在在用的）
"""
import io
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"
OLD_OIL = r"E:\PotatoST\build\zftools\_zf110_old_oil.png"
OUT = r"E:\PotatoST\build\zftools\_zf110_show.png"


def write_png_rgba(path, w, h, rgba):
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4])

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                              + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                              + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def sheet(rows, zoom=26, pad=12):
    tile = 16 * zoom
    cols = max(len(r) for r in rows)
    W = pad + cols * (tile + pad)
    H = pad + len(rows) * (tile + pad)
    buf = bytearray(W * H * 4)
    for i in range(W * H):
        x, y = i % W, i // W
        v = 58 if ((x // 10) + (y // 10)) % 2 == 0 else 92
        buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))
    for ri, row in enumerate(rows):
        for ci, (_, w, h, rgba) in enumerate(row):
            ox, oy = pad + ci * (tile + pad), pad + ri * (tile + pad)
            for y in range(h * zoom):
                for x in range(w * zoom):
                    si = ((y // zoom) * w + (x // zoom)) * 4
                    a = rgba[si + 3]
                    if a == 0:
                        continue
                    di = ((oy + y) * W + (ox + x)) * 4
                    if a == 255:
                        buf[di:di + 3] = bytes(rgba[si:si + 3])
                    else:
                        for c in range(3):
                            buf[di + c] = (rgba[si + c] * a + buf[di + c] * (255 - a)) // 255
                    buf[di + 3] = 255
    return W, H, buf


def load(p):
    w, h, rgba = read_png(p)
    return w, h, rgba


top = [("helm",) + load(os.path.join(TEX, "star_steel_helmet.png")),
       ("LiCO3",) + load(os.path.join(TEX, "lithium_carbonate.png")),
       ("NaCl",) + load(os.path.join(TEX, "sodium_chloride.png")),
       ("sulfur",) + load(os.path.join(TEX, "sulfur.png"))]
bottom = [("oil OLD",) + load(OLD_OIL),
          ("oil NEW",) + load(os.path.join(TEX, "oil_bucket.png"))]

for label, w, h, rgba in top + bottom:
    op = sum(1 for i in range(w * h) if rgba[i * 4 + 3] == 255)
    print("  %-9s %dx%d  不透明 %3d" % (label, w, h, op))

W, H, buf = sheet([top, bottom])
write_png_rgba(OUT, W, H, buf)
print("\n预览: %s (%dx%d, %d B)" % (OUT, W, H, os.path.getsize(OUT)))
