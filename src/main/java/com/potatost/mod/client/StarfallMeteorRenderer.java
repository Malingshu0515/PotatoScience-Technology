package com.potatost.mod.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.potatost.mod.StarfallMeteorEntity;

import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.block.BlockRenderDispatcher;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Blocks;

/**
 * 陨石的渲染器（0.11 ZF114）—— 本工程**第一个实体渲染器**。
 *
 * <p>画法：把一块<b>岩浆方块</b>放大 1.6 倍、绕 Y 轴每 tick 转 12°、再绕 X 轴歪 22°，
 * 用"全亮"光照（{@code 0xF000F0}）—— 于是它自带岩浆的发光纹理与动画，
 * 在夜里从 200 格高空掉下来是一条旋转的橙色火球。零新增贴图资源。</p>
 *
 * <p>{@code getTextureLocation} 是被父类强制要求的抽象方法，但我们走的是
 * {@code BlockRenderDispatcher}（方块模型自带贴图），它返回的路径**不会**被使用；
 * 给一个一定存在的原版路径，纯粹是为了万一有人改成 {@code super.render} 时不 NPE。</p>
 */
public class StarfallMeteorRenderer extends EntityRenderer<StarfallMeteorEntity> {

    /** 尺寸与 {@code ModEntities} 的 {@code sized(1.6F, 1.6F)} 必须一起改。 */
    private static final float SCALE = 1.6F;

    private static final ResourceLocation UNUSED_TEXTURE =
            ResourceLocation.withDefaultNamespace("textures/block/magma.png");

    private final BlockRenderDispatcher blockRenderer;

    public StarfallMeteorRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.blockRenderer = context.getBlockRenderDispatcher();
    }

    @Override
    public ResourceLocation getTextureLocation(StarfallMeteorEntity entity) {
        return UNUSED_TEXTURE;
    }

    @Override
    public void render(StarfallMeteorEntity entity, float entityYaw, float partialTick, PoseStack pose,
                       MultiBufferSource buffer, int packedLight) {
        pose.pushPose();
        pose.translate(0.0D, 0.8D, 0.0D);
        pose.mulPose(Axis.YP.rotationDegrees((entity.tickCount + partialTick) * 12.0F));
        pose.mulPose(Axis.XP.rotationDegrees(22.0F));
        pose.scale(SCALE, SCALE, SCALE);
        pose.translate(-0.5D, -0.5D, -0.5D);
        this.blockRenderer.renderSingleBlock(Blocks.MAGMA_BLOCK.defaultBlockState(), pose, buffer,
                0xF000F0, OverlayTexture.NO_OVERLAY);
        pose.popPose();
        super.render(entity, entityYaw, partialTick, pose, buffer, packedLight);
    }
}
