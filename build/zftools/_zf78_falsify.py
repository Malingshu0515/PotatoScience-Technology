# -*- coding: utf-8 -*-
u"""_zf78_falsify.py —— 反证：故意把 5 处改坏，`_zf78_verify.py` 必须当场挂；逐刀还原再复跑

判据（往轮口径）：
  · 每一刀挂掉的条数必须 **≥1**（0 就是"断言没落在代码上"）；
  · 还原后必须回到 **失败 = 0**（防止"改坏一次就再也回不去"）；
  · 每刀都断言"反向锚点正好命中 1 次"，并且**逐字节还原**（保存原内容再写回）。
"""
import hashlib
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
# ⚠ ZF100 加这一行时忘了定义它 ⇒ 整段 falsify 当场 NameError 崩掉，
#   而**门当时没报**（`_zf100_gatecount.py` 只核"段在不在"，不核"段跑没跑通"）
#   ⇒ 已给 gatecount 补上"日志里不许出现 Traceback"这一条（§4.53 的兄弟）。
RECIPE = os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "recipe")
VERIFIER = os.path.join(TOOLS, "_zf78_verify.py")

KNIVES = [
    (u"K1 每 tick 耗电 8096 → 8000",
     os.path.join(SRC, "DistillationOperatorBlockEntity.java"),
     u"public static final int FE_PER_TICK = 8096;",
     u"public static final int FE_PER_TICK = 8000;"),
    (u"K2 检测窗口下沿 -3 → -4（Y_MAX 跟着变成 +5）",
     os.path.join(SRC, "DistillationTowerStructure.java"),
     u"public static final int Y_MIN = -3;",
     u"public static final int Y_MIN = -4;"),
    (u"K3 ScaledTank 的容量不再乘塔数",
     os.path.join(SRC, "DistillationOperatorBlockEntity.java"),
     u"return Math.max(0, this.perTower * this.towers.getAsInt());",
     u"return this.perTower;"),
    (u"K4 界面把柴油与石脑油的罐对调",
     os.path.join(SRC, "client", "DistillationOperatorScreen.java"),
     u"""        addTank(DistillationOperatorBlockEntity.TANK_DIESEL, ModFluids.DIESEL.get());
        addTank(DistillationOperatorBlockEntity.TANK_NAPHTHA, ModFluids.NAPHTHA.get());""",
     u"""        addTank(DistillationOperatorBlockEntity.TANK_NAPHTHA, ModFluids.NAPHTHA.get());
        addTank(DistillationOperatorBlockEntity.TANK_DIESEL, ModFluids.DIESEL.get());"""),
    (u"K5 c:lpg 标签漏掉 flowing 那一半",
     os.path.join(ROOT, "src", "main", "resources", "data", "c", "tags", "fluid", "lpg.json"),
     u'    "potato_s_t:lpg",\n    "potato_s_t:flowing_lpg"',
     u'    "potato_s_t:lpg"'),
    # ---- 2026-09-24 两件新功能各来一刀 ----
    (u"K6 右键倒流体一次的量 1000 → 500",
     os.path.join(SRC, "DistillationOperatorBlock.java"),
     u"public static final int POUR_PER_CLICK = 1000;",
     u"public static final int POUR_PER_CLICK = 500;"),
    (u"K7 诊断不再跳过「装着控制器自己」的退化锚点",
     os.path.join(SRC, "DistillationTowerStructure.java"),
     u"""                    if (contains(base, controller)) {
                        continue;
                    }
""",
     u""),
    # ---- ZF79 两刀：一个压柏油块要几个、一处"数量不够"的关卡 ----
    (u"K8 压一个柏油块要的沥青 12 → 13",
     os.path.join(SRC, "PressRecipes.java"),
     u"public static final int BITUMEN_PER_BLOCK = 12;",
     u"public static final int BITUMEN_PER_BLOCK = 13;"),
    (u"K10 灌装机手放门禁改回写死高压气罐",
     os.path.join(SRC, "FillingMachineMenu.java"),
     u"                    return stack.getItem() instanceof FluidContainerItem;",
     u"                    return stack.getItem() instanceof HighPressureTankItem;"),
    (u"K11 JEI 箭头的左边界改回写死 4 列",
     os.path.join(SRC, "client", "jei", "MachineRecipeCategory.java"),
     u"        int usedCols = Math.max(1, Math.min(recipe.itemIn().size(), IN_COLS));",
     u"        int usedCols = IN_COLS;"),
    (u"K9 液压机不再检查「数量够不够」",
     os.path.join(SRC, "HydraulicPressBlockEntity.java"),
     u"""        if (!recipe.hasEnough(input)) {
            this.status = STATUS_MATERIAL;
            return;
        }
""",
     u""),
    # ---- ZF80 五刀：手倒的量、手倒的选罐规则、诊断与灌装判据对齐、Shift 诊断、语言新键 ----
    (u"K12 手倒一次的量 1000 → 500",
     os.path.join(SRC, "FillingMachineBlockEntity.java"),
     u"public static final int POUR_PER_CLICK = 1000;",
     u"public static final int POUR_PER_CLICK = 500;"),
    (u"K13 手倒不再优先找「装着同种流体」的罐",
     os.path.join(SRC, "FillingMachineBlockEntity.java"),
     u"                    && this.tanks[i].getFluid().getFluid() == held.getFluid()",
     u"                    && false"),
    (u"K14 诊断的缺电判据与灌装逻辑错开（60 → 120）",
     os.path.join(SRC, "FillingMachineBlockEntity.java"),
     u"""        if (this.energy < ENERGY_PER_TANK) {
            return SlotState.NO_POWER;
        }""",
     u"""        if (this.energy < ENERGY_PER_TANK * 2) {
            return SlotState.NO_POWER;
        }"""),
    (u"K15 Shift 右键不再诊断（直接开界面）",
     os.path.join(SRC, "FillingMachineBlock.java"),
     u"            if (serverPlayer.isShiftKeyDown()) {",
     u"            if (false) {"),
    (u"K16 手倒对非容器也不再放行（会挡掉开界面那条路）",
     os.path.join(SRC, "FillingMachineBlock.java"),
     u"""        if (!(stack.getItem() instanceof FluidContainerItem)) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }""",
     u"""        if (!(stack.getItem() instanceof FluidContainerItem)) {
            return ItemInteractionResult.SUCCESS;
        }"""),
    (u"K17 中文 lang 少一条诊断文案",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang", "zh_cn.json"),
     u"    \"gui.potato_s_t.filling.diag.no_power\":  \"[灌装机] %s 号槽：缺电 —— 机器里只有 %s FE，每个槽每 tick 要 %s FE\",\n",
     u""),
    # ---- ZF81 两刀：电解器能耗常量、tooltip 字面量（都是"活体数字"，改回去必须当场挂）----
    # 自查过 §4.30 那条：坏串 `= 100;` **不是**好串 `= 1000;` 的子串，断言也是逐字比对，不会互相包含
    (u"K18 电解器制氧能耗 1000 → 100",
     os.path.join(SRC, "ElectrolyzerBlockEntity.java"),
     u"public static final int ENERGY_PER_TICK_OXYGEN = 1000;",
     u"public static final int ENERGY_PER_TICK_OXYGEN = 100;"),
    (u"K19 中文 tooltip 退回 100 FE",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang", "zh_cn.json"),
     u"每 tick 消耗 1000 FE 与 10 mB 水",
     u"每 tick 消耗 100 FE 与 10 mB 水"),
    # ---- ZF82 三刀：桶的官方映射、换流器一次取多少、泵接口是不是抽左槽那件容器 ----
    (u"K20 柴油的官方桶指向错误（.bucket 换成汽油桶）",
     os.path.join(SRC, "ModFluids.java"),
     u".bucket(ModItems.DIESEL_BUCKET);",
     u".bucket(ModItems.GASOLINE_BUCKET);"),
    (u"K21 换流器一次取 1000 → 500",
     os.path.join(SRC, "FluidExchangerBlockEntity.java"),
     u"public static final int AMOUNT_PER_OPERATION = 1000;",
     u"public static final int AMOUNT_PER_OPERATION = 500;"),
    (u"K22 泵接口不再抽左槽容器（改成恒空）",
     os.path.join(SRC, "FluidExchangerBlockEntity.java"),
     u"            public FluidStack getFluidInTank(int tank) {\n                return leftContents();\n            }",
     u"            public FluidStack getFluidInTank(int tank) {\n                return FluidStack.EMPTY;\n            }"),
    # ---- ZF83 一刀：铁板模型指回通用贴图（等于"换了但没接线"）----
    (u"K23 铁板模型又指回通用 plate（等于没换）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "item",
                  "iron_plate.json"),
     u'"layer0": "potato_s_t:item/iron_plate"',
     u'"layer0": "potato_s_t:item/plate"'),
    # ---- ZF85 两刀：搬走的贴图注册少一种、路径拼错（都是"搬家搬丢/搬错"的典型）----
    (u"K24 搬注册时漏掉汽油（少一行 registerFluidType）",
     os.path.join(SRC, "PotatoSTClient.java"),
     u'        event.registerFluidType(textures("gasoline"), ModFluids.GASOLINE_TYPE.get());\n',
     u""),
    (u"K25 贴图路径拼错（_still 写成 _stil）",
     os.path.join(SRC, "PotatoSTClient.java"),
     u'"block/" + name + "_still"',
     u'"block/" + name + "_stil"'),
    # ---- ZF89 三刀：留档凭据的哈希、档案里的 ZF89 行、电力高炉 OBJ 的 UV 集合。
    #      （贴图本身是二进制，锚不了文本 ⇒ 改砍"记录了它的那些可核对处"与"模型的 UV"）
    (u"K26 来源凭据里石脑油的 sha1 改一位（留档与凭据对不上）",
     os.path.join(ROOT, "build", u"用户素材", u"_来源凭据.json"),
     u'"sha1": "f2885b6208dfb09c51df12172f4f6264031e0237"',
     u'"sha1": "f2885b6208dfb09c51df12172f4f6264031e0238"'),
    (u"K27 档案 §5 表里的 ZF89 那一行被抹掉",
     os.path.join(ROOT, "docs", u"开发档案.md"),
     u"| ZF89 | **新建 `zf89_pre`**",
     u"| ZF8X | **新建 `zf89_pre`**"),
    # ⚠ K28 原来砍的是"高炉 OBJ 只有 4 个 UV 点"那条断言 —— 0.11 ZF91 换成带真 UV 的模型之后，
    #   那个锚点（`v 2.000000 0.000000 3.000000\nvt 1 1`）已经不存在了，反证脚本自己报了
    #   「锚点命中 0 次」（**这正是反证该有的行为：锚点没了就喊，不静默跳过**）。
    #   这里按新真相改成"砍掉一条面"：`_zf89_verify.py` C 段那条「已换成真 UV（114 个面）」与
    #   `_zf91_verify.py` A 段的「面数 = 114」都必须当场挂。
    (u"K28 高炉北向 OBJ 的第一条面被删掉（面数变 113）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "block",
                  "electric_blast_furnace_north.obj"),
     u"usemtl electric_blast_furnace\nf 2/1/1 1/2/1 3/3/1 4/4/1\n",
     u"usemtl electric_blast_furnace\n"),
    # ---- ZF90 三刀：本轮的正题（板子改指向）、中途收的柴油桶、以及那句活体数字 ----
    (u"K29 银板模型又指回通用 plate（= 本轮的正题被改回去）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "item",
                  "silver_plate.json"),
     u'"layer0": "potato_s_t:item/iron_plate"',
     u'"layer0": "potato_s_t:item/plate"'),
    (u"K30 柴油桶模型改回借原版水桶贴图",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "item",
                  "diesel_bucket.json"),
     u'"layer0": "potato_s_t:item/diesel_bucket"',
     u'"layer0": "minecraft:item/water_bucket"'),
    (u"K31 英文公告那句活体数字 5 → 6（与 TextureCheck 打架）",
     os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md"),
     u"(5 models still do this)",
     u"(6 models still do this)"),
    (u"K32 汽油桶模型改回借原版水桶贴图（本轮最后收的那张）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "item",
                  "gasoline_bucket.json"),
     u'"layer0": "potato_s_t:item/gasoline_bucket"',
     u'"layer0": "minecraft:item/water_bucket"'),
    # ---- ZF91 三刀：真 UV 被改坏、档案那一行被抹、v 方向被翻 ----
    (u"K33 高炉北向 OBJ 的一个 UV 值被挪走（那一面就压到空白处了）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "block",
                  "electric_blast_furnace_north.obj"),
     u"vt 0.378906 0.000000",
     u"vt 0.378906 0.500000"),
    (u"K34 档案 §5 表里的 ZF91 那一行被抹掉",
     os.path.join(ROOT, "docs", u"开发档案.md"),
     u"| ZF91 | **新建 `zf91_pre`**",
     u"| ZF9X | **新建 `zf91_pre`**"),
    (u"K35 model JSON 的 flip_v 被翻成 true（贴图会上下颠倒）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "block",
                  "electric_blast_furnace_north.json"),
     u'"flip_v": false',
     u'"flip_v": true'),
    # ---- ZF92 三刀：本轮的正题（两根接线柱的 UV 归属）+ 档案那一行。
    #      锚点都是"某一面某个角的 vt"，改完那一面的 UV 矩形就不等于那个 16×16 瓦片了：
    #      `_zf92_verify.py` A 段（三面归属 / 16×16）与 `_zf91_verify.py` A 段（矩形尺寸 = 面尺寸×16）都该挂。
    (u"K36 第一根柱子的顶面 UV 挪回「金框」那块（顶面又变成金框）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "block",
                  "electric_blast_furnace_north.obj"),
     u"vt 0.574219 0.453125",
     u"vt 0.574219 0.324219"),
    (u"K37 第二根柱子的顶面 UV 也挪回「金框」那块",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "block",
                  "electric_blast_furnace_north.obj"),
     u"vt 0.601562 0.652344",
     u"vt 0.601562 0.519531"),
    (u"K38 档案 §5 表里的 ZF92 那一行被抹掉",
     os.path.join(ROOT, "docs", u"开发档案.md"),
     u"| ZF92 | **新建 `zf92_pre`**",
     u"| ZF9Y | **新建 `zf92_pre`**"),
    # ---- ZF93 四刀：本轮的正题是"第二张唱片的时长/流式/键/文档"。
    #      时长那一刀特意只差 0.1 s —— 断言必须抓得住"看着对、其实错"的数。
    (u"K39 曲目数据的 length_in_seconds 差 0.1 s（147.1 → 147.0）",
     os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "jukebox_song",
                  "jasmine_flower.json"),
     u'"length_in_seconds": 147.1,',
     u'"length_in_seconds": 147.0,'),
    (u"K40 长音频的 stream 被关掉（stream: true → false）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "sounds.json"),
     u'"sounds": [ { "name": "potato_s_t:music_disc_jasmine_flower", "stream": true } ]',
     u'"sounds": [ { "name": "potato_s_t:music_disc_jasmine_flower", "stream": false } ]'),
    (u"K41 中文 lang 里的物品键拼错最后一个字母（flower → flowr）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang", "zh_cn.json"),
     u'"item.potato_s_t.music_disc_jasmine_flower"',
     u'"item.potato_s_t.music_disc_jasmine_flowr"'),
    (u"K42 档案 §5 表里的 ZF93 那一行被抹掉",
     os.path.join(ROOT, "docs", u"开发档案.md"),
     u"| ZF93 | **新建 `zf93_pre`**",
     u"| ZF9Z | **新建 `zf93_pre`**"),
    # ---- ZF94 三刀：本轮把两根柱子的东/西统一了 ⇒ 那两面的 `vt` 行**现在是重复文本**，
    #      锚点只能用 `f` 行（每条面行都唯一）。改一个顶点的 vt 下标，那一面的 UV 矩形就坏了。
    (u"K43 北向 OBJ 里第二根柱子那个格栅面有个顶点指向了别的 vt（UV 矩形坏掉）",
     os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "models", "block",
                  "electric_blast_furnace_north.obj"),
     u"f 18/49/13 17/50/13 19/51/13 20/52/13",
     u"f 18/1/13 17/50/13 19/51/13 20/52/13"),
    (u"K44 档案 §5 表里的 ZF94 那一行被抹掉",
     os.path.join(ROOT, "docs", u"开发档案.md"),
     u"| ZF94 | **新建 `zf94_pre`**",
     u"| ZF9W | **新建 `zf94_pre`**"),
    (u"K45 贴图清单里的 ZF94 一节被抹掉",
     os.path.join(ROOT, "docs", u"贴图清单.md"),
     u"## ZF94（0.11）：电力高炉两根接线柱的东/西统一",
     u"## ZF9W：电力高炉两根接线柱的东/西统一"),
    # ---- ZF95 四刀：用户口述的 5 条配方，"逐格与规格比"必须抓得住一格之差 ----
    (u"K46 茉莉花唱片的正中那格从火把花变成粗金块（GTG → GGG）",
     os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "recipe",
                  "music_disc_jasmine_flower.json"),
     u'"GTG"',
     u'"GGG"'),
    (u"K47 分馏塔操作器最下面一行从「油罐/控制器/油罐」变成三个油罐（TRT → TTT）",
     os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "recipe",
                  "distillation_operator.json"),
     u'"TRT"',
     u'"TTT"'),
    (u"K48 档案 §5 表里的 ZF95 那一行被抹掉",
     os.path.join(ROOT, "docs", u"开发档案.md"),
     u"| ZF95 | **新建 `zf95_pre`**",
     u"| ZF9V | **新建 `zf95_pre`**"),
    (u"K49 英文公告里「这三件已经有配方了」那句被改回去",
     os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md"),
     u"got their recipes in",
     u"still have no recipe in"),
    # ---- ZF96 五刀：新机器的"三个数 + 一格配方 + 状态灯颜色 + 能力登记" ----
    (u"K50 每批要的沥青 16 → 15",
     os.path.join(SRC, "HydrodesulfurizationChamberBlockEntity.java"),
     u"public static final int BITUMEN_PER_OPERATION = 16;",
     u"public static final int BITUMEN_PER_OPERATION = 15;"),
    (u"K51 每批耗时 200 tick → 100 tick（10 秒 → 5 秒）",
     os.path.join(SRC, "HydrodesulfurizationChamberBlockEntity.java"),
     u"public static final int DURATION_TICKS = 200;",
     u"public static final int DURATION_TICKS = 100;"),
    (u"K52 合成配方第二行从「铁块/气罐/铁块」改回「铁锭/气罐/铁锭」（= 我本轮犯过的那个错）",
     os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "recipe",
                  "hydrodesulfurization_chamber.json"),
     u'"BTB"',
     u'"ITI"'),
    (u"K53 状态码 9 从黄灯改成红灯",
     os.path.join(SRC, "client", "gui", "parts", "StatusLampPart.java"),
     u"case HydrodesulfurizationChamberBlockEntity.STATUS_NO_HYDROGEN -> YELLOW;",
     u"case HydrodesulfurizationChamberBlockEntity.STATUS_NO_HYDROGEN -> RED;"),
    (u"K54 机器不再登记流体能力（管道/泵灌不进氢气）",
     os.path.join(SRC, "PotatoST.java"),
     u"""        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.HYDRODESULFURIZATION_CHAMBER_BE.get(),
                (chamber, side) -> chamber.getFluidHandler());
""",
     u""),
    # ---- ZF97 六刀：两台新机器 + 两种新气体的关键规格 ----
    (u"K55 空气分离器一批的氮气 8 → 7",
     os.path.join(SRC, "AirSeparatorBlockEntity.java"),
     u"public static final int NITROGEN_PER_BATCH = 8;",
     u"public static final int NITROGEN_PER_BATCH = 7;"),
    (u"K56 空气分离器的罐改成「能被灌入」（fill 不再恒 0）",
     os.path.join(SRC, "AirSeparatorBlockEntity.java"),
     u"            return 0;                         // 用户原话「不接受被灌入」",
     u"            return AirSeparatorBlockEntity.this.tanks[TANK_NITROGEN].fill(resource, action);"),
    (u"K57 氨气组成室不再检查催化剂槽",
     os.path.join(SRC, "AmmoniaSynthesisChamberBlockEntity.java"),
     u"        if (!hasCatalyst()) {",
     u"        if (false) {"),
    (u"K58 氨气输出罐下方那个槽的方向反过来（反向改成正向）",
     os.path.join(SRC, "AmmoniaSynthesisChamberBlockEntity.java"),
     u"        moved |= transferToContainer(AMMONIA_TANK_SLOT, TANK_AMMONIA);",
     u"        moved |= transferFromContainer(AMMONIA_TANK_SLOT, TANK_AMMONIA);"),
    (u"K59 c:gaseous 标签里把氨气那两行删掉",
     os.path.join(ROOT, "src", "main", "resources", "data", "c", "tags", "fluid", "gaseous.json"),
     # ⚠ ZF100 在氨气后面又加了两行二氧化碳 ⇒ 老锚点（氨气行 + 换行）不再存在。
     #   改成"氨气那两行 + 行尾逗号"—— 删掉它们的效果与老刀完全一样（标签里没有氨气了）。
     u'    "potato_s_t:ammonia",\n    "potato_s_t:flowing_ammonia",\n',
     u''),
    (u"K60 空气分离器配方第一行第三格从电容改成加热装置（= 我本轮犯过的那个错）",
     os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "recipe",
                  "air_separator.json"),
     u'" KC"',
     u'" KH"'),
    # ---- ZF98 五刀：流体泵"不存流体 / 先问收方 / 旧存档接住" ----
    (u"K61 先抽源再问目标（把 fill-SIMULATE 那一步去掉 = 抽了再说）",
     os.path.join(SRC, "FluidPumpBlockEntity.java"),
     u"                int accepted = output.handler().fill(offer, IFluidHandler.FluidAction.SIMULATE);",
     u"                int accepted = offer.getAmount();"),
    (u"K62 目标不收也照样抽（把「收 0 就放弃」改成「硬塞给它」）",
     os.path.join(SRC, "FluidPumpBlockEntity.java"),
     u"""                if (accepted <= 0) {
                    return moved;                   // 目标不要这种流体 ⇒ 别再抽了
                }""",
     u"""                if (accepted <= 0) {
                    accepted = offer.getAmount();
                }"""),
    (u"K63 把内部罐加回来（泵又开始存流体）",
     os.path.join(SRC, "FluidPumpBlockEntity.java"),
     u"    private FluidStack legacy = FluidStack.EMPTY;",
     u"    private final FluidTank tank = new FluidTank(8000);\n"
     u"    private FluidStack legacy = FluidStack.EMPTY;"),
    (u"K64 重新给泵登记流体能力",
     os.path.join(SRC, "PotatoST.java"),
     u"""        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.FLUID_PUMP_BE.get(),
                (pump, side) -> pump.getEnergyStorage());""",
     u"""        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                ModBlocks.FLUID_PUMP_BE.get(),
                (pump, side) -> pump.getEnergyStorage());
        event.registerBlockEntity(
                Capabilities.FluidHandler.BLOCK,
                ModBlocks.FLUID_PUMP_BE.get(),
                (pump, side) -> null);"""),
    (u"K65 读档不再接住旧存档里的流体（拆罐前存的那些会被丢掉）",
     os.path.join(SRC, "FluidPumpBlockEntity.java"),
     u"                this.legacy = probe.getFluid().copy();",
     u"                this.legacy = FluidStack.EMPTY;"),
    # ---- ZF99 三刀：粒子要在服务端发、只在工作时发、量是常量 ----
    (u"K66 粒子改在服务端用 Level#addParticle 发（= 空操作，一缕烟都看不到）",
     os.path.join(SRC, "AirSeparatorBlockEntity.java"),
     u"""        server.sendParticles(ParticleTypes.CLOUD, x, y, z, PARTICLES_PER_EMIT,
                PARTICLE_SPREAD, 0.02, PARTICLE_SPREAD, PARTICLE_SPEED);""",
     u"""        this.level.addParticle(ParticleTypes.CLOUD, x, y, z, 0.0, 0.0, 0.0);"""),
    (u"K67 粒子挪到红石检查之前（停机时也会冒烟）",
     os.path.join(SRC, "AirSeparatorBlockEntity.java"),
     u"        // ① 红石信号 = 关机（进度保留）",
     u"        spawnWorkParticles();\n        // ① 红石信号 = 关机（进度保留）"),
    (u"K68 冒烟间隔 5 tick → 50 tick（一秒才一次）",
     os.path.join(SRC, "AirSeparatorBlockEntity.java"),
     u"public static final int PARTICLE_INTERVAL = 5;",
     u"public static final int PARTICLE_INTERVAL = 50;"),
    # ---- ZF100 五刀：新配方 + 电力高炉新锚点 + 燃烧反应室的关键数 ----
    (u"K69 电力高炉锚点改回只认原版高炉（自己造的主控又变成摆下去没用的方块）",
     os.path.join(SRC, "ElectricBlastFurnaceStructure.java"),
     u"""case CONTROLLER -> state.is(Blocks.BLAST_FURNACE)
                    || state.is(ModBlocks.ELECTRIC_BLAST_FURNACE.get());""",
     u"""case CONTROLLER -> state.is(Blocks.BLAST_FURNACE);"""),
    (u"K70 锂电池九宫格把中间那行换掉（PLP → LPP，材料一样但摆法变了）",
     os.path.join(RECIPE, "lithium_battery.json"),
     u'"ACA",\n    "PLP",\n    "AMA"',
     u'"ACA",\n    "LPP",\n    "AMA"'),
    (u"K71 燃烧反应室的二氧化碳产物 200 → 20（柴油那一档）",
     os.path.join(SRC, "CombustionChamberBlockEntity.java"),
     u"public static final int CO2_PER_LIQUID_FUEL = 200;",
     u"public static final int CO2_PER_LIQUID_FUEL = 20;"),
    (u"K72 燃烧反应室的氧气罐改成「能被抽走」（必须输入端那条被破坏）",
     os.path.join(SRC, "CombustionChamberBlockEntity.java"),
     u"""            if (isCarbonDioxide(resource)) {
                return CombustionChamberBlockEntity.this.tanks[TANK_CO2].drain(resource, action);
            }""",
     u"""            if (isOxygen(resource)) {
                return CombustionChamberBlockEntity.this.tanks[TANK_OXYGEN].drain(resource, action);
            }
            if (isCarbonDioxide(resource)) {
                return CombustionChamberBlockEntity.this.tanks[TANK_CO2].drain(resource, action);
            }"""),
    # ---- ZF101 四刀：酸性反应室的关键数 ----
    (u"K74 酸性反应室耗能 500 → 400 FE/t",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"public static final int ENERGY_PER_TICK = 500;",
     u"public static final int ENERGY_PER_TICK = 400;"),
    (u"K75 一批硫酸要的硫 10 → 5",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"public static final int SULFUR_PER_BATCH = 10;",
     u"public static final int SULFUR_PER_BATCH = 5;"),
    (u"K76 四个产物罐也变成「能灌入」（只出不进那条被破坏）",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     # ⚠ ZF102 把那句判定从"写死 tank <= TANK_WATER"改成了 isInputTank(tank) ⇒ 锚点跟着换
     u"""            return isInputTank(tank)
                    && AcidicReactionChamberBlockEntity.this.tanks[tank].isFluidValid(stack);""",
     u"""            return AcidicReactionChamberBlockEntity.this.tanks[tank].isFluidValid(stack);"""),
    (u"K77 菜单不再校验配方号（客户端说什么就是什么）",
     os.path.join(SRC, "AcidicReactionChamberMenu.java"),
     u"        if (this.machine == null || !AcidicReactionChamberBlockEntity.isValidRecipe(id)) {",
     u"        if (this.machine == null) {"),
    # ---- ZF102 两刀：第 4 个配方（盐酸）的数 ----
    (u"K78 盐酸配方要的氢气 10 → 5（配比被改）",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"public static final int HYDROCHLORIC_HYDROGEN_PER_TICK = 10;",
     u"public static final int HYDROCHLORIC_HYDROGEN_PER_TICK = 5;"),
    (u"K79 盐酸罐被当成原料罐（只出不进那条被破坏）",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"            TANK_CO2, TANK_OXYGEN, TANK_AMMONIA, TANK_WATER, TANK_HYDROGEN, TANK_CHLORINE,",
     u"            TANK_CO2, TANK_OXYGEN, TANK_AMMONIA, TANK_WATER, TANK_HYDROGEN, TANK_CHLORINE,\n"
     u"            TANK_HYDROCHLORIC,"),
    (u"K73 捕获器不再认燃烧反应室（动力源被摘掉）",
     os.path.join(SRC, "PowerCapturerBlockEntity.java"),
     u"""            if (level.getBlockEntity(neighbor) instanceof CombustionChamberBlockEntity chamber) {
                total += chamber.powerPerTick();
                continue;
            }""",
     u""),
]


