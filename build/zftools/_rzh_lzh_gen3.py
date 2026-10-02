# -*- coding: utf-8 -*-
r"""_rzh_lzh_gen3.py —— 第三份文言文译稿（消息 / 死讯 / 星图 / 群系 / 成就）。

字形取繁体，理据取自盘上实物，不是拍脑袋：

  · 原版 `minecraft/lang/lzh.json`（资源对象 c1399c55…，8557 键）本就是**繁体字形**：
    鐵錠、石炭、礦藝、製物案、爐、終界水玉、%1$s爲%2$s所殺。
    mod 的 lzh 与它同屏显示，字形必须一致。
  · 术语表（_rzh_lzh_glossary.md，2026-09-27 更新版）的表项本身就是繁体：
    鈦、星璨鋼、電解器、熱力金屬、析水為二氣、煉得星璨鋼……表里有的照抄。
    更新版改动的表项已照改：X礦（不作「X礦石」）、深X礦、熱力金屬、
    合成氨反應室、加氫脫硫反應室、合金爐接線口。
  · 姊妹稿 _rzh_lzh_out2.json 亦走繁体 + 文言（星軌墜、隕石、終界、劍氣、唯…、至多…）。
  · 数字、单位、坐标、占位符一律不动：FE / mB / tick / 秒 / %s / %1$s / %%。

用法：`python build/zftools/_rzh_lzh_gen3.py`
"""
from __future__ import print_function
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, u"_rzh_lzh_in3.json")
OUT = os.path.join(HERE, u"_rzh_lzh_out3.json")

