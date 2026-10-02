# -*- coding: utf-8 -*-
r"""_zf163_apply2.py —— 把 B 版（相干行波涟漪 + 原版式上滚）上线，并把常驻门跟到新事实

（文件名带 2：`_zf163_apply.py` 被我自己的 `Remove-Item` 误删了，重建时就地改名，见汇报。）
"""
import io, json, os, sys, shutil, hashlib, math
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
SRC = os.path.join(TOOLS, '_zf163_outB')
PRE = os.path.join(TOOLS, 'zf163_pre')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
GATE = os.path.join(TOOLS, '_zf135_fluidcheck.py')
DOCS = os.path.join(ROOT, 'docs')

fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

def sha1b(b):
    return hashlib.sha1(b).hexdigest()

print(u'===== ① 改前备份 -> zf163_pre =====')
os.makedirs(PRE, exist_ok=True)
names = sorted(os.listdir(SRC))
check(len(names) == 60, u'暂存目录 60 个文件（30 PNG + 30 mcmeta，实测 %d）' % len(names))
n_bak = 0
for n in names:
    a = os.path.join(TEXB, n)
    if not os.path.exists(a):
        check(False, u'改前件不在：%s' % n)
        continue
    b = os.path.join(PRE, n)
    shutil.copy2(a, b)
    if sha1b(open(a, 'rb').read()) == sha1b(open(b, 'rb').read()):
        n_bak += 1
check(n_bak == 60, u'60 份改前件逐字节抄进 zf163_pre（实测 %d）' % n_bak)
shutil.copy2(GATE, os.path.join(PRE, '_zf135_fluidcheck.py'))
for rel in [u'贴图清单.md', u'开发档案.md', u'UpdateAnnouncement_EN.md']:
    shutil.copy2(os.path.join(DOCS, rel), os.path.join(PRE, 'docs__' + rel))
io.open(os.path.join(PRE, '_sha1.txt'), 'w', encoding='utf-8', newline='\n').write(
    u'\n'.join(u'%s\t%s' % (n, sha1b(open(os.path.join(PRE, n), 'rb').read()))
               for n in sorted(os.listdir(PRE)) if n != '_sha1.txt') + u'\n')
check(True, u'备份清单写进 zf163_pre/_sha1.txt')

print()
print(u'===== ② 上线（逐字节复制）=====')
for n in names:
    data = open(os.path.join(SRC, n), 'rb').read()
    open(os.path.join(TEXB, n), 'wb').write(data)
    if sha1b(open(os.path.join(TEXB, n), 'rb').read()) != sha1b(data):
        fails.append(u'%s 复制后回读不一致' % n)
check(not [f for f in fails if u'回读' in f], u'60 份逐字节复制并回读')

print()
print(u'===== ③ 产物体检（尺寸 / 帧数 / mcmeta / 位移公式）=====')
fluids = sorted(set(n[:-10] for n in names if n.endswith('_still.png')))
check(len(fluids) == 15, u'15 种流体（实测 %d）' % len(fluids))
A, T = 2, 32
for f in fluids:
    for sfx, frames_expect, ft_expect in ((u'_still', 32, 2), (u'_flow', 16, None)):
        p = os.path.join(TEXB, f + sfx + '.png')
        w, h, px = read_png(p)
        nf = h // w
        meta = json.loads(io.open(p + '.mcmeta', encoding='utf-8').read())
        ft = meta.get('animation', {}).get('frametime')
        if (w, nf) != (16, frames_expect):
            fails.append(u'%s%s 尺寸/帧数 %dx%d 帧（期望 16 x %d 帧）' % (f, sfx, w, nf, frames_expect))
        if ft != ft_expect:
            fails.append(u'%s%s frametime = %s（期望 %s）' % (f, sfx, ft, ft_expect))
check(not [x for x in fails if u'尺寸/帧数' in x or u'frametime' in x],
      u'30 张：still 16x512/32 帧/frametime 2；flow 16x256/16 帧/frametime 缺省')

bad_col = 0
for f in fluids:
    w, h, px = read_png(os.path.join(TEXB, f + '_still.png'))

    def col(fr, x):
        return [bytes(px[((fr * 16) + y) * 64 + x * 4:((fr * 16) + y) * 64 + x * 4 + 4]) for y in range(16)]
    base = [col(0, x) for x in range(16)]
    for t in range(T):
        for x in range(16):
            dy = int(round(A * math.sin(2 * math.pi * (x / 16.0 - t / float(T)))))
            if col(t, x) != [base[x][(y - dy) % 16] for y in range(16)]:
                bad_col += 1
check(bad_col == 0, u'still：15 种 x 32 帧 x 16 列全部等于行波公式（不符 %d 列）' % bad_col)

bad_flow = 0
for f in fluids:
    w, h, px = read_png(os.path.join(TEXB, f + '_flow.png'))
    rows = [[bytes(px[(fr * 16 + y) * 64:(fr * 16 + y) * 64 + 64]) for y in range(16)] for fr in range(16)]
    for t in range(16):
        if rows[t] != [rows[0][(y + t) % 16] for y in range(16)]:
            bad_flow += 1
check(bad_flow == 0, u'flow：16 帧全部等于"底图每帧上移 1 行"（不符 %d 帧）' % bad_flow)

print()
print(u'===== ④ 常驻门 `_zf135_fluidcheck.py` 换成更严的一套 =====')
NEW = open(os.path.join(TOOLS, '_zf163_gate_new.py'), 'rb').read()
io.open(GATE, 'wb').write(NEW)
import ast
ast.parse(io.open(GATE, encoding='utf-8').read())
check(True, u'_zf135_fluidcheck.py 已换成新判据且能过 ast.parse（%d 字节）' % len(NEW))

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
