# -*- coding: utf-8 -*-
"""_zf133_cleanup2.py —— 按**标记**清诊断（不靠"我记得插了什么"，靠现在盘上有什么）

前两个清理脚本都因为"我记的文本"和"盘上的文本"对不上而中途失败（§4.90 那条老坑：
凭记忆写锚点）。这次反过来：先扫描标记，把带标记的**整块**打出来，按行首/行尾配对删。

标记：`A133DBG`（所有诊断打印都带它）、`DEBUG`（临时开关）、`trace`（临时字符串）。
产品代码里这三样**一个都不该有**；探针里 `[DBG]` 前缀的打印也不该有。

跑法：python build\\zftools\\_zf133_cleanup2.py          # 只看
      python build\\zftools\\_zf133_cleanup2.py --write  # 删
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FILES = [
    r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java",
    r"E:\PotatoST\src\main\java\com\potatost\mod\StarSteelAxeItem.java",
    r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java",
]

MARKERS = ("A133DBG", "DEBUG", "trace", "[DBG]")
WRITE = "--write" in sys.argv


def main():
    for path in FILES:
        lines = io.open(path, encoding="utf-8").read().split("\n")
        hits = [i for i, l in enumerate(lines) if any(m in l for m in MARKERS)]
        if not hits:
            print("=== %s：干净 ===" % path.split("\\")[-1])
            continue
        print("=== %s：命中 %d 行 ===" % (path.split("\\")[-1], len(hits)))
        for i in hits:
            print("  %4d| %s" % (i + 1, lines[i][:150]))
    if not WRITE:
        print("\n（只看模式；要删加 --write）")


main()
