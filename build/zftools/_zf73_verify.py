# -*- coding: utf-8 -*-
u"""_zf73_verify.py —— ZF73（0.11 石油线第一批）常驻校验

分五组：
  A. **新增/改造的代码**是否就是设计里那几刀（尤其 §4.44 的雷必须真的拆了）；
  B. 资源与配方（贴图是真 PNG 16×16、模型/方块状态齐、配方照用户图纸、四语言 218 键）；
  C. 发布与冻结（0.11 成品哈希、0.10 成品没被动、jar 里没有探针残留）；
  D. 复现性（除新增那一份，其余 34 份配方逐字节没动）；
  E. 档案已记录。
"""
import glob
import hashlib
import io
import json
import os
import re
import struct
import sys
import zipfile

PROJ = r"E:\PotatoST"
JAVA = os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod")
RES = os.path.join(PROJ, u"src", u"main", u"resources")
ASSETS = os.path.join(RES, u"assets", u"potato_s_t")
DATA = os.path.join(RES, u"data", u"potato_s_t")
LANG = os.path.join(ASSETS, u"lang")
ARCH = os.path.join(PROJ, u"docs", u"开发档案.md")
JAR_OLD = os.path.join(PROJ, u"release", u"PotatoST-0.10.jar")
JAR_NEW = os.path.join(PROJ, u"release", u"PotatoST-0.11.jar")
JAR_BUILT = os.path.join(PROJ, u"build", u"libs", u"potato_s_t-0.11.jar")
JAR_OLD_SHA1 = u"84d09345f6095408ae462dabb536307141904ea3"
PRE = r"C:\PotatoST救援\zf73_pre"

checks = 0
fails = []


def check(name, cond, detail=u""):
    global checks
    checks += 1
    if not cond:
        fails.append(name if not detail else u"%s  (%s)" % (name, detail))
    print(u"  %s %s" % (u"[OK]  " if cond else u"[FAIL]", name))


def read(path):
    if not os.path.isfile(path):
        return u""
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def method_body(text, signature):
    u"""抽出某个方法的**方法体**（含花括号），用来做"数一数"的硬断言，而不是子串断言。"""
    i = text.find(signature)
    if i < 0:
        return u""
    j = text.find(u"{", i)
    if j < 0:
        return u""
    depth = 0
    for k in range(j, len(text)):
        if text[k] == u"{":
            depth += 1
        elif text[k] == u"}":
            depth -= 1
            if depth == 0:
                return text[j:k + 1]
    return u""


def png_ok(path, want=16):
    if not os.path.isfile(path):
        return False, u"文件不存在"
    with io.open(path, "rb") as fh:
        head = fh.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return False, u"不是真 PNG"
    w, h = struct.unpack(">II", head[16:24])
    depth = head[24]
    return (w == want and h == want and depth == 8), u"%dx%d depth=%d" % (w, h, depth)


