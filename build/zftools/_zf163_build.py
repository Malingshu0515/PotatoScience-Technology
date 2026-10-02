# -*- coding: utf-8 -*-
r"""_zf163_build.py —— 把 15 种流体改成"原版水那样"的动画（**先写到暂存目录**，验完再上线）

原版水的两条事实（`_zf163_extract.py` 从真 jar 量出来的，不是记忆）：
  · **still**：16x512 / **32 帧** / `frametime 2` —— 而它**不是滚动**：
    相邻帧的最佳位移恒为 **0 行**，变化是**原地**的亮暗（每帧约 9% 的像素参与）。
  · **flow** ：32x1024 / 32 帧 / `frametime` 缺省(=1) —— 内容每帧**上移 1 行**。

我们原来的做法（ZF132/ZF135）：still 每帧**整体下滚 1 行**、flow **下滚 2 行**、16 帧 / frametime 3。
⇒ **still 在"行军"**（横条纹一面墙一样往下走），这正是"有点怪"的来源。

本轮改法：
  · **still**：32 帧 / frametime 2，**逐像素原地亮暗** —— 亮暗的**时序掩码直接搬原版水那一套**
    （`water_still_mask.json`：第 t 帧每个像素相对第 0 帧是变亮还是变暗），
    落到我们贴图上 = 把该像素在**自己的调色板**里上/下走一格 ⇒ 与原版水**同节奏、同密度、零位移**。
  · **flow** ：16 帧（16 高的底图，16 帧正好一个周期、不会有两帧重复）/ `frametime` 缺省(=1)，
    **每帧上移 1 行** ⇒ 与原版水**同方向、同速度**（1 像素/刻；原版靠 32 高的底图铺 32 帧，
    我们底图只有 16 高，所以帧数取 16 —— 速度一样，周期减半，这一点如实记账）。
"""
import io, json, os, sys, shutil
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
REF = os.path.join(TOOLS, '_zf163_ref')
OUT = os.path.join(TOOLS, '_zf163_out')
TEXB = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'block')
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


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


print(u'===== ① 读原版水的时序模板 =====')
maskdata = json.load(io.open(os.path.join(REF, 'water_still_mask.json'), encoding='utf-8'))
W = maskdata['w']; N = maskdata['n']; MASK = maskdata['mask']
check((W, N) == (16, 32), u'模板是 16x16 / 32 帧（实测 %dx%d / %d 帧）' % (W, N, N))
dens = [sum(1 for v in MASK[t] if v) / 256.0 for t in range(N)]
print(u'  原版水每帧"参与亮暗"的像素比例：峰值 %.1f%%、均值 %.1f%%'
      % (100 * max(dens), 100 * sum(dens) / N))
refw, refh, refn, reffr = frames_of(os.path.join(REF, 'water_still.png'))
check((refw, refn) == (16, 32), u'参考条 water_still.png = 16x512（实测 %dx%d）' % (refw, refw * refn))
# 交叉验证：模板的 0 值位置必须与原版水"帧 t vs 帧 0 完全相同的像素"对得上
bad = 0
for t in range(N):
    for y in range(refw):
        for x in range(refw):
            same = px_of(reffr[t], refw, x, y) == px_of(reffr[0], refw, x, y)
            if same and MASK[t][y * refw + x] != 0:
                bad += 1
            if (not same) and MASK[t][y * refw + x] == 0:
                bad += 1
check(bad == 0, u'模板与原版水逐像素对得上（对不上的 %d 个）' % bad)

print()
print(u'===== ② 逐个流体读底图（= 现动画的第 0 帧）=====')
fluids = sorted(f[:-10] for f in os.listdir(TEXB) if f.endswith('_still.png'))
check(len(fluids) == 15, u'找到 15 种流体（实测 %d：%s）' % (len(fluids), u' '.join(fluids)))
bases = {}
for f in fluids:
    sw, sh, sn, sf = frames_of(os.path.join(TEXB, f + '_still.png'))
    fw, fh, fn, ff = frames_of(os.path.join(TEXB, f + '_flow.png'))
    check((sw, sh, sn) == (16, 256, 16), u'%s_still 现在是 16x256 / 16 帧（实测 %dx%d / %d）' % (f, sw, sh, sn))
    check((fw, fh, fn) == (16, 256, 16), u'%s_flow 现在是 16x256 / 16 帧（实测 %dx%d / %d）' % (f, fw, fh, fn))
    # 现在的动画是"整体下滚" ⇒ 逐行验算，证明第 0 帧就是底图、也证明我们读对了
    ok = all(sf[t][y * 64:(y + 1) * 64] == sf[0][((y - t) % 16) * 64:((y - t) % 16 + 1) * 64]
             for t in range(16) for y in range(16))
    check(ok, u'%s_still 现在确实是"整体下滚 1 行/帧"（逐行验算差 0）' % f)
    bases[f] = (sf[0], ff[0])

