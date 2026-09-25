# -*- coding: utf-8 -*-
u"""_zf85_callsites.py —— liquidType 去掉 temperature 形参后，4 个调用点也要跟着改"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = r"E:\PotatoST\src\main\java\com\potatost\mod\ModFluids.java"
CALLS = [(u"diesel", u"830", u"1200"), (u"naphtha", u"700", u"700"),
         (u"gasoline", u"750", u"600"), (u"lpg", u"500", u"400")]
fails = []

t = io.open(P, encoding="utf-8").read()
n = 0
for name, density, viscosity in CALLS:
    old = u'liquidType("%s", %s, %s, 300)' % (name, density, viscosity)
    new = u'liquidType("%s", %s, %s)' % (name, density, viscosity)
    hit = t.count(old)
    if hit != 1:
        fails.append(u"%s：锚点命中 %d 次" % (name, hit))
        continue
    t = t.replace(old, new, 1)
    n += 1
    print(u"  [OK]   %s 调用点去掉 300" % name)
io.open(P, "w", encoding="utf-8", newline=u"\n").write(t)
print(u"改了 %d 个调用点，失败项 = %d" % (n, len(fails)))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
