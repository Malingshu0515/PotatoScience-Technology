package com.potatost.mod.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.PoseStack.Pose;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;

import com.potatost.mod.ElectrolyzerBlockEntity;
import com.potatost.mod.ModBlocks;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.client.extensions.common.IClientFluidTypeExtensions;
/**
 * 电解器的世界内水位：在储罐内腔画一个半透明"水盒"。
 *   - 高度 = 内腔高 × 水量/容量，每帧现算（不需要任何逐水位动画资源）
 *   - 贴图用原版动态水精灵 → 水面自带波纹动画
 *   - ★ 水盒跟随方块朝向旋转：BER 不会自动继承 blockstate 的 y 旋转（只有方块模型会），
 *     这里手动补上与 blockstate 等价的旋转（north=0 / east=90 / south=180 / west=270）。
 *   - 数据来自客户端方块实体（由服务端每 20 tick 低频同步，见 ElectrolyzerBlockEntity）
 */
public class ElectrolyzerRenderer implements BlockEntityRenderer<ElectrolyzerBlockEntity> {

    /** 水色（原版默认水颜色 #3F76E4） */
    private static final int WATER_TINT = 0x3F76E4;

    // ===== 储罐内腔（16 格制，Blockbench 模型坐标；该坐标在 facing=north 时与世界坐标重合）=====
    private static final float TANK_X0 = 2.0F;
    private static final float TANK_X1 = 14.0F;
    private static final float TANK_Y0 = 1.0F;    // 罐底（水位最低处）
    private static final float TANK_Y1 = 14.0F;   // 罐顶（满水位）
    private static final float TANK_Z0 = 2.0F;
    private static final float TANK_Z1 = 10.0F;

    /** 本方块使用的朝向属性（原版水平朝向属性；若 ElectrolyzerBlock 用的是自定义属性对象，把这一行换成 ElectrolyzerBlock.FACING） */
    private static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;

    /** 逃生口：若机器摆放正确、但水盒相对储罐整体错 180°，把这里改成 180.0F（只改这一行） */
    private static final float ROTATION_OFFSET = 0.0F;

    public ElectrolyzerRenderer(BlockEntityRendererProvider.Context context) {
    }

