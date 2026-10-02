# -*- coding: utf-8 -*-
"""_zf134_where2.py —— 用 _zf134_apply 的**同一套切片**，然后打印残留 mainCoord 的上下文"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

JOBS = [
    ("    /** 一道冲击波。字段全是**值**", "        /** 主轴坐标（当前采样位置）。 */\n"),
    ("    public static boolean fire(ServerPlayer player", "    /** 推进所有冲击波；由"),
    ("        int ox = owner.getBlockX();", "                BlockState state = wave.level.getBlockState(pos);\n"),
    ("        if (broke) {", "        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {"),
    ("    /** 每 2 tick 一批粒子", "    /** 当前还有几道波"),
]


def strip_comments(src):
    out = re.sub(r"/\*[\s\S]*?\*/", "", src)
    return re.sub(r"//[^\n]*", "", out)


s = io.open(M, encoding="utf-8").read()
for start, end in JOBS:
    i = s.index(start)
    j = s.index(end) + len(end)
    s = s[:i] + "/*CUT*/" + s[j:]

code = strip_comments(s)
lines = code.split("\n")
print("剥注释后 mainCoord = %d 次" % code.count("mainCoord"))
for m in re.finditer("mainCoord", code):
    ln = code[:m.start()].count("\n") + 1
    print("--- 行 %d 附近 ---" % ln)
    for k in range(max(0, ln - 6), min(len(lines), ln + 3)):
        print("  %4d| %s" % (k + 1, lines[k]))
