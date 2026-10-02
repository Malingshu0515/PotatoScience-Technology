# -*- coding: utf-8 -*-
"""ZF157 侦察：五份新素材到底是什么东西（真解码，不看文件名）。"""
import sys, os, io, json, hashlib, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST'
ASSET = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
SRC = os.path.join(ROOT, 'build', '用户素材')


def ihdr(p):
    with open(p, 'rb') as f:
        b = f.read(33)
    assert b[:8] == b'\x89PNG\r\n\x1a\n', 'not png: ' + p
    w, h = struct.unpack('>II', b[16:24])
    return dict(w=w, h=h, depth=b[24], ctype=b[25], interlace=b[28])


def mask(p):
    w, h, px = read_png(p)
    m = [[1 if px[(y * w + x) * 4 + 3] > 0 else 0 for x in range(w)] for y in range(h)]
    return w, h, m


def info(name, p):
    if not os.path.exists(p):
        print('%-42s MISSING' % name)
        return None
    d = ihdr(p)
    w, h, px = read_png(p)
    opaque = 0
    xs = []
    ys = []
    colors = set()
    half = 0
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 4
            a = px[i + 3]
            if a:
                opaque += 1
                xs.append(x)
                ys.append(y)
                colors.add((px[i], px[i + 1], px[i + 2], a))
                if a != 255:
                    half += 1
    bbox = (min(xs), min(ys), max(xs), max(ys)) if xs else None
    print('%-42s %2dx%-3d depth=%d ctype=%d opaque=%-5d half=%-3d colors=%-3d bbox=%s bytes=%d'
          % (name, d['w'], d['h'], d['depth'], d['ctype'], opaque, half, len(colors), bbox,
             os.path.getsize(p)))
    return (w, h, [[1 if px[(y * w + x) * 4 + 3] > 0 else 0 for x in range(w)] for y in range(h)])


def iou(a, b):
    if a is None or b is None:
        return None
    wa, ha, ma = a
    wb, hb, mb = b
    if (wa, ha) != (wb, hb):
        return None
    inter = sum(1 for y in range(ha) for x in range(wa) if ma[y][x] and mb[y][x])
    union = sum(1 for y in range(ha) for x in range(wa) if ma[y][x] or mb[y][x])
    return inter / union if union else 0.0


print('===== 1. 素材区五份新文件 =====')
srcs = {}
for n in ['钛合金头盔_001.png', '钛合金胸甲_001.png', '钛合金护腿_001.png', '钛合金靴子_001.png', '热力金属_001.png']:
    srcs[n] = info(n, os.path.join(SRC, n))

print()
print('===== 2. 参照物（工程里已知形状）=====')
ref_icon = info('item/star_steel_helmet.png (已知 16x16 图标)', os.path.join(ASSET, 'textures', 'item', 'star_steel_helmet.png'))
ref_l1 = info('models/armor/star_steel_layer_1.png (已知盔甲层)', os.path.join(ASSET, 'textures', 'models', 'armor', 'star_steel_layer_1.png'))
t_l1 = info('models/armor/titanium_alloy_layer_1.png (在用)', os.path.join(ASSET, 'textures', 'models', 'armor', 'titanium_alloy_layer_1.png'))
t_l2 = info('models/armor/titanium_alloy_layer_2.png (在用)', os.path.join(ASSET, 'textures', 'models', 'armor', 'titanium_alloy_layer_2.png'))
cur_tm = info('item/thermal_metal.png (在用)', os.path.join(ASSET, 'textures', 'item', 'thermal_metal.png'))

print()
print('===== 3. 掩码 IoU（素材 vs 参照）=====')
for n, m in srcs.items():
    if m is None:
        continue
    print('%-24s vs star_steel_helmet(icon) = %s | vs star_steel_layer_1 = %s | vs titanium_layer_1 = %s'
          % (n, iou(m, ref_icon), iou(m, ref_l1), iou(m, t_l1)))

print()
print('===== 4. 相关物品模型当前指向哪张图 =====')
for m in ['titanium_alloy_helmet', 'titanium_alloy_chestplate', 'titanium_alloy_leggings',
          'titanium_alloy_boots', 'thermal_metal', 'titanium_alloy_sword']:
    p = os.path.join(ASSET, 'models', 'item', m + '.json')
    if os.path.exists(p):
        print('%-28s %s' % (m, open(p, encoding='utf-8').read().strip()))
    else:
        print('%-28s MISSING' % m)
