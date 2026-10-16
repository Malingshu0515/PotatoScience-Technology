# -*- coding: utf-8 -*-
r"""_zf179_fix.py —— 三件事：① 32x32 才是对的（16x16 把图压坏了）② 补回两个模型的改前件 ③ 修我第三次踩的基目录坑

**为什么改成 32x32**（看 `_zf179_preview.png` 得出的，不是拍的）：
  128→16 的 8:1 压完之后，那个"黑洞 + 吸积盘 + 左右尖角"的造型**被压坏了** ——
  左边尖角只剩**孤立 1 个像素**、白环变成疙瘩；128→32（4:1）则把造型完整留住（213 个实体像素）。
  `TextureCheck` 的规则是"16~256 的 2 的幂正方形"都放行（32 不会产生警告），
  而物品贴图本来就画在 16x16 的四边形上（32x32 只是同一尺寸下更细），⇒ 选 32x32。

**漏备份**：`_zf179_apply.py` 的 BAK 里我把资源路径写成了 `models/item/...`（相对 ASSET），
  可 `_zf179_apply.py` 的拼接是**相对仓库根**的 ⇒ 两个模型一条都没抄（**§4.165 第三次**）。
  幸好那两个模型是别的线 16:51 刚加的、**已在 git HEAD 里** ⇒ 逐字节取回并核 sha1。
"""
import io, os, sys, json, shutil, hashlib, subprocess, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png, write_png

ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
ASSET_REL = 'src/main/resources/assets/potato_s_t'
TEXI = os.path.join(ROOT, ASSET_REL.replace('/', os.sep), 'textures', 'item')
BTEXI = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'item')
SRC = os.path.join(ROOT, 'build', '用户素材')
CRED = os.path.join(SRC, '_来源凭据.json')
PRE = os.path.join(TOOLS, 'zf179_pre')
ALT32 = os.path.join(TOOLS, '_zf179_alt32.png')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def sha1b(b):
    return hashlib.sha1(b).hexdigest()

