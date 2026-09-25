# -*- coding: utf-8 -*-
u"""_zf78_assets.py —— ZF78 分馏塔三件套的**非 Java 资源**一次写完。

写什么：
  ① `textures/item/bitumen.png` —— 沥青的占位贴图：用户原话「沥青贴图暂时用火药占位」
     ⇒ 直接从原版 `client.jar` 里把 `assets/minecraft/textures/item/gunpowder.png`
     抠出来放进我们自己的命名空间（和当年钛粉的做法一样：文件落在我们这儿，
     模型指自己，等美术素材来了覆盖这个文件即可，**不会留下悬空引用**）。
  ② 2 个方块的 blockstate + 方块模型（顶/侧，格式照抄 micro_crusher）+ 2 个物品模型。
  ③ `models/item/bitumen.json`（16x16 物品图，普通 generated）。
  ④ 4 张 `c:` 流体标签（柴油/石脑油/汽油/液化石油气）——  0.11 ZF74 立的规矩：
     **每一种流体都必须挂在某个 `c:` 标签里**（审计会查），`replace:false` 绝不覆盖别人的条目。
  ⑤ `data/minecraft/tags/block/mineable/pickaxe.json` 追加两个新方块（同其它机器）。
  ⑥ 四份语言文件各 +22 键（键集合必须**四份一致**，LangCheck 查的就是这个）。

规矩（沿用 _zf73_lang.py）：
  · 每个锚点**断言正好命中 1 次**，不中就不写（宁可不动，也不要把文件改花）；
  · 写完立刻用 json 解析一遍；
  · 幂等：键/方块已经在里面就跳过；
  · 四份语言键数必须相等，且等于 EXPECT_KEYS。
"""
import io
import json
import os
import shutil
import sys
import zipfile

# 控制台按 UTF-8 输出：本文件里全是中文与 ⇒ 之类的符号，GBK 控制台会直接把报错
# 打成 UnicodeEncodeError（ZF78 第一版就这么盖掉了一次真实失败）。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RES = os.path.join(ROOT, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "potato_s_t")
DATA = os.path.join(RES, "data")
LANG = os.path.join(ASSETS, "lang")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

EXPECT_KEYS = 219 + 22

BLOCKS = ["distillation_controller", "distillation_operator"]

# ================= ① 沥青占位贴图 =================

def install_bitumen_texture():
    dst = os.path.join(ASSETS, "textures", "item", "bitumen.png")
    if os.path.exists(dst):
        print(u"  [SKIP] textures/item/bitumen.png 已存在（幂等）")
        return True
    if not os.path.exists(VANILLA_JAR):
        print(u"  [FAIL] 找不到原版 client.jar：%s" % VANILLA_JAR)
        return False
    with zipfile.ZipFile(VANILLA_JAR) as zf:
        name = "assets/minecraft/textures/item/gunpowder.png"
        try:
            raw = zf.read(name)
        except KeyError:
            print(u"  [FAIL] client.jar 里没有 %s" % name)
            return False
    with open(dst, "wb") as fh:
        fh.write(raw)
    print(u"  [OK]   textures/item/bitumen.png <- client.jar:%s（%d B）" % (name, len(raw)))
    return True


# ================= ②③ 模型 / blockstate =================

CUBE = u"""{
  "parent": "minecraft:block/block",
  "textures": {
    "top": "potato_s_t:block/%(name)s_top",
    "side": "potato_s_t:block/%(name)s_side",
    "particle": "potato_s_t:block/%(name)s_side"
  },
  "elements": [
    {
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "faces": {
        "up": { "uv": [0, 0, 16, 16], "texture": "#top" },
        "down": { "uv": [0, 0, 16, 16], "texture": "#top" },
        "north": { "uv": [0, 0, 16, 16], "texture": "#side" },
        "south": { "uv": [0, 0, 16, 16], "texture": "#side" },
        "east": { "uv": [0, 0, 16, 16], "texture": "#side" },
        "west": { "uv": [0, 0, 16, 16], "texture": "#side" }
      }
    }
  ]
}
"""


def write_json(path, text, label):
    if os.path.exists(path):
        print(u"  [SKIP] %s 已存在（幂等）" % label)
        return True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
    print(u"  [OK]   %s" % label)
    return True


