package com.potatost.mod.client;

import java.util.Map;
import java.util.Set;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.PoseStack.Pose;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import com.potatost.mod.ModBlocks;
import com.potatost.mod.TerminalBlock;
import com.potatost.mod.TerminalBlockEntity;

public class TerminalRenderer implements BlockEntityRenderer<TerminalBlockEntity> {
    /** 古铜色（FE 铜线） */
    private static final float BRONZE_R = 0.80F, BRONZE_G = 0.50F, BRONZE_B = 0.20F, BRONZE_A = 0.9F;
    /** 紫色（动力线缆） */
    private static final float PURPLE_R = 0.58F, PURPLE_G = 0.28F, PURPLE_B = 0.92F, PURPLE_A = 0.9F;
    /** 银白色（FE 银线，ZF127；同一条网络上按**每条线自己的速率**选颜色） */
    private static final float SILVER_R = 0.88F, SILVER_G = 0.91F, SILVER_B = 0.95F, SILVER_A = 0.9F;

    private static final ResourceLocation WIRE_TEXTURE =
            ResourceLocation.parse("minecraft:textures/block/white_concrete.png");
    /** ⚠ 线径（= 贴图 1 像素）：ZF127 加银线时**一个字节都没改** —— 用户点名「连接线缆还是一样的像素大小」 */
    private static final double WIRE_RADIUS = 0.03125D;

    public TerminalRenderer(BlockEntityRendererProvider.Context context) {
    }

    @Override
    public boolean shouldRenderOffScreen(TerminalBlockEntity blockEntity) {
        return !blockEntity.getConnections().isEmpty() || !blockEntity.getPowerConnections().isEmpty();
    }

    @Override
    public void render(TerminalBlockEntity terminal, float partialTick, PoseStack poseStack, MultiBufferSource buffer,
                       int packedLight, int packedOverlay) {
        if (terminal.getLevel() == null) return;
        BlockPos selfPos = terminal.getBlockPos();
        BlockState selfState = terminal.getLevel().getBlockState(selfPos);
        if (!selfState.is(ModBlocks.TERMINAL.get())) return;
        Vec3 origin = Vec3.atLowerCornerOf(selfPos);
        Vec3 selfAnchor = terminalAnchor(selfPos, selfState);
        // FE 网络（铜线古铜色 / 银线银白色：一条一条按它自己的速率上色）
        renderFeWires(terminal, origin, selfAnchor, poseStack, buffer, packedLight, packedOverlay);
        // 动力线缆（紫色）
        renderWireSet(terminal, terminal.getPowerConnections(), PURPLE_R, PURPLE_G, PURPLE_B, PURPLE_A,
                origin, selfAnchor, poseStack, buffer, packedLight, packedOverlay);
    }

    /**
     * FE 网络连线：每条线按<b>它自己的速率</b>选颜色（铜线 = 古铜色，银线 = 银白色）。
     *
     * <p>⚠ 线径走的是同一个 {@link #WIRE_RADIUS}（用户点名"像素大小一样"），
     * 铜线银线只差颜色。</p>
     */
    private void renderFeWires(TerminalBlockEntity terminal, Vec3 origin, Vec3 selfAnchor,
                               PoseStack poseStack, MultiBufferSource buffer,
                               int packedLight, int packedOverlay) {
        BlockPos selfPos = terminal.getBlockPos();
        for (Map.Entry<BlockPos, Integer> entry : terminal.getConnections().entrySet()) {
            BlockPos otherPos = entry.getKey();
            if (selfPos.compareTo(otherPos) > 0) continue;   // 每根线只画一次
            BlockState otherState = terminal.getLevel().getBlockState(otherPos);
            if (!otherState.is(ModBlocks.TERMINAL.get())) continue;
            if (!(terminal.getLevel().getBlockEntity(otherPos) instanceof TerminalBlockEntity)) continue;
            Vec3 from = selfAnchor.subtract(origin);
            Vec3 to = terminalAnchor(otherPos, otherState).subtract(origin);
            boolean silver = entry.getValue() >= TerminalBlockEntity.SILVER_TRANSFER_RATE;
            renderWire(poseStack, buffer, packedLight, packedOverlay, from, to,
                    silver ? SILVER_R : BRONZE_R, silver ? SILVER_G : BRONZE_G,
                    silver ? SILVER_B : BRONZE_B, silver ? SILVER_A : BRONZE_A);
        }
    }

