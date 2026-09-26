### 4.123 【客户端崩溃】`BufferBuilder.buildOrThrow()` 对**空** builder 是**直接抛**（ZF133 用户实机抓出）

用户点开客户端直接崩：

```
java.lang.IllegalStateException: BufferBuilder was empty
  at com.mojang.blaze3d.vertex.BufferBuilder.buildOrThrow(BufferBuilder.java:60)
  at com.potatost.mod.client.ShockwaveRenderer.drawWall(ShockwaveRenderer.java:147)
```

我写的原样：

```java
if (any) {
    BufferUploader.drawWithShader(buffer.buildOrThrow());
} else {
    buffer.buildOrThrow();      // ← 本意是「没东西也别把 builder 漏在那儿」，实际是必炸
}
```

**根因**：`buildOrThrow()` 的名字就是「空就抛」—— 空 builder **只能丢弃**，没有「清空它」这种用法。
触发点是**波淡出的最后两帧**：`fade = 1 - age / MAX_SHOW_TICKS` 趋近 0 时三层 alpha 全被
`alpha <= 2` 挡掉 ⇒ `any = false` ⇒ 走到 else。

**修法（把「要不要画」提到建 builder 之前）**：

```java
int coreAlpha = (int) Math.round(255.0D * LAYERS[0][2] * fade * 0.75D);
if (coreAlpha <= 2) {
    return;                            // 整道波都淡到看不见了：不碰 Tesselator
}
BufferBuilder buffer = Tesselator.getInstance().begin(...);
... （到这里必然至少画一个四边形）
BufferUploader.drawWithShader(buffer.buildOrThrow());
```

⇒ 规矩：**`Tesselator.begin()` 一旦调用就欠一次收尾**，所以「可能什么都不画」必须**提前返回**，
不能靠事后判断。常驻校验为此加了 **C13/C13b**（`begin` 次数 == `drawWithShader` 次数；
不许有单独成句的 `buildOrThrow()`），并写了反证 `_zf133_falsify_client.py`（两把刀都咬住）。

### 4.124 【流程】客户端渲染类**必须过一遍 `runClient``** —— 无头探针一辈子碰不到它们

上面那个崩溃之所以能进成品，是因为 ZF133 的验收只跑了 **`runServer`**（无头服务端探针）：
`ShockwaveRenderer` 是 `Dist.CLIENT` 才加载的类，**服务端探针根本不会执行它**，
于是这整条渲染路径**一次都没被跑过**。

⇒ 规矩：只要这一轮碰了 `client/` 下的东西（渲染、HUD、Screen、粒子），
交付前**必须** `runClient` 进一次世界（§3 的发布六步里第 5 步本来就是"真启动"，
我把它当成了"服务端跑过就算"——那是错的）。

⚠ 附带的一条**判据教训**：我复核那次修复时，第一版脚本用
`len(re.findall("buildOrThrow\\(\\)", src)) == 1` 断言「只剩一处」，
结果 **javadoc 里提到的 `buildOrThrow()` 也被数进去了**（数出 3 处）⇒ 断言失败 ⇒ **文件没写盘**。
**复核源码条数之前要先剥注释。**
