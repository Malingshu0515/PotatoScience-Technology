# -*- coding: utf-8 -*-
u"""_zf125_java.py —— ZF125 对**既有 Java** 的 6 处接线（新文件已由 write 工具直接写好）

为什么用脚本而不是编辑器：这些既有文件是 **CRLF**（`.gitattributes` 里写死 `* -text`，
工程明确"一个字节都不转换"），而新写的文件是 LF —— 两种换行在这个工程里是共存的
（.gitattributes 的注释里记着实测：java 42 个 CRLF / 104 个 LF）。所以改既有文件时
必须**沿用该文件自己的换行**，脚本里按文件现读现判。

六处：
  A `ModBlocks.java`        追加：控制器方块 + 物品 + 方块实体 + 接线口 + 接线口方块实体
  B `ModItems.java`         创造页加一行（⚠ ZF109 漏过一次，见 §4.82）
  C `ModMenus.java`         菜单类型
  D `PotatoST.java`         能力：控制器的柴油罐（只进不出）+ 接线口的出电口（只出不进）
  E `PotatoSTClient.java`   界面登记
  F `StatusLampPart.java`   状态码 19「结构不完整」→ 黄灯 + no_structure 后缀

⚠ **本脚本跑过之后改错过一处（已修，留档）**：A 处第一版忘了把锚点接回新内容里，
   于是 `LITHIUM_BATTERY_PLANT.get()).build(null));` 那一行被吃掉、编译失败。
   补回由 `_zf125_fixA.py` 做（它是**逐字节**证明只补了这一行的那个脚本）。
   本文件已同步改成 `A_NEW = A_ANCHOR + …`，所以再跑一次是**安全**的（锚点已不在，会报错停手）。

跑法：
    python build\\zftools\\_zf125_java.py
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")

notes, fails = [], []


def read(path):
    return io.open(path, encoding="utf-8", newline=u"").read()


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def apply(name, rel, old, new):
    u"""把 old（含换行）换成 new；old 必须**恰好命中 1 次**。"""
    path = os.path.join(ROOT, rel)
    text = read(path)
    nl = u"\r\n" if u"\r\n" in text else u"\n"
    old_n = old.replace(u"\n", nl)
    new_n = new.replace(u"\n", nl)
    n = text.count(old_n)
    if n != 1:
        fails.append(u"%s：锚点命中 %d 次（要 1 次）—— 停手，别瞎改" % (name, n))
        return
    io.open(path, "w", encoding="utf-8", newline=u"").write(text.replace(old_n, new_n, 1))
    after = read(path)
    if new_n not in after:
        fails.append(u"%s：写进去之后回读不到新内容" % name)
        return
    notes.append(u"%s  %s  锚点 1 次命中  换行 %s  新 sha1 %s"
                 % (name, rel.replace(u"\\", u"/"), nl.encode(u"unicode_escape").decode(u"ascii"),
                    sha(path)[:12]))


# ======================= A. ModBlocks =======================

A_ANCHOR = u"                    LITHIUM_BATTERY_PLANT.get()).build(null));\n"

# ⚠ 第一版这里写成 apply(..., A_ANCHOR, A_NEW) 而 A_NEW 里**忘了把锚点接回去** ⇒
#    LITHIUM_BATTERY_PLANT.get()).build(null)); 那一行被整行吃掉、编译报 1012/1014 行
#    「非法的表达式开始」。已由 _zf125_fixA.py 补回；本文件同步改成 A_ANCHOR + 新内容，
#    留档以示"本该这么写"。（B/C/D/E 四处本来就是 NEW = ANCHOR + …，没这个毛病。）
A_NEW = A_ANCHOR + u"""
    // ===== 大型柴油发电机（0.11 ZF125）=====

    /**
     * 柴油发电机控制器：用户图纸第 1 层最前排正中间那一格（图上写着 9）。
     *
     * <p>用户原话：「加一个大型柴油发电机 3x5x2 …（30 格图纸）以柴油发电机控制器为正方向
     * 右键打开GUI 显示流体储罐（8000mB）工作指示灯 检测到红石信号停机
     * 可以用流体泵泵入柴油 或用柴油桶/含有柴油的油桶右键添加柴油 每t消耗1mb柴油 7.2kFE」。</p>
     *
     * <p><b>有朝向</b>（{@code FACING} = 机器正面）：机器朝它背后铺 5 排、向上 2 层，
     * 结构定义在 {@link DieselGeneratorStructure}。整台机器<b>没有 OBJ 模型</b> ——
     * 外观就是玩家摆的那 30 格方块。</p>
     */
    public static final DeferredBlock<Block> DIESEL_GENERATOR =
            BLOCKS.register("diesel_generator_controller", () -> new DieselGeneratorBlock(
                    BlockBehaviour.Properties.of()
                            .strength(5.0F, 6.0F)
                            .sound(SoundType.METAL)));

    /** 柴油发电机控制器物品：Shift 显示 30 格摆放图与工作规则 */
    public static final DeferredHolder<Item, BlockItem> DIESEL_GENERATOR_ITEM =
            ModItems.ITEMS.register("diesel_generator_controller",
                    () -> new BlockItem(DIESEL_GENERATOR.get(), new Item.Properties()) {
                        @Override
                        public void appendHoverText(ItemStack stack, TooltipContext context,
                                                    List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
                            DieselGeneratorBlock.appendTooltip(stack, context, tooltipComponents, tooltipFlag);
                        }
                    });

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<DieselGeneratorBlockEntity>>
            DIESEL_GENERATOR_BE = BLOCK_ENTITIES.register("diesel_generator_controller",
            () -> BlockEntityType.Builder.of(DieselGeneratorBlockEntity::new,
                    DIESEL_GENERATOR.get()).build(null));

    /**
     * 接线口：成型时替换掉控制器正上方那一格【接线块】。**没有物品形态**
     * （挖它掉的是接线块），贴图与接线块一样，所以玩家看不出被换过 ——
     * 但它是唯一能<b>出电</b>的地方（{@code canExtract}，邻居 INPUT 端子会来抽）。
     *
     * <p>⚠ 与合金炉的接线口有一处关键差别：那个是 {@code RenderShape.INVISIBLE}
     * （整台机器由控制器的 OBJ 画），这台机器没有 OBJ ⇒ 接线口必须照常渲染，
     * 否则机器顶上会破一个洞。</p>
     */
    public static final DeferredBlock<Block> DIESEL_GENERATOR_PORT = BLOCKS.register("diesel_generator_port",
            () -> new DieselGeneratorPortBlock(BlockBehaviour.Properties.of()
                    .strength(5.0F, 6.0F)
                    .sound(SoundType.METAL)
                    .requiresCorrectToolForDrops()
                    .noLootTable()));

    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<DieselGeneratorPortBlockEntity>>
            DIESEL_GENERATOR_PORT_BE = BLOCK_ENTITIES.register("diesel_generator_port",
            () -> BlockEntityType.Builder.of(DieselGeneratorPortBlockEntity::new,
                    DIESEL_GENERATOR_PORT.get()).build(null));
