# -*- coding: utf-8 -*-
r"""_zf117_recipes.py —— 只读：把"候选节点"相关配方的**关键行**打出来，用于定父链

不改盘。输出 build\zftools\_zf117_recipes.txt
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
OUT = os.path.join(ROOT, r"build\zftools\_zf117_recipes.txt")

WANT = [
    "salt_dryer", "salt_decomposer", "fluid_pump", "fluid_exchanger", "oil_pump",
    "lithium_battery_plant", "lithium_battery", "lithium_battery_component",
    "star_steel_ingot", "starfall_pendant", "raw_vibranium", "star_steel_helmet",
    "star_steel_chestplate", "star_steel_leggings", "star_steel_boots",
    "titanium_helmet", "titanium_chestplate", "sea_salt", "sodium_chloride",
    "lithium_carbonate", "lithium_concentrate", "advanced_metal_block",
    "heat_resistant_metal_block", "thermal_metal", "photovoltaic_component",
    "silicon", "uranium_ingot", "magnet", "wrench", "toner",
]


def main():
    lines = []
    add = lines.append
    files = sorted(os.listdir(RDIR))
    add(u"# ZF117 配方速查（%d 份）" % len(files))
    for w in WANT:
        hits = []
        for fn in files:
            p = os.path.join(RDIR, fn)
            txt = io.open(p, encoding="utf-8").read()
            if u"potato_s_t:" + w in txt:
                hits.append((fn, txt))
        add(u"")
        add(u"## %s —— 出现在 %d 份配方里：%s" % (w, len(hits), u"、".join(h[0] for h in hits)))
        for fn, txt in hits:
            obj = json.loads(txt)
            kind = obj.get("type", u"?").replace("minecraft:", "").replace("potato_s_t:", "")
            add(u"")
            add(u"### %s  [%s]" % (fn, kind))
            if w in fn:
                add(u"```json")
                add(json.dumps(obj, ensure_ascii=False, indent=1))
                add(u"```")
            else:
                add(u"```")
                add(txt.strip())
                add(u"```")
    text = u"\n".join(lines) + u"\n"
    io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"报告 → %s（%d 行）" % (OUT, len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