# ⚠ ZF84/ZF86 两轮我都漏了把新校验脚本挂进来（只加刀不加校验）—— ZF87 一并补齐。
# ⚠ ZF88/ZF89 两轮又漏了同一个动作 ⇒ ZF89 这次补上：**每写一个常驻校验就必须挂进这份名单**。
#   （ZF87 没有自己的校验脚本：油桶那几条并进了 `_zf86_verify.py`。）
VERIFIERS = [os.path.join(TOOLS, "_zf78_verify.py"), os.path.join(TOOLS, "_zf79_verify.py"),
             os.path.join(TOOLS, "_zf80_verify.py"), os.path.join(TOOLS, "_zf81_verify.py"),
             os.path.join(TOOLS, "_zf82_verify.py"), os.path.join(TOOLS, "_zf83_verify.py"),
             os.path.join(TOOLS, "_zf84_verify.py"), os.path.join(TOOLS, "_zf85_verify.py"),
             os.path.join(TOOLS, "_zf86_verify.py"), os.path.join(TOOLS, "_zf88_verify.py"),
             os.path.join(TOOLS, "_zf89_verify.py"), os.path.join(TOOLS, "_zf90_verify.py"),
             os.path.join(TOOLS, "_zf91_verify.py"), os.path.join(TOOLS, "_zf92_verify.py"),
             os.path.join(TOOLS, "_zf93_verify.py"), os.path.join(TOOLS, "_zf94_verify.py"),
             os.path.join(TOOLS, "_zf95_verify.py"), os.path.join(TOOLS, "_zf96_verify.py"),
             os.path.join(TOOLS, "_zf97_verify.py"), os.path.join(TOOLS, "_zf98_verify.py"),
             os.path.join(TOOLS, "_zf99_verify.py"),
             os.path.join(TOOLS, "_zf100_verify.py"),
             os.path.join(TOOLS, "_zf101_verify.py"),
             os.path.join(TOOLS, "_zf102_verify.py")]


