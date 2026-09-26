# -*- coding: utf-8 -*-
r"""_zf141_mineblock.py —— 只读：把 **mineBlock / hurtAndBreak 到底写在哪个类里** 钉死。

为什么单独跑一趟：`_zf141_recon.py` ⑤ 打出来的继承关系与我的印象**不一致**
（SwordItem 直接 extends TieredItem，而且 DiggerItem.java 里**没有** mineBlock）
—— 这种"印象与事实不符"的地方正是最该现抠的。判据不能建立在记忆上。

跑法：python build\zftools\_zf141_mineblock.py
"""
import io
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCES = r"E:\PotatoST\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"
WANT = [
    u"net/minecraft/world/item/Item.java",
    u"net/minecraft/world/item/TieredItem.java",
    u"net/minecraft/world/item/DiggerItem.java",
    u"net/minecraft/world/item/SwordItem.java",
]


def body_of(src, marker):
    u"""把含 marker 的那一行连同它的大括号块整段抠出来（深度配平）。"""
    lines = src.split(u"\n")
    out = []
    for i, line in enumerate(lines):
        if marker not in line:
            continue
        out.append(u"    %5d | %s" % (i + 1, line.rstrip()))
        depth = line.count(u"{") - line.count(u"}")
        j = i
        while depth > 0 and j + 1 < len(lines):
            j += 1
            out.append(u"    %5d | %s" % (j + 1, lines[j].rstrip()))
            depth += lines[j].count(u"{") - lines[j].count(u"}")
    return out


def main():
    zf = zipfile.ZipFile(SOURCES)
    names = zf.namelist()
    print(u"=" * 78)
    print(u"A 整个 sources.jar 里出现 mineBlock 的**全部**位置")
    print(u"=" * 78)
    hits = []
    for n in names:
        if not n.endswith(u".java"):
            continue
        try:
            src = zf.read(n).decode(u"utf-8", u"replace")
        except Exception:
            continue
        if u"mineBlock" in src:
            hits.append(n)
    for n in sorted(hits):
        print(u"  " + n)
    print(u"  共 %d 个文件" % len(hits))

    print(u"")
    print(u"=" * 78)
    print(u"B 四个关键类的 mineBlock 方法体（逐字）")
    print(u"=" * 78)
    for want in WANT:
        hit = [n for n in names if n.endswith(want)]
        if not hit:
            print(u"  !! 没有 %s" % want)
            continue
        src = zf.read(hit[0]).decode(u"utf-8", u"replace")
        print(u"")
        print(u"---- %s ----" % want.split(u"/")[-1])
        for line in src.split(u"\n"):
            s = line.strip()
            if s.startswith(u"public class") or s.startswith(u"public interface"):
                print(u"  " + s)
        got = body_of(src, u"mineBlock(")
        if not got:
            print(u"    （本类里没有 mineBlock）")
        for line in got:
            print(line)

    print(u"")
    print(u"=" * 78)
    print(u"C hurtAndBreak 在 Item 里的签名（mineBlock 里调的就是它）")
    print(u"=" * 78)
    item = zf.read([n for n in names if n.endswith(u"net/minecraft/world/item/Item.java")][0]
                   ).decode(u"utf-8", u"replace")
    for line in item.split(u"\n"):
        if u"hurtAndBreak" in line:
            print(u"  " + line.strip())


main()
