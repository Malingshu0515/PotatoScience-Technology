# -*- coding: utf-8 -*-
r"""_rzh_lzh_check_part.py —— 对**单份**译稿做结构体检（在合并之前就能发现问题）。

合并器只在三份齐了以后才跑；这个脚本让每一份一到手就能验：
键集、键序、占位符序列、`\n` 个数、数字与单位的总量、以及**字形**（混进简体就报）。
用法：`python build/zftools/_rzh_lzh_check_part.py <序号 1|2|3>`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, u"_rzh_lzh_check_part.txt")
PH = re.compile(u"%\\d+\\$s|%s|%%")
# 只在简体里出现、繁体不会这么写的字形（与 _rzh_lzh_verify.py 同一张表）
# ⚠ 别把「面 / 器 / 只 / 言」这类**简繁同形**的字放进来 —— 会把「界面」「電解器」
#   误报成"混进简体"。第一版就栽在这儿。
SIMP = (u"钛钨铀铝钴镍锰锂硅矿锭铁铜银钢电气机门开关热温层数这们来时与并产于过进还"
        u"种样当经应对线号处车马鸟鱼龙凤买卖读写说话语")
UNITS = [u"FE", u"mB", u"tick", u"JEI", u"Shift", u"Y=", u"c:"]


def main():
    n = sys.argv[1] if len(sys.argv) > 1 else u"2"
    a = json.load(io.open(os.path.join(HERE, u"_rzh_lzh_in%s.json" % n), encoding=u"utf-8"))
    b = json.load(io.open(os.path.join(HERE, u"_rzh_lzh_out%s.json" % n), encoding=u"utf-8"))
    L = []
    L.append(u"== 第 %s 份：in %d 键 / out %d 键 ==" % (n, len(a), len(b)))
    L.append(u"键序完全相同: %s" % (list(a) == list(b)))
    miss = [k for k in a if k not in b]
    extra = [k for k in b if k not in a]
    L.append(u"缺 %d / 多 %d %s %s" % (len(miss), len(extra), miss[:4], extra[:4]))

    ph = [k for k in a if k in b and PH.findall(a[k]) != PH.findall(b[k])]
    nl = [k for k in a if k in b and a[k].count(u"\\n") != b[k].count(u"\\n")]
    L.append(u"占位符不符 %d 条 %s" % (len(ph), ph[:5]))
    L.append(u"换行个数不符 %d 条 %s" % (len(nl), nl[:5]))

    for u in UNITS:
        na = sum(v.count(u) for v in a.values())
        nb = sum(v.count(u) for v in b.values())
        L.append(u"单位 %-6s 原文 %3d / 译文 %3d  %s" % (u, na, nb, u"OK" if na == nb else u"!! 不等"))

    simp = [(k, u"".join(ch for ch in b[k] if ch in SIMP)) for k in b]
    simp = [(k, h) for k, h in simp if h]
    L.append(u"混进简体字形的键 %d 个：" % len(simp))
    for k, h in simp[:20]:
        L.append(u"   %-46s %s" % (k, h))

    # 未译：值与原中文逐字相同（简繁同形的词会命中，列出供人工判断）
    same = [k for k in a if k in b and a[k] == b[k]]
    L.append(u"与中文逐字相同 %d 条：" % len(same))
    for k in same:
        L.append(u"   %-46s %s" % (k, b[k].replace(u"\n", u"\\n")[:60]))

    text = u"\n".join(L)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(text + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
