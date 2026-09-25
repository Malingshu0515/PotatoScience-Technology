# -*- coding: utf-8 -*-
u"""_zf122_java.py —— ZF122 在三个汇合点文件里"只加行"（唯一锚点 + 命中次数断言）

为什么用脚本而不是编辑工具：这棵树上有**多个会话同时改同一批文件**（ZF119/ZF120/ZF121 正在跑），
"读—改—写"之间文件经常已经变了，编辑工具会一直报"file changed since it was read"。
脚本一次读、一次写、写完立刻复核，锚点命中数**必须恰好为 1**，不满足就一个字节都不写（档案 §4.6）。

跑法：python build\\zftools\\_zf122_java.py [--write]
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

JAVA = r"E:\PotatoST\src\main\java\com\potatost\mod"
ITEMS = os.path.join(JAVA, "ModItems.java")
MAIN = os.path.join(JAVA, "PotatoST.java")
CLIENT = os.path.join(JAVA, "PotatoSTClient.java")

ITEM_ANCHOR = u"""    public static final DeferredItem<Item> RAW_VIBRANIUM =
            ITEMS.register("raw_vibranium", () -> new Item(new Item.Properties()));
"""

ITEM_ADD = u"""
    // ========== 星仪图之章（0.11 ZF122）==========
    /**
     * 星仪图之章：右键顺次切换**主世界**的天空盒（原版 → 四张星图 → 循环；潜行右键往回切）。
     *
     * <p>用户原话：「星仪图之章 右键顺次切换主世界的天空盒 你看看怎么好做 图我给你了
     * 你想怎么编辑都可以 我感觉这个图真的很好看！」</p>
     *
     * <p><b>只有自己看得见</b>（用户拍板）：选中的编号存在 {@link ModDataComponents#SKY_INDEX}
     * 组件里（跟着物品栈自动同步），渲染全在客户端 —— 不发任何自定义包、不改服务器状态。
     * 默认值 0 = 原版星空，所以刚拿到的书不会一上来就把天换了。</p>
     *
     * <p>配方（0.11 ZF122）：四角纸 + 四边紫水晶碎片 + 中间荧石，图纸在
     * {@code _zf45_recipes.py} 的表里，别手改 recipe\\*.json。</p>
     */
    public static final DeferredItem<Item> STAR_CHART_TOME =
            ITEMS.register("star_chart_tome", () -> new StarChartTomeItem(new Item.Properties()
                    .stacksTo(1)
                    .component(ModDataComponents.SKY_INDEX.get(), 0)));
"""

TAB_ADD = u"                        output.accept(STAR_CHART_TOME.get());// ← 新增（0.11 ZF122 星仪图之章）\n"

MAIN_ANCHOR = u"""        ModEntities.ENTITY_TYPES.register(modEventBus);
        modEventBus.addListener(StarfallNetworking::register);
"""

MAIN_ADD = u"""        // 星仪图之章（0.11 ZF122）：数据组件注册表（sky_index = 这本书看的是哪片天）。
        // 同样属于"必须在构造期碰一下"的那类（§4.72）：少了这行，第一次拿书就会撞注册窗口。
        ModDataComponents.DATA_COMPONENTS.register(modEventBus);
"""

CLIENT_ANCHOR = u"        registerFluidTextures(event);\n"

CLIENT_ADD = u"""        // 星仪图之章（0.11 ZF122）：把天空盒渲染器叫醒 —— 它自己在 init() 里往 **game 总线**
        // 挂 RenderLevelStageEvent（那个事件不是 IModBusEvent，见 SkyboxRenderer 的类注释）。
        com.potatost.mod.client.SkyboxRenderer.init();
"""


def read(p):
    return io.open(p, encoding="utf-8").read()


def insert_once(path, anchor, addition, where_after=True, label=u""):
    text = read(path)
    n = text.count(anchor)
    if n != 1:
        raise AssertionError(u"%s：锚点命中 %d 次（要求恰好 1）\n锚点片段：%r" % (label or path, n, anchor[:80]))
    new = text.replace(anchor, anchor + addition if where_after else addition + anchor)
    io.open(path, "w", encoding="utf-8", newline=u"").write(new)
    return new


def append_to_last_accept(path, line):
    u"""插到创造页 accept 列表的**最后一行之后**（列表长了，锚固定不下来，用"最后一条"这个结构判据）"""
    text = read(path)
    hits = list(re.finditer(r"^ *output\.accept\([^\n]*\n", text, re.M))
    if not hits:
        raise AssertionError(u"创造页里找不到任何 output.accept")
    last = hits[-1]
    new = text[:last.end()] + line + text[last.end():]
    io.open(path, "w", encoding="utf-8", newline=u"").write(new)
    return new, len(hits)


def main(argv):
    write = "--write" in argv
    plan = [
        (ITEMS, ITEM_ANCHOR, ITEM_ADD, u"ModItems 物品注册"),
        (MAIN, MAIN_ANCHOR, MAIN_ADD, u"PotatoST 构造器"),
        (CLIENT, CLIENT_ANCHOR, CLIENT_ADD, u"PotatoSTClient 客户端初始化"),
    ]
    if not write:
        for path, anchor, _add, label in plan:
            n = read(path).count(anchor)
            print(u"   %-24s 锚点命中 %d 次 %s" % (label, n, u"✓" if n == 1 else u"✗"))
        text = read(ITEMS)
        print(u"   %-24s 创造页 accept 行数 %d（新条目插在最后一条之后）"
              % (u"ModItems 创造页", len(re.findall(r"^ *output\.accept\(", text, re.M))))
        print(u"（体检模式，未写盘）")
        return 0

    for path, anchor, add, label in plan:
        insert_once(path, anchor, add, True, label)
        print(u"   已插入：%s" % label)
    _, count = append_to_last_accept(ITEMS, TAB_ADD)
    print(u"   已插入：ModItems 创造页（原来 %d 条 accept）" % count)

    # ---------------- 复核 ----------------
    bad = 0
    checks = [
        (ITEMS, u'ITEMS.register("star_chart_tome"', u"物品注册"),
        (ITEMS, u"STAR_CHART_TOME.get()", u"创造页条目"),
        (MAIN, u"ModDataComponents.DATA_COMPONENTS.register(modEventBus)", u"组件注册"),
        (CLIENT, u"SkyboxRenderer.init()", u"渲染器叫醒"),
    ]
    for path, needle, label in checks:
        n = read(path).count(needle)
        print(u"   %-14s 出现 %d 次 %s" % (label, n, u"✓" if n == 1 else u"✗"))
        bad += 0 if n == 1 else 1
    print(u"复核失败 = %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
