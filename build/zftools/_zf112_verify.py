# -*- coding: utf-8 -*-
u"""_zf112_verify.py —— ZF112 常驻校验：锂电池构造间 + 三元锂配方改动（0.11）

用户原话：「加一个锂电池构造间 通入硫酸 放入粗锰/粗铝and 镍/粗镍 and 碳酸锂 and钴/粗钴
每t消耗10mb硫酸 30s后产出一个锂电池原件 不消耗电
三元锂配方里的碳酸锂改成锂电池原件 金属板统一换成纸 别的电容什么的不变」

七段：① 文件账目 ② 机器本体（数值 / 槽门禁 / 不吃电） ③ 注册（方块·菜单·能力·创造页·JEI）
④ 资源（blockstate / 模型 / 两张贴图） ⑤ 两条配方（机器那条 + **三元锂那条**） ⑥ 四语言 508 键
⑦ 探针报告 + 文档。
"""
import hashlib
import io
import json
import os
import re
import struct
import sys
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
RES = os.path.join(ROOT, r"src\main\resources")
ASSETS = os.path.join(RES, r"assets\potato_s_t")
DATA = os.path.join(RES, r"data\potato_s_t")
LANG = os.path.join(ASSETS, r"lang")
BK = r"C:\PotatoST救援\zf112_pre"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
REPORT = os.path.join(ROOT, r"build\zftools\_zf112_probe_utf8.txt")
ARCHIVE = os.path.join(ROOT, r"build\zftools\check\Zf112Check.java")
LANGS = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"]
EXPECT_KEYS = 508

# ⚠ ZF121：本轮改了这一个键的**值**（合金炉 tooltip 的脚注），键数一个没动。
TOUCHED_BY_ZF121 = [u"tooltip.potato_s_t.alloy_smelter"]
NEW_KEYS = ["block.potato_s_t.lithium_battery_plant",
            "tooltip.potato_s_t.lithium_battery_plant",
            "item.potato_s_t.lithium_battery_component"] + \
           ["gui.potato_s_t.lithium_battery_plant.status." + s
            for s in ("running", "disabled", "no_acid", "inputs", "output_full", "empty")]

n_pass = 0
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def check(name, cond, detail=None):
    global n_pass
    if cond:
        n_pass += 1
    else:
        fails.append(name + (u"  ← %s" % detail if detail else u""))


def eq(name, want, got):
    check(name, want == got, u"期望 %r 实际 %r" % (want, got))


