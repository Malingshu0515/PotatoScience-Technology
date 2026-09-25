# -*- coding: utf-8 -*-
"""PngRecolor.py —— 无第三方依赖的 PNG 读取 / 改色 / 写出（0.10 ZF15）

**为什么不用 Pillow**：本机 `pip install Pillow` 极慢（实测 >2min 无输出）。
而我们要做的事只有一件——把 16×16 的矿石/粗矿贴图**改个色**。
PNG 解码用标准库 `zlib` 就够，代价是得自己还原 scanline 过滤器（见 `_unfilter`）。

用法：
    # ① 体检：看尺寸/色彩类型 + 主色（决定往哪个色相改）
    python build/zftools/PngRecolor.py probe <png...>

    # ② 改色：只动「饱和度 >= sat_min」的像素（= 矿石里的矿物颗粒），石头部分原样保留
    python build/zftools/PngRecolor.py recolor --src A.png --dst B.png --hue-shift 250
    python build/zftools/PngRecolor.py recolor --src A.png --dst B.png --hue 330 --sat-mul 1.1

    # ③ 只看不改（打印改完的主色）
    python build/zftools/PngRecolor.py recolor --src A.png --hue-shift 250 --dry

**为什么要「只动高饱和像素」**：矿贴图 = 灰石头底 + 彩色矿物颗粒。
整体转色相会把石头的暖灰也带偏（16×16 的贴图上一眼能看出来）；
按饱和度分流后，石头保持原样，颗粒换色 —— 这才是「改色」而不是「滤镜」。

**写出格式**：一律 RGBA8（color type 6）。Minecraft 读 RGBA PNG 没问题。
"""
import argparse
import colorsys
import struct
import sys
import zlib

SIG = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _chunks(data):
    pos = 8
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        yield ctype, data[pos + 8:pos + 8 + length]
        pos += 12 + length


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter(raw, width, height, bpp, stride):
    out = bytearray(height * stride)
    prev = bytearray(stride)
    pos = 0
    for y in range(height):
        ft = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + stride])
        pos += stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 0xFF
        elif ft != 0:
            raise ValueError("未知的 PNG 过滤器类型 {0}".format(ft))
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return out


def read_png(path):
    """返回 (width, height, bytearray RGBA)。"""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != SIG:
        raise ValueError("{0} 不是 PNG".format(path))
    width = height = bitdepth = colortype = None
    idat = bytearray()
    plte = None
    trns = None
    for ctype, chunk in _chunks(data):
        if ctype == b"IHDR":
            width, height, bitdepth, colortype, comp, filt, inter = struct.unpack(">IIBBBBB", chunk)
            if bitdepth != 8:
                raise ValueError("只支持 8 位深度，本文件是 {0}".format(bitdepth))
            if inter != 0:
                raise ValueError("不支持隔行扫描 PNG")
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"PLTE":
            plte = chunk
        elif ctype == b"tRNS":
            trns = chunk
    nch = CHANNELS[colortype]
    stride = width * nch
    raw = zlib.decompress(bytes(idat))
    flat = _unfilter(raw, width, height, nch, stride)

    rgba = bytearray(width * height * 4)
    if colortype == 6:
        rgba[:] = flat
    elif colortype == 2:
        for i in range(width * height):
            rgba[i * 4:i * 4 + 3] = flat[i * 3:i * 3 + 3]
            rgba[i * 4 + 3] = 255
    elif colortype == 0:
        for i in range(width * height):
            v = flat[i]
            rgba[i * 4:i * 4 + 4] = bytes((v, v, v, 255))
    elif colortype == 4:
        for i in range(width * height):
            v = flat[i * 2]
            rgba[i * 4:i * 4 + 4] = bytes((v, v, v, flat[i * 2 + 1]))
    elif colortype == 3:
        alpha = trns if trns else b""
        for i in range(width * height):
            idx = flat[i]
            rgba[i * 4:i * 4 + 3] = plte[idx * 3:idx * 3 + 3]
            rgba[i * 4 + 3] = alpha[idx] if idx < len(alpha) else 255
    else:
        raise ValueError("不支持的色彩类型 {0}".format(colortype))
    return width, height, rgba


def _chunk(ctype, payload):
    return (struct.pack(">I", len(payload)) + ctype + payload
            + struct.pack(">I", zlib.crc32(ctype + payload) & 0xFFFFFFFF))


