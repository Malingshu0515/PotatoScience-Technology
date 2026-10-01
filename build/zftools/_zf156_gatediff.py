# -*- coding: utf-8 -*-
u"""_zf156_gatediff.py —— 对比 ZF155 与 ZF156 两次全门快照的**红名单**（只读）。

只回答一件事：**这一轮有没有"新增的红"**，以及新增的那几条是不是本轮的账。

跑法：python build\\zftools\\_zf156_gatediff.py
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ZT = r"E:\PotatoST\build\zftools"


def reds(path):
    if not os.path.isfile(path):
        return None, u""
    text = io.open(path, encoding="utf-8", errors="replace").read()
    out = set()
    inred = False
    for line in text.split(u"\n"):
        if line.startswith(u"---- 红的"):
            inred = True
            continue
        if line.startswith(u"---- 绿的") or line.startswith(u"---- 不在盘上"):
            inred = False
            continue
        if inred:
            # ⚠ 只认"脚本名"那一种行（`  !! _zfNNN_verify.py …`）——
            #   第一版用 `\s*!!\s+(\S+)` 把门里的**明细行**（`        !! 数据变化: …`）也当成红了。
            m = re.match(u"\\s{2}!!\\s+(_[A-Za-z0-9_]+\\.py|_[A-Za-z0-9_]+\\.ps1)\\s*$|"
                         u"\\s{2}!!\\s+(_[A-Za-z0-9_]+\\.py)\\s", line)
            if m:
                out.add(m.group(1) or m.group(2))
    head = re.search(u"绿 = \\d+\\s+红 = \\d+\\s+不存在 = \\d+", text)
    return out, (head.group(0) if head else u"")


def main():
    a, ha = reds(os.path.join(ZT, u"_zf155_gatesnap.txt"))
    b, hb = reds(os.path.join(ZT, u"_zf156_gatesnap.txt"))
    if a is None or b is None:
        print(u"!! 两份快照缺一份：ZF155=%s ZF156=%s" % (a is not None, b is not None))
        return 1
    print(u"ZF155（上一轮收尾）：%s" % ha)
    print(u"ZF156（本轮收尾）  ：%s" % hb)
    print(u"")
    new = sorted(b - a)
    fixed = sorted(a - b)
    print(u"新增的红（%d 条）：" % len(new))
    for n in new:
        print(u"  + " + n)
    print(u"变绿的（%d 条）：" % len(fixed))
    for n in fixed:
        print(u"  - " + n)
    print(u"两轮都红（%d 条，历史账）：%s" % (len(a & b), u", ".join(sorted(a & b))))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
