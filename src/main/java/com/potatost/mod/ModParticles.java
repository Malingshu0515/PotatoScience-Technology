package com.potatost.mod;

import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.Registries;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 本模组的粒子（0.14 ZF174，第一组自定义粒子）。
 *
 * <p>三个都是 {@link SimpleParticleType}：没有额外参数、服务端只管在哪儿生成，
 * 长什么样全由客户端的 provider 说了算（见 {@code client/particle/}）。</p>
 *
 * <p>⚠ 注册分两半：**类型**在这里（两边都要有），**外观**在 {@code PotatoSTClient}
 * 的 {@code RegisterParticleProvidersEvent} 里 —— 少任何一半都会在客户端报
 * "unknown particle" 或干脆看不见（本工程第一次做，写清楚免得下一轮踩）。</p>
 */
public final class ModParticles {

    public static final DeferredRegister<ParticleType<?>> PARTICLES =
            DeferredRegister.create(Registries.PARTICLE_TYPE, PotatoST.MODID);

    /** 事件视界本体：中间全黑 + 一圈细亮边（原版没有"黑粒子"，这颗是黑洞像不像的关键）。 */
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> VOID_CORE =
            PARTICLES.register("void_core", () -> new SimpleParticleType(false));

    /** 软光斑：光子环与吸积盘用（比原版那些硬亮点柔和得多）。 */
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> VOID_GLOW =
            PARTICLES.register("void_glow", () -> new SimpleParticleType(false));

    /** 拖尾：内落流用（按速度方向旋转 ⇒ 物质被拉成丝）。 */
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> VOID_STREAK =
            PARTICLES.register("void_streak", () -> new SimpleParticleType(false));

    private ModParticles() {
    }
}
