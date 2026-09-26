# -*- coding: utf-8 -*-
u"""ZF145 侦察 2：全量物品 vs 成就覆盖 差集；并抓 Java 物品清单与套装定义。"""
import json, os, io, sys, glob, re

ROOT = r'E:\PotatoST'
ADV  = os.path.join(ROOT, 'src', 'main', 'resources', 'data', 'potato_s_t', 'advancement')
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon2.txt')

lines = []
def w(s=u''):
    lines.append(s)

w(u'===== ZF145 侦察 2：成就覆盖差集 =====')

covered = set()
for p in sorted(glob.glob(os.path.join(ADV, '*.json'))):
    d = json.load(io.open(p, encoding='utf-8'))
    for c in (d.get('criteria') or {}).values():
        cond = c.get('conditions') or {}
        for it in (cond.get('items') or []):
            ids = it.get('items')
            if isinstance(ids, str):
                ids = [ids]
            for i in ids:
                covered.add(i)

# ---- 抓所有注册名（ModItems / ModBlocks / ModArmorItems / ModVibraniumSet ...）----
names = set()
javadir = os.path.join(ROOT, 'src', 'main', 'java', 'com', 'potatost', 'mod')
for fp in glob.glob(os.path.join(javadir, '*.java')):
    src = io.open(fp, encoding='utf-8').read()
    for m in re.findall(r'ITEMS\.register\(\s*"([a-z0-9_]+)"', src):
        names.add(m)
    for m in re.findall(r'registerItem\(\s*"([a-z0-9_]+)"', src):
        names.add(m)

# ---- 用 lang 键反推物品（最权威的物品全集）----
lang = json.load(io.open(os.path.join(ROOT, 'src', 'main', 'resources', 'assets',
                                      'potato_s_t', 'lang', 'zh_cn.json'), encoding='utf-8'))
lang_items = sorted(k[len('item.potato_s_t.'):] for k in lang if k.startswith('item.potato_s_t.'))
w(u'lang 里 item.* 键：%d 个' % len(lang_items))

w()
w(u'--- 无成就覆盖的物品（按 lang item.* 全集）---')
no = [n for n in lang_items if ('potato_s_t:' + n) not in covered]
w(u'共 %d 个：' % len(no))
for n in no:
    w(u'    ' + n)

w()
w(u'--- 成就覆盖了但 lang 无 item.* 键的（可能是方块/标签/错字）---')
for i in sorted(covered):
    if i.startswith('potato_s_t:'):
        short = i[len('potato_s_t:'):]
        if short not in lang_items:
            w(u'    ' + i)
w()

# ---- 套装 / 系列定义 ----
w(u'--- ModArmorItems / ModVibraniumSet 概览 ---')
for fn in ('ModArmorItems.java', 'ModVibraniumSet.java', 'ModArmorSet.java', 'ModTiers.java'):
    fp = os.path.join(javadir, fn)
    if not os.path.exists(fp):
        continue
    src = io.open(fp, encoding='utf-8').read()
    ids = sorted(set(re.findall(r'"([a-z0-9_]+)"', src)))
    w(u'[%s] 字符串常量 %d 个: %s' % (fn, len(ids), u', '.join(ids[:60])))
w()

io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
