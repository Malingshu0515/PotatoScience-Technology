package com.potatost.mod.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.potatost.mod.PotatoST;
import com.potatost.mod.StarChartTomeItem;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.client.event.RenderLevelStageEvent;
import net.neoforged.neoforge.common.NeoForge;
import org.joml.Matrix4f;

/**
 * 星仪图的天空盒渲染（0.11 ZF122）—— 本工程**第一次改天空**。
 *
 * <p><b>怎么"换掉"天空</b>：原版没有"自定义天空盒"的接口。这里用的是最省事也最稳的一条：
 * 在 NeoForge 的 {@code RenderLevelStageEvent.Stage.AFTER_SKY}（原版天空**已经画完**、
 * 地形**还没开始画**）这一拍，往摄像机周围画一个<b>不透明的大球幕</b> ——
 * 于是太阳、月亮、星星全被它盖住，而地形随后画在上层，自然遮住地平线以下的部分。</p>
 *
 * <p><b>三个必须写对的细节</b>：</p>
 * <ol>
 *   <li><b>关掉深度写入</b>（{@code depthMask(false)}）：球幕半径 100 格，
 *       若写深度，渲染距离 12 区块（192 格）以外、100 格以内的地形就会被它挡掉；
 *       关掉之后球幕只是个"背景板"，地形该画还画（原版画天空时也是这么干的）。</li>
 *   <li><b>关掉背面剔除</b>（{@code disableCull}）：我们在球**里面**看它，
 *       按外向绕序建的三角形从里面看是背面，不关剔除就什么都看不见。</li>
 *   <li><b>关掉雾</b>：雾是按地形距离算的，球幕在 100 格外 ⇒ 不关雾它会被雾糊成一片白。</li>
 * </ol>
 *
 * <p><b>贴图是等距圆柱投影</b>（2:1）：顶点按球坐标摆，UV 直接取
 * {@code u = 经度/360°、v = 纬度/180°}，所以四张图贴上去不变形（生成脚本见
 * {@code _zf122_textures.py}，已裁成 2:1 再缩放）。</p>
 *
 * <p><b>只有自己看得见</b>（用户拍板）：整个渲染只读"我手上那本书的组件"，不碰服务器、
 * 不发包。切到别的物品后天空**保持不变**（设定是"一本书记住一种天"），
 * 再拿书切回 0 号就回到原版星空。</p>
 */
public final class SkyboxRenderer {

    /** 球幕网格：经度 32 段 × 纬度 16 段 = 512 个四边形（软星云足够了，再多是浪费）。 */
    private static final int SEGMENTS = 32;
    private static final int RINGS = 16;
    /** 半径 100：在原版天空盒的量级内（远小于投影远平面），又足够远到不穿帮。 */
    private static final float RADIUS = 100.0F;

    /** 四张星图的文件名（编号 0 留空 = 原版）。 */
    private static final String[] NAMES = {
            null, "sky_verdant", "sky_mystic", "sky_ember", "sky_tarantula"
    };

    private static final ResourceLocation[] SKIES = new ResourceLocation[NAMES.length];

    /** 每 5 个 float 描述一个顶点：x, y, z, u, v。 */
    private static float[] mesh;
    /** 当前生效的编号（客户端记忆：不拿书也保持，见类注释）。 */
    private static int applied;
    private static boolean ready;

    private SkyboxRenderer() {
    }

