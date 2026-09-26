# -*- coding: utf-8 -*-
u"""ZF145：把 `_zf145_oldsha.txt` 里那 35 行 sha1 表插进 `_zf145_verify.py`（替换占位块）。
   一次成型，命中 1 次才写。只改这一处。
"""
import io, os, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ZT = r'E:\PotatoST\build\zftools'
VER = os.path.join(ZT, u'_zf145_verify.py')
OLD = u'OLD_SHA = {\n    "__PLACEHOLDER__": "0",\n}'
NEW = io.open(os.path.join(ZT, u'_zf145_oldsha.txt'), encoding='utf-8').read()

t = io.open(VER, encoding='utf-8', newline='').read()
# ⚠ 幂等判据不能拿表的第一行（`OLD_SHA = {` —— 占位块里也有这一行！），要用**某一条具体的哈希**
SENTINEL = u'"titanium": "17a1e52a51dfb098e082b8bf736ec86da9133f9f"'
if SENTINEL in t:
    print(u'[跳过] 表已经在里面了（幂等）')
    sys.exit(0)
if t.count(OLD) != 1:
    print(u'!! 占位块命中 %d 次（应为 1）' % t.count(OLD))
    sys.exit(1)
t = t.replace(OLD, NEW, 1)
io.open(VER, 'w', encoding='utf-8', newline='').write(t)
assert io.open(VER, encoding='utf-8', newline='').read() == t
print(u'已写入 %d 行 sha1 表' % NEW.count('\n'))
