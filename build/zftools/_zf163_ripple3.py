# -*- coding: utf-8 -*-
r"""_zf163_ripple3.py —— **D 版：亚像素驻波**（行间线性插值）

C 版（整数行位移）留下的毛病，是量出来才看见的：
    `dy(x,t) = round(2*cos*sin)` 只有 5 档取值 ⇒ **32 帧里 19 对相邻帧逐字节相同**
    （`_zf163_apply3.py` 的实测），也就是"一顿一顿地涌"。
根因不是判据、是**量化**：整数行位移在 16 高的图上一共就那么几档。

D 版把位移换成**实数**，行与行之间按小数部分线性插值：
    w(x, t) = A * cos(2πx/16) * sin(2πt/32)          （实数，单位 = 行）
    输出像素 (x,y) = (1-f)*base(x, i) + f*base(x, i+1)， i = floor(y-w)， f = frac(y-w)
  · t=0 ⇒ w ≡ 0 ⇒ **第 0 帧与原始贴图逐字节相同**；
  · w 连续变化 ⇒ **32 帧各不相同**（这一条正是 C 版做不到的）；
  · 幅度 |w| ≤ 2 行、相邻列 |Δw| ≤ 0.79 行（相干）、32 帧精确闭环。
"""
import io, os, sys, shutil, math
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
PRE = os.path.join(TOOLS, 'zf163_pre')
REF = os.path.join(TOOLS, '_zf163_ref')
OUTC = os.path.join(TOOLS, '_zf163_outC')
OUTD = os.path.join(TOOLS, '_zf163_outD')
A, T = 2.0, 32

fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)


def frames_of(path):
    w, h, px = read_png(path)
    n = h // w
    return w, h, n, [bytes(px[i * w * w * 4:(i + 1) * w * w * 4]) for i in range(n)]


def rgb(fr, x, y):
    i = (y * 16 + x) * 4
    return fr[i], fr[i + 1], fr[i + 2], fr[i + 3]


def w_of(x, t):
    return A * math.cos(2 * math.pi * x / 16.0) * math.sin(2 * math.pi * t / float(T))


def build(base):
    out = bytearray()
    for t in range(T):
        for y in range(16):
            for x in range(16):
                w = w_of(x, t)
                p = y - w
                i = int(math.floor(p))
                f = p - i
                a = rgb(base, x, i % 16)
                b = rgb(base, x, (i + 1) % 16)
                out += bytes((
                    int(round(a[0] * (1 - f) + b[0] * f)),
                    int(round(a[1] * (1 - f) + b[1] * f)),
                    int(round(a[2] * (1 - f) + b[2] * f)),
                    int(round(a[3] * (1 - f) + b[3] * f))))
    return bytes(out)


print(u'===== ① 位移场（实数，行）=====')
for t in (0, 4, 8, 12, 16, 24):
    print(u'  t=%-3d ' % t + u' '.join(u'%+.2f' % w_of(x, t) for x in range(16)))
check(all(abs(w_of(x, 0)) < 1e-12 for x in range(16)), u't=0 时位移处处为 0（第 0 帧 = 原始贴图）')
check(max(abs(w_of(x, t)) for t in range(T) for x in range(16)) <= A + 1e-9, u'最大位移 ≤ %.1f 行' % A)
check(max(abs(w_of(x + 1, t) - w_of(x, t)) for t in range(T) for x in range(15)) <= 0.8,
      u'相邻列位移差 ≤ 0.8 行（相干）')
check(all(abs(w_of(x, T) - w_of(x, 0)) < 1e-12 for x in range(16)), u'32 帧精确闭环（w(t=32) == w(t=0)）')

print()
print(u'===== ② 生成 D 版 =====')
if os.path.isdir(OUTD):
    shutil.rmtree(OUTD)
os.makedirs(OUTD)
fluids = sorted(f[:-10] for f in os.listdir(PRE) if f.endswith('_still.png'))
check(len(fluids) == 15, u'15 种（实测 %d）' % len(fluids))
stats = []
for f in fluids:
    _, _, _, pf = frames_of(os.path.join(PRE, f + '_still.png'))
    base = pf[0]
    data = build(base)
    write_png(os.path.join(OUTD, f + '_still.png'), 16, 16 * T, data)
    fr = [data[i * 1024:(i + 1) * 1024] for i in range(T)]
    if fr[0] != base:
        fails.append(u'%s 第 0 帧 != 原始底图' % f)
    # 逐帧逐像素独立重算
    bad = 0
    for t in range(T):
        for y in range(16):
            for x in range(16):
                w = w_of(x, t)
                p = y - w
                i = int(math.floor(p)); ff = p - i
                a = rgb(base, x, i % 16); b = rgb(base, x, (i + 1) % 16)
                want = bytes((int(round(a[0] * (1 - ff) + b[0] * ff)),
                              int(round(a[1] * (1 - ff) + b[1] * ff)),
                              int(round(a[2] * (1 - ff) + b[2] * ff)),
                              int(round(a[3] * (1 - ff) + b[3] * ff))))
                if fr[t][(y * 16 + x) * 4:(y * 16 + x) * 4 + 4] != want:
                    bad += 1
    same = sum(1 for t in range(1, T) if fr[t] == fr[t - 1])
    # 变化量：改动的像素比例 + 平均 |ΔRGB|
    npx = 0
    dsum = 0
    for t in range(1, T):
        for k in range(0, 1024, 4):
            a = fr[t - 1][k:k + 3]; b = fr[t][k:k + 3]
            if a != b:
                npx += 1
                dsum += (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) / 3.0
    stats.append((f, bad, same, npx / float((T - 1) * 256), dsum / max(1, npx)))
