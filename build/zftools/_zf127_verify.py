# -*- coding: utf-8 -*-
u"""_zf127_verify.py —— ZF127「银线 / 银线轴」常驻校验（静态，不跑服务器）

用户原话：
「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）
  材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t」

七段（判据尽量钉在**用户点名的那些字**上）：
  A 物品：两个物品注册了、耐久 32、进创造页、注释里点名原话与"贴图先不画"；
  B 端子网络：`SILVER_TRANSFER_RATE = 16134`、**铜线档 2048/2048 一个字没变**、
    连接线改成"对端 → 这条线自己的速率"、端子能力按最高档伸缩、NBT 两种格式都认；
  C 接线与渲染：银线轴走自己的分支、与铜线轴**共用**同一个处理器、
    线径 `WIRE_RADIUS` **与改前件逐字节相同**（用户点名"像素大小一样"）、按每条线上色；
  D 资源：两个模型借原版贴图占位、**没有自己的 png**（材质先不画）、
    两条配方与铜线那两条**除材料外结构相同**、且与生成器表逐字节一致；
  E 语言：四语言各 **482** 键、只有那两个新键、其余键与改前件逐字相同、键序不乱；
  F 活体数字：往轮门都跟到 482、待画 **13 → 15** 这条链四处都跟平、
    `_zf71_verify.py` 的 §4.81 UTF-8 钉子补上了；
  G 文档：档案 §4/§5/§9 + 交接 §1/§6 + 公告；
  H 反向：银线**没有**贴图文件、旧的 `Set<BlockPos> connections` 已经不在。

⚠ 本脚本**只读**，不改任何文件；退出码 0 = 全绿。
跑法：
    python build\\zftools\\_zf127_verify.py
"""
import glob
import importlib.util
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
ITEM = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
TEXI = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\item")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
TOOLS = os.path.join(ROOT, r"build\zftools")
DOCS = os.path.join(ROOT, "docs")
BK = r"C:\PotatoST救援\zf127_pre"

MODITEMS = os.path.join(JAVA, u"ModItems.java")
TBE = os.path.join(JAVA, u"TerminalBlockEntity.java")
TB = os.path.join(JAVA, u"TerminalBlock.java")
TR = os.path.join(JAVA, u"client", u"TerminalRenderer.java")

passed = 0
failed = 0
fails = []


def check(name, ok):
    global passed, failed
    if ok:
        passed += 1
        print(u"  [OK]   %s" % name)
    else:
        failed += 1
        fails.append(name)
        print(u"  [FAIL] %s" % name)
    return ok


def read(p):
    return io.open(p, encoding=u"utf-8", newline=u"").read()


def pre(rel):
    """改前件（zf127_pre）里那一份"""
    return read(os.path.join(BK, rel))


def jsonload(p):
    return json.loads(read(p))


# ============================================================
def part_a():
    print(u"\n===== A 物品 =====")
    m = read(MODITEMS)
    check(u"A1 银线登记（id = silver_wire）",
          u'ITEMS.register("silver_wire", () -> new Item(new Item.Properties()));' in m)
    check(u"A2 银线轴登记（id = silver_wire_spool，耐久 32）",
          # ⚠ 第一版只查 `durability(32)));` 这个片段 ⇒ K207（把银线轴改成 16）**没咬住**：
          #   那段文本铜线轴/动力线缆轴上也有。判据必须**连着 id 一起锚**。
          u'ITEMS.register("silver_wire_spool",\n'
          u'                    () -> new Item(new Item.Properties().durability(32)));' in m)
    check(u"A3 两个都进了创造页（§4.82：漏了 = 物品栏看不见 + JEI 搜不到）",
          u"output.accept(SILVER_WIRE.get());" in m
          and u"output.accept(SILVER_WIRE_SPOOL.get());" in m)
    check(u"A4 注释里点名用户原话（「先搞银线」「16134Fe/t」）",
          u"先搞银线" in m and u"16134Fe/t" in m)
    check(u"A5 注释里点名「材质先不画」且写了借的是哪两张原版贴图",
          u"贴图先不画" in m and u"models/item/silver_wire.json" in m
          and u"models/item/silver_wire_spool.json" in m)


