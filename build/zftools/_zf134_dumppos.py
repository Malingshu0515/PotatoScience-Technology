# -*- coding: utf-8 -*-
"""_zf134_dumppos.py —— 把脚本实际切到的位置与内容前两行打出来（定位"为什么没切干净"）"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

JOBS = [
    ("WAVE", "    /** 一道冲击波。字段全是**值**", "        /** 主轴坐标（当前采样位置）。 */"),
    ("FIRE", "    public static boolean fire(ServerPlayer player", "    /** 推进所有冲击波；由"),
    ("TICK", "        int ox = owner.getBlockX();", "                BlockState state = wave.level.getBlockState(pos);"),
    ("BREAK", "        if (broke) {", "        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {"),
    ("PART", "    /** 每 2 tick 一批粒子", "    /** 当前还有几道波"),
]

s = io.open(M, encoding="utf-8").read()
for name, start, end in JOBS:
    i = s.index(start)
    j = s.index(end)
    seg = s[i:j]
    first = seg.split("\n")[0]
    last = seg.rstrip("\n").split("\n")[-1]
    print("== %s ==" % name)
    print("   起点行号 %d 起点列偏移 %d" % (s[:i].count("\n") + 1, i - s.rfind("\n", 0, i) - 1))
    print("   段长 %d 行数 %d" % (len(seg), seg.count("\n")))
    print("   首行: %s" % first.strip()[:80])
    print("   末行: %s" % last.strip()[:80])
    print("   段内 mainCoord=%d  alongX=%d" % (seg.count("mainCoord"), seg.count("alongX")))
