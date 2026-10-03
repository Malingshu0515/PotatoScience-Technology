# -*- coding: utf-8 -*-
r'''_zf162_verify.py —— ZF162（0.13 第六笔）**常驻校验**：删扳手 + 删电力高炉物品形态 + 灌装机放开槽位。

用户原话（2026-09-28）：「删除一下 1.扳手 2.物品形式的电力高炉（这两个有bug没必要修了）
然后给罐装机改一下 所有物品都可以放进去 只不过检测到能被罐装的才可以罐装
（例如mek的喷气背包 目前好像不可以放进去罐咱们mod里的氢）（高压气罐只支持气体 油桶只支持液体 这两个不要动）」

  A 扳手删干净（物品/模型/贴图/五语键/模块类/三处拆解入口/手册图标）
  B 电力高炉**物品形态**删干净（注册/配方/贴图/创造页/JEI 图标/进度改自建触发器/手册图标），
    而**方块本体与它的方块贴图一个字节都没动**
  C 灌装机：三道门全部放开、灌装只认"能力"（自己那两种 + 别的 mod 的 FluidHandler.ITEM）、
    诊断新增 UNSUPPORTED、**气罐/油桶那五个文件改前件 ↔ 盘上逐字节相同**（用户说"不要动"）
  D 表与生成器同口径、五语键数 645/645/645/645/653、文档（§4.169 / §5 ZF162 行 / 公告 / 交接）

跑法：python build\zftools\_zf162_verify.py
'''
import hashlib
import io
import json
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(ASSETS, "lang")
DATA = os.path.join(ROOT, r"src\main\resources\data\potato_s_t")
BOOK = os.path.join(ASSETS, r"patchouli_books\guide\en_us")
PRE = os.path.join(r"C:\PotatoST救援", "zf162_pre")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label if not detail else u"%s（%s）" % (label, detail))
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else u""


def raw(p):
    with open(p, "rb") as fh:
        return fh.read()


def sha1(p):
    return hashlib.sha1(raw(p)).hexdigest()


def src(name):
    return read(os.path.join(JAVA, name))


def code_only(text):
    u"""去掉整行注释后的代码 —— 判据要认**代码**，不认注释（§4 的老账：注释里写一句就能骗过门）。"""
    keep = []
    for line in text.split(u"\n"):
        s = line.strip()
        if s.startswith(u"//") or s.startswith(u"*") or s.startswith(u"/*"):
            continue
        keep.append(line)
    return u"\n".join(keep)


def book(rel):
    return read(os.path.join(BOOK, rel))


def lang(loc):
    p = os.path.join(LANG, loc + u".json")
    if not os.path.isfile(p):
        return {}
    return json.loads(io.open(p, encoding="utf-8").read())


def walk_java():
    out = {}
    for root, _dirs, files in os.walk(JAVA):
        for f in files:
            if f.endswith(".java"):
                p = os.path.join(root, f)
                out[os.path.relpath(p, JAVA)] = read(p)
    return out


def grep_java(pattern):
    rx = re.compile(pattern)
    hits = []
    for rel, text in walk_java().items():
        for i, line in enumerate(text.split(u"\n"), 1):
            if rx.search(line):
                hits.append(u"%s:%d: %s" % (rel, i, line.strip()[:90]))
    return hits


print(u"=== A 段：扳手删干净 ===")
mi = src(u"ModItems.java")
check(u'"wrench"' not in mi and u"WRENCH" not in mi, u"A1 ModItems 里没有扳手的注册", u"" if u"WRENCH" not in mi else u"还有 WRENCH")
hits = grep_java(r"wrench|WRENCH|Wrench")
check(not hits, u"A2 src/main/java 里 wrench/WRENCH 出现 0 次", u" / ".join(hits[:3]))
check(not os.path.isfile(os.path.join(JAVA, u"ElectricBlastFurnaceWrench.java")), u"A3 ElectricBlastFurnaceWrench.java 已删")
check(not os.path.isfile(os.path.join(ASSETS, r"models\item\wrench.json")), u"A4 models/item/wrench.json 已删")
check(not os.path.isfile(os.path.join(ASSETS, r"textures\item\wrench.png")), u"A5 textures/item/wrench.png 已删")
for name in (u"ElectricBlastFurnaceBlock.java", u"ElectricBlastFurnacePartBlock.java", u"AlloySmelterBlock.java"):
    t = src(name)
    check(u"useItemOn" not in t, u"A6 %s 里没有扳手拆解入口（useItemOn）" % name)
