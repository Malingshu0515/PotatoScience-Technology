package com.potatost.mod.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.potatost.mod.ShockwaveManager;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.GameRenderer;
import net.neoforged.neoforge.client.event.RenderLevelStageEvent;
import net.neoforged.neoforge.common.NeoForge;

/**
 * 冲击波的"光墙"渲染（0.11 ZF133）。
 *
 * <p>服务端每 tick 只推一格、拆一排方块，客户端这边要把"看不见的进度"画出来：
 * 在波的当前位置竖一道 **6 宽 × 3 高** 的发光薄墙（外加顶上一条更暗的余晖），
 * 用加法混合（{@code SRC_ALPHA, ONE}）叠出"星屑"的亮度 —— 与 ZF122 那次天空的教训不同，
 * 这次**不要**补摄像机朝向：{@code AFTER_ENTITIES} 那一刻的 pose stack 已经是世界坐标系，
 * 直接按方块坐标画就钉在世界里（补了反而会跟着视角跑）。</p>
 *
 * <p><b>批数与开销</b>：一道波 = 3 层 × 1 个四边形 × 2 个 pass = 6 个四边形/帧，
 * 顶点全是现算的 float，没有纹理、没有分配 —— 十几道波同屏也不到 100 个四边形。
 * 顶点着色用 {@code POSITION_COLOR} + {@code getPositionColorShader}，
 * 这是唯一一条不需要贴图的自定义顶点通道。</p>
 *
 * <p>由 {@code PotatoSTClient} 在客户端初始化时 {@link #init()}（与 ZF122 的
 * {@code SkyboxRenderer} 同一套挂法：{@code RenderLevelStageEvent} 是 game 总线的事件）。</p>
 */
public final class ShockwaveRenderer {

    /** 每一层的字形：向外扩张的格数、垂直扩张的格数、透明度倍率（0~1）。 */
    private static final double[][] LAYERS = {
            {0.0D, 0.0D, 1.00D},   // 芯
            {0.55D, 0.45D, 0.45D}, // 中间
            {1.10D, 0.95D, 0.18D}, // 外晕
    };

    /** 颜色：星璨钢的冷青白（加法混合，所以数值不用拉满）。 */
    private static final float[] CORE_RGB = {0.62F, 0.92F, 1.00F};
    private static final float[] OUTER_RGB = {0.24F, 0.62F, 0.78F};

    /** 顶上那条余晖的高度与透明度。 */
    private static final double GLOW_HEIGHT = 1.15D;
    private static final double GLOW_ALPHA = 0.25D;

    private static boolean ready;

    private ShockwaveRenderer() {
    }

    public static void init() {
        if (ready) {
            return;
        }
        ready = true;
        NeoForge.EVENT_BUS.addListener(ShockwaveRenderer::onRenderLevelStage);
    }

    private static void onRenderLevelStage(RenderLevelStageEvent event) {
        if (event.getStage() != RenderLevelStageEvent.Stage.AFTER_ENTITIES) {
            return;
        }
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.level == null || minecraft.player == null) {
            return;
        }
        java.util.List<ShockwaveClientState.Wave> waves = ShockwaveClientState.liveWaves();
        if (waves.isEmpty()) {
            return;
        }

        long now = minecraft.level.getGameTime();
        float partial = event.getPartialTick().getGameTimeDeltaPartialTick(false);
        PoseStack pose = event.getPoseStack();
        Matrix4fHolder holder = new Matrix4fHolder(pose);
        pose.pushPose();

        RenderSystem.enableBlend();
        RenderSystem.blendFunc(com.mojang.blaze3d.platform.GlStateManager.SourceFactor.SRC_ALPHA,
                com.mojang.blaze3d.platform.GlStateManager.DestFactor.ONE);
        RenderSystem.depthMask(false);
        RenderSystem.disableCull();
        RenderSystem.setShader(GameRenderer::getPositionColorShader);

        for (ShockwaveClientState.Wave wave : waves) {
            float age = (float) (now - wave.startTick) + partial;
            if (age < 0.0F) {
                continue;
            }
            double main = (wave.alongX ? wave.x : wave.z) + wave.sign * age;
            double lateral = wave.alongX ? wave.z : wave.x;
            // 芯在方块中心
            double mainCenter = main + 0.5D;
            double lateralCenter = lateral + 0.5D;
            double baseY = wave.y + 1.0D;
            float fade = Math.max(0.0F, 1.0F - age / ShockwaveClientState.MAX_SHOW_TICKS);

            drawWall(holder, wave.alongX, mainCenter, lateralCenter, baseY,
                    ShockwaveManager.HEIGHT, fade);
        }

