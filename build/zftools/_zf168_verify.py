# -*- coding: utf-8 -*-
u"""_zf168_verify.py —— ZF168（0.13 第九笔）**常驻校验**：流体转化器的"输出罐改不了样板"修复。

用户原话：「**转换器的输出储罐好像改不了**」。病根：`FluidTank` 对**异种流体一律拒收**，
而原来只有"容器 → 机器"一条路 ⇒ 样板定了就换不掉。本轮加的就是反方向那条
`fillContainerFrom`（手拿空容器右键 = 从罐装进容器）。

  A 两条路都在：`pourFrom`（容器→罐）与 `fillContainerFrom`（罐→容器），方块里**两条都试**
    （先倒、倒不进就装），并且"目标罐被别的流体占着"时要**明说怎么换**
  B 口径对称：普通=输出罐（样板）/ 潜行=输入罐（原料）；`POUR_PER_CLICK` 仍是 1000
  C 不吞流体：装走的量 = 容器真正拿到的量；倒了倒不进的部分**还回容器**
  D 那条 API 雷：桶包装器**按整桶结算**（`drain(<一桶)` 返回空）⇒ 必须"整桶模拟、整桶取、多的还回"
  E 探针 12/0 + 文档 + 五语新键

跑法：python build\\zftools\\_zf168_verify.py
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANGDIR = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
PROBE = os.path.join(ZT, u"_zf168_probe_utf8.txt")
PROBE2 = os.path.join(ZT, u"_zf174_probe_utf8.txt")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]
NEW_KEY = u"gui.potato_s_t.fluid_converter.pour.occupied"

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else u""


BE = read(os.path.join(JAVA, u"FluidConverterBlockEntity.java"))
BLK = read(os.path.join(JAVA, u"FluidConverterBlock.java"))

print(u"=== A 段：两条路都在，方块两条都试 ===")
check(u"public Pour fillContainerFrom(" in BE, u"A1 方块实体里有 fillContainerFrom（罐 → 容器）")
check(u"be.fillContainerFrom(stack, toOutput" in BLK, u"A2 方块里倒不进时会反过来试装走")
check(u"be.targetBlocked(stack, toOutput)" in BLK, u"A3 目标罐被占时会给提示")
check(u"gui.potato_s_t.fluid_converter.pour.occupied" in BLK, u"A4 提示走的是新加的那个语言键")

print(u"=== B 段：口径对称 / 数字没动 ===")
check(BE.count(u"? this.output : this.input") >= 2, u"B1 两个方法都是「普通=输出罐、潜行=输入罐」",
      u"实际 %d 处" % BE.count(u"? this.output : this.input"))
check(u"POUR_PER_CLICK = 1000" in BE, u"B2 每次手倒仍是 1000 mB")
check(u"RATE = 50" in BE and u"ENERGY_PER_TICK = 30" in BE, u"B3 锁定数字没动（50 mB/t、30 FE/t）")

print(u"=== C 段：不凭空吞流体 ===")
check(u"container.drain(stack, put - taken.getAmount())" in BE, u"C1 自家容器：装多了要退回去")
check(u"handler.drain(put - taken.getAmount()" in BE, u"C2 别的容器：装多了要退回去")
check(u"handler.fill(drained.copyWithAmount(drained.getAmount() - filled)" in BE,
      u"C3 倒的方向：罐里塞不下的部分还回容器")

print(u"=== D 段：桶包装器那条 API 雷 ===")
check(BE.count(u"handler.drain(Integer.MAX_VALUE, IFluidHandler.FluidAction.SIMULATE)") == 2,
      u"D1 两处都按整桶模拟（探桶里有什么 + 倒的方向；drain(<一桶) 会返回空 —— 这条就是那记闷棍）",
      u"实际 %d 处" % BE.count(u"handler.drain(Integer.MAX_VALUE, IFluidHandler.FluidAction.SIMULATE)"))
check(u"handler.drain(sim.getAmount(), IFluidHandler.FluidAction.EXECUTE)" in BE, u"D2 按整桶取，多的再还回")

print(u"=== E 段：探针 / 语言 / 文档 ===")
rep = read(PROBE)
check(u"通过 = 12   失败 = 0" in rep, u"E1 探针 12/0",
      rep.strip().split(u"\n")[-1] if rep else u"（没有报告）")
check(u"D1 现在岩浆倒得进去" in rep, u"E2 报告里有「罐空了 ⇒ 样板换得掉」那条实测")
bad = []
for lg in LOCALES:
    p = os.path.join(LANGDIR, lg + u".json")
    if os.path.isfile(p) and not json.loads(io.open(p, encoding="utf-8").read()).get(NEW_KEY, u"").strip():
        bad.append(lg)
check(not bad, u"E3 五语都有新键且非空", u"缺 %s" % bad)
check(u"### 4.173 " in read(DOC) and u"| ZF168 |" in read(DOC), u"E4 档案 §4.173 + §5 ZF168 行")
check(u"38. **ZF168 的账" in read(HAND), u"E5 交接 §6 第 38 条")
check(u"## New in 0.13 ZF168" in read(ANN), u"E6 英文公告有 ZF168 段")
if os.path.isfile(JAR):
    import zipfile
    names = zipfile.ZipFile(JAR).namelist()
    check(any(u"FluidConverterBlockEntity.class" in n for n in names), u"E7 产物里有转化器 class")
    check(not [n for n in names if u"Check.class" in os.path.basename(n)], u"E8 产物里没有探针 class")
else:
    check(False, u"E0 成品不在")

print(u"=== F 段：倒不进去时必须**吃下交互**（0.13 ZF174：用户报「shift+右键会把流体倒出来」）===")
check(u"FluidConverterBlockEntity.isFluidContainer(stack)" in BLK
      and u"? ItemInteractionResult.sidedSuccess(false)" in BLK,
      u"F1 手里是流体容器却没倒成时**吃下**交互（返回 PASS 会让原版把桶里的流体倒进世界）")
check(u"public static boolean isFluidContainer(" in BE, u"F2 判据在方块实体里（我们的容器 + 任何挂物品流体能力的容器，含空桶）")
rep2 = read(PROBE2)
check(u"通过 = 9   失败 = 0" in rep2, u"F3 block 级探针 9/0（真 FakePlayer + 真 BlockHitResult 调 useItemOn）",
      rep2.strip().split(u"\n")[-1] if rep2 else u"（没有报告）")
check(u"A1 满桶岩浆潜行右键" in rep2, u"F4 报告里有「交互被吃下、岩浆桶还在」那条实测")

print(u"\n通过 = %d   失败 = %d" % (passed, failed))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if failed else 0)
