# -*- coding: utf-8 -*-
"""_zf54_inject.py —— 反证用：让 form() 不认"接线块那两格"，于是它们也会变成部件格。

预期：探针里「2 port cells」与「77 part cells」两条 FAIL。
跑完 `python _zf54_inject.py --restore` 还原。
"""
import io
import sys

P = r"E:\PotatoST\src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java"
LIVE = u"boolean port = originalAt(p) != null && originalAt(p).is(ModBlocks.WIRING_BLOCK.get());"
DEAD = u"boolean port = false;   // ← 反证用"

t = io.open(P, encoding="utf-8").read()
if (sys.argv[1:] or ["--inject"])[0] == "--restore":
    if DEAD not in t:
        raise SystemExit(u"没找到注入后的文本")
    io.open(P, "w", encoding="utf-8", newline="").write(t.replace(DEAD, LIVE))
    print(u"已还原")
else:
    if LIVE not in t:
        raise SystemExit(u"没找到原始文本")
    io.open(P, "w", encoding="utf-8", newline="").write(t.replace(LIVE, DEAD))
    print(u"已注入")
