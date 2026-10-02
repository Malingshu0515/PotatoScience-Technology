# -*- coding: utf-8 -*-
"""_zf110_oil_preview.py —— 把新旧两张油桶都渲染成放大图，肉眼复核（只读源，写预览图）

要看清：
  A. 旧的那张（ZF87 用户的 油桶.jpg ⇒ 现在的 oil_bucket.png，824 B）
  B. 新的那张（ZF110 用户的 油桶.jpg，779 B）—— 原样 + 去背景后

放大 16 倍拼成一张，棋盘底衬出透明区。
"""
import io
import json
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

TOOLS = r"E:\PotatoST\build\zftools"
OUT = os.path.join(TOOLS, "_zf110_oil_preview.png")
ZOOM = 16


def write_png_rgba(path, w, h, rgba):
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4])

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                              + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def checker(x, y, z=8):
    return (60, 60, 64, 255) if ((x // z) + (y // z)) % 2 == 0 else (90, 90, 96, 255)


def compose(tiles, pad=8, zoom=ZOOM):
    """tiles: list of (label, w, h, rgba)。横排拼一张，每格加棋盘底。"""
    tw, th = 16 * zoom, 16 * zoom
    total_w = pad + len(tiles) * (tw + pad)
    total_h = pad + th + pad
    buf = bytearray(total_w * total_h * 4)
    for i in range(total_w * total_h):
        x, y = i % total_w, i // total_w
        buf[i * 4:i * 4 + 4] = bytes(checker(x, y))
    for ti, (label, w, h, rgba) in enumerate(tiles):
        ox = pad + ti * (tw + pad)
        oy = pad
        for y in range(h * zoom):
            for x in range(w * zoom):
                sx, sy = x // zoom, y // zoom
                si = (sy * w + sx) * 4
                a = rgba[si + 3]
                if a == 0:
                    continue
                di = ((oy + y) * total_w + (ox + x)) * 4
                if a == 255:
                    buf[di:di + 3] = bytes(rgba[si:si + 3])
                    buf[di + 3] = 255
                else:
                    for c in range(3):
                        buf[di + c] = (rgba[si + c] * a + buf[di + c] * (255 - a)) // 255
                    buf[di + 3] = 255
    return total_w, total_h, buf


def strip_background(px, w=16, h=16, tol=26):
    n = w * h
    alpha = [255] * n
    corners = [px[0], px[w - 1], px[(h - 1) * w], px[n - 1]]
    bg = tuple(sorted(c[i] for c in corners)[1] for i in range(3))
    stack = [i for i in range(n)
             if (i // w in (0, h - 1) or i % w in (0, w - 1))
             and all(abs(px[i][c] - bg[c]) <= tol for c in range(3))]
    seen = set(stack)
    while stack:
        i = stack.pop()
        alpha[i] = 0
        y, x = divmod(i, w)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                j = ny * w + nx
                if j not in seen and all(abs(px[j][c] - bg[c]) <= tol for c in range(3)):
                    seen.add(j)
                    stack.append(j)
    return [(px[i][0], px[i][1], px[i][2], alpha[i]) for i in range(n)], bg


tiles = []

# A. 旧成品
w, h, rgba = read_png(os.path.join(TOOLS, "_zf110_old_oil.png"))
tiles.append(("old_824B", w, h, rgba))
print("A 旧成品 oil_bucket.png: %dx%d" % (w, h))

# B. 新图原样（.NET 解的像素，alpha 全 255）
d = json.loads(io.open(os.path.join(TOOLS, "_zf110_oil_pixels.json"), encoding="utf-8").read())
new_px = [tuple(int(v) for v in s.split(",")) for s in d["px"]]
tiles.append(("new_raw", 16, 16, bytearray(b for p in new_px for b in p)))
print("B 新图原样: 16x16（alpha 全 255）")

# C. 新图去背景后（当前 _zf110_convert.py 的做法 —— 有问题的那个）
stripped, bg = strip_background(new_px)
tiles.append(("new_cut", 16, 16, bytearray(b for p in stripped for b in p)))
print("C 新图去背景后: 背景色 %s，留下 %d 个像素"
      % (bg, sum(1 for p in stripped if p[3] == 255)))

# D. 新图原样 + 把最外圈强制透明（另一种可能的做法，供对比）
edge = [(y, x) for y in range(16) for x in range(16)
        if y in (0, 15) or x in (0, 15)]
edge_cut = list(new_px)
for y, x in edge:
    p = edge_cut[y * 16 + x]
    edge_cut[y * 16 + x] = (p[0], p[1], p[2], 0)
tiles.append(("new_edgecut", 16, 16, bytearray(b for p in edge_cut for b in p)))
print("D 新图强制外圈透明: 留下 %d 个像素" % sum(1 for p in edge_cut if p[3] == 255))

tw, th, buf = compose(tiles)
write_png_rgba(OUT, tw, th, buf)
print("\n预览图（放大 %dx，从左到右：old_824B | new_raw | new_cut | new_edgecut）" % ZOOM)
print("  %s  (%dx%d, %d B)" % (OUT, tw, th, os.path.getsize(OUT)))
