# -*- coding: utf-8 -*-
"""_zf69_preview.py —— 出一张"工作台摆法"预览图（纯标准库，4 倍放大）

不是游戏截图：左边 3×3 是**用户那句话**摆出来的九格（外圈 8 个青金石 + 中心 1 个加热装置），
右边是产物格（散热装置）。青金石贴图直接从原版 client.jar 里取（保证是原版那张图），
方块贴图取本项目自己的。
"""
import importlib.util
import io
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"
TEX = os.path.join(PROJ, r"src\main\resources\assets\potato_s_t\textures")
OUT = os.path.join(PROJ, r"build\zftools\zf69_recipe_preview.png")
LAPIS_TMP = os.path.join(PROJ, r"build\zftools\_zf69_lapis.png")

spec = importlib.util.spec_from_file_location("png", os.path.join(PROJ, r"build\zftools\_zf66_png.py"))
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)

SCALE = 4
CELL = 16 * SCALE          # 64
GAP = 4
MARGIN = 12
ARROW_W = 28


def read_png_any(path):
    """读 16x16 贴图。原版 jar 里的物品贴图是 **4 位索引** PNG（colorType=3/depth=4），
    本机 `_zf66_png.py` 只支持 8 位，所以这里单独解一遍（解完摊成 RGBA）。"""
    import struct
    import zlib
    data = io.open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a png: " + path
    pos = 8
    idat = bytearray()
    plte = trns = None
    w = h = depth = ctype = None
    while pos + 8 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype, _c, _f, inter = struct.unpack(">IIBBBBB", body)
            assert inter == 0, "interlaced png not supported: " + path
        elif typ == b"IDAT":
            idat += body
        elif typ == b"PLTE":
            plte = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if depth == 8 and ctype in (2, 6):
        _w, _h, _t, px = png.read_png(path)
        return px
    assert ctype == 3 and depth in (4, 8), "unsupported png: depth=%s ctype=%s" % (depth, ctype)
    stride = (w * depth + 7) // 8
    raw = zlib.decompress(bytes(idat))
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(1, stride):
                line[i] = (line[i] + line[i - 1]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - 1] if i >= 1 else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - 1] if i >= 1 else 0
                b = prev[i]
                c = prev[i - 1] if i >= 1 else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    px = []
    for y in range(h):
        for x in range(w):
            if depth == 8:
                idx = out[y * stride + x]
            else:
                byte = out[y * stride + (x >> 1)]
                idx = (byte >> 4) if (x & 1) == 0 else (byte & 0x0F)
            r, g, b = plte[idx * 3], plte[idx * 3 + 1], plte[idx * 3 + 2]
            a = trns[idx] if (trns is not None and idx < len(trns)) else 255
            px.append((r, g, b, a))
    return px


def load_tex(path):
    px = read_png_any(path)
    assert len(px) == 256, "贴图不是 16x16: %s (%d 像素)" % (path, len(px))
    return px


def scaled(px, times):
    out = []
    for y in range(16):
        row = []
        for x in range(16):
            c = px[y * 16 + x]
            row.extend([c] * times)
        for _ in range(times):
            out.extend(row)
    return out


def blend(dst, dw, x0, y0, src, sw, sh):
    for y in range(sh):
        for x in range(sw):
            r, g, b, a = src[y * sw + x]
            if a == 0:
                continue
            i = (y0 + y) * dw + (x0 + x)
            dr, dg, db, _ = dst[i]
            if a == 255:
                dst[i] = (r, g, b, 255)
            else:
                f = a / 255.0
                dst[i] = (int(dr * (1 - f) + r * f), int(dg * (1 - f) + g * f), int(db * (1 - f) + b * f), 255)


def rect(dst, dw, x0, y0, w, h, color):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            dst[y * dw + x] = color


def main():
    # 原版青金石贴图（从 client.jar 里取，别用我抄的）
    if not os.path.isfile(LAPIS_TMP):
        with zipfile.ZipFile(VANILLA_JAR) as z:
            data = z.read("assets/minecraft/textures/item/lapis_lazuli.png")
        io.open(LAPIS_TMP, "wb").write(data)
    lapis = load_tex(LAPIS_TMP)
    lapis_s = scaled(lapis, SCALE)

    heater_p = os.path.join(TEX, r"block\heater.png")
    sink_p = os.path.join(TEX, r"block\heat_sink.png")
    for p in (heater_p, sink_p):
        if not os.path.isfile(p):
            print(u"缺贴图: %s" % p)
            return 1
    heater_s = scaled(load_tex(heater_p), SCALE)
    sink_s = scaled(load_tex(sink_p), SCALE)

    grid = 3 * CELL + 2 * GAP
    W = MARGIN * 2 + grid + ARROW_W + CELL
    H = MARGIN * 2 + grid
    bg = (198, 198, 198, 255)
    slot = (139, 139, 139, 255)
    canvas = [bg] * (W * H)

    # 九格底
    for r in range(3):
        for c in range(3):
            x0 = MARGIN + c * (CELL + GAP)
            y0 = MARGIN + r * (CELL + GAP)
            rect(canvas, W, x0, y0, CELL, CELL, slot)

    # 外圈青金石、中心加热装置（照用户原话：加热装置围一圈青金石）
    for r in range(3):
        for c in range(3):
            x0 = MARGIN + c * (CELL + GAP)
            y0 = MARGIN + r * (CELL + GAP)
            tex = heater_s if (r == 1 and c == 1) else lapis_s
            blend(canvas, W, x0, y0, tex, CELL, CELL)

    # 箭头
    ax = MARGIN + grid + 4
    ay = MARGIN + grid // 2
    rect(canvas, W, ax, ay - 3, ARROW_W - 10, 6, (85, 85, 85, 255))
    for i in range(10):
        rect(canvas, W, ax + ARROW_W - 10 + i, ay - 10 + i, 1, 20 - 2 * i, (85, 85, 85, 255))

    # 产物格
    rx = MARGIN + grid + ARROW_W
    ry = MARGIN + grid // 2 - CELL // 2
    rect(canvas, W, rx, ry, CELL, CELL, slot)
    blend(canvas, W, rx, ry, sink_s, CELL, CELL)

    png.write_png(OUT, W, H, canvas)
    print(u"写出 %s  (%dx%d)" % (OUT, W, H))
    print(u"九格：外圈 8 个青金石（minecraft:lapis_lazuli）+ 中心 1 个加热装置（potato_s_t:heater）")
    print(u"产物：potato_s_t:heat_sink x1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
