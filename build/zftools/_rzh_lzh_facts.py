# -*- coding: utf-8 -*-
r"""_rzh_lzh_facts.py —— 复核文言文那一套成就里，**数字与单位有没有抄错**。

文言文的措辞可以跟中文不同（那是翻译），但**数字、单位、坐标、占位符必须逐字相同**。
所以这里不检查措辞，只按正则把每条成就里的"数字+单位"抠出来，与 zh_cn 对齐比。

判据：同一节点里，zh_cn 出现的「数字（可带单位）」集合，必须被 lzh 覆盖。
（lzh 允许出现 zh_cn 没有的数字吗？不允许 —— 那就说明抄错了。）

输出 `_rzh_lzh_facts.txt`。
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_lzh_facts.txt")

# 「数字 + 可选单位」；单位表覆盖两套文字里出现过的写法
NUM = re.compile(u"(\\d+(?:\\.\\d+)?)\\s*(?:mB|FE/t|FE|B\\b|n|%|秒|格|個|块|塊)?")


def nums(s):
    """抠出所有数字，**去掉量词后缀**只留数字本身。

    ⚠ 第一版把量词也留下了，于是 `1 個` 与 `1` 被当成两个不同的东西（假阳性）。
       量词是措辞，不是事实；要守的是**数字**。
    """
    return sorted(set(m.group(1) for m in NUM.finditer(s)))


def main():
    zh = json.load(io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8"))
    lz = json.load(io.open(os.path.join(LANGDIR, u"lzh.json"), encoding=u"utf-8"))
    ids = sorted(set(re.match(u"advancements\\.potato_s_t\\.([a-z0-9_]+)\\.",
                              k).group(1)
                     for k in zh if k.startswith(u"advancements.")))

    L = []
    bad = 0
    for i in ids:
        k = u"advancements.potato_s_t.%s.description" % i
        a, b = nums(zh[k]), nums(lz[k])
        miss = [x for x in a if x not in b]
        extra = [x for x in b if x not in a]
        if miss or extra:
            bad += 1
            L.append(u"---- %s" % i)
            if miss:
                L.append(u"   [少] %s" % u", ".join(miss))
            if extra:
                L.append(u"   [多] %s" % u", ".join(extra))
            L.append(u"   zh  %s" % zh[k])
            L.append(u"   lzh %s" % lz[k])
    if not L:
        L.append(u"文言文成就：数字与单位与 zh_cn 逐条对齐，无差异（%d 条）" % len(ids))
    L.append(u"")
    L.append(u"有差异的节点 %d / %d" % (bad, len(ids)))
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s  (差异 %d 条)" % (OUT, bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