def install_models():
    ok = True
    for name in BLOCKS:
        ok &= write_json(os.path.join(ASSETS, "blockstates", name + ".json"),
                         u'{ "variants": { "": { "model": "potato_s_t:block/%s" } } }\n' % name,
                         "blockstates/%s.json" % name)
        ok &= write_json(os.path.join(ASSETS, "models", "block", name + ".json"),
                         CUBE % {"name": name},
                         "models/block/%s.json" % name)
        ok &= write_json(os.path.join(ASSETS, "models", "item", name + ".json"),
                         u'{ "parent": "potato_s_t:block/%s" }\n' % name,
                         "models/item/%s.json" % name)
    ok &= write_json(os.path.join(ASSETS, "models", "item", "bitumen.json"),
                     u'{\n  "parent": "minecraft:item/generated",\n'
                     u'  "textures": { "layer0": "potato_s_t:item/bitumen" }\n}\n',
                     "models/item/bitumen.json")
    return ok


# ================= ④ c: 流体标签 =================

FLUID_TAGS = {
    "diesel": ["potato_s_t:diesel", "potato_s_t:flowing_diesel"],
    "naphtha": ["potato_s_t:naphtha", "potato_s_t:flowing_naphtha"],
    "gasoline": ["potato_s_t:gasoline", "potato_s_t:flowing_gasoline"],
    "lpg": ["potato_s_t:lpg", "potato_s_t:flowing_lpg"],
}


def install_fluid_tags():
    ok = True
    for name, values in FLUID_TAGS.items():
        body = u"{\n  \"replace\": false,\n  \"values\": [\n"
        body += u",\n".join(u'    "%s"' % v for v in values)
        body += u"\n  ]\n}\n"
        ok &= write_json(os.path.join(DATA, "c", "tags", "fluid", name + ".json"), body,
                         "data/c/tags/fluid/%s.json" % name)
    return ok


# ================= ⑤ 挖掘标签 =================

def patch_mineable():
    path = os.path.join(DATA, "minecraft", "tags", "block", "mineable", "pickaxe.json")
    text = io.open(path, "r", encoding="utf-8").read()
    data = json.loads(text)
    missing = [n for n in BLOCKS if ("potato_s_t:" + n) not in data["values"]]
    if not missing:
        print(u"  [SKIP] mineable/pickaxe.json 两个方块都在了（幂等）")
        return True
    anchor = u'"potato_s_t:alloy_smelter_port"'
    hits = text.count(anchor)
    if hits != 1:
        print(u"  [FAIL] mineable/pickaxe.json 锚点命中 %d 次（必须 1 次）" % hits)
        return False
    idx = text.index(anchor)
    block = u"".join(u'    "potato_s_t:%s",\n' % n for n in missing)
    # 插在**最后一项之前**（最后一项没有逗号，所以新加的每一项都带逗号）
    text = text[:idx] + block + text[idx:]
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
    try:
        after = json.loads(io.open(path, "r", encoding="utf-8").read())
    except Exception as exc:
        print(u"  [FAIL] 写完解析失败：%s" % exc)
        return False
    for n in BLOCKS:
        if ("potato_s_t:" + n) not in after["values"]:
            print(u"  [FAIL] 追加后仍然找不到 potato_s_t:%s" % n)
            return False
    if len(after["values"]) != len(data["values"]) + len(missing):
        print(u"  [FAIL] 条目数不对：%d -> %d" % (len(data["values"]), len(after["values"])))
        return False
    print(u"  [OK]   mineable/pickaxe.json +%d 个方块（共 %d 项）"
          % (len(missing), len(after["values"])))
    return True


# ================= ⑥ 语言 =================

ANCHOR = u'"item.potato_s_t.oil_bucket"'

