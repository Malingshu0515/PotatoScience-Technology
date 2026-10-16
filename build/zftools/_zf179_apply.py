# -*- coding: utf-8 -*-
r"""_zf179_apply.py —— 引力装置（128x128 要定尺）+ 矿物探测器（16x16 原字节）

事实（`_zf179_probe.py`）：
  · 两件都是**物品**：`ModItems.java:849 ore_detector` / `:854 gravity_device`；
    现在分别借 `minecraft:item/compass` 与 `minecraft:item/ender_eye`（待画清单 11 个里的两个）。
  · `矿物探测器_001.png` = **16x16 / 8 位 RGBA / 零半透明 / 88 色** ⇒ **原字节复制**。
  · `引力装置_001.png` = **128x128 / 3309 色 / 零半透明** ⇒ 游戏里物品贴图按 16x16 的四边形渲染，
    本工程其余物品也全是 16x16 ⇒ **按 8:1 盒式平均定尺到 16x16**。

定尺的两条讲究（都用得上）：
  ① **只对不透明像素求平均**（按覆盖率加权）⇒ 不会把透明区域的"黑边"混进来；
  ② **alpha 二值化**（块的覆盖率 ≥ 50% 才算实体）⇒ 成品仍是**零半透明**，与工程其余贴图一致。
  同时另存一版 **32x32**（4:1）到工具目录，谁更好看你说了算 —— 切换只要一行。
"""
import io, os, sys, json, shutil, hashlib, struct, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png

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


def downscale(w, h, px, dst):
    """盒式平均 + 只算不透明像素 + alpha 二值化（覆盖率 >= 50%）。"""
    f = w // dst
    out = bytearray(dst * dst * 4)
    solid = 0
    for by in range(dst):
        for bx in range(dst):
            r = g = b = 0
            cov = n = 0
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


print(u'===== ① 备份 -> zf179_pre =====')
os.makedirs(PRE, exist_ok=True)
BAK = ['models/item/gravity_device.json', 'models/item/ore_detector.json',
       'build/用户素材/_来源凭据.json', 'docs/贴图清单.md', 'docs/开发档案.md',
       'docs/UpdateAnnouncement_EN.md', 'build/zftools/_zf71_verify.py', 'build/zftools/_zf90_verify.py']
lines = []
# ⚠ ZF179 第三次踩（§4.165）：资源类 rel 是**相对 ASSET** 的，不能拼 ROOT。
#   两个物品模型当场被判 MISSING、一条都没抄（已用 `_zf179_fix.py` 从 git HEAD 取回）。
for rel in BAK:
    base = ROOT if rel.startswith(('docs/', 'build/')) else os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
    a = os.path.join(base, rel.replace('/', os.sep))
    if os.path.exists(a):
        shutil.copy2(a, os.path.join(PRE, rel.replace('/', '__')))
        lines.append(u'%s\t%s\t%d' % (rel, sha1(a), os.path.getsize(a)))
    else:
        lines.append(u'%s\tMISSING' % rel)
lines.append(u'textures/item/gravity_device.png\t改前不存在（本轮新建件）')
lines.append(u'textures/item/ore_detector.png\t改前不存在（本轮新建件）')
io.open(os.path.join(PRE, '_sha1.txt'), 'w', encoding='utf-8', newline='\n').write(u'\n'.join(lines) + u'\n')
check(len([l for l in lines if u'MISSING' not in l]) == 10, u'备份 8 份 + 记 2 份新建件')

print()
print(u'===== ② 矿物探测器：原字节复制 =====')
sp = os.path.join(SRC, u'矿物探测器_001.png')
tp = os.path.join(TEXI, 'ore_detector.png')
open(tp, 'wb').write(open(sp, 'rb').read())
w, h, px = read_png(tp)
half = sum(1 for i in range(3, len(px), 4) if 0 < px[i] < 255)
check(sha1(tp) == sha1(sp), u'ore_detector.png 原字节（%s…）' % sha1(tp)[:12])
check((w, h) == (16, 16) and half == 0, u'16x16 / 零半透明（实测 %dx%d 半透明 %d）' % (w, h, half))

print()
print(u'===== ③ 引力装置：128x128 -> 16x16（并另存一版 32x32 备选）=====')
sp = os.path.join(SRC, u'引力装置_001.png')
sw, sh, spx = read_png(sp)
check((sw, sh) == (128, 128), u'素材是 128x128（实测 %dx%d）' % (sw, sh))
data16, solid16 = downscale(sw, sh, spx, 16)
data32, solid32 = downscale(sw, sh, spx, 32)
tp = os.path.join(TEXI, 'gravity_device.png')
write_png(tp, 16, 16, data16)
alt = os.path.join(TOOLS, '_zf179_alt32.png')
write_png(alt, 32, 32, data32)
w, h, px = read_png(tp)
half = sum(1 for i in range(3, len(px), 4) if 0 < px[i] < 255)
check((w, h) == (16, 16) and half == 0, u'gravity_device.png = 16x16 / 零半透明（半透明 %d）' % half)
check(solid16 > 60, u'定尺后实体像素 %d/256（形状没被压没）' % solid16)
print(u'  16x16 实体 %d px ／ 32x32 实体 %d px（备选存在 %s）' % (solid16, solid32, os.path.basename(alt)))

