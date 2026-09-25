# -*- coding: utf-8 -*-
u"""_zf79_verify.py —— ZF79 交付校验（常驻，跑在门里）

本轮两件（用户原话）：
  ① 「12个沥青 可以在液压机压成一个柏油块（纯建筑方块 先用煤炭块材质）」
  ② 「我把电力高炉材质放进方块材质文件夹里了」

分区：
  A 液压机配方模型（数量 / 无标签 / 老配方回归）   B 液压机行为与状态
  C 柏油块本体（注册 / 性质 / 资源 / 标签）        D 电力高炉新材质
  E 语言与公告                                     F 文档与成品
"""
import io
import json
import os
import re
import sys
import zipfile
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import PngRecolor as P

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(ROOT, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data")
LANG = os.path.join(ASSETS, "lang")
TOOLS = os.path.join(ROOT, "build", "zftools")

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


def png(path):
    import struct
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return (w, h, head[24], head[25])


# ================= A 配方模型 =================

def section_a():
    print(u"\n== A 液压机配方模型 ==")
    press = src("PressRecipes.java")
    c = int_consts(press)
    eq(u"一个柏油块要 12 个沥青", 12, c.get("BITUMEN_PER_BLOCK"))
    eq(u"耗时/耗电没动（60 tick / 400 FE·t）", (60, 400),
       (c.get("DURATION_TICKS"), c.get("ENERGY_PER_TICK")))
    check(u"Recipe 现在带 inputCount", "int inputCount)" in press
          and "public record Recipe(TagKey<Item> inputTag, Item fallback, Item result, int inputCount)" in press)
    check(u"1 个进 1 个出的便利构造器还在（老 7 条不用改）",
          "public Recipe(TagKey<Item> inputTag, Item fallback, Item result) {" in press)
    check(u"inputTag 允许为 null（沥青按长期规则不挂 c: 标签）",
          "return this.inputTag != null && stack.is(this.inputTag);" in press)
    check(u"数量不够 = 不能开工（hasEnough 与 matches 分开）",
          "public boolean hasEnough(ItemStack stack) {" in press
          and "stack.getCount() >= this.inputCount" in press)
    eq(u"配方共 8 条（7 锭→板 + 1 沥青→柏油块）", 8,
       len(re.findall(r"out\.add\(new Recipe\(", press)))
    check(u"沥青那条只有兜底物品、数量 12",
          "out.add(new Recipe(null, ModItems.BITUMEN.get(), ModBlocks.ASPHALT_BLOCK_ITEM.get()," in press
          and "BITUMEN_PER_BLOCK));" in press)
    for tag in ("COPPER_INGOT", "IRON_INGOT", "NICKEL_INGOT", "COBALT_INGOT", "SILVER_INGOT",
                "ALUMINUM_INGOT", "STEEL_INGOT"):
        check(u"老配方 %s 仍走 c: 标签" % tag,
              ("new Recipe(%s," % tag) in press)
    jm = src("MachineRecipes.java")
    check(u"JEI 侧支持无标签输入（退回兜底物品）",
          "if (recipe.inputTag() != null) {" in jm and "recipe.fallback(), recipe.inputCount())" in jm)
    check(u"JEI 输入图标带数量（12 会显示在图标上）",
          "new ItemStack(holder.value(), recipe.inputCount())" in jm)


# ================= B 液压机行为 =================

def section_b():
    print(u"\n== B 液压机行为与状态 ==")
    be = src("HydraulicPressBlockEntity.java")
    c = int_consts(be)
    eq(u"新状态码 STATUS_MATERIAL = 6", 6, c.get("STATUS_MATERIAL"))
    check(u"数量不够时走新状态、进度保留（不是 resetProgress）",
          "if (!recipe.hasEnough(input)) {" in be and "this.status = STATUS_MATERIAL;" in be)
    i_check = be.find("recipe.hasEnough(input)")
    i_done = be.find("if (this.progress >= this.progressMax) {")
    # ⚠ 用 find 不用 index：index 在"这段被删掉"时会**抛异常**，校验脚本当场崩、
    #   反证脚本连汇总行都读不到（K9 那一刀就是这么暴露的）
    check(u"数量检查排在「满进度结算」之前（否则 11 个也能出货）",
          i_check >= 0 and i_done > i_check)
    check(u"结算按配方数量扣料（不再写死 1）",
          "this.items.extractItem(INPUT_SLOT, recipe.inputCount(), false);" in be)
    lamp = src("StatusLampPart.java", sub=os.path.join("client", "gui", "parts"))
    check(u"状态灯认得新码（颜色 + 文案后缀 + import）",
          "import com.potatost.mod.HydraulicPressBlockEntity;" in lamp
          and "case HydraulicPressBlockEntity.STATUS_MATERIAL -> YELLOW;" in lamp
          and 'case HydraulicPressBlockEntity.STATUS_MATERIAL -> "material";' in lamp)


# ================= C 柏油块 =================

def section_c():
    print(u"\n== C 柏油块本体 ==")
    blocks = src("ModBlocks.java")
    items = src("ModItems.java")
    check(u"方块 id 与注册齐全",
          'BLOCKS.register("asphalt_block"' in blocks
          and 'ModItems.ITEMS.register("asphalt_block"' in blocks)
    check(u"是纯装饰方块（Properties 照原版煤炭块：5.0/6.0 + 石头音 + 要正确工具）",
          "public static final DeferredBlock<Block> ASPHALT_BLOCK = BLOCKS.register(\"asphalt_block\"," in blocks
          and ".strength(5.0F, 6.0F)" in blocks
          and ".sound(SoundType.STONE)" in blocks
          and ".requiresCorrectToolForDrops()));" in blocks)
    check(u"没有方块实体（纯建筑方块）",
          "ASPHALT_BLOCK_BE" not in blocks)
    check(u"进了创造页", "ModBlocks.ASPHALT_BLOCK_ITEM.get()" in items)

    bs = read(os.path.join(ASSETS, "blockstates", "asphalt_block.json"))
    bm = read(os.path.join(ASSETS, "models", "block", "asphalt_block.json"))
    im = read(os.path.join(ASSETS, "models", "item", "asphalt_block.json"))
    check(u"blockstate → 自己的模型", bs is not None and "potato_s_t:block/asphalt_block" in bs)
    check(u"方块模型 = cube_all + 自己的贴图",
          bm is not None and "minecraft:block/cube_all" in bm
          and "potato_s_t:block/asphalt_block" in bm)
    check(u"物品模型 = 方块模型（与其它装饰块一致）",
          im is not None and "potato_s_t:block/asphalt_block" in im)

    tex = os.path.join(ASSETS, "textures", "block", "asphalt_block.png")
    check(u"贴图 16×16 / 8 位 / RGBA（占位：原版煤炭块）", png(tex) == (16, 16, 8, 6))
    prov_path = os.path.join(TOOLS, "_zf79_asphalt_provenance.json")
    if os.path.exists(tex) and os.path.exists(prov_path):
        prov = json.loads(read(prov_path))
        _w, _h, rgba = P.read_png(tex)
        check(u"贴图像素与凭据一致（来源 = client.jar 的煤炭块）",
              hashlib.sha256(bytes(rgba)).hexdigest() == prov.get("rgba_sha256")
              and "coal_block" in prov.get("source", ""))
    else:
        check(u"沥青块贴图凭据存在", False)

    mine = json.loads(read(os.path.join(DATA, "minecraft", "tags", "block", "mineable", "pickaxe.json")))
    check(u"进了 mineable/pickaxe（§4.25：不挂就挖不出来）",
          "potato_s_t:asphalt_block" in mine["values"])
    needs = json.loads(read(os.path.join(DATA, "minecraft", "tags", "block", "needs_stone_tool.json")))
    check(u"**没有**进 needs_stone_tool（与原版煤炭块一致：木镐也能挖）",
          "potato_s_t:asphalt_block" not in needs["values"])
    recipe_dir = os.path.join(DATA, "potato_s_t", "recipe")
    hit = [n for n in os.listdir(recipe_dir) if "asphalt" in n]
    check(u"没有合成台配方（它只能靠液压机压出来）", not hit)


# ================= D 电力高炉新材质 =================

def section_d():
    print(u"\n== D 电力高炉新材质 ==")
    tex = os.path.join(ASSETS, "textures", "block", "electric_blast_furnace.png")
    check(u"electric_blast_furnace.png = 256×256 / 8 位 / RGBA（用户手绘）",
          png(tex) == (256, 256, 8, 6))
    chinese = [n for n in os.listdir(os.path.join(ASSETS, "textures", "block"))
               if any(ord(ch) > 127 for ch in n)]
    check(u"方块贴图目录里没有中文名文件了（§4.24）", not chinese)
    # ⚠ 0.11 ZF90：ZF79 当时把用户原图以 `电力高炉.原名件` **留在资源目录里** ⇒ 它一直被打进 jar
    #   （非 ASCII 路径 + 18 KB 死文件）。ZF90 按 §4.24 的原意挪到 `build/用户素材/` 并记进凭据，
    #   资源目录里不再留任何非 ASCII 文件名 ⇒ 本条断言改成新真相。
    kept = os.path.join(ROOT, "build", u"用户素材", "electric_blast_furnace_original.png")
    check(u"用户原名件已留档在 build/用户素材/（内容与在用贴图逐字节一致）",
          os.path.exists(kept) and open(kept, "rb").read() == open(tex, "rb").read())
    check(u"资源目录里不再有 `.原名件`（ZF90 起打不进 jar）",
          not os.path.exists(os.path.join(ASSETS, "textures", "block", u"电力高炉.原名件")))
    mtl = read(os.path.join(ASSETS, "models", "block", "electric_blast_furnace.mtl"))
    check(u"MTL 仍指向本贴图（模型不用改）",
          mtl is not None and "map_Kd potato_s_t:block/electric_blast_furnace" in mtl)


# ================= E 语言与公告 =================

def section_e():
    print(u"\n== E 语言与公告 ==")
    keys = {}
    for name in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        keys[name] = json.loads(read(os.path.join(LANG, name + ".json")))
    counts = {k: len(v) for k, v in keys.items()}
    check(u"四份语言键数一致且 = 417（ZF107 +48；ZF109 +10）",
          len(set(counts.values())) == 1 and list(counts.values())[0] == 417)
    for name, d in keys.items():
        check(u"%s：柏油块名字 + 液压机新状态文案都在" % name,
              u"block.potato_s_t.asphalt_block" in d
              and u"gui.potato_s_t.hydraulic_press.status.material" in d)
        tip = d.get(u"tooltip.potato_s_t.hydraulic_press", u"")
        low = tip.lower()
        check(u"%s：液压机 tooltip 补了「沥青→柏油块」那行（且原有数值还在）" % name,
              u"12" in tip and (u"柏油块" in tip or u"asphalt" in low
                                or u"アスファルト" in tip or u"асфальт" in low))
    ann = read(os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md"))
    check(u"公告的液压机一行写了 12 Bitumen → 1 Asphalt Block",
          ann is not None and u"**12 Bitumen → 1 Asphalt Block**" in ann)


# ================= F 文档与成品 =================

def section_f():
    print(u"\n== F 文档与成品 ==")
    doc = read(os.path.join(ROOT, "docs", u"开发档案.md"))
    check(u"开发档案 §5 有 ZF79 行", doc is not None and u"| ZF79 |" in doc)
    check(u"§9 有 ZF79 的用户侧验证", doc is not None and u"ZF79" in doc.split(u"## 9")[-1])
    texlist = read(os.path.join(ROOT, "docs", u"贴图清单.md"))
    check(u"贴图清单提到柏油块占位贴图", texlist is not None and u"asphalt_block" in texlist)
    props = read(os.path.join(ROOT, "gradle.properties"))
    check(u"mod_version 仍是 0.11（本轮没有 0.12 任务）",
          props is not None and u"mod_version=0.11" in props)

    check(u"打包前探针已从 src 删除",
          not os.path.exists(os.path.join(SRC, "AsphaltCheck.java")))
    pot = src("PotatoST.java")
    check(u"打包前 PotatoST 里的探针挂钩已删", pot is not None and "AsphaltCheck" not in pot)

    log = read(os.path.join(TOOLS, "_zf79_server.log.utf8.txt")) or read(
        os.path.join(TOOLS, "_zf79_server.log"))
    if log:
        m = re.search(r"\[F79\] ==== passed=(\d+) failed=(\d+) ====", log)
        check(u"探针日志里有汇总行", m is not None)
        if m:
            eq(u"探针实测失败 0 项", "0", m.group(2))
            check(u"探针断言数 ≥ 30（实际 %s）" % m.group(1), int(m.group(1)) >= 30)
    else:
        check(u"找不到探针日志（_zf79_server.log）", False)

    jar = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
    sha_file = jar + ".sha1"
    check(u"成品 release\\PotatoST-0.11.jar 存在", os.path.exists(jar))
    if os.path.exists(jar):
        sha = hashlib.sha1(open(jar, "rb").read()).hexdigest()
        recorded = read(sha_file)
        check(u".sha1 与 jar 实际哈希一致（%s…）" % sha[:8],
              recorded is not None and recorded.strip().lower() == sha)
        with zipfile.ZipFile(jar) as zf:
            names = zf.namelist()
            ebf = zf.read("assets/potato_s_t/textures/block/electric_blast_furnace.png")
        check(u"成品里的电力高炉贴图就是用户那张 256×256",
              ebf == open(os.path.join(ASSETS, "textures", "block",
                                       "electric_blast_furnace.png"), "rb").read())
        need = ["assets/potato_s_t/textures/block/asphalt_block.png",
                "assets/potato_s_t/models/block/asphalt_block.json",
                "assets/potato_s_t/blockstates/asphalt_block.json",
                "assets/potato_s_t/models/item/asphalt_block.json"]
        missing = [n for n in need if n not in names]
        check(u"成品里柏油块的资源都在（缺 %s）" % (missing or u"无"), not missing)
        bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
        check(u"成品里没有探针 class（%s）" % (bad or u"0 个"), not bad)



# ================= G 2026-09-24 的两处修复 =================

def section_g():
    print(u"\n== G 灌装机手放门禁 + JEI 箭头位置（用户 09-24 实测）==")
    menu = src("FillingMachineMenu.java")
    be = src("FillingMachineBlockEntity.java")
    # ① 灌装机：三道门禁同口径（这道门漏改过一次：用户"没办法放油桶"）
    check(u"Menu.mayPlace 认接口（不再写死高压气罐）",
          "return stack.getItem() instanceof FluidContainerItem;" in menu)
    check(u"Menu 里**不许再出现** HighPressureTankItem（写死回归断言）",
          "HighPressureTankItem" not in menu)
    check(u"Menu.getMachineSlotFor（Shift 快移）也认接口",
          "if (stack.getItem() instanceof FluidContainerItem) {" in menu)
    check(u"方块实体的 isItemValid 同样认接口",
          "return stack.getItem() instanceof FluidContainerItem;" in be)

    # ② JEI 箭头：按这条配方实际占用的输入列数算
    cat = src("MachineRecipeCategory.java", sub=os.path.join("client", "jei"))
    check(u"箭头位置改成按配方算（arrowXFor）",
          "private int arrowXFor(MachineRecipes.Entry recipe)" in cat
          and "this.arrow.draw(graphics, arrowXFor(recipe), this.arrowY);" in cat)
    check(u"旧的固定 arrowX 字段已删（不再两套算法并存）",
          "this.arrowX" not in cat and "private final int arrowX;" not in cat)
    # 几何自证：用类别里的常量把两种情形算出来
    c = int_consts(cat)
    pad, slot, in_cols, gap = c.get("PAD"), c.get("SLOT"), c.get("IN_COLS"), c.get("GAP")
    arrow_w = 22          # JEI 原版箭头精灵就是 22×16
    out_x = (pad or 0) + (in_cols or 0) * (slot or 0) + (gap or 0)
    old_x = (pad or 0) + (in_cols or 0) * (slot or 0) + ((gap or 0) - arrow_w) // 2
    one_col = (pad or 0) + 1 * (slot or 0)
    new_one = one_col + (out_x - one_col - arrow_w) // 2
    new_four = (pad or 0) + (in_cols or 0) * (slot or 0) + (out_x - ((pad or 0) + (in_cols or 0) * (slot or 0)) - arrow_w) // 2
    check(u"左边界用的是**实际占用的列数**（不是写死 IN_COLS）",
          "int left = PAD + usedCols * SLOT;" in cat
          and "int usedCols = Math.max(1, Math.min(recipe.itemIn().size(), IN_COLS));" in cat)
    check(u"1 个输入：箭头左移 ≥20px（旧 x=%s → 新 x=%s）" % (old_x, new_one),
          old_x - new_one >= 20)
    check(u"输入满 4 列：位置与旧算法完全一致（x=%s）⇒ 12 输入那种配方不会压槽位" % new_four,
          new_four == old_x)
    check(u"箭头始终落在输入区右边界与输出区之间（不越界）",
          new_one >= one_col and new_one + arrow_w <= out_x)


def main():
    print(u"=========== ZF79 校验：柏油块 + 电力高炉新材质 ===========")
    section_a()
    section_b()
    section_c()
    section_d()
    section_e()
    section_f()
    section_g()
    print(u"\n------------------------------")
    print(u"通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
