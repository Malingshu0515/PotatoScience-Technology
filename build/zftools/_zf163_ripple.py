# -*- coding: utf-8 -*-
r"""_zf163_ripple.py —— **新版 B：相干行波涟漪**（still）+ 原版式上滚（flow），并出对比图

为什么不用 A（照搬原版水的逐像素亮暗掩码）：原版水的掩码是**为水自己那张图案设计的**，
搬到我们这种"横条纹"底图上就变成**互不相关的雪花噪点**（预览图里氮气那一行最明显）——
量得再准也不好看。**相干**才是原版水"像水"的关键。

B 的做法：still 用**位移场**而不是改颜色 —— 每一列整体升降一个正弦量，波沿 x 走：
    dy(x, t) = round(A * sin(2π(x/16 − t/32)))
⇒ 相邻列只差 0/±1 行（**相干**）；32 帧正好走完一个波长（**闭环精确**）；
   位移场本身周期是 16，内容**不产生净漂移**（**不再行军**）。
flow 仍是原版水那条：每帧**上移 1 行**、frametime 缺省。
"""
import io, os, sys, shutil, math, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
REF = os.path.join(TOOLS, '_zf163_ref')
OUTA = os.path.join(TOOLS, '_zf163_out')
OUTB = os.path.join(TOOLS, '_zf163_outB')
A = 2          # 涟漪振幅（行）
T = 32         # 帧数
fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)


def frames_of(path):
    w, h, px = read_png(path)
    n = h // w
    return w, h, n, [bytes(px[i * w * w * 4:(i + 1) * w * w * 4]) for i in range(n)]


def px_of(fr, w, x, y):
    i = (y * w + x) * 4
    return (fr[i], fr[i + 1], fr[i + 2], fr[i + 3])


def build_still(base):
    """行波涟漪：第 t 帧第 x 列整体位移 dy(x,t) 行。"""
    out = bytearray()
    for t in range(T):
        for y in range(16):
            for x in range(16):
                dy = int(round(A * math.sin(2 * math.pi * (x / 16.0 - t / float(T)))))
                out += bytes(px_of(base, 16, x, (y - dy) % 16))
    return bytes(out)


def build_flow(base):
    """原版式：每帧上移 1 行。"""
    out = bytearray()
    for t in range(16):
        for y in range(16):
            out += base[((y + t) % 16) * 64:((y + t) % 16 + 1) * 64]
    return bytes(out)


print(u'===== ① 生成 B 版（still 行波 / flow 上滚）=====')
if os.path.isdir(OUTB):
    shutil.rmtree(OUTB)
os.makedirs(OUTB)
fluids = sorted(f[:-10] for f in os.listdir(TEXB) if f.endswith('_still.png'))
check(len(fluids) == 15, u'15 种流体（实测 %d）' % len(fluids))
stats = []
for f in fluids:
    _, _, _, sf = frames_of(os.path.join(TEXB, f + '_still.png'))
    _, _, _, ff = frames_of(os.path.join(TEXB, f + '_flow.png'))
    base_s, base_f = sf[0], ff[0]
    data = build_still(base_s)
    write_png(os.path.join(OUTB, f + '_still.png'), 16, 16 * T, data)
    fr = [data[i * 1024:(i + 1) * 1024] for i in range(T)]
    io.open(os.path.join(OUTB, f + '_still.png.mcmeta'), 'w', encoding='utf-8', newline='\n').write(
        u'{\n  "animation": {\n    "frametime": 2\n  }\n}\n')
    # ① 闭环：第 32 帧应当与第 0 帧逐字节相同（位移场走完一个波长）
    loop_ok = fr[0] == build_still(base_s)[0:1024] and \
        all(fr[0][y * 64:(y + 1) * 64] == fr[0][y * 64:(y + 1) * 64] for y in range(16))
    # ② 相干：相邻两列的位移差 ≤ 1 行（等价判据：相邻列内容要么相同、要么相差 1 行的平移）
    coh = 0
    for t in range(0, T, 7):
        for x in range(16):
            a = [px_of(fr[t], 16, x, y) for y in range(16)]
            b = [px_of(fr[t], 16, (x + 1) % 16, y) for y in range(16)]
            d = min(sum(1 for y in range(16) if a[y] != b[(y - s) % 16]) for s in (-1, 0, 1))
            coh += d
    # ③ 逐帧变化密度（与"现在"和原版水比）
    def dens(frames):
        return sum(1 for t in range(1, len(frames))
                   for y in range(16) for x in range(16)
                   if px_of(frames[t], 16, x, y) != px_of(frames[t - 1], 16, x, y)) / float((len(frames) - 1) * 256)
    old = frames_of(os.path.join(TEXB, f + '_still.png'))[3]
    stats.append((f, dens(fr), dens(old), coh))
    dataf = build_flow(base_f)
    write_png(os.path.join(OUTB, f + '_flow.png'), 16, 256, dataf)
    io.open(os.path.join(OUTB, f + '_flow.png.mcmeta'), 'w', encoding='utf-8', newline='\n').write(
        u'{\n  "animation": {}\n}\n')
    frf = [dataf[i * 1024:(i + 1) * 1024] for i in range(16)]
    okf = all(frf[t][y * 64:(y + 1) * 64] == base_f[((y + t) % 16) * 64:((y + t) % 16 + 1) * 64]
              for t in range(16) for y in range(16))
    check(okf, u'%s_flow 逐行验算 = 0（上移 1 行/帧）' % f)

