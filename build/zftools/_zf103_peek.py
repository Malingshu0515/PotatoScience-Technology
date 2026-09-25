# -*- coding: utf-8 -*-
u"""_zf103_peek.py —— 只读：把两张用户上传的缩略预览图逐像素 dump 出来看结构

目的：判断它们到底是"两张真正的盔甲贴图被等比缩到 64x32"，还是"四件套的拼版图"。
只读，不改任何东西。
"""
import sys
import zlib
import struct
import os

OBJS = [
    (u"钛合金套装", r"C:\Users\Administrator\.dsh\attachments\v1\objects\84"
                     r"\84c0660b9d956c9af58f4c96242a92bcac9996f5fd09bb2cfc02d108e09a9d7a"),
    (u"星璨钢套装", r"C:\Users\Administrator\.dsh\attachments\v1\objects\02"
                     r"\02239356de18e07b8ceedf3802be7aa3e1152abfa5dfa7873bd968f26f2f7c12"),
]


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not png"
    pos = 8
    idat = b""
    w = h = bitdepth = colortype = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            w, h, bitdepth, colortype, comp, filt, inter = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"IDAT":
            idat += chunk
        pos += 12 + length
    assert bitdepth == 8, bitdepth
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colortype]
    raw = zlib.decompress(idat)
    stride = w * channels
    out = []
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out.append(bytes(line))
        prev = line
    return w, h, channels, out


def main():
    for name, path in OBJS:
        if not os.path.isfile(path):
            print(u"%s: 缺文件" % name)
            continue
        w, h, ch, rows = read_png(path)
        print(u"\n================ %s  %dx%d  channels=%d ================" % (name, w, h, ch))
        # 用 ascii 密度图看形状
        ramp = u" .:-=+*#%@"
        for y in range(0, h, 1):
            row = rows[y]
            line = []
            for x in range(0, w, 2):
                i = x * ch
                a = row[i + 3] if ch == 4 else 255
                r, g, b = row[i], row[i + 1], row[i + 2]
                if a < 16:
                    line.append(u" ")
                else:
                    lum = (r * 299 + g * 587 + b * 114) // 1000
                    # 反相：越亮越空（白底素材）
                    idx = min(9, max(0, (255 - lum) * 10 // 256))
                    line.append(ramp[idx])
            print(u"%3d|%s|" % (y, u"".join(line)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
