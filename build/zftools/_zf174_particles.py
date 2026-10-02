# -*- coding: utf-8 -*-
u"""_zf174_particles.py —— ZF174：自定义粒子（自己的贴图 + 客户端 provider）

用户原话：「这一版先保留 然后你还可以再狠点！按你的办自定义粒子你搞 屏幕扭曲来一点点试试水」。

## 做三个粒子（都用自绘贴图，不再借原版那些小亮点）

| id | 贴图 | 干什么 |
|---|---|---|
| `void_core` | 32×32 暗盘 + 细亮边 | **事件视界本体**：中间是**黑的**（原版没有"黑粒子"），边缘一圈亮 —— 这一颗就能让它像黑洞 |
| `void_glow` | 32×32 软光斑（紫白） | 光子环 / 吸积盘：加色感的软光，比 `END_ROD` 那种硬点柔得多 |
| `void_streak` | 32×32 横向拉长的拖尾 | **内落流**：按速度方向旋转的拖尾 ⇒ "物质被拉成丝"的感觉 |

## 用的是原版那套正规接口（不是黑魔法）

- 服务端：`DeferredRegister<ParticleType<?>>` + `SimpleParticleType`（1.21 里就是给"不需要额外参数的粒子"用的）；
- 客户端：`RegisterParticleProvidersEvent.registerSpriteSet(...)` + 继承 `TextureSheetParticle`；
- 贴图定义：`assets/potato_s_t/particles/<id>.json`（列出贴图名）+ `textures/particle/<id>.png`；
- 粒子一律 `getLightColor` 拉满（全亮）—— 黑洞自己在暗处才好看。

## 屏幕扭曲「一点点」

不写 shader（那要 shader JSON + GLSL + 后处理链，我**看不到画面**不敢上），改走两条**零风险**的路：
    ① 服务端给近处玩家上 **原版 `DARKNESS`**（那本来就是"屏幕一阵阵发暗"的原版画面效果，配我的心跳音正好）；
    ② 客户端**相机侧倾 + FOV 抽吸**（`ViewportEvent.ComputeCameraAngles` / `ComputeFov`）——
       位置从哪来？不用网络：`void_core` 粒子只会在**黑洞中心**生成，客户端在建这颗粒子时把坐标记进一个短名单，
       相机钩子取最近的那个 ⇒ **只在粒子可见范围内扭曲**（原版粒子本来就只发给 32 格内）⇒ 天然按距离生效。
"""
import io
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
FAILS = []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        FAILS.append(label)
    return ok


def w(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)


