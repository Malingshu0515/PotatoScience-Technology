# -*- coding: utf-8 -*-
# _zf135_preview.py —— 30 张流体动画贴图的肉眼复核图（只读 + 写一张 PNG）
# 每行一种流体：still 与 flow 的第一帧 / 中间帧 并排，看"动没动、像不像在流"。
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
OUT = r"E:\PotatoST\build\zftools\_zf135_preview.png"
Z = 8
PAD = 4
GAP = 3

FLUIDS = ["oxygen", "hydrogen", "chlorine", "nitrogen", "ammonia", "carbon_dioxide",
          "lpg", "naphtha", "crude_oil", "diesel", "gasoline",
          "carbonic_acid", "nitric_acid", "sulfuric_acid", "hydrochloric_acid"]


def wpng(path, w, h, buf):
    raw = b"".join(b"\x00" + bytes(buf[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def ch(t, p):
        return struct.pack(">I", len(p)) + t + p + struct.pack(">I", zlib.crc32(t + p) & 0xFFFFFFFF)

    open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                           + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def frame_rows(rgba, fw, fh, f):
    return [bytes(rgba[((f * fh + y) * fw) * 4:((f * fh + y) * fw + fw) * 4]) for y in range(fh)]


# 每行 4 格：still帧0 / still帧8 / flow帧0 / flow帧8
cols = 4
tile = 16 * Z
rowh = tile + GAP
W = PAD * 2 + cols * (tile + GAP)
H = PAD * 2 + len(FLUIDS) * rowh
buf = bytearray(W * H * 4)
for i in range(W * H):
    x, y = i % W, i // W
    v = 46 if ((x // 6) + (y // 6)) % 2 == 0 else 68
    buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))

for ri, fl in enumerate(FLUIDS):
    oy = PAD + ri * rowh
    for ci, (sfx, fidx) in enumerate((("_still", 0), ("_still", 8), ("_flow", 0), ("_flow", 8))):
        p = os.path.join(T, fl + sfx + ".png")
        w, h, rgba = read_png(p)
        fh = 16
        nf = h // fh
        rows = frame_rows(rgba, w, fh, fidx % nf)
        ox = PAD + ci * (tile + GAP)
        for y in range(16):
            row = rows[y]
            for x in range(16):
                r, g, b, a = row[x * 4:x * 4 + 4]
                if a == 0:
                    continue
                for dy in range(Z):
                    base = (oy + y * Z + dy) * W
                    for dx in range(Z):
                        di = (base + ox + x * Z + dx) * 4
                        buf[di:di + 3] = bytes((r, g, b))
                        buf[di + 3] = 255
    print(u"  %-18s 已排（still 帧0/帧8 + flow 帧0/帧8）" % fl)

wpng(OUT, W, H, buf)
print(u"\n列序: still帧0 | still帧8 | flow帧0 | flow帧8（放大 %d 倍）" % Z)
print(u"行序: %s" % u" / ".join(FLUIDS))
print(u"预览: %s (%dx%d)" % (OUT, W, H))
