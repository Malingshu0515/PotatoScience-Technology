# -*- coding: utf-8 -*-
"""_zf134_manager3.py —— 把 `spawnParticles` 也一起换掉（上一次的 assert 正确地拦住了半成品）

上一次：四处切片都成功，但 `spawnParticles` 还在用 `wave.alongX` / `mainCoord(...)`，
复核断言当场拦住（**没有写盘** —— 这正是"写完先复核再落盘"该有的样子）。
这次把 `spawnParticles` 整段一起换。
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

P_START = "    /** 每 2 tick 一批粒子：前缘一道弧 + 上下两条星屑（全走服务端标准粒子包）。 */"
P_END = "    /** 当前还有几道波（探针/验证用，不参与玩法）。 */"

NEW_P = '''    /**
     * 每 2 tick 一批粒子：前缘一道弧 + 上下两条星屑（全走服务端标准粒子包）。
     *
     * <p>采样线与 {@code tick()} **用同一套公式**（前缘 + 法线 × 横向偏移）——
     * 这样"斜着放"时粒子也跟着斜，视觉与破坏范围对得上。</p>
     */
    private static void spawnParticles(Wave wave, double originX, double originZ, int oy, boolean launch) {
        double frontX = wave.frontX(originX);
        double frontZ = wave.frontZ(originZ);
        double perpX = -wave.dirZ;
        double perpZ = wave.dirX;
        boolean inEnd = wave.level.dimension() == Level.END;
        boolean anyWood = false;
        BlockState woodState = null;
        double woodX = 0.0D;
        double woodZ = 0.0D;

        for (int lateral = 0; lateral < WIDTH; lateral++) {
            double lat = lateral - HALF_WIDTH;
            double px = frontX + perpX * lat;
            double pz = frontZ + perpZ * lat;
            double py = oy + 0.5D;

            // 前缘：横扫粒子（原版剑气那个）
            wave.level.sendParticles(ParticleTypes.SWEEP_ATTACK, px, py + 0.6D, pz, 1, 0.0D, 0.0D, 0.0D, 0.0D);
            // 星屑：上下各一颗（"星璨"的那点意思）
            ParticleOptions star = (lateral % 3 == 0 && inEnd) ? ParticleTypes.END_ROD : ParticleTypes.CRIT;
            wave.level.sendParticles(star, px, py + 0.2D, pz, 1, 0.15D, 0.15D, 0.15D, 0.0D);
            wave.level.sendParticles(ParticleTypes.END_ROD, px, py + HEIGHT - 0.3D, pz, 1, 0.1D, 0.1D, 0.1D, 0.0D);
            if (launch || lateral % 2 == 0) {
                wave.level.sendParticles(ParticleTypes.CLOUD, px, py + 0.05D, pz, 1, 0.2D, 0.05D, 0.2D, 0.01D);
            }
        }

        // 拆到木头时补一点木屑（视觉上"这排树被啃掉了"）——
        // ⚠ 沿 6 条采样线找**第一处**木头：斜着走时"前缘正中那一格"未必有东西
        if (!launch) {
            for (int lateral = 0; lateral < WIDTH && !anyWood; lateral++) {
                double lat = lateral - HALF_WIDTH;
                BlockPos probe = new BlockPos(
                        (int) Math.floor(frontX + perpX * lat), oy + 1,
                        (int) Math.floor(frontZ + perpZ * lat));
                BlockState state = wave.level.getBlockState(probe);
                if (isChoppable(state)) {
                    anyWood = true;
                    woodState = state;
                    woodX = probe.getX() + 0.5D;
                    woodZ = probe.getZ() + 0.5D;
                }
            }
            if (anyWood) {
                wave.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, woodState),
                        woodX, oy + 1.5D, woodZ, 6, 0.4D, 0.4D, 0.4D, 0.05D);
            }
        }
    }

'''


def main():
    s = io.open(M, encoding="utf-8").read()
    assert s.count(P_START) == 1, "起点 %d 次" % s.count(P_START)
    assert s.count(P_END) == 1, "终点 %d 次" % s.count(P_END)
    i = s.index(P_START)
    j = s.index(P_END)
    assert j > i
    s = s[:i] + NEW_P + s[j:]
    print("[OK ] spawnParticles 整段已换（%d -> %d 字符）" % (j - i, len(NEW_P)))

    bad = [k for k in ("alongX", "mainCoord(", "int main =", "wave.sign") if k in s]
    assert not bad, "还残留旧结构：%s" % bad
    print("[OK ] 旧字段全清")

    io.open(M, "w", encoding="utf-8", newline="\n").write(s)
    print("ShockwaveManager 已完整改成任意角度")


main()
