# -*- coding: utf-8 -*-
r"""_rzh_zverify.py —— 用户手改中文之后，四语的收口验证。

⚠ 这个脚本踩过一次坑，记下来：第一版把「必须消失」和「必须留下」写在同一个
列表里、靠"为什么"那句自然语言去猜归属，结果 52 个"失败"**全是自己的判定 bug**。
现在改成分开两个结构，且**残留检查一律 key 作用域** —— 文件级扫描会把
「タンクが満杯」这种通用词扫到一堆无关键上，那种命中不是残留。

  G1 键数 / 键集合：五份必须仍然对齐（lzh = 508 + 2 语言元数据）。
  G2a 必须消失：用户删掉的信息，不许在别的语言里活着（**按 key 查**）。
  G2b 必须留下：图纸、"必须挪机器"那句警告、以及译出来的梗（按 key 查）。
  G3 结构：占位符集合与 zh 一致；无 CR；无 BOM；无空值；无首尾空白。

用法：`python build/zftools/_rzh_zverify.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
LOCS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
OUT = os.path.join(HERE, u"_rzh_zverify.txt")

T_AXE3 = u"tooltip.potato_s_t.star_steel_axe.3"
T_AXE2 = u"tooltip.potato_s_t.star_steel_axe.2"
T_SWORD2 = u"tooltip.potato_s_t.star_steel_sword.2"
T_BATT = u"tooltip.potato_s_t.lithium_battery"
T_ELEC = u"tooltip.potato_s_t.electrolyzer"
T_EXCH = u"tooltip.potato_s_t.fluid_exchanger"
T_EXCH_OUT = u"gui.potato_s_t.fluid_exchanger.status.output_full"
T_EXCH_BAD = u"gui.potato_s_t.fluid_exchanger.status.invalid"
T_DIST = u"tooltip.potato_s_t.distillation_operator"
T_DIST_FOUND = u"gui.potato_s_t.distillation.diagnosis.found"
T_DRYER = u"tooltip.potato_s_t.salt_dryer"
T_PUMP = u"tooltip.potato_s_t.fluid_pump"
T_H2 = u"tooltip.potato_s_t.high_pressure_tank.hydrogen_risk"
T_SOLAR = u"tooltip.potato_s_t.solar_panel"
T_CRUSH = u"tooltip.potato_s_t.micro_crusher"
T_CRUSH_OFF = u"gui.potato_s_t.micro_crusher.status.disabled"
T_PRESS = u"tooltip.potato_s_t.hydraulic_press"
T_DECOMP = u"tooltip.potato_s_t.salt_decomposer"
T_LOWGEN = u"tooltip.potato_s_t.low_generator"
T_EBF = u"tooltip.potato_s_t.electric_blast_furnace"
T_ALLOY = u"tooltip.potato_s_t.alloy_smelter"
T_OIL = u"tooltip.potato_s_t.oil_pump"
T_PLANT = u"tooltip.potato_s_t.lithium_battery_plant"
T_PLANT_ACID = u"gui.potato_s_t.lithium_battery_plant.status.no_acid"
T_HDS = u"tooltip.potato_s_t.hydrodesulfurization_chamber"
T_AIR = u"tooltip.potato_s_t.air_separator"
T_NH3 = u"tooltip.potato_s_t.ammonia_synthesis_chamber"
T_COMB = u"tooltip.potato_s_t.combustion_chamber"
T_ACID = u"tooltip.potato_s_t.acidic_reaction_chamber"
T_VIB = u"tooltip.potato_s_t.vibranium_set"
T_TI = u"tooltip.potato_s_t.titanium_alloy_set"
T_SS = u"tooltip.potato_s_t.star_steel_set"
T_CHART3 = u"tooltip.potato_s_t.star_chart.3"
T_PEND3 = u"tooltip.potato_s_t.starfall_pendant.3"
T_PEND4 = u"tooltip.potato_s_t.starfall_pendant.4"
T_DIESEL = u"tooltip.potato_s_t.diesel_generator_controller"
T_DIESEL_OUT = u"gui.potato_s_t.diesel_generator.status.output_full"
T_CAPTURER = u"tooltip.potato_s_t.power_capturer"
T_SHIFT = u"tooltip.potato_s_t.hold_shift"
T_WRENCH = u"item.potato_s_t.wrench"
T_INCOMING = u"message.potato_s_t.starfall.incoming"
T_LOCKED = u"message.potato_s_t.starfall.locked"

A_ACID = u"advancements.potato_s_t.acid.description"
A_ALLOY = u"advancements.potato_s_t.alloy_smelter.description"
A_BLAST = u"advancements.potato_s_t.blast_furnace.description"
A_CAP_D = u"advancements.potato_s_t.capacitor.description"
A_CAP_T = u"advancements.potato_s_t.capacitor.title"
A_COMB = u"advancements.potato_s_t.combustion.description"
A_CRUSH = u"advancements.potato_s_t.crushing.description"
A_DIST_D = u"advancements.potato_s_t.distillation.description"
A_DIST_T = u"advancements.potato_s_t.distillation.title"
A_ELEC = u"advancements.potato_s_t.electrolyzer.description"
A_POWER = u"advancements.potato_s_t.first_power.description"
A_HARD = u"advancements.potato_s_t.hard_alloy.description"
A_LIGHT = u"advancements.potato_s_t.light_alloy.description"
A_ANVIL_D = u"advancements.potato_s_t.music_disc_anvil.description"
A_ANVIL_T = u"advancements.potato_s_t.music_disc_anvil.title"
A_JASMINE = u"advancements.potato_s_t.music_disc_jasmine.description"
A_PRESS = u"advancements.potato_s_t.pressing.description"
A_STABLE = u"advancements.potato_s_t.stable_block.description"
A_STEEL = u"advancements.potato_s_t.steel.description"
A_WIRING = u"advancements.potato_s_t.wiring.description"
A_FLUID = u"advancements.potato_s_t.fluid_logistics.description"
A_LI = u"advancements.potato_s_t.lithium_battery.description"
A_LIP = u"advancements.potato_s_t.lithium_battery_plant.description"
A_OIL = u"advancements.potato_s_t.oil_pump.description"
A_SALT = u"advancements.potato_s_t.salt.description"
A_SALT_T = u"advancements.potato_s_t.salt.title"
A_SS = u"advancements.potato_s_t.star_steel.description"
A_SF = u"advancements.potato_s_t.starfall.description"
A_VIB = u"advancements.potato_s_t.vibranium.description"
A_VIBARM = u"advancements.potato_s_t.vibranium_armor.description"
A_TIARM = u"advancements.potato_s_t.titanium_armor.description"
A_SSTOOL_T = u"advancements.potato_s_t.star_steel_tools.title"
A_SSTOOL_D = u"advancements.potato_s_t.star_steel_tools.description"
A_SLASH = u"advancements.potato_s_t.star_steel_slash.description"
A_TOME_T = u"advancements.potato_s_t.star_chart_tome.title"
A_TOME_D = u"advancements.potato_s_t.star_chart_tome.description"
A_AG = u"advancements.potato_s_t.silver_wire.description"
A_CLEAN = u"advancements.potato_s_t.clean_energy.description"

# ---------------------------------------------------------------------------
# G2a：必须消失 —— (语言, key, 必须消失的串)
# ---------------------------------------------------------------------------
GONE = [
    (u"en_us", T_AXE2, u"15 s cooldown"), (u"ja_jp", T_AXE2, u"クールダウン 15 秒"),
    (u"ru_ru", T_AXE2, u"перезарядка 15 с"), (u"lzh", T_AXE2, u"冷卻 15 秒"),
    (u"en_us", T_AXE2, u"costs 120 durability"), (u"en_us", T_AXE2, u"(15 s cooldown)"),
    (u"ru_ru", T_AXE2, u"и посылает ударную волну"), (u"lzh", T_AXE2, u"（冷卻 15 秒）"),
    (u"en_us", T_SWORD2, u"15 s cooldown"), (u"ja_jp", T_SWORD2, u"クールダウン 15 秒"),
    (u"ru_ru", T_SWORD2, u"перезарядка 15 с"), (u"lzh", T_SWORD2, u"冷卻 15 秒"),
    (u"en_us", T_AXE3, u"stripped log and leaf"), (u"ja_jp", T_AXE3, u"樹皮を剥いだ原木"),
    (u"ru_ru", T_AXE3, u"окорённые брёвна"), (u"lzh", T_AXE3, u"去皮原木與樹葉"),
    (u"en_us", T_AXE3, u"10 + 0.5n"), (u"ja_jp", T_AXE3, u"10 + 0.5n"),
    (u"ru_ru", T_AXE3, u"10 + 0.5n"), (u"lzh", T_AXE3, u"10 + 0.5n"),

    (u"en_us", T_INCOMING, u"- look up"), (u"ja_jp", T_INCOMING, u"見上げてください"),
    (u"ru_ru", T_INCOMING, u"поднимите голову"), (u"lzh", T_INCOMING, u"仰首而觀"),
    (u"en_us", T_LOCKED, u"it can no longer be cancelled"),
    (u"ja_jp", T_LOCKED, u"取り消せません"), (u"ru_ru", T_LOCKED, u"отменить нельзя"),
    (u"lzh", T_LOCKED, u"無可復罷矣"),

    (u"en_us", T_CAPTURER, u"Watches all 6 neighbouring faces"), (u"ja_jp", T_CAPTURER, u"見張り"),
    (u"ru_ru", T_CAPTURER, u"Присматривает"), (u"lzh", T_CAPTURER, u"緊貼之 6 面"),
    (u"en_us", T_CAPTURER, u"waterwheel"), (u"ja_jp", T_CAPTURER, u"水車"),
    (u"ru_ru", T_CAPTURER, u"водяного колеса"), (u"lzh", T_CAPTURER, u"水力磨坊"),

    (u"en_us", T_BATT, u"2x3 / 3x3 / 3x4 up to 12 layers"), (u"ja_jp", T_BATT, u"3×4 は 12 層まで"),
    (u"ru_ru", T_BATT, u"3×4 — до 12 слоёв"), (u"lzh", T_BATT, u"3×4 至多 12 層"),
    (u"en_us", T_BATT, u"accepts a Terminal Block"), (u"ja_jp", T_BATT, u"端子ブロックを付けられる"),
    (u"ru_ru", T_BATT, u"Клеммный блок крепится"), (u"lzh", T_BATT, u"可接接線端子"),
    (u"en_us", T_BATT, u"tile a whole layer"), (u"ja_jp", T_BATT, u"1 層をまとめて敷き詰め"),
    (u"ru_ru", T_BATT, u"замостить слой целиком"), (u"lzh", T_BATT, u"一舉鋪滿一層"),

    (u"en_us", T_SHIFT, u"Hold Shift for details"), (u"ja_jp", T_SHIFT, u"詳細を表示します"),
    (u"ru_ru", T_SHIFT, u"чтобы увидеть подробности"), (u"lzh", T_SHIFT, u"觀其詳$"),

    (u"en_us", T_ELEC, u"No electrolyte: burns 1000 FE"), (u"ja_jp", T_ELEC, u"毎 tick 1000 FE"),
    (u"ru_ru", T_ELEC, u"сжигает 1000 FE"), (u"lzh", T_ELEC, u"每 tick 食 1000 FE"),
    (u"en_us", T_ELEC, u"If a tank fills up"), (u"ja_jp", T_ELEC, u"タンクが満杯、水切れ"),
    (u"ru_ru", T_ELEC, u"Если бак заполнится"), (u"lzh", T_ELEC, u"儲罐既滿、水既竭"),

    (u"en_us", T_EXCH, u"After 3 seconds it draws out"), (u"ja_jp", T_EXCH, u"3 秒後に 1000 mB"),
    (u"ru_ru", T_EXCH, u"Через 3 секунды он забирает"), (u"lzh", T_EXCH, u"3 秒後抽走 1000 mB"),
    (u"en_us", T_EXCH, u"The pump drains the container directly"),
    (u"ja_jp", T_EXCH, u"ある分だけ汲み出します"),
    (u"ru_ru", T_EXCH, u"он качает прямо из контейнера"), (u"lzh", T_EXCH, u"有多少抽多少"),
    (u"en_us", T_EXCH_BAD, u"use an oil bucket"), (u"ja_jp", T_EXCH_BAD, u"入れてください"),
    (u"ru_ru", T_EXCH_BAD, u"нужен нефтяное ведро"), (u"lzh", T_EXCH_BAD, u"須置油桶"),
    (u"en_us", T_EXCH_OUT, u"exactly 1 empty bucket"), (u"ja_jp", T_EXCH_OUT, u"ちょうど 1 個"),
    (u"ru_ru", T_EXCH_OUT, u"ровно 1 пустое ведро"), (u"lzh", T_EXCH_OUT, u"「恰 1 個」"),

    (u"en_us", T_DIST, u"Per tower, per tick"), (u"ja_jp", T_DIST, u"塔 1 基につき毎 tick"),
    (u"ru_ru", T_DIST, u"На каждую башню за тик"), (u"lzh", T_DIST, u"每座塔每 tick"),
    (u"en_us", T_DIST, u"Every 5 ticks"), (u"ja_jp", T_DIST, u"5 tick ごとにアスファルト"),
    (u"ru_ru", T_DIST, u"Каждые 5 тиков"), (u"lzh", T_DIST, u"每 5 tick 出 1 塊瀝青"),
    (u"en_us", T_DIST_FOUND, u"up to 4 are recognised"), (u"ja_jp", T_DIST_FOUND, u"最大 4 基まで認識"),
    (u"ru_ru", T_DIST_FOUND, u"распознаётся до 4"), (u"lzh", T_DIST_FOUND, u"至多認 4 座"),

    (u"en_us", T_DRYER, u"70 FE/t"), (u"ja_jp", T_DRYER, u"70 FE/t"),
    (u"ru_ru", T_DRYER, u"70 FE/т"), (u"lzh", T_DRYER, u"70 FE/t"),

    (u"en_us", T_PUMP, u"whatever it pulls out leaves immediately"),
    (u"ja_jp", T_PUMP, u"吸い出した分はその場で送り出されます"),
    (u"ru_ru", T_PUMP, u"сколько откачал, столько сразу"),
    (u"lzh", T_PUMP, u"抽出幾何，即送走幾何"),
    (u"en_us", T_PUMP, u"anything refused is not touched"),
    (u"ja_jp", T_PUMP, u"一滴も触れません"),
    (u"ru_ru", T_PUMP, u"не притрагивается вовсе"), (u"lzh", T_PUMP, u"一滴不碰"),

    (u"en_us", T_H2, u"bear repeating)"), (u"ja_jp", T_H2, u"二度言います"),
    (u"ru_ru", T_H2, u"повторяют дважды"), (u"lzh", T_H2, u"要事須說兩遍"),

    (u"en_us", T_SOLAR, u"Rain cuts it to 60%"), (u"ja_jp", T_SOLAR, u"雨は 60%"),
    (u"ru_ru", T_SOLAR, u"падает до 60%"), (u"lzh", T_SOLAR, u"雨則降至 60%"),
    (u"en_us", T_SOLAR, u"rather be excused"), (u"ja_jp", T_SOLAR, u"休みたくなる"),
    (u"ru_ru", T_SOLAR, u"предпочла бы отпроситься"), (u"lzh", T_SOLAR, u"其亦欲告假"),

    (u"en_us", T_CRUSH, u"a redstone signal shuts it down"),
    (u"ja_jp", T_CRUSH, u"レッドストーン信号で停止します"),
    (u"ru_ru", T_CRUSH, u"выключает машину"), (u"lzh", T_CRUSH, u"有紅石信號即關機"),
    (u"en_us", T_CRUSH, u"c: common tags"), (u"ja_jp", T_CRUSH, u"c: 共通タグ"),
    (u"ru_ru", T_CRUSH, u"общим тегам c:"), (u"lzh", T_CRUSH, u"c: 通用標籤"),
    (u"en_us", T_CRUSH_OFF, u"any signal stops it"), (u"ja_jp", T_CRUSH_OFF, u"信号があると止まります"),
    (u"ru_ru", T_CRUSH_OFF, u"любой сигнал её останавливает"),
    (u"lzh", T_CRUSH_OFF, u"有信號即停機"),

    (u"en_us", T_PRESS, u"Draws 400 FE/t"), (u"ja_jp", T_PRESS, u"消費電力 400 FE/t"),
    (u"ru_ru", T_PRESS, u"Расход 400 FE/т"), (u"lzh", T_PRESS, u"耗電 400 FE/t"),
    (u"en_us", T_PRESS, u"Also: 12 Bitumen"), (u"ja_jp", T_PRESS, u"おまけ：アスファルト ×12"),
    (u"ru_ru", T_PRESS, u"Бонусом: 12 битума"), (u"lzh", T_PRESS, u"另外：瀝青 ×12"),
    (u"en_us", T_PRESS, u"copper, iron, nickel, cobalt"), (u"ja_jp", T_PRESS, u"加工できるのは"),
    (u"ru_ru", T_PRESS, u"Обрабатывает медь"), (u"lzh", T_PRESS, u"可加工者"),

    (u"en_us", T_DECOMP, u"Draws 20 FE/t and stores only"), (u"ja_jp", T_DECOMP, u"蓄電はわずか 20 FE"),
    (u"ru_ru", T_DECOMP, u"а запас всего 20 FE"), (u"lzh", T_DECOMP, u"自身只存 20 FE"),

    (u"en_us", T_LOWGEN, u"burns for 45 seconds"), (u"ja_jp", T_LOWGEN, u"45 秒間、100 FE/t"),
    (u"ru_ru", T_LOWGEN, u"горит 45 секунд"), (u"lzh", T_LOWGEN, u"焚 45 秒"),
    (u"en_us", T_LOWGEN, u"Internal storage is 1000 FE"), (u"ja_jp", T_LOWGEN, u"内部蓄電は 1000 FE"),
    (u"ru_ru", T_LOWGEN, u"Внутренний запас — 1000 FE"), (u"lzh", T_LOWGEN, u"內中儲能 1000 FE"),
    (u"en_us", T_LOWGEN, u"no fuel is wasted"), (u"ja_jp", T_LOWGEN, u"無駄遣いはしません"),
    (u"ru_ru", T_LOWGEN, u"топливо не пропадает"), (u"lzh", T_LOWGEN, u"不費燃料"),

    (u"en_us", T_EBF, u"Build the shell, then sneak-right-click"),
    (u"ja_jp", T_EBF, u"外殻ができたら"), (u"ru_ru", T_EBF, u"Постройте корпус"),
    (u"lzh", T_EBF, u"外殼既成"),
    (u"en_us", T_EBF, u"Hold a wrench and sneak-right-click"), (u"ja_jp", T_EBF, u"レンチを持って"),
    (u"ru_ru", T_EBF, u"С гаечным ключом и приседанием"), (u"lzh", T_EBF, u"手持扳鉗潛行右鍵"),
    (u"en_us", T_EBF, u"Iron Dust + Carbon Dust -> High Carbon Steel"),
    (u"ja_jp", T_EBF, u"鉄粉 + 炭素粉末 → 高炭素鋼、鉄粉 + 砂利"),
    (u"ru_ru", T_EBF, u"Железная пыль + угольная пыль → высокоуглеродистая"),
    (u"lzh", T_EBF, u"鐵粉 + 印墨 → 高碳鋼"),

    (u"en_us", T_ALLOY, u"cell marked 7"), (u"ja_jp", T_ALLOY, u"図の「7」のマス"),
    (u"ru_ru", T_ALLOY, u"клетка с цифрой 7"), (u"lzh", T_ALLOY, u"圖上書 7 之格"),
    (u"en_us", T_ALLOY, u"Light Titanium Alloy / Hard Titanium Alloy"),
    (u"ja_jp", T_ALLOY, u"軽質チタン合金 / 硬質チタン合金"),
    (u"ru_ru", T_ALLOY, u"лёгкий титановый сплав / твёрдый"),
    (u"lzh", T_ALLOY, u"輕質鈦合金 / 硬質鈦合金"),
    (u"en_us", T_ALLOY, u"Four recipes: Light"), (u"ja_jp", T_ALLOY, u"レシピ 4 種：軽質"),
    (u"ru_ru", T_ALLOY, u"Четыре рецепта: лёгкий"), (u"lzh", T_ALLOY, u"配方四條：輕質"),

    (u"en_us", T_OIL, u"Draws 8n"), (u"ja_jp", T_OIL, u"消費電力 8n"),
    (u"ru_ru", T_OIL, u"Расход 8n"), (u"lzh", T_OIL, u"耗電 8n"),
    (u"en_us", T_OIL, u"tank is output-only"), (u"ja_jp", T_OIL, u"25B タンクは出し専用"),
    (u"ru_ru", T_OIL, u"Бак на 25 вёдер работает только на выход"),
    (u"lzh", T_OIL, u"25B 大罐只出不進"),
    # ⚠ 这里的锚点必须与"必备内容"**互不为子串**：用户把「锁链就是井深 n」
    #   改成「锁链为n」、把「变成旁边那种海洋」改成「变成普通海洋」，
    #   两版只差几个字，锚点必须正好落在差别上，否则 gones 与 keeps 互相打脸。
    (u"en_us", T_OIL, u"below: that count is your well depth n"),
    (u"ja_jp", T_OIL, u"の深さ n：消費"),
    (u"ru_ru", T_OIL, u"глубина n, расход"),
    (u"lzh", T_OIL, u"鎖鏈即井深 n：耗電"),
    (u"en_us", T_OIL, u"turns into the surrounding ocean"),
    (u"ja_jp", T_OIL, u"周囲の海（凍った海"),
    (u"ru_ru", T_OIL, u"превращается в окружающий океан"),
    (u"lzh", T_OIL, u"將化為旁邊那種海洋"),

    (u"en_us", T_PLANT, u"Four inputs, each slot takes an either/or"),
    (u"ja_jp", T_PLANT, u"原料は 4 つ、各スロットは「または」"),
    (u"ru_ru", T_PLANT, u"Четыре входа, каждый слот принимает"),
    (u"lzh", T_PLANT, u"原料四樣，每槽認「或」"),
    (u"en_us", T_PLANT, u"600 mB for one 30-second batch"), (u"ja_jp", T_PLANT, u"合計 600 mB"),
    (u"ru_ru", T_PLANT, u"600 mB на партию"), (u"lzh", T_PLANT, u"凡 600 mB"),
    (u"en_us", T_PLANT, u"consumed on the last tick only"),
    (u"ja_jp", T_PLANT, u"最後の tick にまとめて"),
    (u"ru_ru", T_PLANT, u"списываются только на последнем тике"),
    (u"lzh", T_PLANT, u"至末一 tick 方各扣"),
    (u"en_us", T_PLANT_ACID, u"(600 mB per batch)"), (u"ja_jp", T_PLANT_ACID, u"（1 バッチ 600 mB）"),
    (u"ru_ru", T_PLANT_ACID, u"(600 mB на партию)"), (u"lzh", T_PLANT_ACID, u"（一爐 600 mB）"),

    (u"en_us", T_HDS, u"Per batch: 16 Bitumen"), (u"ja_jp", T_HDS, u"1 バッチ：アスファルト 16 個"),
    (u"ru_ru", T_HDS, u"За партию: 16 битума"), (u"lzh", T_HDS, u"每批：瀝青 16 個"),
    (u"en_us", T_HDS, u"Hydrogen tank holds 4000 mB"), (u"ja_jp", T_HDS, u"水素タンクは 4000 mB"),
    (u"ru_ru", T_HDS, u"Бак водорода — 4000 mB"), (u"lzh", T_HDS, u"氫氣罐 4000 mB"),
    (u"en_us", T_HDS, u"takes bitumen only"), (u"ja_jp", T_HDS, u"アスファルトのみ"),
    (u"ru_ru", T_HDS, u"принимает только битум"), (u"lzh", T_HDS, u"只收瀝青"),

    (u"en_us", T_AIR, u"Every 30 seconds"), (u"ja_jp", T_AIR, u"30 秒ごとに：窒素 8 mB"),
    (u"ru_ru", T_AIR, u"Каждые 30 секунд"), (u"lzh", T_AIR, u"每 30 秒：8 mB 氮氣"),
    (u"en_us", T_AIR, u"Draws 200 FE/t"), (u"ja_jp", T_AIR, u"消費電力 200 FE/t"),
    (u"ru_ru", T_AIR, u"Расход 200 FE/т"), (u"lzh", T_AIR, u"耗電 200 FE/t"),
    (u"en_us", T_AIR, u"tanks are output-only"), (u"ja_jp", T_AIR, u"タンクは出るだけ"),
    (u"ru_ru", T_AIR, u"работают только на выход"), (u"lzh", T_AIR, u"二儲罐只出不進"),

    (u"en_us", T_NH3, u"Per tick: 1 mB Nitrogen"), (u"ja_jp", T_NH3, u"毎 tick：窒素 1 mB"),
    (u"ru_ru", T_NH3, u"За тик: 1 mB азота"), (u"lzh", T_NH3, u"每 tick：1 mB 氮氣"),
    (u"en_us", T_NH3, u"it is not consumed, just leave it there"),
    (u"ja_jp", T_NH3, u"消費されません。置いておくだけ"),
    (u"ru_ru", T_NH3, u"она не расходуется, просто лежит"),
    (u"lzh", T_NH3, u"不耗，置於彼處即可"),

    (u"en_us", T_COMB, u"just place it next to the Capturer"),
    (u"ja_jp", T_COMB, u"キャプチャーの隣に置くだけ"),
    (u"ru_ru", T_COMB, u"просто поставьте её рядом"),
    (u"lzh", T_COMB, u"貼之於捕獲器旁即可"),

    (u"en_us", T_ACID, u"Four input tanks"), (u"ja_jp", T_ACID, u"原料タンク 4 つ"),
    (u"ru_ru", T_ACID, u"Четыре входных бака"), (u"lzh", T_ACID, u"原料罐四"),
    (u"en_us", T_ACID, u"12400 FE buffer"), (u"ja_jp", T_ACID, u"バッファ 12400 FE"),
    (u"ru_ru", T_ACID, u"при буфере 12400 FE"), (u"lzh", T_ACID, u"緩衝 12400 FE"),
    (u"en_us", T_ACID, u"A redstone signal halts it"), (u"ja_jp", T_ACID, u"信号で停止します"),
    (u"ru_ru", T_ACID, u"останавливает машину"), (u"lzh", T_ACID, u"有紅石信號即停機"),
    (u"lzh", T_ACID, u"以按鈕擇方"),

    (u"en_us", T_VIB, u"with a glint of its own"), (u"ja_jp", T_VIB, u"エンチャントの輝きを纏う"),
    (u"ru_ru", T_VIB, u"с собственным сиянием"), (u"lzh", T_VIB, u"自帶附魔光效"),
    (u"en_us", T_TI, u"Enchantment weight 25"), (u"ja_jp", T_TI, u"エンチャント適性 25"),
    (u"ru_ru", T_TI, u"Вес зачарования 25"), (u"lzh", T_TI, u"附魔權重 25"),
    (u"en_us", T_SS, u"Night Vision I, 5 s at a time"), (u"ja_jp", T_SS, u"暗視 I、1 回 5 秒"),
    (u"ru_ru", T_SS, u"Ночное зрение I, по 5 с"), (u"lzh", T_SS, u"夜視 I，每次 4 秒"),
    (u"en_us", T_SS, u"cyclic shield"), (u"ja_jp", T_SS, u"周期の盾"),
    (u"ru_ru", T_SS, u"щит цикличен"), (u"lzh", T_SS, u"週期之護盾"),
    (u"en_us", T_SS, u"Absorption III"), (u"ja_jp", T_SS, u"衝撃吸収 III"),
    (u"ru_ru", T_SS, u"Поглощение III"), (u"lzh", T_SS, u"傷害吸收 III"),
    (u"en_us", T_SS, u"Strength I and Resistance II"), (u"ja_jp", T_SS, u"力 I と耐性 II"),
    (u"ru_ru", T_SS, u"Сила I и Сопротивление II"), (u"lzh", T_SS, u"力量 I 與抗性提升 II"),

    (u"en_us", A_CLEAN, u"rain cuts it to 60%"), (u"ja_jp", A_CLEAN, u"雨は 60%"),
    (u"ru_ru", A_CLEAN, u"дождь режет до 60%"), (u"lzh", A_CLEAN, u"雨減至 60%"),

    (u"en_us", A_ACID, u"four acids, one machine"), (u"ja_jp", A_ACID, u"4 つの酸を 1 台で"),
    (u"ru_ru", A_ACID, u"четыре кислоты"), (u"lzh", A_ACID, u"四酸皆成於此"),
    (u"en_us", A_ALLOY, u"where the alloy line begins"), (u"ja_jp", A_ALLOY, u"合金ラインの出発点"),
    (u"ru_ru", A_ALLOY, u"начало линии сплавов"), (u"lzh", A_ALLOY, u"合金之途自此始"),
    (u"en_us", A_BLAST, u"self-check"), (u"ja_jp", A_BLAST, u"自己診断"),
    (u"ru_ru", A_BLAST, u"самопроверки"), (u"lzh", A_BLAST, u"自檢"),
    (u"en_us", A_CAP_D, u"Copper Ingot + Aluminum Plate"), (u"ja_jp", A_CAP_D, u"銅インゴット + アルミニウム板"),
    (u"ru_ru", A_CAP_D, u"Медный слиток"), (u"lzh", A_CAP_D, u"銅錠 + 鋁板"),
    (u"en_us", A_CAP_T, u"Build a Capacitor"), (u"ja_jp", A_CAP_T, u"コンデンサを作ろう"),
    (u"ru_ru", A_CAP_T, u"Соберите конденсатор"), (u"lzh", A_CAP_T, u"攢得一電容"),
    (u"en_us", A_COMB, u"Burn a piece of fuel"), (u"ja_jp", A_COMB, u"燃料 1 つと酸素 10 mB"),
    (u"ru_ru", A_COMB, u"Единица топлива и 10 mB"), (u"lzh", A_COMB, u"焚一份燃料"),
    (u"en_us", A_CRUSH, u"How steel begins"), (u"ja_jp", A_CRUSH, u"鋼の始まりです"),
    (u"ru_ru", A_CRUSH, u"начинается сталь"), (u"lzh", A_CRUSH, u"即鋼之原料"),
    (u"en_us", A_DIST_D, u"Controller + Processor"), (u"ja_jp", A_DIST_D, u"コントローラー + 操作器"),
    (u"ru_ru", A_DIST_D, u"Контроллер + оператор"), (u"lzh", A_DIST_D, u"主控 + 操作器"),
    (u"en_us", A_DIST_T, u"Five From One"), (u"ja_jp", A_DIST_T, u"原油を五つに分けよう"),
    (u"ru_ru", A_DIST_T, u"Пять из одного"), (u"lzh", A_DIST_T, u"一油分五品"),
    (u"en_us", A_ELEC, u"Electrolyzer: water becomes"), (u"ja_jp", A_ELEC, u"電解装置：水が酸素と水素に"),
    (u"ru_ru", A_ELEC, u"Электролизёр: вода даёт"), (u"lzh", A_ELEC, u"電解器：水 = 氧氣"),
    (u"en_us", A_POWER, u"cheap, good enough, 30 seconds a piece"),
    (u"ja_jp", A_POWER, u"安くて十分、1 個 30 秒"),
    (u"ru_ru", A_POWER, u"дёшево, достаточно, 30 секунд"), (u"lzh", A_POWER, u"廉而足用，30 秒一塊"),
    (u"en_us", A_HARD, u"Light Titanium Alloy + High Carbon Steel"),
    (u"ja_jp", A_HARD, u"軽量チタン合金 + 高炭素鋼"),
    (u"ru_ru", A_HARD, u"Лёгкий титановый сплав"), (u"lzh", A_HARD, u"輕質鈦合金 + 高碳鋼"),
    (u"en_us", A_LIGHT, u"Aluminum Ingot + Titanium Ingot"),
    (u"ja_jp", A_LIGHT, u"アルミニウム + チタン + 銀"),
    (u"ru_ru", A_LIGHT, u"Алюминиевый, титановый"), (u"lzh", A_LIGHT, u"鋁錠 + 鈦錠"),
    (u"en_us", A_ANVIL_D, u"That is all there is to it"), (u"ja_jp", A_ANVIL_D, u"それだけです、他意はありません"),
    (u"ru_ru", A_ANVIL_D, u"Вот и всё, никакого подтекста"), (u"lzh", A_ANVIL_D, u"如是而已，別無他意"),
    (u"en_us", A_ANVIL_T, u"The Anvil and the Republic"), (u"ja_jp", A_ANVIL_T, u"金床と共和国"),
    (u"ru_ru", A_ANVIL_T, u"Наковальня и Республика"), (u"lzh", A_ANVIL_T, u"鐵砧與共和國"),
    (u"en_us", A_JASMINE, u"Soul Lantern + Block of Raw Gold"),
    (u"ja_jp", A_JASMINE, u"ソウルランタン + 金の原石ブロック"),
    (u"ru_ru", A_JASMINE, u"Фонарь душ + блок"), (u"lzh", A_JASMINE, u"魂燈 + 粗金塊"),
    (u"en_us", A_PRESS, u"(3 seconds each)"), (u"ja_jp", A_PRESS, u"（1 枚 3 秒）"),
    (u"ru_ru", A_PRESS, u"(3 секунды на штуку)"), (u"lzh", A_PRESS, u"（3 秒一塊）"),
    (u"en_us", A_STABLE, u"High Carbon Steel, Hard Titanium Alloy and a Gold Block"),
    (u"ja_jp", A_STABLE, u"高炭素鋼 / 硬質チタン合金 / 金ブロック"),
    (u"ru_ru", A_STABLE, u"Высокоуглеродистая сталь, твёрдый"),
    (u"lzh", A_STABLE, u"高碳鋼 / 硬質鈦合金 / 金塊"),
    (u"en_us", A_STEEL, u"Iron dust with carbon dust"), (u"ja_jp", A_STEEL, u"鉄粉 + 炭素粉末を電力高炉へ"),
    (u"ru_ru", A_STEEL, u"Железная пыль с угольной"), (u"lzh", A_STEEL, u"鐵粉 + 印墨投電力高爐"),
    (u"en_us", A_WIRING, u"Terminals are the wires"), (u"ja_jp", A_WIRING, u"端子はそのまま電線です"),
    (u"ru_ru", A_WIRING, u"Клеммы и есть провода"), (u"lzh", A_WIRING, u"接線端子即電線也"),
    (u"en_us", A_FLUID, u"The Fluid Pump stores nothing"), (u"ja_jp", A_FLUID, u"流体ポンプは液体を溜めません"),
    (u"ru_ru", A_FLUID, u"Насос ничего не хранит"), (u"lzh", A_FLUID, u"流體泵不存液體"),
    (u"en_us", A_LI, u"stacked like a pyramid"), (u"ja_jp", A_LI, u"ピラミッドのように積めます"),
    (u"ru_ru", A_LI, u"ставится пирамидой"), (u"lzh", A_LI, u"可如築金字塔而疊高"),
    (u"en_us", A_LIP, u"one per slot, fed with sulfuric acid"),
    (u"ja_jp", A_LIP, u"1 スロットずつ、硫酸を通して"),
    (u"ru_ru", A_LIP, u"по слотам и серная кислота"), (u"lzh", A_LIP, u"各占一槽，通以硫酸"),
    # ⚠ 旧句在「井深」之后是 `n：耗電`（中文标点），新版是 `n：消費`/`n, расход`
    #   ——锚点必须一路带过那个冒号，否则命中的是新版自己（踩过三次）。
    (u"en_us", A_OIL, u"that chain is your well depth n: drawing"),
    (u"ja_jp", A_OIL, u"真下の含水チェーンが井戸の深さ n：消費"),
    (u"ru_ru", A_OIL, u"цепь с водой под ним — глубина n, расход"),
    (u"lzh", A_OIL, u"正下方含水鎖鏈即井深 n：耗電"),
    (u"en_us", A_SALT, u"The Salt Dryer needs no input"), (u"ja_jp", A_SALT, u"塩乾燥機は放置で"),
    (u"ru_ru", A_SALT, u"Сушилке для соли сырьё не нужно"), (u"lzh", A_SALT, u"曬鹽機置之即出海鹽"),
    (u"en_us", A_SALT_T, u"Salt From the Sea"), (u"ja_jp", A_SALT_T, u"海から塩を"),
    (u"ru_ru", A_SALT_T, u"Соль из моря"), (u"lzh", A_SALT_T, u"向海取鹽"),
    (u"en_us", A_SS, u"takes a Netherite Ingot"), (u"ja_jp", A_SS, u"ネザライト + 高炭素鋼"),
    (u"ru_ru", A_SS, u"незерит с высокоуглеродистой"), (u"lzh", A_SS, u"獄髓錠 + 高碳鋼"),
    (u"en_us", A_SF, u"meteor falls from y=200"), (u"ja_jp", A_SF, u"隕石は y=200 から"),
    (u"ru_ru", A_SF, u"метеорит падает с y=200"), (u"lzh", A_SF, u"隕石自 y=200 墜下"),
    (u"en_us", A_VIB, u"hard titanium alloy with thermal metal"),
    (u"ja_jp", A_VIB, u"硬質チタン合金 + 熱力金属"),
    (u"ru_ru", A_VIB, u"твёрдый титановый сплав с термальным"),
    (u"lzh", A_VIB, u"硬質鈦合金 + 熱力金屬"),
    (u"en_us", A_VIBARM, u"Smithing table: each titanium piece"),
    (u"ja_jp", A_VIBARM, u"鍛冶台：チタン合金の 4 部位"),
    (u"ru_ru", A_VIBARM, u"Кузнечный стол: к каждой титановой"),
    (u"lzh", A_VIBARM, u"鍛造台：鈦合金四件"),
    (u"en_us", A_TIARM, u"the smithing table upgrades"), (u"ja_jp", A_TIARM, u"鍛冶台で 4 部位それぞれに"),
    (u"ru_ru", A_TIARM, u"кузнечный стол улучшает"), (u"lzh", A_TIARM, u"鍛造台以鈦合金四件"),
    (u"en_us", A_SSTOOL_T, u"Star Steel Tools"), (u"ja_jp", A_SSTOOL_T, u"星燦鋼の道具"),
    (u"ru_ru", A_SSTOOL_T, u"Инструменты из звёздной стали"), (u"lzh", A_SSTOOL_T, u"星璨鋼工具"),
    (u"en_us", A_SSTOOL_D, u"vanilla patterns in Star Steel"), (u"ja_jp", A_SSTOOL_D, u"レシピはバニラのまま"),
    (u"ru_ru", A_SSTOOL_D, u"схемы как в ванилле"), (u"lzh", A_SSTOOL_D, u"圖樣依原版"),
    (u"en_us", A_SLASH, u"an 8-block starlight slash, and finish a mob"),
    (u"ja_jp", A_SLASH, u"長さ 8 ブロックの星輝斬。これでモブ"),
    (u"ru_ru", A_SLASH, u"разрез длиной 8 блоков; добейте"),
    (u"lzh", A_SLASH, u"斬出長 8 格之星輝劍氣"),
    (u"en_us", A_TOME_T, u"Star Chart Tome"), (u"ja_jp", A_TOME_T, u"星儀図の書"),
    (u"ru_ru", A_TOME_T, u"Звёздный атлас"), (u"lzh", A_TOME_T, u"星儀圖之章"),
    (u"en_us", A_TOME_D, u"cycle four skies"), (u"ja_jp", A_TOME_D, u"4 つの星空を順に切り替え"),
    (u"ru_ru", A_TOME_D, u"меняет четыре неба"), (u"lzh", A_TOME_D, u"依次歷四片星空"),
    (u"en_us", A_AG, u"A line of silver wire carries 16134"),
    (u"ja_jp", A_AG, u"銀線は 1 本 16134"),
    (u"ru_ru", A_AG, u"Линия из серебряного провода тянет 16134"),
    (u"lzh", A_AG, u"銀線一線可跑 16134"),

    (u"en_us", T_CHART3, u"change anyone else's sky"), (u"ja_jp", T_CHART3, u"他の人の空は変わりません"),
    (u"ru_ru", T_CHART3, u"чужое небо не меняется"), (u"lzh", T_CHART3, u"不改他人之天"),
    (u"en_us", T_PEND3, u"(with fire)"), (u"ja_jp", T_PEND3, u"（炎上あり）"),
    (u"ru_ru", T_PEND3, u"(с огнём)"), (u"lzh", T_PEND3, u"（帶火）"),
    # ⚠ 锚点必须带上「7~12」档位本身：新版是「· 7~12：只有破烂粗铁 / 粗铜」，
    #   旧串 `粗鐵 / 粗銅` 在新版里**也出现**，只查它必然误报。
    (u"en_us", T_PEND4, u"7-12: raw iron / raw copper"), (u"ja_jp", T_PEND4, u"7〜12：鉄の原石 / 銅の原石"),
    (u"ru_ru", T_PEND4, u"7–12: рудное железо / рудная медь"), (u"lzh", T_PEND4, u"7~12：粗鐵 / 粗銅"),
    (u"en_us", T_DIESEL, u"cell marked 9"), (u"ja_jp", T_DIESEL, u"図の「9」のマス"),
    (u"ru_ru", T_DIESEL, u"клетка с цифрой 9"), (u"lzh", T_DIESEL, u"圖上書 9 之格"),
    (u"en_us", T_DIESEL_OUT, u"buffer is full"), (u"ja_jp", T_DIESEL_OUT, u"バッファが満杯"),
    (u"ru_ru", T_DIESEL_OUT, u"буфер полон"), (u"lzh", T_DIESEL_OUT, u"緩衝已滿"),
    (u"en_us", T_WRENCH, u"^Wrench$"), (u"ja_jp", T_WRENCH, u"^レンチ$"),
    (u"ru_ru", T_WRENCH, u"^Гаечный ключ$"), (u"lzh", T_WRENCH, u"^扳鉗$"),
]

# ---------------------------------------------------------------------------
# G2b：必须留下 —— (语言, key, 必须出现的串)
# ---------------------------------------------------------------------------
KEEP = [
    (u"en_us", T_AXE3, u"block the axe cannot mine"), (u"ja_jp", T_AXE3, u"斧で採掘できないブロック"),
    (u"ru_ru", T_AXE3, u"топор не может добыть"), (u"lzh", T_AXE3, u"斧不能掘之方塊"),
    (u"en_us", T_AXE3, u"10 s without touching wood"), (u"ja_jp", T_AXE3, u"10 秒間木材に触れない"),
    (u"ru_ru", T_AXE3, u"через 10 с без древесины"), (u"lzh", T_AXE3, u"10 秒未遇木"),

    (u"en_us", T_CAPTURER, u"Alien tech, kid!"), (u"ja_jp", T_CAPTURER, u"宇宙の技術だ、坊や！"),
    (u"ru_ru", T_CAPTURER, u"Инопланетные технологии, малыш!"), (u"lzh", T_CAPTURER, u"外星之技，小子！"),
    (u"en_us", T_CAPTURER, u"power cables"), (u"ja_jp", T_CAPTURER, u"動力ケーブル"),
    (u"ru_ru", T_CAPTURER, u"силовым кабелям"), (u"lzh", T_CAPTURER, u"動力線纜"),

    (u"en_us", T_H2, u"114514"), (u"ja_jp", T_H2, u"114514"),
    (u"ru_ru", T_H2, u"114514"), (u"lzh", T_H2, u"114514"),

    (u"en_us", T_ALLOY, u"2222 | 5115"), (u"ja_jp", T_ALLOY, u"2222 | 5115"),
    (u"ru_ru", T_ALLOY, u"2222 | 5115"), (u"lzh", T_ALLOY, u"2222 | 5115"),
    (u"en_us", T_ALLOY, u"1111 | 0110"), (u"ja_jp", T_ALLOY, u"1111 | 0110"),
    (u"ru_ru", T_ALLOY, u"1111 | 0110"), (u"lzh", T_ALLOY, u"1111 | 0110"),
    (u"en_us", T_DIESEL, u"1 3 1 | 2 1 2"), (u"ja_jp", T_DIESEL, u"1 3 1 ｜ 2 1 2"),
    (u"ru_ru", T_DIESEL, u"1 3 1 | 2 1 2"), (u"lzh", T_DIESEL, u"1 3 1 ｜ 2 1 2"),

    (u"en_us", T_OIL, u"so after one pumping session"), (u"ja_jp", T_OIL, u"1 回汲み上げたら油田が残っている場所へ"),
    (u"ru_ru", T_OIL, u"после одной откачки переставьте её"), (u"lzh", T_OIL, u"須移機器至尚有油田之處"),

    (u"en_us", T_SS, u"the helmet opens a sight beyond sight"),
    (u"ja_jp", T_SS, u"ヘルメットは視界の外を照らす"),
    (u"ru_ru", T_SS, u"шлем открывает зрение за пределами зрения"),
    (u"lzh", T_SS, u"胄亦照及形貌之外"),

    (u"en_us", A_POWER, u"Industrial revolution!!"), (u"ja_jp", A_POWER, u"産業革命！！"),
    (u"ru_ru", A_POWER, u"Промышленная революция!!"), (u"lzh", A_POWER, u"工業革命！！"),
    (u"en_us", A_CAP_T, u"Faraday"), (u"ja_jp", A_CAP_T, u"ファラデー"),
    (u"ru_ru", A_CAP_T, u"Фарадея"), (u"lzh", A_CAP_T, u"法拉第"),
    (u"en_us", A_CAP_D, u"supercapacitor"), (u"ja_jp", A_CAP_D, u"スーパーコンデンサ"),
    (u"ru_ru", A_CAP_D, u"суперконденсатор"), (u"lzh", A_CAP_D, u"超級電容"),
    (u"en_us", A_SALT, u"Grandfather Sun"), (u"ja_jp", A_SALT, u"太陽のおじいちゃん"),
    (u"ru_ru", A_SALT, u"Дедушка Солнце"), (u"lzh", A_SALT, u"太陽公公"),
    (u"en_us", A_FLUID, u"chocolate syrup"), (u"ja_jp", A_FLUID, u"チョコレートシロップ"),
    (u"ru_ru", A_FLUID, u"шоколадный сироп"), (u"lzh", A_FLUID, u"巧克力漿"),
    (u"en_us", A_SLASH, u"Starlight Reaper"), (u"ja_jp", A_SLASH, u"星輝の死神"),
    (u"ru_ru", A_SLASH, u"Звёздного жнеца"), (u"lzh", A_SLASH, u"星輝死神"),
    (u"en_us", A_TOME_T, u"Observ"), (u"ja_jp", A_TOME_T, u"天象を観る"),
    (u"ru_ru", A_TOME_T, u"наблюдает небеса"), (u"lzh", A_TOME_T, u"臣夜觀天象"),
    (u"en_us", A_TOME_D, u"first step toward a new world"), (u"ja_jp", A_TOME_D, u"新しい世界への第一歩"),
    (u"ru_ru", A_TOME_D, u"первый шаг в новый мир"), (u"lzh", A_TOME_D, u"通往新世界之第一步"),
    (u"en_us", A_ANVIL_T, u"Anvil of the Republic"), (u"ja_jp", A_ANVIL_T, u"共和国の金床"),
    (u"ru_ru", A_ANVIL_T, u"Наковальня Республики"), (u"lzh", A_ANVIL_T, u"共和國之砧"),
    (u"en_us", A_LIP, u"Energy storage is expensive"), (u"ja_jp", A_LIP, u"蓄電ってのは高い"),
    (u"ru_ru", A_LIP, u"удовольствие дорогое"), (u"lzh", A_LIP, u"儲能可是很貴噠"),
    (u"en_us", A_LI, u"Quantity turns into quality"), (u"ja_jp", A_LI, u"量が質に変わる"),
    (u"ru_ru", A_LI, u"Количество переходит в качество"), (u"lzh", A_LI, u"量變而質變"),
    (u"en_us", A_CRUSH, u"a crusher crush a crusher"), (u"ja_jp", A_CRUSH, u"粉砕機を粉砕している粉砕機"),
    (u"ru_ru", A_CRUSH, u"раздробить дробилку"), (u"lzh", A_CRUSH, u"碎那正在碎粉碎機的粉碎機"),
    (u"en_us", A_VIBARM, u"Kinetic absorption! Kid"), (u"ja_jp", A_VIBARM, u"運動エネルギー吸収！"),
    (u"ru_ru", A_VIBARM, u"Поглощение кинетики!"), (u"lzh", A_VIBARM, u"動能吸收！"),
    (u"en_us", A_SSTOOL_T, u"Collector"), (u"ja_jp", A_SSTOOL_T, u"収集癖"),
    (u"ru_ru", A_SSTOOL_T, u"Коллекционная"), (u"lzh", A_SSTOOL_T, u"收集癖"),
    (u"en_us", A_COMB, u"charcoal enthusiast"), (u"ja_jp", A_COMB, u"木炭の愛好家"),
    (u"ru_ru", A_COMB, u"Любитель древесного угля"), (u"lzh", A_COMB, u"木炭之青睞者"),
    (u"en_us", A_HARD, u"aerospace material"), (u"ja_jp", A_HARD, u"航空宇宙材料"),
    (u"ru_ru", A_HARD, u"авиационный материал"), (u"lzh", A_HARD, u"航空之材"),
    (u"en_us", A_LIGHT, u"gear revolution"), (u"ja_jp", A_LIGHT, u"装備の改革"),
    (u"ru_ru", A_LIGHT, u"Революция в снаряжении"), (u"lzh", A_LIGHT, u"裝備之改革"),
    (u"en_us", A_ANVIL_D, u"no mercy"), (u"ja_jp", A_ANVIL_D, u"憐れまない"),
    (u"ru_ru", A_ANVIL_D, u"не помилует"), (u"lzh", A_ANVIL_D, u"不憫"),
    (u"en_us", A_ACID, u"carbonated drinks"), (u"ja_jp", A_ACID, u"炭酸飲料"),
    (u"ru_ru", A_ACID, u"газированные напитки"), (u"lzh", A_ACID, u"碳酸飲料"),
    (u"en_us", A_ELEC, u"power hog"), (u"ja_jp", A_ELEC, u"大食らい"),
    (u"ru_ru", A_ELEC, u"обжора"), (u"lzh", A_ELEC, u"電老虎"),
    (u"en_us", A_WIRING, u"Remote transmission!"), (u"ja_jp", A_WIRING, u"遠隔送電！"),
    (u"ru_ru", A_WIRING, u"Передача на расстояние!"), (u"lzh", A_WIRING, u"遠程傳輸！"),
    (u"en_us", T_CHART3, u"understand art"), (u"ja_jp", T_CHART3, u"芸術は分かりません"),
    (u"ru_ru", T_CHART3, u"в искусстве не смыслят"), (u"lzh", T_CHART3, u"不解藝術"),
    (u"en_us", T_PEND4, u"scrap raw iron"), (u"ja_jp", T_PEND4, u"ガラクタ"),
    (u"ru_ru", T_PEND4, u"только хлам"), (u"lzh", T_PEND4, u"唯破爛"),
    (u"en_us", A_JASMINE, u"jasmine flower"), (u"ja_jp", A_JASMINE, u"ジャスミンの花"),
    (u"ru_ru", A_JASMINE, u"жасмина"), (u"lzh", A_JASMINE, u"茉莉花"),
    (u"en_us", A_BLAST, u"multiblock"), (u"ja_jp", A_BLAST, u"マルチブロック"),
    (u"ru_ru", A_BLAST, u"Мультиблок"), (u"lzh", A_BLAST, u"多方塊"),
    (u"en_us", A_SS, u"not a product of Earth"), (u"ja_jp", A_SS, u"地球の産物"),
    (u"ru_ru", A_SS, u"не земное"), (u"lzh", A_SS, u"非地球上之產物"),
    (u"en_us", A_TIARM, u"before you can have the vibranium set"),
    (u"ja_jp", A_TIARM, u"ヴィブラニウムセットが欲しければ"),
    (u"ru_ru", A_TIARM, u"набор вибраниума"), (u"lzh", A_TIARM, u"欲得振金之套"),
    (u"en_us", A_SSTOOL_D, u"full set of Star Steel tools"),
    (u"ja_jp", A_SSTOOL_D, u"星燦鋼の道具一式"),
    (u"ru_ru", A_SSTOOL_D, u"полный набор инструментов"), (u"lzh", A_SSTOOL_D, u"星璨鋼工具一套"),
    (u"en_us", A_SF, u"30-second countdown"), (u"ja_jp", A_SF, u"30 秒のカウントダウン"),
    (u"ru_ru", A_SF, u"отсчёт 30 секунд"), (u"lzh", A_SF, u"30 秒倒數"),
    (u"en_us", A_AG, u"best heat and electricity conductor"),
    (u"ja_jp", A_AG, u"自然界で最高の熱伝導"),
    (u"ru_ru", A_AG, u"Лучший проводник тепла и тока"), (u"lzh", A_AG, u"最善導熱導電之材"),
    (u"en_us", A_VIB, u"Expensive raw materials"), (u"ja_jp", A_VIB, u"高価な原材料"),
    (u"ru_ru", A_VIB, u"Дорогое сырьё"), (u"lzh", A_VIB, u"昂貴之原料"),
    (u"en_us", A_ALLOY, u"Where the alloys begin"), (u"ja_jp", A_ALLOY, u"合金たちの起点"),
    (u"ru_ru", A_ALLOY, u"Начало всех сплавов"), (u"lzh", A_ALLOY, u"合金之起點"),
    (u"en_us", A_STEEL, u"skeleton of nearly everything"),
    (u"ja_jp", A_STEEL, u"この先ほぼすべての骨格"),
    (u"ru_ru", A_STEEL, u"скелет почти всего"), (u"lzh", A_STEEL, u"此後百器之骨"),
    (u"en_us", A_PRESS, u"common part of nearly every machine"),
    (u"ja_jp", A_PRESS, u"ほぼすべての機械の共通部品"),
    (u"ru_ru", A_PRESS, u"общая деталь почти любой машины"), (u"lzh", A_PRESS, u"幾乎諸機通用之件"),
    (u"en_us", A_STABLE, u"Acidic Reaction Chamber wants it"),
    (u"ja_jp", A_STABLE, u"酸性反応室が欲しがります"),
    (u"ru_ru", A_STABLE, u"кислотной камере"), (u"lzh", A_STABLE, u"酸性反應室需之"),
    (u"en_us", A_DIST_D, u"by the power of physics" if False else u"power of physics"),
    (u"ja_jp", A_DIST_D, u"物理学の力"),
    (u"ru_ru", A_DIST_D, u"Силой физики"), (u"lzh", A_DIST_D, u"物理之力"),
    (u"en_us", A_DIST_T, u"Five Equal Parts"), (u"ja_jp", A_DIST_T, u"五等分の原油"),
    (u"ru_ru", A_DIST_T, u"пять равных частей"), (u"lzh", A_DIST_T, u"五等份之原油"),
    (u"en_us", T_WRENCH, u"currently useless"), (u"ja_jp", T_WRENCH, u"今は使うところなし"),
    (u"ru_ru", T_WRENCH, u"пока бесполезен"), (u"lzh", T_WRENCH, u"暫時無用"),
    (u"en_us", T_INCOMING, u"watch out!"), (u"ja_jp", T_INCOMING, u"気をつけて！"),
    (u"ru_ru", T_INCOMING, u"берегитесь!"), (u"lzh", T_INCOMING, u"其慎之！"),
    (u"en_us", T_ACID, u"do not drink it"), (u"ja_jp", T_ACID, u"飲まないでください"),
    (u"ru_ru", T_ACID, u"пить не стоит"), (u"lzh", T_ACID, u"請勿飲之"),
    (u"en_us", T_ELEC, u"makes chlorine"), (u"ja_jp", T_ELEC, u"塩素を産出"),
    (u"ru_ru", T_ELEC, u"пойдёт хлор"), (u"lzh", T_ELEC, u"產氯氣"),
    (u"en_us", T_AIR, u"no shortage of that"), (u"ja_jp", T_AIR, u"いくらでもあります"),
    (u"ru_ru", T_AIR, u"хватает всем"), (u"lzh", T_AIR, u"取之不竭"),
    (u"en_us", T_AIR, u"allegedly"), (u"ja_jp", T_AIR, u"疑問あり"),
    (u"ru_ru", T_AIR, u"якобы"), (u"lzh", T_AIR, u"存疑"),
]


def load(loc):
    p = os.path.join(LANGDIR, loc + u".json")
    raw = io.open(p, "rb").read()
    return p, raw, json.loads(raw.decode(u"utf-8"))


def main():
    data, raws = {}, {}
    for loc in LOCS:
        p, raw, d = load(loc)
        data[loc], raws[loc] = d, (p, raw)
    bad = 0
    L = []

    L.append(u"===== G1 键数 / 键集合 =====")
    for loc in LOCS:
        L.append(u"%-6s keys=%d" % (loc, len(data[loc])))
    base = set(data[u"zh_cn"])
    for loc in (u"en_us", u"ja_jp", u"ru_ru"):
        d1, d2 = base - set(data[loc]), set(data[loc]) - base
        if d1 or d2:
            bad += 1
            L.append(u"[错] %s 键集合不一致：少 %d 多 %d" % (loc, len(d1), len(d2)))
        else:
            L.append(u"OK   %s 键集合与 zh_cn 一致" % loc)
    extra = set(data[u"lzh"]) - base
    if extra != {u"language.name", u"language.region"}:
        bad += 1
        L.append(u"[错] lzh 多出的键异常：%s" % sorted(extra))
    else:
        L.append(u"OK   lzh 只多 language.name / language.region")

    L.append(u"")
    L.append(u"===== G2a 必须消失（按 key）=====")
    n_gone = 0
    for loc, key, needle in GONE:
        v = data[loc].get(key)
        if v is None:
            bad += 1
            L.append(u"[错] %s 没有键 %s" % (loc, key))
            continue
        if re.search(needle, v) if needle.startswith(u"^") else (needle in v):
            bad += 1
            L.append(u"[错] %s / %s 仍有「%s」" % (loc, key, needle))
        else:
            n_gone += 1
    L.append(u"OK   %d 条残留检查全部干净" % n_gone if bad == 0 or n_gone == len(GONE)
             else u"%d / %d 条干净" % (n_gone, len(GONE)))

    L.append(u"")
    L.append(u"===== G2b 必须留下（按 key）=====")
    n_keep = 0
    for loc, key, needle in KEEP:
        v = data[loc].get(key)
        if v is None or needle not in v:
            bad += 1
            L.append(u"[错] %s / %s 缺「%s」" % (loc, key, needle))
        else:
            n_keep += 1
    L.append(u"OK   %d 条必备内容全部在" % n_keep if n_keep == len(KEEP)
             else u"%d / %d 条在" % (n_keep, len(KEEP)))

    L.append(u"")
    L.append(u"===== G3 结构 =====")
    zh = data[u"zh_cn"]
    for loc in LOCS:
        p, raw = raws[loc]
        problems = []
        if raw.startswith(b"\xef\xbb\xbf"):
            problems.append(u"有 BOM")
        if b"\r" in raw:
            problems.append(u"有 CR")
        for k, v in data[loc].items():
            a = sorted(re.findall(r"%[0-9$]*s", v))
            b = sorted(re.findall(r"%[0-9$]*s", zh.get(k, u"")))
            if a != b:
                problems.append(u"占位符 %s: %s != zh %s" % (k, a, b))
            if v.strip() == u"" and zh.get(k, u"").strip() != u"":
                problems.append(u"空值 %s" % k)
            if v != v.rstrip() or v != v.lstrip(u"\n"):
                problems.append(u"首尾空白 %s" % k)
        if problems:
            bad += 1
            L.append(u"[错] %s：%d 处" % (loc, len(problems)))
            for s in problems[:10]:
                L.append(u"       %s" % s)
        else:
            L.append(u"OK   %s 无 BOM/CR、占位符与 zh 一致、无空值/首尾空白" % loc)

    L.append(u"")
    L.append(u"===== 结论 =====")
    L.append(u"全部通过（消失检查 %d 条 / 必备检查 %d 条）" % (len(GONE), len(KEEP))
             if bad == 0 else u"有 %d 处问题" % bad)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"bad=%d gone=%d/%d keep=%d/%d -> %s"
          % (bad, n_gone, len(GONE), n_keep, len(KEEP), OUT))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
