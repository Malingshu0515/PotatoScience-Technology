# -*- coding: utf-8 -*-
"""_zf133_dbg13b.py —— 末地场景里把末影人与发射者的坐标打出来"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

A = "        ender.setNoAi(true);"
B = A + """
        say(TAG + "      [DMG] 末影人 @ " + String.format("%.2f,%.2f,%.2f",
                ender.getX(), ender.getY(), ender.getZ())
                + " 发射者 @ " + String.format("%.2f,%.2f,%.2f",
                        endPlayer.getX(), endPlayer.getY(), endPlayer.getZ())
                + " 维度=" + end.dimension().location());"""

s = io.open(CHK, encoding="utf-8").read()
n = s.count(A)
assert n == 1, "锚点 %d" % n
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(A, B, 1))
print("[OK] 已加末影人坐标打印")
