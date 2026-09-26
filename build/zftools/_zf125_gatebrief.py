# -*- coding: utf-8 -*-
u"""_zf125_gatebrief.py —— 把全门快照的**摘要**抽出来（只留绿/红判词 + 每条红的前 120 字）

为什么：这些门的输出里带整份语言键表，动辄十几 KB；控制台是 GBK，直接打还乱码。
摘要写进 `_zf125_gatesnap_summary.txt`，用文件工具读就不会撑爆上下文。

跑法：
    python build\\zftools\\_zf125_gatebrief.py
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ZT = r"E:\PotatoST\build\zftools"
SRC = os.path.join(ZT, u"_zf125_gatesnap.txt")
DST = os.path.join(ZT, u"_zf125_gatesnap_summary.txt")


def main():
    # ⚠ PowerShell 5.1 的 `>` 重定向默认写 **UTF-16LE**（不是 UTF-8）—— 这里两种都认
    raw = open(SRC, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8", "replace")
    lines = text.split(u"\n")
    out = []
    green = []
    for l in lines:
        s = l.rstrip()
        if s.startswith(u"绿 =") or s.startswith(u"判词") or s.startswith(u"===="):
            out.append(s)
        elif s.startswith(u"  !!"):
            out.append(s[:150])
        elif s.startswith(u"  OK "):
            green.append(s[5:])
    out.append(u"")
    out.append(u"---- 绿的 %d 份 ----" % len(green))
    out.append(u"、".join(green))
    io.open(DST, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(out) + u"\n")
    print(u"摘要 %d 行 → %s" % (len(out), DST))


if __name__ == u"__main__":
    main()
