# -*- coding: utf-8 -*-
u"""_zf112_mkgatesnap.py —— 从 _zf111_gatesnap.py 派生本轮的全门快照脚本（只改两处）"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
SRC = os.path.join(ZT, "_zf111_gatesnap.py")
DST = os.path.join(ZT, "_zf112_gatesnap.py")

t = io.open(SRC, encoding="utf-8").read()
old = u'"_zf109_verify.py", "_zf111_verify.py"]'
new = u'"_zf109_verify.py", "_zf111_verify.py", "_zf112_verify.py"]'
if t.count(old) != 1:
    print(u"NAMES 锚点命中 %d 次 —— 不改" % t.count(old))
    sys.exit(1)
t = t.replace(old, new)
t = t.replace(u"全门快照（ZF111）", u"全门快照（ZF112）")
if u"_zf112_verify.py" not in t:
    print(u"名字没插进去")
    sys.exit(1)
io.open(DST, "w", encoding="utf-8", newline=u"\n").write(t)
print(u"写好 %s（%d 行）" % (DST, len(t.split(u"\n"))))
sys.exit(0)
