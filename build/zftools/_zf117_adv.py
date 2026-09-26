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
         zh=(u"锂电池构造间", u"通硫酸（每 tick 1 mB，一炉 600 mB），四槽各放：粗锰或粗铝、镍、碳酸锂、钴，30 秒出一个锂电池原件"),
         en=("Lithium Battery Plant", "Sulfuric Acid in (1 mB/tick, 600 mB a batch) and one item per slot: raw manganese or aluminium, nickel, lithium carbonate, cobalt - a Lithium Battery Part every 30 s"),
         ja=(u"リチウム電池工房", u"硫酸を通し（毎 tick 1 mB、1 バッチ 600 mB）、4 スロットに 1 つずつ：粗マンガンか粗アルミ、ニッケル、炭酸リチウム、コバルト → 30 秒で電池部品 1 個"),
         ru=("Цех литиевых батарей", "Серная кислота (1 mB/тик, 600 mB на партию) и по предмету в слот: марганец или алюминий, никель, карбонат лития, кобальт — деталь за 30 с")),
    dict(id="lithium_battery", parent="lithium_battery_plant", frame="task", icon="lithium_battery",
         crit=("any", ["lithium_battery"]),
         zh=(u"三元聚合物锂电池", u"纸 + 电容 + 一般金属块 + 锂电池原件 → 三元聚合物锂电池；一块存 4M FE，能像搭金字塔那样叠高，只有底面能接线"),
         en=("Ternary Polymer Lithium Battery", "Paper + Capacitor + Common Metal Block + Lithium Battery Part -> Ternary Polymer Lithium Battery; 4M FE per block, stack it like a pyramid, terminals on the bottom only"),
         ja=(u"三元系ポリマーリチウム電池", u"紙 + コンデンサ + 一般金属ブロック + リチウム電池部品 → 三元系ポリマーリチウム電池。1 ブロック 4M FE、ピラミッドのように積め、端子は底面のみ"),
         ru=("Тройной полимер-литиевый аккумулятор", "Бумага + конденсатор + обычный металлический блок + деталь → литиевая батарея; 4M FE на блок, складывается пирамидой, клеммы только снизу")),

    # ---------------------------------------------------------------- A④⑤ 星璨钢线
    dict(id="star_steel", parent="hard_alloy", frame="goal", icon="star_steel_ingot",
         crit=("any", ["star_steel_ingot"]),
         zh=(u"炼出星璨钢", u"合金炉一炉吃：下界合金锭 + 4 高碳钢 + 钴锭 + 银锭 + 铜锭 + 深层钴矿石 + 末影水晶，出 3 个星璨钢锭（12000 FE/t 满跑 30 秒）"),
         en=("Forge the Star Steel", "Alloy Smelter, one batch: Netherite + 4 High Carbon Steel + Cobalt + Silver + Copper + Deepslate Cobalt Ore + Ender Crystal -> 3 Star Steel Ingots (12000 FE/t, 30 s)"),
         ja=(u"星燦鋼を鍛えよう", u"合金精錬炉 1 バッチ：ネザライト + 高炭素鋼 4 + コバルト + 銀 + 銅 + 深層コバルト鉱石 + エンダークリスタル → 星燦鋼 3 個（12000 FE/t で 30 秒）"),
         ru=("Выкуйте звёздную сталь", "Плавильня, партия: незерит + 4 высокоуглеродистой стали + кобальт + серебро + медь + глубинная кобальтовая руда + кристалл Края → 3 слитка звёздной стали (12000 FE/т, 30 с)")),
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
         zh=(u"向海要油", u"采油机站在海洋油田：正下方泡水的锁链就是井深 n，耗电 8n²+80n FE/t、出油 10n mB/s，25B 横罐只出不进"),
         en=("Oil From Beneath the Sea", "An Oil Pump in an Ocean Oilfield: the chain in the water below is the well depth n - 8n²+80n FE/t in, 10n mB/s out, 25B tank out only"),
         ja=(u"海の底から油を", u"採油機は海洋油田に設置：真下で水に浸かる鎖が井戸の深さ n。消費 8n²+80n FE/t、産出 10n mB/s、25B タンクは出すだけ"),
         ru=("Нефть из-под моря", "Нефтевышка в морском месторождении: цепь в воде под ней — глубина n; 8n²+80n FE/т, 10n mB/с, бак 25B только отдаёт")),

    # ---------------------------------------------------------------- A⑥ 星轨坠（彩蛋位）
    dict(id="starfall", parent="new_beginning", frame="challenge", icon="starfall_pendant",
         hidden=True, crit=("any", ["starfall_pendant", "raw_vibranium"]),
         zh=(u"召唤一颗星星", u"右键甩出星轨坠：4 点耐久、一次扣 1，30 秒倒计时、前 10 秒可取消；陨石从 y=200 砸下，7~20 威力带火，还夹 3 块粗振金"),
         en=("Call Down a Star", "Right-click to cast a Starfall: 4 durability, one per throw, a 30 s countdown you can cancel in the first 10 s - then a meteor at y=200, power 7~20, fire and 3 Raw Vibranium"),
         ja=(u"星を呼び下ろす", u"右クリックで星軌墜を投げる：耐久 4、1 回で 1 消費、30 秒のカウントダウンは最初の 10 秒なら取消可。隕石は y=200 から、威力 7~20、延焼と粗ビブラニウム 3 個"),
         ru=("Позовите звезду", "ПКМ бросает Звёздный груз: прочность 4, по 1 за бросок, отсчёт 30 с можно отменить в первые 10 с — затем метеорит с y=200, сила 7~20, огонь и 3 сырого вибраниума")),

    # ---------------------------------------------------------------- B⑦⑧ 两条老空洞
    dict(id="salt", parent="steel", frame="task", icon="sea_salt",
         crit=("any", ["sea_salt", "salt_dryer"]),
         zh=(u"向大海要盐", u"晒盐机不用喂东西，摆着就出盐、通电更快；海盐丢进电解器加水出氯气，交给盐分解构器则 64 个海盐 40 秒出氯化钠"),
         en=("Salt From the Sea", "The Salt Dryer needs no input - just leave it out for Sea Salt, faster with power; salt + water in the Electrolyzer gives chlorine, or 64 salt in the Decomposer for sodium chloride in 40 s"),
         ja=(u"海から塩を", u"塩乾燥機は何も入れずに放置で海塩ができ、通電すると速くなります。海塩は電解装置で水と一緒に塩素に、塩分解構築器なら海塩 64 個から 40 秒で塩化ナトリウム"),
         ru=("Соль из моря", "Солесушилке не нужно сырьё: даёт морскую соль сама, с энергией быстрее; соль с водой в электролизёре даёт хлор, а 64 соли в разлагателе — хлорид натрия за 40 с")),
    dict(id="fluid_logistics", parent="stronger_power", frame="task", icon="fluid_pump",
         crit=("any", ["fluid_pump", "fluid_exchanger"]),
         zh=(u"液体物流", u"流体泵不存液体，只送收得下的目标，也能抽干液体源；容器换流器拿空桶换出罐里 1000 mB 对应的桶"),
         en=("Fluid Logistics", "The Fluid Pump stores nothing, only moves fluid into a destination that accepts it, and can drain sources; the Exchanger turns an empty bucket into the one matching the 1000 mB in its tank"),
         ja=(u"液体物流", u"流体ポンプは液体を溜めず、受け取れる送り先へ送るだけ（液体源の汲み上げも可）。容器換装器は空バケツを、タンク内 1000 mB に対応するバケツに変える"),
         ru=("Жидкостная логистика", "Насос ничего не хранит: лишь перекачивает жидкость в принимающий приёмник и умеет выкачивать источники; обменник делает из пустого ведра ведро под 1000 mB из бака")),
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