    /**
     * 由 {@code PotatoSTClient} 在客户端初始化时调用一次。
     *
     * <p>⚠ 用**静态块 + init()** 而不是 {@code @EventBusSubscriber}：
     * {@code RenderLevelStageEvent} 是 **game 总线**的事件（它不是 {@code IModBusEvent}），
     * 而这个类只在客户端加载 ⇒ 在这里挂监听既明确又不碰 NeoForge 那套
     * "省略 bus= 默认挂哪条总线" 的坑（档案 §11.5 记过这笔账）。</p>
     */
    public static void init() {
        if (ready) {
            return;
        }
        ready = true;
        for (int i = 1; i < SKIES.length; i++) {
            SKIES[i] = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID,
                    "textures/skybox/" + NAMES[i] + ".png");
        }
        mesh = buildDome();
        NeoForge.EVENT_BUS.addListener(SkyboxRenderer::onRenderLevelStage);
    }

    /** 球坐标 → 直角坐标；UV 用等距圆柱（u 沿经度、v 沿纬度，从北极到南极）。 */
    private static float[] buildDome() {
        float[] out = new float[SEGMENTS * RINGS * 4 * 5];
        int p = 0;
        for (int r = 0; r < RINGS; r++) {
            double latTop = Math.PI * (0.5D - (double) r / RINGS);
            double latBottom = Math.PI * (0.5D - (double) (r + 1) / RINGS);
            float vTop = (float) r / RINGS;
            float vBottom = (float) (r + 1) / RINGS;
            for (int s = 0; s < SEGMENTS; s++) {
                double lonLeft = 2.0D * Math.PI * s / SEGMENTS;
                double lonRight = 2.0D * Math.PI * (s + 1) / SEGMENTS;
                float uLeft = (float) s / SEGMENTS;
                float uRight = (float) (s + 1) / SEGMENTS;
                p = put(out, p, latTop, lonLeft, uLeft, vTop);
                p = put(out, p, latBottom, lonLeft, uLeft, vBottom);
                p = put(out, p, latBottom, lonRight, uRight, vBottom);
                p = put(out, p, latTop, lonRight, uRight, vTop);
            }
        }
        return out;
    }

    private static int put(float[] out, int p, double lat, double lon, float u, float v) {
        float y = (float) (RADIUS * Math.sin(lat));
        float horizontal = (float) (RADIUS * Math.cos(lat));
        out[p++] = (float) (horizontal * Math.cos(lon));
        out[p++] = y;
        out[p++] = (float) (horizontal * Math.sin(lon));
        out[p++] = u;
        out[p++] = v;
        return p;
    }

    private static void onRenderLevelStage(RenderLevelStageEvent event) {
        if (event.getStage() != RenderLevelStageEvent.Stage.AFTER_SKY) {
            return;
        }
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.player == null || minecraft.level == null) {
            return;
        }
        // 用户原话是"主世界"的天空盒 ⇒ 下界/末地一概不动
        if (minecraft.level.dimension() != Level.OVERWORLD) {
            return;
        }
        // 手上拿着书就跟着书的组件走（这本书就是这个天）；不拿书时保持上次的设定
        ItemStack held = minecraft.player.getMainHandItem();
        if (held.getItem() instanceof StarChartTomeItem) {
            applied = StarChartTomeItem.currentIndex(held);
        }
        int index = applied;
        if (index <= 0 || index >= SKIES.length) {
            return;
        }

        float fogStart = RenderSystem.getShaderFogStart();
        float fogEnd = RenderSystem.getShaderFogEnd();
        PoseStack pose = event.getPoseStack();
        // ⚠⚠ 这一行是本渲染器**最容易漏**的一步（0.11 ZF122 用户实测抓出来的）：
        //   `AFTER_SKY` 那一刻的 pose stack 里**只有摄像机位置、没有摄像机朝向**，
        //   不补朝向的话，球幕是在**摄像空间**里画的 ⇒ 天空等于贴在屏幕上、
        //   你一转视线它就跟着转（用户原话：「这个天空会随着视角转动啊 不行的啦 需要定住的
        //   要不然会很晕 而且怪怪的」）。
        //   补法就是原版 renderSky 用的那一句：把模型视图矩阵（纯旋转、无平移）乘上去，
        //   球幕于是钉在世界坐标里，跟原版的星星一样"天不动、人转"。
        pose.pushPose();
        pose.mulPose(event.getModelViewMatrix());
        Matrix4f matrix = pose.last().pose();

        RenderSystem.setShaderFogStart(Float.MAX_VALUE);
        RenderSystem.setShaderFogEnd(Float.MAX_VALUE);
        RenderSystem.setShader(GameRenderer::getPositionTexShader);
        RenderSystem.setShaderTexture(0, SKIES[index]);
        RenderSystem.depthMask(false);
        RenderSystem.disableCull();
        RenderSystem.disableBlend();

        BufferBuilder buffer = Tesselator.getInstance()
                .begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX);
        for (int i = 0; i < mesh.length; i += 5) {
            buffer.addVertex(matrix, mesh[i], mesh[i + 1], mesh[i + 2])
                    .setUv(mesh[i + 3], mesh[i + 4]);
        }
        BufferUploader.drawWithShader(buffer.buildOrThrow());

        RenderSystem.enableCull();
        RenderSystem.depthMask(true);
        RenderSystem.setShaderFogStart(fogStart);
        RenderSystem.setShaderFogEnd(fogEnd);
        pose.popPose();
    }
}
