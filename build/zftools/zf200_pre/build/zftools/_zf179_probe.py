# -*- coding: utf-8 -*-
r"""_zf179_probe.py —— 侦察：引力装置 / 矿物探测器的素材与现状（真解码 + 读模型）"""
import io, json, os, sys, hashlib, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
ASSET = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
SRC = os.path.join(ROOT, 'build', '用户素材')


def sha1(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()


def ihdr(p):
    b = open(p, 'rb').read(33)
    assert b[:8] == b'\x89PNG\r\n\x1a\n', 'not png'
    w, h = struct.unpack('>II', b[16:24])
    return w, h, b[24], b[25]


def info(label, p):
    if not os.path.exists(p):
        print(u'  %-46s MISSING' % label)
        return None
    w, h, d, ct = ihdr(p)
    ww, hh, px = read_png(p)
    tot = ww * hh
    opaque = sum(1 for i in range(3, len(px), 4) if px[i] == 255)
    half = sum(1 for i in range(3, len(px), 4) if 0 < px[i] < 255)
    clear = tot - opaque - half
    cols = len(set((px[i], px[i + 1], px[i + 2], px[i + 3]) for i in range(0, len(px), 4)))
    print(u'  %-46s %3dx%-4d d=%d ct=%d  不透明=%-6d 半透明=%-5d 全透明=%-6d 色=%-5d %d B  %s'
          % (label, w, h, d, ct, opaque, half, clear, cols, os.path.getsize(p), sha1(p)[:12]))
    return (w, h, px, opaque, half, clear)


print(u'===== 轮号 =====')
print(u'  zf179_pre %s ／ 别人的 _zf179_verify.py %s'
      % (u'已存在' if os.path.exists(os.path.join(TOOLS, 'zf179_pre')) else u'还是空的',
         u'**已存在**' if os.path.exists(os.path.join(TOOLS, '_zf179_verify.py')) else u'不存在'))

print()
print(u'===== ① 两份素材（真解码）=====')
a = info(u'引力装置_001.png', os.path.join(SRC, u'引力装置_001.png'))
b = info(u'矿物探测器_001.png', os.path.join(SRC, u'矿物探测器_001.png'))

print()
print(u'===== ② 现状：两个物品模型与它们在用的贴图 =====')
for mid in ('gravity_device', 'ore_detector'):
    mp = os.path.join(ASSET, 'models', 'item', mid + '.json')
    if os.path.exists(mp):
        print(u'  models/item/%s.json: %s' % (mid, io.open(mp, encoding='utf-8').read().strip().replace('\n', ' ')))
    else:
        print(u'  models/item/%s.json  **不存在**' % mid)
    tp = os.path.join(ASSET, 'textures', 'item', mid + '.png')
    info(u'in-use textures/item/%s.png' % mid, tp)

print()
print(u'===== ③ 这两个名字在语言文件里（防「名字相近」）=====')
lg = json.loads(io.open(os.path.join(ASSET, 'lang', 'zh_cn.json'), encoding='utf-8').read())
for k, v in sorted(lg.items()):
    if any(s in v for s in (u'引力', u'探测', u'重力')):
        print(u'  %-52s %s' % (k, v))

print()
print(u'===== ④ 这两个 id 在 Java 里注册成什么 =====')
SRCJ = os.path.join(ROOT, 'src', 'main', 'java', 'com', 'potatost', 'mod')
for fn in sorted(os.listdir(SRCJ)):
    if not fn.endswith('.java'):
        continue
    t = io.open(os.path.join(SRCJ, fn), encoding='utf-8').read()
    if 'gravity_device' in t or 'ore_detector' in t:
        for i, l in enumerate(t.splitlines(), 1):
            if ('gravity_device' in l or 'ore_detector' in l) and 'register' in l.lower():
                print(u'  %s:%d  %s' % (fn, i, l.strip()[:130]))

print()
print(u'===== ⑤ 素材是不是"已经就是本工程要的规格" =====')
for label, r in ((u'引力装置', a), (u'矿物探测器', b)):
    if r is None:
        continue
    w, h, px, op, half, clear = r
    print(u'  %-10s %dx%d  半透明=%d  全透明=%d  ⇒ %s'
          % (label, w, h, half, clear,
             u'16x16，可直接原字节复制' if (w, h) == (16, 16) else u'**不是 16x16**，要定尺'))
