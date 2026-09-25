# -*- coding: utf-8 -*-
u"""_zf75_worldgen.py —— ZF75 全部数据文件：地表油田（mini_oilfield）+ 海洋油田群系 + 三处接线

写 6 份新 JSON（配置特征 / 放置特征 / 3 份群系注入器 / 群系）+ 补 3 份世界预设 + is_overworld 标签 + 四语言。
每处"改老文件"的替换都断言「正好命中 1 次」，不中就整篇不写。
"""
import io
import json
import os
import sys

PROJ = r"E:\PotatoST"
RES = os.path.join(PROJ, u"src", u"main", u"resources")
DATA = os.path.join(RES, u"data", u"potato_s_t")
PRESETS = os.path.join(RES, u"data", u"minecraft", u"worldgen", u"world_preset")
LANG = os.path.join(RES, u"assets", u"potato_s_t", u"lang")

NEW_FILES = {}

# ① 配置特征：原版 minecraft:lake，barrier=石头、fluid=原油（level 0 = 源方块）
NEW_FILES[os.path.join(DATA, u"worldgen", u"configured_feature", u"mini_oilfield.json")] = {
    u"type": u"minecraft:lake",
    u"config": {
        u"barrier": {u"type": u"minecraft:simple_state_provider",
                     u"state": {u"Name": u"minecraft:stone"}},
        u"fluid": {u"type": u"minecraft:simple_state_provider",
                   u"state": {u"Name": u"potato_s_t:crude_oil",
                              u"Properties": {u"level": u"0"}}},
    },
}

# ② 放置特征：与"地表岩浆湖"逐项对齐（rarity 200 / in_square / 地表高度图 / biome 过滤）
NEW_FILES[os.path.join(DATA, u"worldgen", u"placed_feature", u"mini_oilfield_placed.json")] = {
    u"feature": u"potato_s_t:mini_oilfield",
    u"placement": [
        {u"type": u"minecraft:rarity_filter", u"chance": 200},
        {u"type": u"minecraft:in_square"},
        {u"type": u"minecraft:heightmap", u"heightmap": u"WORLD_SURFACE_WG"},
        {u"type": u"minecraft:biome"},
    ],
}

OIL_PLACED = u"potato_s_t:mini_oilfield_placed"

# ③ 群系注入器：基础 1 份（全主世界）+ 沙漠/恶地各追加 2 份 ⇒ 沙漠恶地 = 3 倍（用户要求）
NEW_FILES[os.path.join(DATA, u"neoforge", u"biome_modifier", u"mini_oilfield.json")] = {
    u"type": u"neoforge:add_features",
    u"biomes": u"#minecraft:is_overworld",
    u"features": [OIL_PLACED],
    u"step": u"lakes",
}
for tag in (u"a", u"b"):
    NEW_FILES[os.path.join(DATA, u"neoforge", u"biome_modifier",
                           u"mini_oilfield_desert_%s.json" % tag)] = {
        u"type": u"neoforge:add_features",
        u"biomes": [u"#minecraft:is_desert", u"#minecraft:is_badlands"],
        u"features": [OIL_PLACED],
        u"step": u"lakes",
    }

