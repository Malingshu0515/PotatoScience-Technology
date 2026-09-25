# -*- coding: utf-8 -*-
u"""_zf75_mkgates.py —— 由 `_zf74_gates.ps1` 生成 `_zf75_gates.ps1`（末尾加 ZF75 校验）"""
import io
import os
import sys

Z = r"E:\PotatoST\build\zftools"
SRC = os.path.join(Z, u"_zf74_gates.ps1")
DST = os.path.join(Z, u"_zf75_gates.ps1")

OLD = u"Run-Py  'ZF74 verify'      '_zf74_verify.py'  $null"
NEW = (u"Run-Py  'ZF74 verify'      '_zf74_verify.py'  $null\n"
       u"# ZF75 本轮：世界生成（地表油田 + 海洋油田群系）35 项 + 内置反证\n"
       u"Run-Py  'ZF75 verify'      '_zf75_verify.py'  $null")


def main():
    text = io.open(SRC, "r", encoding="utf-8").read()
    if text.count(OLD) != 1:
        print(u"锚点命中 %d 次 ⇒ 不写" % text.count(OLD))
        return 1
    text = text.replace(OLD, NEW, 1)
    text = text.replace(u"_zf74_gates.ps1", u"_zf75_gates.ps1")
    text = text.replace(u"ZF74（流体通用标签）交付前门检查", u"ZF75（世界生成）交付前门检查")
    io.open(DST, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"已生成 %s" % DST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
