# -*- coding: utf-8 -*-
"""_zf150_retarget4.py —— 手工收尾那 3 份**多行 check()** 的门

`_zf150_retarget3.py` 用"逐行正则"改，撞上跨行的 `check(...)` 时把缩进/结构弄坏了；
好在它写盘前有一道 `ast.parse` 自检，**那 3 份根本没写盘**（挡对了）。

这里改成**整段字符串替换**，一次换掉整个 check 调用（含跨行），再 `ast.parse` 自检。
"""
import ast
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = r"E:\PotatoST\build\zftools"
OLD, NEW = 579, 583
fails = []

PATCHES = [
    ("_zf73_verify.py",
     u'check(u"B11 四语言各 579 键（… + ZF109 采油机 10）", all(v == 579 for v in counts.values()), str(counts))',
     u'check(u"B11 四语言各 583 键（… + ZF109 采油机 10 + ZF150 四种粒 4）",\n'
     u'          all(v == 583 for v in counts.values()), str(counts))'),
    ("_zf78_verify.py",
     u'check(u"四份语言键数一致且 = 579（ZF107 +48；ZF109 +10）",\n'
     u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 579)',
     u'check(u"四份语言键数一致且 = 583（ZF107 +48；ZF109 +10；ZF150 四种粒 +4）",\n'
     u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 583)'),
    ("_zf79_verify.py",
     u'check(u"四份语言键数一致且 = 579（ZF107 +48；ZF109 +10）",\n'
     u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 579)',
     u'check(u"四份语言键数一致且 = 583（ZF107 +48；ZF109 +10；ZF150 四种粒 +4）",\n'
     u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 583)'),
]

for fn, old, new in PATCHES:
    p = os.path.join(TOOLS, fn)
    if not os.path.exists(p):
        fails.append(u"%s 不在" % fn)
        print(u"  !! %s 不在" % fn)
        continue
    t = io.open(p, encoding="utf-8").read()
    if new in t and old not in t:
        print(u"  [幂等] %s" % fn)
        continue
    n = t.count(old)
    if n != 1:
        fails.append(u"%s 锚点 %d 次" % (fn, n))
        print(u"  !! %s 锚点 %d 次（原样保留）" % (fn, n))
        continue
    out = t.replace(old, new)
    try:
        ast.parse(out)
    except SyntaxError as e:
        fails.append(u"%s 改后语法错误 %s" % (fn, e))
        print(u"  !! %s 改后语法错误，没写盘：%s" % (fn, e))
        continue
    io.open(p, "w", encoding="utf-8", newline="\n").write(out)
    print(u"  [OK] %s（整段替换 + 语法自检通过）" % fn)

# 全部 _zf*_verify 再扫一遍语法
print(u"\n== 全部 _zf*_verify.py 语法自检 ==")
bad = []
for f in sorted(os.listdir(TOOLS)):
    if not (f.startswith("_zf") and f.endswith("_verify.py")):
        continue
    try:
        ast.parse(io.open(os.path.join(TOOLS, f), encoding="utf-8").read())
    except SyntaxError as e:
        bad.append((f, e))
        print(u"  !! %s : %s" % (f, e))
if not bad:
    print(u"  [OK] 全部能解析")

print(u"\n失败项 = %d" % (len(fails) + len(bad)))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if (fails or bad) else 0)
