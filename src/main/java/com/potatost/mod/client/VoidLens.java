package com.potatost.mod.client;

import java.util.ArrayList;
import java.util.List;

import com.potatost.mod.ModParticles;

import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterParticleProvidersEvent;
import net.neoforged.neoforge.client.event.ViewportEvent;

import com.potatost.mod.client.particle.VoidCoreParticle;
import com.potatost.mod.client.particle.VoidGlowParticle;
import com.potatost.mod.client.particle.VoidStreakParticle;

/**
 * 黑洞的**客户端观感**（0.14 ZF174）：粒子 provider + 「一点点屏幕扭曲」。
 *
 * <h2>屏幕扭曲为什么不用 shader</h2>
 * <p>真正的引力透镜要写 shader（GLSL + 后处理链），而我**看不到画面**、没法迭代调参 ——
 * 瞎上大概率是"一片糊"或者直接崩客户端。所以本轮走两条**零风险**的路，
 * 合起来已经很像"空间被扭了"：</p>
 * <ol>
 *   <li><b>相机侧倾 + FOV 抽吸</b>（{@link ViewportEvent.ComputeCameraAngles} /
 *       {@link ViewportEvent.ComputeFov}）：靠近黑洞时视角轻微打滚、视野被"吸"一下；</li>
 *   <li><b>服务端给近处玩家上原版 {@code DARKNESS}</b>（见 {@code BlackHoleManager}）——
 *       那本来就是"屏幕一阵阵发暗"的原版画效，配心跳音正好，且**完全不动渲染管线**。</li>
 * </ol>
 *
 * <h2>「位置从粒子来」这一招</h2>
 * <p>客户端**不知道**服务端黑洞在哪（本工程没有网络通道）。但 {@code void_core} 粒子
 * <b>只会在黑洞中心生成</b>，而原版粒子只发给 32 格内的玩家 ⇒ 客户端每 tick 都会收到它的位置。
 * 于是 {@link VoidCoreParticle} 建粒子时把坐标记进 {@link #RECENT}，
 * 相机钩子取"最近的、还新鲜的那个" ⇒ <b>天然按距离生效</b>，一行网络代码都不用写。</p>
 */
@EventBusSubscriber(modid = com.potatost.mod.PotatoST.MODID, value = Dist.CLIENT)
public final class VoidLens {

    /** 最近见到的 void_core 位置：{x, y, z, 客户端 tick}。 */
    private static final List<double[]> RECENT = new ArrayList<>();

    /** 粒子存活期（tick）：超过就当"那个黑洞没了"。 */
    private static final int FRESH_TICKS = 30;
    /** 超过这个距离就不扭（与粒子可见范围同量级）。 */
    private static final double MAX_DIST = 34.0D;

    private VoidLens() {
    }

    /** 由 {@link VoidCoreParticle} 的构造函数调（客户端每颗粒子都会来一次）。 */
    public static void note(double x, double y, double z) {
        long now = Minecraft.getInstance().level == null ? 0L
                : Minecraft.getInstance().level.getGameTime();
        RECENT.add(new double[]{x, y, z, now});
        if (RECENT.size() > 64) {
            RECENT.subList(0, RECENT.size() - 64).clear();
        }
    }

    /** 离相机最近的那个"新鲜"黑洞中心；没有就返回 null。 */
    private static Vec3 nearest() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return null;
        }
        long now = mc.level.getGameTime();
        Vec3 eye = mc.player.getEyePosition();
        Vec3 best = null;
        double bestD = MAX_DIST;
        for (double[] r : RECENT) {
            if (now - (long) r[3] > FRESH_TICKS) {
                continue;
            }
            Vec3 p = new Vec3(r[0], r[1], r[2]);
            double d = p.distanceTo(eye);
            if (d < bestD) {
                bestD = d;
                best = p;
            }
        }
        return best;
    }

    /** 0 = 远（无效果）→ 1 = 贴脸。 */
    private static float strength() {
        Vec3 p = nearest();
        if (p == null) {
            return 0.0F;
        }
        Minecraft mc = Minecraft.getInstance();
        double d = p.distanceTo(mc.player.getEyePosition());
        return (float) Mth.clamp(1.0D - d / MAX_DIST, 0.0D, 1.0D);
    }

    /** 相机侧倾：一圈很慢的打滚（像被引力拧了一下）。 */
    @SubscribeEvent
    public static void onCameraAngles(ViewportEvent.ComputeCameraAngles event) {
        float s = strength();
        if (s <= 0.01F) {
            return;
        }
        float t = (float) (event.getPartialTick()
                + Minecraft.getInstance().level.getGameTime() * 0.02D);
        // 幅度压得很小（最多 ~3.2 度）：这是"扭曲一点点"，不是把人转晕
        event.setRoll(event.getRoll() + (float) Math.sin(t * 1.7D) * 3.2F * s);
        event.setPitch(event.getPitch() + (float) Math.sin(t * 2.3D) * 1.1F * s);
    }

    /** FOV 抽吸：靠近时视野被"吸"宽一点点，离开时收回。 */
    @SubscribeEvent
    public static void onComputeFov(ViewportEvent.ComputeFov event) {
        if (!event.usedConfiguredFov()) {
            return;
        }
        float s = strength();
        if (s <= 0.01F) {
            return;
        }
        event.setFOV(event.getFOV() + 9.0F * s);
    }

    /** 粒子外观注册（**少这一步粒子就看不见**）。 */
    @SubscribeEvent
    public static void onRegisterParticleProviders(RegisterParticleProvidersEvent event) {
        event.registerSpriteSet(ModParticles.VOID_CORE.get(), VoidCoreParticle.Provider::new);
        event.registerSpriteSet(ModParticles.VOID_GLOW.get(), VoidGlowParticle.Provider::new);
        event.registerSpriteSet(ModParticles.VOID_STREAK.get(), VoidStreakParticle.Provider::new);
    }
}
