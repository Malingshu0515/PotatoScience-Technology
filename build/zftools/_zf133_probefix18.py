# -*- coding: utf-8 -*-
"""_zf133_probefix18.py —— 时间线撞车：`T_B_CHECK` 与 `T_D` 都是 120

现象：`checkD` 跑了（它的断言在报告里）但 `buildD` 没跑（报告里没有「③ (d)」那行）
⇒ `wallLog` 是 null ⇒ tick 里 NPE ⇒ 整场在 t=150 崩掉（后面 9 个场景一个没跑）。

根因：我把 `T_B_CHECK` 从 60 改成 120 时，没注意 `T_D` 本来就是 120 ——
`if (t == T_B_CHECK) ... else if (t == T_D)` 里前者先命中，后者永远轮不到。

⚠ 这条要记进档案：**时间线常量必须两两不同**（同值就等于后面的整段被静默跳过，
而且症状是"后面的场景全没跑"，很容易看成一堆无关的失败）。

修法：`T_D` = 130、`T_D_CHECK` = 160（都错开）。

跑法：python build\\zftools\\_zf133_probefix18.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

PAIRS = [
    ("    private static final int T_D = 120;          // ③ 石头墙",
     "    private static final int T_D = 130;          // ③ 石头墙（⚠ 不能与 T_B_CHECK 同值）"),
    ("    private static final int T_D_CHECK = 150;",
     "    private static final int T_D_CHECK = 160;"),
]

s = io.open(CHK, encoding="utf-8").read()
for a, b in PAIRS:
    n = s.count(a)
    assert n == 1, "锚点 %d：%r" % (n, a[:50])
    s = s.replace(a, b, 1)
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] T_D 130 / T_D_CHECK 160")

# 复核：把所有 T_xxx 常量列出来，检查有没有重复值
import re
vals = {}
for m in re.finditer(r"int (T_[A-Z_]+) = (\d+);", s):
    name, v = m.group(1), int(m.group(2))
    vals.setdefault(v, []).append(name)
print("--- 时间线现值 ---")
for v in sorted(vals):
    flag = "  ⚠ 撞车" if len(vals[v]) > 1 else ""
    print("  %4d : %s%s" % (v, ", ".join(vals[v]), flag))
dups = {v: n for v, n in vals.items() if len(n) > 1}
print("撞车组数 =", len(dups))
sys.exit(1 if dups else 0)
