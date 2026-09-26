# -*- coding: utf-8 -*-
r"""_rzh_showlang.py —— 把指定语言里**含某个词**的键值列出来（只读）。

用途：改完 ja/ru 的矿名后，把每一处实际结果拉出来肉眼过一遍 —— 尤其是俄语的
形容词变格，正则替换最容易在这儿悄悄产出一个"语法通顺但拼错"的词。

用法：`python build/zftools/_rzh_showlang.py <语言> <词1> [词2] ...`
结论写 `_rzh_showlang.txt`（UTF-8，不用 shell 重定向）。
"""
from __future__ import print_function
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_showlang.txt")


def main():
    if len(sys.argv) < 3:
        print(u"用法: python _rzh_showlang.py <语言> <词1> [词2] ...")
        print(u"      python _rzh_showlang.py <语言> --re <正则>")
        return 1
    loc = sys.argv[1]
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        d = json.load(f)

    if sys.argv[2] == u"--re":
        import re
        rx = re.compile(sys.argv[3])
        lines = [u"语言 %s；正则 %s" % (loc, sys.argv[3]), u""]
        for k in sorted(d):
            ms = sorted(set(rx.findall(d[k])))
            if ms:
                lines.append(u"   %-30s %s" % (u", ".join(ms), k))
        text = u"\n".join(lines)
    else:
        needles = sys.argv[2:]
        lines = [u"语言 %s；查 %s" % (loc, u" / ".join(needles)), u""]
        for k in sorted(d):
            v = d[k]
            if any(n in v for n in needles):
                lines.append(u"---- %s" % k)
                for seg in v.split(u"\n"):
                    lines.append(u"     %s" % seg)
        text = u"\n".join(lines)
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(text + u"\n")
    print(u"wrote %s (%d 字节)" % (OUT, os.path.getsize(OUT)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
