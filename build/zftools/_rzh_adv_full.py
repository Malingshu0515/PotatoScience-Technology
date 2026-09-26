# -*- coding: utf-8 -*-
r"""_rzh_adv_full.py —— 打印全部成就的**完整**说明（四语并排），供逐条改写。

`_rzh_adv_survey.py` 只给首行和字数；要动笔得看全文。
输出 `_rzh_adv_full.txt`（UTF-8，脚本自己写）。
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_adv_full.txt")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]


def main():
    d = {}
    for loc in LOCALES:
        with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
            d[loc] = json.load(f)
    zh = d[u"zh_cn"]
    ids = sorted(set(re.match(u"advancements\\.potato_s_t\\.([a-z0-9_]+)\\.",
                              k).group(1)
                     for k in zh if k.startswith(u"advancements.")))
    only = sys.argv[1:] if len(sys.argv) > 1 else None

    L = []
    for i in ids:
        if only and i not in only:
            continue
        k = u"advancements.potato_s_t.%s" % i
        L.append(u"=" * 100)
        L.append(u"### %s" % i)
        for loc, tag in zip(LOCALES, [u"zh", u"en", u"ja", u"ru"]):
            L.append(u"  [%s] 标题 %s" % (tag, d[loc].get(k + u".title", u"<缺>")))
            L.append(u"  [%s] 说明 %s" % (tag, d[loc].get(k + u".description", u"<缺>")))
        L.append(u"")

    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(u"\n".join(L) + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
