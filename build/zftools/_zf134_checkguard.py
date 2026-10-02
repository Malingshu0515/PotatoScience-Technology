# -*- coding: utf-8 -*-
"""_zf134_checkguard.py —— 直接复刻 manager5 的"剥注释"复核，看它到底数到了什么"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

s = io.open(M, encoding="utf-8").read()
# 用占位符替换五段（与 manager5 同样的位置）
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

def strip_comments(src):
    out = re.sub(r"/\*[\s\S]*?\*/", "", src)
    out = re.sub(r"//[^\n]*", "", out)
    return out

code = strip_comments(s)
print("剥注释后：")
for k in ("alongX", "mainCoord", "int main =", "wave.sign"):
    print("   %-12s %d 次" % (k, code.count(k)))
print("原始（未剥）里 mainCoord =", s.count("mainCoord"))
# 看看未被剥掉的 mainCoord 上下文
for m in re.finditer("mainCoord", code):
    p = m.start()
    print("   ...%s..." % code[max(0, p - 70):p + 50].replace("\n", " / ")[:150])