wi = [loc for loc in LOCALES if u"item.potato_s_t.wrench" in lang(loc)]
check(not wi, u"A7 五语都没有 item.potato_s_t.wrench", u" / ".join(wi))
check(u"potato_s_t:wrench" not in book(r"categories\faq.json")
      and u"potato_s_t:wrench" not in book(r"entries\faq\machine.json")
      and u"potato_s_t:wrench" not in book(r"entries\getting_started\rules.json"),
      u"A8 手册三个图标不再指向扳手")
check(u'"icon": "potato_s_t:filling_machine"' in book(r"categories\faq.json")
      and u'"icon": "potato_s_t:filling_machine"' in book(r"entries\faq\machine.json")
      and u'"icon": "patchouli:guide_book"' in book(r"entries\getting_started\rules.json"),
      u"A9 三个图标都换成了真实存在的物品（灌装机 / 手册本体）")
check(u"wrench" not in read(os.path.join(ZT, u"_zf148_book.py")), u"A10 手册生成器 _zf148_book.py 跟着改了（表 ↔ 盘同口径）")

print(u"\n=== B 段：电力高炉的物品形态删干净（方块本体不许动）===")
mb = src(u"ModBlocks.java")
check(u"ELECTRIC_BLAST_FURNACE_ITEM" not in mb, u"B1 ModBlocks 里没有 ELECTRIC_BLAST_FURNACE_ITEM")
hits = grep_java(r"ELECTRIC_BLAST_FURNACE_ITEM|electric_blast_furnace\"")
check(not grep_java(r"ELECTRIC_BLAST_FURNACE_ITEM"), u"B2 全工程没有 ELECTRIC_BLAST_FURNACE_ITEM 的引用",
      u" / ".join(grep_java(r"ELECTRIC_BLAST_FURNACE_ITEM")[:3]))
check(u"ELECTRIC_BLAST_FURNACE = BLOCKS.register(\"electric_blast_furnace\"" in mb, u"B3 控制器**方块**本体仍在注册")
check(os.path.isfile(os.path.join(ASSETS, r"textures\block\electric_blast_furnace.png")), u"B4 方块贴图 textures/block/electric_blast_furnace.png 仍在")
check(not os.path.isfile(os.path.join(ASSETS, r"models\item\electric_blast_furnace.json")), u"B5 物品模型已删")
check(not os.path.isfile(os.path.join(ASSETS, r"textures\item\electric_blast_furnace.png")), u"B6 物品贴图已删")
check(not os.path.isfile(os.path.join(DATA, r"recipe\electric_blast_furnace.json")), u"B7 配方 JSON 已删")
gen45 = u"\n".join(l for l in read(os.path.join(ZT, u"_zf45_recipes.py")).split(u"\n")
                   if not l.lstrip().startswith(u"#"))
