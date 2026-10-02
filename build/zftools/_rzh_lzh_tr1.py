# -*- coding: utf-8 -*-
r"""_rzh_lzh_tr1.py —— 第一份文言译稿（物品 / 方块名，138 键）。

契约（照 `_rzh_lzh_glossary.md` 更新版）：
  * 字形用**繁体**（原版 minecraft/lang/lzh.json 就是繁体：鐵礦 / 鐵璞 / 鐵錠 / 鐵胄 / 鐵鎧）；
  * 术语表里有的，一字不差照抄（X錠 / X板 / X礦 / 深X礦 / X粉 / X桶 / X線 …）；
  * 键序照输入 `_rzh_lzh_in1.json`，一个不多一个不少。

表外自立之处（术语表没写、原版 lzh 有先例的，从原版）：
  头盔→胄、胸甲→鎧、护腿→護腿、靴子→靴（原版：鐵胄 / 鐵鎧 / 鐵護腿 / 鐵鞾）
  锹→鍁（原版 item.minecraft.iron_shovel = 鐵鍁）
其余表外（扳手 / 墨粉 / 光伏元件 / 测试流体储罐 / 创造模式线缆）取其可用之译，
理由见交稿说明。用法：`python build/zftools/_rzh_lzh_tr1.py`
"""
from __future__ import print_function
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN1 = os.path.join(HERE, u"_rzh_lzh_in1.json")
OUT1 = os.path.join(HERE, u"_rzh_lzh_out1.json")
ZH = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                  u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang", u"zh_cn.json")

