# -*- coding: utf-8 -*-
u"""_zf176_fixreg.py —— 把我误伤的 3 处能力登记改回 `getFluidHandler()`（只留流体转化器那处用
`handlerFor(side)`）。误伤原因：`(machine, side) -> machine.getFluidHandler());` 这个串在
`PotatoST.java` 里出现 **4** 次（灌装机 / 饮料罐装机 / 转化器 / 柴油发电机），我一次全替换了。

跑法：python build\\zftools\\_zf176_fixreg.py [--write]
"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

P = r"E:\PotatoST\src\main\java\com\potatost\mod\PotatoST.java"


def main(argv):
    write = u"--write" in argv
    text = io.open(P, encoding="utf-8", newline=u"").read()
    lines = text.split(u"\n")
    fixed = 0
    for i, ln in enumerate(lines):
        if u"machine.handlerFor(side)" not in ln:
            continue
        owner = u""
        for j in range(max(0, i - 6), i):
            m = re.search(u"ModBlocks\\.([A-Z0-9_]+)\\.get\\(\\)", lines[j])
            if m:
                owner = m.group(1)
        if owner and owner != u"FLUID_CONVERTER_BE":
            lines[i] = ln.replace(u"machine.handlerFor(side)", u"machine.getFluidHandler()")
            fixed += 1
            print(u"  改回：%s（第 %d 行）" % (owner, i + 1))
        else:
            print(u"  保留 handlerFor：%s（第 %d 行）" % (owner or u"?", i + 1))
    if write:
        io.open(P, "w", encoding="utf-8", newline=u"").write(u"\n".join(lines))
    print(u"模式：%s ｜ 改回 %d 处" % (u"落盘" if write else u"干跑", fixed))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