    @Override
    public void render(ElectrolyzerBlockEntity be, float partialTick, PoseStack poseStack, MultiBufferSource buffer,
                       int packedLight, int packedOverlay) {
        Level level = be.getLevel();
        if (level == null) {
            return;
        }
        BlockPos pos = be.getBlockPos();
        BlockState state = level.getBlockState(pos);
        if (!state.is(ModBlocks.ELECTROLYZER.get())) {
            return;   // 挖掉后残留帧守卫
        }

        int amount = be.getFluidHandler().getFluidInTank(0).getAmount();
        if (amount <= 0) {
            return;   // 空罐什么都不画
        }
        float ratio = Math.min(1.0F, amount / (float) ElectrolyzerBlockEntity.INPUT_CAPACITY);

        // ===== 跟着方块朝向转 =====
        // 与 blockstate 的 y 旋转等价（方向取反）：north=0 / east=-90 / south=180 / west=90
        Direction facing = state.hasProperty(FACING) ? state.getValue(FACING) : Direction.NORTH;
        float rotation = ROTATION_OFFSET + switch (facing) {
            case EAST -> -90.0F;
            case SOUTH -> 180.0F;
            case WEST -> 90.0F;
            default -> 0.0F;   // NORTH
        };

        float x0 = TANK_X0 / 16.0F;
        float x1 = TANK_X1 / 16.0F;
        float z0 = TANK_Z0 / 16.0F;
        float z1 = TANK_Z1 / 16.0F;
        float y0 = TANK_Y0 / 16.0F;
        float yTop = (TANK_Y0 + (TANK_Y1 - TANK_Y0) * ratio) / 16.0F;

        // 原版水精灵（动态贴图，UV 取当前帧）
        IClientFluidTypeExtensions ext = IClientFluidTypeExtensions.of(Fluids.WATER);
        TextureAtlasSprite sprite = Minecraft.getInstance()
                .getTextureAtlas(TextureAtlas.LOCATION_BLOCKS)
                .apply(ext.getStillTexture());
        float u0 = sprite.getU0();
        float u1 = sprite.getU1();
        float v0 = sprite.getV0();
        float v1 = sprite.getV1();

        float r = ((WATER_TINT >> 16) & 0xFF) / 255.0F;
        float g = ((WATER_TINT >> 8) & 0xFF) / 255.0F;
        float b = (WATER_TINT & 0xFF) / 255.0F;

        VertexConsumer consumer = buffer.getBuffer(RenderType.entityTranslucent(TextureAtlas.LOCATION_BLOCKS));

        // 绕方块中心旋转（与方块模型 y 旋转同一个支点）
        poseStack.pushPose();
        poseStack.translate(0.5F, 0.0F, 0.5F);
        poseStack.mulPose(Axis.YP.rotationDegrees(rotation));
        poseStack.translate(-0.5F, 0.0F, -0.5F);

        // 光照：每面取"旋转后它朝向的世界方向"外侧那一格（facing=north 时与旧版完全相同）
        Direction left = switch (facing) {
            case NORTH -> Direction.WEST;
            case WEST -> Direction.SOUTH;
            case SOUTH -> Direction.EAST;
            default -> Direction.NORTH;   // EAST
        };
        int lightFront = LevelRenderer.getLightColor(level, pos.relative(facing));
        int lightBack = LevelRenderer.getLightColor(level, pos.relative(facing.getOpposite()));
        int lightLeft = LevelRenderer.getLightColor(level, pos.relative(left));
        int lightRight = LevelRenderer.getLightColor(level, pos.relative(left.getOpposite()));
        int lightUp = LevelRenderer.getLightColor(level, pos.above());

        Pose pose = poseStack.last();

        // 四个侧面 + 水面（底面藏在模型里，不画）
        quad(consumer, pose, lightFront, packedOverlay,
                x0, y0, z0, x0, yTop, z0, x1, yTop, z0, x1, y0, z0,
                u0, v0, u1, v1, 0.0F, 0.0F, -1.0F, r, g, b);
        quad(consumer, pose, lightBack, packedOverlay,
                x1, y0, z1, x1, yTop, z1, x0, yTop, z1, x0, y0, z1,
                u0, v0, u1, v1, 0.0F, 0.0F, 1.0F, r, g, b);
        quad(consumer, pose, lightLeft, packedOverlay,
                x0, y0, z1, x0, yTop, z1, x0, yTop, z0, x0, y0, z0,
                u0, v0, u1, v1, -1.0F, 0.0F, 0.0F, r, g, b);
        quad(consumer, pose, lightRight, packedOverlay,
                x1, y0, z0, x1, yTop, z0, x1, yTop, z1, x1, y0, z1,
                u0, v0, u1, v1, 1.0F, 0.0F, 0.0F, r, g, b);
        quad(consumer, pose, lightUp, packedOverlay,
                x0, yTop, z0, x0, yTop, z1, x1, yTop, z1, x1, yTop, z0,
                u0, v0, u1, v1, 0.0F, 1.0F, 0.0F, r, g, b);

        poseStack.popPose();
    }

    private static void quad(VertexConsumer consumer, Pose pose, int light, int overlay,
                             float x0, float y0, float z0,
                             float x1, float y1, float z1,
                             float x2, float y2, float z2,
                             float x3, float y3, float z3,
                             float u0, float v0, float u1, float v1,
                             float nx, float ny, float nz,
                             float r, float g, float b) {
        vertex(consumer, pose, x0, y0, z0, u0, v1, light, overlay, nx, ny, nz, r, g, b);
        vertex(consumer, pose, x1, y1, z1, u0, v0, light, overlay, nx, ny, nz, r, g, b);
        vertex(consumer, pose, x2, y2, z2, u1, v0, light, overlay, nx, ny, nz, r, g, b);
        vertex(consumer, pose, x3, y3, z3, u1, v1, light, overlay, nx, ny, nz, r, g, b);
    }

    private static void vertex(VertexConsumer consumer, Pose pose, float x, float y, float z,
                               float u, float v, int light, int overlay,
                               float nx, float ny, float nz,
                               float r, float g, float b) {
        consumer.addVertex(pose.pose(), x, y, z)
                .setColor((int) (r * 255), (int) (g * 255), (int) (b * 255), 255)
                .setUv(u, v)
                .setOverlay(overlay)
                .setLight(light)
                .setNormal(pose, nx, ny, nz);
    }
}