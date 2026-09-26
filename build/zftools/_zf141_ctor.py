# -*- coding: utf-8 -*-
r"""_zf141_ctor.py —— 只读：把五个工具类 + Tiers 的**全文**打出来（都很短，别再写筛子）。

第一版我写了个"只挑构造器/TOOL 组件那几行"的筛子，结果**一行都没匹配上**
（筛子本身有 bug）—— 这正是本工程那条老账：**筛子比正文更容易骗人**。
这些文件加起来不到 550 行，全打出来比写筛子便宜。

跑法：python build\zftools\_zf141_ctor.py
"""
import io
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCES = r"E:\PotatoST\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"
OUT = r"E:\PotatoST\build\zftools\_zf141_ctor.txt"
FILES = [
    u"net/minecraft/world/item/SwordItem.java",
    u"net/minecraft/world/item/DiggerItem.java",
    u"net/minecraft/world/item/PickaxeItem.java",
    u"net/minecraft/world/item/HoeItem.java",
    u"net/minecraft/world/item/Tiers.java",
]


def main():
    zf = zipfile.ZipFile(SOURCES)
    names = zf.namelist()
    buf = []
    for want in FILES:
        hit = [n for n in names if n.endswith(want)]
        if not hit:
            buf.append(u"!! 没有 %s" % want)
            continue
        src = zf.read(hit[0]).decode(u"utf-8", u"replace")
        lines = src.split(u"\n")
        buf.append(u"")
        buf.append(u"=" * 78)
        buf.append(u"---- %s ----（共 %d 行）" % (want.split(u"/")[-1], len(lines)))
        buf.append(u"=" * 78)
        for i, line in enumerate(lines, 1):
            buf.append(u"%5d | %s" % (i, line.rstrip()))
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(u"\n".join(buf) + u"\n")
    print(u"写好了：%s（%d 行）" % (OUT, len(buf)))


main()
