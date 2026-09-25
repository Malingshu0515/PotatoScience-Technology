# -*- coding: utf-8 -*-
"""_zf45_recipes.py —— 合成配方表的生成 + 自检（ZF45 起，表里现在 30 条）

表的来源（每条都是用户给的图纸/口述，逐条追加）：
  ZF45：14 条（微型粉碎机 … 铜线）
  ZF47：+1 条（耐热金属块）
  ZF69：+1 条（散热装置 —— 加热装置围一圈青金石）
  ZF73：+1 条（油桶 —— 铜锭/铁桶/铜锭 + 钢板/铁桶/钢板 + 铁板/铝锭/铁板，吃 2 个铁桶出 1 个）
  ZF106：+8 条（两套盔甲 —— 图纸逐格照抄原版铁套，材料换成轻质钛合金 / 星璨钢锭）
⇒ 本表是这 30 份 JSON 的**唯一来源**，改配方改这里再 `--write`，
  顺手拿到「id 真实存在 / 每格字符都在 key 里 / key 无冗余」的机械核对，
  以及可复现性（重跑后别的文件哈希一字不变）。

用户这一批给的是**一张 3×3 的图纸文字**（【】= 一格），这里先把图纸抄成
{pattern, key, result}，再生成 JSON。抄一遍的用处是：脚本能机械地核对
"每格字符都在 key 里 / key 没有多余字符 / 行列数一致 / 物品 id 真实存在"，
而这些正是**摆上去才发现做不出来**的那类错（RecipeCheck 的注释里写的同一个坑）。

id 存在性怎么查（不依赖游戏）：
  · `potato_s_t:` → 在 ModItems.java / ModBlocks.java 里 grep `register("<id>"`；
  · `minecraft:`   → 在 client.jar 里找 `assets/minecraft/models/item/<id>.json`
                     （原版每个物品都有模型，所以"找不到模型"= id 打错了）。

跑法：
    python build/zftools/_zf45_recipes.py --check     # 只校验，不写
    python build/zftools/_zf45_recipes.py --write
"""
import argparse
import collections
import io
import json
import os
import re
import sys
import zipfile

PROJ = r"E:\PotatoST"
OUT = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t", "recipe")
JAVA = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

