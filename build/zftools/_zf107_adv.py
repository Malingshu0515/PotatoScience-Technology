# -*- coding: utf-8 -*-
u"""_zf107_adv.py —— ZF107 成就（进度）树：一份表 → 24 个新成就 JSON + 四语言 48 键

用户原话：
  「你自己发挥一下 把进度（成就）做一点 最好能引导一下玩家 全流程
    但也不是非得一个步骤就冒一个成就那么烦琐」

设计口径（我定的，写在 docs 里）：
  · **一个 Tab、一条主线、四条支线**：根节点仍是老成就 `new_beginning`（"新的开始！"），
    但它的判定从"低阶发电机"前移到**第一台机器（微型粉碎机）** —— 原来那句
    「简洁的电力来源 方便且够用」整句搬给新节点 `first_power`（第一度电），文案不丢。
  · 只有**里程碑**才给成就：整台机器 / 关键材料 / 关键配方；中间零件（加热装置、
    散热装置、线轴……）一律并进上一级成就的说明里 —— 这就是用户说的"别太烦琐"。
  · 说明文字**写下一步该干什么**（引导），不是复述物品名。
  · 判定只用**数据包触发器**（`inventory_changed` / `placed_block`），不动 Java：
    本轮不引入自定义 CriterionTrigger，风险最小。
  · `oil`（石油）用 `inventory_changed` + `minecraft:custom_data` 子谓词，
    要求油桶里**真的装着原油**（空桶不算）—— 探针会两种都试，见 `_zf107_verify.py`。

⚠ 两处刻意"不改"：`stronger_power` / `clean_energy` 的判据与文案一个字节不改，
   只把父链从 `new_beginning` 改挂到新的 `first_power`（树形更顺，玩家的已得成就也不会掉）。
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

u = lambda s: s  # noqa: E731  （只是让下面那张大表里的中文更好读）

# ---------------------------------------------------------------- 节点表
# crit 形式：
#   ("any",  [物品…])      一条判据、物品之间是"或" —— 拿到其中任意一件
#   ("all",  [物品…])      多条判据全都要 —— "凑齐"
#   ("placed", 方块 id)    placed_block
#   ("oil",)               油桶里装着原油（custom_data 子谓词）
NODES = [
    # ============ 主脉：从第一台机器到电力 ============
    dict(id="crushing", parent="new_beginning", frame="task", icon="iron_powder",
         crit=("any", ["iron_powder", "carbon"]),
         zh=(u"磨成粉", u"粉碎机把锭和矿磨成粉：铁粉 + 碳粉就是钢的原料（碳粉烧煤或木炭都行）"),
         en=("Grind It Down", "The crusher turns ingots and ore into dust: Iron Dust + Carbon Dust is what steel is made of (Carbon Dust comes from coal or charcoal)"),
         ja=(u"粉にする", u"粉砕機はインゴットや鉱石を粉にする：鉄粉 + 炭素粉末が鋼の材料（炭素粉末は石炭か木炭から）"),
         ru=("В пыль", "Дробилка превращает слитки и руду в пыль: железная пыль + угольная пыль — это сырьё для стали (угольная пыль — из угля или древесного угля)")),
    dict(id="pressing", parent="new_beginning", frame="task", icon="iron_plate",
         crit=("any", ["iron_plate", "copper_plate", "aluminum_plate",
                       "nickel_plate", "cobalt_plate", "silver_plate", "steel_plate"]),
         zh=(u"压成板", u"液压机把锭压成板 —— 铁板、铜板、铝板是所有机器的通用零件"),
         en=("Flat as a Plate", "The hydraulic press flattens ingots into plates — iron, copper and aluminum plates are the universal parts of every machine"),
         ja=(u"板にする", u"油圧プレスでインゴットを板に —— 鉄板・銅板・アルミニウム板はすべての機械の共通部品"),
         ru=("В пластины", "Гидравлический пресс расплющивает слитки в пластины — железные, медные и алюминиевые пластины нужны любой машине")),
    dict(id="wiring", parent="new_beginning", frame="task", icon="terminal",
         crit=("any", ["terminal", "wiring_block"]),
         zh=(u"接电", u"接线端子就是电线：拿铜线轴右键两个端子连起来（动力网络用动力线缆轴），潜行右键切换输入 / 输出"),
         en=("Wire It Up", "Terminal Blocks are the wires: right-click two of them with a Copper Wire Spool to link them (Power Cable Spool for the power network); sneak-right-click to switch input / output"),
         ja=(u"配線する", u"端子ブロックが電線：銅線のスプールで2つの端子を右クリックして接続（動力網は動力ケーブルのスプール）、スニーク右クリックで入力 / 出力を切替"),
         ru=("Провода", "Клеммные блоки — это провода: соедините два катушкой с медным проводом (для силовой сети — катушкой силового кабеля); с Shift — переключение вход / выход")),
    dict(id="first_power", parent="new_beginning", frame="task", icon="low_generator",
         crit=("any", ["low_generator"]),
         # ⚠ 这句的标点是**盘上那份说了算**：19:52 我写的是空格版「简洁的电力来源 方便且够用」，
         #    现在的盘上是润色过的逗号版（`，`）—— 以盘上为准写回表里，否则重跑生成器会报"值冲突"。
         zh=(u"第一度电", u"简洁的电力来源，方便且够用 —— 塞煤或木炭发电，再用端子把电送到机器旁"),
         en=("First Watt", "A simple power source - handy and sufficient. Burn coal or charcoal, then run the power to your machines with terminals"),
         ja=(u"最初の一ワット", u"簡素な電力源 便利で十分 —— 石炭か木炭を燃やし、端子で機械まで電気を送る"),
         ru=("Первый ватт", "Простой источник энергии — удобно и достаточно. Жгите уголь или древесный уголь и ведите энергию к машинам через клеммы")),
    dict(id="capacitor", parent="pressing", frame="task", icon="capacitor",
         crit=("any", ["capacitor"]),
         zh=(u"电容", u"铜锭 + 铝板 + 银板 = 电容；电力高炉、合金炉、太阳能板都要它"),
         en=("Capacitor", "Copper Ingot + Aluminum Plate + Silver Plate = Capacitor; the Electric Blast Furnace, Alloy Smelter and Solar Panel all need one"),
         ja=(u"コンデンサ", u"銅インゴット + アルミニウム板 + 銀インゴット = コンデンサ；電力高炉・合金精錬炉・ソーラーパネルに必要"),
         ru=("Конденсатор", "Медный слиток + алюминиевая пластина + серебряный слиток = конденсатор; он нужен доменной печи, плавильне и солнечной панели")),

    # ============ 主脉：高温与合金 ============
    dict(id="blast_furnace", parent="capacitor", frame="goal", icon="electric_blast_furnace",
         crit=("any", ["electric_blast_furnace"]),
         zh=(u"电力高炉", u"一栋 3×3×3 的多方块：正面锚点放原版高炉或主控，再用外壳围起来 —— 摆好后右键主控自检"),
         en=("Electric Blast Furnace", "A 3×3×3 multiblock: put a vanilla Blast Furnace or the controller as the front anchor, then wall it in with casings — right-click the controller to check the build"),
         ja=(u"電力高炉", u"3×3×3 のマルチブロック：正面のアンカーにバニラの高炉かコントローラーを置き、外殻で囲う —— 設置後はコントローラーを右クリックで自己診断"),
         ru=("Электрическая доменная печь", "Мультиблок 3×3×3: спереди ставится обычная доменная печь или контроллер, затем обшивается корпусами — щёлкните контроллер, чтобы проверить постройку")),
    dict(id="steel", parent="blast_furnace", frame="goal", icon="high_carbon_steel",
         crit=("any", ["high_carbon_steel"]),
         zh=(u"钢铁是这样炼成的", u"铁粉 + 碳粉丢进电力高炉 → 高碳钢；钢材是后面几乎所有东西的骨架"),
         en=("Thus Steel Was Made", "Iron Dust + Carbon Dust into the Electric Blast Furnace → High Carbon Steel; steel is the backbone of nearly everything after this"),
         ja=(u"鋼はこうして作られる", u"鉄粉 + 炭素粉末を電力高炉へ → 高炭素鋼；以降のほぼすべては鋼が骨組み"),
         ru=("Так варится сталь", "Железная пыль + угольная пыль в электрическую доменную печь → высокоуглеродистая сталь; сталь — каркас почти всего дальше")),
    dict(id="titanium", parent="steel", frame="goal", icon="titanium_ingot",
         crit=("any", ["titanium_ingot"]),
         zh=(u"钛", u"粗钛先粉碎成钛粉，钛粉再进电力高炉 → 钛锭"),
         en=("Titanium", "Crush Raw Titanium into Titanium Dust, then run the dust through the Electric Blast Furnace → Titanium Ingot"),
         ja=(u"チタン", u"粗チタンを粉砕してチタン粉にし、電力高炉へ → チタンインゴット"),
         ru=("Титан", "Раздробите необработанный титан в титановую пыль и пропустите её через доменную печь → титановый слиток")),
    dict(id="electrolyzer", parent="steel", frame="task", icon="electrolyzer",
         crit=("any", ["electrolyzer"]),
         zh=(u"电解", u"电解器：水 + 电 → 氧气 + 氢气；加海盐再电解 → 氯气 + 氢气"),
         en=("Electrolysis", "Electrolyzer: water + power → Oxygen + Hydrogen; with Sea Salt → Chlorine + Hydrogen"),
         ja=(u"電気分解", u"電解装置：水 + 電力 → 酸素 + 水素；海塩を足すと → 塩素 + 水素"),
         ru=("Электролиз", "Электролизёр: вода + энергия → кислород + водород; с морской солью → хлор + водород")),
    dict(id="gas_handling", parent="steel", frame="task", icon="high_pressure_tank",
         crit=("all", ["high_pressure_tank", "filling_machine"]),
         zh=(u"气体的存取", u"高压气罐只装气体、油桶只装液体；两者都靠灌装机灌装"),
         en=("Storing Gas", "The High-Pressure Gas Tank takes only gases and the Oil Bucket only liquids; the Filling Machine fills both"),
         ja=(u"気体の出し入れ", u"高圧ガスタンクは気体専用、オイルバケツは液体専用；どちらも充填機で充填する"),
         ru=("Хранение газов", "Баллон берёт только газы, нефтяное ведро — только жидкости; наполняет и то и другое разливочная машина")),
    dict(id="alloy_smelter", parent="capacitor", frame="goal", icon="alloy_smelter",
         crit=("any", ["alloy_smelter"]),
         zh=(u"合金炉", u"主控 + 电源端口 + 炉体：三种金属板 + 电容 + 加热装置 + 散热装置 —— 合金线的起点"),
         en=("Alloy Smelter", "Controller + power port + casings: three kinds of plate + Capacitor + Heater + Heat Sink — the start of the alloy line"),
         ja=(u"合金精錬炉", u"コントローラー + 電源ポート + 炉体：3 種の板 + コンデンサ + 加熱装置 + 放熱装置 —— 合金ラインの起点"),
         ru=("Плавильня сплавов", "Контроллер + энергопорт + корпуса: три вида пластин + конденсатор + нагреватель + радиатор — начало линии сплавов")),
    dict(id="light_alloy", parent="alloy_smelter", frame="task", icon="light_titanium_alloy",
         crit=("any", ["light_titanium_alloy"]),
         zh=(u"轻质钛合金", u"铝锭 + 钛锭 + 银锭 → 轻质钛合金（合金炉，一批 30 秒）"),
         en=("Lightweight Titanium Alloy", "Aluminum Ingot + Titanium Ingot + Silver Ingot → Lightweight Titanium Alloy (alloy smelter, 30 s per batch)"),
         ja=(u"軽量チタン合金", u"アルミニウムインゴット + チタンインゴット + 銀インゴット → 軽量チタン合金（合金炉で 1 回 30 秒）"),
         ru=("Лёгкий титановый сплав", "Алюминиевый слиток + титановый слиток + серебряный слиток → лёгкий титановый сплав (30 с в плавильне)")),
    dict(id="hard_alloy", parent="light_alloy", frame="goal", icon="hard_titanium_alloy",
         crit=("any", ["hard_titanium_alloy"]),
         zh=(u"硬质钛合金", u"轻质钛合金 + 高碳钢 + 镍锭 → 硬质钛合金"),
         en=("Hard Titanium Alloy", "Lightweight Titanium Alloy + High Carbon Steel + Nickel Ingot → Hard Titanium Alloy"),
         ja=(u"硬質チタン合金", u"軽量チタン合金 + 高炭素鋼 + ニッケルインゴット → 硬質チタン合金"),
         ru=("Твёрдый титановый сплав", "Лёгкий титановый сплав + высокоуглеродистая сталь + никелевый слиток → твёрдый титановый сплав")),
    dict(id="stable_block", parent="hard_alloy", frame="task", icon="stable_metal_block",
         crit=("any", ["stable_metal_block"]),
         zh=(u"稳定金属块", u"高碳钢 / 硬质钛合金 / 金块 摆成九宫格 → 稳定金属块（酸性反应室要它）"),
         en=("Stable Metal Block", "High Carbon Steel / Hard Titanium Alloy / Gold Block in a 3×3 → Stable Metal Block (the acidic chamber needs it)"),
         ja=(u"安定金属ブロック", u"高炭素鋼 / 硬質チタン合金 / 金ブロック を 3×3 に → 安定金属ブロック（酸性反応室に必要）"),
         ru=("Стабильный металлический блок", "Высокоуглеродистая сталь / твёрдый титановый сплав / золотой блок в 3×3 → стабильный блок (нужен кислотной камере)")),
    dict(id="titanium_tools", parent="light_alloy", frame="task", icon="titanium_alloy_pickaxe",
         crit=("any", ["titanium_alloy_pickaxe", "titanium_alloy_sword"]),
         zh=(u"钛合金工具", u"轻质钛合金 + 木棍 → 钛合金剑与镐"),
         en=("Titanium Tools", "Lightweight Titanium Alloy + Stick → Titanium Alloy Sword and Pickaxe"),
         ja=(u"チタン合金の道具", u"軽量チタン合金 + 棒 → チタン合金の剣とツルハシ"),
         ru=("Титановый инструмент", "Лёгкий титановый сплав + палка → меч и кирка из титанового сплава")),

    # ============ 支线：石油化工 ============
    dict(id="oil", parent="steel", frame="task", icon="oil_bucket",
         crit=("oil",),
         zh=(u"石油", u"用油桶去地表油田或海洋油田舀一桶原油（空桶不算数）"),
         en=("Oil", "Take an Oil Bucket to a surface or ocean oilfield and scoop up some crude oil (an empty bucket does not count)"),
         ja=(u"石油", u"オイルバケツを持って地表油田か海洋油田へ行き、原油を汲む（空のバケツではだめ）"),
         ru=("Нефть", "Возьмите нефтяное ведро и зачерпните сырую нефть на наземном или океанском месторождении (пустое ведро не считается)")),
    dict(id="distillation", parent="oil", frame="goal", icon="distillation_controller",
         crit=("any", ["distillation_controller"]),
         zh=(u"分馏塔", u"主控 + 操作员：把原油分成柴油、汽油、石脑油、液化石油气和沥青"),
         en=("Distillation Tower", "Controller + operator: split crude oil into diesel, gasoline, naphtha, LPG and bitumen"),
         ja=(u"分留塔", u"コントローラー + オペレーター：原油をディーゼル・ガソリン・ナフサ・LPG・アスファルトに分ける"),
         ru=("Ректификационная колонна", "Контроллер + оператор: разделяют нефть на дизель, бензин, нафту, СНГ и битум")),
    dict(id="fuel", parent="distillation", frame="task", icon="diesel_bucket",
         crit=("any", ["diesel_bucket", "gasoline_bucket"]),
         zh=(u"柴油与汽油", u"两种液体燃料，都是给燃烧反应室用的（柴油 1200 动力、汽油 1000）"),
         en=("Diesel & Gasoline", "Two liquid fuels, both for the Combustion Chamber (diesel 1200 power, gasoline 1000)"),
         ja=(u"ディーゼルとガソリン", u"2 種の液体燃料。どちらも燃焼反応室で使う（ディーゼル 1200 動力、ガソリン 1000）"),
         ru=("Дизель и бензин", "Два жидких топлива для камеры сгорания (дизель — 1200 мощности, бензин — 1000)")),
    dict(id="sulfur", parent="distillation", frame="task", icon="sulfur",
         crit=("any", ["sulfur"]),
         zh=(u"硫", u"沥青 + 氢气进加氢脱硫反应仓 → 硫（硫酸的原料）"),
         en=("Sulfur", "Bitumen + Hydrogen into the Hydrodesulfurization Chamber → Sulfur (the raw material for sulfuric acid)"),
         ja=(u"硫黄", u"アスファルト + 水素を水素化脱硫反応チャンバーへ → 硫黄（硫酸の原料）"),
         ru=("Сера", "Битум + водород в камеру гидроочистки → сера (сырьё для серной кислоты)")),
    dict(id="ammonia", parent="electrolyzer", frame="task", icon="ammonia_synthesis_chamber",
         crit=("any", ["ammonia_synthesis_chamber"]),
         zh=(u"合成氨", u"空气分离器出氮气，氮气 + 氢气在氨气组成室里合成氨气（硝酸的原料）"),
         en=("Ammonia", "The Air Separator gives nitrogen; nitrogen + hydrogen make Ammonia in the Ammonia Synthesis Chamber (raw material for nitric acid)"),
         ja=(u"アンモニア合成", u"空気分離器で窒素、窒素 + 水素をアンモニア合成室で → アンモニア（硝酸の原料）"),
         ru=("Аммиак", "Разделитель воздуха даёт азот; азот + водород в камере синтеза → аммиак (сырьё для азотной кислоты)")),
    dict(id="combustion", parent="fuel", frame="goal", icon="combustion_chamber",
         crit=("any", ["combustion_chamber"]),
         zh=(u"燃烧反应室", u"一份燃料 + 10 mB 氧气 → 二氧化碳；拿原木去烧还能顺手得到木炭"),
         en=("Combustion Chamber", "One fuel + 10 mB Oxygen → Carbon Dioxide; feed it a log and you also get charcoal"),
         ja=(u"燃焼反応室", u"燃料 1 つ + 10 mB 酸素 → 二酸化炭素；原木を燃やせば木炭も手に入る"),
         ru=("Камера сгорания", "Одно топливо + 10 mB кислорода → углекислый газ; с брёвнами попутно получите древесный уголь")),
    dict(id="acid", parent="combustion", frame="goal", icon="acidic_reaction_chamber",
         crit=("any", ["acidic_reaction_chamber"]),
         zh=(u"酸性反应室", u"碳酸 / 硝酸 / 硫酸 / 盐酸 —— 四种酸都在这里合成"),
         en=("Acidic Reaction Chamber", "Carbonic, nitric, sulfuric and hydrochloric acid — all four are made here"),
         ja=(u"酸性反応室", u"炭酸・硝酸・硫酸・塩酸 —— 4 つの酸はここで合成する"),
         ru=("Кислотная камера", "Угольная, азотная, серная и соляная кислота — все четыре делаются здесь")),

    # ============ 彩蛋（隐藏，只有拿到才会显形） ============
    dict(id="music_disc_anvil", parent="new_beginning", frame="challenge", icon="music_disc_anvil_of_the_republic",
         hidden=True, crit=("any", ["music_disc_anvil_of_the_republic"]),
         zh=(u"铁砧与共和国", u"红石 + 钛锭 + 铁砧 = 一张唱片。就这样，没有别的意思"),
         en=("The Anvil and the Republic", "Redstone + Titanium Ingot + Anvil = a music disc. That's it. No deeper meaning"),
         ja=(u"金床と共和国", u"レッドストーン + チタンインゴット + 金床 = 音楽ディスク。それだけ、他意はない"),
         ru=("Наковальня и республика", "Редстоун + титановый слиток + наковальня = пластинка. И всё, без подтекста")),
    dict(id="music_disc_jasmine", parent="new_beginning", frame="challenge", icon="music_disc_jasmine_flower",
         hidden=True, crit=("any", ["music_disc_jasmine_flower"]),
         zh=(u"茉莉花", u"魂灯 + 粗金块 + 火把花 = 另一张唱片。好一朵美丽的茉莉花"),
         en=("Jasmine Flower", "Soul Lantern + Raw Gold Block + Torchflower = another music disc. What a beautiful jasmine flower"),
         ja=(u"ジャスミンの花", u"ソウルランタン + 金の原石ブロック + トーチフラワー = もう一枚の音楽ディスク。なんと美しいジャスミンの花"),
         ru=("Цветок жасмина", "Фонарь душ + блок необработанного золота + факельник = ещё одна пластинка. Какой красивый цветок жасмина")),
]

# 老成就的改法（判据/父链）：只改这里列出的字段，其余一个字节不动
ROOT_ICON = "micro_crusher"
REPARENT = {"clean_energy": "potato_s_t:first_power",
            "stronger_power": "potato_s_t:first_power"}


def mod_ids():
    u"""盘上真正注册过的物品/方块 id（判据里只许出现这些，或下面那张 vanilla 白名单）"""
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
    u"""判据 → (criteria, requirements)

    ⚠⚠ **本轮的第一次探针就是被这里抓住的**：`minecraft:inventory_changed` 的
    `conditions.items` 是一个**谓词列表**，它的语义是**「与」**（每个谓词都要被满足），
    不是「或」。所以"拿到这几种板子里的任意一种"**不能**写成
    `{"items": [{"items": A}, {"items": B}]}` —— 那样要求 A 和 B 同时到手。
    正确写法（原版的"或"）：**一条判据只放一个物品**，再把这几条判据塞进
    **同一个 requirement 组**（JSON 是『外层 = 与，内层 = 或』）。
    """
    kind = node["crit"][0]
    if kind in ("any", "all"):
        items = node["crit"][1]
        crit = {}
        for n, i in enumerate(items):
            crit["got%d" % n] = {"trigger": "minecraft:inventory_changed",
                                 "conditions": {"items": [{"items": "potato_s_t:" + i}]}}
        if kind == "any":
            requirements = [list(crit.keys())]          # 一个组 = 组内任选其一 = 「或」
        else:
            requirements = [[k] for k in crit]          # 每个判据各占一组 = 全都要 = 「与」
        return crit, requirements
    if kind == "placed":
        crit = {"placed": {"trigger": "minecraft:placed_block",
                           "conditions": {"location": [{"condition": "minecraft:block_state_property",
                                                        "block": "potato_s_t:" + node["crit"][1]}]}}}
        return crit, [["placed"]]
    if kind == "oil":
        # 只认"桶里真的有原油"：custom_data 子谓词（空桶、装别的液体都不算）
        # 探针实测：`minecraft:custom_data` 是**部分匹配** —— 只写 fluid.id 就够，
        # 不用连 amount 一起写死（否则装 1000/2000/3000 得各写一条）。
        crit = {"oil": {"trigger": "minecraft:inventory_changed",
                        "conditions": {"items": [{
                            "items": "potato_s_t:oil_bucket",
                            "predicates": {"minecraft:custom_data": {
                                "fluid": {"id": "potato_s_t:crude_oil"}}}}]}}}
        return crit, [["oil"]]
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
    known = set(n["id"] for n in NODES) | {"new_beginning", "clean_energy", "stronger_power"}
    # ---- 写前自检（§4.6 锚点唯一 / 图闭合 / 物品存在）
    for n in NODES:
        if n["parent"] not in known:
            fails.append(u"%s：父节点 %s 不在树里" % (n["id"], n["parent"]))
        if n["icon"] not in ids:
            fails.append(u"%s：图标物品 %s 没在盘上注册" % (n["id"], n["icon"]))
        spec = n["crit"]
        for i in (spec[1] if len(spec) > 1 and isinstance(spec[1], list) else []):
            if i not in ids:
                fails.append(u"%s：判据物品 %s 没在盘上注册" % (n["id"], i))
    seen = set()
    for n in NODES:
        if n["id"] in seen:
            fails.append(u"重名节点 %s" % n["id"])
        seen.add(n["id"])
    # 环检测
    par = dict((n["id"], n["parent"]) for n in NODES)
    for n in NODES:
        walk, cur = set(), n["id"]
        while cur in par:
            if cur in walk:
                fails.append(u"%s：父链成环" % n["id"])
                break
            walk.add(cur)
            cur = par[cur]
    if fails:
        print(u"写前自检就挂了，一个字节都没落盘：")
        for f in fails:
            print(u"  !! " + f)
        return 1

    # ---- 1) 新成就
    written = 0
    for n in NODES:
        path = os.path.join(ROOT, ADIR, n["id"] + ".json")
        obj = build(n)
        text = json.dumps(obj, ensure_ascii=False, indent=2) + u"\n"
        back = json.loads(text)
        if back["display"]["title"]["translate"] != obj["display"]["title"]["translate"]:
            fails.append(u"%s：回读不一致" % n["id"])
            continue
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
        written += 1
    print(u"  新成就 %d 份" % written)

    # ---- 2) 三份老成就：只动该动的字段
    rootp = os.path.join(ROOT, ADIR, u"new_beginning.json")
    raw = io.open(rootp, encoding="utf-8").read()
    obj = json.loads(raw)
    obj["display"]["icon"] = {"count": 1, "id": "potato_s_t:" + ROOT_ICON}
    obj["criteria"] = {"got": {"trigger": "minecraft:inventory_changed",
                               "conditions": {"items": [{"items": "potato_s_t:" + ROOT_ICON}]}}}
    obj["requirements"] = [["got"]]
    io.open(rootp, "w", encoding="utf-8", newline=u"\n").write(
        json.dumps(obj, ensure_ascii=False, indent=2) + u"\n")
    print(u"  老成就 new_beginning：根节点判据 → %s" % ROOT_ICON)
    for name, newparent in sorted(REPARENT.items()):
        p = os.path.join(ROOT, ADIR, name + u".json")
        obj = json.loads(io.open(p, encoding="utf-8").read())
        old = obj.get("parent")
        if old == newparent:
            print(u"  老成就 %s：父链已经是 %s" % (name, newparent))
            continue
        obj["parent"] = newparent
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(obj, ensure_ascii=False, indent=2) + u"\n")
        print(u"  老成就 %s：父链 %s → %s" % (name, old, newparent))

    # ---- 3) 四语言
    for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
        loc_key = {"zh_cn": "zh", "en_us": "en", "ja_jp": "ja", "ru_ru": "ru"}[loc]
        p = os.path.join(ROOT, LANG, loc + ".json")
        raw = io.open(p, encoding="utf-8").read()
        data = json.loads(raw)
        table = {}
        for n in NODES:
            t, d = n[loc_key]
            table["advancements.potato_s_t.%s.title" % n["id"]] = t
            table["advancements.potato_s_t.%s.description" % n["id"]] = d
        # 老根节点的说明换成本轮文案（标题不动）—— 这是**改**已有键，所以先从表里拿出来，
        # 免得被"键已存在"的重复检查误伤
        new_root_desc = {
            "zh_cn": u"做出微型粉碎机 —— 它把矿石磨成粉，是后面一切的地基",
            "en_us": "Build a Micro Crusher - it grinds ore into dust, and everything else is built on that",
            "ja_jp": u"微粉砕機を作ろう —— 鉱石を粉にする、すべての土台",
            "ru_ru": "Соберите микро-дробилку — она измельчает руду в пыль, и на этом держится всё остальное",
        }[loc]
        dup = [k for k in table if k in data]
        # 重跑友好：已经有**同值**的键就当"已经写好了"跳过；只有**值不一样**才算冲突。
        # （本轮的探针改过一次判据写法，脚本重跑过好几遍，所以这里必须认得出"我就是我"。）
        same = [k for k in dup if data[k] == table[k]]
        conflict = [k for k in dup if data[k] != table[k]]
        if conflict:
            fails.append(u"%s：这些键已经有**别的值**了 %s" % (loc, [(k, data[k], table[k]) for k in conflict]))
            continue
        for k in same:
            table.pop(k)
        if same:
            print(u"  [--]   %-12s %d 个键已经在盘上且同值，跳过" % (loc + u".json", len(same)))
        root_key = u"advancements.potato_s_t.new_beginning.description"
        root_done = data.get(root_key) == new_root_desc
        if not table and root_done:
            print(u"  [OK]   %-12s 键数 %d 已经到位，无需改动" % (loc + u".json", len(data)))
            continue
        if u"advancements.potato_s_t.new_beginning.title" not in data:
            fails.append(u"%s：连老根节点的标题键都不在" % loc)
            continue
        lines = raw.split(u"\n")
        old_line = None
        for i, l in enumerate(lines):
            if l.strip().startswith(u'"advancements.potato_s_t.new_beginning.description"'):
                old_line = i
                break
        if old_line is None:
            fails.append(u"%s：找不到老根节点的说明行" % loc)
            continue
        if not root_done:
            lines[old_line] = u'    %s:  %s,' % (json.dumps(root_key, ensure_ascii=False),
                                                 json.dumps(new_root_desc, ensure_ascii=False))
        last = max(i for i, l in enumerate(lines) if l.strip().startswith(u'"'))
        if table:
            if not lines[last].rstrip().endswith(u","):
                lines[last] = lines[last].rstrip() + u","
            block = [u'    %s:  %s,' % (json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False))
                     for k, v in sorted(table.items())]
            block[-1] = block[-1][:-1]
            lines[last + 1:last + 1] = block
        text = u"\n".join(lines)
        back = json.loads(text)
        if len(back) != len(data) + len(table):
            fails.append(u"%s：回读键数 %d ≠ %d" % (loc, len(back), len(data) + len(table)))
            continue
        if back.get(root_key) != new_root_desc:
            fails.append(u"%s：回读后老根节点的说明还是旧的" % loc)
            continue
        io.open(p, "w", encoding="utf-8", newline=u"").write(text)
        print(u"  [OK]   %-12s %d → %d 键（+%d）" % (loc + u".json", len(data), len(back), len(table)))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
