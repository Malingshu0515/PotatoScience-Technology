# -*- coding: utf-8 -*-
u"""_zf113_mkgatesnap.py —— 从 _zf112_gatesnap.py 派生本轮的全门快照脚本（只改两处）"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
t = io.open(os.path.join(ZT, "_zf112_gatesnap.py"), encoding="utf-8").read()
old = u'"_zf111_verify.py", "_zf112_verify.py"]'
new = u'"_zf111_verify.py", "_zf112_verify.py", "_zf113_verify.py"]'
if t.count(old) != 1:
    print(u"锚点命中 %d 次" % t.count(old))
    sys.exit(1)
t = t.replace(old, new).replace(u"全门快照（ZF112）", u"全门快照（ZF113）")
io.open(os.path.join(ZT, "_zf113_gatesnap.py"), "w", encoding="utf-8",
        newline=u"\n").write(t)
print(u"写好 _zf113_gatesnap.py")
sys.exit(0)
