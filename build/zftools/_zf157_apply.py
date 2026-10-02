# -*- coding: utf-8 -*-
r"""_zf157_apply.py —— ZF157：钛合金套 4 件背包图标 + 热力金属新贴图（0.12）

用户原话：「材质加一下喂 宝宝 你上回把钛合金装备和热力金属新材质都遗漏了」

事实（_zf157_probe.py 真解码得出，不看文件名）：
  · 素材 5 份全是 16x16 / 8 位 / RGBA / **零半透明**；
  · 四件盔甲的 alpha 掩码不透明像素 78 / 138 / 104 / 88 —— 与 ZF116 那四件
    星璨钢**图标**同族（头盔对星璨钢头盔图标 IoU 0.974）；
  · 热力金属的不透明像素 = **135**，与 ZF143 那四种锭的锭形**完全相同**。
  ⇒ 四件是**背包图标**（不是 64x32 的盔甲层），一件是锭形物品图。
"""
import sys, os, io, json, hashlib, struct, shutil
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

ROOT = r'E:\PotatoST'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
PRE = os.path.join(TOOLS, 'zf157_pre')
SRC = os.path.join(ROOT, 'build', '用户素材')
ASSET = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
CRED = os.path.join(SRC, '_来源凭据.json')

fails, notes = [], []
def check(ok, msg):
    (notes if ok else fails).append(msg)
    print(('  [OK]   ' if ok else '  [FAIL] ') + msg)

