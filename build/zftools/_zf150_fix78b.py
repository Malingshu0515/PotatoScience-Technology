# -*- coding: utf-8 -*-
"""_zf150_fix78b.py —— 补最后漏掉的一处：`_zf78_verify.py` 的 513-514 还是 579

前面几版都因为锚点被我用过一次而没打上（幂等判断把它跳过了）。这里按**行号区间**
精确定位那两行、原地替换，再 `ast.parse` 自检。
"""
import ast
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\build\zftools\_zf78_verify.py"

t = io.open(P, encoding="utf-8").read()
lines = t.split(u"\n")

OLD_A = u'check(u"四份语言键数一致且 = 579（ZF107 +48；ZF109 +10）",'
NEW_A = u'check(u"四份语言键数一致且 = 583（ZF107 +48；ZF109 +10；ZF150 四种粒 +4）",'
OLD_B = u'len(set(counts.values())) == 1 and list(counts.values())[0] == 579)'
NEW_B = u'          len(set(counts.values())) == 1 and list(counts.values())[0] == 583)'

n = 0
for i, ln in enumerate(lines):
    if ln.strip() == OLD_A:
        lines[i] = u"    " + NEW_A
        n += 1
        print(u"  [改] 第 %d 行（标签）" % (i + 1))
    elif ln.strip() == OLD_B:
        lines[i] = NEW_B
        n += 1
        print(u"  [改] 第 %d 行（断言）" % (i + 1))

if n == 0:
    print(u"  [幂等] 没找到要改的行")
    sys.exit(0)

out = u"\n".join(lines)
try:
    ast.parse(out)
except SyntaxError as e:
    print(u"  !! 改后语法错误，没写盘：%s" % e)
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="\n").write(out)
print(u"  [OK] 改了 %d 处 + 语法自检通过" % n)
