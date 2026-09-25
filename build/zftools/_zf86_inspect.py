# -*- coding: utf-8 -*-
u"""_zf86_inspect.py —— 看清用户新放的三张 + 被动过的铜板（只读，不改）

要回答的问题：
  1. `碳酸锂.png` 是 20×20 RGBA —— 板面占了哪一块？（决定"裁 16×16"还是"缩放"）
  2. 三件物品现在的模型指向哪（借的原版贴图？自己的？）
  3. `copper_plate.png` 其实是 JPEG —— 解出来看看是不是用户那张铜板
"""
import io
import json
import os
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
MODELS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")


def png_px(path):
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
    for y in range(h):
        off = y * (w * 4 + 1)
        filt = raw[off]
        if filt != 0:
            raise ValueError(u"%s 第 %d 行 filter=%d" % (path, y, filt))
        for x in range(w):
            px.append(tuple(raw[off + 1 + x * 4:off + 5 + x * 4]))
    return w, h, px


def main():
    print(u"== ① 碳酸锂.png（20×20）的 alpha 分布 ==")
    w, h, px = png_px(os.path.join(TEX, u"碳酸锂.png"))
    print(u"  尺寸 %d×%d，不透明像素 %d / %d"
          % (w, h, sum(1 for p in px if p[3] == 255), w * h))
    rows, cols = [], []
    for y in range(h):
        row = u""
        for x in range(w):
            a = px[y * w + x][3]
            row += u"#" if a == 255 else (u"." if a == 0 else u"+")
        rows.append(row)
        if u"#" in row or u"+" in row:
            cols.append(y)
    for r in rows:
        print(u"     " + r)
    xs = [x for y in range(h) for x in range(w) if px[y * w + x][3] != 0]
    ys = [y for y in range(h) for x in range(w) if px[y * w + x][3] != 0]
    if xs:
        print(u"  非透明像素的包围盒：x %d..%d，y %d..%d（宽 %d 高 %d）"
              % (min(xs), max(xs), min(ys), max(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))

    print(u"\n== ② 三件物品现在的模型指向 ==")
    for name in [u"lithium_carbonate", u"sodium_chloride", u"capacitor", u"copper_plate"]:
        p = os.path.join(MODELS, name + u".json")
        t = io.open(p, encoding="utf-8").read() if os.path.exists(p) else u"(没有这个模型)"
        print(u"  %-18s %s" % (name, t.replace(u"\n", u" ").strip()[:110]))

    print(u"\n== ③ copper_plate.png（其实是 JPEG）前几行颜色 ==")
    dump = os.path.join(ROOT, r"build\zftools\_zf86_jpg_pixels.json")
    if os.path.exists(dump):
        d = json.loads(io.open(dump, encoding="utf-8").read())
        for key in d:
            print(u"  %s：%d 个像素，前 4 个 %s" % (key, len(d[key]), d[key][:4]))
    else:
        print(u"  （还没导出像素）")


if __name__ == "__main__":
    sys.exit(main())
