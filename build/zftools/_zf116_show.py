# -*- coding: utf-8 -*-
u"""_zf116_show.py —— 星璨钢套装四件 + 待画的四件对照（只读 + 写一张预览 PNG）

上排：已上线的星璨钢四件（头盔 ZF110；胸甲/护腿/靴子 ZF116）
下排：仍在借原版铁套的钛合金四件（还没画）
"""
import io
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

TEXI = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"
OUT = r"E:\PotatoST\build\zftools\_zf116_show.png"


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


def sheet(rows, zoom=24, pad=12):
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
        for ci, (label, w, h, rgba) in enumerate(row):
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


def load(name):
    p = os.path.join(TEXI, name)
    if not os.path.exists(p):
        return None
    w, h, rgba = read_png(p)
    return (name.replace(".png", ""), w, h, rgba)


top = [load("star_steel_helmet.png"), load("star_steel_chestplate.png"),
       load("star_steel_leggings.png"), load("star_steel_boots.png")]
bottom = [load(n) for n in ("titanium_alloy_helmet.png", "titanium_alloy_chestplate.png",
                            "titanium_alloy_leggings.png", "titanium_alloy_boots.png")]

print(u"上排 = 星璨钢四件（本套已齐）")
for t in top:
    print(u"  %s" % (u"有 " + t[0] if t else u"缺"))
print(u"下排 = 钛合金四件（仍借原版铁套，还没画）")
for t in bottom:
    print(u"  %s" % (u"有 " + t[0] if t else u"缺（借原版）"))

rows = [[t for t in top if t]]
if any(bottom):
    rows.append([t for t in bottom if t])
W, H, buf = sheet(rows)
write_png_rgba(OUT, W, H, buf)
print(u"\n预览: %s (%dx%d, %d B)" % (OUT, W, H, os.path.getsize(OUT)))
