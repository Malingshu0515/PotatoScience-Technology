# -*- coding: utf-8 -*-
u"""_zf128_docs3.py —— 记第三条真事：**交接文档 §6 的错位**（ZF127 提交里就带进去了）

`_zf127_docs.py` / `_zf128_docs.py` 都用 `insert_after_line(..., u"18. **ZF126 的账**", ...)`
往交接文档里插新条目 —— 而那里每一条都是**跨多行的整段**，按**首行**匹配 ⇒
新条目被插进了**上一条的正文中间**（盘上顺序一度是 17 → 18头 → 19头 → 20 → 19尾 → 18尾）。

本轮已用 `_zf128_handfix.py` 重排修好（18/19/20 各自连续、顺序正确），这里补：
  ① 档案 §4.112：这条雷（**多行条目的"插在某条之后"必须按整条结束位置算**）；
  ② 档案 §9：ZF128 小节里补一句"顺手修好了交接文档 §6 的错位"；
  ③ 交接 §6 第 20 条补 ⑦。

跑法：
    python build\\zftools\\_zf128_docs3.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOCS = r"E:\PotatoST\docs"
ARC = os.path.join(DOCS, u"开发档案.md")
HAND = os.path.join(DOCS, u"多会话协作交接.md")
notes, fails = [], []

LESSON = u'''### 4.112 【文档雷】"插在某条之后"不能按**首行**匹配 —— 我把交接文档的三条插串了（0.11 ZF128）

交接文档 §6 里每一条都是**跨多行的整段**（第一条行号只是段首）。`_zf127_docs.py` / `_zf128_docs.py`
都用 `insert_after_line(name, path, u"18. **ZF126 的账**", block)` 这种写法 ⇒
它找到的是**段首那一行**，于是新条目被插进了**上一条的正文中间**。盘上一度是：

```
17 → 18(段首) → 19(段首) → 20(整段) → 19(剩下) → 18(剩下)
```

而且 ZF127 那次**已经提交**（`68aaa43`）⇒ 文档坏了整整一轮才被本轮的自查发现
（ZF128 想给第 20 条补一段时，锚点匹配 0 次 —— 才发现第 19/20 条根本不在自己该在的地方）。

**规矩**：
- 往"多行整段"的文档里插内容，锚点必须落在**整条的结束**（下一条的段首 / 空行 / 文件尾），
  不能落在这条自己的段首；
- 插入型脚本**自己要有自检**：插完断言"新条目在旧条目之后、且旧条目仍然连续"
  （本轮 `_zf128_handfix.py` 就是这么验的）；
- 更一般的：**凡是"按行首匹配"的补丁，先问一句"这一行是不是某段的第一行"**。

'''

ADD = (u"\n\n**另外**：给第 20 条补素材线那段时，锚点匹配 0 次 ⇒ 才发现交接文档 §6 的顺序是坏的：\n\n"
       u"```\n17 → 18(段首) → 19(段首) → 20(整段) → 19(剩下) → 18(剩下)\n```\n\n"
       u"原因是 ZF127/ZF128 的文档脚本都用「插在 `18. **ZF126 的账**` 这一行之后」这种**按段首匹配**的写法，"
       u"而这些条目都是跨多行的整段 —— ZF127 那次**已经提交**，坏了整整一轮。\n"
       u"本轮用 `_zf128_handfix.py` 按行区间重排（18/19/20 各自连续、顺序正确，并自检过），"
       u"并记成 §4.112。\n")

ADD20 = (u"\n    ⑦ ⚠ **顺手修好一处上一轮带进来的文档伤**：交接文档 §6 第 18/19/20 条一度是"
         u"「18头 → 19头 → 20 → 19尾 → 18尾」（按**段首**匹配插入的后果，ZF127 那次已提交）⇒ "
         u"本轮用 `_zf128_handfix.py` 重排并自检，记成 §4.112。\n")


def main():
    t = io.open(ARC, encoding="utf-8", newline=u"").read()
    anchor = u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）"
    if u"### 4.112" in t:
        notes.append(u"§4.112 已经写过（幂等跳过）")
    elif t.count(anchor) == 1:
        io.open(ARC, "w", encoding="utf-8", newline=u"").write(t.replace(anchor, LESSON + anchor, 1))
        notes.append(u"档案 §4 新增 4.112")
    else:
        fails.append(u"§4 锚点命中 %d 次" % t.count(anchor))

    t = io.open(ARC, encoding="utf-8", newline=u"").read()
    anchor = u"| 文档 | —— | §4.111 记两条雷；交接 §6 第 20 条补记这一段 |"
    if u"**另外**：给第 20 条补素材线那段时" in t:
        notes.append(u"§9 那段已经写过（幂等跳过）")
    elif t.count(anchor) == 1:
        io.open(ARC, "w", encoding="utf-8", newline=u"").write(
            t.replace(anchor, anchor + ADD, 1))
        notes.append(u"档案 §9 第五节：补上「顺手修好文档错位」那一段")
    else:
        fails.append(u"§9 锚点命中 %d 次" % t.count(anchor))

    t = io.open(HAND, encoding="utf-8", newline=u"").read()
    mark = u"见 §4.111 与 §9 第五节。"
    if u"⑦ ⚠ **顺手修好一处上一轮带进来的文档伤**" in t:
        notes.append(u"交接第 20 条 ⑦ 已经写过（幂等跳过）")
    elif t.count(mark) == 1:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(
            t.replace(mark, mark + ADD20.rstrip(u"\n"), 1))
        notes.append(u"交接 §6 第 20 条：补 ⑦（文档错位已修）")
    else:
        fails.append(u"交接第 20 条锚点命中 %d 次" % t.count(mark))

    print(u"\n".join(u"  [OK] " + x for x in notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
