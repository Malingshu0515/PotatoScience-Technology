package com.potatost.mod.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.math.Axis;
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
 *
 * <p><b>两极的黑洞盖片</b>（0.11 ZF140）：等距圆柱投影在两极是塌的，照片类星图在那儿会
 * 出现放射状拉伸。修法是在两极各盖一张黑洞图（用户给的素材，抠出本体做成独立贴图）。
 * <b>四张星图共用同一张盖片</b>，原版星空不受影响。细节见 {@link #BLACK_HOLE}。</p>
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

    /**
     * 极点黑洞盖片（0.11 ZF140）—— 用户原话：「天空盒一个点会看到明显的拉伸现象 解决不了
     * 那正好在那个地方（四张星图都需要）补个黑洞」。
     *
     * <p><b>病根</b>：天空盒走的是等距圆柱投影（2:1，见类注释），这种投影在**南北两极**
     * 天然是塌的 —— 贴图最上面那一行像素要摊满整圈 360° 方位角，于是那一带的图案被拉成
     * 放射状的"万箭穿心"。照片类星图躲不掉（原图不是按全景图拍的）。</p>
     *
     * <p><b>为什么是盖片、不是把黑洞烤进四张星图</b>：1024×512 的星图，极点那一圈
     * （0~11.25°）只有 32 行像素，却要摊满 360°；真烤进去出来是一团马赛克。
     * 盖片自带一张图、自己的正方形网格，分辨率与星图解耦，而且**一张图四张星图共用**。</p>
     *
     * <p><b>为什么网格按 (a,b) 摆而不是按经纬度摆</b>：站在球心正对极点看过去，
     * 屏幕上的一点与"切平面坐标 (a,b)"成正比（焦距 × (a,b)）。所以只要把顶点摆在
     * {@code θ = atan(|(a,b)|·tan θmax)} 处，贴图就是**正对极点时不变形**的那张原图 ——
     * 这一条由 `_zf140_mapping.py` 常驻守着（正对极点的渲染 vs 原图，平均绝对差须 ≤2/255）。</p>
     */
    private static final ResourceLocation BLACK_HOLE = ResourceLocation.fromNamespaceAndPath(
            PotatoST.MODID, "textures/skybox/black_hole.png");
    /** 盖片角半径（度）：28° 是看图定的 —— 极点那一圈拉伸最明显的就是头一个网格环（11.25°）。 */
    private static final float HOLE_DEGREES = 28.0F;
    /** 每边 16 格 ⇒ 两极共 512 个四边形（比球幕还便宜）。 */
    private static final int HOLE_GRID = 16;
    /** 比球幕**略小一圈**：不写深度、又后画，本来就压得住，这只多一层保险。 */
    private static final float HOLE_RADIUS = RADIUS * 0.995F;

    private static final ResourceLocation[] SKIES = new ResourceLocation[NAMES.length];

    /** 每 5 个 float 描述一个顶点：x, y, z, u, v。 */
    private static float[] mesh;
    /** 黑洞盖片网格：`caps[0]` 北极、`caps[1]` 南极（同样每 5 个 float 一个顶点）。 */
    private static float[][] caps;
    /** 与 ModArmorItems 同一个写法：全限定名，省得动 import 表。 */
    private static final org.slf4j.Logger LOGGER = com.mojang.logging.LogUtils.getLogger();
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
        caps = buildCaps();
        verifyCaps();
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
        // 天球自转（用户 2026-09-25 追加的要求：「天空可以设置成一个游戏日转一圈」）：
        // 绕 **X 轴** 转、周期取 24000 tick —— 与日月的节拍完全一致
        //（原版 renderSky 也是 Axis.XP + ClientLevel.getTimeOfDay；我这边用 getGameTime()%24000
        // 自己算比例，省掉 partialTick 那套 API，反正 0.015°/tick 的步进看不出来）。
        pose.mulPose(Axis.XP.rotationDegrees((minecraft.level.getGameTime() % 24000L) / 24000.0F * 360.0F));
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

        drawBlackHoles(matrix);

        RenderSystem.enableCull();
        RenderSystem.depthMask(true);
        RenderSystem.setShaderFogStart(fogStart);
        RenderSystem.setShaderFogEnd(fogEnd);
        pose.popPose();
    }

    /**
     * 两个极点的盖片网格。`(a,b)` 在盖片自己的切平面里取值 `[-1,1]²`（正方形网格），
     * 顶点位置由 {@code θ = atan(|(a,b)|·tan θmax)} 定 —— 见 {@link #BLACK_HOLE} 的说明。
     */
    private static float[][] buildCaps() {
        float tmax = (float) Math.tan(Math.toRadians(HOLE_DEGREES));
        float[][] out = new float[2][];
        for (int p = 0; p < 2; p++) {
            float poleY = (p == 0) ? 1.0F : -1.0F;
            float[] cap = new float[HOLE_GRID * HOLE_GRID * 4 * 5];
            int n = 0;
            for (int r = 0; r < HOLE_GRID; r++) {
                float b0 = -1.0F + 2.0F * r / HOLE_GRID;
                float b1 = -1.0F + 2.0F * (r + 1) / HOLE_GRID;
                for (int c = 0; c < HOLE_GRID; c++) {
                    float a0 = -1.0F + 2.0F * c / HOLE_GRID;
                    float a1 = -1.0F + 2.0F * (c + 1) / HOLE_GRID;
                    n = putCap(cap, n, a0, b0, poleY, tmax);
                    n = putCap(cap, n, a0, b1, poleY, tmax);
                    n = putCap(cap, n, a1, b1, poleY, tmax);
                    n = putCap(cap, n, a1, b0, poleY, tmax);
                }
            }
            out[p] = cap;
        }
        return out;
    }

    private static int putCap(float[] out, int n, float a, float b, float poleY, float tmax) {
        double g = Math.sqrt((double) a * a + (double) b * b);
        double theta = Math.atan(g * tmax);
        double phi = Math.atan2(b, a);
        double sin = Math.sin(theta);
        double cos = Math.cos(theta);
        out[n++] = (float) (HOLE_RADIUS * sin * Math.cos(phi));
        out[n++] = (float) (HOLE_RADIUS * poleY * cos);
        out[n++] = (float) (HOLE_RADIUS * sin * Math.sin(phi));
        // ⚠ 两个 0.5+0.5x 的**符号**是量出来的，不是猜的：正对极点看过去必须与原图逐像素重合
        //   （V 少一个加号 = 上下颠倒，平均绝对差从 0.79/255 涨到 61.4/255）。
        out[n++] = (float) (0.5D + 0.5D * a);
        out[n++] = (float) (0.5D + 0.5D * b);
        return n;
    }

    /** 球幕之后把两极的黑洞盖片按 SRC_ALPHA / ONE_MINUS_SRC_ALPHA 混上去。 */
    private static void drawBlackHoles(Matrix4f matrix) {
        RenderSystem.setShader(GameRenderer::getPositionTexShader);
        RenderSystem.setShaderTexture(0, BLACK_HOLE);
        RenderSystem.enableBlend();
        RenderSystem.defaultBlendFunc();
        RenderSystem.depthMask(false);
        RenderSystem.disableCull();
        for (float[] cap : caps) {
            BufferBuilder buffer = Tesselator.getInstance()
                    .begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX);
            for (int i = 0; i < cap.length; i += 5) {
                buffer.addVertex(matrix, cap[i], cap[i + 1], cap[i + 2])
                        .setUv(cap[i + 3], cap[i + 4]);
            }
            BufferUploader.drawWithShader(buffer.buildOrThrow());
        }
        RenderSystem.disableBlend();
    }

    /**
     * 开机自检（0.11 ZF140）：把**真的顶点数组**量一遍，结果打进日志。
     *
     * <p>量两件事，都是"盖片对不对"的定义：</p>
     * <ol>
     *   <li>每个顶点都必须落在半径 {@link #HOLE_RADIUS} 的球面上；</li>
     *   <li>uv 必须与位置构成恒等 —— 顶点方向的 gnomonic 坐标
     *       {@code (x, z) / |y|} 要**恰好等于** {@code (2u-1, 2v-1)·tanθmax}。
     *       这一条成立，正对极点看过去就是原图；不成立就是被拉过或翻过。</li>
     * </ol>
     *
     * <p>⚠ 只记日志、**不抛异常**：玩家的客户端不该因为一行自检挂掉。
     * 判据由 `_zf140_verify.py`（A20）和 runClient 的日志检查两头兜住。</p>
     */
    private static void verifyCaps() {
        double tmax = Math.tan(Math.toRadians(HOLE_DEGREES));
        double worst = 0.0D;
        int vertices = 0;
        for (float[] cap : caps) {
            for (int i = 0; i < cap.length; i += 5) {
                double x = cap[i];
                double y = cap[i + 1];
                double z = cap[i + 2];
                double len = Math.sqrt(x * x + y * y + z * z);
                double wantA = (2.0D * cap[i + 3] - 1.0D) * tmax;
                double wantB = (2.0D * cap[i + 4] - 1.0D) * tmax;
                worst = Math.max(worst, Math.abs(x / Math.abs(y) - wantA));
                worst = Math.max(worst, Math.abs(z / Math.abs(y) - wantB));
                worst = Math.max(worst, Math.abs(len - HOLE_RADIUS) / HOLE_RADIUS);
                vertices++;
            }
        }
        if (worst > 1.0E-6D) {
            LOGGER.error("SkyboxRenderer: black-hole cap geometry BROKEN, max error {} "
                    + "(expected <= 1e-6) - the pole view will be distorted.", worst);
        } else {
            LOGGER.info("SkyboxRenderer: black-hole caps OK - {} poles, {} vertices, "
                    + "grid {}x{}, half-angle {} deg, max error {}.",
                    caps.length, vertices, HOLE_GRID, HOLE_GRID, HOLE_DEGREES, worst);
        }
    }
}