def part_b():
    print(u"\n===== B 端子网络 =====")
    b = read(TBE)
    check(u"B1 SILVER_TRANSFER_RATE = 16134（用户给的数）",
          u"public static final int SILVER_TRANSFER_RATE = 16_134;" in b)
    check(u"B2 铜线档一个字没变（TRANSFER_RATE = 2048 / MAX_ENERGY = 2048）",
          u"public static final int TRANSFER_RATE = 2048;" in b
          and u"public static final int MAX_ENERGY = 2048;" in b)
    check(u"B3 容量分档：铜线档 = MAX_ENERGY、更高档 = 2 × 速率",
          u"return lineRate <= TRANSFER_RATE ? MAX_ENERGY : lineRate * 2;" in b)
    check(u"B4 注释里记下探针抓到的第一版 bug（max() 会把铜线档顶到 4096）",
          u"第一版 bug" in b and u"4096" in b)
    check(u"B5 连接集合是「对端 → 这条线的速率」",
          u"private final Map<BlockPos, Integer> connections = new HashMap<>();" in b)
    check(u"B6 旧的 Set<BlockPos> connections 已经不在了",
          u"Set<BlockPos> connections" not in b)
    check(u"B7 IO 接口按 lineRate()/capacity()（不再写死 TRANSFER_RATE/MAX_ENERGY）",
          u"int accepted = Math.min(Math.min(maxReceive, lineRate()), capacity() - energy);" in b
          and u"int extracted = Math.min(Math.min(maxExtract, lineRate()), energy);" in b
          and u"return capacity();" in b)
    check(u"B8 均衡按**每条线自己的速率**（两端取小）",
          u"int line = Math.min(entry.getValue(), other.rateTo(this.getBlockPos()));" in b)
    check(u"B9 addConnection 带速率，且升级不降级",
          u"public boolean addConnection(BlockPos other, int rate) {" in b
          and u"if (rate > old) {" in b)
    check(u"B10 读盘认两种格式：CompoundTag（pos+rate）优先，老存档 LongTag 兜底按铜线",
          u'ListTag list = tag.getList("connections", Tag.TAG_COMPOUND);' in b
          and u'for (Tag entry : tag.getList("connections", Tag.TAG_LONG)) {' in b
          and u"this.connections.put(BlockPos.of(((LongTag) entry).getAsLong()), TRANSFER_RATE);" in b)
    check(u"B11 存盘写 pos + rate",
          u'c.putLong("pos", entry.getKey().asLong());' in b
          and u'c.putInt("rate", entry.getValue());' in b)
    check(u"B12 银线拆掉之后电量夹到新上限（不做隔空搬运）",
          u"if (energy > cap) {" in b)
    check(u"B13 读完连接才知道该按哪档夹（Mth.clamp(this.energy, 0, capacity())）",
          u"this.energy = Mth.clamp(this.energy, 0, capacity());" in b)


def part_c():
    print(u"\n===== C 接线与渲染 =====")
    t = read(TB)
    r = read(TR)
    check(u"C1 银线轴分支在，且用 SILVER_TRANSFER_RATE",
          u"stack.is(ModItems.SILVER_WIRE_SPOOL.get())" in t
          and u"handleConnectionTool(level, pos, player, TerminalBlockEntity.SILVER_TRANSFER_RATE)" in t)
    check(u"C2 铜线轴分支仍在，且用 TRANSFER_RATE（行为与之前一致）",
          u"stack.is(ModItems.COPPER_WIRE_SPOOL.get())" in t
          and u"handleConnectionTool(level, pos, player, TerminalBlockEntity.TRANSFER_RATE)" in t)
    check(u"C3 两个分支**共用**同一个处理器（只有速率参数不同）",
          u"private boolean handleConnectionTool(Level level, BlockPos pos, Player player, int rate) {" in t
          and t.count(u"handleConnectionTool(") == 3)
    check(u"C4 连线时两端都记同一个速率",
          u"if (self.addConnection(previous, rate)) {" in t
          and u"other.addConnection(pos, rate);" in t)
    check(u"C5 紫色动力线缆那条分支没被动（还是 POWER_CABLE_SPOOL + addPowerConnection）",
          u"stack.is(ModItems.POWER_CABLE_SPOOL.get())" in t
          and u"handlePowerConnectionTool(level, pos, player)" in t)
    check(u"C6 渲染器有银白色常量（SILVER_R/G/B/A）",
          u"private static final float SILVER_R = 0.88F, SILVER_G = 0.91F, SILVER_B = 0.95F, SILVER_A = 0.9F;" in r)
    check(u"C7 FE 连线按**每条线自己的速率**上色（renderFeWires）",
          u"boolean silver = entry.getValue() >= TerminalBlockEntity.SILVER_TRANSFER_RATE;" in r
          and u"renderFeWires(terminal, origin, selfAnchor, poseStack, buffer, packedLight, packedOverlay);" in r)
    check(u"C8 动力线缆仍走紫色那一套（renderWireSet + PURPLE）",
          u"terminal.getPowerConnections(), PURPLE_R, PURPLE_G, PURPLE_B, PURPLE_A," in r)
    radius = [l for l in pre(r"src\main\java\com\potatost\mod\client\TerminalRenderer.java").split(u"\n")
              if u"WIRE_RADIUS =" in l]
    now = [l for l in r.split(u"\n") if u"WIRE_RADIUS =" in l]
    check(u"C9 **线径那一行与改前件逐字节相同**（用户点名「连接线缆还是一样的像素大小」）",
          len(radius) == 1 and now and radius[0] in now)


