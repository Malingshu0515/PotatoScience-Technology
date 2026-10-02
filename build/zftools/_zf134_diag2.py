# -*- coding: utf-8 -*-
"""_zf134_diag2.py —— 逐个锚点验证：起止行在盘上各出现几次、位置在哪（不再靠断言猜）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

ANCHORS = [
    "    /** 一道冲击波。字段全是**值**（Level 引用只在服务端活着时用，玩家一退就丢）。 */",
    "        /** 主轴坐标（当前采样位置）。 */",
    "    public static boolean fire(ServerPlayer player, ItemStack axe) {",
    "    /** 推进所有冲击波；由 {@code PotatoST} 挂在 {@code ServerTickEvent.Post} 上。 */",
    "        int ox = owner.getBlockX();",
    "                BlockState state = wave.level.getBlockState(pos);",
    "        if (broke) {",
    "        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {",
    "    /** 每 2 tick 一批粒子：前缘一道弧 + 上下两条星屑（全走服务端标准粒子包）。 */",
    "    /** 当前还有几道波（探针/验证用，不参与玩法）。 */",
]

s = io.open(M, encoding="utf-8").read()
print("文件长度", len(s), "行数", s.count("\n"))
for a in ANCHORS:
    print("%2d 次  %s" % (s.count(a), a.strip()[:70]))
