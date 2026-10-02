package com.potatost.mod.client.particle;

import com.potatost.mod.client.VoidLens;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;

/**
 * 软光斑：**带初速度**（内落流会把它往奇点送），边走边缩小、变淡 —— 像被吸进去的光。
 *
 * <p>0.14 ZF174：本工程第一批自定义粒子。共同点：
 * ① 全亮（{@code getLightColor} 拉满）—— 黑洞要的就是"自己在暗里发光"；
 * ② 不受物理影响（{@code hasPhysics = false}）⇒ 不会被地形挤掉；
 * ③ 走 {@code PARTICLE_SHEET_TRANSLUCENT} ⇒ 贴图的 alpha 生效（软边靠它）。</p>
 */
public class VoidGlowParticle extends TextureSheetParticle {

    protected VoidGlowParticle(ClientLevel level, double x, double y, double z, SpriteSet sprites) {
        super(level, x, y, z);
        this.setSprite(sprites.get(this.random));
        this.hasPhysics = false;
        this.gravity = 0.0F;
        this.friction = 0.96F;
        this.lifetime = 18 + this.random.nextInt(10);
        this.quadSize = 0.35F + this.random.nextFloat() * 0.45F;
        this.xd = xd; this.yd = yd; this.zd = zd;
    }

    @Override
    public int getLightColor(float partialTick) {
        return 0xF000F0;   // 全亮
    }

    @Override
    public ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_TRANSLUCENT;
    }

    /** 客户端注册用的 provider（{@code RegisterParticleProvidersEvent} 里挂）。 */
    public record Provider(SpriteSet sprites) implements ParticleProvider<SimpleParticleType> {
        @Override
        public net.minecraft.client.particle.Particle createParticle(SimpleParticleType type,
                ClientLevel level, double x, double y, double z, double xd, double yd, double zd) {
            return new VoidGlowParticle(level, x, y, z, this.sprites);
        }
    }
}
