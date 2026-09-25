package com.potatost.mod.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.PoseStack.Pose;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import com.potatost.mod.LithiumBatteryBlockEntity;
import com.potatost.mod.ModBlocks;
import com.potatost.mod.PotatoST;

/**
 * 锂电池渲染：每列贴图纵向拉伸，相邻电池面不画 → 显示为一个整体。类似 Create 流体储罐。
 *
 * ★ 光照规则：必须取"面外侧那一格"的光。取方块自己这一格的话，实体方块内部天空光≈0，侧面会全黑
 *   （顶面正常，因为正好取的是上方空气）。这与原版方块模型按面取光的做法一致。
 * ★ 批处理规则：同一个 RenderType 的顶点必须连续写完，之后才允许 getBuffer 下一个 RenderType，
 *   否则旧 VertexConsumer 会因 IllegalStateException: Not building! 崩溃。
 */
public class LithiumBatteryRenderer implements BlockEntityRenderer<LithiumBatteryBlockEntity> {

    private static final ResourceLocation SIDE_TEX =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "textures/block/lithium_battery_side.png");
    private static final ResourceLocation TOP_TEX =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "textures/block/lithium_battery_top.png");

    public LithiumBatteryRenderer(BlockEntityRendererProvider.Context context) {
    }

    @Override
    public void render(LithiumBatteryBlockEntity be, float partialTick, PoseStack poseStack,
                       MultiBufferSource buffer, int packedLight, int packedOverlay) {
        Level level = be.getLevel();
        if (level == null) return;
        BlockPos pos = be.getBlockPos();
        if (!level.getBlockState(pos).is(ModBlocks.LITHIUM_BATTERY.get())) return;

        int h = 1;
        int localY = 0;
        if (be.isFormed() && be.getController() != null) {
            h = Math.max(1, be.getHeight());
            localY = pos.getY() - be.getController().getY();
        }
        float vTop = (float) (h - localY - 1) / h;
        float vBottom = (float) (h - localY) / h;

        Pose pose = poseStack.last();

        // ★ 每个面都取相邻空气格的光照（关键修复）
        int lightUp    = LevelRenderer.getLightColor(level, pos.above());
        int lightDown  = LevelRenderer.getLightColor(level, pos.below());
        int lightNorth = LevelRenderer.getLightColor(level, pos.north());
        int lightSouth = LevelRenderer.getLightColor(level, pos.south());
        int lightEast  = LevelRenderer.getLightColor(level, pos.east());
        int lightWest  = LevelRenderer.getLightColor(level, pos.west());

        VertexConsumer side = buffer.getBuffer(RenderType.entityCutoutNoCull(SIDE_TEX));

        if (!isBattery(level, pos.below())) {
            quad(side, pose, lightDown, packedOverlay,
                    v(0, 0, 0), v(1, 0, 0), v(1, 0, 1), v(0, 0, 1),
                    0F, 0F, 1F, 0F, 1F, 1F, 0F, 1F,
                    0F, -1F, 0F);
        }
        if (!isBattery(level, pos.north())) {
            quad(side, pose, lightNorth, packedOverlay,
                    v(0, 0, 0), v(0, 1, 0), v(1, 1, 0), v(1, 0, 0),
                    0F, vBottom, 0F, vTop, 1F, vTop, 1F, vBottom,
                    0F, 0F, -1F);
        }
        if (!isBattery(level, pos.south())) {
            quad(side, pose, lightSouth, packedOverlay,
                    v(1, 0, 1), v(1, 1, 1), v(0, 1, 1), v(0, 0, 1),
                    0F, vBottom, 0F, vTop, 1F, vTop, 1F, vBottom,
                    0F, 0F, 1F);
        }
        if (!isBattery(level, pos.east())) {
            quad(side, pose, lightEast, packedOverlay,
                    v(1, 0, 1), v(1, 0, 0), v(1, 1, 0), v(1, 1, 1),
                    0F, vBottom, 1F, vBottom, 1F, vTop, 0F, vTop,
                    1F, 0F, 0F);
        }
        if (!isBattery(level, pos.west())) {
            quad(side, pose, lightWest, packedOverlay,
                    v(0, 0, 0), v(0, 0, 1), v(0, 1, 1), v(0, 1, 0),
                    0F, vBottom, 1F, vBottom, 1F, vTop, 0F, vTop,
                    -1F, 0F, 0F);
        }

        // 侧面写完，才切换到顶面材质
        if (!isBattery(level, pos.above())) {
            VertexConsumer top = buffer.getBuffer(RenderType.entityCutoutNoCull(TOP_TEX));
            quad(top, pose, lightUp, packedOverlay,
                    v(0, 1, 0), v(0, 1, 1), v(1, 1, 1), v(1, 1, 0),
                    0F, 0F, 0F, 1F, 1F, 1F, 1F, 0F,
                    0F, 1F, 0F);
        }
    }

    private static Vec3 v(double x, double y, double z) {
        return new Vec3(x, y, z);
    }

    private static boolean isBattery(Level level, BlockPos p) {
        return level.getBlockState(p).is(ModBlocks.LITHIUM_BATTERY.get());
    }

    private static void quad(VertexConsumer c, Pose pose, int light, int overlay,
                             Vec3 p0, Vec3 p1, Vec3 p2, Vec3 p3,
                             float u0, float v0, float u1, float v1,
                             float u2, float v2, float u3, float v3,
                             float nx, float ny, float nz) {
        vertex(c, pose, p0, u0, v0, light, overlay, nx, ny, nz);
        vertex(c, pose, p1, u1, v1, light, overlay, nx, ny, nz);
        vertex(c, pose, p2, u2, v2, light, overlay, nx, ny, nz);
        vertex(c, pose, p3, u3, v3, light, overlay, nx, ny, nz);
    }

    private static void vertex(VertexConsumer c, Pose pose, Vec3 p, float u, float v,
                               int light, int overlay, float nx, float ny, float nz) {
        c.addVertex(pose.pose(), (float) p.x, (float) p.y, (float) p.z)
                .setColor(255, 255, 255, 255)
                .setUv(u, v)
                .setOverlay(overlay)
                .setLight(light)
                .setNormal(pose, nx, ny, nz);
    }
}