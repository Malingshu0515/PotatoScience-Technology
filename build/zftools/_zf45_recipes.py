# -*- coding: utf-8 -*-
"""_zf45_recipes.py —— 合成配方表的生成 + 自检（ZF45 起；定形 31 条 + 锻造台 4 条）

表的来源（每条都是用户给的图纸/口述，逐条追加）：
  ZF45：14 条（微型粉碎机 … 铜线）
  ZF47：+1 条（耐热金属块）
  ZF69：+1 条（散热装置 —— 加热装置围一圈青金石）
  ZF73：+1 条（油桶 —— 铜锭/铁桶/铜锭 + 钢板/铁桶/钢板 + 铁板/铝锭/铁板，吃 2 个铁桶出 1 个）
  ZF106：+8 条（两套盔甲 —— 图纸逐格照抄原版铁套，材料换成轻质钛合金 / 星璨钢锭）
  ZF118：+1 条（星轨坠）
  ZF120：+4 条**锻造台**（振金套 —— 用户原话「照抄原版下界合金的锻造台配方，
        只不过是钛合金作为升级基底」）⇒ 从这一轮起本文件同时管两种配方类型：
        `RECIPES` = `minecraft:crafting_shaped`（工作台 3×3 图纸）
        `SMITHING` = `minecraft:smithing_transform`（锻造台：模板 + 基底 + 添加物）
⇒ 本表是这 35 份 JSON 的**唯一来源**，改配方改这里再 `--write`，
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

    # ===== ZF127 追加（银线 / 银线轴：与铜线那两条**逐字对应**，只把铜换成银）=====
    # 「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）」
    # 【银锭】【银锭】 → 4 根银线（铜线走 c:ingots/copper，银线同一条规矩走 c:ingots/silver）
    dict(name="silver_wire", category="redstone", result=("potato_s_t:silver_wire", 4),
         pattern=["SS"],
         key={"S": ("tag", "c:ingots/silver")}),

    # 【银线】×3 / 【银线】【空线轴】【银线】 / 【银线】×3 → 1 个银线轴（＝铜线轴那张图纸）
    dict(name="silver_wire_spool", category="misc", result=("potato_s_t:silver_wire_spool", 1),
         pattern=["WWW", "WSW", "WWW"],
         key={"W": ("item", "potato_s_t:silver_wire"),
              "S": ("item", "potato_s_t:empty_spool")}),

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
    # ① 三元聚合物锂电池：四角纸 / 两侧纸 / 中心电容 + 锂电池原件 + 外壳
    #    ⚠ ZF112（用户：「三元锂配方里的碳酸锂改成锂电池原件 金属板统一换成纸」）
    #      改了这张图纸，但**只改了 JSON、没改本表**（踩了「不要手写 JSON」那条规矩）。
    #      ZF118 加星轨坠时按规矩重跑生成器 ⇒ 当场把 JSON 打回旧版、被脚本的前置断言抓住
    #      （`_zf118_recipe.py` 写完前先比 zf118_pre 的哈希）。现在表与盘一致。
    dict(name="lithium_battery", category="redstone",
         result=("potato_s_t:lithium_battery", 1),
         pattern=["ACA", "PLP", "AMA"],
         key={"A": ("item", "minecraft:paper"),
              "C": ("item", "potato_s_t:capacitor"),
              "P": ("item", "minecraft:paper"),
              "L": ("item", "potato_s_t:lithium_battery_component"),
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

    # ===== ZF118 追加（用户原话：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢
    #      四角放岩浆块」）=====
    # 【岩浆块】【星璨钢锭】【岩浆块】 / 【星璨钢锭】【下界之星】【星璨钢锭】 /
    # 【岩浆块】【星璨钢锭】【岩浆块】 → 星轨坠
    dict(name="starfall_pendant", category="misc",
         result=("potato_s_t:starfall_pendant", 1),
         pattern=["MSM", "SNS", "MSM"],
         key={"M": ("item", "minecraft:magma_block"),
              "S": ("item", "potato_s_t:star_steel_ingot"),
              "N": ("item", "minecraft:nether_star")}),

    # ===== ZF122 追加（星仪图之章；今年轮我自己定的图纸 —— 用户说"你看着办"）=====
    # 【纸】【紫水晶碎片】【纸】 / 【紫水晶碎片】【荧石】【紫水晶碎片】 / 【纸】【紫水晶碎片】【纸】
    dict(name="star_chart_tome", category="misc",
         result=("potato_s_t:star_chart_tome", 1),
         pattern=["PAP", "AGA", "PAP"],
         key={"P": ("item", "minecraft:paper"),
              "A": ("item", "minecraft:amethyst_shard"),
              "G": ("item", "minecraft:glowstone")}),

    # ===== ZF134 追加（星璨钢斧）=====
    # 用户原话：「星璨钢斧头加个配方 原版斧头配方 原材料换成星璨钢就行」。
    #   原版斧头那张（本轮从 client.jar 现抠 `data/minecraft/recipe/iron_axe.json`）：
    #       pattern ["XX", "X#", " #"]、key {"#": stick, "X": 材料锭}、category equipment、count 1
    #   —— 只有 `X` 这一处换成本模组的星璨钢锭，其余逐字照抄（连 `#` 这个字符都照抄，
    #   免得跟原版的逐字段对照多一处"其实没差"的差异）。
    #   ⚠ 别把它写成 2×2 或"两个锭 + 两根棍"：原版斧子是**三行** —— 第一行两格、
    #     第二行第二格是棍、第三行**第一格空着**、第二格是棍。错一格就是"摆上去做不出来"，
    #     而 RecipeCheck 只查"字符在不在 key 里"，抓不到形状语义 ⇒
    #     `_zf134_verify.py` 才逐格对着原版那张比。
    # 【星璨钢锭】【星璨钢锭】 / 【星璨钢锭】【木棍】 / 【】【木棍】 → 星璨钢斧
    dict(name="star_steel_axe", category="equipment",
         result=("potato_s_t:star_steel_axe", 1),
         pattern=["XX", "X#", " #"],
         key={"X": ("item", "potato_s_t:star_steel_ingot"),
              "#": ("item", "minecraft:stick")}),
]

# ============================================================
#  锻造台配方（ZF120：振金套）
#
#  用户原话：「照抄原版下界合金的锻造台配方，只不过是钛合金作为升级基底」。
#  原版那张（`data/minecraft/recipe/netherite_helmet_smithing.json`，本轮从
#  client.jar 现抠）就四个字段：type / template / base / addition / result，
#  逐字抄过来只有三处改动：
#    ① base（基底）    钻石件 → **钛合金件**（用户点名的那一处）
#    ② addition（添加物）下界合金锭 → 振金锭
#    ③ result          下界合金件 → 振金件
#  ⚠ template 保持原版的**下界合金升级模板**不变 —— 用户说"照抄原版"，
#    只点名了基底这一处不同；造一个"振金升级模板"要新增物品 + 贴图，
#    不是本轮该顺手做的事。要换的话：4 条配方各改一行 + 新增 1 个物品 + 1 张贴图。
#  ⚠ 键序（type/addition/base/result/template）照抄原版 JSON，
#    这样两边能逐字段对照；`json.dumps` 按插入序输出，下面的 OrderedDict 就是键序本身。
# ============================================================
SMITHING = [
    dict(name="vibranium_helmet_smithing",
         base="potato_s_t:titanium_alloy_helmet",
         result=("potato_s_t:vibranium_helmet", 1)),
    dict(name="vibranium_chestplate_smithing",
         base="potato_s_t:titanium_alloy_chestplate",
         result=("potato_s_t:vibranium_chestplate", 1)),
    dict(name="vibranium_leggings_smithing",
         base="potato_s_t:titanium_alloy_leggings",
         result=("potato_s_t:vibranium_leggings", 1)),
    dict(name="vibranium_boots_smithing",
         base="potato_s_t:titanium_alloy_boots",
         result=("potato_s_t:vibranium_boots", 1)),
]

# 锻造台三槽的公共值：模板 = 原版下界合金升级模板；添加物 = 振金锭。
SMITHING_TEMPLATE = u"minecraft:netherite_upgrade_smithing_template"
SMITHING_ADDITION = u"potato_s_t:vibranium_ingot"

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
                src = f.read()
            # 【ZF120 补】方法名必须是**通配**的。原来那句 `register\(\s*"..."` 只认
            #   字面叫 register 的方法 —— 而 ZF120 给 ModArmorItems 加了一个
            #   `registerVibranium(...)`（振金四件与另外两套的参数表不同，故意分开写），
            #   于是这条规则把**已经注册好的 4 个 vibranium_* 判成"不存在"**（4 条假 FAIL）。
            #   判据是"方法名里含 register 的调用"，而不是"方法名恰好等于 register" ——
            #   与 ZF106 那次（类名单写窄了）是同一类错：**取证范围本身就是判据的一部分**（§4.71/§4.76）。
            for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*"([a-z0-9_]+)"', src):
                if "register" in m.group(1).lower():
                    MOD_IDS.add(m.group(2))
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


def build_smithing(entry, problems):
    u"""把一条锻造台配方拼成 JSON（键序照抄原版 `netherite_*_smithing.json`）。

    比定形配方少一堆形状校验（锻造台没有 pattern），但多两条**同部位**校验 ——
    "胸甲的配方拿头盔当基底"正是抄四行时最容易错的那种，而且错了在游戏里
    只是"某个部位做不出来"，不会报任何错。
    """
    name = entry["name"]
    base = entry["base"]
    result_id, result_count = entry["result"]
    check_id(base, problems, u"%s/base" % name)
    check_id(SMITHING_ADDITION, problems, u"%s/addition" % name)
    check_id(SMITHING_TEMPLATE, problems, u"%s/template" % name)
    check_id(result_id, problems, u"%s/result" % name)
    if result_count != 1:
        problems.append(u"%s: 锻造台配方的 result.count 必须是 1（原版口径）" % name)
    slot = name.split(u"_")[1]          # vibranium_<slot>_smithing
    if not base.endswith(u"titanium_alloy_" + slot):
        problems.append(u"%s: 基底 %s 不是同部位的钛合金件（应为 titanium_alloy_%s）"
                        % (name, base, slot))
    if not result_id.endswith(u"vibranium_" + slot):
        problems.append(u"%s: 产物 %s 与基底不是同一部位（应为 vibranium_%s）"
                        % (name, result_id, slot))

    obj = collections.OrderedDict()
    obj["type"] = u"minecraft:smithing_transform"
    obj["addition"] = {"item": SMITHING_ADDITION}
    obj["base"] = {"item": base}
    obj["result"] = {"count": result_count, "id": result_id}
    obj["template"] = {"item": SMITHING_TEMPLATE}
    return name, obj


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    problems = []
    built = [build(r, problems) for r in RECIPES]
    built_smithing = [build_smithing(r, problems) for r in SMITHING]

    # 同一个产物出现两条配方 = 多半是抄重了（两种类型放一起数）
    results = collections.Counter(r["result"][0] for r in RECIPES + SMITHING)
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

    for name, obj in built_smithing:
        text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
        if args.write:
            with io.open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print(u"  [写出] %s.json  %s <- %s + %s + %s"
                  % (name, obj["result"]["id"], obj["template"]["item"],
                     obj["base"]["item"], obj["addition"]["item"]))
        else:
            print(u"  [校验] %s  %s + %s + %s"
                  % (name, obj["template"]["item"], obj["base"]["item"], obj["addition"]["item"]))
        back = json.loads(text)
        if back["base"] != obj["base"] or back["result"] != obj["result"]:
            problems.append(u"%s: 回读的 base/result 不一致" % name)

    print(u"")
    print(u"定形配方 %d 条 + 锻造台配方 %d 条 = %d 条"
          % (len(RECIPES), len(SMITHING), len(RECIPES) + len(SMITHING)))
    print(u"本模组 id 抽查：%d 个已注册" % len(mod_ids()))
    print(u"原版物品模型：%d 个可用" % len(vanilla_models()))
    for p in problems:
        print(u"  [FAIL] " + p)
    print(u"失败项 = %d" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
