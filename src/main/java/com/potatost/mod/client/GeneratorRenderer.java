package com.potatost.mod.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;
import com.potatost.mod.GeneratorBlockEntity;
import com.potatost.mod.ModBlocks;
import com.potatost.mod.PotatoST;

public class GeneratorRenderer implements BlockEntityRenderer<GeneratorBlockEntity> {
    private static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "textures/block/generator.png");
    /** 转速 rad/tick（约 25 tick 一圈） */
    private static final float ROTOR_SPEED = 0.25F;

    private final GeneratorModel model;

    public GeneratorRenderer(BlockEntityRendererProvider.Context context) {
        this.model = new GeneratorModel(GeneratorModel.createBodyLayer().bakeRoot());
    }

    @Override
    public void render(GeneratorBlockEntity generator, float partialTick, PoseStack poseStack,
                       MultiBufferSource buffer, int packedLight, int packedOverlay) {
        Level level = generator.getLevel();
        if (level == null) return;
        // 挖掉方块后的残留帧守卫（沿用端子渲染器写法）
        if (!level.getBlockState(generator.getBlockPos()).is(ModBlocks.GENERATOR.get())) return;

        poseStack.pushPose();
        // BER 坐标原点在方块角上，模型 XZ 占整格 -> 居中
        poseStack.translate(0.5D, 0.0D, 0.5D);
        // 接受动力（正在转化）时旋转；用 gameTime + partialTick 保证平滑
        float rotorAngle = generator.isActive() ? (level.getGameTime() + partialTick) * ROTOR_SPEED : 0.0F;
        VertexConsumer consumer = buffer.getBuffer(RenderType.entityCutoutNoCull(TEXTURE));
        // 模型主体在 y=8..24（顶端伸进上面半格），用上方方块光照
        int light = LevelRenderer.getLightColor(level, generator.getBlockPos().above());
        model.render(poseStack, consumer, light, packedOverlay, rotorAngle);
        poseStack.popPose();
    }
}