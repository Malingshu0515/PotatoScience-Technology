# -*- coding: utf-8 -*-
u"""ZF145 侦察 9：探针要用的三个 API 取证（sources.jar）。
  ① ServerAdvancementManager 的读取入口（getAllAdvancements / getTree / get）
  ② PLAYER_KILLED_ENTITY.trigger 的调用点（真击杀到底走不走它）
  ③ Player.advancements 的用法（getOrStartProgress / award）
只读。
"""
import io, os, re, sys, zipfile, glob

ROOT = r'E:\PotatoST'
OUT  = os.path.join(ROOT, 'build', 'zftools', '_zf145_recon9.txt')
SRC  = glob.glob(os.path.join(ROOT, 'build', 'neoForm', '*', 'sources.jar'))[0]
zf = zipfile.ZipFile(SRC)
names = zf.namelist()
lines = []
def w(s=u''):
    lines.append(s)

w(u'===== ZF145 侦察 9 =====')
w()
w(u'--- ① ServerAdvancementManager ---')
hit = [n for n in names if n.endswith('server/ServerAdvancementManager.java')]
w(u'%s' % hit)
if hit:
    src = zf.read(hit[0]).decode('utf-8', 'replace').splitlines()
    for i, l in enumerate(src):
        if re.search(r'public |getAllAdvancements|getTree|AdvancementHolder get\(', l):
            w(u'  %4d| %s' % (i + 1, l.strip()[:120]))
w()

w(u'--- ② PLAYER_KILLED_ENTITY.trigger 的调用点 ---')
for n in names:
    if not n.endswith('.java'):
        continue
    s = zf.read(n).decode('utf-8', 'replace')
    if 'PLAYER_KILLED_ENTITY.trigger' in s:
        for i, l in enumerate(s.splitlines(), 1):
            if 'PLAYER_KILLED_ENTITY.trigger' in l:
                w(u'  %s:%d  %s' % (n, i, l.strip()[:140]))
w()
w(u'--- ②b INVENTORY_CHANGED.trigger 的调用点 ---')
for n in names:
    if not n.endswith('.java'):
        continue
    s = zf.read(n).decode('utf-8', 'replace')
    if 'INVENTORY_CHANGED.trigger' in s:
        for i, l in enumerate(s.splitlines(), 1):
            if 'INVENTORY_CHANGED.trigger' in l:
                w(u'  %s:%d  %s' % (n, i, l.strip()[:140]))
w()
w(u'--- ③ PlayerAdvancements 的公开入口 ---')
hit = [n for n in names if n.endswith('advancements/PlayerAdvancements.java')]
if hit:
    src = zf.read(hit[0]).decode('utf-8', 'replace').splitlines()
    for i, l in enumerate(src, 1):
        if re.search(r'^\s*public ', l):
            w(u'  %4d| %s' % (i, l.strip()[:120]))
w()
w(u'--- ④ LivingEntity.die 末尾（击杀归属） ---')
hit = [n for n in names if n.endswith('world/entity/LivingEntity.java')]
if hit:
    src = zf.read(hit[0]).decode('utf-8', 'replace').splitlines()
    start = None
    for i, l in enumerate(src):
        if re.search(r'public void die\(DamageSource', l):
            start = i
            break
    if start is not None:
        for i in range(start, min(len(src), start + 90)):
            if re.search(r'kill|Kill|killer|award|BROADCAST|dropAllDeathLoot', src[i]):
                w(u'  %4d| %s' % (i + 1, src[i].strip()[:130]))
w()
io.open(OUT, 'w', encoding='utf-8').write(u'\n'.join(lines))
sys.stdout.write(u'OK -> %s\n' % OUT)
