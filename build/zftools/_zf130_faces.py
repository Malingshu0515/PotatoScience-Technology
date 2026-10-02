# -*- coding: utf-8 -*-
u"""_zf117_faces.py —— 按「顶 / 底 / 侧×4」排版出对照图（只读 + 写一张 PNG）

左边一组 = 现状（cube_all：六面都是同一张）
右边一组 = 提议（顶/底 = 你给的新图，四个侧面 = 现有那张）
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
OUT = r"E:\PotatoST\build\zftools\_zf117_faces.png"
Z = 11
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


def draw(buf, W, ox, oy, w, h, rgba, zoom=Z):
    for y in range(h * zoom):
        for x in range(w * zoom):
            si = ((y // zoom) * w + (x // zoom)) * 4
            a = rgba[si + 3]
            di = ((oy + y) * W + (ox + x)) * 4
            if a == 0:
                continue
            if a == 255:
                buf[di:di + 3] = bytes(rgba[si:si + 3])
            else:
                for c in range(3):
                    buf[di + c] = (rgba[si + c] * a + buf[di + c] * (255 - a)) // 255
            buf[di + 3] = 255


def load(p):
    return read_png(p) if os.path.exists(p) else None


def block_rows(cand_p, cur_p):
    """返回两行：现状 [cur×6] / 提议 [cand(up), cand(down), cur×4]"""
    cur = load(cur_p)
    cand = load(cand_p)
    if not cur or not cand:
        return None
    return ([("up", cur), ("down", cur), ("N", cur), ("S", cur), ("E", cur), ("W", cur)],
            [("UP", cand), ("DOWN", cand), ("N", cur), ("S", cur), ("E", cur), ("W", cur)])


JOBS = [
    (u"锂电池构造器", os.path.join(USERART, u"锂电池构造器上和下面_001.png"),
     os.path.join(TEXB, "lithium_battery_plant.png")),
    (u"柴油发电机控制器", os.path.join(USERART, u"柴油发电机控制器顶部&底部_001.png"),
     os.path.join(TEXB, "diesel_generator_controller.png")),
]

tile = 16 * Z
cols = 6
W = PAD + cols * (tile + PAD)
nrows = len(JOBS) * 2
H = PAD + nrows * (tile + PAD)

buf = bytearray(W * H * 4)
for i in range(W * H):
    x, y = i % W, i // W
    v = 52 if ((x // 8) + (y // 8)) % 2 == 0 else 78
    buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))

# 行间隔线
r = 0
for label, cand, cur in JOBS:
    rr = block_rows(cand, cur)
    if not rr:
        print(u"  !! %s 缺图" % label)
        continue
    for row in rr:
        oy = PAD + r * (tile + PAD)
        for ci, (face, (w, h, rgba)) in enumerate(row):
            ox = PAD + ci * (tile + PAD)
            draw(buf, W, ox, oy, w, h, rgba)
        r += 1
    print(u"  %s：两行已排（上=现状六面同一张，下=顶/底换新）" % label)

wpng(OUT, W, H, buf)
print(u"\n对照图: %s (%dx%d)" % (OUT, W, H))
print(u"列序：UP / DOWN / 北 / 南 / 东 / 西")
