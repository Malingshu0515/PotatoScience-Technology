# -*- coding: utf-8 -*-
u"""ZF145 侦察：成就（advancement）现状盘点。
只读，不改任何文件。
"""
import json, os, io, sys, glob, re

ROOT = r'E:\PotatoST'
ADV  = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'potato_s_t', 'advancement')
LANG = os.path.join(ROOT, 'src', 'main', 'resources', 'assets', 'potato_s_t', 'lang')
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon.txt')

lines = []
def w(s=''):
    lines.append(s)

w(u'===== ZF145 侦察：成就盘点 =====')
w()

# ---------- 1. 全部成就 ----------
w(u'--- 1. 成就清单（35 个） ---')
rows = []
for p in sorted(glob.glob(os.path.join(ADV, '*.json'))):
    name = os.path.basename(p)[:-5]
    try:
        d = json.load(io.open(p, encoding='utf-8'))
    except Exception as e:
        w(u'[JSON 解析失败] %s : %s' % (name, e))
        continue
    disp = d.get('display') or {}
    icon = (disp.get('icon') or {}).get('id', '?')
    parent = d.get('parent', u'(根)')
    frame = disp.get('frame', 'task')
    hidden = disp.get('hidden', False)
    crit = list((d.get('criteria') or {}).keys())
    req = d.get('requirements') or []
    rows.append((name, parent.replace('potato_s_t:', ''), icon.replace('potato_s_t:', ''),
                 frame, hidden, len(crit), len(req)))
w(u'%-22s %-24s %-40s %-10s %-6s %s' % ('文件', '父', '图标', '框', '隐藏', '条件/组'))
for r in rows:
    w(u'%-22s %-24s %-40s %-10s %-6s %d/%d' % (r[0], r[1], r[2], r[3], u'是' if r[4] else u'否', r[5], r[6]))
w()

# ---------- 2. 成就 id 集合 vs lang ----------
w(u'--- 2. lang 键完整性 ---')
for loc in ('zh_cn', 'en_us', 'ja_jp', 'ru_ru'):
    fp = os.path.join(LANG, loc + '.json')
    if not os.path.exists(fp):
        w(u'[缺失] %s' % fp); continue
    j = json.load(io.open(fp, encoding='utf-8'))
    miss = []
    for name in [r[0] for r in rows]:
        for k in ('title', 'description'):
            key = u'advancements.potato_s_t.%s.%s' % (name, k)
            if key not in j:
                miss.append(key)
    extra = [k for k in j if k.startswith('advancements.potato_s_t.')
             and not any(k.startswith(u'advancements.potato_s_t.%s.' % n) for n in [r[0] for r in rows])]
    w(u'%s : 总键 %d，成就键 %d，缺失 %d，孤儿 %d' % (
        loc, len(j), len([k for k in j if k.startswith('advancements.potato_s_t.')]), len(miss), len(extra)))
    for k in miss:
        w(u'   [缺] ' + k)
    for k in extra:
        w(u'   [孤儿] ' + k)
w()

# ---------- 3. 星璨系列物品 ----------
w(u'--- 3. 星璨 / 钛 / 振金 系列物品是否已有成就 ---')
covered = set()
for r in rows:
    p = os.path.join(ADV, r[0] + '.json')
    d = json.load(io.open(p, encoding='utf-8'))
    for c in (d.get('criteria') or {}).values():
        for it in ((c.get('conditions') or {}).get('items') or []):
            ids = it.get('items')
            if isinstance(ids, str):
                ids = [ids]
            for i in ids:
                covered.add(i)
w(u'成就已覆盖的物品数：%d' % len(covered))

# 从 ModItems.java 抓注册名
moditems = io.open(os.path.join(ROOT, 'src', 'main', 'java', 'com', 'potatost', 'mod', 'ModItems.java'),
                   encoding='utf-8').read()
names = re.findall(r'registerItem\(\s*"([a-z0-9_]+)"', moditems)
if not names:
    names = re.findall(r'"([a-z0-9_]+)"\s*,\s*\(\)\s*->\s*new', moditems)
w(u'ModItems 里抓到的注册名 %d 个' % len(names))
fams = {}
for n in names:
    for fam in ('star_steel', 'titanium_alloy', 'vibranium', 'tungsten', 'aluminium', 'silver', 'steel'):
        if n == fam or n.startswith(fam):
            fams.setdefault(fam, []).append(n)
for fam in sorted(fams):
    w(u'[系列] %s' % fam)
    for n in sorted(fams[fam]):
        w(u'    %-42s %s' % (n, u'已有成就' if ('potato_s_t:' + n) in covered else u'—— 无成就'))
w()

io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
