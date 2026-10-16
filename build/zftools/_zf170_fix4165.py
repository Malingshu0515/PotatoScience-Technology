# -*- coding: utf-8 -*-
r"""_zf170_fix4165.py —— 给 §4.165 补记「第 2 次」（用**结构**定位，不用那句可能重复的散文）

上一跑用句子 `不许来自我手写的那张清单。` 当锚点，实测命中 **2 次** ⇒ 判据按 §4.17 拒绝动手。
改成结构定位：找到 `### 4.165 ` 这一节，插在**这一节结束之前**（下一个 `###`/`##` 标题前）。
"""
import io, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'E:\PotatoST\PotatoSTneoforge1.21.1'
ARCH = os.path.join(ROOT, 'docs', u'开发档案.md')
NOTE = (u"\n**第 2 次（0.13 ZF170）**：同一个循环我**又照抄了一遍** —— 四份改前件（三张在用贴图 + 一个方块模型）"
        u"没抄进 `zf170_pre`，三张贴图**当场被覆盖**。这次是**逐份断言**把它拦下来的（每条 `check` 都红了，"
        u"不像 ZF157 那次被 `check(True, …)` 蒙过去 —— 那一课记在这一节上面）。补法同前：git HEAD 取回 + "
        u"sha1 与 dry 实测逐位核对 + `build/resources/main` 里的旧副本交叉印证。\n\n"
        u"**规矩（加一条）**：写备份循环时，**先问「这份 rel 是相对谁的」**，再写 `os.path.join`；"
        u"清单里混着两套口径时，宁可用**两个列表**分开写，也别用一条 `if` 猜。\n")
fails = []
def check(ok, msg):
    print((u'  [OK]   ' if ok else u'  [FAIL] ') + msg)
    if not ok:
        fails.append(msg)

t = io.open(ARCH, encoding='utf-8').read()
if u'第 2 次（0.13 ZF170）' in t:
    print(u'  [幂等] §4.165 已经记过第 2 次')
else:
    lines = t.split(u'\n')
    i = None
    for k, l in enumerate(lines):
        if l.startswith(u'### 4.165 '):
            i = k
            break
    check(i is not None, u'找到 §4.165 标题行')
    if i is not None:
        j = None
        for k in range(i + 1, len(lines)):
            if lines[k].startswith(u'### ') or lines[k].startswith(u'## '):
                j = k
                break
        check(j is not None, u'找到这一节的结束边界（下一个标题）')
        if j is not None:
            # 插在结尾的最后一个非空行之后
            while j - 1 > i and lines[j - 1].strip() == u'':
                j -= 1
            t = u'\n'.join(lines[:j]) + NOTE + u'\n'.join(lines[j:])
            io.open(ARCH, 'w', encoding='utf-8', newline='\n').write(t)
            print(u'  [OK] 已插在第 %d 行（%s）之前' % (j + 1, lines[j][:28] if j < len(lines) else u'文末'))

t = io.open(ARCH, encoding='utf-8').read()
check(t.count(u'第 2 次（0.13 ZF170）') == 1, u'「第 2 次（0.13 ZF170）」恰好 1 处（实测 %d）' % t.count(u'第 2 次（0.13 ZF170）'))
check(t.count(u'### 4.165 ') == 1, u'§4.165 标题仍只有 1 个（实测 %d）' % t.count(u'### 4.165 '))
# 顺带把正文里那句重复散文数一下（只报数，不改别人的东西）
print(u'  说明：那句收尾散文在全文出现 %d 次（我原来的锚点挑得不好，改用结构定位）' % t.count(u'不许来自我手写的那张清单。'))
print(u'  档案现在 %d 字节' % len(t.encode()))
print(u'失败项 = %d' % len(fails))
sys.exit(1 if fails else 0)
