# -*- coding: utf-8 -*-
r"""_zf179_128.py —— ZF179 补记：引力装置**直接上 128×128 原样**（用户：「行直接上128」）

这一手最简单也最干净：**原字节复制**（不重采样、不二值化），sha1 与素材逐位相同。
代价（如实记账）：物品贴图固定画在 **16 逻辑像素**的四边形上 ⇒
  · 界面缩放 2（物品约 32 px）：128 会被 mipmap 平滑成"照片感"，不像像素画那么锐；
  · 界面缩放 4（约 64 px）：仍然平滑；**缩放 8** 才 1:1。
  也就是说低缩放时"更清楚"靠的是**细节多**，不是"像素锐"—— 预览图第三格就是低缩放的模拟。
"""
import io, os, sys, json, shutil, hashlib, struct, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
TEXI = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'textures', 'item')
BTEXI = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'item')
SRC = os.path.join(ROOT, 'build', '用户素材')
CRED = os.path.join(SRC, '_来源凭据.json')
PRE = os.path.join(TOOLS, 'zf179_pre')
DOCS = os.path.join(ROOT, 'docs')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def sha1b(b):
    return hashlib.sha1(b).hexdigest()
def read(p):
    return io.open(p, encoding='utf-8').read()
def write(p, t):
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

print(u'===== ① 留档 64x64，再上 128 原样 =====')
cur = os.path.join(TEXI, 'gravity_device.png')
w, h, _ = read_png(cur)
keep = os.path.join(PRE, 'gravity_device.64x64.png')
shutil.copy2(cur, keep)
check((w, h) == (64, 64), u'上线前的 64x64 已留档为 zf179_pre/gravity_device.64x64.png（实测 %dx%d）' % (w, h))
src = os.path.join(SRC, u'引力装置_001.png')
data = open(src, 'rb').read()
open(cur, 'wb').write(data)
w, h, px = read_png(cur)
op = sum(1 for i in range(3, len(px), 4) if px[i] == 255)
half = sum(1 for i in range(3, len(px), 4) if 0 < px[i] < 255)
check((w, h) == (128, 128), u'现在是 128x128（实测 %dx%d）' % (w, h))
check(sha1b(open(cur, 'rb').read()) == sha1b(data), u'**原字节复制**，与素材逐位相同（%s…）' % sha1b(data)[:12])
check(sha1b(data).startswith('8c283a8272b7'), u'正是素材 `引力装置_001.png` 那份（8c283a8272b7…）')
check(half == 0, u'零半透明（实体 %d / 16384 像素，3309 色）' % op)

print()
print(u'===== ② 凭据说明改成 128 原样 =====')
raw = read(CRED)
dj = json.loads(raw)
check((json.dumps(dj, ensure_ascii=False, indent=2) + u'\n') == raw, u'凭据自洽')
e = dj.get('gravity_device.png')
check(e is not None, u'凭据里有 gravity_device.png')
if e is not None:
    e[u'说明'] = (u'用户 ZF179 给的手持式引力装置贴图。**素材 128x128 / 3309 色 / 零半透明**。'
                  u'尺寸试过四档（都是量出来才定的）：128→16（8:1）造型被压坏（左尖角只剩孤立 1 像素，'
                  u'留档 _zf179_reject16.png）；128→32（4:1）完整但看不出来是黑洞；128→64（2:1）能用但'
                  u'用户仍要更清楚 ⇒ **最终用户拍板「直接上 128」：原字节复制、不重采样**，与素材 sha1 逐位相同。'
                  u'⚠ 代价如实记：物品贴图固定画在 16 逻辑像素的四边形上，**低界面缩放下靠 mipmap 平滑**，'
                  u'观感偏"照片感"而非像素画；缩放 8 才 1:1。TextureCheck 放行「16~256 的 2 的幂正方形」，'
                  u'128 不产生警告。')
io.open(CRED, 'w', encoding='utf-8', newline='\n').write(json.dumps(dj, ensure_ascii=False, indent=2) + u'\n')
check(u'直接上 128' in json.loads(read(CRED))['gravity_device.png'][u'说明'], u'凭据说明已写「直接上 128」')
check(len(json.loads(read(CRED))) == 61, u'凭据仍 61 条')

print()
print(u'===== ③ 复核图：64x64（2x）／ 128x128（1x）／ 128 在低缩放下的模拟（面积平均到 32 再 4x）=====')
w64, h64, p64 = read_png(keep)
w128, h128, p128 = read_png(cur)
# 模拟低缩放：128 -> 32（面积平均，只算不透明像素 + alpha 二值化）
sim = bytearray(32 * 32 * 4)
for by in range(32):
    for bx in range(32):
        r = g = b = cov = n = 0
        for y in range(by * 4, by * 4 + 4):
            for x in range(bx * 4, bx * 4 + 4):
                i = (y * 128 + x) * 4
                if p128[i + 3]:
                    cov += 1
                    r += p128[i]; g += p128[i + 1]; b += p128[i + 2]
                    n += 1
        o = (by * 32 + bx) * 4
        if n and cov * 2 >= 16:
            sim[o] = r // n; sim[o + 1] = g // n; sim[o + 2] = b // n; sim[o + 3] = 255
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

