# -*- coding: utf-8 -*-
r"""_zf157_preview.py —— ZF157 复核图：左=改前 / 右=改后（五件），全部按 16x16 等比放大 8 倍

左列：
  · 热力金属 —— 把改前那张 160x160 占位色块**按游戏的方式缩到 16x16**（盒式平均）再画
  · 四件钛合金 —— 从**原版 client jar** 里取 `minecraft:item/iron_*`（改前真正在用的那张）
"""
import sys, os, io, zipfile
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png
import TextureCheck as TC

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
PRE = os.path.join(TOOLS, 'zf157_pre')
ASSET = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
TMP = os.path.join(TOOLS, '_zf157_tmp')
os.makedirs(TMP, exist_ok=True)

VANILLA = TC.VANILLA_JAR
print(u'原版 jar: %s' % VANILLA)


def load(path):
    w, h, px = read_png(path)
    return w, h, px


def box16(w, h, px):
    """把任意尺寸盒式平均成 16x16（游戏渲染大图时就是这个观感）。"""
    out = bytearray(16 * 16 * 4)
    for y in range(16):
        for x in range(16):
            x0, x1 = x * w // 16, max(x * w // 16 + 1, (x + 1) * w // 16)
            y0, y1 = y * h // 16, max(y * h // 16 + 1, (y + 1) * h // 16)
            acc = [0, 0, 0, 0]
            n = 0
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    i = (yy * w + xx) * 4
                    for c in range(4):
                        acc[c] += px[i + c]
                    n += 1
            for c in range(4):
                out[(y * 16 + x) * 4 + c] = acc[c] // n
    return 16, 16, out


def from_jar(tex):
    dst = os.path.join(TMP, tex.rsplit('/', 1)[-1])
    with zipfile.ZipFile(VANILLA) as z:
        data = z.read('assets/minecraft/textures/' + tex + '.png')
    with open(dst, 'wb') as f:
        f.write(data)
    return load(dst)


ROWS = [
    (u'热力金属', os.path.join(PRE, 'src__main__resources__assets__potato_s_t__textures__item__thermal_metal.png'), None,
     os.path.join(ASSET, 'textures', 'item', 'thermal_metal.png')),
    (u'钛合金头盔', None, 'item/iron_helmet', os.path.join(ASSET, 'textures', 'item', 'titanium_alloy_helmet.png')),
    (u'钛合金胸甲', None, 'item/iron_chestplate', os.path.join(ASSET, 'textures', 'item', 'titanium_alloy_chestplate.png')),
    (u'钛合金护腿', None, 'item/iron_leggings', os.path.join(ASSET, 'textures', 'item', 'titanium_alloy_leggings.png')),
    (u'钛合金靴子', None, 'item/iron_boots', os.path.join(ASSET, 'textures', 'item', 'titanium_alloy_boots.png')),
]

S = 8          # 放大倍数
CELL = 16 * S  # 128
GAP = 10
M = 12
COLS = 2
W = M * 2 + CELL * COLS + GAP
H = M * 2 + CELL * len(ROWS) + GAP * (len(ROWS) - 1)
canvas = bytearray(W * H * 4)
# 棋盘底（半透明处看得见）
for y in range(H):
    for x in range(W):
        v = 210 if ((x // 8 + y // 8) % 2 == 0) else 180
        i = (y * W + x) * 4
        canvas[i] = canvas[i + 1] = canvas[i + 2] = v
        canvas[i + 3] = 255


def blit(dst_w, dst_h, dst, src_w, src_h, src, ox, oy, scale):
    for y in range(src_h):
        for x in range(src_w):
            si = (y * src_w + x) * 4
            a = src[si + 3]
            if not a:
                continue
            for dy in range(scale):
                for dx in range(scale):
                    di = ((oy + y * scale + dy) * dst_w + (ox + x * scale + dx)) * 4
                    if a == 255:
                        dst[di:di + 4] = src[si:si + 4]
                    else:
                        for c in range(3):
                            dst[di + c] = (src[si + c] * a + dst[di + c] * (255 - a)) // 255
                        dst[di + 3] = 255


report = []
for r, (label, before_path, before_jar, after_path) in enumerate(ROWS):
    if before_path:
        bw, bh, bp = load(before_path)
        if (bw, bh) != (16, 16):
            bw, bh, bp = box16(bw, bh, bp)
    else:
        bw, bh, bp = from_jar(before_jar)
    aw, ah, ap = load(after_path)
    oy = M + r * (CELL + GAP)
    blit(W, H, canvas, bw, bh, bp, M, oy, S)
    blit(W, H, canvas, aw, ah, ap, M + CELL + GAP, oy, S)
    report.append(u'%-12s 改前 %dx%d -> 改后 %dx%d' % (label, bw, bh, aw, ah))


def write_png(path, w, h, rgba):
    import zlib, struct
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgba[y * w * 4:(y + 1) * w * 4]
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


OUT = os.path.join(TOOLS, '_zf157_preview.png')
write_png(OUT, W, H, canvas)
print(u'\n'.join(report))
print(u'\n已写出 %s（%dx%d，左列=改前 / 右列=改后）' % (OUT, W, H))
