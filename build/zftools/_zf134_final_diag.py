# -*- coding: utf-8 -*-
"""_zf134_final_diag.py —— 打印"切完之后"那几行的原样文本（定位 mainCoord 的来源）"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

s = io.open(M, encoding="utf-8").read()
JOBS = [
    ("    /** 一道冲击波。字段全是**值**", "        /** 主轴坐标（当前采样位置）。 */"),
    ("    public static boolean fire(ServerPlayer player", "    /** 推进所有冲击波；由"),
    ("        int ox = owner.getBlockX();", "                BlockState state = wave.level.getBlockState(pos);"),
    ("        if (broke) {", "        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {"),
    ("    /** 每 2 tick 一批粒子", "    /** 当前还有几道波"),
]
for start, end in JOBS:
    i, j = s.index(start), s.index(end)
    s = s[:i] + "/*CUT*/" + s[j:]

print("切完后 mainCoord 出现 %d 次，逐处上下文：" % s.count("mainCoord"))
pos = 0
while True:
    p = s.find("mainCoord", pos)
    if p < 0:
        break
    ln = s[:p].count("\n") + 1
    lines = s.split("\n")
    print("  --- 行 %d ---" % ln)
    for k in range(max(0, ln - 4), min(len(lines), ln + 2)):
        print("   %4d| %s" % (k + 1, lines[k]))
    pos = p + 1