check(u"electric_blast_furnace" not in gen45, u"B8 配方生成器表里那条也删了（表 ↔ 盘同口径；注释里的历史说明不算）")
ti = [loc for loc in LOCALES if u"tooltip.potato_s_t.electric_blast_furnace" in lang(loc)]
check(not ti, u"B9 五语都没有 tooltip.potato_s_t.electric_blast_furnace", u" / ".join(ti))
bi = [loc for loc in LOCALES if u"block.potato_s_t.electric_blast_furnace" not in lang(loc)]
check(not bi, u"B10 但**方块名**键五语都还在（GUI 标题要用）", u" / ".join(bi))
eb = src(u"ElectricBlastFurnaceBlock.java")
check(u"MachineDrops.dropInventory" in eb, u"B11 onRemove 仍显式调 MachineDrops.dropInventory（Audit B 文本级判据）")
check(u"ModBlocks.ELECTRIC_BLAST_FURNACE_ITEM" not in eb, u"B12 onRemove 不再 pop 那个不存在的物品")

adv = json.loads(io.open(os.path.join(DATA, r"advancement\blast_furnace.json"), encoding="utf-8").read())
check(adv[u"criteria"][u"got0"][u"trigger"] == u"potato_s_t:ebf_formed", u"B13 进度改挂自建触发器 potato_s_t:ebf_formed",
      repr(adv[u"criteria"][u"got0"][u"trigger"]))
check(adv[u"display"][u"icon"][u"id"] == u"minecraft:blast_furnace", u"B14 进度图标换成原版高炉")
check(u"electric_blast_furnace" not in json.dumps(adv, ensure_ascii=False), u"B15 进度 JSON 里不再提那个物品")
steel = json.loads(io.open(os.path.join(DATA, r"advancement\steel.json"), encoding="utf-8").read())
check(steel[u"parent"] == u"potato_s_t:blast_furnace", u"B16 子进度 steel 的父节点没断")
trg = src(u"EbfFormedTrigger.java")
check(u'TRIGGERS.register("ebf_formed"' in trg and u"BuiltInRegistries.TRIGGER_TYPES" in trg,
      u"B17 触发器注册名与注册表正确")
check(u"EbfFormedTrigger.TRIGGERS.register(modEventBus);" in src(u"PotatoST.java"), u"B18 PotatoST 构造期登记了它")
check(src(u"BlastFurnaceAssembly.java").count(u"EBF_FORMED.get().trigger(") == 1
      and src(u"ElectricBlastFurnaceBlock.java").count(u"EBF_FORMED.get().trigger(") == 1,
      u"B19 两个装配入口各触发一次（主路 + 老存档裸控制器）")
check(u'case "electric_blast_furnace" -> new ItemStack(Items.BLAST_FURNACE);' in read(
    os.path.join(JAVA, r"client\jei\PotatoSTJeiPlugin.java")), u"B20 JEI 分类图标换成原版高炉（分类本身没删）")
check(u'"icon": "minecraft:blast_furnace"' in book(r"entries\materials\blast_alloy.json"), u"B21 手册「电力高炉」条目图标也跟着换")

print(u"\n=== C 段：灌装机（槽位放开 / 灌装只认能力 / 诊断说实话）===")
be = src(u"FillingMachineBlockEntity.java")
menu = src(u"FillingMachineMenu.java")
blk = src(u"FillingMachineBlock.java")
check(re.search(r"public boolean isItemValid\(int slot, ItemStack stack\) \{.*?return true;", be, re.S) is not None,
      u"C1 方块实体 isItemValid 放行一切")
check(re.search(r"public boolean mayPlace\(ItemStack stack\) \{.*?return true;", menu, re.S) is not None,
      u"C2 菜单手放 mayPlace 放行一切")
check(u"return stack.getItem() instanceof FluidContainerItem" not in code_only(menu), u"C3 Shift 快移那道门也不再只认自家接口")
check(u"FluidContainerItem" not in code_only(menu), u"C4 菜单里连 FluidContainerItem 都不再出现（三道门同口径 = 都不把关）")
check(u"Capabilities.FluidHandler.ITEM" in be, u"C5 灌装认识别的 mod 的流体容器（物品流体能力）")
check(u"private boolean tryFillForeignContainer(" in be and u"handler.getContainer()" in be,
      u"C6 新路：拷贝上灌 → getContainer() 取回结果")
