# -*- coding: utf-8 -*-
u"""_zf102_retarget.py —— 把往轮校验脚本里的活体数字跟到本轮（ZF102）

  · 流体 14 → **15**（+盐酸）：`_zf71` / `_zf97` / `_zf100` / `_zf101`
  · 键数 332 → **335**：`_zf71` / `_zf73` / `_zf75` / `_zf78` / `_zf79` / `_zf80` / `_zf81` /
    `_zf82` / `_zf93` / `_zf96` / `_zf97` / `_zf98` / `_zf100` / `_zf101` / 英文公告
  · `liquidType` 调用点 7 → **8**（`_zf78` / `_zf85`）
  · `c:` 流体标签表 +1（`_zf74`）、"只新增"名单 +1（`_zf97`）
  · `_zf78_falsify.py`：挂上本轮校验 + 两把新刀（K78/K79）
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
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")

EDITS = [
    # ---------------- 流体 14 → 15 ----------------
    ("_zf71_verify.py", u"check(fl == 14", u"check(fl == 15"),
    ("_zf97_verify.py", u"EXPECT_FLUIDS = 14", u"EXPECT_FLUIDS = 15"),
    ("_zf100_verify.py", u"EXPECT_FLUIDS = 14", u"EXPECT_FLUIDS = 15"),
    ("_zf101_verify.py", u"EXPECT_FLUIDS = 14", u"EXPECT_FLUIDS = 15"),

    # ---------------- 键数 332 → 335 ----------------
    ("_zf71_verify.py", u"== {332}", u"== {335}"),
    ("_zf71_verify.py", u'u"332 keys each"', u'u"335 keys each"'),
    ("_zf73_verify.py", u"四语言各 332 键（… + ZF101 17）", u"四语言各 335 键（… + ZF102 3）"),
    ("_zf73_verify.py", u"all(v == 332 for v in counts.values())", u"all(v == 335 for v in counts.values())"),
    ("_zf75_verify.py", u"四语言各 332 键（ZF101 起）", u"四语言各 335 键（ZF102 起）"),
    ("_zf75_verify.py", u"all(v == 332 for v in counts.values())", u"all(v == 335 for v in counts.values())"),
    ("_zf78_verify.py", u"= 332（ZF101 酸性反应室 +17）", u"= 335（ZF102 盐酸 +3）"),
    ("_zf78_verify.py", u"list(counts.values())[0] == 332)", u"list(counts.values())[0] == 335)"),
    ("_zf79_verify.py", u"= 332（ZF101 酸性反应室 +17）", u"= 335（ZF102 盐酸 +3）"),
    ("_zf79_verify.py", u"list(counts.values())[0] == 332)", u"list(counts.values())[0] == 335)"),
    ("_zf80_verify.py", u"EXPECT_KEYS = 332", u"EXPECT_KEYS = 335"),
    ("_zf81_verify.py", u'eq(u"语言键数（ZF101 起 332）", 332, len(inside))',
     u'eq(u"语言键数（ZF102 起 335）", 335, len(inside))'),
    ("_zf82_verify.py", u"EXPECT_KEYS = 332", u"EXPECT_KEYS = 335"),
    ("_zf82_verify.py", u'and u"332 keys each" in ann)', u'and u"335 keys each" in ann)'),
    ("_zf93_verify.py", u"EXPECT_KEYS = 332", u"EXPECT_KEYS = 335"),
    ("_zf96_verify.py", u"EXPECT_KEYS = 332", u"EXPECT_KEYS = 335"),
    ("_zf97_verify.py", u"EXPECT_KEYS = 332", u"EXPECT_KEYS = 335"),
    ("_zf98_verify.py", u"EXPECT_KEYS = 332", u"EXPECT_KEYS = 335"),
    ("_zf100_verify.py", u"EXPECT_KEYS = 332", u"EXPECT_KEYS = 335"),
    ("_zf101_verify.py", u"EXPECT_KEYS = 332", u"EXPECT_KEYS = 335"),
    ("..\\..\\docs\\UpdateAnnouncement_EN.md", u"(332 keys each)", u"(335 keys each)"),

    # ---------------- liquidType 调用点 7 → 8 ----------------
    ("_zf78_verify.py", u'fluids.count("() -> liquidType(") == 7', u'fluids.count("() -> liquidType(") == 8'),
    ("_zf78_verify.py", u"共用同一个液体类型工厂（不抄七遍 initializeClient）",
     u"共用同一个液体类型工厂（不抄八遍 initializeClient）"),
    ("_zf85_verify.py", u'mf.count(u"liquidType(\\"") == 7', u'mf.count(u"liquidType(\\"") == 8'),
    ("_zf85_verify.py", u"7 个调用点都不再传第 4 个参数（4 种分馏产物 + 3 种酸）",
     u"8 个调用点都不再传第 4 个参数（4 种分馏产物 + 4 种酸）"),

    # ---------------- c: 标签表 / 只新增名单 ----------------
    ("_zf74_verify.py", u"11 份 c: 流体标签", u"12 份 c: 流体标签"),
    ("_zf74_verify.py",
     u'''        u"sulfuric_acid.json": [u"potato_s_t:sulfuric_acid", u"potato_s_t:flowing_sulfuric_acid"],''',
     u'''        u"sulfuric_acid.json": [u"potato_s_t:sulfuric_acid", u"potato_s_t:flowing_sulfuric_acid"],
        u"hydrochloric_acid.json": [u"potato_s_t:hydrochloric_acid",
                                    u"potato_s_t:flowing_hydrochloric_acid"],'''),
    ("_zf97_verify.py",
     u'''           [u"ammonia.json", u"carbon_dioxide.json", u"carbonic_acid.json", u"nitric_acid.json",
            u"nitrogen.json", u"sulfuric_acid.json"], sorted(added))''',
     u'''           [u"ammonia.json", u"carbon_dioxide.json", u"carbonic_acid.json",
            u"hydrochloric_acid.json", u"nitric_acid.json", u"nitrogen.json",
            u"sulfuric_acid.json"], sorted(added))'''),

    # ---------------- 反证名单 + 两把新刀 ----------------
    ("_zf78_falsify.py",
     u'''    (u"K73 捕获器不再认燃烧反应室（动力源被摘掉）",''',
     u'''    # ---- ZF102 两刀：第 4 个配方（盐酸）的数 ----
    (u"K78 盐酸配方要的氢气 10 → 5（配比被改）",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"public static final int HYDROCHLORIC_HYDROGEN_PER_TICK = 10;",
     u"public static final int HYDROCHLORIC_HYDROGEN_PER_TICK = 5;"),
    (u"K79 盐酸罐被当成原料罐（只出不进那条被破坏）",
     os.path.join(SRC, "AcidicReactionChamberBlockEntity.java"),
     u"            TANK_CO2, TANK_OXYGEN, TANK_AMMONIA, TANK_WATER, TANK_HYDROGEN, TANK_CHLORINE,",
     u"            TANK_CO2, TANK_OXYGEN, TANK_AMMONIA, TANK_WATER, TANK_HYDROGEN, TANK_CHLORINE,\\n"
     u"            TANK_HYDROCHLORIC,"),
    (u"K73 捕获器不再认燃烧反应室（动力源被摘掉）",'''),
    ("_zf78_falsify.py",
     u'''             os.path.join(TOOLS, "_zf101_verify.py")]''',
     u'''             os.path.join(TOOLS, "_zf101_verify.py"),
             os.path.join(TOOLS, "_zf102_verify.py")]'''),
]


def main():
    fails, plan = [], []
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
        print(u"  [FAIL] 锚点不对 ⇒ 一条都不写：")
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
        print(u"  [OK]   %-20s %s" % (name, old.splitlines()[0].strip()[:60]))
    if fails:
        print(u"  [FAIL] 写到一半出问题：")
        for f in fails:
            print(u"    !! " + f)
        return 1
    print()
    checks = [("_zf71_verify.py", u"check(fl == 15", True),
              ("_zf71_verify.py", u"== {335}", True),
              ("_zf97_verify.py", u"EXPECT_FLUIDS = 15", True),
              ("_zf97_verify.py", u"EXPECT_KEYS = 335", True),
              ("_zf100_verify.py", u"EXPECT_KEYS = 335", True),
              ("_zf101_verify.py", u"EXPECT_KEYS = 335", True),
              ("_zf101_verify.py", u"EXPECT_FLUIDS = 15", True),
              ("_zf78_verify.py", u"== 8", True),
              ("_zf85_verify.py", u"== 8", True),
              ("_zf74_verify.py", u'"hydrochloric_acid.json"', True),
              ("_zf97_verify.py", u'"hydrochloric_acid.json"', True),
              ("_zf78_falsify.py", u"_zf102_verify.py", True),
              ("_zf78_falsify.py", u"K79 ", True)]
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
