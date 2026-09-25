package com.potatost.mod;

/**
 * 共享储能池的<b>纯计算</b>（0.10 ZF24 提取）。
 *
 * <p>为什么单独一个类：太阳能板的"池子"其实只有一件事 ——
 * 把一次 {@code receive}/{@code extract} 摊到若干块各自的缓冲上。
 * 这件事<b>不需要认识 Minecraft</b>（不认识 {@code Level}、不认识 {@code BlockEntity}），
 * 所以把它抽成"对一个 {@code long[]} 做增减"之后，就能<b>用一个 main 方法直接验算</b>
 * —— 见 {@code build/zftools/check/GroupEnergyCheck.java}。
 * 这比"盯着 647 行的方块实体看"靠谱得多，也是本项目第一次让核心逻辑可脱离游戏运行。</p>
 *
 * <p>约定：{@code energies[i]} 是第 i 块的存量，每块的上限都是 {@code perBlock}（= 512）。
 * 两个方法都按<b>下标顺序</b>摊派 —— 顺序本身不重要（总量守恒才是关键），
 * 但固定顺序能让同一份存档每次跑出一样的分布，便于对账。</p>
 *
 * <p>⚠ {@code perBlock} 是 {@code long}：<b>余数一定要在整数域里先乘后除</b>。
 * 若先算 {@code rate / n} 再乘 {@code n}，余数会被丢掉，池子每 tick 少收几点电。</p>
 */
public final class GroupEnergy {

    private GroupEnergy() {
    }

    /** 把 {@code amount} 按顺序往各块里补，返回真正补进去的总量（可能小于 amount —— 池子满了）。 */
    public static long fill(long[] energies, long perBlock, long amount) {
        long left = Math.max(0L, amount);
        long accepted = 0L;
        for (int i = 0; i < energies.length && left > 0L; i++) {
            long space = perBlock - energies[i];
            if (space <= 0L) {
                continue;
            }
            long move = Math.min(left, space);
            energies[i] += move;
            accepted += move;
            left -= move;
        }
        return accepted;
    }

    /** 把 {@code amount} 按顺序从各块里扣，返回真正扣出来的总量（可能小于 amount —— 池子空了）。 */
    public static long drain(long[] energies, long amount) {
        long left = Math.max(0L, amount);
        long taken = 0L;
        for (int i = 0; i < energies.length && left > 0L; i++) {
            long move = Math.min(left, energies[i]);
            if (move <= 0L) {
                continue;
            }
            energies[i] -= move;
            taken += move;
            left -= move;
        }
        return taken;
    }

    /** 池子现有总量（对外 {@code getEnergyStored()} 报的就是它）。 */
    public static long total(long[] energies) {
        long sum = 0L;
        for (long e : energies) {
            sum += e;
        }
        return sum;
    }

    /** 池子容量（对 {@code getMaxEnergyStored()} 报的就是它）。 */
    public static long capacity(int blocks, long perBlock) {
        return (long) Math.max(0, blocks) * perBlock;
    }

    /**
     * 一秒（20 tick）里，组内每块各发到多少 —— <b>先乘后除，余数不丢</b>。
     *
     * <p>例：3 块共 135 FE/t（ZF29 上午档）⇒ {@code 135 * 20 / 3 = 900}；
     * 若写成 {@code (135 / 3) * 20 = 900} 恰好也一样，但换成 20 FE/t 就差出来了：
     * {@code 20 * 20 / 3 = 133} vs {@code (20 / 3) * 20 = 120} —— 后者每秒白丢 13 FE（6.5%）。
     * 所以这一条**先乘后除**的写法不能"看起来等价"就改掉。</p>
     */
    public static long perPanelPerSecond(int totalRate, int blocks) {
        if (blocks <= 0) {
            return 0L;
        }
        return (long) totalRate * 20L / blocks;
    }
}