        RenderSystem.enableCull();
        RenderSystem.depthMask(true);
        RenderSystem.defaultBlendFunc();
        RenderSystem.disableBlend();
        pose.popPose();
    }

    /** 一道波的全部四边形（每层一个正面 + 顶上的余晖）。 */
    private static void drawWall(Matrix4fHolder holder, boolean alongX, double main, double lateral,
                                 double baseY, int height, float fade) {
        BufferBuilder buffer = Tesselator.getInstance()
                .begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_COLOR);
        boolean any = false;
        for (double[] layer : LAYERS) {
            double half = ShockwaveManager.HALF_WIDTH + layer[0];
            double top = baseY + height + layer[1];
            int alpha = (int) Math.round(255.0D * layer[2] * fade * 0.75D);
            if (alpha <= 2) {
                continue;
            }
            // 内层更白、外层更青（"星璨"那点意思）
            float[] rgb = layer[2] > 0.5D ? CORE_RGB : OUTER_RGB;
            int ta = alpha;
            int ba = Math.min(255, alpha + 60);
            quad(buffer, holder, alongX, main, lateral - half, lateral + half, top, baseY,
                    rgb, ta, ta, ba, ba);
            any = true;
        }
        // 顶上的余晖（只往上一小块，朝上淡出）
        int glowAlpha = (int) Math.round(255.0D * GLOW_ALPHA * fade);
        if (glowAlpha > 2) {
            double half = ShockwaveManager.HALF_WIDTH + 0.3D;
            double top = baseY + ShockwaveManager.HEIGHT + GLOW_HEIGHT;
            quad(buffer, holder, alongX, main, lateral - half, lateral + half, top,
                    baseY + ShockwaveManager.HEIGHT, CORE_RGB, 0, 0, glowAlpha, glowAlpha);
            any = true;
        }
        if (any) {
            BufferUploader.drawWithShader(buffer.buildOrThrow());
        } else {
            buffer.buildOrThrow();
        }
    }

    /** 一个竖直的四边形：底边两个点 alpha 高、顶边两个点 alpha 低（底亮顶淡）。 */
    private static void quad(BufferBuilder buffer, Matrix4fHolder holder, boolean alongX,
                             double main, double lateralFrom, double lateralTo,
                             double topY, double bottomY, float[] rgb,
                             int topAlpha, int topAlpha2, int bottomAlpha, int bottomAlpha2) {
        if (alongX) {
            buffer.addVertex(holder.matrix(), (float) main, (float) bottomY, (float) lateralFrom)
                    .setColor(rgb[0], rgb[1], rgb[2], bottomAlpha / 255.0F);
            buffer.addVertex(holder.matrix(), (float) main, (float) bottomY, (float) lateralTo)
                    .setColor(rgb[0], rgb[1], rgb[2], bottomAlpha2 / 255.0F);
            buffer.addVertex(holder.matrix(), (float) main, (float) topY, (float) lateralTo)
                    .setColor(rgb[0], rgb[1], rgb[2], topAlpha2 / 255.0F);
            buffer.addVertex(holder.matrix(), (float) main, (float) topY, (float) lateralFrom)
                    .setColor(rgb[0], rgb[1], rgb[2], topAlpha / 255.0F);
        } else {
            buffer.addVertex(holder.matrix(), (float) lateralFrom, (float) bottomY, (float) main)
                    .setColor(rgb[0], rgb[1], rgb[2], bottomAlpha / 255.0F);
            buffer.addVertex(holder.matrix(), (float) lateralTo, (float) bottomY, (float) main)
                    .setColor(rgb[0], rgb[1], rgb[2], bottomAlpha2 / 255.0F);
            buffer.addVertex(holder.matrix(), (float) lateralTo, (float) topY, (float) main)
                    .setColor(rgb[0], rgb[1], rgb[2], topAlpha2 / 255.0F);
            buffer.addVertex(holder.matrix(), (float) lateralFrom, (float) topY, (float) main)
                    .setColor(rgb[0], rgb[1], rgb[2], topAlpha / 255.0F);
        }
    }

    /** 只是为了让 {@code org.joml.Matrix4f} 的 import 收在一处（渲染热路径里取矩阵）。 */
    private record Matrix4fHolder(PoseStack pose) {
        org.joml.Matrix4f matrix() {
            return pose.last().pose();
        }
    }
}
