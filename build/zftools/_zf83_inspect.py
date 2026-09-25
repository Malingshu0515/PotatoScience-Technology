# -*- coding: utf-8 -*-
u"""_zf83_inspect.py —— 先把"手上到底有什么"看清楚（不改任何东西）

1. 三张 jpg（16×16 / 24bpp）的像素 vs 现有 PNG（16×16 RGBA）的 RGB：
   —— 若一致 ⇒ 现有 PNG 就是这三张原图的转档（只是把某色背景做成了透明），
      steel/copper 不用重做；若不一致 ⇒ 说明用户给的是**新图**，要重做。
2. 顺带把 alpha 情况数出来（背景是不是透明、透明像素多少个）。
"""
import io
import json
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TEX = ROOT + r"\src\main\resources\assets\potato_s_t\textures\item"
TOOLS = ROOT + r"\build\zftools"


def read_png(path):
    b = io.open(path, "rb").read()
    w, h = struct.unpack(">II", b[16:24])
    idat = b""
    i = 8
    while i < len(b):
        ln = struct.unpack(">I", b[i:i + 4])[0]
        tag = b[i + 4:i + 8]
        if tag == b"IDAT":
            idat += b[i + 8:i + 8 + ln]
        i += 12 + ln
    raw = zlib.decompress(idat)
    px = []
    prev = bytearray(w * 4)
    for y in range(h):
        f = raw[y * (w * 4 + 1)]
        line = bytearray(raw[y * (w * 4 + 1) + 1:(y + 1) * (w * 4 + 1)])
        # 只处理 filter 0（本工程的贴图都是 0）——不是 0 就报出来
        if f != 0:
            raise ValueError(u"%s 第 %d 行用了 filter %d，本脚本只认 0" % (path, y, f))
        px.append(bytes(line))
        prev = line
    return w, h, px


def main():
    jpgs = json.loads(io.open(TOOLS + r"\_zf83_jpg_pixels.json", encoding="utf-8").read())
    for key, png_name in [(u"copper", u"copper_plate.png"), (u"steel", u"steel_plate.png"),
                          (u"iron", u"iron_plate.png"), (u"_generic", u"plate.png")]:
        path = TEX + u"\\" + png_name
        try:
            w, h, rows = read_png(path)
        except Exception as e:
            print(u"  %-18s 读不了：%s" % (png_name, e))
            continue
        alphas = []
        rgb = []
        for y in range(16):
            for x in range(16):
                r, g, b, a = rows[y][x * 4:x * 4 + 4]
                alphas.append(a)
                rgb.append(u"%d,%d,%d" % (r, g, b))
        trans = sum(1 for a in alphas if a == 0)
        info = u"%s：16×16 RGBA，全透明像素 %d 个，alpha 取值 %s" % (
            png_name, trans, sorted(set(alphas))[:6])
        if key in jpgs:
            same = sum(1 for a, b in zip(rgb, jpgs[key]) if a == b)
            # 半透明/透明处 RGB 可能被清零，只比不透明像素
            opaque_same = 0
            opaque_total = 0
            for i, a in enumerate(alphas):
                if a == 255:
                    opaque_total += 1
                    if rgb[i] == jpgs[key][i]:
                        opaque_same += 1
            info += u"；与 %s.jpg 的 RGB 相同像素 %d/256，其中**不透明**像素里相同 %d/%d" % (
                key, same, opaque_same, opaque_total)
        print(u"  " + info)
    print()
    print(u"判据：如果 不透明像素里相同 == 不透明像素总数，说明现有 PNG 就是这张 jpg 的转档")


if __name__ == "__main__":
    sys.exit(main())