# ④ 海洋油田群系：以石岸为底 + 海草/海带；水色 4047AD = 4212653（用户指定）
STONY_FEATURES = [
    [], [u"minecraft:lake_lava_underground", u"minecraft:lake_lava_surface"],
    [u"minecraft:amethyst_geode"], [u"minecraft:monster_room", u"minecraft:monster_room_deep"],
    [], [],
    [u"minecraft:ore_dirt", u"minecraft:ore_gravel", u"minecraft:ore_granite_upper",
     u"minecraft:ore_granite_lower", u"minecraft:ore_diorite_upper", u"minecraft:ore_diorite_lower",
     u"minecraft:ore_andesite_upper", u"minecraft:ore_andesite_lower", u"minecraft:ore_tuff",
     u"minecraft:ore_coal_upper", u"minecraft:ore_coal_lower", u"minecraft:ore_iron_upper",
     u"minecraft:ore_iron_middle", u"minecraft:ore_iron_small", u"minecraft:ore_gold",
     u"minecraft:ore_gold_lower", u"minecraft:ore_redstone", u"minecraft:ore_redstone_lower",
     u"minecraft:ore_diamond", u"minecraft:ore_diamond_medium", u"minecraft:ore_diamond_large",
     u"minecraft:ore_diamond_buried", u"minecraft:ore_lapis", u"minecraft:ore_lapis_buried",
     u"minecraft:ore_copper", u"minecraft:underwater_magma", u"minecraft:disk_sand",
     u"minecraft:disk_clay", u"minecraft:disk_gravel"],
    [],
    [u"minecraft:spring_water", u"minecraft:spring_lava"],
    [u"minecraft:glow_lichen", u"minecraft:flower_default", u"minecraft:patch_grass_badlands",
     u"minecraft:brown_mushroom_normal", u"minecraft:red_mushroom_normal",
     u"minecraft:patch_sugar_cane", u"minecraft:patch_pumpkin",
     u"minecraft:seagrass_normal", u"minecraft:kelp_cold"],
    [u"minecraft:freeze_top_layer"],
]
MONSTERS = [
    {u"type": u"minecraft:spider", u"weight": 100, u"minCount": 4, u"maxCount": 4},
    {u"type": u"minecraft:zombie", u"weight": 95, u"minCount": 4, u"maxCount": 4},
    {u"type": u"minecraft:zombie_villager", u"weight": 5, u"minCount": 1, u"maxCount": 1},
    {u"type": u"minecraft:skeleton", u"weight": 100, u"minCount": 4, u"maxCount": 4},
    {u"type": u"minecraft:creeper", u"weight": 100, u"minCount": 4, u"maxCount": 4},
    {u"type": u"minecraft:slime", u"weight": 100, u"minCount": 4, u"maxCount": 4},
    {u"type": u"minecraft:enderman", u"weight": 10, u"minCount": 1, u"maxCount": 4},
    {u"type": u"minecraft:witch", u"weight": 5, u"minCount": 1, u"maxCount": 1},
    {u"type": u"minecraft:drowned", u"weight": 5, u"minCount": 1, u"maxCount": 1},
]
NEW_FILES[os.path.join(DATA, u"worldgen", u"biome", u"ocean_oilfield.json")] = {
    u"temperature": 0.5,
    u"downfall": 0.5,
    u"has_precipitation": True,
    u"effects": {
        u"sky_color": 8233727,
        u"fog_color": 12638463,
        u"water_color": 4212653,
        u"water_fog_color": 329011,
        u"mood_sound": {u"sound": u"minecraft:ambient.cave", u"tick_delay": 6000,
                        u"block_search_extent": 8, u"offset": 2.0},
    },
    u"spawners": {
        u"ambient": [{u"type": u"minecraft:bat", u"weight": 10, u"minCount": 8, u"maxCount": 8}],
        u"axolotls": [], u"creature": [], u"misc": [], u"monster": MONSTERS,
        u"underground_water_creature": [{u"type": u"minecraft:glow_squid", u"weight": 10,
                                         u"minCount": 4, u"maxCount": 6}],
        u"water_ambient": [{u"type": u"minecraft:cod", u"weight": 10, u"minCount": 3, u"maxCount": 6}],
        u"water_creature": [{u"type": u"minecraft:squid", u"weight": 1, u"minCount": 1, u"maxCount": 4}],
    },
    u"spawn_costs": {},
    u"carvers": {u"air": [u"minecraft:cave", u"minecraft:cave_extra_underground", u"minecraft:canyon"]},
    u"features": STONY_FEATURES,
}

BIOME_NAME = {
    u"zh_cn.json": u"海洋油田",
    u"en_us.json": u"Ocean Oilfield",
    u"ja_jp.json": u"海洋油田",
    u"ru_ru.json": u"Морское нефтяное месторождение",
}

fails = []


def write_new():
    for path, payload in NEW_FILES.items():
        folder = os.path.dirname(path)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text + u"\n")
        print(u"  [写出] %s" % os.path.relpath(path, PROJ))


def patch(path, old, new, label):
    text = io.open(path, "r", encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        fails.append(u"%s：锚点命中 %d 次" % (label, n))
        print(u"  !! %s：锚点命中 %d 次" % (label, n))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(text.replace(old, new, 1))
    print(u"  [补丁] %s" % label)


def main():
    write_new()
    # 世界预设：三个都加两个可选字段（旧存档靠 Java 侧默认值兜底）
    for name in (u"normal.json", u"amplified.json", u"large_biomes.json"):
        patch(os.path.join(PRESETS, name),
              u'          "chance": 0.75\n',
              u'          "chance": 0.75,\n'
              u'          "oil_biome": "potato_s_t:ocean_oilfield",\n'
              u'          "oil_chance": 0.15\n',
              u"世界预设 %s 加 oil_biome/oil_chance" % name)
    # is_overworld：新群系要能生成矿石/特征
    patch(os.path.join(RES, u"data", u"minecraft", u"tags", u"worldgen", u"biome", u"is_overworld.json"),
          u'    "potato_s_t:salty_river"\n',
          u'    "potato_s_t:salty_river",\n    "potato_s_t:ocean_oilfield"\n',
          u"is_overworld 追加海洋油田")
    # 四语言：群系名（插在 block.potato_s_t.crude_oil 那行之后；锚点必须正好 1 次）
    for name, value in BIOME_NAME.items():
        path = os.path.join(LANG, name)
        text = io.open(path, "r", encoding="utf-8").read()
        anchor = u'"block.potato_s_t.crude_oil"'
        if text.count(anchor) != 1:
            fails.append(u"语言 %s 锚点命中 %d 次" % (name, text.count(anchor)))
            print(u"  !! 语言 %s 锚点命中 %d 次" % (name, text.count(anchor)))
            continue
        line = u'  "biome.potato_s_t.ocean_oilfield":  "%s",\n' % value
        if line in text:
            print(u"  [SKIP] %s 已有群系键" % name)
            continue
        idx = text.index(anchor)
        eol = text.index(u"\n", idx) + 1
        text = text[:eol] + line + text[eol:]
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
        data = json.loads(text)
        print(u"  [补丁] 语言 %s +biome 键（共 %d 键）" % (name, len(data)))
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
