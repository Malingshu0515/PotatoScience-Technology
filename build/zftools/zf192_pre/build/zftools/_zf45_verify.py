# -*- coding: utf-8 -*-
"""_zf45_verify.py —— ZF45 语言/贴图的**独立**复核（只读，不改任何文件）

**为什么不 import _zf45_lang.py 里的表来比**：那样是拿"我以为我写进去的东西"
去比"我写进去的东西"，两边一起错就永远查不出来（档案 §4.27 的教训：
探针的期望值必须**照着规格另写一遍**，不能引用被测常量本身）。
所以下面每个字符串都是**手打第二遍**的，不是从 _zf45_lang.py 抄的。

查 5 件事：
  ① 四语言都能解析、键集完全一致（各 180 键）；
  ② 4 个新物品键的四语言值 = 手打的第二遍；
  ③ carbon/toner 的改名生效，且**中文显示名没有重名**（这是 ②③ 改动真正的目的）；
  ④ 两条说明：行数正好多了 2 行 / 1 行，且**原有内容一句没丢**（逐语言抽查关键词）；
  ⑤ 4 张贴图 + 4 个模型文件都在盘上。
"""
import io
import json
import os
import sys

PROJ = r"E:\PotatoST"
LANG = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "lang")
ITEM_TEX = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "textures", "item")
ITEM_MODEL = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t", "models", "item")

fails = []


def check(cond, msg):
    if cond:
        print(u"  [OK]   " + msg)
    else:
        print(u"  [FAIL] " + msg)
        fails.append(msg)


def load(code):
    with io.open(os.path.join(LANG, code + ".json"), "r", encoding="utf-8") as f:
        return json.loads(f.read())


# ---------- ① 键集 ----------
print(u"== ① 四语言键集 ==")
langs = {c: load(c) for c in ("zh_cn", "en_us", "ja_jp", "ru_ru")}
base = set(langs["zh_cn"])
for c, d in langs.items():
    check(len(d) == 182, u"%s 共 %d 键（期望 182 = 原有 176 + 本批 6）" % (c, len(d)))
    check(set(d) == base, u"%s 键集与 zh_cn 一致" % c)

# ---------- ② 新键（手打第二遍） ----------
print(u"\n== ② 新增 4 个物品键 ==")
EXPECT_NEW = {
    "item.potato_s_t.iron_powder": {"zh_cn": u"铁粉", "en_us": u"Iron Dust", "ja_jp": u"鉄粉", "ru_ru": u"Железная пыль"},
    "item.potato_s_t.magnet": {"zh_cn": u"磁铁", "en_us": u"Magnet", "ja_jp": u"磁石", "ru_ru": u"Магнит"},
    "item.potato_s_t.thermal_metal": {"zh_cn": u"热力金属", "en_us": u"Thermal Metal", "ja_jp": u"熱金属",
                                      "ru_ru": u"Термальный металл"},
    "item.potato_s_t.photovoltaic_component": {"zh_cn": u"光伏原件", "en_us": u"Photovoltaic Component",
                                               "ja_jp": u"太陽光発電素子", "ru_ru": u"Фотоэлектрический компонент"},
}
for key, table in EXPECT_NEW.items():
    for c, want in table.items():
        got = langs[c].get(key)
        check(got == want, u"%s / %s = %r" % (c, key, got))

# JEI 高炉分类的两条说明（同样手打第二遍；%s 占位符四语言必须一致）
EXPECT_JEI = {
    "gui.potato_s_t.jei.energy_per_item": {
        "zh_cn": u"每件耗电 %s FE", "en_us": u"Costs %s FE per item",
        "ja_jp": u"1 個あたり %s FE", "ru_ru": u"Расход %s FE за предмет"},
    "gui.potato_s_t.jei.ebf_vanilla": {
        "zh_cn": u"原版高炉能烧的东西这里也能烧",
        "en_us": u"Also smelts everything a blast furnace can",
        "ja_jp": u"溶鉱炉で焼けるものもすべて扱えます",
        "ru_ru": u"Также плавит всё, что умеет доменная печь"},
}
for key, table in EXPECT_JEI.items():
    for c, want in table.items():
        got = langs[c].get(key)
        check(got == want, u"%s / %s = %r" % (c, key, got))
# ⚠ 第二版这里对**两条**键都断言"各含 1 个 %s"，其中 ebf_vanilla 根本没有占位符 ⇒ 假 FAIL。
#   占位符断言只对带参数的那条成立（LangCheck 的 ② 项才是权威的占位符检查）。
check(all(langs[c]["gui.potato_s_t.jei.energy_per_item"].count("%s") == 1 for c in langs),
      u"gui.potato_s_t.jei.energy_per_item 四语言各含 1 个 %%s")
check(all("%s" not in langs[c]["gui.potato_s_t.jei.ebf_vanilla"] for c in langs),
      u"gui.potato_s_t.jei.ebf_vanilla 四语言都不含占位符")

