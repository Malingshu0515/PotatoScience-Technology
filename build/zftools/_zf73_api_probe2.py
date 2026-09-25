# -*- coding: utf-8 -*-
u"""_zf73_api_probe2.py —— 只读：第二轮 API 取证（写完流体还差这几处）

1. `FluidType.Properties` 的**构造器方法名**（density/viscosity/canConvertToSource/... 到底叫什么）；
2. `IClientFluidTypeExtensions` 的渲染层/贴图方法名（`getRenderType` 存不存在、默认返回什么）；
3. 原版 `Blocks.WATER` 那条 `LiquidBlock` 的属性链（照抄一份最保险）；
4. 原版 `LavaFluid` 的流动参数（tick 30 / slope 2 / drop 2 到底写在哪）；
5. `BucketItem` 的拾取路径（确认不设 `.bucket()` 时原版空桶**拾不走**原油）。
"""
import glob
import os
import sys
import zipfile

PROJ = r"E:\PotatoST"
GRADLE = r"E:\gradle-home"

TARGETS = [
    (u"neoforge", u"net/neoforged/neoforge/fluids/FluidType.java",
     [u"public Properties ", u"public static Properties create"]),
    (u"neoforge", u"net/neoforged/neoforge/client/extensions/common/IClientFluidTypeExtensions.java",
     [u"getRenderType", u"getTintColor", u"getStillTexture", u"getFlowingTexture"]),
    (u"vanilla", u"net/minecraft/world/level/block/Blocks.java",
     [u"LiquidBlock(Fluids.WATER", u"LiquidBlock(Fluids.LAVA"]),
    (u"vanilla", u"net/minecraft/world/level/material/LavaFluid.java",
     [u"getTickDelay", u"getSlopeFindDistance", u"getDropOff", u"canConvertToSource",
      u"slopeFindDistance", u"levelDecreasePerBlock", u"tickRate"]),
    (u"vanilla", u"net/minecraft/world/item/BucketItem.java",
     [u"BucketPickup", u"getBucket", u"pickupBlock"]),
]


def find(patterns):
    hits = []
    for p in patterns:
        hits.extend(glob.glob(p, recursive=True))
    hits = [h for h in hits if os.path.isfile(h)]
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0] if hits else None


def ctx(lines, idx, before, after):
    lo = max(0, idx - before)
    hi = min(len(lines), idx + after + 1)
    for j in range(lo, hi):
        print(u"      %4d| %s" % (j + 1, lines[j].rstrip()[:150]))


def main():
    jars = {
        u"vanilla": find([os.path.join(PROJ, u"build", u"neoForm", u"**", u"sources.jar")]),
        u"neoforge": find([os.path.join(GRADLE, u"**", u"neoforge-*-sources.jar")]),
    }
    for kind, entry, needles in TARGETS:
        print(u"\n================ %s ================" % entry)
        path = jars.get(kind)
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
        count = 0
        for i, line in enumerate(lines):
            s = line.strip()
            if not s or s.startswith(u"*") or s.startswith(u"//") or s.startswith(u"/*"):
                continue
            if any(n in line for n in needles):
                count += 1
                if count > 14:
                    print(u"  ... (截断)")
                    break
                ctx(lines, i, 1, 1)
                print(u"      ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
