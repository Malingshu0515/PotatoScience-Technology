# -*- coding: utf-8 -*-
"""_zf143_preview.py —— 四锭「现有 vs 新图」对照（只读 + 写一张 PNG）

现有那四张是 **160×160** 的占位色块（游戏按 16×16 渲染，等于糊成一坨）；
新图是 16×16 的真锭形。对照图里把现有那张**按 16×16 采样**（=游戏里实际看到的），
跟新图并排，一眼看出差别。
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
T = r"E:\PotatoST\src\main\resources\assets\potato_s_t\textures\item"
OUT = r"E:\PotatoST\build\zftools\_zf143_preview.png"
Z = 18
PAD = 8
GAP = 6

JOBS = [(u"银锭.png", "silver_ingot", u"银"),
        (u"镍锭.png", "nickel_ingot", u"镍"),
        (u"铝锭.png", "aluminum_ingot", u"铝"),
        (u"钴锭.png", "cobalt_ingot", u"钴")]


def wpng(path, w, h, buf):
    raw = b"".join(b"\x00" + bytes(buf[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def ch(t, p):
        return struct.pack(">I", len(p)) + t + p + struct.pack(">I", zlib.crc32(t + p) & 0xFFFFFFFF)

    open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
                           + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def sample16(w, h, rgba):
    """把任意尺寸按 16×16 最近邻采样 —— 复刻"游戏按 16×16 渲染"的效果"""
    out = bytearray()
    for y in range(16):
        sy = min(h - 1, int((y + 0.5) * h / 16))
        for x in range(16):
            sx = min(w - 1, int((x + 0.5) * w / 16))
            i = (sy * w + sx) * 4
            out += bytes(rgba[i:i + 4])
    return out


# 布局：每行 4 格 = 现有(游戏所见) | 新图 | 现有原图(缩略整幅) | 空格
cols = 3
tile = 16 * Z
W = PAD * 2 + cols * (tile + GAP)
H = PAD * 2 + len(JOBS) * (tile + GAP)
buf = bytearray(W * H * 4)
for i in range(W * H):
    x, y = i % W, i // W
    v = 46 if ((x // 6) + (y // 6)) % 2 == 0 else 68
    buf[i * 4:i * 4 + 4] = bytes((v, v, v + 4, 255))


def put(ox, oy, px16, z=Z):
    for y in range(16):
        for x in range(16):
            i = (y * 16 + x) * 4
            a = px16[i + 3]
            if a == 0:
                continue
            for dy in range(z):
                base = (oy + y * z + dy) * W
                for dx in range(z):
                    di = (base + ox + x * z + dx) * 4
                    buf[di:di + 3] = bytes(px16[i:i + 3])
                    buf[di + 3] = 255


for ri, (src, dst, cn) in enumerate(JOBS):
    oy = PAD + ri * (tile + GAP)
    # ① 现有（按 16×16 采样）
    q = os.path.join(T, dst + ".png")
    w2, h2, r2 = read_png(q)
    put(PAD, oy, sample16(w2, h2, r2))
    # ② 新图（原样）
    w1, h1, r1 = read_png(os.path.join(U, src))
    put(PAD + (tile + GAP), oy, sample16(w1, h1, r1))
    print(u"  %s：现有 %dx%d → 游戏所见 16x16 ｜ 新图 %dx%d" % (cn, w2, h2, w1, h1))

wpng(OUT, W, H, buf)
print(u"\n每行：左=现有（游戏里实际看到的）｜中=你给的新图（放大 %d 倍）" % Z)
print(u"行序：%s" % u" / ".join(c for _, _, c in JOBS))
print(u"预览: %s (%dx%d)" % (OUT, W, H))
