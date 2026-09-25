# -*- coding: utf-8 -*-
u"""_zf88_gatefix.py —— 把 ZF88 的校验脚本挂进门脚本（上一步的字符串替换没命中，Run 行数没加）"""
import io
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\build\zftools\_zf88_gates.ps1"
fails = []

t = io.open(P, encoding="utf-8").read()
anchor = u"Run-Py  'ZF86 verify'      '_zf86_verify.py'  $null\n"
add = (u"# ZF87/ZF88：油桶贴图 + 四张素材 + 原油/柴油流体贴图（都是「用户放图 ⇒ 转档 ⇒ 指向自己」）\n"
       u"Run-Py  'ZF88 verify'      '_zf88_verify.py'  $null\n")
if u"'_zf88_verify.py'" in t:
    print(u"  [OK]   已经挂过 ZF88 verify（跳过）")
elif t.count(anchor) != 1:
    fails.append(u"锚点命中 %d 次" % t.count(anchor))
else:
    t = t.replace(anchor, anchor + add, 1)
    io.open(P, "w", encoding="utf-8", newline=u"\n").write(t)
    print(u"  [OK]   ZF88 verify 已挂进门脚本")

n = len(re.findall(r"(?m)^Run-(?:Ps1|Py)\s+'", t))
print(u"现在 Run 行数 = %d（应为 41）" % n)
if n != 41:
    fails.append(u"Run 行数 %d ≠ 41" % n)
print(u"失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
