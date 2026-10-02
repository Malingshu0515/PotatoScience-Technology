# -*- coding: utf-8 -*-
"""_zf134_where.py —— 剥注释后 mainCoord 到底还在代码的哪一行（打印上下文）"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

s = io.open(M, encoding="utf-8").read()
# 复刻 manager5 的替换（只替换，不写盘），再看剩下什么
JOBS = [
    ("    /** 一道冲击波。字段全是**值**", "        /** 主轴坐标（当前采样位置）。 */"),
    ("    public static boolean fire(ServerPlayer player", "    /** 推进所有冲击波；由"),
    ("        int ox = owner.getBlockX();", "                BlockState state = wave.level.getBlockState(pos);"),
    ("        if (broke) {", "        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {"),
    ("    /** 每 2 tick 一批粒子", "    /** 当前还有几道波"),
]
KEYS = {
    "    /** 一道冲击波。字段全是**值**": "/*WAVE*/",
    "    public static boolean fire(ServerPlayer player": "/*FIRE*/",
    "        int ox = owner.getBlockX();": "/*TICK*/",
    "        if (broke) {": "/*BREAK*/",
    "    /** 每 2 tick 一批粒子": "/*PART*/",
}
for start, end in JOBS:
    i, j = s.index(start), s.index(end)
    s = s[:i] + KEYS[start] + s[j:]

code = re.sub(r"/\*[\s\S]*?\*/", "/*C*/", s)
code = re.sub(r"//[^\n]*", "", code)
print("剥注释后 mainCoord 出现 %d 次" % code.count("mainCoord"))
for m in re.finditer("mainCoord", code):
    ln = code[:m.start()].count("\n") + 1
    print("  行 %d: %s" % (ln, code.split("\n")[ln - 1].strip()[:120]))
print("--- 替换后的 tick 采样区（前 30 行）---")
i = code.find("/*TICK*/")
print("\n".join(code[i:i + 1400].split("\n")[:30]))
