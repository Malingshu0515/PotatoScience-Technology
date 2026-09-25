# -*- coding: utf-8 -*-
u"""_zf101_unprobe.py —— 卸探针：删源文件 + 摘挂钩，并核对 PotatoST.java **只增不删**

本轮 PotatoST.java 本来就该改（多登记了酸性反应室的三条能力）⇒ 不能要求"逐字节相同"，
改成两条更贴题的断言：① 一行都不许删；② 新增的行里不许夹着探针挂钩。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
PROBE = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "Zf101Check.java")
MAIN = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "PotatoST.java")
BK = r"C:\PotatoST救援\zf101_pre\src\main\java\com\potatost\mod\PotatoST.java"

fails = []

if os.path.exists(PROBE):
    os.remove(PROBE)
    print(u"删掉探针源文件 Zf101Check.java")
else:
    print(u"（探针源文件已不在）")

text = io.open(MAIN, encoding="utf-8").read()
hook = u"\n\n        Zf101Check.register();   // ← 临时探针（ZF101），跑完删"
if hook in text:
    io.open(MAIN, "w", encoding="utf-8", newline=u"").write(text.replace(hook, u"", 1))
    print(u"摘掉挂钩")
elif u"Zf101Check" not in text:
    print(u"（挂钩已不在 = 之前摘过了）")
else:
    fails.append(u"PotatoST.java 里找不到挂钩锚点")

after = io.open(MAIN, encoding="utf-8").read()
if u"Zf101Check" in after:
    fails.append(u"PotatoST.java 里还残留 Zf101Check")

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
    if [l for l in added if u"Zf101Check" in l]:
        fails.append(u"新增行里还夹着探针挂钩")
    if not added:
        fails.append(u"PotatoST.java 与改前件没有差异 ⇒ 那三条能力登记是不是没加上？")
else:
    fails.append(u"找不到改前件 %s" % BK)

left = [f for dp, _, fs in os.walk(os.path.join(ROOT, "src", "main", "java"))
        for f in fs if f.endswith(".java") and "Check" in f]
print(u"源码树里剩下的探针 %d 个" % len(left))
if left:
    fails.append(u"源码树里还有探针：%s" % left)

print(u"失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
