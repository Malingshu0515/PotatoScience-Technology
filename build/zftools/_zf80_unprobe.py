# -*- coding: utf-8 -*-
u"""_zf80_unprobe.py —— 卸探针：删源文件 + 摘掉 PotatoST 里的挂钩（§9 规矩）"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
PROBE = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "FillingOilCheck.java")
MAIN = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "PotatoST.java")

fails = []

if os.path.exists(PROBE):
    os.remove(PROBE)
    print(u"删掉探针源文件")
else:
    print(u"探针源文件本来就不在（已删过）")

text = io.open(MAIN, encoding="utf-8").read()
hook = u"\n\n        FillingOilCheck.register();   // ← 临时探针（ZF80），跑完删"
if hook in text:
    text = text.replace(hook, u"")
    print(u"摘掉 PotatoST 里的挂钩")
else:
    print(u"挂钩已经不在（或写法变了）")
io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text)

after = io.open(MAIN, encoding="utf-8").read()
if u"FillingOilCheck" in after:
    fails.append(u"PotatoST.java 里还残留 FillingOilCheck")
left = [os.path.join(dp, f)
        for dp, _, fs in os.walk(os.path.join(ROOT, "src", "main", "java"))
        for f in fs if f.endswith(".java") and "Check" in f]
if left:
    fails.append(u"源码树里还有探针：%s" % left)
print(u"残留检查：源码树探针 %d 个 / 挂钩 %s"
      % (len(left), u"在" if u"FillingOilCheck" in after else u"无"))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
