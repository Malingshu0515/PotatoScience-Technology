# -*- coding: utf-8 -*-
"""_zf133_finalize.py —— 收尾：把探针时间线按实测校正 + 撤掉挂在 PotatoST 上的钩子

## ① `T_I_ALIVE = 520` 是错的（实测：波在 t≈507 就已经自己散了）
波有 64 格射程上限、1 格/tick，而 (i) 那一场在 **t=450** 出手 ⇒ 它最晚活到 t≈450+64=514。
（实测那条断言报的是 `拆到木头之后 57 tick` ⇒ 探针已经把 T_I_ALIVE 调到 507 过，
57 tick 这个数就是这么来的。）正确的"还活着"检查点必须落在 **拆到木头之后 ~60 tick 以内、
且仍在 64 格射程内** ⇒ 取 **t=490**（出手后 40 tick、拆到木头约在 t=453 ⇒ 之后 37 tick）。

⚠ 这条断言本身的**语义**没问题（"滚动窗口会重置计时"），坏的是采样时刻。
   与其把窗口放宽到"射程够不到"，不如把检查点挪进射程 —— 这才是真的在验那条规则。

## ② 卸钩子：`PotatoST.java` 里那行 `Zf133Check.register();` 必须删干净（§4.7）
探针源文件先留档到 `build/zftools/check/Zf133Check.java`（本工程惯例：探针留档、源码删掉）。

跑法：python build\\zftools\\_zf133_finalize.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
CHK = ROOT + r"\src\main\java\com\potatost\mod\Zf133Check.java"
MAIN = ROOT + r"\src\main\java\com\potatost\mod\PotatoST.java"

# ---- ① 时间线 ----
s = io.open(CHK, encoding="utf-8").read()
pairs = [
    ("    private static final int T_I_ALIVE = 507;",
     "    private static final int T_I_ALIVE = 490;   // 出手后 40 tick（射程 64 内）"),
    ("    private static final int T_I_ALIVE = 520;",
     "    private static final int T_I_ALIVE = 490;   // 出手后 40 tick（射程 64 内）"),
]
done = False
for a, b in pairs:
    if s.count(a) == 1:
        s = s.replace(a, b, 1)
        print("[OK] T_I_ALIVE -> 490（原锚点：%s）" % a.strip()[-20:])
        done = True
        break
if not done:
    import re
    m = re.search(r"int T_I_ALIVE = (\d+);", s)
    assert m, "找不到 T_I_ALIVE"
    s = s.replace(m.group(0), "int T_I_ALIVE = 490;   // 出手后 40 tick（射程 64 内）", 1)
    print("[OK] T_I_ALIVE 由 %s 改成 490（按正则找到）" % m.group(1))
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)

# ---- ② 卸钩子 ----
t = io.open(MAIN, encoding="utf-8").read()
import re
before = len(t)
t2 = re.sub(r"\n[ \t]*// ⚠⚠ 临时探针（ZF133）[^\n]*\n[ \t]*Zf133Check\.register\(\);\n", "\n", t)
if t2 == t:
    t2 = re.sub(r"\n[ \t]*Zf133Check\.register\(\);[^\n]*\n", "\n", t)
print("[OK] 钩子已删" if len(t2) < before else "[WARN] 没找到钩子文本（可能已被删）")
io.open(MAIN, "w", encoding="utf-8", newline="\n").write(t2)
left = "Zf133Check" in io.open(MAIN, encoding="utf-8").read()
print("PotatoST 里残留 Zf133Check =", left)
