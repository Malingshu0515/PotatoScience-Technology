# -*- coding: utf-8 -*-
u"""_zf74_mkgates.py —— 由 `_zf73_gates.ps1` 生成 `_zf74_gates.ps1`（只在末尾加一行 ZF74 校验）"""
import io
import os
import sys

Z = r"E:\PotatoST\build\zftools"
SRC = os.path.join(Z, u"_zf73_gates.ps1")
DST = os.path.join(Z, u"_zf74_gates.ps1")

OLD = u"Run-Py  'ZF73 verify'      '_zf73_verify.py'  $null"
NEW = (u"Run-Py  'ZF73 verify'      '_zf73_verify.py'  $null\n"
       u"# ZF74 本轮：流体 c: 通用标签（29 项：标签文件形状 / 判定真的认标签 / 发布与作废 / 文档）\n"
       u"Run-Py  'ZF74 verify'      '_zf74_verify.py'  $null")


def main():
    text = io.open(SRC, "r", encoding="utf-8").read()
    if text.count(OLD) != 1:
        print(u"锚点命中 %d 次 ⇒ 不写" % text.count(OLD))
        return 1
    text = text.replace(OLD, NEW, 1)
    text = text.replace(u"_zf73_gates.ps1", u"_zf74_gates.ps1")
    text = text.replace(u"#  _zf73_gates.ps1 —— ZF73（0.11 石油线第一批）交付前门检查",
                        u"#  _zf74_gates.ps1 —— ZF74（流体通用标签）交付前门检查")
    io.open(DST, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"已生成 %s" % DST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
