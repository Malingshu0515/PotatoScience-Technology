# -*- coding: utf-8 -*-
u"""_zf85_unprobe.py —— 卸探针：删源文件 + 摘挂钩，并核对 PotatoST.java 与改前件逐字节相同"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
PROBE = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "FluidRegCheck.java")
MAIN = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "PotatoST.java")
REF = os.path.join(r"C:\PotatoST救援\zf82_pre", r"src\main\java\com\potatost\mod\PotatoST.java")

fails = []
if os.path.exists(PROBE):
    os.remove(PROBE)
    print(u"删掉探针源文件")
text = io.open(MAIN, encoding="utf-8").read()
hook = u"\n\n        FluidRegCheck.register();   // ← 临时探针（ZF85），跑完删"
if hook in text:
    text = text.replace(hook, u"")
    print(u"摘掉挂钩")
io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text)
after = io.open(MAIN, encoding="utf-8").read()
if u"FluidRegCheck" in after:
    fails.append(u"PotatoST.java 里还残留 FluidRegCheck")
if os.path.exists(REF):
    print(u"与 zf82_pre 基准逐字节相同：%s"
          % (u"是 ✓" if hashlib.sha1(open(MAIN, 'rb').read()).hexdigest()
             == hashlib.sha1(open(REF, 'rb').read()).hexdigest() else u"**否**（ZF82 之后它本来就改过能力登记，只作参考）"))
left = [f for dp, _, fs in os.walk(os.path.join(ROOT, "src", "main", "java"))
        for f in fs if f.endswith(".java") and "Check" in f]
if left:
    fails.append(u"源码树里还有探针：%s" % left)
print(u"源码树探针 %d 个" % len(left))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
