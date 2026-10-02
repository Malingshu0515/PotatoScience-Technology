# -*- coding: utf-8 -*-
r"""_zf163_apply3.py —— 上线 C 版（驻波），并把常驻门的公式与"静止帧"例外一起跟平

三件事：
  ① 15 张 `*_still.png` 换成 `_zf163_outC/`（**flow 不动** —— B 版的 flow 已经是对的：1 行/帧上移）；
  ② 判据 A：新版第 0 帧必须与**改前件的第 0 帧**（= 用户给的原始贴图）逐字节相同；
     判据 B：第 t 帧每一列 == 底图该列按驻波公式位移；
  ③ 常驻门 `_zf135_fluidcheck.py`：把公式从"行波"改成"驻波"，
     并给判据 (3) 加一条**有理由的例外** —— 驻波在过零处（t=0,1,16,17,31）
     **位移场恒为 0**，那几帧与相邻帧逐字节相同是**数学上必然**的，
     只有"公式说该动却没动"才算红。
"""
import io, json, os, sys, shutil, hashlib, math, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
SRC = os.path.join(TOOLS, '_zf163_outC')
PRE = os.path.join(TOOLS, 'zf163_pre')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
GATE = os.path.join(TOOLS, '_zf135_fluidcheck.py')
A, T = 2, 32

fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)


def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def frames_of(path):
    w, h, px = read_png(path)
    n = h // w
    return w, h, n, [bytes(px[i * w * w * 4:(i + 1) * w * w * 4]) for i in range(n)]


def dy_of(x, t):
    return int(round(A * math.cos(2 * math.pi * x / 16.0) * math.sin(2 * math.pi * t / float(T))))


print(u'===== ① 上线 15 张 still（逐字节复制）=====')
names = sorted(f for f in os.listdir(SRC) if f.endswith('.png'))
check(len(names) == 15, u'暂存 15 张（实测 %d）' % len(names))
for n in names:
    data = open(os.path.join(SRC, n), 'rb').read()
    open(os.path.join(TEXB, n), 'wb').write(data)
    check(sha1b(open(os.path.join(TEXB, n), 'rb').read()) == sha1b(data), u'%s 逐字节上线' % n)

print()
print(u'===== ② 判据：第 0 帧 == 原始贴图；每一列 == 驻波公式 =====')
fluids = sorted(n[:-10] for n in names)
bad0 = badcol = 0
rest = []
for f in fluids:
    _, _, _, newf = frames_of(os.path.join(TEXB, f + '_still.png'))
    _, _, _, pref = frames_of(os.path.join(PRE, f + '_still.png'))
    base = pref[0]
    if newf[0] != base:
        bad0 += 1
    for t in range(T):
        for x in range(16):
            want = [base[((y - dy_of(x, t)) % 16) * 64 + x * 4:((y - dy_of(x, t)) % 16) * 64 + x * 4 + 4] for y in range(16)]
            got = [newf[t][y * 64 + x * 4:y * 64 + x * 4 + 4] for y in range(16)]
            if got != want:
                badcol += 1
    r = [t for t in range(1, T) if newf[t] == newf[t - 1]]
    rest.append((f, r))
check(bad0 == 0, u'15 种的**第 0 帧**都与原始贴图逐字节相同（不符 %d）' % bad0)
check(badcol == 0, u'15 种 x 32 帧 x 16 列 全部等于驻波公式（不符 %d 列）' % badcol)
allrest = sorted(set(t for _, r in rest for t in r))
print(u'  "与上一帧逐字节相同"的帧号（15 种完全一致）：%s' % allrest)
check(all(all(dy_of(x, t) == 0 for x in range(16)) for t in allrest),
      u'这些帧**公式上就是零位移**（t=%s）⇒ 相同是数学必然，不是"没动"' % allrest)

print()
print(u'===== ③ 常驻门跟平 =====')
g = io.open(GATE, encoding='utf-8').read()
pairs = [
    (u'                dy = int(round(RIPPLE_A * math.sin(2 * math.pi * (x / 16.0 - t / float(FRAMES_STILL)))))',
     u'                dy = int(round(RIPPLE_A * math.cos(2 * math.pi * x / 16.0)\n'
     u'                                     * math.sin(2 * math.pi * t / float(FRAMES_STILL))))'),
    (u'所以本轮改成：**still = 相干行波涟漪**（每一列整体升降 `round(2*sin(2pi(x/16 - t/32)))` 行、\n零净漂移、32 帧闭环），**flow = 每帧上移 1 行**。',
     u'所以本轮改成：**still = 相干驻波**（每一列整体升降 `round(2*cos(2pi x/16)*sin(2pi t/32))` 行、\n'
     u't=0 时位移处处为 0 ⇒ **第 0 帧就是你给的原始贴图**、零净漂移、32 帧闭环），**flow = 每帧上移 1 行**。\n\n'
     u'⚠ 驻波在过零处（t=0,1,16,17,31）**位移场恒为 0** ⇒ 那几帧与相邻帧逐字节相同是**数学必然**。\n'
     u'判据 (3) 因此写成"**只有公式说该动却没动**才算红"：允许相同，但**必须先证明公式在该帧恒为 0**。'),
    (u'''    quiet = []
    for n in anim:
        w, h, rgba = read_png(os.path.join(T, n + ".png"))
        nf = h // 16
        for t in range(1, nf):
            if bytes(rgba[(t - 1) * 1024:t * 1024]) == bytes(rgba[t * 1024:(t + 1) * 1024]):
                quiet.append(u"%s 第 %d 帧与上一帧一模一样" % (n, t))''',
     u'''    def is_rest(t):
        return all(int(round(RIPPLE_A * math.cos(2 * math.pi * x / 16.0)
                             * math.sin(2 * math.pi * t / float(FRAMES_STILL)))) == 0 for x in range(16))

    quiet = []
    for n in anim:
        w, h, rgba = read_png(os.path.join(T, n + ".png"))
        nf = h // 16
        for t in range(1, nf):
            if bytes(rgba[(t - 1) * 1024:t * 1024]) == bytes(rgba[t * 1024:(t + 1) * 1024]):
                if n.endswith("_still") and (is_rest(t) or is_rest(t - 1)):
                    continue          # 驻波过零：公式说不动，相同是对的
                quiet.append(u"%s 第 %d 帧与上一帧一模一样" % (n, t))'''),
]
for old, new in pairs:
    n = g.count(old)
    check(n == 1, u'锚点命中 1 次（实测 %d）：%s…' % (n, old.strip().splitlines()[0][:40]))
    if n == 1:
        g = g.replace(old, new)
io.open(GATE, 'w', encoding='utf-8', newline='\n').write(g)
import ast
ast.parse(io.open(GATE, encoding='utf-8').read())
check(True, u'_zf135_fluidcheck.py 改后能过 ast.parse')

print()
print(u'===== ④ 跑门 =====')
r = subprocess.run([sys.executable, GATE], cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = r.stdout.decode('utf-8', 'replace')
print(u'\n'.join(out.strip().splitlines()[-6:]))
check(r.returncode == 0, u'_zf135_fluidcheck.py rc=0（实测 %d）' % r.returncode)
io.open(os.path.join(TOOLS, '_zf163_gate.txt'), 'w', encoding='utf-8', newline='\n').write(out)

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
