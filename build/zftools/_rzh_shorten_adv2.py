# -*- coding: utf-8 -*-
r"""_rzh_shorten_adv2.py —— 第二轮瘦身：英文 / 俄文 / 日文再收一点。

第一轮（`_rzh_shorten_adv.py`）已把中文压到位，但 en 仍 171~209、ru 127~188。
本轮只对 en_us / ru_ru / ja_jp 做**更紧的替换**，并且**只在新值确实更短时才应用**
（免得手滑把某条改长了）。中文不动。
"""
import io
import json
import sys

LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"

TIGHTER = {
    u"en_us": {
        u"oil_pump": u"An Oil Pump in an Ocean Oilfield: the chain in the water below is the well depth n - 8n\u00b2+80n FE/t in, 10n mB/s out, 25B tank out only",
        u"starfall": u"Right-click to cast a Starfall: 4 durability, one per throw, a 30 s countdown you can cancel in the first 10 s - then a meteor at y=200, power 7~20, fire and 3 Raw Vibranium",
        u"fluid_logistics": u"The Fluid Pump stores nothing, only moves fluid into a destination that accepts it, and can drain sources; the Exchanger turns an empty bucket into the one matching the 1000 mB in its tank",
        u"lithium_battery_plant": u"Sulfuric Acid in (1 mB/tick, 600 mB a batch) and one item per slot: raw manganese or aluminium, nickel, lithium carbonate, cobalt - a Lithium Battery Part every 30 s",
        u"star_steel": u"Alloy Smelter, one batch: Netherite + 4 High Carbon Steel + Cobalt + Silver + Copper + Deepslate Cobalt Ore + Ender Crystal -> 3 Star Steel Ingots (12000 FE/t, 30 s)",
        u"salt": u"The Salt Dryer needs no input - just leave it out for Sea Salt, faster with power; salt + water in the Electrolyzer gives chlorine, or 64 salt in the Decomposer for sodium chloride in 40 s",
        u"lithium_battery": u"Paper + Capacitor + Common Metal Block + Lithium Battery Part -> Ternary Polymer Lithium Battery; 4M FE per block, stack it like a pyramid, terminals on the bottom only",
        u"wiring": u"Terminal Blocks are your wiring: link two with a Copper Wire Spool (the Power Cable Spool for the power network), sneak-right-click to switch input / output",
        u"blast_furnace": u"A 3\u00d73\u00d73 multiblock: put a vanilla blast furnace or the controller on the front and wall it in, then right-click the controller for a self-check",
    },
    u"ru_ru": {
        u"oil_pump": u"Нефтевышка в морском месторождении: цепь в воде под ней — глубина n; 8n\u00b2+80n FE/т, 10n mB/с, бак 25B только отдаёт",
        u"starfall": u"ПКМ бросает Звёздный груз: прочность 4, по 1 за бросок, отсчёт 30 с можно отменить в первые 10 с — затем метеорит с y=200, сила 7~20, огонь и 3 сырого вибраниума",
        u"fluid_logistics": u"Насос ничего не хранит: лишь перекачивает жидкость в принимающий приёмник и умеет выкачивать источники; обменник делает из пустого ведра ведро под 1000 mB из бака",
        u"lithium_battery_plant": u"Серная кислота (1 mB/тик, 600 mB на партию) и по предмету в слот: марганец или алюминий, никель, карбонат лития, кобальт — деталь за 30 с",
        u"star_steel": u"Плавильня, партия: незерит + 4 высокоуглеродистой стали + кобальт + серебро + медь + глубинная кобальтовая руда + кристалл Края → 3 слитка звёздной стали (12000 FE/т, 30 с)",
        u"salt": u"Солесушилке не нужно сырьё: даёт морскую соль сама, с энергией быстрее; соль с водой в электролизёре даёт хлор, а 64 соли в разлагателе — хлорид натрия за 40 с",
        u"lithium_battery": u"Бумага + конденсатор + обычный металлический блок + деталь → литиевая батарея; 4M FE на блок, складывается пирамидой, клеммы только снизу",
        u"wiring": u"Клеммные блоки — это проводка: соедините два катушкой с медным проводом (для сети — катушкой силового кабеля), ПКМ с приседом переключает вход / выход",
        u"blast_furnace": u"Мультиблок 3\u00d73\u00d73: на переднюю опору — доменная печь или контроллер, обнести корпусом, затем ПКМ по контроллеру для самопроверки",
    },
    u"ja_jp": {
        u"star_steel": u"合金精錬炉 1 バッチ：ネザライト + 高炭素鋼 4 + コバルト + 銀 + 銅 + 深層コバルト鉱石 + エンダークリスタル → 星燦鋼 3 個（12000 FE/t で 30 秒）",
        u"starfall": u"右クリックで星軌墜を投げる：耐久 4、1 回で 1 消費、30 秒のカウントダウンは最初の 10 秒なら取消可。隕石は y=200 から、威力 7~20、延焼と粗ビブラニウム 3 個",
        u"lithium_battery_plant": u"硫酸を通し（毎 tick 1 mB、1 バッチ 600 mB）、4 スロットに 1 つずつ：粗マンガンか粗アルミ、ニッケル、炭酸リチウム、コバルト → 30 秒で電池部品 1 個",
    },
}

fails = []
raw = {}
for loc in [u"en_us", u"ru_ru", u"ja_jp"]:
    raw[loc] = io.open(LANG % loc, encoding=u"utf-8", newline=u"").read()

plan = []
for loc, table in TIGHTER.items():
    for nid, new in table.items():
        key = u'"advancements.potato_s_t.%s.description"' % nid
        i = raw[loc].find(key)
        if i < 0:
            fails.append(u"%s / %s：找不到键" % (loc, nid))
            continue
        c = raw[loc].index(u":", i)
        j = raw[loc].index(u'"', c + 1)
        k = j + 1
        while True:
            if raw[loc][k] == u"\\":
                k += 2
                continue
            if raw[loc][k] == u'"':
                break
            k += 1
        old_lit = raw[loc][j:k + 1]
        old_val = json.loads(old_lit)
        new_lit = json.dumps(new, ensure_ascii=False)
        if old_val == new:
            continue
        if len(new) >= len(old_val):
            print(u"[--] %s / %-24s 新值没更短（%d ≥ %d），跳过" % (loc, nid, len(new), len(old_val)))
            continue
        n = raw[loc].count(old_lit)
        if n != 1:
            fails.append(u"%s / %s：老值出现 %d 次" % (loc, nid, n))
            continue
        plan.append((loc, old_lit, new_lit, nid, len(old_val), len(new)))

if fails:
    print(u"写前自检挂了，没落盘：")
    for f in fails:
        print(u"  !! " + f)
    sys.exit(1)

print(u"%-8s %-24s %s" % (u"语言", u"节点", u"字数 老 → 新"))
for loc in [u"en_us", u"ru_ru", u"ja_jp"]:
    text = raw[loc]
    for (l, old_lit, new_lit, nid, lo, ln) in [p for p in plan if p[0] == loc]:
        text = text.replace(old_lit, new_lit, 1)
        print(u"%-8s %-24s %3d → %3d" % (loc, nid, lo, ln))
    if text != raw[loc]:
        assert len(json.loads(text)) == len(json.loads(raw[loc])), u"键数变了"
        io.open(LANG % loc, u"w", encoding=u"utf-8", newline=u"").write(text)

print(u"\n第二轮改了 %d 处" % len(plan))
