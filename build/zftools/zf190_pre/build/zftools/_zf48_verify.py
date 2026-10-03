# -*- coding: utf-8 -*-
"""_zf48_verify.py —— ZF48 的**独立**盘面复核（只读，规格手打第二遍）

查 6 件事：
  ① 四语言键集一致、各 190 键（185 + 5）；新键值 = 手打的第二遍；中文无重名；
  ② 贴图**全部借原版铁/火药**（用户指定）—— 模型里的 layer0/all 必须指向 minecraft:，
     而且那 4 张原版贴图在 client.jar 里真的存在（否则是紫黑格）；
  ③ 掉落表：两张都掉 raw_titanium（精准采集掉自己）；
  ④ 世界生成：**"稀有度比黄金略高"** —— 与 client.jar 里原版金矿的实际数值对照算一遍；
  ⑤ 挖掘等级/标签：pickaxe、needs_iron_tool、c:ores|raw_materials|ingots/titanium；
  ⑥ 加工链的两端不在错的地方：**粗钛**不许有原版冶炼配方（本脚本查不了配方管理器，
     那部分由探针在服务端上验）；这里只核 JSON 层面没有多出 smelting/blasting 文件。
"""
import io
import json
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
RES = os.path.join(PROJ, "src", "main", "resources")
LANG = os.path.join(RES, "assets", "potato_s_t", "lang")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data", "potato_s_t")
CLIENT_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)