# ============================================================
#  图纸（照用户原文抄）
#  顺序 = 用户给的顺序
# ============================================================
RECIPES = [
    # 【铜锭】【红石粉】【铜锭】 / 【】【铁块】【】 / 【】【切石机】【】 → 微型粉碎机
    dict(name="micro_crusher", category="misc", result=("potato_s_t:micro_crusher", 1),
         pattern=["CRC", " I ", " S "],
         key={"C": ("tag", "c:ingots/copper"), "R": ("item", "minecraft:redstone"),
              "I": ("item", "minecraft:iron_block"), "S": ("item", "minecraft:stonecutter")}),

    # 【红石粉】【铜锭】【红石粉】 / 【水桶】【一般金属块】【水桶】 / 【铁粒】【铜锭】【铁粒】 → 液压机
    dict(name="hydraulic_press", category="misc", result=("potato_s_t:hydraulic_press", 1),
         pattern=["RCR", "WMW", "NCN"],
         key={"R": ("item", "minecraft:redstone"), "C": ("tag", "c:ingots/copper"),
              "W": ("item", "minecraft:water_bucket"), "M": ("item", "potato_s_t:common_metal_block"),
              "N": ("item", "minecraft:iron_nugget")}),

    # 【一般金属块】【高压气罐】【一般金属块】 / 【高压气罐】【银锭】【高压气罐】 /
    # 【高压气罐】【铜板】【高压气罐】 → 灌装机
    dict(name="filling_machine", category="misc", result=("potato_s_t:filling_machine", 1),
         pattern=["MTM", "TST", "TCT"],
         key={"M": ("item", "potato_s_t:common_metal_block"),
              "T": ("item", "potato_s_t:high_pressure_tank"),
              "S": ("tag", "c:ingots/silver"), "C": ("item", "potato_s_t:copper_plate")}),

    # 【高碳钢】【线】【高碳钢】 / 【铁锭】【银板】【铁锭】 / 【铁锭】【】【铁锭】 → 晒盐机
    # （第三行中间是**空槽**：pattern 里就是一个空格）
    dict(name="salt_dryer", category="misc", result=("potato_s_t:salt_dryer", 1),
         pattern=["SGS", "IPI", "I I"],
         key={"S": ("item", "potato_s_t:high_carbon_steel"), "G": ("item", "minecraft:string"),
              "I": ("tag", "c:ingots/iron"), "P": ("item", "potato_s_t:silver_plate")}),

    # 【铁板】【高碳钢】【铁板】 / 【磁铁】【铜线轴】【磁铁】 / 【铁板】【铜线轴】【铁板】 → 发电机
    dict(name="generator", category="redstone", result=("potato_s_t:generator", 1),
         pattern=["PSP", "MCM", "PCP"],
         key={"P": ("item", "potato_s_t:iron_plate"), "S": ("item", "potato_s_t:high_carbon_steel"),
              "M": ("item", "potato_s_t:magnet"), "C": ("item", "potato_s_t:copper_wire_spool")}),

    # 一圈铁板 → 16 个流体管道
    dict(name="fluid_pipe", category="misc", result=("potato_s_t:fluid_pipe", 16),
         pattern=["PPP", "P P", "PPP"],
         key={"P": ("item", "potato_s_t:iron_plate")}),

    # 【流体管道】 / 【发电机】 / 【电容】 → 流体泵
    dict(name="fluid_pump", category="misc", result=("potato_s_t:fluid_pump", 1),
         pattern=["P", "G", "C"],
         key={"P": ("item", "potato_s_t:fluid_pipe"), "G": ("item", "potato_s_t:generator"),
              "C": ("item", "potato_s_t:capacitor")}),

    # 【一般金属块】【海盐】【一般金属块】 / 【钴板】【镍板】【钴板】 /
    # 【一般金属块】【铜板】【一般金属块】 → 盐分解构器
    dict(name="salt_decomposer", category="misc", result=("potato_s_t:salt_decomposer", 1),
         pattern=["MSM", "KNK", "MCM"],
         key={"M": ("item", "potato_s_t:common_metal_block"), "S": ("item", "potato_s_t:sea_salt"),
              "K": ("item", "potato_s_t:cobalt_plate"), "N": ("item", "potato_s_t:nickel_plate"),
              "C": ("item", "potato_s_t:copper_plate")}),

    # 【玻璃板】×3 / 【硅】×3 / 【铝板】【银锭】【铝板】 → 光伏原件
    dict(name="photovoltaic_component", category="misc", result=("potato_s_t:photovoltaic_component", 1),
         pattern=["GGG", "QQQ", "ASA"],
         key={"G": ("item", "minecraft:glass_pane"), "Q": ("item", "potato_s_t:silicon"),
              "A": ("item", "potato_s_t:aluminum_plate"), "S": ("tag", "c:ingots/silver")}),

    # 【光伏原件】【电容】【光伏原件】 / 【铁板】×3 → 太阳能板
    dict(name="solar_panel", category="redstone", result=("potato_s_t:solar_panel", 1),
         pattern=["PCP", "III"],
         key={"P": ("item", "potato_s_t:photovoltaic_component"),
              "C": ("item", "potato_s_t:capacitor"), "I": ("item", "potato_s_t:iron_plate")}),

    # 【银锭】×3 / 【铜板】×3 / 【银锭】×3 → 热力金属
    dict(name="thermal_metal", category="misc", result=("potato_s_t:thermal_metal", 1),
         pattern=["SSS", "CCC", "SSS"],
         key={"S": ("tag", "c:ingots/silver"), "C": ("item", "potato_s_t:copper_plate")}),

    # 【铁锭】【热力金属】【铁锭】 / 【一般金属块】【热力金属】【一般金属块】 /
    # 【铁锭】【热力金属】【铁锭】 → 加热装置（既有装饰方块，本批才给它配方）
    dict(name="heater", category="misc", result=("potato_s_t:heater", 1),
         pattern=["ITI", "MTM", "ITI"],
         key={"I": ("tag", "c:ingots/iron"), "T": ("item", "potato_s_t:thermal_metal"),
              "M": ("item", "potato_s_t:common_metal_block")}),

    # 中间一列铁 → 1 个空线轴
    dict(name="empty_spool", category="misc", result=("potato_s_t:empty_spool", 1),
         pattern=[" I ", " I ", " I "],
         key={"I": ("tag", "c:ingots/iron")}),

    # 【铜锭】【铜锭】 → 4 个铜线
    dict(name="copper_wire", category="redstone", result=("potato_s_t:copper_wire", 4),
         pattern=["CC"],
         key={"C": ("tag", "c:ingots/copper")}),

    # ===== ZF47 追加（用户口述，还是走本脚本 ⇒ 照样享受"id 存在性"机械核对）=====
    # 【铁板】【高碳钢】【铁板】 / 【热力金属】【一般金属块】【热力金属】 /
    # 【铁板】【高碳钢】【铁板】 → 耐热金属块（ZF34 就注册了，一直没配方）
    dict(name="heat_resistant_metal_block", category="misc",
         result=("potato_s_t:heat_resistant_metal_block", 1),
         pattern=["PSP", "TMT", "PSP"],
         key={"P": ("item", "potato_s_t:iron_plate"), "S": ("item", "potato_s_t:high_carbon_steel"),
              "T": ("item", "potato_s_t:thermal_metal"),
              "M": ("item", "potato_s_t:common_metal_block")}),

    # ===== ZF69 追加（用户口述：加热装置围一圈青金石）=====
    # 【青金石】×3 / 【青金石】【加热装置】【青金石】 / 【青金石】×3 → 散热装置
    # （ZF34 就注册了、一直没有配方；本批补上 ⇒ 装饰方块里没配方的从 3 个减到 2 个）
    dict(name="heat_sink", category="misc", result=("potato_s_t:heat_sink", 1),
         pattern=["LLL", "LHL", "LLL"],
         key={"L": ("item", "minecraft:lapis_lazuli"), "H": ("item", "potato_s_t:heater")}),

    # ===== ZF73 追加（0.11 石油线第一批；用户 2026-09-24 给的图纸）=====
    # 【铜锭】【铁桶】【铜锭】 / 【钢板】【铁桶】【钢板】 / 【铁板】【铝锭】【铁板】 → 油桶
    # 用户拍板：「配方吃两个」⇒ 吃 2 个原版铁桶、**产出 1 个**油桶。
    # 铜锭按本工程长期规则走 c: 标签（跨 mod 兼容），铁桶/铝锭/铁板/钢板都是确指物品。
    dict(name="oil_bucket", category="misc", result=("potato_s_t:oil_bucket", 1),
         pattern=["CBC", "SBS", "IAI"],
         key={"C": ("tag", "c:ingots/copper"), "B": ("item", "minecraft:bucket"),
              "S": ("item", "potato_s_t:steel_plate"), "I": ("item", "potato_s_t:iron_plate"),
              "A": ("item", "potato_s_t:aluminum_ingot")}),

    # ===== ZF100 追加（用户：「前面那几个没配方的机器你看着加吧 可以略微难一点 参考别的」）=====
    # 用户随后**收窄了范围**：「停停停只要刚才那两个机器的配方」⇒ 只做**两台机器**：
    #   ① 三元聚合物锂电池（ZF02 起就没配方）
    #   ② 电力高炉主控（ZF39 起就没配方）
    # 扳手（工具）、高级金属块 / 稳定金属块（装饰方块）那三条**撤掉**（2026-09-25 当天撤回）。
    # 图纸由我按现有配方的手感与价位定；每件都只给**一条**配方，产物 id 与材料 id 由本脚本机械核对。
    #
    # ① 三元聚合物锂电池：四角铝板 / 两侧铜板 / 中心电容 + 碳酸锂 + 外壳
    dict(name="lithium_battery", category="redstone",
         result=("potato_s_t:lithium_battery", 1),
         pattern=["ACA", "PLP", "AMA"],
         key={"A": ("item", "potato_s_t:aluminum_plate"),
              "C": ("item", "potato_s_t:capacitor"),
              "P": ("item", "potato_s_t:copper_plate"),
              "L": ("item", "potato_s_t:lithium_carbonate"),
              "M": ("item", "potato_s_t:common_metal_block")}),

    # ② 电力高炉控制器：中心=**原版高炉**（它就是"升级过的炉子"），
    #    两翼接线块、上下加热装置、四角铁板、底下一颗电容
    #    ⚠ 材料里**不许**出现钢板/高碳钢/磁铁/钛锭 —— 那些只有电力高炉做得出来（死锁）
    dict(name="electric_blast_furnace", category="misc",
         result=("potato_s_t:electric_blast_furnace", 1),
         pattern=["PHP", "WCW", "PAP"],
         key={"P": ("item", "potato_s_t:iron_plate"),
              "H": ("item", "potato_s_t:heater"),
              "W": ("item", "potato_s_t:wiring_block"),
              "C": ("item", "minecraft:blast_furnace"),
              "A": ("item", "potato_s_t:capacitor")}),

    # ③ 燃烧反应室（用户原话给的图纸）：【】【高压气罐】【】 /
    #    【散热装置】【铁板】【耐热金属块】 / 【电容】【加热装置】【打火石】
    dict(name="combustion_chamber", category="misc",
         result=("potato_s_t:combustion_chamber", 1),
         pattern=[" T ", "HPK", "CAF"],
         key={"T": ("item", "potato_s_t:high_pressure_tank"),
              "H": ("item", "potato_s_t:heat_sink"),
              "P": ("item", "potato_s_t:iron_plate"),
              "K": ("item", "potato_s_t:heat_resistant_metal_block"),
              "C": ("item", "potato_s_t:capacitor"),
              "A": ("item", "potato_s_t:heater"),
              "F": ("item", "minecraft:flint_and_steel")}),

    # ④ 酸性反应室（用户原话给的图纸）：【铜块】【稳定金属块】【加热装置】 /
    #    【钛锭】【灌装机】【钛锭】 / 【红石火把】【电解器】【拉杆】
    #    ⚠ 稳定金属块**自己没有配方**（ZF100 那轮用户说"只要那两个机器的配方"）⇒ 这台机器
    #      在生存里暂时做不出来，已挂进档案 §9 的待办
    dict(name="acidic_reaction_chamber", category="misc",
         result=("potato_s_t:acidic_reaction_chamber", 1),
         pattern=["CSH", "TFT", "REL"],
         key={"C": ("item", "minecraft:copper_block"),
              "S": ("item", "potato_s_t:stable_metal_block"),
              "H": ("item", "potato_s_t:heater"),
              "T": ("item", "potato_s_t:titanium_ingot"),
              "F": ("item", "potato_s_t:filling_machine"),
              "R": ("item", "minecraft:redstone_torch"),
              "E": ("item", "potato_s_t:electrolyzer"),
              "L": ("item", "minecraft:lever")}),

    # ⑤ 稳定金属块（0.11 ZF104，用户口述）：【高碳钢】【硬质钛合金】【高碳钢】 /
    #    【金块】【硬质钛合金】【金块】 / 【高碳钢】【硬质钛合金】【高碳钢】
    #    ⚠ 这块方块 ZF34 就注册、ZF100 那轮用户说"只要那两个机器的配方"时**仍然没给**，
    #      本轮（ZF104）补上 ⇒「还没有配方」的名单里只剩 高级金属块 与 扳手
    #      （酸性反应室的图纸要用它，所以这一条一补上，那台机器在生存里就能做了）
    dict(name="stable_metal_block", category="misc",
         result=("potato_s_t:stable_metal_block", 1),
         pattern=["SAS", "GAG", "SAS"],
         key={"S": ("item", "potato_s_t:high_carbon_steel"),
              "A": ("item", "potato_s_t:hard_titanium_alloy"),
              "G": ("item", "minecraft:gold_block")}),

    # ===== ZF106 追加（用户原话：「钛合金套和星璨套配方加上 套用原版合成配方
    #       （铁合金用轻质钛合金）星辰套就用星璨钢」）=====
    # ⇒ **图纸逐格照抄原版铁套**（不是自己设计的），只把 `minecraft:iron_ingot` 换成
    #   钛合金套 → `potato_s_t:light_titanium_alloy`、星璨钢套 → `potato_s_t:star_steel_ingot`。
    #   原版那四张是从 `client.jar` 的 `data/minecraft/recipe/iron_*.json` 现抠的（不靠记忆）：
    #     头盔 XXX / X X      胸甲 X X,XXX,XXX      护腿 XXX,X X,X X      靴子 X X,X X
    #   ⚠ 用**精确 id**而不是 `#c:ingots/*` 标签：用户说的是"用轻质钛合金 / 用星璨钢"这两种**具体材料**，
    #     不是"任意钛合金锭 / 任意钢锭"。
    # 头盔：XXX / X X
    dict(name="titanium_alloy_helmet", category="equipment",
         result=("potato_s_t:titanium_alloy_helmet", 1),
         pattern=["XXX", "X X"],
         key={"X": ("item", "potato_s_t:light_titanium_alloy")}),
    # 胸甲：X X / XXX / XXX
    dict(name="titanium_alloy_chestplate", category="equipment",
         result=("potato_s_t:titanium_alloy_chestplate", 1),
         pattern=["X X", "XXX", "XXX"],
         key={"X": ("item", "potato_s_t:light_titanium_alloy")}),
    # 护腿：XXX / X X / X X
    dict(name="titanium_alloy_leggings", category="equipment",
         result=("potato_s_t:titanium_alloy_leggings", 1),
         pattern=["XXX", "X X", "X X"],
         key={"X": ("item", "potato_s_t:light_titanium_alloy")}),
    # 靴子：X X / X X
    dict(name="titanium_alloy_boots", category="equipment",
         result=("potato_s_t:titanium_alloy_boots", 1),
         pattern=["X X", "X X"],
         key={"X": ("item", "potato_s_t:light_titanium_alloy")}),
    # 星璨钢套：图纸同上，材料换成星璨钢锭
    dict(name="star_steel_helmet", category="equipment",
         result=("potato_s_t:star_steel_helmet", 1),
         pattern=["XXX", "X X"],
         key={"X": ("item", "potato_s_t:star_steel_ingot")}),
    dict(name="star_steel_chestplate", category="equipment",
         result=("potato_s_t:star_steel_chestplate", 1),
         pattern=["X X", "XXX", "XXX"],
         key={"X": ("item", "potato_s_t:star_steel_ingot")}),
    dict(name="star_steel_leggings", category="equipment",
         result=("potato_s_t:star_steel_leggings", 1),
         pattern=["XXX", "X X", "X X"],
         key={"X": ("item", "potato_s_t:star_steel_ingot")}),
    dict(name="star_steel_boots", category="equipment",
         result=("potato_s_t:star_steel_boots", 1),
         pattern=["X X", "X X"],
         key={"X": ("item", "potato_s_t:star_steel_ingot")}),
]

