package com.potatost.mod.client;

import com.potatost.mod.ShockwaveNetworking;

import net.minecraft.client.Minecraft;

/**
 * 冲击波的**客户端**状态（0.11 ZF133）。
 *
 * <p>只保存"起手那一刻的服务器世界时间 + 起点 + 主轴方向"这几个数，
 * 当前推进到哪一格由客户端拿 {@code level.getGameTime()} 现算 ——
 * 与 ZF114 的倒计时同一套思路（整场 10 秒只收 1 个包）。</p>
 *
 * <p>防脏数据：剩余时间超过 {@link #MAX_SHOW_TICKS} 的（说明是上一个世界留下的旧包）
 * 直接忽略。</p>
 */
public final class ShockwaveClientState {

    /** 最多画多久（服务端 10 秒的闲置上限 + 一点余量）。 */
    public static final int MAX_SHOW_TICKS = 20 * 14;

    /** 一波的起点与方向。 */
    public static final class Wave {
        public final double x;
        public final double y;
        public final double z;
        public final boolean alongX;
        public final int sign;
        public final long startTick;

        Wave(double x, double y, double z, boolean alongX, int sign, long startTick) {
            this.x = x;
            this.y = y;
            this.z = z;
            this.alongX = alongX;
            this.sign = sign;
            this.startTick = startTick;
        }
    }

    /** 同时最多画几波（防止包刷屏；正常玩法里一道波 10 秒就散了）。 */
    private static final int MAX_WAVES = 8;

    private static final java.util.List<Wave> WAVES = new java.util.ArrayList<>();

    private ShockwaveClientState() {
    }

    public static void accept(ShockwaveNetworking.ShockwavePayload payload) {
        WAVES.add(new Wave(payload.x(), payload.y(), payload.z(),
                payload.alongX(), payload.sign(), payload.startTick()));
        while (WAVES.size() > MAX_WAVES) {
            WAVES.remove(0);
        }
    }

    /**
     * 取当前还"活着"的波（过期的顺手清掉）。
     *
     * <p>返回内部列表本身（不复制）—— 这是每帧都调的渲染路径，复制一份纯属浪费；
     * 调用方只读。</p>
     */
    public static java.util.List<Wave> liveWaves() {
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.level == null || WAVES.isEmpty()) {
            return java.util.Collections.emptyList();
        }
        long now = minecraft.level.getGameTime();
        WAVES.removeIf(w -> {
            long age = now - w.startTick;
            return age < 0L || age > MAX_SHOW_TICKS;
        });
        return WAVES;
    }

    /** 收到新起点时清空（换世界 / 断线重连用）。 */
    public static void clear() {
        WAVES.clear();
    }
}
