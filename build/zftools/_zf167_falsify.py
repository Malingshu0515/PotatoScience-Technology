# -*- coding: utf-8 -*-
u"""_zf167_falsify.py —— ZF167 的反证：**每一把刀都必须被点名的那一条判据咬住**

判据不能只证明"现在是绿的"。这里逐把往被测对象上砍一刀，要求 `_zf167_verify.py`
**点名的那一条**变红（只红不点名不算数）。31 把刀覆盖：

    可乐        音效 / 两条时长 / 营养 3 / 饱和 9 / 原版 usingConvertsTo / 不许自己写返还
    配方表      一轮 100 tick / 600 FE/t / 2糖1豆1罐 / 10-500-0 mB
    机器        三罐容量 / 乙醇标签 / 状态码新号 / 整批扣流体 / 扣三样 / 直写产物 / 检查顺序
    方块        挂 ticker / 手倒走物品能力 / ItemInteractionResult / useWithoutItem / 掉落
    注册        三处 ModBlocks / 三条能力 / JEI 的 MACHINES+case（ZF123 的真坑）/ JEI 常量转调
    资源        占位贴图逐字节 / 四份配方形状与产物 / c:ethanol 标签 / 语言缺键 / 硬编码中文

每把刀：① 精确替换（锚点必须**正好一次**）→ ② 跑 `_zf167_verify.py --fast` →
③ 要求 `[FAIL] <点名 id>` 真的出现 → ④ **逐字节还原**并复核 sha256。

跑法：python build\\zftools\\_zf167_falsify.py
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, r"build\zftools")
VERIFY = os.path.join(TOOLS, "_zf167_verify.py")
MOD = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(ASSETS, "lang")
DATA = os.path.join(ROOT, r"src\main\resources\data")

COLA = os.path.join(MOD, "ColaItem.java")
RECIPES = os.path.join(MOD, "CanningMachineRecipes.java")
BE = os.path.join(MOD, "BeverageCanningMachineBlockEntity.java")
BLOCK = os.path.join(MOD, "BeverageCanningMachineBlock.java")
ITEMS = os.path.join(MOD, "ModItems.java")
BLOCKS = os.path.join(MOD, "ModBlocks.java")
MAIN = os.path.join(MOD, "PotatoST.java")
JEI = os.path.join(MOD, r"client\jei\PotatoSTJeiPlugin.java")
MACHINE_RECIPES = os.path.join(MOD, "MachineRecipes.java")
LAMP = os.path.join(MOD, r"client\gui\parts\StatusLampPart.java")

# (名字, 文件, 原文, 换成, 必须变红的判据 id)
KNIVES = [
    (u"K01 急迫 120s → 60s", COLA, u"HASTE_TICKS = 20 * 120;", u"HASTE_TICKS = 20 * 60;", u"A3"),
    (u"K02 食用音效退回默认（GENERIC_EAT）", COLA,
     u"    public SoundEvent getEatingSound() {\n        return SoundEvents.HONEY_DRINK;\n    }",
     u"    public SoundEvent getEatingSound() {\n        return SoundEvents.GENERIC_EAT;\n    }", u"A2"),
    (u"K03 饱和度修饰 1.5 → 1.0（就不是 9 点了）", ITEMS,
     u".saturationModifier(1.5F)", u".saturationModifier(1.0F)", u"A4"),
    (u"K04 饥饿值 3 → 4", ITEMS, u".nutrition(3)", u".nutrition(4)", u"A4"),
    (u"K05 删掉 usingConvertsTo（不返还空罐了）", ITEMS,
     u"                            .usingConvertsTo(EMPTY_ALUMINUM_CAN.get()) // 吃完返还一个空铝罐（用户给的）\n",
     u"", u"A6"),
    (u"K06 自己写一套返还逻辑（不走原版）", COLA,
     u"    public ColaItem(Item.Properties properties) {",
     u"    @Override\n    public ItemStack finishUsingItem(ItemStack s, Level l, net.minecraft.world.entity.LivingEntity e) {\n"
     u"        return new ItemStack(ModItems.EMPTY_ALUMINUM_CAN.get());\n    }\n\n"
     u"    public ColaItem(Item.Properties properties) {", u"A6"),
    (u"K07 耗电 600 → 500 FE/t", RECIPES, u"ENERGY_PER_TICK = 600;", u"ENERGY_PER_TICK = 500;", u"A7"),
    (u"K08 一轮 5 秒 → 10 秒", RECIPES, u"DURATION_TICKS = 20 * 5;", u"DURATION_TICKS = 20 * 10;", u"A7"),
    (u"K09 水 500 → 100 mB", RECIPES, u"WATER_MB = 500;", u"WATER_MB = 100;", u"A9"),
    (u"K10 水罐容量 1000 → 2000", BE, u"TANK_CAPACITY_WATER = 1000;", u"TANK_CAPACITY_WATER = 2000;", u"A11"),
    (u"K11 乙醇罐改成什么都收（兼容性没意义了）", BE,
     u"new FluidTank(TANK_CAPACITY_ETHANOL, s -> s != null && !s.isEmpty() && s.getFluid().is(ETHANOL_TAG));",
     u"new FluidTank(TANK_CAPACITY_ETHANOL, s -> s != null && !s.isEmpty());", u"A16"),
    (u"K12 缺流体蹭液压机的号（20 → 6）", BE,
     u"STATUS_NO_FLUID = 20;", u"STATUS_NO_FLUID = 6;", u"A24"),
    (u"K13 结算时漏扣水", BE,
     u"        this.tanks[TANK_WATER].drain(can.waterMb(), IFluidHandler.FluidAction.EXECUTE);\n", u"", u"A20"),
    (u"K14 产物改用 insertItem（会被输出槽门禁静默吞掉）", BE,
     u"        ItemStack existing = this.items.getStackInSlot(SLOT_OUTPUT);\n"
     u"        if (existing.isEmpty()) {\n"
     u"            this.items.setStackInSlot(SLOT_OUTPUT, can.createOutput());\n"
     u"        } else {\n"
     u"            this.items.setStackInSlot(SLOT_OUTPUT,\n"
     u"                    existing.copyWithCount(existing.getCount() + can.resultCount()));\n"
     u"        }",
     u"        this.items.insertItem(SLOT_OUTPUT, can.createOutput(), false);", u"A22"),
    (u"K15 每 tick 把流体检查提到电之前", BE,
     u"        if (this.energy < can.energyPerTick()) {\n            this.status = STATUS_NO_POWER;\n            return;\n        }\n"
     u"        if (!hasFluids(can)) {\n            this.status = STATUS_NO_FLUID;\n            return;\n        }",
     u"        if (!hasFluids(can)) {\n            this.status = STATUS_NO_FLUID;\n            return;\n        }\n"
     u"        if (this.energy < can.energyPerTick()) {\n            this.status = STATUS_NO_POWER;\n            return;\n        }",
     u"A19"),
    (u"K16 手倒只认本 mod 的容器（水桶倒不进去）", BLOCK,
     u"        IFluidHandlerItem held = stack.getCapability(Capabilities.FluidHandler.ITEM);",
     u"        IFluidHandlerItem held = stack.getItem() instanceof FluidContainerItem ? null : null;", u"A27"),
    (u"K17 useItemOn 返回类型退回 InteractionResult（1.21 编不过）", BLOCK,
     u"    protected ItemInteractionResult useItemOn(", u"    protected InteractionResult useItemOn(", u"A28"),
    (u"K18 删掉 useWithoutItem（空手开不了界面）", BLOCK,
     u"    @Override\n    protected InteractionResult useWithoutItem(", u"    @Override\n    protected InteractionResult REMOVED_useWithoutItem(", u"A29"),
    (u"K19 破坏时不掉出槽里的东西", BLOCK,
     u"            MachineDrops.dropInventory(level, pos, be.getInventory());\n", u"", u"A30"),
    (u"K20 ModBlocks 少注册方块实体", BLOCKS,
     u'            BLOCK_ENTITIES.register("beverage_canning_machine",', u'            BLOCK_ENTITIES.SKIPPED("beverage_canning_machine",', u"A31"),
    (u"K21 PotatoST 少注册流体能力", MAIN,
     u"        event.registerBlockEntity(\n                Capabilities.FluidHandler.BLOCK,\n"
     u"                ModBlocks.BEVERAGE_CANNING_MACHINE_BE.get(),\n"
     u"                (machine, side) -> machine.getFluidHandler());\n",
     u"", u"A33"),
    (u"K22 JEI 加了 MACHINES 却漏 case（ZF123 那个真坑）", JEI,
     u'            case "beverage_canning_machine" -> new ItemStack(ModBlocks.BEVERAGE_CANNING_MACHINE_ITEM.get());\n',
     u"", u"A35"),
    (u"K23 JEI 那条展示里写死 500（不转调常量）", MACHINE_RECIPES,
     u"                        new FluidAmount(net.minecraft.world.level.material.Fluids.WATER,\n"
     u"                                CanningMachineRecipes.WATER_MB)),",
     u"                        new FluidAmount(net.minecraft.world.level.material.Fluids.WATER, 500)),", u"A37"),
    (u"K24 状态灯没挂新号（悬停会说成'材料不够'）", LAMP,
     u'            case BeverageCanningMachineBlockEntity.STATUS_NO_FLUID -> "no_fluid";\n', u"", u"A25"),
    (u"K25 ModItems 里塞一句硬编码中文串", ITEMS,
     u"public class ModItems {", u"public class ModItems {\n    private static final String ZF167_K25 = \"罐装机\";", u"A38"),
]

# 资源刀（改数据/贴图/语言）
RES_KNIVES = [
    (u"K26 空铝罐图纸第三行填上东西", u"can_pattern", u"B4"),
    (u"K27 熔炉产物 5 → 1 个铝粒", u"smelt_count", u"B3"),
    (u"K28 机器图纸的轻质压力板换成铁块", u"machine_key", u"B6"),
    (u"K29 c:ethanol 标签改成 replace:true", u"tag_replace", u"B8"),
    (u"K30 语言缺一个键（ja_jp 少 status.no_fluid）", u"lang_missing", u"B11"),
    (u"K31 占位贴图动一个字节", u"tex_byte", u"B1"),
]

fails = []


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def sha256b(b):
    return hashlib.sha256(b).hexdigest()


def run_verify():
    r = subprocess.run([sys.executable, VERIFY, u"--fast"], cwd=ROOT, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def count_reds(out):
    u"""只数**行首**的 `[FAIL]`。

    ⚠ 第一版用 `out.count("[FAIL]")` ⇒ 校验脚本里那条「报告里 0 条 [FAIL]」的**标签**
    自己被数成一条红 ⇒ 反证永远认为"起点不干净"（自锁）。标签已改，计数也改成行首匹配。
    """
    return len(re.findall(u"(?m)^\\s*\\[FAIL\\]", out))


def restore(path, original):
    open(path, "wb").write(original)
    return sha256(path) == sha256b(original)


def knife_text(name, path, old, new, expect):
    if not os.path.exists(path):
        fails.append(u"%s：%s 不在" % (name, path))
        return
    original = open(path, "rb").read()
    text = original.decode("utf-8")
    n = text.count(old)
    if n != 1:
        print(u"  [SKIP] %s —— 锚点出现 %d 次（要 1）" % (name, n))
        fails.append(u"%s：锚点 %d 次" % (name, n))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(text.replace(old, new, 1))
    rc, out = run_verify()
    hit = (u"[FAIL] %s " % expect) in out or (u"[FAIL] %s\n" % expect) in out
    ok_restore = restore(path, original)
    print(u"  [%s] %-44s ⇒ %s（exit=%d）%s"
          % (u"OK" if (hit and ok_restore) else u"!!", name, u"咬住" if hit else u"**没咬住**", rc,
             u"" if ok_restore else u"  ⚠ 还原失败！"))
    if not hit:
        fails.append(u"%s：点名判据 %s 没红" % (name, expect))
    if not ok_restore:
        fails.append(u"%s：还原不逐字节相同" % name)


def knife_res(name, kind, expect):
    if kind == u"can_pattern":
        p = os.path.join(DATA, r"potato_s_t\recipe\empty_aluminum_can.json")
        original = open(p, "rb").read()
        d = json.loads(original.decode("utf-8"))
        d[u"pattern"][2] = u"NPN"
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        rc, out = run_verify()
        hit = u"[FAIL] %s " % expect in out
        ok_restore = restore(p, original)
    elif kind == u"smelt_count":
        p = os.path.join(DATA, r"potato_s_t\recipe\empty_aluminum_can_from_smelting.json")
        original = open(p, "rb").read()
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            original.decode("utf-8").replace(u'"count": 5', u'"count": 1'))
        rc, out = run_verify()
        hit = u"[FAIL] %s " % expect in out
        ok_restore = restore(p, original)
    elif kind == u"machine_key":
        p = os.path.join(DATA, r"potato_s_t\recipe\beverage_canning_machine.json")
        original = open(p, "rb").read()
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            original.decode("utf-8").replace(u"minecraft:light_weighted_pressure_plate",
                                              u"minecraft:iron_block"))
        rc, out = run_verify()
        hit = u"[FAIL] %s " % expect in out
        ok_restore = restore(p, original)
    elif kind == u"tag_replace":
        p = os.path.join(DATA, r"c\tags\fluid\ethanol.json")
        original = open(p, "rb").read()
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            original.decode("utf-8").replace(u'"replace": false', u'"replace": true'))
        rc, out = run_verify()
        hit = u"[FAIL] %s " % expect in out
        ok_restore = restore(p, original)
    elif kind == u"lang_missing":
        p = os.path.join(LANG, "ja_jp.json")
        original = open(p, "rb").read()
        d = json.loads(original.decode("utf-8"))
        d.pop(u"gui.potato_s_t.beverage_canning_machine.status.no_fluid", None)
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        rc, out = run_verify()
        hit = u"[FAIL] %s " % expect in out
        ok_restore = restore(p, original)
    elif kind == u"tex_byte":
        p = os.path.join(ASSETS, r"textures\block\beverage_canning_machine_top.png")
        original = open(p, "rb").read()
        b = bytearray(original)
        b[len(b) // 2] ^= 0xFF
        open(p, "wb").write(bytes(b))
        rc, out = run_verify()
        hit = u"[FAIL] %s " % expect in out
        ok_restore = restore(p, original)
    else:
        fails.append(u"%s：未知刀型 %s" % (name, kind))
        return
    print(u"  [%s] %-44s ⇒ %s（exit=%d）%s"
          % (u"OK" if (hit and ok_restore) else u"!!", name, u"咬住" if hit else u"**没咬住**", rc,
             u"" if ok_restore else u"  ⚠ 还原失败！"))
    if not hit:
        fails.append(u"%s：点名判据 %s 没红" % (name, expect))
    if not ok_restore:
        fails.append(u"%s：还原不逐字节相同" % name)


def main():
    total = len(KNIVES) + len(RES_KNIVES)
    print(u"== 反证开始（%d 把文本刀 + %d 把资源刀）==" % (len(KNIVES), len(RES_KNIVES)))
    print(u"\n[起点] 先确认校验现在是绿的")
    rc, out = run_verify()
    nfail = count_reds(out)
    print(u"  exit=%d，[FAIL] %d 条" % (rc, nfail))
    if nfail > 0:
        print(u"  [!!] 起点就不干净（可能探针报告还没跑出来），先修好再来")
        return 1
    for name, path, old, new, expect in KNIVES:
        knife_text(name, path, old, new, expect)
    for name, kind, expect in RES_KNIVES:
        knife_res(name, kind, expect)

    print(u"\n== 收尾：全部还原之后再跑一次校验 ==")
    rc, out = run_verify()
    nfail = count_reds(out)
    tail = [l for l in out.split(u"\n") if u"通过" in l]
    print(u"  %s" % (tail[-1] if tail else u"（没有统计行）"))
    if nfail:
        fails.append(u"收尾：还原后仍有 %d 条红" % nfail)

    print(u"\n被咬住 %d / %d 把，失败项 = %d" % (total - len(fails), total, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