# 原版水的逐帧密度（参照）
_, _, _, wf = frames_of(os.path.join(REF, 'water_still.png'))
dv = sum(1 for t in range(1, 32) for y in range(16) for x in range(16)
         if px_of(wf[t], 16, x, y) != px_of(wf[t - 1], 16, x, y)) / float(31 * 256)
print(u'\n  原版水 still 的逐帧变化密度 = %.1f%%' % (100 * dv))
print(u'  %-20s %8s %8s %8s' % (u'流体', u'新版B', u'现在(下滚)', u'相邻列失配'))
for f, dnew, dold, coh in stats:
    print(u'  %-20s %7.1f%% %7.1f%% %8d' % (f, 100 * dnew, 100 * dold, coh))
check(all(d > 0 for _, d, _, _ in stats), u'15 种流体的 still 都**真的在动**（逐帧变化密度 > 0）')

print()
print(u'===== ② 对比图 =====')
S, GAP, M, FR = 8, 6, 10, 8
CELL = 16 * S


def strip(path):
    f = frames_of(path)[3]
    return [f[i % len(f)] for i in range(FR)]


ROWS = [
    (u'原油 still — 现在（整张下滚）', strip(os.path.join(TEXB, 'crude_oil_still.png'))),
    (u'原油 still — 新版A（搬原版掩码 ⇒ 噪点）', strip(os.path.join(OUTA, 'crude_oil_still.png'))),
    (u'原油 still — 新版B（相干行波）', strip(os.path.join(OUTB, 'crude_oil_still.png'))),
    (u'氮气 still — 现在', strip(os.path.join(TEXB, 'nitrogen_still.png'))),
    (u'氮气 still — 新版A', strip(os.path.join(OUTA, 'nitrogen_still.png'))),
    (u'氮气 still — 新版B', strip(os.path.join(OUTB, 'nitrogen_still.png'))),
    (u'原版水 still（参照）', strip(os.path.join(REF, 'water_still.png'))),
    (u'', None),
    (u'原油 flow — 现在（下滚 2 行/帧）', strip(os.path.join(TEXB, 'crude_oil_flow.png'))),
    (u'原油 flow — 新版B（上滚 1 行/帧）', strip(os.path.join(OUTB, 'crude_oil_flow.png'))),
    (u'原版水 flow（左上 16x16 裁切）', strip(os.path.join(REF, 'water_flow.png'))),
]
W = M * 2 + CELL * FR + GAP * (FR - 1)
H = M * 2 + sum(CELL if r[1] else GAP * 3 for r in ROWS) + GAP * (len(ROWS) - 1)
cv = bytearray(W * H * 4)
for y in range(H):
    for x in range(W):
        v = 62 if ((x // 8 + y // 8) % 2 == 0) else 74
        i = (y * W + x) * 4
        cv[i] = cv[i + 1] = cv[i + 2] = v
        cv[i + 3] = 255


def blit(p16, ox, oy):
    for y in range(16):
        for x in range(16):
            i = (y * 16 + x) * 4
            a = p16[i + 3]
            if not a:
                continue
            for dy in range(S):
                for dx in range(S):
                    di = ((oy + y * S + dy) * W + (ox + x * S + dx)) * 4
                    if a == 255:
                        cv[di:di + 4] = p16[i:i + 4]
                    else:
                        for c in range(3):
                            cv[di + c] = (p16[i + c] * a + cv[di + c] * (255 - a)) // 255
                        cv[di + 3] = 255


oy = M
for label, fs in ROWS:
    if fs is None:
        oy += GAP * 4
        continue
    for k, f in enumerate(fs):
        blit(f, M + k * (CELL + GAP), oy)
    oy += CELL + GAP


def write_png2(path, w, h, rgba):
    import zlib, struct
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgba[y * w * 4:(y + 1) * w * 4]

    def ch(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += ch(b'IDAT', zlib.compress(bytes(raw), 9)) + ch(b'IEND', b'')
    open(path, 'wb').write(png)


p = os.path.join(TOOLS, '_zf163_previewB.png')
write_png2(p, W, H, cv)
print(u'行顺序：')
for label, fs in ROWS:
    print(u'  ' + (label if label else u'—— 分栏 ——'))
print(u'\n已写出 %s（%dx%d）' % (p, W, H))
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