print(u'===== ① 补回两个模型的改前件（git HEAD，逐字节）=====')
for rel, needle in (('models/item/gravity_device.json', b'minecraft:item/ender_eye'),
                    ('models/item/ore_detector.json', b'minecraft:item/compass')):
    r = subprocess.run(['git', '-C', ROOT, 'show', 'HEAD:' + ASSET_REL + '/' + rel],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    check(r.returncode == 0, u'HEAD 里有 %s' % rel)
    if r.returncode != 0:
        continue
    b = r.stdout
    check(needle in b, u'取回的那份仍是借原版（含 %s）' % needle.decode())
    dst = os.path.join(PRE, (ASSET_REL + '/' + rel).replace('/', '__'))
    open(dst, 'wb').write(b)
    check(sha1b(open(dst, 'rb').read()) == sha1b(b), u'  %s 写入 zf179_pre 后回读一致（%s… / %d B）'
          % (os.path.basename(rel), sha1b(b)[:12], len(b)))
# 重写真实清单
lines = []
for rel in ('models/item/gravity_device.json', 'models/item/ore_detector.json'):
    p = os.path.join(PRE, (ASSET_REL + '/' + rel).replace('/', '__'))
    lines.append(u'%s\t%s\t%d\t(git HEAD 取回)' % (rel, sha1b(open(p, 'rb').read()), os.path.getsize(p)))
for rel in ('build/用户素材/_来源凭据.json', 'docs/贴图清单.md', 'docs/开发档案.md',
            'docs/UpdateAnnouncement_EN.md', 'build/zftools/_zf71_verify.py', 'build/zftools/_zf90_verify.py'):
    b = os.path.join(PRE, rel.replace('/', '__'))
    if os.path.exists(b):
        lines.append(u'%s\t%s\t%d\t(备份)' % (rel, sha1b(open(b, 'rb').read()), os.path.getsize(b)))
lines.append(u'textures/item/gravity_device.png\t改前不存在（本轮新建件；**借的是 minecraft:item/ender_eye**）')
lines.append(u'textures/item/ore_detector.png\t改前不存在（本轮新建件；**借的是 minecraft:item/compass**）')
io.open(os.path.join(PRE, '_sha1.txt'), 'w', encoding='utf-8', newline='\n').write(u'\n'.join(lines) + u'\n')
check(len(lines) == 10, u'zf179_pre/_sha1.txt 重写成 %d 行' % len(lines))

print()
print(u'===== ② 修 `_zf179_apply.py` 的基目录（第三次踩同一个坑）=====')
AP = os.path.join(TOOLS, '_zf179_apply.py')
s = io.open(AP, encoding='utf-8').read()
a = u"for rel in BAK:\n    a = os.path.join(ROOT, rel.replace('/', os.sep))"
b = (u"# \u26a0 ZF179 \u7b2c\u4e09\u6b21\u8e29\uff08\u00a74.165\uff09\uff1a\u8d44\u6e90\u7c7b rel \u662f**\u76f8\u5bf9 ASSET** \u7684\uff0c\u4e0d\u80fd\u62fc ROOT\u3002\n"
     u"#   \u4e24\u4e2a\u7269\u54c1\u6a21\u578b\u5f53\u573a\u88ab\u5224 MISSING\u3001\u4e00\u6761\u90fd\u6ca1\u6284\uff08\u5df2\u7528 `_zf179_fix.py` \u4ece git HEAD \u53d6\u56de\uff09\u3002\n"
     u"for rel in BAK:\n"
     u"    base = ROOT if rel.startswith(('docs/', 'build/')) else os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')\n"
     u"    a = os.path.join(base, rel.replace('/', os.sep))")
if b in s:
    print(u'  [幂等] 已修过')
else:
    check(s.count(a) == 1, u'锚点命中 1 次（实测 %d）' % s.count(a))
    if s.count(a) == 1:
        io.open(AP, 'w', encoding='utf-8', newline='\n').write(s.replace(a, b))
        import ast
        ast.parse(io.open(AP, encoding='utf-8').read())
        print(u'  [OK] `_zf179_apply.py` 已修且能过 ast.parse')

print()
print(u'===== ③ 引力装置改成 32x32（把被否掉的 16x16 留档）=====')
cur = os.path.join(TEXI, 'gravity_device.png')
w, h, px = read_png(cur)
rej = os.path.join(TOOLS, '_zf179_reject16.png')
shutil.copy2(cur, rej)
check((w, h) == (16, 16), u'旧的 16x16 已留档为 _zf179_reject16.png')
data = open(ALT32, 'rb').read()
open(cur, 'wb').write(data)
w, h, px = read_png(cur)
op = sum(1 for i in range(3, len(px), 4) if px[i] == 255)
half = sum(1 for i in range(3, len(px), 4) if 0 < px[i] < 255)
check((w, h) == (32, 32) and half == 0, u'现在是 32x32 / 零半透明（实体 %d 像素）' % op)
check(sha1b(data) == sha1b(open(ALT32, 'rb').read()), u'与 4:1 定尺的那份逐字节相同（%s…）' % sha1b(data)[:12])

print()
print(u'===== ④ 凭据说明改成 32x32 =====')
raw = io.open(CRED, encoding='utf-8').read()
data_j = json.loads(raw)
check((json.dumps(data_j, ensure_ascii=False, indent=2) + u'\n') == raw, u'凭据自洽（读进来再原样写回一致）')
e = data_j.get('gravity_device.png')
check(e is not None, u'凭据里有 gravity_device.png')
if e is not None:
    e[u'说明'] = (u'用户 ZF179 给的手持式引力装置贴图。**素材是 128x128 / 3309 色 / 零半透明**。'
                  u'⚠ 先按 8:1 定尺成 16x16 试过一版：**造型被压坏**（左边尖角只剩孤立 1 个像素、白环变疙瘩），'
                  u'见 build/zftools/_zf179_reject16.png ⇒ 改成 **4:1 定尺成 32x32**（%d 个实体像素、零半透明），'
                  u'造型完整。**为什么 32x32 可以**：TextureCheck 的规则是「16~256 的 2 的幂正方形」都放行'
                  u'（32 不产生警告），而物品贴图本来就画在 16x16 的四边形上 —— 32x32 只是同一尺寸下更细。'
                  u'定尺算法：只对不透明像素求平均（覆盖率加权）＋ alpha 二值化（覆盖率 >= 50%%）。' % op)
io.open(CRED, 'w', encoding='utf-8', newline='\n').write(json.dumps(data_j, ensure_ascii=False, indent=2) + u'\n')
check(u'32x32' in json.loads(io.open(CRED, encoding='utf-8').read())['gravity_device.png'][u'说明'],
      u'凭据说明已改成 32x32')
check(len(json.loads(io.open(CRED, encoding='utf-8').read())) == 61, u'凭据仍 61 条（没多没少）')

print()
print(u'===== ⑤ 复核图：原始 128 / 被否掉的 16 / **成品 32** =====')
GAP, M, CELL = 12, 12, 128
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
                                   (rej, 8), (cur, 4))):
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
print(u'  左=原始 128x128 ／ 中=**被否掉的 16x16**（8x，看左尖角那个孤点）／ 右=**成品 32x32**（4x）⇒ %s' % PV)

print()
print(u'===== ⑥ processResources + 产物 + 门（含 ModelCheck 的孤儿清单）=====')
r = subprocess.run([os.path.join(ROOT, 'gradlew.bat'), 'processResources', '--console=plain'], cwd=ROOT,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
check(u'BUILD SUCCESSFUL' in r.stdout.decode('utf-8', 'replace'), u'gradle processResources BUILD SUCCESSFUL')
for n in ('gravity_device', 'ore_detector'):
    a = os.path.join(TEXI, n + '.png')
    b = os.path.join(BTEXI, n + '.png')
    hb = sha1b(open(b, 'rb').read()) if os.path.exists(b) else 'MISSING'
    check(sha1b(open(a, 'rb').read()) == hb, u'产物 %-22s %s…' % (n + '.png', hb[:12]))
for g in ['TextureCheck.py', 'ModelCheck.py', 'JsonCheck.py']:
    rr = subprocess.run([sys.executable, os.path.join(TOOLS, g)], cwd=ROOT,
                        env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o = rr.stdout.decode('utf-8', 'replace')
    io.open(os.path.join(TOOLS, '_zf179_' + g.split('.')[0] + '.txt'), 'w', encoding='utf-8',
            newline='\n').write(o)
    tail = [l.strip() for l in o.splitlines() if (u'失败' in l or u'结论' in l or u'提示' in l or u'非法' in l)]
    print(u'  %-18s rc=%d  %s' % (g, rr.returncode, u' | '.join(tail[-2:])))
    check(rr.returncode == 0, u'%s rc=0' % g)
mc = io.open(os.path.join(TOOLS, '_zf179_ModelCheck.txt'), encoding='utf-8').read()
print(u'  --- ModelCheck 的孤儿提示（33 -> 36 那三条）---')
for l in mc.splitlines():
    if l.strip().startswith(u'[WARN]') or u'孤儿' in l:
        print(u'  ' + l.strip()[:150])

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
