# -*- coding: utf-8 -*-
u"""_zf81_unprobe.py —— 卸探针：删源文件 + 摘挂钩，并核对 PotatoST.java 与改前件逐字节相同"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
PROBE = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "ElectrolyzerCheck.java")
MAIN = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "PotatoST.java")
BK = r"C:\PotatoST救援\zf81_pre\src\main\java\com\potatost\mod\PotatoST.java"

fails = []

if os.path.exists(PROBE):
    os.remove(PROBE)
    print(u"删掉探针源文件")
text = io.open(MAIN, encoding="utf-8").read()
hook = u"\n\n        ElectrolyzerCheck.register();   // ← 临时探针（ZF81），跑完删"
if hook in text:
    text = text.replace(hook, u"")
    print(u"摘掉挂钩")
io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text)

after = io.open(MAIN, encoding="utf-8").read()
if u"ElectrolyzerCheck" in after:
    fails.append(u"PotatoST.java 里还残留 ElectrolyzerCheck")
if os.path.exists(BK):
    if hashlib.sha1(open(MAIN, "rb").read()).hexdigest() != hashlib.sha1(open(BK, "rb").read()).hexdigest():
        fails.append(u"PotatoST.java 与改前件不同 ⇒ 挂钩没摘干净")
    else:
        print(u"PotatoST.java 与改前件逐字节相同 ✓")
left = [f for dp, _, fs in os.walk(os.path.join(ROOT, "src", "main", "java"))
        for f in fs if f.endswith(".java") and "Check" in f]
if left:
    fails.append(u"源码树里还有探针：%s" % left)
print(u"源码树探针 %d 个" % len(left))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
