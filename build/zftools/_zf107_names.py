import json
ids=["micro_crusher","iron_powder","carbon","iron_plate","copper_plate","aluminum_plate","terminal","wiring_block","low_generator","generator","power_capturer","capacitor","heater","heat_sink","common_metal_block","thermal_metal","electric_blast_furnace","high_carbon_steel","titanium_ingot","titanium_powder","raw_titanium","electrolyzer","high_pressure_tank","filling_machine","alloy_smelter","light_titanium_alloy","hard_titanium_alloy","nickel_ingot","silver_ingot","aluminum_ingot","stable_metal_block","gold_block","titanium_alloy_pickaxe","titanium_alloy_sword","oil_bucket","crude_oil","distillation_controller","diesel_bucket","gasoline_bucket","sulfur","bitumen","hydrodesulfurization_chamber","ammonia_synthesis_chamber","air_separator","nitrogen","oxygen","hydrogen","ammonia","combustion_chamber","acidic_reaction_chamber","carbon_dioxide","music_disc_anvil_of_the_republic","anvil","redstone","stick","copper_wire_spool","power_cable_spool","sea_salt","silicon","photovoltaic_component","solar_panel"]
L={f:json.load(open("src/main/resources/assets/potato_s_t/lang/%s.json"%f,encoding="utf-8")) for f in ["zh_cn","en_us","ja_jp","ru_ru"]}
def look(i):
    for pre in ("block.potato_s_t.","item.potato_s_t.","fluid_type.potato_s_t."):
        if pre+i in L["en_us"]:
            return [L[f].get(pre+i,"?") for f in ("zh_cn","en_us","ja_jp","ru_ru")]
    return None
for i in ids:
    r=look(i)
    print("%-34s %s" % (i, " | ".join(r) if r else "**NO LANG**"))
