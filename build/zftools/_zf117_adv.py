# -*- coding: utf-8 -*-
u"""_zf117_adv.py —— ZF117 进度树**补线**：8 个新节点 + 四语言 16 键（432 → 448）

用户原话：「嗯嗯 成就该更新了宝宝」

设计口径（沿用 ZF107 立下的规矩：**只给里程碑、说明文字写下一步该干什么、判定只用数据包触发器**）：

  A. **ZF107 之后新加的内容**（这是"更新"二字最直接的所指）：
     ① `oil_pump`        采油机（ZF109）—— 挂 `distillation`，goal
     ② `lithium_battery_plant` 锂电池构造间（ZF112/115）—— 挂 `acid`，goal
     ③ `lithium_battery` 三元聚合物锂电池 —— 挂 ②，task
     ④ `star_steel`      星璨钢（ZF111）—— 挂 `hard_alloy`（合金线的顶），goal
     ⑤ `star_steel_armor` 星璨钢套装（ZF110/116）—— 挂 ④，**challenge**（四件"与"）
     ⑥ `starfall`        星轨坠 + 粗振金（ZF114）—— 挂根，**hidden challenge**（彩蛋位）
  B. **两条老空洞**（ZF107 当时把这类并进上一级说明里了，但这两条连"上一级"都没提）：
     ⑦ `salt`            海盐 / 晒盐机 —— 挂 `steel`，task
        （理由：`electrolyzer` 的说明写着「加海盐再电解」，但**全树没有一处说海盐哪来**）
     ⑧ `fluid_logistics` 流体泵 + 容器换流器 —— 挂 `stronger_power`，task
        （理由：两台都是"整台机器"级的东西，且流体泵是采油机/分馏塔的必备件）

⚠ 判据写法沿用 §4.74 那条雷的结论：
   `inventory_changed` 的 `items` 是**「与」**⇒「或」必须写成**多条判据塞进同一个 requirement 组**。

⚠ 六处**我定的**（用户没说的，写在档案里等拍板）：
   ① 星璨钢挂 `hard_alloy` 而不是 `stable_block`（合金线的血统）；
   ② 星轨坠挂**根**、且**隐藏**（理由：它与两张唱片一样**没有配方**、只能创造拿，
      做成主线上的一环会留下一个生存永远点不亮的空洞）；
   ③ 套装那条用 challenge 而不隐藏（它是真能打出来的，只是要 24 个锭）；
   ④ 海盐挂 `steel`（晒盐机的配方要高碳钢 + 银板，和电解器同层）；
   ⑤ 液体物流挂 `stronger_power`（流体泵的配方要发电机）；
   ⑥ 说明文字里的数字全部来自盘上的常数（n 的公式、600 mB、720 万 FE、4M FE、24 个锭……）。
"""
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
ADIR = r"src\main\resources\data\potato_s_t\advancement"
LANG = r"src\main\resources\assets\potato_s_t\lang"
JAVA = r"src\main\java\com\potatost\mod"

KEY_OLD = 432          # ZF114 之后的活体数字
KEY_NEW = KEY_OLD + 16  # 8 节点 × 标题/说明

u = lambda s: s  # noqa: E731

