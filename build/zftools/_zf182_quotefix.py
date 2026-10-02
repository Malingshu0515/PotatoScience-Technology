# -*- coding: utf-8 -*-
u"""_zf182_quotefix.py —— 把 `_zf182_slam.py` 里**中文串中的 ASCII 双引号**换成「」（本工程的老纪律）。

规则（只动紧挨着汉字的引号，不碰代码里的真引号）：
  · 前一个字符是汉字 ⇒ `"` → `」`
  · 后一个字符是汉字 ⇒ `"` → `「`
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
    text = re.sub(u'(?<=[' + CJK + u'])"', u'\u300d', text)
    text = re.sub(u'"(?=[' + CJK + u'])', u'\u300c', text)
    n = sum(1 for a, b in zip(before, text) if a != b)
    print(u"替换掉 %d 个中文引号" % n)
    if write and text != before:
        io.open(P, "w", encoding="utf-8", newline=u"").write(text)
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
