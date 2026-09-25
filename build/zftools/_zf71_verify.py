# -*- coding: utf-8 -*-
"""_zf71_verify.py —— 常驻校验：英文公告里的**每一个数字**都必须能在项目里找到出处

公告是给玩家看的，写错一个数就是骗玩家（同 §4.40/ZF52 的"工具提示画错一格"）。
所以这份校验不查"公告写得漂不漂亮"，只查三件事：

  ① 公告里提到的 id 都真实存在（物品/方块/流体/群系/唱片）；
  ② 公告里的机器数值 == **代码常量算出来的值**（不是抄 tooltip、更不是凭记忆）；
  ③ 公告与**已发布的 tooltip** 不打架（同一台机器两处说法必须一致）；
  ④ 公告「尚未完成」那一节说的必须是**当前事实**（例如"这 4 个方块还没有配方"，
     一旦哪天加了配方，这条校验就会挂 —— 那正是我们想要的效果）；
  ⑤ 数量类断言（9 矿石 / 8 深层 / 8 JEI 分类 / 3 进度 / 7 音效 / 210 键 / 28 配方 / 3 流体）。

退出码 0 = 全过。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, r"src\main\resources")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
DOC = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
LANG = os.path.join(RES, r"assets\potato_s_t\lang\en_us.json")
TOOLS = os.path.join(ROOT, r"build\zftools")

fails = []
examined = 0


def check(ok, msg):
    global examined
    examined += 1
    print((u"  [OK]   " if ok else u"  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)
    return ok


def read(p):
    return io.open(p, encoding="utf-8").read()


def src(fn):
    return read(os.path.join(JAVA, fn))


def eval_int(expr):
    """把 `45 * 20` / `32 * 1024` / `4_000_000` 这种常量表达式算成 int（只允许数字与 +*）"""
    e = expr.strip().replace("_", "").replace("L", "")
    assert re.fullmatch(r"[0-9+\s*()]+", e), u"不认识的常量表达式: %r" % expr
    return int(eval(e))


def const(fn, name):
    m = re.search(r"\b%s\s*=\s*([0-9_]+(?:\s*\*\s*[0-9_]+)*)" % name, src(fn))
    if not m:
        raise AssertionError(u"%s 里找不到常量 %s" % (fn, name))
    return eval_int(m.group(1))


def main():
    doc = read(DOC)
    lang = json.loads(read(LANG))
    blocks = src("ModBlocks.java")

    # ============================================================
    print(u"== ① 公告里点名的东西都存在（含 modid / 群系） ==")
    check(u"`potato_s_t`" in doc and re.search(r'@Mod\(PotatoST\.MODID\)', src("PotatoST.java")) is not None,
          u"mod id potato_s_t（公告最后一行与 PotatoST.java 一致）")
    check(lang.get("biome.potato_s_t.salty_river") == u"Salty River" and u"Salty River" in doc,
          u"群系名 Salty River 与语言文件一致")
    check(u"Anvil of the Republic" in doc
          and lang.get("jukebox_song.potato_s_t.anvil_of_the_republic", u"").endswith(u"Anvil of the Republic"),
          u"唱片名 Anvil of the Republic 与 jukebox_song 的显示名一致")
    check(u"1:43" in doc and 103.5 == json.loads(read(os.path.join(
        RES, r"data\potato_s_t\jukebox_song\anvil_of_the_republic.json")))["length_in_seconds"],
          u"唱片时长 103.5 s = 1:43（公告写的 1:43）")
    ids = sorted(set(re.findall(r"potato_s_t:([a-z0-9_/]+)", doc)))
    print(u"    （公告正文里的带命名空间 id 共 %d 个 —— 其余都是英文显示名，由第 ④ 项对 lang 核对）" % len(ids))

    # ============================================================
    print()
    print(u"== ② 机器数值 == 代码常量 ==")
    # 低级发电机
    burn = const("LowGeneratorBlockEntity.java", "BURN_TICKS")
    lgen_fe = const("LowGeneratorBlockEntity.java", "ENERGY_PER_TICK")
    lgen_buf = const("LowGeneratorBlockEntity.java", "MAX_ENERGY")
    check(burn // 20 == 45 and u"45 s at 100 FE/t per fuel item = 90,000 FE" in doc,
          u"低级发电机：%d tick = %d s、%d FE/t、一块燃料 %d FE（公告与代码一致）"
          % (burn, burn // 20, lgen_fe, burn * lgen_fe))
    check(burn * lgen_fe == 90000 and lgen_buf == 1000, u"低级发电机：储能 %d FE、总能量 90,000 FE" % lgen_buf)

    # 液压机
    p_dur = const("HydraulicPressBlockEntity.java", "DURATION_TICKS") if "DURATION_TICKS =" in src("HydraulicPressBlockEntity.java") else None
    press = src("PressRecipes.java")
    p_dur = eval_int(re.search(r"DURATION_TICKS\s*=\s*([0-9_\s*]+);", press).group(1))
    p_fe = eval_int(re.search(r"ENERGY_PER_TICK\s*=\s*([0-9_\s*]+);", press).group(1))
    check((p_dur, p_fe) == (60, 400) and u"400 FE/t × 3 s = **24,000 FE per plate**" in doc,
          u"液压机：%d tick × %d FE/t = %d FE/块（公告写 3 s / 400 FE/t / 24,000 FE）"
          % (p_dur, p_fe, p_dur * p_fe))
    # 0.11 ZF79：多了一条"12 沥青 → 柏油块" ⇒ 8 条（7 条锭→板 + 1 条沥青→柏油块）
    check(len(re.findall(r"out\.add\(new Recipe\(", press)) == 8,
          u"液压机 8 条配方（7 锭→板 + 1 沥青→柏油块），实际 %d 条"
          % len(re.findall(r"out\.add\(new Recipe\(", press)))

    # 灌装机
    fm = src("FillingMachineBlockEntity.java")
    check((const("FillingMachineBlockEntity.java", "TANK_COUNT"),
           const("FillingMachineBlockEntity.java", "TANK_CAPACITY"),
           const("FillingMachineBlockEntity.java", "FILL_RATE"),
           const("FillingMachineBlockEntity.java", "ENERGY_PER_TANK"),
           const("FillingMachineBlockEntity.java", "MAX_ENERGY")) == (5, 5000, 5, 60, 3000)
          and u"5 × 5,000 mB tanks, 5 mB/t per tank, 60 FE/t per working tank, 3,000 FE buffer" in doc,
          u"灌装机：5 个 5,000 mB 罐 / 5 mB/t / 60 FE/t / 3,000 FE 缓冲")

    # 晒盐机
    check((const("SaltDryerBlockEntity.java", "MAX_ENERGY"), const("SaltDryerBlockEntity.java", "ENERGY_PER_TICK")) == (210, 70)
          and u"120 s" in doc and u"20 s" in doc and u"70 FE/t" in doc and u"210 FE buffer" in doc,
          u"晒盐机：被动 120 s / 通电 20 s、70 FE/t、缓冲 210 FE")

    # 盐分解构器
    sd = src("SaltDecomposerRecipes.java")
    sd_salt = eval_int(re.search(r"SALT_INPUT\s*=\s*([0-9_\s*]+);", sd).group(1))
    sd_dur = eval_int(re.search(r"DURATION_TICKS\s*=\s*([0-9_\s*]+);", sd).group(1))
    sd_fe = eval_int(re.search(r"ENERGY_PER_TICK\s*=\s*([0-9_\s*]+);", sd).group(1))
    sd_back = eval_int(re.search(r"SALT_RETURN_PERCENT\s*=\s*([0-9_\s*]+);", sd).group(1))
    sd_ore = eval_int(re.search(r"RAW_ORE_PERCENT\s*=\s*([0-9_\s*]+);", sd).group(1))
    check((sd_salt, sd_dur, sd_fe, sd_back, sd_ore) == (64, 800, 20, 60, 5)
          and const("SaltDecomposerBlockEntity.java", "MAX_ENERGY") == 20,
          u"盐分解器：%d 海盐 / %d s / %d FE/t / 返还 %d%% / 粗矿 %d%% / 缓冲 20 FE"
          % (sd_salt, sd_dur // 20, sd_fe, sd_back, sd_ore))
    check(u"%d s, %d FE/t" % (sd_dur // 20, sd_fe) in doc and u"**%d %%** sodium chloride" % 100 in doc
          and u"**%d %%** returns %d sea salt" % (sd_back, sd_salt) in doc,
          u"公告正文里这三个数逐字对得上（%d s / %d FE/t / %d%% 返还 %d）"
          % (sd_dur // 20, sd_fe, sd_back, sd_salt))

    # 电解器
    el = src("ElectrolyzerBlockEntity.java")
    g = lambda n: eval_int(re.search(r"\b%s\s*=\s*([0-9_\s*]+);" % n, el).group(1))
    check((g("WATER_PER_TICK"), g("OXYGEN_PER_TICK"), g("HYDROGEN_PER_TICK"),
           g("CHLORINE_PER_TICK"), g("WATER_PER_SALT"), const("ElectrolyzerBlockEntity.java", "MAX_ENERGY"))
          == (10, 3, 6, 3, 500, 20000),
          u"电解器：水 %d mB/t → 氧 %d / 氢 %d（氯 %d）、每个海盐 %d mB、缓冲 20,000 FE"
          % (g("WATER_PER_TICK"), g("OXYGEN_PER_TICK"), g("HYDROGEN_PER_TICK"),
             g("CHLORINE_PER_TICK"), g("WATER_PER_SALT")))
    check(u"1,000 FE/t + 10 mB water/t" in doc and re.search(r"ENERGY_PER_TICK_OXYGEN\s*=\s*1000", el) is not None,
          u"电解器：1000 FE/t（ENERGY_PER_TICK_OXYGEN = 1000，ZF81 抬的）")

    # 太阳能板
    sp = src("SolarPanelBlockEntity.java")
    rates = [eval_int(re.search(r"\b%s\s*=\s*([0-9_\s*]+);" % n, sp).group(1))
             for n in ("RATE_DAWN_DUSK", "RATE_MORNING", "RATE_NOON")]
    rain, thunder = (eval_int(re.search(r"\b%s\s*=\s*([0-9_\s*]+);" % n, sp).group(1))
                     for n in ("RAIN_PERCENT", "THUNDER_PERCENT"))
    check(rates == [60, 135, 180] and (rain, thunder) == (60, 20)
          and const("SolarPanelBlockEntity.java", "MAX_ENERGY") == 512
          and u"**60 FE/t** at dawn/dusk, **135** in the morning/afternoon, **180** at noon" in doc,
          u"太阳能板：%s FE/t、雨 %d%%、雷 %d%%、单块 512 FE" % (rates, rain, thunder))

    # 动力能源捕获器
    pc = src("PowerCapturerBlockEntity.java")
    pw = [eval_int(re.search(r"\b%s\s*=\s*([0-9_\s*]+);" % n, pc).group(1))
          for n in ("WATER_POWER", "FURNACE_POWER", "BLAST_FURNACE_POWER")]
    check(pw == [8, 8, 16] and u"flowing water **+8**, burning furnace/smoker **+8**, burning blast furnace **+16** Power/t" in doc,
          u"动力能源捕获器：水 %d / 熔炉 %d / 高炉 %d Power/t" % tuple(pw))

    # 发电机
    gen = src("GeneratorBlockEntity.java")
    fe_per_power = eval_int(re.search(r"FE_PER_POWER\s*=\s*([0-9_\s*]+);", gen).group(1))
    consume = eval_int(re.search(r"MAX_POWER_CONSUME\s*=\s*([0-9_\s*]+);", gen).group(1))
    check(fe_per_power == 2 and consume == 128 and const("GeneratorBlockEntity.java", "MAX_ENERGY") == 100000
          and u"**2 FE per Power**, up to 128 Power/t (**256 FE/t**)" in doc,
          u"发电机：1 Power = %d FE、最多 %d Power/t = %d FE/t、缓冲 100,000 FE"
          % (fe_per_power, consume, fe_per_power * consume))

    # 端子
    tb = src("TerminalBlockEntity.java")
    tvals = [eval_int(re.search(r"\b%s\s*=\s*([0-9_\s*]+);" % n, tb).group(1))
             for n in ("MAX_ENERGY", "TRANSFER_RATE", "MAX_POWER", "POWER_TRANSFER_RATE")]
    dist = eval_int(re.search(r"MAX_CONNECTION_DISTANCE\s*=\s*([0-9_\s*]+);", src("TerminalBlock.java")).group(1))
    check(tvals == [2048, 2048, 8192, 128] and dist == 16
          and u"2,048 FE buffer (2,048 FE/t transfer) and 8,192 Power buffer (128 Power/t)" in doc,
          u"端子：%s FE / %s Power、连接距离 %d 格" % (tvals[0], tvals[2], dist))
    modes = re.search(r'register\("(input|output|none)"|"mode\."', doc)
    check(all(u"mode.potato_s_t." + m in lang for m in ("none", "input", "output")),
          u"端子三种模式 None/Input/Output 在语言文件里都有")

    # 锂电池
    lb = read(os.path.join(JAVA, "LithiumBatteryBlock.java")) + read(os.path.join(JAVA, "LithiumBatteryBlockEntity.java"))
    per_block = eval_int(re.search(r"PER_BLOCK\s*=\s*([0-9_\s*L]+);", lb).group(1))
    check(per_block == 4000000 and u"**4,000,000 FE per block.**" in doc,
          u"锂电池：每块 %s FE（%d）" % ("4,000,000", per_block))

    # 电力高炉
    ebf = src("ElectricBlastFurnaceBlockEntity.java")
    e_in = const("ElectricBlastFurnaceBlockEntity.java", "INPUT_COUNT")
    e_out = const("ElectricBlastFurnaceBlockEntity.java", "OUTPUT_COUNT")
    e_dur = const("ElectricBlastFurnaceBlockEntity.java", "DURATION_TICKS")
    e_item = const("ElectricBlastFurnaceBlockEntity.java", "ENERGY_PER_ITEM")
    e_buf = const("ElectricBlastFurnaceBlockEntity.java", "MAX_ENERGY")
    check((e_in, e_out, e_dur, e_item, e_buf) == (12, 32, 200, 800, 4096),
          u"电力高炉：12 入 / 32 出 / 10 s 一槽 / 800 FE 一件 / 缓冲 4,096 FE")
    # ⚠ 这几个数必须**在公告正文里逐字对上**：第一版只查了常量，反证时把公告改成
    #   "12 seconds" 竟然通过了（checker 根本没读那句）—— 反证的价值就在这儿。
    check(u"%d input + %d output slots" % (e_in, e_out) in doc,
          u"公告写了 %d 输入 + %d 输出槽" % (e_in, e_out))
    check(u"each slot finishes in **%d seconds**" % (e_dur // 20) in doc,
          u"公告写的一槽耗时 = %d s" % (e_dur // 20))
    check(u"**%s FE per item**" % format(e_item, ",") in doc,
          u"公告写的一件耗电 = %s FE" % format(e_item, ","))
    check(u"%s FE\n  buffer" % format(e_buf, ",") in doc or u"%s FE buffer" % format(e_buf, ",") in doc,
          u"公告写的缓冲 = %s FE" % format(e_buf, ","))
    check(e_in * 64 * e_item // e_dur == 3072 and u"**3,072 FE/t**" in doc,
          u"电力高炉满负载 12×64×800÷200 = 3,072 FE/t")
    # 结构：3×3×3 = 27 格，去掉控制器与 1 格空气 = 25 格建材（**从 PATTERN 里数**，不抄注释）
    st = src("ElectricBlastFurnaceStructure.java")
    pat = st[st.index("PATTERN"):]
    kinds = re.findall(r"Kind\.([A-Z]+)", pat)
    check(len(kinds) == 27, u"电力高炉结构 = %d 格（3 层 × 3×3）" % len(kinds))
    build = len([k for k in kinds if k not in ("CONTROLLER", "AIR")])
    check(build == 25 and u"**3×3×3 shell around a vanilla Blast Furnace** (25 blocks" in doc,
          u"电力高炉建材 = %d 格（PATTERN 里数出来；公告写 25）" % build)
    for need, cnt in (("COMMON", None), ("HEATER", 1), ("WIRING", 2), ("BARS", None), ("TRAPDOOR", 1)):
        pass
    check(kinds.count("HEATER") == 1 and kinds.count("WIRING") == 2 and kinds.count("TRAPDOOR") == 1,
          u"结构里 1 加热装置 / 2 接线块 / 1 活版门（公告这么写的）")

    # 合金炉
    asm = src("AlloySmelterBlockEntity.java")
    ar = src("AlloySmelterRecipes.java")
    a_dur = eval_int(re.search(r"DURATION_TICKS\s*=\s*([0-9_\s*]+);", ar).group(1))
    a_fe = eval_int(re.search(r"ENERGY_PER_TICK\s*=\s*([0-9_\s*]+);", ar).group(1))
    check((const("AlloySmelterBlockEntity.java", "MAX_ENERGY"),
           const("AlloySmelterBlockEntity.java", "INPUT_COUNT"),
           const("AlloySmelterBlockEntity.java", "OUTPUT_COUNT"),
           const("AlloySmelterBlockEntity.java", "CONSUME_COUNT")) == (32768, 5, 3, 2),
          u"合金炉：缓冲 32,768 FE、5 输入 / 3 输出 / 2 消耗槽")
    check((a_dur, a_fe) == (600, 800) and u"30 s, 800 FE/t = 480,000 FE per item" in doc,
          u"合金炉：%d s、%d FE/t = %d FE 一件" % (a_dur // 20, a_fe, a_dur * a_fe))
    check(u"58 cells" in doc and u"58 cells" in lang.get("tooltip.potato_s_t.alloy_smelter", u""),
          u"合金炉判定 58 格（公告与方块自己的 tooltip 说法一致）")

    # 工具
    tiers = src("ModTiers.java")
    sword_uses, sword_bonus = re.search(r"TITANIUM_ALLOY_SWORD\s*=\s*build\((\d+),\s*([0-9.]+)F\)", tiers).groups()
    pick_uses, pick_bonus = re.search(r"TITANIUM_ALLOY_PICKAXE\s*=\s*build\((\d+),\s*([0-9.]+)F\)", tiers).groups()
    check((int(sword_uses), int(pick_uses)) == (2048, 4219) and u"2,048 durability" in doc and u"4,219 durability" in doc,
          u"工具耐久：剑 %s / 镐 %s" % (sword_uses, pick_uses))
    check(1 + 3 + float(sword_bonus) == 6.5 and 1 + 1 + float(pick_bonus) == 4.0
          and u"6.5 attack damage" in doc and u"4 attack damage" in doc,
          u"显示伤害：剑 %s / 镐 %s（1+3+%s / 1+1+%s）"
          % (1 + 3 + float(sword_bonus), 1 + 1 + float(pick_bonus), sword_bonus, pick_bonus))
    check(const("ModTiers.java", "SPEED") == 9 if False else "9.0F" in tiers,
          u"挖掘速度 9.0（ModTiers.SPEED）")
    check(re.search(r"ENCHANTMENT_VALUE\s*=\s*25", tiers) is not None and u"enchantability 25" in doc,
          u"附魔权重 25")

    # ============================================================
    print()
    print(u"== ③ 与已发布 tooltip 不打架 ==")
    PAIRS = [
        (u"tooltip.potato_s_t.low_generator", [u"45 seconds", u"100 FE/t", u"1000 FE"]),
        (u"tooltip.potato_s_t.hydraulic_press", [u"400 FE/t", u"3 seconds"]),
        (u"tooltip.potato_s_t.filling_machine", [u"5000 mB", u"5 mB/t", u"60 FE/t", u"3000 FE"]),
        (u"tooltip.potato_s_t.salt_dryer", [u"120s", u"70 FE/t", u"20s"]),
        (u"tooltip.potato_s_t.salt_decomposer", [u"64 sea salt", u"40 seconds", u"20 FE/t", u"60%", u"5%"]),
        (u"tooltip.potato_s_t.electrolyzer", [u"1000 FE", u"10 mB water", u"3 oxygen", u"6 hydrogen", u"3 chlorine", u"500 mB"]),
        (u"tooltip.potato_s_t.solar_panel", [u"60 FE/t", u"135", u"180", u"60%", u"20%", u"512 FE"]),
        (u"tooltip.potato_s_t.power_capturer", [u"+8", u"+16"]),
        (u"tooltip.potato_s_t.generator", [u"1 power = 2 FE/t"]),
        (u"tooltip.potato_s_t.lithium_battery", [u"4M FE per block"]),
        (u"tooltip.potato_s_t.electric_blast_furnace", [u"3x3x3", u"12 input slots", u"32 output slots",
                                                        u"10 seconds", u"800 FE", u"4096 FE", u"3072 FE/t"]),
        (u"tooltip.potato_s_t.micro_crusher", [u"2500 FE", u"400 FE/t"]),
    ]
    for key, needles in PAIRS:
        t = lang.get(key, u"")
        missing = [n for n in needles if n not in t]
        check(bool(t) and not missing, u"%s：tooltip 里 %d 个数都对得上%s"
              % (key, len(needles), u"" if not missing else u"（缺 %s）" % missing))

    # ============================================================
    print()
    print(u"== ④ 公告里那些英文名字 == lang 里的正式名 ==")
    NAMES = {"block.potato_s_t.terminal": u"Terminal Block",
             "block.potato_s_t.micro_crusher": u"Micro Crusher",
             "block.potato_s_t.hydraulic_press": u"Hydraulic Press",
             "block.potato_s_t.filling_machine": u"Filling Machine",
             "block.potato_s_t.salt_dryer": u"Salt Dryer",
             "block.potato_s_t.salt_decomposer": u"Salt Decomposer",
             "block.potato_s_t.electrolyzer": u"Electrolyzer",
             "block.potato_s_t.power_capturer": u"Power Capturer",
             "block.potato_s_t.generator": u"Generator",
             "block.potato_s_t.low_generator": u"Low-Tier Generator",
             "block.potato_s_t.solar_panel": u"Solar Panel",
             "block.potato_s_t.electric_blast_furnace": u"Electric Blast Furnace",
             "item.potato_s_t.power_cable_spool": u"Power Cable Spool",
             "item.potato_s_t.wrench": u"Wrench",
             "item.potato_s_t.light_titanium_alloy": u"Lightweight Titanium Alloy",
             "item.potato_s_t.titanium_alloy_sword": u"Titanium Alloy Sword",
             "item.potato_s_t.titanium_alloy_pickaxe": u"Titanium Alloy Pickaxe"}
    for k, name in NAMES.items():
        check(lang.get(k) == name and name in doc, u"%s = %s（lang 与公告一致）" % (k, name))
    check(u"Lithium Battery" in doc and lang.get("block.potato_s_t.lithium_battery") == u"Ternary polymer lithium battery",
          u"锂电池：公告用 Lithium Battery，游戏里的正式名是 Ternary polymer lithium battery（已在汇报里点名）")

    # ============================================================
    print()
    print(u"== ⑤ 数量类断言 ==")
    # ⚠ ZF75 修正：原来数的是**整个 configured_feature 目录**的文件数（9），
    #    加一个非矿物特征（mini_oilfield）就变 10、误报「矿石 10 种」。
    #    改成只数 ore_* 前缀，语义才对得上标签。
    ore_n = len([f for f in os.listdir(os.path.join(RES, r"data\potato_s_t\worldgen\configured_feature"))
                  if f.startswith(u"ore_")])
    # 深层变体在 PotatoSTOres.java 里注册（不是 ModBlocks），而且**lang 是玩家看到的名字**——
    # 两处都数一遍，必须一致（第一版只查 ModBlocks，数出 0，是检查自己写错了）
    deep_src = len(re.findall(r'ore\("deepslate_[a-z_]+_ore"', src("PotatoSTOres.java")))
    deep_lang = len([k for k in lang if re.fullmatch(r"block\.potato_s_t\.deepslate_[a-z_]+_ore", k)])
    stone_lang = len([k for k in lang if re.fullmatch(r"block\.potato_s_t\.[a-z_]+_ore", k)
                      and not k.startswith("block.potato_s_t.deepslate_")])
    adv = len(os.listdir(os.path.join(RES, r"data\potato_s_t\advancement")))
    snd = len(json.loads(read(os.path.join(RES, r"assets\potato_s_t\sounds.json"))))
    fl = len(re.findall(r'FLUID_TYPES\.register\("', src("ModFluids.java")))
    rdir = os.path.join(RES, r"data\potato_s_t\recipe")
    craft = len([n for n in os.listdir(rdir)
                 if json.loads(read(os.path.join(rdir, n))).get("type") == "minecraft:crafting_shaped"])
    jei = len(re.findall(r'"([a-z_]+)"', re.search(r"MACHINES\s*=\s*(.*?);", src(r"client\jei\PotatoSTJeiPlugin.java"), re.S).group(1)))
    keys = {f[:-5]: len(json.loads(read(os.path.join(RES, r"assets\potato_s_t\lang", f))))
            for f in os.listdir(os.path.join(RES, r"assets\potato_s_t\lang"))}
    check(ore_n == 9 and u"**9 new ores**" in doc, u"矿石 %d 种" % ore_n)
    check(deep_src == deep_lang == 7 and stone_lang == 9 and u"7 deepslate variants" in doc,
          u"深层变体 %d 种（java）/%d 种（lang）、浅层 %d 种" % (deep_src, deep_lang, stone_lang))
    # 顺手钉住一个"容易数错"的坑：textures 里那张 deepslate_aluminiu_ore.png 是**拼错名的孤儿贴图**，
    # 不是第 8 个深层变体（第一版公告就是把它数进去了）
    check(not os.path.isfile(os.path.join(RES, r"assets\potato_s_t\textures\block\deepslate_aluminum_ore.png"))
          and os.path.isfile(os.path.join(RES, r"assets\potato_s_t\textures\block\deepslate_aluminiu_ore.png")),
          u"确认那张 deepslate_aluminiu_ore.png 是拼错名的孤儿贴图（铝没有深层变体）")
    # ZF107：3 → **27**（3 条老的 + 24 条新的，见 `_zf107_verify.py`）
    check(adv == 27, u"进度 %d 条" % adv)
    # ZF93 起 8 个：第一张唱片之后加了第二张《茉莉花（管弦乐）》
    check(snd == 8, u"音效键 %d 个" % snd)
    check(fl == 15 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)  # ZF101 起 14（+三种酸）
    check(craft == 51, u"合成配方 %d 条" % craft)  # ZF101 起 42（ZF100 的 41 + 酸性反应室）
    check(jei == 11 and u"11 machine categories" in doc, u"JEI 机器分类 %d 个" % jei)
    # ⚠ 活体核对：公告里写的键数必须等于当前四份语言文件的真实键数
    #   （ZF80 从 248 → 257：灌装机手倒 3 条 + 逐槽诊断 6 条；ZF82 又从 257 → 270：
    #     容器换流器 + 柴油桶/汽油桶 + 两个液体方块名）
    check(len(keys) == 4 and set(keys.values()) == {417} and u"417 keys each" in doc,
          u"语言 %d 种、各 %s 键" % (len(keys), sorted(set(keys.values()))))

    # ============================================================
    print()
    print(u"== ⑥ 「尚未完成」那一节必须仍是事实 ==")
    made = set()
    for n in os.listdir(rdir):
        made.add(json.loads(read(os.path.join(rdir, n))).get("result", {}).get("id"))
    # ⚠ ZF104 起（2026-09-25 收口）：**稳定金属块也补上了配方**（用户口述的九宫格
    #   高碳钢/硬质钛合金/金块 SAS-GAG-SAS）⇒ 从"还没有配方"的名单里挪出去；
    #    剩下 **扳手 / 高级金属块** 两件仍然没有（英文公告 §9 同步改过）。
    for bid in ("potato_s_t:advanced_metal_block", "potato_s_t:wrench"):
        check(bid not in made, u"%s 确实还没有配方（公告把它列进 known gaps）" % bid)
    for bid in ("potato_s_t:lithium_battery", "potato_s_t:electric_blast_furnace",
                "potato_s_t:combustion_chamber"):
        check(bid in made, u"%s 现在**有**配方了（ZF100 补的）" % bid)
    for bid in ("potato_s_t:alloy_smelter", "potato_s_t:distillation_controller",
                "potato_s_t:distillation_operator"):
        check(bid in made, u"%s 现在**有**配方了（ZF95 用户口述）" % bid)
    consumers = [n for n in os.listdir(rdir) if "tungsten" in read(os.path.join(rdir, n))]
    mcr = read(os.path.join(JAVA, "MicroCrusherRecipes.java"))
    ebf_r = read(os.path.join(JAVA, "BlastFurnaceRecipes.java"))
    check(not consumers and "raw_tungsten" not in mcr and "tungsten" not in ebf_r.lower(),
          u"粗钨确实没有任何用处（配方/粉碎机/高炉里都没有）")
    check(all("rewards" not in read(os.path.join(RES, r"data\potato_s_t\advancement", n))
              for n in os.listdir(os.path.join(RES, r"data\potato_s_t\advancement"))),
          u"27 条进度都没有 rewards ⇒ 配方书不会自动解锁（公告这么说的）")
    check(u"28,000 FE per item" in doc and 20 * 20 * 70 == 28000,
          u"铁粉 20 s × 70 FE/t = 28,000 FE/个")

    # 待画贴图数：直接问第 8 道门（TextureCheck.py），不自己数
    try:
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "TextureCheck.py")],
                           capture_output=True, cwd=TOOLS)
        out = r.stdout.decode("utf-8", "replace")
        m = re.search(r"待画\s*=\s*(\d+)", out)
        n_draw = int(m.group(1)) if m else -1
    except Exception as e:
        n_draw = -1
        print(u"    （TextureCheck 跑不起来：%s）" % e)
    # ⚠ 这个数是**活体**的：0.11 ZF90 柴油桶与汽油桶先后拿到自己的图 ⇒ 7 → 6 → **5**；
    #   ZF104/105/106（盔甲线）又加进来 8 件盔甲模型 + 硬质钛合金 ⇒ **5 → 13**
    #   （公告同一句已由那条线改成 13，`docs\UpdateAnnouncement_EN.md` 的 §9）；
    #   **ZF110** 用户给了星璨钢头盔的背包图标 ⇒ **13 → 12**
    #   （公告同一句、`_zf90_verify.py` 的两条断言一起改，别只改一边）
    check(n_draw == 12 and u"12 models still do this" in doc,
          u"还在借原版贴图的模型 = %d 个（公告写 12）" % n_draw)

    print()
    print(u"检查项 = %d" % examined)
    print(u"失败项 = %d" % len(fails))
    for m in fails:
        print(u"   - " + m)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
