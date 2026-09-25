package com.potatost.mod.client;

import com.potatost.mod.StarfallNetworking;

import net.minecraft.client.Minecraft;

/**
 * 星轨坠倒计时的**客户端**状态（0.11 ZF114）。
 *
 * <p>只保存一个截止时刻 {@code endTick}：剩余秒数由"客户端世界时间"现算
 * （客户端与服务器的世界时间同步推进），所以整场倒计时只需要 4 个包，
 * 而不是每 tick 一个包。</p>
 *
 * <p>防脏数据三件事：① 没有世界时一律当作没有倒计时；② 剩余时间超过总时长
 * （说明 {@code endTick} 是上一个世界留下的）直接忽略；③ 收到"下落中"时，
 * 即使没有后续包，最多 12 秒后 HUD 自己消失。</p>
 */
public final class StarfallClientState {

    /** 「陨石下落中」这行字最多显示多久（防止包丢了一直挂在屏幕上）。 */
    private static final int FALLING_SHOW_TICKS = 20 * 12;

    /** 倒计时上限（比服务端的 600 略宽，只用来识别"上个世界的脏数据"）。 */
    private static final int MAX_COUNTDOWN_TICKS = 20 * 40;

    private static long endTick = Long.MIN_VALUE;
    private static long fallingUntilTick = Long.MIN_VALUE;
    private static int targetX;
    private static int targetY;
    private static int targetZ;

    public static void accept(StarfallNetworking.StarfallPayload payload) {
        switch (payload.phase()) {
            case StarfallNetworking.PHASE_START -> {
                endTick = payload.endTick();
                fallingUntilTick = Long.MIN_VALUE;
                targetX = payload.x();
                targetY = payload.y();
                targetZ = payload.z();
            }
            case StarfallNetworking.PHASE_FALLING -> {
                endTick = Long.MIN_VALUE;
                fallingUntilTick = now() + FALLING_SHOW_TICKS;
            }
            default -> clear();
        }
    }

    public static boolean isCounting() {
        if (endTick == Long.MIN_VALUE || !hasLevel()) {
            return false;
        }
        long remain = endTick - now();
        return remain > -20L && remain <= MAX_COUNTDOWN_TICKS;
    }

    public static int remainTicks() {
        return (int) Math.max(0L, endTick - now());
    }

    public static boolean isFalling() {
        return fallingUntilTick != Long.MIN_VALUE && hasLevel() && now() < fallingUntilTick;
    }

    /** 落点坐标（给 HUD 备用/调试；当前 UI 只画倒计时，不画坐标）。 */
    public static int targetX() {
        return targetX;
    }

    public static int targetY() {
        return targetY;
    }

    public static int targetZ() {
        return targetZ;
    }

    public static void clear() {
        endTick = Long.MIN_VALUE;
        fallingUntilTick = Long.MIN_VALUE;
    }

    private static boolean hasLevel() {
        return Minecraft.getInstance().level != null;
    }

    private static long now() {
        Minecraft minecraft = Minecraft.getInstance();
        return minecraft.level == null ? Long.MIN_VALUE : minecraft.level.getGameTime();
    }

    private StarfallClientState() {
    }
}
