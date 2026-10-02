# -*- coding: utf-8 -*-
"""_zf150_fix78c.py —— 补 `_zf78_verify.py` 的 `section_c()` 里缺的 `tower` 赋值

## 症状

`python _zf78_verify.py` 跑到 `section_c()` 第 284 行崩：
    UnboundLocalError: cannot access local variable 'tower'
因为它第 284 行用了 `tower`，而 `tower = read_src(...)` 在**同一个函数的 373 行**才出现
⇒ Python 把 `tower` 判成局部变量，284 行时还没绑定。

## 这是**预存**的伤，不是我造成的

`_zf150_retarget*.py` 系列**只替换含 579 的行**；284 行里没有 579。
`_zf150_repair*.py` 只动"顶格的 check("与中文串里的引号；`tower =` 不匹配任一条。
`ast.parse` 也查不出它 —— **语法合法、运行才炸**（这正是"编译绿 ≠ 能跑"那一族）。

## 修法

在 `section_c()` 里、**第一次用到 `tower` 之前**补一行 `tower = read_src(...)`
（与 373 行同一份来源，语义不变）。补完立刻**真跑一遍**这道门确认不崩。
"""
import ast
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf78_verify.py"

t = io.open(P, encoding="utf-8").read()
if u'    tower = read_src("DistillationTowerStructure.java")\n' in t.split(u"\n")[206:290].__str__():
    print(u"  [幂等] section_c 里已经有 tower 赋值")
    sys.exit(0)

# 锚点：section_c 的定义 + 它开头那两行（唯一）
anchor = (u'def section_c():\n'
          u'    print(u"\\n== C 分馏塔操作器（数值 / 每 tick / 停机）==")\n'
          u'    op = read_src("DistillationOperatorBlockEntity.java")\n')
add = u'    tower = read_src("DistillationTowerStructure.java")\n'

if t.count(anchor) != 1:
    print(u"  !! 锚点出现 %d 次，没写盘" % t.count(anchor))
    sys.exit(1)

out = t.replace(anchor, anchor + add, 1)
try:
    ast.parse(out)
except SyntaxError as e:
    print(u"  !! 改后语法错误，没写盘：%s" % e)
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="\n").write(out)
print(u"  [OK] 已在 section_c 开头补 tower 赋值（第 210 行附近）+ 语法自检通过")

print(u"\n== 真跑一遍这道门 ==")
r = subprocess.run([sys.executable, P], capture_output=True, cwd=os.path.dirname(P))
out_txt = r.stdout.decode("utf-8", "replace")
err = r.stderr.decode("utf-8", "replace")
tail = [l for l in out_txt.splitlines() if l.strip()][-6:]
for l in tail:
    print(u"  " + l)
if u"Traceback" in err:
    print(u"  !! 仍在崩：")
    for l in err.splitlines()[-6:]:
        print(u"     " + l)
    sys.exit(1)
print(u"\n  [OK] 跑完了，没有 Traceback")
