# -*- coding: utf-8 -*-
r"""_zf98_verify.py —— ZF98 常驻校验：流体泵改成"不存流体、只做传输、优先送目标收得下的"

用户原话（本轮全部规格，一条）：

  「流体泵改一下 本身不能储存流体 只做传输 且优先传输目标容器需要/能被接受 的流体」

骨架仍是**规格 → 实现**：

  A 泵**不存流体**：没有内部罐字段、没有 getFluidHandler()、没有流体能力登记、不再写 "tank"
  B **只做传输**：一 tick 内直连搬运（SIMULATE 问目标 → 抽源 → 灌目标），中途没有第二个容器
  C **优先级**：目标已有的流体先试；目标收 0 **就不抽**（这就是"优先…能被接受"落地处）
  D 老功能一个不少：红石停机 / 速率与电费分档 / 范围公式 / 吸世界源方块 / 防"左脚踩右脚"
  E 旧存档兼容：拆罐前存在泵里的流体被接住并吐出去（**不凭空销毁玩家的东西**）
  F 工具提示四语言都改了口 + 文档
  G 成品 jar
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
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
LANG = os.path.join(ASSETS, "lang")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
EXPECT_KEYS = 482           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键
# 四语言里"泵不存液体"那句话的锚点（各自的措辞）
NO_TANK_PHRASE = {
    "zh_cn": u"泵本身不存液体",
    "en_us": u"stores no fluid itself",
    "ja_jp": u"ポンプ自体は液体を溜めません",
    "ru_ru": u"Насос сам не хранит жидкость",
}

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


def main():
    print(u"=========== ZF98 校验：流体泵 = 不存流体 / 只做传输 / 优先送目标收得下的 ===========")
    pump = read(os.path.join(JAVA, "FluidPumpBlockEntity.java"))
    common = read(os.path.join(JAVA, "PotatoST.java"))
    check(u"泵的源码在", pump is not None)
    pump = pump or u""
    common = common or u""

    print(u"\n== A 泵不存流体 ==")
    check(u"没有内部罐字段（private final FluidTank tank）",
          not re.search(r"private\s+final\s+FluidTank\s+tank\b", pump))
    check(u"没有 getFluidHandler()（泵不再对外暴露罐）",
          u"public IFluidHandler getFluidHandler()" not in pump)
    check(u"旧常量声明 `int TANK_CAPACITY = 8000;` 已经没了，改名成 LEGACY_TANK_CAPACITY"
          u"（只用于读档）",
          u"public static final int TANK_CAPACITY = 8000;" not in pump
          and u"LEGACY_TANK_CAPACITY = 8000" in pump)
    # 能力登记：PotatoST.java 里 FluidHandler.BLOCK 那几处都不许提到泵
    seg = common
    hits = [m.start() for m in re.finditer(r"Capabilities\.FluidHandler\.BLOCK", seg)]
    near = [i for i in hits if seg.find(u"FLUID_PUMP_BE", i, i + 400) >= 0]
    eq(u"PotatoST 里没有给泵登记流体能力（FluidHandler 登记共 %d 处，涉及泵的 0 处）"
       % len(hits), [], near)
    check(u"代码里写明撤销流体能力的原因（用户原话 + 泵里没有罐）",
          u"0.11 ZF98" in common and u"不再暴露流体能力" in common)
    # 存档里不再写 tank
    save = body(pump, u"protected void saveAdditional(CompoundTag tag") or u""
    check(u"存档不再写 \"tank\" 键（只可能写 legacy）",
          u'tag.put("tank"' not in save and u'tag.put("legacy"' in save)

    print(u"\n== B 只做传输：一 tick 内直连搬运 ==")
    tick = body(pump, u"private void serverTick()") or u""
    eq(u"serverTick 里一次都不碰内部罐（this.tank / .tank.）", 0,
       len(re.findall(r"this\.tank|(?:^|[^A-Za-z_])tank\.", tick)))
    push = body(pump, u"private int push(Target output, List<Target> sources, Fluid fluid, "
                      u"int max, int maxInput)") or u""
    check(u"push(...) 抠得出来（= 直连搬运那一段）", push != u"")
    ask = push.find(u"output.handler().fill(offer, IFluidHandler.FluidAction.SIMULATE)")
    take = push.find(u"source.handler().drain(offer.copyWithAmount(accepted)")
    give = push.find(u"output.handler().fill(drained, IFluidHandler.FluidAction.EXECUTE)")
    check(u"顺序 = 先问目标（SIMULATE）→ 再抽源 → 再灌目标（%d < %d < %d）"
           % (ask, take, give), 0 <= ask < take < give)
    check(u"灌进去的比抽出来的少时**把多的塞回源**（绝不凭空吞流体）",
          u"source.handler().fill(back, IFluidHandler.FluidAction.EXECUTE)" in push)
    check(u"serverTick 里调用 push(...) 完成搬运", u"push(output, sources, fluid," in tick)
    check(u"旧的两段式（抽进罐 + 罐压出去）已经彻底消失",
          u"room = TANK_CAPACITY" not in tick and u"this.tank.drain" not in tick
          and u"this.tank.fill" not in tick)

    print(u"\n== C 优先级：目标已有的流体先试、收不下就不抽 ==")
    order = body(pump, u"private List<Fluid> preferenceOrder(Target output, List<Target> sources, "
                       u"int maxInput)") or u""
    check(u"preferenceOrder(...) 抠得出来", order != u"")
    first_out = order.find(u"output.handler().getFluidInTank")
    first_src = order.find(u"source.handler().getFluidInTank")
    check(u"先看**目标**已有的流体，再看源里有什么（%d < %d）" % (first_out, first_src),
          0 <= first_out < first_src)
    check(u"目标收 0 ⇒ 立刻放弃这种流体、不再抽（push 里 return）",
          u"if (accepted <= 0) {\n                    return moved;" in push)
    dest_loop = tick.find(u"for (Target output : outputs)")
    src_loop = tick.find(u"for (Fluid fluid : preferenceOrder(")
    check(u"外层是目标、内层是流体（先把一个目标喂饱再换下一个）",
          0 <= dest_loop < src_loop)
    check(u"整轮搬运仍受速率预算约束（budget / moved）",
          u"int budget = mbPerTick(this.rate);" in tick and u"moved >= budget" in tick)

    print(u"\n== D 老功能一个不少 ==")
    check(u"红石信号 = 停机（hasNeighborSignal 提前返回）",
          u"hasNeighborSignal" in tick and u"if (this.level.hasNeighborSignal(this.getBlockPos()))" in tick)
    check(u"速率 0 = 不耗电不搬运", u"if (this.rate <= 0) {" in tick)
    check(u"电费分档与流量公式原样保留",
          u"public static int fePerTick(int ratePercent)" in pump
          and u"public static int mbPerTick(int ratePercent)" in pump
          and u"FE_BASE_PER_PERCENT = 4" in pump and u"MB_PER_PERCENT = 10" in pump)
    check(u"范围公式原样保留（≤200% 合计 32 格，每 +50% 加 1 格）",
          u"RANGE_FREE = 32" in pump and u"RANGE_STEP_PER = 50" in pump
          and u"public static int maxRange(int ratePercent)" in pump)
    check(u"还是只认液体方块本体 + 源液体（含水方块不算）",
          u"instanceof LiquidBlock" in pump and u"fluid.isSource()" in pump)
    check(u"防「左脚踩右脚」那条（源位置从输出候选里剔除）还在",
          u"sourcePositions.contains(output.pos())" in tick)
    check(u"世界源方块的账本仍随存档保存（world_pump）",
          u'tag.put("world_pump", list)' in save and u'tag.getList("world_pump"' in pump)
    check(u"速率上限仍是 800%", u"MAX_RATE = 800" in pump)

    print(u"\n== E 旧存档兼容：拆罐前泵里的流体不凭空消失 ==")
    load = body(pump, u"protected void loadAdditional(CompoundTag tag") or u""
    check(u"读档时把旧的 \"tank\" 标签接住（读进 legacy）",
          u'tag.getCompound("tank")' in load and u"this.legacy = probe.getFluid().copy()" in load)
    flush = body(pump, u"private int flushLegacy(List<Target> outputs, int max)") or u""
    check(u"flushLegacy(...) 抠得出来", flush != u"")
    check(u"遗留流体确实是**灌进目标**（fill SIMULATE → fill EXECUTE），不是丢掉",
          u"output.handler().fill(offer, IFluidHandler.FluidAction.SIMULATE)" in flush
          and u"IFluidHandler.FluidAction.EXECUTE)" in flush)
    check(u"倒干净之后字段清空（之后新存档里泵不存任何流体）",
          u"this.legacy = left <= 0 ? FluidStack.EMPTY" in flush)
    check(u"flushLegacy 在搬运之前被调用、且占速率预算",
          u"int moved = flushLegacy(outputs, budget);" in tick)

    print(u"\n== F 工具提示与文档 ==")
    for name in LANGS:
        d = json.loads(read(os.path.join(LANG, name + u".json")))
        eq(u"%s 键数（本轮不增减键）" % name, EXPECT_KEYS, len(d))
        tip = d.get(u"tooltip.potato_s_t.fluid_pump", u"")
        check(u"%s 的泵提示写了「不存液体」：%s" % (name, NO_TANK_PHRASE[name]),
              NO_TANK_PHRASE[name] in tip)
        check(u"%s 的泵提示确实换过口（现在是四行，不止原来那一句）" % name,
              tip.count(u"\n") >= 3)
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    check(u"档案里有 ZF98 那一行", u"| ZF98 |" in arch)
    check(u"档案 §4 有本轮那条规矩", u"### 4.66 " in arch)
    check(u"档案 §9 有 ZF98 那一节", u"### ZF98（0.11）" in arch)
    check(u"公告里写了泵不存液体", u"stores no fluid" in ann)

    print(u"\n== G 成品 jar ==")
    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            rel = u"com/potatost/mod/FluidPumpBlockEntity.class"
            check(u"成品里有泵的 class", rel in names)
            check(u"成品里没有探针 class",
                  not [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")])

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
