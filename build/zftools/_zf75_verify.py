# -*- coding: utf-8 -*-
u"""_zf75_verify.py —— ZF75（世界生成）常驻校验 + 内置反证

`python _zf75_verify.py`            正常校验
`python _zf75_verify.py --falsify`  改坏水色 → 校验必须挂 → 逐字节还原
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile

PROJ = r"E:\PotatoST"
RES = os.path.join(PROJ, u"src", u"main", u"resources")
DATA = os.path.join(RES, u"data", u"potato_s_t")
MC = os.path.join(RES, u"data", u"minecraft")
JAVA = os.path.join(PROJ, u"src", u"main", u"java", u"com", u"potatost", u"mod")
LAYOUT = os.path.join(JAVA, u"SaltyRiverBiomeSource.java")
ARCH = os.path.join(PROJ, u"docs", u"开发档案.md")
PLAN = os.path.join(PROJ, u"docs", u"v0.11规划.md")
ANN = os.path.join(PROJ, u"docs", u"UpdateAnnouncement_EN.md")
JAR = os.path.join(PROJ, u"release", u"PotatoST-0.11.jar")
JAR_BUILT = os.path.join(PROJ, u"build", u"libs", u"potato_s_t-0.11.jar")
JAR_OLD = os.path.join(PROJ, u"release", u"PotatoST-0.10.jar")
BIOME = os.path.join(DATA, u"worldgen", u"biome", u"ocean_oilfield.json")
VOIDED = u"39e66beb0a7e"

checks = 0
fails = []


def check(name, cond, detail=u""):
    global checks
    checks += 1
    if not cond:
        fails.append(name if not detail else u"%s  (%s)" % (name, detail))
    print(u"  %s %s" % (u"[OK]  " if cond else u"[FAIL]", name))


def read(path):
    return io.open(path, "r", encoding="utf-8", errors="replace").read() if os.path.isfile(path) else u""


def load(path):
    try:
        return json.loads(read(path))
    except Exception:
        return {}


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def verify():
    global checks, fails
    checks, fails = 0, []
    src = read(LAYOUT)
    arch = read(ARCH)
    plan = read(PLAN)
    ann = read(ANN)

    # ---- A. 数据文件 ----
    print(u"\n=== A. 世界生成数据 ===")
    cfg = load(os.path.join(DATA, u"worldgen", u"configured_feature", u"mini_oilfield.json"))
    check(u"A1 配置特征是 minecraft:lake", cfg.get(u"type") == u"minecraft:lake")
    state = cfg.get(u"config", {}).get(u"fluid", {}).get(u"state", {})
    check(u"A2 湖里放的是 potato_s_t:crude_oil level 0（源方块）",
          state.get(u"Name") == u"potato_s_t:crude_oil"
          and state.get(u"Properties", {}).get(u"level") == u"0")
    check(u"A3 barrier 是石头（与原版 lake_lava 一致）",
          cfg.get(u"config", {}).get(u"barrier", {}).get(u"state", {}).get(u"Name") == u"minecraft:stone")
    pl = load(os.path.join(DATA, u"worldgen", u"placed_feature", u"mini_oilfield_placed.json"))
    types = [m.get(u"type") for m in pl.get(u"placement", [])]
    check(u"A4 放置特征与地表岩浆湖同参数（rarity 200 / in_square / 高度图 / biome）",
          u"minecraft:rarity_filter" in types and u"minecraft:in_square" in types
          and u"minecraft:heightmap" in types and u"minecraft:biome" in types
          and pl[u"placement"][0].get(u"chance") == 200)
    base = load(os.path.join(DATA, u"neoforge", u"biome_modifier", u"mini_oilfield.json"))
    check(u"A5 基础注入器：is_overworld + step lakes",
          base.get(u"biomes") == u"#minecraft:is_overworld" and base.get(u"step") == u"lakes"
          and base.get(u"features") == [u"potato_s_t:mini_oilfield_placed"])
    # ⚠ ZF76 修复：原来这里是"两份注入器重复注入同一个 placed feature" ⇒
    #   原版 FeatureSorter 报 `Feature order cycle found`，**新建世界直接崩**（用户报的卡 0%）。
    #   现在改成"再挂一份更密的放置特征"：基础 chance 200 + dense chance 100 ⇒ 沙漠恶地 3 倍，
    #   而且没有任何特征被重复注入。
    extra = load(os.path.join(DATA, u"neoforge", u"biome_modifier",
                              u"mini_oilfield_desert_a.json"))
    check(u"A6 沙漠/恶地追加注入器挂的是 dense 版本（tag 形式，单值）",
          extra.get(u"biomes") == u"#potato_s_t:oilfield_dense"
          and extra.get(u"step") == u"lakes"
          and extra.get(u"features") == [u"potato_s_t:mini_oilfield_placed_dense"])
    dense_pl = load(os.path.join(DATA, u"worldgen", u"placed_feature",
                                 u"mini_oilfield_placed_dense.json"))
    check(u"A6b dense 版放置参数与基础一致，只有 rarity 是 100（200 的一半 ⇒ 合计 3 倍）",
          dense_pl.get(u"feature") == u"potato_s_t:mini_oilfield"
          and dense_pl[u"placement"][0].get(u"chance") == 100
          and [m.get(u"type") for m in dense_pl.get(u"placement", [])]
          == [m.get(u"type") for m in pl.get(u"placement", [])])
    # 回归断言：我们注入的 placed feature 不许重复（重复 = Feature order cycle = 新建世界崩）
    injected = []
    for f in os.listdir(os.path.join(DATA, u"neoforge", u"biome_modifier")):
        if f.startswith(u"mini_oilfield"):
            injected.extend(load(os.path.join(DATA, u"neoforge", u"biome_modifier", f))
                            .get(u"features", []))
    check(u"A6c 注入特征没有重复（Feature order cycle 的根因）",
          len(injected) == len(set(injected)), u", ".join(injected))
    dense = load(os.path.join(DATA, u"tags", u"worldgen", u"biome", u"oilfield_dense.json"))
    check(u"A7 #potato_s_t:oilfield_dense = [badlands tag, desert]（replace:false）",
          dense.get(u"replace") is False
          and sorted(dense.get(u"values", [])) == sorted([u"#minecraft:is_badlands", u"minecraft:desert"]))
    check(u"A8 没有引用不存在的 #minecraft:is_desert（1.21.1 里没有这张标签）",
          u"is_desert" not in read(os.path.join(DATA, u"tags", u"worldgen", u"biome",
                                                u"oilfield_dense.json")))
    iso = load(os.path.join(MC, u"tags", u"worldgen", u"biome", u"is_overworld.json"))
    check(u"A9 is_overworld 追加了海洋油田（仍 replace:false）",
          iso.get(u"replace") is False and u"potato_s_t:ocean_oilfield" in iso.get(u"values", [])
          and u"potato_s_t:salty_river" in iso.get(u"values", []))
    biome = load(BIOME)
    check(u"A10 群系水色 = 4212653 (4047AD)", biome.get(u"effects", {}).get(u"water_color") == 4212653)
    check(u"A11 群系以石岸为底 + 海草/海带",
          u"minecraft:seagrass_normal" in json.dumps(biome) and u"minecraft:kelp_cold" in json.dumps(biome))
    check(u"A12 群系水里补了 cod/squid",
          u"minecraft:cod" in json.dumps(biome) and u"minecraft:squid" in json.dumps(biome))

    # ---- B. Java ----
    print(u"\n=== B. 群系源 ===")
    check(u"B1 OCEAN_OILFIELD key 存在", u"OCEAN_OILFIELD" in src)
    check(u"B2 两个新字段是可选字段（旧存档缺字段也能解出来）",
          u'.optionalFieldOf("oil_biome")' in src and u'.optionalFieldOf("oil_chance"' in src)
    check(u"B3 旧存档兜底用 Holder.Reference#unwrapLookup()", u"unwrapLookup()" in src)
    # ZF77：改成"靠岸的浅海"（用户：「还是放在海里吧 靠近岸边就行」）
    check(u"B4 浅海 → 油田分支存在", u"original.is(Biomes.OCEAN)" in src)
    check(u"B4b 近岸判定（四邻至少一个不是海，用 #minecraft:is_ocean）",
          u"isCoastalOcean" in src and u"is_ocean" in src and u"NEIGHBOUR_OFFSETS" in src)
    check(u"B4c 没再动石岸（旧的 STONY_SHORE 分支已删）", u"Biomes.STONY_SHORE" not in src)
    check(u"B5 咸水河公式一个字节没改（含原乘数、且没有掺入 OIL_SALT）",
          u"* 341873128712L" in src and u"isSaltySection" in src
          and u"OIL_SALT" not in src.split(u"isSaltySection")[1].split(u"private boolean isOilSection")[0])
    check(u"B6 油田用另一套常数", u"OIL_SALT" in src and u"0x5EEDL" in src)
    check(u"B7 源码里 0 个探针类",
          not [f for f in os.listdir(JAVA) if u"Check" in f and f.endswith(u".java")])

    # ---- C. 语言 / 发布 / 文档 ----
    print(u"\n=== C. 语言 · 发布 · 文档 ===")
    counts = {}
    for name in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        data = load(os.path.join(RES, u"assets", u"potato_s_t", u"lang", name))
        counts[name] = len(data)
        check(u"C1 %s 有 biome.potato_s_t.ocean_oilfield" % name,
              u"biome.potato_s_t.ocean_oilfield" in data)
    check(u"C2 四语言各 482 键（ZF104 起；ZF107 +48；ZF109 +10）", all(v == 482 for v in counts.values()), str(counts))
    check(u"C3 成品 == 构建产物", os.path.isfile(JAR) and os.path.isfile(JAR_BUILT)
          and sha1(JAR) == sha1(JAR_BUILT))
    check(u"C4 .sha1 文件与成品一致", os.path.isfile(JAR)
          and read(JAR + u".sha1").strip() == sha1(JAR))
    check(u"C5 0.10 成品未动", sha1(JAR_OLD) == u"84d09345f6095408ae462dabb536307141904ea3")
    if os.path.isfile(JAR):
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
        check(u"C6 jar 里有 6 份新数据文件",
              all(n in names for n in (
                  u"data/potato_s_t/worldgen/configured_feature/mini_oilfield.json",
                  u"data/potato_s_t/worldgen/placed_feature/mini_oilfield_placed.json",
                  u"data/potato_s_t/worldgen/biome/ocean_oilfield.json",
                  u"data/potato_s_t/neoforge/biome_modifier/mini_oilfield.json",
                  u"data/potato_s_t/neoforge/biome_modifier/mini_oilfield_desert_a.json",
                  u"data/potato_s_t/tags/worldgen/biome/oilfield_dense.json")))
        check(u"C7 jar 里没有探针 class", not [n for n in names if u"Check" in n])
    check(u"C8 档案记了上一版作废（%s…）" % VOIDED, VOIDED in arch)
    check(u"C9 档案记了新成品哈希", sha1(JAR)[:12] in arch if os.path.isfile(JAR) else False)
    check(u"C10 档案有 §5 ZF75 行", u"| ZF75 |" in arch)
    check(u"C11 规划文档记了 ZF75 完成", u"ZF75 已完成" in plan)
    check(u"C12 公告不再说「原油只能在创造里放」", u"creative-only fluid" not in ann
          and u"now generates in the world" in ann)

    print(u"\n============================================")
    print(u"检查项 = %d   失败项 = %d" % (checks, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


def falsify():
    u"""内置反证：改坏群系水色 → 校验必须挂 → 逐字节还原。"""
    print(u"反证：把 ocean_oilfield.json 的水色改成 1")
    with io.open(BIOME, "rb") as fh:
        original = fh.read()
    before = hashlib.sha1(original).hexdigest()
    text = original.decode("utf-8")
    n = text.count(u'"water_color": 4212653')
    if n != 1:
        print(u"  !! 锚点命中 %d 次，无法反证" % n)
        return 1
    try:
        io.open(BIOME, "wb").write(text.replace(u'"water_color": 4212653', u'"water_color": 1').encode("utf-8"))
        rc = subprocess.run([sys.executable, u"-X", u"utf8", os.path.abspath(__file__)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode
        print(u"  改坏后校验返回码 = %d（必须非 0）" % rc)
        ok = rc != 0
    finally:
        io.open(BIOME, "wb").write(original)
        same = hashlib.sha1(io.open(BIOME, "rb").read()).hexdigest() == before
        print(u"  还原: %s" % (u"逐字节相同" if same else u"!! 不一致"))
        ok = ok and same
    print(u"反证结果: %s" % (u"抓住" if ok else u"没抓住"))
    return 0 if ok else 1


if __name__ == "__main__":
    if u"--falsify" in sys.argv:
        sys.exit(falsify())
    sys.exit(verify())
