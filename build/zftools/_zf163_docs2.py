# -*- coding: utf-8 -*-
r"""_zf163_docs2.py —— ZF163 文档收尾（修两个自摆的乌龙）+ 终检

两个乌龙，都是我自己写脚本时留下的：
  ① 风险号写死：`PIT` 里的标题我手写成 `### 4.168`，可脚本自己算出"下一个空号 = 4.171"
     （别的线又占了 4.168~4.170）⇒ 插进去就**撞号**了。修：把标题改成 4.171，变更行里的引用一起改。
  ② 变量名撞车：公告的**路径**叫 `ANN`，公告的**正文**后来也叫 `ANN` ⇒ 正文把路径覆盖掉，
     下一行 `read(ANN)` 就去读"一整篇公告文本"当路径（FileNotFoundError）。
     修：本脚本用 `ANN_PATH` / `ANN_TEXT`，并顺手把 `_zf163_docs.py` 里的重名也改掉。
"""
import io, os, re, sys, hashlib, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
DOCS = os.path.join(ROOT, 'docs')
ARCH = os.path.join(DOCS, u'开发档案.md')
ANN_PATH = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
BTEXB = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'block')
fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def read(p):
    return io.open(p, encoding='utf-8').read()
def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

print(u'===== ① 把撞号的 §4.168 改成 §4.171 =====')
t = read(ARCH)
OLD = u'### 4.168 【做法雷】"动画有点怪"先别调参数'
NEW = u'### 4.171 【做法雷】"动画有点怪"先别调参数'
n = t.count(OLD)
check(n == 1, u'锚点命中 1 次（实测 %d）' % n)
if n == 1:
    write(ARCH, t.replace(OLD, NEW))
t = read(ARCH)
for a, b in ((u'立 **§4.168**', u'立 **§4.171**'),):
    c = t.count(a)
    check(c == 1, u'变更行里 `%s` 命中 1 次（实测 %d）' % (a, c))
    if c == 1:
        write(ARCH, t.replace(a, b))
        t = read(ARCH)
heads = re.findall(u'^### 4\\.(\\d+) ', t, re.M)
dups = sorted(set(h for h in heads if heads.count(h) > 1))
print(u'  现行 §4 号：%d 个（重复号：%s —— 重复不是我这轮造的，只保证 4.171 只有一个）'
      % (len(heads), u','.join(u'4.' + d for d in dups) or u'无'))
check(heads.count(u'171') == 1, u'§4.171 恰好一个（实测 %d）' % heads.count(u'171'))
check(u'### 4.171 【做法雷】' in t, u'§4.171 标题在')

print()
print(u'===== ② 英文公告（用不撞车的变量名）=====')
ANN_TEXT = u"""
## New in 0.13 ZF163 - Fluid animations now move like vanilla water

- **The still textures no longer march.** Every fluid used to scroll its whole 16x16 tile downwards
  one row per frame. Measured against vanilla, that was **5-9x more change per frame than water**
  (49-98% of pixels per frame, against water's 11%) - a stripe pattern walking down a wall, which is
  exactly what looked wrong.
- **What vanilla actually does** (measured out of the real client jar): `water_still` is **32 frames,
  `frametime` 2**, and it **does not scroll at all** - the best vertical shift between neighbouring
  frames is 0 rows; it shimmers in place. `water_flow` is 32 frames of a 32x32 tile scrolling **up**
  one row per frame.
- **Still fluid is now a sub-pixel standing wave**: each column rises and falls by
  `2*cos(2*pi*x/16)*sin(2*pi*t/32)` rows, interpolated between rows, over **32 frames at
  `frametime` 2**. The displacement is **exactly zero at frame 0**, so the art you supplied is shown
  untouched at rest; the surface heaves in place with no net drift, and all 32 frames differ.
- **Flowing fluid now scrolls up one row per frame** (16 frames, default frametime) - the same
  direction and the same speed as vanilla water's flow, instead of scrolling down at half speed.
- Three earlier approaches were tried and thrown away, with the measurements kept in the notes:
  transplanting vanilla water's pixel mask (uncorrelated noise on our stripe art), a travelling wave
  (non-zero displacement at frame 0, so the art was distorted at rest), and an integer standing wave
  (**19 of 31 neighbouring frames were byte-identical** - it stuttered).
"""
raw = read(ANN_PATH)
if u'ZF163' in raw:
    print(u'  [幂等] 英文公告已有 ZF163 条')
else:
    if not raw.endswith(u'\n'):
        raw += u'\n'
    write(ANN_PATH, raw + ANN_TEXT)
    check(u'ZF163' in read(ANN_PATH), u'英文公告加了一条（%d -> %d 字节）'
          % (len(raw.encode()), len(read(ANN_PATH).encode())))

print()
print(u'===== ③ 顺手修 `_zf163_docs.py` 里的变量重名 =====')
P = os.path.join(TOOLS, '_zf163_docs.py')
s = read(P)
if u'ANN_TEXT = u"""' in s:
    print(u'  [幂等] 已修过')
else:
    pairs = [(u'ANN = u"""\n## New in 0.13 ZF163', u'ANN_TEXT = u"""\n## New in 0.13 ZF163'),
             (u'raw = read(ANN)\nif u\'ZF163\' in raw:', u'raw = read(ANN_PATH)\nif u\'ZF163\' in raw:'),
             (u'    write(ANN, raw + ANN)\n    check(u\'ZF163\' in read(ANN)', u'    write(ANN_PATH, raw + ANN_TEXT)\n    check(u\'ZF163\' in read(ANN_PATH)')]
    for a, b in pairs:
        c = s.count(a)
        check(c == 1, u'锚点命中 1 次（实测 %d）：%s' % (c, a.splitlines()[0][:40]))
        if c == 1:
            s = s.replace(a, b)
    write(P, s)
    import ast
    ast.parse(read(P))
    check(True, u'_zf163_docs.py 改后能过 ast.parse')

print()
print(u'===== ④ 终检：产物 / 四门 =====')
n_ok = 0
tot = 0
for f in sorted(os.listdir(TEXB)):
    if not (f.endswith('_still.png') or f.endswith('_flow.png')):
        continue
    tot += 1
    a = os.path.join(TEXB, f)
    b = os.path.join(BTEXB, f)
    ha = hashlib.sha1(open(a, 'rb').read()).hexdigest()
    hb = hashlib.sha1(open(b, 'rb').read()).hexdigest() if os.path.exists(b) else 'MISSING'
    if ha == hb:
        n_ok += 1
check(tot == 30 and n_ok == 30, u'build 产物 30 张流体贴图与源逐字节一致（%d/%d）' % (n_ok, tot))
for g in ['TextureCheck.py', 'ModelCheck.py', 'JsonCheck.py', '_zf135_fluidcheck.py']:
    r = subprocess.run([sys.executable, os.path.join(TOOLS, g)], cwd=ROOT,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode('utf-8', 'replace')
    tail = [l.strip() for l in out.splitlines() if (u'失败' in l or u'结论' in l or u'非法' in l or u'最大比值' in l)]
    print(u'  %-24s rc=%d  %s' % (g, r.returncode, u' | '.join(tail[-2:])))
    check(r.returncode == 0, u'%s rc=0' % g)
print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