"""

# ======================= B. ModItems =======================

B_ANCHOR = u"                        output.accept(STAR_CHART_TOME.get());// ← 新增（0.11 ZF122 星仪图之章）\n"

B_NEW = B_ANCHOR + \
    u"                        output.accept(ModBlocks.DIESEL_GENERATOR_ITEM.get());// ← 新增（0.11 ZF125 大型柴油发电机控制器）\n"

# ======================= C. ModMenus =======================

C_ANCHOR = (u"    public static final DeferredHolder<MenuType<?>, MenuType<LithiumBatteryPlantMenu>>\n"
            u"            LITHIUM_BATTERY_PLANT_MENU =\n"
            u"            MENU_TYPES.register(\"lithium_battery_plant\",\n"
            u"                    () -> new MenuType<>(LithiumBatteryPlantMenu::new, FeatureFlags.DEFAULT_FLAGS));\n")

C_NEW = C_ANCHOR + u"""
    /** 大型柴油发电机菜单（0.11 ZF125）—— 一个机器槽都没有，只有一个 8000 mB 柴油罐 + 一盏工作指示灯 */
    public static final DeferredHolder<MenuType<?>, MenuType<DieselGeneratorMenu>> DIESEL_GENERATOR_MENU =
            MENU_TYPES.register("diesel_generator_controller",
                    () -> new MenuType<>(DieselGeneratorMenu::new, FeatureFlags.DEFAULT_FLAGS));
"""

# ======================= D. PotatoST 能力 =======================

D_ANCHOR = u"        // ⚠ 锂电池构造间**没有能量能力**：用户原话末句「不消耗电」⇒ 与加氢脱硫反应仓同一条路。\n"

D_NEW = D_ANCHOR + u"""
        // ㊿ 大型柴油发电机（0.11 ZF125）：**出电口挂在接线口那一格**，控制器本体不登记能量能力 ——
        //     这是本工程多方块机器的老规矩（电力高炉 / 合金炉都是"电只从接线口走"）。
        //     接线口交出来的是"只出不进"的接口（canExtract 恒真），邻居的 INPUT 端子会主动来抽；
        //     结构没成型时 getEnergyStorage() 返回 null ⇒ 整个能力不存在。
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.DIESEL_GENERATOR_PORT_BE.get(),
                (port, side) -> port.getEnergyStorage());

        // 51 大型柴油发电机：8000 mB 柴油罐 —— **只进不出**（泵灌得进来、一滴抽不出去）。
        //     控制器本体与接线口**都**登记：玩家把泵放控制器正面、或放机器顶上（接线口上方）都能喂它，
        //     两条路没有方向限制（用户原话「可以用流体泵泵入柴油」）。
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.DIESEL_GENERATOR_BE.get(),
                (machine, side) -> machine.getFluidHandler());
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.DIESEL_GENERATOR_PORT_BE.get(),
                (port, side) -> port.getFluidHandler());
