# -*- coding: utf-8 -*-
r"""_rzh_adv_noop_check.py —— 把 `_rzh_adv_trim.TRIM` 里"新旧一样"的条目挑出来。

为什么单独一个脚本：`_rzh_adv_trim.py` 的守卫会对这种条目**整批拒绝**
（这是对的 —— 一条没意义的编辑通常说明我把原文抄错了），
但排查时得知道**到底是哪几条**。这里只读，输出到 `_rzh_adv_noop.txt`。
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _rzh_adv_trim import TRIM   # noqa: E402

OUT = os.path.join(HERE, u"_rzh_adv_noop.txt")

LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")


def main():
    data = {}
    for loc in LOCALES:
        with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
            data[loc] = json.load(f)

    L = []
    for node, per in sorted(TRIM.items()):
        for loc, (old, new) in sorted(per.items()):
            key = u"advancements.potato_s_t.%s.description" % node
            cur = data[loc].get(key)
            tag = []
            if old == new:
                tag.append(u"新旧一样")
            if cur == new:
                tag.append(u"盘上已是新值（幂等）")
            elif cur != old:
                tag.append(u"盘上与旧值不符")
            if tag:
                L.append(u"%-26s %-6s %s" % (node, loc, u" / ".join(tag)))
                if cur != old:
                    L.append(u"     盘上: %r" % cur)
                    L.append(u"     旧值: %r" % old)

    text = u"\n".join(L) if L else u"没有问题的条目"
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(text + u"\n")
    print(u"wrote %s (%d 条)" % (OUT, len(L)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
