# -*- coding: utf-8 -*-
r"""_zf170_apply.py —— 饮料灌装机三面新材质（侧面 / 顶部 / 底部）

用法：`python _zf170_apply.py dry` 只侦察；不带参数才真改。

素材名把四个槽里的三个点得很清楚：**侧面 / 顶部 / 底部**（没有"正面"）。
现有模型 `models/block/filling_machine.json` 有 **three** 个贴图槽（top / side / front），
`up` 与 `down` **都**用 `#top`（重复用同一张）⇒ 这轮：
  · `side`  ← 侧面
  · `top`   ← 顶部
  · **新增 `bottom` 槽** ← 底部，并把 `down` 面从 `#top` 改成 `#bottom`（与采油机 ZF154 同一套做法）
  · `front` **不动**（用户没给正面图）—— 这一条会在汇报里点名请他拍板
"""
import io, json, os, sys, shutil, hashlib, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png

DRY = (len(sys.argv) > 1 and sys.argv[1].lower() == 'dry')
ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
TOOLS = os.path.join(ROOT, 'build', 'zftools')
PRE = os.path.join(TOOLS, 'zf170_pre')
SRC = os.path.join(ROOT, 'build', '用户素材')
ASSET = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
MODEL_REL = 'models/block/filling_machine.json'
CRED = os.path.join(SRC, '_来源凭据.json')

PAIRS = [
    (u'饮料灌装机侧面_001.png', 'textures/block/filling_machine_side.png', u'侧面', u'四面（南/东/西）'),
    (u'饮料灌装机顶部_001.png', 'textures/block/filling_machine_top.png', u'顶部', u'顶面'),
    (u'饮料灌装机底部_001.png', 'textures/block/filling_machine_bottom.png', u'底部', u'底面（本轮新开的槽）'),
]

