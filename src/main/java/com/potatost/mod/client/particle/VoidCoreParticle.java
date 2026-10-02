package com.potatost.mod.client.particle;

import com.potatost.mod.client.VoidLens;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;

/**
 * 事件视界本体：**一大颗**黑盘（quadSize 随寿命微涨），几乎不动 —— 它就是「洞」本身。
 *
 * <p>0.14 ZF174：本工程第一批自定义粒子。共同点：
 * ① 全亮（{@code getLightColor} 拉满）—— 黑洞要的就是"自己在暗里发光"；
 * ② 不受物理影响（{@code hasPhysics = false}）⇒ 不会被地形挤掉；
 * ③ 走 {@code PARTICLE_SHEET_TRANSLUCENT} ⇒ 贴图的 alpha 生效（软边靠它）。</p>
 */
public class VoidCoreParticle extends TextureSheetParticle {

    protected VoidCoreParticle(ClientLevel level, double x, double y, double z, SpriteSet sprites) {
        super(level, x, y, z);
        // 0.14 ZF174：把「我在这儿」报给相机钩子（黑洞位置只从粒子来，见 VoidLens）
        VoidLens.note(x, y, z);
        this.setSprite(sprites.get(this.random));
        this.hasPhysics = false;
        this.gravity = 0.0F;
        this.friction = 0.96F;
        this.lifetime = 14 + this.random.nextInt(6);
        this.quadSize = 1.6F + this.random.nextFloat() * 0.5F;
        this.alpha = 1.0F;
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
            return new VoidCoreParticle(level, x, y, z, this.sprites);
        }
    }
}