"""

# ======================= E. PotatoSTClient =======================

E_ANCHOR = (u"        event.register(ModMenus.LITHIUM_BATTERY_PLANT_MENU.get(),\n"
            u"                com.potatost.mod.client.LithiumBatteryPlantScreen::new);   // 0.11 ZF112 锂电池构造间\n")

E_NEW = E_ANCHOR + (u"        event.register(ModMenus.DIESEL_GENERATOR_MENU.get(),\n"
                    u"                com.potatost.mod.client.DieselGeneratorScreen::new);   // 0.11 ZF125 大型柴油发电机\n")

# ======================= F. StatusLampPart =======================

F1_OLD = u"import com.potatost.mod.CombustionChamberBlockEntity;\nimport com.potatost.mod.FluidExchangerBlockEntity;\n"
F1_NEW = (u"import com.potatost.mod.CombustionChamberBlockEntity;\n"
          u"import com.potatost.mod.DieselGeneratorBlockEntity;\n"
          u"import com.potatost.mod.FluidExchangerBlockEntity;\n")

F2_OLD = (u"            case LithiumBatteryPlantBlockEntity.STATUS_NO_ACID,\n"
          u"                 LithiumBatteryPlantBlockEntity.STATUS_INPUTS -> YELLOW;\n"
          u"            default -> OFF;\n")
F2_NEW = (u"            case LithiumBatteryPlantBlockEntity.STATUS_NO_ACID,\n"
          u"                 LithiumBatteryPlantBlockEntity.STATUS_INPUTS -> YELLOW;\n"
          u"            // 0.11 ZF125：大型柴油发电机的 19「结构不完整」—— 开不了工，黄灯\n"
          u"            case DieselGeneratorBlockEntity.STATUS_NO_STRUCTURE -> YELLOW;\n"
          u"            default -> OFF;\n")

F3_OLD = (u"            case LithiumBatteryPlantBlockEntity.STATUS_NO_ACID -> \"no_acid\";\n"
          u"            case LithiumBatteryPlantBlockEntity.STATUS_INPUTS -> \"inputs\";\n"
          u"            default -> \"empty\";\n")
F3_NEW = (u"            case LithiumBatteryPlantBlockEntity.STATUS_NO_ACID -> \"no_acid\";\n"
          u"            case LithiumBatteryPlantBlockEntity.STATUS_INPUTS -> \"inputs\";\n"
          u"            // 0.11 ZF125：大型柴油发电机的 19\n"
          u"            case DieselGeneratorBlockEntity.STATUS_NO_STRUCTURE -> \"no_structure\";\n"
          u"            default -> \"empty\";\n")

F4_OLD = (u"     * 另外新起两个号：<b>10 = 氮气不够</b>、<b>11 = 催化剂槽里没有铁粉</b>。</p>\n")
F4_NEW = F4_OLD + (u"     *\n"
                   u"     * <p>0.11 ZF125：大型柴油发电机新起 <b>19 = 结构不完整</b> —— 6~18 全被占了，\n"
                   u"     * 语义都对不上「这台机器的壳没搭完」⇒ 只能新起号（这条规矩的另一半：\n"
                   u"     * 不能共用时得说清楚为什么）。</p>\n")


def main():
    apply(u"A ModBlocks", r"src\main\java\com\potatost\mod\ModBlocks.java", A_ANCHOR, A_NEW)
    apply(u"B ModItems", r"src\main\java\com\potatost\mod\ModItems.java", B_ANCHOR, B_NEW)
    apply(u"C ModMenus", r"src\main\java\com\potatost\mod\ModMenus.java", C_ANCHOR, C_NEW)
    apply(u"D PotatoST", r"src\main\java\com\potatost\mod\PotatoST.java", D_ANCHOR, D_NEW)
    apply(u"E PotatoSTClient", r"src\main\java\com\potatost\mod\PotatoSTClient.java", E_ANCHOR, E_NEW)
    apply(u"F1 StatusLampPart 导入", r"src\main\java\com\potatost\mod\client\gui\parts\StatusLampPart.java",
          F1_OLD, F1_NEW)
    apply(u"F2 StatusLampPart 黄灯", r"src\main\java\com\potatost\mod\client\gui\parts\StatusLampPart.java",
          F2_OLD, F2_NEW)
    apply(u"F3 StatusLampPart 后缀", r"src\main\java\com\potatost\mod\client\gui\parts\StatusLampPart.java",
          F3_OLD, F3_NEW)
    apply(u"F4 StatusLampPart 注释", r"src\main\java\com\potatost\mod\client\gui\parts\StatusLampPart.java",
          F4_OLD, F4_NEW)

    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改动 %d 处" % len(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
