# -*- coding: utf-8 -*-
u"""_zf140_java.py —— ZF140：给 `SkyboxRenderer` 加"极点黑洞盖片"

改前件由 `_zf140_backup.py` 备份并核哈希；本脚本**只改一个文件**：
`src/main/java/com/potatost/mod/client/SkyboxRenderer.java`。

三处插入 + 一段新方法：
  ① 常量：黑洞盖片的贴图、角半径、网格密度；
  ② `init()` 里建网格（与球幕同一个生命周期，绝不在渲染线程里现算）；
  ③ 球幕画完**紧接着**画盖片（同一个 pose、同一个"关雾/不写深度"的窗口里）；
  ④ 新方法 `buildCaps / putCap / drawBlackHoles`。

⚠ 全部锚点**先回读、逐条断言"恰好一次"**再落盘（档案 §4.125：切片要吃掉起点、终点、
  终点行的剩余部分；锚点命中数不是 1 就整体不写，免得留下半成品）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod", "client", "SkyboxRenderer.java")

# ------------------------------------------------------------------ ① 常量
ANCHOR_CONST = u"""    /** 四张星图的文件名（编号 0 留空 = 原版）。 */
    private static final String[] NAMES = {
            null, "sky_verdant", "sky_mystic", "sky_ember", "sky_tarantula"
    };
"""
INSERT_CONST = ANCHOR_CONST + u"""
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
"""

# ------------------------------------------------------------------ ② init
ANCHOR_INIT = u"""        mesh = buildDome();
        NeoForge.EVENT_BUS.addListener(SkyboxRenderer::onRenderLevelStage);
"""
INSERT_INIT = u"""        mesh = buildDome();
        caps = buildCaps();
        NeoForge.EVENT_BUS.addListener(SkyboxRenderer::onRenderLevelStage);
"""

ANCHOR_FIELD = u"""    /** 每 5 个 float 描述一个顶点：x, y, z, u, v。 */
    private static float[] mesh;
"""
INSERT_FIELD = u"""    /** 每 5 个 float 描述一个顶点：x, y, z, u, v。 */
    private static float[] mesh;
    /** 黑洞盖片网格：`caps[0]` 北极、`caps[1]` 南极（同样每 5 个 float 一个顶点）。 */
    private static float[][] caps;
"""

# ------------------------------------------------------------------ ③ 画
ANCHOR_DRAW = u"""        BufferUploader.drawWithShader(buffer.buildOrThrow());

        RenderSystem.enableCull();
        RenderSystem.depthMask(true);
"""
INSERT_DRAW = u"""        BufferUploader.drawWithShader(buffer.buildOrThrow());

        drawBlackHoles(matrix);

        RenderSystem.enableCull();
        RenderSystem.depthMask(true);
"""

# ------------------------------------------------------------------ ④ 新方法
ANCHOR_TAIL = u"""        RenderSystem.setShaderFogStart(fogStart);
        RenderSystem.setShaderFogEnd(fogEnd);
        pose.popPose();
    }
}
"""
INSERT_TAIL = u"""        RenderSystem.setShaderFogStart(fogStart);
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
}
"""

# ------------------------------------------------------------------ 类注释补一段
ANCHOR_DOC = u""" * <p><b>只有自己看得见</b>（用户拍板）：整个渲染只读"我手上那本书的组件"，不碰服务器、
 * 不发包。切到别的物品后天空**保持不变**（设定是"一本书记住一种天"），
 * 再拿书切回 0 号就回到原版星空。</p>
 */
"""
INSERT_DOC = u""" * <p><b>只有自己看得见</b>（用户拍板）：整个渲染只读"我手上那本书的组件"，不碰服务器、
 * 不发包。切到别的物品后天空**保持不变**（设定是"一本书记住一种天"），
 * 再拿书切回 0 号就回到原版星空。</p>
 *
 * <p><b>两极的黑洞盖片</b>（0.11 ZF140）：等距圆柱投影在两极是塌的，照片类星图在那儿会
 * 出现放射状拉伸。修法是在两极各盖一张黑洞图（用户给的素材，抠出本体做成独立贴图）。
 * <b>四张星图共用同一张盖片</b>，原版星空不受影响。细节见 {@link #BLACK_HOLE}。</p>
 */
"""

PATCHES = [
    (u"常量", ANCHOR_CONST, INSERT_CONST),
    (u"字段", ANCHOR_FIELD, INSERT_FIELD),
    (u"init", ANCHOR_INIT, INSERT_INIT),
    (u"画盖片", ANCHOR_DRAW, INSERT_DRAW),
    (u"类注释", ANCHOR_DOC, INSERT_DOC),
    (u"新方法", ANCHOR_TAIL, INSERT_TAIL),
]


def main(argv):
    write = "--write" in argv
    text = io.open(JAVA, "r", encoding="utf-8", newline="").read()
    print(u"改前 %d 字节 / %d 行" % (len(text.encode("utf-8")), text.count("\n") + 1))

    # 先全部验锚点，一条不合格就整体不写
    for name, old, new in PATCHES:
        n = text.count(old)
        assert n == 1, u"锚点[%s]命中 %d 次（必须恰好 1 次）" % (name, n)
        assert len(new) > len(old), u"锚点[%s]的替换文本没变长" % name
        # 原文里每一个非空行都必须原样活在新文本里 —— 插入不许顺手改掉既有行
        for line in old.split("\n"):
            assert not line.strip() or line in new, \
                u"锚点[%s]的原文行在新文本里丢了：%r" % (name, line)
        print(u"  ✓ 锚点[%s] 命中 1 次，%d 字节" % (name, len(old.encode("utf-8"))))

    for name, old, new in PATCHES:
        text = text.replace(old, new, 1)

    # 落盘前的自检：关键锚点必须还在、且新东西都在
    for needle in (u"private static float[][] caps;", u"caps = buildCaps();",
                   u"drawBlackHoles(matrix);", u"private static final ResourceLocation BLACK_HOLE",
                   u"RenderSystem.setShaderTexture(0, BLACK_HOLE);",
                   u"HOLE_DEGREES = 28.0F", u"private static float[][] buildCaps()",
                   u"private static void drawBlackHoles(Matrix4f matrix)",
                   u"out[n++] = (float) (0.5D + 0.5D * b);"):
        assert text.count(needle) == 1, u"自检失败：%s 出现 %d 次" % (needle, text.count(needle))
    assert text.count(u"BufferUploader.drawWithShader") == 2, u"buildOrThrow 调用点不是 2 处"
    assert text.count(u"buildOrThrow()") == 2, u"buildOrThrow 不是 2 处"
    assert text.count(u"class SkyboxRenderer") == 1

    print(u"改后 %d 字节 / %d 行" % (len(text.encode("utf-8")), text.count("\n") + 1))
    if write:
        io.open(JAVA, "w", encoding="utf-8", newline="").write(text)
        print(u"  >>> 已写入 %s" % JAVA)
    else:
        print(u"  （只试算，未写盘；加 --write 才落盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