def main():
    # ---------- ① 贴图（Pillow 自绘） ----------
    from PIL import Image
    px_dir = os.path.join(ASSETS, "textures", "particle")
    os.makedirs(px_dir, exist_ok=True)
    N = 32

    # void_core：正中纯黑（alpha 255），外边一圈细亮边（紫白），再往外柔和衰减
    core = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    cp = core.load()
    for y in range(N):
        for x in range(N):
            dx = (x - N / 2.0 + 0.5) / (N / 2.0)
            dy = (y - N / 2.0 + 0.5) / (N / 2.0)
            r = math.hypot(dx, dy)
            if r <= 0.62:
                cp[x, y] = (2, 0, 8, 255)                      # 视界：几乎全黑
            elif r <= 0.74:
                k = (r - 0.62) / 0.12                          # 光子环：细亮边
                cp[x, y] = (int(150 + 105 * k), int(90 + 80 * k), 255, 255)
            elif r <= 1.0:
                k = 1.0 - (r - 0.74) / 0.26                    # 外圈柔和发光
                cp[x, y] = (120, 70, 220, int(150 * k * k))
    core.save(os.path.join(px_dir, "void_core.png"))
    check(u"void_core.png（32×32 暗盘 + 亮边）", os.path.exists(os.path.join(px_dir, "void_core.png")))

    # void_glow：软光斑（径向衰减，紫偏白心）
    glow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    gp = glow.load()
    for y in range(N):
        for x in range(N):
            r = math.hypot((x - N / 2.0 + 0.5) / (N / 2.0), (y - N / 2.0 + 0.5) / (N / 2.0))
            if r >= 1.0:
                continue
            k = (1.0 - r) ** 2.2
            gp[x, y] = (int(190 + 65 * k), int(120 + 120 * k), 255, int(230 * k))
    glow.save(os.path.join(px_dir, "void_glow.png"))
    check(u"void_glow.png（32×32 软光斑）", os.path.exists(os.path.join(px_dir, "void_glow.png")))

    # void_streak：横向拉长的拖尾（左亮右淡）
    streak = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    sp = streak.load()
    for y in range(N):
        for x in range(N):
            u = x / (N - 1.0)
            v = (y - N / 2.0 + 0.5) / (N / 2.0)
            thick = 0.16 + 0.5 * u                               # 头细尾粗
            if abs(v) > thick:
                continue
            k = (1.0 - abs(v) / thick) ** 1.6 * (1.0 - u * 0.85)
            sp[x, y] = (int(200 + 55 * k), int(150 + 90 * k), 255, int(235 * k))
    streak.save(os.path.join(px_dir, "void_streak.png"))
    check(u"void_streak.png（32×32 拖尾）", os.path.exists(os.path.join(px_dir, "void_streak.png")))

    # ---------- ② 粒子定义 JSON ----------
    defs = {u"void_core": [u"potato_s_t:void_core"],
            u"void_glow": [u"potato_s_t:void_glow"],
            u"void_streak": [u"potato_s_t:void_streak"]}
    for pid, tex in defs.items():
        p = os.path.join(ASSETS, "particles", pid + u".json")
        w(p, json.dumps({u"textures": tex}, ensure_ascii=False, indent=2) + u"\n")
        check(u"particles/%s.json" % pid, os.path.exists(p))

    # ---------- ③ ModParticles ----------
    w(os.path.join(MOD, "ModParticles.java"), u'''package com.potatost.mod;

import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.Registries;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 本模组的粒子（0.14 ZF174，第一组自定义粒子）。
 *
 * <p>三个都是 {@link SimpleParticleType}：没有额外参数、服务端只管在哪儿生成，
 * 长什么样全由客户端的 provider 说了算（见 {@code client/particle/}）。</p>
 *
 * <p>⚠ 注册分两半：**类型**在这里（两边都要有），**外观**在 {@code PotatoSTClient}
 * 的 {@code RegisterParticleProvidersEvent} 里 —— 少任何一半都会在客户端报
 * "unknown particle" 或干脆看不见（本工程第一次做，写清楚免得下一轮踩）。</p>
 */
public final class ModParticles {

    public static final DeferredRegister<ParticleType<?>> PARTICLES =
            DeferredRegister.create(Registries.PARTICLE_TYPE, PotatoST.MODID);

    /** 事件视界本体：中间全黑 + 一圈细亮边（原版没有"黑粒子"，这颗是黑洞像不像的关键）。 */
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> VOID_CORE =
            PARTICLES.register("void_core", () -> new SimpleParticleType(false));

    /** 软光斑：光子环与吸积盘用（比原版那些硬亮点柔和得多）。 */
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> VOID_GLOW =
            PARTICLES.register("void_glow", () -> new SimpleParticleType(false));

    /** 拖尾：内落流用（按速度方向旋转 ⇒ 物质被拉成丝）。 */
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> VOID_STREAK =
            PARTICLES.register("void_streak", () -> new SimpleParticleType(false));

    private ModParticles() {
    }
}
''')
    check(u"ModParticles.java 已写出", os.path.exists(os.path.join(MOD, "ModParticles.java")))

    # ---------- ④ 三个客户端粒子类 ----------
    base = u'''package com.potatost.mod.client.particle;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.RandomSource;

/**
 * %s
 *
 * <p>0.14 ZF174：本工程第一批自定义粒子。共同点：
 * ① 全亮（{@code getLightColor} 拉满）—— 黑洞要的就是"自己在暗里发光"；
 * ② 不受物理影响（{@code hasPhysics = false}）⇒ 不会被地形挤掉；
 * ③ 走 {@code PARTICLE_SHEET_TRANSLUCENT} ⇒ 贴图的 alpha 生效（软边靠它）。</p>
 */
public class %s extends TextureSheetParticle {

    protected %s(ClientLevel level, double x, double y, double z, SpriteSet sprites) {
        super(level, x, y, z);
        this.setSprite(sprites.get(this.random));
        this.hasPhysics = false;
        this.gravity = 0.0F;
        this.friction = 0.96F;
%s
    }

    @Override
    public int getLightColor(float partialTick) {
        return 0xF000F0;   // 全亮
    }

    @Override
    public ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_TRANSLUCENT;
    }

    /** 客户端注册用的 provider（{@code RegisterParticleProvidersEvent} 里挂）。 */
    public record Provider(SpriteSet sprites) implements ParticleProvider<SimpleParticleType> {
        @Override
        public net.minecraft.client.particle.Particle createParticle(SimpleParticleType type,
                ClientLevel level, double x, double y, double z, double xd, double yd, double zd,
                RandomSource random) {
            return new %s(level, x, y, z, this.sprites);
        }
    }
}
'''
    specs = [
        (u"VoidCoreParticle",
         u"事件视界本体：**一大颗**黑盘（quadSize 随寿命微涨），几乎不动 —— 它就是「洞」本身。",
         u"        this.lifetime = 14 + this.random.nextInt(6);\n"
         u"        this.quadSize = 1.6F + this.random.nextFloat() * 0.5F;\n"
         u"        this.alpha = 1.0F;"),
        (u"VoidGlowParticle",
         u"软光斑：**带初速度**（内落流会把它往奇点送），边走边缩小、变淡 —— 像被吸进去的光。",
         u"        this.lifetime = 18 + this.random.nextInt(10);\n"
         u"        this.quadSize = 0.35F + this.random.nextFloat() * 0.45F;\n"
         u"        this.xd = xd; this.yd = yd; this.zd = zd;"),
        (u"VoidStreakParticle",
         u"拖尾：把**速度方向转成贴图的旋转角** ⇒ 一条条顺着运动方向的丝（内落流的灵魂）。",
         u"        this.lifetime = 10 + this.random.nextInt(6);\n"
         u"        this.quadSize = 0.5F + this.random.nextFloat() * 0.5F;\n"
         u"        this.xd = xd; this.yd = yd; this.zd = zd;\n"
         u"        this.roll = (float) Math.atan2(zd, xd);"),
    ]
    for cls, doc, body in specs:
        p = os.path.join(MOD, r"client\particle", cls + u".java")
        w(p, base % (doc, cls, cls, body, cls))
        check(u"client/particle/%s.java" % cls, os.path.exists(p))

    print(u"\n（相机侧倾/FOV 与 service 端的接线在 _zf174_wire.py 里做）")
    print(u"失败项 = %d" % len(FAILS))
    for f in FAILS:
        print(u"  !! " + f)
    return 1 if FAILS else 0


if __name__ == u"__main__":
    sys.exit(main())
