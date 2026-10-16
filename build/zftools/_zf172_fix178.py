# -*- coding: utf-8 -*-
r"""_zf172_fix178.py —— 修 §4.178：插进去的是字面量 `### 4.%d`（忘了套 `% nxt`）

顺手把 `_zf172_docs.py` 里那个漏掉的格式化补上，免得下次重跑又插一个 `%d` 进去。
"""
import io, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
ARCH = os.path.join(ROOT, 'docs', u'开发档案.md')
SCR = os.path.join(ROOT, 'build', 'zftools', '_zf172_docs.py')
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

t = io.open(ARCH, encoding='utf-8').read()
OLD = u'### 4.%d 【命名雷】'
NEW = u'### 4.178 【命名雷】'
n = t.count(OLD)
print(u'  档案里那个字面量标题（### 4.<百分号>d 【命名雷】）命中 %d 次' % n)
if u'### 4.178 ' in t:
    print(u'  [幂等] 已经是 4.178')
elif n == 1:
    io.open(ARCH, 'w', encoding='utf-8', newline='\n').write(t.replace(OLD, NEW))
    print(u'  [OK] 已替换为 `### 4.178 【命名雷】`')
else:
    check(False, u'锚点命中 %d 次，不动手' % n)
t = io.open(ARCH, encoding='utf-8').read()
check(t.count(u'### 4.178 ') == 1, u'§4.178 标题恰好 1 个（实测 %d）' % t.count(u'### 4.178 '))
check(u'### 4.%d ' not in t, u'字面量 `### 4.%d` 已绝迹')
nums = [int(m.group(1)) for m in re.finditer(u'^### 4\\.(\\d+)', t, re.M)]
check(nums.count(178) == 1, u'4.178 在编号序列里（现最大 4.%d）' % max(nums))
check(u'| ZF172 |' in t and u'⚠ ZF172 更正' in t, u'ZF172 变更行与两处更正都还在')

print()
print(u'===== 修脚本里漏掉的格式化 =====')
s = io.open(SCR, encoding='utf-8').read()
A = u'别只算改名。\\n")'
B = u'别只算改名。\\n") % nxt'
if B in s:
    print(u'  [幂等] 脚本已修')
else:
    check(s.count(A) == 1, u'脚本锚点命中 1 次（实测 %d）' % s.count(A))
    if s.count(A) == 1:
        io.open(SCR, 'w', encoding='utf-8', newline='\n').write(s.replace(A, B))
        import ast
        ast.parse(io.open(SCR, encoding='utf-8').read())
        print(u'  [OK] `_zf172_docs.py` 的 PIT 现在会套 `% nxt`（改后过 ast.parse）')

print()
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