T = {
    # ---- 粗X（术语表：raw X = 粗X） ----
    u"item.potato_s_t.raw_vibranium": u"粗振金",
    u"item.potato_s_t.raw_manganese": u"粗錳",
    u"item.potato_s_t.raw_lithium": u"粗鋰",
    u"item.potato_s_t.raw_aluminum": u"粗鋁",
    u"item.potato_s_t.raw_cobalt": u"粗鈷",
    u"item.potato_s_t.raw_nickel": u"粗鎳",
    u"item.potato_s_t.raw_silver": u"粗銀",
    u"item.potato_s_t.raw_uranium": u"粗鈾",
    u"item.potato_s_t.raw_tungsten": u"粗鎢",
    u"item.potato_s_t.raw_titanium": u"粗鈦",
    # ---- X錠 ----
    u"item.potato_s_t.star_steel_ingot": u"星璨鋼錠",
    u"item.potato_s_t.vibranium_ingot": u"振金錠",
    u"item.potato_s_t.aluminum_ingot": u"鋁錠",
    u"item.potato_s_t.cobalt_ingot": u"鈷錠",
    u"item.potato_s_t.nickel_ingot": u"鎳錠",
    u"item.potato_s_t.silver_ingot": u"銀錠",
    u"item.potato_s_t.uranium_ingot": u"鈾錠",
    u"item.potato_s_t.titanium_ingot": u"鈦錠",
    # ---- X礦 / 深X礦 ----
    u"block.potato_s_t.aluminum_ore": u"鋁礦",
    u"block.potato_s_t.cobalt_ore": u"鈷礦",
    u"block.potato_s_t.nickel_ore": u"鎳礦",
    u"block.potato_s_t.silver_ore": u"銀礦",
    u"block.potato_s_t.uranium_ore": u"鈾礦",
    u"block.potato_s_t.manganese_ore": u"錳礦",
    u"block.potato_s_t.lithium_ore": u"鋰礦",
    u"block.potato_s_t.wolframite_ore": u"黑鎢礦",
    u"block.potato_s_t.titanium_ore": u"鈦礦",
    u"block.potato_s_t.deepslate_cobalt_ore": u"深鈷礦",
    u"block.potato_s_t.deepslate_nickel_ore": u"深鎳礦",
    u"block.potato_s_t.deepslate_silver_ore": u"深銀礦",
    u"block.potato_s_t.deepslate_uranium_ore": u"深鈾礦",
    u"block.potato_s_t.deepslate_manganese_ore": u"深錳礦",
    u"block.potato_s_t.deepslate_wolframite_ore": u"深黑鎢礦",
    u"block.potato_s_t.deepslate_titanium_ore": u"深鈦礦",
    # ---- X板 ----
    u"item.potato_s_t.iron_plate": u"鐵板",
    u"item.potato_s_t.nickel_plate": u"鎳板",
    u"item.potato_s_t.cobalt_plate": u"鈷板",
    u"item.potato_s_t.silver_plate": u"銀板",
    u"item.potato_s_t.aluminum_plate": u"鋁板",
    u"item.potato_s_t.steel_plate": u"鋼板",
    u"item.potato_s_t.copper_plate": u"銅板",
    # ---- X粉 ----
    u"item.potato_s_t.carbon": u"碳粉",
    u"item.potato_s_t.iron_powder": u"鐵粉",
    u"item.potato_s_t.titanium_powder": u"鈦粉",
    u"item.potato_s_t.lithium_concentrate": u"鋰礦精粉",
    # ---- 线 / 轴 / 端子 ----
    u"item.potato_s_t.copper_wire": u"銅線",
    u"item.potato_s_t.silver_wire": u"銀線",
    u"item.potato_s_t.empty_spool": u"空線軸",
    u"item.potato_s_t.copper_wire_spool": u"銅線軸",
    u"item.potato_s_t.silver_wire_spool": u"銀線軸",
    u"item.potato_s_t.power_cable_spool": u"動力線纜軸",
    u"block.potato_s_t.terminal": u"接線端子",
    u"block.potato_s_t.wiring_block": u"接線塊",
    u"block.potato_s_t.creative_cable": u"創造模式線纜",
    # ---- 油 / 化工 ----
    u"block.potato_s_t.crude_oil": u"原油",
    u"item.potato_s_t.oil_bucket": u"油桶",
    u"item.potato_s_t.bitumen": u"瀝青",
    u"block.potato_s_t.asphalt_block": u"柏油塊",
    u"block.potato_s_t.diesel": u"柴油",
    u"block.potato_s_t.gasoline": u"汽油",
    u"item.potato_s_t.diesel_bucket": u"柴油桶",
    u"item.potato_s_t.gasoline_bucket": u"汽油桶",
    u"item.potato_s_t.sea_salt": u"海鹽",
    u"item.potato_s_t.sodium_chloride": u"氯化鈉",
    u"item.potato_s_t.lithium_carbonate": u"碳酸鋰",
    u"item.potato_s_t.sulfur": u"硫",
    u"item.potato_s_t.silicon": u"矽",
    # ---- 机器 / 结构（术语表照抄） ----
    u"block.potato_s_t.electrolyzer": u"電解器",
    u"block.potato_s_t.distillation_controller": u"分餾塔控制器",
    u"block.potato_s_t.distillation_operator": u"分餾塔操作器",
    u"block.potato_s_t.fluid_exchanger": u"容器換流器",
    u"block.potato_s_t.fluid_pipe": u"流體管道",
    u"block.potato_s_t.fluid_pump": u"流體泵",
    u"block.potato_s_t.test_fluid_tank": u"測試流體儲罐",
    u"item.potato_s_t.high_pressure_tank": u"高壓氣罐",
    u"block.potato_s_t.filling_machine": u"灌裝機",
    u"block.potato_s_t.salt_dryer": u"曬鹽機",
    u"block.potato_s_t.salt_decomposer": u"鹽分解器",
    u"block.potato_s_t.solar_panel": u"太陽能板",
    u"block.potato_s_t.micro_crusher": u"微型粉碎機",
    u"block.potato_s_t.hydraulic_press": u"液壓機",
    u"block.potato_s_t.heater": u"加熱裝置",
    u"block.potato_s_t.heat_sink": u"散熱裝置",
    u"block.potato_s_t.generator": u"發電機",
    u"block.potato_s_t.low_generator": u"低級發電機",
    u"block.potato_s_t.power_capturer": u"動力能源捕獲器",
    u"block.potato_s_t.electric_blast_furnace": u"電力高爐",
    u"block.potato_s_t.electric_blast_furnace_part": u"電力高爐",
    u"block.potato_s_t.alloy_smelter": u"合金爐主控",
    u"block.potato_s_t.alloy_smelter_port": u"合金爐接線口",
    u"block.potato_s_t.alloy_smelter_part": u"合金冶煉爐",
    u"block.potato_s_t.oil_pump": u"採油機",
    u"block.potato_s_t.air_separator": u"空氣分離器",
    u"block.potato_s_t.combustion_chamber": u"燃燒反應室",
    u"block.potato_s_t.acidic_reaction_chamber": u"酸性反應室",
    u"block.potato_s_t.hydrodesulfurization_chamber": u"加氫脫硫反應室",
    u"block.potato_s_t.ammonia_synthesis_chamber": u"合成氨反應室",
    u"block.potato_s_t.lithium_battery": u"鋰電池",
    u"block.potato_s_t.lithium_battery_plant": u"鋰電池構造間",
    u"item.potato_s_t.lithium_battery_component": u"鋰電池元件",
    u"block.potato_s_t.diesel_generator_controller": u"柴油發電機控制器",
    u"block.potato_s_t.diesel_generator_port": u"柴油發電機接線口",
    # ---- 金属块 / 电容 / 磁石 / 热力金属 ----
    u"block.potato_s_t.common_metal_block": u"一般金屬塊",
    u"block.potato_s_t.advanced_metal_block": u"高級金屬塊",
    u"block.potato_s_t.stable_metal_block": u"穩定金屬塊",
    u"block.potato_s_t.heat_resistant_metal_block": u"耐熱金屬塊",
    u"item.potato_s_t.capacitor": u"電容",
    u"item.potato_s_t.magnet": u"磁石",
    u"item.potato_s_t.thermal_metal": u"熱力金屬",
    u"item.potato_s_t.high_carbon_steel": u"高碳鋼",
    # ---- 合金 / 工具（原版 lzh：鐵斧 / 鐵劍 / 鐵鎬 / 鐵鋤 / 鐵鍁） ----
    u"item.potato_s_t.light_titanium_alloy": u"輕質鈦合金",
    u"item.potato_s_t.hard_titanium_alloy": u"硬質鈦合金",
    u"item.potato_s_t.star_steel_axe": u"星璨鋼斧",
    u"item.potato_s_t.star_steel_sword": u"星璨鋼劍",
    u"item.potato_s_t.star_steel_pickaxe": u"星璨鋼鎬",
    u"item.potato_s_t.star_steel_hoe": u"星璨鋼鋤",
    u"item.potato_s_t.star_steel_shovel": u"星璨鋼鍁",
    u"item.potato_s_t.titanium_alloy_sword": u"鈦合金劍",
    u"item.potato_s_t.titanium_alloy_pickaxe": u"鈦合金鎬",
    # ---- 甲胄（原版 lzh：鐵胄 / 鐵鎧 / 鐵護腿 / 鐵鞾） ----
    u"item.potato_s_t.titanium_alloy_helmet": u"鈦合金胄",
    u"item.potato_s_t.titanium_alloy_chestplate": u"鈦合金鎧",
    u"item.potato_s_t.titanium_alloy_leggings": u"鈦合金護腿",
    u"item.potato_s_t.titanium_alloy_boots": u"鈦合金靴",
    u"item.potato_s_t.star_steel_helmet": u"星璨鋼胄",
    u"item.potato_s_t.star_steel_chestplate": u"星璨鋼鎧",
    u"item.potato_s_t.star_steel_leggings": u"星璨鋼護腿",
    u"item.potato_s_t.star_steel_boots": u"星璨鋼靴",
    u"item.potato_s_t.vibranium_helmet": u"振金胄",
    u"item.potato_s_t.vibranium_chestplate": u"振金鎧",
    u"item.potato_s_t.vibranium_leggings": u"振金護腿",
    u"item.potato_s_t.vibranium_boots": u"振金靴",
    # ---- 杂项 ----
    u"item.potato_s_t.star_chart_tome": u"星儀圖之章",
    u"item.potato_s_t.starfall_pendant": u"星軌墜",
    u"item.potato_s_t.music_disc_anvil_of_the_republic": u"音樂唱片",
    u"item.potato_s_t.music_disc_jasmine_flower": u"音樂唱片",
    u"item.potato_s_t.photovoltaic_component": u"光伏器件",
    u"item.potato_s_t.wrench": u"扳鉗",
    u"item.potato_s_t.toner": u"印墨",
}

