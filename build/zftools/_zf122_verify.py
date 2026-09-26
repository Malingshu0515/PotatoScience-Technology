# -*- coding: utf-8 -*-
u"""_zf122_verify.py —— ZF122 常驻校验：星仪图之章（切换主世界天空盒）

用户原话：「星仪图之章 右键顺次切换主世界的天空盒 你看看怎么好做 图我给你了
你想怎么编辑都可以 我感觉这个图真的很好看！」
两条拍板：**只你自己看得见**（纯客户端渲染）/ **配方我看着办**（已给：四角纸 + 四边紫水晶碎片 + 中间荧石）。

期望值一律**照原话与设计稿硬写**，不从被测代码里读常量（档案 §4.27）。
"""
import io
import json
import os
import re
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
CLIENT = os.path.join(JAVA, "client")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
TOOLS = os.path.join(ROOT, r"build\zftools")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe\star_chart_tome.json")
DOC_EN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")

EXPECT_KEYS = 483
NEW_KEYS = 10
SKY_TEXTURES = ("sky_verdant", "sky_mystic", "sky_ember", "sky_tarantula")
LANGS = ("zh_cn", "en_us", "ja_jp", "ru_ru")

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def png_header(path):
    try:
        d = open(path, "rb").read(26)
    except Exception:
        return None
    if len(d) < 26 or d[:8] != b"\x89PNG\r\n\x1a\n" or d[12:16] != b"IHDR":
        return None
    w, h = struct.unpack(">II", d[16:24])
    return w, h, d[25]