TOWER_ZH = (
    u"结构 4×4×7（7 层）：\\n"
    u"· 第 1~2 层：四角放 一般金属块\\n"
    u"· 第 3 / 5 层：角=一般金属块、边=耐热金属块、正中 2×2=加热装置\\n"
    u"· 第 4 / 6 层：一圈耐热金属块（中间空）\\n"
    u"· 第 7 层：4×4 全部一般金属块\\n"
    u"· 图纸上画着空的格子必须是空气\\n"
    u"检测范围：周围 32×32×10 格；把数到的塔数发给相邻的分馏塔操作器"
)
OP_ZH = (
    u"每座分馏塔每 tick：8 mB 原油 + 8096 FE → 3 柴油 + 2 石脑油 + 2 汽油 + 1 液化石油气\\n"
    u"每 5 tick 出 1 块沥青（每座塔）；沥青满 64 且没清理 ⇒ 停止分馏\\n"
    u"容量（每座塔）：能量 8096 FE、原油 12 桶、每种产品 2.5 桶\\n"
    u"给红石信号才开始分馏 · 最多识别 4 座分馏塔"
)
TOWER_EN = (
    u"Structure 4x4x7 (7 layers):\\n"
    u"- Layers 1-2: Common Metal Block on the four corners\\n"
    u"- Layers 3 / 5: corners = Common Metal Block, edges = Heat-Resistant Metal Block, "
    u"centre 2x2 = Heater\\n"
    u"- Layers 4 / 6: a ring of Heat-Resistant Metal Block (hollow)\\n"
    u"- Layer 7: 4x4 of Common Metal Block\\n"
    u"- Every cell drawn as empty must be air\\n"
    u"Scans 32x32x10 around itself and reports the tower count to an adjacent Operator"
)
OP_EN = (
    u"Per tower, per tick: 8 mB crude oil + 8096 FE -> 3 diesel + 2 naphtha + 2 gasoline + 1 LPG\\n"
    u"Every 5 ticks: 1 bitumen per tower; a full stack of 64 and no room left stops it\\n"
    u"Capacity per tower: 8096 FE, 12 buckets of oil, 2.5 buckets per product\\n"
    u"Needs a redstone signal; recognises up to 4 towers"
)
TOWER_JA = (
    u"構造 4×4×7（7 層）：\\n"
    u"・第 1〜2 層：四隅に一般金属ブロック\\n"
    u"・第 3 / 5 層：角＝一般金属ブロック、辺＝耐熱金属ブロック、中央 2×2＝加熱装置\\n"
    u"・第 4 / 6 層：耐熱金属ブロックの輪（中は空洞）\\n"
    u"・第 7 層：4×4 すべて一般金属ブロック\\n"
    u"・空きマスは空気であること\\n"
    u"検出範囲：周囲 32×32×10 ブロック。塔の数を隣の分留塔操作器へ送ります"
)
OP_JA = (
    u"塔 1 基・毎 tick：原油 8 mB + 8096 FE → ディーゼル 3 + ナフサ 2 + ガソリン 2 + LPG 1\\n"
    u"5 tick ごとに瀝青 1 個（塔 1 基あたり）。64 個たまると停止\\n"
    u"容量（塔 1 基あたり）：エネルギー 8096 FE、原油 12 バケツ、各製品 2.5 バケツ\\n"
    u"レッドストーン信号で開始・最大 4 基まで認識"
)
TOWER_RU = (
    u"Структура 4×4×7 (7 слоёв):\\n"
    u"· Слои 1–2: по углам обычный металлический блок\\n"
    u"· Слои 3 / 5: углы — обычный блок, края — жаростойкий блок, центр 2×2 — нагреватель\\n"
    u"· Слои 4 / 6: кольцо из жаростойкого блока (внутри пусто)\\n"
    u"· Слой 7: 4×4 из обычного металлического блока\\n"
    u"· Все пустые клетки должны быть воздухом\\n"
    u"Радиус 32×32×10; передаёт число башен соседнему оператору"
)
OP_RU = (
    u"На башню за тик: 8 mB нефти + 8096 FE → 3 дизеля + 2 нафты + 2 бензина + 1 LPG\\n"
    u"Каждые 5 тиков 1 битум на башню; полный стак 64 останавливает процесс\\n"
    u"Ёмкость на башню: 8096 FE, 12 ведёр нефти, 2,5 ведра каждого продукта\\n"
    u"Нужен сигнал редстоуна; распознаётся до 4 башен"
)

