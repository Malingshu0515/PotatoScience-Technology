package com.potatost.mod.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.potatost.mod.PotatoST;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/**
 * 发电机的"手持/背包"渲染器：与世界里 GeneratorRenderer 复用同一个 GeneratorModel，
 * 姿势（第一/第三人称、GUI、地面、展示框）由物品模型 JSON 的 display 段自动应用。
 * 注意：整个 mod 只应有一个 BEWLR 实例（官方文档要求），这里用懒加载单例。
 */
public class GeneratorItemRenderer extends BlockEntityWithoutLevelRenderer {

    private static final ResourceLocation TEXTURE =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "textures/block/generator.png");

    private static GeneratorItemRenderer instance;

    private final GeneratorModel model;

    private GeneratorItemRenderer() {
        super(Minecraft.getInstance().getBlockEntityRenderDispatcher(), Minecraft.getInstance().getEntityModels());
        this.model = new GeneratorModel(GeneratorModel.createBodyLayer().bakeRoot());
    }

    /** 懒加载单例（getCustomRenderer 只在渲染时被调用，那时 Minecraft 实例一定已就绪） */
    public static GeneratorItemRenderer getInstance() {
        if (instance == null) {
            instance = new GeneratorItemRenderer();
        }
        return instance;
    }

    @Override
    public void renderByItem(ItemStack stack, ItemDisplayContext context, PoseStack poseStack,
                             MultiBufferSource buffer, int packedLight, int packedOverlay) {
        poseStack.pushPose();
        // 与世界渲染同样的落地偏移（模型 pivot=16，自带落地；XZ 居中）
        poseStack.translate(0.5D, 0.0D, 0.5D);
        VertexConsumer consumer = buffer.getBuffer(RenderType.entityCutoutNoCull(TEXTURE));
        // 手里/图标里的转子保持静止（角度 0）；想让它在手里也转，把 0.0F 换成按时间的角度即可
        this.model.render(poseStack, consumer, packedLight, packedOverlay, 0.0F);
        poseStack.popPose();
    }
}