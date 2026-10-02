# -*- coding: utf-8 -*-
"""_zf150_fixquote.py —— 修 `_zf78_verify.py` 里**中文串内用 ASCII 双引号**的伤（两处）

`check(u"诊断按"错格数最少"挑，…")` —— 那对 ASCII 双引号把字符串截断了，
后面全成了语法垃圾。按本工程 §4.24 族的规矩换成**中文引号「」**。

同文件第 285 行本来就是「」（对的），376 行也是 —— 只有 315 / 345 两处是坏的。
改完全量 `ast.parse` 自检。
"""
import ast
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"E:\PotatoST\build\zftools\_zf78_verify.py"
OLD = u'check(u"诊断按"错格数最少"挑，并报第一处不符的格子",'
NEW = u'check(u"诊断按「错格数最少」挑，并报第一处不符的格子",'

t = io.open(P, encoding="utf-8").read()
n = t.count(OLD)
print(u"  坏锚点出现 %d 次" % n)
if n == 0:
    if NEW in t:
        print(u"  [幂等] 已经修过")
    else:
        print(u"  !! 一处都没找到，人工看")
        sys.exit(1)
else:
    out = t.replace(OLD, NEW)
    try:
        ast.parse(out)
    except SyntaxError as e:
        print(u"  !! 改完仍语法错误，没写盘：%s" % e)
        # 把出错那几行打出来，方便人工
        lines = out.split(u"\n")
        for i in range(max(0, e.lineno - 4), min(len(lines), e.lineno + 2)):
            print(u"     %4d: %s" % (i + 1, lines[i]))
        sys.exit(1)
    io.open(P, "w", encoding="utf-8", newline="\n").write(out)
    print(u"  [OK] 修了 %d 处 + 语法自检通过" % n)

print(u"\n== 全部 _zf*_verify.py 语法自检 ==")
T = os.path.dirname(P)
bad, total = [], 0
for f in sorted(os.listdir(T)):
    if not (f.startswith("_zf") and f.endswith("_verify.py")):
        continue
    total += 1
    try:
        ast.parse(io.open(os.path.join(T, f), encoding="utf-8").read())
    except SyntaxError as e:
        bad.append((f, str(e)))
print(u"  共 %d 份；有问题 %d 份" % (total, len(bad)))
for f, e in bad:
    print(u"   !! %s : %s" % (f, e))
sys.exit(1 if bad else 0)
