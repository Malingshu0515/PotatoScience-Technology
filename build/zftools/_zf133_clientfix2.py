# -*- coding: utf-8 -*-
"""_zf133_clientfix2.py —— 同一次修复，但复核改成"只数代码行"（注释里提到方法名不算）

上一次 replace 已经成功，只是在复核时把 javadoc 里提到的 `buildOrThrow()` 也数进去了
⇒ 断言失败、没写盘（所以文件还是旧的）。修法：复核前**先剥掉注释**。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\client\ShockwaveRenderer.java"

OLD = """    /** 一道波的全部四边形（每层一个正面 + 顶上的余晖）。 */
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
            // 内层更白、外层更青（\"星璨\"那点意思）
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
    }"""

NEW = """    /**
     * 一道波的全部四边形（每层一个正面 + 顶上的余晖）。
     *
     * <p>⚠⚠ <b>必须先算「要不要画」，再碰 `Tesselator`</b>（ZF133 用户实机抓出的崩溃）：
     * 原版 `BufferBuilder.buildOrThrow()` 对**空** builder 是**直接抛**
     * （名字里的 orThrow 就是这个意思），根本没有「清空它」这种用法。
     * 我第一版写成「没东西就 `else { buffer.buildOrThrow(); }` 收个尾」，
     * 于是**波淡出的最后两帧**（三层 alpha 都被 `<= 2` 挡掉）必炸：
     * `IllegalStateException: BufferBuilder was empty`。</p>
     */
    private static void drawWall(Matrix4fHolder holder, boolean alongX, double main, double lateral,
                                 double baseY, int height, float fade) {
        // ⚠ 门槛与下面循环里**同一份算法**（否则「过了门槛却没画」又会欠一次收尾）
        int coreAlpha = (int) Math.round(255.0D * LAYERS[0][2] * fade * 0.75D);
        if (coreAlpha <= 2) {
            return;   // 整道波都淡到看不见了：**不开始** builder
        }
        BufferBuilder buffer = Tesselator.getInstance()
                .begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_COLOR);
        for (double[] layer : LAYERS) {
            double half = ShockwaveManager.HALF_WIDTH + layer[0];
            double top = baseY + height + layer[1];
            int alpha = (int) Math.round(255.0D * layer[2] * fade * 0.75D);
            if (alpha <= 2) {
                continue;
            }
            // 内层更白、外层更青（星璨那点意思）
            float[] rgb = layer[2] > 0.5D ? CORE_RGB : OUTER_RGB;
            int ta = alpha;
            int ba = Math.min(255, alpha + 60);
            quad(buffer, holder, alongX, main, lateral - half, lateral + half, top, baseY,
                    rgb, ta, ta, ba, ba);
        }
        // 顶上的余晖（只往上一小块，朝上淡出）
        int glowAlpha = (int) Math.round(255.0D * GLOW_ALPHA * fade);
        if (glowAlpha > 2) {
            double half = ShockwaveManager.HALF_WIDTH + 0.3D;
            double top = baseY + ShockwaveManager.HEIGHT + GLOW_HEIGHT;
            quad(buffer, holder, alongX, main, lateral - half, lateral + half, top,
                    baseY + ShockwaveManager.HEIGHT, CORE_RGB, 0, 0, glowAlpha, glowAlpha);
        }
        // 到这里一定至少有一个四边形（门槛已在函数开头判过）
        BufferUploader.drawWithShader(buffer.buildOrThrow());
    }"""


def strip_comments(src):
    """去掉 // 行注释与 /* */ 块注释（复核用，避免把注释里的方法名当成调用）。"""
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    src = re.sub(r"//[^\n]*", "", src)
    return src


s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
s = s.replace(OLD, NEW, 1)

code = strip_comments(s)
calls = code.count("buildOrThrow()")
print("代码里（去注释后）buildOrThrow() 出现 %d 次" % calls)
assert calls == 1, "还有别处调 buildOrThrow"
assert "drawWithShader(buffer.buildOrThrow())" in code
assert "BufferUploader" in code

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] 已改成「先算后画」：builder 开始后必然至少一个四边形")
