# -*- coding: utf-8 -*-
u"""_zf80_verify.py —— ZF80 交付校验（常驻，跑在门里）

用户原话：「灌装机不往油桶灌液体」。
探针 `FillingOilCheck` 把整条链验了一遍（**83 项全过**，含"原油池 → 泵 → 灌装机 → 空油桶"复刻），
⇒ 机器逻辑没坏；四种完全不同的成因（罐空 / 缺电 / 罐里是气体 / 容器已满）玩家看到的
都是"一点反应都没有"。所以本轮交付两件：

  ① 手倒：手里拿容器右键机器 ⇒ 倒进罐（原先只能靠管道/泵）
  ② 诊断：空手 Shift 右键 ⇒ 逐槽说清"为什么没在灌"

分区：
  A 手倒（pourFrom / pickTankFor / PourOutcome）      B 诊断（stateOf 与灌装逻辑逐条对齐）
  C 方块交互（两种右键各走哪条路）                     D 语言（ZF80 时四份 257 键 + 新 9 键；ZF82 起 270）
  E 回归（这台机器与石油线的既有行为不许被带坏）        F 成品与文档
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
RES = os.path.join(ROOT, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
LANG = os.path.join(ASSETS, "lang")
TOOLS = os.path.join(ROOT, "build", "zftools")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")

LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
NEW_KEYS = [
    u"gui.potato_s_t.filling.pour.poured",
    u"gui.potato_s_t.filling.pour.empty",
    u"gui.potato_s_t.filling.pour.noroom",
    u"gui.potato_s_t.filling.diag.tank_empty",
    u"gui.potato_s_t.filling.diag.slot_empty",
    u"gui.potato_s_t.filling.diag.full",
    u"gui.potato_s_t.filling.diag.no_power",
    u"gui.potato_s_t.filling.diag.rejected",
    u"gui.potato_s_t.filling.diag.filling",
]
EXPECT_KEYS = 432           # … + ZF112 锂电池构造间 9 键

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


def body(java, signature):
    u"""按大括号配对抠出方法/枚举体（签名必须唯一出现，否则返回 None）。

    ⚠ 用 find 不用 index：片段被删掉时 index 会抛异常把整个校验脚本带崩，
      反证台就解析不到汇总行（ZF79 那轮真踩过，见档案 §9）。
    """
    if not java:
        return None
    at = java.find(signature)
    if at < 0 or java.find(signature, at + 1) >= 0:
        return None
    i = java.find(u"{", at + len(signature) - 1)
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(java)):
        if java[j] == u"{":
            depth += 1
        elif java[j] == u"}":
            depth -= 1
            if depth == 0:
                return java[i:j + 1]
    return None


def order(text, fragments):
    u"""片段在文本里的先后顺序（有任何一个找不到就返回 None）。"""
    if text is None:
        return None
    pos = []
    for frag in fragments:
        at = text.find(frag)
        if at < 0:
            return None
        pos.append(at)
    return pos


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


def sig(value):
    u"""与 LangCheck.ps1 的 Get-Sig 同口径。"""
    return u"|".join(u"%" + c for c in re.findall(r"%([sdif%])", value))


def lang(l):
    p = os.path.join(LANG, l + u".json")
    return json.loads(io.open(p, encoding="utf-8").read()) if os.path.exists(p) else None


# ================= A 手倒 =================

def section_a():
    print(u"\n== A 手倒：手里拿容器右键 = 倒进罐 ==")
    be = src("FillingMachineBlockEntity.java")
    c = int_consts(be)
    eq(u"一次倒 1000 mB（POUR_PER_CLICK）", 1000, c.get("POUR_PER_CLICK"))

    pour = body(be, u"public PourOutcome pourFrom(ItemStack stack)")
    check(u"pourFrom 抠得出来（方法签名唯一）", pour is not None)
    if pour is None:
        return
    seq = order(pour, [
        u"if (!(stack.getItem() instanceof FluidContainerItem container)) {",
        u"FluidStack held = container.contents(stack);",
        u"if (held.isEmpty()) {",
        u"int target = pickTankFor(held);",
        u"tank.fill(held.copyWithAmount(want), IFluidHandler.FluidAction.SIMULATE);",
        u"FluidStack drained = container.drain(stack, accepted);",
        u"int moved = tank.fill(drained, IFluidHandler.FluidAction.EXECUTE);",
        u"setChanged();",
        u"return new PourOutcome(PourResult.POURED, target, moved, tank.getFluid().copy());",
    ])
    check(u"四步顺序：认容器 → 取内容 → 选罐 → SIMULATE → 真取 → 真灌 → setChanged", seq is not None)
    if seq:
        check(u"顺序真的是这个先后（位置递增）", all(seq[i] < seq[i + 1] for i in range(len(seq) - 1)))
    check(u"六条失败出口（1 非容器 + 1 空容器 + 4 处倒不进）",
          pour.count(u"return PourOutcome.of(PourResult.") == 6)
    check(u"三个失败码都用上了（NO_CONTAINER / EMPTY / NO_ROOM）",
          all(u"PourOutcome.of(PourResult.%s)" % n in pour
              for n in [u"NO_CONTAINER", u"EMPTY", u"NO_ROOM"]))
    check(u"多取的流体**塞回容器**（绝不凭空吞流体）",
          u"container.fill(stack, back, back.getAmount());" in pour
          and pour.find(u"container.fill(stack, back") < pour.find(u"if (moved <= 0)"))
    check(u"SIMULATE 先问能收多少再真取（不会取多了塞不回去）",
          pour.find(u"SIMULATE") < pour.find(u"container.drain(stack, accepted)"))

    pick = body(be, u"private int pickTankFor(FluidStack held)")
    check(u"pickTankFor 抠得出来", pick is not None)
    if pick:
        check(u"① 先找**装着同种流体**且有空间的罐",
              u"&& this.tanks[i].getFluid().getFluid() == held.getFluid()" in pick
              and u"&& this.tanks[i].getFluidAmount() < this.tanks[i].getCapacity()" in pick)
        check(u"② 再找第一个**空罐**", u"if (this.tanks[i].isEmpty()) {" in pick)
        check(u"③ 都不行 = −1（异种流体不混装）", u"return -1;" in pick)

    check(u"PourOutcome 四个字段（结果 / 罐号 / 量 / 流体）",
          u"public record PourOutcome(PourResult result, int tank, int amount, FluidStack fluid)"
          in be)
    check(u"四个结果码齐（NO_CONTAINER / EMPTY / NO_ROOM / POURED）",
          all(re.search(r"\b%s\b" % n, body(be, u"public enum PourResult") or u"") for n in
              [u"NO_CONTAINER", u"EMPTY", u"NO_ROOM", u"POURED"]))


# ================= B 诊断 =================

def section_b():
    print(u"\n== B 诊断：stateOf 必须与灌装逻辑逐条对齐 ==")
    be = src("FillingMachineBlockEntity.java")
    fill = body(be, u"private boolean tryFillSlot(int index)")
    state = body(be, u"public SlotState stateOf(int index)")
    check(u"tryFillSlot / stateOf 都抠得出来", fill is not None and state is not None)
    if fill is None or state is None:
        return

    guards = [u"if (tank.isEmpty()) {", u"if (container == null) {",
              u"if (container.space(inSlot) <= 0) {", u"if (this.energy < ENERGY_PER_TANK) {"]
    a = order(fill, guards)
    b = order(state, guards)
    check(u"灌装逻辑的四道判据顺序 = 抠得出来", a is not None)
    check(u"诊断的四道判据顺序 = 抠得出来", b is not None)
    if a and b:
        check(u"两边判据**顺序完全相同**（罐 → 容器 → 空间 → 电）",
              all(a[i] < a[i + 1] for i in range(3)) and all(b[i] < b[i + 1] for i in range(3)))
    # ⚠ 判据要**逐字**比对：反证 K14 把 `this.energy < ENERGY_PER_TANK` 改成 `… * 2`，
    #   而坏串正好**包含**好串 ⇒ 只查"子串在不在"的写法会放它过去（§4.30「先怀疑期望」同源）。
    same = [g for g in guards if fill.count(g) == 1 and state.count(g) == 1]
    check(u"四道判据两边**逐字相同**（%d/4：%s）" % (len(same), same),
          len(same) == 4)
    check(u"诊断最后一关问的也是**同一个问题**（容器收不收这种流体）",
          u"if (!container.accepts(tank.getFluid().getFluid())) {" in state
          and u"int moved = container.fill(inSlot, tank.getFluid(), FILL_RATE);" in fill)

    st = body(be, u"public enum SlotState")
    names = [u"TANK_EMPTY", u"SLOT_EMPTY", u"FULL", u"NO_POWER", u"REJECTED", u"FILLING"]
    check(u"SlotState 六个状态齐全（%s）" % u"/".join(names),
          st is not None and all(re.search(r"\b%s\b" % n, st) for n in names))
    eq(u"stateOf 正好六条 return（没有多余分支）", 6, state.count(u"return SlotState."))
    check(u"诊断读数三个口子（电量 / 罐里流体 / 容器剩余空间）",
          u"public int getEnergy()" in be and u"public FluidStack fluidOf(int index)" in be
          and u"public int spaceOf(int index)" in be)
    check(u"spaceOf 没容器时返回 −1（界面/诊断要能分辨「没容器」与「满了」）",
          u"return container == null ? -1 : container.space(inSlot);" in be)


# ================= C 方块交互 =================

def section_c():
    print(u"\n== C 方块交互：空手 Shift = 诊断，手拿容器 = 倒，其余原样 ==")
    blk = src("FillingMachineBlock.java")
    use = body(blk, u"protected InteractionResult useWithoutItem(BlockState state, Level level, "
                    u"BlockPos pos, Player player,")
    check(u"useWithoutItem 抠得出来", use is not None)
    if use:
        check(u"Shift 走诊断", u"if (serverPlayer.isShiftKeyDown()) {" in use
              and u"diagnose(serverPlayer, be);" in use)
        check(u"不按 Shift 仍然开界面（原行为不动）", u"serverPlayer.openMenu(be);" in use)
        check(u"诊断在开界面之前判（Shift 分支在后）",
              use.find(u"diagnose(serverPlayer, be);") < use.find(u"serverPlayer.openMenu(be);"))

    item = body(blk, u"protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, "
                     u"Level level, BlockPos pos,")
    check(u"useItemOn 抠得出来", item is not None)
    if item:
        check(u"手里不是容器 ⇒ 原样放行（回到开界面那条路）",
              u"""        if (!(stack.getItem() instanceof FluidContainerItem)) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }""" in item)
        check(u"手里是容器 ⇒ 交给 pourFrom", u"be.pourFrom(stack)" in item)
        check(u"倒成功放倒水声", u"SoundEvents.BUCKET_EMPTY" in item)
        check(u"三种结果各有提示（倒成 / 空容器 / 倒不进）",
              all(k in item for k in [u"gui.potato_s_t.filling.pour.poured",
                                      u"gui.potato_s_t.filling.pour.empty",
                                      u"gui.potato_s_t.filling.pour.noroom"]))

    diag = body(blk, u"private static void diagnose(ServerPlayer player, "
                     u"FillingMachineBlockEntity be)")
    check(u"diagnose 抠得出来", diag is not None)
    if diag:
        keys = [u"diag.tank_empty", u"diag.slot_empty", u"diag.full", u"diag.no_power",
                u"diag.rejected", u"diag.filling"]
        check(u"六个状态各有文案（%d/6）" % sum(1 for k in keys if k in diag),
              all(u"gui.potato_s_t.filling." + k in diag for k in keys))
        check(u"槽号从 1 开始念给玩家", u"int slot = i + 1;" in diag)
        check(u"五个罐全念（循环到 TANK_COUNT）",
              u"i < FillingMachineBlockEntity.TANK_COUNT" in diag)
        check(u"诊断走聊天栏（false = 聊天，不是 actionbar）",
              u"player.displayClientMessage(line, false);" in diag)


# ================= D 语言 =================

def section_d():
    print(u"\n== D 四份语言 ==")
    data = {}
    for l in LANGS:
        obj = lang(l)
        check(u"%s 解析得动" % l, obj is not None)
        data[l] = obj or {}
        eq(u"%s 键数 = %d" % (l, EXPECT_KEYS), EXPECT_KEYS, len(obj or {}))
    base = set(data[LANGS[0]].keys())
    check(u"四份键集合完全一致",
          all(set(data[l].keys()) == base for l in LANGS))
    missing = {l: [k for k in NEW_KEYS if k not in data[l]] for l in LANGS}
    check(u"9 个新键四份都齐（缺 %s）" % (missing if any(missing.values()) else u"无"),
          not any(missing.values()))
    badsig = [k for k in NEW_KEYS if len(set(sig(data[l].get(k, u"")) for l in LANGS)) != 1]
    check(u"新键的 %%s 占位符签名四份一致（缺 %s）" % (badsig or u"无"), not badsig)
    for l in LANGS:
        tip = data[l].get(u"tooltip.potato_s_t.filling_machine", u"")
        check(u"%s：tooltip 已改成「流体」（不再说气体）" % l,
              all(w not in tip for w in [u"气体", u"ガス", u"газом"]))
        check(u"%s：tooltip 提了新手势（Shift 诊断）" % l, u"Shift" in tip or u"shift" in tip)
    stale = [k for k in [u"gui.potato_s_t.distillation.diagnosis.found",
                         u"gui.potato_s_t.distillation.pour.rejected",
                         u"block.potato_s_t.asphalt_block",
                         u"gui.potato_s_t.hydraulic_press.status.material",
                         u"tooltip.potato_s_t.high_pressure_tank.total",
                         u"block.potato_s_t.filling_machine"]
             if k not in base]
    check(u"老键一个没丢（抽查 6 个：%s）" % (stale or u"都在"), not stale)


# ================= E 回归 =================

def section_e():
    print(u"\n== E 回归：既有行为不许被带坏 ==")
    be = src("FillingMachineBlockEntity.java")
    c = int_consts(be)
    eq(u"五个罐", 5, c.get("TANK_COUNT"))
    eq(u"每罐 5000 mB", 5000, c.get("TANK_CAPACITY"))
    eq(u"每 tick 灌 5 mB", 5, c.get("FILL_RATE"))
    eq(u"每罐每 tick 60 FE", 60, c.get("ENERGY_PER_TANK"))
    eq(u"缓冲 3000 FE", 3000, c.get("MAX_ENERGY"))
    fill = body(be, u"private boolean tryFillSlot(int index)") or u""
    check(u"灌装核心三步没动（灌 → 罐扣 → 扣电）",
          u"int moved = container.fill(inSlot, tank.getFluid(), FILL_RATE);" in fill
          and u"tank.drain(moved, IFluidHandler.FluidAction.EXECUTE);" in fill
          and u"this.energy -= ENERGY_PER_TANK;" in fill)
    check(u"五个罐仍对任何流体开放（ZF73 那条不改回去）",
          u"return stack != null && !stack.isEmpty();" in be)

    menu = src("FillingMachineMenu.java")
    check(u"三道门禁仍同口径（手放 / Shift 快移 / 方块实体）",
          menu.count(u"stack.getItem() instanceof FluidContainerItem") == 2
          and (src("FillingMachineBlockEntity.java") or u"").count(
              u"return stack.getItem() instanceof FluidContainerItem;") == 1)
    check(u"菜单里不许再出现写死的高压气罐（§4.51 负向断言）",
          u"HighPressureTankItem" not in menu)
    eq(u"菜单里重复的 Fluids 导入已清（这轮顺手修的）", 1,
       menu.count(u"import net.minecraft.world.level.material.Fluids;"))

    mf = src("ModFluids.java")
    isg = body(mf, u"public static boolean isGas(Fluid fluid)")
    check(u"气体判定仍是**正向**白名单（§4.44：负向判定是待还的债）",
          isg is not None and u"Tags.Fluids.GASEOUS" in isg
          and all(g in isg for g in [u"OXYGEN.get()", u"HYDROGEN.get()", u"CHLORINE.get()"]))
    check(u"isGas 里不许出现「非水非岩浆」那种负向写法", isg is not None
          and u"Fluids.WATER" not in isg and u"Fluids.LAVA" not in isg)
    check(u"液体判定 = 非气体（油桶收任何液体）",
          u"return !isGas(fluid);" in mf)
    obc = src("OilBucketContents.java")
    check(u"油桶的收液规则走 ModFluids.isLiquid",
          u"return ModFluids.isLiquid(fluid);" in obc)
    check(u"油桶仍然只装一种（异种拒收那条没被手倒绕过）",
          u"if (have != Fluids.EMPTY && have != incoming) {" in obc)


# ================= F 成品与文档 =================

def section_f():
    print(u"\n== F 成品与文档 ==")
    sha_file = JAR + u".sha1"
    sha = None
    if os.path.exists(JAR):
        raw = open(JAR, "rb").read()
        sha = hashlib.sha1(raw).hexdigest()
        rec = read(sha_file)
        check(u".sha1 与 jar 实际哈希一致（%s…）" % sha[:8],
              rec is not None and rec.strip().lower() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            bad = [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
            check(u"成品里没有探针 class（%s）" % (bad or u"0 个"), not bad)
            inside = json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode(u"utf-8"))
        eq(u"成品里的中文语言文件也是 %d 键" % EXPECT_KEYS, EXPECT_KEYS, len(inside))
        miss = [k for k in NEW_KEYS if k not in inside]
        check(u"成品里带着 9 个新键（缺 %s）" % (miss or u"无"), not miss)
    else:
        check(u"成品 jar 存在", False)

    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    plan = read(os.path.join(DOCS, u"v0.11规划.md")) or u""
    ann = read(os.path.join(DOCS, u"UpdateAnnouncement_EN.md")) or u""
    check(u"档案里有 ZF80 那一行", u"| ZF80 |" in arch)
    check(u"档案里记了 §4.52 这条新雷", u"### 4.52" in arch)
    check(u"档案里写了「灌装机不往油桶灌液体」这次实测", u"不往油桶灌液体" in arch)
    check(u"档案里留了探针结论 83 项全过", u"83 项" in arch or u"83/0" in arch)
    if sha:
        check(u"档案里写着当前成品哈希 %s…" % sha[:8], sha in arch)
        check(u"规划/公告里也写到这一轮",
              (u"ZF80" in plan) and (u"ZF80" in ann or u"diagnosis" in ann))
    check(u"文档里没有 __NEWSHA__ 之类的占位残留",
          u"__NEWSHA__" not in arch and u"__NEWSHA__" not in plan and u"__NEWSHA__" not in ann)


def main():
    print(u"=========== ZF80 校验：灌装机手倒 + 逐槽诊断 ===========")
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    section_f()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
