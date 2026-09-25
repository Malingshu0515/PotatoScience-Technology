# -*- coding: utf-8 -*-
u"""_zf101_retarget.py —— 把往轮校验脚本里的**活体数字与名单**跟到本轮（ZF101）

  · 定形配方 41 → **42**（+酸性反应室）
  · 流体 11 → **14**（+碳酸/硝酸/硫酸）
  · 键数 315 → **332**（+17：方块名/说明/6 条状态/3 个按钮名 + 3 条按钮说明/3 个流体名）
  · 新增配方名单 +1：`acidic_reaction_chamber.json`（`_zf73_repro` / `_zf73_verify` / `_zf95_verify`）
  · `_zf74_verify.py` 的 `c:` 流体标签表 +3 份酸、`_zf97_verify.py` 的"只新增"名单 +3
  · `_zf78_falsify.py`：挂上本轮校验 + 四把新刀（K74~K77）

规矩（ZF96 起）：每条锚点必须恰好命中一次；同一份文件有多条改动时**写之前重新读一遍**。
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
ACIDS = [u"carbonic_acid", u"nitric_acid", u"sulfuric_acid"]

EDITS = []

# ---------------- 定形配方 41 → 42 ----------------
EDITS += [
    ("_zf71_verify.py",
     u'    check(craft == 41, u"合成配方 %d 条" % craft)  # ZF100 起 41（ZF97 的 38 + 本轮三件：锂电池/高炉主控/燃烧反应室）',
     u'    check(craft == 42, u"合成配方 %d 条" % craft)  # ZF101 起 42（ZF100 的 41 + 酸性反应室）'),
    ("_zf95_verify.py", u"EXPECT_SHAPED = 41", u"EXPECT_SHAPED = 42"),
    ("_zf96_verify.py", u"EXPECT_SHAPED = 41", u"EXPECT_SHAPED = 42"),
    ("_zf97_verify.py", u"EXPECT_SHAPED = 41", u"EXPECT_SHAPED = 42"),
    # （ZF100 那句 EXPECT_SHAPED 的注释已在第一遍改写里跟到 42；这里不再重复改）
]

# ---------------- 流体 11 → 14 ----------------
EDITS += [
    ("_zf71_verify.py",
     u'    check(fl == 11 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)  # ZF100 起 11（+二氧化碳）',
     u'    check(fl == 14 and u"oxygen, hydrogen, chlorine" in doc, u"流体 %d 种" % fl)  # ZF101 起 14（+三种酸）'),
    ("_zf97_verify.py", u"EXPECT_FLUIDS = 11", u"EXPECT_FLUIDS = 14"),
    ("_zf97_verify.py", u'    eq(u"流体类型总数（10 + 1 二氧化碳）", EXPECT_FLUIDS, fl)',
     u'    eq(u"流体类型总数（ZF101 起 14）", EXPECT_FLUIDS, fl)'),
    ("_zf100_verify.py", u"EXPECT_FLUIDS = 11          # 10 + 二氧化碳",
     u"EXPECT_FLUIDS = 14          # 10 + 二氧化碳 + 三种酸"),
]

# ---------------- 键数 315 → 332 ----------------
EDITS += [
    ("_zf71_verify.py",
     u'    check(len(keys) == 4 and set(keys.values()) == {315} and u"315 keys each" in doc,',
     u'    check(len(keys) == 4 and set(keys.values()) == {332} and u"332 keys each" in doc,'),
    ("_zf73_verify.py",
     u'    check(u"B11 四语言各 315 键（… + ZF100 12）", all(v == 315 for v in counts.values()), str(counts))',
     u'    check(u"B11 四语言各 332 键（… + ZF101 17）", all(v == 332 for v in counts.values()), str(counts))'),
    ("_zf75_verify.py",
     u'    check(u"C2 四语言各 315 键（ZF100 起）", all(v == 315 for v in counts.values()), str(counts))',
     u'    check(u"C2 四语言各 332 键（ZF101 起）", all(v == 332 for v in counts.values()), str(counts))'),
    ("_zf78_verify.py",
     u'''    check(u"四份语言键数一致且 = 315（ZF100 燃烧反应室 +12）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 315)''',
     u'''    check(u"四份语言键数一致且 = 332（ZF101 酸性反应室 +17）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 332)'''),
    ("_zf79_verify.py",
     u'''    check(u"四份语言键数一致且 = 315（ZF100 燃烧反应室 +12）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 315)''',
     u'''    check(u"四份语言键数一致且 = 332（ZF101 酸性反应室 +17）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 332)'''),
    ("_zf80_verify.py", u"EXPECT_KEYS = 315", u"EXPECT_KEYS = 332"),
    ("_zf81_verify.py",
     u'        eq(u"语言键数（ZF100 起 315）", 315, len(inside))',
     u'        eq(u"语言键数（ZF101 起 332）", 332, len(inside))'),
    ("_zf82_verify.py", u"EXPECT_KEYS = 315", u"EXPECT_KEYS = 332"),
    ("_zf82_verify.py", u'          and u"315 keys each" in ann)',
     u'          and u"332 keys each" in ann)'),
    ("_zf93_verify.py", u"EXPECT_KEYS = 315", u"EXPECT_KEYS = 332"),
    ("_zf96_verify.py", u"EXPECT_KEYS = 315", u"EXPECT_KEYS = 332"),
    ("_zf96_verify.py", u"# ⚠ 活体数字：ZF96 那轮是 284（272 + 本轮 12）；ZF97 又 +19 ⇒ 303；ZF100 再 +12 ⇒ 315",
     u"# ⚠ 活体数字：ZF96 那轮是 284；ZF97 +19 ⇒ 303；ZF100 +12 ⇒ 315；ZF101 +17 ⇒ 332"),
    ("_zf97_verify.py", u"EXPECT_KEYS = 315                    # ZF97 的 303 + ZF100 燃烧反应室的 12",
     u"EXPECT_KEYS = 332                    # ZF97 的 303 + ZF100 的 12 + ZF101 的 17"),
    ("_zf98_verify.py", u"EXPECT_KEYS = 315", u"EXPECT_KEYS = 332"),
    ("_zf100_verify.py", u"EXPECT_KEYS = 315           # 303 + 12（方块名/说明/7 条状态/2 条手倒/二氧化碳流体名）",
     u"EXPECT_KEYS = 332           # ZF100 的 315 + ZF101 的 17"),
]

# ---------------- 新增配方名单 +1 ----------------
EDITS += [
    ("_zf73_repro.py",
     u'''          u"lithium_battery.json", u"electric_blast_furnace.json",
          u"combustion_chamber.json"}''',
     u'''          u"lithium_battery.json", u"electric_blast_furnace.json",
          u"combustion_chamber.json", u"acidic_reaction_chamber.json"}'''),
    ("_zf73_verify.py",
     u'''sorted(cur - pre) == [u"air_separator.json", u"alloy_smelter.json",''',
     u'''sorted(cur - pre) == [u"acidic_reaction_chamber.json", u"air_separator.json",
                                    u"alloy_smelter.json",'''),
    ("_zf95_verify.py",
     u'''                 u"lithium_battery.json", u"electric_blast_furnace.json",
                 u"combustion_chamber.json"]''',
     u'''                 u"lithium_battery.json", u"electric_blast_furnace.json",
                 u"combustion_chamber.json", u"acidic_reaction_chamber.json"]'''),
    # ZF100 的"只新增那 3 份"随轮次增长
    ("_zf100_verify.py",
     u'        eq(u"盘上比改前正好多这 3 份", sorted(n + u".json" for n in SPEC), sorted(extra))',
     u'        # ⚠ 新增名单随轮次增长（ZF101 起多一份酸性反应室）—— "改前那些逐字节未变"才是这条的内容\n'
     u'        eq(u"盘上比改前多出来的就是预期的那些（+ ZF101 的酸性反应室）",\n'
     u'           sorted([n + u".json" for n in SPEC] + [u"acidic_reaction_chamber.json"]), sorted(extra))'),
]

# ---------------- c: 流体标签表 +3 ----------------
EDITS += [
    ("_zf74_verify.py",
     u'''    print(u"\\n=== A. 8 份 c: 流体标签（ZF97 加 nitrogen/ammonia、ZF100 加 carbon_dioxide）===")''',
     u'''    print(u"\\n=== A. 11 份 c: 流体标签（ZF97 加 nitrogen/ammonia、ZF100 加 carbon_dioxide、"
     u"ZF101 加三种酸）===")'''),
    ("_zf74_verify.py",
     u'''        u"carbon_dioxide.json": [u"potato_s_t:carbon_dioxide", u"potato_s_t:flowing_carbon_dioxide"],''',
     u'''        u"carbon_dioxide.json": [u"potato_s_t:carbon_dioxide", u"potato_s_t:flowing_carbon_dioxide"],
        u"carbonic_acid.json": [u"potato_s_t:carbonic_acid", u"potato_s_t:flowing_carbonic_acid"],
        u"nitric_acid.json": [u"potato_s_t:nitric_acid", u"potato_s_t:flowing_nitric_acid"],
        u"sulfuric_acid.json": [u"potato_s_t:sulfuric_acid", u"potato_s_t:flowing_sulfuric_acid"],'''),
    ("_zf97_verify.py",
     u'''        eq(u"流体标签只新增 nitrogen/ammonia（+ ZF100 的 carbon_dioxide）三份",
           [u"ammonia.json", u"carbon_dioxide.json", u"nitrogen.json"], sorted(added))''',
     u'''        eq(u"流体标签只新增预期的那些（ZF97 两种气体 + ZF100 二氧化碳 + ZF101 三种酸）",
           [u"ammonia.json", u"carbon_dioxide.json", u"carbonic_acid.json", u"nitric_acid.json",
            u"nitrogen.json", u"sulfuric_acid.json"], sorted(added))'''),
]

# ---------------- 反证名单 + 本轮四把刀 ----------------
EDITS += [
    ("_zf78_falsify.py",
     u'''    (u"K73 捕获器不再认燃烧反应室（动力源被摘掉）",''',
     u'''    # ---- ZF101 四刀：酸性反应室的关键数 ----
    (u"K74 酸性反应室耗能 500 → 400 FE/t",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"public static final int ENERGY_PER_TICK = 500;",
     u"public static final int ENERGY_PER_TICK = 400;"),
    (u"K75 一批硫酸要的硫 10 → 5",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"public static final int SULFUR_PER_BATCH = 10;",
     u"public static final int SULFUR_PER_BATCH = 5;"),
    (u"K76 三个产物罐也变成"能灌入"（只出不进那条被破坏）",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"            return tank <= TANK_WATER && AcidicReactionChamberBlockEntity.this.tanks[tank].isFluidValid(stack);",
     u"            return AcidicReactionChamberBlockEntity.this.tanks[tank].isFluidValid(stack);"),
    (u"K77 菜单不再校验配方号（客户端说什么就是什么）",
     os.path.join(SRC, "AcidicReactionChamberMenu.java"),
     u"        if (this.machine == null || !AcidicReactionChamberBlockEntity.isValidRecipe(id)) {",
     u"        if (this.machine == null) {"),
    (u"K73 捕获器不再认燃烧反应室（动力源被摘掉）",'''),
    ("_zf78_falsify.py",
     u'''             os.path.join(TOOLS, "_zf100_verify.py")]''',
     u'''             os.path.join(TOOLS, "_zf100_verify.py"),
             os.path.join(TOOLS, "_zf101_verify.py")]'''),
    ("..\\..\\docs\\UpdateAnnouncement_EN.md", u"(315 keys each)", u"(332 keys each)"),
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
            fails.append(u"%s：锚点命中 %d 次\n      %s" % (name, n, old.splitlines()[0]))
            continue
        plan.append((name, p, old, new, False))
    if fails:
        print(u"  [FAIL] 锚点不对 ⇒ **一条都不写**：")
        for f in fails:
            print(u"    !! " + f)
        return 1
    for name, p, old, new, done in plan:
        if done:
            print(u"  [SKIP] %-20s 已经跟过了" % name)
            continue
        t = io.open(p, encoding="utf-8").read()
        if t.count(old) != 1:
            fails.append(u"%s：写之前锚点命中 %d 次" % (name, t.count(old)))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
        print(u"  [OK]   %-20s %s" % (name, old.splitlines()[0].strip()[:64]))
    if fails:
        print(u"  [FAIL] 写到一半出问题：")
        for f in fails:
            print(u"    !! " + f)
        return 1
    print()
    checks = [
        ("_zf71_verify.py", u"check(craft == 42,", True),
        ("_zf71_verify.py", u"check(fl == 14", True),
        ("_zf71_verify.py", u"== {332}", True),
        ("_zf95_verify.py", u"EXPECT_SHAPED = 42", True),
        ("_zf96_verify.py", u"EXPECT_SHAPED = 42", True),
        ("_zf97_verify.py", u"EXPECT_SHAPED = 42", True),
        ("_zf97_verify.py", u"EXPECT_FLUIDS = 14", True),
        ("_zf97_verify.py", u"EXPECT_KEYS = 332", True),
        ("_zf100_verify.py", u"EXPECT_SHAPED = 42", True),
        ("_zf100_verify.py", u"EXPECT_KEYS = 332", True),
        ("_zf100_verify.py", u"EXPECT_FLUIDS = 14", True),
        ("_zf73_repro.py", u'"acidic_reaction_chamber.json"', True),
        ("_zf73_verify.py", u'"acidic_reaction_chamber.json"', True),
        ("_zf74_verify.py", u'"sulfuric_acid.json"', True),
        ("_zf97_verify.py", u'"sulfuric_acid.json"', True),
        ("_zf78_falsify.py", u"_zf101_verify.py", True),
        ("_zf78_falsify.py", u"K77 ", True),
        ("_zf98_verify.py", u"EXPECT_KEYS = 332", True),
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