blit(p64, 64, 64, M, M, 2)
blit(p128, 128, 128, M + CELL + GAP, M, 1)
blit(sim, 32, 32, M + (CELL + GAP) * 2, M, 4)

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

PV = os.path.join(TOOLS, '_zf179_preview128.png')
write_png2(PV, W, H, cv)
print(u'  左=上一版 64x64（2x）／ 中=**现在上线的 128x128**（1x）／ 右=低缩放模拟 ⇒ %s' % PV)

print()
print(u'===== ④ processResources + 产物 + 门 =====')
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
    tail = [l.strip() for l in o.splitlines() if (u'失败' in l or u'结论' in l or u'提示' in l or u'非法' in l)]
    print(u'  %-18s rc=%d  %s' % (g, rr.returncode, u' | '.join(tail[-2:])))
    check(rr.returncode == 0, u'%s rc=0' % g)
    if u'gravity_device' in o:
        for l in o.splitlines():
            if u'gravity_device' in l and (u'WARN' in l or u'!!' in l):
                print(u'    !! ' + l.strip()[:150])

print()
print(u'===== ⑤ 文档补记（ZF179 补记：改上 128）=====')
LIST = os.path.join(DOCS, u'贴图清单.md')
ARCH = os.path.join(DOCS, u'开发档案.md')
ANN = os.path.join(DOCS, 'UpdateAnnouncement_EN.md')
NOTE = (u"\n- **ZF179 补记（用户拍板）**：「行直接上128」⇒ 引力装置**改用 128x128 原字节复制**（不重采样、不二值化，"
        u"sha1 与素材 `8c283a8272b7` 逐位相同）。上文那张四种定尺的对比表因此**只作留档**："
        u"16 / 32 / 64 三版都在 `build/zftools/`（`_zf179_reject16.png` / `_zf179_keep32.png` / "
        u"`zf179_pre/gravity_device.64x64.png`）。"
        u"⚠ 代价如实记：物品贴图固定画在 16 逻辑像素的四边形上 ⇒ **低界面缩放下靠 mipmap 平滑**，观感偏"
        u"「照片感」而不是像素画（预览 `_zf179_preview128.png` 第三格就是低缩放模拟）；缩放 8 才 1:1。\n")
t = read(LIST)
if u'ZF179 补记（用户拍板）' in t:
    print(u'  [幂等] 清单已记')
else:
    check(u'## ZF179（0.13）' in t, u'清单里有 ZF179 节')
    i = t.index(u'\n---\n', t.index(u'## ZF179（0.13）'))
    write(LIST, t[:i] + NOTE + t[i:])
    check(u'ZF179 补记（用户拍板）' in read(LIST), u'贴图清单已补记')
t = read(ARCH)
ADD = (u"　**ZF179 补记**：用户拍板「行直接上128」⇒ 引力装置改用 **128x128 原字节复制**"
       u"（sha1 `8c283a8272b7` 与素材逐位相同；16/32/64 三版留档在 `build/zftools/`）。")
if u'行直接上128' in t:
    print(u'  [幂等] 档案已记')
else:
    key = u"待画 **11 → 9**（落回原值） | 见 §4.165 / §9 |"
    n = t.count(key)
    check(n == 1, u'ZF179 行尾锚点命中 1 次（实测 %d）' % n)
    if n == 1:
        write(ARCH, t.replace(key, u"待画 **11 → 9**（落回原值） |" + ADD + u" 见 §4.165 / §9 |"))
        check(u'行直接上128' in read(ARCH), u'档案变更行已补记')
t = read(ANN)
EN = (u"\n**ZF179 follow-up:** the Gravity Device texture is now the **original 128x128**, copied in\n"
      u"byte-for-byte rather than rescaled. Note the trade-off for the record: an item texture is always\n"
      u"drawn on a 16-pixel quad, so at low GUI scales the extra detail is smoothed by mipmapping (it reads\n"
      u"more like a tiny illustration than pixel art); it is 1:1 only at GUI scale 8. The 16/32/64 variants\n"
      u"are kept in the tools folder.\n")
if u'ZF179 follow-up' in t:
    print(u'  [幂等] 公告已记')
else:
    if not t.endswith(u'\n'):
        t += u'\n'
    write(ANN, t + EN)
    check(u'ZF179 follow-up' in read(ANN), u'英文公告已补记')

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
