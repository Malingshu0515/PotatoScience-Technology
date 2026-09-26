# -*- coding: utf-8 -*-
u"""_zf125_verify.py —— ZF125「大型柴油发电机」常驻校验（静态，不跑服务器）

用户原话（一条消息给全图纸与功能）：
「加一个大型柴油发电机 3x5x2 第一层【耐热金属块】【流体泵】【耐热金属块】，
【耐热金属块】【低级发电机】【耐热金属块】，【耐热金属块】【燃烧反应室】【耐热金属块】，
【耐热金属块】【低级发电机】【耐热金属块】，【耐热金属块】【柴油发电机控制器】【耐热金属块】
第二层 【一般金属块】【耐热金属块】【一般金属块】，【铜块】【铜格栅】【铜块】，【铜块】【铜格栅】【铜块】，
【铜块】【铜格栅】【铜块】，【一般金属块】【接线块】【一般金属块】（铜无论氧化/涂蜡程度都可以）
以柴油发电机控制器为正方向 右键打开GUI 显示流体储罐（8000mB）工作指示灯 检测到红石信号停机
可以用流体泵泵入柴油 或用柴油桶/含有柴油的油桶右键添加柴油 每t消耗1mb柴油 7.2kFE
柴油发电机控制器配方;【】【流体管道】【】，【铜块】【熔炉】【铜块】，【】【钢板】【】」

四段判据：
  A 结构定义（30 格图纸逐字 + 铜 8/8 变体 + 判定不许用 holes.isEmpty）
  B 控制器方块与方块实体（8000/1/7200 + 五档状态 + 红石 + 倒柴油 + 接线口复位）
  C 接线口（贴图=接线块、未成型不给电、控制器本体不登记能量能力）
  D 六个既有文件"只动了该动的地方"（**改前件 = 现状删掉那一段插入**，逐字节）
  E 资源与数据（贴图/模型/配方/标签/四语言 475 键）
  F 往轮判据里的活体数字跟上（464 → 482）

⚠ 本脚本**只读**，不改任何文件；退出码 0 = 全绿。
跑法：
    python build\\zftools\\_zf125_verify.py
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PngRecolor import read_png   # noqa: E402

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")
TOOLS = os.path.join(ROOT, r"build\zftools")
BK = r"C:\PotatoST救援\zf125_pre"

passed = 0
failed = 0
fails = []


def check(name, ok):
    global passed, failed
    if ok:
        passed += 1
        print(u"  [OK]   %s" % name)
    else:
        failed += 1
        fails.append(name)
        print(u"  [FAIL] %s" % name)
    return ok


def read(p):
    return io.open(p, encoding=u"utf-8", newline=u"").read()


def rel(*parts):
    return os.path.join(ROOT, *parts)


def jload(p):
    try:
        return json.loads(read(p))
    except Exception as e:
        fails.append(u"JSON 读不了：%s（%s）" % (p, e))
        return None


def only_inserted(rel_path, marker_list, name):
    u"""强判据：改前件 == 现状**删掉一段连续插入**（没删东西、没挪位置）。"""
    cur_path = rel(*rel_path.split(u"/"))
    bak_path = os.path.join(BK, *rel_path.split(u"/"))
    if not os.path.exists(bak_path):
        return check(u"%s：改前件在 zf125_pre" % name, False)
    before, cur = read(bak_path), read(cur_path)
    ok = True
    p = 0
    while p < min(len(before), len(cur)) and before[p] == cur[p]:
        p += 1
    s = 0
    while (s < min(len(before), len(cur)) - p
           and before[len(before) - 1 - s] == cur[len(cur) - 1 - s]):
        s += 1
    inserted = cur[p:len(cur) - s]
    if p + s != len(before):
        ok = False
    for m in marker_list:
        if m not in inserted:
            ok = False
    return check(u"%s：改前件 = 现状删掉 %d 字符的插入（%s）"
                 % (name, len(cur) - len(before), u"、".join(marker_list)[:60]), ok)


def only_added_snippets(rel_path, snippets, name):
    u"""同一类判据，但允许**多处**互不相邻的插入：把每段插入原样抠掉，必须逐字节回到改前件。"""
    cur_path = rel(*rel_path.split(u"/"))
    bak_path = os.path.join(BK, *rel_path.split(u"/"))
    if not os.path.exists(bak_path):
        return check(u"%s：改前件在 zf125_pre" % name, False)
    before, cur = read(bak_path), read(cur_path)
    stripped = cur
    bad = []
    for sn in snippets:
        if stripped.count(sn) != 1:
            bad.append(u"片段命中 %d 次" % stripped.count(sn))
            continue
        stripped = stripped.replace(sn, u"", 1)
    return check(u"%s：抠掉 %d 段插入后与改前件逐字节相同%s"
                 % (name, len(snippets), u"" if not bad else u"（%s）" % u"、".join(bad)),
                 not bad and stripped == before)


# ==================================================================
# A 结构定义
# ==================================================================

def part_a():
    print(u"\n===== A 结构定义（DieselGeneratorStructure.java）=====")
    p = os.path.join(JAVA, u"DieselGeneratorStructure.java")
    if not check(u"A0 文件在", os.path.exists(p)):
        return
    t = read(p)
    check(u"A1 尺寸 3×5×2 = 30 格",
          re.search(r"WIDTH = 3;", t) and re.search(r"DEPTH = 5;", t)
          and re.search(r"HEIGHT = 2;", t) and re.search(r"CELLS = WIDTH \* DEPTH \* HEIGHT", t))
    check(u"A2 控制器在第 1 层 / 最前排 / 正中间（0,4,1）",
          re.search(r"CTRL_Y = 0;", t) and re.search(r"CTRL_J = 4;", t)
          and re.search(r"CTRL_I = 1;", t))
    # 图纸逐字（用户原话转写成字符）
    want = [
        u"\"RPR\"", u"\"RGR\"", u"\"RBR\"", u"\"RGR\"", u"\"RCR\"",
        u"\"MRM\"", u"\"OKO\"", u"\"OKO\"", u"\"OKO\"", u"\"MWM\"",
    ]
    miss = [w for w in want if w not in t]
    check(u"A3 图纸 10 行逐字照抄用户原话（%s）" % (u"全中" if not miss else u"缺 " + u",".join(miss)),
          not miss)
    check(u"A4 九种格子类型都在",
          all(re.search(r"\b%s\b" % k, t) for k in
              (u"HEAT", u"COMMON", u"PUMP", u"GENERATOR", u"CHAMBER",
               u"CONTROLLER", u"WIRING", u"COPPER", u"GRATE")))
    pairs = [(u"HEAT", u"ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get()"),
             (u"COMMON", u"ModBlocks.COMMON_METAL_BLOCK.get()"),
             (u"PUMP", u"ModBlocks.FLUID_PUMP.get()"),
             (u"GENERATOR", u"ModBlocks.LOW_GENERATOR.get()"),
             (u"CHAMBER", u"ModBlocks.COMBUSTION_CHAMBER.get()"),
             (u"CONTROLLER", u"ModBlocks.DIESEL_GENERATOR.get()"),
             (u"WIRING", u"ModBlocks.WIRING_BLOCK.get()"),
             (u"COPPER", u"Blocks.COPPER_BLOCK"),
             (u"GRATE", u"Blocks.COPPER_GRATE")]
    bad = [b for k, b in pairs
           if not re.search(r"case %s: return %s;" % (k, re.escape(b)), t)]
    check(u"A5 blockFor 九种映射全对（%s）" % (u"全中" if not bad else u"错 " + u",".join(bad)),
          not bad)
    copper = [u"COPPER_BLOCK", u"EXPOSED_COPPER", u"WEATHERED_COPPER", u"OXIDIZED_COPPER",
              u"WAXED_COPPER_BLOCK", u"WAXED_EXPOSED_COPPER", u"WAXED_WEATHERED_COPPER",
              u"WAXED_OXIDIZED_COPPER"]
    # ⚠ 集合里最后一个元素后面没有逗号（是 `)`），所以判据要认两种收尾
    missing = [c for c in copper
               if not re.search(r"Blocks\.%s[,)]" % c, t)]
    check(u"A6 铜块 8 个变体全在（氧化 × 涂蜡）%s"
          % (u"" if not missing else u"缺 " + u",".join(missing)), not missing)
    grates = [u"COPPER_GRATE", u"EXPOSED_COPPER_GRATE", u"WEATHERED_COPPER_GRATE",
              u"OXIDIZED_COPPER_GRATE", u"WAXED_COPPER_GRATE", u"WAXED_EXPOSED_COPPER_GRATE",
              u"WAXED_WEATHERED_COPPER_GRATE", u"WAXED_OXIDIZED_COPPER_GRATE"]
    missing = [c for c in grates if not re.search(r"Blocks\.%s[,)]" % c, t)]
    check(u"A7 铜格栅 8 个变体全在%s"
          % (u"" if not missing else u"（缺 " + u",".join(missing) + u"）"), not missing)
    check(u"A8 接线块那一格认「接线块 or 接线口」两种",
          u"ModBlocks.WIRING_BLOCK.get()) || isPort(state)" in t)
    check(u"A9 offset 朝背后铺 + 向上叠（getOpposite / getClockWise / above）",
          u"relative(facing.getOpposite(), CTRL_J - j)" in t
          and u"relative(facing.getClockWise(), i - CTRL_I)" in t
          and u"above(y - CTRL_Y)" in t)
    # ⚠ 注释里**故意**引用了 holes.isEmpty() 当反面教材（§4.56），所以只查代码那一句
    check(u"A10 判定用的是 holeCount，不是 holes.isEmpty()（§4.56 那一课）",
          u"return this.holeCount == 0;" in t
          and re.search(r"return\s+holes\.isEmpty\(\)", t) is None)
    sym = [u"RPR", u"RGR", u"RBR", u"RCR", u"MRM", u"OKO", u"MWM"]
    check(u"A11 十行全是回文 ⇒ 左右镜像不会搭错（%d 行）" % len(want),
          all(s == s[::-1] for s in sym))
    check(u"A12 inspect 有「不收集明细」那条路（limit <= 0）", u"if (limit > 0 && holes.size() < limit)" in t)


# ==================================================================
# B 控制器
# ==================================================================

def part_b():
    print(u"\n===== B 控制器（方块 + 方块实体）=====")
    be = os.path.join(JAVA, u"DieselGeneratorBlockEntity.java")
    blk = os.path.join(JAVA, u"DieselGeneratorBlock.java")
    if not check(u"B0 两个文件都在", os.path.exists(be) and os.path.exists(blk)):
        return
    b = read(be)
    k = read(blk)
    check(u"B1 罐 8000 mB（用户原话 8000mB）", u"TANK_CAPACITY = 8000;" in b)
    check(u"B2 每 tick 烧 1 mB 柴油（用户原话 每t消耗1mb柴油）", u"MB_PER_TICK = 1;" in b)
    check(u"B3 每 tick 发 7200 FE（用户原话 7.2kFE）", u"ENERGY_PER_TICK = 7200;" in b)
    check(u"B4 缓冲（ZF126 起 18000 —— 用户点名给的；与产量解耦）",
          u"MAX_ENERGY = 18_000;" in b and u"MAX_ENERGY = ENERGY_PER_TICK;" not in b
          and u"MAX_ENERGY = 7200;" not in b)
    check(u"B5 结构不完整 = 新状态码 19（共享表里没被占）",
          u"STATUS_NO_STRUCTURE = 19;" in b)
    check(u"B6 红石信号 = 停机（STATUS_DISABLED + return）",
          u"hasNeighborSignal(this.worldPosition)" in b and u"STATUS_DISABLED;" in b)
    check(u"B7 结构不全就不烧油（STATUS_NO_STRUCTURE + return）",
          re.search(r"if \(!this\.formed\) \{\s*\n\s*this\.status = STATUS_NO_STRUCTURE;\s*\n\s*return;", b)
          is not None)
    check(u"B8 缓冲满就暂停烧油（hasRoom → STATUS_OUTPUT_FULL）",
          u"private boolean hasRoom()" in b and u"MAX_ENERGY - this.energy >= ENERGY_PER_TICK" in b
          and u"STATUS_OUTPUT_FULL;" in b)
    check(u"B9 罐里不足 1 mB 就不开工（STATUS_EMPTY）",
          u"this.tank.getFluidAmount() < MB_PER_TICK" in b and u"STATUS_EMPTY;" in b)
    check(u"B10 结算：扣 MB_PER_TICK 柴油 + 加 ENERGY_PER_TICK 电",
          u"this.tank.drain(MB_PER_TICK, IFluidHandler.FluidAction.EXECUTE);" in b
          and u"this.energy += ENERGY_PER_TICK;" in b)
    check(u"B11 零物品槽（SLOT_COUNT = 0）", u"public static final int SLOT_COUNT = 0;" in b)
    check(u"B12 空手右键开界面（openMenu）", u"serverPlayer.openMenu(be);" in k)
    check(u"B13 缺格上报前 4 处（reportHoles + invalid 键）",
          u"public static void reportHoles(" in k and u"be.findHoles(4)" in k
          and u"gui.potato_s_t.diesel_generator.invalid" in k)
    check(u"B14 倒柴油两条路：原版柴油桶（整桶 1000）+ FluidContainerItem",
          u"stack.is(ModItems.DIESEL_BUCKET.get())" in k
          and u"stack.getItem() instanceof FluidContainerItem" in k
          and u"POUR_PER_CLICK = 1000;" in k)
    check(u"B15 柴油桶倒空后还一个空铁桶（ItemUtils.createFilledResult）",
          u"ItemUtils.createFilledResult(stack, player, new ItemStack(Items.BUCKET))" in k)
    check(u"B16 只认柴油：FluidType 比对（含流动变体）",
          u"stack.getFluid().getFluidType() == ModFluids.DIESEL_TYPE.get()" in b)
    check(u"B17 控制器被挖掉时把接线口换回接线块",
          u"DieselGeneratorStructure.portPos(pos)" in k and u"isPort(level.getBlockState(port))" in k)
    check(u"B18 挖控制器掉控制器本身（getDrops）",
          u"return List.of(new ItemStack(this));" in k)
    check(u"B19 有朝向：FACING + 放置时朝玩家（getOpposite）",
          u"public static final DirectionProperty FACING = HorizontalDirectionalBlock.FACING;" in k
          and u"context.getHorizontalDirection().getOpposite()" in k)
    check(u"B20 双端 ticker（§4.26）",
          u"createTickerHelper(type, ModBlocks.DIESEL_GENERATOR_BE.get()," in k)
    check(u"B21 流体能力：只进不出（drain 两个重载都返回空）",
          b.count(u"return FluidStack.EMPTY;") >= 2 and u"if (!isDiesel(resource)) {" in b)
    check(u"B22 存盘：只存电与罐（结构不存盘，读盘后第一 tick 自己算）",
          u"tag.putInt(\"energy\", this.energy);" in b and u"this.tank.writeToNBT(registries, tankTag);" in b
          and u"this.structureTimer = 0;" in b)


# ==================================================================
# C 接线口
# ==================================================================

def part_c():
    print(u"\n===== C 接线口 =====")
    pb = os.path.join(JAVA, u"DieselGeneratorPortBlock.java")
    pe = os.path.join(JAVA, u"DieselGeneratorPortBlockEntity.java")
    if not check(u"C0 两个文件都在", os.path.exists(pb) and os.path.exists(pe)):
        return
    b = read(pb)
    e = read(pe)
    mb = read(os.path.join(JAVA, u"ModBlocks.java"))
    check(u"C1 没有物品形态（ModBlocks 里没有 DIESEL_GENERATOR_PORT_ITEM）",
          u"DIESEL_GENERATOR_PORT_ITEM" not in mb)
    check(u"C2 RenderShape.MODEL（没 OBJ ⇒ 不能 INVISIBLE，否则机器顶上破洞）",
          u"return RenderShape.MODEL;" in b and u"return RenderShape.INVISIBLE" not in b)
    check(u"C3 摸它右键 = 开控制器界面",
          u"serverPlayer.openMenu(be);" in b and u"instanceof DieselGeneratorBlockEntity be" in b)
    check(u"C4 挖它掉一个接线块（WIRING_BLOCK_ITEM）",
          u"new ItemStack(ModBlocks.WIRING_BLOCK_ITEM.get())" in b)
    check(u"C5 未成型 / 没主控 ⇒ 能力返回 null（不给电）",
          u"master != null && master.isFormed() ? master.getEnergyStorage() : null;" in e)
    check(u"C6 主控就在正下方（worldPosition.below()）", u"this.worldPosition.below()" in e)
    check(u"C7 接线口也收柴油（getFluidHandler 转给主控）",
          u"return master == null ? null : master.getFluidHandler();" in e)


# ==================================================================
# D 六个既有文件：只动了该动的地方
# ==================================================================

def part_d():
    print(u"\n===== D 既有文件的改动面 =====")
    mb = read(os.path.join(JAVA, u"ModBlocks.java"))
    check(u"D1 ModBlocks 五个注册都在",
          all(x in mb for x in (u"DIESEL_GENERATOR =", u"DIESEL_GENERATOR_ITEM =",
                               u"DIESEL_GENERATOR_BE =", u"DIESEL_GENERATOR_PORT =",
                               u"DIESEL_GENERATOR_PORT_BE =")))
    mi = read(os.path.join(JAVA, u"ModItems.java"))
    check(u"D2 进创造页了（§4.82 那次就是这么漏的）",
          u"output.accept(ModBlocks.DIESEL_GENERATOR_ITEM.get());" in mi)
    mm = read(os.path.join(JAVA, u"ModMenus.java"))
    check(u"D3 菜单类型注册（id = diesel_generator_controller）",
          u"DIESEL_GENERATOR_MENU =" in mm and u"\"diesel_generator_controller\"" in mm)
    ps = read(os.path.join(JAVA, u"PotatoST.java"))
    check(u"D4 能量能力挂在**接线口**上（电只从接线口出）",
          re.search(r"Capabilities\.EnergyStorage\.BLOCK,\s*\n\s*ModBlocks\.DIESEL_GENERATOR_PORT_BE\.get\(\)", ps)
          is not None)
    check(u"D5 控制器本体**不**登记能量能力（多方块老规矩）",
          re.search(r"Capabilities\.EnergyStorage\.BLOCK,\s*\n\s*ModBlocks\.DIESEL_GENERATOR_BE\.get\(\)", ps)
          is None)
    check(u"D6 柴油：控制器与接线口都登记流体能力（六面同权）",
          ps.count(u"ModBlocks.DIESEL_GENERATOR_BE.get(),\n                (machine, side) -> machine.getFluidHandler()")
          + ps.count(u"ModBlocks.DIESEL_GENERATOR_PORT_BE.get(),\n                (port, side) -> port.getFluidHandler()") == 2)
    pc = read(os.path.join(JAVA, u"PotatoSTClient.java"))
    check(u"D7 界面登记（DieselGeneratorScreen）",
          u"ModMenus.DIESEL_GENERATOR_MENU.get()" in pc and u"DieselGeneratorScreen::new" in pc)
    sl = read(os.path.join(JAVA, u"client", u"gui", u"parts", u"StatusLampPart.java"))
    check(u"D8 状态灯：19 → 黄灯 + no_structure 后缀",
          u"case DieselGeneratorBlockEntity.STATUS_NO_STRUCTURE -> YELLOW;" in sl
          and u"case DieselGeneratorBlockEntity.STATUS_NO_STRUCTURE -> \"no_structure\";" in sl)

    print(u"\n  --- 「只动了该动的地方」逐字节 ---")
    only_inserted(r"src/main/java/com/potatost/mod/ModBlocks.java",
                  [u"diesel_generator_controller", u"DIESEL_GENERATOR_PORT_BE"], u"D9 ModBlocks")
    # ⚠ ZF127 retarget：ModItems 从本轮起是**三段**互不相邻的插入（ZF125 的柴油机那行 +
    #   ZF127 的银线/银线轴登记 + ZF127 的创造页两行）⇒ 单段前缀后缀那套不成立，
    #   换成"把每段原样抠掉，必须逐字节回到 zf125_pre"。
    #   两段原文是**从两个改前件算出来的**（zf125_pre→zf127_pre、zf127_pre→盘上），不手抄
    #   —— 这段判据是逐字节的，手抄最容易把行尾空格抄错。
    only_added_snippets(r"src/main/java/com/potatost/mod/ModItems.java", [
        u'    output.accept(ModBlocks.DIESEL_GENERATOR_ITEM.get());// ← 新增（0.11 ZF125 大型柴油发电机控制器）\n                    ',
        u'\n    // ===== 银线 / 银线轴（0.11 ZF127）=====\n    /**\n     * 银线：银线轴的原料（2 个银锭 → 4 根，与铜线逐字对应）。\n     *\n     * <p><b>⚠ 贴图先不画</b>（用户点名「材质先不画」）⇒ 模型借原版<b>铁粒</b>占位\n     * （见 {@code models/item/silver_wire.json}），与"电容借铁粒 / 硅借火药"同一个做法。</p>\n     */\n    public static final DeferredItem<Item> SILVER_WIRE =\n            ITEMS.register("silver_wire", () -> new Item(new Item.Properties()));\n\n    /**\n     * 银线轴：与铜线轴<b>逐项一致</b>（32 点耐久、右键连端子、耗尽返还空线轴、连接距离 16 格、\n     * 线径一样粗），只有两处不同 —— ① 线缆渲染成<b>银白色</b>；② 单线速率\n     * {@link TerminalBlockEntity#SILVER_TRANSFER_RATE} = <b>16134 FE/t</b>（铜线 2048）。\n     *\n     * <p>用户原话：「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）\n     * 材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t」。</p>\n     *\n     * <p><b>⚠ 贴图先不画</b>：模型借原版<b>铁锭</b>占位（见 {@code models/item/silver_wire_spool.json}）。</p>\n     */\n    public static final DeferredItem<Item> SILVER_WIRE_SPOOL =\n            ITEMS.register("silver_wire_spool",\n                    () -> new Item(new Item.Properties().durability(32)));\n',
        u'SILVER_WIRE.get());            // ← 0.11 ZF127 银线\n                        output.accept(SILVER_WIRE_SPOOL.get());      // ← 0.11 ZF127 银线轴\n                        output.accept('], u"D10 ModItems（3 段插入）")
    only_inserted(r"src/main/java/com/potatost/mod/ModMenus.java",
                  [u"DIESEL_GENERATOR_MENU"], u"D11 ModMenus")
    only_inserted(r"src/main/java/com/potatost/mod/PotatoST.java",
                  [u"DIESEL_GENERATOR_PORT_BE"], u"D12 PotatoST")
    only_inserted(r"src/main/java/com/potatost/mod/PotatoSTClient.java",
                  [u"DieselGeneratorScreen"], u"D13 PotatoSTClient")
    # ⚠ StatusLampPart 这一轮是**四处**互不相邻的插入（导入 / 黄灯 / 后缀 / 注释），
    #    单段前缀后缀那套在这里不成立 ⇒ 换成"把每段原样抠掉，必须回到改前件"
    only_added_snippets(r"src/main/java/com/potatost/mod/client/gui/parts/StatusLampPart.java", [
        u"import com.potatost.mod.DieselGeneratorBlockEntity;\n",
        u"            // 0.11 ZF125：大型柴油发电机的 19「结构不完整」—— 开不了工，黄灯\n"
        u"            case DieselGeneratorBlockEntity.STATUS_NO_STRUCTURE -> YELLOW;\n",
        u"            // 0.11 ZF125：大型柴油发电机的 19\n"
        u"            case DieselGeneratorBlockEntity.STATUS_NO_STRUCTURE -> \"no_structure\";\n",
        u"     *\n"
        u"     * <p>0.11 ZF125：大型柴油发电机新起 <b>19 = 结构不完整</b> —— 6~18 全被占了，\n"
        u"     * 语义都对不上「这台机器的壳没搭完」⇒ 只能新起号（这条规矩的另一半：\n"
        u"     * 不能共用时得说清楚为什么）。</p>\n",
    ], u"D14 StatusLampPart")
    only_inserted(r"src/main/resources/data/minecraft/tags/block/mineable/pickaxe.json",
                  [u"potato_s_t:diesel_generator_controller", u"potato_s_t:diesel_generator_port"],
                  u"D15 pickaxe 标签")
    only_inserted(r"src/main/resources/data/minecraft/tags/block/needs_stone_tool.json",
                  [u"potato_s_t:diesel_generator_controller", u"potato_s_t:diesel_generator_port"],
                  u"D16 needs_stone_tool 标签")


# ==================================================================
# E 资源与数据
# ==================================================================

def part_e():
    print(u"\n===== E 资源与数据 =====")
    tex = os.path.join(ASSETS, u"textures", u"block", u"diesel_generator_controller.png")
    if check(u"E1 控制器贴图在", os.path.exists(tex)):
        try:
            w, h, _ = read_png(tex)
            check(u"E1b 贴图是真 PNG 且 16×16（实测 %d×%d）" % (w, h), (w, h) == (16, 16))
        except Exception as ex:
            check(u"E1b 贴图能解码（%s）" % ex, False)
    bs = jload(os.path.join(ASSETS, u"blockstates", u"diesel_generator_controller.json"))
    check(u"E2 方块状态覆盖四个朝向",
          isinstance(bs, dict) and set(bs.get(u"variants", {}).keys())
          == {u"facing=north", u"facing=east", u"facing=south", u"facing=west"})
    mbm = jload(os.path.join(ASSETS, u"models", u"block", u"diesel_generator_controller.json"))
    # ⚠ ZF128（**素材线的改动，我这边跟平判据**）：控制器模型从 `textures.all` 一张占位图
    #   改成了 `cube_bottom_top`（顶/底 = 新画的 `_top`，侧面仍是那张占位）⇒ 判据改成
    #   "**每一处贴图都是本模组 block/ 下控制器自己的图、而且文件在盘上**"：
    #   强度不变（照样不许借原版/别人的图），以后素材线再加面也不用改这道门。
    _texs = mbm.get(u"textures", {}) if isinstance(mbm, dict) else {}
    _bad = []
    for _k, _v in _texs.items():
        _parts = _v.split(u":", 1)[-1].split(u"/") if u":" in _v else _v.split(u"/")
        _p = os.path.join(ASSETS, u"textures", *(_parts[:-1]), _parts[-1] + u".png")
        if not _v.startswith(u"potato_s_t:block/diesel_generator_controller") or not os.path.exists(_p):
            _bad.append(_k)
    check(u"E3 方块模型每一处贴图都是控制器自己的图且在盘上（%s；不合规 %s）" % (_texs, _bad),
          bool(_texs) and not _bad)
    mim = jload(os.path.join(ASSETS, u"models", u"item", u"diesel_generator_controller.json"))
    check(u"E4 物品模型继承方块模型",
          isinstance(mim, dict) and mim.get(u"parent") == u"potato_s_t:block/diesel_generator_controller")
    pm = jload(os.path.join(ASSETS, u"models", u"block", u"diesel_generator_port.json"))
    check(u"E5 接线口贴图 = 接线块那张（玩家看不出被换过）",
          isinstance(pm, dict) and pm.get(u"textures", {}).get(u"all") == u"potato_s_t:block/wiring_block")
    pb = jload(os.path.join(ASSETS, u"blockstates", u"diesel_generator_port.json"))
    check(u"E6 接线口方块状态（无属性，单变体）",
          isinstance(pb, dict) and list(pb.get(u"variants", {}).keys()) == [u""])

    rc = jload(os.path.join(DATA, u"potato_s_t", u"recipe", u"diesel_generator_controller.json"))
    ok = isinstance(rc, dict) and rc.get(u"type") == u"minecraft:crafting_shaped" \
        and rc.get(u"pattern") == [u" P ", u"CBC", u" S "] \
        and rc.get(u"key", {}).get(u"P") == {u"item": u"potato_s_t:fluid_pipe"} \
        and rc.get(u"key", {}).get(u"C") == {u"tag": u"potato_s_t:copper_blocks"} \
        and rc.get(u"key", {}).get(u"B") == {u"item": u"minecraft:furnace"} \
        and rc.get(u"key", {}).get(u"S") == {u"item": u"potato_s_t:steel_plate"} \
        and rc.get(u"result") == {u"id": u"potato_s_t:diesel_generator_controller", u"count": 1}
    check(u"E7 控制器配方逐字照用户原话（空·流体管道·空 / 铜块·熔炉·铜块 / 空·钢板·空）", ok)
    tag = jload(os.path.join(DATA, u"potato_s_t", u"tags", u"item", u"copper_blocks.json"))
    want8 = [u"minecraft:%s" % s for s in
             (u"copper_block", u"exposed_copper", u"weathered_copper", u"oxidized_copper",
              u"waxed_copper_block", u"waxed_exposed_copper", u"waxed_weathered_copper",
              u"waxed_oxidized_copper")]
    check(u"E8 配方里的铜块收 8 种（用户原话：铜无论氧化/涂蜡程度都可以）",
          isinstance(tag, dict) and sorted(tag.get(u"values", [])) == sorted(want8))
    pk = jload(os.path.join(DATA, u"minecraft", u"tags", u"block", u"mineable", u"pickaxe.json"))
    check(u"E9 两个新方块都在 pickaxe 标签里（§4.25：漏了挖下去什么都不掉）",
          isinstance(pk, dict) and u"potato_s_t:diesel_generator_controller" in pk.get(u"values", [])
          and u"potato_s_t:diesel_generator_port" in pk.get(u"values", []))
    st = jload(os.path.join(DATA, u"minecraft", u"tags", u"block", u"needs_stone_tool.json"))
    check(u"E10 两个新方块都在 needs_stone_tool 里（木镐不够）",
          isinstance(st, dict) and u"potato_s_t:diesel_generator_controller" in st.get(u"values", [])
          and u"potato_s_t:diesel_generator_port" in st.get(u"values", []))

    print(u"\n  --- 四语言 ---")
    LANG = os.path.join(ASSETS, u"lang")
    tables = {}
    for loc in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        p = os.path.join(LANG, loc + u".json")
        raw = open(p, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            check(u"E11 %s 无 BOM" % loc, False)
        text = raw.decode(u"utf-8")
        check(u"E11 %s 纯净 LF / 无 BOM" % loc, u"\r" not in text and raw[:3] != b"\xef\xbb\xbf")
        tables[loc] = json.loads(text)
    check(u"E12 四份都是 482 键（本轮 +12：11 个机键 + 接线口那个）",
          all(len(tables[l]) == 482 for l in tables))
    base = set(tables[u"zh_cn"].keys())
    check(u"E13 四份键集合完全相同",
          all(set(tables[l].keys()) == base for l in tables))
    new_keys = [u"block.potato_s_t.diesel_generator_controller",
                u"tooltip.potato_s_t.diesel_generator_controller",
                u"gui.potato_s_t.diesel_generator.status.running",
                u"gui.potato_s_t.diesel_generator.status.disabled",
                u"gui.potato_s_t.diesel_generator.status.empty",
                u"gui.potato_s_t.diesel_generator.status.output_full",
                u"gui.potato_s_t.diesel_generator.status.no_structure",
                u"gui.potato_s_t.diesel_generator.invalid",
                u"gui.potato_s_t.diesel_generator.pour.empty",
                u"gui.potato_s_t.diesel_generator.pour.rejected",
                u"gui.potato_s_t.diesel_generator.pour.full",
                # ⚠ 第 12 个键是 `_zf123_langaudit.py` 抓出来的（接线口没有语言键）⇒
                #    照盘上先例（alloy_smelter_port / _part 都有 block.* 键）补上。
                #    它排在最后，所以下面 E15 按下标取的 [7]/[9] 不受影响。
                u"block.potato_s_t.diesel_generator_port"]
    miss = [k for k in new_keys if k not in base]
    check(u"E14 十二个新键四份都在%s" % (u"" if not miss else u"（缺 %s）" % miss), not miss)
    sigs = set()
    for loc in tables:
        sigs.add(tuple(tables[loc][k].count(u"%s") for k in new_keys))
    check(u"E15 十二个新键的占位符签名四份一致（invalid 8 个 %s）",
          len(sigs) == 1 and list(sigs)[0][7] == 8 and list(sigs)[0][9] == 1)
    # 界面里那盏灯的键前缀与语言键必须对得上
    scr = read(os.path.join(JAVA, u"client", u"DieselGeneratorScreen.java"))
    pref = re.search(r"STATUS_KEY_PREFIX = \"([^\"]+)\"", scr)
    if check(u"E16 界面里的状态灯前缀能取到", pref is not None):
        pref = pref.group(1)
        want_sfx = [u"running", u"disabled", u"empty", u"output_full", u"no_structure"]
        miss = [s for s in want_sfx if pref + s not in base]
        check(u"E17 灯会用到的五个后缀键都在（%s）" % pref, not miss)

    print(u"\n  --- 语言文件：改前件 + 本轮那 12 个键（键序不许乱、老值一个都不许动）---")
    for loc in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        relp = u"src/main/resources/assets/potato_s_t/lang/%s.json" % loc
        bak = os.path.join(BK, *relp.split(u"/"))
        cur = read(rel(*relp.split(u"/")))
        if not os.path.exists(bak):
            check(u"E18 %s：改前件在 zf125_pre" % loc, False)
            continue
        b, c = json.loads(read(bak)), json.loads(cur)
        added = set(c) - set(b)
        removed = set(b) - set(c)
        changed = [k for k in b if k in c and c[k] != b[k]]
        order_ok = [k for k in c if k in b] == list(b)
        # ⚠ ZF127 retarget：语言键是**每轮都在涨**的活体数字 —— 本轮（ZF127 银线/银线轴）
        #   又加了两个 ⇒ 期望是"ZF125 那 12 个 + 后续轮次加的"，判据强度不变。
        later = {u"item.potato_s_t.silver_wire", u"item.potato_s_t.silver_wire_spool"}
        check(u"E18 %s：新增 %d 键（ZF125 的 12 + ZF127 的 2）/ 删 0 / 老值改 0 / 键序没乱（共 %d 键）"
              % (loc, len(added), len(c)),
              added == set(new_keys) | later and not removed and not changed and order_ok)


# ==================================================================
# F 往轮判据的活体数字
# ==================================================================

def part_f():
    print(u"\n===== F 往轮判据 retarget =====")
    for n, what in ((u"_zf100_verify.py", u"EXPECT_KEYS = 482"),
                    (u"_zf101_verify.py", u"EXPECT_KEYS = 482"),
                    (u"_zf102_verify.py", u"EXPECT_KEYS = 482")):
        p = os.path.join(TOOLS, n)
        check(u"F1 %s 的键数跟到 482" % n, os.path.exists(p) and what in read(p))
    p = os.path.join(TOOLS, u"_zf103_verify.py")
    check(u"F2 _zf103_verify.py 的键数与文案都跟到 482",
          os.path.exists(p) and u"len(table) == 482" in read(p) and u"总键数 482" in read(p))
    left = []
    for n in (u"_zf100_verify.py", u"_zf101_verify.py", u"_zf102_verify.py", u"_zf103_verify.py"):
        if u"464" in read(os.path.join(TOOLS, n)):
            left.append(n)
    check(u"F3 四份里再无裸的 464%s" % (u"" if not left else u"（残留 %s）" % left), not left)
    check(u"F4 改前件在（_sha1.txt + _zf125_newfiles.txt）",
          os.path.exists(os.path.join(BK, u"_sha1.txt"))
          and os.path.exists(os.path.join(BK, u"_zf125_newfiles.txt")))
    check(u"F5 本轮**没有**动别的机器的结构常量（合金炉 58 / 高炉 / 分馏塔）",
          u"REQUIRED_CELLS = 58;" in read(os.path.join(JAVA, u"AlloySmelterStructure.java"))
          and u"SIZE = 4;" in read(os.path.join(JAVA, u"DistillationTowerStructure.java")))


def main():
    print(u"ZF125 大型柴油发电机：常驻校验（静态）")
    part_a()
    part_b()
    part_c()
    part_d()
    part_e()
    part_f()
    print(u"\n==================== 汇总 ====================")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! %s" % f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
