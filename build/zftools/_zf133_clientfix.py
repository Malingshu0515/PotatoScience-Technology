# -*- coding: utf-8 -*-
"""_zf133_clientfix.py —— ★ 客户端崩溃：`BufferBuilder was empty`

## 现场（用户给的 runClient 日志）
```
java.lang.IllegalStateException: BufferBuilder was empty
  at com.mojang.blaze3d.vertex.BufferBuilder.buildOrThrow(BufferBuilder.java:60)
  at com.potatost.mod.client.ShockwaveRenderer.drawWall(ShockwaveRenderer.java:147)
```

## 根因（我写的，两处都不对）
`drawWall` 里那句：
```java
if (any) {
    BufferUploader.drawWithShader(buffer.buildOrThrow());
} else {
    buffer.buildOrThrow();      // ← 这一行必炸：buildOrThrow() 对空 builder 就是抛
}
```
我写 `else` 分支的**本意**是"三个层的 alpha 都被 `alpha <= 2` 挡掉时别把 builder 漏在那儿"。
但 `buildOrThrow()` 的语义是「**空就抛**」（名字里的 orThrow）—— 空 builder 应当**直接丢弃**，
根本没有"清空它"这种操作。

为什么是"淡出的尾巴"炸：`fade = 1 - age / MAX_SHOW_TICKS`，当 `age` 逼近 1400 tick 时
`fade → 0` ⇒ 三层 alpha 全是 0 ⇒ `any=false` ⇒ 走到 else ⇒ 抛。
（那一刻波还有效、`liveWaves()` 还留着它 —— 正好是"最后一两帧"。）

## 修法（改成**先算后画**，根本不进那个状态）
把"要不要画"在**建 builder 之前**算清楚：
```java
float coreAlpha = 圈芯那一层的 alpha;
if (coreAlpha <= 2) return false;          // 整道波都淡到看不见了：直接返回，不碰 Tesselator
BufferBuilder buffer = ...begin(...);      // 到这里一定至少有一个四边形
...
BufferUploader.drawWithShader(buffer.buildOrThrow());   // 唯一一次 build，且必然非空
```
⇒ 规矩：**`Tesselator.begin()` 之后必须保证至少 addVertex 一次**；
"如果没东西就不 build"这种分支**不能靠事后判断**（builder 一旦开始就欠一次收尾）。

## 为什么探针没抓住（要写进档案）
探针是**无头服务端**，`ShockwaveRenderer` 只在客户端加载 ⇒ **这一整块从来没被执行过**。
=> 新规矩：**客户端渲染类必须过一遍 `runClient`**（这次我只跑了 `runServer`，直接漏掉一整条路径）。

跑法：python build\\zftools\\_zf133_clientfix.py
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
    }"""

NEW = """    /**
     * 一道波的全部四边形（每层一个正面 + 顶上的余晖）。
     *
     * <p>⚠⚠ <b>必须先算"要不要画"，再碰 `Tesselator`</b>（ZF133 用户实机抓出的崩溃）：
     * 原版 {@code BufferBuilder.buildOrThrow()} 对**空** builder 是**直接抛**
     * （名字里的 orThrow 就是这个意思），根本没有"清空它"这种用法。
     * 我第一版写成"没东西就 `else { buffer.buildOrThrow(); }` 收个尾"，
     * 于是**波淡出的最后两帧**（三层 alpha 都被 `<= 2` 挡掉）必炸：
     * {@code IllegalStateException: BufferBuilder was empty}。</p>
     */
    private static void drawWall(Matrix4fHolder holder, boolean alongX, double main, double lateral,
                                 double baseY, int height, float fade) {
        // ⚠ 门槛的算法与下面循环里**同一份**（否则"过了门槛却没画"又会欠一次收尾）
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
            // 内层更白、外层更青（"星璨"那点意思）
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
        // 到这里一定至少有一个四边形（门槛已经在函数开头判过）
        BufferUploader.drawWithShader(buffer.buildOrThrow());
    }"""

s = io.open(P, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
s = s.replace(OLD, NEW, 1)

# 复核：整个文件里 buildOrThrow 只能出现在 drawWithShader 里，且只有一次
calls = re.findall(r"buildOrThrow\(\)", s)
print("buildOrThrow 出现 %d 次" % len(calls))
assert len(calls) == 1, "还有别处调 buildOrThrow"
assert "drawWithShader(buffer.buildOrThrow())" in s

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] 已改成「先算后画」：builder 开始后必然至少一个四边形")
