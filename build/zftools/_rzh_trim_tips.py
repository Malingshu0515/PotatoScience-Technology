# -*- coding: utf-8 -*-
r"""_rzh_trim_tips.py —— 机器说明"去流水账"（用户：「看清明显是流水账的删除」）。

口径（用户点头的边界）：
  · **删**：JEI 里已经有的配方表 / 配方耗时与 FE/t；同一条说明里**重复出现**的同一个数值。
  · **留**：多方块**摆放图纸**（那是结构本身，JEI 里没有）、机制说明、"削成 1 格就激活不了"
    这类告警、状态行、以及**该机器独有的**规格数字。

做法：复用带自检的 `_rzh_setkv`（按行首键定位、取到的字面量必须等于该键解析值、
       回读确认键数不变，否则整体不写盘）。只改这 6 个键的**值**，键一个不动。
"""
import importlib.util
import io
import json
import sys

spec = importlib.util.spec_from_file_location(u"kv", u"build/zftools/_rzh_setkv.py")
kv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kv)

NEW = {
    u"tooltip.potato_s_t.micro_crusher": {
        u"zh_cn": u"粉碎配方见 JEI（有红石信号就关机）。\n"
                  u"内部缓冲 2500 FE。\n"
                  u"（矿石、粗锂与石英走 c: 通用标签匹配，别的 mod 的同类物品也认）",
        u"en_us": u"Crushing recipes are in JEI (a redstone signal shuts it down).\n"
                  u"Internal buffer: 2500 FE.\n"
                  u"(Ores, raw lithium and quartz match by c: common tags, so other mods' equivalents count too)",
        u"ja_jp": u"粉砕レシピは JEI をご覧ください（レッドストーン信号で停止します）。\n"
                  u"内部バッファ：2500 FE。\n"
                  u"（鉱石・粗リチウム・クォーツは c: 共通タグで判定するので、他の MOD の同等品も使えます）",
        u"ru_ru": u"Рецепты дробления — в JEI (сигнал редстоуна выключает машину).\n"
                  u"Внутренний буфер: 2500 FE.\n"
                  u"(Руды, необработанный литий и кварц определяются по общим тегам c:, так что аналоги из других модов тоже подойдут)",
    },
    u"tooltip.potato_s_t.electrolyzer": {
        u"zh_cn": u"不给电解质：每 tick 吃掉 1000 FE 和 10 mB 水，吐出 3 氧气 + 6 氢气。\n"
                  u"往电解质槽里放一块海盐，它就改产氯气：同样耗电耗水，产 3 氯气 + 6 氢气，"
                  u"但每 500 mB 水要多消耗 1 个海盐。\n"
                  u"储罐满了、没水了、断电了，它会自己停下来歇着。",
        u"en_us": u"No electrolyte: burns 1000 FE and 10 mB of water per tick, yields 3 Oxygen + 6 Hydrogen.\n"
                  u"Drop a piece of Sea Salt into the electrolyte slot and it switches to Chlorine: same power and "
                  u"water, 3 Chlorine + 6 Hydrogen, but one Sea Salt per 500 mB of water.\n"
                  u"If a tank fills up, the water runs dry or the power cuts out, it quietly stops and waits.",
        u"ja_jp": u"電解質なし：毎 tick 1000 FE と水 10 mB を消費し、酸素 3 + 水素 6 を生み出します。\n"
                  u"電解質スロットに海塩を 1 個入れると塩素に切り替わります：電力と水は同じで、塩素 3 + 水素 6。"
                  u"ただし水 500 mB につき海塩 1 個を余分に消費します。\n"
                  u"タンクが満杯、水切れ、停電のいずれかになると、静かに止まって待ちます。",
        u"ru_ru": u"Без электролита: сжигает 1000 FE и 10 mB воды за тик, выдаёт 3 кислорода + 6 водорода.\n"
                  u"Положите в слот электролита морскую соль — и он переключится на хлор: те же энергия и вода, "
                  u"3 хлора + 6 водорода, но одна морская соль на каждые 500 mB воды.\n"
                  u"Если бак заполнится, вода кончится или пропадёт питание, он тихо встанет и подождёт.",
    },
    u"tooltip.potato_s_t.distillation_operator": {
        u"zh_cn": u"每座塔每 tick：8 mB 原油 + 8096 FE → 3 柴油 + 2 石脑油 + 2 汽油 + 1 液化石油气。\n"
                  u"每 5 tick 出 1 块沥青（每座塔）；沥青攒到 64 还没人收，它就停工。\n"
                  u"每座塔的容量：原油 12 桶、每种产品 2.5 桶。\n"
                  u"给它红石信号才开始干活；最多认 4 座塔。",
        u"en_us": u"Per tower, per tick: 8 mB crude oil + 8096 FE -> 3 Diesel + 2 Naphtha + 2 Gasoline + 1 LPG\n"
                  u"Every 5 ticks: 1 Bitumen per tower. Pile up 64 with nobody collecting and it stops.\n"
                  u"Per tower: 12 buckets of oil, 2.5 buckets of each product\n"
                  u"Needs a redstone signal to start; recognises up to 4 towers.",
        u"ja_jp": u"塔 1 基につき毎 tick：原油 8 mB + 8096 FE → ディーゼル 3 + ナフサ 2 + ガソリン 2 + 液化石油ガス 1\n"
                  u"5 tick ごとにアスファルト 1 個（塔 1 基あたり）。64 個たまったまま誰も回収しないと止まります。\n"
                  u"塔 1 基あたりの容量：原油 12 バケツ、各製品 2.5 バケツ\n"
                  u"レッドストーン信号で開始。認識できるのは最大 4 基までです。",
        u"ru_ru": u"На каждую башню за тик: 8 mB сырой нефти + 8096 FE → 3 дизеля + 2 нафты + 2 бензина + 1 СУГ\n"
                  u"Каждые 5 тиков: 1 битум на башню. Наберётся 64 и никто не заберёт — работа встанет.\n"
                  u"На башню: 12 вёдер нефти, 2,5 ведра каждого продукта\n"
                  u"Начинает по сигналу редстоуна; распознаёт до 4 башен.",
    },
    u"tooltip.potato_s_t.electric_blast_furnace": {
        u"zh_cn": u"用 3×3×3 的结构装配而成。\n"
                  u"外壳搭好后，空手潜行右键成型 —— 锚点放原版高炉，或者本模组的电力高炉主控，都行。\n"
                  u"手持扳手潜行右键可以拆开。\n"
                  u"12 个输入槽、32 个输出槽，每个槽 10 秒烧完；每件物品耗电 800 FE。\n"
                  u"铁粉 + 碳粉 → 高碳钢；铁粉 + 沙砾 → 磁铁（放进任意两个输入槽，它会自动配对）。\n"
                  u"除了本模组的矿物处理，原版高炉能烧的东西这里都能烧。",
        u"en_us": u"Assembled from a 3x3x3 structure.\n"
                  u"Build the shell, then sneak-right-click empty-handed to form it - the anchor can be either a "
                  u"vanilla blast furnace or this mod's own controller.\n"
                  u"Hold a wrench and sneak-right-click to take it apart.\n"
                  u"12 input slots and 32 output slots; each slot finishes in 10 seconds, at 800 FE per item.\n"
                  u"Iron Dust + Carbon Dust -> High Carbon Steel; Iron Dust + Gravel -> Magnet (drop them into any two "
                  u"input slots and it pairs them up on its own).\n"
                  u"On top of this mod's ore processing, anything a vanilla blast furnace can smelt works here too.",
        u"ja_jp": u"3×3×3 の構造物として組み上げます。\n"
                  u"外殻ができたら、素手でスニーク右クリックして完成させます — アンカーはバニラの溶鉱炉でも、"
                  u"本 MOD の電力高炉コントローラーでも構いません。\n"
                  u"レンチを持ってスニーク右クリックすると解体できます。\n"
                  u"入力 12 スロット、出力 32 スロット。1 スロットは 10 秒で焼き上がり、アイテム 1 個につき 800 FE を消費します。\n"
                  u"鉄粉 + 炭素粉末 → 高炭素鋼、鉄粉 + 砂利 → 磁石（どの入力スロット 2 つに入れても、ひとりでに組み合わせます）。\n"
                  u"本 MOD の鉱物処理のほか、バニラの溶鉱炉で焼けるものは何でも扱えます。",
        u"ru_ru": u"Собирается из конструкции 3×3×3.\n"
                  u"Постройте корпус, затем присядьте и щёлкните правой кнопкой пустой рукой, чтобы собрать — опорой "
                  u"может быть как обычная доменная печь, так и собственный контроллер мода.\n"
                  u"С гаечным ключом и приседанием та же кнопка разбирает её обратно.\n"
                  u"12 входных и 32 выходных слота; каждый слот обрабатывается 10 секунд, по 800 FE за предмет.\n"
                  u"Железная пыль + угольная пыль → высокоуглеродистая сталь; железная пыль + гравий → магнит "
                  u"(положите их в любые два входных слота, он сам найдёт пару).\n"
                  u"Кроме обработки руды из этого мода, здесь плавится всё, что умеет обычная доменная печь.",
    },
    u"tooltip.potato_s_t.diesel_generator_controller": {
        u"zh_cn": u"大型柴油发电机摆放方式（控制器＝图上写着 9 的那一格：第 1 层、最前排、正中间）\n"
                  u"1 耐热金属块　2 一般金属块　3 流体泵　4 低级发电机\n"
                  u"5 燃烧反应室　6 铜块　7 铜格栅　8 接线块　9 柴油发电机控制器\n"
                  u"第 1 层（底）｜第 2 层\n"
                  u"1 3 1 ｜ 2 1 2\n"
                  u"1 4 1 ｜ 6 7 6\n"
                  u"1 5 1 ｜ 6 7 6\n"
                  u"1 4 1 ｜ 6 7 6\n"
                  u"1 9 1 ｜ 2 8 2\n"
                  u"以控制器的朝向为正面，机器朝它背后铺 5 排、向上 2 层，一格都不能少。\n"
                  u"铜块与铜格栅：氧化到什么程度、打没打蜡都行（16 种全收）。\n"
                  u"摆齐后控制器正上方那格接线块会变成接线口（贴图一样，挖掉掉回接线块）—— 电只从那里出。\n"
                  u"界面：一个 8000 mB 柴油罐 ＋ 一盏工作指示灯；每 tick 烧 1 mB 柴油发 7200 FE，有红石信号即停机。\n"
                  u"柴油怎么进：接泵灌（控制器本体或接线口都行），或拿柴油桶 / 装着柴油的油桶右键控制器。\n"
                  u"⚠ 里面那台流体泵 / 两台低级发电机 / 一台燃烧反应室成型后照样是它们自己，不会被吃掉。",
        u"en_us": u"How to lay out the Diesel Generator (the controller is the cell marked 9: layer 1, front row, centre)\n"
                  u"1 Heat-Resistant Metal Block  2 Common Metal Block  3 Fluid Pump  4 Low-Tier Generator\n"
                  u"5 Combustion Chamber  6 Block of Copper  7 Copper Grate  8 Wiring Block  9 Diesel Generator Controller\n"
                  u"Layer 1 (bottom) | Layer 2\n"
                  u"1 3 1 | 2 1 2\n"
                  u"1 4 1 | 6 7 6\n"
                  u"1 5 1 | 6 7 6\n"
                  u"1 4 1 | 6 7 6\n"
                  u"1 9 1 | 2 8 2\n"
                  u"With the controller's facing as the front, the machine runs 5 rows back and 2 layers up - not a single cell less.\n"
                  u"Copper blocks and grates: any oxidation level, waxed or not (all 16 count).\n"
                  u"Once complete, the Wiring Block directly above the controller becomes a port (same texture, drops back "
                  u"as a Wiring Block) - and that is the only place power comes out.\n"
                  u"GUI: an 8000 mB diesel tank and a status lamp; 1 mB of diesel per tick makes 7200 FE; a redstone signal halts it.\n"
                  u"Getting diesel in: hook up a pump (controller or port), or right-click the controller with a Diesel "
                  u"Bucket or an oil bucket holding diesel.\n"
                  u"⚠ The Fluid Pump / two Low-Tier Generators / Combustion Chamber inside stay as they are - they are not consumed.",
        u"ja_jp": u"大型ディーゼル発電機の配置（コントローラーは図の「9」のマス：第 1 層、最前列、中央）\n"
                  u"1 耐熱金属ブロック　2 一般金属ブロック　3 流体ポンプ　4 低級発電機\n"
                  u"5 燃焼反応室　6 銅ブロック　7 銅グレーチング　8 配線ブロック　9 ディーゼル発電機コントローラー\n"
                  u"第 1 層（底面）｜第 2 層\n"
                  u"1 3 1 ｜ 2 1 2\n"
                  u"1 4 1 ｜ 6 7 6\n"
                  u"1 5 1 ｜ 6 7 6\n"
                  u"1 4 1 ｜ 6 7 6\n"
                  u"1 9 1 ｜ 2 8 2\n"
                  u"コントローラーの向きを正面として、背後へ 5 列・上へ 2 層、1 マスも欠かさずに。\n"
                  u"銅ブロックと銅グレーチング：酸化の度合いも、ろうを塗ったかも問いません（16 種すべて可）。\n"
                  u"組み上がると、コントローラー真上の配線ブロックが接続口になります（貼図は同じ、掘ると配線ブロックに戻る）"
                  u"—— 電力はそこからしか出ません。\n"
                  u"界面：8000 mB のディーゼルタンク ＋ 動作ランプ。毎 tick ディーゼル 1 mB を燃やして 7200 FE を発電、"
                  u"レッドストーン信号で停止します。\n"
                  u"ディーゼルの入れ方：ポンプで送る（コントローラー本体でも接続口でも可）、またはディーゼル入りバケツ / "
                  u"ディーゼル入りオイルバケツを持ってコントローラーを右クリック。\n"
                  u"⚠ 中の流体ポンプ / 低級発電機 2 台 / 燃焼反応室は、成型後もそのまま残ります（消えません）。",
        u"ru_ru": u"Как выложить большой дизель-генератор (контроллер — клетка с цифрой 9: слой 1, передний ряд, центр)\n"
                  u"1 Жаростойкий металлический блок　2 Обычный металлический блок　3 Жидкостный насос　4 Простой генератор\n"
                  u"5 Камера сгорания　6 Медный блок　7 Медная решётка　8 Соединительный блок　9 Контроллер дизель-генератора\n"
                  u"Слой 1 (низ) | Слой 2\n"
                  u"1 3 1 | 2 1 2\n"
                  u"1 4 1 | 6 7 6\n"
                  u"1 5 1 | 6 7 6\n"
                  u"1 4 1 | 6 7 6\n"
                  u"1 9 1 | 2 8 2\n"
                  u"Перед — сторона, куда смотрит контроллер; машина уходит на 5 рядов назад и на 2 слоя вверх, ни одной клеткой меньше.\n"
                  u"Медные блоки и решётки: любая степень окисления, вощёные или нет (подходят все 16).\n"
                  u"Когда всё выложено, соединительный блок прямо над контроллером становится портом (текстура та же, "
                  u"при разрушении возвращается соединительным блоком) — и энергия выходит только оттуда.\n"
                  u"Интерфейс: бак дизеля на 8000 mB и лампа работы; 1 mB дизеля за тик даёт 7200 FE; сигнал редстоуна останавливает.\n"
                  u"Как подать дизель: насосом (в контроллер или в порт) либо щёлкнув ПКМ по контроллеру ведром дизеля "
                  u"или нефтяным ведром с дизелем.\n"
                  u"⚠ Жидкостный насос / два простых генератора / камера сгорания внутри остаются собой — их не съедает.",
    },
    u"tooltip.potato_s_t.solar_panel": {
        u"zh_cn": u"只在白天发电，越靠正午越强（逐时段数值见 JEI）。\n"
                  u"下雨降到 60%，雷暴只剩 20% —— 天气不好，它也想请假。\n"
                  u"正上方必须是空气或无色玻璃。\n"
                  u"自身储能 512 FE，自动给下方设备供电。\n"
                  u"水平相邻的太阳能板自动并联，发电量与储能整组共享。",
        u"en_us": u"Generates power in daylight only, strongest around noon (see JEI for the hour-by-hour numbers).\n"
                  u"Rain cuts it to 60% and a thunderstorm to 20% - in bad weather it would rather be excused.\n"
                  u"The block directly above must be air or colorless glass.\n"
                  u"Stores 512 FE and feeds the block below automatically.\n"
                  u"Horizontally adjacent panels link up on their own, sharing generation and storage across the whole group.",
        u"ja_jp": u"昼間だけ発電し、正午に近いほど強くなります（時間帯ごとの数値は JEI をご覧ください）。\n"
                  u"雨は 60%、雷雨は 20% まで落ちます — 天気が悪いと休みたくなるようです。\n"
                  u"真上は空気か無色のガラスでなければなりません。\n"
                  u"蓄電 512 FE、真下の装置へ自動で給電します。\n"
                  u"水平に隣り合うパネルは自動で並列接続し、発電量と蓄電を組全体で共有します。",
        u"ru_ru": u"Вырабатывает энергию только днём, сильнее всего около полудня (почасовые числа — в JEI).\n"
                  u"В дождь выработка падает до 60%, в грозу — до 20%: в плохую погоду она предпочла бы отпроситься.\n"
                  u"Блок прямо над панелью должен быть воздухом или бесцветным стеклом.\n"
                  u"Хранит 512 FE и сама питает блок под собой.\n"
                  u"Панели, стоящие в ряд, соединяются автоматически: выработка и запас общие на всю группу.",
    },
}

fails = []
for loc in kv.LOCALES:
    rel = kv.LANG % loc
    mapping = dict((k, v[loc]) for k, v in NEW.items())
    lab, ch = kv.set_values(rel, mapping, u"trim")
    if lab is None:
        fails.append(ch)
    else:
        print(u"== %s：改 %d 个机器说明" % (loc, len(ch)))
        for k, a, b in ch:
            print(u"     %-42s %4d → %4d 字" % (k.split(u".")[-1], len(a), len(b)))

if fails:
    print(u"\n[!!] 失败，相关文件未写：")
    for f in fails:
        print(u"   " + f)
    sys.exit(1)
print(u"\n完成。")
