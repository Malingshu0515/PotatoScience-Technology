# -*- coding: utf-8 -*-
u"""ZF145 侦察 6：DamageSourcePredicate 字段 + 原版成就里 killing_blow 的实例。只读。"""
import io, os, re, sys, zipfile, glob, json

ROOT = r'E:\PotatoST'
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon6.txt')
SRC  = glob.glob(os.path.join(ROOT, 'build', 'neoForm', '*', 'sources.jar'))
lines = []
def w(s=u''):
    lines.append(s)

w(u'===== ZF145 侦察 6 =====')
zf = zipfile.ZipFile(SRC[0])
names = zf.namelist()

w(u'##### DamageSourcePredicate.java #####')
hit = [n for n in names if re.search(r'advancements/critereon/DamageSourcePredicate\.java$', n)]
w(u'命中: %s' % hit)
if hit:
    for i, l in enumerate(zf.read(hit[0]).decode('utf-8', 'replace').splitlines()[:60]):
        w(u'  %4d| %s' % (i + 1, l))
w()

w(u'##### 原版成就里出现 killing_blow 的实例 #####')
# client.jar 里有官方数据包
cli = glob.glob(os.path.join(ROOT, 'build', 'neoForm', '*', 'client.jar')) or \
      glob.glob(os.path.join(ROOT, '.gradle', '**', 'client.jar'), recursive=True)
w(u'client.jar 候选: %s' % cli[:3])
found = 0
if cli:
    zc = zipfile.ZipFile(cli[0])
    advs = [n for n in zc.namelist() if n.startswith('data/minecraft/advancement/') and n.endswith('.json')]
    w(u'原版成就 %d 份' % len(advs))
    for n in advs:
        txt = zc.read(n).decode('utf-8', 'replace')
        if 'killing_blow' in txt:
            found += 1
            w(u'--- %s ---' % n)
            w(txt[:1400])
            w()
    w(u'含 killing_blow 的原版成就数 = %d' % found)
    # 顺带看一份带 damage_type 标签的谓词写法
    w(u'##### 原版成就里 tags/damage_type 引用 #####')
    for n in advs:
        txt = zc.read(n).decode('utf-8', 'replace')
        if 'damage_type' in txt and 'killing_blow' not in txt:
            w(u'--- %s ---' % n)
            w(txt[:900]); w()

io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
