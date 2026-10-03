# -*- coding: utf-8 -*-
"""_zf46_verify.py —— ZF46 的**独立**复核（只读）

规矩（§4.27 / §4.30）：期望值**手打第二遍**，不 import _zf46_lang.py 的表。
查 5 件事：
  ① 四语言键集一致、各 185 键（182 + 3）；
  ② 3 个新键的四语言值 = 手打的第二遍；中文显示名无重名；
  ③ 贴图 3 张、模型与 blockstate 各 3+2 份都在盘上，且 layer0/all 指向的贴图存在；
  ④ 掉落表：两张都指向 raw_tungsten（含精准采集分支）；
  ⑤ 世界生成：configured/placed 两份 JSON 的**数值**（size / count / 高度）与策划值一致，
     且 biome_modifier 里真的挂上了。
"""
import io
import json
import os
import sys

PROJ = r"E:\PotatoST"
RES = os.path.join(PROJ, "src", "main", "resources")
LANG = os.path.join(RES, "assets", "potato_s_t", "lang")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data", "potato_s_t")

fails = []


def check(cond, msg):
    print((u"  [OK]   " if cond else u"  [FAIL] ") + msg)
    if not cond:
        fails.append(msg)


def load(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read())


# ---------- ① 键集 ----------
print(u"== ① 四语言键集 ==")
langs = {c: load(os.path.join(LANG, c + ".json")) for c in ("zh_cn", "en_us", "ja_jp", "ru_ru")}
base = set(langs["zh_cn"])
for c, d in langs.items():
    # ⚠ 这里**不写死绝对值**：ZF46 收工时是 185，之后每加一批东西都会涨（§4.30）。
    #   真正的不变量是"四语言键集完全一致"，绝对数由 LangCheck（交付门）去报。
    check(len(d) == len(langs["zh_cn"]), u"%s 共 %d 键（与 zh_cn 一致）" % (c, len(d)))
    check(set(d) == base, u"%s 键集与 zh_cn 一致" % c)

# ---------- ② 新键（手打第二遍） ----------
print(u"\n== ② 新增 3 个键 ==")
EXPECT = {
    "block.potato_s_t.wolframite_ore": {
        "zh_cn": u"黑钨矿", "en_us": u"Wolframite Ore", "ja_jp": u"タングステン鉱石",
        "ru_ru": u"Вольфрамовая руда"},
    "block.potato_s_t.deepslate_wolframite_ore": {
        "zh_cn": u"深层黑钨矿", "en_us": u"Deepslate Wolframite Ore",
        "ja_jp": u"深層岩のタングステン鉱石", "ru_ru": u"Вольфрамовая руда в глубинном сланце"},
    "item.potato_s_t.raw_tungsten": {
        "zh_cn": u"粗钨", "en_us": u"Raw Tungsten", "ja_jp": u"粗タングステン",
        "ru_ru": u"Необработанный вольфрам"},
}
for key, table in EXPECT.items():
    for c, want in table.items():
        got = langs[c].get(key)
        check(got == want, u"%s / %s = %r" % (c, key, got))

names = {}
for k, v in langs["zh_cn"].items():
    if k.startswith(("item.potato_s_t.", "block.potato_s_t.")):
        names.setdefault(v, []).append(k)
allowed = {u"电力高炉"}          # 控制器与部件格故意同名
bad = {v: ks for v, ks in names.items() if len(ks) > 1 and v not in allowed}
check(not bad, u"中文显示名无意外重名（黑钨矿/粗钨都没撞）")
if bad:
    for v, ks in bad.items():
        print(u"         !! %s -> %s" % (v, ks))

# ---------- ③ 贴图 / 模型 / blockstate ----------
print(u"\n== ③ 贴图与模型 ==")
for tex in ("block/wolframite_ore.png", "block/deepslate_wolframite_ore.png", "item/raw_tungsten.png"):
    p = os.path.join(ASSETS, "textures", tex)
    ok = os.path.isfile(p)
    check(ok, u"textures/%s 存在（%d 字节）" % (tex, os.path.getsize(p) if ok else -1))
for name, layer_key, expect_tex in (
        ("block/wolframite_ore", "all", "potato_s_t:block/wolframite_ore"),
        ("block/deepslate_wolframite_ore", "all", "potato_s_t:block/deepslate_wolframite_ore"),
        ("item/raw_tungsten", "layer0", "potato_s_t:item/raw_tungsten")):
    p = os.path.join(ASSETS, "models", name + ".json")
    if not os.path.isfile(p):
        check(False, u"models/%s.json 存在" % name)
        continue
    tex = load(p)["textures"][layer_key]
    check(tex == expect_tex, u"models/%s.json %s = %s" % (name, layer_key, tex))
for name in ("wolframite_ore", "deepslate_wolframite_ore"):
    p = os.path.join(ASSETS, "blockstates", name + ".json")
    ok = os.path.isfile(p)
    check(ok, u"blockstates/%s.json 存在" % name)
    if ok:
        model = load(p)["variants"][""]["model"]
        check(model == "potato_s_t:block/" + name, u"blockstates/%s.json -> %s" % (name, model))
    p = os.path.join(ASSETS, "models", "item", name + ".json")
    ok = os.path.isfile(p)
    check(ok, u"models/item/%s.json（方块物品）存在" % name)
    if ok:
        check(load(p)["parent"] == "potato_s_t:block/" + name, u"models/item/%s.json 指向方块模型" % name)

