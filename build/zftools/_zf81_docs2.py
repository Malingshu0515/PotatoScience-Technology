# -*- coding: utf-8 -*-
u"""_zf81_docs2.py —— ZF81 第二份文档：§4.53 工具坑（PowerShell 字符串手术 + 假绿日志）

§5 的 ZF81 行已经写好（`_zf81_docs.py`），这里只补"雷"那一条，并在 §9 里加一行提示。
插入点都断言"恰好命中 1 次"（ToolLint 硬规矩）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOCS = r"E:\PotatoST\docs"
DOC = os.path.join(DOCS, u"开发档案.md")
fails = []

TRAP = u"""
### 4.53 【工具雷】用 PowerShell 字符串替换去"生成脚本"⇒ 门少跑了一半，日志却全绿（0.11 ZF81）

本轮生成 `_zf81_gates.ps1` 时图省事，拿 ZF80 那份做了两次 `.Replace()` + `Set-Content`。
后果两条，都很隐蔽：

| 看到的现象 | 真实情况 |
|---|---|
| 日志里 `结论: 通过`、`失败项 = 0` 一大堆 | **ToolLint / RecipeCheck / JsonCheck / ZF75 / ZF78 / ZF80 verify 与 falsify 根本没跑** —— 那 6 个 `Run-` 行被并进了上一行的注释里（PowerShell 往返把长行折了行） |
| 脚本注释读起来是中文 | 内容其实是"UTF-8 当 GBK 再存成 UTF-8"的**乱码**（`Get-Content` 默认按 ANSI 读） |

**规矩**：
1. **脚本/配置这类要长期存在的文件，一律用文件工具整份写**，不许"读进来 — 字符串替换 — 写回去"。
   一次性改文案的脚本可以这么做（而且要断言锚点命中次数），但**脚本本身**不行。
2. **"没有 FAIL"不等于"跑过了"**。门跑完必须核对**段数**：新写 `_zf81_gatecount.py`
   从 `.ps1` 里抠出所有 `Run-* '<段名>'`，再去日志里找 `==== <段名> ====`；
   缺一段就 FAIL（本轮先手工跑，下一轮起写进门脚本最后一步）。
3. 同类推广：任何"生成的文件"都要有一条**自证**——本轮门脚本的教训是
   `Run` 行数（34）与日志段数（34 + 门结束）对不上就是坏的。
"""

NOTE = u"""
- [ ] **门日志完整性**：`_zf81_gates.ps1` 里有 34 个 `Run-` 段，日志里必须出现 34 段 + 门结束
      （核对脚本 `_zf81_gatecount.py`；这条是 §4.53 那个坑留下的保险）
"""


def main():
    text = io.open(DOC, encoding="utf-8").read()

    if u"### 4.53" not in text:
        anchor = u"\n\n| 版本 | 内容 |"
        if text.count(anchor) != 1:
            fails.append(u"§4.53 插入点命中 %d 次（必须 1 次）" % text.count(anchor))
        else:
            text = text.replace(anchor, u"\n" + TRAP + anchor, 1)

    if u"### ZF81（0.11）电解器 1000 FE/t" in text and u"_zf81_gatecount.py" not in text:
        anchor = u"### ZF81（0.11）电解器 1000 FE/t —— 待你实测"
        if text.count(anchor) != 1:
            fails.append(u"§9 ZF81 段锚点命中 %d 次（必须 1 次）" % text.count(anchor))
        else:
            text = text.replace(anchor, anchor + u"\n" + NOTE, 1)

    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"档案 §4.53 + §9 提示写完，失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
