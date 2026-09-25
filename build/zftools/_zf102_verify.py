# -*- coding: utf-8 -*-
r"""_zf102_verify.py —— ZF102 常驻校验：酸性反应室加两个罐子（氢/氯）+ 第 4 个配方（盐酸）

用户原话（一条）：

  「酸性反应器再加两个罐子（氢气和氯气）1000MB 然后新加配方盐酸
    10mb氢气+10mb氯气+5mb水 产出5mb盐酸 耗能一致」

骨架：
  A 常量：罐 7→10、配方 3→4、4 号配方的四个数与"耗能一致"
  B 罐与配方接线：新罐接在最后（老存档不串味）、产物罐 / 产物 / 批次判定
  C 界面：10 个罐 + 4 个按钮 + 面板加宽
  D 新流体盐酸（§6 四处一起改，且**不是气体**）
  E 探针取证 / 活体数字 / 文档 / 成品 jar
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
PROBE = os.path.join(TOOLS, "_zf102_probe_utf8.txt")

EXPECT_KEYS = 398           # … + ZF107 成就 48 键
EXPECT_FLUIDS = 15          # ZF101 的 14 + 盐酸
EXPECT_SHAPED = 51          # 本轮不改配方（合成配方仍是 42 条）
passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def sha1f(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    print(u"=========== ZF102 校验：酸性反应室 + 氢/氯两罐 + 盐酸配方 ===========")
    be = read(os.path.join(JAVA, "AcidicReactionChamberBlockEntity.java")) or u""
    scr = read(os.path.join(JAVA, r"client\AcidicReactionChamberScreen.java")) or u""
    menu = read(os.path.join(JAVA, "AcidicReactionChamberMenu.java")) or u""
    mf = read(os.path.join(JAVA, "ModFluids.java")) or u""

    print(u"\n== A 常量：罐 7→10、配方 3→4 ==")
    for const, note in ((u"TANK_HYDROGEN = 7", u"氢气罐接在最后（老存档的号不动）"),
                        (u"TANK_CHLORINE = 8", u"氯气罐"),
                        (u"TANK_HYDROCHLORIC = 9", u"盐酸罐"),
                        (u"TANK_COUNT = 10", u"罐总数 10"),
                        (u"RECIPE_HYDROCHLORIC = 3", u"第 4 个配方"),
                        (u"RECIPE_COUNT = 4", u"配方总数 4"),
                        (u"HYDROCHLORIC_HYDROGEN_PER_TICK = 10", u"4 号：10 mB 氢气"),
                        (u"HYDROCHLORIC_CHLORINE_PER_TICK = 10", u"4 号：10 mB 氯气"),
                        (u"HYDROCHLORIC_WATER_PER_TICK = 5", u"4 号：5 mB 水"),
                        (u"HYDROCHLORIC_OUT_PER_TICK = 5", u"4 号：出 5 mB 盐酸")):
        check(u"%s —— %s" % (const, note), const in be)
    check(u"耗能仍是 500 FE/t（用户原话「耗能一致」）", u"ENERGY_PER_TICK = 500" in be)
    check(u"储能仍是 12400 FE", u"MAX_ENERGY = 12400" in be)
    check(u"六个原料罐 + 四个产物罐两张表都在",
          u"INPUT_TANKS = {" in be and u"OUTPUT_TANKS = {" in be
          and be.count(u"TANK_HYDROGEN, TANK_CHLORINE,") == 1
          and u"TANK_CARBONIC, TANK_NITRIC, TANK_SULFURIC, TANK_HYDROCHLORIC," in be)
    # ⚠ 光"两张表都在"不够：K79 那把刀就是把盐酸罐塞进 INPUT_TANKS，结果一条断言都没挂
    #   ⇒ 这里**把两张表的内容抠出来逐个数**（输入表里不许有产物罐、输出表里不许有原料罐）。
    in_block = be.split(u"INPUT_TANKS = {")[1].split(u"};")[0] if u"INPUT_TANKS = {" in be else u""
    out_block = be.split(u"OUTPUT_TANKS = {")[1].split(u"};")[0] if u"OUTPUT_TANKS = {" in be else u""
    check(u"输入罐表里**没有**盐酸罐（只出不进那条不许被破坏）",
          u"TANK_HYDROCHLORIC" not in in_block)
    check(u"输入罐表里没有其它产物罐", all(t not in in_block for t in
                                       (u"TANK_CARBONIC", u"TANK_NITRIC", u"TANK_SULFURIC")))
    check(u"输出罐表里没有原料罐（氢/氯/水/二氧化碳/氧/氨）",
          all(t not in out_block for t in (u"TANK_HYDROGEN", u"TANK_CHLORINE", u"TANK_WATER",
                                           u"TANK_CO2", u"TANK_OXYGEN", u"TANK_AMMONIA")))
    check(u"输入表 6 个罐、输出表 4 个罐（数出来）",
          in_block.count(u"TANK_") == 6 and out_block.count(u"TANK_") == 4)

    print(u"\n== B 罐与配方的接线 ==")
    check(u"fill 认氢气与氯气两条新分支",
          u"if (isHydrogen(resource)) {" in be and u"if (isChlorine(resource)) {" in be)
    check(u"drain 走 OUTPUT_TANKS 表（不再写死 TANK_CARBONIC..TANK_SULFURIC 的区间）",
          u"for (int tank : OUTPUT_TANKS)" in be)
    check(u"isFluidValid 只在输入罐里放行（isInputTank）",
          u"return isInputTank(tank)" in be)
    check(u"4 号的产物罐 = 盐酸罐（outputTankOf 里有一支）",
          u"case RECIPE_HYDROCHLORIC -> TANK_HYDROCHLORIC;" in be)
    check(u"4 号的产物 = 盐酸（productOf 里有一支）",
          u"case RECIPE_HYDROCHLORIC -> ModFluids.HYDROCHLORIC_ACID.get();" in be)
    check(u"4 号是连续式（isBatch 只认硫酸那一支）",
          u"return recipe == RECIPE_SULFURIC;" in be)
    check(u"连续式那条把氢气/氯气/水的检查都算进去了",
          u"this.tanks[TANK_HYDROGEN].getFluidAmount() < needHydrogen" in be
          and u"this.tanks[TANK_CHLORINE].getFluidAmount() < needChlorine" in be
          and u"hydrochloric ? HYDROCHLORIC_WATER_PER_TICK : 0" in be)
    check(u"扣料四条新分支都在（氢气/氯气/水）",
          u"this.tanks[TANK_HYDROGEN].drain(needHydrogen" in be
          and u"this.tanks[TANK_CHLORINE].drain(needChlorine" in be)
    check(u"新罐的 DataSlot 与 DATA_COUNT 都跟了",
          u"DATA_HYDROGEN = 12" in be and u"DATA_CHLORINE = 13" in be
          and u"DATA_HYDROCHLORIC = 14" in be and u"DATA_COUNT = 15" in be)
    check(u"菜单把三个新罐映射到自己的 DataSlot",
          u"DATA_HYDROGEN;" in menu and u"DATA_CHLORINE;" in menu and u"DATA_HYDROCHLORIC;" in menu)

    print(u"\n== C 界面 ==")
    check(u"界面画 10 个罐（6 进 4 出）", scr.count(u"new FluidTankPart(") == 10)
    check(u"面板加宽到 214（多一排罐 + 一个产物罐 + 第 4 个按钮）", u"WIDTH = 214" in scr)
    check(u"按钮按 RECIPE_COUNT 自动加到 4 个",
          u"for (int recipe = 0; recipe < AcidicReactionChamberBlockEntity.RECIPE_COUNT; recipe++)" in scr)
    check(u"硫槽与状态灯让位到新位置（不压在罐上）",
          u"SULFUR_SLOT_X = 160" in menu and u"new StatusLampPart(174" in scr)

    print(u"\n== D 新流体盐酸（§6 四处一起改） ==")
    check(u"FluidType + Source + Flowing 都注册了",
          u'FLUID_TYPES.register("hydrochloric_acid"' in mf
          and u'FLUIDS.register("hydrochloric_acid"' in mf
          and u'FLUIDS.register("flowing_hydrochloric_acid"' in mf)
    check(u"客户端有贴图注册",
          u'textures("hydrochloric_acid")' in (read(os.path.join(JAVA, "PotatoSTClient.java")) or u""))
    for suffix in ("still", "flow"):
        check(u"hydrochloric_acid_%s.png 在" % suffix,
              os.path.exists(os.path.join(RES, r"assets\potato_s_t\textures\block",
                                          u"hydrochloric_acid_%s.png" % suffix)))
    tag = json.loads(read(os.path.join(RES, r"data\c\tags\fluid\hydrochloric_acid.json")) or u"{}")
    eq(u"c:hydrochloric_acid 标签两份",
       [u"potato_s_t:hydrochloric_acid", u"potato_s_t:flowing_hydrochloric_acid"], tag.get(u"values"))
    gas_body = re.search(r"public static boolean isGas\(Fluid fluid\)\s*\{(.*?)\n    \}", mf, re.S)
    body = gas_body.group(1) if gas_body else u""
    check(u"盐酸**不在** isGas 白名单里（酸是液体）", u"HYDROCHLORIC_ACID.get()" not in body)
    gaseous = json.loads(read(os.path.join(RES, r"data\c\tags\fluid\gaseous.json")) or u"{}")
    check(u"盐酸也不在 #c:gaseous 里",
          all(u"hydrochloric" not in v for v in gaseous.get(u"values", [])))

    print(u"\n== E 探针取证 ==")
    rep = read(PROBE)
    check(u"探针报告在（%s）" % os.path.basename(PROBE), rep is not None)
    if rep:
        eq(u"报告里 FAIL = 0", 0, len(re.findall(r"\[FAIL\]", rep)))
        check(u"报告结论是「全部成立」", u"全部成立（0 项不符）" in rep)
        for line in (u"罐总数 = 10",
                     u"配方总数 = 4",
                     u"氢气罐 = 7 / 氯气罐 = 8 / 盐酸罐 = 9",
                     u"一 tick：氢气 10 → 0",
                     u"一 tick：氯气 10 → 0",
                     u"一 tick：水 5 → 0",
                     u"一 tick：盐酸 0 → 5",
                     u"一 tick：电 12400 → 11900",
                     u"原料用光 ⇒ 流体原料不足 14",
                     u"盐酸罐满了 ⇒ 产物罐满 4",
                     u"往机器里灌盐酸 ⇒ 一滴不收",
                     u"盐酸罐抽得出来",
                     u"氢气抽不走（原料罐只进不出）",
                     u"盐酸**不是**气体"):
            hit = [l for l in rep.splitlines() if line in l and u"[OK]" in l]
            check(u"探针里这条是 [OK]：%s" % line, bool(hit))

    print(u"\n== F 活体数字 / 文档 / 成品 ==")
    names = sorted(n for n in os.listdir(os.path.join(RES, r"data\potato_s_t\recipe"))
                   if n.endswith(u".json"))
    shaped = [n for n in names
              if (json.loads(read(os.path.join(RES, r"data\potato_s_t\recipe", n))) or {})
              .get("type") == u"minecraft:crafting_shaped"]
    eq(u"盘上定形配方总数（本轮没动）", EXPECT_SHAPED, len(shaped))
    fl = len(re.findall(r'FLUID_TYPES\.register\("', mf))
    eq(u"流体类型总数", EXPECT_FLUIDS, fl)
    for f, anchor in ((u"_zf71_verify.py", u"check(fl == %d" % EXPECT_FLUIDS),
                      (u"_zf71_verify.py", u"== {%d}" % EXPECT_KEYS),
                      (u"_zf97_verify.py", u"EXPECT_FLUIDS = %d" % EXPECT_FLUIDS),
                      (u"_zf97_verify.py", u"EXPECT_KEYS = %d" % EXPECT_KEYS),
                      (u"_zf100_verify.py", u"EXPECT_FLUIDS = %d" % EXPECT_FLUIDS),
                      (u"_zf101_verify.py", u"EXPECT_FLUIDS = %d" % EXPECT_FLUIDS),
                      (u"_zf101_verify.py", u"EXPECT_KEYS = %d" % EXPECT_KEYS),
                      (u"_zf78_verify.py", u'fluids.count("() -> liquidType(") == 8'),
                      (u"_zf85_verify.py", u'mf.count(u"liquidType(\\"") == 8'),
                      (u"_zf74_verify.py", u'"hydrochloric_acid.json"')):
        check(u"%s 跟到了（%s）" % (f, anchor), anchor in (read(os.path.join(TOOLS, f)) or u""))
    fal = read(os.path.join(TOOLS, u"_zf78_falsify.py")) or u""
    check(u"本脚本已挂进 _zf78_falsify.py 的 VERIFIERS", u'"_zf102_verify.py"' in fal)
    for k in (u"K78 ", u"K79 "):
        check(u"_zf78_falsify.py 里有刀 %s" % k, (u'u"%s' % k) in fal)
    gates = read(os.path.join(TOOLS, u"_zf102_gates.ps1")) or u""
    check(u"本轮闸门脚本在、且声明了 ZF102 那一段", u"_zf102_verify.py" in gates)

    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    check(u"档案 §5 有 ZF102 那一行", u"| ZF102 |" in arch)
    check(u"档案 §9 有 ZF102 那一节", u"### ZF102（0.11）" in arch)
    check(u"公告写了盐酸那一条", u"Hydrochloric" in ann or u"hydrochloric" in ann)
    lang = {}
    for f in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        d = json.loads(read(os.path.join(RES, r"assets\potato_s_t\lang", f)))
        lang[f] = d
        eq(u"%s 键数" % f, EXPECT_KEYS, len(d))
    for k in (u"fluid_type.potato_s_t.hydrochloric_acid",
              u"gui.potato_s_t.acidic_reaction_chamber.recipe.name.3",
              u"gui.potato_s_t.acidic_reaction_chamber.recipe.info.3"):
        check(u"四语言都有 %s" % k, all(k in lang[f] for f in lang))

    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            inner = zf.namelist()
            check(u"成品里有盐酸的贴图与标签",
                  u"assets/potato_s_t/textures/block/hydrochloric_acid_still.png" in inner
                  and u"data/c/tags/fluid/hydrochloric_acid.json" in inner)
            probes = [n for n in inner if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
            eq(u"成品里没有探针 class", [], probes)
            check(u"成品里 zh_cn 是 %d 键" % EXPECT_KEYS,
                  len(json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
                  == EXPECT_KEYS)

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
