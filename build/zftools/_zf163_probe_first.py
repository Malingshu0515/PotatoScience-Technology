# -*- coding: utf-8 -*-
r"""_zf158_probe.py —— 先量原版水，再决定怎么改（从真 jar 现抠，不靠记忆）

要回答四个问题：
  ① 原版 `water_still` / `water_flow` 的 mcmeta 到底写了什么（frametime / interpolate / frames）
  ② 尺寸与帧数（16x512 = 32 帧？）
  ③ **它是"整张往下滚"吗** —— 逐对相邻帧求"最佳竖向位移 + 匹配率"
  ④ 后 16 帧是不是前 16 帧的重复（若周期只有 16 帧，32 帧就是浪费一半）
"""
import io, json, os, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png
import TextureCheck as TC

JAR = TC.VANILLA_JAR
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_zf158_tmp')
os.makedirs(TMP, exist_ok=True)


def grab(tex):
    """把 jar 里的贴图与 mcmeta 落到临时目录，返回 (png路径, mcmeta文本或None)"""
    png = os.path.join(TMP, tex.rsplit('/', 1)[-1] + '.png')
    with zipfile.ZipFile(JAR) as z:
        names = z.namelist()
        src = 'assets/minecraft/textures/' + tex + '.png'
        with open(png, 'wb') as f:
            f.write(z.read(src))
        meta = None
        m = 'assets/minecraft/textures/' + tex + '.png.mcmeta'
        if m in names:
            meta = z.read(m).decode('utf-8')
    return png, meta


def frames(path):
    w, h, px = read_png(path)
    n = h // w
    out = []
    for i in range(n):
        fr = bytearray()
        for y in range(w):
            base = ((i * w + y) * w) * 4
            fr += px[base:base + w * 4]
        out.append(fr)
    return w, h, n, out


def best_shift(a, w, b):
    """b 相对 a 往下位移几行时最像（返回 位移, 完全相同的像素比例）"""
    best = (-1, -1.0)
    for s in range(w):
        same = 0
        for y in range(w):
            if a[y * w * 4:(y + 1) * w * 4] == b[((y - s) % w) * w * 4:((y - s) % w + 1) * w * 4]:
                same += w
        r = same / float(w * w)
        if r > best[1]:
            best = (s, r)
    return best


for tex in ['block/water_still', 'block/water_flow', 'block/lava_still', 'block/lava_flow']:
    png, meta = grab(tex)
    w, h, n, fr = frames(png)
    print(u'=============== %s ===============' % tex)
    print(u'  尺寸 %dx%d  帧数 %d  文件 %d 字节' % (w, h, n, os.path.getsize(png)))
    print(u'  mcmeta: %s' % (meta.strip().replace('\n', ' ') if meta else u'（没有 mcmeta）'))
    # 相邻帧最佳位移
    shifts = []
    for i in range(min(n - 1, 8)):
        s, r = best_shift(fr[i], w, fr[i + 1])
        shifts.append((s, r))
    print(u'  相邻帧最佳位移（前 8 对）: ' + u'  '.join(u'%d行/%.3f' % t for t in shifts))
    # 每帧相对第 0 帧
    rel = []
    for i in range(n):
        s, r = best_shift(fr[0], w, fr[i])
        rel.append((s, r))
    print(u'  第 i 帧 vs 第 0 帧: ' + u'  '.join(u'%d/%.2f' % t for t in rel[:12]) + (u' …' if n > 12 else u''))
    # 后半是不是前半的重复
    if n >= 4:
        half = n // 2
        dup = sum(1 for i in range(half) if fr[i] == fr[i + half])
        print(u'  后 %d 帧里有 %d 帧与前半逐字节相同' % (half, dup))
        print(u'  第 0 帧 == 第 %d 帧 ? %s' % (half, fr[0] == fr[half]))
    print()
