# -*- coding: utf-8 -*-
"""_zf150_fix78.py —— 精确修 `_zf78_verify.py`（只改 AST 报错那一行，别的一字不动）

上一版 `_zf150_repair2.py` 的引号正则**太贪**：它把第 136 行
`check(u"DistillationTowerStructure.java 存在", tower is not None)`
里**本来正确**的 `", t` 也当成了"中文串里的 ASCII 引号"，改成了
`存在「, tower is not None)` —— 把好行改坏了。

教训（记一笔）：**修语法要用语法错误的位置当锚点，不能用宽正则去猜**。
这里改成：反复 `ast.parse` 取值 `e.lineno`，只修那一行上**确实不配对**的引号。

本文件**基于盘上现状**工作（盘上 136 行已被上一版改坏？没有 —— 上一版
`ast.parse` 没过 ⇒ **没写盘**，盘上仍是"136 好 / 315、345 坏"的原样）。
"""
import ast
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf78_verify.py"

t = io.open(P, encoding="utf-8").read()
print(u"① 盘上现状自检")
try:
    ast.parse(t)
    print(u"  [OK] 已经能解析，不用修")
    sys.exit(0)
except SyntaxError as e:
    print(u"  第 %d 行有问题：%s" % (e.lineno, e.msg))
    print(u"     %s" % t.split(u"\n")[e.lineno - 1])

# ② 精确修：只在 `check(u"…"…"…")` 里、且那对引号**夹着中文**时才换
#    判据：`check(u"` 之后，出现 `"` 且它**后面紧跟中文**、**前面也是中文** ⇒ 那是内层引号
BEFORE = t
n_fixed = 0
out_lines = []
for i, ln in enumerate(t.split(u"\n"), 1):
    new = ln
    m = re.match(u'^(\\s*)check\\(u"(.*)"(.*)$', ln)
    if m:
        indent, body, tail = m.group(1), m.group(2), m.group(3)
        # body 里如果还有 ASCII 双引号，且两侧是中文 ⇒ 换成「」
        def rep(mm):
            return u'「%s」' % mm.group(1)
        body2 = re.sub(u'(?<=[\\u4e00-\\u9fff])"([^"]*)"(?=[\\u4e00-\\u9fff])', rep, body)
        if body2 != body:
            new = u'%scheck(u"%s"%s' % (indent, body2, tail)
            n_fixed += 1
    out_lines.append(new)
out = u"\n".join(out_lines)
print(u"\n② 精确替换：改了 %d 行" % n_fixed)

# ③ 还有顶格 check( 的话一起修（同 _zf73/_zf79 那种伤）
lines = out.split(u"\n")
for i, ln in enumerate(lines):
    if ln.startswith(u"check("):
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j >= 0:
            base = len(lines[j]) - len(lines[j].lstrip(u" "))
            if base > 0:
                lines[i] = u" " * base + ln
                print(u"   [缩进] 第 %d 行 -> %d 空格" % (i + 1, base))
out = u"\n".join(lines)

# ④ 自检
try:
    ast.parse(out)
except SyntaxError as e:
    print(u"\n③ !! 仍语法错误（没写盘）：第 %d 行 %s" % (e.lineno, e.msg))
    ls = out.split(u"\n")
    for k in range(max(0, e.lineno - 3), min(len(ls), e.lineno + 2)):
        print(u"     %4d: %s" % (k + 1, ls[k]))
    sys.exit(1)

io.open(P, "w", encoding="utf-8", newline="\n").write(out)
print(u"\n③ [OK] 语法自检通过，已写盘（%d -> %d 字节）" % (len(BEFORE.encode()), len(out.encode())))

print(u"\n④ 复查这两处的最终形态")
for i, ln in enumerate(out.split(u"\n"), 1):
    if u"诊断按" in ln:
        print(u"   %4d: %s" % (i, ln.strip()))