# ============================================================
#  id 存在性
# ============================================================
MOD_IDS = None
VANILLA_MODELS = None


def mod_ids():
    global MOD_IDS
    if MOD_IDS is None:
        MOD_IDS = set()
        # 【ZF106 补】这里原来只扫 ModItems / ModBlocks 两个文件 —— 而 0.11 起
        #   「同一个 DeferredRegister 可以跨类写」成了本工程的惯例（先 PotatoSTOres，
        #   后 ModArmorItems 把 9 个物品注册进 ModItems.ITEMS）。
        #   ⇒ 新增的注册类如果不加进这张名单，本表会把**已经注册好的 id** 判成"不存在"
        #   （本轮 12 条假 FAIL 全是这个）。判据是"grep 全部在注册东西的类"，
        #   所以这份名单要跟着"谁在注册"一起涨。
        for fn in ("ModItems.java", "ModBlocks.java", "ModArmorItems.java", "PotatoSTOres.java"):
            path = os.path.join(JAVA, fn)
            if not os.path.isfile(path):
                continue
            with io.open(path, "r", encoding="utf-8") as f:
                MOD_IDS |= set(re.findall(r'register\(\s*"([a-z0-9_]+)"', f.read()))
    return MOD_IDS


def vanilla_models():
    global VANILLA_MODELS
    if VANILLA_MODELS is None:
        VANILLA_MODELS = set()
        if os.path.isfile(VANILLA_JAR):
            with zipfile.ZipFile(VANILLA_JAR) as z:
                for n in z.namelist():
                    m = re.match(r"assets/minecraft/models/item/([a-z0-9_]+)\.json$", n)
                    if m:
                        VANILLA_MODELS.add(m.group(1))
    return VANILLA_MODELS


