# -*- coding: utf-8 -*-
u"""_zf100_retarget.py —— 把往轮校验脚本里的**活体数字与名单**跟到本轮（ZF100）

本轮改了什么数（用户中途收窄过范围：「停停停只要刚才那两个机器的配方」，随后又加了燃烧反应室）：
  · 定形配方 38 → **41**：`_zf71_verify.py`（craft）/ `_zf95_verify.py` / `_zf96_verify.py` /
    `_zf97_verify.py`（EXPECT_SHAPED）—— 本轮新增 **3** 条：
    三元聚合物锂电池 / 电力高炉主控 / 燃烧反应室
  · 新增配方名单 +3：`_zf73_repro.py`（NEW_OK）/ `_zf73_verify.py`（D2）/ `_zf95_verify.py`（later）
  · `_zf71_verify.py` 的「还没有配方」反向断言 —— **名单要改**：
    锂电池与电力高炉主控本轮补上了配方 ⇒ 从"没有"名单里挪出去；
    **高级金属块 / 稳定金属块 / 扳手仍然没有**（用户明确说只要那两个机器 + 燃烧反应室）⇒ 留在名单里
  · `_zf78_falsify.py`：挂上本轮校验 + 五把新刀（K69~K73）

规矩（ZF96 起）：**每条锚点必须恰好命中一次**；同一份文件有多条改动时，**写之前重新读一遍**
（第一版拿"计划阶段读到的原文"写，后一条会把前一条整个覆盖 —— 本轮自证当场抓出来过）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TOOLS = r"E:\PotatoST\build\zftools"
ROOT = r"E:\PotatoST"
RECIPE = os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "recipe")

EDITS = [
    # ---------------- 活体数字 ----------------
    ("_zf71_verify.py",
     u'    check(craft == 38, u"合成配方 %d 条" % craft)  # ZF97 起 38（ZF95 的 5 条 + ZF96 的加氢脱硫反应仓 + ZF97 的两台机器）',
     u'    check(craft == 41, u"合成配方 %d 条" % craft)  # ZF100 起 41（ZF97 的 38 + 本轮三件：锂电池/高炉主控/燃烧反应室）'),

    ("_zf95_verify.py", u"EXPECT_SHAPED = 38", u"EXPECT_SHAPED = 41"),
    ("_zf96_verify.py", u"EXPECT_SHAPED = 38", u"EXPECT_SHAPED = 41"),
    ("_zf97_verify.py", u"EXPECT_SHAPED = 38", u"EXPECT_SHAPED = 41"),

    # ---------------- 「还没有配方」的名单：改内容，不是删掉 ----------------
    ("_zf71_verify.py",
     u'''    # ⚠ ZF95 起：用户口述的 5 条配方上线 ⇒ **合金炉主控 / 分馏塔控制器 / 分馏塔操作器 已经有配方了**，
    #   这三件从"还没有配方"的名单里挪出去（英文公告 §9 同步改过）；仍在名单里的是剩下三件。
    for bid in ("potato_s_t:lithium_battery", "potato_s_t:advanced_metal_block",
                "potato_s_t:stable_metal_block"):
        check(bid not in made, u"%s 确实还没有配方（公告把它列进 known gaps）" % bid)
''',
     u'''    # ⚠ ZF100 起：**锂电池与电力高炉主控补上了配方**（用户：「前面那几个没配方的机器你看着加吧」）
    #   ⇒ 这两件从"还没有配方"的名单里挪出去；用户随后明确「只要刚才那两个机器的配方」
    #     ⇒ **扳手 / 高级金属块 / 稳定金属块仍然没有**，名单里留着（英文公告 §9 同步改过）。
    for bid in ("potato_s_t:advanced_metal_block", "potato_s_t:stable_metal_block",
                "potato_s_t:wrench"):
        check(bid not in made, u"%s 确实还没有配方（公告把它列进 known gaps）" % bid)
    for bid in ("potato_s_t:lithium_battery", "potato_s_t:electric_blast_furnace",
                "potato_s_t:combustion_chamber"):
        check(bid in made, u"%s 现在**有**配方了（ZF100 补的）" % bid)
'''),

    # ---------------- 新增配方名单 ----------------
    ("_zf73_repro.py",
     u'''          u"hydrodesulfurization_chamber.json",
          u"air_separator.json", u"ammonia_synthesis_chamber.json"}''',
     u'''          u"hydrodesulfurization_chamber.json",
          u"air_separator.json", u"ammonia_synthesis_chamber.json",
          u"lithium_battery.json", u"electric_blast_furnace.json",
          u"combustion_chamber.json"}'''),

    ("_zf73_verify.py",
     u'''sorted(cur - pre) == [u"air_separator.json", u"alloy_smelter.json",
                                    u"ammonia_synthesis_chamber.json",
                                    u"distillation_controller.json",
                                    u"distillation_operator.json", u"fluid_exchanger.json",
                                    u"hydrodesulfurization_chamber.json",
                                    u"music_disc_anvil_of_the_republic.json",
                                    u"music_disc_jasmine_flower.json", u"oil_bucket.json"],''',
     u'''sorted(cur - pre) == [u"air_separator.json", u"alloy_smelter.json",
                                    u"ammonia_synthesis_chamber.json",
                                    u"combustion_chamber.json",
                                    u"distillation_controller.json",
                                    u"distillation_operator.json",
                                    u"electric_blast_furnace.json", u"fluid_exchanger.json",
                                    u"hydrodesulfurization_chamber.json",
                                    u"lithium_battery.json",
                                    u"music_disc_anvil_of_the_republic.json",
                                    u"music_disc_jasmine_flower.json", u"oil_bucket.json"],'''),

    ("_zf95_verify.py",
     u'''        later = [u"hydrodesulfurization_chamber.json", u"air_separator.json",
                 u"ammonia_synthesis_chamber.json"]''',
     u'''        later = [u"hydrodesulfurization_chamber.json", u"air_separator.json",
                 u"ammonia_synthesis_chamber.json",
                 u"lithium_battery.json", u"electric_blast_furnace.json",
                 u"combustion_chamber.json"]'''),

    # ---------------- 反证名单 + 本轮五把刀 ----------------
    ("_zf78_falsify.py",
     u'''    (u"K68 冒烟间隔 5 tick → 50 tick（一秒才一次）",
     os.path.join(SRC, "AirSeparatorBlockEntity.java"),
     u"public static final int PARTICLE_INTERVAL = 5;",
     u"public static final int PARTICLE_INTERVAL = 50;"),
]''',
     u'''    (u"K68 冒烟间隔 5 tick → 50 tick（一秒才一次）",
     os.path.join(SRC, "AirSeparatorBlockEntity.java"),
     u"public static final int PARTICLE_INTERVAL = 5;",
     u"public static final int PARTICLE_INTERVAL = 50;"),
    # ---- ZF100 五刀：新配方 + 电力高炉新锚点 + 燃烧反应室的关键数 ----
    (u"K69 电力高炉锚点改回只认原版高炉（自己造的主控又变成摆下去没用的方块）",
     os.path.join(SRC, "ElectricBlastFurnaceStructure.java"),
     u"""case CONTROLLER -> state.is(Blocks.BLAST_FURNACE)
                    || state.is(ModBlocks.ELECTRIC_BLAST_FURNACE.get());""",
     u"""case CONTROLLER -> state.is(Blocks.BLAST_FURNACE);"""),
    (u"K70 锂电池九宫格把中间那行换掉（PLP → LPP，材料一样但摆法变了）",
     os.path.join(RECIPE, "lithium_battery.json"),
     u'"ACA",\\n    "PLP",\\n    "AMA"',
     u'"ACA",\\n    "LPP",\\n    "AMA"'),
    (u"K71 燃烧反应室的二氧化碳产物 200 → 20（柴油那一档）",
     os.path.join(SRC, "CombustionChamberBlockEntity.java"),
     u"public static final int CO2_PER_LIQUID_FUEL = 200;",
     u"public static final int CO2_PER_LIQUID_FUEL = 20;"),
    (u"K72 燃烧反应室的氧气罐改成「能被抽走」（必须输入端那条被破坏）",
     os.path.join(SRC, "CombustionChamberBlockEntity.java"),
     u"""            if (isCarbonDioxide(resource)) {
                return CombustionChamberBlockEntity.this.tanks[TANK_CO2].drain(resource, action);
            }""",
     u"""            if (isOxygen(resource)) {
                return CombustionChamberBlockEntity.this.tanks[TANK_OXYGEN].drain(resource, action);
            }
            if (isCarbonDioxide(resource)) {
                return CombustionChamberBlockEntity.this.tanks[TANK_CO2].drain(resource, action);
            }"""),
    (u"K73 捕获器不再认燃烧反应室（动力源被摘掉）",
     os.path.join(SRC, "PowerCapturerBlockEntity.java"),
     u"""            if (level.getBlockEntity(neighbor) instanceof CombustionChamberBlockEntity chamber) {
                total += chamber.powerPerTick();
                continue;
            }""",
     u""),
]'''),

    ("_zf78_falsify.py",
     u'''             os.path.join(TOOLS, "_zf99_verify.py")]''',
     u'''             os.path.join(TOOLS, "_zf99_verify.py"),
             os.path.join(TOOLS, "_zf100_verify.py")]'''),

    # ---------------- 流体数 10 → 11、isGas 白名单 10 → 12（新气体"二氧化碳"） ----------------
    ("_zf71_verify.py",
     u'    check(fl == 10 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)  # ZF97 起 10（+氮气/氨气）',
     u'    check(fl == 11 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)  # ZF100 起 11（+二氧化碳）'),

    ("_zf73_verify.py",
     u'    check(u"A14 isGas 正向列举：10 个气体变体一个不少（5 种 × 2；实测 %d）" % gas_hits, gas_hits == 10)',
     u'    check(u"A14 isGas 正向列举：12 个气体变体一个不少（6 种 × 2；实测 %d）" % gas_hits, gas_hits == 12)'),

    ("_zf74_verify.py",
     u'''    check(u"B1 isGas 仍写死自家 3 种（数据包没加载时也认得出）",
          len(re.findall(r"fluid == \\w+\\.get\\(\\)", body)) == 10)''',
     u'''    check(u"B1 isGas 仍写死自家 6 种（数据包没加载时也认得出）",
          len(re.findall(r"fluid == \\w+\\.get\\(\\)", body)) == 12)'''),

    ("_zf97_verify.py",
     u'''    eq(u"isGas 正向列举现在是 5 种气体 × 2 变体 = %d 个" % EXPECT_FLUIDS, EXPECT_FLUIDS, gas_hits)''',
     u'''    eq(u"isGas 正向列举现在是 6 种气体 × 2 变体 = %d 个" % EXPECT_GAS_VARIANTS,
       EXPECT_GAS_VARIANTS, gas_hits)'''),

    ("_zf97_verify.py",
     u'''    eq(u"流体类型总数（8 + 2）", EXPECT_FLUIDS, fl)''',
     u'''    eq(u"流体类型总数（10 + 1 二氧化碳）", EXPECT_FLUIDS, fl)'''),

    ("_zf97_verify.py",
     u'''EXPECT_FLUIDS = 10''',
     u'''EXPECT_FLUIDS = 11
# isGas 正向白名单里的变体条数（6 种气体 × 源/流动）—— ZF100 起与"流体类型总数"不再相等
EXPECT_GAS_VARIANTS = 12'''),

    # ---------------- 键数 303 → 315（燃烧反应室 + 二氧化碳共 12 键） ----------------
    ("_zf71_verify.py",
     u'    check(len(keys) == 4 and set(keys.values()) == {303} and u"303 keys each" in doc,',
     u'    check(len(keys) == 4 and set(keys.values()) == {315} and u"315 keys each" in doc,'),
    ("_zf73_verify.py",
     u'    check(u"B11 四语言各 303 键（ZF78 27 + ZF79 2 + ZF80 9 + ZF82 13 + ZF93 2 + ZF96 12 + ZF97 19）", all(v == 303 for v in counts.values()), str(counts))',
     u'    check(u"B11 四语言各 315 键（… + ZF100 12）", all(v == 315 for v in counts.values()), str(counts))'),
    ("_zf75_verify.py",
     u'    check(u"C2 四语言各 303 键（ZF97 起）", all(v == 303 for v in counts.values()), str(counts))',
     u'    check(u"C2 四语言各 315 键（ZF100 起）", all(v == 315 for v in counts.values()), str(counts))'),
    ("_zf78_verify.py",
     u'''    check(u"四份语言键数一致且 = 303（ZF97 两台新机器 +19）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 303)''',
     u'''    check(u"四份语言键数一致且 = 315（ZF100 燃烧反应室 +12）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 315)'''),
    ("_zf79_verify.py",
     u'''    check(u"四份语言键数一致且 = 303（ZF97 两台新机器 +19）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 303)''',
     u'''    check(u"四份语言键数一致且 = 315（ZF100 燃烧反应室 +12）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 315)'''),
    ("_zf80_verify.py", u"EXPECT_KEYS = 303", u"EXPECT_KEYS = 315"),
    ("_zf81_verify.py",
     u'        eq(u"语言键数（ZF97 起 303：两台新机器 +19）", 303, len(inside))',
     u'        eq(u"语言键数（ZF100 起 315）", 315, len(inside))'),
    ("_zf82_verify.py", u"EXPECT_KEYS = 303", u"EXPECT_KEYS = 315"),
    ("_zf82_verify.py", u'          and u"303 keys each" in ann)',
     u'          and u"315 keys each" in ann)'),
    ("_zf93_verify.py", u"EXPECT_KEYS = 303", u"EXPECT_KEYS = 315"),
    ("_zf96_verify.py",
     u'''# ⚠ 活体数字：ZF96 那轮是 284（272 + 本轮 12）；ZF97 又 +19 ⇒ 303
EXPECT_KEYS = 303''',
     u'''# ⚠ 活体数字：ZF96 那轮是 284（272 + 本轮 12）；ZF97 又 +19 ⇒ 303；ZF100 再 +12 ⇒ 315
EXPECT_KEYS = 315'''),
    ("_zf97_verify.py",
     u"EXPECT_KEYS = 284 + len(NEW_KEYS)     # 303",
     u"EXPECT_KEYS = 315                    # ZF97 的 303 + ZF100 燃烧反应室的 12"),
    ("_zf98_verify.py", u"EXPECT_KEYS = 303", u"EXPECT_KEYS = 315"),

    # ---------------- 流体标签：多了一份 carbon_dioxide.json、gaseous 从 10 条到 12 条 ----------------
    ("_zf74_verify.py",
     u'''    print(u"\\n=== A. 7 份 c: 流体标签（ZF97 加了 nitrogen/ammonia）===")''',
     u'''    print(u"\\n=== A. 8 份 c: 流体标签（ZF97 加 nitrogen/ammonia、ZF100 加 carbon_dioxide）===")'''),
    ("_zf74_verify.py",
     u'''                          u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia"],''',
     u'''                          u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia",
                          u"potato_s_t:carbon_dioxide", u"potato_s_t:flowing_carbon_dioxide"],'''),
    ("_zf74_verify.py",
     u'''        u"ammonia.json": [u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia"],''',
     u'''        u"ammonia.json": [u"potato_s_t:ammonia", u"potato_s_t:flowing_ammonia"],
        u"carbon_dioxide.json": [u"potato_s_t:carbon_dioxide", u"potato_s_t:flowing_carbon_dioxide"],'''),
    ("_zf97_verify.py",
     u'        eq(u"流体标签只新增 nitrogen/ammonia 两份", [u"ammonia.json", u"nitrogen.json"], sorted(added))',
     u'        eq(u"流体标签只新增 nitrogen/ammonia（+ ZF100 的 carbon_dioxide）三份",\n'
     u'           [u"ammonia.json", u"carbon_dioxide.json", u"nitrogen.json"], sorted(added))'),

    # ---------------- 英文公告里的键数 ----------------
    ("..\\..\\docs\\UpdateAnnouncement_EN.md", u"(303 keys each)", u"(315 keys each)"),
]


def main():
    fails = []
    plan = []
    for name, old, new in EDITS:
        p = os.path.join(TOOLS, name)
        t = io.open(p, encoding="utf-8").read()
        n = t.count(old)
        if n == 0 and t.count(new) >= 1:
            plan.append((name, p, old, new, True))
            continue
        if n != 1:
            fails.append(u"%s：锚点命中 %d 次（必须 1 次）\n      %s" % (name, n, old.splitlines()[0]))
            continue
        plan.append((name, p, old, new, False))
    if fails:
        print(u"  [FAIL] 锚点不对 ⇒ **一条都不写**：")
        for f in fails:
            print(u"    !! " + f)
        return 1

    for name, p, old, new, done in plan:
        if done:
            print(u"  [SKIP] %-20s 已经跟过了：%s" % (name, old.splitlines()[0].strip()[:60]))
            continue
        t = io.open(p, encoding="utf-8").read()      # ⚠ 写之前重新读（同一份文件可能有多条改动）
        if t.count(old) != 1:
            fails.append(u"%s：写之前锚点命中 %d 次" % (name, t.count(old)))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
        print(u"  [OK]   %-20s %s" % (name, old.splitlines()[0].strip()[:70]))
    if fails:
        print(u"  [FAIL] 写到一半出问题：")
        for f in fails:
            print(u"    !! " + f)
        return 1

    print()
    checks = [
        ("_zf71_verify.py", u"check(craft == 41,", True),
        ("_zf71_verify.py", u'"potato_s_t:wrench"', True),
        ("_zf71_verify.py", u"potato_s_t:combustion_chamber", True),
        ("_zf71_verify.py", u"确实还没有配方", True),
        ("_zf95_verify.py", u"EXPECT_SHAPED = 41", True),
        ("_zf96_verify.py", u"EXPECT_SHAPED = 41", True),
        ("_zf97_verify.py", u"EXPECT_SHAPED = 41", True),
        ("_zf73_repro.py", u'"combustion_chamber.json"', True),
        ("_zf73_verify.py", u'"combustion_chamber.json"', True),
        ("_zf95_verify.py", u'"combustion_chamber.json"', True),
        ("_zf78_falsify.py", u"_zf100_verify.py", True),
        ("_zf78_falsify.py", u"K73 ", True),
        ("_zf71_verify.py", u"check(fl == 11", True),
        ("_zf73_verify.py", u"gas_hits == 12)", True),
        ("_zf74_verify.py", u")) == 12)", True),
        ("_zf97_verify.py", u"EXPECT_GAS_VARIANTS = 12", True),
    ]
    bad = 0
    for name, needle, want in checks:
        t = io.open(os.path.join(TOOLS, name), encoding="utf-8").read()
        ok = (needle in t) == want
        print(u"  [%s] %-20s %s" % (u"OK" if ok else u"FAIL", name, needle))
        bad += 0 if ok else 1
    print(u"\n失败项 = %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
