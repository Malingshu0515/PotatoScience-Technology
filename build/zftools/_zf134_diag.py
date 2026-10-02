# -*- coding: utf-8 -*-
"""_zf134_diag.py —— 为什么锚点匹配不上（逐字符 diff，不靠眼睛）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

START = "    /** 一道冲击波。字段全是**值**（Level 引用只在服务端活着时用，玩家一退就丢）。 */"
END = "        /** 主轴坐标（当前采样位置）。 */"

s = io.open(M, encoding="utf-8").read()
i = s.find(START)
j = s.find(END)
print("START idx =", i, " END idx =", j)
if i > 0 and j > i:
    seg = s[i:j]
    print("段长 =", len(seg))
    print("--- 前 12 行 ---")
    for k, l in enumerate(seg.split("\n")[:12]):
        print("%3d| %s" % (k, l))
    print("--- 该段里有没有 alongX ---", "alongX" in seg)
