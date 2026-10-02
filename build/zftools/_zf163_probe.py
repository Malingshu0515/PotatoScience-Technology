# -*- coding: utf-8 -*-
r"""_zf161_probe.py —— 先量原版水，再决定怎么改（从真 jar 现抠，不靠记忆）

⚠ 原版 `water_still.png` 是 **4 位调色板**（PngRecolor 只吃 8 位）⇒ 本探针用**带 Pillow 的
   运行时**跑（`dsh-primary-runtime` 的 python），只用来**量原版**；本工程的贴图读写仍走 PngRecolor。

要回答五个问题：
  ① 原版 `water_still` / `water_flow` 的 mcmeta 到底写了什么（frametime / interpolate / frames）
  ② 尺寸与帧数（16x512 = 32 帧？）
  ③ **它是"整张往下滚"吗** —— 逐对相邻帧求"最佳竖向位移 + 匹配率"
  ④ 后 16 帧是不是前 16 帧的重复
  ⑤ 我们那 16 帧 / frametime 3 / 每帧滚 1 行的做法，与原版差在哪
"""
import io, json, os, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

JAR = r'E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar'
TOOLS = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(TOOLS, '_zf161_tmp')
os.makedirs(TMP, exist_ok=True)


def grab(tex):
    png = os.path.join(TMP, tex.rsplit('/', 1)[-1] + '.png')
    with zipfile.ZipFile(JAR) as z:
        names = z.namelist()
        with open(png, 'wb') as f:
            f.write(z.read('assets/minecraft/textures/' + tex + '.png'))
        meta = None
        m = 'assets/minecraft/textures/' + tex + '.png.mcmeta'
        if m in names:
            meta = z.read(m).decode('utf-8')
    return png, meta


def frames(path):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    px = im.tobytes()
    n = h // w
    return w, h, n, [px[i * w * w * 4:(i + 1) * w * w * 4] for i in range(n)], im


def best_shift(a, w, b):
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


def diff_ratio(a, b, w):
    n = 0
    for i in range(0, w * w * 4, 4):
        if a[i:i + 4] != b[i:i + 4]:
            n += 1
    return n / float(w * w)


for tex in ['block/water_still', 'block/water_flow', 'block/lava_still', 'block/lava_flow']:
    png, meta = grab(tex)
    w, h, n, fr, im = frames(png)
    print(u'=============== %s ===============' % tex)
    print(u'  尺寸 %dx%d  帧数 %d  文件 %d 字节  原图 mode=%s' % (w, h, n, os.path.getsize(png), im.mode))
    print(u'  mcmeta: %s' % (meta.strip().replace('\n', ' ') if meta else u'（没有 mcmeta）'))
    print(u'  颜色数 %d  带 alpha %s' % (len(set(im.convert('RGBA').getdata())), any(p[3] != 255 for p in im.convert('RGBA').getdata())))
    shifts = [best_shift(fr[i], w, fr[i + 1]) for i in range(min(n - 1, 6))]
    print(u'  相邻帧最佳位移（前 6 对）: ' + u'  '.join(u'%d行/%.3f' % t for t in shifts))
    rel = [best_shift(fr[0], w, fr[i]) for i in range(min(n, 10))]
    print(u'  第 i 帧 vs 第 0 帧: ' + u'  '.join(u'%d/%.2f' % t for t in rel))
    if n >= 4:
        half = n // 2
        dup = sum(1 for i in range(half) if fr[i] == fr[i + half])
        print(u'  后 %d 帧里 %d 帧与前半逐字节相同；第 0 帧 == 第 %d 帧 ? %s'
              % (half, dup, half, fr[0] == fr[half]))
    print(u'  相邻帧**实际**不同像素比例（第0帧 vs 第1帧）: %.3f' % diff_ratio(fr[0], fr[1], w))
    print()