print()
print(u'===== ④ 两个模型改指自己 =====')
for mid, old, new in (('gravity_device', 'minecraft:item/ender_eye', 'potato_s_t:item/gravity_device'),
                      ('ore_detector', 'minecraft:item/compass', 'potato_s_t:item/ore_detector')):
    mp = os.path.join(ASSET, 'models', 'item', mid + '.json')
    t = io.open(mp, encoding='utf-8').read()
    n = t.count(u'"' + old + u'"')
    check(n == 1, u'%s 里旧值 `%s` 恰好 1 次（实测 %d）' % (mid, old, n))
    if n == 1:
        io.open(mp, 'w', encoding='utf-8', newline='\n').write(t.replace(u'"' + old + u'"', u'"' + new + u'"'))
        back = json.loads(io.open(mp, encoding='utf-8').read())
        check(back['textures']['layer0'] == new and back['parent'] == 'minecraft:item/generated',
              u'%s 的 layer0 -> %s（parent 未动）' % (mid, new))

print()
print(u'===== ⑤ 凭据 +2 =====')
raw = io.open(CRED, encoding='utf-8').read()
data = json.loads(raw)
check((json.dumps(data, ensure_ascii=False, indent=2) + '\n') == raw, u'凭据"读进来再原样写回"与盘上逐字节相同')
n0 = len(data)
data['gravity_device.png'] = {
    u'原名': u'引力装置_001.png',
    u'sha1': sha1(os.path.join(SRC, u'引力装置_001.png')),
    u'bytes': os.path.getsize(os.path.join(SRC, u'引力装置_001.png')),
    u'轮次': u'ZF179',
    u'说明': u'用户 ZF179 给的手持式引力装置贴图。**素材是 128x128 / 3309 色 / 零半透明**，而物品贴图按 16x16 的'
            u'四边形渲染、本工程其余物品也全是 16x16 ⇒ 用「**只对不透明像素求平均（覆盖率加权）+ alpha 二值化（覆盖率 >= 50%）**」'
            u'定尺成 16x16（零半透明，%d 个实体像素）；另存一版 32x32 在 build/zftools/_zf179_alt32.png 备选。' % solid16,
}
data['ore_detector.png'] = {
    u'原名': u'矿物探测器_001.png',
    u'sha1': sha1(os.path.join(SRC, u'矿物探测器_001.png')),
    u'bytes': os.path.getsize(os.path.join(SRC, u'矿物探测器_001.png')),
    u'轮次': u'ZF179',
    u'说明': u'用户 ZF179 给的矿物探测器贴图（16x16 / 8 位 RGBA / 零半透明 / 88 色）⇒ **原字节复制**成 '
            u'textures/item/ore_detector.png。',
}
io.open(CRED, 'w', encoding='utf-8', newline='\n').write(json.dumps(data, ensure_ascii=False, indent=2) + u'\n')
check(len(json.loads(io.open(CRED, encoding='utf-8').read())) == n0 + 2, u'凭据 %d -> %d 条' % (n0, n0 + 2))

print()
print(u'===== ⑥ 复核图（原始 128 / 备选 32 / 成品 16）=====')
S, GAP, M = 8, 12, 12
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
                    if a == 255:
                        cv[di:di + 4] = px[i:i + 4]
                    else:
                        for c in range(3):
                            cv[di + c] = (px[i + c] * a + cv[di + c] * (255 - a)) // 255
                        cv[di + 3] = 255


w1, h1, p1 = read_png(sp)                      # 128 原图，1:1
blit(p1, w1, h1, M, M, 1)
w2, h2, p2 = read_png(alt)                     # 32 备选，4x
blit(p2, w2, h2, M + CELL + GAP, M, 4)
w3, h3, p3 = read_png(tp)                      # 16 成品，8x
blit(p3, w3, h3, M + (CELL + GAP) * 2, M, 8)


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
print(u'===== ⑦ processResources + 产物 + 两门 =====')
r = subprocess.run([os.path.join(ROOT, 'gradlew.bat'), 'processResources', '--console=plain'], cwd=ROOT,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
check(u'BUILD SUCCESSFUL' in r.stdout.decode('utf-8', 'replace'), u'gradle processResources BUILD SUCCESSFUL')
for n in ('gravity_device', 'ore_detector'):
    a = os.path.join(TEXI, n + '.png')
    b = os.path.join(BTEXI, n + '.png')
    hb = sha1(b) if os.path.exists(b) else 'MISSING'
    check(sha1(a) == hb, u'产物 textures/item/%-22s %s…' % (n + '.png', hb[:12]))
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