def load(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def jar_json(zf, name):
    return json.loads(zf.read(name).decode("utf-8"))


# ---------- ① 语言 ----------
print(u"== ① 四语言 ==")
langs = {c: load(os.path.join(LANG, c + ".json")) for c in ("zh_cn", "en_us", "ja_jp", "ru_ru")}
base = set(langs["zh_cn"])
for c, d in langs.items():
    # ⚠ 这里**不写死绝对值**：ZF48 收工时是 190，之后每加一批东西都会涨（§4.30 那两条假 FAIL）。
    #   真正的不变量是"四语言键集完全一致"，绝对数由 LangCheck（交付门）去报。
    check(len(d) == len(langs["zh_cn"]), u"%s 共 %d 键（与 zh_cn 一致）" % (c, len(d)))
    check(set(d) == base, u"%s 键集与 zh_cn 一致" % c)

EXPECT = {
    "block.potato_s_t.titanium_ore": {"zh_cn": u"钛矿", "en_us": u"Titanium Ore",
                                      "ja_jp": u"チタン鉱石", "ru_ru": u"Титановая руда"},
    "block.potato_s_t.deepslate_titanium_ore": {"zh_cn": u"深层钛矿", "en_us": u"Deepslate Titanium Ore",
                                                "ja_jp": u"深層岩のチタン鉱石",
                                                "ru_ru": u"Титановая руда в глубинном сланце"},
    "item.potato_s_t.raw_titanium": {"zh_cn": u"粗钛", "en_us": u"Raw Titanium",
                                     "ja_jp": u"粗チタン", "ru_ru": u"Необработанный титан"},
    "item.potato_s_t.titanium_powder": {"zh_cn": u"钛粉", "en_us": u"Titanium Dust",
                                        "ja_jp": u"チタン粉", "ru_ru": u"Титановая пыль"},
    "item.potato_s_t.titanium_ingot": {"zh_cn": u"钛锭", "en_us": u"Titanium Ingot",
                                       "ja_jp": u"チタンインゴット", "ru_ru": u"Титановый слиток"},
}
for key, table in EXPECT.items():
    for c, want in table.items():
        got = langs[c].get(key)
        check(got == want, u"%s / %s = %r" % (c, key, got))

names = {}
for k, v in langs["zh_cn"].items():
    if k.startswith(("item.potato_s_t.", "block.potato_s_t.")):
        names.setdefault(v, []).append(k)
allowed = {u"电力高炉"}
bad = {v: ks for v, ks in names.items() if len(ks) > 1 and v not in allowed}
check(not bad, u"中文显示名无意外重名")
if bad:
    for v, ks in bad.items():
        print(u"         !! %s -> %s" % (v, ks))

# ---------- ② 贴图全部借原版 ----------
print(u"\n== ② 贴图（用户指定：都借原版铁的，钛粉借火药）==")
WANT = {
    "block/titanium_ore": ("all", "minecraft:block/iron_ore"),
    "block/deepslate_titanium_ore": ("all", "minecraft:block/deepslate_iron_ore"),
    "item/raw_titanium": ("layer0", "minecraft:item/raw_iron"),
    "item/titanium_powder": ("layer0", "minecraft:item/gunpowder"),
    "item/titanium_ingot": ("layer0", "minecraft:item/iron_ingot"),
}
zf = zipfile.ZipFile(CLIENT_JAR)
jar_names = set(zf.namelist())
for model, (slot, tex) in WANT.items():
    p = os.path.join(ASSETS, "models", model + ".json")
    if not os.path.isfile(p):
        check(False, u"models/%s.json 存在" % model)
        continue
    got = load(p)["textures"][slot]
    check(got == tex, u"models/%s.json %s = %s" % (model, slot, got))
    path = tex.split(":", 1)[1]
    check("assets/minecraft/textures/{0}.png".format(path) in jar_names,
          u"原版贴图 textures/%s.png 在 client.jar 里" % path)
    check(not os.path.isfile(os.path.join(ASSETS, "textures", path + ".png")),
          u"（本项目没有重复造一张 %s.png —— 借的就是借的）" % path)

# ---------- ③ 掉落表 ----------
print(u"\n== ③ 掉落表 ==")
for ore, ore_id in (("titanium_ore", "potato_s_t:titanium_ore"),
                    ("deepslate_titanium_ore", "potato_s_t:deepslate_titanium_ore")):
    p = os.path.join(DATA, "loot_table", "blocks", ore + ".json")
    if not os.path.isfile(p):
        check(False, u"loot_table/blocks/%s.json 存在" % ore)
        continue
    d = load(p)
    kids = d["pools"][0]["entries"][0]["children"]
    check(kids[0]["name"] == ore_id, u"%s：精准采集掉自己" % ore)
    check(kids[1]["name"] == "potato_s_t:raw_titanium", u"%s：否则掉粗钛（%s）" % (ore, kids[1]["name"]))

# ---------- ④ 稀有度 vs 原版金矿 ----------
print(u"\n== ④ 「稀有度比黄金略高」——与原版金矿实算对照 ==")
gold_cfg = jar_json(zf, "data/minecraft/worldgen/configured_feature/ore_gold_buried.json")
gold_placed = jar_json(zf, "data/minecraft/worldgen/placed_feature/ore_gold.json")
gold_lower = jar_json(zf, "data/minecraft/worldgen/placed_feature/ore_gold_lower.json")
gold_size = gold_cfg["config"]["size"]
gold_discard = gold_cfg["config"]["discard_chance_on_air_exposure"]
gold_count = gold_placed["placement"][0]["count"]
gold_extra = gold_lower["placement"][0]["count"]["max_inclusive"]
gold_max = (gold_count + gold_extra) * gold_size

cfg = load(os.path.join(DATA, "worldgen", "configured_feature", "ore_titanium.json"))
placed = load(os.path.join(DATA, "worldgen", "placed_feature", "ore_titanium_placed.json"))
ti_size = cfg["config"]["size"]
ti_discard = cfg["config"]["discard_chance_on_air_exposure"]
ti_count = placed["placement"][0]["count"]
hr = [x for x in placed["placement"] if x["type"] == "minecraft:height_range"][0]["height"]
ti_max = ti_count * ti_size

print(u"  原版金矿：每区块 {0} 簇(+{1} 簇低位) × {2} 块 = 上限 {3} 块，空气丢弃率 {4}，高度 -64~32（梯形）".format(
    gold_count, gold_extra, gold_size, gold_max, gold_discard))
print(u"  钛矿    ：每区块 {0} 簇 × {1} 块 = 上限 {2} 块，空气丢弃率 {3}，高度 {4}~{5}（均匀）".format(
    ti_count, ti_size, ti_max, ti_discard, hr["min_inclusive"]["absolute"], hr["max_inclusive"]["absolute"]))
ratio = 1.0 - float(ti_max) / float(gold_max)
print(u"  ⇒ 钛矿上限比金矿少 {0:.0f}%（「略高」的量化口径）".format(ratio * 100))
check(ti_discard == gold_discard, u"空气丢弃率与金矿一致（{0}）—— 否则密度不可比".format(ti_discard))
check(0.10 <= ratio <= 0.35, u"比金矿稀 {0:.0f}%，落在「略高」的区间 10%~35%".format(ratio * 100))
check(cfg["config"]["targets"][0]["state"]["Name"] == "potato_s_t:titanium_ore", u"石头层 → 钛矿")
check(cfg["config"]["targets"][1]["state"]["Name"] == "potato_s_t:deepslate_titanium_ore", u"深板岩层 → 深层钛矿")
bm = load(os.path.join(DATA, "neoforge", "biome_modifier", "potato_st_ores.json"))
check("potato_s_t:ore_titanium_placed" in bm["features"], u"biome_modifier 挂上了（共 %d 条）" % len(bm["features"]))

# ---------- ⑤ 标签 ----------
print(u"\n== ⑤ 标签 ==")
for tag, want in (("needs_iron_tool", ["potato_s_t:titanium_ore", "potato_s_t:deepslate_titanium_ore"]),
                  ("mineable/pickaxe", ["potato_s_t:titanium_ore", "potato_s_t:deepslate_titanium_ore"])):
    vals = load(os.path.join(RES, "data", "minecraft", "tags", "block", tag + ".json"))["values"]
    for w in want:
        check(w in vals, u"#minecraft:%s 含 %s" % (tag, w))
TAGS = [("item", "ores/titanium", ["potato_s_t:titanium_ore", "potato_s_t:deepslate_titanium_ore"]),
        ("block", "ores/titanium", ["potato_s_t:titanium_ore", "potato_s_t:deepslate_titanium_ore"]),
        ("item", "raw_materials/titanium", ["potato_s_t:raw_titanium"]),
        ("item", "ingots/titanium", ["potato_s_t:titanium_ingot"]),
        ("item", "titanium_ingots", ["potato_s_t:titanium_ingot"])]
for reg, tag, want in TAGS:
    p = os.path.join(RES, "data", "c", "tags", reg, tag + ".json")
    if not os.path.isfile(p):
        check(False, u"data/c/tags/%s/%s.json 存在" % (reg, tag))
        continue
    vals = load(p)["values"]
    for w in want:
        check(w in vals, u"#c:%s（%s）含 %s" % (tag, reg, w))
check("potato_s_t:titanium_ingot" in load(os.path.join(RES, "data", "c", "tags", "item", "ingots.json"))["values"],
      u"钛锭也进了父标签 #c:ingots")

# ---------- ⑥ 不许有原版冶炼配方 ----------
print(u"\n== ⑥ 粗钛 / 钛粉 的配方文件（JSON 层面）==")
recipe_dir = os.path.join(DATA, "recipe")
raw_hits = []
powder_hits = []
for f in sorted(os.listdir(recipe_dir)):
    if not f.endswith(".json"):
        continue
    text = io.open(os.path.join(recipe_dir, f), encoding="utf-8").read()
    if "raw_titanium" in text:
        raw_hits.append(f)
    if "titanium_powder" in text:
        powder_hits.append(f)
check(raw_hits == [], u"没有任何 JSON 配方引用 raw_titanium（实际 %s）" % (raw_hits or u"无"))
check(powder_hits == [], u"没有任何 JSON 配方引用 titanium_powder（实际 %s）—— 它只能走电力高炉" % (powder_hits or u"无"))

print(u"\n------------------------------")
print(u"失败项 = %d" % len(fails))
print(u"结论: " + (u"通过" if not fails else u"有失败项"))
sys.exit(1 if fails else 0)