# ---------- ③ 改名 + 中文重名 ----------
print(u"\n== ③ carbon / toner 改名 + 中文显示名重名检查 ==")
check(langs["zh_cn"]["item.potato_s_t.carbon"] == u"碳粉", u"carbon 中文 = 碳粉")
check(langs["zh_cn"]["item.potato_s_t.toner"] == u"墨粉", u"toner 中文 = 墨粉（不再和碳粉撞名）")
check(langs["en_us"]["item.potato_s_t.carbon"] == u"Carbon Dust", u"carbon 英文 = Carbon Dust")

names = {}
for k, v in langs["zh_cn"].items():
    if k.startswith("item.potato_s_t.") or k.startswith("block.potato_s_t."):
        names.setdefault(v, []).append(k)
dup = {v: ks for v, ks in names.items() if len(ks) > 1}
# 「电力高炉」的控制器与部件格是**故意**同名（用户要求 Jade 显示统一）
allowed = {u"电力高炉"}
bad = {v: ks for v, ks in dup.items() if v not in allowed}
check(not bad, u"中文显示名无意外重名（例外：%s）" % u"、".join(sorted(allowed)))
if bad:
    for v, ks in bad.items():
        print(u"         !! %s -> %s" % (v, ks))

# ---------- ④ 两条说明 ----------
print(u"\n== ④ 说明行插入（行数 + 原有内容） ==")
for c in langs:
    tool = langs[c]["tooltip.potato_s_t.micro_crusher"]
    check(tool.count("\n") == 12, u"%s 粉碎机说明 %d 行（期望 13 行）" % (c, tool.count("\n") + 1))
    check(tool.count("10 FE") == 1 and tool.count("70 FE") == 1, u"%s 粉碎机说明含 10 FE/t 与 70 FE/t" % c)
    blast = langs[c]["tooltip.potato_s_t.electric_blast_furnace"]
    # 原文 5 行（ZF44 那条），本批插进去 1 行 ⇒ 6 行。
    # ⚠ 这里第一版写的是 7 行，跑出来 4 个语言一起 FAIL —— 错的是我的期望值，不是文件
    #   （同一批的粉碎机那条 13 行就过了）。期望值照规格另写一遍的意义正在这里：
    #   它会抓错，但抓到的可能是**我自己算错**，所以 FAIL 要先怀疑期望值。
    check(blast.count("\n") == 5, u"%s 高炉说明 %d 行（期望 6 行）" % (c, blast.count("\n") + 1))
    check(blast.count("800") == 1 and blast.count("4096") == 1, u"%s 高炉说明仍保留 800/4096" % c)

# 逐语言抽查"原有内容没被挤掉"
spot = {
    "zh_cn": [u"紫水晶块", u"绿宝石矿石", u"粗锂", u"内部缓冲 2500 FE", u"除本模组的矿物处理外"],
    "en_us": [u"Block of Amethyst", u"Emerald Ore", u"Raw Lithium", u"Internal buffer", u"It also handles everything"],
    "ja_jp": [u"アメジストブロック", u"エメラルド鉱石", u"粗リチウム", u"内部バッファ", u"溶鉱炉で焼けるものはすべて"],
    "ru_ru": [u"Блок аметиста", u"Изумрудная руда", u"Необработанный литий", u"Внутренний буфер", u"Обрабатывает всё"],
}
for c, words in spot.items():
    tool = langs[c]["tooltip.potato_s_t.micro_crusher"]
    blast = langs[c]["tooltip.potato_s_t.electric_blast_furnace"]
    for w in words[:4]:
        check(w in tool, u"%s 粉碎机说明仍含 %r" % (c, w))
    check(words[4] in blast, u"%s 高炉说明仍含 %r" % (c, words[4]))

# 四语言的说明必须**互不相同**（防止把某一种的文案复制到另一种）
tools = [langs[c]["tooltip.potato_s_t.micro_crusher"] for c in langs]
check(len(set(tools)) == 4, u"四种语言的粉碎机说明互不相同")
blasts = [langs[c]["tooltip.potato_s_t.electric_blast_furnace"] for c in langs]
check(len(set(blasts)) == 4, u"四种语言的高炉说明互不相同")

# ---------- ⑤ 贴图 / 模型 ----------
print(u"\n== ⑤ 新物品的贴图与模型 ==")
for name in ("iron_powder", "magnet", "thermal_metal", "photovoltaic_component"):
    tex = os.path.join(ITEM_TEX, name + ".png")
    mod = os.path.join(ITEM_MODEL, name + ".json")
    check(os.path.isfile(tex), u"textures/item/%s.png 存在（%d 字节）" % (
        name, os.path.getsize(tex) if os.path.isfile(tex) else -1))
    check(os.path.isfile(mod), u"models/item/%s.json 存在" % name)
    if os.path.isfile(mod):
        with io.open(mod, "r", encoding="utf-8") as f:
            layer = json.loads(f.read())["textures"]["layer0"]
        check(layer == "potato_s_t:item/" + name, u"%s 模型 layer0 = %s" % (name, layer))

print(u"\n------------------------------")
print(u"失败项 = %d" % len(fails))
print(u"结论: " + (u"通过" if not fails else u"有失败项"))
sys.exit(1 if fails else 0)
