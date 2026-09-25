# -*- coding: utf-8 -*-
u"""_zf73_api_probe3.py —— 只读：最后一批 API 取证（密度/黏度/亮度、方块属性 liquid()、bucket 默认值）"""
import glob
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
GRADLE = r"E:\gradle-home"

TARGETS = [
    (u"neoforge", u"net/neoforged/neoforge/fluids/FluidType.java",
     [u"public Properties density", u"public Properties viscosity", u"public Properties temperature",
      u"public Properties lightLevel", u"public Properties rarity", u"public Properties canConvertToSource"]),
    (u"neoforge", u"net/neoforged/neoforge/fluids/BaseFlowingFluid.java",
     [u"Supplier<? extends Item> bucket", u"getBucket", u"Supplier<? extends LiquidBlock> block",
      u"getBlock", u"explosionResistance"]),
    (u"vanilla", u"net/minecraft/world/level/block/state/BlockBehaviour.java",
     [u"public Properties liquid", u"public Properties noLootTable", u"public Properties replaceable"]),
    (u"vanilla", u"net/minecraft/world/level/block/Blocks.java",
     [u"new LiquidBlock(", u"LiquidBlock("]),
]


def find(patterns):
    hits = []
    for p in patterns:
        hits.extend(glob.glob(p, recursive=True))
    hits = [h for h in hits if os.path.isfile(h)]
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0] if hits else None


def main():
    jars = {
        u"vanilla": find([os.path.join(PROJ, u"build", u"neoForm", u"**", u"sources.jar")]),
        u"neoforge": find([os.path.join(GRADLE, u"**", u"neoforge-*-sources.jar")]),
    }
    for kind, entry, needles in TARGETS:
        print(u"\n================ %s ================" % entry)
        path = jars.get(kind)
        lines = []
        if path:
            with zipfile.ZipFile(path) as zf:
                try:
                    lines = zf.read(entry).decode("utf-8", "replace").split(u"\n")
                except KeyError:
                    print(u"  (jar 里没有这个条目)")
                    continue
        count = 0
        for i, line in enumerate(lines):
            s = line.strip()
            if not s or s.startswith(u"*") or s.startswith(u"//") or s.startswith(u"/*"):
                continue
            if any(n in line for n in needles):
                count += 1
                if count > 10:
                    print(u"  ... (截断)")
                    break
                for j in range(max(0, i - 1), min(len(lines), i + 2)):
                    print(u"      %4d| %s" % (j + 1, lines[j].rstrip()[:140]))
                print(u"      ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