KEYS = {
    u"zh_cn.json": [
        (u"block.potato_s_t.distillation_controller", u"分馏塔控制器"),
        (u"block.potato_s_t.distillation_operator", u"分馏塔操作器"),
        (u"item.potato_s_t.bitumen", u"沥青"),
        (u"fluid_type.potato_s_t.diesel", u"柴油"),
        (u"fluid.potato_s_t.diesel", u"柴油"),
        (u"fluid_type.potato_s_t.naphtha", u"石脑油"),
        (u"fluid.potato_s_t.naphtha", u"石脑油"),
        (u"fluid_type.potato_s_t.gasoline", u"汽油"),
        (u"fluid.potato_s_t.gasoline", u"汽油"),
        (u"fluid_type.potato_s_t.lpg", u"液化石油气"),
        (u"fluid.potato_s_t.lpg", u"液化石油气"),
        (u"gui.potato_s_t.distillation.towers", u"分馏塔：%s / %s 座"),
        (u"gui.potato_s_t.distillation.status.running", u"分馏中"),
        (u"gui.potato_s_t.distillation.status.no_controller", u"未连接分馏塔控制器"),
        (u"gui.potato_s_t.distillation.status.no_tower", u"未检测到分馏塔"),
        (u"gui.potato_s_t.distillation.status.no_redstone", u"无红石信号"),
        (u"gui.potato_s_t.distillation.status.bitumen_full", u"沥青已满（64），停止分馏"),
        (u"gui.potato_s_t.distillation.status.no_oil", u"石油不足"),
        (u"gui.potato_s_t.distillation.status.no_power", u"电力不足"),
        (u"gui.potato_s_t.distillation.status.product_full", u"产品储罐已满"),
        (u"tooltip.potato_s_t.distillation_controller", TOWER_ZH),
        (u"tooltip.potato_s_t.distillation_operator", OP_ZH),
    ],
    u"en_us.json": [
        (u"block.potato_s_t.distillation_controller", u"Distillation Tower Controller"),
        (u"block.potato_s_t.distillation_operator", u"Distillation Tower Operator"),
        (u"item.potato_s_t.bitumen", u"Bitumen"),
        (u"fluid_type.potato_s_t.diesel", u"Diesel"),
        (u"fluid.potato_s_t.diesel", u"Diesel"),
        (u"fluid_type.potato_s_t.naphtha", u"Naphtha"),
        (u"fluid.potato_s_t.naphtha", u"Naphtha"),
        (u"fluid_type.potato_s_t.gasoline", u"Gasoline"),
        (u"fluid.potato_s_t.gasoline", u"Gasoline"),
        (u"fluid_type.potato_s_t.lpg", u"LPG"),
        (u"fluid.potato_s_t.lpg", u"LPG"),
        (u"gui.potato_s_t.distillation.towers", u"Towers: %s / %s"),
        (u"gui.potato_s_t.distillation.status.running", u"Distilling"),
        (u"gui.potato_s_t.distillation.status.no_controller", u"No controller adjacent"),
        (u"gui.potato_s_t.distillation.status.no_tower", u"No distillation tower found"),
        (u"gui.potato_s_t.distillation.status.no_redstone", u"No redstone signal"),
        (u"gui.potato_s_t.distillation.status.bitumen_full", u"Bitumen slot full (64)"),
        (u"gui.potato_s_t.distillation.status.no_oil", u"Not enough oil"),
        (u"gui.potato_s_t.distillation.status.no_power", u"Not enough power"),
        (u"gui.potato_s_t.distillation.status.product_full", u"Product tanks full"),
        (u"tooltip.potato_s_t.distillation_controller", TOWER_EN),
        (u"tooltip.potato_s_t.distillation_operator", OP_EN),
    ],
    u"ja_jp.json": [
        (u"block.potato_s_t.distillation_controller", u"分留塔コントローラー"),
        (u"block.potato_s_t.distillation_operator", u"分留塔操作器"),
        (u"item.potato_s_t.bitumen", u"アスファルト"),
        (u"fluid_type.potato_s_t.diesel", u"ディーゼル"),
        (u"fluid.potato_s_t.diesel", u"ディーゼル"),
        (u"fluid_type.potato_s_t.naphtha", u"ナフサ"),
        (u"fluid.potato_s_t.naphtha", u"ナフサ"),
        (u"fluid_type.potato_s_t.gasoline", u"ガソリン"),
        (u"fluid.potato_s_t.gasoline", u"ガソリン"),
        (u"fluid_type.potato_s_t.lpg", u"液化石油ガス"),
        (u"fluid.potato_s_t.lpg", u"液化石油ガス"),
        (u"gui.potato_s_t.distillation.towers", u"分留塔：%s / %s 基"),
        (u"gui.potato_s_t.distillation.status.running", u"分留中"),
        (u"gui.potato_s_t.distillation.status.no_controller", u"隣にコントローラーがない"),
        (u"gui.potato_s_t.distillation.status.no_tower", u"分留塔が見つからない"),
        (u"gui.potato_s_t.distillation.status.no_redstone", u"レッドストーン信号なし"),
        (u"gui.potato_s_t.distillation.status.bitumen_full", u"瀝青が満杯（64）で停止"),
        (u"gui.potato_s_t.distillation.status.no_oil", u"原油不足"),
        (u"gui.potato_s_t.distillation.status.no_power", u"電力不足"),
        (u"gui.potato_s_t.distillation.status.product_full", u"製品タンクが満杯"),
        (u"tooltip.potato_s_t.distillation_controller", TOWER_JA),
        (u"tooltip.potato_s_t.distillation_operator", OP_JA),
    ],
    u"ru_ru.json": [
        (u"block.potato_s_t.distillation_controller", u"Контроллер ректификационной колонны"),
        (u"block.potato_s_t.distillation_operator", u"Оператор ректификационной колонны"),
        (u"item.potato_s_t.bitumen", u"Битум"),
        (u"fluid_type.potato_s_t.diesel", u"Дизель"),
        (u"fluid.potato_s_t.diesel", u"Дизель"),
        (u"fluid_type.potato_s_t.naphtha", u"Нафта"),
        (u"fluid.potato_s_t.naphtha", u"Нафта"),
        (u"fluid_type.potato_s_t.gasoline", u"Бензин"),
        (u"fluid.potato_s_t.gasoline", u"Бензин"),
        (u"fluid_type.potato_s_t.lpg", u"СУГ"),
        (u"fluid.potato_s_t.lpg", u"СУГ"),
        (u"gui.potato_s_t.distillation.towers", u"Башни: %s / %s"),
        (u"gui.potato_s_t.distillation.status.running", u"Перегонка"),
        (u"gui.potato_s_t.distillation.status.no_controller", u"Нет контроллера рядом"),
        (u"gui.potato_s_t.distillation.status.no_tower", u"Колонны не найдены"),
        (u"gui.potato_s_t.distillation.status.no_redstone", u"Нет сигнала редстоуна"),
        (u"gui.potato_s_t.distillation.status.bitumen_full", u"Слот битума заполнен (64)"),
        (u"gui.potato_s_t.distillation.status.no_oil", u"Недостаточно нефти"),
        (u"gui.potato_s_t.distillation.status.no_power", u"Недостаточно энергии"),
        (u"gui.potato_s_t.distillation.status.product_full", u"Баки продуктов полны"),
        (u"tooltip.potato_s_t.distillation_controller", TOWER_RU),
        (u"tooltip.potato_s_t.distillation_operator", OP_RU),
    ],
}

