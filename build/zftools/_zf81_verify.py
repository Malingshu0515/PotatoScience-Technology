# -*- coding: utf-8 -*-
u"""_zf81_verify.py —— ZF81 交付校验（常驻，跑在门里）

用户原话：「电解器还是改成 1000Fe/t 吧」。本轮只动**能耗**这一个数（水/产物速度一个没动）：

  A 代码：两个常量 = 1000 + 缓冲仍 ≥ 单 tick 电费（ZF38「泵永久待机」那条坑）
  B 注释/文案：Java 注释、四份 lang tooltip、JEI 说明注释里不许再出现 100 FE
  C 活体数字：英文公告 + `_zf71_verify.py` 的期望值都跟上（上一轮就是漏了这个白跑一遍门）
  D 回归：速度类常量一个没动；JEI 仍是引用常量（不是写死的字面量）
  E 成品与文档
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
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
LANG = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t", "lang")
TOOLS = os.path.join(ROOT, "build", "zftools")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]

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


def src(name, sub=None):
    return read(os.path.join(SRC, sub, name) if sub else os.path.join(SRC, name))


def int_consts(java):
    if not java:
        return {}
    raw = {}
    for m in re.finditer(r"\b([A-Z][A-Z0-9_]*)\s*=\s*([^;{}]+);", java):
        name, expr = m.group(1), m.group(2).strip()
        if re.fullmatch(r"[0-9A-Za-z_ ()*+\-]+", expr):
            raw[name] = expr
    resolved = {}

    def resolve(name, depth=0):
        if name in resolved:
            return resolved[name]
        if depth > 8 or name not in raw:
            return None
        expr = raw[name]

        def sub(mm):
            ident = mm.group(0)
            if ident.isdigit():
                return ident
            val = resolve(ident, depth + 1)
            return str(val) if val is not None else "?"

        expr2 = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", sub, expr)
        if "?" in expr2:
            return None
        try:
            val = int(eval(expr2, {"__builtins__": {}}, {}))
        except Exception:
            return None
        resolved[name] = val
        return val

    for n in list(raw):
        resolve(n)
    return resolved


# ================= A 代码 =================

def section_a():
    print(u"\n== A 电解器能耗常量 ==")
    el = src("ElectrolyzerBlockEntity.java")
    c = int_consts(el)
    eq(u"纯水制氧 = 1000 FE/t", 1000, c.get("ENERGY_PER_TICK_OXYGEN"))
    eq(u"盐水制氯 = 1000 FE/t", 1000, c.get("ENERGY_PER_TICK_CHLORINE"))
    check(u"两个常量**逐字**写成 1000（不是算出来的别的东西）",
          u"public static final int ENERGY_PER_TICK_OXYGEN = 1000;" in el
          and u"public static final int ENERGY_PER_TICK_CHLORINE = 1000;" in el)
    eq(u"兼容别名 ENERGY_PER_TICK 仍指向盐水那一个", 1000, c.get("ENERGY_PER_TICK"))
    check(u"别名不是新写死的数字（还是引用常量）",
          u"public static final int ENERGY_PER_TICK = ENERGY_PER_TICK_CHLORINE;" in el)
    # 缓冲 ≥ 单 tick 电费：ZF38 那条「泵永久待机」的坑
    cost = max(c.get("ENERGY_PER_TICK_OXYGEN") or 0, c.get("ENERGY_PER_TICK_CHLORINE") or 0)
    check(u"缓冲 %s FE ≥ 单 tick 电费 %s FE（否则机器永久待机）"
          % (c.get("MAX_ENERGY"), cost), (c.get("MAX_ENERGY") or 0) >= cost)
    check(u"两处扣电都扣的是新常量（不是残留的 100）",
          u"this.energy -= ENERGY_PER_TICK_OXYGEN;" in el
          and u"this.energy -= ENERGY_PER_TICK_CHLORINE;" in el)
    check(u"两处**门槛**也都比的是新常量",
          u"if (this.energy < ENERGY_PER_TICK_OXYGEN) {" in el
          and u"if (this.energy < ENERGY_PER_TICK_CHLORINE) {" in el)
    log = u"（缓冲 " + str(c.get("MAX_ENERGY")) + u" FE ⇒ 满载 " + str((c.get("MAX_ENERGY") or 0) // (cost or 1)) + u" tick）"
    print(u"  —— " + log)


# ================= B 注释与文案 =================

def section_b():
    print(u"\n== B 注释 / 四份 tooltip / JEI 说明 ==")
    el = src("ElectrolyzerBlockEntity.java")
    bad = [ln.strip()[:70] for ln in el.split(u"\n")
           if u"100 FE" in ln and u"抬到 1000" not in ln and u"100 FE/t 时是" not in ln]
    check(u"代码注释里不再有「100 FE/t」的现行说法（历史沿革那两处除外）：%s" % (bad or u"无"),
          not bad)
    check(u"类注释写清了这轮改了什么（ZF81 1000 FE/t）", u"0.11 ZF81 改的数" in el)

    recipes = src("MachineRecipes.java")
    check(u"JEI 说明里也不再有 100 FE/t",
          u"100 FE/t" not in recipes and u"1000 FE/t" in recipes)
    check(u"JEI 的两条能耗仍是**引用常量**（不是写死的字面量）",
          u"Component.translatable(\"gui.potato_s_t.jei.energy\", "
          u"ElectrolyzerBlockEntity.ENERGY_PER_TICK_OXYGEN)" in recipes
          and u"Component.translatable(\"gui.potato_s_t.jei.energy\", "
              u"ElectrolyzerBlockEntity.ENERGY_PER_TICK_CHLORINE)" in recipes)

    for l in LANGS:
        p = os.path.join(LANG, l + u".json")
        tip = u""
        if os.path.exists(p):
            for line in read(p).split(u"\n"):
                if u"tooltip.potato_s_t.electrolyzer" in line:
                    tip = line
        check(u"%s：tooltip 已是 1000 FE" % l, u"1000 FE" in tip)
        check(u"%s：tooltip 不再说 100 FE" % l, u"100 FE" not in tip)
        check(u"%s：水/产物/海盐那三个数没被动（10 mB / 3 / 6 / 500 mB）" % l,
              all(x in tip for x in [u"10 mB", u"3 ", u"6 ", u"500 mB"])
              or all(x in tip for x in [u"10 mB", u"500 mB"]))


# ================= C 活体数字 =================

def section_c():
    print(u"\n== C 活体数字（公告 + 活体校验脚本）==")
    ann = read(os.path.join(DOCS, u"UpdateAnnouncement_EN.md")) or u""
    check(u"英文公告电解器行 = 1,000 FE/t + 10 mB water/t",
          u"1,000 FE/t + 10 mB water/t" in ann)
    check(u"英文公告里那个旧的 100 FE/t 没了", u"100 FE/t + 10 mB water/t" not in ann)

    zf71 = read(os.path.join(TOOLS, u"_zf71_verify.py")) or u""
    check(u"ZF71 活体校验：期望常量 = 1000", u'ENERGY_PER_TICK_OXYGEN\\s*=\\s*1000' in zf71)
    check(u"ZF71 活体校验：不再期望 100（那条 old 断言已改）",
          u'ENERGY_PER_TICK_OXYGEN\\s*=\\s*100"' not in zf71)
    check(u"ZF71 活体校验：tooltip 字面量 1000 FE",
          u'(u"tooltip.potato_s_t.electrolyzer", [u"1000 FE"' in zf71)


# ================= D 回归 =================

def section_d():
    print(u"\n== D 回归：只动了能耗这一个数 ==")
    el = src("ElectrolyzerBlockEntity.java")
    c = int_consts(el)
    eq(u"耗水速度仍是 10 mB/t", 10, c.get("WATER_PER_TICK"))
    eq(u"产氧速度仍是 3", 3, c.get("OXYGEN_PER_TICK"))
    eq(u"产氢速度仍是 6", 6, c.get("HYDROGEN_PER_TICK"))
    eq(u"产氯速度仍是 3", 3, c.get("CHLORINE_PER_TICK"))
    eq(u"每个海盐仍是 500 mB 水", 500, c.get("WATER_PER_SALT"))
    eq(u"缓冲仍是 20000（本轮没动它）", 20000, c.get("MAX_ENERGY"))
    eq(u"水槽容量仍是 1000", 1000, c.get("INPUT_CAPACITY"))
    eq(u"三个产品罐仍是 800", 800, c.get("OXYGEN_CAPACITY"))
    check(u"模式选择逻辑没动（有海盐 ⇒ 氯）",
          u"return this.processChlorine(salt);" in el and u"return this.processOxygen();" in el)


# ================= E 成品与文档 =================

def section_e():
    print(u"\n== E 成品与文档 ==")
    sha = None
    if os.path.exists(JAR):
        sha = hashlib.sha1(open(JAR, "rb").read()).hexdigest()
        rec = read(JAR + u".sha1")
        check(u".sha1 与 jar 实际哈希一致（%s…）" % sha[:8],
              rec is not None and rec.strip().lower() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            bad = [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
            check(u"成品里没有探针 class（%s）" % (bad or u"0 个"), not bad)
            inside = json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode(u"utf-8"))
        check(u"成品里的中文 tooltip 也是 1000 FE",
              u"1000 FE" in inside.get(u"tooltip.potato_s_t.electrolyzer", u""))
        eq(u"语言键数（ZF112 起 432）", 432, len(inside))
    else:
        check(u"成品 jar 存在", False)

    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    check(u"档案里有 ZF81 那一行", u"| ZF81 |" in arch)
    check(u"档案里记了用户原话", u"电解器还是改成 1000Fe/t" in arch)
    check(u"档案里写了探针结论 27 项全过", u"27" in arch and u"探针" in arch)
    check(u"档案里**提出**了缓冲只剩 20 tick 这件事（待用户拍板，不许默默改）",
          u"20 tick" in arch)
    if sha:
        check(u"档案里写着当前成品哈希 %s…" % sha[:8], sha in arch)
    check(u"文档里没有 __NEWSHA__ 之类的占位残留", u"__NEWSHA__" not in arch)


def main():
    print(u"=========== ZF81 校验：电解器 1000 FE/t ===========")
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
