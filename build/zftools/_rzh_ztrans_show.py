# -*- coding: utf-8 -*-
"""Print side-by-side zh vs four locales for the keys the user rewrote, so the
tone/coverage can be eyeballed as a finished product rather than as a diff."""
import io
import json
import os

LANG = r"E:\PotatoST\src\main\resources\assets\potato_s_t\lang"
OUT = r"E:\PotatoST\build\zftools\_rzh_ztrans_show.txt"

SHOW = [
    "tooltip.potato_s_t.power_capturer",
    "tooltip.potato_s_t.high_pressure_tank.hydrogen_risk",
    "tooltip.potato_s_t.electrolyzer",
    "tooltip.potato_s_t.solar_panel",
    "tooltip.potato_s_t.micro_crusher",
    "tooltip.potato_s_t.electric_blast_furnace",
    "advancements.potato_s_t.first_power.description",
    "advancements.potato_s_t.capacitor.title",
    "advancements.potato_s_t.capacitor.description",
    "advancements.potato_s_t.crushing.description",
    "advancements.potato_s_t.acid.description",
    "advancements.potato_s_t.electrolyzer.description",
    "advancements.potato_s_t.salt.description",
    "advancements.potato_s_t.fluid_logistics.description",
    "advancements.potato_s_t.star_steel_slash.description",
    "advancements.potato_s_t.star_chart_tome.title",
    "advancements.potato_s_t.star_chart_tome.description",
    "advancements.potato_s_t.vibranium_armor.description",
    "advancements.potato_s_t.music_disc_anvil.title",
    "advancements.potato_s_t.music_disc_anvil.description",
    "advancements.potato_s_t.music_disc_jasmine.description",
    "advancements.potato_s_t.lithium_battery_plant.description",
    "advancements.potato_s_t.lithium_battery.description",
    "advancements.potato_s_t.fuel.description",
    "advancements.potato_s_t.hard_alloy.description",
    "advancements.potato_s_t.light_alloy.description",
    "advancements.potato_s_t.wiring.description",
    "advancements.potato_s_t.star_steel_tools.title",
    "advancements.potato_s_t.star_steel_tools.description",
    "advancements.potato_s_t.blast_furnace.description",
    "advancements.potato_s_t.distillation.title",
    "advancements.potato_s_t.distillation.description",
    "advancements.potato_s_t.steel.description",
    "advancements.potato_s_t.stable_block.description",
    "advancements.potato_s_t.pressing.description",
    "advancements.potato_s_t.salt.title",
    "advancements.potato_s_t.alloy_smelter.description",
    "advancements.potato_s_t.star_steel.description",
    "item.potato_s_t.wrench",
    "tooltip.potato_s_t.hold_shift",
    "message.potato_s_t.starfall.locked",
]

d = dict((l, json.load(io.open(os.path.join(LANG, l + ".json"), encoding="utf-8")))
         for l in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"))

L = []
for k in SHOW:
    L.append("# " + k)
    for l in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"):
        L.append("  %-6s %s" % (l, d[l].get(k, "<MISSING>").replace("\n", "\\n")))
    L.append("")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("wrote", OUT)