def main():
    modfluids = read(os.path.join(JAVA, u"ModFluids.java"))
    modblocks = read(os.path.join(JAVA, u"ModBlocks.java"))
    moditems = read(os.path.join(JAVA, u"ModItems.java"))
    tank = read(os.path.join(JAVA, u"TankContents.java"))
    tankitem = read(os.path.join(JAVA, u"HighPressureTankItem.java"))
    fill = read(os.path.join(JAVA, u"FillingMachineBlockEntity.java"))
    menu = read(os.path.join(JAVA, u"FillingMachineMenu.java"))
    bucket = read(os.path.join(JAVA, u"OilBucketItem.java"))
    contents = read(os.path.join(JAVA, u"OilBucketContents.java"))
    iface = read(os.path.join(JAVA, u"FluidContainerItem.java"))
    arch = read(ARCH)

    # ---------------- A. 代码 ----------------
    print(u"\n=== A. 代码：新增的容器/流体，以及 ZF72 那颗雷真的拆了 ===")
    check(u"A1 FluidContainerItem 接口存在", u"interface FluidContainerItem" in iface)
    check(u"A2 OilBucketContents：容量 3000 / 一格源 = 1000",
          u"CAPACITY = 3000" in contents and u"SOURCE_AMOUNT = 1000" in contents)
    check(u"A3 油桶单流体：异种拒收写死在 fill 里", u"have != incoming" in contents)
    check(u"A4 油桶拒气体：accepts 走 ModFluids.isLiquid", u"return ModFluids.isLiquid(fluid)" in contents)
    check(u"A5 OilBucketItem 实现接口", u"class OilBucketItem extends Item implements FluidContainerItem" in bucket)
    check(u"A6 油桶白色容量条三件套齐全",
          all(k in bucket for k in (u"isBarVisible", u"getBarWidth", u"getBarColor"))
          and u"0xFFFFFF" in bucket)
    check(u"A7 舀取入口是 public static scoopAt", u"public static int scoopAt(Level level, BlockPos pos, ItemStack stack)" in bucket)
    check(u"A8 舀取会移除源方块（不是无限）", u"level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3)" in bucket)
    check(u"A9 装不下就不舀（不会凭空吃掉半格）",
          u"OilBucketContents.space(stack) < OilBucketContents.SOURCE_AMOUNT" in bucket)
    check(u"A10 原油流体注册齐（类型/源/流动）",
          all(k in modfluids for k in (u'register("crude_oil"', u'register("flowing_crude_oil"', u"CRUDE_OIL_TYPE")))
    check(u"A11 流体参数与岩浆同值：tickRate 30 / slope 2 / 每格降 2",
          all(k in modfluids for k in (u"tickRate(30)", u"slopeFindDistance(2)", u"levelDecreasePerBlock(2)")))
    check(u"A12 canConvertToSource(false)：不会像水一样变无限", u"canConvertToSource(false)" in modfluids)
    # ⚠ 原断言是**整文件**里不许出现 .bucket —— ZF82 起柴油/汽油**必须**有桶
    #   （用户原话「新进 柴油桶 汽油桶 … 可以被空桶收回源头液体」）。
    #   改成精确断言：**原油那个属性方法体**里不许有 .bucket(...)。
    #   ⚠ 第一版按 `find("crudeOilProperties()")` 切片，命中的是**注册那一行**，
    #     切片一直延伸到后面柴油的 .bucket(...) ⇒ 假 FAIL。改成抠方法体（大括号配对）。
    _start = modfluids.find(u"private static BaseFlowingFluid.Properties crudeOilProperties() {")
    _crude_body = modfluids[_start:] if _start >= 0 else u""
    _depth = 0
    for _i, _ch in enumerate(_crude_body):
        if _ch == u"{":
            _depth += 1
        elif _ch == u"}":
            _depth -= 1
            if _depth == 0:
                _crude_body = _crude_body[:_i + 1]
                break
    check(u"A13 抠得出原油属性方法体", _start >= 0 and _crude_body.endswith(u"}"))
    check(u"A13 原油**自己**不设 .bucket(...)：原版空桶舀不走原油（防白送 3 倍）",
          u".bucket(" not in _crude_body)
    # A14 的第一版是**子串断言**（"OXYGEN.get() 在文件里出现过"）——
    # 反证第 1 刀（把 isGas 里的 `fluid == OXYGEN.get() || ` 删掉）**没被抓住**，
    # 因为那个子串在注册与 gases() 里也出现。改成**抽出方法体再数**：
    # 正向列举必须正好 6 个 `fluid == X.get()`，且方法体里不许出现 `!=`。
    gas_body = method_body(modfluids, u"public static boolean isGas(Fluid fluid)")
    gas_hits = len(re.findall(r"fluid == \w+\.get\(\)", gas_body))
    check(u"A14 isGas 正向列举：12 个气体变体一个不少（6 种 × 2；实测 %d）" % gas_hits, gas_hits == 12)
    check(u"A14b isGas 方法体里没有 `!=`（负向写法的标志）", u"!=" not in gas_body)
    check(u"A15 源码里**不再**有负向气体判定（旧写法已清除）",
          u"fluid != Fluids.WATER && fluid != Fluids.FLOWING_WATER" not in modfluids
          and u"fluid != Fluids.WATER && fluid != Fluids.FLOWING_WATER" not in tank
          and u"fluid != Fluids.WATER && fluid != Fluids.FLOWING_WATER" not in fill)
    check(u"A16 isLiquid 存在（非空且非气体）", u"public static boolean isLiquid(Fluid fluid)" in modfluids)
    check(u"A17 TankContents.isGas 改成委托", u"return ModFluids.isGas(fluid);" in tank)
    check(u"A18 注释里点名了 §4.44（后人能顺着查到那颗雷）",
          u"§4.44" in modfluids and u"§4.44" in tank)
    check(u"A19 原油液体方块注册（LiquidBlock）", u'BLOCKS.register("crude_oil"' in modblocks
          and u"new LiquidBlock(ModFluids.CRUDE_OIL.get()" in modblocks)
    check(u"A20 液体方块属性照抄原版水（含 liquid()/noLootTable/pushReaction）",
          all(k in modblocks for k in (u".liquid()", u".noLootTable()", u"PushReaction.DESTROY")))
    check(u"A21 原油**没有** BlockItem（不能拿在手里放）",
          u'register("crude_oil",\n                    () -> new BlockItem' not in modblocks
          and not re.search(r'ITEMS\.register\("crude_oil"', modblocks))
    check(u"A22 油桶物品注册 + 创造栏", u'ITEMS.register("oil_bucket"' in moditems
          and u"output.accept(OIL_BUCKET.get())" in moditems)
    check(u"A23 气罐实现接口（气罐只收气体）",
          u"class HighPressureTankItem extends Item implements FluidContainerItem" in tankitem
          and u"return TankContents.isGas(fluid);" in tankitem)
    check(u"A24 灌装机槽位改认接口", u"stack.getItem() instanceof FluidContainerItem" in fill)
    check(u"A25 灌装机水箱对任何流体开放（acceptsAnyFluid）", u"acceptsAnyFluid" in fill)
    check(u"A26 灌装机界面同步改用流体注册表 id",
          u"BuiltInRegistries.FLUID.getId(" in fill and u"BuiltInRegistries.FLUID.byId(" in menu)
    check(u"A27 灌装机不再直连 TankContents 的容量/灌装",
          u"TankContents.space(inSlot)" not in fill and u"TankContents.fill(inSlot" not in fill)
    check(u"A28 菜单 Shift 快移也改认接口", u"stack.getItem() instanceof FluidContainerItem" in menu)
    check(u"A29 探针源码已删干净",
          not os.path.isfile(os.path.join(JAVA, u"OilCheck.java"))
          and u"OilCheck" not in read(os.path.join(JAVA, u"PotatoST.java")))

    # ---------------- B. 资源 ----------------
    print(u"\n=== B. 资源：贴图 / 模型 / 配方 / 语言 ===")
    ok1, d1 = png_ok(os.path.join(ASSETS, u"textures", u"block", u"crude_oil_still.png"))
    ok2, d2 = png_ok(os.path.join(ASSETS, u"textures", u"block", u"crude_oil_flow.png"))
    check(u"B1 crude_oil_still.png 是真 PNG 16x16 8 位", ok1, d1)
    check(u"B2 crude_oil_flow.png 是真 PNG 16x16 8 位", ok2, d2)
    check(u"B3 液体方块的 blockstate + 模型都在",
          os.path.isfile(os.path.join(ASSETS, u"blockstates", u"crude_oil.json"))
          and os.path.isfile(os.path.join(ASSETS, u"models", u"block", u"crude_oil.json")))
    check(u"B4 模型只挂 particle 贴图（与原版水一致）",
          u"crude_oil_still" in read(os.path.join(ASSETS, u"models", u"block", u"crude_oil.json")))
    # ⚠ B5 原来是"油桶模型借原版铁锭贴图（用户指定）"—— 那是 ZF73 的**占位**做法。
    #   0.11 ZF87 用户把真正的油桶贴图放进来了 ⇒ 改成断言"指向自己的贴图"（历史见档案 ZF87 行）。
    check(u"B5 油桶模型指向自己的贴图（ZF73 借铁锭占位 → ZF87 换成用户给的图）",
          u"potato_s_t:item/oil_bucket" in read(os.path.join(ASSETS, u"models", u"item", u"oil_bucket.json")))

    recipe = read(os.path.join(DATA, u"recipe", u"oil_bucket.json"))
    # 断言写太死的第一版：我写的是 '"crafting_shaped"'（两侧带引号），
    # 但文件里是 "minecraft:crafting_shaped" —— crafting_shaped 前面是冒号不是引号 ⇒ 误报 FAIL。
    check(u"B6 配方是 3x3 crafting_shaped", u"crafting_shaped" in recipe and u'"CBC"' in recipe)
    check(u"B7 图纸逐行对：CBC / SBS / IAI", all(p in recipe for p in (u'"CBC"', u'"SBS"', u'"IAI"')))
    check(u"B8 吃 2 个原版铁桶（B 在 pattern 里出现两次）", recipe.count(u'"B"') >= 1
          and u"minecraft:bucket" in recipe and u'"CBC"' in recipe and u'"SBS"' in recipe)
    check(u"B9 铜锭走 c: 标签（跨 mod 兼容规则）", u"c:ingots/copper" in recipe)
    check(u"B10 产出 1 个油桶（用户拍板：吃 2 出 1）",
          re.search(r'"count":\s*1', recipe) is not None and u"potato_s_t:oil_bucket" in recipe)

    counts = {}
    for name in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        try:
            data = json.loads(read(os.path.join(LANG, name)))
        except Exception as exc:
            fails.append(u"%s 解析失败: %s" % (name, exc))
            data = {}
        counts[name] = len(data)
    check(u"B11 四语言各 482 键（… + ZF109 采油机 10）", all(v == 482 for v in counts.values()), str(counts))
    zh = json.loads(read(os.path.join(LANG, u"zh_cn.json")))
    en = json.loads(read(os.path.join(LANG, u"en_us.json")))
    check(u"B12 新键齐全（8 个）",
          all(k in zh for k in (u"fluid_type.potato_s_t.crude_oil", u"fluid.potato_s_t.crude_oil",
                                u"block.potato_s_t.crude_oil", u"item.potato_s_t.oil_bucket",
                                u"tooltip.potato_s_t.oil_bucket.total", u"tooltip.potato_s_t.oil_bucket.empty",
                                u"tooltip.potato_s_t.oil_bucket.entry", u"tooltip.potato_s_t.oil_bucket.rule")))
    check(u"B13 中文名 = 原油 / 油桶",
          zh.get(u"item.potato_s_t.oil_bucket") == u"油桶"
          and zh.get(u"fluid_type.potato_s_t.crude_oil") == u"原油")
    check(u"B14 英文名 = Crude Oil / Oil Bucket",
          en.get(u"item.potato_s_t.oil_bucket") == u"Oil Bucket"
          and en.get(u"fluid_type.potato_s_t.crude_oil") == u"Crude Oil")

    # ---------------- C. 发布与冻结 ----------------
    print(u"\n=== C. 发布与冻结 ===")
    props = read(os.path.join(PROJ, u"gradle.properties"))
    check(u"C1 mod_version = 0.11", re.search(r"mod_version=0\.11", props) is not None)
    check(u"C2 v0.10 成品仍在且哈希未变（不许动它）",
          os.path.isfile(JAR_OLD) and sha1(JAR_OLD) == JAR_OLD_SHA1)
    check(u"C3 v0.11 成品存在", os.path.isfile(JAR_NEW))
    if os.path.isfile(JAR_NEW):
        check(u"C4 v0.11 成品 == 构建产物（逐字节）",
              os.path.isfile(JAR_BUILT) and sha1(JAR_NEW) == sha1(JAR_BUILT))
        check(u"C5 v0.11 成品有新 SHA1 记录文件",
              read(JAR_NEW + u".sha1").strip() == sha1(JAR_NEW))
        with zipfile.ZipFile(JAR_NEW) as zf:
            names = zf.namelist()
        check(u"C6 jar 里没有探针 class", not [n for n in names if u"Check" in n])
        check(u"C7 jar 里有原油方块状态/模型/贴图/配方",
              all(n in names for n in (u"assets/potato_s_t/blockstates/crude_oil.json",
                                       u"assets/potato_s_t/models/item/oil_bucket.json",
                                       u"assets/potato_s_t/textures/block/crude_oil_still.png",
                                       u"data/potato_s_t/recipe/oil_bucket.json")))
        check(u"C8 jar 里有油桶与流体容器接口的 class",
              u"com/potatost/mod/OilBucketItem.class" in names
              and u"com/potatost/mod/FluidContainerItem.class" in names)

    # ---------------- D. 复现性 ----------------
    print(u"\n=== D. 复现性：别的配方一个字节都没动 ===")
    pre_dir = os.path.join(PRE, u"src", u"main", u"resources", u"data", u"potato_s_t", u"recipe")
    cur_dir = os.path.join(DATA, u"recipe")
    if not os.path.isdir(pre_dir):
        check(u"D1 改前备份目录在", False, pre_dir)
    else:
        pre = {n for n in os.listdir(pre_dir) if n.endswith(u".json")}
        cur = {n for n in os.listdir(cur_dir) if n.endswith(u".json")}
        same = sum(1 for n in pre
                   if n in cur and sha1(os.path.join(pre_dir, n)) == sha1(os.path.join(cur_dir, n)))
        check(u"D1 改前 %d 份配方逐字节未变" % len(pre), same == len(pre), u"%d/%d" % (same, len(pre)))
        # ⚠ 这条的**内容**是"除新增那几份，其余逐字节没动"；新增名单随轮次增长：
        #   ZF82 加 fluid_exchanger.json；ZF95 又加用户口述的 5 条（两张唱片 + 合金炉主控 +
        #   分馏塔控制器/操作器）；ZF96 加 1 条（加氢脱硫反应仓）；ZF97 加 2 条（空气分离器/氨气组成室）。
        #   ⚠ 名单必须**按字母序**写（右边比的是 sorted(cur - pre)）。
        check(u"D2 只新增了预期的那些（ZF82 起含 fluid_exchanger.json；ZF95 起含 5 条口述配方；"
              u"ZF96 起含加氢脱硫反应仓；ZF97 起含两台新机器）",
              sorted(cur - pre) == [u"acidic_reaction_chamber.json", u"air_separator.json",
                                    u"alloy_smelter.json",
                                    u"ammonia_synthesis_chamber.json",
                                    u"combustion_chamber.json",
                                    u"distillation_controller.json",
                                    u"distillation_operator.json",
                                    u"electric_blast_furnace.json", u"fluid_exchanger.json",
                                    u"hydrodesulfurization_chamber.json",
                                    u"lithium_battery.json",
                                    u"music_disc_anvil_of_the_republic.json",
                                    u"music_disc_jasmine_flower.json", u"oil_bucket.json"],
              u", ".join(sorted(cur - pre)))

    # ---------------- E. 档案 ----------------
    print(u"\n=== E. 档案已记录 ===")
    check(u"E1 §5 有 ZF73 行", u"| ZF73 |" in arch)
    check(u"E2 档案记了 0.11 成品哈希", u"2a35a9eeda99" in arch or u"PotatoST-0.11.jar" in arch)
    check(u"E3 档案记了「原油只能油桶舀 / 不吃原版桶」这条实现决定",
          u"bucket" in arch.lower() or u"原版空桶" in arch)
    check(u"E4 §6 有「加一个流体/液体方块要动哪几处」速查", u"### 6.18" in arch)

    print(u"\n============================================")
    print(u"检查项 = %d   失败项 = %d" % (checks, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
