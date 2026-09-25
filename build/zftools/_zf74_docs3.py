# -*- coding: utf-8 -*-
u"""_zf74_docs3.py —— 把新成品 SHA1 写进档案 §9（ZF74 校验 C8 要求的）"""
import io
import sys

ARCH = r"E:\PotatoST\docs\开发档案.md"
OLD = u"（成品 `release\\PotatoST-0.11.jar`，**同版本重打包 ⇒ `2a35a9ee…` 作废**）"
NEW = (u"（成品 `release\\PotatoST-0.11.jar` = **`39e66beb0a7ee2037c466ff343a6d4dc42484274`**"
       u"（2,227,272 B / 724 条目）；**同版本重打包 ⇒ 上一版 `2a35a9ee…` 作废**）")


def main():
    text = io.open(ARCH, "r", encoding="utf-8").read()
    n = text.count(OLD)
    if n != 1:
        print(u"锚点命中 %d 次（必须 1）⇒ 不写" % n)
        return 1
    io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(text.replace(OLD, NEW, 1))
    print(u"§9 已记入新成品 SHA1 与作废声明")
    return 0


if __name__ == "__main__":
    sys.exit(main())