check(all(b == 0 for _, b, _, _, _ in stats), u'15 种 x 32 帧 x 256 像素 全部逐像素等于插值公式（不符 %d）' % sum(b for _, b, _, _, _ in stats))
check(all(s == 0 for _, _, s, _, _ in stats), u'15 种的 32 帧**两两相邻都不相同**（相同的对数 = %d）' % sum(s for _, _, s, _, _ in stats))
check(all(frames_of(os.path.join(OUTD, f + '_still.png'))[3][0]
          == frames_of(os.path.join(PRE, f + '_still.png'))[3][0] for f in fluids),
      u'15 种的第 0 帧都与原始贴图逐字节相同')

print(u'\n  %-20s %10s %10s' % (u'流体', u'改动像素比', u'平均|ΔRGB|'))
for f, _, _, d, de in stats:
    print(u'  %-20s %9.1f%% %10.2f' % (f, 100 * d, de))

# 原版水的同样两个数（拿它的 32 帧参考条量）
_, _, _, wf = frames_of(os.path.join(REF, 'water_still.png'))
npx = dsum = 0
for t in range(1, 32):
    for k in range(0, 1024, 4):
        a = wf[t - 1][k:k + 3]; b = wf[t][k:k + 3]
        if a != b:
            npx += 1
            dsum += (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) / 3.0
print(u'\n  原版 water_still：改动像素 **%.1f%%**、平均 |ΔRGB| **%.2f**'
      % (100 * npx / float(31 * 256), dsum / max(1, npx)))
print(u'  （我们老做法：改动像素 49~98%%）')

print()
print(u'===== ③ 对比图（取 t=4..11 这一段，C 版的"顿"正好在这一段）=====')
S, GAP, M, FR, OFF = 8, 6, 10, 8, 4
CELL = 16 * S


def strip(path, off=OFF):
    f = frames_of(path)[3]
    return [f[(off + i) % len(f)] for i in range(FR)]


ROWS = [
    (u'原油 still — 原始贴图（= D 版第 0 帧）', strip(os.path.join(PRE, 'crude_oil_still.png'), 0)),
    (u'原油 still — C 版整数驻波（这一版有"顿"）', strip(os.path.join(OUTC, 'crude_oil_still.png'))),
    (u'原油 still — D 版亚像素驻波', strip(os.path.join(OUTD, 'crude_oil_still.png'))),
    (u'氮气 still — 原始贴图', strip(os.path.join(PRE, 'nitrogen_still.png'), 0)),
    (u'氮气 still — C 版整数驻波', strip(os.path.join(OUTC, 'nitrogen_still.png'))),
    (u'氮气 still — D 版亚像素驻波', strip(os.path.join(OUTD, 'nitrogen_still.png'))),
    (u'原版水 still（参照）', strip(os.path.join(REF, 'water_still.png'))),
]
W = M * 2 + CELL * FR + GAP * (FR - 1)
H = M * 2 + CELL * len(ROWS) + GAP * (len(ROWS) - 1)
cv = bytearray(W * H * 4)
for y in range(H):
    for x in range(W):
        v = 62 if ((x // 8 + y // 8) % 2 == 0) else 74
        i = (y * W + x) * 4
        cv[i] = cv[i + 1] = cv[i + 2] = v
        cv[i + 3] = 255
for r, (label, fs) in enumerate(ROWS):
    oy = M + r * (CELL + GAP)
    for k, f in enumerate(fs):
        for y in range(16):
            for x in range(16):
                i = (y * 16 + x) * 4
                a = f[i + 3]
                if not a:
                    continue
                for dyy in range(S):
                    for dxx in range(S):
                        di = ((oy + y * S + dyy) * W + (M + k * (CELL + GAP) + x * S + dxx)) * 4
                        if a == 255:
                            cv[di:di + 4] = f[i:i + 4]
                        else:
                            for c in range(3):
                                cv[di + c] = (f[i + c] * a + cv[di + c] * (255 - a)) // 255
                            cv[di + 3] = 255


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


p = os.path.join(TOOLS, '_zf163_previewD.png')
write_png2(p, W, H, cv)
print(u'行顺序：')
for label, _ in ROWS:
    print(u'  ' + label)
print(u'\n已写出 %s（%dx%d）' % (p, W, H))
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
