# -*- coding: utf-8 -*-
u"""_zf174_wire.py —— ZF174 接线：粒子注册（两侧）/ 相机侧倾 + FOV 抽吸 / 黑洞里用上自定义粒子 + 近处给 DARKNESS"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
FAILS = []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        FAILS.append(label)


def read(p):
    return io.open(p, encoding="utf-8").read()


def w(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def main():
    # ---------- ① 客户端：VoidLens（相机扭曲的"位置从粒子来"那一招）+ provider ----------
    lens = u'''package com.potatost.mod.client;

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
'''
    w(os.path.join(MOD, r"client\VoidLens.java"), lens)
    check(u"client/VoidLens.java 已写出", os.path.exists(os.path.join(MOD, r"client\VoidLens.java")))

    # VoidCoreParticle 记坐标
    p = os.path.join(MOD, r"client\particle\VoidCoreParticle.java")
    t = read(p)
    t = t.replace(u"        this.setSprite(sprites.get(this.random));",
                  u"        // 0.14 ZF174：把「我在这儿」报给相机钩子（黑洞位置只从粒子来，见 VoidLens）\n"
                  u"        VoidLens.note(x, y, z);\n"
                  u"        this.setSprite(sprites.get(this.random));")
    w(p, t)
    check(u"VoidCoreParticle 已上报坐标", u"VoidLens.note" in read(p))

    # ---------- ② 服务端：注册粒子类型 ----------
    main_java = os.path.join(MOD, "PotatoST.java")
    t = read(main_java)
    if u"ModParticles.PARTICLES.register" in t:
        print(u"  [幂等] 粒子类型已注册")
    else:
        m = re.search(u"(\\s*)(ModBlocks\\.[A-Z_]+\\.[A-Za-z]*?register\\(modBus\\);)", t)
        if not m:
            m = re.search(u"(\\s*)([A-Za-z]+\\.[A-Z_]+\\.[A-Za-z]*register\\(modBus\\);[^\\n]*)", t)
        if not m:
            check(u"找到 modBus 注册点", False)
        else:
            ins = (u"\n%s// 0.14 ZF174：本模组第一组自定义粒子（黑洞用）\n%sModParticles.PARTICLES.register(modBus);"
                   % (m.group(1), m.group(1)))
            t = t[:m.end(1)] + ins + t[m.end(1):]
            w(main_java, t)
            check(u"粒子类型已注册到 modBus", u"ModParticles.PARTICLES.register(modBus)" in read(main_java))

    # ---------- ③ 黑洞：用上自定义粒子 + 近处给 DARKNESS ----------
    bh = os.path.join(MOD, "BlackHoleManager.java")
    t = read(bh)
    repl = [
        # 事件视界：每 tick 一颗核心粒子（它同时是"相机扭曲"的位置源）
        (u'''        // ── 光子环：贴着急速旋转的亮环（每 tick、24 点、切向速度）── 黑洞的"招牌" ──
        ring(level, ParticleTypes.END_ROD, cx, cy, cz, 2.35D, 24, spin * 2.2D, 0.0D, 0.22D);''',
         u'''        // ── 事件视界**本体**（0.14 ZF174 自定义粒子）：一颗大黑盘，中间真的黑 ──
        //    它只在这里生成 ⇒ 客户端靠它反推黑洞位置（相机扭曲那点事，见 client/VoidLens）
        fx(level, ModParticles.VOID_CORE.get(), cx, cy, cz, 1, 0.0D, 0.0D, 0.0D, 0.0D);

        // ── 光子环：贴着急速旋转的亮环（每 tick、24 点、切向速度）── 黑洞的"招牌" ──
        ring(level, ModParticles.VOID_GLOW.get(), cx, cy, cz, 2.35D, 24, spin * 2.2D, 0.0D, 0.22D);'''),
        # 内落流换成拖尾粒子
        (u'''                fx(level, ParticleTypes.PORTAL, cx + Math.cos(a) * r, y, cz + Math.sin(a) * r,
                        1, -Math.cos(a) * 0.5D, -0.05D, -Math.sin(a) * 0.5D, 0.5D);''',
         u'''                fx(level, ModParticles.VOID_STREAK.get(), cx + Math.cos(a) * r, y,
                        cz + Math.sin(a) * r, 1, -Math.cos(a) * 0.5D, -0.05D, -Math.sin(a) * 0.5D, 0.5D);'''),
        # 吸积盘三层里的两层换成软光斑
        (u'''            disk(level, ParticleTypes.SOUL_FIRE_FLAME, cx, cy, cz, 4.5D, 26, spin * 0.8D, 0.22D, 0.18D);''',
         u'''            disk(level, ModParticles.VOID_GLOW.get(), cx, cy, cz, 4.5D, 26, spin * 0.8D, 0.22D, 0.18D);'''),
        (u'''            disk(level, ParticleTypes.END_ROD, cx, cy, cz, 6.5D, 30, -spin * 0.55D, -0.18D, 0.16D);''',
         u'''            disk(level, ModParticles.VOID_GLOW.get(), cx, cy, cz, 6.5D, 30, -spin * 0.55D, -0.18D, 0.16D);'''),
        # 近处玩家：原版 DARKNESS（"屏幕一阵阵发暗"），这就是"一点点屏幕扭曲"的服务端那半
        (u'''            double dist = e.position().distanceTo(hole.center);''',
         u'''            double dist = e.position().distanceTo(hole.center);
            // 0.14 ZF174：近处的**玩家**额外吃一层原版 DARKNESS —— 那是现成的"屏幕发暗"画效
            //   （配心跳音正合适），且完全不碰渲染管线。15 格内、每 20 tick 续一次。
            if (e instanceof Player dp && dist <= 15.0D && hole.age % 20 == 0) {
                dp.addEffect(new net.minecraft.world.effect.MobEffectInstance(
                        net.minecraft.world.effect.MobEffects.DARKNESS, 60, 0, false, false, false));
            }'''),
    ] + [
        (u"import net.minecraft.world.item.ItemStack;",
         u"import com.potatost.mod.ModParticles;\nimport net.minecraft.world.item.ItemStack;"),
    ]
    for a, b in repl:
        if a not in t:
            check(u"锚点没找到：%s" % a.strip()[:48], False)
            continue
        t = t.replace(a, b, 1)
    w(bh, t)
    check(u"黑洞已用上三个自定义粒子", u"ModParticles.VOID_CORE.get()" in read(bh)
          and u"ModParticles.VOID_STREAK.get()" in read(bh))
    check(u"近处玩家上 DARKNESS", u"MobEffects.DARKNESS" in read(bh))

    print(u"失败项 = %d" % len(FAILS))
    for f in FAILS:
        print(u"  !! " + f)
    return 1 if FAILS else 0


if __name__ == u"__main__":
    sys.exit(main())