NODES = [
    # ---------------------------------------------------------------- A①②③ 锂电池线
    dict(id="lithium_battery_plant", parent="acid", frame="goal", icon="lithium_battery_plant",
         crit=("any", ["lithium_battery_plant"]),
         zh=(u"锂电池构造间",
             u"通上硫酸（每 tick 1 mB，一炉 600 mB —— 800 的罐刚好够一整炉），四个槽各放一份：粗锰或粗铝、"
             u"镍或粗镍、碳酸锂、钴或粗钴 —— 30 秒出一个锂电池原件。这台机器不耗电"
             u"（碳酸锂 = 锂矿精粉进电力高炉烧出来）"),
         en=("Lithium Battery Plant",
             "Feed it sulfuric acid (1 mB per tick, 600 mB per batch - the 800 mB tank covers a whole batch) "
             "and one of each: raw manganese or raw aluminium, nickel or raw nickel, lithium carbonate, "
             "cobalt or raw cobalt - 30 s later you get a Lithium Battery Component. This machine uses no power "
             "(lithium carbonate = lithium concentrate through the Electric Blast Furnace)"),
         ja=(u"リチウム電池工房",
             u"硫酸を注入し（毎 tick 1 mB、1 バッチ 600 mB —— 800 mB のタンクでちょうど 1 バッチ）、"
             u"4 つのスロットに粗マンガンか粗アルミ、ニッケルか粗ニッケル、炭酸リチウム、コバルトか粗コバルトを"
             u"1 つずつ —— 30 秒でリチウム電池部品が 1 つ。この機械は電力を消費しない"
             u"（炭酸リチウム = リチウム精鉱を電力高炉へ）"),
         ru=("Цех литиевых батарей",
             "Подайте серную кислоту (1 mB за тик, 600 mB на партию — бака на 800 mB хватает ровно на партию) "
             "и по одному: сырой марганец или сырой алюминий, никель или сырой никель, карбонат лития, "
             "кобальт или сырой кобальт — через 30 с получите компонент литиевой батареи. "
             "Эта машина не потребляет энергию (карбонат лития = литиевый концентрат в электродоменную печь)")),
    dict(id="lithium_battery", parent="lithium_battery_plant", frame="task", icon="lithium_battery",
         crit=("any", ["lithium_battery"]),
         zh=(u"三元聚合物锂电池",
             u"纸 + 电容 + 一般金属块 + 锂电池原件 → 三元聚合物锂电池；一块存 4M FE，还能像搭金字塔那样往上叠"
             u"（2×2 六层 / 3×3 十二层 / 5×5 三十二层），只有底面能接线"),
         en=("Ternary Polymer Lithium Battery",
             "Paper + Capacitor + Common Metal Block + Lithium Battery Component → a Ternary Polymer Lithium "
             "Battery; one block stores 4M FE and they stack into a pyramid (2×2 up to 6 high, 3×3 up to 12, "
             "5×5 up to 32); only the bottom layer takes cables"),
         ja=(u"三元系ポリマーリチウム電池",
             u"紙 + コンデンサ + 一般金属ブロック + リチウム電池部品 → 三元系ポリマーリチウム電池。"
             u"1 ブロックで 4M FE を蓄え、ピラミッド状に積める（2×2 は 6 段、3×3 は 12 段、5×5 は 32 段まで）。"
             u"配線できるのは最下段だけ"),
         ru=("Тройной полимер-литиевый аккумулятор",
             "Бумага + конденсатор + обычный металлический блок + компонент литиевой батареи → тройной "
             "полимер-литиевый аккумулятор; один блок хранит 4M FE, а из них складывается пирамида "
             "(2×2 до 6 в высоту, 3×3 до 12, 5×5 до 32); кабели подходят только к нижнему слою")),

    # ---------------------------------------------------------------- A④⑤ 星璨钢线
    dict(id="star_steel", parent="hard_alloy", frame="goal", icon="star_steel_ingot",
         crit=("any", ["star_steel_ingot"]),
         zh=(u"星璨钢",
             u"合金炉：下界合金锭 + 4 高碳钢 + 钴锭 + 银锭 + 铜锭，另外还要吃掉 1 个深层钴矿石和 1 个末影水晶 "
             u"→ 3 个星璨钢锭；12000 FE/t 要跑满 30 秒（一炉 720 万 FE）"),
         en=("Star Steel",
             "Alloy Smelter: Netherite Ingot + 4 High Carbon Steel + Cobalt Ingot + Silver Ingot + Copper Ingot, "
             "and it also eats 1 Deepslate Cobalt Ore and 1 End Crystal → 3 Star Steel Ingots; "
             "12000 FE/t for a full 30 s (7.2M FE per batch)"),
         ja=(u"星燦鋼",
             u"合金精錬炉：ネザライトインゴット + 高炭素鋼 4 + コバルトインゴット + 銀インゴット + 銅インゴット、"
             u"さらに深層コバルト鉱石 1 とエンドクリスタル 1 を消費 → 星燦鋼インゴット 3 つ。"
             u"12000 FE/t で 30 秒（1 バッチ 720 万 FE）"),
         ru=("Звёздная сталь",
             "Плавильня: слиток незерита + 4 высокоуглеродистой стали + кобальт + серебро + медь, "
             "а также 1 глубинная кобальтовая руда и 1 кристалл Края → 3 слитка звёздной стали; "
             "12000 FE/t ровно 30 с (7,2 млн FE за партию)")),
    dict(id="star_steel_armor", parent="star_steel", frame="challenge", icon="star_steel_chestplate",
         crit=("all", ["star_steel_helmet", "star_steel_chestplate", "star_steel_leggings",
                       "star_steel_boots"]),
         zh=(u"星璨钢套装",
             u"头盔 5 + 胸甲 8 + 护腿 7 + 靴子 4 = 24 个星璨钢锭 —— 四件全穿在身上，就是本模组最硬的一套"),
         en=("Star Steel Suit",
             "Helmet 5 + Chestplate 8 + Leggings 7 + Boots 4 = 24 Star Steel Ingots - wear all four and you "
             "have the toughest set in this mod"),
         ja=(u"星燦鋼の装備一式",
             u"ヘルメット 5 + チェストプレート 8 + レギンス 7 + ブーツ 4 = 星燦鋼インゴット 24 個 —— "
             u"4 つ揃えて装備すれば、この Mod で最も硬い一式"),
         ru=("Комплект звёздной стали",
             "Шлем 5 + нагрудник 8 + штаны 7 + ботинки 4 = 24 слитка звёздной стали — наденьте все четыре, "
             "и это самый прочный комплект в моде")),

    # ---------------------------------------------------------------- A① 采油机
    dict(id="oil_pump", parent="distillation", frame="goal", icon="oil_pump",
         crit=("any", ["oil_pump"]),
         zh=(u"海底油田",
             u"采油机要站在海洋油田里：正下方那一串泡在水里的锁链就是井深 n —— 耗电 8n²+80n FE/t、"
             u"出油 10n mB/s，25B 的横罐只出不进（得用管道 / 流体泵抽走）；每采够 25~80 桶，"
             u"附近 10×10 区块的油田会变成旁边的海洋（冻洋 / 暖洋 / 温带海洋……），"
             u"那一刻它自己脚下也不再是油田、会停机，挪个地方接着抽"),
         en=("Oil Under the Sea",
             "The Oil Pump must stand in an ocean oilfield: the run of waterlogged chains straight below is the "
             "well depth n - 8n²+80n FE/t in, 10n mB/s out, and the 25-bucket horizontal tank is drain-only "
             "(pipe or pump it out). Every 25-80 buckets, the oilfield within 10×10 chunks turns into the "
             "neighbouring ocean (frozen, warm, temperate...), which also stops the pump - move it along"),
         ja=(u"海底油田",
             u"採油機は海洋油田の中に置く：真下に続く水没した鎖の本数が井戸の深さ n —— 8n²+80n FE/t を消費して "
             u"10n mB/s を汲み上げる。25B の横型タンクは出すだけで、配管かポンプで抜く必要がある。"
             u"25~80 バケツごとに周囲 10×10 チャンクの油田が隣の海（凍った海・暖かい海・温和な海…）に変わり、"
             u"その時この機械の足元も油田でなくなるので停止する —— 場所を移して続けよう"),
         ru=("Нефть под морем",
             "Насос должен стоять в океанском месторождении: затопленные цепочки прямо под ним — это глубина "
             "скважины n — 8n²+80n FE/t на входе, 10n mB/s на выходе, а горизонтальный бак на 25 ведёр только "
             "выдаёт (качайте трубой или насосом). Каждые 25-80 ведёр месторождение в радиусе 10×10 чанков "
             "превращается в соседний океан (замёрзший, тёплый, умеренный...), и насос встаёт — переносите его")),

    # ---------------------------------------------------------------- A⑥ 星轨坠（彩蛋位）
    dict(id="starfall", parent="new_beginning", frame="challenge", icon="starfall_pendant",
         hidden=True, crit=("any", ["starfall_pendant", "raw_vibranium"]),
         zh=(u"星轨坠",
             u"右键甩出星轨坠：4 点耐久、一次扣 1 点，快捷栏上方亮起 30 秒红色倒计时；前 10 秒再右键能取消，"
             u"之后聊天栏替你报时，最后 1 秒报出使用者和坐标 —— 陨石从 y=200 砸下来，7~20 威力带火，"
             u"喷出的粗矿里 15 以上还固定夹 3 块粗振金"),
         en=("Starfall Pendant",
             "Right-click the Starfall Pendant: 4 durability, one per use, and a red 30-second countdown lights "
             "up above your hotbar; you can cancel it in the first 10 seconds, after that chat counts down for "
             "you and the last second names the user and the coordinates - the meteor comes down from y=200, "
             "explodes with power 7-20 and fire, and 15+ also drops 3 Raw Vibranium"),
         ja=(u"星墜のペンダント",
             u"右クリックで使用：耐久 4、1 回で 1 消費。ホットバーの上に 30 秒の赤いカウントダウンが出る。"
             u"最初の 10 秒はもう一度右クリックで取消でき、以降はチャットが秒読みし、最後の 1 秒に使用者と座標が"
             u"告げられる —— 隕石は y=200 から落下し、威力 7~20・延焼ありの爆発。15 以上なら粗ビブラニウムが "
             u"3 つ確定で出る"),
         ru=("Подвеска звездопада",
             "ПКМ по подвеске: прочность 4, одна за использование, и над хотбаром загорается красный отсчёт "
             "на 30 с; первые 10 с можно отменить, дальше чат отсчитывает сам, а в последнюю секунду назовёт "
             "пользователя и координаты — метеорит падает с y=200, взрыв силой 7-20 с огнём, а при 15+ "
             "выпадет 3 куска сырого вибраниума")),

    # ---------------------------------------------------------------- B⑦⑧ 两条老空洞
    dict(id="salt", parent="steel", frame="task", icon="sea_salt",
         crit=("any", ["sea_salt", "salt_dryer"]),
         zh=(u"海盐",
             u"晒盐机不用喂任何东西：摆着慢慢晒，通电快得多 → 海盐。海盐丢进电解器加水就出氯气（盐酸的原料），"
             u"或者交给盐分解构器：64 个海盐 40 秒，100% 出氯化钠、60% 把海盐还给你、5% 掉一块粗矿"),
         en=("Sea Salt",
             "The Salt Dryer needs no input: leave it in the sun, or power it to go much faster → Sea Salt. "
             "Drop it into the Electrolyzer with water for Chlorine (the raw material for hydrochloric acid), "
             "or feed the Salt Decomposer: 64 Sea Salt over 40 s gives 100% Sodium Chloride, hands 60% of the "
             "salt back and has a 5% chance of a raw ore"),
         ja=(u"海塩",
             u"塩田機は入力不要：放っておけばゆっくり、通電すればずっと速く → 海塩。海塩を水と一緒に電解装置へ"
             u"入れると塩素（塩酸の原料）。塩分解器に 64 個入れると 40 秒で塩化ナトリウム 100%、"
             u"海塩 60% 返却、5% で粗鉱石が 1 つ"),
         ru=("Морская соль",
             "Солнечной сушилке не нужно сырьё: оставьте её на солнце или подайте энергию, чтобы шло быстрее → "
             "морская соль. Бросьте её в электролизёр с водой ради хлора (сырьё для соляной кислоты) "
             "или в разложитель соли: 64 соли за 40 с дают 100% хлорида натрия, 60% соли обратно "
             "и 5% шанс на сырую руду")),
    dict(id="fluid_logistics", parent="stronger_power", frame="task", icon="fluid_pump",
         crit=("any", ["fluid_pump", "fluid_exchanger"]),
         zh=(u"液体物流",
             u"流体泵自己不存液体：只把源里的液体往目标搬，而且优先送目标收得下的那种，"
             u"也能把世界里的液体源方块抽干；容器换流器拿 1 个空桶，换出罐里那 1000 mB 对应的桶"
             u"（水 → 水桶、柴油 → 柴油桶，别的 mod 的流体只要有桶也行）"),
         en=("Fluid Logistics",
             "The Fluid Pump stores nothing: it only moves fluid from the sources into the target, preferring "
             "whatever the target accepts, and it can drain liquid source blocks from the world. "
             "The Fluid Exchanger takes 1 empty bucket and turns it into the bucket of the 1000 mB in its tank "
             "(water → Water Bucket, diesel → Diesel Bucket, other mods too if they have one)"),
         ja=(u"液体物流",
             u"流体ポンプは液体を溜めない：供給元から目標へ移すだけで、目標が受け取れる種類を優先し、"
             u"世界の液体源ブロックも吸い上げられる。容器交換器は空のバケツ 1 つで、タンク内 1000 mB に"
             u"対応するバケツを作る（水 → 水入りバケツ、ディーゼル → ディーゼル入りバケツ、"
             u"他 Mod の流体も桶があれば可）"),
         ru=("Жидкостная логистика",
             "Насос ничего не хранит: он лишь перекачивает жидкость из источников в цель, предпочитая то, "
             "что цель принимает, и может осушать исходные блоки жидкости в мире. Обменник берёт 1 пустое "
             "ведро и делает ведро тех 1000 mB, что в его баке (вода → ведро воды, дизель → ведро дизеля, "
             "у других модов — если есть своё ведро)")),
]

