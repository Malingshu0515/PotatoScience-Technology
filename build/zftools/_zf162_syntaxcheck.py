# -*- coding: utf-8 -*-
u"""_zf162_syntaxcheck.py —— 跟平之后逐份 `ast.parse` 自检（§4：门坏了要说出来，不能静默）。

跑法：python build\\zftools\\_zf162_syntaxcheck.py
"""
import ast
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"
RET = os.path.join(ZT, u"_zf162_retarget.py")
GATE = os.path.join(ZT, u"_zf162_gatesnap.py")


def names_from(p):
    t = io.open(p, encoding="utf-8").read()
    out = set(re.findall(u'u"(_zf[0-9a-z_]+\\.py)"', t))
    out |= set(re.findall(u'u"(_zf[0-9a-z_]+\\.ps1)"', t))
    return out


files = sorted(names_from(RET) | names_from(GATE))
bad = []
for f in files:
    p = os.path.join(ZT, f)
    if not os.path.isfile(p):
        continue
    try:
        ast.parse(io.open(p, encoding="utf-8").read())
    except SyntaxError as e:
        bad.append(u"%s: 第 %s 行 %s" % (f, e.lineno, e.msg))
print(u"语法自检：%d 份门（%d 份在盘上），语法错 %d 份" % (len(files), len([f for f in files if os.path.isfile(os.path.join(ZT, f))]), len(bad)))
for b in bad:
    print(u"  !! " + b)
sys.exit(1 if bad else 0)
