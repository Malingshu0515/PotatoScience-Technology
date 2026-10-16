# -*- coding: utf-8 -*-
r"""_zf179_hires.py —— 引力装置改 **64x64**（用户：「高清点行不行 要不然看不出来是黑洞了」）

尺寸账（一路都是量出来的，不是拍的）：
  · 128→**16**（8:1）：造型被压坏 —— 左尖角只剩孤立 1 个像素（`_zf179_reject16.png`）；
  · 128→**32**（4:1）：造型完整，但用户说"看不出来是黑洞"；
  · 128→**64**（2:1）：本轮采用。
**为什么高清真的更有用**：物品贴图固定画在 16 逻辑像素的四边形上 ——
  界面缩放 2 时 32x32 正好 1:1、**64x64 会被放大 2 倍**；界面缩放 4 时 64x64 才 1:1。
  也就是说**贴图分辨率越高，在高缩放/拿在手里时越清楚**（低缩放时靠 mipmap 平滑）。
`TextureCheck` 的规则是「16~256 的 2 的幂正方形」都放行 ⇒ 64 不产生警告。
"""
import io, os, sys, json, shutil, hashlib, struct, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png

ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
TEXI = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'item')
BTEXI = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'item')
SRC = os.path.join(ROOT, 'build', '用户素材')
CRED = os.path.join(SRC, '_来源凭据.json')
PRE = os.path.join(TOOLS, 'zf179_pre')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def sha1b(b):
    return hashlib.sha1(b).hexdigest()


def downscale(w, h, px, dst):
    f = w // dst
    out = bytearray(dst * dst * 4)
    solid = 0
    for by in range(dst):
        for bx in range(dst):
            r = g = b = cov = n = 0
            for y in range(by * f, (by + 1) * f):
                for x in range(bx * f, (bx + 1) * f):
                    i = (y * w + x) * 4
                    if px[i + 3]:
                        cov += 1
                        r += px[i]; g += px[i + 1]; b += px[i + 2]
                        n += 1
            o = (by * dst + bx) * 4
            if n and cov * 2 >= f * f:
                out[o] = r // n; out[o + 1] = g // n; out[o + 2] = b // n; out[o + 3] = 255
                solid += 1
    return bytes(out), solid


sp = os.path.join(SRC, u'引力装置_001.png')
sw, sh, spx = read_png(sp)
check((sw, sh) == (128, 128), u'素材仍是 128x128（实测 %dx%d）' % (sw, sh))

print(u'===== ① 先把现在的 32x32 留档，再出 64x64 =====')
cur = os.path.join(TEXI, 'gravity_device.png')
w32, h32, _ = read_png(cur)
keep32 = os.path.join(TOOLS, '_zf179_keep32.png')
shutil.copy2(cur, keep32)
check((w32, h32) == (32, 32), u'32x32 那版留档为 _zf179_keep32.png')
data64, solid64 = downscale(sw, sh, spx, 64)
write_png(cur, 64, 64, data64)
w, h, px = read_png(cur)
op = sum(1 for i in range(3, len(px), 4) if px[i] == 255)
half = sum(1 for i in range(3, len(px), 4) if 0 < px[i] < 255)
check((w, h) == (64, 64), u'现在是 64x64（实测 %dx%d）' % (w, h))
check(half == 0, u'零半透明（实体 %d / 4096 像素）' % op)
check(op == solid64, u'实体像素数与定尺函数一致（%d）' % solid64)

print()
print(u'===== ② 顺手把 128 原样那版也备一份（万一你要最极致的）=====')
raw128 = os.path.join(TOOLS, '_zf179_alt128.png')
open(raw128, 'wb').write(open(sp, 'rb').read())
check(sha1b(open(raw128, 'rb').read()) == sha1b(open(sp, 'rb').read()), u'128x128 原字节备在 _zf179_alt128.png')

print()
print(u'===== ③ 凭据说明改成 64x64（把三次尺寸的账都写上）=====')
raw = io.open(CRED, encoding='utf-8').read()
dj = json.loads(raw)
check((json.dumps(dj, ensure_ascii=False, indent=2) + u'\n') == raw, u'凭据自洽')
e = dj.get('gravity_device.png')
check(e is not None, u'凭据里有 gravity_device.png')
if e is not None:
    e[u'说明'] = (u'用户 ZF179 给的手持式引力装置贴图。**素材 128x128 / 3309 色 / 零半透明**。'
                  u'尺寸试了三档（都是量出来才定的）：128→16（8:1）造型被压坏（左尖角只剩孤立 1 像素，'
                  u'留档 _zf179_reject16.png）；128→32（4:1）完整但用户说"看不出来是黑洞"；'
                  u'⇒ **采用 128→64（2:1）**，%d 个实体像素、零半透明。'
                  u'**为什么高清有用**：物品贴图固定画在 16 逻辑像素的四边形上 —— 界面缩放 2 时 32x32 才 1:1、'
                  u'64x64 会被放大 2 倍；缩放 4 时 64x64 才 1:1 ⇒ 分辨率越高，高缩放/拿在手里越清楚。'
                  u'`TextureCheck` 放行「16~256 的 2 的幂正方形」⇒ 64 不产生警告。'
                  u'算法：只对不透明像素求平均（覆盖率加权）＋ alpha 二值化（覆盖率 >= 50%%）。' % op)
io.open(CRED, 'w', encoding='utf-8', newline='\n').write(json.dumps(dj, ensure_ascii=False, indent=2) + u'\n')
check(u'64x64' in json.loads(io.open(CRED, encoding='utf-8').read())['gravity_device.png'][u'说明'],
      u'凭据说明已写 64x64')
check(len(json.loads(io.open(CRED, encoding='utf-8').read())) == 61, u'凭据仍 61 条')

print()
print(u'===== ④ 复核图：32 / 64 / 128 三档，各按"屏幕上 128 px"放大看 =====')
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

for k, (path, scale) in enumerate(((keep32, 4), (cur, 2), (sp, 1))):
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
print(u'  左=32x32（4x，旧）／ 中=**64x64（2x，新）**／ 右=128x128（1x，原图）⇒ %s' % PV)

print()
print(u'===== ⑤ processResources + 产物 + 门 =====')
r = subprocess.run([os.path.join(ROOT, 'gradlew.bat'), 'processResources', '--console=plain'], cwd=ROOT,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
check(u'BUILD SUCCESSFUL' in r.stdout.decode('utf-8', 'replace'), u'gradle processResources BUILD SUCCESSFUL')
for n in ('gravity_device', 'ore_detector'):
    a = os.path.join(TEXI, n + '.png')
    b = os.path.join(BTEXI, n + '.png')
    hb = sha1b(open(b, 'rb').read()) if os.path.exists(b) else 'MISSING'
    check(sha1b(open(a, 'rb').read()) == hb, u'产物 %-22s %s…' % (n + '.png', hb[:12]))
for g in ['TextureCheck.py', 'ModelCheck.py']:
    rr = subprocess.run([sys.executable, os.path.join(TOOLS, g)], cwd=ROOT,
                        env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o = rr.stdout.decode('utf-8', 'replace')
    tail = [l.strip() for l in o.splitlines() if (u'失败' in l or u'结论' in l or u'提示' in l or u'警告' in l)]
    print(u'  %-18s rc=%d  %s' % (g, rr.returncode, u' | '.join(tail[-2:])))
    check(rr.returncode == 0, u'%s rc=0' % g)

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
