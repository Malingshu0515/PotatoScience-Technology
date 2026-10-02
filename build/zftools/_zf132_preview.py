# -*- coding: utf-8 -*-
"""_zf132_preview.py —— 动态贴图的肉眼复核图（只读 + 写 PNG）

⚠ 帧数**从图高自动推**，不写死：第一版写死"32 帧 / 取帧 0,8,16,24"，
   改成 16 帧之后同一份脚本直接 IndexError（取不存在的第 24 帧）。
   贴图是 16 的整数倍高 ⇒ nf = h / 16，取帧位置按 nf 等分。
"""
import io
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\PotatoST\build\zftools")
from PngRecolor import read_png  # noqa: E402

T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\block"
OUT = r"E:\PotatoST\build\zftools\_zf132_preview.png"
Z = 10
PAD = 6

NAMES = ["diesel_still", "diesel_flow", "gasoline_still",
         "gasoline_flow", "crude_oil_still", "crude_oil_flow"]


def wpng(path, w, h, buf):
    raw = b""
    for y in range(h):
        raw += b"\x00" + bytes(buf[y * w * 4:(y + 1) * w * 4])

    def ch(t, p):
        return struct.pack(">I", len(p)) + t + p + struct.pack(">I", zlib.crc32(t + p) & 0xFFFFFFFF)

    io.open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                              + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                              + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def frame_rows(rgba, fw, fh, f):
    return [bytes(rgba[((f * fh + y) * fw) * 4:((f * fh + y) * fw + fw) * 4]) for y in range(fh)]


rows = []
pick_used = None
for n in NAMES:
    p = os.path.join(T, n + ".png")
    w, h, rgba = read_png(p)
    fh = 16
    if h % fh:
        print(u"  !! %s 高 %d 不是 16 的整数倍" % (n, h))
        continue
    nf = h // fh
    pick = [0, nf // 4, nf // 2, (3 * nf) // 4]
    pick_used = pick
    tiles = [frame_rows(rgba, w, fh, f) for f in pick]
    r0, r1 = frame_rows(rgba, w, fh, 0), frame_rows(rgba, w, fh, 1)
    d = sum(1 for y in range(fh) for x in range(w)
            if r0[y][x * 4:x * 4 + 4] != r1[y][x * 4:x * 4 + 4])
    print(u"  %-18s %dx%d = %d 帧  取帧 %s  帧0↔帧1 差 %d px" % (n, w, h, nf, pick, d))
    rows.append(tiles)

tile = 16 * Z
cols = len(pick_used)
W = PAD + cols * (tile + PAD)
H = PAD + len(rows) * (tile + PAD)
buf = bytearray(W * H * 4)
for i in range(W * H):
    x, y = i % W, i // W
    v = 50 if ((x // 7) + (y // 7)) % 2 == 0 else 74
    buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))

for ri, tiles in enumerate(rows):
    oy = PAD + ri * (tile + PAD)
    for ci, trows in enumerate(tiles):
        ox = PAD + ci * (tile + PAD)
        for y in range(16):
            row = trows[y]
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

wpng(OUT, W, H, buf)
print(u"\n行序: %s" % u" / ".join(NAMES))
print(u"列序: 帧 %s（放大 %d 倍）" % (pick_used, Z))
print(u"预览: %s (%dx%d)" % (OUT, W, H))
