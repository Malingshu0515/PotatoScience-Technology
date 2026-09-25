# -*- coding: utf-8 -*-
r"""_rzh_shorten_adv.py —— 成就说明瘦身：10 条过长文案 × 四语言。

背景：用户反馈「成就介绍太长了」。实测最长的是串行会话新加的 8 条进度线：
      `oil_pump` 中文 168 字 / 英文 374 / 俄文 380 —— 在成就提示框里根本显示不下。

口径：
  · **只改 description 的值，不动任何键** ⇒ 键数仍 448、键集合不变。
  · `_zf117_verify.py` 的 `MUST` 表钉的"必须出现的事实"**一条不许丢**（脚本里自带断言）。
  · 只收长到离谱的 10 条；`alloy_smelter` / `wiring` / `blast_furnace` 只是顺带收尾。

做法：逐条**精确子串替换**（老值 → 新值），每条要求命中恰好 1 次；
      任何一条命中 0 次或 >1 次 ⇒ 打印后**整体不写盘**，避免半途改坏。
"""
import io
import json
import sys

LANG = u"src/main/resources/assets/potato_s_t/lang/%s.json"

NEW = {
    u"oil_pump": {
        u"zh_cn": u"采油机站在海洋油田：正下方泡水的锁链就是井深 n，耗电 8n\u00b2+80n FE/t、出油 10n mB/s，25B 横罐只出不进",
        u"en_us": u"Stand an Oil Pump in an Ocean Oilfield: the chain hanging in the water below is the well depth n - 8n\u00b2+80n FE/t in, 10n mB/s out, and the 25B tank only gives (pump it out)",
        u"ja_jp": u"採油機は海洋油田に設置：真下で水に浸かる鎖が井戸の深さ n。消費 8n\u00b2+80n FE/t、産出 10n mB/s、25B タンクは出すだけ",
        u"ru_ru": u"Ставьте нефтевышку в морском месторождении: цепь в воде под ней — это глубина n; 8n\u00b2+80n FE/т на вход, 10n mB/с на выход, бак 25B только отдаёт",
    },
    u"starfall": {
        u"zh_cn": u"右键甩出星轨坠：4 点耐久、一次扣 1，30 秒倒计时、前 10 秒可取消；陨石从 y=200 砸下，7~20 威力带火，还夹 3 块粗振金",
        u"en_us": u"Right-click to cast a Starfall: 4 durability, 1 per throw, a 30 s countdown you can still cancel in the first 10 s - then a meteor hits from y=200, power 7~20, with fire and 3 Raw Vibranium",
        u"ja_jp": u"右クリックで星軌墜を投げる：耐久 4、1 回で 1 消費、30 秒のカウントダウンは最初の 10 秒なら取消可。隕石は y=200 から落下、威力 7~20 で延焼、粗ビブラニウム 3 個付き",
        u"ru_ru": u"ПКМ бросает Звёздный груз: прочность 4, по 1 за бросок, отсчёт 30 с можно отменить в первые 10 с — потом метеорит с y=200, сила 7~20, с огнём и 3 кусками сырого вибраниума",
    },
    u"fluid_logistics": {
        u"zh_cn": u"流体泵不存液体，只送收得下的目标，也能抽干液体源；容器换流器拿空桶换出罐里 1000 mB 对应的桶",
        u"en_us": u"The Fluid Pump stores nothing, only moves fluid into a destination that accepts it, and can drain fluid sources; the Exchanger turns an empty bucket into the bucket matching the 1000 mB in its tank",
        u"ja_jp": u"流体ポンプは液体を溜めず、受け取れる送り先へ送るだけ（液体源の汲み上げも可）。容器換装器は空バケツを、タンク内 1000 mB に対応するバケツに変える",
        u"ru_ru": u"Насос ничего не хранит: он лишь перекачивает жидкость в приёмник, который её принимает, и умеет выкачивать источники; обменник превращает пустое ведро в ведро под 1000 mB из бака",
    },
    u"lithium_battery_plant": {
        u"zh_cn": u"通硫酸（每 tick 1 mB，一炉 600 mB），四槽各放：粗锰或粗铝、镍、碳酸锂、钴，30 秒出一个锂电池原件",
        u"en_us": u"Sulfuric Acid in (1 mB/tick, 600 mB a batch), then one item per slot: raw manganese or aluminium, nickel, lithium carbonate, cobalt - one Lithium Battery Part every 30 s",
        u"ja_jp": u"硫酸を通し（毎 tick 1 mB、1 バッチ 600 mB）、4 スロットに 1 つずつ：粗マンガンか粗アルミ、ニッケル、炭酸リチウム、コバルト → 30 秒でリチウム電池部品 1 個",
        u"ru_ru": u"Подайте серную кислоту (1 mB/тик, 600 mB на партию) и по одному предмету в слот: марганец или алюминий, никель, карбонат лития, кобальт — деталь за 30 с",
    },
    u"star_steel": {
        u"zh_cn": u"合金炉一炉吃：下界合金锭 + 4 高碳钢 + 钴锭 + 银锭 + 铜锭 + 深层钴矿石 + 末影水晶，出 3 个星璨钢锭（12000 FE/t 满跑 30 秒）",
        u"en_us": u"Alloy Smelter, one batch: Netherite Ingot + 4 High Carbon Steel + Cobalt + Silver + Copper + Deepslate Cobalt Ore + Ender Crystal -> 3 Star Steel Ingots (12000 FE/t for a full 30 s)",
        u"ja_jp": u"合金精錬炉 1 バッチ：ネザライトインゴット + 高炭素鋼 4 + コバルト + 銀 + 銅 + 深層コバルト鉱石 + エンダークリスタル → 星燦鋼インゴット 3 個（12000 FE/t で 30 秒）",
        u"ru_ru": u"Плавильня, партия: слиток незерита + 4 высокоуглеродистой стали + кобальт + серебро + медь + глубинная кобальтовая руда + кристалл Края → 3 слитка звёздной стали (12000 FE/т, 30 с)",
    },
    u"salt": {
        u"zh_cn": u"晒盐机不用喂东西，摆着就出盐、通电更快；海盐丢进电解器加水出氯气，交给盐分解构器则 64 个海盐 40 秒出氯化钠",
        u"en_us": u"The Salt Dryer needs no input - just leave it out and it makes Sea Salt, faster with power; sea salt into the Electrolyzer with water gives chlorine, or 64 of it into the Decomposer for sodium chloride in 40 s",
        u"ja_jp": u"塩乾燥機は何も入れずに放置で海塩ができ、通電すると速くなります。海塩は電解装置で水と一緒に塩素に、塩分解構築器なら海塩 64 個から 40 秒で塩化ナトリウム",
        u"ru_ru": u"Солесушилке не нужно сырьё: просто стоит и даёт морскую соль, с энергией быстрее; соль в электролизёр с водой даёт хлор, а 64 соли в разлагателе — хлорид натрия за 40 с",
    },
    u"lithium_battery": {
        u"zh_cn": u"纸 + 电容 + 一般金属块 + 锂电池原件 → 三元聚合物锂电池；一块存 4M FE，能像搭金字塔那样叠高，只有底面能接线",
        u"en_us": u"Paper + Capacitor + Common Metal Block + Lithium Battery Part -> Ternary Polymer Lithium Battery; 4M FE per block, stack it up like a pyramid, terminals on the bottom face only",
        u"ja_jp": u"紙 + コンデンサ + 一般金属ブロック + リチウム電池部品 → 三元系ポリマーリチウム電池。1 ブロック 4M FE、ピラミッドのように積め、端子は底面のみ",
        u"ru_ru": u"Бумага + конденсатор + обычный металлический блок + деталь → литиевая батарея; 4M FE на блок, складывается пирамидой, клеммы только снизу",
    },
    u"alloy_smelter": {
        u"zh_cn": u"主控 + 电源端口 + 炉体：三种金属板 + 电容 + 加热装置 + 散热装置 —— 合金线的起点",
        u"en_us": u"Controller + power port + furnace body: three metal plates + a capacitor + a heater + a heat sink - where the alloy line begins",
        u"ja_jp": u"コントローラー + 電源ポート + 炉体：3 種の金属板 + コンデンサ + 加熱装置 + 放熱装置 —— 合金ラインの出発点",
        u"ru_ru": u"Контроллер + порт питания + корпус: три вида пластин + конденсатор + нагреватель + радиатор — начало линии сплавов",
    },
    u"wiring": {
        u"zh_cn": u"接线端子就是电线：拿铜线轴右键两个端子连起来（动力网络用动力线缆轴），潜行右键切换输入 / 输出",
        u"en_us": u"Terminal Blocks are your wiring: link two of them with a Copper Wire Spool (use the Power Cable Spool for the power network), sneak-right-click to switch input / output",
        u"ja_jp": u"端子ブロックがそのまま電線：銅線のスプールで 2 つの端子を右クリックして繋ぎ（動力網は動力ケーブルのスプール）、スニーク右クリックで入力 / 出力を切替",
        u"ru_ru": u"Клеммные блоки — это и есть проводка: соедините два катушкой с медным проводом (для силовой сети — катушкой силового кабеля), ПКМ с приседанием переключает вход / выход",
    },
    u"blast_furnace": {
        u"zh_cn": u"一栋 3\u00d73\u00d73 的多方块：正面锚点放原版高炉或主控，再用外壳围起来，摆好右键主控自检",
        u"en_us": u"A 3\u00d73\u00d73 multiblock: put a vanilla blast furnace or the controller on the front anchor and wall it in, then right-click the controller for a self-check",
        u"ja_jp": u"3\u00d73\u00d73 のマルチブロック：正面のアンカーに溶鉱炉かコントローラーを置き、外殻で囲います。組んだらコントローラーを右クリックで自己診断",
        u"ru_ru": u"Мультиблок 3\u00d73\u00d73: на переднюю опору — доменная печь или контроллер, обнести корпусом, затем ПКМ по контроллеру для самопроверки",
    },
}

