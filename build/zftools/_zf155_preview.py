# -*- coding: utf-8 -*-
u"""_zf155_preview.py —— 把 ZF155 那张 16x16 通用升级模板贴图放大成给人看的预览图。

顺带**自己解一遍 PNG**（不信写它的那个脚本）：尺寸 / 位深 / 颜色类型 / 交织 / 每行滤波器
/ 非空像素数 / 独立颜色数，全部重新算一遍；放大用 8 倍最近邻（不插值，看得清像素格）。
产出：build\\zftools\\_zf155_preview.png
"""
import io
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
SRC = os.path.join(ZT, u"_zf155_texture_src.png")
TEX = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item\universal_upgrade_template.png"
SCALE = 8


def read_png(path):
    src = open(path, "rb").read()
    assert src[:8] == b"\x89PNG\r\n\x1a\n", u"不是 PNG"
    pos, idat, ihdr = 8, b"", None
    while pos < len(src):
        (ln,) = struct.unpack(">I", src[pos:pos + 4])
        tag = src[pos + 4:pos + 8]
        payload = src[pos + 8:pos + 8 + ln]
        if tag == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", payload)
        elif tag == b"IDAT":
            idat += payload
        pos += 12 + ln
    w, h, depth, ctype, comp, filt, inter = ihdr
    raw = zlib.decompress(idat)
    assert depth == 8 and ctype == 6, u"只认 8 位 RGBA"
    stride = w * 4
    rows, filters = [], []
    for y in range(h):
        f = raw[y * (stride + 1)]
        filters.append(f)
        assert f == 0, u"第 %d 行滤波器是 %d（本工程只写 0）" % (y, f)
        rows.append(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
    return w, h, rows, filters


def write_png(path, w, h, rows):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n"
                 + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw, 9))
                 + chunk(b"IEND", b""))


def main():
    w, h, rows, filters = read_png(TEX)
    print(u"源贴图：%s" % TEX)
    print(u"  %dx%d / 8 位 RGBA / 滤波器全 0 = %s" % (w, h, all(f == 0 for f in filters)))

    px = [[tuple(rows[y][x * 4:x * 4 + 4]) for x in range(w)] for y in range(h)]
    solid = sum(1 for y in range(h) for x in range(w) if px[y][x][3] == 255)
    half = sum(1 for y in range(h) for x in range(w) if 0 < px[y][x][3] < 255)
    colors = sorted({px[y][x] for y in range(h) for x in range(w)})
    print(u"  不透明 %d / 256，半透明 %d，独立颜色 %d" % (solid, half, len(colors)))
    for c in colors:
        n = sum(1 for y in range(h) for x in range(w) if px[y][x] == c)
        print(u"    %-18s x%d" % (str(c), n))

    big = []
    for y in range(h):
        row = b""
        for x in range(w):
            row += bytes(px[y][x]) * SCALE
        big += [row] * SCALE
    out = os.path.join(ZT, u"_zf155_preview.png")
    write_png(out, w * SCALE, h * SCALE, big)
    print(u"\n放大 %dx → %s（%d 字节）" % (SCALE, out, os.path.getsize(out)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