OLD_NODES = ["new_beginning", "clean_energy", "stronger_power", "crushing", "pressing", "wiring",
             "first_power", "capacitor", "blast_furnace", "steel", "titanium", "electrolyzer",
             "gas_handling", "alloy_smelter", "light_alloy", "hard_alloy", "stable_block",
             "titanium_tools", "oil", "distillation", "fuel", "sulfur", "ammonia", "combustion",
             "acid", "music_disc_anvil", "music_disc_jasmine"]


def mod_ids():
    u"""盘上真正注册过的物品/方块 id（判据里只许出现这些）"""
    ids = set()
    for f in ("ModItems.java", "ModBlocks.java", "PotatoSTOres.java", "ModArmorItems.java"):
        p = os.path.join(ROOT, JAVA, f)
        if os.path.exists(p):
            ids |= set(re.findall(r'register\(\s*"([a-z0-9_]+)"',
                                  io.open(p, encoding="utf-8").read()))
    return ids


def display(node, background=False):
    icon = node["icon"]
    d = {
        "icon": {"count": 1, "id": "potato_s_t:" + icon},
        "title": {"translate": "advancements.potato_s_t.%s.title" % node["id"]},
        "description": {"translate": "advancements.potato_s_t.%s.description" % node["id"]},
        "frame": node["frame"],
        "show_toast": True,
        "announce_to_chat": True,
        "hidden": bool(node.get("hidden")),
    }
    if background:
        d["background"] = "potato_s_t:textures/block/common_metal_block.png"
    return d


