# -*- coding: utf-8 -*-
u"""_zf109_docs_fix.py —— 把 §4.79/§4.80 挪回 §4 的尾巴，并补一条 §4.81

**为什么要挪**：`_zf109_docs.py` 把 §4.79/§4.80 插在「`### 6.1` 之前」，
但这份档案里 `## 6.` 的标题**就在 §6.1 上一行** ⇒ 两条雷被塞进了 §6 里面（章号错了）。
正确的位置是 §4 的末尾：本轮表头 `| 版本 | 内容 |` 之前。

**顺带补 §4.81**：本轮真抓到一个**假绿**校验器 —— `_zf70_verify.py` 在 UTF-8 控制台里
跑是"检查项 = 91 / 失败项 = 0"，但被 gatesnap 用**管道**调起来时，打印 `⇒`（U+21D2）
按 GBK 编码直接 `UnicodeEncodeError` 崩掉、退出码 1、**一行汇总都没打**（已修）。

⚠ 动手前先把当前这份抄到改前件里（`zf109_pre\\_doc_before_move.md`）。
"""
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"
BK = r"C:\PotatoST救援\zf109_pre\_doc_before_move.md"

HEAD_479 = u"### 4.79 【实现雷】"
HEAD_480 = u"### 4.80 【方法论】"
HEAD_61 = u"### 6.1 加一个**音乐唱片**"
ANCHOR_TABLE = u"| 版本 | 内容 |"

SEC481 = u"""
### 4.81 【方法论】常驻校验在"管道里"崩掉 = **假绿**（0.11 ZF109）

`_zf70_verify.py` 在 UTF-8 控制台里手跑是「检查项 = 91 / 失败项 = 0」，一切正常。
但 `_zf109_gatesnap.py` 是用 `subprocess` + **管道**去调它的，那一刻 Python 的 stdout
按**平台默认编码（GBK）**走 ⇒ 它打印 `⇒`（U+21D2）时直接
`UnicodeEncodeError: 'gbk' codec can't encode character`，**中途崩掉**、退出码 1、
连汇总行都没来得及打。快照上看到的红是"没有汇总行"，很容易被误读成"这份门的格式怪"。

**两条规矩**：

1. **每一份常驻校验都必须自己把 stdout 钉成 UTF-8**（本工程别的脚本都有这段，
   `_zf70_verify.py` 是漏的那一份，已补）：
   ```python
   try:
       sys.stdout.reconfigure(encoding="utf-8", errors="replace")
   except Exception:
       pass
   ```
2. **"在我这儿是绿的"不算数** —— 交付前必须用**跟快照同一条路**（管道/子进程）再跑一遍。
   本轮还顺手让 `_zf109_gatesnap.py` 认得老一代的汇总格式（`检查项 = N   失败项 = M`），
   免得汇总行整条丢掉、只剩一句"没有汇总行"。
"""

fails = []


def main():
    text = io.open(DOC, encoding="utf-8", newline="").read()
    if u"\r" in text:
        fails.append(u"档案里有 CR")
    lines = text.split(u"\n")

    # ① 先抄一份当前状态
    os.makedirs(os.path.dirname(BK), exist_ok=True)
    shutil.copy2(DOC, BK)
    print(u"① 移动前的档案已抄到 %s" % BK)

    # ② 定位 §4.79 那一坨
    starts = [i for i, l in enumerate(lines) if l.startswith(HEAD_479)]
    ends = [i for i, l in enumerate(lines) if l.startswith(HEAD_61)]
    if len(starts) != 1 or len(ends) != 1:
        fails.append(u"定位失败：§4.79 命中 %d 次、§6.1 命中 %d 次" % (len(starts), len(ends)))
        print(u"失败项 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    s, e = starts[0], ends[0]
    block = lines[s:e]
    if not any(l.startswith(HEAD_480) for l in block):
        fails.append(u"切出来的块里没有 §4.80")
    if sum(1 for l in block if l.startswith(u"### ")) != 2:
        fails.append(u"切出来的块里有 %d 个 ###（应为 2：4.79 + 4.80）"
                     % sum(1 for l in block if l.startswith(u"### ")))
    print(u"② 切出 %d 行（§4.79 起、§6.1 前）" % len(block))

    # ③ 去掉尾部空行，补上 §4.81
    while block and block[-1].strip() == u"":
        block.pop()
    block.append(SEC481.rstrip(u"\n"))
    block.append(u"")
    print(u"③ 补上 §4.81（假绿那条），现在 %d 行" % len(block))

    # ④ 从原位置删掉，插到本轮表头之前
    rest = lines[:s] + lines[e:]
    anchors = [i for i, l in enumerate(rest) if l.strip() == ANCHOR_TABLE]
    if len(anchors) != 1:
        fails.append(u"表头锚点命中 %d 次" % len(anchors))
        print(u"失败项 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    out_lines = rest[:anchors[0]] + block + rest[anchors[0]:]
    out = u"\n".join(out_lines)

    # ⑤ 核对
    for h in (HEAD_479, HEAD_480, u"### 4.81 【方法论】"):
        if out.count(h) != 1:
            fails.append(u"核对：%s 出现 %d 次" % (h, out.count(h)))
    for i, l in enumerate(out.split(u"\n")):
        if l.startswith(HEAD_479):
            # §4.79 必须在表头之前、且 `## 6.` 还在它后面
            pass
    idx_479 = out.index(HEAD_479)
    idx_tab = out.index(ANCHOR_TABLE)
    idx_6 = out.index(u"\n## 6. ")
    if not (idx_479 < idx_tab < idx_6):
        fails.append(u"顺序不对：§4.79@%d 表头@%d ##6@%d" % (idx_479, idx_tab, idx_6))
    if fails:
        print(u"失败项 = %d（**没落盘**）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(out)
    print(u"④ 落盘：§4.79 < 表头 < `## 6.` ⇒ %s" % u"顺序正确")
    print(u"   行数 %d → %d" % (len(lines), len(out.split(u"\n"))))
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