# _zf117_verify.py 的 MUST 表：这些事实一个字都不许丢
MUST = {
    u"oil_pump": [u"8n\u00b2+80n", u"10n mB/s", u"25B"],
    u"lithium_battery_plant": [u"1 mB", u"600 mB", u"30 \u79d2"],
    u"lithium_battery": [u"4M FE"],
    u"star_steel": [u"12000 FE/t", u"30 \u79d2"],
    u"star_steel_armor": [u"24"],
    u"starfall": [u"y=200", u"7~20"],
    u"salt": [u"\u6d77\u76d0"],
    u"fluid_logistics": [u"1000 mB"],
}

LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]
fails = []

# ---- 写前断言 1：中文新文案必须保留 MUST 的事实 ----
for nid, facts in MUST.items():
    if nid not in NEW:
        continue
    v = NEW[nid][u"zh_cn"]
    for f in facts:
        if f not in v:
            fails.append(u"%s：新中文文案丢了事实「%s」" % (nid, f))

# ---- 写前断言 2：新文案必须比老文案短 ----
raw = {}
for loc in LOCALES:
    raw[loc] = io.open(LANG % loc, encoding=u"utf-8", newline=u"").read()

plan = []          # (loc, old_literal, new_literal, nid)
for loc in LOCALES:
    for nid, table in NEW.items():
        key = u'"advancements.potato_s_t.%s.description"' % nid
        i = raw[loc].find(key)
        if i < 0:
            fails.append(u"%s / %s：找不到这个键" % (loc, nid))
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
        new_lit = json.dumps(table[loc], ensure_ascii=False)
        if old_lit == new_lit:
            continue
        n = raw[loc].count(old_lit)
        if n != 1:
            fails.append(u"%s / %s：老值在文件里出现 %d 次（要求恰好 1）" % (loc, nid, n))
            continue
        plan.append((loc, old_lit, new_lit, nid, len(json.loads(old_lit)), len(table[loc])))

if fails:
    print(u"写前自检就挂了，一个字节都没落盘：")
    for f in fails:
        print(u"  !! " + f)
    sys.exit(1)

# ---- 落盘：逐条替换 ----
print(u"%-8s %-24s %s" % (u"语言", u"节点", u"字数 老 → 新"))
for loc in LOCALES:
    text = raw[loc]
    for (l, old_lit, new_lit, nid, lo, ln) in [p for p in plan if p[0] == loc]:
        text = text.replace(old_lit, new_lit, 1)
        print(u"%-8s %-24s %3d → %3d" % (loc, nid, lo, ln))
    back = json.loads(text)
    if len(back) != len(json.loads(raw[loc])):
        print(u"  !! %s 回读键数变了，本份不写" % loc)
        sys.exit(1)
    io.open(LANG % loc, u"w", encoding=u"utf-8", newline=u"").write(text)

print(u"\n改了 %d 处；四份键数应与改前一致" % len(plan))
