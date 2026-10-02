# -*- coding: utf-8 -*-
"""_zf133_docs2.py —— ZF133 档案落笔（修正上一版两个字符串里的 ASCII 双引号）

⚠ 上一版 `_zf133_docs.py` 在 ROW 与 SECTION 里用了 ASCII `"` 包中文短语，
   把 Python 字符串提前截断 ⇒ 语法错。**本工程一律用「」**（§4 那几条老坑之一）。
   这次把三个片段都放进独立文件读，避免再和引号纠缠。

跑法：python build\\zftools\\_zf133_docs2.py            # 只看
      python build\\zftools\\_zf133_docs2.py --write     # 落笔
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = r"E:\PotatoST\docs\开发档案.md"
T = r"E:\PotatoST\build\zftools"
WRITE = "--write" in sys.argv

ROW_FILE = os.path.join(T, "_zf133_row.txt")
SEC_FILE = os.path.join(T, "_zf133_section.md")
R4_FILE = os.path.join(T, "_zf133_pitfall.md")

ROW_ANCHOR = "| ZF132 |"
SEC_ANCHOR = "## 10. 备份策略"
R4_ANCHOR = "### 4.112"


def main():
    s = io.open(DOC, encoding="utf-8").read()
    before = len(s)

    parts = {}
    for name, path in (("台账行", ROW_FILE), ("§9 段", SEC_FILE), ("§4 段", R4_FILE)):
        assert os.path.isfile(path), "缺文件：%s" % path
        parts[name] = io.open(path, encoding="utf-8").read()

    for name, anchor in (("台账行", ROW_ANCHOR), ("§9 段", SEC_ANCHOR), ("§4 段", R4_ANCHOR)):
        n = s.count(anchor)
        print("锚点 %-6s 出现 %d 次" % (name, n))
        assert n == 1, "锚点 %s 不唯一" % name

    if not WRITE:
        print("（只看模式；要落笔加 --write）")
        return

    # ① 台账行：插在 ZF132 那一行之后
    i = s.index(ROW_ANCHOR)
    line_end = s.index("\n", i) + 1
    s = s[:line_end] + parts["台账行"].rstrip("\n") + "\n" + s[line_end:]

    # ② §9 段：插在 "## 10. 备份策略" 之前
    j = s.index(SEC_ANCHOR)
    s = s[:j] + parts["§9 段"].strip("\n") + "\n\n" + s[j:]

    # ③ §4 五条：插在 "### 4.112" 之前
    k = s.index(R4_ANCHOR)
    s = s[:k] + parts["§4 段"].strip("\n") + "\n\n" + s[k:]

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(s)
    print("已落笔：%d -> %d 字符（+%d）" % (before, len(s), len(s) - before))

    body = io.open(DOC, encoding="utf-8").read()
    for key in ("ZF133", "4.113", "4.117", "星璨钢斧", "zf133_pre"):
        print("  复核 %-10s 出现 %d 次" % (key, body.count(key)))


main()
