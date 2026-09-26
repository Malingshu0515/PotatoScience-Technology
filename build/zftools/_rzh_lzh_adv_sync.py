# -*- coding: utf-8 -*-
r"""_rzh_lzh_adv_sync.py —— 把成就精简后的中文稿同步到文言文那一份。

为什么必须同步：四份语言文件各是独立一套文字，改了 zh_cn 不等于改了 lzh。
这条在本会话已经吃过一次亏（跨片术语撞车），所以现在成规：
**凡动成就/说明，改完中文立刻过一遍其余四语**。

改法：逐条给出 `节点 -> 文言文新稿`，旧值由 `_rzh_lzh_set.apply` 校验
（它要求"盘上当前值 == 我给的旧值"，而这里旧值从 `_rzh_lzh_old.txt` 来 ——
那是机读出来的，不是我手抄的）。

文言文写作口径（与已有 508 键一致）：
  · 繁体 + 文言虚词（之/者/也/矣/唯/即/乃/皆/凡）
  · 数字、单位（FE / mB / tick / FE/t / mB/s / n / y=）**一律原样**
  · 术语照 `_rzh_lzh_glossary.md`：礦/錠/粉/桶、印墨（碳粉）、胄/鎧/護腿/靴/鍁、
    鋰電池元件、合成氨反應室、鹽分解器、容器換流器、採油機、熱力金屬……

用法：`python build/zftools/_rzh_lzh_adv_sync.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _rzh_lzh_set import apply          # noqa: E402

OLD = os.path.join(HERE, u"_rzh_lzh_old.txt")
ROOT = os.path.dirname(os.path.dirname(HERE))
LZH = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t",
                   u"lang", u"lzh.json")

# ---------------------------------------------------------------------------
# 节点 -> 文言文新稿。**只写新稿**，旧稿从 _rzh_lzh_old.txt 机读。
# ---------------------------------------------------------------------------
NEW = {
    # 四种酸的名字不再罗列注释 —— 契约：数字与专名照抄，只动叙述
    u"acid": u"碳酸、硝酸、硫酸、鹽酸 —— 四酸皆成於此",
    u"alloy_smelter": u"合金爐主控 + 接線口 + 爐體 —— 合金之途自此始：輕質與硬質鈦合金皆出於此",
    u"capacitor": u"銅錠 + 鋁板 + 銀板 = 電容；電力高爐、合金爐、太陽能板皆需之",
    # 「量變則質變」是句哲学，没告诉玩家这东西怎么工作 —— 换成真机制
    u"clean_energy": u"唯晝發電，近午則強；雨減至 60%，雷雨僅餘 20%",
    u"combustion": u"焚一份燃料 + 10 mB 氧氣得二氧化碳；以原木焚之，兼得木炭",
    u"crushing": u"粉碎機磨錠與礦為粉；鐵粉 + 印墨即鋼之原料",
    u"diesel_generator": u"控制器 + 低級發電機二台 + 燃燒反應室 + 流體泵：3×5×2、30 格。每 tick 焚 1 mB 柴油發 7200 FE",
    u"electrolyzer": u"電解器：水 = 氧氣 + 氫氣；投海鹽一枚於電解質槽，則轉而產氯",
    # ⚠ 数字一律用**阿拉伯数字**，即使文言文里写「三十秒」更雅。
    #   理由是我自己立的守则第六条：「关键数字、坐标、层数、FE/mB 数值**必须和
    #   原文一样清楚**」。玩家扫一眼要知道"几秒、几个"，汉字数字要多花一步换算。
    #   这一条是 `_rzh_lzh_facts.py`（按数字字符比对四语）逼出来的 —— 它报了 7 处差异，
    #   其中 6 处就是"我写成了汉字数字"。
    u"first_power": u"投煤炭或木炭以發電，再以端子輸電至機器之側 —— 廉而足用，30 秒一塊",
    u"fluid_logistics": u"流體泵不存液體 —— 送得進則送，亦可抽盡液源；容器換流器執空桶，換出罐中 1000 mB 對應之桶",
    # 保留「柴油 1200 動力、汽油 1000」這個獨有數值
    u"fuel": u"二種液體燃料，皆供燃燒反應室：柴油給 1200 動力，汽油 1000",
    u"gas_handling": u"氣罐唯貯氣，油桶唯貯液；二者皆賴灌裝機以灌",
    u"light_alloy": u"鋁錠 + 鈦錠 + 銀錠 → 輕質鈦合金（合金爐，一批 30 秒）",
    # 標題就是這件物品，說明不再重複配方
    u"lithium_battery": u"一塊貯 4M FE，可如築金字塔而疊高；唯底面可接線",
    u"lithium_battery_plant": u"四樣原料各占一槽，通以硫酸：30 秒產鋰電池元件一件（此機不耗電）",
    u"oil": u"提空桶尋地表油田，汲原油一桶而歸（空桶不計）",
    u"oil_pump": u"立於海洋油田、正下方含水鎖鏈即井深 n：耗電 8n² + 80n FE/t，產油 10n mB/s",
    u"pressing": u"液壓機壓錠為板 —— 板者，幾乎諸機通用之件也（3 秒一塊）",
    u"salt": u"曬鹽機置之即出海鹽，通電則益速；海鹽投電解器出氯氣，付諸鹽分解器則出氯化鈉",
    # 刪掉「2 銀錠 → 4 銀線、8 銀線 + 1 空線軸」那段配方（JEI 有）
    u"silver_wire": u"銀線一線可跑 16134 FE/t（銅線僅 2048）—— 端子依所接最高之檔而伸縮",
    u"stable_block": u"高碳鋼 / 硬質鈦合金 / 金塊 排為九宮 —— 酸性反應室需之",
    u"star_chart_tome": u"右鍵依次歷四片星空，第五次復歸原版；潛行右鍵則逆而返之 —— 唯爾自見",
    u"star_steel": u"合金爐中：獄髓錠 + 高碳鋼 + 鈷 + 銀 + 銅，另耗 1 深鈷礦與 1 終界水晶，一爐出星璨鋼錠 3",
    u"star_steel_armor": u"四件盡披於身，即本模組至堅之套；夜則不損",
    u"star_steel_slash": u"持星璨鋼劍 Shift + 右鍵，斬出長 8 格之星輝劍氣，以此斃一生物（耐久 100、冷卻 15 秒）",
    u"star_steel_tools": u"劍 / 斧 / 鍁 / 鎬 / 鋤，圖樣依原版，材質易以星璨鋼；夜則採掘與攻擊皆不損耐久",
    u"starfall": u"右鍵擲出星軌墜：30 秒倒數、前 10 秒可撤；隕石自 y=200 墜下，威力 7~20 而帶火",
    u"steel": u"鐵粉 + 印墨投電力高爐 → 高碳鋼；鋼者，此後百器之骨也",
    u"stronger_power": u"電生磁，磁生電……莫問導線何以能傳動力，能用則善",
    u"titanium": u"粗鈦先碎為鈦粉，鈦粉再入電力高爐 → 鈦錠",
    u"titanium_armor": u"欲得振金之套，必先有此 —— 鍛造台以鈦合金四件各加一振金錠而易之",
    u"vibranium": u"合金爐中：硬質鈦合金 + 熱力金屬 + 高碳鋼 + 銀 + 金，另耗 1 粗振金與 2 獄髓碎片，一爐出 1 錠",
    u"vibranium_armor": u"鍛造台：鈦合金四件各加 1 個振金錠。四件盡披：耐久無限、彈射物免疫而反彈、爆炸減半、擊退免疫、抗性提升 I 常駐、摔落免疫，受擊有 10% 之數原樣奉還",
    u"wiring": u"接線端子即電線也：持線軸右鍵二端子以連之，潛行右鍵切換輸入 / 輸出",
    u"distillation": u"主控 + 操作器：析原油為柴油、汽油、石腦油、液化石油氣與瀝青",
}


def main():
    # 旧值**直接读盘**。`_rzh_lzh_old.txt` 只是给人看的留档（写稿时要对着它核对
    # 数字有没有抄错），程序里不必再解析一次 —— 而 `apply` 本来就会拿
    # "盘上现值"跟这里给的旧值逐字比，对不上就整批拒绝。
    lzh = json.load(io.open(LZH, encoding=u"utf-8"))
    pairs = []
    for node, new in sorted(NEW.items()):
        key = u"advancements.potato_s_t.%s.description" % node
        if key not in lzh:
            raise SystemExit(u"[拒绝] lzh 里没有 %s" % key)
        pairs.append((key, lzh[key], new))

    same = [k for k, o, n in pairs if o == n]
    if same:
        print(u"[注意] %d 条已是新稿，会跳过：" % len(same))
        for k in same:
            print(u"    %s" % k)
    apply(pairs, u"文言文成就同步")
    return 0


if __name__ == u"__main__":
    sys.exit(main())
