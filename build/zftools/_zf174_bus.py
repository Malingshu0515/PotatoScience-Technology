# -*- coding: utf-8 -*-
u"""_zf174_bus.py —— 找准 PotatoST 里的 mod 事件总线名，把粒子类型注册挂上去"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\PotatoST.java"
t = io.open(P, encoding="utf-8").read()

print(u"== 文件里所有与总线/注册有关的行 ==")
for i, line in enumerate(t.split(u"\n"), 1):
    s = line.strip()
    if (u"IEventBus" in s or u"Bus" in s or u".register(" in s) and not s.startswith(u"//"):
        print(u"  L%-5d %s" % (i, s[:118]))

if u"ModParticles.PARTICLES.register" in t:
    print(u"  [幂等] 已经注册过")
    sys.exit(0)

# 构造器参数里那个 IEventBus 名
m = re.search(u"IEventBus\\s+(\\w+)", t)
name = m.group(1) if m else u"modBus"
print(u"== 判定总线名：%s ==" % name)

# 找一个"ModXxx.register(<总线>)" 形状的行（各个 DeferredRegister 都是这么挂的）
pat = re.compile(u"(?m)^(\\s*)([A-Za-z0-9_]+\\.[A-Za-z0-9_]*register\\(" + re.escape(name) + u"\\)[^\\n]*)$")
m2 = pat.search(t)
if not m2:
    pat = re.compile(u"(?m)^(\\s*)([^\\n]*\\b" + re.escape(name) + u"\\b[^\\n]*register[^\\n]*)$")
    m2 = pat.search(t)
if not m2:
    print(u"  [!!] 还是没找到锚点（请看上面的行清单）")
    sys.exit(1)
ind = m2.group(1)
ins = (u"\n" + ind + u"// 0.14 ZF174：本模组第一组自定义粒子（黑洞用）—— 挂到 mod 总线上\n"
       + ind + u"ModParticles.PARTICLES.register(" + name + u");")
t = t[:m2.end(0)] + ins + t[m2.end(0):]
io.open(P, "w", encoding="utf-8", newline=u"\n").write(t)
print(u"  已插在「%s」之后" % m2.group(2).strip()[:70])
sys.exit(0)