# 键序无关，落盘时按输入顺序重排；键名必须与 in3 逐字相同。
T = {
    u"itemGroup.potato_s_t": u"PotatoS&T",

    # ---- 星仪图 / 星轨坠 ----
    u"message.potato_s_t.star_chart.switched": u"星儀圖：%s",
    u"message.potato_s_t.starfall.cancelled": u"星軌墜之召已罷",
    u"message.potato_s_t.starfall.countdown": u"★ %s 之星軌墜：尚餘 %s 秒",
    u"message.potato_s_t.starfall.incoming": u"⚠ 隕石正向 %s %s 墜下 —— 仰首而觀",
    u"message.potato_s_t.starfall.locked": u"既已鎖定，無可復罷矣",
    u"message.potato_s_t.starfall.started": u"星軌墜已起牽引：30 秒後落地，10 秒內再右鍵一次則可罷之",
    u"message.potato_s_t.starfall.warning": u"⚠ %s 之星軌墜已鎖定 %s %s %s —— 速離彼處！",

    # ---- 星图（星图册所循环的四片天 + 原版）----
    u"sky.potato_s_t.0": u"原版星空",
    u"sky.potato_s_t.1": u"碧霄星雲",
    u"sky.potato_s_t.2": u"星海幽巒",
    u"sky.potato_s_t.3": u"赤河星漢",
    u"sky.potato_s_t.4": u"蛛巢星雲",

    # ---- 端子模式 ----
    u"mode.potato_s_t.none": u"無",
    u"mode.potato_s_t.input": u"輸入",
    u"mode.potato_s_t.output": u"輸出",
    u"message.potato_s_t.terminal_mode": u"接線端子之式：%s",
    u"message.potato_s_t.terminal_selected": u"已擇此端子！再右鍵他端子，即可連之",
    u"message.potato_s_t.terminal_connected": u"接線端子已連",
    u"message.potato_s_t.terminal_cancelled": u"已罷選",
    u"message.potato_s_t.terminal_too_far": u"相距過遠！至多 %s 格。電亦有性",
    u"message.potato_s_t.terminal_already_connected": u"此二端子固已相連矣",
    u"message.potato_s_t.terminal_missing": u"前所擇之端子已不存，請重擇之",

    # ---- 锂电池多方块 ----
    u"message.potato_s_t.battery_status": u"鋰電池已成：%s×%s×%s（共 %s 塊），能量 %s / %s FE",
    u"message.potato_s_t.battery_not_formed": u"鋰電池未成：須一完整長方體（2×2 至多 6 層；2×3 / 3×3 / 3×4 至多 12 層；4×4 / 5×5 至多 32 層）",
    u"message.potato_s_t.battery_layer_placed": u"已置 %s 塊鋰電池",
    u"message.potato_s_t.battery_layer_blocked": u"置之不成：所置之位有阻",
    u"message.potato_s_t.battery_layer_no_items": u"置之不成：鋰電池不足（須 %s 塊）",
    u"message.potato_s_t.battery_layer_no_room": u"置之不成：此底面已至極（限 %s 層）",
    u"message.potato_s_t.battery_base_invalid": u"置之不成：底面之形不合（唯認 2×2、2×3、3×3、3×4、4×4、5×5）",
    u"message.potato_s_t.battery_single_no_stack": u"單塊鋰電池疊之不起：請先鋪至少 2×2 之底面",

    # ---- 群系 / 唱片 ----
    u"biome.potato_s_t.ocean_oilfield": u"海洋油田",
    u"biome.potato_s_t.salty_river": u"鹹水河",
    u"jukebox_song.potato_s_t.anvil_of_the_republic": u"牢薯不甘囚 - 共和國之砧",
    u"jukebox_song.potato_s_t.jasmine_flower": u"茉莉花（管弦樂）",

    # ---- 太阳能板 ----
    u"message.potato_s_t.solar_status": u"太陽能板並聯：%s 塊，合計發電 %s FE/t",
    u"message.potato_s_t.solar_self": u"本塊分得 %s FE/t，狀態：%s",
    u"message.potato_s_t.solar_pool": u"共享儲能 %s / %s FE（本塊緩衝 %s / %s FE）",
    u"message.potato_s_t.solar.state.clear": u"晴",
    u"message.potato_s_t.solar.state.rain": u"雨天（發電 60%）",
    u"message.potato_s_t.solar.state.thunder": u"雷暴（發電 20%）",
    u"message.potato_s_t.solar.state.night": u"夜間不發電",
    u"message.potato_s_t.solar.state.blocked": u"上有遮蔽",
    u"message.potato_s_t.solar.state.dimension": u"此維度無陽光",

    # ---- 开篇 ----
    u"advancements.potato_s_t.new_beginning.title": u"PotatoS&T",
    u"advancements.potato_s_t.new_beginning.description": u"造微型粉碎機 —— 磨礦石為粉，此後一切之基也",
    u"advancements.potato_s_t.stronger_power.title": u"電源更勁",
    u"advancements.potato_s_t.stronger_power.description": u"電生磁，磁生電……莫問導線何以能傳動力",
    u"advancements.potato_s_t.clean_energy.title": u"初入清潔能源",
    u"advancements.potato_s_t.clean_energy.description": u"量積則質變",

    # ---- 死讯 ----
    u"death.attack.potato_s_t.vibranium_reflect": u"%1$s 之攻，原樣還諸己身",
    u"death.attack.potato_s_t.star_steel_slash": u"%1$s 為星光所貫",
    u"message.potato_s_t.star_steel_void_block": u"星璨鋼套：已傳至最近之方塊上",
    u"message.potato_s_t.star_steel_void_swap": u"星璨鋼套：近旁無方塊，已與生物易位",
    u"message.potato_s_t.star_steel_void_failed": u"星璨鋼套：既無方塊，亦無生物可易位",

    # ---- 成就：酸 / 合金炉 / 氨 / 高炉 ----
    u"advancements.potato_s_t.acid.description": u"碳酸 / 硝酸 / 硫酸 / 鹽酸 —— 四酸皆成於此",
    u"advancements.potato_s_t.acid.title": u"酸性反應室",
    u"advancements.potato_s_t.alloy_smelter.description": u"合金爐主控 + 合金爐接線口 + 爐體：三種金屬板 + 電容 + 加熱裝置 + 散熱裝置 —— 合金之途自此始",
    u"advancements.potato_s_t.alloy_smelter.title": u"配成一爐",
    u"advancements.potato_s_t.ammonia.description": u"空氣分離器出氮氣，氮氣 + 氫氣於合成氨反應室中合成氨氣（硝酸之原料）",
    u"advancements.potato_s_t.ammonia.title": u"合成氨",
    u"advancements.potato_s_t.blast_furnace.description": u"一棟 3×3×3 之多方塊：正面錨點置原版高爐或主控，再以外殼圍之，安置既畢，右鍵主控自檢",
    u"advancements.potato_s_t.blast_furnace.title": u"築高爐",
    u"advancements.potato_s_t.capacitor.description": u"銅錠 + 鋁板 + 銀板 = 電容；電力高爐、合金爐、太陽能板皆需之",
    u"advancements.potato_s_t.capacitor.title": u"攢得一電容",
    u"advancements.potato_s_t.combustion.description": u"一份燃料 + 10 mB 氧氣 → 二氧化碳；以原木焚之，兼得木炭",
    u"advancements.potato_s_t.combustion.title": u"燃燒反應室",

    # ---- 成就：粉碎 / 分馏 / 电解 / 发电 / 燃料 / 气罐 ----
    u"advancements.potato_s_t.crushing.description": u"粉碎機磨錠與礦為粉：鐵粉 + 碳粉即鋼之原料（碳粉燒煤炭或木炭皆可）",
    u"advancements.potato_s_t.crushing.title": u"磨而為粉",
    u"advancements.potato_s_t.distillation.description": u"主控 + 操作器：析原油為柴油、汽油、石腦油、液化石油氣與瀝青",
    u"advancements.potato_s_t.distillation.title": u"一油分五品",
    u"advancements.potato_s_t.electrolyzer.description": u"電解器：水 + 電 → 氧氣 + 氫氣；加海鹽再電解 → 氯氣 + 氫氣",
    u"advancements.potato_s_t.electrolyzer.title": u"析水為二氣",
    u"advancements.potato_s_t.first_power.description": u"簡潔之電源，便而足用 —— 投煤炭或木炭以發電，再以端子輸電至機器之側",
    u"advancements.potato_s_t.first_power.title": u"第一度電",
    u"advancements.potato_s_t.fuel.description": u"二種液體燃料，皆供燃燒反應室之用（柴油 1200 動力、汽油 1000）",
    u"advancements.potato_s_t.fuel.title": u"柴油與汽油",
    u"advancements.potato_s_t.gas_handling.description": u"高壓氣罐唯貯氣，油桶唯貯液；二者皆賴灌裝機以灌之",
    u"advancements.potato_s_t.gas_handling.title": u"氣體之存取",

    # ---- 成就：两种钛合金 / 两张唱片 / 石油 ----
    u"advancements.potato_s_t.hard_alloy.description": u"輕質鈦合金 + 高碳鋼 + 鎳錠 → 硬質鈦合金",
    u"advancements.potato_s_t.hard_alloy.title": u"硬質鈦合金",
    u"advancements.potato_s_t.light_alloy.description": u"鋁錠 + 鈦錠 + 銀錠 → 輕質鈦合金（合金爐，一批 30 秒）",
    u"advancements.potato_s_t.light_alloy.title": u"輕質鈦合金",
    u"advancements.potato_s_t.music_disc_anvil.description": u"紅石 + 鈦錠 + 鐵砧 = 一張唱片。如是而已，別無他意",
    u"advancements.potato_s_t.music_disc_anvil.title": u"鐵砧與共和國",
    u"advancements.potato_s_t.music_disc_jasmine.description": u"魂燈 + 粗金塊 + 火把花 = 又一張唱片。好一朵美麗之茉莉花",
    u"advancements.potato_s_t.music_disc_jasmine.title": u"茉莉花",
    u"advancements.potato_s_t.oil.description": u"提油桶尋地表油田，汲原油一桶而歸（空桶不計）",
    u"advancements.potato_s_t.oil.title": u"石油",

    # ---- 成就：压板 / 稳定块 / 炼钢 / 硫 / 钛 ----
    u"advancements.potato_s_t.pressing.description": u"液壓機壓錠為板 —— 鐵板、銅板、鋁板，凡機器通用之件也",
    u"advancements.potato_s_t.pressing.title": u"壓而為板",
    u"advancements.potato_s_t.stable_block.description": u"高碳鋼 / 硬質鈦合金 / 金塊 排為九宮 → 穩定金屬塊（酸性反應室需之）",
    u"advancements.potato_s_t.stable_block.title": u"穩定金屬塊",
    u"advancements.potato_s_t.steel.description": u"鐵粉 + 碳粉投入電力高爐 → 高碳鋼；鋼者，此後百器之骨也",
    u"advancements.potato_s_t.steel.title": u"鋼鐵如是鍊成",
    u"advancements.potato_s_t.sulfur.description": u"瀝青 + 氫氣入加氫脫硫反應室 → 硫（硫酸之原料）",
    u"advancements.potato_s_t.sulfur.title": u"瀝青中取硫",
    u"advancements.potato_s_t.titanium.description": u"粗鈦先碎為鈦粉，鈦粉再入電力高爐 → 鈦錠",
    u"advancements.potato_s_t.titanium.title": u"鈦",
    u"advancements.potato_s_t.titanium_tools.description": u"輕質鈦合金 + 木棍 → 鈦合金劍與鎬",
    u"advancements.potato_s_t.titanium_tools.title": u"鈦合金工具",
    u"advancements.potato_s_t.wiring.description": u"接線端子即電線也：持銅線軸右鍵二端子以連之（動力網絡用動力線纜軸），潛行右鍵切換輸入 / 輸出",
    u"advancements.potato_s_t.wiring.title": u"通電",
    u"advancements.potato_s_t.fluid_logistics.description": u"流體泵不存液體，唯送目標所能受者，亦可抽盡液源；容器換流器執空桶，換出罐中 1000 mB 對應之桶",
    u"advancements.potato_s_t.fluid_logistics.title": u"液體物流",

    # ---- 成就：锂电池 / 采油 / 晒盐 ----
    u"advancements.potato_s_t.lithium_battery.description": u"紙 + 電容 + 一般金屬塊 + 鋰電池原件 → 三元聚合物鋰電池；一塊貯 4M FE，可如築金字塔而疊高，唯底面可接線",
    u"advancements.potato_s_t.lithium_battery.title": u"三元聚合物鋰電池",
    u"advancements.potato_s_t.lithium_battery_plant.description": u"通硫酸（每 tick 1 mB，一爐 600 mB），四槽各置：粗錳或粗鋁、鎳、碳酸鋰、鈷，30 秒產鋰電池原件一件",
    u"advancements.potato_s_t.lithium_battery_plant.title": u"鋰電池構造間",
    u"advancements.potato_s_t.oil_pump.description": u"採油機立於海洋油田：正下方含水鎖鏈即井深 n，耗電 8n² + 80n FE/t、產油 10n mB/s，25B 橫罐只出不進",
    u"advancements.potato_s_t.oil_pump.title": u"海底取油",
    u"advancements.potato_s_t.salt.description": u"曬鹽機不須投料，置之即出鹽，通電則益速；海鹽投入電解器加水則出氯氣，付諸鹽分解器，則 64 個海鹽 40 秒出氯化鈉",
    u"advancements.potato_s_t.salt.title": u"向海取鹽",

    # ---- 成就：星璨钢 / 套装 / 星轨坠 ----
    u"advancements.potato_s_t.star_steel.description": u"合金爐一爐吞：獄髓錠 + 4 高碳鋼 + 鈷錠 + 銀錠 + 銅錠 + 深鈷礦 + 終界水晶，出星璨鋼錠 3 個（12000 FE/t 滿跑 30 秒）",
    u"advancements.potato_s_t.star_steel.title": u"煉得星璨鋼",
    u"advancements.potato_s_t.star_steel_armor.description": u"頭盔 5 + 胸甲 8 + 護腿 7 + 靴子 4 = 24 個星璨鋼錠 —— 四件盡披於身，即本模組至堅之套",
    u"advancements.potato_s_t.star_steel_armor.title": u"星璨鋼套裝",
    u"advancements.potato_s_t.starfall.description": u"右鍵擲出星軌墜：耐久 4 點、用一次則減一點，30 秒倒數、前 10 秒可撤；隕石自 y=200 墜下，7~20 威力之爆（帶火），另夾 3 塊粗振金",
    u"advancements.potato_s_t.starfall.title": u"召星墜地",

    # ---- 成就：振金 / 两套甲 / 工具 / 剑气 / 星仪图 ----
    u"advancements.potato_s_t.vibranium.title": u"煉出振金",
    u"advancements.potato_s_t.vibranium.description": u"合金爐一爐吞：硬質鈦合金 1 + 熱力金屬 8 + 高碳鋼 2 + 銀錠 3 + 金錠 12，另以 1 粗振金 + 2 獄髓碎片為耗 —— 14500 FE/t 滿跑 30 秒出 1 錠",
    u"advancements.potato_s_t.vibranium_armor.title": u"振金套裝",
    u"advancements.potato_s_t.vibranium_armor.description": u"鍛造台：鈦合金四件各加 1 個振金錠（模板用獄髓升級）。四件盡披：彈射物免疫而反彈、爆炸減半、擊退免疫、抗性提升 I 常駐、摔落免疫、受擊有 10% 之數原樣奉還",
    u"advancements.potato_s_t.titanium_armor.title": u"鈦合金套裝",
    u"advancements.potato_s_t.titanium_armor.description": u"頭盔 5 + 胸甲 8 + 護腿 7 + 靴子 4 = 24 個輕質鈦合金 —— 欲得振金之套，必先有此：鍛造台乃以鈦合金四件各加一振金錠而易之",
    u"advancements.potato_s_t.star_steel_tools.title": u"星璨鋼工具",
    u"advancements.potato_s_t.star_steel_tools.description": u"劍 / 斧 / 鍬 / 鎬 / 鋤，圖樣依原版，材質易以星璨鋼；夜則採掘與攻擊皆不損耐久，劍尚可 Shift + 右鍵發星輝劍氣一道",
    u"advancements.potato_s_t.star_steel_slash.title": u"星輝斬",
    u"advancements.potato_s_t.star_steel_slash.description": u"持星璨鋼劍 Shift + 右鍵，斬出長 8 格之劍氣，以此斃一生物 —— 劍氣貫沿途一切敵，各受 12 點傷害、為星輝所照 5 秒；其代價為 100 點耐久與 15 秒冷卻",
    u"advancements.potato_s_t.star_chart_tome.title": u"星儀圖之章",
    u"advancements.potato_s_t.star_chart_tome.description": u"4 紙 + 4 紫水晶碎片 + 1 熒石 = 一本；右鍵依次歷四片星空，第五次復歸原版星空，潛行右鍵則逆而返之 —— 唯爾自見",

    # ---- 成就：柴油发电机 / 银线 ----
    u"advancements.potato_s_t.diesel_generator.title": u"大型柴油發電機",
    u"advancements.potato_s_t.diesel_generator.description": u"3×5×2 之 30 格結構：控制器 + 低級發電機二台 + 燃燒反應室 + 流體泵；每 tick 焚 1 mB 柴油發 7200 FE，柴油罐 8000 mB、內中緩衝 18000 FE",
    u"advancements.potato_s_t.silver_wire.title": u"銀線",
    u"advancements.potato_s_t.silver_wire.description": u"2 銀錠 → 4 銀線，8 銀線 + 1 空線軸 = 1 個銀線軸；以此接線，一線可跑 16134 FE/t（銅線 2048），端子依所接最高之檔而伸縮",
}

