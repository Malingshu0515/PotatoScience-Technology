# -*- coding: utf-8 -*-
"""_zf134_probe_loop.py —— 逐步打印：每次替换后 alongX 还剩几次（定位那个"1 次"）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

JOBS = [
    ("    /** 一道冲击波。字段全是**值**", "        /** 主轴坐标（当前采样位置）。 */"),
    ("    public static boolean fire(ServerPlayer player", "    /** 推进所有冲击波；由"),
    ("        int ox = owner.getBlockX();", "                BlockState state = wave.level.getBlockState(pos);"),
    ("        if (broke) {", "        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {"),
    ("    /** 每 2 tick 一批粒子", "    /** 当前还有几道波"),
]

s = io.open(M, encoding="utf-8").read()
print("起点 alongX =", s.count("alongX"))
for k, (start, end) in enumerate(JOBS):
    i, j = s.index(start), s.index(end)
    seg = s[i:j]
    print("job %d: 段长 %d，段内 alongX=%d mainCoord=%d" %
          (k, len(seg), seg.count("alongX"), seg.count("mainCoord")))
    s = s[:i] + "/*CUT*/" + s[j:]
    print("     替换后全文 alongX =", s.count("alongX"))

print("--- 剩下 alongX 的上下文 ---")
pos = 0
while True:
    p = s.find("alongX", pos)
    if p < 0:
        break
    print("   ...%s..." % s[max(0, p - 60):p + 40].replace("\n", " / "))
    pos = p + 1