fails = []
def check(ok, msg):
    print(('  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

def sha1(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()

def ihdr(p):
    b = open(p, 'rb').read(33)
    assert b[:8] == b'\x89PNG\r\n\x1a\n', 'not png: ' + p
    w, h = struct.unpack('>II', b[16:24])
    return w, h, b[24], b[25]

def info(label, p):
    if not os.path.exists(p):
        print(u'  %-40s MISSING' % label)
        return None
    w, h, d, ct = ihdr(p)
    ww, hh, px = read_png(p)
    opaque = sum(1 for i in range(3, len(px), 4) if px[i])
    cols = len(set((px[i], px[i + 1], px[i + 2], px[i + 3]) for i in range(0, len(px), 4)))
    print(u'  %-40s %2dx%-3d depth=%d ctype=%d opaque=%-4d/%-4d colors=%-4d %d B  %s'
          % (label, w, h, d, ct, opaque, w * h, cols, os.path.getsize(p), sha1(p)[:12].lower()))
    return (w, h, opaque, cols, px)

print(u'===== ① 素材（真解码）=====')
print(u'  轮号检查：zf170_pre %s / 别人的 _zf170_verify.py %s'
      % (u'不存在' if not os.path.exists(PRE) else u'**已存在**',
         u'不存在' if not os.path.exists(os.path.join(TOOLS, '_zf170_verify.py')) else u'**已存在**'))
check(not os.path.exists(PRE), u'zf170 还是空的（备份目录不存在）')
check(not os.path.exists(os.path.join(TOOLS, '_zf170_verify.py')), u'没人用过 ZF170 这个号')
srcs = {}
for name, tgt, zh, where in PAIRS:
    r = info(name + u'（' + zh + u' → ' + where + u'）', os.path.join(SRC, name))
    check(r is not None, u'素材在：%s' % name)
    if r:
        check((r[0], r[1]) == (16, 16), u'%s 是 16x16（实测 %dx%d）' % (name, r[0], r[1]))
        srcs[name] = r
check(len(srcs) == 3, u'三张都在（实测 %d）' % len(srcs))

print()
print(u'===== ② 现状（模型与三个槽）=====')
mp = os.path.join(ASSET, MODEL_REL.replace('/', os.sep))
mtxt = io.open(mp, encoding='utf-8').read()
m = json.loads(mtxt)
print(u'  模型槽位：%s' % json.dumps(m.get('textures', {}), ensure_ascii=False))
faces = m['elements'][0]['faces']
for k in ('up', 'down', 'north', 'south', 'east', 'west'):
    print(u'    %-6s -> %s' % (k, faces[k]['texture']))
check(u'"top": "potato_s_t:block/filling_machine_top",' in mtxt, u'模型里有 top 槽（锚点 1 次）')
check(mtxt.count(u'"texture": "#top"') == 2, u'up 与 down **都**用 #top（实测 %d 处）' % mtxt.count(u'"texture": "#top"'))
check(u'"bottom"' not in mtxt, u'模型里**还没有** bottom 槽（本轮新开）')
for name, tgt, zh, where in PAIRS[:2]:
    p = os.path.join(ASSET, tgt.replace('/', os.sep))
    if os.path.exists(p):
        info(u'在用：' + tgt.split('/')[-1], p)
info(u'在用：filling_machine_front.png（本轮不动）', os.path.join(ASSET, 'textures/block/filling_machine_front.png'.replace('/', os.sep)))

print()
print(u'===== ③ 三张素材互不相同（防"同一张图贴三遍"）=====')
px3 = [srcs[n][4] for n, _, _, _ in PAIRS]
for i in range(3):
    for j in range(i + 1, 3):
        same = px3[i] == px3[j]
        check(not same, u'%s vs %s 不是同一张' % (PAIRS[i][0], PAIRS[j][0]))

if DRY:
    print()
    print(u'（dry：什么都没改。计划：备份 3 份在用贴图 + 模型 + 凭据 → 原字节复制 3 张 → '
          u'模型加 bottom 槽、down 面改 #bottom → 凭据 +3 条）')
    sys.exit(1 if fails else 0)

print()
print(u'===== ④ 改前备份 -> zf170_pre =====')
os.makedirs(PRE, exist_ok=True)
BAK = ['textures/block/filling_machine_side.png', 'textures/block/filling_machine_top.png',
       'textures/block/filling_machine_front.png', MODEL_REL,
       'build/用户素材/_来源凭据.json', 'docs/贴图清单.md', 'docs/开发档案.md',
       'docs/UpdateAnnouncement_EN.md']
lines = []
# ⚠ ZF170 补账：这里原来只拼 ROOT —— 而 `textures/`、`models/` 是**相对 ASSET** 的，
#   四份改前件当场被判 MISSING、一份都没抄（其中三张贴图还被覆盖了）。
#   真正的改前件已用 `_zf170_fixbak.py` 从 git HEAD 取回（见 §4.165 第 2 次）。
for rel in BAK:
    base = ROOT if rel.startswith(('docs/', 'build/')) else os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t')
    a = os.path.join(base, rel.replace('/', os.sep))
    dst = os.path.join(PRE, rel.replace('/', '__'))
    if os.path.exists(a):
        shutil.copy2(a, dst)
        h = sha1(a)
        lines.append(u'%s\t%s\t%d\t(备份)' % (rel, h, os.path.getsize(a)))
        check(sha1(dst) == h, u'备份回读一致：%s' % rel)
    else:
        lines.append(u'%s\tMISSING' % rel)
        check(False, u'改前件不在：%s' % rel)
lines.append(u'%s\t改前不存在（本轮**新建件**）' % 'textures/block/filling_machine_bottom.png')
io.open(os.path.join(PRE, '_sha1.txt'), 'w', encoding='utf-8', newline='\n').write(u'\n'.join(lines) + u'\n')

print()
print(u'===== ⑤ 落位（原字节复制）=====')
for name, tgt, zh, where in PAIRS:
    sp = os.path.join(SRC, name)
    tp = os.path.join(ASSET, tgt.replace('/', os.sep))
    data = open(sp, 'rb').read()
    open(tp, 'wb').write(data)
    check(sha1(tp) == sha1(sp), u'%s 逐字节一致（%s）' % (tgt, sha1(tp)[:12].lower()))

print()
print(u'===== ⑥ 模型：加 bottom 槽 + down 面改指自己 =====')
a1 = u'"top": "potato_s_t:block/filling_machine_top",'
b1 = (u'"top": "potato_s_t:block/filling_machine_top",\n'
      u'    "bottom": "potato_s_t:block/filling_machine_bottom",')
check(mtxt.count(a1) == 1, u'槽位锚点命中 1 次（实测 %d）' % mtxt.count(a1))
a2 = u'"down": { "uv": [0, 0, 16, 16], "texture": "#top" },'
b2 = u'"down": { "uv": [0, 0, 16, 16], "texture": "#bottom" },'
check(mtxt.count(a2) == 1, u'down 面锚点命中 1 次（实测 %d）' % mtxt.count(a2))
new = mtxt.replace(a1, b1).replace(a2, b2)
io.open(mp, 'w', encoding='utf-8', newline='\n').write(new)
back = json.loads(io.open(mp, encoding='utf-8').read())
check(back['textures'].get('bottom') == 'potato_s_t:block/filling_machine_bottom', u'bottom 槽已加')
check(back['elements'][0]['faces']['down']['texture'] == '#bottom', u'down 面已指向 #bottom')
check(back['elements'][0]['faces']['up']['texture'] == '#top', u'up 面仍是 #top')
check(back['elements'][0]['faces']['north']['texture'] == '#front', u'north 面仍是 #front（正面没动）')
check(back['textures'].get('front') == 'potato_s_t:block/filling_machine_front', u'front 槽没动')

print()
print(u'===== ⑦ 凭据登记 =====')
raw = io.open(CRED, encoding='utf-8').read()
data = json.loads(raw)
check((json.dumps(data, ensure_ascii=False, indent=2) + '\n') == raw,
      u'凭据文件"读进来再原样写回"与盘上逐字节相同（⇒ 我的改动是纯追加）')
n0 = len(data)
for name, tgt, zh, where in PAIRS:
    key = os.path.basename(tgt)
    if key in data:
        check(False, u'凭据里已有 %s' % key)
        continue
    data[key] = {
        u'原名': name,
        u'sha1': sha1(os.path.join(SRC, name)),
        u'bytes': os.path.getsize(os.path.join(SRC, name)),
        u'轮次': u'ZF170',
        u'说明': u'用户 ZF170 给的饮料灌装机%s贴图（16x16 / 8 位 RGBA）⇒ 原字节复制成 %s，用于%s。'
                % (zh, tgt, where),
    }
io.open(CRED, 'w', encoding='utf-8', newline='\n').write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
check(len(json.loads(io.open(CRED, encoding='utf-8').read())) == n0 + 3, u'凭据 %d -> %d 条' % (n0, n0 + 3))

print()
print(u'失败项 = %d' % len(fails))
for f in fails:
    print(u'  !! ' + f)
sys.exit(1 if fails else 0)
