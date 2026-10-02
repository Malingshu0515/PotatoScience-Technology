# -*- coding: utf-8 -*-
u"""_zf182_quotefix2.py —— 修回上一步**误伤**的引号。

`_zf182_quotefix.py` 的规则"后一个字符是汉字 ⇒ `"` → `「`"太粗：它把 **Python 字面量的开引号**
（`u"被动…`）也换成了 `u「被动…`，直接语法错。本脚本只做一件事：
**凡是 `「` 前面不是汉字/中文标点的，一律改回 ASCII 双引号**（那必然是误伤的字面量开引号）。
"""
import io
import re
import sys

P = r"E:\PotatoST\build\zftools\_zf182_slam.py"
CJK = u"\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"


def main(argv):
    write = u"--write" in argv
    text = io.open(P, encoding="utf-8", newline=u"").read()
    before = text
    text = re.sub(u'(?<![' + CJK + u'])\u300c', u'"', text)
    n = sum(1 for a, b in zip(before, text) if a != b)
    print(u"修回 %d 个误伤的开引号" % n)
    if write and text != before:
        io.open(P, "w", encoding="utf-8", newline=u"").write(text)
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
