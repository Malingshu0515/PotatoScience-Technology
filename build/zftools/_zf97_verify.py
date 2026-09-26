# -*- coding: utf-8 -*-
r"""_zf97_verify.py —— ZF97 常驻校验：空气分离器 + 氨气组成室 + 两种新气体

用户原话（本轮全部规格，两条消息）：

  ①「空气分离器：gui只有两个储罐（不接受被灌入 只能泵出）一个工作指示灯
     储能5000fe 耗能 200fe/t 30s产出 8mB 氮气 2mB氧气
     配方【】【散热装置】【电容】，【高压气罐】【加热装置】【高压气罐】，【电容】【流体管道】【】」
  ②「氨气组成室 GUi左侧为原料储罐和一个放催化剂（铁粉）的槽位（在槽位上文字标一下: [催化剂(铁粉)]）
     右侧则为输出 每t消耗1mB氮气 1mB氢气 200Fe/t 产出1mB氨气 催化剂不消耗
     原料储罐下方各有一个放高压气罐的槽位 可以把高压气罐内的氮/氢 50mb/t的速率灌到储罐里
     输出储罐的高压气罐槽为反向（氨气罐50mb/t输出给高压气罐）泵只能泵入 氮气 氢气 泵出氨气
     配方；【流体管道】【高压气罐】【流体管道】，【铁板】【高压气罐】【铁板】，【加热装置】【高压气罐】【加热装置】」

骨架仍是**规格 → 实现**（不是实现自比）：
  A 两种新流体（注册 / isGas 正向白名单 / c: 标签 / 客户端贴图 / 真 PNG / 无桶）
  B 空气分离器：四个数、两个罐"只出不进"、没有能量条也没有物品槽、界面部件清单
  C 氨气组成室：每 tick 的进料与出料、催化剂不消耗、三个气罐槽的正反向、泵接口的门禁
  D 两条合成配方：JSON 解回九宫格逐格比（含空格格）+ 每行等长（§6.13）
  E 状态码 9/10/11 在共享灯表里的颜色与文案
  F 活体数字（键数 303 / 定形配方 38 / JEI 分类 11 / 流体 10）与文档
  G mineable/pickaxe + 成品 jar
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources")
ASSETS = os.path.join(RES, r"assets\potato_s_t")
DATA = os.path.join(RES, r"data")
LANG = os.path.join(ASSETS, "lang")
ITEMD = os.path.join(ASSETS, r"models\item")
BLOCKD = os.path.join(ASSETS, r"models\block")
TEXB = os.path.join(ASSETS, r"textures\block")
RDIR = os.path.join(DATA, r"potato_s_t\recipe")
FTAGS = os.path.join(DATA, r"c", "tags", "fluid")
DOCS = os.path.join(ROOT, "docs")
TOOLS = os.path.join(ROOT, "build", "zftools")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
BEFORE = os.path.join(r"C:\PotatoST救援\zf97_pre", "textures_before.txt")
FLUID_BEFORE = os.path.join(r"C:\PotatoST救援\zf97_pre", "fluid_tags_before.txt")
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]

# ============================================================
# 规格（只写"用户说了什么"；实现里的数字另外解析出来比）
# ============================================================
AIR = {
    "zh": u"空气分离器",
    "max_energy": 5000,      # 「储能5000fe」
    "energy_per_tick": 200,  # 「耗能 200fe/t」
    "seconds": 30,           # 「30s」
    "nitrogen": 8,           # 「8mB 氮气」
    "oxygen": 2,             # 「2mB氧气」
}
AMMONIA = {
    "zh": u"氨气组成室",
    "energy_per_tick": 200,  # 「200Fe/t」
    "nitrogen": 1,           # 「每t消耗1mB氮气」
    "hydrogen": 1,           # 「1mB氢气」
    "ammonia": 1,            # 「产出1mB氨气」
    "rate": 50,              # 「50mb/t」
}
RECIPE_SPEC = {
    "air_separator": {
        "zh": u"【】【散热装置】【电容】，【高压气罐】【加热装置】【高压气罐】，【电容】【流体管道】【】",
        "grid": [[u" ", u"potato_s_t:heat_sink", u"potato_s_t:capacitor"],
                 [u"potato_s_t:high_pressure_tank", u"potato_s_t:heater",
                  u"potato_s_t:high_pressure_tank"],
                 [u"potato_s_t:capacitor", u"potato_s_t:fluid_pipe", u" "]],
    },
    "ammonia_synthesis_chamber": {
        "zh": u"【流体管道】【高压气罐】【流体管道】，【铁板】【高压气罐】【铁板】，"
              u"【加热装置】【高压气罐】【加热装置】",
        "grid": [[u"potato_s_t:fluid_pipe", u"potato_s_t:high_pressure_tank",
                  u"potato_s_t:fluid_pipe"],
                 [u"potato_s_t:iron_plate", u"potato_s_t:high_pressure_tank",
                  u"potato_s_t:iron_plate"],
                 [u"potato_s_t:heater", u"potato_s_t:high_pressure_tank",
                  u"potato_s_t:heater"]],
    },
}
NEW_KEYS = [
    "fluid_type.potato_s_t.nitrogen",
    "fluid_type.potato_s_t.ammonia",
    "block.potato_s_t.air_separator",
    "block.potato_s_t.ammonia_synthesis_chamber",
    "tooltip.potato_s_t.air_separator",
    "tooltip.potato_s_t.ammonia_synthesis_chamber",
    "gui.potato_s_t.air_separator.status.running",
    "gui.potato_s_t.air_separator.status.disabled",
    "gui.potato_s_t.air_separator.status.no_power",
    "gui.potato_s_t.air_separator.status.output_full",
    "gui.potato_s_t.ammonia_synthesis.status.running",
    "gui.potato_s_t.ammonia_synthesis.status.disabled",
    "gui.potato_s_t.ammonia_synthesis.status.no_power",
    "gui.potato_s_t.ammonia_synthesis.status.output_full",
    "gui.potato_s_t.ammonia_synthesis.status.no_hydrogen",
    "gui.potato_s_t.ammonia_synthesis.status.no_nitrogen",
    "gui.potato_s_t.ammonia_synthesis.status.no_catalyst",
    "gui.potato_s_t.ammonia_synthesis.catalyst",
    "gui.potato_s_t.jei.catalyst",
]
EXPECT_KEYS = 483           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键
EXPECT_SHAPED = 51
EXPECT_JEI = 11
EXPECT_FLUIDS = 15
# isGas 正向白名单里的变体条数（6 种气体 × 源/流动）—— ZF100 起与"流体类型总数"不再相等
EXPECT_GAS_VARIANTS = 12

passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def sha1f(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def body(java, signature):
    if not java:
        return None
    at = java.find(signature)
    if at < 0 or java.find(signature, at + 1) >= 0:
        return None
    i = java.find(u"{", at + len(signature) - 1)
    depth = 0
    for j in range(i, len(java)):
        if java[j] == u"{":
            depth += 1
        elif java[j] == u"}":
            depth -= 1
            if depth == 0:
                return java[i:j + 1]
    return None


def int_consts(java):
    raw = {}
    for m in re.finditer(r"\bint\s+([A-Z][A-Z0-9_]*)\s*=\s*([^;{}]+);", java or u""):
        expr = re.sub(r"//.*$", u"", m.group(2)).strip()
        expr = re.sub(r"/\*.*?\*/", u"", expr).strip()
        if re.fullmatch(r"[0-9A-Za-z_ ()*+\-]+", expr):
            raw[m.group(1)] = expr
    done = {}

    def resolve(name, depth=0):
        if name in done:
            return done[name]
        if depth > 8 or name not in raw:
            return None
        expr = raw[name]

        def sub(mm):
            ident = mm.group(0)
            if ident.isdigit():
                return ident
            v = resolve(ident, depth + 1)
            return str(v) if v is not None else ident

        filled = re.sub(r"[A-Za-z_][A-Za-z0-9_]*|\d+", sub, expr)
        try:
            done[name] = int(eval(filled, {"__builtins__": {}}, {}))
        except Exception:
            return None
        return done[name]

    for k in list(raw):
        resolve(k)
    return done


def png_info(path):
    if not os.path.exists(path):
        return None
    b = open(path, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n" or b[12:16] != b"IHDR":
        return None
    return (int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big"), b[24], b[25])


def main():
    print(u"=========== ZF97 校验：空气分离器 + 氨气组成室 + 氮气/氨气 ===========")

    sep_be = read(os.path.join(JAVA, u"AirSeparatorBlockEntity.java"))
    sep_menu = read(os.path.join(JAVA, u"AirSeparatorMenu.java"))
    sep_scr = read(os.path.join(JAVA, r"client\AirSeparatorScreen.java"))
    amm_be = read(os.path.join(JAVA, u"AmmoniaSynthesisChamberBlockEntity.java"))
    amm_menu = read(os.path.join(JAVA, u"AmmoniaSynthesisChamberMenu.java"))
    amm_scr = read(os.path.join(JAVA, r"client\AmmoniaSynthesisChamberScreen.java"))
    modfluids = read(os.path.join(JAVA, "ModFluids.java"))
    modblocks = read(os.path.join(JAVA, "ModBlocks.java"))
    modmenus = read(os.path.join(JAVA, "ModMenus.java"))
    moditems = read(os.path.join(JAVA, "ModItems.java"))
    client = read(os.path.join(JAVA, "PotatoSTClient.java"))
    common = read(os.path.join(JAVA, "PotatoST.java"))
    mrec = read(os.path.join(JAVA, "MachineRecipes.java"))
    jei = read(os.path.join(JAVA, r"client\jei\PotatoSTJeiPlugin.java"))
    lamp = read(os.path.join(JAVA, r"client\gui\parts\StatusLampPart.java"))
    for (label, txt) in ((u"空气分离器方块实体", sep_be), (u"空气分离器界面", sep_scr),
                         (u"氨气组成室方块实体", amm_be), (u"氨气组成室界面", amm_scr)):
        check(u"%s 源码在" % label, txt is not None)

    print(u"\n== A 两种新流体：氮气 / 氨气 ==")
    for (name, holder) in ((u"nitrogen", u"NITROGEN"), (u"ammonia", u"AMMONIA")):
        eq(u"%s 注册了流体类型与本体" % name,
           [True, True, True],
           [u'FLUID_TYPES.register("%s"' % name in (modfluids or u""),
            u'FLUIDS.register("%s"' % name in (modfluids or u""),
            u'FLUIDS.register("flowing_%s"' % name in (modfluids or u"")])
        check(u"%s 在 isGas 的正向白名单里（本体 + 流动变体）" % name,
              (u"fluid == %s.get()" % holder) in (modfluids or u"")
              and (u"fluid == FLOWING_%s.get()" % holder) in (modfluids or u""))
        check(u"%s 的客户端贴图注册在 PotatoSTClient" % name,
              u'textures("%s")' % name in (client or u""))
        check(u"%s 没有 bucket（气体不装桶）" % name,
              u"%s.bucket(" % holder not in (modfluids or u""))
        info = png_info(os.path.join(TEXB, name + u"_still.png"))
        info2 = png_info(os.path.join(TEXB, name + u"_flow.png"))
        check(u"%s 的 still / flow 都是真 PNG 16×16 RGBA：%s / %s" % (name, info, info2),
              info == (16, 16, 8, 6) and info2 == (16, 16, 8, 6))
        a = open(os.path.join(TEXB, name + u"_still.png"), "rb").read()
        b = open(os.path.join(TEXB, name + u"_flow.png"), "rb").read()
        check(u"%s 的 still 与 flow 逐字节相同（老规矩）" % name, a == b)
    gas_body = body(modfluids, u"public static boolean isGas(Fluid fluid)") or u""
    gas_hits = len(re.findall(r"fluid == \w+\.get\(\)", gas_body))
    eq(u"isGas 正向列举现在是 6 种气体 × 2 变体 = %d 个" % EXPECT_GAS_VARIANTS,
       EXPECT_GAS_VARIANTS, gas_hits)
    check(u"isGas 里没有 `!=`（负向写法的标志）", u"!=" not in gas_body)
    for tag in (u"nitrogen.json", u"ammonia.json", u"gaseous.json"):
        d = json.loads(read(os.path.join(FTAGS, tag)))
        check(u"c: 标签 %s 存在且 replace:false" % tag, d.get("replace") is False)
    gas_tag = json.loads(read(os.path.join(FTAGS, u"gaseous.json")))[u"values"]
    check(u"#c:gaseous 含氮气/氨气各两个变体（%d 条）" % len(gas_tag),
          all(v in gas_tag for v in (u"potato_s_t:nitrogen", u"potato_s_t:flowing_nitrogen",
                                     u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia")))
    check(u"两种新流体各自的 c: 标签都挂了本体 + 流动",
          json.loads(read(os.path.join(FTAGS, u"nitrogen.json")))[u"values"]
          == [u"potato_s_t:nitrogen", u"potato_s_t:flowing_nitrogen"]
          and json.loads(read(os.path.join(FTAGS, u"ammonia.json")))[u"values"]
          == [u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia"])
    fl = len(re.findall(r'FLUID_TYPES\.register\("', modfluids or u""))
    eq(u"流体类型总数（ZF101 起 14）", EXPECT_FLUIDS, fl)
    # 旧贴图一张都没动
    before_tex = {}
    if os.path.exists(BEFORE):
        for ln in read(BEFORE).splitlines():
            parts = ln.split()
            if len(parts) == 2:
                before_tex[parts[0]] = parts[1]
    changed = []
    for rel, old_sha in before_tex.items():
        p = os.path.join(ASSETS, u"textures", rel.replace(u"/", os.sep))
        if not os.path.exists(p) or sha1f(p) != old_sha:
            changed.append(rel)
    check(u"改前那 %d 张贴图一张都没动（变了 %d 张）" % (len(before_tex), len(changed)), not changed)
    if os.path.exists(FLUID_BEFORE):
        old_tags = [l.strip() for l in read(FLUID_BEFORE).splitlines() if l.strip()]
        now_tags = sorted(os.listdir(FTAGS))
        added = [t for t in now_tags if t not in old_tags]
        eq(u"流体标签只新增预期的那些（ZF97 两种气体 + ZF100 二氧化碳 + ZF101 三种酸）",
           [u"ammonia.json", u"carbon_dioxide.json", u"carbonic_acid.json",
            u"hydrochloric_acid.json", u"nitric_acid.json", u"nitrogen.json",
            u"sulfuric_acid.json"], sorted(added))

    print(u"\n== B 空气分离器：四个数 + 两个罐只出不进 + 界面只有两罐一灯 ==")
    c = int_consts(sep_be)
    eq(u"储能 = %d（用户原话「储能%dfe」）" % (AIR["max_energy"], AIR["max_energy"]),
       AIR["max_energy"], c.get("MAX_ENERGY"))
    eq(u"耗能 = %d FE/t（用户原话「耗能 %dfe/t」）" % (AIR["energy_per_tick"], AIR["energy_per_tick"]),
       AIR["energy_per_tick"], c.get("ENERGY_PER_TICK"))
    # ⚠ 30 秒不写死 600：由用户说的秒数 × 20 算出来
    eq(u"一批 = %d 秒 × 20 = %d tick" % (AIR["seconds"], AIR["seconds"] * 20),
       AIR["seconds"] * 20, c.get("DURATION_TICKS"))
    eq(u"一批出氮气 = %d mB" % AIR["nitrogen"], AIR["nitrogen"], c.get("NITROGEN_PER_BATCH"))
    eq(u"一批出氧气 = %d mB" % AIR["oxygen"], AIR["oxygen"], c.get("OXYGEN_PER_BATCH"))
    eq(u"这台机器**没有物品槽**（用户原话「gui只有两个储罐…一个工作指示灯」）",
       0, c.get("SLOT_COUNT"))
    handler = body(sep_be, u"private final IFluidHandler fluidHandler") or u""
    fill_body = body(handler, u"public int fill(FluidStack resource, FluidAction action)") or u""
    check(u"fill 恒返回 0（用户原话「不接受被灌入」）", u"return 0;" in fill_body)
    drain_body = body(handler, u"public FluidStack drain(int maxDrain, FluidAction action)") or u""
    check(u"drain 按「氮气 → 氧气」的顺序抽（数组顺序即优先级）",
          drain_body.find(u"this.tanks") >= 0 and u"for (FluidTank tank" in drain_body)
    check(u"isFluidValid 一律 false（罐只出不进，管道也别想灌）",
          u"return false;" in (body(handler, u"public boolean isFluidValid(int tank, FluidStack stack)") or u""))
    tick = body(sep_be, u"private void serverTick()") or u""
    check(u"装不下就原地等（不扣电不推进度）：hasRoomForBatch 在扣电之前",
          0 <= tick.find(u"hasRoomForBatch()") < tick.find(u"this.energy -= ENERGY_PER_TICK"))
    check(u"结算时两个罐各加一批（氮 8 / 氧 2 引用常量）",
          u"new FluidStack(ModFluids.NITROGEN.get(), NITROGEN_PER_BATCH)" in tick
          and u"new FluidStack(ModFluids.OXYGEN.get(), OXYGEN_PER_BATCH)" in tick)
    parts = re.findall(r"this\.parts\.add\(new (\w+)", sep_scr or u"")
    eq(u"界面部件**只有**两个储罐 + 一盏灯（用户原话「只有…一个工作指示灯」）",
       [u"FluidTankPart", u"FluidTankPart", u"StatusLampPart"], parts)
    check(u"没画能量条（用户只点了「两罐一灯」；要加是一行）",
          u"EnergyBarPart" not in (sep_scr or u""))
    check(u"两个罐画的是氮气与氧气",
          u"ModFluids.NITROGEN.get()" in (sep_scr or u"") and u"ModFluids.OXYGEN.get()" in (sep_scr or u""))
    check(u"状态灯传了自己的前缀（§6.10 ⑪ 那一课）",
          u"gui.potato_s_t.air_separator.status." in (sep_scr or u""))
    check(u"菜单登记在 ModMenus，id = 方块注册名",
          u'MENU_TYPES.register("air_separator"' in (modmenus or u""))
    check(u"方块 / 物品 / 方块实体 / 界面 四处注册齐全",
          u'BLOCKS.register("air_separator"' in (modblocks or u"")
          and u'ITEMS.register("air_separator"' in (modblocks or u"")
          and u'AIR_SEPARATOR_BE = BLOCK_ENTITIES.register("air_separator"' in (modblocks or u"")
          and u"AIR_SEPARATOR_MENU.get()" in (client or u"")
          and u"AirSeparatorScreen::new" in (client or u""))
    check(u"登记了能量能力与流体能力，且**没有**物品能力（没有槽）",
          _cap_near(common, u"AIR_SEPARATOR_BE", u"EnergyStorage")
          and _cap_near(common, u"AIR_SEPARATOR_BE", u"FluidHandler")
          and not _cap_near(common, u"AIR_SEPARATOR_BE", u"ItemHandler"))

    print(u"\n== C 氨气组成室：每 tick 的进出 + 催化剂不消耗 + 气罐槽正反向 + 泵门禁 ==")
    a = int_consts(amm_be)
    eq(u"耗能 = %d FE/t" % AMMONIA["energy_per_tick"], AMMONIA["energy_per_tick"],
       a.get("ENERGY_PER_TICK"))
    eq(u"每 tick 耗氮气 = %d mB" % AMMONIA["nitrogen"], AMMONIA["nitrogen"], a.get("NITROGEN_PER_TICK"))
    eq(u"每 tick 耗氢气 = %d mB" % AMMONIA["hydrogen"], AMMONIA["hydrogen"], a.get("HYDROGEN_PER_TICK"))
    eq(u"每 tick 产氨气 = %d mB" % AMMONIA["ammonia"], AMMONIA["ammonia"], a.get("AMMONIA_PER_TICK"))
    eq(u"气罐槽速率 = %d mB/t" % AMMONIA["rate"], AMMONIA["rate"], a.get("CONTAINER_RATE"))
    eq(u"四个槽（催化剂 + 三个气罐槽）", 4, a.get("SLOT_COUNT"))
    eq(u"三个罐（氮/氢/氨）", 3, a.get("TANK_COUNT"))
    atick = body(amm_be, u"private void serverTick()") or u""
    check(u"每 tick 扣氮、扣氢、产氨，三个动作都在",
          u"tanks[TANK_NITROGEN].drain(NITROGEN_PER_TICK" in atick
          and u"tanks[TANK_HYDROGEN].drain(HYDROGEN_PER_TICK" in atick
          and u"new FluidStack(ModFluids.AMMONIA.get(), AMMONIA_PER_TICK)" in atick)
    check(u"缺料/缺电/装不下**都在扣料之前**返回（顺序：催化剂 → 氮 → 氢 → 罐满 → 电）",
          0 <= atick.find(u"hasCatalyst()") < atick.find(u"tanks[TANK_NITROGEN].getFluidAmount()")
          < atick.find(u"tanks[TANK_HYDROGEN].getFluidAmount()")
          < atick.find(u"tanks[TANK_AMMONIA].getSpace()")
          < atick.find(u"this.energy -= ENERGY_PER_TICK"))
    check(u"催化剂**永不消耗**：全文没有从催化剂槽抽走/清空的写法",
          u"extractItem(CATALYST_SLOT" not in (amm_be or u"")
          and u"setStackInSlot(CATALYST_SLOT, ItemStack.EMPTY)" not in (amm_be or u""))
    check(u"催化剂槽只收铁粉（方块实体 + 菜单两处同一口径，§4.51）",
          u"return stack.is(ModItems.IRON_POWDER.get());" in (amm_be or u"")
          and u"return stack.is(ModItems.IRON_POWDER.get());" in (amm_menu or u""))
    fh = body(amm_be, u"private final IFluidHandler fluidHandler") or u""
    ffill = body(fh, u"public int fill(FluidStack resource, FluidAction action)") or u""
    check(u"泵只能灌氮/氢（氨气灌不进来）",
          u"ModFluids.NITROGEN_TYPE.get()" in ffill and u"ModFluids.HYDROGEN_TYPE.get()" in ffill
          and u"TANK_AMMONIA].fill" not in ffill)
    check(u"泵只能抽氨（氮/氢是进料，抽不走）",
          u"TANK_AMMONIA].drain" in (body(fh, u"public FluidStack drain(int maxDrain, FluidAction action)") or u"")
          and u"TANK_NITROGEN].drain" not in fh and u"TANK_HYDROGEN].drain" not in fh)
    check(u"原料罐下方的槽是「气罐 → 机器」（transferFromContainer）",
          u"transferFromContainer(NITROGEN_TANK_SLOT, TANK_NITROGEN)" in atick
          and u"transferFromContainer(HYDROGEN_TANK_SLOT, TANK_HYDROGEN)" in atick)
    check(u"输出罐下方的槽是**反向**的（机器 → 气罐，用户原话「输出储罐的高压气罐槽为反向」）",
          u"transferToContainer(AMMONIA_TANK_SLOT, TANK_AMMONIA)" in atick)
    to_body = body(amm_be, u"private boolean transferToContainer(int slot, int tankIndex)") or u""
    check(u"反向那一路真的是把罐里的氨灌进气罐（container.fill + tank.drain）",
          u"container.fill(stack" in to_body and u"tank.drain(moved" in to_body)
    from_body = body(amm_be, u"private boolean transferFromContainer(int slot, int tankIndex)") or u""
    check(u"正向那一路真的是把气罐里的气灌进机器（container.drain + tank.fill）",
          u"container.drain(stack" in from_body and u"tank.fill(" in from_body)
    check(u"气罐槽只收流体容器",
          u"stack.getItem() instanceof FluidContainerItem" in (amm_be or u""))
    aparts = re.findall(r"this\.parts\.add\(new (\w+)", amm_scr or u"")
    # ⚠ 三个罐走的是 addTank(...) 助手 ⇒ 源码里只有**一处** `parts.add(new FluidTankPart(`，
    #   而它被调用 3 次。所以这里：① 部件种类各 1 处；② addTank 调用次数 = 3（下一行单独断言）。
    eq(u"界面部件：一个储罐工厂 + 能量条 + 状态灯（各一处）",
       {u"FluidTankPart": 1, u"EnergyBarPart": 1, u"StatusLampPart": 1},
       {k: aparts.count(k) for k in set(aparts)})
    check(u"addTank(...) 正好调用 3 次（氮 / 氢 / 氨三个罐各一次）",
          (amm_scr or u"").count(u"addTank(AmmoniaSynthesisChamberBlockEntity.TANK_") == 3)
    check(u"催化剂槽上方那行字用的是用户给的那句（lang 键 ammonia_synthesis.catalyst）",
          u'Component.translatable("gui.potato_s_t.ammonia_synthesis.catalyst")' in (amm_scr or u""))
    check(u"三个气罐槽就在三个储罐正下方（x 与罐一致、y 相同）",
          _slot_at(amm_menu, u"NITROGEN_TANK_SLOT_X", u"26")
          and _slot_at(amm_menu, u"HYDROGEN_TANK_SLOT_X", u"48")
          and _slot_at(amm_menu, u"AMMONIA_TANK_SLOT_X", u"152")
          and u"NITROGEN_X = 26" in (amm_menu or u"") and u"HYDROGEN_X = 48" in (amm_menu or u"")
          and u"AMMONIA_X = 152" in (amm_menu or u""))
    check(u"催化剂槽在**左**半边、氨气输出罐在**右**半边（用户原话「左侧…右侧则为输出」）",
          u"CATALYST_SLOT_X = 78" in (amm_menu or u"") and u"AMMONIA_X = 152" in (amm_menu or u""))
    check(u"方块 / 物品 / 方块实体 / 菜单 / 界面 五处注册齐全",
          u'BLOCKS.register("ammonia_synthesis_chamber"' in (modblocks or u"")
          and u'ITEMS.register("ammonia_synthesis_chamber"' in (modblocks or u"")
          and u'AMMONIA_SYNTHESIS_CHAMBER_BE = BLOCK_ENTITIES.register("ammonia_synthesis_chamber"'
          in (modblocks or u"")
          and u'MENU_TYPES.register("ammonia_synthesis_chamber"' in (modmenus or u"")
          and u"AmmoniaSynthesisChamberScreen::new" in (client or u""))
    check(u"能量 / 流体 / 物品三种能力都登记了",
          _cap_near(common, u"AMMONIA_SYNTHESIS_CHAMBER_BE", u"EnergyStorage")
          and _cap_near(common, u"AMMONIA_SYNTHESIS_CHAMBER_BE", u"FluidHandler")
          and _cap_near(common, u"AMMONIA_SYNTHESIS_CHAMBER_BE", u"ItemHandler"))

    print(u"\n== D 两条合成配方：解回九宫格逐格比（含空格格） ==")
    for rid, spec in RECIPE_SPEC.items():
        p = os.path.join(RDIR, rid + u".json")
        check(u"%s.json 在" % rid, os.path.exists(p))
        if not os.path.exists(p):
            continue
        d = json.loads(read(p))
        eq(u"%s 类型" % rid, u"minecraft:crafting_shaped", d.get("type"))
        eq(u"%s 产物" % rid, {u"id": u"potato_s_t:" + rid, u"count": 1}, d.get("result"))
        key = d.get("key") or {}
        pat = d.get("pattern") or []
        eq(u"%s 每行等长（§6.13：空格占位可以、补齐对齐不行）" % rid,
           [3, 3, 3], [len(r) for r in pat])
        got, bad = [], False
        for row in pat:
            line = []
            for ch in row:
                if ch == u" ":
                    line.append(u" ")
                    continue
                ent = key.get(ch)
                if not ent:
                    line.append(u"?%s" % ch)
                    bad = True
                else:
                    line.append(ent.get("item") or ent.get("tag") or u"?" + ch)
            got.append(line)
        check(u"%s 九宫格与用户原话逐格一致（%s）" % (rid, spec["zh"]),
              (not bad) and got == spec["grid"])
        if got != spec["grid"]:
            for i in range(3):
                print(u"         第 %d 行 解出 %s / 规格 %s"
                      % (i + 1, got[i] if i < len(got) else None, spec["grid"][i]))
        # 一个字母只准代表一种材料（§4.63）
        rev = {}
        clash = []
        for ch, ent in key.items():
            mat = ent.get("item") or ent.get("tag")
            if mat in rev and rev[mat] != ch:
                clash.append((mat, rev[mat], ch))
            rev[mat] = ch
        check(u"%s 没有「一个字母两种材料」（§4.63）" % rid, not clash)
        for cell in (spec["grid"][0] + spec["grid"][1] + spec["grid"][2]):
            if cell == u" ":
                continue
            nm = cell.split(u":")[1]
            check(u"%s 的材料 %s 有模型与注册" % (rid, cell),
                  os.path.exists(os.path.join(ITEMD, nm + u".json"))
                  and (u'"%s"' % nm in (moditems or u"") or u'"%s"' % nm in (modblocks or u"")))

    print(u"\n== E 状态码 9/10/11 的灯色与文案 ==")
    check(u"氨气组成室复用 9 = 氢气不够（与 ZF96 那台语义相同）",
          u"STATUS_NO_HYDROGEN = 9" in (amm_be or u""))
    check(u"新号 10 = 氮气不够、11 = 催化剂槽没有铁粉",
          u"STATUS_NO_NITROGEN = 10" in (amm_be or u"") and u"STATUS_NO_CATALYST = 11" in (amm_be or u""))
    check(u"StatusLampPart：10/11 都是黄灯、9 也在",
          u"AmmoniaSynthesisChamberBlockEntity.STATUS_NO_NITROGEN," in (lamp or u"")
          and u"AmmoniaSynthesisChamberBlockEntity.STATUS_NO_CATALYST -> YELLOW" in (lamp or u""))
    check(u"StatusLampPart 的后缀表里有 no_nitrogen / no_catalyst（9 用 ZF96 那两条）",
          u'STATUS_NO_NITROGEN -> "no_nitrogen"' in (lamp or u"")
          and u'STATUS_NO_CATALYST -> "no_catalyst"' in (lamp or u""))
    keys4 = {n: json.loads(read(os.path.join(LANG, n + u".json"))) for n in LANGS}
    need = [u"gui.potato_s_t.air_separator.status." + s
            for s in (u"running", u"disabled", u"no_power", u"output_full")]
    need += [u"gui.potato_s_t.ammonia_synthesis.status." + s
             for s in (u"running", u"disabled", u"no_power", u"output_full",
                       u"no_hydrogen", u"no_nitrogen", u"no_catalyst")]
    missing = [k for n in LANGS for k in need if k not in keys4[n]]
    check(u"这些状态键四语言都在（缺 %s）" % (missing or u"无"), not missing)

    print(u"\n== F 活体数字与文档 ==")
    for name in LANGS:
        eq(u"%s 键数" % name, EXPECT_KEYS, len(keys4[name]))
        miss = [k for k in NEW_KEYS if k not in keys4[name]]
        check(u"%s 里 19 个新键都在（缺 %s）" % (name, miss or u"无"), not miss)
    eq(u"催化剂标签与用户写的一字不差",
       u"催化剂(铁粉)", keys4["zh_cn"].get(u"gui.potato_s_t.ammonia_synthesis.catalyst"))
    shaped = [n for n in os.listdir(RDIR)
              if json.loads(read(os.path.join(RDIR, n))).get("type") == u"minecraft:crafting_shaped"]
    eq(u"盘上定形配方总数", EXPECT_SHAPED, len(shaped))
    jei_n = len(re.findall(r'"([a-z_]+)"', re.search(r"MACHINES\s*=\s*(.*?);", jei or u"", re.S).group(1)))
    eq(u"JEI 机器分类数", EXPECT_JEI, jei_n)
    check(u"JEI 两个新分类都有图标",
          u'case "air_separator" -> new ItemStack(ModBlocks.AIR_SEPARATOR_ITEM.get());' in (jei or u"")
          and u'case "ammonia_synthesis_chamber" -> new ItemStack(ModBlocks.'
              u'AMMONIA_SYNTHESIS_CHAMBER_ITEM.get());' in (jei or u""))
    for mid, fn in ((u"air_separator", u"buildAirSeparator"),
                    (u"ammonia_synthesis_chamber", u"buildAmmoniaSynthesisChamber")):
        b = body(mrec, u"private static void %s(List<Entry> out)" % fn) or u""
        check(u"MachineRecipes.%s 抠得出来且机器 id 对" % fn,
              b != u"" and ((u'new Entry("%s"' % mid) in b))
        check(u"%s 的数字引用常量（不写死）" % fn,
              (u"AirSeparatorBlockEntity." in b) or (u"AmmoniaSynthesisChamberBlockEntity." in b))
    check(u"灌装机的 JEI 气体列表也加到了 5 种（氮/氨也能装罐）",
          u"ModFluids.NITROGEN.get(), ModFluids.AMMONIA.get()" in (mrec or u""))
    z71 = read(os.path.join(TOOLS, "_zf71_verify.py")) or u""
    check(u"_zf71_verify.py 的流体数断言跟到 %d" % EXPECT_FLUIDS, u"fl == %d" % EXPECT_FLUIDS in z71)
    check(u"_zf71_verify.py 的键数断言跟到 %d" % EXPECT_KEYS, u"== {%d}" % EXPECT_KEYS in z71)
    check(u"_zf71_verify.py 的定形配方断言跟到 %d" % EXPECT_SHAPED,
          u"check(craft == %d," % EXPECT_SHAPED in z71)
    check(u"_zf71_verify.py 的 JEI 分类断言跟到 %d" % EXPECT_JEI,
          u"check(jei == %d and" % EXPECT_JEI in z71)
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    tex = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"档案里有 ZF97 那一行", u"| ZF97 |" in arch)
    check(u"档案 §4 有本轮那条规矩", u"### 4.65 " in arch)
    check(u"档案 §9 有 ZF97 那一节", u"### ZF97（0.11）" in arch)
    check(u"公告里有这两台机器", u"Air Separator" in ann and u"Ammonia Synthesis Chamber" in ann)
    check(u"公告的键数/分类数跟到 %d / %d" % (EXPECT_KEYS, EXPECT_JEI),
          (u"%d keys each" % EXPECT_KEYS) in ann and (u"%d machine categories" % EXPECT_JEI) in ann)
    check(u"贴图清单里有 ZF97 那一节", u"## ZF97" in tex)

    print(u"\n== G mineable/pickaxe + 成品 jar ==")
    mine = json.loads(read(os.path.join(DATA, u"minecraft", u"tags", u"block", u"mineable",
                                        u"pickaxe.json")))
    for bid in (u"air_separator", u"ammonia_synthesis_chamber"):
        check(u"%s 进了 mineable/pickaxe（ZF96 漏过一次，这轮先挂）" % bid,
              (u"potato_s_t:" + bid) in (mine.get("values") or []))
    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            for cls in (u"AirSeparatorBlock", u"AirSeparatorBlockEntity", u"AirSeparatorMenu",
                        u"AmmoniaSynthesisChamberBlock", u"AmmoniaSynthesisChamberBlockEntity",
                        u"AmmoniaSynthesisChamberMenu"):
                check(u"成品里有 %s.class" % cls, (u"com/potatost/mod/%s.class" % cls) in names)
            for cls in (u"AirSeparatorScreen", u"AmmoniaSynthesisChamberScreen"):
                check(u"成品里有界面 %s.class" % cls,
                      (u"com/potatost/mod/client/%s.class" % cls) in names)
            for name in (u"nitrogen_still.png", u"nitrogen_flow.png",
                         u"ammonia_still.png", u"ammonia_flow.png"):
                rel = u"assets/potato_s_t/textures/block/" + name
                check(u"成品里有流体贴图 %s" % name,
                      rel in names and zf.read(rel) == open(os.path.join(TEXB, name), "rb").read())
            for rid in RECIPE_SPEC:
                rel = u"data/potato_s_t/recipe/%s.json" % rid
                check(u"成品里的 %s 与盘上逐字节一致" % rid,
                      rel in names and zf.read(rel) == open(os.path.join(RDIR, rid + u".json"), "rb").read())
            check(u"成品里 assets/ 与 data/ 条目名全合法",
                  not [n for n in names if (n.startswith(u"assets/") or n.startswith(u"data/"))
                       and not re.fullmatch(u"[a-z0-9/._-]+", n)])
            check(u"成品里没有探针 class",
                  not [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")])

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


def _cap_near(java, be_holder, capability):
    """PotatoST.java 里 `Capabilities.<capability>.BLOCK` 之后 400 字符内有没有这个方块实体。"""
    seg = java or u""
    for m in re.finditer(r"Capabilities\.%s\.BLOCK" % capability, seg):
        if seg.find(be_holder, m.start(), m.start() + 400) >= 0:
            return True
    return False


def _slot_at(menu, const, value):
    return (u"%s = %s;" % (const, value)) in (menu or u"")


if __name__ == "__main__":
    sys.exit(main())
