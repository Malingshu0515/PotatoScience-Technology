# -*- coding: utf-8 -*-
u"""_zf73_api_probe.py —— 只读：把本轮要用的 API 签名从 jar 里当场抠出来

不靠记忆写 NeoForge 的 `FluidType.Properties` / `BaseFlowingFluid.Properties` 方法名，
以及原版 `LiquidBlock` 构造器、`FlowingFluid` 的流动参数方法。
输入：`build/neoForm/.../sources.jar`（打过补丁的原版源码）+ `neoforge-*-sources.jar`。
"""
import glob
import io
import os
import re
import sys
import zipfile

PROJ = r"E:\PotatoST"
GRADLE = r"E:\gradle-home"

TARGETS = [
    (u"vanilla", u"net/minecraft/world/level/block/LiquidBlock.java",
     [u"public LiquidBlock", u"protected final", u"FlowingFluid", u"class LiquidBlock"]),
    (u"vanilla", u"net/minecraft/world/level/material/FlowingFluid.java",
     [u"abstract", u"getSlopeFindDistance", u"getDropOff", u"getTickDelay", u"canConvertToSource",
      u"protected int", u"public int"]),
    (u"neoforge", u"net/neoforged/neoforge/fluids/BaseFlowingFluid.java",
     [u"public Properties", u"tickRate", u"slopeFindDistance", u"levelDecreasePerBlock",
      u"block(", u"bucket(", u"blastResistance", u"public int", u"public float"]),
    (u"neoforge", u"net/neoforged/neoforge/fluids/FluidType.java",
     [u"public Properties", u"canConvertToSource", u"canHydrate", u"canDrown", u"canSwim",
      u"canPushEntity", u"canExtinguish", u"supportsBoating", u"density", u"viscosity",
      u"temperature", u"lightLevel", u"luminosity", u"public boolean can", u"public int get"]),
]


def find(patterns):
    hits = []
    for p in patterns:
        hits.extend(glob.glob(p, recursive=True))
    hits = [h for h in hits if os.path.isfile(h)]
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0] if hits else None


def main():
    vanilla = find([os.path.join(PROJ, u"build", u"neoForm", u"**", u"sources.jar")])
    neoforge = find([os.path.join(GRADLE, u"**", u"neoforge-*-sources.jar")])
    print(u"vanilla sources : %s" % vanilla)
    print(u"neoforge sources: %s" % neoforge)
    jars = {u"vanilla": vanilla, u"neoforge": neoforge}

    for kind, entry, needles in TARGETS:
        path = jars.get(kind)
        print(u"\n================ %s ================" % entry)
        if not path:
            print(u"  (缺 jar)")
            continue
        with zipfile.ZipFile(path) as zf:
            try:
                text = zf.read(entry).decode("utf-8", "replace")
            except KeyError:
                print(u"  (jar 里没有这个条目)")
                continue
        lines = text.split(u"\n")
        printed = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(u"*") or stripped.startswith(u"//"):
                continue
            if any(n in line for n in needles):
                print(u"  %4d| %s" % (i, stripped[:150]))
                printed += 1
                if printed >= 60:
                    print(u"  ... (截断)")
                    break
    return 0


if __name__ == "__main__":
    sys.exit(main())