# 简体字形黑名单：只在简体里出现、繁体不这么写的字（混进来就是失手）
SIMP = (u"钛钨铀铝钴镍锰锂硅矿锭铁铜银钢电气机门开关热温层数这们来时后为与并产于"
        u"过进还种样当经对应点线号处车马鸟鱼龙凤买卖读写说话语言锹锨剑镐锄护"
        u"头轨仪图炼压装储测试缆换块盐晒体构间氢脱烧炉钳仅")


def main():
    with io.open(IN1, encoding=u"utf-8") as f:
        src = json.load(f)
    out = dict((k, T[k]) for k in src)          # 键序 = 输入键序

    missing = [k for k in src if k not in T]
    extra = [k for k in T if k not in src]
    if missing or extra:
        raise SystemExit(u"[拒绝] 映射表与输入不符：缺 %s / 多 %s" % (missing[:5], extra[:5]))

    text = json.dumps(out, ensure_ascii=False, indent=2)
    if u"\r" in text:
        text = text.replace(u"\r\n", u"\n")
    with io.open(OUT1, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(text + u"\n")
    print(u"wrote %s  (%d keys, %d bytes)" % (os.path.basename(OUT1), len(out), os.path.getsize(OUT1)))

    # ---- 自检 ----
    b = json.load(io.open(OUT1, encoding=u"utf-8"))
    print(u"keys equal:", list(src) == list(b), len(src), len(b))
    same = [k for k in src if src[k] == b[k]]
    print(u"untranslated (still identical to zh):", same)
    print(u"too long (>9 chars):", [(k, b[k]) for k in b if len(b[k]) > 9])
    longer = [(k, b[k], src[k]) for k in src if len(b[k]) > len(src[k]) + 1]
    print(u"longer than input+1:", longer)
    ph = [(k, b[k]) for k in b if u"%" in b[k] or u"\\n" in b[k]]
    print(u"placeholders/newlines:", ph)
    simp = [(k, u"".join(c for c in b[k] if c in SIMP)) for k in b if any(c in SIMP for c in b[k])]
    print(u"simplified glyphs leaked:", simp)

    if os.path.exists(ZH):
        zh = json.load(io.open(ZH, encoding=u"utf-8"))
        samezh = [k for k in b if zh.get(k) == b[k]]
        print(u"identical to zh_cn on disk (%d):" % len(samezh), samezh)


if __name__ == u"__main__":
    main()
