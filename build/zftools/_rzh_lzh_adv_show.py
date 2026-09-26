# -*- coding: utf-8 -*-
r"""_rzh_lzh_adv_show.py —— 把 lzh 的成就文案拉出来，与 zh_cn 并排（只读）。

用途：改了 zh_cn 的成就说明之后，文言文那一份也得跟上（它是独立的一套文字）。
先看清楚**哪些条还停在旧译法**，再动手。

输出 `_rzh_lzh_adv_show.txt`。
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_lzh_adv_show.txt")


def main():
    zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))
    lz = json.load(io.open(os.path.join(LANGDIR, u"lzh.json"), encoding=u"utf-8"))
    ids = sorted(set(re.match(u"advancements\\.potato_s_t\\.([a-z0-9_]+)\\.",
                              k).group(1)
                     for k in zh if k.startswith(u"advancements.")))
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    L = []
    for i in ids:
        if only and i not in only:
            continue
        k = u"advancements.potato_s_t.%s" % i
        L.append(u"---- %-24s %s" % (i, zh[k + u".title"]))
        L.append(u"  zh   %s" % zh[k + u".description"])
        L.append(u"  lzh  %s" % lz[k + u".description"])
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
