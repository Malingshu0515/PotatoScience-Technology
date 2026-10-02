# -*- coding: utf-8 -*-
u"""_zf174_fix.py —— 修三处：createParticle 少一个参数（1.21.1 没有 RandomSource）/ VoidLens 的 import / 粒子类型注册锚点"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MOD = r"E:\PotatoST\src\main\java\com\potatost\mod"

# ① 三个粒子类：去掉 RandomSource 形参 + 那个 import；补 VoidLens 的 import
for cls in (u"VoidCoreParticle", u"VoidGlowParticle", u"VoidStreakParticle"):
    p = os.path.join(MOD, r"client\particle", cls + u".java")
    t = io.open(p, encoding="utf-8").read()
    t = t.replace(u"import net.minecraft.util.RandomSource;\n", u"")
    t = t.replace(u"                RandomSource random) {", u"                ) {")
    t = t.replace(u", double xd, double yd, double zd,\n                ) {",
                  u", double xd, double yd, double zd) {")
    if u"import com.potatost.mod.client.VoidLens;" not in t:
        t = t.replace(u"import net.minecraft.client.multiplayer.ClientLevel;",
                      u"import com.potatost.mod.client.VoidLens;\nimport net.minecraft.client.multiplayer.ClientLevel;")
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)
    print(u"  修 %s：RandomSource 形参 %s / VoidLens import %s"
          % (cls, u"已去掉" if u"RandomSource random" not in t else u"**还在**",
             u"已在" if u"import com.potatost.mod.client.VoidLens;" in t else u"**缺**"))

# ② 粒子类型注册：在含 register(modBus) 的第一行之后插
p = os.path.join(MOD, u"PotatoST.java")
t = io.open(p, encoding="utf-8").read()
if u"ModParticles.PARTICLES.register" in t:
    print(u"  粒子类型：已经注册过")
else:
    m = re.search(u"(?m)^(\\s*)([A-Za-z0-9_.]*register\\(modBus\\)[^\\n]*)$", t)
    if not m:
        print(u"  [!!] 还是找不到 modBus 锚点（下面列出所有 modBus 行）")
        for line in t.split(u"\n"):
            if u"modBus" in line:
                print(u"      " + line.strip()[:110])
    else:
        ind = m.group(1)
        ins = (u"\n" + ind + u"// 0.14 ZF174：本模组第一组自定义粒子（黑洞用）\n"
               + ind + u"ModParticles.PARTICLES.register(modBus);")
        t = t[:m.end(0)] + ins + t[m.end(0):]
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)
        print(u"  粒子类型：已插在「%s」之后" % m.group(2).strip()[:60])
sys.exit(0)
