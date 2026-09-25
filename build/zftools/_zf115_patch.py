# -*- coding: utf-8 -*-
u"""_zf115_patch.py —— 把 ZF112 留下的三处字面量跟到 ZF115 的新数（600 / 800 / 1）

① 探针 `Zf112Check.java`：从存档抄回 src，并把里面的字面量改成新数（§4.27：探针的期望值
   一律写字面量、不从被测常量抄 —— 所以改数必须**手改探针**，探针才会真的验到新数）；
② `_zf112_verify.py`：几处断言 + 探针报告里的字样；
③ `_zf112_falsify.py`：K133/K134 的锚点（原来钉 10 / 8000，现在是 1 / 800）。
"""
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, r"build\zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
fails = []


def patch(path, pairs, name):
    t = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        if t.count(old) < 1:
            fails.append(u"%s：锚点没命中（%s）" % (name, old[:46]))
            continue
        t = t.replace(old, new)
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t)
    print(u"  [OK] %s" % name)


# ① 探针：从存档抄回 src 并改字面量
ARCH = os.path.join(ZT, r"check\Zf112Check.java")
SRC = os.path.join(JAVA, "Zf112Check.java")
shutil.copy2(ARCH, SRC)
patch(SRC, [
    (u"eq(\"每 tick 10 mB\", 10, LithiumBatteryPlantBlockEntity.ACID_PER_TICK);",
     u"eq(\"每 tick 1 mB（ZF115：原来是 10）\", 1, LithiumBatteryPlantBlockEntity.ACID_PER_TICK);"),
    (u"eq(\"一炉 6000 mB\", 6000, LithiumBatteryPlantBlockEntity.ACID_PER_OPERATION);",
     u"eq(\"一炉 600 mB（ZF115：原来是 6000）\", 600, "
     u"LithiumBatteryPlantBlockEntity.ACID_PER_OPERATION);"),
    (u"eq(\"罐装得下一炉（8000 ≥ 6000）\", 8000, LithiumBatteryPlantBlockEntity.TANK_CAPACITY);",
     u"eq(\"罐装得下一炉（800 ≥ 600）\", 800, LithiumBatteryPlantBlockEntity.TANK_CAPACITY);"),
    (u"new FluidStack(ModFluids.SULFURIC_ACID.get(), 1000), IFluidHandler.FluidAction.EXECUTE);\n"
     u"        eq(\"硫酸灌得进去 1000 mB\", 1000, taken);",
     u"new FluidStack(ModFluids.SULFURIC_ACID.get(), 500), IFluidHandler.FluidAction.EXECUTE);\n"
     u"        eq(\"硫酸灌得进去 500 mB\", 500, taken);"),
    (u"eq(\"罐里 1000 mB\", 1000, be.getTank().getFluidAmount());",
     u"eq(\"罐里 500 mB\", 500, be.getTank().getFluidAmount());"),
    (u"while (be.getTank().getFluidAmount() < 6000)", u"while (be.getTank().getFluidAmount() < 600)"),
    (u"eq(\"开机前罐里有 6000 mB（一炉的量）\", 6000, be.getTank().getFluidAmount());",
     u"eq(\"开机前罐里有 600 mB（一炉的量）\", 600, be.getTank().getFluidAmount());"),
    (u"eq(\"硫酸正好扣掉 6000 mB\", 0, be.getTank().getFluidAmount());",
     u"eq(\"硫酸正好扣掉 600 mB\", 0, be.getTank().getFluidAmount());"),
    (u"while (be.getTank().getFluidAmount() >= 10) {\n            be.getTank().drain(10,",
     u"while (be.getTank().getFluidAmount() >= 1) {\n            be.getTank().drain(1,"),
], u"探针字面量")

# ② 常驻校验
patch(os.path.join(ZT, u"_zf112_verify.py"), [
    (u'check(u"每 tick 10 mB", "ACID_PER_TICK = 10;" in be)',
     u'check(u"每 tick 1 mB（ZF115）", "ACID_PER_TICK = 1;" in be)'),
    (u'check(u"罐 8000（装得下一炉）", "TANK_CAPACITY = 8000;" in be)',
     u'check(u"罐 800（装得下一炉 600）", "TANK_CAPACITY = 800;" in be)'),
    (u'eq(u"罐装得下一炉（8000 ≥ 6000）", 8000, LithiumBatteryPlantBlockEntity.TANK_CAPACITY)',
     u'eq(u"罐装得下一炉（800 ≥ 600）", 800, LithiumBatteryPlantBlockEntity.TANK_CAPACITY)'),
    (u'check(u"报告里记了一炉的酸账", u"硫酸正好扣掉 6000 mB" in rep)',
     u'check(u"报告里记了一炉的酸账", u"硫酸正好扣掉 600 mB" in rep)'),
], u"_zf112_verify")

# ③ 反证刀锚点
patch(os.path.join(ZT, u"_zf112_falsify.py"), [
    (u'("K133", u"硫酸从 10 mB/t 改成 1 mB/t", BE, u"ACID_PER_TICK = 10;", u"ACID_PER_TICK = 1;",\n'
     u'     u"每 tick 10 mB"),',
     u'("K133", u"硫酸从 1 mB/t 改回 10 mB/t（ZF115 后的刀）", BE, u"ACID_PER_TICK = 1;",\n'
     u'     u"ACID_PER_TICK = 10;", u"每 tick 1 mB"),'),
    (u'("K134", u"罐从 8000 改回 2000（装不下一炉）", BE, u"TANK_CAPACITY = 8000;",\n'
     u'     u"TANK_CAPACITY = 2000;", u"罐 8000"),',
     u'("K134", u"罐从 800 改回 8000（与消耗不匹配）", BE, u"TANK_CAPACITY = 800;",\n'
     u'     u"TANK_CAPACITY = 8000;", u"罐 800"),'),
], u"_zf112_falsify")

print(u"失败项 = %d" % len(fails))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if fails else 0)