def sha1(p):
    with open(p, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()

def ihdr(p):
    with open(p, 'rb') as f:
        b = f.read(33)
    assert b[:8] == b'\x89PNG\r\n\x1a\n', 'not a real PNG: ' + p
    w, h = struct.unpack('>II', b[16:24])
    return dict(w=w, h=h, depth=b[24], ctype=b[25], interlace=b[28])

def decode(p):
    w, h, px = read_png(p)
    opaque = half = 0
    m = []
    for y in range(h):
        row = []
        for x in range(w):
            a = px[(y * w + x) * 4 + 3]
            row.append(1 if a else 0)
            if a:
                opaque += 1
                if a != 255:
                    half += 1
        m.append(row)
    return w, h, opaque, half, m

def iou(a, b):
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        return None
    inter = sum(1 for y in range(len(a)) for x in range(len(a[0])) if a[y][x] and b[y][x])
    union = sum(1 for y in range(len(a)) for x in range(len(a[0])) if a[y][x] or b[y][x])
    return inter / union if union else 0.0

# (素材名, 目标贴图(相对 ASSET), 不透明像素, 模型(相对 ASSET), 模型里要被换掉的旧值)
ITEMS = [
    (u'钛合金头盔_001.png', 'textures/item/titanium_alloy_helmet.png', 78,
     'models/item/titanium_alloy_helmet.json', 'minecraft:item/iron_helmet', u'钛合金头盔'),
    (u'钛合金胸甲_001.png', 'textures/item/titanium_alloy_chestplate.png', 138,
     'models/item/titanium_alloy_chestplate.json', 'minecraft:item/iron_chestplate', u'钛合金胸甲'),
    (u'钛合金护腿_001.png', 'textures/item/titanium_alloy_leggings.png', 104,
     'models/item/titanium_alloy_leggings.json', 'minecraft:item/iron_leggings', u'钛合金护腿'),
    (u'钛合金靴子_001.png', 'textures/item/titanium_alloy_boots.png', 88,
     'models/item/titanium_alloy_boots.json', 'minecraft:item/iron_boots', u'钛合金靴子'),
    (u'热力金属_001.png', 'textures/item/thermal_metal.png', 135,
     'models/item/thermal_metal.json', None, u'热力金属'),
]

print(u'===== ① 改前备份 -> zf157_pre =====')
os.makedirs(PRE, exist_ok=True)
BAK = [u'textures/item/thermal_metal.png',
       u'models/item/titanium_alloy_helmet.json', u'models/item/titanium_alloy_chestplate.json',
       u'models/item/titanium_alloy_leggings.json', u'models/item/titanium_alloy_boots.json',
       u'docs/贴图清单.md', u'docs/开发档案.md', u'docs/UpdateAnnouncement_EN.md',
       u'build/zftools/_zf90_verify.py', u'build/用户素材/_来源凭据.json']
lines = []
# ⚠ ZF157 补账：这里原来写的是 `os.path.join(ROOT, rel)` —— 但资源类的 rel
#   是**相对 ASSET** 的，于是五份改前件当场被判成 MISSING、一份都没抄（当时打了 [MISS]）。
#   真正的改前件已经用 `_zf157_finish.py` 从 git HEAD 取回。
ASSET_REL_BAK = 'src/main/resources/assets/potato_s_t/'
for rel in BAK:
    base = ROOT if rel.startswith(('docs/', 'build/')) else os.path.join(ROOT, ASSET_REL_BAK.replace('/', os.sep))
    a = os.path.join(base, rel.replace('/', os.sep))
    dst = os.path.join(PRE, rel.replace('/', '__'))
    if os.path.exists(a):
        shutil.copy2(a, dst)
        h = sha1(a)
        lines.append('%s  %s  %d' % (rel, h, os.path.getsize(a)))
        if sha1(dst) != h:
            fails.append(u'备份回读不一致：' + rel)
    else:
        lines.append('%s  MISSING' % rel)
        print(u'  [MISS] ' + rel)
for rel, _, _, _, _, _ in ITEMS:
    t = os.path.join(ASSET, ITEMS[0][1])  # placeholder, real loop below
    break
for it in ITEMS:
    tgt = os.path.join(ASSET, it[1].replace('/', os.sep))
    if not os.path.exists(tgt):
        lines.append(u'%s  MISSING（本轮的**新建件**，改前不存在）' % it[1])
for i in range(4):
    tgt = os.path.join(ASSET, ITEMS[i][1].replace('/', os.sep))
    print(u'  %s  %s' % (u'[新建件·改前不存在]' if not os.path.exists(tgt) else u'[!! 已存在]', ITEMS[i][1]))
io.open(os.path.join(PRE, '_sha1.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
n_copied = sum(1 for rel in BAK if os.path.exists(os.path.join(PRE, rel.replace('/', '__'))))
check(n_copied == len(BAK), u'备份 %d/%d 份（清单见 zf157_pre/_sha1.txt）' % (n_copied, len(BAK)))

print()
print(u'===== ② 素材体检（真解码）=====')
masks = {}
src_sha = {}
for name, tgt, want_opaque, model, old, zh in ITEMS:
    sp = os.path.join(SRC, name)
    ok = os.path.exists(sp)
    check(ok, u'素材存在：%s' % name)
    if not ok:
        continue
    d = ihdr(sp)
    check(d['w'] == 16 and d['h'] == 16, u'%s 尺寸 16x16（实测 %dx%d）' % (name, d['w'], d['h']))
    check(d['depth'] == 8 and d['ctype'] == 6, u'%s 8 位 RGBA（depth=%d ctype=%d）' % (name, d['depth'], d['ctype']))
    w, h, opaque, half, m = decode(sp)
    check(opaque == want_opaque, u'%s 不透明像素 = %d（实测 %d）' % (name, want_opaque, opaque))
    check(half == 0, u'%s 零半透明像素（实测 %d）' % (name, half))
    masks[name] = (w, h, m)
    src_sha[name] = sha1(sp)
    print(u'         sha1 = %s   bytes = %d' % (src_sha[name][:12].lower(), os.path.getsize(sp)))

# 形状佐证：头盔图标 vs 星璨钢头盔图标（同一件东西的两个配色）
ref = os.path.join(ASSET, 'textures', 'item', 'star_steel_helmet.png')
if os.path.exists(ref):
    _, _, _, _, rm = decode(ref)
    v = iou(masks[u'钛合金头盔_001.png'][2], rm)
    check(v is not None and v >= 0.90, u'头盔图标掩码 vs 星璨钢头盔图标 IoU = %.4f（≥0.90 ⇒ 同一族的盔甲图标）' % v)
# 四件互不相同（否则是同一张图贴四遍）
for i in range(4):
    for j in range(i + 1, 4):
        a = ITEMS[i][0]; b = ITEMS[j][0]
        v = iou(masks[a][2], masks[b][2])
        check(v is not None and v < 0.90, u'%s vs %s IoU = %.4f（<0.90 ⇒ 四件各是各的形状）' % (a, b, v))
# 热力金属 = 锭形（与四种锭同一形状）
ing = os.path.join(ASSET, 'textures', 'item', 'silver_ingot.png')
if os.path.exists(ing):
    _, _, _, _, im = decode(ing)
    v = iou(masks[u'热力金属_001.png'][2], im)
    check(v is not None and v >= 0.95, u'热力金属掩码 vs 银锭掩码 IoU = %.4f（≥0.95 ⇒ 锭形）' % v)

print()
print(u'===== ③ 落位（原字节复制）+ 模型改指向 =====')
for name, tgt, want_opaque, model, old, zh in ITEMS:
    sp = os.path.join(SRC, name)
    tp = os.path.join(ASSET, tgt.replace('/', os.sep))
    os.makedirs(os.path.dirname(tp), exist_ok=True)
    with open(sp, 'rb') as f:
        data = f.read()
    with open(tp, 'wb') as f:
        f.write(data)
    back = sha1(tp)
    check(back == src_sha[name], u'%s 逐字节一致（%s）' % (tgt, back[:12].lower()))
    check(os.path.getsize(tp) == os.path.getsize(sp), u'%s 字节数 %d' % (tgt, os.path.getsize(tp)))
    # 模型：把 layer0 指到自己的贴图
    mp = os.path.join(ASSET, model.replace('/', os.sep))
    if old:
        txt = io.open(mp, encoding='utf-8').read()
        n = txt.count(u'"' + old + u'"')
        check(n == 1, u'%s 里旧值 `%s` 恰好出现 1 次（实测 %d）' % (model, old, n))
        if n == 1:
            newline = u'potato_s_t:item/' + os.path.basename(tgt)[:-4]
            txt = txt.replace(u'"' + old + u'"', u'"' + newline + u'"')
            io.open(mp, 'w', encoding='utf-8', newline='\n').write(txt)
            after = io.open(mp, encoding='utf-8').read()
            check(u'"' + newline + u'"' in after and old not in after,
                  u'%s 的 layer0 -> %s（parent 未动：%s）' % (model, newline,
                  u'"parent": "minecraft:item/generated"' in after))
    else:
        after = io.open(mp, encoding='utf-8').read()
        check(u'potato_s_t:item/thermal_metal' in after,
              u'%s 本来就指向自己的贴图 ⇒ 一个字节没动' % model)

print()
print(u'===== ④ 凭据登记（纯追加，先证明"不改也能原样写回"）=====')
raw = io.open(CRED, encoding='utf-8').read()
data = json.loads(raw)
same = (json.dumps(data, ensure_ascii=False, indent=2) + '\n') == raw
check(same, u'凭据文件能被"读进来再原样写回"（格式自洽，我的改动就是纯追加）')
n0 = len(data)
for name, tgt, want_opaque, model, old, zh in ITEMS:
    key = os.path.basename(tgt)
    if key in data:
        check(False, u'凭据里已经有 %s（不该覆盖）' % key)
        continue
    data[key] = {
        u'原名': name,
        u'sha1': src_sha[name],
        u'bytes': os.path.getsize(os.path.join(SRC, name)),
        u'轮次': u'ZF157',
        u'说明': u'用户 ZF157 给的 %s 贴图（16x16 / 8 位 RGBA / 零半透明）⇒ 原字节复制成 %s。'
                % (zh, tgt) + (u'物品模型由借原版 %s 改成指向自己（待画清单 13 -> 9）。' % old if old
                               else u'顶掉原来那张 160x160 的程序生成占位色块（物品模型本来就指向自己，一个字节没动）。'),
    }
io.open(CRED, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(data, ensure_ascii=False, indent=2) + '\n')
back = json.loads(io.open(CRED, encoding='utf-8').read())
check(len(back) == n0 + 5, u'凭据 %d -> %d 条' % (n0, len(back)))
for name, tgt, want_opaque, model, old, zh in ITEMS:
    k = os.path.basename(tgt)
    check(k in back and back[k][u'sha1'] == src_sha[name], u'凭据里 %s 的 sha1 与素材一致' % k)

print()
print(u'------------------------------')
print(u'失败项 = %d' % len(fails))
for f in fails:
    print(u'  !! ' + f)
print(u'结论: ' + (u'通过' if not fails else u'有失败项'))
sys.exit(1 if fails else 0)
