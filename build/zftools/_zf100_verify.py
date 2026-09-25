# -*- coding: utf-8 -*-
r"""_zf100_verify.py —— ZF100 常驻校验：两条机器配方 + 电力高炉新锚点 + 燃烧反应室

用户原话（三条，按时间顺序）：

  ① 「前面那几个没配方的机器你看着加吧 可以略微难一点 参考别的」
  ② 「停停停只要刚才那两个机器的配方」   ← 收窄范围
  ③ 燃烧反应室那一整段（图纸 + 三个罐 + 两个槽 + 燃料规则 + 黑烟 + 动力 800/1200）

⚠ **配方规格是我定的**（用户在 ①里说"你看着加"，随后 ② 明确只要两台机器）⇒
   这份校验的第一件事就是**把规格钉死**，免得以后有人悄悄改一个格子还以为没事。
   规格同时写在档案 §9 的 ZF100 那一节。

骨架：
  A 三条新配方（锂电池 / 电力高炉主控 / 燃烧反应室）逐格等于规格
  B 设计红线：电力高炉主控**不许**要求"只有电力高炉才做得出来"的材料 —— 否则死锁
  C 产物唯一：每件只有一条配方
  D 电力高炉：锚点两种都认（源码）+ 探针在真服务端上的取证
  E 燃烧反应室：燃料判定 / 反应档案 / 三个罐的方向 / 状态码 / 粒子 / 捕获器识别
  F 新气体二氧化碳的"四处一起改"（§6 清单）
  G 只新增不改旧：拿改前那份成品 jar 当独立证据源
  H 活体数字 41 / 315 键 / 11 流体 + 往轮断言 + 文档 + 成品 jar
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
RDIR = os.path.join(RES, r"data\potato_s_t\recipe")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
PRE_JAR = r"C:\PotatoST救援\zf100_pre\release\PotatoST-0.11.jar"
PRE_SHA = u"533749f3053558f8f201fc397f1c72725f80a40d"
PROBE = os.path.join(TOOLS, "_zf100_probe_utf8.txt")

EXPECT_SHAPED = 43          # ZF97 的 38 + 本轮 3
EXPECT_KEYS = 398           # … + ZF107 成就 48 键
EXPECT_FLUIDS = 15          # 10 + 二氧化碳 + 三种酸
EXPECT_GAS_VARIANTS = 12    # 6 种气体 × 源/流动

SPEC = {
    u"lithium_battery": dict(
        category=u"redstone",
        pattern=[u"ACA", u"PLP", u"AMA"],
        key={u"A": u"potato_s_t:aluminum_plate", u"C": u"potato_s_t:capacitor",
             u"P": u"potato_s_t:copper_plate", u"L": u"potato_s_t:lithium_carbonate",
             u"M": u"potato_s_t:common_metal_block"}),
    u"electric_blast_furnace": dict(
        category=u"misc",
        pattern=[u"PHP", u"WCW", u"PAP"],
        key={u"P": u"potato_s_t:iron_plate", u"H": u"potato_s_t:heater",
             u"W": u"potato_s_t:wiring_block", u"C": u"minecraft:blast_furnace",
             u"A": u"potato_s_t:capacitor"}),
    # 用户口述的图纸：【】【高压气罐】【】/【散热装置】【铁板】【耐热金属块】/【电容】【加热装置】【打火石】
    u"combustion_chamber": dict(
        category=u"misc",
        pattern=[u" T ", u"HPK", u"CAF"],
        key={u"T": u"potato_s_t:high_pressure_tank", u"H": u"potato_s_t:heat_sink",
             u"P": u"potato_s_t:iron_plate", u"K": u"potato_s_t:heat_resistant_metal_block",
             u"C": u"potato_s_t:capacitor", u"A": u"potato_s_t:heater",
             u"F": u"minecraft:flint_and_steel"}),
}

# 只有电力高炉才做得出来的材料（拿它们当"造电力高炉"的材料 = 死锁）
EBF_GATED = {u"potato_s_t:high_carbon_steel", u"potato_s_t:steel_plate",
             u"potato_s_t:magnet", u"potato_s_t:titanium_ingot",
             u"potato_s_t:light_titanium_alloy"}

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


def load(name):
    t = read(os.path.join(RDIR, name + u".json"))
    if t is None:
        return None
    try:
        return json.loads(t)
    except Exception:
        return None


def main():
    print(u"=========== ZF100 校验：两条机器配方 + 电力高炉新锚点 + 燃烧反应室 ===========")

    print(u"\n== A 三条新配方逐格等于规格 ==")
    registered = set()
    for fn in ("ModItems.java", "ModBlocks.java"):
        registered |= set(re.findall(r'register\(\s*"([a-z0-9_]+)"', read(os.path.join(JAVA, fn)) or u""))
    vanilla_models = set()
    vpath = os.path.join(TOOLS, "check", "_vanilla_models.txt")
    if os.path.exists(vpath):
        vanilla_models = set(l.strip() for l in read(vpath).splitlines() if l.strip())
    for name in sorted(SPEC):
        spec = SPEC[name]
        obj = load(name)
        check(u"%s.json 能解析" % name, obj is not None)
        if obj is None:
            continue
        eq(u"%s: type" % name, u"minecraft:crafting_shaped", obj.get("type"))
        eq(u"%s: category" % name, spec["category"], obj.get("category"))
        eq(u"%s: 九宫格逐行" % name, spec["pattern"], obj.get("pattern"))
        rows = obj.get("pattern") or []
        eq(u"%s: 3 行 × 每行 3 格" % name, [3, 3, 3], [len(r) for r in rows])
        got = {}
        for ch, ing in (obj.get("key") or {}).items():
            got[ch] = ing.get("item") or (u"#" + ing.get("tag") if ing.get("tag") else u"（无）")
        eq(u"%s: 字母 → 材料" % name, spec["key"], got)
        check(u"%s: 每个字母正好一种材料（§4.63 不许一个字母两种材料）" % name,
              len(set(spec["key"].values())) == len(spec["key"]))
        used = set(u"".join(rows))
        eq(u"%s: key 里没有用不上的字母" % name, set(), set(spec["key"]) - used)
        eq(u"%s: 模式里没有 key 之外的字符" % name, set(), (used - set(spec["key"])) - {u" "})
        res = obj.get("result") or {}
        eq(u"%s: 产物 id" % name, u"potato_s_t:" + name, res.get("id"))
        eq(u"%s: 产物数量 1" % name, 1, res.get("count"))
        for ch, iid in sorted(spec["key"].items()):
            ns, _, path = iid.partition(u":")
            if ns == u"potato_s_t":
                check(u"%s/%s: %s 在本模组注册过" % (name, ch, iid), path in registered)
            elif vanilla_models:
                check(u"%s/%s: %s 是原版物品" % (name, ch, iid), path in vanilla_models)

    print(u"\n== B 设计红线：造电力高炉的东西不许依赖电力高炉自己 ==")
    bad = sorted(set(SPEC[u"electric_blast_furnace"]["key"].values()) & EBF_GATED)
    check(u"电力高炉主控的材料里没有「只有电力高炉才做得出来」的东西（%s）"
          % (u"、".join(bad) if bad else u"无"), not bad)
    print(u"    （注：燃烧反应室的图纸是**用户口述**的，里面用了耐热金属块，"
          u"而耐热金属块要电力高炉产的高碳钢 ⇒ 这台机器天然排在电力高炉之后，"
          u"这是用户的图纸、不是红线）")

    print(u"\n== C 产物唯一：每件只有一条配方 ==")
    names = sorted(n for n in os.listdir(RDIR) if n.endswith(u".json"))
    producers = {}
    for n in names:
        o = load(n[:-5])
        if not o:
            continue
        rid = (o.get("result") or {}).get("id")
        if rid:
            producers.setdefault(rid, []).append(n)
    for name in sorted(SPEC):
        eq(u"potato_s_t:%s 只有一条配方" % name,
           [name + u".json"], producers.get(u"potato_s_t:" + name, []))

    print(u"\n== D 电力高炉：锚点两种都认 ==")
    st = read(os.path.join(JAVA, "ElectricBlastFurnaceStructure.java")) or u""
    check(u"matches(CONTROLLER) 同时接受原版高炉与电力高炉自己",
          u"case CONTROLLER -> state.is(Blocks.BLAST_FURNACE)\n"
          u"                    || state.is(ModBlocks.ELECTRIC_BLAST_FURNACE.get());" in st)
    blk = read(os.path.join(JAVA, "ElectricBlastFurnaceBlock.java")) or u""
    check(u"「裸控制器 + 空手 Shift 右键」那条成型路仍在（本轮只是让它走得通）",
          u"&& !be.isFormed()" in blk
          and u"BlastFurnaceAssembly.form((ServerLevel) level, pos, facing);" in blk)

    print(u"\n== E 燃烧反应室：燃料 / 档案 / 罐的方向 / 状态码 / 粒子 / 捕获器 ==")
    cc = read(os.path.join(JAVA, "CombustionChamberBlockEntity.java")) or u""
    check(u"方块实体源码在", cc != u"")
    for const, val in ((u"OXYGEN_PER_OPERATION = 10", u"一次反应 10 mB 氧气"),
                       (u"CO2_PER_LOG = 10", u"原木出 10 mB 二氧化碳"),
                       (u"CHARCOAL_PER_LOG = 1", u"原木出 1 个木炭"),
                       (u"CO2_PER_LIQUID_FUEL = 200", u"柴油/汽油出 200 mB 二氧化碳"),
                       (u"WATER_PER_LIQUID_FUEL = 50", u"柴油/汽油出 50 mB 水"),
                       (u"CO2_PER_FUEL = 5", u"其余燃料出 5 mB 二氧化碳"),
                       (u"DURATION_DEFAULT = 3 * 20", u"默认 3 秒"),
                       (u"DURATION_LAVA = 10 * 20", u"岩浆桶 10 秒"),
                       (u"DURATION_LIQUID_FUEL = 30 * 20", u"柴油/汽油 30 秒"),
                       (u"POWER_DEFAULT = 800", u"默认动力 800"),
                       (u"POWER_DIESEL = 1200", u"柴油动力 1200"),
                       (u"POWER_GASOLINE = 1000", u"汽油动力 1000（用户当场拍板）"),
                       (u"OXYGEN_CAPACITY = 1200", u"氧气罐 1200 mB"),
                       (u"CO2_CAPACITY = 10000", u"二氧化碳罐 10000 mB"),
                       (u"TANK_COUNT = 3", u"三个罐"),
                       (u"SLOT_COUNT = 2", u"两个槽（燃料 + 副产物）")):
        check(u"%s —— %s" % (const, val), const in cc)
    check(u"燃料判定用原版熔炉的燃烧时间（getBurnTime(SMELTING)）",
          u"stack.getBurnTime(RecipeType.SMELTING) > 0" in cc)
    check(u"额外认本模组的柴油桶与汽油桶", u"stack.is(ModItems.DIESEL_BUCKET.get())" in cc
          and u"stack.is(ModItems.GASOLINE_BUCKET.get())" in cc)
    check(u"原木按原版 #minecraft:logs 标签认", u"stack.is(ItemTags.LOGS)" in cc)
    check(u"氧气罐只进不出（对外的 drain 分支里没有氧气罐；机器内部扣氧不算）",
          u"CombustionChamberBlockEntity.this.tanks[TANK_OXYGEN].drain" not in cc)
    check(u"二氧化碳罐只出不进（fill 只往氧气罐灌）",
          u"if (!isOxygen(resource)) {\n                return 0;\n            }" in cc)
    check(u"开始反应那一 tick 就扣燃料与氧气（用户原话「消耗一份燃料和10mB氧气开始反应」）",
          u"this.items.extractItem(FUEL_SLOT, 1, false);" in cc
          and u"this.tanks[TANK_OXYGEN].drain(OXYGEN_PER_OPERATION" in cc)
    check(u"结算前先看三个去处放不放得下（§4.14 不许吞东西）",
          u"if (co2Space() < this.activeCo2 || waterSpace() < this.activeWater)" in cc
          and u"if (!byproductFits(this.activeByproduct))" in cc)
    check(u"反应档案在开始时定死并存盘（中途换燃料不改变这一批）",
          u'tag.putInt("activeCo2"' in cc and u'tag.putInt("activePower"' in cc)
    check(u"状态灯新号 12（缺氧气）与 13（副产物槽放不下）", u"STATUS_NO_OXYGEN = 12" in cc
          and u"STATUS_BYPRODUCT = 13" in cc)
    check(u"黑烟用原版 SMOKE（不是白烟 CLOUD）", u"ParticleTypes.SMOKE" in cc
          and u"ParticleTypes.CLOUD" not in cc)
    check(u"黑烟在服务端发（§4.67：ServerLevel#sendParticles）",
          u"server.sendParticles(ParticleTypes.SMOKE" in cc and u"addParticle(" not in cc)
    check(u"黑烟的调用被 status=RUNNING 且 progress>0 两条闸门夹住",
          u"if (this.status != STATUS_RUNNING || this.progress <= 0) {" in cc)
    check(u"动力档对外只暴露 powerPerTick()", u"public int powerPerTick()" in cc)
    cap = read(os.path.join(JAVA, "PowerCapturerBlockEntity.java")) or u""
    check(u"动力能源捕获器的 6 面扫描认得燃烧反应室",
          u"instanceof CombustionChamberBlockEntity chamber" in cap
          and u"total += chamber.powerPerTick();" in cap)
    lamp = read(os.path.join(JAVA, r"client\gui\parts\StatusLampPart.java")) or u""
    check(u"状态灯部件把 12/13 都画成黄灯并给出文案后缀",
          u"STATUS_NO_OXYGEN," in lamp and u"STATUS_BYPRODUCT -> YELLOW" in lamp
          and u"-> \"no_oxygen\"" in lamp and u"-> \"byproduct\"" in lamp)
    # ⚠ 这台机器**没有能量能力**（用户没给能耗数）：PotatoST 里只登记两条能力（物品 + 流体），
    #   方块实体里连 EnergyStorage 这个词都不该出现。第一版这条写成"PotatoST.java 里有
    #   CombustionChamberBlockEntity 这个类名"—— 那个类名只出现在 ModBlocks 里 ⇒ 假 FAIL。
    pot = read(os.path.join(JAVA, "PotatoST.java")) or u""
    check(u"这台机器**没有能量能力**（用户没给能耗数）",
          pot.count(u"ModBlocks.COMBUSTION_CHAMBER_BE.get()") == 2
          and u"EnergyStorage" not in cc and u"MAX_ENERGY" not in cc)
    for f in ("CombustionChamberBlock.java", "CombustionChamberMenu.java",
              r"client\CombustionChamberScreen.java"):
        check(u"%s 在" % f, read(os.path.join(JAVA, f)) is not None)
    menu = read(os.path.join(JAVA, "CombustionChamberMenu.java")) or u""
    check(u"菜单与方块实体用**同一道**燃料门禁（§4.51）",
          u"return CombustionChamberBlockEntity.isFuel(stack);" in menu)
    scr = read(os.path.join(JAVA, r"client\CombustionChamberScreen.java")) or u""
    check(u"界面画三个罐（氧气/二氧化碳/水），且状态灯带自己的文案前缀",
          scr.count(u"new FluidTankPart(") == 3
          and u'gui.potato_s_t.combustion_chamber.status.' in scr)
    check(u"方块已进 mineable/pickaxe（否则挖了什么都不掉）",
          u'"potato_s_t:combustion_chamber"' in
          (read(os.path.join(RES, r"data\minecraft\tags\block\mineable\pickaxe.json")) or u""))

    print(u"\n== F 新气体二氧化碳：四处一起改（§6 清单）==")
    mf = read(os.path.join(JAVA, "ModFluids.java")) or u""
    check(u"① ModFluids 注册了 CARBON_DIOXIDE / FLOWING_CARBON_DIOXIDE",
          u'FLUIDS.register("carbon_dioxide"' in mf
          and u'FLUIDS.register("flowing_carbon_dioxide"' in mf)
    check(u"① 密度是负的（气体）", u".density(-44)" in mf)
    gas_body = re.search(r"public static boolean isGas\(Fluid fluid\)\s*\{(.*?)\n    \}",
                         mf, re.S)
    hits = len(re.findall(r"fluid == \w+\.get\(\)", gas_body.group(1) if gas_body else u""))
    eq(u"② isGas 正向白名单 = %d 个变体（6 种 × 2）" % EXPECT_GAS_VARIANTS, EXPECT_GAS_VARIANTS, hits)
    check(u"② isGas 里没有负向写法", u"!=" not in (gas_body.group(1) if gas_body else u"!="))
    client = read(os.path.join(JAVA, "PotatoSTClient.java")) or u""
    check(u"③ 客户端登记了 carbon_dioxide 的流体贴图",
          u'textures("carbon_dioxide")' in client)
    for p in (r"textures\block\carbon_dioxide_still.png",
              r"textures\block\carbon_dioxide_flow.png"):
        check(u"③ %s 在" % p, os.path.exists(os.path.join(RES, r"assets\potato_s_t", p)))
    ftag = os.path.join(RES, r"data\c\tags\fluid")
    check(u"④ c:carbon_dioxide 标签挂了本体 + 流动",
          json.loads(read(os.path.join(ftag, "carbon_dioxide.json")))[u"values"]
          == [u"potato_s_t:carbon_dioxide", u"potato_s_t:flowing_carbon_dioxide"])
    gas = json.loads(read(os.path.join(ftag, "gaseous.json")))[u"values"]
    check(u"④ #c:gaseous 里也有二氧化碳（%d 条）" % len(gas),
          u"potato_s_t:carbon_dioxide" in gas and u"potato_s_t:flowing_carbon_dioxide" in gas)
    lang0 = json.loads(read(os.path.join(RES, r"assets\potato_s_t\lang\zh_cn.json")))
    eq(u"④ 语言里有流体名", u"二氧化碳", lang0.get(u"fluid_type.potato_s_t.carbon_dioxide"))
    jm = read(os.path.join(JAVA, "MachineRecipes.java")) or u""
    check(u"④ JEI 灌装机那张表也加了二氧化碳（气体 5 → 6 种）",
          u"ModFluids.CARBON_DIOXIDE.get()" in jm)

    print(u"\n== G 探针取证（真服务端上的 %s）==" % os.path.basename(PROBE))
    rep = read(PROBE)
    check(u"探针报告在", rep is not None)
    if rep:
        eq(u"报告里 FAIL = 0", 0, len(re.findall(r"\[FAIL\]", rep)))
        check(u"报告结论是「全部成立」", u"全部成立（0 项不符）" in rep)
        for line in (u"摆**自己造的主控** + 外围壳 ⇒ validate() 通过（本轮新开的路）",
                     u"拆解后锚点那格是空气（不许原地留一台）",
                     u"拆解后另外 26 格全部还原成建材",
                     u"老路：围着**原版高炉**搭好壳 ⇒ validate() 仍然通过",
                     u"外壳缺一角 ⇒ validate() 必须报错",
                     u"硬摆 combustion_chamber 的九宫格 ⇒ 命中的是 potato_s_t:combustion_chamber",
                     u"开始反应那一 tick 就扣掉 1 份燃料",
                     u"原木跑完出 10 mB 二氧化碳",
                     u"原木跑完副产物槽里有 1 个木炭",
                     u"原木跑完出 0 mB 水",
                     u"氧气罐**抽不走**",
                     u"没有氧气 ⇒ 状态灯 12",
                     u"副产物槽堵着 ⇒ 状态灯 13",
                     u"相邻捕获器把反应室算进产量",
                     u"柴油跑完：200 mB 二氧化碳 + 50 mB 水",
                     # ⚠ 这是 **ZF100 那一轮探针报告里冻着的那句话**（41 条），不是当前值：
                     #    当前值由 EXPECT_SHAPED 管（ZF101 起是 42）
                     u"本模组 crafting 配方 = 41 条"):
            hit = [l for l in rep.splitlines() if line in l and u"[OK]" in l]
            check(u"探针里这条是 [OK]：%s" % line, bool(hit))

    print(u"\n== H 只新增不改旧（独立证据源 = 改前那份成品 jar）==")
    if not os.path.exists(PRE_JAR):
        print(u"    （找不到 %s ⇒ 这几条跳过）" % PRE_JAR)
    else:
        eq(u"改前 jar 就是 ZF99 那一版", PRE_SHA, sha1f(PRE_JAR))
        with zipfile.ZipFile(PRE_JAR) as zf:
            inside = {n.split(u"/")[-1]: zf.read(n) for n in zf.namelist()
                      if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")}
        changed = [n for n in sorted(inside)
                   if not os.path.exists(os.path.join(RDIR, n))
                   or open(os.path.join(RDIR, n), "rb").read() != inside[n]]
        eq(u"改前那 %d 份配方逐字节未变" % len(inside), [], changed)
        extra = set(n for n in os.listdir(RDIR) if n.endswith(u".json")) - set(inside)
        # ⚠ 新增名单随轮次增长（ZF101 起多一份酸性反应室）—— "改前那些逐字节未变"才是这条的内容
        eq(u"盘上比改前多出来的就是预期的那些（+ ZF101 的酸性反应室）",
           sorted([n + u".json" for n in SPEC] + [u"acidic_reaction_chamber.json"]), sorted(extra))

    print(u"\n== I 活体数字 / 往轮断言 / 文档 / 成品 ==")
    shaped = [n for n in names if (load(n[:-5]) or {}).get("type") == u"minecraft:crafting_shaped"]
    eq(u"盘上定形配方总数", EXPECT_SHAPED, len(shaped))
    fl = len(re.findall(r'FLUID_TYPES\.register\("', read(os.path.join(JAVA, "ModFluids.java")) or u""))
    eq(u"流体类型总数", EXPECT_FLUIDS, fl)
    for f, anchor in ((u"_zf71_verify.py", u"check(craft == %d," % EXPECT_SHAPED),
                      (u"_zf71_verify.py", u"check(fl == %d" % EXPECT_FLUIDS),
                      (u"_zf95_verify.py", u"EXPECT_SHAPED = %d" % EXPECT_SHAPED),
                      (u"_zf96_verify.py", u"EXPECT_SHAPED = %d" % EXPECT_SHAPED),
                      (u"_zf97_verify.py", u"EXPECT_SHAPED = %d" % EXPECT_SHAPED),
                      (u"_zf97_verify.py", u"EXPECT_FLUIDS = %d" % EXPECT_FLUIDS),
                      (u"_zf97_verify.py", u"EXPECT_GAS_VARIANTS = %d" % EXPECT_GAS_VARIANTS),
                      (u"_zf73_verify.py", u"gas_hits == %d)" % EXPECT_GAS_VARIANTS),
                      (u"_zf74_verify.py", u")) == %d)" % EXPECT_GAS_VARIANTS)):
        check(u"%s 的活体数字已跟到（%s）" % (f, anchor), anchor in (read(os.path.join(TOOLS, f)) or u""))
    z73r = read(os.path.join(TOOLS, u"_zf73_repro.py")) or u""
    z73v = read(os.path.join(TOOLS, u"_zf73_verify.py")) or u""
    for n in sorted(SPEC):
        check(u"_zf73_repro.py 的新增名单里有 %s.json" % n, u'"%s.json"' % n in z73r)
        check(u"_zf73_verify.py 的 D2 名单里有 %s.json" % n, u'"%s.json"' % n in z73v)
    fal = read(os.path.join(TOOLS, u"_zf78_falsify.py")) or u""
    check(u"本脚本已挂进 _zf78_falsify.py 的 VERIFIERS", u'"_zf100_verify.py"' in fal)
    for k in (u"K69 ", u"K70 ", u"K71 ", u"K72 ", u"K73 "):
        check(u"_zf78_falsify.py 里有刀 %s" % k, (u'u"%s' % k) in fal)
    gates = read(os.path.join(TOOLS, u"_zf100_gates.ps1")) or u""
    check(u"本轮闸门脚本在、且声明了 ZF100 那一段", u"_zf100_verify.py" in gates)
    check(u"闸门脚本把 gatecount 也算进去", u"_zf100_gatecount.py" in gates)

    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    check(u"档案 §5 有 ZF100 那一行", u"| ZF100 |" in arch)
    check(u"档案 §9 有 ZF100 那一节", u"### ZF100（0.11）" in arch)
    check(u"档案 §4 有本轮那条规矩（配方要跟机器锚点一起改）", u"### 4.68 " in arch)
    check(u"档案记了燃烧反应室的图纸与三个罐", u"燃烧反应室" in arch and u"10000" in arch)
    check(u"公告不再说锂电池「没有配方」，改成这三件仍没有",
          u"the Stable Metal Block have no crafting recipe yet" not in ann
          and u"no crafting recipe yet" in ann)
    check(u"公告写了锂电池与高炉主控这版拿到了配方", u"got their recipes in this build" in ann)
    check(u"公告写了电力高炉两种锚点都行",
          u"either a vanilla blast furnace or this mod's own controller" in ann)
    check(u"公告写了燃烧反应室", u"Combustion Reaction Chamber" in ann)

    lang = {}
    for f in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        d = json.loads(read(os.path.join(RES, r"assets\potato_s_t\lang", f)))
        lang[f] = d
        eq(u"%s 键数" % f, EXPECT_KEYS, len(d))
    for k in (u"block.potato_s_t.combustion_chamber", u"tooltip.potato_s_t.combustion_chamber",
              u"gui.potato_s_t.combustion_chamber.status.running",
              u"gui.potato_s_t.combustion_chamber.status.no_oxygen",
              u"gui.potato_s_t.combustion_chamber.status.byproduct",
              u"gui.potato_s_t.combustion_chamber.pour.empty",
              u"gui.potato_s_t.combustion_chamber.pour.rejected",
              u"fluid_type.potato_s_t.carbon_dioxide"):
        check(u"四语言都有 %s" % k, all(k in lang[f] for f in lang))

    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            inner = zf.namelist()
            for n in sorted(SPEC):
                check(u"成品里有 data/potato_s_t/recipe/%s.json" % n,
                      u"data/potato_s_t/recipe/%s.json" % n in inner)
            check(u"成品里有燃烧反应室的 class",
                  u"com/potatost/mod/CombustionChamberBlockEntity.class" in inner)
            check(u"成品里有二氧化碳的两张贴图",
                  u"assets/potato_s_t/textures/block/carbon_dioxide_still.png" in inner)
            probes = [n for n in inner if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
            eq(u"成品里没有探针 class", [], probes)
            check(u"成品里 zh_cn 仍是 %d 键" % EXPECT_KEYS,
                  len(json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
                  == EXPECT_KEYS)

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
