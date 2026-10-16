# -*- coding: utf-8 -*-
r"""_zf179_apply2.py —— 补上凭据两条（`%` 要写成 `%%`）+ 复核图 + 产物 + 两门

上一跑崩在哪：凭据说明里写了「覆盖率 >= 50%）」，而那是 `%` 后面跟了个全角括号 ⇒
Python 当成格式符（`ValueError: unsupported format character`）。贴图与模型**已经改完**了，
崩溃点在写凭据之前 ⇒ 凭据一个字节没动（这点是干净的）。
"""
import io, os, sys, json, hashlib, struct, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
ASSET = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
TEXI = os.path.join(ASSET, 'textures', 'item')
BTEXI = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'item')
SRC = os.path.join(ROOT, 'build', '用户素材')
CRED = os.path.join(SRC, '_来源凭据.json')
PRE = os.path.join(TOOLS, 'zf179_pre')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def sha1(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()

print(u'===== ① 先看 zf179_pre/_sha1.txt 里到底哪条 MISSING =====')
p = os.path.join(PRE, '_sha1.txt')
if os.path.exists(p):
    for l in io.open(p, encoding='utf-8').read().splitlines():
        mark = u'  <== MISSING' if u'MISSING' in l else u''
        print(u'  ' + l + mark)
else:
    check(False, u'zf179_pre/_sha1.txt 不在')

print()
print(u'===== ② 现在盘上的状态（贴图 + 模型）=====')
for n in ('gravity_device', 'ore_detector'):
    tp = os.path.join(TEXI, n + '.png')
    w, h, px = read_png(tp)
    op = sum(1 for i in range(3, len(px), 4) if px[i] == 255)
    half = sum(1 for i in range(3, len(px), 4) if 0 < px[i] < 255)
    mp = os.path.join(ASSET, 'models', 'item', n + '.json')
    m = json.loads(io.open(mp, encoding='utf-8').read())
    print(u'  %-16s %2dx%-3d 实体=%-4d 半透明=%-3d %s… layer0=%s'
          % (n, w, h, op, half, sha1(tp)[:12], m['textures']['layer0']))
    check(m['textures']['layer0'] == 'potato_s_t:item/' + n, u'%s 的 layer0 已指向自己' % n)

print()
print(u'===== ③ 凭据 +2（这回把 % 写好）=====')
raw = io.open(CRED, encoding='utf-8').read()
data = json.loads(raw)
check((json.dumps(data, ensure_ascii=False, indent=2) + u'\n') == raw, u'凭据"读进来再原样写回"与盘上逐字节相同')
n0 = len(data)
w, h, px = read_png(os.path.join(TEXI, 'gravity_device.png'))
solid16 = sum(1 for i in range(3, len(px), 4) if px[i] == 255)
if 'gravity_device.png' not in data:
    data['gravity_device.png'] = {
        u'原名': u'引力装置_001.png',
        u'sha1': sha1(os.path.join(SRC, u'引力装置_001.png')),
        u'bytes': os.path.getsize(os.path.join(SRC, u'引力装置_001.png')),
        u'轮次': u'ZF179',
        u'说明': (u'用户 ZF179 给的手持式引力装置贴图。**素材是 128x128 / 3309 色 / 零半透明**，'
                  u'而物品贴图按 16x16 的四边形渲染、本工程其余物品也全是 16x16 ⇒ 用「只对不透明像素求平均'
                  u'（覆盖率加权）＋ alpha 二值化（覆盖率 >= 50%%）」定尺成 16x16（零半透明，'
                  u'%d 个实体像素）；另存一版 32x32 在 build/zftools/_zf179_alt32.png 备选。' % solid16),
    }
else:
    print(u'  [幂等] 凭据已有 gravity_device.png')
if 'ore_detector.png' not in data:
    data['ore_detector.png'] = {
        u'原名': u'矿物探测器_001.png',
        u'sha1': sha1(os.path.join(SRC, u'矿物探测器_001.png')),
        u'bytes': os.path.getsize(os.path.join(SRC, u'矿物探测器_001.png')),
        u'轮次': u'ZF179',
        u'说明': u'用户 ZF179 给的矿物探测器贴图（16x16 / 8 位 RGBA / 零半透明 / 88 色）⇒ **原字节复制**成 textures/item/ore_detector.png。',
    }
else:
    print(u'  [幂等] 凭据已有 ore_detector.png')
io.open(CRED, 'w', encoding='utf-8', newline='\n').write(json.dumps(data, ensure_ascii=False, indent=2) + u'\n')
back = json.loads(io.open(CRED, encoding='utf-8').read())
check(len(back) == n0 + (0 if u'引力装置_001.png' in raw else 2) or len(back) in (n0, n0 + 2),
      u'凭据 %d -> %d 条' % (n0, len(back)))
for k in ('gravity_device.png', 'ore_detector.png'):
    check(k in back, u'凭据里有 %s' % k)

print()
print(u'===== ④ 复核图：原始 128 / 备选 32 / 成品 16（各按 128 px 显示）=====')
alt = os.path.join(TOOLS, '_zf179_alt32.png')
GAP, M = 12, 12
CELL = 128
W = M * 2 + CELL * 3 + GAP * 2
H = M * 2 + CELL + GAP
cv = bytearray(W * H * 4)
for y in range(H):
    for x in range(W):
        v = 62 if ((x // 8 + y // 8) % 2 == 0) else 74
        i = (y * W + x) * 4
        cv[i] = cv[i + 1] = cv[i + 2] = v
        cv[i + 3] = 255

def blit(px, sw, sh, ox, oy, scale):
    for y in range(sh):
        for x in range(sw):
            i = (y * sw + x) * 4
            a = px[i + 3]
            if not a:
                continue
            for dy in range(scale):
                for dx in range(scale):
                    di = ((oy + y * scale + dy) * W + (ox + x * scale + dx)) * 4
                    cv[di:di + 4] = px[i:i + 4]

for k, (path, scale) in enumerate(((os.path.join(SRC, u'引力装置_001.png'), 1),
                                   (alt, 4), (os.path.join(TEXI, 'gravity_device.png'), 8))):
    w, h, px = read_png(path)
    blit(px, w, h, M + k * (CELL + GAP), M, scale)

def write_png2(path, w, h, rgba):
    import zlib
    raw2 = bytearray()
    for y in range(h):
        raw2.append(0)
        raw2 += rgba[y * w * 4:(y + 1) * w * 4]
    def ch(tag, d):
        return struct.pack('>I', len(d)) + tag + d + struct.pack('>I', zlib.crc32(tag + d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += ch(b'IDAT', zlib.compress(bytes(raw2), 9)) + ch(b'IEND', b'')
    open(path, 'wb').write(png)

PV = os.path.join(TOOLS, '_zf179_preview.png')
write_png2(PV, W, H, cv)
print(u'  左=原始 128x128 ／ 中=备选 32x32（4x）／ 右=**成品 16x16**（8x）⇒ %s' % PV)

print()
print(u'===== ⑤ processResources + 产物 + 两门 =====')
r = subprocess.run([os.path.join(ROOT, 'gradlew.bat'), 'processResources', '--console=plain'], cwd=ROOT,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
check(u'BUILD SUCCESSFUL' in r.stdout.decode('utf-8', 'replace'), u'gradle processResources BUILD SUCCESSFUL')
for n in ('gravity_device', 'ore_detector'):
    a = os.path.join(TEXI, n + '.png')
    b = os.path.join(BTEXI, n + '.png')
    hb = sha1(b) if os.path.exists(b) else 'MISSING'
    check(sha1(a) == hb, u'产物 textures/item/%-20s %s…' % (n + '.png', hb[:12]))
for g in ['TextureCheck.py', 'ModelCheck.py', 'JsonCheck.py']:
    rr = subprocess.run([sys.executable, os.path.join(TOOLS, g)], cwd=ROOT,
                        env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o = rr.stdout.decode('utf-8', 'replace')
    tail = [l.strip() for l in o.splitlines() if (u'失败' in l or u'结论' in l or u'提示' in l or u'非法' in l)]
    print(u'  %-18s rc=%d  %s' % (g, rr.returncode, u' | '.join(tail[-2:])))
    check(rr.returncode == 0, u'%s rc=0' % g)

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
