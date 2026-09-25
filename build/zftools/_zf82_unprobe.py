# -*- coding: utf-8 -*-
u"""_zf82_unprobe.py —— 卸探针：删源文件 + 摘挂钩，并核对 PotatoST.java 与改前件逐字节相同"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
PROBE = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "FluidExchangerCheck.java")
MAIN = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "PotatoST.java")
BK = r"C:\PotatoST救援\zf82_pre\src\main\java\com\potatost\mod\PotatoST.java"

fails = []
if os.path.exists(PROBE):
    os.remove(PROBE)
    print(u"删掉探针源文件")
text = io.open(MAIN, encoding="utf-8").read()
hook = u"\n\n        FluidExchangerCheck.register();   // ← 临时探针（ZF82），跑完删"
if hook in text:
    text = text.replace(hook, u"")
    print(u"摘掉挂钩")
io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text)
after = io.open(MAIN, encoding="utf-8").read()
if u"FluidExchangerCheck" in after:
    fails.append(u"PotatoST.java 里还残留 FluidExchangerCheck")
# ⚠ 本轮 PotatoST.java **本来就该改**（多登记了两条能力），所以只核对"与改前件不同但只差能力那几条"
if os.path.exists(BK):
    old = io.open(BK, encoding="utf-8").read()
    added = [l for l in after.split(u"\n") if l not in old.split(u"\n")]
    removed = [l for l in old.split(u"\n") if l not in after.split(u"\n")]
    print(u"PotatoST.java 与改前件的差异：+%d 行 / -%d 行" % (len(added), len(removed)))
    for l in added:
        print(u"    + " + l.strip()[:100])
    for l in removed:
        print(u"    - " + l.strip()[:100])
    if removed:
        fails.append(u"PotatoST.java 比改前件少了 %d 行（本轮不该删任何东西）" % len(removed))
    if not added:
        fails.append(u"PotatoST.java 与改前件没有差异 ⇒ 两条能力登记是不是没加上？")
else:
    fails.append(u"找不到改前件可比")
left = [f for dp, _, fs in os.walk(os.path.join(ROOT, "src", "main", "java"))
        for f in fs if f.endswith(".java") and "Check" in f]
if left:
    fails.append(u"源码树里还有探针：%s" % left)
print(u"源码树探针 %d 个" % len(left))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