fails = []


def unescape_for_compare(value):
    u"""把"写进文件的转义形式"还原成"json 解析出来的形式"再比。

    ⚠ 这两个不是同一个字符串：源里的 `\\n` 是**反斜杠 + n 两个字符**（正是 JSON 里
    表示换行的写法，写进文件后 json.loads 会读成真正的换行）。所以核对时要把
    期望值里的 `\\n` 换成真换行，否则每一条多行 tooltip 都会假 FAIL（ZF78 第一版就踩了）。
    """
    return value.replace(u"\\n", u"\n")


def install_lang():
    counts = {}
    for name, pairs in KEYS.items():
        path = os.path.join(LANG, name)
        text = io.open(path, "r", encoding="utf-8").read()
        existing = [k for k, _ in pairs if (u'"%s"' % k) in text]
        if len(existing) == len(pairs):
            print(u"  [SKIP] %s：%d 个键都在了（幂等）" % (name, len(pairs)))
        elif existing:
            fails.append(u"%s：只命中 %d/%d 个键（半成品，人工看一眼）"
                         % (name, len(existing), len(pairs)))
            continue
        else:
            hits = text.count(ANCHOR)
            if hits != 1:
                fails.append(u"%s：锚点命中 %d 次（必须正好 1 次）" % (name, hits))
                continue
            idx = text.index(ANCHOR)
            eol = text.index(u"\n", idx) + 1
            block = u"".join(u'  "%s":  "%s",\n' % (k, v) for k, v in pairs)
            text = text[:eol] + block + text[eol:]
            io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
            print(u"  [OK]   %s：+%d 键" % (name, len(pairs)))
        try:
            data = json.loads(io.open(path, "r", encoding="utf-8").read())
        except Exception as exc:
            fails.append(u"%s：写完解析失败 %s" % (name, exc))
            continue
        counts[name] = len(data)
        for k, v in pairs:
            if data.get(k) != unescape_for_compare(v):
                fails.append(u"%s：键 %s 的值不对（读到 %r）" % (name, k, data.get(k)))
    print(u"\n各语言键数：%s" % u", ".join(u"%s=%d" % (k, v) for k, v in sorted(counts.items())))
    if len(set(counts.values())) != 1:
        fails.append(u"四份语言键数不一致：%s" % counts)
    elif list(counts.values()) and list(counts.values())[0] != EXPECT_KEYS:
        fails.append(u"键数不是预期的 %d，实际 %d" % (EXPECT_KEYS, list(counts.values())[0]))
    return True


def main():
    print(u"== ① 沥青占位贴图（借原版火药图，落成我们自己的文件）==")
    install_bitumen_texture()
    print(u"== ②③ blockstate / 方块模型 / 物品模型 ==")
    install_models()
    print(u"== ④ c: 流体标签 ==")
    install_fluid_tags()
    print(u"== ⑤ mineable/pickaxe.json ==")
    patch_mineable()
    print(u"== ⑥ 语言（四份）==")
    install_lang()
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
