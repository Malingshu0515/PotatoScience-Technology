# -*- coding: utf-8 -*-
u"""ZF145 侦察 10：PlayerAdvancements 的公开方法 + ServerPlayer.getAdvancements。只读。"""
import io, os, re, sys, zipfile, glob
ROOT = r'E:\PotatoST'
SRC  = glob.glob(os.path.join(ROOT, 'build', 'neoForm', '*', 'sources.jar'))[0]
zf = zipfile.ZipFile(SRC)
names = zf.namelist()
hit = [n for n in names if n.endswith('PlayerAdvancements.java')]
print(u'文件: %s' % hit)
if hit:
    for i, l in enumerate(zf.read(hit[0]).decode('utf-8', 'replace').splitlines(), 1):
        if re.search(r'\bpublic\b', l):
            print(u'%4d| %s' % (i, l.strip()[:130]))
print(u'')
hit = [n for n in names if n.endswith('server/level/ServerPlayer.java')]
for i, l in enumerate(zf.read(hit[0]).decode('utf-8', 'replace').splitlines(), 1):
    if 'getAdvancements' in l or 'killedEntity' in l:
        print(u'ServerPlayer %4d| %s' % (i, l.strip()[:130]))
