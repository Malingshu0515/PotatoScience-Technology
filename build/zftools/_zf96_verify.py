# -*- coding: utf-8 -*-
r"""_zf96_verify.py —— ZF96 常驻校验：加氢脱硫反应仓 + 硫

用户原话（本轮全部规格，一条到底）：

  「加一个 加氢脱硫反应仓 GUI 一个氢气罐 左侧放沥青 每16个沥青 消耗1000mB氢气 10s  产出一个 硫
    配方；【铁锭】【银锭】【银锭】，【铁块】【高压气罐】【铁块】，【红石块】【一般金属块】【红石块】」

所以本校验的骨架是**规格 → 实现**（不是"实现 ↔ 实现自比"）：

  A 机器常量：16 沥青 / 1000 mB 氢气 / 10 秒 / 1 硫 —— 从**用户原话**那张表出发，
    逐条与 Java 里的常量与结算代码对；
  B 结算顺序：放不下就原地等（不扣料）、最后一 tick 才扣、缺料只停不清进度、红石即停；
  C 不吃电（用户没给能耗数 ⇒ 不发明）：没有能量能力、没有能量条；
  D 界面：一个氢气罐 + 左侧沥青槽 + 右侧硫槽 + 自己的状态灯文案前缀；
  E 状态码 9（"氢气不够"）在共享灯表里补齐了颜色与文案；
  F JEI：机器 id = 方块注册名、四个数都引用常量（不是写死的字面量）；
  G 合成配方 JSON 解回九宫格，逐格与用户那三行比；
  H 新物品「硫」：注册 / 模型 / 真 PNG / 四语言键 / 进创造页；
  I 活体数字（键数、配方数、JEI 分类）与文档；
  J 成品 jar：哈希、新类与资源在不在、配方与盘上逐字节一致。
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
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources")
ASSETS = os.path.join(RES, r"assets\potato_s_t")
DATA = os.path.join(RES, r"data")
LANG = os.path.join(ASSETS, "lang")
ITEMD = os.path.join(ASSETS, r"models\item")
BLOCKD = os.path.join(ASSETS, r"models\block")
TEXB = os.path.join(ASSETS, r"textures\block")
TEXI = os.path.join(ASSETS, r"textures\item")
RDIR = os.path.join(DATA, r"potato_s_t\recipe")
DOCS = os.path.join(ROOT, "docs")
TOOLS = os.path.join(ROOT, "build", "zftools")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
BEFORE = os.path.join(r"C:\PotatoST救援\zf96_pre", "textures_before.txt")
ID = u"hydrodesulfurization_chamber"
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]

# ============================================================
# 规格（只写"用户说了什么"；实现里的数字要**另外**解析出来比）
# ============================================================
SPEC = {
    "zh": u"加氢脱硫反应仓",
    "bitumen": 16,          # 「每16个沥青」
    "hydrogen_mb": 1000,    # 「消耗1000mB氢气」
    "seconds": 10,          # 「10s」
    "sulfur": 1,            # 「产出一个 硫」
}
# 合成配方：用户那三行字，逐格抄成表（铁锭 / 银锭 / 铁块 / 高压气罐 / 红石块 / 一般金属块）
RECIPE_SPEC = {
    "zh": u"【铁锭】【银锭】【银锭】，【铁块】【高压气罐】【铁块】，【红石块】【一般金属块】【红石块】",
    "grid": [[u"c:ingots/iron", u"c:ingots/silver", u"c:ingots/silver"],
             [u"minecraft:iron_block", u"potato_s_t:high_pressure_tank", u"minecraft:iron_block"],
             [u"minecraft:redstone_block", u"potato_s_t:common_metal_block",
              u"minecraft:redstone_block"]],
}
NEW_KEYS = [
    "block.potato_s_t.hydrodesulfurization_chamber",
    "item.potato_s_t.sulfur",
    "tooltip.potato_s_t.hydrodesulfurization_chamber",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.running",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.disabled",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.empty",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.material",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.output_full",
    "gui.potato_s_t.hydrodesulfurization_chamber.status.no_hydrogen",
    "gui.potato_s_t.hydrodesulfurization_chamber.pour.empty",
    "gui.potato_s_t.hydrodesulfurization_chamber.pour.rejected",
    "gui.potato_s_t.jei.no_energy",
]
# ⚠ 活体数字：ZF96 那轮是 284；ZF97 +19 ⇒ 303；ZF100 +12 ⇒ 315；ZF101 +17 ⇒ 332
EXPECT_KEYS = 508           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键
EXPECT_SHAPED = 51
EXPECT_JEI = 11

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


def body(java, signature):
    """从签名处抠出配对的 {...}（签名必须在文件里唯一，否则返回 None）。"""
    if not java:
        return None
    at = java.find(signature)
    if at < 0 or java.find(signature, at + 1) >= 0:
        return None
    i = java.find(u"{", at + len(signature) - 1)
    depth = 0
    for j in range(i, len(java)):
        if java[j] == u"{":
            depth += 1
        elif java[j] == u"}":
            depth -= 1
            if depth == 0:
                return java[i:j + 1]
    return None


def int_consts(java):
    """解析 `public static final int NAME = <算术式>;`（表达式里可以引用别的常量）。"""
    raw = {}
    for m in re.finditer(r"\bint\s+([A-Z][A-Z0-9_]*)\s*=\s*([^;{}]+);", java or u""):
        expr = m.group(2).strip()
        # 去掉尾注释
        expr = re.sub(r"//.*$", u"", expr).strip()
        if re.fullmatch(r"[0-9A-Za-z_ ()*+\-]+", expr):
            raw[m.group(1)] = expr
    done = {}

    def resolve(name, depth=0):
        if name in done:
            return done[name]
        if depth > 8 or name not in raw:
            return None
        expr = raw[name]

        def sub(mm):
            ident = mm.group(0)
            if ident.isdigit():
                return ident
            v = resolve(ident, depth + 1)
            return str(v) if v is not None else ident

        filled = re.sub(r"[A-Za-z_][A-Za-z0-9_]*|\d+", sub, expr)
        try:
            val = int(eval(filled, {"__builtins__": {}}, {}))
        except Exception:
            return None
        done[name] = val
        return val

    for k in list(raw):
        resolve(k)
    return done


def png_info(path):
    """真 PNG + 尺寸（只读文件头，不引第三方库）。"""
    if not os.path.exists(path):
        return None
    b = open(path, "rb").read()
    if b[:8] != b"\x89PNG\r\n\x1a\n" or b[12:16] != b"IHDR":
        return None
    w = int.from_bytes(b[16:20], "big")
    h = int.from_bytes(b[20:24], "big")
    depth, ctype = b[24], b[25]
    return (w, h, depth, ctype)


def main():
    print(u"=========== ZF96 校验：加氢脱硫反应仓 + 硫 ===========")

    be_path = os.path.join(JAVA, u"HydrodesulfurizationChamberBlockEntity.java")
    blk_path = os.path.join(JAVA, u"HydrodesulfurizationChamberBlock.java")
    menu_path = os.path.join(JAVA, u"HydrodesulfurizationChamberMenu.java")
    scr_path = os.path.join(JAVA, r"client\HydrodesulfurizationChamberScreen.java")
    be, blk = read(be_path), read(blk_path)
    menu, scr = read(menu_path), read(scr_path)
    moditems, modblocks = read(os.path.join(JAVA, "ModItems.java")), read(os.path.join(JAVA, "ModBlocks.java"))
    modmenus = read(os.path.join(JAVA, "ModMenus.java"))
    client = read(os.path.join(JAVA, "PotatoSTClient.java"))
    common = read(os.path.join(JAVA, "PotatoST.java"))
    mrec = read(os.path.join(JAVA, "MachineRecipes.java"))
    jei = read(os.path.join(JAVA, r"client\jei\PotatoSTJeiPlugin.java"))
    lamp = read(os.path.join(JAVA, r"client\gui\parts\StatusLampPart.java"))
    for (label, txt) in ((u"方块实体", be), (u"方块", blk), (u"菜单", menu), (u"界面", scr)):
        check(u"%s 源码在" % label, txt is not None)

    print(u"\n== A 机器常量：与用户原话逐条对 ==")
    c = int_consts(be)
    eq(u"每批沥青 = %d（用户原话「每%d个沥青」）" % (SPEC["bitumen"], SPEC["bitumen"]),
       SPEC["bitumen"], c.get("BITUMEN_PER_OPERATION"))
    eq(u"每批氢气 = %d mB（用户原话「消耗%dmB氢气」）" % (SPEC["hydrogen_mb"], SPEC["hydrogen_mb"]),
       SPEC["hydrogen_mb"], c.get("HYDROGEN_PER_OPERATION"))
    eq(u"每批硫 = %d（用户原话「产出一个 硫」）" % SPEC["sulfur"],
       SPEC["sulfur"], c.get("SULFUR_PER_OPERATION"))
    # ⚠ 不把 200 写进期望值：由「10 秒」× 20 tick/秒 算出来
    eq(u"每批耗时 = %d 秒 × 20 = %d tick（用户原话「%ds」）"
       % (SPEC["seconds"], SPEC["seconds"] * 20, SPEC["seconds"]),
       SPEC["seconds"] * 20, c.get("DURATION_TICKS"))
    # 氢气罐容量：用户没给 ⇒ 只要求"至少装得下一批 + 是个整数常量"，并如实打出我选的数
    cap = c.get("TANK_CAPACITY")
    check(u"氢气罐容量 %s mB ≥ 一批（%d）—— 用户没给这个数，是我选的（见类注释）"
          % (cap, SPEC["hydrogen_mb"]),
          isinstance(cap, int) and cap >= SPEC["hydrogen_mb"])

    tick = body(be, u"private void serverTick()")
    check(u"serverTick 抠得出来", tick is not None)
    tick = tick or u""

    print(u"\n== B 结算：三样一起扣、放不下就等、缺料不清进度、红石即停 ==")
    check(u"最后一 tick 扣沥青：extractItem(INPUT_SLOT, BITUMEN_PER_OPERATION, false)",
          u"extractItem(INPUT_SLOT, BITUMEN_PER_OPERATION, false)" in tick)
    check(u"最后一 tick 扣氢气：tank.drain(HYDROGEN_PER_OPERATION, EXECUTE)",
          u"tank.drain(HYDROGEN_PER_OPERATION, IFluidHandler.FluidAction.EXECUTE)" in tick)
    check(u"最后一 tick 出硫：new ItemStack(ModItems.SULFUR.get(), SULFUR_PER_OPERATION)",
          u"new ItemStack(ModItems.SULFUR.get(), SULFUR_PER_OPERATION)" in tick)
    room = tick.find(u"sulfurSpace() < SULFUR_PER_OPERATION")
    take = tick.find(u"extractItem(INPUT_SLOT")
    check(u"放不下就先返回（不扣料）：空间判断在扣料之前（%d < %d）" % (room, take),
          0 <= room < take)
    reset_branch = tick.find(u"input.getCount() < BITUMEN_PER_OPERATION")
    after = tick.find(u"return;", reset_branch) if reset_branch >= 0 else -1
    check(u"沥青不够的岔路里**没有** resetProgress（只停不清，进度保留）",
          reset_branch >= 0 and after > reset_branch
          and u"resetProgress" not in tick[reset_branch:after])
    check(u"红石信号 = 关机，且在罐头一条判断（hasNeighborSignal 在最前）",
          tick.find(u"hasNeighborSignal") >= 0
          and tick.find(u"hasNeighborSignal") < tick.find(u"getStackInSlot(INPUT_SLOT)"))
    # 中间每一 tick 只推进度、不动料
    early = tick.find(u"if (this.progress + 1 < this.progressMax)")
    room_at = tick.find(u"sulfurSpace() < SULFUR_PER_OPERATION")
    check(u"推进度的那一支里不碰沥青/氢气（材料只在最后一 tick 结算）",
          early >= 0 and room_at > early and u"extractItem" not in tick[early:room_at])

    print(u"\n== C 能力登记 + 不吃电（用户没给能耗数 ⇒ 不发明） ==")
    check(u"方块实体里没有 IEnergyStorage / MAX_ENERGY",
          u"IEnergyStorage" not in (be or u"") and u"MAX_ENERGY" not in (be or u""))
    seg = common or u""
    hit = seg.find(u"HYDRODESULFURIZATION_CHAMBER_BE")
    eblock = [m.start() for m in re.finditer(r"Capabilities\.EnergyStorage\.BLOCK", seg)]
    near = any(seg.find(u"HYDRODESULFURIZATION_CHAMBER", i, i + 400) >= 0 for i in eblock)
    check(u"PotatoST.java 没给这台机器登记能量能力（%d 处 EnergyStorage 登记里没有它）"
          % len(eblock), hit >= 0 and not near)
    itemreg = [m.start() for m in re.finditer(r"Capabilities\.ItemHandler\.BLOCK", seg)]
    check(u"登记了物品栏能力（沥青进 / 硫出，自动化能取）",
          any(seg.find(u"HYDRODESULFURIZATION_CHAMBER_BE", i, i + 400) >= 0 for i in itemreg))
    freg = [m.start() for m in re.finditer(r"Capabilities\.FluidHandler\.BLOCK", seg)]
    check(u"登记了流体能力（管道/泵接上来就能灌氢气）",
          any(seg.find(u"HYDRODESULFURIZATION_CHAMBER_BE", i, i + 400) >= 0 for i in freg))
    check(u"罐只收氢气（validator 比的是 HYDROGEN_TYPE）", u"ModFluids.HYDROGEN_TYPE.get()" in (be or u""))
    check(u"界面里没有能量条（EnergyBarPart 不出现）", u"EnergyBarPart" not in (scr or u""))

    print(u"\n== D 界面：一个氢气罐 + 左侧沥青槽 + 右侧硫槽 + 自己的状态灯前缀 ==")
    add = re.findall(r"this\.parts\.add\(new (\w+)", scr or u"")
    eq(u"界面部件" , [u"FluidTankPart", u"ProgressArrowPart", u"StatusLampPart"], add)
    check(u"罐里画的是氢气（ModFluids.HYDROGEN）", u"ModFluids.HYDROGEN.get()" in (scr or u""))
    eq(u"只有一个罐（用户原话「一个氢气罐」）", 1, (scr or u"").count(u"new FluidTankPart("))
    mi = re.search(r"INPUT_SLOT_X\s*=\s*(-?\d+)", menu or u"")
    mx = re.search(r"OUTPUT_SLOT_X\s*=\s*(-?\d+)", menu or u"")
    check(u"沥青槽在**左**、硫槽在**右**（%s < %s）"
          % (mi.group(1) if mi else u"?", mx.group(1) if mx else u"?"),
          bool(mi and mx) and int(mi.group(1)) < int(mx.group(1)))
    check(u"状态灯传了自己的文案前缀（不传会显示微型粉碎机的「正在粉碎」，§6.10 ⑪）",
          u"STATUS_KEY_PREFIX" in (scr or u"")
          and u"gui.potato_s_t.hydrodesulfurization_chamber.status." in (scr or u""))
    check(u"菜单登记在 ModMenus（id = 方块注册名）",
          u'MENU_TYPES.register("%s"' % ID in (modmenus or u""))
    check(u"界面登记在 PotatoSTClient",
          u"HYDRODESULFURIZATION_CHAMBER_MENU.get()" in (client or u"")
          and u"HydrodesulfurizationChamberScreen::new" in (client or u""))
    # §4.25 的家族规矩：本工程**每一台机器**都挂进 mineable/pickaxe（_zf78/_zf79 各有一条同样的断言）
    mine = json.loads(read(os.path.join(DATA, u"minecraft", u"tags", u"block", u"mineable",
                                        u"pickaxe.json")))
    check(u"新机器进了 mineable/pickaxe（机器方块家族的老规矩）",
          (u"potato_s_t:" + ID) in (mine.get("values") or []))

    print(u"\n== E 状态码 9「氢气不够」在共享灯表里补齐 ==")
    eq(u"方块实体里的 9 号就是氢气不够", 9, c.get("STATUS_NO_HYDROGEN"))
    check(u"StatusLampPart 把 9 号画成黄灯",
          u"HydrodesulfurizationChamberBlockEntity.STATUS_NO_HYDROGEN -> YELLOW" in (lamp or u""))
    check(u"StatusLampPart 的文案后缀表里有 no_hydrogen",
          u'STATUS_NO_HYDROGEN -> "no_hydrogen"' in (lamp or u""))
    check(u"这台机器**不**用 3 号（「没电」在这台机器上没有意义）",
          u"STATUS_NO_POWER" not in (be or u""))

    print(u"\n== F JEI：机器 id = 方块注册名，数字全部引用常量 ==")
    blkseg = mrec or u""
    jb = body(blkseg, u"private static void buildHydrodesulfurizationChamber(List<Entry> out)")
    check(u"buildHydrodesulfurizationChamber 抠得出来", jb is not None)
    jb = jb or u""
    check(u"机器 id 用的是方块注册名 %s" % ID, u'new Entry("%s"' % ID in jb)
    check(u"沥青数量引用常量 BITUMEN_PER_OPERATION（不写死 16）",
          u"HydrodesulfurizationChamberBlockEntity.BITUMEN_PER_OPERATION" in jb)
    check(u"氢气量引用常量 HYDROGEN_PER_OPERATION（不写死 1000）",
          u"HydrodesulfurizationChamberBlockEntity.HYDROGEN_PER_OPERATION" in jb)
    check(u"耗时引用常量 DURATION_TICKS / 20（不写死 10）",
          u"HydrodesulfurizationChamberBlockEntity.DURATION_TICKS / 20" in jb)
    check(u"明写「不耗电」那一行（不然玩家会以为漏写了能耗）",
          u'Component.translatable("gui.potato_s_t.jei.no_energy")' in jb)
    check(u"注册进 JEI 分类表（MACHINES 里加了一行且 id 一致）",
          u'"%s"' % ID in (jei or u""))
    check(u"JEI 图标给了这台机器方块",
          u'case "%s" -> new ItemStack(ModBlocks.HYDRODESULFURIZATION_CHAMBER_ITEM.get());' % ID
          in (jei or u""))

    print(u"\n== G 合成配方：JSON 解回九宫格，逐格与用户那三行比 ==")
    rp = os.path.join(RDIR, ID + u".json")
    check(u"%s.json 在" % ID, os.path.exists(rp))
    if os.path.exists(rp):
        d = json.loads(read(rp))
        eq(u"配方类型", u"minecraft:crafting_shaped", d.get("type"))
        eq(u"产物", {u"id": u"potato_s_t:" + ID, u"count": 1}, d.get("result"))
        key = d.get("key") or {}
        got, bad = [], False
        for row in (d.get("pattern") or []):
            line = []
            for ch in row:
                ent = key.get(ch)
                if not ent:
                    line.append(u"?%s" % ch)
                    bad = True
                else:
                    line.append(ent.get("item") or ent.get("tag") or u"?" + ch)
            got.append(line)
        check(u"九宫格与用户原话逐格一致（%s）" % RECIPE_SPEC["zh"],
              (not bad) and got == RECIPE_SPEC["grid"])
        if got != RECIPE_SPEC["grid"]:
            for i in range(3):
                print(u"         第 %d 行 解出 %s / 规格 %s"
                      % (i + 1, got[i] if i < len(got) else None, RECIPE_SPEC["grid"][i]))
    # 材料真的存在
    vanilla_ok = {"minecraft:iron_block": u"iron_block",
                  "minecraft:redstone_block": u"redstone_block"}
    for cell in (RECIPE_SPEC["grid"][0] + RECIPE_SPEC["grid"][1] + RECIPE_SPEC["grid"][2]):
        if cell.startswith(u"c:"):
            tagfile = os.path.join(DATA, u"c", u"tags", u"item", cell.split(u"/")[-1] + u".json")
            # 本工程自己提供的标签有文件；原版的那几个（c:ingots/iron）由 NeoForge 提供
            # ⇒ 用"老配方里已经在用"当证据（用户早就合成过终端/加热器那些）
            used = False
            for n in os.listdir(RDIR):
                if u'"tag": "%s"' % cell in (read(os.path.join(RDIR, n)) or u""):
                    used = True
                    break
            check(u"标签 #%s：%s" % (cell, u"本工程提供" if os.path.exists(tagfile) else u"老配方在用"),
                  os.path.exists(tagfile) or used)
        elif cell.startswith(u"potato_s_t:"):
            nm = cell.split(u":")[1]
            # 物品或方块：模型在（物品模型 / blockstate 二者其一）+ 注册名在源码里出现
            registered = (u'"%s"' % nm in (moditems or u"")) or (u'"%s"' % nm in (modblocks or u""))
            check(u"材料 %s 有模型与注册" % cell,
                  (os.path.exists(os.path.join(ITEMD, nm + u".json"))
                   or os.path.exists(os.path.join(BLOCKD, nm + u".json")))
                  and registered)
        else:
            check(u"%s 是原版方块（不猜）" % cell, cell in vanilla_ok)

    print(u"\n== H 新物品「硫」 ==")
    check(u"ModItems 里注册了 sulfur",
          u'ITEMS.register("sulfur"' in (moditems or u"") and u"DeferredItem<Item> SULFUR" in (moditems or u""))
    check(u"硫进了创造模式标签页", u"output.accept(SULFUR.get());" in (moditems or u""))
    check(u"机器也进了创造页", u"output.accept(ModBlocks.HYDRODESULFURIZATION_CHAMBER_ITEM.get());" in (moditems or u""))
    mp = os.path.join(ITEMD, u"sulfur.json")
    check(u"models/item/sulfur.json 在且指自己的贴图",
          os.path.exists(mp) and u"potato_s_t:item/sulfur" in (read(mp) or u""))
    info = png_info(os.path.join(TEXI, u"sulfur.png"))
    check(u"textures/item/sulfur.png 是真 PNG 16×16（8 位 RGBA）：%s" % (info,),
          info is not None and info[0] == 16 and info[1] == 16 and info[2] == 8 and info[3] == 6)
    # 三张贴图都是"我们自己的"（所以英文公告里"还在借原版贴图 = 5"不变）
    before_tex = {}
    if os.path.exists(BEFORE):
        for ln in read(BEFORE).splitlines():
            parts = ln.split()
            if len(parts) == 2:
                before_tex[parts[0]] = parts[1]
    for rel in (u"block/hydrodesulfurization_chamber_side.png",
                u"block/hydrodesulfurization_chamber_top.png",
                u"item/sulfur.png"):
        check(u"新贴图 %s 不在改前清单里（= 本轮新增，没覆盖旧图）" % rel, rel not in before_tex)
    # 旧贴图一张都没动（只比"改前清单里那些"）
    changed = []
    for rel, old_sha in before_tex.items():
        p = os.path.join(ASSETS, u"textures", rel.replace(u"/", os.sep))
        if not os.path.exists(p) or sha1f(p) != old_sha:
            changed.append(rel)
    check(u"改前那 %d 张贴图一张都没动（变了 %d 张）" % (len(before_tex), len(changed)), not changed)

    print(u"\n== I 四语言 + 活体数字 ==")
    keys = {}
    for name in LANGS:
        d = json.loads(read(os.path.join(LANG, name + u".json")))
        keys[name] = d
        eq(u"%s 键数" % name, EXPECT_KEYS, len(d))
        missing = [k for k in NEW_KEYS if k not in d]
        check(u"%s 里 12 个新键都在（缺 %s）" % (name, missing or u"无"), not missing)
    ph = {n: keys[n].get(u"gui.potato_s_t.hydrodesulfurization_chamber.pour.rejected", u"").count(u"%s")
          for n in LANGS}
    check(u"pour.rejected 四语言各含 1 个 %%s（占位符要对齐）：%s" % ph, set(ph.values()) == {1})
    check(u"jei.no_energy 四语言都不含占位符",
          all(u"%s" not in keys[n].get(u"gui.potato_s_t.jei.no_energy", u"") for n in LANGS))
    z71 = read(os.path.join(TOOLS, "_zf71_verify.py")) or u""
    check(u"_zf71_verify.py 的键数断言跟到 %d" % EXPECT_KEYS, u"== {%d}" % EXPECT_KEYS in z71)
    check(u"_zf71_verify.py 的定形配方断言跟到 %d" % EXPECT_SHAPED,
          u"check(craft == %d," % EXPECT_SHAPED in z71)
    check(u"_zf71_verify.py 的 JEI 分类断言跟到 %d" % EXPECT_JEI,
          u"check(jei == %d and" % EXPECT_JEI in z71)
    shaped = [n for n in os.listdir(RDIR)
              if json.loads(read(os.path.join(RDIR, n))).get("type") == u"minecraft:crafting_shaped"]
    eq(u"盘上定形配方总数", EXPECT_SHAPED, len(shaped))
    jei_n = len(re.findall(r'"([a-z_]+)"', re.search(r"MACHINES\s*=\s*(.*?);", jei or u"", re.S).group(1)))
    eq(u"JEI 机器分类数", EXPECT_JEI, jei_n)

    print(u"\n== J 文档 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    tex = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    check(u"档案里有 ZF96 那一行", u"| ZF96 |" in arch)
    check(u"档案 §4 有本轮那条规矩", u"### 4.63 " in arch)
    check(u"档案 §9 有 ZF96 那一节", u"### ZF96（0.11）" in arch)
    check(u"公告里有这台机器的行", u"Hydrodesulfurization Chamber" in ann)
    check(u"公告的键数跟到 %d" % EXPECT_KEYS, u"%d keys each" % EXPECT_KEYS in ann)
    check(u"公告的 JEI 分类跟到 %d" % EXPECT_JEI, u"%d machine categories" % EXPECT_JEI in ann)
    check(u"公告里「还在借原版贴图 = 5」没被本轮改动（三张新图都是我们自己的）",
          u"5 models still do this" in ann)
    check(u"贴图清单里有 ZF96 那一节", u"## ZF96" in tex)

    print(u"\n== K 成品 jar ==")
    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            for cls in (u"HydrodesulfurizationChamberBlock", u"HydrodesulfurizationChamberBlockEntity",
                        u"HydrodesulfurizationChamberMenu"):
                rel = u"com/potatost/mod/%s.class" % cls
                check(u"成品里有 %s" % rel, rel in names)
            check(u"成品里有界面 class",
                  u"com/potatost/mod/client/HydrodesulfurizationChamberScreen.class" in names)
            rel = u"data/potato_s_t/recipe/%s.json" % ID
            check(u"成品里的新配方与盘上逐字节一致",
                  rel in names and zf.read(rel) == open(rp, "rb").read())
            rel = u"assets/potato_s_t/textures/item/sulfur.png"
            check(u"成品里的硫贴图与盘上逐字节一致",
                  rel in names and zf.read(rel) == open(os.path.join(TEXI, u"sulfur.png"), "rb").read())
            check(u"成品里 assets/ 与 data/ 条目名全合法",
                  not [n for n in names if (n.startswith(u"assets/") or n.startswith(u"data/"))
                       and not re.fullmatch(u"[a-z0-9/._-]+", n)])
            check(u"成品里没有探针 class",
                  not [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")])

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
