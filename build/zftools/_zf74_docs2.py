# -*- coding: utf-8 -*-
u"""_zf74_docs2.py —— 补上 `_zf74_docs.py` 没写进去的三处档案编辑

为什么没写进去：`_zf74_docs.py` 的 §9 锚点我写成了「六个空格 + 并把 `_zf69_repro.py` 改成**响的**。」，
而档案里那一行是「`_zf73_repro.py`（…），并把 `_zf69_repro.py` 改成**响的**。」——
锚点带了不该有的行首空格 ⇒ 命中 0 次 ⇒ **按规矩整个文件不写**（另外三个文件已写）。

这里复用 `_zf74_docs` 里已经写好的内容块，只把 §9 锚点换成行内片段。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _zf74_docs as d  # noqa: E402  （复用内容块，避免两份文案漂移）

ARCH = d.ARCH
A_S9_FIXED = u"并把 `_zf69_repro.py` 改成**响的**。"


def main():
    text = io.open(ARCH, "r", encoding="utf-8").read()
    pairs = [
        (d.A_S6, d.SEC_619 + d.A_S6, u"§6.19"),
        (d.A_ROW, d.A_ROW + u"\n" + d.ROW_ZF74, u"§5 ZF74 行"),
        (A_S9_FIXED, A_S9_FIXED + u"\n" + d.SEC_S9.rstrip(u"\n"), u"§9 ZF74 待办"),
    ]
    for old, new, what in pairs:
        n = text.count(old)
        if n != 1:
            print(u"  !! %s：命中 %d 次（必须 1）⇒ 整篇不写" % (what, n))
            return 1
        text = text.replace(old, new, 1)
        print(u"  [OK] %s" % what)
    io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"档案三处补齐（§6.19 / §5 ZF74 行 / §9）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
