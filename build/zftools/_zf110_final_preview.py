# -*- coding: utf-8 -*-
"""_zf110_final_preview.py —— ZF110 五张成品的放大复核图（只读，写预览 PNG）

上排：这轮上线/改指向的四张（原字节复制）
下排：油桶的四种候选（旧版 / 新原样 / 泛洪去背 / 外圈掏空）
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
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"
OUT = os.path.join(TOOLS, "_zf110_final_preview.png")
ZOOM = 14
PAD = 10


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


def sheet(rows, zoom=ZOOM, pad=PAD, tile=16):
    tw = tile * zoom
    cols = max(len(r) for r in rows)
    total_w = pad + cols * (tw + pad)
    total_h = pad + len(rows) * (tw + pad)
    buf = bytearray(total_w * total_h * 4)
    for i in range(total_w * total_h):
        x, y = i % total_w, i // total_w
        v = 60 if ((x // 8) + (y // 8)) % 2 == 0 else 92
        buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))
    for ri, row in enumerate(rows):
        for ci, (label, w, h, rgba) in enumerate(row):
            ox = pad + ci * (tw + pad)
            oy = pad + ri * (tw + pad)
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


def from_png(p):
    w, h, rgba = read_png(p)
    return w, h, rgba


# --- 上排：这轮上线/改指向的四张 ---
top = []
for name in ["star_steel_helmet.png", "lithium_carbonate.png", "sodium_chloride.png", "sulfur.png"]:
    p = os.path.join(TEX, name)
    w, h, rgba = from_png(p)
    top.append((name, w, h, rgba))
    print("上排 %-28s %dx%d" % (name, w, h))

# --- 下排：油桶四种候选 ---
d = json.loads(io.open(os.path.join(TOOLS, "_zf110_oil_pixels.json"), encoding="utf-8").read())
new_px = [tuple(int(v) for v in s.split(",")) for s in d["px"]]

bottom = []
w, h, rgba = from_png(os.path.join(TOOLS, "_zf110_old_oil.png"))
bottom.append(("old_824B", w, h, rgba))
bottom.append(("new_raw", 16, 16, bytearray(b for p in new_px for b in p)))
stripped, bg = strip_background(new_px)
bottom.append(("new_cut_%dpx" % sum(1 for p in stripped if p[3] == 255),
               16, 16, bytearray(b for p in stripped for b in p)))
edge_cut = list(new_px)
for y in range(16):
    for x in range(16):
        if y in (0, 15) or x in (0, 15):
            p = edge_cut[y * 16 + x]
            edge_cut[y * 16 + x] = (p[0], p[1], p[2], 0)
bottom.append(("new_edge_%dpx" % sum(1 for p in edge_cut if p[3] == 255),
               16, 16, bytearray(b for p in edge_cut for b in p)))
print("下排 old_824B | new_raw | new_cut | new_edge（背景色 %s）" % (bg,))

tw, th, buf = sheet([top, bottom])
write_png_rgba(OUT, tw, th, buf)
print("\n预览图: %s (%dx%d, %d B)" % (OUT, tw, th, os.path.getsize(OUT)))
print("  上排=这轮上线的四张；下排=油桶四候选")
