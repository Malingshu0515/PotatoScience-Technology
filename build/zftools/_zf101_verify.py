# -*- coding: utf-8 -*-
r"""_zf101_verify.py —— ZF101 常驻校验：酸性反应室 + 三种新酸

用户原话（一条到底）：

  「加一个酸性反应室（配方【铜块】【稳定金属块】【加热装置】，【钛锭】【灌装机】【钛锭】，
    【红石火把】【电解器】【拉杆】）Gui 输入；二氧化碳储罐 氧气储罐 氨气储罐 水储罐（各1000Mb）
    一个硫槽位 输出槽；硝酸 硫酸 碳酸储罐各1000Mb 三个选择按钮 在储罐下方 选择则执行相应的配方
    （gui别的你发挥）配方；1.10mb二氧化碳+1mb水 产出1mb碳酸 2.1mb氧气+1mb氨气 产出1mb硝酸
    3.10个硫+100MB水 产出100MB硫酸 耗能皆为500fe/t 储能12400fe」

骨架：
  A 配方（用户给的九宫格）逐格等于规格
  B 三个配方与三种节奏（1/2 号每 tick、3 号一批）+ 用户给的数一个不改
  C 七个罐的方向：四种原料只进不出、三种酸只出不进
  D 界面：三个按钮走菜单按钮通道 + 七个罐 + 能量条 + 状态灯（新号 14）
  E 三种酸是**液体不是气体**（§6 的"加流体四处一起改"）
  F 探针取证 / 只新增不改旧 / 活体数字 / 文档 / 成品 jar
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
PRE_JAR = r"C:\PotatoST救援\zf101_pre\release\PotatoST-0.11.jar"
PRE_SHA = u"d47203540f4d8da703ee01a8764bdcf5de363f01"
PROBE = os.path.join(TOOLS, "_zf101_probe_utf8.txt")

EXPECT_SHAPED = 51          # ZF100 的 41 + 本轮 1
EXPECT_KEYS = 492           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键 + ZF125 柴油发电机 11 键
EXPECT_FLUIDS = 15          # ZF100 的 11 + 三种酸

ACIDS = (u"carbonic_acid", u"nitric_acid", u"sulfuric_acid")

SPEC = dict(
    pattern=[u"CSH", u"TFT", u"REL"],
    key={u"C": u"minecraft:copper_block", u"S": u"potato_s_t:stable_metal_block",
         u"H": u"potato_s_t:heater", u"T": u"potato_s_t:titanium_ingot",
         u"F": u"potato_s_t:filling_machine", u"R": u"minecraft:redstone_torch",
         u"E": u"potato_s_t:electrolyzer", u"L": u"minecraft:lever"})

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
    print(u"=========== ZF101 校验：酸性反应室 + 三种新酸 ===========")
    be = read(os.path.join(JAVA, "AcidicReactionChamberBlockEntity.java")) or u""
    scr = read(os.path.join(JAVA, r"client\AcidicReactionChamberScreen.java")) or u""
    menu = read(os.path.join(JAVA, "AcidicReactionChamberMenu.java")) or u""
    mf = read(os.path.join(JAVA, "ModFluids.java")) or u""

    print(u"\n== A 配方：用户给的九宫格逐格 ==")
    obj = json.loads(read(os.path.join(RDIR, "acidic_reaction_chamber.json")) or u"{}")
    eq(u"type", u"minecraft:crafting_shaped", obj.get("type"))
    eq(u"九宫格逐行", SPEC["pattern"], obj.get("pattern"))
    got = {}
    for ch, ing in (obj.get("key") or {}).items():
        got[ch] = ing.get("item") or (u"#" + ing.get("tag") if ing.get("tag") else u"（无）")
    eq(u"字母 → 材料", SPEC["key"], got)
    eq(u"产物", u"potato_s_t:acidic_reaction_chamber", (obj.get("result") or {}).get("id"))
    eq(u"产物数量", 1, (obj.get("result") or {}).get("count"))
    check(u"每个字母一种材料（§4.63）", len(set(SPEC["key"].values())) == len(SPEC["key"]))
    reg = set()
    for fn in ("ModItems.java", "ModBlocks.java"):
        reg |= set(re.findall(r'register\(\s*"([a-z0-9_]+)"', read(os.path.join(JAVA, fn)) or u""))
    for ch, iid in sorted(SPEC["key"].items()):
        if iid.startswith(u"potato_s_t:"):
            check(u"%s（%s）在本模组注册过" % (iid, ch), iid.split(u":")[1] in reg)
    # ⚠ 用户图纸用了"稳定金属块"，而它自己没有配方 ⇒ 记一笔（不是 FAIL，是事实）
    stable_owner = [n for n in os.listdir(RDIR)
                    if (json.loads(read(os.path.join(RDIR, n))) or {}).get("result", {}).get("id")
                    == u"potato_s_t:stable_metal_block"]
    print(u"    ⚠ 稳定金属块自己的配方数 = %d（0 ⇒ 这台机器目前只能创造拿，已挂 §9 待办）"
          % len(stable_owner))

    print(u"\n== B 三个配方与两种节奏（用户给的数一个不改）==")
    for const, note in ((u"ENERGY_PER_TICK = 500", u"耗能 500 FE/t"),
                        (u"MAX_ENERGY = 12400", u"储能 12400 FE"),
                        (u"TANK_CAPACITY = 1000", u"七个罐各 1000 mB"),
                        (u"CARBONIC_CO2_PER_TICK = 10", u"1 号：10 mB 二氧化碳"),
                        (u"CARBONIC_WATER_PER_TICK = 1", u"1 号：1 mB 水"),
                        (u"CARBONIC_OUT_PER_TICK = 1", u"1 号：出 1 mB 碳酸"),
                        (u"NITRIC_OXYGEN_PER_TICK = 1", u"2 号：1 mB 氧气"),
                        (u"NITRIC_AMMONIA_PER_TICK = 1", u"2 号：1 mB 氨气"),
                        (u"NITRIC_OUT_PER_TICK = 1", u"2 号：出 1 mB 硝酸"),
                        (u"SULFUR_PER_BATCH = 10", u"3 号：10 个硫"),
                        (u"SULFURIC_WATER_PER_BATCH = 100", u"3 号：100 mB 水"),
                        (u"SULFURIC_OUT_PER_BATCH = 100", u"3 号：出 100 mB 硫酸"),
                        (u"SULFURIC_DURATION_TICKS = 100", u"3 号：一批 100 tick（= 5 秒，我定的）"),
                        # ⚠ ZF102 把罐加到 10、配方加到 4（这一行跟着改；ZF101 当年的数是 7 / 3）
                        (u"TANK_COUNT = 10", u"十个罐（ZF102 起：6 进 4 出）"),
                        (u"SLOT_COUNT = 2", u"两个槽（硫 + 输出）"),
                        (u"RECIPE_COUNT = 4", u"四个配方（ZF102 起）")):
        check(u"%s —— %s" % (const, note), const in be)
    check(u"1/2 号是每 tick 一次（continuousTick）", u"private void continuousTick()" in be)
    check(u"3 号是批次式（batchTick）", u"private void batchTick()" in be)
    check(u"3 号的材料在**最后一 tick** 才扣（前面只推进度）",
          u"this.items.extractItem(SULFUR_SLOT, SULFUR_PER_BATCH, false);" in be
          and u"if (this.progress + 1 < this.progressMax) {" in be)
    check(u"三种岔路都在（没电 3 / 原料不足 14 / 产物罐满 4）",
          u"STATUS_NO_POWER = 3" in be and u"STATUS_INPUTS = 14" in be
          and u"STATUS_OUTPUT_FULL = 4" in be and u"STATUS_MATERIAL = 6" in be)
    check(u"电不够时一滴原料都不动（检查在扣料之前）",
          be.find(u"if (this.energy < ENERGY_PER_TICK)") < be.find(u"this.energy -= ENERGY_PER_TICK;"))

    print(u"\n== C 罐的方向（ZF102 起：6 进 4 出）==")
    check(u"灌入只认那几种原料（ZF102 加了氢/氯两条分支）", u"if (isCarbonDioxide(resource)) {" in be
          and u"if (isOxygen(resource)) {" in be and u"if (isAmmonia(resource)) {" in be
          and u"if (isWater(resource)) {" in be and be.count(u"            return 0;\n") >= 1)
    # ⚠ ZF102：产物罐从"写死区间"改成了 OUTPUT_TANKS 表（新增盐酸罐时不想再数区间）
    check(u"抽走只在产物罐表里找（原料罐永远抽不走）",
          u"for (int tank : OUTPUT_TANKS)" in be and u"OUTPUT_TANKS = {" in be)
    check(u"输出罐不接收灌入（isFluidValid 只在输入罐表里放行）",
          u"return isInputTank(tank)" in be and u"INPUT_TANKS = {" in be)
    check(u"硫槽只收硫（与菜单同一道门禁 §4.51）",
          u"return slot == SULFUR_SLOT && stack.is(ModItems.SULFUR.get());" in be
          and u"return stack.is(ModItems.SULFUR.get());" in menu)

    print(u"\n== D 界面：三个按钮 + 菜单按钮通道 ==")
    check(u"三个按钮是依次加的（RECIPE_COUNT 个）",
          u"for (int recipe = 0; recipe < AcidicReactionChamberBlockEntity.RECIPE_COUNT; recipe++)" in scr)
    check(u"按钮在产物储罐下方（y=110，储罐 y=64+40）",
          u"BUTTON_Y = 110" in scr and u"OUTPUT_Y = 64" in scr)
    check(u"按钮走原版菜单按钮通道（handleInventoryButtonClick）",
          u"handleInventoryButtonClick(screen.getMenu().containerId, this.recipe)" in
          (read(os.path.join(JAVA, r"client\gui\parts\RecipeButtonPart.java")) or u""))
    check(u"菜单那一侧 clickMenuButton 再校验一次配方号",
          u"public boolean clickMenuButton(Player player, int id)" in menu
          and u"AcidicReactionChamberBlockEntity.isValidRecipe(id)" in menu
          and u"this.machine.setSelected(id);" in menu)
    check(u"界面画 10 个罐（ZF102 起 6 进 4 出）+ 能量条 + 进度条 + 状态灯",
          scr.count(u"new FluidTankPart(") == 10 and u"new EnergyBarPart(" in scr
          and u"new ProgressBarPart(" in scr and u"new StatusLampPart(" in scr)
    check(u"状态灯带自己的文案前缀（§6.10 ⑪）",
          u'gui.potato_s_t.acidic_reaction_chamber.status.' in scr)
    check(u"界面基类新增了鼠标点击通路（老部件默认不受影响）",
          u"default boolean mouseClicked(MachineScreen<?> screen, double mouseX, double mouseY, int button)" in
          (read(os.path.join(JAVA, r"client\gui\GuiPart.java")) or u"")
          and u"public boolean mouseClicked(double mouseX, double mouseY, int button)" in
          (read(os.path.join(JAVA, r"client\gui\MachineScreen.java")) or u""))
    lamp = read(os.path.join(JAVA, r"client\gui\parts\StatusLampPart.java")) or u""
    check(u"状态灯部件给 14 号配了黄灯与文案后缀",
          u"STATUS_INPUTS -> YELLOW" in lamp and u'-> "inputs"' in lamp)

    print(u"\n== E 三种酸：液体不是气体（§6 四处一起改）==")
    for name in ACIDS:
        reg_ok = (
            u'FLUID_TYPES.register("%s"' % name in mf
            and u'FLUIDS.register("%s"' % name in mf
            and u'FLUIDS.register("flowing_%s"' % name in mf
        )
        check(u"%s：FluidType + Source + Flowing 都注册了" % name, reg_ok)
        check(u"%s：客户端有贴图注册" % name,
              u'textures("%s")' % name in (read(os.path.join(JAVA, "PotatoSTClient.java")) or u""))
        for suffix in ("still", "flow"):
            check(u"%s_%s.png 在" % (name, suffix),
                  os.path.exists(os.path.join(RES, r"assets\potato_s_t\textures\block",
                                              u"%s_%s.png" % (name, suffix))))
        tag = json.loads(read(os.path.join(RES, r"data\c\tags\fluid", name + u".json")) or u"{}")
        eq(u"c:%s 标签两份" % name,
           [u"potato_s_t:" + name, u"potato_s_t:flowing_" + name], tag.get(u"values"))
    gas_body = re.search(r"public static boolean isGas\(Fluid fluid\)\s*\{(.*?)\n    \}", mf, re.S)
    body = gas_body.group(1) if gas_body else u""
    for name in ACIDS:
        check(u"%s **不在** isGas 白名单里（酸是液体，气罐该拒收、油桶该收）" % name,
              (u"CARBONIC_ACID.get()" not in body if name == "carbonic_acid" else True)
              and (u"SULFURIC_ACID.get()" not in body) and (u"NITRIC_ACID.get()" not in body))
    gaseous = json.loads(read(os.path.join(RES, r"data\c\tags\fluid\gaseous.json")) or u"{}")
    for name in ACIDS:
        check(u"%s **不在** #c:gaseous 里" % name,
              all(u"potato_s_t:" + name != v for v in gaseous.get(u"values", [])))

    print(u"\n== F 探针取证 ==")
    rep = read(PROBE)
    check(u"探针报告在（%s）" % os.path.basename(PROBE), rep is not None)
    if rep:
        eq(u"报告里 FAIL = 0", 0, len(re.findall(r"\[FAIL\]", rep)))
        check(u"报告结论是「全部成立」", u"全部成立（0 项不符）" in rep)
        for line in (u"硬摆用户那张九宫格 ⇒ 命中一条配方",
                     u"红石火把换成普通火把 ⇒ 不出这台机器",
                     u"0 号一 tick：二氧化碳 20 → 10",
                     u"1 号一 tick：氨气 10 → 9",
                     u"2 号第 1 tick：进度 0 → 1",
                     u"2 号跑完：10 个硫全被吃掉",
                     u"2 号这一批一共花了 50,000 FE",
                     u"电只有 499 ⇒ 状态 = 没电 3",
                     u"二氧化碳罐空了 ⇒ 状态 = 流体原料不足 14",
                     u"碳酸罐满了 ⇒ 状态 = 产物罐满 4",
                     u"想抽走二氧化碳 ⇒ 抽不出来",
                     u"往这台机器灌碳酸 ⇒ 一滴不收",
                     u"配方号 -1 / 3 / 99 都不合法"):
            hit = [l for l in rep.splitlines() if line in l and u"[OK]" in l]
            check(u"探针里这条是 [OK]：%s" % line, bool(hit))

    print(u"\n== G 只新增不改旧 / 活体数字 / 文档 / 成品 ==")
    if os.path.exists(PRE_JAR):
        eq(u"改前 jar 就是 ZF100 那一版", PRE_SHA, sha1f(PRE_JAR))
        with zipfile.ZipFile(PRE_JAR) as zf:
            inside = {n.split(u"/")[-1]: zf.read(n) for n in zf.namelist()
                      if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")}
        names = sorted(n for n in os.listdir(RDIR) if n.endswith(u".json"))
        changed = [n for n in sorted(inside)
                   if n not in names or open(os.path.join(RDIR, n), "rb").read() != inside[n]]
        eq(u"改前那 %d 份配方逐字节未变" % len(inside), [], changed)
        eq(u"盘上比改前正好多这一份", [u"acidic_reaction_chamber.json"],
           sorted(set(names) - set(inside)))
    else:
        print(u"    （找不到改前 jar ⇒ 这几条跳过）")
    shaped = [n for n in os.listdir(RDIR)
              if (json.loads(read(os.path.join(RDIR, n))) or {}).get("type") == u"minecraft:crafting_shaped"]
    eq(u"盘上定形配方总数", EXPECT_SHAPED, len(shaped))
    fl = len(re.findall(r'FLUID_TYPES\.register\("', mf))
    eq(u"流体类型总数", EXPECT_FLUIDS, fl)
    for f, anchor in ((u"_zf71_verify.py", u"check(craft == %d," % EXPECT_SHAPED),
                      (u"_zf71_verify.py", u"check(fl == %d" % EXPECT_FLUIDS),
                      (u"_zf95_verify.py", u"EXPECT_SHAPED = %d" % EXPECT_SHAPED),
                      (u"_zf96_verify.py", u"EXPECT_SHAPED = %d" % EXPECT_SHAPED),
                      (u"_zf97_verify.py", u"EXPECT_SHAPED = %d" % EXPECT_SHAPED),
                      (u"_zf97_verify.py", u"EXPECT_FLUIDS = %d" % EXPECT_FLUIDS),
                      (u"_zf100_verify.py", u"EXPECT_SHAPED = %d" % EXPECT_SHAPED),
                      (u"_zf100_verify.py", u"EXPECT_KEYS = %d" % EXPECT_KEYS)):
        check(u"%s 跟到了 %s" % (f, anchor), anchor in (read(os.path.join(TOOLS, f)) or u""))
    z100 = read(os.path.join(TOOLS, u"_zf100_verify.py")) or u""
    check(u"_zf100_verify.py 的键数已跟到 %d" % EXPECT_KEYS, u"EXPECT_KEYS = %d" % EXPECT_KEYS in z100)
    fal = read(os.path.join(TOOLS, u"_zf78_falsify.py")) or u""
    check(u"本脚本已挂进 _zf78_falsify.py 的 VERIFIERS", u'"_zf101_verify.py"' in fal)
    for k in (u"K74 ", u"K75 ", u"K76 ", u"K77 "):
        check(u"_zf78_falsify.py 里有刀 %s" % k, (u'u"%s' % k) in fal)
    gates = read(os.path.join(TOOLS, u"_zf101_gates.ps1")) or u""
    check(u"本轮闸门脚本在、且声明了 ZF101 那一段", u"_zf101_verify.py" in gates)

    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    check(u"档案 §5 有 ZF101 那一行", u"| ZF101 |" in arch)
    check(u"档案 §9 有 ZF101 那一节", u"### ZF101（0.11）" in arch)
    check(u"档案记了「稳定金属块没配方 ⇒ 这台机器暂时做不出来」", u"稳定金属块" in arch)
    check(u"公告里有酸性反应室", u"Acidic Reaction Chamber" in ann)
    lang = {}
    for f in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"ru_ru.json"):
        d = json.loads(read(os.path.join(RES, r"assets\potato_s_t\lang", f)))
        lang[f] = d
        eq(u"%s 键数" % f, EXPECT_KEYS, len(d))
    for k in (u"block.potato_s_t.acidic_reaction_chamber", u"tooltip.potato_s_t.acidic_reaction_chamber",
              u"gui.potato_s_t.acidic_reaction_chamber.status.running",
              u"gui.potato_s_t.acidic_reaction_chamber.status.inputs",
              u"gui.potato_s_t.acidic_reaction_chamber.status.no_power",
              u"gui.potato_s_t.acidic_reaction_chamber.recipe.name.0",
              u"gui.potato_s_t.acidic_reaction_chamber.recipe.info.2",
              u"fluid_type.potato_s_t.carbonic_acid", u"fluid_type.potato_s_t.sulfuric_acid"):
        check(u"四语言都有 %s" % k, all(k in lang[f] for f in lang))

    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            inner = zf.namelist()
            check(u"成品里有 recipe/acidic_reaction_chamber.json",
                  u"data/potato_s_t/recipe/acidic_reaction_chamber.json" in inner)
            for rel in (u"com/potatost/mod/AcidicReactionChamberBlockEntity.class",
                        u"com/potatost/mod/client/gui/parts/RecipeButtonPart.class",
                        u"assets/potato_s_t/textures/block/sulfuric_acid_still.png",
                        u"data/c/tags/fluid/nitric_acid.json"):
                check(u"成品里有 %s" % rel, rel in inner)
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
