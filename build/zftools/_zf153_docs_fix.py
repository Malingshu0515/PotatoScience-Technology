# -*- coding: utf-8 -*-
u"""_zf153_docs_fix.py —— 档案里三处收尾修正（读-改-写**一次**写完，缩小与别人并发写的窗口）

① 台账行里的探针项数：我写的是"46 项"，报告里实际是 **54** 条 [OK]（写数字时报告还没落盘）；
② 台账行里的常驻校验项数："58 项" → 实际 **77 项**（写完文档、探针报告到位之后的真实数）；
③ §9 证据表那行要出现**逐字**的「587 键」—— `_zf145_verify.py` 的 H3 判据就是找这个串
   （我原来写的是「583 → 587」，没有"键"字，门当场红 —— 判据没错，是我的文案没跟上）。

跑法：python build\\zftools\\_zf153_docs_fix.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\docs\开发档案.md"

FIXES = [
    (u"**46 项 ALL OK**", u"**54 项 ALL OK**"),
    (u"常驻 `_zf153_verify.py` **58 项 0 失败**", u"常驻 `_zf153_verify.py` **77 项 0 失败**"),
    (u"| 语言 | 四语言 **583 → 587**、`lzh` 585 → **589**；",
     u"| 语言 | 四语言 **583 → 587 键**（587 键 × 4）、`lzh` 585 → **589 键**；"),
]

t = io.open(P, encoding="utf-8").read()
fails = []
for old, new in FIXES:
    n = t.count(old)
    if n == 1:
        t = t.replace(old, new)
        print(u"  [OK] %s → %s" % (old[:28], new[:28]))
    elif n == 0 and new in t:
        print(u"  [幂等] 已经是 %s" % new[:28])
    else:
        fails.append(u"锚点 %d 次：%s" % (n, old[:40]))
        print(u"  [!!] 锚点 %d 次：%s" % (n, old[:40]))
if not fails:
    io.open(P, "w", encoding="utf-8", newline=u"\n").write(t)
    print(u"  [OK] 写回（%d 字节）" % len(t.encode("utf-8")))
back = io.open(P, encoding="utf-8").read()
for _old, new in FIXES:
    print(u"  [%s] 回读：%s" % (u"OK" if new in back else u"!!", new[:30]))
print(u"失败项 = %d" % len(fails))
sys.exit(1 if fails else 0)
