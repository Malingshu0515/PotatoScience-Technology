# -*- coding: utf-8 -*-
u"""_zf72_vanilla_evidence.py —— 把「原版事实」从原版/NeoForge 的 jar 里抠出来，落成证据文件

为什么要这一步：v0.11 规划里写了几个**原版事实**（岩浆湖地表概率 = 1/200、lake 特征的
barrier=石头、fluid 岩浆 level 0、NeoForge 21.1.235 没有原油通用标签、石岸水色 4159204），
这些不能靠记忆。本脚本每次从 jar 重新抠一遍并写
`build/zftools/_zf72_vanilla_evidence.json`；`_zf72_verify.py` 再拿**文档里的说法**与
这份证据逐条对齐 —— 哪天原版/NeoForge 换了版本，证据会变、校验会挂。

只读 jar，只写一个 json。
"""
import glob
import io
import json
import os
import sys
import zipfile

GRADLE = r"E:\gradle-home"
OUT = r"E:\PotatoST\build\zftools\_zf72_vanilla_evidence.json"

fails = []


def find_jar(pattern):
    hits = glob.glob(os.path.join(GRADLE, u"**", pattern), recursive=True)
    if not hits:
        return None
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0]


def read_entry(zf, name):
    try:
        return zf.read(name).decode("utf-8")
    except KeyError:
        return None


def main():
    client_extra = find_jar("client-extra.jar")
    neoforge_src = find_jar("neoforge-*-sources.jar")
    print(u"client-extra : %s" % client_extra)
    print(u"neoforge-src : %s" % neoforge_src)
    if client_extra is None or neoforge_src is None:
        print(u"!! 找不到 jar，无法取证")
        return 1

    ev = {
        "generated_by": "_zf72_vanilla_evidence.py",
        "client_extra_jar": client_extra,
        "neoforge_sources_jar": neoforge_src,
    }

    # ---------- 原版地表岩浆湖 ----------
    with zipfile.ZipFile(client_extra) as zf:
        surf_txt = read_entry(zf, u"data/minecraft/worldgen/placed_feature/lake_lava_surface.json")
        lake_txt = read_entry(zf, u"data/minecraft/worldgen/configured_feature/lake_lava.json")
        stony_txt = read_entry(zf, u"data/minecraft/worldgen/biome/stony_shore.json")
        ocean_txt = read_entry(zf, u"data/minecraft/worldgen/biome/ocean.json")
    if surf_txt is None or lake_txt is None or stony_txt is None or ocean_txt is None:
        print(u"!! 原版 json 取不到（版本变了？）")
        return 1

    surf = json.loads(surf_txt)
    lake = json.loads(lake_txt)
    stony = json.loads(stony_txt)
    ocean = json.loads(ocean_txt)

    rarity = None
    for mod in surf.get("placement", []):
        if mod.get("type") == u"minecraft:rarity_filter":
            rarity = mod.get("chance")
    ev["lake_lava_surface"] = {
        "feature": surf.get("feature"),
        "rarity_chance": rarity,
        "placement_types": [m.get("type") for m in surf.get("placement", [])],
    }
    cfg = lake.get("config", {})
    fluid_state = cfg.get(u"fluid", {}).get(u"state", {})
    barrier_state = cfg.get(u"barrier", {}).get(u"state", {})
    ev["lake_lava_config"] = {
        "type": lake.get("type"),
        "barrier": barrier_state.get(u"Name"),
        "fluid": fluid_state.get(u"Name"),
        "fluid_level": fluid_state.get(u"Properties", {}).get(u"level"),
    }
    ev["stony_shore"] = {"water_color": stony.get("effects", {}).get("water_color"),
                         "temperature": stony.get("temperature")}
    ev["ocean"] = {"water_color": ocean.get("effects", {}).get("water_color")}

    # ---------- 用户给的水色 4047AD ----------
    ev["oilfield_water_color"] = {
        "hex_from_user": u"4047AD",
        "dec": int(u"4047AD", 16),
    }

    # ---------- NeoForge 有没有原油通用标签 ----------
    with zipfile.ZipFile(neoforge_src) as zf:
        tags_txt = read_entry(zf, u"net/neoforged/neoforge/common/Tags.java")
    if tags_txt is None:
        print(u"!! Tags.java 取不到")
        return 1
    needles = [u"crude_oil", u"CRUDE_OIL", u"crudeOil", u"oil"]
    hits = []
    for i, line in enumerate(tags_txt.split(u"\n"), 1):
        low = line.lower()
        for n in needles:
            if n.lower() in low:
                hits.append({"line": i, "text": line.strip()[:160]})
                break
    ev["neoforge_tags_java"] = {
        "path": u"net/neoforged/neoforge/common/Tags.java",
        "oil_hits": hits,
        "oil_tag_present": len(hits) > 0,
    }

    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(ev, ensure_ascii=False, indent=2, sort_keys=True))

    print(u"\n--- 取证结果 ---")
    print(u"地表岩浆湖 rarity chance = %s" % ev["lake_lava_surface"]["rarity_chance"])
    print(u"lake 配置: barrier=%s fluid=%s level=%s"
          % (ev["lake_lava_config"]["barrier"], ev["lake_lava_config"]["fluid"],
             ev["lake_lava_config"]["fluid_level"]))
    print(u"石岸水色 = %s   海洋水色 = %s" % (ev["stony_shore"]["water_color"], ev["ocean"]["water_color"]))
    print(u"4047AD 十进制 = %s" % ev["oilfield_water_color"]["dec"])
    print(u"NeoForge Tags.java 命中 oil 的行数 = %d" % len(hits))
    print(u"证据文件: %s  (%d B)" % (OUT, os.path.getsize(OUT)))
    for f in fails:
        print(u"  !! " + f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
