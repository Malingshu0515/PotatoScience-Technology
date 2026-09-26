# -*- coding: utf-8 -*-
u"""_zf82_verify.py —— ZF82 交付校验（常驻，跑在门里）

用户原话两件：
  ① 「新进 柴油桶 汽油桶（先用水桶贴图）和原版水桶一致 可以倒出相应的流体返回空桶
     并可以被空桶收回源头液体」
  ② 「【容器换流器】… 3s后 消耗油罐内1000mb的液体 把桶变成相应的流体桶
     （别的mod的流体也可以，前提是流体有对应桶的形式）流体泵也可以把液体泵出
     这个是直接消耗油罐的流体容量 然后泵出 有多少泵多少（取决于泵的速率）」

分区：
  A 两个桶（官方桶映射 / 放置 / 舀取 / 原油仍无桶的回归）
  B 容器换流器（数值 / 状态码 / 结算顺序 / 门槛）
  C 泵接口（抽的就是左槽容器 / 只出不进 / SIMULATE 不消耗）
  D 资源与合成配方（用户给的九宫格）
  E 语言（四份 270 键 + 13 个新键）
  F 成品与文档
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
DATA = os.path.join(RES, "data", "potato_s_t")
LANG = os.path.join(ASSETS, "lang")
DOCS = os.path.join(ROOT, "docs")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru"]
EXPECT_KEYS = 482           # … + ZF112 锂电池构造间 9 键 + ZF117 进度 16 键
NEW_KEYS = [
    u"item.potato_s_t.diesel_bucket", u"item.potato_s_t.gasoline_bucket",
    u"block.potato_s_t.diesel", u"block.potato_s_t.gasoline",
    u"block.potato_s_t.fluid_exchanger", u"tooltip.potato_s_t.fluid_exchanger",
    u"gui.potato_s_t.fluid_exchanger.status.empty",
    u"gui.potato_s_t.fluid_exchanger.status.invalid",
    u"gui.potato_s_t.fluid_exchanger.status.output_full",
    u"gui.potato_s_t.fluid_exchanger.status.running",
    u"gui.potato_s_t.fluid_exchanger.status.material",
    u"gui.potato_s_t.fluid_exchanger.status.no_bucket",
    u"gui.potato_s_t.fluid_exchanger.status.gas",
]

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


# ================= A 两个桶 =================

def section_a():
    print(u"\n== A 柴油桶 / 汽油桶 ==")
    fluids = src("ModFluids.java")
    items = src("ModItems.java")
    blocks = src("ModBlocks.java")
    for name in [u"diesel", u"gasoline"]:
        upper = name.upper()
        check(u"%s 的流动参数挂了 .bucket(ModItems.%s_BUCKET)"
              % (name, upper), u".bucket(ModItems.%s_BUCKET)" % upper in fluids)
        check(u"%s 的流动参数挂了 .block(ModBlocks.%s)" % (name, upper),
              u".block(ModBlocks.%s)" % upper in fluids)
        check(u"%s 的属性链里**不许**出现 FluidType 上的 can* 开关（那是 liquidType 的活）"
              % name,
              u".canConvertToSource" not in (body(fluids, u"private static BaseFlowingFluid.Properties %sProperties()" % name) or u""))
    check(u"两个桶都是原版 BucketItem（放置/舀取/返空桶全走原版）",
          u"new BucketItem(ModFluids.DIESEL.get()" in items
          and u"new BucketItem(ModFluids.GASOLINE.get()" in items)
    check(u"两个桶都设了 craftRemainder(Items.BUCKET).stacksTo(1)（原版水桶同款）",
          items.count(u"new Item.Properties().craftRemainder(Items.BUCKET).stacksTo(1)") >= 2)
    for name in [u"DIESEL", u"GASOLINE"]:
        check(u"ModBlocks.%s 是 LiquidBlock 且 properties 照原油那套" % name,
              u'BLOCKS.register("%s"' % name.lower() in blocks
              and u"public static final DeferredBlock<LiquidBlock> %s = BLOCKS.register" % name in blocks)
    check(u"两个液体方块**都没有** BlockItem（液体方块不进物品栏）",
          u'"diesel",\n                    () -> new BlockItem' not in blocks
          and u'"gasoline",\n                    () -> new BlockItem' not in blocks)
    check(u"原油仍然**故意不设** .bucket(...)（ZF73 老规矩：一桶 3000 mB 会白送三倍）",
          u"故意不调 {@code .bucket(...)}" in fluids
          and u".bucket(ModItems.OIL_BUCKET)" not in fluids)
    check(u"石脑油 / 液化石油气也没加桶（用户只点了柴油与汽油）",
          u".bucket(ModItems.NAPHTHA_BUCKET" not in fluids
          and u".bucket(ModItems.LPG_BUCKET" not in fluids)


# ================= B 换流器 =================

def section_b():
    print(u"\n== B 容器换流器 ==")
    be = src("FluidExchangerBlockEntity.java")
    c = int_consts(be)
    eq(u"一次换桶的时间 60 tick（3 秒）", 60, c.get("DURATION_TICKS"))
    eq(u"一次换 1000 mB", 1000, c.get("AMOUNT_PER_OPERATION"))
    eq(u"左槽 = 0 / 右槽 = 1 / 共 2 槽", 0, c.get("LEFT_SLOT"))
    eq(u"右槽号", 1, c.get("RIGHT_SLOT"))
    eq(u"槽位数", 2, c.get("SLOT_COUNT"))
    ok_codes = {u"STATUS_EMPTY": 1, u"STATUS_INVALID": 2, u"STATUS_OUTPUT_FULL": 4,
                u"STATUS_RUNNING": 5, u"STATUS_MATERIAL": 6,
                u"STATUS_NO_BUCKET": 7, u"STATUS_GAS": 8}
    bad = [k for k, v in ok_codes.items() if c.get(k) != v]
    check(u"七个状态码沿用全模组那一套（1/2/4/5/6 复用 + 7/8 新加；不符 %s）" % (bad or u"无"),
          not bad)
    check(u"状态灯部件认得 7/8 两个新码（否则灯是灰的、悬停是空）",
          u"FluidExchangerBlockEntity.STATUS_NO_BUCKET" in
          (src("StatusLampPart.java", sub=os.path.join("client", "gui", "parts")) or u"")
          and u"FluidExchangerBlockEntity.STATUS_GAS" in
          (src("StatusLampPart.java", sub=os.path.join("client", "gui", "parts")) or u""))

    tick = body(be, u"private void serverTick()")
    check(u"serverTick 抠得出来", tick is not None)
    if tick:
        seq = [u"FluidContainerItem container = leftContainer();",
               u"if (held.isEmpty()) {",
               u"if (ModFluids.isGas(held.getFluid())) {",
               u"Item bucket = held.getFluid().getBucket();",
               u"if (bucket == Items.AIR) {",
               u"if (held.getAmount() < AMOUNT_PER_OPERATION) {",
               u"if (!right.is(Items.BUCKET) || right.getCount() != 1) {",
               u"this.progress++;",
               u"finish(container, bucket);"]
        pos = [tick.find(x) for x in seq]
        check(u"九步判据顺序齐全且递增（空→气体→有桶→量够→右槽→进度→结算）"
              u"（缺：%s）" % [x for x, p in zip(seq, pos) if p < 0],
              all(p >= 0 for p in pos) and all(pos[i] < pos[i + 1] for i in range(len(pos) - 1)))
        check(u"加满即结算（与液压机同款，不许拖到下一 tick）",
              tick.find(u"this.progress++;") < tick.find(u"finish(container, bucket);")
              and u"this.progress >= this.progressMax" in tick)
    fin = body(be, u"private void finish(FluidContainerItem container, Item bucket)")
    check(u"finish 抠得出来", fin is not None)
    if fin:
        check(u"先取后放（取不到 1000 mB 就把取出来的还回去，绝不吞流体）",
              fin.find(u"container.drain(left, AMOUNT_PER_OPERATION)") < fin.find(
                  u"this.items.setStackInSlot(RIGHT_SLOT, new ItemStack(bucket));")
              and u"container.fill(left, drained, drained.getAmount());" in fin)
    check(u"右槽产物就是那个流体的官方桶",
          u"this.items.setStackInSlot(RIGHT_SLOT, new ItemStack(bucket));" in be)
    check(u"左槽容器内容变了要写回槽位（物品组件里的流体）",
          u"this.items.setStackInSlot(LEFT_SLOT, left);" in be)


# ================= C 泵接口 =================

def section_c():
    print(u"\n== C 泵接口（直接抽左槽那件容器）==")
    be = src("FluidExchangerBlockEntity.java")
    handler = body(be, u"public IFluidHandler getFluidHandler()")
    check(u"getFluidHandler 抠得出来", handler is not None)
    if handler:
        check(u"报的流体 = 左槽容器的内容物（不是机器自己的罐）",
              u"return leftContents();" in handler)
        check(u"容量 = 容器容量（装着多少 + 还能装多少）",
              u"container.contents(stack).getAmount() + container.space(stack)" in handler)
        check(u"只出不进：fill 恒 0 且 isFluidValid 恒 false",
              u"return 0;" in handler and u"return false;   // 只抽不倒" in handler)
        check(u"指名流体的 drain 会先比对种类（异种不抽）",
              u"held.getFluid() != resource.getFluid()" in handler)
    drain = body(be, u"public FluidStack drainFromLeftContainer(int maxAmount, "
                     u"IFluidHandler.FluidAction action)")
    check(u"drainFromLeftContainer 抠得出来", drain is not None)
    if drain:
        check(u"SIMULATE 只算不取（内容物在物品组件里，取了就真没了）",
              drain.find(u"if (action.simulate()) {") < drain.find(u"container.drain(stack, take)"))
        check(u"真取的那一步走容器自己的 drain",
              u"FluidStack drained = container.drain(stack, take);" in drain)
    pot = src("PotatoST.java")
    check(u"能力登记：流体（六面）", u"ModBlocks.FLUID_EXCHANGER_BE.get(),\n"
                                  u"                (exchanger, side) -> exchanger.getFluidHandler()" in pot)
    check(u"能力登记：物品（六面）",
          u"(exchanger, side) -> exchanger.getInventory()" in pot)
    check(u"**没有**登记能量能力（用户没给能耗数 ⇒ 本轮不耗电，也不许偷偷加）",
          u"FLUID_EXCHANGER_BE.get(),\n                (exchanger, side) -> exchanger.getEnergyStorage" not in pot
          and not os.path.exists(os.path.join(SRC, "FluidExchangerEnergy.java")))


# ================= D 资源与配方 =================

def section_d():
    print(u"\n== D 资源与合成配方 ==")
    need = [u"blockstates/diesel.json", u"blockstates/gasoline.json",
            u"models/block/diesel.json", u"models/block/gasoline.json",
            u"models/item/diesel_bucket.json", u"models/item/gasoline_bucket.json",
            u"blockstates/fluid_exchanger.json", u"models/block/fluid_exchanger.json",
            u"models/item/fluid_exchanger.json",
            u"textures/block/fluid_exchanger.png"]
    missing = [n for n in need if not os.path.exists(os.path.join(ASSETS, *n.split(u"/")))]
    check(u"资源齐（缺 %s）" % (missing or u"无"), not missing)
    for name in [u"diesel_bucket", u"gasoline_bucket"]:
        obj = json.loads(read(os.path.join(ASSETS, "models", "item", name + u".json")))
        # ⚠ 0.11 ZF90：用户先后给这两张桶贴图 ⇒ 从"借原版水桶"改成指向自己的图。
        #   本条断言改成新真相（ZF87/ZF89 同一改法：不删历史，把断言改成现在的真相）。
        eq(u"%s 的物品模型指向自己的贴图（ZF90 起，不再借原版水桶）" % name,
           u"potato_s_t:item/" + name, obj.get(u"textures", {}).get(u"layer0"))
    rec_p = os.path.join(DATA, "recipe", u"fluid_exchanger.json")
    rec = json.loads(read(rec_p)) if os.path.exists(rec_p) else {}
    eq(u"配方类型 = crafting_shaped", u"minecraft:crafting_shaped", rec.get(u"type"))
    eq(u"配方图案 = 用户给的三行", [u" M ", u"PBP", u"FTF"], rec.get(u"pattern"))
    keys = rec.get(u"key", {})
    want = {u"M": u"potato_s_t:common_metal_block", u"P": u"potato_s_t:iron_plate",
            u"B": u"potato_s_t:oil_bucket", u"F": u"potato_s_t:fluid_pipe",
            u"T": u"potato_s_t:high_pressure_tank"}
    bad = {k: v for k, v in want.items() if keys.get(k, {}).get(u"item") != v}
    check(u"五个材料 id 与用户说的对得上（不符 %s）" % (bad or u"无"), not bad)
    eq(u"产物 = potato_s_t:fluid_exchanger",
       u"potato_s_t:fluid_exchanger", rec.get(u"result", {}).get(u"id"))


# ================= E 语言 =================

def section_e():
    print(u"\n== E 四份语言 ==")
    data = {}
    for l in LANGS:
        p = os.path.join(LANG, l + u".json")
        data[l] = json.loads(read(p)) if os.path.exists(p) else {}
        eq(u"%s 键数 = %d" % (l, EXPECT_KEYS), EXPECT_KEYS, len(data[l]))
    base = set(data[LANGS[0]].keys())
    check(u"四份键集合一致", all(set(data[l].keys()) == base for l in LANGS))
    miss = {l: [k for k in NEW_KEYS if k not in data[l]] for l in LANGS}
    check(u"13 个新键四份都齐（缺 %s）" % (miss if any(miss.values()) else u"无"),
          not any(miss.values()))
    sig = lambda s: u"|".join(u"%" + ch for ch in re.findall(r"%([sdif%])", s))
    badsig = [k for k in NEW_KEYS if len(set(sig(data[l].get(k, u"")) for l in LANGS)) != 1]
    check(u"新键占位符签名四份一致（缺 %s）" % (badsig or u"无"), not badsig)
    nl = [len(data[l].get(u"tooltip.potato_s_t.fluid_exchanger", u"").split(u"\n")) for l in LANGS]
    check(u"换流器 tooltip 四份行数一致（%s）" % nl, len(set(nl)) == 1 and nl[0] >= 3)
    stale = [k for k in [u"item.potato_s_t.oil_bucket", u"block.potato_s_t.crude_oil",
                         u"fluid_type.potato_s_t.diesel", u"block.potato_s_t.asphalt_block",
                         u"tooltip.potato_s_t.filling_machine"]
             if k not in base]
    check(u"老键一个没丢（抽查 5 个：%s）" % (stale or u"都在"), not stale)


# ================= F 成品与文档 =================

def section_f():
    print(u"\n== F 成品与文档 ==")
    sha = None
    if os.path.exists(JAR):
        sha = hashlib.sha1(open(JAR, "rb").read()).hexdigest()
        rec = read(JAR + u".sha1")
        check(u".sha1 与 jar 一致（%s…）" % sha[:8],
              rec is not None and rec.strip().lower() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names = zf.namelist()
            bad = [n for n in names if u"Check" in n.split(u"/")[-1] and n.endswith(u".class")]
            check(u"成品里没有探针 class（%s）" % (bad or u"0 个"), not bad)
            inside = json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode(u"utf-8"))
            need = [u"assets/potato_s_t/models/item/diesel_bucket.json",
                    u"assets/potato_s_t/models/item/gasoline_bucket.json",
                    u"assets/potato_s_t/textures/block/fluid_exchanger.png",
                    u"data/potato_s_t/recipe/fluid_exchanger.json"]
            miss = [n for n in need if n not in names]
            check(u"成品里带着本轮的新资源（缺 %s）" % (miss or u"无"), not miss)
        eq(u"成品里中文键数 = %d" % EXPECT_KEYS, EXPECT_KEYS, len(inside))
        miss = [k for k in NEW_KEYS if k not in inside]
        check(u"成品里带着 13 个新键（缺 %s）" % (miss or u"无"), not miss)
    else:
        check(u"成品 jar 存在", False)

    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    listing = read(os.path.join(DOCS, u"贴图清单.md")) or u""
    ann = read(os.path.join(DOCS, u"UpdateAnnouncement_EN.md")) or u""
    check(u"档案里有 ZF82 那一行", u"| ZF82 |" in arch)
    check(u"档案里记了用户原话（两件都记）",
          u"新进 柴油桶 汽油桶" in arch and u"容器换流器" in arch)
    check(u"档案里写了探针结论 48 项全过", u"48" in arch and u"探针" in arch)
    check(u"档案里记了 ZF82 的两个坑（属性链放错类 / 探针自己的旧断言）",
          u"4.54" in arch and u"4.55" in arch)
    check(u"贴图清单里登记了柴油桶/汽油桶（借水桶贴图）与换流器占位图",
          u"diesel_bucket" in listing and u"fluid_exchanger" in listing)
    check(u"英文公告里有 ZF82 两件与 270 键", u"Container Fluid Exchanger" in ann
          and u"482 keys each" in ann)
    if sha:
        check(u"档案里写着当前成品哈希 %s…" % sha[:8], sha in arch)
    check(u"文档里没有 __NEWSHA__ 之类的占位残留", u"__NEWSHA__" not in arch)


def main():
    print(u"=========== ZF82 校验：柴油桶/汽油桶 + 容器换流器 ===========")
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
