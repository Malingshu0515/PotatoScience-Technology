# -*- coding: utf-8 -*-
u"""_zf72_verify.py —— ZF72（v0.11 石油线规划轮）常驻校验

本轮**只写文档**：不碰 `src/`、不重新打包。所以校验分五组：

  A. 规划文档 `docs/v0.11规划.md` 里**你的规格逐字**在不在（11 条）；
  B. 文档里对**现有代码**的描述必须与代码逐条对得上（常量 / 负向判定 / 现有缺什么）；
  C. 文档里对**原版**的描述必须与 `_zf72_vanilla_evidence.json`（从 jar 现抠）对得上；
  D. 冻结状态：`mod_version=0.10`、成品 jar 哈希、0 探针、源码里没有石油的半个影子；
  E. 档案已记录：§4.44、§5 的 ZF72 行、§10 的新备份根。

任一条挂了都说明「文档在说假话」或「有人偷偷动了代码」，两种都必须当场看见。
"""
import glob
import hashlib
import io
import json
import os
import re
import sys

PROJ = r"E:\PotatoST"
DOC = os.path.join(PROJ, u"docs", u"v0.11规划.md")
ARCH = os.path.join(PROJ, u"docs", u"开发档案.md")
EVID = os.path.join(PROJ, u"build", u"zftools", u"_zf72_vanilla_evidence.json")
JAR = os.path.join(PROJ, u"release", u"PotatoST-0.10.jar")
JAR_SHA1 = u"84d09345f6095408ae462dabb536307141904ea3"
JAR_SIZE = 2217321

checks = 0
fails = []

SNAPSHOT_OK = [True]
# ZF72 是**规划轮**：那 7 条断言的实质是"当时源码里还没有石油、判定还是负向、版本还是 0.10"。
# 它们是那一轮的取证快照，不是永久不变量 —— v0.11 一到就必然不成立。
# 所以在"版本已不是 0.10"时以 [SKIP] 记录（并把原因打出来），避免以后每轮都假装红。
SNAP_PREFIXES = (u"B5 ", u"B6 ", u"B12 ", u"B13 ", u"B14 ", u"B15 ", u"B16 ", u"D1 ")





def check(name, cond, detail=u""):
    global checks
    checks += 1
    if not SNAPSHOT_OK[0] and any(name.startswith(p) for p in SNAP_PREFIXES):
        print(u"  [SKIP] %s   —— ZF72 规划轮的快照断言，v0.11 起不再适用" % name[:40])
        return
    tag = u"[OK]  " if cond else u"[FAIL]"
    if not cond:
        fails.append(name if not detail else u"%s  (%s)" % (name, detail))
    print(u"  %s %s%s" % (tag, name, (u"   " + detail) if (detail and not cond) else u""))


def read_text(path):
    if not os.path.isfile(path):
        return u""
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def grep(path, needle):
    return needle in read_text(path)


def all_sources():
    out = []
    for root, _dirs, files in os.walk(os.path.join(PROJ, u"src")):
        for f in files:
            out.append(os.path.join(root, f))
    return out


