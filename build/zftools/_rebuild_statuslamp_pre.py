# -*- coding: utf-8 -*-
"""补一份 zf30 阶段里漏备份的"改前"文件：`StatusLampPart.java`。

漏的原因：它是**既有文件被修改**，而我在建 zf30_pre 时列的清单里没有它
（清单是按"我打算改哪些"写的，而它是"进 GUI 时才想起来要参数化"才改的）。
按 §4.17 的三级来源，这属于第 ③ 级 **减法重建**：把这次的三处改动反向去掉。

本次对该文件只做了三件事：
  ① 类注释改成"第一台用它的机器是微型粉碎机"并加了一段 ZF30 说明
  ② 加常量 `MICRO_CRUSHER_PREFIX` + 字段 `keyPrefix` + 新构造器（老的转发过去）
  ③ `translationKeyOf(now)` 拆成 `suffixOf(now)`，前缀改为字段拼接
反向做完之后，文件应当与 zf30 动手前**语义一致**（只改注释里的措辞也会一并还原成原文）。
"""
import io
import os

PATH = r"E:\PotatoST\src\main\java\com\potatost\mod\client\gui\parts\StatusLampPart.java"
DST = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf30_pre\StatusLampPart.java"

text = io.open(PATH, encoding="utf-8").read()

REVERSALS = [
    # ① 类注释还原（连同 ZF30 那段一起去掉）
    ('''/**
 * 状态灯：一个小方灯 + 悬停说明（0.10 新增，第一台用它的机器是微型粉碎机）。
 *
 * <p>颜色语义（与各机器方块实体里的 STATUS_* 一一对应）：
 * <ul>
 *   <li><b>绿</b>：配方有效且电够，正在运行；</li>
 *   <li><b>红</b>：配方有效但电不够；</li>
 *   <li><b>黄</b>：开不了工——红石信号关机 / 输入槽空 / 物品不可加工 / 输出槽满。</li>
 * </ul>
 * 状态值由服务端每 tick 算好，经 ContainerData 同步过来，客户端只负责上色。</p>
 *
 * <p><b>ⓘ 0.10 ZF30 修：文案前缀必须由构造方给。</b>
 * 第一版把 {@code "gui.potato_s_t.micro_crusher.status."} 写死在类里，
 * 液压机直接复用这个部件 ⇒ 悬停显示的是「<b>正在粉碎</b>」。
 * 颜色/状态码两边本来就一致（六个 STATUS_* 取值相同），所以只有文案会错 ——
 * 这种"复用部件时漏掉参数化"的错误编译不报、检查脚本也查不到（键都存在，只是属于另一台机器），
 * 只能靠**在游戏里把鼠标放上去**发现。用户截图点出来的就是这个。</p>
 */''',
     '''/**
 * 状态灯：一个小方灯 + 悬停说明（0.10 新增，微型粉碎机用）。
 *
 * <p>颜色语义（与 {@link MicroCrusherBlockEntity} 里的 STATUS_* 一一对应）：
 * <ul>
 *   <li><b>绿</b>：配方有效且电够，正在粉碎；</li>
 *   <li><b>红</b>：配方有效但电不够；</li>
 *   <li><b>黄</b>：开不了工——红石信号关机 / 输入槽空 / 物品不可粉碎 / 输出槽满。</li>
 * </ul>
 * 状态值由服务端每 tick 算好，经 ContainerData 同步过来，客户端只负责上色。</p>
 */'''),
    # ② 常量 + 字段 + 构造器还原
    ('''    /** 微型粉碎机的文案前缀（老调用点不传前缀时用它，保持向后兼容） */
    public static final String MICRO_CRUSHER_PREFIX = "gui.potato_s_t.micro_crusher.status.";

    private final int x;
    private final int y;
    private final int size;
    private final IntSupplier status;
    /** 悬停文案前缀，形如 {@code gui.potato_s_t.<机器id>.status.} */
    private final String keyPrefix;

    public StatusLampPart(int x, int y, int size, IntSupplier status) {
        this(x, y, size, status, MICRO_CRUSHER_PREFIX);
    }

    public StatusLampPart(int x, int y, int size, IntSupplier status, String keyPrefix) {
        this.x = x;
        this.y = y;
        this.size = size;
        this.status = status;
        this.keyPrefix = keyPrefix;
    }''',
     '''    private final int x;
    private final int y;
    private final int size;
    private final IntSupplier status;

    public StatusLampPart(int x, int y, int size, IntSupplier status) {
        this.x = x;
        this.y = y;
        this.size = size;
        this.status = status;
    }'''),
    # ③ tooltip 里的前缀拼接
    ('''        gg.renderTooltip(screen.font(), Component.translatable(this.keyPrefix + suffixOf(now)), mouseX, mouseY);''',
     '''        gg.renderTooltip(screen.font(), Component.translatable(translationKeyOf(now)), mouseX, mouseY);'''),
    # ④ suffixOf 还原成 translationKeyOf
    ('''    /**
     * 状态码 → 文案后缀。
     *
     * <p>用的是 {@link MicroCrusherBlockEntity} 的常量，因为**各机器的六个状态码取值一致**
     * （0=关机 1=空 2=无效 3=没电 4=输出满 5=运行中），这里只按数值映射。
     * 加新机器时如果沿用同一套状态码，只要给出自己的 {@code keyPrefix} 即可。</p>
     */
    private static String suffixOf(int status) {
        return switch (status) {
            case MicroCrusherBlockEntity.STATUS_RUNNING -> "running";
            case MicroCrusherBlockEntity.STATUS_NO_POWER -> "no_power";
            case MicroCrusherBlockEntity.STATUS_DISABLED -> "disabled";
            case MicroCrusherBlockEntity.STATUS_INVALID -> "invalid";
            case MicroCrusherBlockEntity.STATUS_OUTPUT_FULL -> "output_full";
            default -> "empty";
        };
    }''',
     '''    private static String translationKeyOf(int status) {
        String suffix = switch (status) {
            case MicroCrusherBlockEntity.STATUS_RUNNING -> "running";
            case MicroCrusherBlockEntity.STATUS_NO_POWER -> "no_power";
            case MicroCrusherBlockEntity.STATUS_DISABLED -> "disabled";
            case MicroCrusherBlockEntity.STATUS_INVALID -> "invalid";
            case MicroCrusherBlockEntity.STATUS_OUTPUT_FULL -> "output_full";
            default -> "empty";
        };
        return "gui.potato_s_t.micro_crusher.status." + suffix;
    }'''),
]

for i, (new, old) in enumerate(REVERSALS, 1):
    n = text.count(new)
    assert n == 1, "第 %d 处反向锚点命中 %d 次" % (i, n)
    text = text.replace(new, old)

# 还原后不该再有 ZF30 的痕迹
for bad in ("keyPrefix", "MICRO_CRUSHER_PREFIX", "suffixOf", "ZF30"):
    assert bad not in text, "还原后仍含 %s" % bad

io.open(DST, "w", encoding="utf-8", newline="").write(text)
print("已补建改前副本：%s" % DST)
print("  %d 字节（改后 %d 字节）" % (os.path.getsize(DST), os.path.getsize(PATH)))
