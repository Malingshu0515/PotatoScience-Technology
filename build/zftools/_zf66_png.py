# -*- coding: utf-8 -*-
"""_zf66_png.py —— 纯标准库的 PNG 读/写（本机没有 Pillow，ZF60 那套 WPF 解码只能读不能细查）

这一轮要用它回答两件事：
  ① 用户给的两张工具贴图**是不是真有透明底**（RGBA 却整张不透明 = 游戏里一个实心方块）；
  ② 万一不是，把背景色抠成透明再写回去（`--key <r,g,b>` 只抠指定颜色，其余像素逐字节不动）。

用法:
    python _zf66_png.py <file.png> [more.png ...]                  # 打印规格 + alpha 统计 + 主色
    python _zf66_png.py <in.png> --out <out.png> --key 255,255,255 # 把纯白背景抠成透明
"""
import io
import struct
import sys
import zlib


def read_png(path):
    data = io.open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a png: " + path
    pos = 8
    idat = bytearray()
    w = h = depth = ctype = None
    plte = None
    trns = None
    while pos + 8 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, comp, filt, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and inter == 0, "only 8-bit non-interlaced supported"
        elif typ == b"IDAT":
            idat += body
        elif typ == b"PLTE":
            plte = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IEND":
            break
        pos += 12 + ln

    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(bytes(idat))
    stride = w * chans
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(chans, stride):
                line[i] = (line[i] + line[i - chans]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - chans] if i >= chans else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - chans] if i >= chans else 0
                b = prev[i]
                c = prev[i - chans] if i >= chans else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line

    # 统一摊成 RGBA
    px = []
    for i in range(0, len(out), chans):
        if ctype == 6:
            px.append(tuple(out[i:i + 4]))
        elif ctype == 2:
            px.append((out[i], out[i + 1], out[i + 2], 255))
        elif ctype == 0:
            v = out[i]
            px.append((v, v, v, 255))
        elif ctype == 4:
            v = out[i]
            px.append((v, v, v, out[i + 1]))
        elif ctype == 3:
            idx = out[i]
            r, g, b = plte[idx * 3], plte[idx * 3 + 1], plte[idx * 3 + 2]
            a = trns[idx] if trns is not None and idx < len(trns) else 255
            px.append((r, g, b, a))
    return w, h, ctype, px


def write_png(path, w, h, px):
    # ZF92 补的护栏：以前这里不校验元组长度，传了 3 元组也照写，
    # 结果产出一张自己都读不回来的坏 PNG（ZF91 的 _zf91_overlay.png 就是这么坏的）。
    if len(px) != w * h:
        raise ValueError(u"write_png: 像素数 %d != %d×%d = %d" % (len(px), w, h, w * h))
    for i, p in enumerate(px):
        if len(p) != 4:
            raise ValueError(u"write_png: 第 %d 个像素是 %d 元组（必须 RGBA 4 元组）: %r" % (i, len(p), tuple(p)))
        for c in p:
            if not (0 <= c <= 255):
                raise ValueError(u"write_png: 第 %d 个像素分量越界: %r" % (i, tuple(p)))
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw += bytes(px[y * w + x])

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    io.open(path, "wb").write(png)


def stats(path):
    w, h, ctype, px = read_png(path)
    alpha0 = sum(1 for p in px if p[3] == 0)
    alpha255 = sum(1 for p in px if p[3] == 255)
    partial = w * h - alpha0 - alpha255
    colors = {}
    for p in px:
        if p[3] > 0:
            colors[p[:3]] = colors.get(p[:3], 0) + 1
    top = sorted(colors.items(), key=lambda kv: -kv[1])[:4]
    print(u"%-26s %dx%d  colorType=%d  alpha=0 的像素 %d/%d  半透明 %d"
          % (path.replace("\\", "/").split("/")[-1], w, h, ctype, alpha0, w * h, partial))
    print(u"    不透明像素的主色: " + u"  ".join(u"#%02X%02X%02X x%d" % (c[0], c[1], c[2], n) for c, n in top))
    return w, h, px


def main(argv):
    if len(argv) >= 4 and argv[1] == "--out":
        src, dst, key = argv[0], argv[2], None
        for i, a in enumerate(argv):
            if a == "--key":
                key = tuple(int(v) for v in argv[i + 1].split(","))
        w, h, ctype, px = read_png(src)
        if key is None:
            print("缺 --key r,g,b")
            return 2
        n = 0
        out = []
        for p in px:
            if p[0] == key[0] and p[1] == key[1] and p[2] == key[2]:
                out.append((p[0], p[1], p[2], 0))
                n += 1
            else:
                out.append(p)
        write_png(dst, w, h, out)
        print(u"抠掉 %d 个 #%02X%02X%02X 像素 -> %s" % (n, key[0], key[1], key[2], dst))
        stats(dst)
        return 0

    for p in argv:
        stats(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
