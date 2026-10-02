# -*- coding: utf-8 -*-
u"""_zf117_preview.py —— 出「顶/底/侧」对照图，供用户确认映射（只读 + 写一张 PNG）

每行三格：候选「顶/底」贴图 → 现有「侧面」贴图 → 两者合起来的效果（等轴俯视示意）
"""
import io
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

USERART = r"E:\PotatoST\build\用户素材"
TEXB = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
TEXI = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"
OUT = r"E:\PotatoST\build\zftools\_zf117_preview.png"
ZOOM = 14
PAD = 10


def wpng(path, w, h, rgba):
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4])

    def ch(t, p):
        return struct.pack(">I", len(p)) + t + p + struct.pack(">I", zlib.crc32(t + p) & 0xFFFFFFFF)

    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                              + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                              + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def sheet(rows, tile=16, zoom=ZOOM, pad=PAD):
    tw = tile * zoom
    cols = max(len(r) for r in rows)
    W = pad + cols * (tw + pad)
    H = pad + len(rows) * (tw + pad)
    buf = bytearray(W * H * 4)
    for i in range(W * H):
        x, y = i % W, i // W
        v = 58 if ((x // 10) + (y // 10)) % 2 == 0 else 92
        buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))
    for ri, row in enumerate(rows):
        for ci, (label, w, h, rgba) in enumerate(row):
            ox, oy = pad + ci * (tw + pad), pad + ri * (tw + pad)
            for y in range(min(h, tile) * zoom):
                for x in range(min(w, tile) * zoom):
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


def L(p, label):
    if not os.path.exists(p):
        return None
    w, h, rgba = read_png(p)
    return (label, w, h, rgba)


rows = []
print(u"逐行：候选「顶/底」 / 现有「六面」 / 物品")
for label, cand, cur in [
    (u"锂电池构造器", os.path.join(USERART, u"锂电池构造器上和下面_001.png"),
     os.path.join(TEXB, "lithium_battery_plant.png")),
    (u"柴油发电机控制器", os.path.join(USERART, u"柴油发电机控制器顶部&底部_001.png"),
     os.path.join(TEXB, "diesel_generator_controller.png")),
]:
    a, b = L(cand, u"顶底"), L(cur, u"现有")
    if a and b:
        rows.append([a, b])
        print(u"  %s：顶底 %dx%d  /  现有 %dx%d" % (label, a[1], a[2], b[1], b[2]))

items = [L(os.path.join(USERART, u"银线_001.png"), u"银线"),
         L(os.path.join(USERART, u"银线轴_001.png"), u"银线轴")]
items = [i for i in items if i]
if items:
    rows.append(items)
    print(u"  物品：%d 件" % len(items))

W, H, buf = sheet(rows)
wpng(OUT, W, H, buf)
print(u"\n预览: %s (%dx%d)" % (OUT, W, H))