check(u"ItemStack.isSameItemSameComponents(result, inSlot)" in be and u"result.isEmpty()" in be,
      u"C7 两道「绝不吞东西 / 绝不吞流体」的闸门（空栈 + 结果与灌前相同即放弃）")
check(u"container.fill(inSlot, tank.getFluid(), FILL_RATE)" in be, u"C8 我们自己那两种容器的灌装那几行一字未动")
check(u"container.space(inSlot) <= 0" in be and u"container.accepts(tank.getFluid().getFluid())" in be,
      u"C9 气罐/油桶的判据（space / accepts）原样保留")
check(u"UNSUPPORTED" in be and u"UNSUPPORTED" in blk, u"C10 新状态 UNSUPPORTED 在方块实体与诊断里都有")
check(u"return stack != null && !stack.isEmpty();" in be, u"C11 水箱仍然「什么都收」（ZF73 那条规矩没动）")
check(u"FILL_RATE = 5" in be and u"ENERGY_PER_TANK = 60" in be and u"MAX_ENERGY = 3000" in be
      and u"TANK_CAPACITY = 5000" in be, u"C12 四个锁定数字一个没动")
untouched = [u"FluidContainerItem.java", u"HighPressureTankItem.java", u"OilBucketItem.java",
             u"OilBucketContents.java", u"TankContents.java"]
same = [n for n in untouched
        if sha1(os.path.join(JAVA, n)) == sha1(os.path.join(PRE, r"src\main\java\com\potatost\mod", n))]
check(len(same) == len(untouched), u"C13 用户点名「不要动」的五个文件改前件 ↔ 盘上逐字节相同",
      u"不同：%s" % u" / ".join([n for n in untouched if n not in same]))
for loc in LOCALES:
    v = lang(loc).get(u"gui.potato_s_t.filling.diag.unsupported", u"")
    check(v.count(u"%s") == 1, u"C14 %s 有 diag.unsupported 且恰好一个占位符" % loc, repr(v[:40]))

print(u"\n=== D 段：表 / 语言 / 文档 ===")
counts = {loc: len(lang(loc)) for loc in LOCALES}
check(counts[u"zh_cn"] >= 645 and counts[u"en_us"] >= 645 and counts[u"ja_jp"] >= 645
      and counts[u"ru_ru"] >= 645
      and counts[u"lzh"] >= 653, u"D1 键数 ≥ 645/645/645/645/653（ZF166 起盘上不钉死：别的线在加键）", repr(counts))
r = subprocess.run([sys.executable, os.path.join(ZT, u"_zf45_recipes.py")],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
check(r.returncode == 0, u"D2 配方生成器「只校验」模式 0 失败（表 ↔ 盘同口径）",
      r.stdout.decode("gbk", "replace").strip().split(u"\n")[-1][:80])
n_recipe = sum(len([f for f in files if f.endswith(".json")]) for _r, _d, files in os.walk(os.path.join(DATA, "recipe")))
check(n_recipe >= 94 and os.path.isfile(os.path.join(DATA, "recipe", u"fluid_converter.json")),
      u"D3 盘上配方 ≥ 94 份且含流体转化器那条（ZF166 起；别的线在途加配方不再误伤本门）",
      u"实际 %d" % n_recipe)
doc = read(DOC)
check(u"§4.169" in doc and u"ZF162" in doc, u"D4 档案有 §4.169（ZF162 工具雷）")
check(u"| ZF162 |" in doc, u"D5 档案 §5 有 ZF162 台账行")
check(u"ZF162" in read(HAND), u"D6 交接文档写了 ZF162（键数/成品行的活体数字）")
check(u"ZF162" in read(ANN), u"D7 英文公告有 ZF162 那一段")
check(u"扳手" in doc and u"物品形式" in doc, u"D8 档案如实记了「扳手被删」「物品形式的电力高炉被删」这两件事")

print(u"\n通过 = %d   失败 = %d" % (passed, failed))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if failed else 0)