    private void renderWireSet(TerminalBlockEntity terminal, Set<BlockPos> set,
                               float r, float g, float b, float a,
                               Vec3 origin, Vec3 selfAnchor,
                               PoseStack poseStack, MultiBufferSource buffer, int packedLight, int packedOverlay) {
        BlockPos selfPos = terminal.getBlockPos();
        for (BlockPos otherPos : set) {
            if (selfPos.compareTo(otherPos) > 0) continue;   // 每根线只画一次
            BlockState otherState = terminal.getLevel().getBlockState(otherPos);
            if (!otherState.is(ModBlocks.TERMINAL.get())) continue;
            BlockEntity be = terminal.getLevel().getBlockEntity(otherPos);
            if (!(be instanceof TerminalBlockEntity)) continue;
            Vec3 from = selfAnchor.subtract(origin);
            Vec3 to = terminalAnchor(otherPos, otherState).subtract(origin);
            renderWire(poseStack, buffer, packedLight, packedOverlay, from, to, r, g, b, a);
        }
    }

    private Vec3 terminalAnchor(BlockPos pos, BlockState state) {
        if (!state.hasProperty(TerminalBlock.FACING)) {
            return pos.getCenter();
        }
        Direction facing = state.getValue(TerminalBlock.FACING);
        Vec3 normal = Vec3.atLowerCornerOf(facing.getNormal()).scale(0.0625D);
        return pos.getCenter().add(normal);
    }

    private void renderWire(PoseStack poseStack, MultiBufferSource buffer, int packedLight, int packedOverlay,
                            Vec3 from, Vec3 to, float r, float g, float b, float a) {
        Vec3 direction = to.subtract(from);
        double length = direction.length();
        if (length < 0.01D) return;
        Vec3 d = direction.scale(1.0D / length);
        Vec3 reference = Math.abs(d.y) < 0.9D ? new Vec3(0, 1, 0) : new Vec3(1, 0, 0);
        Vec3 axis = d.cross(reference).normalize();
        Vec3 other = d.cross(axis).normalize();
        Vec3[] corners = new Vec3[4];
        corners[0] = axis.add(other).scale(WIRE_RADIUS);
        corners[1] = other.subtract(axis).scale(WIRE_RADIUS);
        corners[2] = axis.add(other).scale(-WIRE_RADIUS);
        corners[3] = axis.subtract(other).scale(WIRE_RADIUS);
        VertexConsumer consumer = buffer.getBuffer(RenderType.entityTranslucent(WIRE_TEXTURE));
        Pose pose = poseStack.last();
        for (int i = 0; i < 4; i++) {
            Vec3 c0 = corners[i];
            Vec3 c1 = corners[(i + 1) % 4];
            addVertex(consumer, pose, from.add(c0), 0.0F, 0.0F, packedLight, packedOverlay, r, g, b, a);
            addVertex(consumer, pose, from.add(c1), 0.0F, 1.0F, packedLight, packedOverlay, r, g, b, a);
            addVertex(consumer, pose, to.add(c1), 1.0F, 1.0F, packedLight, packedOverlay, r, g, b, a);
            addVertex(consumer, pose, to.add(c0), 1.0F, 0.0F, packedLight, packedOverlay, r, g, b, a);
        }
    }

    private void addVertex(VertexConsumer consumer, Pose pose, Vec3 pos, float u, float v,
                           int packedLight, int packedOverlay, float r, float g, float b, float a) {
        consumer.addVertex(pose.pose(), (float) pos.x, (float) pos.y, (float) pos.z)
                .setColor((int) (r * 255), (int) (g * 255), (int) (b * 255), (int) (a * 255))
                .setUv(u, v)
                .setOverlay(packedOverlay)
                .setLight(packedLight)
                .setNormal(pose, 0.0F, 1.0F, 0.0F);
    }
}