# -*- coding: utf-8 -*-
u"""_zf160_recon.py —— ZF160 侦察（只读）：9 种矿的矿脉大小 / 每区块次数 / 高度区间，与原版铜对照。

用户原话：「银矿矿脉可以稍微调大一点 大概和铜差不多（或者生成权重大一点也可以）然后铝的权重调小1~2」。

跑法：python build\\zftools\\_zf160_recon.py [--write]
"""
import io
import json
import os
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
WG = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\worldgen")
CFG = os.path.join(WG, "configured_feature")
PLC = os.path.join(WG, "placed_feature")
JAR = r"E:\gradle-home\caches\ng_execute\b618213606478f4c62e6974e895a173b103a054e4a7be1bf630f2feeb65c5c3b\client-extra.jar"
OUT = os.path.join(ROOT, r"build\zftools\_zf160_recon.txt")
ORES = ["aluminum", "cobalt", "nickel", "silver", "uranium", "manganese", "lithium",
        "wolframite", "titanium"]
LINES = []


def say(s):
    LINES.append(s)
    print(s)


def placement_summary(pl):
    count = None
    height = u""
    for step in pl:
        if step.get("type") == "minecraft:count":
            count = step.get("count")
        if step.get("type") == "minecraft:height_range":
            h = step.get("height", {})
            lo = h.get("min_inclusive", {})
            hi = h.get("max_inclusive", {})
            height = u"%s..%s（%s）" % (json.dumps(lo, ensure_ascii=False), json.dumps(hi, ensure_ascii=False),
                                       h.get("type", u"").split(":")[-1])
    return count, height


def main(argv):
    say(u"=========== ZF160 侦察：矿脉大小与次数 ===========")
    say(u"")
    say(u"%-12s %6s %8s  %s" % (u"矿", u"size", u"count", u"高度区间"))
    for name in ORES:
        cfg = json.loads(io.open(os.path.join(CFG, u"ore_%s.json" % name), encoding="utf-8").read())
        pl = json.loads(io.open(os.path.join(PLC, u"ore_%s_placed.json" % name), encoding="utf-8").read())
        c, h = placement_summary(pl.get("placement", []))
        say(u"%-12s %6s %8s  %s" % (name, cfg.get("config", {}).get("size"), c, h))

    say(u"")
    say(u"---- 原版对照（client-extra.jar 里现抠）----")
    z = zipfile.ZipFile(JAR)
    for label, cfgname, plcname in ((u"铜（小脉）", "ore_copper_small", "ore_copper"),
                                    (u"铜（大脉）", "ore_copper_large", "ore_copper_large"),
                                    (u"铁（小脉）", "ore_iron_small", "ore_iron_small"),
                                    (u"金", "ore_gold", "ore_gold")):
        c = json.loads(z.read(u"data/minecraft/worldgen/configured_feature/%s.json" % cfgname).decode("utf-8"))
        p = json.loads(z.read(u"data/minecraft/worldgen/placed_feature/%s.json" % plcname).decode("utf-8"))
        cnt, h = placement_summary(p.get("placement", []))
        say(u"%-12s %6s %8s  %s" % (label, c.get("config", {}).get("size"), cnt, h))

    say(u"")
    say(u"---- 铝那张图纸的原始内容（要看清楚改的是哪一处）----")
    say(io.open(os.path.join(PLC, u"ore_aluminum_placed.json"), encoding="utf-8").read())
    say(u"=========== 侦察完 ===========")
    if u"--write" in argv:
        io.open(OUT, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(LINES) + u"\n")
        print(u"（已写 %s）" % OUT)
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