PH = re.compile(u"%\\d+\\$s|%s|%%")


def main():
    with io.open(IN, encoding=u"utf-8") as f:
        zh = json.load(f)

    missing = [k for k in zh if k not in T]
    extra = [k for k in T if k not in zh]
    if missing or extra:
        raise SystemExit(u"[拒绝] 键不齐：缺 %s；多 %s" % (missing[:8], extra[:8]))

    bad_ph, bad_nl = [], []
    for k, zv in zh.items():
        v = T[k]
        if PH.findall(zv) != PH.findall(v):
            bad_ph.append((k, PH.findall(zv), PH.findall(v)))
        if zv.count(u"\\n") != v.count(u"\\n"):
            bad_nl.append((k, zv.count(u"\\n"), v.count(u"\\n")))
    if bad_ph or bad_nl:
        raise SystemExit(u"[拒绝] 占位符/换行不符：%s %s" % (bad_ph[:5], bad_nl[:5]))

    ordered = dict((k, T[k]) for k in zh)
    text = json.dumps(ordered, ensure_ascii=False, indent=2)
    with io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n") as f:
        f.write(text + u"\n")
    print(u"wrote %s（%d 键，%d 字节）" % (OUT, len(ordered), os.path.getsize(OUT)))

    # 与中文原文逐字相同的键（专有名词之属，须人工确认后进 SAME_OK）
    same = [k for k in zh if zh[k] == T[k]]
    print(u"与 zh_cn 逐字相同（%d）：%s" % (len(same), same))
    return 0


if __name__ == u"__main__":
    raise SystemExit(main())