def part_d():
    print(u"\n===== D 资源 =====")
    mw = jsonload(os.path.join(ITEM, u"silver_wire.json"))
    ms = jsonload(os.path.join(ITEM, u"silver_wire_spool.json"))
    check(u"D1 两个模型仍是 item/generated（素材线换贴图**不该动父**）",
          mw.get("parent") == u"minecraft:item/generated"
          and ms.get("parent") == u"minecraft:item/generated")
    # ⚠ ZF128：原来那条「layer0 借原版（铁粒 / 铁锭）」的判据**作废** —— 素材线在本轮期间
    #   把这两张画了（用户当初说"材质先不画"，图到了就换成正向判据 D2 / D2b）。
    check(u"D2 两个模型指向**我们自己的**贴图（素材线 ZF128 期间画的）",
          mw["textures"]["layer0"] == u"potato_s_t:item/silver_wire"
          and ms["textures"]["layer0"] == u"potato_s_t:item/silver_wire_spool")
    ok_png = True
    for name in (u"silver_wire.png", u"silver_wire_spool.png"):
        p = os.path.join(TEXI, name)
        if not os.path.exists(p) or open(p, "rb").read(8) != b"\x89PNG\r\n\x1a\n":
            ok_png = False
    check(u"D2b 那两张 png 在盘上且是真 PNG（读文件头）", ok_png)
    check(u"D3 铜线那两个模型与改前件逐字节相同（没顺手动铜）",
          read(os.path.join(ITEM, u"copper_wire.json"))
          == pre(r"src\main\resources\assets\potato_s_t\models\item\copper_wire.json")
          and read(os.path.join(ITEM, u"copper_wire_spool.json"))
          == pre(r"src\main\resources\assets\potato_s_t\models\item\copper_wire_spool.json"))
    check(u"D4 铜线轴配方与改前件逐字节相同（本轮只**新增**银线那两条）",
          read(os.path.join(RECIPE, u"copper_wire_spool.json"))
          == pre(r"src\main\resources\data\potato_s_t\recipe\copper_wire_spool.json"))

    silver_wire = jsonload(os.path.join(RECIPE, u"silver_wire.json"))
    silver_spool = jsonload(os.path.join(RECIPE, u"silver_wire_spool.json"))
    copper_wire = jsonload(os.path.join(RECIPE, u"copper_wire.json"))
    copper_spool = jsonload(os.path.join(RECIPE, u"copper_wire_spool.json"))
    # ⚠ 第一版拿 pattern 的字面值比（"SS" vs "CC"）⇒ 假 FAIL：**形状一样、字母当然不同**
    #   （字母只是 key 的索引）。要比的是"行列数"与"材料表"（§4.106：期望写错的第三次）。
    shape = lambda r: [len(row) for row in r["pattern"]]           # noqa: E731
    check(u"D5 银线配方 = 铜线配方（形状/数量一样，材料换成 #c:ingots/silver）",
          shape(silver_wire) == shape(copper_wire)
          and silver_wire["result"]["count"] == copper_wire["result"]["count"] == 4
          and silver_wire["key"]["S"]["tag"] == u"c:ingots/silver"
          and copper_wire["key"]["C"]["tag"] == u"c:ingots/copper"
          and len(silver_wire["key"]) == len(copper_wire["key"]) == 1)
    check(u"D6 银线轴配方 = 铜线轴配方（同一张 3×3 图纸，8 根线 + 空线轴）",
          shape(silver_spool) == shape(copper_spool) == [3, 3, 3]
          and silver_spool["key"]["S"] == copper_spool["key"]["S"]
          and silver_spool["key"]["W"]["item"] == u"potato_s_t:silver_wire"
          and copper_spool["key"]["W"]["item"] == u"potato_s_t:copper_wire")

    # 生成器表 ↔ 盘上 JSON 逐字节（§4.93：配方只改表再 --write）
    spec = importlib.util.spec_from_file_location(u"zf45", os.path.join(TOOLS, u"_zf45_recipes.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    names = [r["name"] for r in mod.RECIPES]
    check(u"D7 两条都在生成器表 `_zf45_recipes.py` 里（表是唯一来源）",
          u"silver_wire" in names and u"silver_wire_spool" in names)
    problems = []
    built = dict(mod.build(r, problems) for r in mod.RECIPES)
    ok_bytes = True
    for name in (u"silver_wire", u"silver_wire_spool"):
        want = json.dumps(built[name], ensure_ascii=False, indent=2) + u"\n"
        if read(os.path.join(RECIPE, name + u".json")) != want:
            ok_bytes = False
    check(u"D8 盘上那两条 JSON == 生成器表算出来的（逐字节）", ok_bytes and not problems)
    tag = jsonload(os.path.join(ROOT, r"src\main\resources\data\c\tags\item\ingots\silver.json"))
    check(u"D9 `#c:ingots/silver` 里有我们自己的银锭（配方摆得进去）",
          u"potato_s_t:silver_ingot" in tag["values"])

    n_recipe = len(glob.glob(os.path.join(RECIPE, u"*.json")))
    shaped = 0
    for p in glob.glob(os.path.join(RECIPE, u"*.json")):
        if jsonload(p).get("type") == u"minecraft:crafting_shaped":
            shaped += 1
    check(u"D10 配方目录 %d 份（活体数字；其中 crafting_shaped %d 条）" % (n_recipe, shaped),
          n_recipe >= 68 and shaped >= 58)


def part_e():
    print(u"\n===== E 四语言 =====")
    tables = {}
    for loc in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"):
        tables[loc] = jsonload(os.path.join(LANG, loc + u".json"))
    check(u"E1 四份各 482 键（本轮 +2）", all(len(t) == 482 for t in tables.values()))
    check(u"E2 四份键集合完全一致", len({tuple(sorted(t)) for t in tables.values()}) == 1)
    want = {u"zh_cn": u"银线", u"en_us": u"Silver Wire", u"ja_jp": u"銀線",
            u"ru_ru": u"Серебряный провод"}
    check(u"E3 `item.potato_s_t.silver_wire` 四语言的值都写了",
          all(tables[l].get(u"item.potato_s_t.silver_wire") == v for l, v in want.items()))
    want2 = {u"zh_cn": u"银线轴", u"en_us": u"Silver Wire Spool", u"ja_jp": u"銀線のスプール",
             u"ru_ru": u"Катушка с серебряным проводом"}
    check(u"E4 `item.potato_s_t.silver_wire_spool` 四语言的值都写了",
          all(tables[l].get(u"item.potato_s_t.silver_wire_spool") == v for l, v in want2.items()))

    same, order_ok = True, True
    for loc in tables:
        old = jsonload(os.path.join(BK, r"src\main\resources\assets\potato_s_t\lang", loc + u".json"))
        for k, v in old.items():
            if tables[loc].get(k) != v:
                same = False
        it = iter(tables[loc])
        if not all(k in it for k in old):      # 老键序必须是新键序的子序列（只插了两个键）
            order_ok = False
    check(u"E5 除新增那两个键外，**老键的值与改前件逐字相同**", same)
    check(u"E6 老键的相对顺序没乱（新键序是老键序的超序列）", order_ok)


def part_f():
    print(u"\n===== F 活体数字与门 =====")
    left = []
    for fn in sorted(os.listdir(TOOLS)):
        if not fn.endswith(u".py") or fn in (u"_zf125_falsify.py", u"_zf126_falsify.py"):
            continue
        # ⚠ 也要跳过**本脚本自己** —— F1 的标签里就写着那个旧数字（自指的经典坑）
        if fn == u"_zf127_verify.py":
            continue
        if not any(k in fn for k in (u"_verify", u"_guard", u"_repro", u"_audit")):
            continue
        if re.search(r"\b476\b", read(os.path.join(TOOLS, fn))):
            left.append(fn)
    check(u"F1 常驻门里再没有裸的旧键数（除两份历史刀与本脚本自己）", not left)

    z71 = read(os.path.join(TOOLS, u"_zf71_verify.py"))
    ann = read(os.path.join(DOCS, u"UpdateAnnouncement_EN.md"))
    z90 = read(os.path.join(TOOLS, u"_zf90_verify.py"))
    listing = read(os.path.join(DOCS, u"贴图清单.md"))
    # ⚠ ZF128：待画那个数**每来一张美术素材就动一次**（素材线在本轮期间把银线那两张画了 ⇒ 15 → 13，
    #   他们同时也把 `_zf71/_zf90/公告` 三处手改成了 13）。这条判据从此**问 TextureCheck 现数**，
    #   两边自动对齐 —— 而且 `PYTHONIOENCODING=utf-8` 是必须的：被管道调起来的子进程默认按 GBK 输出，
    #   父进程按 UTF-8 解码就会把「待画」两字解成乱码、正则一条都匹配不上（§4.81 的镜像面）。
    import subprocess as _sp
    _r = _sp.run([sys.executable, os.path.join(TOOLS, u"TextureCheck.py")],
                 stdout=_sp.PIPE, stderr=_sp.STDOUT, cwd=TOOLS,
                 env=dict(os.environ, PYTHONIOENCODING=u"utf-8"))
    _m = re.search(r"待画\s*=\s*(\d+)", _r.stdout.decode(u"utf-8", u"replace"))
    _n = int(_m.group(1)) if _m else -1
    check(u"F2 `_zf71_verify.py` 的 n_draw == TextureCheck 现数（%d）" % _n,
          _n > 0 and (u"n_draw == %d" % _n) in z71)
    check(u"F3 公告那句 `%d models still do this` 在" % _n,
          _n > 0 and (u"%d models still do this" % _n) in ann)
    check(u"F4 `_zf90_verify.py` 三处都跟到现数（%d）" % _n,
          _n > 0 and (u"%d models still do this" % _n) in z90
          and (u'"n_draw == %d" in z71' % _n) in z90
          and (u"## 待画（%d 个" % _n) in z90)
    check(u"F5 贴图清单表头 == TextureCheck 现数（%d 个）" % _n,
          _n > 0 and (u"## 待画（%d 个" % _n) in listing)
    check(u"F5b 银线那两张已经搬进「已经有自己贴图的」表",
          u"| `textures/item/` | `silver_wire.png` | 银线 |" in listing
          and u"| `textures/item/` | `silver_wire_spool.png` | 银线轴 |" in listing)
    check(u"F6 `_zf71_verify.py` 补上了 §4.81 的 UTF-8 stdout 钉子（否则被管道调起来必崩）",
          u'sys.stdout.reconfigure(encoding="utf-8", errors="replace")' in z71)
    check(u"F7 公告键数 = 482", u"(482 keys each)" in ann)
    check(u"F8 公告里有银线那一节（0.11 ZF127）",
          u"ZF127" in ann and u"Silver Wire" in ann)


def part_g():
    print(u"\n===== G 文档 =====")
    arc = read(os.path.join(DOCS, u"开发档案.md"))
    hand = read(os.path.join(DOCS, u"多会话协作交接.md"))
    check(u"G1 档案 §5 有 ZF127 那一行", u"| ZF127 |" in arc)
    check(u"G2 档案 §9 有 ZF127 小节", u"### ZF127（0.11）" in arc)
    check(u"G3 档案 §4 记了本轮的新雷（§4.105 / §4.106 / §4.109 都有）",
          u"### 4.105" in arc and u"### 4.106" in arc and u"### 4.109" in arc)
    check(u"G4 交接文档的键数活体数字 = 482", u"**482 键 × 4**" in hand or u"482 键 × 4" in hand)
    check(u"G5 交接文档 §6 有第 19 条（ZF127）", u"19. **ZF127 的账" in hand)


def part_h():
    print(u"\n===== H 反向 =====")
    check(u"H1 银线那两张贴图**在盘上**（素材线已经画了；ZF127 时它们是借原版贴图的占位）",
          os.path.exists(os.path.join(TEXI, u"silver_wire.png"))
          and os.path.exists(os.path.join(TEXI, u"silver_wire_spool.png")))
    tb = read(TB)
    power_block = tb[tb.index(u"POWER_CABLE_SPOOL"):tb.index(u"COPPER_WIRE_SPOOL")]
    check(u"H2 紫色动力那一套里没有银线（动力 ≠ FE，两套网络不许混）",
          u"SILVER" not in power_block and u"handlePowerConnectionTool" in power_block)
    probe = os.path.join(TOOLS, u"_zf127_probe_utf8.txt")
    if os.path.exists(probe):
        text = read(probe)
        m = re.search(r"通过 (\d+)", text)
        check(u"H3 探针报告在盘上且**全绿**（%s 项）" % (m.group(1) if m else u"?"),
              u"全绿" in text and m is not None and int(m.group(1)) >= 40)
    else:
        check(u"H3 探针报告在盘上", False)


def main():
    part_a()
    part_b()
    part_c()
    part_d()
    part_e()
    part_f()
    part_g()
    part_h()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == u"__main__":
    sys.exit(main())
