# -*- coding: utf-8 -*-
r"""_zf172_fix.py —— 撤销对**灌装机**的误改 + 把三张素材落到**饮料罐装机**（可重跑）

事实（用户原话）：「不不不宝 是饮料罐装机改贴图 不是灌装机」
本工程有**两台**机器：`filling_machine` = **灌装机**、`beverage_canning_machine` = **饮料罐装机**。
ZF170/ZF171 我把素材落到了灌装机上 —— 那是**误放**，这一轮原样退回，再落对地方。

罐装机的模型本来只有 top / side 两个槽（`up`+`down` 都用 `#top`，四面都用 `#side`，**没有正面**）
⇒ 用户给的「顶部 / 侧面 / 底部」正好对上：顶部→top、侧面→side、**底部新开 `bottom` 槽**。

⚠ 第一次跑时我用**平名字**去 `zf170_pre` 找那两个贴图，可它们是 `_zf170_fixbak.py` 写的
   **带路径编码**的名字（`src__main__…__filling_machine_side.png`）⇒ 找不到、脚本中途抛异常。
   这一版改成**按后缀在备份目录里找**（`find_in`），并且整脚本可重跑。
"""
# ⚠⚠ **不要重跑**：第一步会把**现值**当成改前件抄进 `zf172_pre`，
#   而现值已经是新贴图了 ⇒ 重跑会把真正的改前件覆盖掉。
#   （这一轮已经执行完毕；要重做请先从 `zf172_pre` 把改前件护住。）
import io, os, sys, json, shutil, hashlib, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
ASSET = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
TEXB = os.path.join(ASSET, 'textures', 'block')
BTEXB = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'textures', 'block')
SRC = os.path.join(ROOT, 'build', '用户素材')
CRED = os.path.join(SRC, '_来源凭据.json')
P170 = os.path.join(TOOLS, 'zf170_pre')
P171 = os.path.join(TOOLS, 'zf171_pre')
PRE = os.path.join(TOOLS, 'zf172_pre')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)
def sha1(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()
def find_in(d, suffix):
    if not os.path.isdir(d):
        return None
    for f in sorted(os.listdir(d)):
        if f.endswith(suffix):
            return os.path.join(d, f)
    return None

print(u'===== 轮号 =====')
print(u'  zf172_pre %s ／ 别人的 _zf172_verify.py %s'
      % (u'已存在（本轮重跑）' if os.path.exists(PRE) else u'还是空的',
         u'**已存在**' if os.path.exists(os.path.join(TOOLS, '_zf172_verify.py')) else u'不存在'))
check(not os.path.exists(os.path.join(TOOLS, '_zf172_verify.py')), u'没人用过 ZF172 这个号（没有别人的门）')

print()
print(u'===== ① 备份"罐装机"的改前件（这轮真正要改的那台）=====')
os.makedirs(PRE, exist_ok=True)
CAN = ['textures/block/beverage_canning_machine_side.png',
       'textures/block/beverage_canning_machine_top.png',
       'models/block/beverage_canning_machine.json']
before = {}
for rel in CAN:
    a = os.path.join(ASSET, rel.replace('/', os.sep))
    check(os.path.exists(a), u'改前件在：%s' % rel)
    if os.path.exists(a):
        shutil.copy2(a, os.path.join(PRE, rel.replace('/', '__')))
        before[rel] = sha1(a)
        check(sha1(os.path.join(PRE, rel.replace('/', '__'))) == before[rel],
              u'  备份回读一致（%s…）' % before[rel][:12])
print(u'  罐装机改前：side %s… ／ top %s… ／ model %s…'
      % (before.get(CAN[0], u'?')[:12], before.get(CAN[1], u'?')[:12], before.get(CAN[2], u'?')[:12]))

print()
print(u'===== ② 撤销对灌装机的误改（回到 ZF170 之前的原样）=====')
REV = [('filling_machine_side.png', P170, '719c785060ce'),
       ('filling_machine_top.png', P170, '8bedfc2b861d'),
       ('filling_machine_front.png', P171, '3430395ef96d')]
for name, src_dir, want in REV:
    s = find_in(src_dir, name)
    d = os.path.join(TEXB, name)
    check(s is not None, u'备份里有 %s（在 %s 里按后缀找到）' % (name, os.path.basename(src_dir)))
    if s is None:
        continue
    open(d, 'wb').write(open(s, 'rb').read())
    h = sha1(d)
    check(h.startswith(want), u'%s 已退回 %s…（应为 %s…）' % (name, h[:12], want))
b = os.path.join(TEXB, 'filling_machine_bottom.png')
if os.path.exists(b):
    shutil.move(b, os.path.join(PRE, 'filling_machine_bottom.png.误建件'))
check(not os.path.exists(b), u'误建的 filling_machine_bottom.png 不在工程里（已挪进 zf172_pre）')
ms = find_in(P170, 'filling_machine.json')
check(ms is not None, u'备份里有灌装机模型（%s）' % (os.path.basename(ms) if ms else u'?'))
if ms:
    md = os.path.join(ASSET, 'models', 'block', 'filling_machine.json')
    shutil.copy2(ms, md)
    m = json.loads(io.open(md, encoding='utf-8').read())
    check('bottom' not in m['textures'], u'灌装机模型已退回：没有 bottom 槽')
    check(m['elements'][0]['faces']['down']['texture'] == '#top', u'灌装机 down 面退回 #top')
    check(m['elements'][0]['faces']['north']['texture'] == '#front', u'灌装机 north 面仍 #front')
    check(sha1(md) == sha1(ms), u'灌装机模型与 ZF170 改前件逐字节相同')

print()
print(u'===== ③ 落到罐装机（原字节复制）=====')
PAIRS = [(u'饮料灌装机侧面_001.png', 'textures/block/beverage_canning_machine_side.png', u'侧面'),
         (u'饮料灌装机顶部_001.png', 'textures/block/beverage_canning_machine_top.png', u'顶部'),
         (u'饮料灌装机底部_001.png', 'textures/block/beverage_canning_machine_bottom.png', u'底部')]
for name, rel, zh in PAIRS:
    sp = os.path.join(SRC, name)
    tp = os.path.join(ASSET, rel.replace('/', os.sep))
    data = open(sp, 'rb').read()
    open(tp, 'wb').write(data)
    w, h, px = read_png(tp)
    check(sha1(tp) == sha1(sp) and (w, h) == (16, 16),
          u'%s ← %s（%dx%d，%s…）' % (rel.split('/')[-1], name, w, h, sha1(tp)[:12]))

print()
print(u'===== ④ 罐装机模型：新开 bottom 槽、down 面改指自己 =====')
mp = os.path.join(ASSET, 'models', 'block', 'beverage_canning_machine.json')
t = io.open(mp, encoding='utf-8').read()
if u'"bottom"' in t:
    print(u'  [幂等] 罐装机模型已有 bottom 槽')
else:
    a1 = u'"top": "potato_s_t:block/beverage_canning_machine_top",'
    b1 = (u'"top": "potato_s_t:block/beverage_canning_machine_top",\n'
          u'    "bottom": "potato_s_t:block/beverage_canning_machine_bottom",')
    a2 = u'"down": { "uv": [0, 0, 16, 16], "texture": "#top" },'
    b2 = u'"down": { "uv": [0, 0, 16, 16], "texture": "#bottom" },'
    check(t.count(a1) == 1, u'top 槽锚点命中 1 次（实测 %d）' % t.count(a1))
    check(t.count(a2) == 1, u'down 面锚点命中 1 次（实测 %d）' % t.count(a2))
    io.open(mp, 'w', encoding='utf-8', newline='\n').write(t.replace(a1, b1).replace(a2, b2))
m = json.loads(io.open(mp, encoding='utf-8').read())
check(m['textures'].get('bottom') == 'potato_s_t:block/beverage_canning_machine_bottom', u'bottom 槽在')
check(m['elements'][0]['faces']['down']['texture'] == '#bottom', u'down 面指 #bottom')
check(m['elements'][0]['faces']['up']['texture'] == '#top', u'up 面仍 #top')
for k in ('north', 'south', 'east', 'west'):
    check(m['elements'][0]['faces'][k]['texture'] == '#side', u'%s 面仍 #side' % k)

print()
print(u'===== ⑤ 凭据：三条误记的键名改成罐装机 =====')
raw = io.open(CRED, encoding='utf-8').read()
data = json.loads(raw)
check((json.dumps(data, ensure_ascii=False, indent=2) + '\n') == raw, u'凭据"读进来再原样写回"与盘上逐字节相同')
REN = {'filling_machine_side.png': ('beverage_canning_machine_side.png', u'侧面'),
       'filling_machine_top.png': ('beverage_canning_machine_top.png', u'顶部')}
for old, (new, zh) in REN.items():
    if old in data:
        e = data.pop(old)
        e[u'说明'] = (u'用户 ZF172 给的饮料**罐装机**%s贴图（16x16 / 8 位 RGBA；素材原名 `%s` —— '
                      u'名字里写的是"灌装机"，用户随后澄清是**罐装机**）⇒ 原字节复制成 textures/block/%s。'
                      % (zh, e.get(u'原名'), new))
        e[u'轮次'] = u'ZF172'
        data[new] = e
        check(True, u'%s -> %s' % (old, new))
    else:
        check(new in data, u'凭据里已是 %s（%s 已不在）' % (new, old))
if 'beverage_canning_machine_bottom.png' not in data:
    data['beverage_canning_machine_bottom.png'] = {
        u'原名': u'饮料灌装机底部_001.png',
        u'sha1': sha1(os.path.join(SRC, u'饮料灌装机底部_001.png')),
        u'bytes': os.path.getsize(os.path.join(SRC, u'饮料灌装机底部_001.png')),
        u'轮次': u'ZF172',
        u'说明': u'用户 ZF172 给的饮料**罐装机**底部贴图（16x16 / 8 位 RGBA）⇒ 原字节复制成 '
                u'textures/block/beverage_canning_machine_bottom.png，并给罐装机的模型**新开 bottom 槽**'
                u'（原来底面用的是顶面那张）。',
    }
io.open(CRED, 'w', encoding='utf-8', newline='\n').write(json.dumps(data, ensure_ascii=False, indent=2) + u'\n')
back = json.loads(io.open(CRED, encoding='utf-8').read())
check('filling_machine_side.png' not in back and 'filling_machine_top.png' not in back, u'凭据里已无灌装机那两个误记键')
check(all(k in back for k in ('beverage_canning_machine_side.png', 'beverage_canning_machine_top.png',
                             'beverage_canning_machine_bottom.png')), u'罐装机三条都在')
check(len(back) == 59, u'凭据条数 = 59（55 原有 + ZF170 三条 + ZF172 新增的 bottom 一条；实测 %d）' % len(back))

print()
print(u'===== ⑥ processResources + 产物核对 + 三门 =====')
r = subprocess.run([os.path.join(ROOT, 'gradlew.bat'), 'processResources', '--console=plain'], cwd=ROOT,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
check(u'BUILD SUCCESSFUL' in r.stdout.decode('utf-8', 'replace'), u'gradle processResources BUILD SUCCESSFUL')
for rel in ['textures/block/beverage_canning_machine_side.png', 'textures/block/beverage_canning_machine_top.png',
            'textures/block/beverage_canning_machine_bottom.png', 'textures/block/filling_machine_side.png',
            'textures/block/filling_machine_top.png', 'textures/block/filling_machine_front.png']:
    a = os.path.join(ASSET, rel.replace('/', os.sep))
    bb = os.path.join(BTEXB, rel.split('/')[-1])
    hb = sha1(bb) if os.path.exists(bb) else 'MISSING'
    check(sha1(a) == hb, u'产物 %-40s %s…' % (rel.split('/')[-1], hb[:12]))
bm = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'models', 'block', 'beverage_canning_machine.json')
check(os.path.exists(bm) and u'"bottom"' in io.open(bm, encoding='utf-8').read(), u'产物里的罐装机模型带 bottom 槽')
fm = os.path.join(ROOT, 'build', 'resources', 'main', 'assets', 'potato_s_t', 'models', 'block', 'filling_machine.json')
check(u'"bottom"' not in io.open(fm, encoding='utf-8').read(), u'产物里的灌装机模型**没有** bottom 槽（误改已退）')

print()
print(u'===== ⑦ 复核图（罐装机：改前 / 改后）=====')
S, GAP, M = 8, 10, 10
CELL = 16 * S
ROWS = [(u'改前 side/top（占位）', [os.path.join(PRE, 'textures__block__beverage_canning_machine_%s.png' % k)
                                for k in ('side', 'top')]),
        (u'改后 side/top/bottom', [os.path.join(TEXB, 'beverage_canning_machine_%s.png' % k) for k in ('side', 'top', 'bottom')])]
W = M * 2 + CELL * 3 + GAP * 2
H = M * 2 + CELL * 2 + GAP * 3
cv = bytearray(W * H * 4)
for y in range(H):
    for x in range(W):
        v = 62 if ((x // 8 + y // 8) % 2 == 0) else 74
        i = (y * W + x) * 4
        cv[i] = cv[i + 1] = cv[i + 2] = v
        cv[i + 3] = 255
for rr, (label, ps) in enumerate(ROWS):
    oy = M + rr * (CELL + GAP * 2)
    for c, p in enumerate(ps):
        if not os.path.exists(p):
            continue
        w, h, px = read_png(p)
        ox = M + c * (CELL + GAP)
        for y in range(16):
            for x in range(16):
                i = (y * 16 + x) * 4
                if not px[i + 3]:
                    continue
                for dy in range(S):
                    for dx in range(S):
                        di = ((oy + y * S + dy) * W + (ox + x * S + dx)) * 4
                        cv[di:di + 4] = px[i:i + 4]


def write_png2(path, w, h, rgba):
    import zlib, struct
    raw2 = bytearray()
    for y in range(h):
        raw2.append(0)
        raw2 += rgba[y * w * 4:(y + 1) * w * 4]

    def ch(tag, data_):
        return struct.pack('>I', len(data_)) + tag + data_ + struct.pack('>I', zlib.crc32(tag + data_) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += ch(b'IDAT', zlib.compress(bytes(raw2), 9)) + ch(b'IEND', b'')
    open(path, 'wb').write(png)


PV = os.path.join(TOOLS, '_zf172_preview.png')
write_png2(PV, W, H, cv)
print(u'  上排 = 改前（side / top 占位）、下排 = 改后（side / top / bottom）⇒ %s' % PV)

print()
print(u'===== ⑧ 三门 =====')
for g in ['TextureCheck.py', 'ModelCheck.py', 'JsonCheck.py']:
    rr = subprocess.run([sys.executable, os.path.join(TOOLS, g)], cwd=ROOT,
                        env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    o = rr.stdout.decode('utf-8', 'replace')
    tail = [l.strip() for l in o.splitlines() if (u'失败' in l or u'结论' in l or u'非法' in l or u'提示' in l)]
    print(u'  %-20s rc=%d  %s' % (g, rr.returncode, u' | '.join(tail[-2:])))
    check(rr.returncode == 0, u'%s rc=0' % g)

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
