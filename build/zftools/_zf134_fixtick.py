# -*- coding: utf-8 -*-
"""_zf134_fixtick.py —— 补两处：粒子调用签名 + 被我切坏的 if/else 结构

① 第 308 行还在用旧签名 `spawnParticles(wave, owner, ox, oy, oz, false)`
   —— 它在我切掉的"采样头"**之后**，所以没被那一刀覆盖（我该顺手一起改的）。
② 第 311 起：`if (broke) {...}` 的 else 分支被我切断了 ——
   原来的结构是 `if (broke) {...} else if (++sinceBreak >= IDLE) { return false; }`，
   我切到 `} else if (...)` 之前，于是 `else if` 那半截留在了新内容后面。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

FIXES = [
    # ① 粒子调用
    ("            spawnParticles(wave, owner, ox, oy, oz, false);",
     "            spawnParticles(wave, owner.getX(), owner.getZ(), oy, false);"),
    # ② 断掉的 if/else：把新音效块 + 残留的 else-if 接回去
    ("""        if (broke) {
            wave.sinceBreak = 0;
            wave.level.playSound(null, frontX, oy + 1.0D, frontZ,
                    SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 0.7F, 0.7F);

            return false;    // 用户第 2 条：10 秒没碰到原木 ⇒ 消失""",
     """        if (broke) {
            wave.sinceBreak = 0;
            wave.level.playSound(null, frontX, oy + 1.0D, frontZ,
                    SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 0.7F, 0.7F);
        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {
            return false;    // 用户第 2 条：10 秒没碰到原木 ⇒ 消失"""),
]


def main():
    s = io.open(M, encoding="utf-8").read()
    for i, (a, b) in enumerate(FIXES):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段" % (i + 1))
    io.open(M, "w", encoding="utf-8", newline="\n").write(s)
    print("已写盘")


main()