print()
print(u'===== ③ 生成新版（写到暂存 _zf163_out）=====')
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
report = []
for f in fluids:
    still0, flow0 = bases[f]
    # ---- 调色板（按亮度排序）----
    cols = sorted(set(px_of(still0, 16, x, y) for y in range(16) for x in range(16)), key=lum)
    idx = {c: i for i, c in enumerate(cols)}
    # ---- still：32 帧，原地亮暗（模板 = 原版水那一套）----
    out = bytearray()
    clamped = 0
    for t in range(N):
        for y in range(16):
            for x in range(16):
                c = px_of(still0, 16, x, y)
                s = MASK[t][y * 16 + x]
                i = idx[c] + s
                if s and not (0 <= i < len(cols)):
                    clamped += 1
                    i = idx[c]
                nc = cols[i] if s else c
                out += bytes(nc)
    sw_, sh_, sn_, sf_ = 16, 16 * N, N, [bytes(out[i * 1024:(i + 1) * 1024]) for i in range(N)]
    write_png(os.path.join(OUT, f + '_still.png'), 16, 16 * N, out)
    # ---- flow：16 帧，每帧上移 1 行 ----
    out2 = bytearray()
    for t in range(16):
        for y in range(16):
            out2 += flow0[((y + t) % 16) * 64:((y + t) % 16 + 1) * 64]
    write_png(os.path.join(OUT, f + '_flow.png'), 16, 256, out2)
    # 逐行验算：新版 flow 第 t 帧 == 底图第 (y+t) 行 ⇒ 内容上移 t 行
    fr2 = [bytes(out2[i * 1024:(i + 1) * 1024]) for i in range(16)]
    okf = all(fr2[t][y * 64:(y + 1) * 64] == flow0[((y + t) % 16) * 64:((y + t) % 16 + 1) * 64]
              for t in range(16) for y in range(16))
    check(okf, u'%s_flow 逐行验算 = 0（上移 1 行/帧）' % f)
    # still 的零位移：任意两帧的"最佳竖向位移"都必须是 0 行
    worst = 0
    for t in range(1, N):
        best = (0, -1.0)
        for s in range(16):
            same = sum(1 for y in range(16) if sf_[t][y * 64:(y + 1) * 64] == sf_[0][((y - s) % 16) * 64:((y - s) % 16 + 1) * 64])
            r = same / 16.0
            if r > best[1]:
                best = (s, r)
        if best[0] != 0:
            worst += 1
    check(worst == 0, u'%s_still 32 帧里"最像的位移不是 0 行"的帧数 = %d（要 0 ⇒ 不再行军）' % (f, worst))
    report.append((f, len(cols), clamped, sum(1 for t in range(N) for v in MASK[t] if v) / float(N * 256)))

print()
print(u'===== ④ 密度对齐 =====')
for f, ncol, cl, d in report:
    print(u'  %-20s 调色板 %d 色  被夹住的像素 %-4d  参与亮暗的像素密度 %.1f%%' % (f, ncol, cl, 100 * d))

print()
print(u'===== ⑤ 写 mcmeta =====')
for f in fluids:
    io.open(os.path.join(OUT, f + '_still.png.mcmeta'), 'w', encoding='utf-8', newline='\n').write(
        u'{\n  "animation": {\n    "frametime": 2\n  }\n}\n')
    io.open(os.path.join(OUT, f + '_flow.png.mcmeta'), 'w', encoding='utf-8', newline='\n').write(
        u'{\n  "animation": {}\n}\n')
check(len([x for x in os.listdir(OUT) if x.endswith('.mcmeta')]) == 30, u'30 份 mcmeta 写好（原版水 still=2 / flow 缺省）')
print(u'暂存目录：%s（%d 个文件）' % (OUT, len(os.listdir(OUT))))
print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
