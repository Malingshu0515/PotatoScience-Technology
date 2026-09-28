# -*- coding: utf-8 -*-
u"""_zf155_peek3.py —— 取"成品行"与公告里那两处当前哈希的**逐字原文**（只读），供打包脚本当锚点。"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HAND = r"E:\PotatoST\docs\多会话协作交接.md"
ANN = r"E:\PotatoST\docs\UpdateAnnouncement_EN.md"

hand = io.open(HAND, encoding="utf-8").read().split("\n")
print(u"== 交接 §1 成品行 / 未发布构建行 ==")
for i, l in enumerate(hand):
    if u"已发布成品" in l or u"未发布的构建" in l:
        print(u"%5d| %s" % (i + 1, l))
        print(u"      repr=%r" % l[:80])

ann = io.open(ANN, encoding="utf-8").read().split("\n")
print(u"\n== 公告里所有 fa2c550d / 5,848,073 出现处 ==")
for i, l in enumerate(ann):
    if u"fa2c550d" in l or u"5,848,073" in l:
        print(u"%5d| %s" % (i + 1, l.strip()[:200]))
