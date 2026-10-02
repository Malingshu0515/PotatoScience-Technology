# -*- coding: utf-8 -*-
u"""_zf167_verify.py —— ZF167 的常驻校验：空铝罐 + 可乐 + 饮料罐装机（0.13）

用户原话（逐字）：
    「先加个空铝罐配方；【】【铝粒】【】，【】【铝板】【】，【】【】【】合成2个空铝罐
      熔炉/高炉烧制一个空铝罐产出5个铝粒；再加一个饮料罐装机（配方；【】【铁锭】【】，
      【拉杆】【银版】【铁活版门】，【轻质压力板】【高压气罐】【流体管道】）
      一个碳酸储罐（100MB）一个水储罐（1000mb）一个乙醇储罐（100mb 目前本mod没有乙醇
      做个兼容别的mod的乙醇）三个输入槽 一个输出槽 耗电600fe/t 先做一个配方试试水
      1.10mb碳酸+500mb水+2糖+1可可豆+1空铝罐 5s产出1罐可乐
      可乐是食物 但是食用音效用蜂蜜瓶的 食用后给予120s的急迫 3s的生命恢复1
      恢复3点饥饿值 9点饱和度 （食用后返还一个空铝罐）」

断言分五类、每条带稳定 id（反证脚本按 id 点名校验"这一刀必须被这一条咬住"）：
  A **源码结构**：七处数值各落在哪、能不能作弊（自己写死的数、漏 JEI case、状态码蹭号…）
  B **资源/数据**：贴图占位是不是逐字节副本、四份配方的形状、`c:ethanol` 标签、五语言键
  C **端到端证据**：真服务端探针 `Zf167Check` 的报告（跑一轮的账 + 可乐真吃一罐 + 负向对照）
  D **没把往轮的门弄红**（真跑）
  E **开工前就红的门**（只记录，不判红）

⚠ 判据吃**被测对象本身**：A 读真源码（先 strip_comments，§4.152），B 读真字节/真 JSON，
   C 读探针跑出来的真报告，D 是真跑别人的门。

跑法：python build\\zftools\\_zf167_verify.py [--fast]
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
CHECK = os.path.join(TOOLS, "check")
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(ASSETS, "lang")
DATA = os.path.join(ROOT, r"src\main\resources\data")
PROBE_REPORT = os.path.join(CHECK, u"zf167_罐装机取证.log")

COLA = os.path.join(MOD, "ColaItem.java")
RECIPES = os.path.join(MOD, "CanningMachineRecipes.java")
BE = os.path.join(MOD, "BeverageCanningMachineBlockEntity.java")
BLOCK = os.path.join(MOD, "BeverageCanningMachineBlock.java")
MENU = os.path.join(MOD, "BeverageCanningMachineMenu.java")
SCREEN = os.path.join(MOD, r"client\BeverageCanningMachineScreen.java")
LAMP = os.path.join(MOD, r"client\gui\parts\StatusLampPart.java")
ITEMS = os.path.join(MOD, "ModItems.java")
BLOCKS = os.path.join(MOD, "ModBlocks.java")
MENUS = os.path.join(MOD, "ModMenus.java")
MAIN = os.path.join(MOD, "PotatoST.java")
CLIENT = os.path.join(MOD, "PotatoSTClient.java")
JEI = os.path.join(MOD, r"client\jei\PotatoSTJeiPlugin.java")
MACHINE_RECIPES = os.path.join(MOD, "MachineRecipes.java")

fails, n_pass = [], 0


def check(cid, name, ok, detail=u""):
    global n_pass
    if ok:
        n_pass += 1
        print(u"  [OK]   %s %s %s" % (cid, name, detail))
    else:
        fails.append(cid)
        print(u"  [FAIL] %s %s %s" % (cid, name, detail))


def eq(cid, name, want, got):
    check(cid, name, want == got, u"（期望 %r，实际 %r）" % (want, got))


def read(p):
    return io.open(p, encoding="utf-8").read()


def raw(p):
    return open(p, "rb").read()


def strip_comments(text):
    text = re.sub(u"/\\*.*?\\*/", u"", text, flags=re.S)
    return re.sub(u"(?m)//.*$", u"", text)


def cut(text, start, end):
    u"""取 [start, end)；任一锚点不在就返回空串（§4.151：绝不一路取到文件尾）。"""
    i = text.find(start)
    if i < 0:
        return u""
    j = text.find(end, i)
    return u"" if j < 0 else text[i:j]


# ================================================================
#  A 源码结构
# ================================================================
def section_a():
    print(u"\n================ A 源码结构 ================")
    for p in (COLA, RECIPES, BE, BLOCK, MENU, SCREEN):
        check(u"A0", u"新文件在（%s）" % os.path.basename(p), os.path.exists(p))
    if fails:
        return
    cola = strip_comments(read(COLA))
    rec = strip_comments(read(RECIPES))
    # ⚠ 切片的锚点**必须从原文里找**（下面几处收尾锚点是注释行）：
    #   先 strip_comments 会把 `// ==== 创造模式标签页 ====` 与 javadoc 一起剃掉 ⇒
    #   cut() 找不到收尾锚点 ⇒ 返回空串 ⇒ 判据假红。ZF153 的 A11 踩过一模一样的一次，
    #   这一轮又踩了（所以这次两处都从原文切、切完再剥）。
    be_raw = read(BE)
    be = strip_comments(be_raw)
    blk = strip_comments(read(BLOCK))
    items_raw = read(ITEMS)
    items = strip_comments(items_raw)
    blocks = strip_comments(read(BLOCKS))
    menus = strip_comments(read(MENUS))
    main = strip_comments(read(MAIN))
    client = strip_comments(read(CLIENT))
    jei = strip_comments(read(JEI))
    lamp = strip_comments(read(LAMP))

    # --- 可乐 ---
    check(u"A1", u"ColaItem 继承 Item", re.search(u"class\\s+ColaItem\\s+extends\\s+Item", cola) is not None)
    check(u"A2", u"食用音效与饮用音效都是蜂蜜瓶那一支（SoundEvents.HONEY_DRINK）",
          cola.count(u"SoundEvents.HONEY_DRINK") == 2)
    check(u"A3", u"两条时长常量：急迫 20*120、生命恢复 20*3",
          re.search(u"HASTE_TICKS\\s*=\\s*20\\s*\\*\\s*120", cola) is not None
          and re.search(u"REGENERATION_TICKS\\s*=\\s*20\\s*\\*\\s*3", cola) is not None)
    # 食物数值（在 ModItems 里挂）—— 从**原文**切，切完再剥注释
    block = strip_comments(cut(items_raw, u"COLA =", u"// ========== 创造模式标签页"))
    check(u"A4", u"注册处挂了 food(...)：饥饿 3 + 饱和度修饰 1.5F（⇒ 9 点）",
          u".nutrition(3)" in block and u".saturationModifier(1.5F)" in block)
    check(u"A5", u"两条效果：DIG_SPEED（急迫）+ REGENERATION，用 ColaItem 的常量",
          u"MobEffects.DIG_SPEED" in block and u"ColaItem.HASTE_TICKS" in block
          and u"MobEffects.REGENERATION" in block and u"ColaItem.REGENERATION_TICKS" in block)
    check(u"A6", u"吃完返还空铝罐走**原版** usingConvertsTo（不是自己写的返还逻辑）",
          u".usingConvertsTo(EMPTY_ALUMINUM_CAN.get())" in block and u"finishUsingItem" not in cola)

    # --- 配方表 ---
    check(u"A7", u"配方表：一轮 20*5 tick、600 FE/t",
          re.search(u"DURATION_TICKS\\s*=\\s*20\\s*\\*\\s*5", rec) is not None
          and re.search(u"ENERGY_PER_TICK\\s*=\\s*600", rec) is not None)
    check(u"A8", u"配方表：2 糖 / 1 可可豆 / 1 空铝罐",
          re.search(u"SUGAR_COUNT\\s*=\\s*2", rec) is not None
          and re.search(u"COCOA_COUNT\\s*=\\s*1", rec) is not None
          and re.search(u"CAN_COUNT\\s*=\\s*1", rec) is not None)
    check(u"A9", u"配方表：10 mB 碳酸 / 500 mB 水 / 0 mB 乙醇",
          re.search(u"CARBONIC_MB\\s*=\\s*10", rec) is not None
          and re.search(u"WATER_MB\\s*=\\s*500", rec) is not None
          and re.search(u"ETHANOL_MB\\s*=\\s*0", rec) is not None)
    check(u"A10", u"产出那一栈是**现取**的（表里没有 static final ItemStack，§4.1）",
          u"new ItemStack(this.result" in rec or u"new ItemStack(this.result," in rec)

    # --- 方块实体 ---
    check(u"A11", u"三只罐的容量：碳酸 100 / 水 1000 / 乙醇 100",
          re.search(u"TANK_CAPACITY_CARBONIC\\s*=\\s*100", be) is not None
          and re.search(u"TANK_CAPACITY_WATER\\s*=\\s*1000", be) is not None
          and re.search(u"TANK_CAPACITY_ETHANOL\\s*=\\s*100", be) is not None)
    check(u"A12", u"储能 = 600 × 20（20 tick 的钱）",
          re.search(u"MAX_ENERGY\\s*=\\s*600\\s*\\*\\s*20", be) is not None)
    check(u"A13", u"三个输入槽 + 一个输出槽（槽号 0/1/2/3）",
          u"SLOT_SUGAR = 0" in be and u"SLOT_COCOA = 1" in be and u"SLOT_CAN = 2" in be
          and u"SLOT_OUTPUT = 3" in be and u"SLOT_COUNT = 4" in be)
    check(u"A14", u"碳酸罐校验器 = 本 mod 的碳酸流体类型",
          u"ModFluids.CARBONIC_ACID_TYPE.get()" in be)
    check(u"A15", u"水罐校验器 = 原版水的流体类型",
          u"NeoForgeMod.WATER_TYPE.value()" in be)
    check(u"A16", u"乙醇罐校验器 = c:ethanol 标签（兼容别的 mod）",
          u"ETHANOL_TAG" in be and u"getFluid().is(ETHANOL_TAG)" in be
          and re.search(u'ETHANOL_TAG\\s*=\\s*FluidTags\\.create\\(\\s*'
                        u'ResourceLocation\\.fromNamespaceAndPath\\("c",\\s*"ethanol"\\)', be) is not None)
    check(u"A17", u"四种槽位门禁：糖 / 可可豆 / 空铝罐 / 输出槽不许放",
          u"Items.SUGAR" in be and u"Items.COCOA_BEANS" in be
          and u"ModItems.EMPTY_ALUMINUM_CAN.get()" in be and u"default -> false" in be)
    check(u"A18", u"输入罐只进不出（drain 永远返回空）",
          be.count(u"return FluidStack.EMPTY;") >= 2)

    # 每 tick 的检查顺序：电 → 流体 → 输出
    body = cut(be, u"private void serverTickBody()", u"private static String keyOf(")
    i_e = body.find(u"can.energyPerTick()")
    i_f = body.find(u"hasFluids(can)")
    i_o = body.find(u"canInsert(can.createOutput())")
    check(u"A19", u"每 tick 的检查顺序：先电、再流体、最后输出位置",
          body != u"" and 0 <= i_e < i_f < i_o, u"电@%d 流体@%d 输出@%d" % (i_e, i_f, i_o))

    fin = strip_comments(cut(be_raw, u"private boolean finish(", u"/** 输出槽能不能装下这一栈"))
    check(u"A20", u"结算时整批扣三种流体（按配方给的 mB）",
          fin.count(u".drain(can.") == 3 and u"can.carbonicMb()" in fin
          and u"can.waterMb()" in fin and u"can.ethanolMb()" in fin)
    check(u"A21", u"结算时扣三样物品（extractItem ×3）", fin.count(u"extractItem(") == 3)
    check(u"A22", u"产物用 setStackInSlot **直写**（不查 isItemValid，§4.13 同族坑）",
          u"setStackInSlot(SLOT_OUTPUT" in fin and u"insertItem(" not in fin)
    check(u"A23", u"罐也存盘（writeToNBT / readFromNBT 各一次以上）",
          be.count(u"writeToNBT(") >= 1 and be.count(u"readFromNBT(") >= 1)
    check(u"A24", u"「缺流体」用**新号 20**（没蹭液压机的 6）",
          re.search(u"STATUS_NO_FLUID\\s*=\\s*20", be) is not None)
    check(u"A25", u"状态灯那两个 switch 都挂了新号（colorOf + suffixOf）",
          lamp.count(u"BeverageCanningMachineBlockEntity.STATUS_NO_FLUID") == 2
          and u'"no_fluid"' in lamp)

    # --- 方块 ---
    check(u"A26", u"方块 ticker 挂在 BE::tick 上",
          u"BeverageCanningMachineBlockEntity::tick" in blk)
    check(u"A27", u"手倒走**物品流体能力**（原版水桶也认）",
          u"Capabilities.FluidHandler.ITEM" in blk)
    check(u"A28", u"手倒的返回类型是 ItemInteractionResult（1.21 的签名）",
          u"protected ItemInteractionResult useItemOn" in blk
          and u"ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION" in blk)
    check(u"A29", u"空手右键开界面（useWithoutItem）", u"useWithoutItem" in blk)
    check(u"A30", u"破坏时掉出四个槽（onRemove + MachineDrops）+ 自己会掉（getDrops）",
          u"MachineDrops.dropInventory" in blk and u"getDrops" in blk)

    # --- 注册四处 ---
    check(u"A31", u"ModBlocks：方块 + 物品 + 方块实体 三样都注册了",
          blocks.count(u'register("beverage_canning_machine"') == 3)
    check(u"A32", u"ModMenus 注册了菜单", u'"beverage_canning_machine"' in menus)
    check(u"A33", u"PotatoST 注册了三条能力（FE / 物品 / 流体）",
          main.count(u"ModBlocks.BEVERAGE_CANNING_MACHINE_BE.get()") == 3
          and u"Capabilities.FluidHandler.BLOCK" in main)
    check(u"A34", u"PotatoSTClient 注册了界面", u"BEVERAGE_CANNING_MACHINE_MENU" in client)
    check(u"A35", u"JEI：机器进了 MACHINES **且** iconFor 有对应 case（ZF123 的坑）",
          u'"beverage_canning_machine"' in jei
          and u'case "beverage_canning_machine"' in jei)
    check(u"A36", u"MachineRecipes：buildBeverageCanningMachine 被调用且方法在",
          u"buildBeverageCanningMachine(out)" in strip_comments(read(MACHINE_RECIPES))
          and u"private static void buildBeverageCanningMachine" in strip_comments(read(MACHINE_RECIPES)))
    mr = strip_comments(read(MACHINE_RECIPES))
    mbody = cut(mr, u"private static void buildBeverageCanningMachine", u"\n}")
    check(u"A37", u"JEI 那条展示的数值**转调** CanningMachineRecipes 的常量（不另写数字）",
          mbody != u"" and mbody.count(u"CanningMachineRecipes.") >= 5 and u"500" not in mbody
          and u"600" not in mbody)

    # --- 纪律：不许硬编码中文 ---
    bad = []
    for name in (u"ColaItem.java", u"CanningMachineRecipes.java",
                 u"BeverageCanningMachineBlockEntity.java", u"BeverageCanningMachineBlock.java",
                 u"BeverageCanningMachineMenu.java", u"ModItems.java", u"ModBlocks.java"):
        t = strip_comments(read(os.path.join(MOD, name)))
        for m in re.finditer(u'"[^"\\n]*[\\u4e00-\\u9fff][^"\\n]*"', t):
            bad.append(u"%s: %s" % (name, m.group(0)[:30]))
    check(u"A38", u"被改/新建的 java 里没有硬编码中文串", not bad, u"；".join(bad[:3]))


# ================================================================
#  B 资源与数据
# ================================================================
def section_b():
    print(u"\n================ B 资源与数据 ================")
    btex = os.path.join(ASSETS, "textures", "block")
    # 占位贴图：逐字节副本
    for src, dst in ((u"micro_crusher_top.png", u"beverage_canning_machine_top.png"),
                     (u"micro_crusher_side.png", u"beverage_canning_machine_side.png")):
        a, b = os.path.join(btex, src), os.path.join(btex, dst)
        ok = os.path.exists(a) and os.path.exists(b) and raw(a) == raw(b)
        check(u"B1", u"%s 是 %s 的逐字节副本（占位）" % (dst, src), ok)
    # 五个 JSON
    files = {u"blockstates/beverage_canning_machine.json": None,
             u"models/block/beverage_canning_machine.json": u"potato_s_t:block/beverage_canning_machine",
             u"models/item/beverage_canning_machine.json": u"potato_s_t:block/beverage_canning_machine",
             u"models/item/empty_aluminum_can.json": u"minecraft:item/glass_bottle",
             u"models/item/cola.json": u"minecraft:item/honey_bottle"}
    for rel, want in files.items():
        p = os.path.join(ASSETS, rel.replace(u"/", os.sep))
        ok = os.path.exists(p)
        if ok and want is not None:
            text = read(p)
            ok = want in text
        check(u"B2", u"%s 在且指向对" % rel, ok, u"" if ok else u"找 %s" % want)
    # 四份配方
    recipes = {
        u"empty_aluminum_can.json": (2, u"potato_s_t:empty_aluminum_can", None),
        u"empty_aluminum_can_from_smelting.json": (5, u"potato_s_t:aluminum_nugget", 200),
        u"empty_aluminum_can_from_blasting.json": (5, u"potato_s_t:aluminum_nugget", 100),
        u"beverage_canning_machine.json": (1, u"potato_s_t:beverage_canning_machine", None),
    }
    for name, (count, result, time) in recipes.items():
        p = os.path.join(DATA, r"potato_s_t\recipe", name)
        if not os.path.exists(p):
            check(u"B3", u"%s 在" % name, False)
            continue
        d = json.loads(read(p))
        ok = d[u"result"][u"id"] == result and d[u"result"][u"count"] == count
        if time is not None:
            ok = ok and d[u"cookingtime"] == time
        check(u"B3", u"%s：产物 %d × %s%s" % (name, count, result,
                                            u" / %d tick" % time if time else u""), ok)
    can = json.loads(read(os.path.join(DATA, r"potato_s_t\recipe\empty_aluminum_can.json")))
    check(u"B4", u"空铝罐图纸：铝粒在上、铝板在中、第三行空（用户给的样子）",
          can[u"pattern"][0][1] == u"N" and can[u"pattern"][1][1] == u"P"
          and can[u"pattern"][2].strip() == u"")
    mac = json.loads(read(os.path.join(DATA, r"potato_s_t\recipe\beverage_canning_machine.json")))
    check(u"B5", u"机器图纸与用户给的三行逐格相同（I/LST/PHF）",
          [list(r) for r in mac[u"pattern"]] == [[u" ", u"I", u" "], [u"L", u"S", u"T"], [u"P", u"H", u"F"]])
    check(u"B6", u"机器图纸的七件材料对得上（含原版轻质测重压力板）",
          mac[u"key"][u"P"][u"item"] == u"minecraft:light_weighted_pressure_plate"
          and mac[u"key"][u"S"][u"item"] == u"potato_s_t:silver_plate"
          and mac[u"key"][u"H"][u"item"] == u"potato_s_t:high_pressure_tank"
          and mac[u"key"][u"F"][u"item"] == u"potato_s_t:fluid_pipe")
    # 乙醇标签
    p = os.path.join(DATA, r"c\tags\fluid\ethanol.json")
    check(u"B7", u"c:ethanol 标签文件在", os.path.exists(p))
    if os.path.exists(p):
        d = json.loads(read(p))
        check(u"B8", u"c:ethanol 是 replace:false + 空表（与别的 mod 那份合并）",
              d.get(u"replace") is False and d.get(u"values") == [])
    # 语言
    codes = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")
    tables = {c: json.loads(read(os.path.join(LANG, c + u".json"))) for c in codes}
    four = [tables[c] for c in codes[:4]]
    check(u"B9", u"四语言键集合完全相同", len(set(frozenset(t) for t in four)) == 1,
          u" / ".join(u"%s %d" % (c, len(tables[c])) for c in codes))
    check(u"B10", u"lzh 与四份的差集恰好是 language.name / language.region",
          set(tables[u"lzh"]) - set(tables[u"zh_cn"]) == {u"language.name", u"language.region"})
    keys = ([u"item.potato_s_t.empty_aluminum_can", u"item.potato_s_t.cola",
             u"tooltip.potato_s_t.cola.1", u"tooltip.potato_s_t.cola.2",
             u"block.potato_s_t.beverage_canning_machine",
             u"tooltip.potato_s_t.beverage_canning_machine",
             u"gui.potato_s_t.canning.pour.poured", u"gui.potato_s_t.canning.pour.rejected"]
            + [u"gui.potato_s_t.beverage_canning_machine.status." + s
               for s in (u"disabled", u"empty", u"invalid", u"no_power", u"output_full",
                         u"running", u"no_fluid")])
    check(u"B11", u"本轮 %d 个键五份都有且非空" % len(keys),
          all(tables[c].get(k) for c in codes for k in keys),
          u"缺：%s" % [k for k in keys if not tables[u"zh_cn"].get(k)][:2])
    zh = tables[u"zh_cn"]
    check(u"B12", u"机器说明里的三个容量与耗电都写着（100 / 1000 / 100 / 600）",
          all(s in zh[u"tooltip.potato_s_t.beverage_canning_machine"]
              for s in (u"100", u"1000", u"600")))
    check(u"B13", u"可乐说明里写着 120 / 3 / 3 / 9 四个数",
          all(s in zh[u"tooltip.potato_s_t.cola.1"] for s in (u"120", u"3", u"9")))
    check(u"B14", u"说明里没有 ASCII 双引号（中文串一律「」）",
          not [k for k in keys if u'"' in zh.get(k, u"")])
    # 借原版
    borrowed = []
    for fn in sorted(os.listdir(os.path.join(ASSETS, r"models\item"))):
        if fn.endswith(u".json"):
            d = json.loads(read(os.path.join(ASSETS, r"models\item", fn)))
            l0 = d.get(u"textures", {}).get(u"layer0", u"")
            if isinstance(l0, str) and l0.startswith(u"minecraft:"):
                borrowed.append(fn[:-5])
    check(u"B15", u"空铝罐与可乐都在「借原版贴图」名单里（待画表里有它们）",
          u"empty_aluminum_can" in borrowed and u"cola" in borrowed,
          u"借原版 %d 个" % len(borrowed))


# ================================================================
#  C 探针报告
# ================================================================
def section_c():
    print(u"\n================ C 真服务端探针报告 ================")
    check(u"C1", u"报告在盘上（%s）" % os.path.basename(PROBE_REPORT), os.path.exists(PROBE_REPORT))
    if not os.path.exists(PROBE_REPORT):
        return
    rep = read(PROBE_REPORT)
    nfail = len(re.findall(u"\\[FAIL\\]", rep))
    check(u"C2", u"报告里 0 条 [FAIL]", nfail == 0, u"实测 %d 条" % nfail)
    check(u"C3", u"verdict = ALL OK", u"verdict: ALL OK" in rep)
    for cid, needle, label in [
        (u"C4", u"[OK]   B7 罐装机那一条配方命中", u"配方命中（2 糖 + 1 可可豆 + 1 空铝罐）"),
        (u"C5", u"[OK]   B1 空铝罐的合成配方在", u"合成配方真的加载了"),
        (u"C6", u"[OK]   B4 smelting 产物 = 5 个铝粒", u"熔炉 5 铝粒"),
        (u"C7", u"[OK]   B4 blasting 产物 = 5 个铝粒", u"高炉 5 铝粒"),
        (u"C8", u"[OK]   C1 容量：碳酸 100 / 水 1000 / 乙醇 100 mB", u"罐容量"),
        (u"C9", u"[OK]   C9 产出 1 罐可乐", u"真跑一轮产出可乐"),
        (u"C10", u"[OK]   C11 碳酸正好扣 10 mB", u"扣 10 mB 碳酸"),
        (u"C11", u"[OK]   C12 水正好扣 500 mB", u"扣 500 mB 水"),
        (u"C12", u"[OK]   C13 乙醇一点没动", u"乙醇没动"),
        (u"C13", u"[OK]   C15 净耗电 = 60,000 FE", u"一轮 60,000 FE"),
        (u"C14", u"[OK]   C6 三只罐都是**只进不出**", u"输入罐只进不出"),
        (u"C15", u"[OK]   D2 乙醇罐**不收**水", u"乙醇罐负向对照"),
        (u"C16", u"[OK]   D5 碳酸罐**不收**水", u"碳酸/水互斥"),
        (u"C17", u"[OK]   E2 恢复 3 点饥饿值", u"可乐真吃：饥饿 +3"),
        (u"C18", u"[OK]   E3 恢复 9 点饱和度", u"可乐真吃：饱和 +9"),
        (u"C19", u"[OK]   E4 急迫 120 秒", u"急迫 2400 tick"),
        (u"C20", u"[OK]   E5 生命恢复 I 3 秒", u"生命恢复 60 tick"),
        (u"C21", u"[OK]   E6 吃完返还一个空铝罐", u"返还空罐"),
        (u"C22", u"[OK]   E9 输出槽被石头占着", u"输出满 ⇒ OUTPUT_FULL"),
        (u"C23", u"[OK]   E11 没电", u"缺电 ⇒ NO_POWER"),
        (u"C24", u"[OK]   E12 有料有电但罐是空的", u"缺流体 ⇒ NO_FLUID"),
        (u"C25", u"[OK]   C7 红石信号下状态 = DISABLED", u"红石 ⇒ 停机"),
    ]:
        check(cid, label, needle in rep, u"找 %s" % needle)


# ================================================================
#  D 往轮的门
# ================================================================
def section_d():
    print(u"\n================ D 往轮的门没被弄红（真跑）================")
    for cid, script in [(u"D1", u"_zf114_verify.py"), (u"D2", u"_zf142_verify.py"),
                        (u"D3", u"_zf145_verify.py"), (u"D4", u"_zf148_verify.py"),
                        (u"D5", u"_zf149_verify.py"), (u"D6", u"_zf150_verify.py"),
                        (u"D7", u"_zf153_verify.py")]:
        p = os.path.join(TOOLS, script)
        if not os.path.exists(p):
            check(cid, u"%s 在盘上" % script, False)
            continue
        r = subprocess.run([sys.executable, p], cwd=ROOT, capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        tail = [l for l in out.split(u"\n") if l.strip()][-1:] or [u""]
        check(cid, u"%s 仍然 exit 0" % script, r.returncode == 0,
              u"（%s）" % tail[0].strip()[:70])


def section_e():
    print(u"\n================ E 开工前就红的门（只记录）================")
    for script, why in [
        (u"_zf141_verify.py", u"别人清了 build/用户素材 里的星璨钢源图 + 配方数变了（往轮已记档）"),
        (u"_zf119_verify.py", u"别人清了 build/用户素材/振金锭.png"),
        (u"_zf139_verify.py", u"配方份数被别人加过（活体数字）"),
    ]:
        p = os.path.join(TOOLS, script)
        r = subprocess.run([sys.executable, p], cwd=ROOT, capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        nfail = len(re.findall(u"\\[FAIL\\]|!!", out))
        print(u"  [记录] %s exit=%d，%d 条失败 —— %s" % (script, r.returncode, nfail, why))


def main():
    fast = u"--fast" in sys.argv
    section_a()
    section_b()
    section_c()
    if fast:
        print(u"\n（--fast：跳过 D 往轮门 / E 记录）")
    else:
        section_d()
        section_e()
    print(u"\n通过 %d 项，失败 %d 项" % (n_pass, len(fails)))
    if fails:
        print(u"失败清单：%s" % u"、".join(fails))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