def run_verifier():
    u"""两条常驻校验**一起跑**、把失败数相加。

    ⚠ 第一版只跑 `_zf78_verify.py` ⇒ ZF79 那两把刀（沥青要几个、数量关卡）
    "改坏了却仍然 0 失败" —— 不是断言没落上，是**刀砍在了另一条校验管的地盘上**。
    """
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    passed = 0
    failed = 0
    out_all = []
    for path in VERIFIERS:
        p = subprocess.run([sys.executable, path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, cwd=ROOT)
        out = (p.stdout or "") + (p.stderr or "")
        out_all.append(out)
        m = re.search(r"通过 = (\d+)\s+失败 = (\d+)", out)
        if not m:
            return None, u"\n".join(out_all)
        passed += int(m.group(1))
        failed += int(m.group(2))
    return (passed, failed), u"\n".join(out_all)


def main():
    fails = []
    base, out = run_verifier()
    if base is None:
        print(u"  [FAIL] 基线跑不起来：\n%s" % out[-800:])
        return 1
    print(u"基线：通过 = %d 失败 = %d" % base)
    if base[1] != 0:
        print(u"  [FAIL] 基线就不是绿的，先修好再做反证")
        return 1

    for label, path, good, bad in KNIVES:
        original = io.open(path, encoding="utf-8").read()
        before = hashlib.sha1(original.encode("utf-8")).hexdigest()
        if original.count(good) != 1:
            fails.append(u"%s：锚点命中 %d 次" % (label, original.count(good)))
            continue
        try:
            io.open(path, "w", encoding="utf-8", newline=u"\n").write(
                original.replace(good, bad, 1))
            res, _ = run_verifier()
            if res is None:
                fails.append(u"%s：改坏后校验脚本没跑出汇总行" % label)
            elif res[1] < 1:
                fails.append(u"%s：改坏了却仍然 0 失败（断言没落在代码上）" % label)
            else:
                print(u"  [OK]   %s ⇒ 挂 %d 条（%s）" % (label, res[1], u"符合预期"))
        finally:
            io.open(path, "w", encoding="utf-8", newline=u"\n").write(original)

        # ⚠ 还原必须**按内容哈希**核（第一版我用"坏串还在不在"判，而 K5 的坏串正好是
        #   好串的子串 ⇒ 假 FAIL，与 §4.30「先怀疑期望」同一条）
        after = hashlib.sha1(io.open(path, encoding="utf-8").read().encode("utf-8")).hexdigest()
        if after != before:
            fails.append(u"%s：还原后内容哈希不一致（%s != %s）" % (label, after[:8], before[:8]))
        else:
            print(u"         ↳ 还原后内容哈希一致 %s ✓" % before[:8])

        res2, out2 = run_verifier()
        if res2 is None or res2[1] != 0:
            fails.append(u"%s：还原后没回到全绿（%s）" % (label, res2))
        else:
            print(u"         ↳ 还原后 通过 = %d 失败 = 0 ✓" % res2[0])

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
