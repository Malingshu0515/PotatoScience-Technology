# -*- coding: utf-8 -*-
r"""_zf163_apply4.py —— 上线 D 版（亚像素驻波）+ 常驻门换成 v2"""
import io, os, sys, json, math, hashlib, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
SRC = os.path.join(TOOLS, '_zf163_outD')
PRE = os.path.join(TOOLS, 'zf163_pre')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
GATE = os.path.join(TOOLS, '_zf135_fluidcheck.py')
A, T = 2.0, 32
fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

def sha1b(b):
    return hashlib.sha1(b).hexdigest()

def frames_of(path):
    w, h, px = read_png(path)
    return [bytes(px[i * w * w * 4:(i + 1) * w * w * 4]) for i in range(h // w)]

print(u'===== ① 上线 15 张 still（逐字节复制）=====')
names = sorted(f for f in os.listdir(SRC) if f.endswith('.png'))
check(len(names) == 15, u'暂存 15 张（实测 %d）' % len(names))
ok = 0
for n in names:
    data = open(os.path.join(SRC, n), 'rb').read()
    open(os.path.join(TEXB, n), 'wb').write(data)
    if sha1b(open(os.path.join(TEXB, n), 'rb').read()) == sha1b(data):
        ok += 1
check(ok == 15, u'15 张逐字节上线并回读（实测 %d）' % ok)

print()
print(u'===== ② 上线后复验（第 0 帧 / 亚像素公式 / 相邻帧全不同）=====')
b0 = bad = same = 0
for f in sorted(n[:-10] for n in names):
    newf = frames_of(os.path.join(TEXB, f + '_still.png'))
    base = frames_of(os.path.join(PRE, f + '_still.png'))[0]
    if newf[0] != base:
        b0 += 1
    for t in range(T):
        for y in range(16):
            for x in range(16):
                w = A * math.cos(2 * math.pi * x / 16.0) * math.sin(2 * math.pi * t / float(T))
                p = y - w
                i = int(math.floor(p)); fr_ = p - i
                ga = base[(i % 16) * 64 + x * 4:(i % 16) * 64 + x * 4 + 4]
                gb = base[((i + 1) % 16) * 64 + x * 4:((i + 1) % 16) * 64 + x * 4 + 4]
                want = bytes(int(round(ga[c] * (1 - fr_) + gb[c] * fr_)) for c in range(4))
                if newf[t][(y * 16 + x) * 4:(y * 16 + x) * 4 + 4] != want:
                    bad += 1
    same += sum(1 for t in range(1, T) if newf[t] == newf[t - 1])
check(b0 == 0, u'15 种第 0 帧 == 原始贴图（不符 %d）' % b0)
check(bad == 0, u'15 种 x 32 帧 x 256 像素 == 亚像素插值（不符 %d）' % bad)
check(same == 0, u'32 帧两两相邻都不相同（相同的对数 = %d）' % same)

print()
print(u'===== ③ 常驻门换成 v2（判据 (3) 恢复"逐对必须不同"、判据 (4) 改成亚像素）=====')
NEW = open(os.path.join(TOOLS, '_zf163_gate_v2.py'), 'rb').read()
io.open(GATE, 'wb').write(NEW)
import ast
ast.parse(io.open(GATE, encoding='utf-8').read())
check(True, u'_zf135_fluidcheck.py 已换成 v2 且能过 ast.parse（%d 字节）' % len(NEW))

print()
print(u'===== ④ 跑门 =====')
r = subprocess.run([sys.executable, GATE], cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = r.stdout.decode('utf-8', 'replace')
io.open(os.path.join(TOOLS, '_zf163_gate.txt'), 'w', encoding='utf-8', newline='\n').write(out)
print(u'\n'.join([l for l in out.splitlines() if l.startswith(u'  [OK]') or u'失败项' in l or u'最大比值' in l]))
check(r.returncode == 0, u'_zf135_fluidcheck.py rc=0（实测 %d）' % r.returncode)

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
