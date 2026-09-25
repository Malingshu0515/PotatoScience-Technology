# -*- coding: utf-8 -*-
u"""_zf109_verify.py —— ZF109 常驻校验：采油机（0.11）

用户原话：「海洋油田可以利用起来了 加一个采油机（配方；【硬质钛合金】【耐热金属块】【硬质钛合金】，
【油桶】【高压气罐】【油桶】，【流体泵】【流体泵】【流体泵】） 在海洋油田群系工作
gui为一个大罐子25B储量（不是那种竖直的了 是一个横过来的矩形罐子）和一个工作指示灯
能量条不需要 下方必须有水源方块 检测下方连接的 含水锁链的数量
耗能公式为 80n*1/10n+80n FE/t 原油获取为 10n mb/s （n为下方含水链个数）
每开采25~80桶原油 附近10*10的海洋油桶群系会变成符合旁边群系的海洋（冻洋 暖洋 温带海洋...）」
用户拍板：耗能公式 = **B 读法 8n²+80n**；转换范围 = **10×10 区块**。

十一段，逐段都能失败（§4.17）：
  ① 文件账目 ② 配方逐格核对（用户原话那张九宫格） ③ 常数与公式（**真算**，不是看字符串）
  ④ 方块实体语义（群系门禁 / 下探计数 / 抽干触发） ⑤ 群系转换器（原版 API 三件套 + 只改油田 + 票选）
  ⑥ 注册与能力 ⑦ 界面（横躺罐 + 状态灯前缀 + 没有能量条 + 没有槽位）
  ⑧ 状态码 15/16 的接线与配色 ⑨ 四语言 408 键 ⑩ 资源（blockstate / 模型 / 贴图 / 挖掘标签）
  ⑪ 探针的 UTF-8 报告（真游戏跑出来的那份）还在且全绿
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
TEXB = os.path.join(ASSETS, r"textures\block")
LANG = os.path.join(ASSETS, r"lang")
BK = r"C:\PotatoST救援\zf109_pre"
DOC = os.path.join(ROOT, r"docs\开发档案.md")
PLAN = os.path.join(ROOT, r"docs\贴图清单.md")
ANN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
REPORT = os.path.join(ROOT, r"build\zftools\_zf109_probe_utf8.txt")

# 家族调色板（ZF108 从微型粉碎机/燃烧反应室量出来的；采油机只用了其中 5 个）
FAMILY = {(0x4a, 0x4a, 0x52), (0x34, 0x36, 0x3b), (0x23, 0x23, 0x2a),
          (0x6e, 0x6e, 0x78), (0x9a, 0xa2, 0xac), (0xc4, 0x60, 0x22), (0xe8, 0x91, 0x2f)}

NEW_JAVA = ["OilPumpBlock.java", "OilPumpBlockEntity.java", "OilPumpMenu.java",
            "OilfieldDepletion.java"]
PROBE_ARCHIVE = os.path.join(ROOT, r"build\zftools\check\Zf109Check.java")
NEW_CLIENT = [r"client\OilPumpScreen.java"]
NEW_KEYS = ["block.potato_s_t.oil_pump",
            "tooltip.potato_s_t.oil_pump",
            "gui.potato_s_t.oil_pump.chains",
            "gui.potato_s_t.oil_pump.rate"]
STATUS_SUFFIX = ["running", "disabled", "no_power", "output_full", "not_oilfield", "no_chain"]
LANGS = ["zh_cn.json", "en_us.json", "ja_jp.json", "ru_ru.json"]
EXPECT_KEYS = 408

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
    u"""够用的 PNG 读入（本工程自己生成的 8 位 RGB/RGBA 非隔行）"""
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
    global n_pass
    be_path = os.path.join(JAVA, "OilPumpBlockEntity.java")

    # ============ ① 文件账目 ============
    print(u"== ① 文件账目 ==")
    for n in NEW_JAVA:
        check(u"Java 在盘上：%s" % n, os.path.exists(os.path.join(JAVA, n)))
    for n in NEW_CLIENT:
        check(u"界面在盘上：%s" % n, os.path.exists(os.path.join(JAVA, n)))
    for rel in (r"blockstates\oil_pump.json", r"models\block\oil_pump.json",
                r"models\item\oil_pump.json", r"textures\block\oil_pump.png"):
        check(u"资源在盘上：%s" % rel, os.path.exists(os.path.join(ASSETS, rel)))
    check(u"配方在盘上：recipe/oil_pump.json",
          os.path.exists(os.path.join(DATA, r"recipe\oil_pump.json")))
    check(u"改前件 zf109_pre 在", os.path.isdir(BK))
    n_bk = 0
    if os.path.isdir(BK):
        for _d, _s, _fs in os.walk(BK):
            n_bk += len(_fs)
    check(u"改前件抄了 ≥100 份（含子目录）", n_bk >= 100, u"实际 %d" % n_bk)
    check(u"补账说明在（FluidTankPart）", os.path.exists(os.path.join(BK, u"_补说明.txt")))
    check(u"探针钩子已经摘掉（PotatoST 里不许留 Zf109Check）",
          "Zf109Check" not in read(os.path.join(JAVA, "PotatoST.java")))
    check(u"探针源文件已从 src 删掉", not os.path.exists(os.path.join(JAVA, "Zf109Check.java")))
    check(u"探针存档在 build/zftools/check/（先抄后删）", os.path.exists(PROBE_ARCHIVE))
    check(u"探针存档 sha1 = 567357fd…",
          os.path.exists(PROBE_ARCHIVE)
          and hashlib.sha1(open(PROBE_ARCHIVE, "rb").read()).hexdigest()
          == "567357fd1f62773f4c94db79c94139f114ddfc01")

    # ============ ② 配方：逐格核对用户原话 ============
    print(u"\n== ② 配方 ==")
    rec = json.loads(read(os.path.join(DATA, r"recipe\oil_pump.json")))
    eq(u"类型 = crafting_shaped", "minecraft:crafting_shaped", rec.get("type"))
    eq(u"九宫格三行", ["ATA", "BHB", "PPP"], rec.get("pattern"))
    keys = rec.get("key", {})
    eq(u"五个原料符号", ["A", "B", "H", "P", "T"], sorted(keys))
    want_items = {"A": "potato_s_t:hard_titanium_alloy",      # 硬质钛合金
                  "T": "potato_s_t:heat_resistant_metal_block",   # 耐热金属块
                  "B": "potato_s_t:oil_bucket",              # 油桶
                  "H": "potato_s_t:high_pressure_tank",      # 高压气罐
                  "P": "potato_s_t:fluid_pump"}              # 流体泵
    for sym, item in sorted(want_items.items()):
        eq(u"符号 %s = %s" % (sym, item), item, keys.get(sym, {}).get("item"))
    eq(u"产物 = oil_pump ×1", {"id": "potato_s_t:oil_pump", "count": 1}, rec.get("result"))
    # 用户原话那张图逐格翻译：第一行 ATA、第二行 BHB、第三行 PPP
    eq(u"第一行 = 硬质钛合金 / 耐热金属块 / 硬质钛合金",
       ["A", "T", "A"], list(rec["pattern"][0]))
    eq(u"第二行 = 油桶 / 高压气罐 / 油桶", ["B", "H", "B"], list(rec["pattern"][1]))
    eq(u"第三行 = 流体泵 ×3", ["P", "P", "P"], list(rec["pattern"][2]))

    # ============ ③ 常数与公式（真算） ============
    print(u"\n== ③ 常数与公式 ==")
    be = read(be_path)
    for name, want in (("TANK_CAPACITY", 25000), ("MB_PER_SECOND_PER_CHAIN", 10),
                       ("DEBT_MIN_BUCKETS", 25), ("DEBT_MAX_BUCKETS", 80),
                       ("CONVERT_CHUNKS", 10), ("MAX_ENERGY", 32768),
                       ("MAX_CHAIN_SCAN", 64), ("SCAN_INTERVAL", 20), ("SLOT_COUNT", 0)):
        m = re.search(name + r"\s*=\s*([0-9* ]+);", be)
        got = None
        if m:
            try:
                got = eval(m.group(1).strip(), {"__builtins__": {}}, {})
            except Exception as e:
                got = "EVAL %s" % e
        eq(u"常量 %s" % name, want, got)
    m = re.search(r"public static int fePerTick\(int chains\)\s*\{\s*return\s+([^;]+);", be)
    check(u"找得到 fePerTick 的返回表达式", m is not None)
    if m:
        expr = m.group(1).replace("chains", "n")
        for n, want in ((0, 0), (1, 88), (2, 192), (3, 312), (10, 1600), (64, 37888)):
            try:
                got = eval(expr, {"__builtins__": {}}, {"n": n})
            except Exception as e:
                got = "EVAL %s" % e
            eq(u"耗能公式 n=%d（8n²+80n）" % n, want, got)
    m2 = re.search(r"public static int mbPerSecond\(int chains\)\s*\{\s*return\s+([^;]+);", be)
    check(u"找得到 mbPerSecond 的返回表达式", m2 is not None)
    if m2:
        expr = m2.group(1).replace("chains", "n").replace("MB_PER_SECOND_PER_CHAIN", "10")
        for n, want in ((0, 0), (1, 10), (10, 100), (64, 640)):
            try:
                got = eval(expr, {"__builtins__": {}}, {"n": n})
            except Exception as e:
                got = "EVAL %s" % e
            eq(u"产量公式 n=%d（10n mB/s）" % n, want, got)

    # ============ ④ 方块实体语义 ============
    print(u"\n== ④ 方块实体语义 ==")
    check(u"只在海洋油田开工（读 getBiome + 比 OCEAN_OILFIELD）",
          "getBiome(this.worldPosition).is(SaltyRiverBiomeSource.OCEAN_OILFIELD)" in be)
    check(u"不在油田 → 状态 15", "this.status = STATUS_NOT_OILFIELD" in be)
    check(u"没有链条 → 状态 16", "this.status = STATUS_NO_CHAIN" in be)
    check(u"下探只看水源（fluid.isSource()）", "fluid.isSource()" in be)
    check(u"下探认水（Fluids.WATER）", "isSame(Fluids.WATER)" in be)
    check(u"含水锁链 = 原版锁链 + WATERLOGGED", "state.is(Blocks.CHAIN)" in be
          and "ChainBlock.WATERLOGGED" in be)
    check(u"不是水就当场断（break）", re.search(r"fluid\.getType\(\)\.isSame\(Fluids\.WATER\)\)\s*\{\s*break;", be) is not None)
    check(u"下探有上限（循环用 MAX_CHAIN_SCAN）", "i < MAX_CHAIN_SCAN" in be)
    check(u"抽干了就调转换器（10×10 区块）",
          "OilfieldDepletion.convertAround(server, this.worldPosition, CONVERT_CHUNKS)" in be)
    check(u"欠账门槛在 25~80 桶之间随机",
          "DEBT_MIN_BUCKETS" in be and "DEBT_MAX_BUCKETS" in be and "nextInt" in be)
    check(u"欠账门槛存盘（convertAtMb）", 'tag.putInt("convertAtMb"' in be
          and 'tag.getInt("convertAtMb")' in be)
    check(u"累计采出存盘（pumpedMb，long）", 'tag.putLong("pumpedMb"' in be
          and 'tag.getLong("pumpedMb")' in be)
    check(u"罐走子标签存盘（§4.49）", 'tag.put("Tank", child)' in be)
    check(u"罐满就不扣电（OUTPUT_FULL 在付电之前）",
          be.index("STATUS_OUTPUT_FULL") < be.index("this.energy -= cost"))
    check(u"流体口只出不进（fill 恒 0）", re.search(r"public int fill\(FluidStack resource, FluidAction action\)\s*\{\s*return 0;", be) is not None)
    check(u"红石信号 = 停机", "hasNeighborSignal" in be and "STATUS_DISABLED" in be)

    # ============ ⑤ 群系转换器 ============
    print(u"\n== ⑤ 群系转换器 ==")
    dep = read(os.path.join(JAVA, "OilfieldDepletion.java"))
    check(u"用原版 fillBiomesFromNoise（1.21.1 唯一的口子）", "fillBiomesFromNoise" in dep)
    check(u"改完 setUnsaved(true)（否则不落盘）", "chunk.setUnsaved(true);" in dep)
    check(u"用 resendBiomesForChunks 通知客户端（不是整块重发）",
          "getChunkSource().chunkMap.resendBiomesForChunks(loaded)" in dep
          and "ClientboundLevelChunkWithLightPacket" not in dep)
    check(u"resolver 只改海洋油田、别的原样返回",
          "current.is(SaltyRiverBiomeSource.OCEAN_OILFIELD)" in dep and "return current;" in dep)
    check(u"用的是 ChunkStatus.FULL + 不强制加载（false）",
          "ChunkStatus.FULL, false" in dep)
    check(u"没加载的区块跳过（不为了它去加载 100 个区块）", "skipped" in dep)
    check(u"票选只认 #minecraft:is_ocean", 'withDefaultNamespace("is_ocean")' in dep)
    check(u"票数相同按 id 字典序（可复现）", "compareTo(best) < 0" in dep)
    check(u"一格海都没有时兜底 minecraft:ocean", "Biomes.OCEAN" in dep)
    check(u"注释里写明了「整根柱子」那个坑", u"整根柱子" in dep)
    check(u"注释里写明了 resendBiomesForChunks 只发调色板",
          u"只发群系调色板" in dep)

    # ============ ⑥ 注册与能力 ============
    print(u"\n== ⑥ 注册与能力 ==")
    blocks = read(os.path.join(JAVA, "ModBlocks.java"))
    menus = read(os.path.join(JAVA, "ModMenus.java"))
    pot = read(os.path.join(JAVA, "PotatoST.java"))
    client = read(os.path.join(JAVA, "PotatoSTClient.java"))
    check(u"ModBlocks：方块注册名 oil_pump", 'BLOCKS.register("oil_pump"' in blocks)
    check(u"ModBlocks：方块实体注册名 oil_pump", 'BLOCK_ENTITIES.register("oil_pump"' in blocks)
    check(u"ModBlocks：物品走 Shift 说明（tooltip.potato_s_t.oil_pump）",
          "tooltip.potato_s_t.oil_pump" in blocks)
    check(u"ModMenus：菜单注册名 oil_pump", 'MENU_TYPES.register("oil_pump"' in menus)
    check(u"PotatoST：给采油机挂了收 FE 的能力",
          "ModBlocks.OIL_PUMP_BE.get()" in pot and "Capabilities.EnergyStorage.BLOCK" in pot)
    check(u"PotatoST：给采油机挂了流体能力",
          "pump.getFluidHandler()" in pot)
    check(u"PotatoST：**没有**给采油机挂物品能力",
          "OIL_PUMP_BE.get(),\n                (chamber, side) -> chamber.getInventory()" not in pot)
    check(u"PotatoSTClient：登记了采油机界面",
          "ModMenus.OIL_PUMP_MENU.get()" in client and "OilPumpScreen::new" in client)

    # ============ ⑦ 界面 ============
    print(u"\n== ⑦ 界面 ==")
    scr = read(os.path.join(JAVA, r"client\OilPumpScreen.java"))
    mnu = read(os.path.join(JAVA, "OilPumpMenu.java"))
    check(u"用横躺的罐子（FluidTankPart.horizontal）", "FluidTankPart.horizontal(" in scr)
    check(u"工作指示灯用自己的文案前缀",
          'STATUS_KEY_PREFIX = "gui.potato_s_t.oil_pump.status."' in scr)
    check(u"状态灯把前缀传下去了（§6.10 ⑪ 那个坑）", "STATUS_KEY_PREFIX)" in scr)
    check(u"界面里没有能量条（用户原话「能量条不需要」）",
          "EnergyBarPart" not in scr and "COLOR_BAR" not in scr)
    check(u"界面里没有进度条", "ProgressBarPart" not in scr and "ProgressArrowPart" not in scr)
    check(u"两行数字用的是自己的键",
          "gui.potato_s_t.oil_pump.chains" in scr and "gui.potato_s_t.oil_pump.rate" in scr)
    check(u"菜单：机器槽数 = SLOT_COUNT（= 0）",
          "OilPumpBlockEntity.SLOT_COUNT" in mnu)
    check(u"菜单 stillValid 认自己的方块", "ModBlocks.OIL_PUMP.get()" in mnu)
    check(u"菜单坐标与界面共用（罐子常量在菜单里）",
          "TANK_X" in mnu and "OilPumpMenu.TANK_X" in scr)
    check(u"横躺开关是**加法**（竖直那条路没被改坏）",
          "gg.blit(ax, ay + this.h - fill, 0, this.w, fill, sprite, r, g, b, a);"
          in read(os.path.join(JAVA, r"client\gui\parts\FluidTankPart.java")))

    # ============ ⑧ 状态码 15/16 ============
    print(u"\n== ⑧ 状态码 ==")
    lamp = read(os.path.join(JAVA, r"client\gui\parts\StatusLampPart.java"))
    check(u"灯：15 号走黄灯", "OilPumpBlockEntity.STATUS_NOT_OILFIELD" in lamp)
    check(u"灯：16 号走黄灯", "OilPumpBlockEntity.STATUS_NO_CHAIN" in lamp)
    check(u"灯：15 号的后缀 not_oilfield", '"not_oilfield"' in lamp)
    check(u"灯：16 号的后缀 no_chain", '"no_chain"' in lamp)
    # 共享命名空间：15 / 16 不许被别的机器占着
    others = []
    for fn in sorted(os.listdir(JAVA)):
        if not fn.endswith("BlockEntity.java") or fn == "OilPumpBlockEntity.java":
            continue
        for mm in re.finditer(r"STATUS_(\w+)\s*=\s*(\d+)\s*;", read(os.path.join(JAVA, fn))):
            if int(mm.group(2)) in (15, 16):
                others.append(u"%s:%s=%s" % (fn, mm.group(1), mm.group(2)))
    eq(u"15/16 号没被别的机器占用（共享命名空间）", [], others)
    for code in (15, 16):
        check(u"采油机自己声明了 %d 号" % code,
              ("STATUS_NOT_OILFIELD = %d" % code) in be or ("STATUS_NO_CHAIN = %d" % code) in be)

    # ============ ⑨ 四语言 ============
    print(u"\n== ⑨ 四语言 ==")
    order_ref, data_ref = None, None
    all_langs = {}
    for name in LANGS:
        raw = io.open(os.path.join(LANG, name), encoding="utf-8", newline="").read()
        check(u"%s 没有 CR" % name, "\r" not in raw)
        j = json.loads(raw)
        all_langs[name] = j
        eq(u"%s 键数" % name, EXPECT_KEYS, len(j))
        if order_ref is None:
            order_ref, data_ref = list(j), j
        else:
            eq(u"%s 键序与 zh_cn 逐位相同" % name, order_ref, list(j))
            eq(u"%s 每个键的值都非空" % name, [], [k for k, v in j.items() if not str(v).strip()])
        for k in NEW_KEYS + ["gui.potato_s_t.oil_pump.status." + s for s in STATUS_SUFFIX]:
            check(u"%s 有键 %s" % (name, k), k in j)
        for k, v in j.items():
            if k.startswith(("tooltip.potato_s_t.oil_pump", "gui.potato_s_t.oil_pump")):
                check(u"%s 的 %s 里没有 ASCII 双引号" % (name, k), u"\"" not in v)
    if data_ref is not None:
        check(u"状态灯那 6 个后缀在四语言里都能拼出键",
              all(("gui.potato_s_t.oil_pump.status." + s) in data_ref for s in STATUS_SUFFIX))
    # 占位符个数：少了/多了都是 bug（界面那两行是 %s 参数化的）
    for name, j in sorted(all_langs.items()):
        eq(u"%s：chains 那行有 1 个 %%s" % name, 1,
           j.get("gui.potato_s_t.oil_pump.chains", u"").count(u"%s"))
        eq(u"%s：rate 那行有 2 个 %%s" % name, 2,
           j.get("gui.potato_s_t.oil_pump.rate", u"").count(u"%s"))
        for k in ["block.potato_s_t.oil_pump", "tooltip.potato_s_t.oil_pump"] \
                + ["gui.potato_s_t.oil_pump.status." + s for s in STATUS_SUFFIX]:
            eq(u"%s：%s 不该有 %%s" % (name, k), 0, j.get(k, u"").count(u"%s"))

    # ============ ⑩ 资源 ============
    print(u"\n== ⑩ 资源 ==")
    bs = json.loads(read(os.path.join(ASSETS, r"blockstates\oil_pump.json")))
    eq(u"blockstate 只有一种变体（没有朝向）", [""], list(bs.get("variants", {})))
    eq(u"blockstate 指向 potato_s_t:block/oil_pump", "potato_s_t:block/oil_pump",
       bs["variants"][""]["model"])
    bm = json.loads(read(os.path.join(ASSETS, r"models\block\oil_pump.json")))
    eq(u"方块模型父级 = cube_all", "minecraft:block/cube_all", bm.get("parent"))
    eq(u"方块模型贴图", "potato_s_t:block/oil_pump", bm.get("textures", {}).get("all"))
    im = json.loads(read(os.path.join(ASSETS, r"models\item\oil_pump.json")))
    eq(u"物品模型父级 = 方块模型", "potato_s_t:block/oil_pump", im.get("parent"))
    w, h, ch, rows = read_png(os.path.join(TEXB, "oil_pump.png"))
    eq(u"贴图 16×16", (16, 16), (w, h))
    eq(u"贴图是 RGBA", 4, ch)
    colors = set()
    opaque = True
    for row in rows:
        for px in row:
            colors.add(px[:3])
            if px[3] != 255:
                opaque = False
    check(u"没有半透明像素", opaque)
    check(u"颜色数 ≤ 8（平涂；旧的糊图是 228 色）", len(colors) <= 8, u"实际 %d" % len(colors))
    check(u"用色全部落在家族调色板里", colors <= FAMILY, u"多出来的 %r" % (colors - FAMILY))
    check(u"贴图体积 < 1000 字节", os.path.getsize(os.path.join(TEXB, "oil_pump.png")) < 1000)
    tag = read(os.path.join(RES, r"data\minecraft\tags\block\mineable\pickaxe.json"))
    check(u"挖掘标签里有 potato_s_t:oil_pump（§4.52/ZF96 那个漏挂）",
          "potato_s_t:oil_pump" in tag)

    # ============ ⑪ 探针报告 ============
    print(u"\n== ⑪ 探针报告 ==")
    check(u"探针 UTF-8 报告在盘上", os.path.exists(REPORT))
    if os.path.exists(REPORT):
        rep = read(REPORT)
        check(u"报告是全绿（verdict: ALL OK）", "verdict: ALL OK" in rep)
        check(u"报告里没有 [FAIL]", "[FAIL]" not in rep)
        check(u"报告里记了转换结果（target=）", "target=" in rep)
        check(u"报告里记了票选那一节", u"ring chunks written" in rep)

    # ============ 文档 ============
    print(u"\n== 文档 ==")
    doc = read(DOC)
    plan = read(PLAN)
    ann = read(ANN)
    check(u"档案 §5 有 ZF109 行", u"| ZF109 |" in doc)
    check(u"档案 §9 有 ZF109 小节", u"ZF109（0.11）" in doc)
    check(u"档案里写明了 1.21.1 没有 getBiomes/fillBiome/setBiome",
          u"fillBiome" in doc and u"javap" in doc)
    check(u"档案里写明了「整根柱子」那个坑", u"整根柱子" in doc)
    check(u"贴图清单里有 oil_pump.png", u"oil_pump.png" in plan)
    check(u"EN 公告的键数已重定目标到 408", u"(408 keys each)" in ann)

    print(u"")
    print(u"通过 = %d   失败 = %d" % (n_pass, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