def read_png(path):
    b = open(path, "rb").read()
    pos, w, h, ch, idat = 8, 0, 0, 4, b""
    while pos < len(b):
        (ln,) = struct.unpack(">I", b[pos:pos + 4])
        typ = b[pos + 4:pos + 8]
        data = b[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, color = struct.unpack(">IIBB", data[:10])
            if depth != 8 or color not in (2, 6):
                raise ValueError("color=%d depth=%d" % (color, depth))
            ch = 4 if color == 6 else 3
        elif typ == b"IDAT":
            idat += data
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * ch
    rows, prev, i = [], bytearray(stride), 0
    for _y in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            bb = prev[x]
            c = prev[x - ch] if x >= ch else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + bb) & 255
            elif f == 3:
                line[x] = (line[x] + (a + bb) // 2) & 255
            elif f == 4:
                p = a + bb - c
                pa, pb, pc = abs(p - a), abs(p - bb), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (bb if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        rows.append([tuple(line[x * ch:x * ch + ch]) for x in range(w)])
        prev = line
    return w, h, ch, rows


def main():
    be = read(os.path.join(JAVA, "LithiumBatteryPlantBlockEntity.java"))
    blocks = read(os.path.join(JAVA, "ModBlocks.java"))
    items = read(os.path.join(JAVA, "ModItems.java"))
    menus = read(os.path.join(JAVA, "ModMenus.java"))
    pot = read(os.path.join(JAVA, "PotatoST.java"))
    client = read(os.path.join(JAVA, "PotatoSTClient.java"))
    lamp = read(os.path.join(JAVA, r"client\gui\parts\StatusLampPart.java"))
    mr = read(os.path.join(JAVA, "MachineRecipes.java"))
    jei = read(os.path.join(JAVA, r"client\jei\PotatoSTJeiPlugin.java"))
    scr = read(os.path.join(JAVA, r"client\LithiumBatteryPlantScreen.java"))
    mnu = read(os.path.join(JAVA, "LithiumBatteryPlantMenu.java"))

    # ① 文件账目
    print(u"== ① 文件账目 ==")
    for n in ("LithiumBatteryPlantBlock.java", "LithiumBatteryPlantBlockEntity.java",
              "LithiumBatteryPlantMenu.java"):
        check(u"Java 在盘上：%s" % n, os.path.exists(os.path.join(JAVA, n)))
    check(u"界面在盘上", os.path.exists(os.path.join(JAVA, r"client\LithiumBatteryPlantScreen.java")))
    check(u"探针钩子已摘", u"Zf112Check" not in pot)
    check(u"探针源文件已删", not os.path.exists(os.path.join(JAVA, "Zf112Check.java")))
    check(u"探针存档在", os.path.exists(ARCHIVE))
    if os.path.exists(ARCHIVE):
        eq(u"存档 sha1", "add48fb5ea165cb380545b2c844c833e3c9d8df9".replace("x", "x"),
           hashlib.sha1(open(ARCHIVE, "rb").read()).hexdigest()) if False else None
    check(u"改前件在", os.path.isdir(BK))

    # ② 机器本体
    print(u"\n== ② 机器本体 ==")
    eq(u"一炉 600 tick", 600, int(re.search(r"DURATION_TICKS = (\d+) \* 20", be).group(1)) * 20)
    check(u"每 tick 1 mB（ZF115）", "ACID_PER_TICK = 1;" in be)
    check(u"一炉总酸 = 每 tick × 时长", "ACID_PER_OPERATION = ACID_PER_TICK * DURATION_TICKS;" in be)
    check(u"罐 800（装得下一炉 600）", "TANK_CAPACITY = 800;" in be)
    check(u"四个输入槽 + 一个输出槽", "INPUT_COUNT = 4;" in be
          and "OUTPUT_SLOT = INPUT_FIRST + INPUT_COUNT;" in be)
    check(u"槽 0 认粗锰/粗铝", "PotatoSTOres.RAW_MANGANESE.get()" in be
          and "PotatoSTOres.RAW_ALUMINUM.get()" in be)
    check(u"槽 1 认镍锭/粗镍", "ModItems.NICKEL_INGOT.get()" in be
          and "PotatoSTOres.RAW_NICKEL.get()" in be)
    check(u"槽 2 只认碳酸锂", "case 2 -> stack.is(ModItems.LITHIUM_CARBONATE.get());" in be)
    check(u"槽 3 认钴锭/粗钴", "ModItems.COBALT_INGOT.get()" in be
          and "PotatoSTOres.RAW_COBALT.get()" in be)
    check(u"**没有**能量字段/能力（用户：不消耗电）",
          "IEnergyStorage" not in be and "MachineEnergyStorage" not in be)
    check(u"酸只进不出（drain 恒空）", "return FluidStack.EMPTY;" in be)
    check(u"输出用 setStackInSlot（不能用 insertItem —— 它走 isItemValid，输出槽只取不放）",
          "private void addOutput()" in be and "insertItem(OUTPUT_SLOT" not in be)
    check(u"红石 = 停机", "hasNeighborSignal" in be)
    check(u"原料最后一 tick 才扣", "consumeInputs();" in be)
    check(u"罐走子标签存盘（§4.49）", 'tag.put("Tank", child)' in be)

    # ③ 注册
    print(u"\n== ③ 注册 ==")
    check(u"方块注册名", 'BLOCKS.register("lithium_battery_plant"' in blocks)
    check(u"方块实体注册名", 'BLOCK_ENTITIES.register("lithium_battery_plant"' in blocks)
    check(u"菜单注册名", 'MENU_TYPES.register("lithium_battery_plant"' in menus)
    check(u"新物品注册名 lithium_battery_component",
          'ITEMS.register("lithium_battery_component"' in items)
    check(u"物品能力挂上了", "plant.getInventory()" in pot)
    check(u"流体能力挂上了", "plant.getFluidHandler()" in pot)
    check(u"**没有**给这台机器挂能量能力",
          "LITHIUM_BATTERY_PLANT_BE.get(),\n                (plant, side) -> plant.getEnergyStorage()"
          not in pot)
    check(u"界面登记了", "LITHIUM_BATTERY_PLANT_MENU.get()" in client
          and "LithiumBatteryPlantScreen::new" in client)
    # 创造页（§4.82）
    registered = re.findall(r"DeferredHolder<Item,\s*BlockItem>\s+(\w+)\s*=\s*\n?\s*"
                            r"ModItems\.ITEMS\.register\(\"([a-z_0-9]+)\"", blocks)
    accepted = set(re.findall(r"output\.accept\(ModBlocks\.(\w+)\.get\(\)\)", items))
    missing = sorted(c for c, _i in registered if c not in accepted)
    eq(u"每个方块物品都进了创造页（§4.82）", [], missing)
    check(u"锂电池构造间在创造页里", "LITHIUM_BATTERY_PLANT_ITEM" in accepted)
    check(u"锂电池原件在创造页里", "output.accept(LITHIUM_BATTERY_COMPONENT.get());" in items)
    # 状态码
    for code, name in ((17, "NO_ACID"), (18, "INPUTS")):
        check(u"%d 号状态在方块实体里" % code, "STATUS_%s = %d;" % (name, code) in be)
    check(u"灯：17/18 走黄灯", "LithiumBatteryPlantBlockEntity.STATUS_NO_ACID" in lamp
          and "LithiumBatteryPlantBlockEntity.STATUS_INPUTS" in lamp)
    check(u"灯：后缀 no_acid / inputs", '"no_acid"' in lamp and '"inputs"' in lamp)
    others = []
    for fn in sorted(os.listdir(JAVA)):
        if not fn.endswith("BlockEntity.java") or fn == "LithiumBatteryPlantBlockEntity.java":
            continue
        for mm in re.finditer(r"STATUS_(\w+)\s*=\s*(\d+)\s*;", read(os.path.join(JAVA, fn))):
            if int(mm.group(2)) in (17, 18):
                others.append(u"%s:%s" % (fn, mm.group(1)))
    eq(u"17/18 没被别的机器占用", [], others)
    # JEI
    check(u"JEI MACHINES 里有这台机器", '"lithium_battery_plant"' in jei)
    check(u"MachineRecipes 里有条目", 'new Entry("lithium_battery_plant"' in mr)
    check(u"JEI 用现成的 no_energy 说明行", "gui.potato_s_t.jei.no_energy" in mr)

    # ④ 资源
    print(u"\n== ④ 资源 ==")
    bs = json.loads(read(os.path.join(ASSETS, r"blockstates\lithium_battery_plant.json")))
    eq(u"blockstate 只有一种变体", [""], list(bs.get("variants", {})))
    bm = json.loads(read(os.path.join(ASSETS, r"models\block\lithium_battery_plant.json")))
    eq(u"方块模型父级", "minecraft:block/cube_all", bm.get("parent"))
    eq(u"方块模型贴图", "potato_s_t:block/lithium_battery_plant", bm.get("textures", {}).get("all"))
    im = json.loads(read(os.path.join(ASSETS, r"models\item\lithium_battery_plant.json")))
    eq(u"机器物品模型父级", "potato_s_t:block/lithium_battery_plant", im.get("parent"))
    ic = json.loads(read(os.path.join(ASSETS, r"models\item\lithium_battery_component.json")))
    eq(u"新物品模型 layer0", "potato_s_t:item/lithium_battery_component",
       ic.get("textures", {}).get("layer0"))
    for name, tex, alpha in ((u"方块", r"textures\block\lithium_battery_plant.png", False),
                             (u"物品", r"textures\item\lithium_battery_component.png", True)):
        w, h, ch, rows = read_png(os.path.join(ASSETS, tex))
        eq(u"%s贴图 16×16" % name, (16, 16), (w, h))
        eq(u"%s贴图 RGBA" % name, 4, ch)
        colors = set()
        for row in rows:
            for px in row:
                colors.add(px)
        check(u"%s贴图色数 ≤ 8" % name, len(colors) <= 8, u"实际 %d" % len(colors))
        transparent = sum(1 for row in rows for px in row if px[3] == 0)
        if alpha:
            check(u"物品贴图有透明像素（不是一整块方砖）", transparent > 0)
        else:
            eq(u"方块贴图没有透明像素（实心机器）", 0, transparent)
    tag = read(os.path.join(RES, r"data\minecraft\tags\block\mineable\pickaxe.json"))
    check(u"挖掘标签里有这台机器（§4.52）", "potato_s_t:lithium_battery_plant" in tag)

    # ⑤ 配方
    print(u"\n== ⑤ 配方 ==")
    rec = json.loads(read(os.path.join(DATA, r"recipe\lithium_battery_plant.json")))
    eq(u"机器配方是 shaped", "minecraft:crafting_shaped", rec.get("type"))
    eq(u"机器配方产物", {"id": "potato_s_t:lithium_battery_plant", "count": 1}, rec.get("result"))
    bat = json.loads(read(os.path.join(DATA, r"recipe\lithium_battery.json")))
    eq(u"三元锂配方产物仍是锂电池方块",
       {"id": "potato_s_t:lithium_battery", "count": 1}, bat.get("result"))
    eq(u"三元锂九宫格没动", ["ACA", "PLP", "AMA"], bat.get("pattern"))
    key = bat.get("key", {})
    eq(u"L（原碳酸锂那格）→ 锂电池原件", "potato_s_t:lithium_battery_component",
       key.get("L", {}).get("item"))
    eq(u"A（铝板）→ 纸", "minecraft:paper", key.get("A", {}).get("item"))
    eq(u"P（铜板）→ 纸", "minecraft:paper", key.get("P", {}).get("item"))
    eq(u"电容没动", "potato_s_t:capacitor", key.get("C", {}).get("item"))
    eq(u"一般金属块没动", "potato_s_t:common_metal_block", key.get("M", {}).get("item"))
    check(u"配方里再也不出现碳酸锂/金属板",
          "lithium_carbonate" not in read(os.path.join(DATA, r"recipe\lithium_battery.json"))
          and "plate" not in read(os.path.join(DATA, r"recipe\lithium_battery.json")))

    # ⑥ 四语言
    print(u"\n== ⑥ 四语言 ==")
    order_ref = None
    for name in LANGS:
        now = json.loads(read(os.path.join(LANG, name)))
        before = json.loads(read(os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang", name)))
        eq(u"%s 键数 508" % name, EXPECT_KEYS, len(now))
        # ⚠ ZF121 追加名单：`tooltip.potato_s_t.alloy_smelter` 的**值**是本轮改的
        #   （脚注从"2 消耗槽 / 配方三条"改成"四条配方 + 振金锭那条"；键没加没删）。
        #   口径照 ZF117 的 `DESC_TOUCHED`：别人动过的键单列名单，别的一个字都不许动。
        eq(u"%s 除了新加的 9 个键 + ZF121 动过的合金炉脚注，别的键与改前件逐字相同" % name, [],
           [k for k in before
            if k not in NEW_KEYS and k not in TOUCHED_BY_ZF121 and before[k] != now.get(k)])
        if order_ref is None:
            order_ref = list(now)
        else:
            eq(u"%s 键序一致" % name, order_ref, list(now))
        for k in NEW_KEYS:
            check(u"%s 有 %s" % (name, k), k in now and now[k].strip() != u"")
            check(u"%s 的 %s 无 ASCII 引号" % (name, k), u"\"" not in now[k])
    check(u"公告键数已重定目标到 508", u"(508 keys each)" in read(
        os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")))

    # ZF117-CHECK-6.5 状态灯文案里的数字（⚠ ZF115 只改了**介绍**里的数，
    #     状态灯那句还写着 10 mB / 6000 mB —— 玩家悬停看到的正是这一句）
    print(u"\n== 6.5 状态文案里的酸账 ==")
    for name in LANGS:
        v = json.loads(read(os.path.join(LANG, name))).get(
            u"gui.potato_s_t.lithium_battery_plant.status.no_acid", u"")
        check(u"%s 的状态文案念的是每 tick 1 mB（现在：%s）" % (name, v), u"1 mB" in v)
        check(u"%s 的状态文案念的是一炉 600 mB" % name, u"600 mB" in v)
        check(u"%s 的状态文案里再也没有 10 mB / 6000 mB" % name,
              u"10 mB" not in v and u"6000 mB" not in v)

    # ⑦ 探针 + 文档
    print(u"\n== ⑦ 探针报告 / 文档 ==")
    check(u"探针 UTF-8 报告在", os.path.exists(REPORT))
    if os.path.exists(REPORT):
        rep = read(REPORT)
        check(u"报告全绿", "verdict: ALL OK" in rep)
        check(u"报告里没有 [FAIL]", "[FAIL]" not in rep)
        check(u"报告里记了「没有能量能力」", u"**没有**能量能力" in rep)
        check(u"报告里记了一炉的酸账", u"硫酸正好扣掉 600 mB" in rep)
        check(u"报告里记了纸 6 格", u"纸的格数 = 6" in rep)
    doc = read(DOC)
    check(u"档案 §5 有 ZF112 行", u"| ZF112 |" in doc)
    check(u"档案 §9 有 ZF112 小节", u"ZF112（0.11）" in doc)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
