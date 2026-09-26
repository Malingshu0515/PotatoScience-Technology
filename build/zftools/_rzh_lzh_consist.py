# -*- coding: utf-8 -*-
r"""_rzh_lzh_consist.py —— 查「物品/方块名」与「正文里叫它的写法」是否一致。

为什么必须单独查一遍：三份译稿是**并行**产出的 —— 第 1 片译物品名，第 2 片译
tooltip/GUI，第 3 片译成就。同一个东西在第 1 片叫「鋰電池元件」，在第 2 片正文里
可能还写着「鋰電池原件」；片内自洽，**合起来才暴露**。

判据不是"这两串必须一样"（正文常有量词/复数差异），而是：
  对每个 item./block. 显示名，看**同一语言里有多少条非物品键的正文提到它**；
  再列出正文里出现、但**对不上任何显示名**的候选词（人工过目）。
另外单独查一个高频风险：显示名 A 与显示名 B **互为前缀**时（鋰電池 / 鋰電池元件，
三元聚合物鋰電池 / 鋰電池），正文用哪一个才不会读串。

用法：`python build/zftools/_rzh_lzh_consist.py`
结论写 `_rzh_lzh_consist.txt`。
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), u"_rzh_lzh_consist.txt")

# 需要盯的"名字族"：物品名里的关键字 -> 正文里可能出现的各种叫法
FAMILIES = [
    (u"胄", [u"胄", u"頭盔", u"盔"]),
    (u"鎧", [u"鎧", u"胸甲", u"甲"]),
    (u"護腿", [u"護腿", u"腿甲", u"脛甲"]),
    (u"靴", [u"靴", u"靴子", u"鞾"]),
    (u"鍁", [u"鍁", u"鏟", u"鍬", u"鏟子"]),
    (u"鋰電池", [u"鋰電池", u"鋰電池元件", u"鋰電池原件", u"三元聚合物鋰電池", u"三元鋰電池"]),
    (u"扳鉗", [u"扳鉗", u"扳手", u"鉗"]),
    (u"印墨", [u"印墨", u"墨粉", u"碳粉"]),
    (u"光伏", [u"光伏器件", u"光伏元件", u"光起電力"]),
    (u"音樂唱片", [u"音樂唱片", u"留聲盤", u"唱片"]),
    (u"海鹽", [u"海鹽", u"鹽"]),
    (u"合金爐", [u"合金爐", u"冶煉爐", u"精錬爐"]),
    (u"熱力金屬", [u"熱力金屬", u"熱金"]),
]


def main():
    d = json.load(io.open(os.path.join(LANGDIR, u"lzh.json"), encoding=u"utf-8"))
    names = dict((k, v) for k, v in d.items()
                 if k.startswith(u"item.") or k.startswith(u"block."))

    L = []
    L.append(u"== 名字族：正文里用了哪一种叫法 ==")
    for canon, variants in FAMILIES:
        L.append(u"")
        L.append(u"---- 规范名/关键字「%s」" % canon)
        for v in variants:
            keys = [k for k in d if v in d[k] and k not in names]
            nkeys = [k for k in names if v in names[k]]
            if not keys and not nkeys:
                continue
            mark = u" ←物品名" if nkeys else u""
            L.append(u"     「%s」：正文 %2d 条 / 物品名 %d 个%s" % (v, len(keys), len(nkeys), mark))
            for k in keys[:6]:
                L.append(u"        %s" % k)

    # 互为前缀的显示名 —— 正文用短名会读串
    L.append(u"")
    L.append(u"== 互为前缀的显示名（正文必须写全，否则读串）==")
    vs = sorted((v, k) for k, v in names.items())
    for i, (a, ka) in enumerate(vs):
        for b, kb in vs[i + 1:]:
            if len(a) < len(b) and b.startswith(a):
                na = sum(d[k].count(a) for k in d if k not in names)
                nb = sum(d[k].count(b) for k in d if k not in names)
                L.append(u"   「%s」(%s) ⊂ 「%s」(%s)   正文出现：短 %d 次 / 长 %d 次"
                         % (a, ka.split(u".")[-1], b, kb.split(u".")[-1], na, nb))

    text = u"\n".join(L)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(text + u"\n")
    print(u"wrote %s" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