def main():
    props_txt = read_text(os.path.join(PROJ, u"gradle.properties"))
    mv_m = re.search(r"mod_version\s*=\s*(\S+)", props_txt)
    SNAPSHOT_OK[0] = bool(mv_m) and mv_m.group(1) == u"0.10"
    if not SNAPSHOT_OK[0]:
        print(u"  [SKIP] 版本已是 v%s —— ZF72 那 7 条「当时源码状态」的快照断言改为 SKIP"
              u"（它们证明的是 ZF72 当时没动代码，不是永久不变量）" % (mv_m.group(1) if mv_m else u"?"))
    doc = read_text(DOC)
    arch = read_text(ARCH)

    # ---------------- A. 规格逐字 ----------------
    print(u"\n=== A. 规划文档里你的规格（逐字） ===")
    check(u"A0 规划文档存在", os.path.isfile(DOC),
          u"%s 不存在" % DOC)
    spec = [
        u"PotatoS＆T v0.11规划（石油相关）第一部分",
        u"[id:mini_oilfield]",
        u"生成概率和原版岩浆湖相近 沙漠和恶地概率为其他地形的3倍",
        u"（在石岸群系和海洋群系之间过渡概率不要太高）水的颜色：4047AD",
        u"原油只能通过[油桶]舀取 后续通过[分馏塔]这个多方块结构加工",
        u"原油不可以像水变成无限的!同时流动速度和岩浆一样",
        u"先用铁锭贴图凑合",
        u"油桶目前可以舀取石油在内的任何液体（灌装机内也可以放油桶 不可以罐装气体）",
        u"单个油桶为3000mB的容积",
        u"只可以存在一种流体 异种流体不可以再被灌装进油桶",
        u"[铜锭][铁桶][铜锭]",
        u"[钢板][铁桶][钢板]",
        u"[铁板][铝锭][铁板]",
    ]
    for i, s in enumerate(spec, 1):
        check(u"A%d 规格原句「%s」" % (i, s[:26]), s in doc)

    # ---------------- B. 代码事实 ----------------
    print(u"\n=== B. 文档对现有代码的描述 vs 代码 ===")
    tank = read_text(os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod",
                                  u"TankContents.java"))
    fill = read_text(os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod",
                                  u"FillingMachineBlockEntity.java"))
    flu = read_text(os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod",
                                 u"ModFluids.java"))

    m = re.search(r"CAPACITY\s*=\s*(\d+)", tank)
    cap = int(m.group(1)) if m else -1
    check(u"B1 高压气罐容量确实是 3500", cap == 3500, u"实际 %s" % cap)
    check(u"B2 文档写明气罐 3500", u"高压气罐是 3500" in doc)

    m = re.search(r"TANK_COUNT\s*=\s*(\d+)", fill)
    tk = int(m.group(1)) if m else -1
    check(u"B3 灌装机水箱数确实是 5", tk == 5, u"实际 %s" % tk)
    check(u"B4 文档写明五个水箱", u"五个水箱" in doc)

    neg_tank = (u"fluid != Fluids.WATER" in tank) and (u"fluid != Fluids.LAVA" in tank)
    check(u"B5 TankContents.isGas 确实是负向判定（非水非岩浆）", neg_tank)
    neg_fill = (u"fluid != Fluids.WATER" in fill) and (u"fluid != Fluids.LAVA" in fill)
    check(u"B6 FillingMachine.isGasFluid 同样是负向判定", neg_fill)
    check(u"B7 文档把这条列为头号雷 L1", u"L1" in doc and u"非水非岩浆" in doc)

    # ⚠ B8/B9 是 ZF72 那轮的"当时的代码事实"：
    #   0.11 ZF85 把 `GAS_COUNT` / `idOf` / `byId` 三个**再没人调用**的成员删掉了
    #   （ZF73 起界面改用**流体注册表 id**，IDE 报"方法从未使用"）。
    #   所以这两条改成断言"现在的事实"，并保留历史说明 —— 文档里那段记录记的是当年为什么错，
    #   不是"现在还有这个方法"。
    check(u"B8 ModFluids 里那个只认 3 种气体的紧凑编号体系已删除（ZF85）",
          u"GAS_COUNT" not in flu and u"public static int idOf(" not in flu
          and u"public static Fluid byId(" not in flu)
    check(u"B9 界面改用的是**流体注册表 id**（ZF73 起，见灌装机菜单）",
          u"BuiltInRegistries.FLUID" in read_text(os.path.join(
              PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod",
              u"FillingMachineMenu.java")))

    presets = glob.glob(os.path.join(PROJ, u"src", u"main", u"resources", u"data", u"minecraft",
                                     u"worldgen", u"world_preset", u"*.json"))
    ok = len(presets) == 3 and all(u"potato_s_t:salty_river" in read_text(p) for p in presets)
    check(u"B10 三个世界预设都引用了 potato_s_t:salty_river", ok, u"预设数 %d" % len(presets))

    tag_doc = read_text(os.path.join(PROJ, u"src", u"main", u"resources", u"data", u"minecraft",
                                     u"tags", u"worldgen", u"biome", u"is_overworld.json"))
    check(u"B11 is_overworld.json 是同工程覆盖且含 salty_river",
          u"salty_river" in tag_doc and u"replace" in tag_doc)

    srcs = all_sources()
    # B12 的第一版断言写得太粗：它抓「字面出现过 LiquidBlock」，结果命中了
    # FluidPumpBlockEntity（泵的判定就是 instanceof LiquidBlock）与 ModFluids 的注释。
    # 「从没注册过液体方块」说的是**注册**，所以断言要收窄到 new LiquidBlock(
    registered = [p for p in srcs if u"new LiquidBlock(" in read_text(p)]
    check(u"B12 工程里确实从没**注册**过液体方块（原油会是第一个）", len(registered) == 0,
          u"命中 %d 个文件" % len(registered))
    pump = read_text(os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod",
                                  u"FluidPumpBlockEntity.java"))
    pump_rule = u"instanceof LiquidBlock" in pump
    check(u"B12b 泵确实只认液体方块实例（这也是原油必须做成方块的理由）", pump_rule)
    check(u"B12c 文档写明了泵这条判定 + 待决 11", u"instanceof LiquidBlock" in doc
          and u"待决 11" in doc)
    check(u"B13 三种气体确实没有 bucket（ModFluids 里 0 处 bucket(）", u"bucket(" not in flu)

    oil_refs = [p for p in srcs if (u"crude_oil" in read_text(p) or u"oil_bucket" in read_text(p)
                                    or u"ocean_oilfield" in read_text(p))]
    check(u"B14 源码里没有石油的半个影子（本轮没动代码）", len(oil_refs) == 0,
          u"命中: %s" % u", ".join(os.path.basename(p) for p in oil_refs[:5]))
    check(u"B15 还没有 ocean_oilfield.json 群系文件",
          not os.path.isfile(os.path.join(PROJ, u"src", u"main", u"resources", u"data",
                                          u"potato_s_t", u"worldgen", u"biome",
                                          u"ocean_oilfield.json")))
    check(u"B16 还没有 oil_bucket 配方文件",
          not os.path.isfile(os.path.join(PROJ, u"src", u"main", u"resources", u"data",
                                          u"potato_s_t", u"recipe", u"oil_bucket.json")))

    # ---------------- C. 原版证据 ----------------
    print(u"\n=== C. 文档对原版的描述 vs 现抠证据 ===")
    ev = {}
    if os.path.isfile(EVID):
        with io.open(EVID, "r", encoding="utf-8") as fh:
            ev = json.load(fh)
    check(u"C1 原版证据文件存在", bool(ev))
    rarity = ev.get(u"lake_lava_surface", {}).get(u"rarity_chance")
    check(u"C2 证据：原版地表岩浆湖 rarity = 200", rarity == 200, u"实际 %s" % rarity)
    check(u"C3 文档：概率按原版岩浆湖 1/200", u"rarity_filter: chance 200" in doc)
    cfg = ev.get(u"lake_lava_config", {})
    check(u"C4 证据：lake 的 barrier=石头 fluid=岩浆 level 0",
          cfg.get(u"barrier") == u"minecraft:stone" and cfg.get(u"fluid") == u"minecraft:lava"
          and str(cfg.get(u"fluid_level")) == u"0")
    check(u"C5 文档：barrier=石头 / fluid=原油 level 0",
          u"barrier=石头" in doc and u"fluid=原油 level 0" in doc)
    dec = ev.get(u"oilfield_water_color", {}).get(u"dec")
    check(u"C6 证据：4047AD = 4212653", dec == 4212653, u"实际 %s" % dec)
    check(u"C7 文档：水色十进制 4212653", u"4212653" in doc)
    check(u"C8 文档：原版水色 4159204（对照）", u"4159204" in doc
          and ev.get(u"stony_shore", {}).get(u"water_color") == 4159204)
    check(u"C9 证据：NeoForge Tags.java 里没有原油通用标签",
          ev.get(u"neoforge_tags_java", {}).get(u"oil_tag_present") is False)
    check(u"C10 文档：上游没有「原油类」c: 标签这条事实仍在（ZF74 起我们按 c:crude_oil 约定挂上了）",
          u"没有**原油类通用 `c:` 标签" in doc or u"没有" in doc and u"c: tags/fluid" in doc.lower())

    # ---------------- D. 冻结状态 ----------------
    print(u"\n=== D. 冻结状态（本轮不该动 jar / 版本） ===")
    props = read_text(os.path.join(PROJ, u"gradle.properties"))
    mv = re.search(r"mod_version\s*=\s*(\S+)", props)
    check(u"D1 mod_version 仍是 0.10", bool(mv) and mv.group(1) == u"0.10",
          u"实际 %s" % (mv.group(1) if mv else u"?"))
    check(u"D2 成品 jar 存在", os.path.isfile(JAR))
    if os.path.isfile(JAR):
        check(u"D3 成品 jar SHA1 仍是 %s…" % JAR_SHA1[:12], sha1(JAR) == JAR_SHA1, sha1(JAR))
        check(u"D4 成品 jar 大小仍是 %d B" % JAR_SIZE, os.path.getsize(JAR) == JAR_SIZE,
              u"%d" % os.path.getsize(JAR))
    probes = glob.glob(os.path.join(PROJ, u"src", u"main", u"java", u"**", u"*Check*.java"),
                       recursive=True)
    check(u"D5 源码里 0 个探针类", len(probes) == 0, u"%d 个" % len(probes))

    # ---------------- E. 档案已记录 ----------------
    print(u"\n=== E. 开发档案已记录 ===")
    check(u"E1 §4.44 负向判定雷已立条", u"### 4.44" in arch)
    check(u"E2 §5 有 ZF72 流水线行", u"| ZF72 |" in arch)
    check(u"E3 档案指向本轮规划文档", u"docs/v0.11规划.md" in arch or u"docs\\v0.11规划.md" in arch)
    check(u"E4 §10 记了新备份根", u"C:\\PotatoST救援" in arch)

    # ---------------- F. 文档自身完整性 ----------------
    print(u"\n=== F. 规划文档自身完整性 ===")
    check(u"F1 待决 10 条都在（§5 表格 10 行）",
          len(re.findall(r"^\| \d+ \| ", doc, re.M)) >= 10,
          u"找到 %d 行" % len(re.findall(r"^\| \d+ \| ", doc, re.M)))
    for fn in [u"crude_oil_still.png", u"crude_oil_flow.png", u"oil_bucket.png"]:
        check(u"F2 贴图需求含 %s" % fn, fn in doc)
    check(u"F3 有分轮建议 ZF73 / ZF74", u"ZF73" in doc and u"ZF74" in doc)
    check(u"F4 明确写了本轮不动 jar", u"不作废" in doc and u"84d09345" in doc)

    print(u"\n============================================")
    print(u"检查项 = %d   失败项 = %d" % (checks, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    print(u"规划文档: %s  (%d B)" % (DOC, os.path.getsize(DOC) if os.path.isfile(DOC) else 0))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
