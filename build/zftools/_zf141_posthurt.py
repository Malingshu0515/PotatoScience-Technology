# -*- coding: utf-8 -*-
r"""_zf141_posthurt.py —— 只读：postHurtEnemy 定义在哪、被谁调、有没有分端。

为什么查：本轮想给三把星璨钢新工具写「夜晚不磨损」，而**磨损有两个来源** ——
  · 采掘 → `Item.mineBlock`（已由斧子 ZF133 证明可覆写）
  · 攻击 → `Item.postHurtEnemy`（剑 1/击、DiggerItem 系 2/击）
不查清楚"谁在什么时候调它"，就可能写出"客户端也扣一次"或者"这个钩子根本不触发"的实现。

跑法：python build\zftools\_zf141_posthurt.py
"""
import io
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCES = r"E:\PotatoST\build\neoForm\neoFormJoined1.21.1-20240808.144430\sources.jar"


def main():
    zf = zipfile.ZipFile(SOURCES)
    names = zf.namelist()
    print(u"=" * 78)
    print(u"A sources.jar 里出现 postHurtEnemy 的全部文件")
    print(u"=" * 78)
    files = []
    for n in names:
        if not n.endswith(u".java"):
            continue
        src = zf.read(n).decode(u"utf-8", u"replace")
        if u"postHurtEnemy" in src:
            files.append((n, src))
    for n, _s in files:
        print(u"  " + n)
    print(u"  共 %d 个文件" % len(files))

    print(u"")
    print(u"=" * 78)
    print(u"B 每一处的上下文（定义 + 调用点）")
    print(u"=" * 78)
    for n, src in files:
        lines = src.split(u"\n")
        print(u"")
        print(u"---- %s ----" % n)
        for i, line in enumerate(lines, 1):
            if u"postHurtEnemy" not in line:
                continue
            lo = max(1, i - 8)
            hi = min(len(lines), i + 8)
            print(u"  ...（第 %d 行附近）" % i)
            for j in range(lo, hi + 1):
                mark = u">>" if j == i else u"  "
                print(u"  %s %5d | %s" % (mark, j, lines[j - 1].rstrip()))
            print(u"")


main()
