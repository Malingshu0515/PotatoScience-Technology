# -*- coding: utf-8 -*-
r"""_zf163_extract.py —— 把原版水的帧序列导成 **8 位 RGBA** 的参考条（用带 Pillow 的运行时跑）

为什么要导：原版 `water_still.png` 是 **4 位调色板**，本工程的 `PngRecolor.read_png` 只吃 8 位。
导出的两张图只当**参考与时序模板**用，不参与出包。

同时量三件事（后面判定"像不像原版水"要用）：
  ① still：每一帧相对第 0 帧改了多少像素（亮度掩码的密度随时间怎么变）
  ② still：相邻帧之间有多少像素的**亮暗方向**发生了变化（这正是我们要搬到自家贴图上的东西）
  ③ flow：相邻帧的位移与**方向**（在 32 宽上是 31 行 ⇒ 内容每帧**上移 1 行**）
"""
import io, json, os, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

JAR = r'E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar'
TOOLS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(TOOLS, '_zf163_ref')
os.makedirs(OUT, exist_ok=True)


def grab(tex, out_name):
    with zipfile.ZipFile(JAR) as z:
        data = z.read('assets/minecraft/textures/' + tex + '.png')
        meta = z.read('assets/minecraft/textures/' + tex + '.png.mcmeta').decode('utf-8')
    p = os.path.join(OUT, 'raw_' + out_name + '.png')
    with open(p, 'wb') as f:
        f.write(data)
    im = Image.open(p).convert('RGBA')
    dst = os.path.join(OUT, out_name + '.png')
    im.save(dst)
    print(u'%s -> %s  %s  %s' % (tex, dst, im.size, meta.strip().replace('\n', ' ')))
    return im


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def frames(im):
    w, h = im.size
    n = h // w
    px = im.tobytes()
    return w, n, [px[i * w * w * 4:(i + 1) * w * w * 4] for i in range(n)]


def pix(fr, w, x, y):
    i = (y * w + x) * 4
    return (fr[i], fr[i + 1], fr[i + 2], fr[i + 3])


still = grab('block/water_still', 'water_still')
flow = grab('block/water_flow', 'water_flow')

w, n, fr = frames(still)
print(u'\n===== still：%dx%d / %d 帧 =====' % (w, n, w))
dev = []
for t in range(n):
    c = sum(1 for y in range(w) for x in range(w) if pix(fr[t], w, x, y) != pix(fr[0], w, x, y))
    dev.append(c)
print(u'  每帧相对第 0 帧改变的像素数：' + u' '.join(str(c) for c in dev))
print(u'  （256 像素里，峰值 %d = %.1f%%；均值 %.1f%%）' % (max(dev), 100.0 * max(dev) / 256,
                                                     100.0 * sum(dev) / len(dev) / 256))
adj = []
signflip = []
for t in range(1, n):
    c = 0
    sf = 0
    for y in range(w):
        for x in range(w):
            a = pix(fr[t - 1], w, x, y)
            b = pix(fr[t], w, x, y)
            if a != b:
                c += 1
                da = lum(b) - lum(a)
                d0 = lum(b) - lum(pix(fr[0], w, x, y))
                if (da > 0) != (d0 > 0):
                    sf += 1
    adj.append(c)
    signflip.append(sf)
print(u'  相邻帧改变的像素数：' + u' '.join(str(c) for c in adj))
print(u'  相邻帧"亮暗方向翻转"的像素数：' + u' '.join(str(c) for c in signflip))
print(u'  循环闭合：第 0 帧 == 第 %d 帧 ? %s' % (n, fr[0] == fr[n - 1]))

# 亮度掩码（相对第 0 帧的亮暗方向）—— 这就是要搬到自家贴图上的"时序模板"
mask = []
for t in range(n):
    row = []
    for y in range(w):
        for x in range(w):
            d = lum(pix(fr[t], w, x, y)) - lum(pix(fr[0], w, x, y))
            row.append(1 if d > 0 else (-1 if d < 0 else 0))
    mask.append(row)
json.dump({'w': w, 'n': n, 'mask': mask}, io.open(os.path.join(OUT, 'water_still_mask.json'), 'w', encoding='utf-8'))
print(u'  亮度时序模板已写出：water_still_mask.json（%d 帧 x %d 像素，取值 -1/0/+1）' % (n, w * w))

# flow 的位移
w2, n2, fr2 = frames(flow)
print(u'\n===== flow：%dx%d / %d 帧 =====' % (w2, n2, w2))


def best_shift(a, b, w):
    best = (-1, -1.0)
    for s in range(w):
        same = sum(1 for y in range(w) if a[y * w * 4:(y + 1) * w * 4] == b[((y - s) % w) * w * 4:((y - s) % w + 1) * w * 4])
        r = same / float(w)
        if r > best[1]:
            best = (s, r)
    return best


print(u'  相邻帧最佳位移：' + u'  '.join(u'%d行/%.2f' % best_shift(fr2[i], fr2[i + 1], w2) for i in range(6)))
print(u'  ⇒ 32 宽上的 31 行 = 内容每帧**上移 1 行**')
