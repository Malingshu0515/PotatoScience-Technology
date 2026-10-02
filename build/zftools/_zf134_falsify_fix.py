# -*- coding: utf-8 -*-
"""_zf134_falsify_fix.py —— K-A1 的锚点对不上（少了一个空格级差异）

拿盘上真实那一行来定位，然后把锚点改成逐字一致（又是"凭记忆写锚点"，第 N 次）。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"
FAL = r"E:\PotatoST\build\zftools\_zf134_falsify_angle.py"

s = io.open(SHOCK, encoding="utf-8").read()
i = s.find("double lat = lateral - HALF_WIDTH;")
line = s[s.rfind("\n", 0, i) + 1: s.find("\n", i)]
print("盘上那一行: %r" % line)

f = io.open(FAL, encoding="utf-8").read()
old = '"                double lat = lateral - HALF_WIDTH;      // -3 .. +2（偶数宽的对称铺法）"'
new = '"%s"' % line.replace("\\", "\\\\").replace('"', '\\"')
n = f.count(old)
print("脚本里的锚点出现 %d 次" % n)
assert n >= 1
f = f.replace(old, new)
io.open(FAL, "w", encoding="utf-8", newline="\n").write(f)
print("[OK] K-A1 锚点已改成逐字一致")
