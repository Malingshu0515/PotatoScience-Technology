# -*- coding: utf-8 -*-
u"""ZF145：列出所有常驻门里含 492 的**每一行**（分类用）。只读。"""
import glob, io, os, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
ZT = r'E:\PotatoST\build\zftools'
out = []
for p in sorted(glob.glob(os.path.join(ZT, u'_zf*_verify.py'))):
    name = os.path.basename(p)
    if name in (u'_zf142_verify.py', u'_zf143_verify.py'):
        continue
    for i, line in enumerate(io.open(p, encoding='utf-8').read().split('\n'), 1):
        if u'492' in line:
            out.append(u'%-22s %4d | %s' % (name, i, line.strip()[:150]))
io.open(os.path.join(ZT, u'_zf145_lines492.txt'), 'w', encoding='utf-8').write(u'\n'.join(out))
print(u'%d 行 -> _zf145_lines492.txt' % len(out))
