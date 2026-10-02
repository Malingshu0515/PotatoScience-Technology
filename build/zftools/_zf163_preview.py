# -*- coding: utf-8 -*-
r"""_zf163_preview.py —— 复核图：现在 / 新版 / 原版水，三条并排（只看前 8 帧）

上半 = still（16x16 一帧），下半 = flow。
⚠ 原版水 flow 是 32x32，为了同屏，**只裁左上 16x16**（记账：这张图不能拿来看原版 flow 的全貌）。
"""
import io, os, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
OUT = os.path.join(TOOLS, '_zf163_out')
REF = os.path.join(TOOLS, '_zf163_ref')
S = 8
CELL = 16 * S
GAP = 6
M = 10
FRAMES = 8


def fr(path, base=16):
    w, h, px = read_png(path)
    n = h // w
    out = []
    for i in range(n):
        sub = bytearray()
        for y in range(base):
            row = (i * w + y) * w * 4
            sub += px[row:row + base * 4]
        out.append((base, sub))
    return out


def strip(path, base=16):
    f = fr(path, base)
    return [f[i % len(f)][1] for i in range(FRAMES)]


ROWS = [
    (u'原油 still — 现在', strip(os.path.join(TEXB, 'crude_oil_still.png'))),
    (u'原油 still — 新版', strip(os.path.join(OUT, 'crude_oil_still.png'))),
    (u'氮气 still — 现在', strip(os.path.join(TEXB, 'nitrogen_still.png'))),
    (u'氮气 still — 新版', strip(os.path.join(OUT, 'nitrogen_still.png'))),
    (u'氯气 still — 现在', strip(os.path.join(TEXB, 'chlorine_still.png'))),
    (u'氯气 still — 新版', strip(os.path.join(OUT, 'chlorine_still.png'))),
    (u'原版水 still', strip(os.path.join(REF, 'water_still.png'))),
    (u'', None),
    (u'原油 flow — 现在', strip(os.path.join(TEXB, 'crude_oil_flow.png'))),
    (u'原油 flow — 新版', strip(os.path.join(OUT, 'crude_oil_flow.png'))),
    (u'原版水 flow（左上 16x16 裁切）', strip(os.path.join(REF, 'water_flow.png'))),
]

W = M * 2 + CELL * FRAMES + GAP * (FRAMES - 1)
rowh = [CELL if r[1] else GAP * 2 for r in ROWS]
H = M * 2 + sum(rowh) + GAP * (len(ROWS) - 1)
canvas = bytearray(W * H * 4)
for y in range(H):
    for x in range(W):
        v = 62 if ((x // 8 + y // 8) % 2 == 0) else 74
        i = (y * W + x) * 4
        canvas[i] = canvas[i + 1] = canvas[i + 2] = v
        canvas[i + 3] = 255


def blit(px16, ox, oy):
    for y in range(16):
        for x in range(16):
            i = (y * 16 + x) * 4
            a = px16[i + 3]
            if not a:
                continue
            for dy in range(S):
                for dx in range(S):
                    di = ((oy + y * S + dy) * W + (ox + x * S + dx)) * 4
                    if a == 255:
                        canvas[di:di + 4] = px16[i:i + 4]
                    else:
                        for c in range(3):
                            canvas[di + c] = (px16[i + c] * a + canvas[di + c] * (255 - a)) // 255
                        canvas[di + 3] = 255


oy = M
for label, frames in ROWS:
    if frames is None:
        oy += GAP * 2 + GAP
        continue
    for k, f in enumerate(frames):
        blit(f, M + k * (CELL + GAP), oy)
    oy += CELL + GAP


def write_png(path, w, h, rgba):
    import zlib, struct
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgba[y * w * 4:(y + 1) * w * 4]

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


p = os.path.join(TOOLS, '_zf163_preview.png')
write_png(p, W, H, canvas)
print(u'行顺序（每行 8 帧，从左到右 = 第 0..7 帧）：')
for label, frames in ROWS:
    print(u'  ' + (label if label else u'—— 分栏 ——'))
print(u'\n已写出 %s（%dx%d）' % (p, W, H))