def write_png(path, width, height, rgba):
    raw = bytearray()
    row = width * 4
    for y in range(height):
        raw.append(0)                      # 过滤器 0（None）：16×16 压缩后没多大差别，胜在不会算错
        raw += rgba[y * row:(y + 1) * row]
    body = (SIG
            + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(body)


def _hsv(r, g, b):
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)


def _rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, min(max(s, 0.0), 1.0), min(max(v, 0.0), 1.0))
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def histogram(rgba, width, height, sat_min=0.0):
    """按出现次数排序的颜色直方图（含 HSV）。"""
    counts = {}
    for i in range(width * height):
        r, g, b, a = rgba[i * 4:i * 4 + 4]
        if a == 0:
            continue
        if sat_min > 0.0:
            h, s, v = _hsv(r, g, b)
            if s < sat_min:
                continue
        counts[(r, g, b)] = counts.get((r, g, b), 0) + 1
    rows = []
    for (r, g, b), n in counts.items():
        h, s, v = _hsv(r, g, b)
        rows.append((n, r, g, b, h * 360.0, s, v))
    rows.sort(key=lambda t: (-t[0], t[1], t[2], t[3]))
    return rows


def _report(label, rows, top=16):
    print("  {0}（{1} 种颜色）".format(label, len(rows)))
    for n, r, g, b, h, s, v in rows[:top]:
        print("    #{0:02X}{1:02X}{2:02X}  x{3:<4} H={4:6.1f}  S={5:.2f}  V={6:.2f}".format(r, g, b, n, h, s, v))


def cmd_probe(args):
    for path in args.files:
        w, h, rgba = read_png(path)
        print("== {0}  {1}x{2} ==".format(path, w, h))
        _report("全部颜色", histogram(rgba, w, h), top=args.top)
        if args.sat_min > 0:
            _report("饱和像素（S>={0}）".format(args.sat_min), histogram(rgba, w, h, args.sat_min), top=args.top)
        print("")
    return 0


def cmd_recolor(args):
    w, h, rgba = read_png(args.src)
    if args.hue is None and args.hue_shift == 0.0 and args.sat_mul == 1.0 and args.val_mul == 1.0:
        print("什么都没改（既没给 --hue/--hue-shift，也没给 --sat-mul/--val-mul）")
        return 2
    out = bytearray(rgba)
    touched = 0
    for i in range(w * h):
        r, g, b, a = rgba[i * 4:i * 4 + 4]
        if a == 0:
            continue
        hh, s, v = _hsv(r, g, b)
        if s < args.sat_min:
            continue                                  # 石头底：原样保留
        if args.hue is not None:
            hh = args.hue / 360.0
        hh += args.hue_shift / 360.0
        s *= args.sat_mul
        v *= args.val_mul
        nr, ng, nb = _rgb(hh, s, v)
        out[i * 4:i * 4 + 3] = bytes((nr, ng, nb))
        touched += 1
    total = sum(1 for i in range(w * h) if rgba[i * 4 + 3] != 0)
    print("{0}  {1}x{2}  改了 {3}/{4} 个不透明像素（{5:.0f}%，阈值 S>={6}）".format(
        args.src, w, h, touched, total, 100.0 * touched / max(total, 1), args.sat_min))
    _report("改后主色（饱和像素）", histogram(out, w, h, args.sat_min), top=8)
    if args.dst and not args.dry:
        write_png(args.dst, w, h, out)
        print("已写出 {0}".format(args.dst))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description="无依赖 PNG 改色工具")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("probe", help="打印尺寸与主色")
    p.add_argument("files", nargs="+")
    p.add_argument("--top", type=int, default=16)
    p.add_argument("--sat-min", type=float, default=0.15, help="另外列出饱和像素的主色（默认 0.15）")
    p.set_defaults(func=cmd_probe)

    r = sub.add_parser("recolor", help="按饱和度分流改色")
    r.add_argument("--src", required=True)
    r.add_argument("--dst")
    r.add_argument("--hue", type=float, default=None, help="把命中像素的色相**设成**这个角度(0-360)")
    r.add_argument("--hue-shift", type=float, default=0.0, help="在原有色相上**转**这么多度")
    r.add_argument("--sat-min", type=float, default=0.15, help="只改 S>= 此值的像素（石头不动）")
    r.add_argument("--sat-mul", type=float, default=1.0)
    r.add_argument("--val-mul", type=float, default=1.0)
    r.add_argument("--dry", action="store_true")
    r.set_defaults(func=cmd_recolor)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