def criteria_of(node):
    u"""判据 → (criteria, requirements)；「或」= 多条判据同一个组，「与」= 每条判据各占一组（§4.74）"""
    kind = node["crit"][0]
    items = node["crit"][1]
    crit = {}
    for n, i in enumerate(items):
        crit["got%d" % n] = {"trigger": "minecraft:inventory_changed",
                             "conditions": {"items": [{"items": "potato_s_t:" + i}]}}
    if kind == "any":
        return crit, [list(crit.keys())]
    if kind == "all":
        return crit, [[k] for k in crit]
    raise ValueError("unknown crit kind %r" % (kind,))


def build(node, background=False):
    obj = {}
    if node.get("parent"):
        obj["parent"] = "potato_s_t:" + node["parent"]
    obj["display"] = display(node, background)
    crit, requirements = criteria_of(node)
    obj["criteria"] = crit
    obj["requirements"] = requirements
    obj["sends_telemetry_event"] = False
    return obj


def main():
    fails = []
    ids = mod_ids()
    known = set(OLD_NODES) | set(n["id"] for n in NODES)
    # ---- 写前自检（锚点 / 图闭合 / 物品真注册 / 图标不许复用别人）
    for n in NODES:
        if n["parent"] not in known:
            fails.append(u"%s：父节点 %s 不在树里" % (n["id"], n["parent"]))
        for i in [n["icon"]] + list(n["crit"][1]):
            if i not in ids:
                fails.append(u"%s：%s 没在盘上注册" % (n["id"], i))
        if n["frame"] not in ("task", "goal", "challenge"):
            fails.append(u"%s：frame 非法 %s" % (n["id"], n["frame"]))
        if len(n["crit"][1]) != len(set(n["crit"][1])):
            fails.append(u"%s：判据物品有重复" % n["id"])
        for loc in ("zh", "en", "ja", "ru"):
            t, d = n[loc]
            if not t.strip() or not d.strip():
                fails.append(u"%s/%s：标题或说明为空" % (n["id"], loc))
            if u'"' in t or u'"' in d:
                fails.append(u"%s/%s：出现了 ASCII 双引号（§4.24）" % (n["id"], loc))
    seen = set()
    for n in NODES:
        if n["id"] in seen:
            fails.append(u"重名节点 %s" % n["id"])
        if n["id"] in OLD_NODES:
            fails.append(u"%s：与老节点重名" % n["id"])
        seen.add(n["id"])
    par = dict((n["id"], n["parent"]) for n in NODES)
    for n in NODES:
        walk, cur = set(), n["id"]
        while cur in par:
            if cur in walk:
                fails.append(u"%s：父链成环" % n["id"])
                break
            walk.add(cur)
            cur = par[cur]
    # 老节点必须在盘上
    for p in OLD_NODES:
        if not os.path.exists(os.path.join(ROOT, ADIR, p + u".json")):
            fails.append(u"老节点缺失：%s" % p)
    if fails:
        print(u"写前自检就挂了，一个字节都没落盘：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    # ---- 1) 新成就（不许覆盖已存在的**不同**内容）
    for n in NODES:
        path = os.path.join(ROOT, ADIR, n["id"] + u".json")
        text = json.dumps(build(n), ensure_ascii=False, indent=2) + u"\n"
        if os.path.exists(path):
            old = io.open(path, encoding="utf-8").read()
            if old == text:
                print(u"  [--]   %-24s 已在盘上且逐字节相同，跳过" % (n["id"] + u".json"))
                continue
            fails.append(u"%s 已存在且内容不同 —— 停手（先看清那是谁的）" % (n["id"] + u".json"))
            continue
        back = json.loads(text)
        if back["display"]["title"]["translate"] != "advancements.potato_s_t.%s.title" % n["id"]:
            fails.append(u"%s：回读不一致" % n["id"])
            continue
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
        print(u"  [OK]   %-24s %d B" % (n["id"] + u".json", len(text.encode("utf-8"))))
    if fails:
        print(u"有节点写失败，语言一个字节不动")
        for f in fails:
            print(u"  !! " + f)
        return 1

    # ---- 2) 四语言
    for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        loc_key = {"zh_cn": "zh", "en_us": "en", "ja_jp": "ja", "ru_ru": "ru"}[loc]
        p = os.path.join(ROOT, LANG, loc + u".json")
        raw = io.open(p, encoding="utf-8").read()
        data = json.loads(raw)
        before = dict(data)
        table = {}
        for n in NODES:
            t, d = n[loc_key]
            table["advancements.potato_s_t.%s.title" % n["id"]] = t
            table["advancements.potato_s_t.%s.description" % n["id"]] = d
        dup = [k for k in table if k in data]
        same = [k for k in dup if data[k] == table[k]]
        conflict = [k for k in dup if data[k] != table[k]]
        if conflict:
            fails.append(u"%s：这些键已经有**别的值** %s" % (loc, conflict))
            continue
        for k in same:
            table.pop(k)
        if not table:
            print(u"  [--]   %-12s %d 键已到位，无需改动" % (loc + u".json", len(data)))
            continue
        lines = raw.split(u"\n")
        anchor = None
        for i, l in enumerate(lines):
            if l.strip().startswith(u'"advancements.potato_s_t.'):
                anchor = i
        if anchor is None:
            fails.append(u"%s：找不到 advancements 区块的锚点行" % loc)
            continue
        if not lines[anchor].rstrip().endswith(u","):
            lines[anchor] = lines[anchor].rstrip() + u","
        block = [u'    %s:  %s,' % (json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False))
                 for k, v in sorted(table.items())]
        lines[anchor + 1:anchor + 1] = block
        text = u"\n".join(lines)
        back = json.loads(text)
        if len(back) != len(data) + len(table):
            fails.append(u"%s：回读键数 %d ≠ %d" % (loc, len(back), len(data) + len(table)))
            continue
        changed = [k for k in before if k not in back or back[k] != before[k]]
        if changed:
            fails.append(u"%s：动到了老键 %s" % (loc, changed[:5]))
            continue
        if len(back) != KEY_NEW:
            fails.append(u"%s：键数 %d ≠ 预期 %d" % (loc, len(back), KEY_NEW))
            continue
        io.open(p, "w", encoding="utf-8", newline=u"").write(text)
        print(u"  [OK]   %-12s %d → %d 键（+%d）" % (loc + u".json", len(data), len(back), len(table)))

    print(u"\n新节点 = %d，键数 %d → %d" % (len(NODES), KEY_OLD, KEY_NEW))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
