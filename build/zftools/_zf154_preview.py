# -*- coding: utf-8 -*-
"""_zf154_preview.py —— 采油机「现状 vs 提议」六面对照（只读 + 写一张 PNG）

现状：`cube_all`，六面都是同一张 `oil_pump.png`。
提议（照 ZF130 那两台机器的同一套做法）：`cube_bottom_top` ——
**顶/底 = 用户新给的**，**四个侧面 = 现有那张**。
"""
import io
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

U = r"E:\PotatoST\build\用户素材"
T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
OUT = r"E:\PotatoST\build\zftools\_zf154_preview.png"
Z = 11
PAD = 8
GAP = 4


def wpng(path, w, h, buf):
    raw = b"".join(b"\x00" + bytes(buf[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def ch(t, p):
        return struct.pack(">I", len(p)) + t + p + struct.pack(">I", zlib.crc32(t + p) & 0xFFFFFFFF)

    open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                           + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def load(p):
    return read_png(p) if os.path.exists(p) else None


cur = load(os.path.join(T, "oil_pump.png"))
new = load(os.path.join(U, u"采油机顶部和底部_001.png"))
if not cur or not new:
    print(u"  !! 缺图")
    sys.exit(1)

tile = 16 * Z
FACES = [u"顶 UP", u"底 DOWN", u"北 N", u"南 S", u"东 E", u"西 W"]
rows = [
    (u"现状 cube_all", [cur] * 6),
    (u"提议 bottom_top", [new, new, cur, cur, cur, cur]),
]
W = PAD * 2 + 6 * (tile + GAP)
H = PAD * 2 + len(rows) * (tile + GAP)
buf = bytearray(W * H * 4)
for i in range(W * H):
    x, y = i % W, i // W
    v = 44 if ((x // 7) + (y // 7)) % 2 == 0 else 66
    buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))

for ri, (label, imgs) in enumerate(rows):
    oy = PAD + ri * (tile + GAP)
    for ci, (w, h, rgba) in enumerate(imgs):
        ox = PAD + ci * (tile + GAP)
        for y in range(16):
            for x in range(16):
                i = (y * w + x) * 4
                a = rgba[i + 3]
                if a == 0:
                    continue
                for dy in range(Z):
                    base = (oy + y * Z + dy) * W
                    for dx in range(Z):
                        di = (base + ox + x * Z + dx) * 4
                        buf[di:di + 3] = bytes(rgba[i:i + 3])
                        buf[di + 3] = 255
    print(u"  %-16s 已排" % label)

wpng(OUT, W, H, buf)
print(u"\n列序：%s" % u" ｜ ".join(FACES))
print(u"行序：上=现状（六面同一张）／下=提议（顶底换新、四面不动）")
print(u"预览: %s (%dx%d)" % (OUT, W, H))
