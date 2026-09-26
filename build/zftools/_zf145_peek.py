# -*- coding: utf-8 -*-
u"""ZF145：逐字打印 _zf107_verify.py 的 45~80 行（核对 gatefix 的幂等判断）。只读。"""
import io
p = r'E:\PotatoST\build\zftools\_zf107_verify.py'
t = io.open(p, encoding='utf-8', newline='').read().split('\n')
for i, l in enumerate(t[44:80], 45):
    print(u'%4d|%s' % (i, l))
