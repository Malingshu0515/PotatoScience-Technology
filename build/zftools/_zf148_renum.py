# -*- coding: utf-8 -*-
u"""_zf148_renum.py —— ZF148 补丁（第二版）：把**我这一节**的编号定到 §4.158（幂等）。

为什么一路改到这个号：`开发档案.md` 的 §4 编号**不按文件位置递增**，而且**已经有两套并行的序列**
（实测：162 条标题、max = **4.157**，其中 `4.90/4.91/4.92/4.146/4.147/4.148/4.149/4.150/4.152`
**各占两份** —— 两条线各编各的）。我第一版按"文件里最后一条 = 4.150"取了 §4.151 ⇒ 撞；
第二版改到 4.152 ⇒ **又**撞（也是两份）。定稿：**取 max(全文件 §4 编号) + 1 = 4.158**。
⚠ 只动本轮自己写下的那几处；别人的节一个字不动。

跑法：python build\\zftools\\_zf148_renum.py [--write]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

DOC = r"E:\PotatoST\docs\开发档案.md"
NEW = u"4.158"

JOBS = [
    (u"### 4.152 【工具雷】**联动帕秋莉**这一轮踩到的四个坑（0.12 ZF148）",
     u"### %s 【工具雷】**联动帕秋莉**这一轮踩到的四个坑（0.12 ZF148）" % NEW,
     u"档案标题 → §%s" % NEW),
    (u"见 §9 ｜ 见 §4.152 |", u"见 §9 ｜ 见 §%s |" % NEW, u"§5 行里的引用"),
    (u"（见 §4.152 第 5 条）", u"（见 §%s 第 5 条）" % NEW, u"§9 里的引用"),
]

TIP = u"""⚠ **顺带一条同族教训（本轮真踩了两次）**：`§4` 的编号**既不看文件位置、也不是全局唯一** ——
实测 162 条 §4 标题里 max = **4.157**，而且 `4.90/4.91/4.92/4.146…4.150/4.152` **各占两份**
（两条线各编各的）。本轮第一版取"文件里最后一条 + 1" = 4.151 ⇒ 撞；第二版改 4.152 ⇒ **又**撞。
**口径：取 `max(全文件 §4 编号) + 1`，而且动手前先 `grep '^#{3,4} 4\\.'` 数一遍重复**。
"""


def main(argv):
    write = u"--write" in argv
    text = io.open(DOC, encoding=u"utf-8", newline=u"").read()

    nums = [int(m.group(1)) for m in re.finditer(u"(?m)^#{3,4} 4\\.([0-9]+)", text)]
    dup = sorted({n for n in nums if nums.count(n) > 1})
    mine = [n for n in nums if n >= 158]
    print(u"盘上 §4 编号：共 %d 条，max = %d，重复编号 %s" % (len(nums), max(nums), dup))
    print(u"本轮目标 = §%s（盘上 158 以上目前 %d 条）" % (NEW, len(mine)))
    if mine:
        print(u"  [警告] 已经有人用到 %s —— 请再确认一次" % mine)

    fails, notes, new = [], [], text
    for old, rep, label in JOBS:
        if rep in new and old not in new:
            notes.append(u"  [跳过] %s（已经是 §%s，幂等）" % (label, NEW))
            continue
        n = new.count(old)
        if n != 1:
            fails.append(u"%s：命中 %d 次（应为 1）" % (label, n))
            continue
        new = new.replace(old, rep, 1)
        notes.append(u"  [改] %s" % label)

    head = u"### %s 【工具雷】**联动帕秋莉**这一轮踩到的四个坑（0.12 ZF148）\n" % NEW
    if u"本轮真踩了两次" not in new:
        if head in new:
            new = new.replace(head, head + u"\n" + TIP, 1)
            notes.append(u"  [改] 补上「取号取 max+1」这条口径")
        else:
            fails.append(u"补口径：找不到 §%s 标题" % NEW)

    print(u"\n".join(notes))
    print(u"")
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    io.open(DOC, u"w", encoding=u"utf-8", newline=u"").write(new)
    assert io.open(DOC, encoding=u"utf-8", newline=u"").read() == new
    print(u"已写盘")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