# ---------- ④ 掉落表 ----------
print(u"\n== ④ 掉落表 ==")
for ore, ore_id in (("wolframite_ore", "potato_s_t:wolframite_ore"),
                    ("deepslate_wolframite_ore", "potato_s_t:deepslate_wolframite_ore")):
    p = os.path.join(DATA, "loot_table", "blocks", ore + ".json")
    if not os.path.isfile(p):
        check(False, u"loot_table/blocks/%s.json 存在" % ore)
        continue
    data = load(p)
    kids = data["pools"][0]["entries"][0]["children"]
    self_drop = kids[0]["name"]
    raw_drop = kids[1]["name"]
    check(self_drop == ore_id, u"%s：精准采集掉自己（%s）" % (ore, self_drop))
    check(raw_drop == "potato_s_t:raw_tungsten", u"%s：否则掉粗钨（%s）" % (ore, raw_drop))
    check(data["random_sequence"] == "potato_s_t:blocks/" + ore, u"%s：random_sequence 对得上" % ore)

# ---------- ⑤ 世界生成 ----------
print(u"\n== ⑤ 世界生成 ==")
cfg = load(os.path.join(DATA, "worldgen", "configured_feature", "ore_wolframite.json"))
check(cfg["type"] == "minecraft:ore", u"configured_feature type = minecraft:ore")
check(cfg["config"]["size"] == 4, u"矿脉大小 size = 4（实际 %s）" % cfg["config"]["size"])
targets = {t["target"]["tag"]: t["state"]["Name"] for t in cfg["config"]["targets"]}
check(targets.get("minecraft:stone_ore_replaceables") == "potato_s_t:wolframite_ore",
      u"石头层 -> 黑钨矿（%s）" % targets.get("minecraft:stone_ore_replaceables"))
check(targets.get("minecraft:deepslate_ore_replaceables") == "potato_s_t:deepslate_wolframite_ore",
      u"深板岩层 -> 深层黑钨矿（%s）" % targets.get("minecraft:deepslate_ore_replaceables"))

placed = load(os.path.join(DATA, "worldgen", "placed_feature", "ore_wolframite_placed.json"))
check(placed["feature"] == "potato_s_t:ore_wolframite", u"placed_feature 指向 configured")
kinds = [p["type"] for p in placed["placement"]]
check(kinds == ["minecraft:count", "minecraft:in_square", "minecraft:height_range", "minecraft:biome"],
      u"placement 四段齐全（%s）" % kinds)
count = [p for p in placed["placement"] if p["type"] == "minecraft:count"][0]["count"]
hr = [p for p in placed["placement"] if p["type"] == "minecraft:height_range"][0]["height"]
check(count == 6, u"每区块 6 簇（实际 %s）" % count)
check(hr["min_inclusive"]["absolute"] == -64 and hr["max_inclusive"]["absolute"] == 16,
      u"高度 -64~16（实际 %s~%s）" % (hr["min_inclusive"]["absolute"], hr["max_inclusive"]["absolute"]))

bm = load(os.path.join(DATA, "neoforge", "biome_modifier", "potato_st_ores.json"))
check("potato_s_t:ore_wolframite_placed" in bm["features"],
      u"biome_modifier 里挂上了（共 %d 条）" % len(bm["features"]))
check(bm["biomes"] == "#minecraft:is_overworld" and bm["step"] == "underground_ores",
      u"biome_modifier 的 biomes/step 没被动过")

# ---------- ⑥ 挖掘等级与 c: 标签 ----------
print(u"\n== ⑥ 标签 ==")
for tag, want in (("needs_iron_tool", ["potato_s_t:wolframite_ore", "potato_s_t:deepslate_wolframite_ore"]),
                  ("mineable/pickaxe", ["potato_s_t:wolframite_ore", "potato_s_t:deepslate_wolframite_ore"])):
    p = os.path.join(RES, "data", "minecraft", "tags", "block", tag + ".json")
    vals = load(p)["values"]
    for w in want:
        check(w in vals, u"#minecraft:%s 含 %s" % (tag, w))
for p, want in ((os.path.join(RES, "data", "c", "tags", "item", "ores", "tungsten.json"), "potato_s_t:wolframite_ore"),
                (os.path.join(RES, "data", "c", "tags", "item", "ores", "tungsten.json"), "potato_s_t:deepslate_wolframite_ore"),
                (os.path.join(RES, "data", "c", "tags", "block", "ores", "tungsten.json"), "potato_s_t:wolframite_ore"),
                (os.path.join(RES, "data", "c", "tags", "item", "raw_materials", "tungsten.json"), "potato_s_t:raw_tungsten")):
    if not os.path.isfile(p):
        check(False, u"存在 " + os.path.relpath(p, RES))
        continue
    check(want in load(p)["values"], u"%s 含 %s" % (os.path.relpath(p, RES).replace("\\", "/"), want))

print(u"\n------------------------------")
print(u"失败项 = %d" % len(fails))
print(u"结论: " + (u"通过" if not fails else u"有失败项"))
sys.exit(1 if fails else 0)