def main():
    j = lambda n: read(os.path.join(JAVA, n))

    # ============ A 文件 ============
    for n in ("ModDataComponents.java", "StarChartTomeItem.java"):
        check(u"A1 有 %s" % n, os.path.exists(os.path.join(JAVA, n)))
    check(u"A2 有 client/SkyboxRenderer.java", os.path.exists(os.path.join(CLIENT, "SkyboxRenderer.java")))
    check(u"A3 有物品模型", os.path.exists(os.path.join(ASSETS, u"models", u"item", u"star_chart_tome.json")))
    for t in SKY_TEXTURES:
        check(u"A4 有天空盒贴图 %s.png" % t, os.path.exists(os.path.join(ASSETS, u"textures", u"skybox", t + u".png")))

    # ============ B 注册与装配 ============
    items = j("ModItems.java")
    check(u"B1 注册了 star_chart_tome", u'ITEMS.register("star_chart_tome"' in items)
    check(u"B2 进了创造页", u"output.accept(STAR_CHART_TOME.get())" in items)
    check(u"B3 物品默认组件 = 0（原版天）", u".component(ModDataComponents.SKY_INDEX.get(), 0)" in items)
    main_java = j("PotatoST.java")
    check(u"B4 构造期注册数据组件（§4.72）",
          u"ModDataComponents.DATA_COMPONENTS.register(modEventBus)" in main_java)
    cli = j("PotatoSTClient.java")
    check(u"B5 客户端初始化里叫醒渲染器", u"SkyboxRenderer.init()" in cli)

    # ============ C 组件 ============
    comp = j("ModDataComponents.java")
    check(u"C1 组件 persistent + networkSynchronized",
          u".persistent(Codec.INT)" in comp and u".networkSynchronized(ByteBufCodecs.VAR_INT)" in comp)
    check(u"C2 注册名是 sky_index", u'register("sky_index"' in comp)

    # ============ D 切换逻辑（照设计稿硬写）============
    item = j("StarChartTomeItem.java")
    check(u"D1 五种状态（原版 + 四张星图）", u"SKY_COUNT = 4" in item and u"STATES = SKY_COUNT + 1" in item)
    check(u"D2 正向循环取模", u"(current + 1) % STATES" in item)
    check(u"D3 潜行往回切（floorMod 防负数）", u"Math.floorMod(current - 1, STATES)" in item)
    check(u"D4 切换后写回组件", u"stack.set(ModDataComponents.SKY_INDEX.get(), next)" in item)
    check(u"D5 提示走 lang（Java 里没有硬编码中文文案）",
          u'translatable("message.potato_s_t.star_chart.switched"' in item)
    check(u"D6 名字也走 lang", u'"sky.potato_s_t." + next' in item)

    # ============ E 渲染器（"只有自己看得见"的落地）============
    sky = read(os.path.join(CLIENT, "SkyboxRenderer.java"))
    check(u"E1 挂在 AFTER_SKY 这一拍", u"RenderLevelStageEvent.Stage.AFTER_SKY" in sky)
    check(u"E2 只动主世界", u"minecraft.level.dimension() != Level.OVERWORLD" in sky)
    check(u"E3 关深度写入（否则会挡掉 100 格外的地形）", u"RenderSystem.depthMask(false)" in sky)
    check(u"E4 关背面剔除（从球内看）", u"RenderSystem.disableCull()" in sky)
    check(u"E5 关雾", u"setShaderFogStart(Float.MAX_VALUE)" in sky)
    check(u"E6 恢复现场（深度与雾）",
          u"RenderSystem.depthMask(true)" in sky and u"setShaderFogEnd(fogEnd)" in sky)
    check(u"E7 贴图路径 = textures/skybox/<名字>.png", u'"textures/skybox/" + NAMES[i] + ".png"' in sky)
    check(u"E8 球幕 32×16 段、半径 100",
          u"SEGMENTS = 32" in sky and u"RINGS = 16" in sky and u"RADIUS = 100.0F" in sky)
    check(u"E9 等距圆柱投影（u 沿经度、v 沿纬度）",
          u"2.0D * Math.PI * s / SEGMENTS" in sky and u"Math.PI * (0.5D - (double) r / RINGS)" in sky)
    check(u"E10 用 game 总线的 addListener（不是 mod 总线）",
          u"NeoForge.EVENT_BUS.addListener(SkyboxRenderer::onRenderLevelStage)" in sky)
    # ⚠ ZF122 用户实测抓出来的真 bug：不补摄像机朝向 ⇒ 天空跟着视线转（"贴屏幕上"）
    check(u"E12 补上摄像机朝向（天空钉在世界里，不跟着视线转）",
          u"pose.mulPose(event.getModelViewMatrix())" in sky)
    check(u"E14 天球按游戏日自转（24000 tick 一圈、绕 X 轴）",
          u"getGameTime() % 24000L" in sky and u"Axis.XP.rotationDegrees" in sky)
    check(u"E13 补朝向用 push/pop 包起来（不污染后面的渲染）",
          sky.count(u"pose.pushPose()") >= 1 and sky.count(u"pose.popPose()") >= 1)
    # "只有自己看得见"：本轮**不许**新增任何自定义数据包
    net = j("StarfallNetworking.java")
    check(u"E11 没有为天空盒新增数据包（纯客户端）",
          u"star_chart" not in net and u"sky_index" not in net)

    # ============ F 资源 ============
    for t in SKY_TEXTURES:
        head = png_header(os.path.join(ASSETS, u"textures", u"skybox", t + u".png"))
        if head is None:
            check(u"F1 %s 是真 PNG" % t, False, u"文件头不对")
            continue
        w, h, ctype = head
        eq(u"F1 %s 是 1024×512 的 2:1 图（等距圆柱）" % t, (1024, 512), (w, h))
        check(u"F2 %s 是调色板或真彩 PNG（colorType %d）" % (t, ctype), ctype in (2, 3, 6))
    # ⚠ **真解码**：只看文件头会被"IDAT 长度只有一半"的坏 PNG 骗过去
    #   —— ZF122 就是这么交付了一版**黑紫天空**（用户实测抓出来的第二种坏法）。
    sys.path.insert(0, TOOLS)
    from _zf66_png import read_png
    for t in SKY_TEXTURES:
        path = os.path.join(ASSETS, u"textures", u"skybox", t + u".png")
        try:
            w3, h3, _c3, px3 = read_png(path)
        except Exception as exc:
            check(u"F5 %s 能被真解码器读出来" % t, False, u"%s" % exc)
            continue
        eq(u"F5 %s 解码尺寸 1024×512" % t, (1024, 512), (w3, h3))
        eq(u"F6 %s 解码像素数" % t, 1024 * 512, len(px3))
        seam = max(abs(a - b) for a, b in zip(px3[0], px3[w3 - 1]))
        eq(u"F7 %s 首列与末列逐像素相同（U 向零接缝）" % t, 0, seam)

    head = png_header(os.path.join(ASSETS, u"textures", u"item", u"star_chart_tome.png"))
    eq(u"F3 物品图标 16×16 RGBA", (16, 16, 6), head)
    model = json.loads(read(os.path.join(ASSETS, u"models", u"item", u"star_chart_tome.json")))
    eq(u"F4 图标模型指向自己", u"potato_s_t:item/star_chart_tome", model.get(u"textures", {}).get(u"layer0"))

    # ============ G 配方（图纸照设计稿硬写）============
    check(u"G1 配方 JSON 存在", os.path.exists(RECIPE))
    if os.path.exists(RECIPE):
        r = json.loads(read(RECIPE))
        eq(u"G2 是工作台定形配方", u"minecraft:crafting_shaped", r.get(u"type"))
        eq(u"G3 九宫格 = PAP/AGA/PAP", [u"PAP", u"AGA", u"PAP"], r.get(u"pattern"))
        keys = r.get(u"key", {})
        eq(u"G4 三种材料是 纸/紫水晶碎片/荧石",
           {u"item": u"minecraft:paper"}, keys.get(u"P", {}).get(u"item") and dict(keys[u"P"]) or None)
        eq(u"G5 A = 紫水晶碎片", u"minecraft:amethyst_shard", keys.get(u"A", {}).get(u"item"))
        eq(u"G6 G = 荧石", u"minecraft:glowstone", keys.get(u"G", {}).get(u"item"))
        res = r.get(u"result", {})
        eq(u"G7 产物 = 星仪图之章 ×1", (u"potato_s_t:star_chart_tome", 1),
           (res.get(u"id"), res.get(u"count")))

    # ============ H 四语言 ============
    lang = dict((l, json.loads(read(os.path.join(LANG, l + u".json")))) for l in LANGS)
    eq(u"H1 四语言键数一致且 = %d" % EXPECT_KEYS, [EXPECT_KEYS] * 4, [len(lang[l]) for l in LANGS])
    base = set(lang["zh_cn"])
    for l in LANGS[1:]:
        eq(u"H2 %s 键集合与 zh_cn 一致" % l, set(), base ^ set(lang[l]))
    shapes = {u"item.potato_s_t.star_chart_tome": 0, u"message.potato_s_t.star_chart.switched": 1}
    for i in range(5):
        shapes[u"sky.potato_s_t.%d" % i] = 0
    for i in (1, 2, 3):
        shapes[u"tooltip.potato_s_t.star_chart.%d" % i] = 0
    eq(u"H3 新增键正好 %d 个" % NEW_KEYS, NEW_KEYS, len(shapes))
    for key, shape in shapes.items():
        for l in LANGS:
            v = lang[l].get(key)
            if v is None:
                check(u"H4 %s / %s 存在" % (l, key), False)
                continue
            eq(u"H4 %s / %s 占位符个数" % (l, key), shape, v.count(u"%s"))
            check(u"H5 %s / %s 没有 ASCII 双引号" % (l, key), u'"' not in v)
    check(u"H6 英文公告跟到 %d 键" % EXPECT_KEYS, u"(%d keys each)" % EXPECT_KEYS in read(DOC_EN))

    # ============ I 文档 ============
    doc = read(os.path.join(ROOT, r"docs\开发档案.md"))
    check(u"I1 档案 §5 有 ZF122 行", u"| ZF122 |" in doc)
    check(u"I2 档案 §9 有 ZF122 小节", u"### ZF122（0.11）星仪图之章" in doc)

    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
