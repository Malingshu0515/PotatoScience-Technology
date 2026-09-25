# -*- coding: utf-8 -*-
"""ZF35：把 `接线块` 素材落成方块贴图 `wiring_block.png`。

用户：「再加个接线块」+ 一张 `接线块_001.png`（实为 160×160 webp）。

⚠ 通道顺序这次**先看原始字节再定**（§4.23），不靠文件名也不靠猜：
   `_zf35_decode.ps1` 打印出的裸字节里，最饱和不透明像素 = (0,187,255,255)；
   你发的预览图里那道框是**橙黄色**的 ⇒ 按 R,G,B,A 读会得到 (0,187,255)=青蓝（错），
   按 B,G,R,A 读得到 (255,187,0)=橙（对） ⇒ **这份裸像素是 BGRA**，写 PNG 时要换回 R,G,B。
   （与 ZF33 那六张同一套做法。）

尺寸：160×160 **不是 2 的幂**，按 §6.8 的结论**面积平均降到 16×16**。
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import write_png

SRC = r"E:\PotatoST\build\zftools\_block_imgs\接线块.rgba"
DST = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block\wiring_block.png"

raw = io.open(SRC, "rb").read()
n = len(raw) // 4
side = int(n ** 0.5)
if side * side != n:
    raise SystemExit("不是正方形（%d 像素）" % n)
print("源尺寸 = %d×%d" % (side, side))


def average_downscale(raw, src_side, dst):
    step = src_side / float(dst)
    out = bytearray(dst * dst * 4)
    for ty in range(dst):
        y0, y1 = int(ty * step), max(int(ty * step) + 1, int((ty + 1) * step))
        for tx in range(dst):
            x0, x1 = int(tx * step), max(int(tx * step) + 1, int((tx + 1) * step))
            sr = sg = sb = sa = 0
            cnt = 0
            for y in range(y0, min(y1, src_side)):
                for x in range(x0, min(x1, src_side)):
                    i = (y * src_side + x) * 4
                    # 源是 BGRA
                    sb += raw[i]
                    sg += raw[i + 1]
                    sr += raw[i + 2]
                    sa += raw[i + 3]
                    cnt += 1
            o = (ty * dst + tx) * 4
            out[o] = sr // cnt          # 写 PNG 时是 RGBA
            out[o + 1] = sg // cnt
            out[o + 2] = sb // cnt
            out[o + 3] = sa // cnt
    return out


dst_side = 16
flat = average_downscale(raw, side, dst_side)
write_png(DST, dst_side, dst_side, flat)
print("%d→%d 已写出 %s  %d 字节" % (side, dst_side, DST, os.path.getsize(DST)))

# ---- 落盘后回读，用能失败的判据检查 ----
back = io.open(DST, "rb").read()
px = []
import zlib
import struct
# 极简 PNG 反读：只认 PngRecolor 写出的 RGBA8、无过滤器的那一套太脆，改用 zlib 解 IDAT
w = struct.unpack(">I", back[16:20])[0]
h = struct.unpack(">I", back[20:24])[0]
idat = b""
pos = 8
while pos < len(back):
    ln = struct.unpack(">I", back[pos:pos + 4])[0]
    typ = back[pos + 4:pos + 8]
    if typ == b"IDAT":
        idat += back[pos + 8:pos + 8 + ln]
    pos += 12 + ln
data = zlib.decompress(idat)
stride = w * 4
print("回读尺寸 = %d×%d   解出 %d 字节" % (w, h, len(data)))

opaque = []
i = 0
for y in range(h):
    i = y * (stride + 1) + 1          # 每行开头 1 字节过滤器类型
    for x in range(w):
        o = i + x * 4
        if data[o + 3] > 0:
            opaque.append((data[o], data[o + 1], data[o + 2], data[o + 3]))

r = sum(p[0] for p in opaque) / len(opaque)
g = sum(p[1] for p in opaque) / len(opaque)
b = sum(p[2] for p in opaque) / len(opaque)
warm = sum(1 for p in opaque if p[0] > p[2] + 8)
cool = sum(1 for p in opaque if p[2] > p[0] + 8)
sat = max(opaque, key=lambda p: max(p[:3]) - min(p[:3]))
print("均色 = (%3.0f,%3.0f,%3.0f)   暖 %d / 冷 %d   不透明像素 %d" % (r, g, b, warm, cool, len(opaque)))
print("最饱和像素 = (%d,%d,%d,%d)" % sat)

fail = 0


def check(ok, msg):
    global fail
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail += 1


# 判据：预览图里那道框是**橙黄**的 ⇒ 最饱和像素必须 R>G>B（不是 B>G>R）
check(sat[0] > sat[1] > sat[2], "最饱和像素是暖色（R>G>B = 橙黄），实际 (%d,%d,%d)" % sat[:3])
check(sat[0] - sat[2] > 100, "暖冷差够大（>100），实际 %d" % (sat[0] - sat[2]))
check(warm > cool, "暖色像素比冷色多（%d vs %d）" % (warm, cool))
check(0.55 < g / 255.0, "整体偏亮（灰色机身），G 均值 = %.0f" % g)

print()
print("失败项 = %d" % fail)
sys.exit(1 if fail else 0)
