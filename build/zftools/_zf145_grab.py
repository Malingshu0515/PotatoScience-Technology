# -*- coding: utf-8 -*-
u"""ZF145：抓四处要跟平的片段的**逐字**原文（供 gatefix 的 C 段用）。只读。"""
import hashlib, io, os, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
ROOT = r'E:\PotatoST'
ZT = os.path.join(ROOT, 'build', 'zftools')
ADIR = os.path.join(ROOT, r'src\main\resources\data\potato_s_t\advancement')

print(u'new_beginning.json sha1 = %s'
      % hashlib.sha1(open(os.path.join(ADIR, 'new_beginning.json'), 'rb').read()).hexdigest())
print(u'damage_type 目录: %s'
      % [n for n in os.listdir(os.path.join(ROOT, r'src\main\resources\data\potato_s_t\damage_type'))])
print(u'')

def show(fn, pat, ctx=0):
    p = os.path.join(ZT, fn)
    lines = io.open(p, encoding='utf-8', newline='').read().split('\n')
    print(u'===== %s /%s/ =====' % (fn, pat))
    for i, l in enumerate(lines):
        if pat in l:
            for k in range(i - ctx, i + ctx + 1):
                print(u'%4d|%s' % (k + 1, lines[k]))
    print(u'')

show(u'_zf117_verify.py', u'"new_beginning": "', 2)
show(u'_zf117_verify.py', u'新增的成就键正好', 0)
show(u'_zf139_verify.py', u'本轮只加这一个', 3)
show(u'_zf139_verify.py', u'ks[i + 1] == TOOLTIP_KEY', 4)
show(u'_zf139_verify.py', u'DEATH_KEY =', 0)
show(u'_zf139_verify.py', u'TOOLTIP_KEY =', 0)
