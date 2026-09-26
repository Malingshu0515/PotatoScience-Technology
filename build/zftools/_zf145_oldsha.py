# -*- coding: utf-8 -*-
u"""ZF145：把**盘上现有的 43 条进度**里"不是本轮新建的那 35 条"的 sha1 打出来，
   直接贴进 `_zf145_verify.py` 的 OLD_SHA 表（口径同 `_zf117_verify.py`）。
   只读。"""
import hashlib, io, os, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
ADIR = r'E:\PotatoST\src\main\resources\data\potato_s_t\advancement'
NEW = {"vibranium", "vibranium_armor", "titanium_armor", "star_steel_tools",
       "star_steel_slash", "star_chart_tome", "diesel_generator", "silver_wire"}
rows = []
for f in sorted(os.listdir(ADIR)):
    if not f.endswith('.json'):
        continue
    n = f[:-5]
    if n in NEW:
        continue
    h = hashlib.sha1(open(os.path.join(ADIR, f), 'rb').read()).hexdigest()
    rows.append((n, h))
out = [u'OLD_SHA = {']
for n, h in rows:
    out.append(u'    "%s": "%s",' % (n, h))
out.append(u'}')
out.append(u'# 合计 %d 份（43 - 本轮新建的 8）' % len(rows))
txt = u'\n'.join(out)
io.open(r'E:\PotatoST\build\zftools\_zf145_oldsha.txt', 'w', encoding='utf-8').write(txt)
print(txt)
