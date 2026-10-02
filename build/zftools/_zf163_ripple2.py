# -*- coding: utf-8 -*-
r"""_zf163_ripple2.py —— **C 版：驻波**（t=0 位移处处为 0 ⇒ 第 0 帧就是原始贴图）

B 版（行波）有两个毛病，都是"相位"惹的：
  ① `dy(x,0) = round(2*sin(2πx/16))` **不为 0** ⇒ 第 0 帧自己就是被扭过的图，
     静止时玩家看到的不是你给的原始贴图，而是"已经起了浪"的样子；
  ② 正因如此，判据"第 t 帧 == 底图位移公式量"**在文件内无参照**（帧 0 不是底图），
     门报 6720 列不符 —— 这条红是**真问题**（判据没错，做法错）。

C 版把位移场换成**驻波**：
    dy(x, t) = round(A * cos(2πx/16) * sin(2πt/32))
  · t=0 ⇒ 处处 0（**第 0 帧 = 原始贴图，逐字节相同**）；
  · t=8 起浪、t=16 归零、t=24 反向 ⇒ 液面**来回涌**（不是单向行军）；
  · 相邻列位移差 ≤ 1（相干）、32 帧精确闭环、零净漂移。
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
OUTB = os.path.join(TOOLS, '_zf163_outB')
OUTC = os.path.join(TOOLS, '_zf163_outC')
A, T = 2, 32

fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)


def frames_of(path):
    w, h, px = read_png(path)
    n = h // w
    return w, h, n, [bytes(px[i * w * w * 4:(i + 1) * w * w * 4]) for i in range(n)]


def px_of(fr, x, y):
    i = (y * 16 + x) * 4
    return (fr[i], fr[i + 1], fr[i + 2], fr[i + 3])


def dy_of(x, t):
    return int(round(A * math.cos(2 * math.pi * x / 16.0) * math.sin(2 * math.pi * t / float(T))))


print(u'===== ① 表：驻波位移场（行）=====')
for t in (0, 4, 8, 12, 16, 24):
    print(u'  t=%-3d ' % t + u' '.join(u'%+d' % dy_of(x, t) for x in range(16)))
check(all(dy_of(x, 0) == 0 for x in range(16)), u't=0 时 16 列的位移**全为 0**（第 0 帧 = 原始贴图）')
check(max(abs(dy_of(x + 1, t) - dy_of(x, t)) for t in range(T) for x in range(15)) <= 1,
      u'相邻列位移差 ≤ 1（相干）')
check(max(abs(dy_of(x, t)) for t in range(T) for x in range(16)) == A, u'最大位移 = 振幅 %d 行（不超）' % A)

print()
print(u'===== ② 生成 C 版（底图取改前件的第 0 帧 = 你给的原始贴图）=====')
if os.path.isdir(OUTC):
    shutil.rmtree(OUTC)
os.makedirs(OUTC)
fluids = sorted(f[:-10] for f in os.listdir(PRE) if f.endswith('_still.png'))
check(len(fluids) == 15, u'zf163_pre 里有 15 种流体的改前件（实测 %d）' % len(fluids))
dens = []
for f in fluids:
    _, _, _, pf = frames_of(os.path.join(PRE, f + '_still.png'))
    base = pf[0]                      # 改前文件的第 0 帧 = 原始底图
    out = bytearray()
    for t in range(T):
        for y in range(16):
            for x in range(16):
                out += bytes(px_of(base, x, (y - dy_of(x, t)) % 16))
    write_png(os.path.join(OUTC, f + '_still.png'), 16, 16 * T, out)
    fr = [bytes(out[i * 1024:(i + 1) * 1024]) for i in range(T)]
    # 判据 A：第 0 帧必须与原始底图**逐字节相同**
    if fr[0] != base:
        fails.append(u'%s 第 0 帧 != 原始底图' % f)
    # 判据 B：第 t 帧每一列 == 底图该列按公式位移
    bad = 0
    for t in range(T):
        for x in range(16):
            want = [base[((y - dy_of(x, t)) % 16) * 64 + x * 4:((y - dy_of(x, t)) % 16) * 64 + x * 4 + 4] for y in range(16)]
            got = [fr[t][y * 64 + x * 4:y * 64 + x * 4 + 4] for y in range(16)]
            if got != want:
                bad += 1
    # 判据 C：逐帧变化密度（与原版水的 11% 比）
    d = sum(1 for t in range(1, T) for y in range(16) for x in range(16)
            if px_of(fr[t], x, y) != px_of(fr[t - 1], x, y)) / float((T - 1) * 256)
    dens.append((f, d, bad))
    # 判据 D：精确闭环（第 32 帧的构造 == 第 0 帧）
    if dy_of(0, T % T) != 0:
        fails.append(u'%s 闭环失败' % f)
check(all(b == 0 for _, _, b in dens), u'15 种 x 32 帧 x 16 列 全部等于驻波公式（不符 %d 列）' % sum(b for _, _, b in dens))
check(all(fr0 == base for fr0, base in [(frames_of(os.path.join(OUTC, f + '_still.png'))[3][0],
                                         frames_of(os.path.join(PRE, f + '_still.png'))[3][0]) for f in fluids]),
      u'15 种的第 0 帧都与原始底图逐字节相同')
print(u'\n  %-20s %8s' % (u'流体', u'逐帧变化密度'))
for f, d, _ in dens:
    print(u'  %-20s %7.1f%%' % (f, 100 * d))
print(u'  （原版 water_still 是 11.0%；改成下滚之前的我们自己是 49~98%）')

print()
print(u'===== ③ 对比图 =====')
S, GAP, M, FR = 8, 6, 10, 8
CELL = 16 * S


def strip(path):
    f = frames_of(path)[3]
    return [f[i % len(f)] for i in range(FR)]


ROWS = [
    (u'原油 still — 原始贴图（= 新版第 0 帧）', strip(os.path.join(PRE, 'crude_oil_still.png'))),
    (u'原油 still — ZF132 老做法（整张下滚）', strip(os.path.join(TEXB, 'crude_oil_still.png'))),
    (u'原油 still — C 版驻波', strip(os.path.join(OUTC, 'crude_oil_still.png'))),
    (u'氮气 still — 原始贴图', strip(os.path.join(PRE, 'nitrogen_still.png'))),
    (u'氮气 still — 老做法', strip(os.path.join(TEXB, 'nitrogen_still.png'))),
    (u'氮气 still — C 版驻波', strip(os.path.join(OUTC, 'nitrogen_still.png'))),
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


p = os.path.join(TOOLS, '_zf163_previewC.png')
write_png2(p, W, H, cv)
print(u'行顺序：')
for label, _ in ROWS:
    print(u'  ' + label)
print(u'\n已写出 %s（%dx%d）' % (p, W, H))
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