def check_id(item_id, problems, where):
    ns, _, path = item_id.partition(":")
    if ns == "potato_s_t":
        if path not in mod_ids():
            problems.append(u"%s: 本模组没有注册物品 %s" % (where, item_id))
    elif ns == "minecraft":
        if path not in vanilla_models():
            problems.append(u"%s: 原版没有物品 %s" % (where, item_id))
    else:
        problems.append(u"%s: 非本模组/原版的命名空间 %s（要人工确认）" % (where, item_id))


def build(recipe, problems):
    name = recipe["name"]
    pat = recipe["pattern"]
    key = recipe["key"]
    if not (1 <= len(pat) <= 3):
        problems.append(u"%s: 行数 %d 不在 1..3" % (name, len(pat)))
    widths = set(len(r) for r in pat)
    if len(widths) != 1:
        problems.append(u"%s: 各行列数不一致 %s" % (name, [len(r) for r in pat]))
    elif not (1 <= widths.pop() <= 3):
        problems.append(u"%s: 列数不在 1..3" % name)
    used = set(ch for r in pat for ch in r if ch != " ")
    for ch in used:
        if ch not in key:
            problems.append(u"%s: 模式里的 %r 在 key 里没有" % (name, ch))
    for ch in key:
        if ch not in used:
            problems.append(u"%s: key 里的 %r 没被用到" % (name, ch))
    for ch, (kind, value) in key.items():
        if kind == "item":
            check_id(value, problems, u"%s/%s" % (name, ch))
    check_id(recipe["result"][0], problems, u"%s/result" % name)

    obj = collections.OrderedDict()
    obj["type"] = "minecraft:crafting_shaped"
    obj["category"] = recipe["category"]
    obj["pattern"] = list(pat)
    kobj = collections.OrderedDict()
    for ch in sorted(key):
        kind, value = key[ch]
        kobj[ch] = {kind: value}
    obj["key"] = kobj
    obj["result"] = {"id": recipe["result"][0], "count": recipe["result"][1]}
    return name, obj


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    problems = []
    built = [build(r, problems) for r in RECIPES]

    # 同一个产物出现两条配方 = 多半是抄重了
    results = collections.Counter(r["result"][0] for r in RECIPES)
    for rid, n in results.items():
        if n > 1:
            problems.append(u"产物 %s 被写了 %d 条配方" % (rid, n))

    for name, obj in built:
        text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
        if args.write:
            with io.open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print(u"  [写出] %s.json  %s x%d" % (name, obj["result"]["id"], obj["result"]["count"]))
        else:
            print(u"  [校验] %s  %s" % (name, " / ".join(obj["pattern"])))
        # 写出去的东西自己能解析回来吗（BOM/转义/换行都在这句话里过一遍）
        back = json.loads(text)
        if back["pattern"] != list(obj["pattern"]):
            problems.append(u"%s: 回读的 pattern 不一致" % name)

    print(u"")
    print(u"配方 %d 条" % len(RECIPES))
    print(u"本模组 id 抽查：%d 个已注册" % len(mod_ids()))
    print(u"原版物品模型：%d 个可用" % len(vanilla_models()))
    for p in problems:
        print(u"  [FAIL] " + p)
    print(u"失败项 = %d" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
