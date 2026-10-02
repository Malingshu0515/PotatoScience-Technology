# -*- coding: utf-8 -*-
u"""_zf162_peek.py —— 把还要跟平的几处断言原文打出来（只读，写进 _zf162_peek.txt）。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")
ZT = r"E:\PotatoST\build\zftools"
WANT = {
    u"_zf109_verify.py": [u"方块物品一共"],
    u"_zf128_verify.py": [u"PotatoST.java == 改前件"],
    u"_zf107_verify.py": [u"没有键被删掉"],
    u"_zf117_verify.py": [u"老节点"],
    u"_zf145_verify.py": [u"老节点"],
}
out = []
for name, keys in WANT.items():
    p = os.path.join(ZT, name)
    lines = io.open(p, encoding="utf-8").read().split(u"\n")
    out.append(u"===== " + name)
    for i, l in enumerate(lines):
        for k in keys:
            if k in l:
                lo = max(0, i - 6)
                for j in range(lo, min(len(lines), i + 3)):
                    out.append(u"%4d| %s" % (j + 1, lines[j]))
                out.append(u"")
io.open(os.path.join(ZT, u"_zf162_peek.txt"), "w", encoding="utf-8", newline=u"\n").write(
    u"\n".join(out) + u"\n")
print(u"已写 _zf162_peek.txt")
