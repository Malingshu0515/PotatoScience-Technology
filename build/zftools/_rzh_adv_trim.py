# -*- coding: utf-8 -*-
r"""_rzh_adv_trim.py —— 成就说明精简（四语一起改）。

用户口径（本轮）：「成就……润色一下 精简一下 然后再检查一遍有没有流水账」。
判别口径沿用前几轮定下的那一条：

  **删**：JEI 里已有的配方表 / 配方材料清单 / 与同句重复的数值
  **留**：机制、触发条件、用法、该成就独有的数值（8n²+80n、7200 FE、16134 FE/t、
          7~20 威力……），以及告警

⚠⚠ 旧值**不在本文件里手抄** —— 这是踩过坑之后改的写法。
   本文件只写"新值"（`NEW`），旧值由 `_rzh_adv_now.json`（`_rzh_adv_dump_json.py`
   从盘上现导）提供。理由：平行线随时会动这些键，手抄旧值 = 抄一次多一次抄错的
   机会，而守卫只会告诉你"不符"，不会告诉你"盘上现在到底是什么"。
   顺带一提，旧值用 JSON 字面量而不是手写 Python 串，还免掉了引号与转义的坑。

用法：
    python build/zftools/_rzh_adv_dump_json.py     # 先导盘上现况
    python build/zftools/_rzh_adv_trim.py          # 再改
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
NOW = os.path.join(HERE, u"_rzh_adv_now.json")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

# ---------------------------------------------------------------------------
# 新值：`节点 -> {语言: 新说明}`
# 只有**要改**的语言才写进来；没写的语言不动。
# ---------------------------------------------------------------------------
NEW = {
    u"acid": {
        u"zh_cn": "碳酸、硝酸、硫酸、盐酸 —— 四种酸，一台机器",
        u"en_us": "Carbonic, nitric, sulfuric, hydrochloric: four acids, one machine",
        u"ja_jp": "炭酸・硝酸・硫酸・塩酸 —— 4 つの酸を 1 台で",
        u"ru_ru": "Карбоновая, азотная, серная, соляная: четыре кислоты на одной машине",
    },
    u"alloy_smelter": {
        u"zh_cn": "主控 + 接线口 + 炉体 —— 合金线的起点：轻质与硬质钛合金都从这儿出",
        u"en_us": "Controller + port + furnace body - where the alloy line begins: light and hard titanium alloy both come from here",
        u"ja_jp": "コントローラー + 接続口 + 炉体 —— 合金ラインの出発点。軽質・硬質チタン合金はここから",
        u"ru_ru": "Контроллер, порт и корпус — начало линии сплавов: лёгкий и твёрдый титановый сплав родом отсюда",
    },
    u"capacitor": {
        u"zh_cn": "铜锭 + 铝板 + 银板 = 电容；电力高炉、合金炉、太阳能板都要它",
        u"en_us": "Copper Ingot + Aluminum Plate + Silver Plate = Capacitor; the Electric Blast Furnace, Alloy Smelter and Solar Panel all want one",
        u"ja_jp": "銅インゴット + アルミニウム板 + 銀板 = コンデンサ。電力高炉・合金精錬炉・ソーラーパネルが欲しがります",
        u"ru_ru": "Медный слиток, алюминиевая и серебряная пластины = конденсатор; его хотят доменная печь, плавильня сплавов и солнечная панель",
    },
    u"clean_energy": {
        u"zh_cn": "白天发电，越靠正午越强；雨天只剩 60%，雷暴只剩 20%",
        u"en_us": "Daylight only, strongest at noon - rain cuts it to 60%, a thunderstorm to 20%",
        u"ja_jp": "昼だけ発電し、正午に最も強い。雨は 60%、雷雨は 20% まで落ちます",
        u"ru_ru": "Только днём, сильнее всего в полдень: дождь режет до 60%, гроза — до 20%",
    },
    u"combustion": {
        u"zh_cn": "烧一份燃料 + 10 mB 氧气出二氧化碳；拿原木去烧还能顺手得到木炭",
        u"en_us": "Burn a piece of fuel with 10 mB of oxygen for carbon dioxide, and logs give charcoal on the side",
        u"ja_jp": "燃料 1 つと酸素 10 mB で二酸化炭素。原木を燃やせば木炭もついでに手に入ります",
        u"ru_ru": "Единица топлива и 10 mB кислорода дают углекислый газ, а брёвна — ещё и древесный уголь попутно",
    },
    u"crushing": {
        u"zh_cn": "粉碎机把锭和矿磨成粉；铁粉 + 碳粉就是钢的原料",
        u"en_us": "The crusher grinds ingots and ore into dust; iron dust plus carbon dust is how steel begins",
        u"ja_jp": "粉砕機がインゴットと鉱石を粉にします。鉄粉 + 炭素粉末が鋼の始まりです",
        u"ru_ru": "Дробилка мелет слитки и руду в пыль: железная пыль и угольная пыль — вот с чего начинается сталь",
    },
    u"diesel_generator": {
        u"zh_cn": "控制器 + 两台低级发电机 + 燃烧反应室 + 流体泵：3×5×2、30 格。每 tick 烧 1 mB 柴油发 7200 FE",
        u"en_us": "Controller, two Low Generators, a Combustion Chamber and a Fluid Pump in 3x5x2, 30 blocks. 1 mB of diesel per tick makes 7200 FE",
        u"ja_jp": "コントローラー + 低級発電機 2 台 + 燃焼反応室 + 流体ポンプで 3×5×2・30 ブロック。毎 tick ディーゼル 1 mB で 7200 FE",
        u"ru_ru": "Контроллер, два слабых генератора, камера сгорания и насос — 3x5x2, 30 блоков. 1 mB дизеля за тик даёт 7200 FE",
    },
    u"distillation": {
        u"zh_cn": "主控 + 操作器：把原油分成柴油、汽油、石脑油、液化石油气和沥青",
        u"en_us": "Controller + Processor: split crude oil into diesel, gasoline, naphtha, LPG and bitumen",
    },
    u"electrolyzer": {
        u"zh_cn": "电解器：水 = 氧气 + 氢气；往电解质槽里放一块海盐，就改产氯气",
        u"en_us": "Electrolyzer: water becomes oxygen and hydrogen; drop sea salt into the electrolyte slot and it makes chlorine instead",
        u"ja_jp": "電解装置：水が酸素と水素に。電解質スロットに海塩を 1 つ入れると塩素に切り替わります",
        u"ru_ru": "Электролизёр: вода даёт кислород и водород; положите в слот электролита морскую соль — пойдёт хлор",
    },
    u"first_power": {
        u"zh_cn": "塞煤或木炭发电，再用端子把电送到机器旁 —— 便宜、够用、30 秒一块",
        u"en_us": "Feed it coal or charcoal and run the power to your machines with terminals - cheap, good enough, 30 seconds a piece",
        u"ja_jp": "石炭か木炭を入れて発電し、端子で機械のそばまで電気を送ります —— 安くて十分、1 個 30 秒",
        u"ru_ru": "Закиньте уголь или древесный уголь и проведите энергию к машинам клеммами — дёшево, достаточно, 30 секунд на единицу",
    },
    u"fluid_logistics": {
        u"zh_cn": u"流体泵不存液体 —— 送得进就送，也能抽干液体源；容器换流器拿空桶换出罐里 1000 mB 对应的桶",
        u"en_us": u"The Fluid Pump stores nothing - it feeds what will take the fluid and can drain sources dry; the Exchanger turns an empty bucket into one of the fluid its tank holds, 1000 mB at a time",
        u"ja_jp": u"流体ポンプは液体を溜めません —— 受け取れる先へ送るだけ（液体源の汲み上げも可）。流体交換器は空バケツを、タンク内 1000 mB に対応するバケツに変えます",
        u"ru_ru": u"Насос ничего не хранит: льёт туда, где примут, и умеет выкачивать источники досуха; обменник делает из пустого ведра ведро жидкости из бака — по 1000 mB за раз",
    },
    u"fuel": {
        u"zh_cn": "两种液体燃料，都是喂燃烧反应室的：柴油给 1200 动力，汽油 1000",
        u"en_us": "Two liquid fuels for the Combustion Chamber: diesel gives 1200 power, gasoline 1000",
        u"ja_jp": "2 種の液体燃料はどちらも燃焼反応室用：ディーゼルは 1200 動力、ガソリンは 1000",
        u"ru_ru": "Два жидких топлива для камеры сгорания: дизель даёт 1200 мощности, бензин — 1000",
    },
    u"gas_handling": {
        u"zh_cn": "气罐只装气体、油桶只装液体；两者都靠灌装机灌",
        u"en_us": "Gas tanks take gases, oil buckets take liquids; the Filling Machine fills both",
        u"ja_jp": "ガスタンクは気体専用、オイルバケツは液体専用。どちらも充填機で詰めます",
        u"ru_ru": "Баллоны — под газы, нефтяные вёдра — под жидкости; и то и другое наполняет разливочная машина",
    },
    u"light_alloy": {
        u"en_us": "Aluminum Ingot + Titanium Ingot + Silver Ingot -> Light Titanium Alloy (Alloy Smelter, one 30-second batch)",
        u"ja_jp": "アルミニウム + チタン + 銀の各インゴット → 軽質チタン合金（合金精錬炉、1 バッチ 30 秒）",
        u"ru_ru": "Алюминиевый, титановый и серебряный слитки → лёгкий титановый сплав (плавильня, партия за 30 секунд)",
    },
    u"lithium_battery": {
        u"en_us": "4M FE apiece, stacked like a pyramid, terminals on the bottom face only",
        u"ja_jp": "1 ブロック 4M FE。ピラミッドのように積めます。端子を付けられるのは底面だけ",
        u"ru_ru": "4M FE на блок, ставится пирамидой; клеммы — только на нижнюю грань",
    },
    u"lithium_battery_plant": {
        u"zh_cn": "四样原料各占一槽，通入硫酸：30 秒出一件锂电池元件（这台机器不耗电）",
        u"en_us": "Four inputs, one per slot, fed with sulfuric acid: one Lithium Battery Part every 30 seconds (no power needed)",
        u"ja_jp": "4 つの原料を 1 スロットずつ、硫酸を通して：30 秒で電池部品 1 個（電力は不要）",
        u"ru_ru": "Четыре входа по слотам и серная кислота: деталь раз в 30 секунд (энергия не нужна)",
    },
    u"oil": {
        u"zh_cn": "拎着空桶去找一处地表油田，舀一桶原油回来（空桶不算数）",
        u"en_us": "Take an empty bucket to a surface oilfield and scoop up crude oil (an empty bucket does not count)",
        u"ja_jp": "空のバケツを持って地表油田を探し、原油を汲んできましょう（空のバケツは無効）",
        u"ru_ru": "Возьмите пустое ведро, найдите наземное месторождение и зачерпните сырой нефти (пустое ведро не считается)",
    },
    u"oil_pump": {
        u"zh_cn": "站在海洋油田、正下方泡水的锁链就是井深 n：耗电 8n²+80n FE/t，出油 10n mB/s",
        u"en_us": "Stand it in an Ocean Oilfield with a waterlogged chain below: that count is your well depth n, drawing 8n²+80n FE/t for 10n mB/s",
        u"ja_jp": "海洋油田に設置し、真下の含水チェーンが井戸の深さ n：消費 8n²+80n FE/t、産油 10n mB/s",
        u"ru_ru": "Поставьте в морском месторождении: цепь с водой под ним — глубина n, расход 8n²+80n FE/т при добыче 10n mB/с",
    },
    u"pressing": {
        u"zh_cn": "液压机把锭压成板 —— 板是几乎所有机器的通用零件（3 秒一块）",
        u"en_us": "The hydraulic press turns ingots into plates - the common part of nearly every machine (3 seconds each)",
        u"ja_jp": "油圧プレスがインゴットを板に —— 板はほぼすべての機械の共通部品（1 枚 3 秒）",
        u"ru_ru": "Пресс превращает слитки в пластины — общая деталь почти любой машины (3 секунды на штуку)",
    },
    u"salt": {
        u"zh_cn": "晒盐机摆着就出海盐、通电更快；海盐丢进电解器出氯气，交给盐分解器则出氯化钠",
        u"en_us": "The Salt Dryer needs no input and just makes sea salt, faster with power; sea salt becomes chlorine in the Electrolyzer, or sodium chloride in the Salt Decomposer",
        u"ja_jp": "塩乾燥機は放置で海塩ができ、通電すると速くなります。海塩は電解装置で塩素に、塩分解装置で塩化ナトリウムに",
        u"ru_ru": "Сушилке для соли сырьё не нужно: морская соль идёт сама, с энергией быстрее; электролизёр даёт из неё хлор, солеразлагатель — хлорид натрия",
    },
    u"silver_wire": {
        u"zh_cn": "银线一条能跑 16134 FE/t（铜线只有 2048）—— 端子按接到的最高档伸缩",
        u"en_us": "A line of silver wire carries 16134 FE/t where copper manages only 2048; terminals scale to the highest tier attached",
        u"ja_jp": "銀線は 1 本 16134 FE/t（銅線は 2048 のみ）。端子は繋がった中で一番高い等級に合わせて伸縮します",
        u"ru_ru": "Линия из серебряного провода тянет 16134 FE/т (медный — лишь 2048), а клеммы подстраиваются под высший класс",
    },
    u"stable_block": {
        u"zh_cn": "高碳钢 / 硬质钛合金 / 金块 摆成九宫格 —— 酸性反应室要它",
        u"en_us": "High Carbon Steel, Hard Titanium Alloy and a Gold Block in a nine-cell grid - the Acidic Reaction Chamber wants one",
        u"ja_jp": "高炭素鋼 / 硬質チタン合金 / 金ブロックを 3×3 に —— 酸性反応室が欲しがります",
        u"ru_ru": "Высокоуглеродистая сталь, твёрдый титановый сплав и золотой блок сеткой 3×3 — нужен кислотной камере",
    },
    u"star_chart_tome": {
        u"zh_cn": "右键依次换过四片星空、第五次回到原版；潜行右键往回切 —— 只有你自己看得见",
        u"en_us": "Right-click to cycle four skies and a fifth to return to vanilla; sneak-right-click goes back - and only you see it",
        u"ja_jp": "右クリックで 4 つの星空を順に切り替え、5 回目でバニラに戻ります。スニーク右クリックで逆送り —— 見えるのは自分だけ",
        u"ru_ru": "ПКМ меняет четыре неба по кругу, пятое возвращает ванильное, ПКМ с приседом — назад; и видите это только вы",
    },
    u"star_steel": {
        u"zh_cn": "合金炉里下界合金锭 + 高碳钢 + 钴 + 银 + 铜，另耗 1 深层钴矿石和 1 末影水晶，一炉出 3 个星璨钢锭",
        u"en_us": "One Alloy Smelter batch takes a Netherite Ingot with high carbon steel, cobalt, silver and copper, plus a deepslate cobalt ore and an end crystal, and yields 3 Star Steel Ingots",
        u"ja_jp": "合金精錬炉 1 バッチ：ネザライト + 高炭素鋼 + コバルト + 銀 + 銅、さらに深層コバルト鉱石とエンダークリスタル → 星燦鋼 3 個",
        u"ru_ru": "Партия в плавильне: незерит с высокоуглеродистой сталью, кобальтом, серебром и медью, плюс глубинная кобальтовая руда и кристалл Края → 3 слитка звёздной стали",
    },
    u"star_steel_armor": {
        u"zh_cn": "四件全穿在身上，就是本模组最硬的一套；夜里还不磨损",
        u"en_us": "Wear the whole set for the toughest armour in the mod - and it does not wear down at night",
        u"ja_jp": "4 部位そろえば本 MOD 最硬の一揃い。しかも夜は摩耗しません",
        u"ru_ru": "Наденьте все четыре части — это самый прочный комплект в моде, и ночью он не изнашивается",
    },
    u"star_steel_tools": {
        u"zh_cn": "剑 / 斧 / 锹 / 镐 / 锄，图纸照原版、材料换成星璨钢；夜晚采掘与攻击都不磨损耐久",
        u"en_us": "Sword, axe, shovel, pickaxe and hoe - vanilla patterns in Star Steel; at night, mining and attacking cost no durability",
        u"ja_jp": "剣 / 斧 / シャベル / ツルハシ / クワ —— レシピはバニラのまま材料を星燦鋼に。夜間は採掘と攻撃で耐久を消費しません",
        u"ru_ru": "Меч, топор, лопата, кирка и мотыга — схемы как в ванилле, но из звёздной стали; ночью добыча и атаки не тратят прочность",
    },
    u"steel": {
        u"zh_cn": "铁粉 + 碳粉丢进电力高炉 → 高碳钢；钢材是后面几乎所有东西的骨架",
        u"en_us": "Iron dust with carbon dust into the Electric Blast Furnace gives High Carbon Steel - the skeleton of nearly everything after this",
        u"ja_jp": "鉄粉 + 炭素粉末を電力高炉へ → 高炭素鋼。鋼はこの先ほぼすべての骨格です",
        u"ru_ru": "Железная пыль с угольной пылью в доменной печи дают высокоуглеродистую сталь — скелет почти всего дальнейшего",
    },
    u"titanium": {
        u"zh_cn": "粗钛先粉碎成钛粉，钛粉再进电力高炉 → 钛锭",
        u"en_us": "Crush raw titanium into dust first, then smelt that dust in the Electric Blast Furnace",
        u"ja_jp": "粗チタンはまず粉砕してチタン粉に。その粉を電力高炉へ → チタンインゴット",
        u"ru_ru": "Сначала раздробите сырой титан в пыль, потом плавьте пыль в доменной печи",
    },
    u"stronger_power": {
        u"zh_cn": "电生磁，磁生电……别问导线为什么能传动力，能用就行",
        u"en_us": "Electricity makes magnetism, magnetism makes electricity... do not ask why a wire carries power, just enjoy it",
        u"ja_jp": "電気が磁気を、磁気が電気を……なぜ導線が動力を運べるのかは聞かないで。使えれば正義です",
        u"ru_ru": "Электричество рождает магнетизм, магнетизм — электричество... не спрашивайте, как провод передаёт энергию: работает — и ладно",
    },
    u"titanium_armor": {
        u"zh_cn": "想要振金套，就得先有它 —— 锻造台拿钛合金四件各加一个振金锭换出来",
        u"en_us": "You cannot reach vibranium without it: the smithing table upgrades each titanium piece with a Vibranium Ingot",
        u"ja_jp": "ヴィブラニウムの前にこれが必要：鍛冶台で 4 部位それぞれにヴィブラニウムインゴット 1 個を足して作り替えます",
        u"ru_ru": "Без него не будет вибраниума: кузнечный стол улучшает каждую деталь одним слитком вибраниума",
    },
    u"vibranium": {
        u"zh_cn": "合金炉里硬质钛合金 + 热力金属 + 高碳钢 + 银 + 金，另耗 1 粗振金和 2 下界合金碎片，一炉出一个",
        u"en_us": "One Alloy Smelter batch takes hard titanium alloy with thermal metal, high carbon steel, silver and gold, plus a raw vibranium and two netherite scraps, for one ingot",
        u"ja_jp": "合金精錬炉 1 バッチ：硬質チタン合金 + 熱力金属 + 高炭素鋼 + 銀 + 金、さらに粗ヴィブラニウムとネザライト片 → 1 個",
        u"ru_ru": "Партия в плавильне: твёрдый титановый сплав с термальным металлом, высокоуглеродистой сталью, серебром и золотом, плюс сырой вибраниум и два незеритовых обломка → один слиток",
    },
    u"vibranium_armor": {
        u"zh_cn": "锻造台：钛合金四件各加 1 个振金锭。穿满四件：无限耐久、弹射物免疫并反弹、爆炸减半、免击退、常驻抗性提升 I、免摔落，受击时 10% 概率原样奉还",
        u"en_us": "Smithing table: each titanium piece + 1 Vibranium Ingot. All four: unbreakable, projectiles reflected, explosions halved, no knockback, Resistance I, no fall damage, and a 10% chance to return any hit as it came",
        u"ja_jp": "鍛冶台：チタン合金の 4 部位にそれぞれヴィブラニウムインゴット 1 個。4 つ揃えると：耐久無限、投射物を跳ね返し、爆発は半減、ノックバック無効、常時耐性 I、落下無効、被弾時に 10% でその一撃をそのまま返します",
        u"ru_ru": "Кузнечный стол: к каждой титановой детали + 1 слиток вибраниума. Все четыре: неразрушимо, снаряды отражаются, взрывы вдвое слабее, нет отбрасывания, сопротивление I, нет урона от падения и 10% шанс вернуть весь удар",
    },
    # 这两条本来不在第一批里（它们不是配方表），但字数偏大：
    # star_steel_slash 82 字里有一半是"沿途每个敌人各吃 12 点伤害并被照亮 5 秒"，
    # 那两句在剑自己的 tooltip 里逐条写着；成就只要说清"怎么放、代价多少"。
    u"star_steel_slash": {
        u"zh_cn": u"拿星璨钢剑 Shift + 右键，一道 8 格长的星辉剑气；斩中生物即达成（100 耐久、15 秒冷却）",
        u"en_us": u"Shift + right-click a Star Steel Sword for an 8-block starlight slash, and finish a mob with it (100 durability, 15 s cooldown)",
        u"ja_jp": u"星燦鋼の剣で Shift + 右クリック、長さ 8 ブロックの星輝斬。これでモブを仕留めれば達成（耐久 100・クールダウン 15 秒）",
        u"ru_ru": u"Shift + ПКМ мечом из звёздной стали — разрез длиной 8 блоков; добейте им моба (100 прочности, перезарядка 15 с)",
    },
    u"starfall": {
        u"zh_cn": u"右键甩出星轨坠：30 秒倒计时、前 10 秒可取消，陨石从 y=200 砸下，7~20 威力带火",
        u"en_us": u"Right-click the pendant: a 30-second countdown, cancellable in the first 10, then a meteor falls from y=200 at power 7-20 with fire",
        u"ja_jp": u"右クリックでペンダントを放つ：30 秒のカウントダウン、最初の 10 秒は取消可。隕石は y=200 から威力 7〜20・炎上ありで落下",
        u"ru_ru": u"ПКМ подвеской: отсчёт 30 секунд, первые 10 можно отменить, затем метеорит падает с y=200 силой 7–20 с огнём",
    },
    u"wiring": {
        u"zh_cn": "接线端子就是电线：铜线轴右键两个端子连起来，潜行右键切换输入 / 输出",
        u"en_us": "Terminals are the wires: link two with a spool in hand, sneak-right-click toggles input/output",
        u"ja_jp": "端子はそのまま電線です：スプールで 2 つの端子を右クリックして繋ぎ、スニーク右クリックで入力 / 出力を切り替えます",
        u"ru_ru": "Клеммы и есть провода: свяжите две катушкой в руке, ПКМ с приседом переключает вход и выход",
    },
}


def load(loc):
    p = os.path.join(LANGDIR, loc + u".json")
    with io.open(p, encoding=u"utf-8", newline=u"") as f:
        text = f.read()
    return p, text, json.loads(text)


def line_index(text):
    idx = {}
    for n, line in enumerate(text.split(u"\n")):
        s = line.lstrip()
        if s.startswith(u'"'):
            end = s.find(u'":')
            if end >= 0:
                idx[s[1:end]] = n
    return idx


def main():
    if not os.path.exists(NOW):
        raise SystemExit(u"[拒绝] 缺 %s，先跑 _rzh_adv_dump_json.py" % NOW)
    with io.open(NOW, encoding=u"utf-8") as f:
        now = json.load(f)

    # 先全量校验，一个都不落盘
    plans = {}
    noop = []
    for node, per in sorted(NEW.items()):
        if node not in now:
            raise SystemExit(u"[拒绝] 盘上快照里没有节点 %s" % node)
        for loc, new in sorted(per.items()):
            old = now[node][loc]
            if old == new:
                # 「新旧一样」= 这条编辑没有意义。**跳过并计数**，不再整批拒绝：
                # 快照每刷新一次就可能多出几条这样的（我刚把某句改短，盘上就成了新值），
                # 为它们整天报错只会掩盖真正的问题。报告里照样列出来，人得看一眼。
                noop.append((node, loc))
                continue
            plans.setdefault(loc, []).append((node, old, new))
    if noop:
        # ⚠ 别在 print 里用 ⚠ 之类的符号：Windows 控制台是 GBK，直接
        #   UnicodeEncodeError 把整个脚本打死（本会话已经栽过一次）。
        print(u"[注意] %d 条与盘上现况相同，跳过：" % len(noop))
        for node, loc in noop:
            print(u"    %-24s %s" % (node, loc))

    total_old = total_new = 0
    for loc, items in sorted(plans.items()):
        path, text, data = load(loc)
        lines = text.split(u"\n")
        idx = line_index(text)
        ops = []
        for node, old, new in items:
            key = u"advancements.potato_s_t.%s.description" % node
            if data.get(key) == new:
                continue        # 幂等：这一条已经落过盘了（快照可能已被刷新）
            if data.get(key) != old:
                raise SystemExit(u"[拒绝] %s 的 %s 既不是快照里的旧值、也不是新值\n  盘上: %r"
                                 % (loc, key, data.get(key)))
            ops.append((idx[key], key, node, old, new))
        for lineno, key, node, old, new in ops:
            lines[lineno] = u'  %s: %s,' % (json.dumps(key, ensure_ascii=False),
                                            json.dumps(new, ensure_ascii=False))
        out = u"\n".join(lines)
        if u"\r" in out:
            raise SystemExit(u"[拒绝] %s 出现 CR" % loc)
        json.loads(out)
        io.open(path, u"w", encoding=u"utf-8", newline=u"\n").write(out)
        print(u"\n===== %s：%d 条 =====" % (loc, len(ops)))
        for _, _, node, old, new in sorted(ops, key=lambda x: x[2]):
            total_old += len(old)
            total_new += len(new)
            print(u"  %-24s %3d -> %3d 字  (-%d)" % (node, len(old), len(new),
                                                     len(old) - len(new)))

    # ---- 写后复读 ----
    print(u"\n===== 写后复读 =====")
    bad = 0
    for loc, items in sorted(plans.items()):
        data = load(loc)[2]
        for node, old, new in items:
            key = u"advancements.potato_s_t.%s.description" % node
            if data.get(key) != new:
                bad += 1
                print(u"[错] %s %s" % (loc, node))
    print(u"复读 %s" % (u"全部就位" if bad == 0 else u"%d 处不符" % bad))

    # ---- 结构 ----
    print(u"\n===== 结构 =====")
    sets = dict((l, set(load(l)[2])) for l in LOCALES)
    base = sets[u"zh_cn"]
    for l in LOCALES:
        ok = sets[l] == base
        if not ok:
            bad += 1
        print(u"%-6s %3d 键  %s" % (l, len(sets[l]), u"与 zh_cn 一致" if ok else u"不一致！"))

    print(u"\n本次涉及 %d 条 × %d 语：%d -> %d 字（-%.0f%%）"
          % (len(NEW), len(plans), total_old, total_new,
             100.0 * (total_old - total_new) / max(1, total_old)))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
