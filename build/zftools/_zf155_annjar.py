# -*- coding: utf-8 -*-
u"""_zf155_annjar.py —— 公告 ZF155 那一条补一句 Download（这一版成品里装了什么）。

跑法：python build\\zftools\\_zf155_annjar.py [--write]
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.12.jar")
SHA = JAR + u".sha1"

sha = io.open(SHA, encoding="ascii").read().strip()
size = u"{:,}".format(os.path.getsize(JAR))
ANCHOR = u"- Works across `/reload` (the table is re-widened before recipes are sent to clients).\n"
ADD = (u"\n**Download:** `release/PotatoST-0.12.jar` - **%s bytes**, sha1 **`%s`** "
       u"(rebuilt for 0.12 with the Universal Upgrade Template; the previous jar is superseded).\n"
       % (size, sha))


def main(argv):
    write = u"--write" in argv
    text = io.open(ANN, encoding="utf-8", newline="").read()
    if u"## New in 0.12 ZF155" not in text:
        print(u"!! 公告里没有 ZF155 那一条")
        return 1
    if text.count(ANCHOR) != 1:
        print(u"!! 锚点命中 %d 次" % text.count(ANCHOR))
        return 1
    if u"rebuilt for 0.12 with the Universal Upgrade Template" in text:
        print(u"  [跳过] 已经补过了（幂等）")
        return 0
    print(u"待插入：%s" % ADD.strip())
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    io.open(ANN, u"w", encoding="utf-8", newline=u"").write(text.replace(ANCHOR, ANCHOR + ADD, 1))
    print(u"已落盘")
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
