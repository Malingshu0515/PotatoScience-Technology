# -*- coding: utf-8 -*-
r"""_zf117_audit.py —— ZF117 开工前的只读盘点：**哪些机器/关键物品还没有进度节点**

只读，不改盘。输出到 build\zftools\_zf117_audit.txt（也打到 stdout）。

口径：
  · 「被引用」= 出现在任何 advancement JSON 的 **图标** 或 **判据物品** 里；
  · 引用集合由 advancement 目录现读，不写死；
  · 盘上注册的 id 由 java 现读（ModItems / ModBlocks / PotatoSTOres / ModArmorItems）；
  · 另附一份**人工分档**：机器 / 多方块 / 关键材料 三组，看各组里谁没被引用。
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ADIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang\zh_cn.json")
OUT = os.path.join(ROOT, r"build\zftools\_zf117_audit.txt")

# 人工分档：只列"值得给成就"的候选（机器 / 多方块 / 关键材料）
MACHINES = [
    "micro_crusher", "hydraulic_press", "wiring_block", "terminal", "low_generator",
    "generator", "solar_panel", "power_capturer", "electric_blast_furnace", "alloy_smelter",
    "electrolyzer", "air_separator", "ammonia_synthesis_chamber", "salt_dryer",
    "salt_decomposer", "hydrodesulfurization_chamber", "distillation_controller",
    "distillation_operator", "combustion_chamber", "acidic_reaction_chamber",
    "filling_machine", "fluid_pump", "fluid_exchanger", "oil_pump",
    "lithium_battery_plant", "lithium_battery",
]
MATERIALS = [
    "iron_powder", "carbon", "toner", "iron_plate", "copper_plate", "aluminum_plate",
    "nickel_plate", "cobalt_plate", "silver_plate", "steel_plate", "capacitor",
    "copper_wire", "copper_wire_spool", "power_cable_spool", "high_carbon_steel",
    "titanium_ingot", "light_titanium_alloy", "hard_titanium_alloy", "stable_metal_block",
    "advanced_metal_block", "heat_resistant_metal_block", "common_metal_block",
    "thermal_metal", "high_pressure_tank", "photovoltaic_component", "silicon",
    "sea_salt", "sodium_chloride", "lithium_carbonate", "lithium_concentrate",
    "lithium_battery_component", "star_steel_ingot", "star_steel_helmet",
    "star_steel_chestplate", "star_steel_leggings", "star_steel_boots",
    "starfall_pendant", "raw_vibranium", "uranium_ingot", "magnet", "wrench",
    "titanium_alloy_pickaxe", "titanium_alloy_sword", "oil_bucket", "diesel_bucket",
    "gasoline_bucket", "sulfur", "asphalt_block", "bitumen", "empty_spool",
]


def registered():
    ids = {}
    for f in ("ModItems.java", "ModBlocks.java", "PotatoSTOres.java", "ModArmorItems.java"):
        p = os.path.join(JAVA, f)
        if not os.path.exists(p):
            continue
        raw = io.open(p, encoding="utf-8").read()
        for m in re.finditer(r'register\(\s*"([a-z0-9_]+)"', raw):
            ids.setdefault(m.group(1), f)
    return ids


def referenced():
    ref = {}
    for name in sorted(os.listdir(ADIR)):
        if not name.endswith(".json"):
            continue
        p = os.path.join(ADIR, name)
        obj = json.loads(io.open(p, encoding="utf-8").read())
        node = name[:-5]
        got = set()
        icon = obj.get("display", {}).get("icon", {}).get("id", "")
        if icon.startswith("potato_s_t:"):
            got.add(icon.split(":", 1)[1])
        txt = io.open(p, encoding="utf-8").read()
        for m in re.finditer(r'"potato_s_t:([a-z0-9_]+)"', txt):
            got.add(m.group(1))
        for g in got:
            ref.setdefault(g, []).append(node)
    return ref


def lang():
    data = json.loads(io.open(LANG, encoding="utf-8").read())
    return data


def main():
    ids = registered()
    ref = referenced()
    L = lang()
    lines = []
    add = lines.append
    add(u"# ZF117 盘点：进度覆盖率（只读）")
    add(u"")
    add(u"盘上注册 id = %d（ModItems/ModBlocks/Ores/ArmorItems）" % len(ids))
    add(u"advancement 文件 = %d" % len([n for n in os.listdir(ADIR) if n.endswith(u".json")]))
    add(u"advancement 里被引用过的 mod id = %d" % len(ref))
    add(u"")

    def name(i):
        return L.get(u"item.potato_s_t." + i) or L.get(u"block.potato_s_t." + i) or u"?"

    add(u"## 一、机器组（%d）—— 谁没有节点" % len(MACHINES))
    add(u"")
    add(u"| id | 中文名 | 注册 | 被哪条进度引用 |")
    add(u"|---|---|---|---|")
    for i in MACHINES:
        who = u"、".join(sorted(set(ref.get(i, [])))) or u"**（无）**"
        add(u"| `%s` | %s | %s | %s |" % (i, name(i), u"有" if i in ids else u"**没注册**", who))
    add(u"")
    add(u"## 二、关键材料组（%d）—— 谁没有节点" % len(MATERIALS))
    add(u"")
    add(u"| id | 中文名 | 注册 | 被哪条进度引用 |")
    add(u"|---|---|---|---|")
    for i in MATERIALS:
        who = u"、".join(sorted(set(ref.get(i, [])))) or u"**（无）**"
        add(u"| `%s` | %s | %s | %s |" % (i, name(i), u"有" if i in ids else u"**没注册**", who))
    add(u"")
    add(u"## 三、被引用过的 id 全表（%d）" % len(ref))
    add(u"")
    for i in sorted(ref):
        add(u"- `%s`（%s） ← %s" % (i, name(i), u"、".join(sorted(set(ref[i])))))
    add(u"")
    text = u"\n".join(lines) + u"\n"
    io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(text)
    print(text)
    print(u"报告 → %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
