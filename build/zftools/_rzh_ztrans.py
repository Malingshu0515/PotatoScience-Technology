# -*- coding: utf-8 -*-
r"""_rzh_ztrans.py —— 把用户手改的中文（zh_cn）翻成 en_us / ja_jp / ru_ru / lzh。

策略：**中文是唯一事实源**。每条翻译的旧值一律在运行时从目标语言文件里读出来，
绝不手抄（手抄过一次，因并行会话重润色而对不上，整批被拒）。

语气按用户这一轮的写法走：幽默、口语、玩梗都译出来，不只是翻字面；
他的删减尺度照搬 —— 他删掉的从属解释与配方数字，别的语言也一并删。

落盘走 `_rzh_fix_batch.py` 的 EDITS 通道（行首锚定 + 旧值必须相等 + 写后复读）。
lzh 走它自己的 `_rzh_lzh_set.apply`（同一套校验）。

用法：`python build/zftools/_rzh_ztrans.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")

# ---------------------------------------------------------------------------
# 翻译表：键 -> {语言: 新值}
# 未列出的语言 = 该语言这条不动。
# ---------------------------------------------------------------------------
T = {}

T[u"tooltip.potato_s_t.star_steel_axe.2"] = {
    u"en_us": u"Shift + right-click: spend 120 durability to send a 6-block-wide shockwave along your facing",
    u"ja_jp": u"Shift + 右クリック：耐久を 120 消費し、向いている方向へ幅 6 ブロックの衝撃波を放つ",
    u"ru_ru": u"Shift + ПКМ: потратьте 120 прочности и пошлите ударную волну шириной 6 блоков по направлению взгляда",
    u"lzh": u"Shift + 右鍵：耗 120 點耐久，向所面之處放衝擊波一道，廣 6 格",
}

T[u"tooltip.potato_s_t.star_steel_axe.3"] = {
    u"en_us": u"The shockwave fells every log along its path; it dies when it meets a block the axe cannot mine, or after 10 s without touching wood.\nIn the End it also deals ranged damage",
    u"ja_jp": u"衝撃波は進路上の原木をすべて薙ぎ倒す。斧で採掘できないブロックに当たるか、10 秒間木材に触れないと消える。\nエンドでは追加で遠距離ダメージ",
    u"ru_ru": u"Волна валит все брёвна на пути; исчезает, встретив блок, который топор не может добыть, или через 10 с без древесины.\nВ Крае дополнительно наносит урон на расстоянии",
    u"lzh": u"衝擊波拆沿途所有原木；撞及斧不能掘之方塊，或 10 秒未遇木，即散。\n於終界：另加遠程傷害",
}

T[u"tooltip.potato_s_t.star_steel_sword.2"] = {
    u"en_us": u"Shift + right-click: spend 100 durability to cut an 8-block starlight slash along your facing",
    u"ja_jp": u"Shift + 右クリック：耐久を 100 消費し、向いている方向へ長さ 8 ブロックの星輝斬を放つ",
    u"ru_ru": u"Shift + ПКМ: потратьте 100 прочности и рассеките звёздный разрез длиной 8 блоков по направлению взгляда",
    u"lzh": u"Shift + 右鍵：耗 100 點耐久，向所面之處斬出星輝劍氣一道，長 8 格",
}

T[u"message.potato_s_t.starfall.incoming"] = {
    u"en_us": u"⚠ A meteor is falling toward %s %s - watch out!",
    u"ja_jp": u"⚠ 隕石が %s %s に向かって落下中 —— 気をつけて！",
    u"ru_ru": u"⚠ Метеорит летит в %s %s — берегитесь!",
    u"lzh": u"⚠ 隕石正向 %s %s 墜下 —— 其慎之！",
}

T[u"message.potato_s_t.starfall.locked"] = {
    u"en_us": u"Locked in - too late now",
    u"ja_jp": u"すでにロック済み —— もう手遅れです",
    u"ru_ru": u"Уже зафиксировано — поздно",
    u"lzh": u"既已鎖定，為時已晚",
}

T[u"tooltip.potato_s_t.power_capturer"] = {
    u"en_us": u"...draws power while sitting next to a power source\nDelivered by power cables\n(Alien tech, kid!)",
    u"ja_jp": u"…動力源の隣にあると動力を得ます\n動力ケーブルで送ります\n（宇宙の技術だ、坊や！）",
    u"ru_ru": u"…рядом с источником энергии — получает энергию\nПередаётся по силовым кабелям\n(Инопланетные технологии, малыш!)",
    u"lzh": u"…緊鄰動力源時，獲取動力\n賴動力線纜以傳\n（外星之技，小子！）",
}

T[u"tooltip.potato_s_t.lithium_battery"] = {
    u"en_us": u"Stores 4M FE per block. Batteries placed edge to edge in a solid cuboid merge into a single multiblock on their own. Only the top face can transfer FE",
    u"ja_jp": u"1 ブロックあたり 4M FE を蓄えます。リチウム電池を隙間なく並べて完全な直方体にすると、自動で 1 つのマルチブロックにまとまります。FE を送れるのは上面だけです",
    u"ru_ru": u"Хранит 4M FE на блок. Батареи, поставленные вплотную и образующие цельный прямоугольный параллелепипед, сами объединяются в один мультиблок. Передавать FE умеет только верхняя грань",
    u"lzh": u"單塊儲能 4M FE。以鋰電池緊貼排作完整長方體，則自合成一多方塊。唯頂面可傳 FE",
}

T[u"tooltip.potato_s_t.hold_shift"] = {
    u"en_us": u"Hold Shift to consult the details",
    u"ja_jp": u"Shift を押すと詳細を参照できます",
    u"ru_ru": u"Удерживайте Shift, чтобы свериться с подробностями",
    u"lzh": u"按住 Shift 參閱其詳",
}

T[u"tooltip.potato_s_t.electrolyzer"] = {
    u"en_us": u"With no electrolyte it makes hydrogen and oxygen as usual\nDrop sea salt into the electrolyte slot and it makes chlorine, spending 1 extra sea salt per 500 mB of water.",
    u"ja_jp": u"電解質なしなら、水素と酸素を通常どおり産出\n電解質スロットに海塩を入れると塩素を産出。水 500 mB につき海塩 1 個を余分に消費します。",
    u"ru_ru": u"Без электролита выдаёт водород и кислород как обычно\nПоложите морскую соль в слот электролита — пойдёт хлор, по 1 лишней соли на каждые 500 mB воды.",
    u"lzh": u"無電解質時，如常產氫氧\n電解質槽中置海鹽，則產氯氣。每 500 mB 水多耗 1 海鹽。",
}

T[u"tooltip.potato_s_t.fluid_exchanger"] = {
    u"en_us": u"Left slot: an oil bucket or gas tank holding a fluid; right slot: 1 empty bucket.\nOut comes a bucket of that fluid (water -> Water Bucket, diesel -> Diesel Bucket; in theory any fluid works, as long as it has a bucket form of its own).\nFluids with no bucket form (crude oil / naphtha / LPG) are refused outright.\nFor gases (gas tank) hook up a Fluid Pump",
    u"ja_jp": u"左スロット：流体の入ったオイルバケツ / 高圧ガスタンク。右スロット：空のバケツ 1 個。\nその流体のバケツを出力します（水→水入りバケツ、ディーゼル→ディーゼル入りバケツ。理論上どの流体でも、専用のバケツ型があれば大丈夫です）。\nバケツの形を持たない流体（原油 / ナフサ / LPG）は問答無用でお断りします。\n気体（高圧ガスタンク）は流体ポンプを接続してください",
    u"ru_ru": u"Левый слот: нефтяное ведро или газовый баллон с жидкостью; правый слот: 1 пустое ведро.\nНа выходе — ведро этой жидкости (вода → ведро воды, дизель → ведро дизеля; теоретически годится любая жидкость, лишь бы у неё была своя форма ведра).\nЖидкости без формы ведра (нефть / нафта / СУГ) отклоняются без разговоров.\nДля газов (газовый баллон) подключите жидкостный насос",
    u"lzh": u"左槽置盛流體之油桶 / 高壓氣罐；右槽置 1 空桶。\n輸出盛此流體之桶（水→水桶，柴油→柴油桶；理論上任何流體皆可，惟須其自有桶裝之形）。\n無桶形之流體（原油 / 石腦油 / 液化石油氣）一概拒收。\n氣體（高壓氣罐）請接流體泵",
}

T[u"gui.potato_s_t.fluid_exchanger.status.invalid"] = {
    u"en_us": u"[Fluid Exchanger] That thing in the left slot is not a fluid container - an oil bucket or a gas tank is required!",
    u"ja_jp": u"[流体交換器] 左スロットの中身は流体容器ではありません —— オイルバケツか高圧ガスタンクが必要です！",
    u"ru_ru": u"[Обменник жидкостей] То, что лежит в левом слоте, — не контейнер для жидкости: нужны нефтяное ведро или газовый баллон!",
    u"lzh": u"[容器換流器] 左槽之物非流體容器 —— 須油桶或高壓氣罐！",
}

T[u"gui.potato_s_t.fluid_exchanger.status.output_full"] = {
    u"en_us": u"[Fluid Exchanger] The right slot needs 1 empty bucket - it becomes that fluid's bucket right there",
    u"ja_jp": u"[流体交換器] 右スロットには空のバケツ 1 個 —— その場でその流体のバケツになります",
    u"ru_ru": u"[Обменник жидкостей] В правый слот нужно 1 пустое ведро — оно станет ведром этой жидкости прямо там",
    u"lzh": u"[容器換流器] 右槽須置 1 空桶 —— 其將就地化為此流體之桶",
}

T[u"tooltip.potato_s_t.distillation_operator"] = {
    u"en_us": u"Per tower: 12 buckets of oil, 2.5 buckets of each product.\nA redstone signal starts it; it recognises up to 4 towers.",
    u"ja_jp": u"塔 1 基あたりの容量：原油 12 バケツ、各製品 2.5 バケツ。\nレッドストーン信号で開始。認識できるのは最大 4 基までです。",
    u"ru_ru": u"На башню: 12 вёдер нефти, 2,5 ведра каждого продукта.\nНачинает по сигналу редстоуна; распознаёт до 4 башен.",
    u"lzh": u"每座塔之容量：原油 12 桶、每種產品 2.5 桶。\n紅石信號激活則始作工；至多識 4 座塔。",
}

T[u"gui.potato_s_t.distillation.diagnosis.found"] = {
    u"en_us": u"Detected %s distillation tower(s) - up to 4",
    u"ja_jp": u"分留塔を %s 基検出しました（最大 4 基）",
    u"ru_ru": u"Обнаружено башен: %s (до 4)",
    u"lzh": u"檢測得 %s 座分餾塔（至多 4 座）",
}

T[u"tooltip.potato_s_t.salt_dryer"] = {
    u"en_us": u"In an ocean or salty river biome, at Y 0-64 and with a water source below, it produces 1 Sea Salt every 120 seconds.\nFeed it FE and that drops to one every 20 seconds. Sunshine is free, but electricity is faster.",
    u"ja_jp": u"海洋または塩水河バイオーム、Y 0〜64 で真下に水源ブロックがあるとき、120 秒ごとに海塩を 1 個生成します。\nFE を供給すると 20 秒ごとに 1 個へ短縮されます。太陽はただですが、電気のほうが速いのです。",
    u"ru_ru": u"В биоме океана или Солёной реки, на высоте Y 0–64 и при источнике воды под блоком даёт 1 морскую соль каждые 120 секунд.\nПодайте FE — и срок сократится до одной соли каждые 20 секунд. Солнце бесплатно, но электричество быстрее.",
    u"lzh": u"在海洋或鹹水河群系、Y 0~64 且下方有水源方塊時，每 120 秒產 1 海鹽。\n與之通 FE，則每 20 秒 1 個。畢竟日曬之速，不如電也。",
}

T[u"tooltip.potato_s_t.fluid_pump"] = {
    u"en_us": u"Front face is the input, back face is the output; pipes attach to those two faces only.\nThe pump stores no fluid itself\nIt only moves fluids the destination accepts\nRight-click for the rate (0% - 800%).",
    u"ja_jp": u"正面が入力、背面が出力です。パイプを付けられるのはこの 2 面だけ。\nポンプ自体は液体を溜めません\n送り先が受け取れる流体だけを送ります\n右クリックで画面を開き、速度を調整できます（0% - 800%）。",
    u"ru_ru": u"Передняя грань — вход, задняя — выход; трубы крепятся только к этим двум граням.\nСам насос жидкость не хранит\nОн перекачивает только то, что принимает приёмник\nПКМ открывает интерфейс настройки скорости (0% - 800%).",
    u"lzh": u"正面為輸入、背面為輸出；管道唯可接此二面。\n泵自身不存液體\n唯送目標所能受之流體\n右鍵開界面調速（0% - 800%）。",
}

T[u"tooltip.potato_s_t.high_pressure_tank.hydrogen_risk"] = {
    u"en_us": u"⚠ Hydrogen has reached %s mB: DANGER! Keep away from open flames! DANGER! (Important things bear saying 114514 times)",
    u"ja_jp": u"⚠ 水素が %s mB に達しました：危険！火気に近づけないでください！危険！（大事なことなので 114514 回言います）",
    u"ru_ru": u"⚠ Водород достиг %s mB: ОПАСНО! Не подносите к открытому огню! ОПАСНО! (Важное повторяют 114514 раз)",
    u"lzh": u"⚠ 氫氣已達 %s mB：危矣！請勿近明火！危矣！（要事須說 114514 遍）",
}

T[u"tooltip.potato_s_t.solar_panel"] = {
    u"en_us": u"Generates power in daylight only, strongest around noon (see JEI for the hour-by-hour numbers).\nThe block directly above must be air or colorless glass.\nStores 512 FE and feeds the block below automatically.\nHorizontally adjacent panels link up on their own, sharing generation and storage across the whole group.",
    u"ja_jp": u"昼間だけ発電し、正午に近いほど強くなります（時間帯ごとの数値は JEI をご覧ください）。\n真上は空気か無色のガラスでなければなりません。\n蓄電 512 FE、真下の装置へ自動で給電します。\n水平に隣り合うパネルは自動で並列接続し、発電量と蓄電を組全体で共有します。",
    u"ru_ru": u"Вырабатывает энергию только днём, сильнее всего около полудня (почасовые числа — в JEI).\nБлок прямо над панелью должен быть воздухом или бесцветным стеклом.\nХранит 512 FE и сама питает блок под собой.\nПанели, стоящие в ряд, соединяются автоматически: выработка и запас общие на всю группу.",
    u"lzh": u"唯晝間發電，愈近正午愈強（逐時之數見 JEI）。\n正上方須是空氣或無色玻璃。\n自身儲能 512 FE，自為下方之器供電。\n水平相鄰之太陽能板自相並聯，發電之量與儲能整組共享。",
}

T[u"tooltip.potato_s_t.micro_crusher"] = {
    u"en_us": u"Crushing recipes are in JEI.\nInternal buffer: 2500 FE.",
    u"ja_jp": u"粉砕レシピは JEI をご覧ください。\n内部バッファ：2500 FE。",
    u"ru_ru": u"Рецепты дробления — в JEI.\nВнутренний буфер: 2500 FE.",
    u"lzh": u"粉碎之方見 JEI。\n內中緩衝 2500 FE。",
}

T[u"gui.potato_s_t.micro_crusher.status.disabled"] = {
    u"en_us": u"Shut down: a redstone signal is detected",
    u"ja_jp": u"停止中：レッドストーン信号を検出",
    u"ru_ru": u"Выключено: обнаружен сигнал редстоуна",
    u"lzh": u"已關閉：偵得紅石信號",
}

T[u"tooltip.potato_s_t.hydraulic_press"] = {
    u"en_us": u"Presses mineral ingots into the matching plates.\nA redstone signal halts it; progress is kept.\nFull recipe list in JEI.",
    u"ja_jp": u"鉱物インゴットを対応する板材へ鍛圧します。\nレッドストーン信号を入れると停止し、進捗は保持されます。\nレシピ一覧は JEI をご覧ください。",
    u"ru_ru": u"Прессует слитки в соответствующие пластины.\nСигнал редстоуна останавливает работу; прогресс сохраняется.\nПолный список рецептов — в JEI.",
    u"lzh": u"以礦物錠鍛壓為對應之板。\n通入紅石信號即停機，進度猶存。\n配方一覽見 JEI。",
}

T[u"tooltip.potato_s_t.salt_decomposer"] = {
    u"en_us": u"Takes sea salt apart to get sodium chloride.\nFeed in 64 Sea Salt, and 40 seconds later 1 Sodium Chloride comes out.\n60% chance to return all 64 Sea Salt; a separate 5% chance of one random raw ore as a bonus.\nA redstone signal halts it; progress is kept.",
    u"ja_jp": u"海塩を分解して塩化ナトリウムを取り出します。\n1 回につき海塩 64 個を投入し、40 秒後に塩化ナトリウム 1 個ができます。\n60% の確率で海塩 64 個が戻り、さらに 5% の確率でランダムな粗鉱が 1 個おまけで付きます。\nレッドストーン信号を入れると停止し、進捗は保持されます。",
    u"ru_ru": u"Разбирает морскую соль на хлорид натрия.\nЗа один цикл расходуется 64 морской соли, и через 40 секунд выходит 1 хлорид натрия.\nС вероятностью 60% вся соль возвращается; отдельно с вероятностью 5% в подарок падает случайная руда.\nСигнал редстоуна останавливает работу; прогресс сохраняется.",
    u"lzh": u"以海鹽拆為氯化鈉。\n每投海鹽 64 個，40 秒後產 1 氯化鈉。\n60% 之數返還海鹽 64 個；另有 5% 之數外贈隨機粗礦一個。\n通入紅石信號即停機，進度猶存。",
}

T[u"tooltip.potato_s_t.low_generator"] = {
    u"en_us": u"Burns coal or charcoal to make power.\nA redstone signal halts it.",
    u"ja_jp": u"石炭か木炭を燃やして発電します。\nレッドストーン信号を入れると停止します。",
    u"ru_ru": u"Сжигает уголь или древесный уголь ради энергии.\nСигнал редстоуна останавливает работу.",
    u"lzh": u"焚煤炭或木炭以發電。\n通入紅石信號即停機。",
}

T[u"tooltip.potato_s_t.electric_blast_furnace"] = {
    u"en_us": u"Assembled from a 3x3x3 structure.\n12 input slots and 32 output slots; each slot finishes in 10 seconds, at 800 FE per item.\nOn top of this mod's ore processing, anything a vanilla blast furnace can smelt works here too.",
    u"ja_jp": u"3×3×3 の構造物として組み上げます。\n入力 12 スロット、出力 32 スロット。1 スロットは 10 秒で焼き上がり、アイテム 1 個につき 800 FE を消費します。\n本 MOD の鉱物処理のほか、バニラの溶鉱炉で焼けるものは何でも扱えます。",
    u"ru_ru": u"Собирается из конструкции 3×3×3.\n12 входных и 32 выходных слота; каждый слот обрабатывается 10 секунд, по 800 FE за предмет.\nКроме обработки руды из этого мода, здесь плавится всё, что умеет обычная доменная печь.",
    u"lzh": u"以 3×3×3 之結構裝配而成。\n12 輸入槽、32 輸出槽，每槽 10 秒燒畢；每物耗電 800 FE。\n除本模組之礦物處理，原版高爐所能冶者，此中皆可冶。",
}

T[u"item.potato_s_t.wrench"] = {
    u"en_us": u"Wrench (currently useless)",
    u"ja_jp": u"レンチ（今は使うところなし）",
    u"ru_ru": u"Гаечный ключ (пока бесполезен)",
    u"lzh": u"扳鉗（暫時無用）",
}

T[u"tooltip.potato_s_t.alloy_smelter"] = {
    u"en_us": u"How to lay out the Alloy Smelter\n1 Heat-Resistant Metal Block  2 Common Metal Block  3 Heater  4 Blast Furnace\n5 Wiring Block  6 Heat Sink  7 Alloy Smelter Controller  0 Empty\nLayer 1 (bottom) | Layer 2\n2222 | 5115\n2332 | 4004\n2332 | 4004\n2332 | 4004\n2222 | 6117\nLayer 3 | Layer 4 (top)\n1111 | 0110\n1001 | 0110\n1001 | 0110\n1001 | 0110\n1111 | 0110\nBuild all 4 layers to the blueprint (58 cells to check: the base, the three-high wall and those two columns of Heat-Resistant Metal Block on the roof) and make sure the shell carries at least 1 Wiring Block; then it activates on its own (the inside is up to you, and the rest of the roof does not matter).\nRight-clicking the controller also activates it, and it will tell you which cell is missing. Only once it is active does right-clicking open the GUI.\n5 input slots that take ingots only, 3 output slots, 2 consumption slots (they take whatever a recipe names as its consumable); 32768 FE of storage, and power comes in through the port alone. Four recipes in JEI;",
    u"ja_jp": u"合金精錬炉の配置\n1 耐熱金属ブロック　2 一般金属ブロック　3 加熱装置　4 溶鉱炉\n5 配線ブロック　6 放熱装置　7 合金精錬炉コントローラー　0 空き\n第 1 層（底面）| 第 2 層\n2222 | 5115\n2332 | 4004\n2332 | 4004\n2332 | 4004\n2222 | 6117\n第 3 層 | 第 4 層（上面）\n1111 | 0110\n1001 | 0110\n1001 | 0110\n1001 | 0110\n1111 | 0110\n図のとおりに 4 層すべてを置き（確認するのは 58 マス：底面 + 高さ 3 の壁 + 上面の耐熱金属ブロック 2 列）、外殻に配線ブロックが 1 個以上あれば自動で起動します（内部は自由、上面の残りは問いません）。\nコントローラーを右クリックしても起動できます。足りないマスを教えてくれます。起動後に右クリックすると画面が開きます。\n入力 5（インゴットのみ）/ 出力 3 / 消費 2（レシピが指定した消耗品を入れる）；蓄電 32768 FE、電力は接続口からのみ。レシピ 4 種は JEI をご覧ください；",
    u"ru_ru": u"Как выложить плавильню сплавов\n1 Жаростойкий металлический блок　2 Обычный металлический блок　3 Нагреватель　4 Доменная печь\n5 Соединительный блок　6 Радиатор　7 Контроллер плавильни сплавов　0 Пусто\nСлой 1 (низ) | Слой 2\n2222 | 5115\n2332 | 4004\n2332 | 4004\n2332 | 4004\n2222 | 6117\nСлой 3 | Слой 4 (верх)\n1111 | 0110\n1001 | 0110\n1001 | 0110\n1001 | 0110\n1111 | 0110\nВыложите все 4 слоя по схеме (проверяются 58 клеток: дно, стена высотой три блока и те два столбца жаростойкого блока на крыше) и убедитесь, что в корпусе есть хотя бы 1 соединительный блок — тогда она активируется сама (внутри делайте что хотите, остальная крыша не важна).\nПКМ по контроллеру тоже активирует её, и он назовёт недостающую клетку. Только после активации ПКМ открывает интерфейс.\n5 входных слотов только под слитки, 3 выходных, 2 расходных (туда кладётся то, что рецепт называет расходником); буфер 32768 FE, энергия только через порт. Четыре рецепта — в JEI;",
    u"lzh": u"合金爐擺放之式\n1 耐熱金屬塊　2 一般金屬塊　3 加熱裝置　4 高爐\n5 接線塊　6 散熱裝置　7 合金爐主控　0 空\n第 1 層（底）| 第 2 層\n2222 | 5115\n2332 | 4004\n2332 | 4004\n2332 | 4004\n2222 | 6117\n第 3 層 | 第 4 層（頂）\n1111 | 0110\n1001 | 0110\n1001 | 0110\n1001 | 0110\n1111 | 0110\n照圖將 4 層擺畢（須核 58 格：底面 + 三格高之牆 + 頂面那兩列耐熱金屬塊），且外殼上至少有 1 接線塊，方自激活（內中隨意置，頂面餘格不問）。\n右鍵主控亦可激活，缺何一格其將告爾；激活後右鍵方開界面。\n5 輸入槽只收錠、3 輸出槽、2 消耗槽（置配方所點名當耗之物）；儲能 32768 FE，電只自接線口入。配方四條見 JEI；",
}

T[u"tooltip.potato_s_t.oil_pump"] = {
    u"en_us": u"Only runs in the Ocean Oilfield biome - anywhere else it shuts down.\nThe block below must be water, and waterlogged chains are required (count up to 64 blocks).\nEvery 25-80 buckets pumped, the ocean oilfield in a 10x10 chunk area centred on the machine turns into ordinary ocean (frozen / warm / temperate ...).\n⚠ That area includes the machine itself, so after one pumping session move it to wherever oilfield is left.",
    u"ja_jp": u"海洋油田バイオームでのみ稼働します —— 足元が海洋油田でなければ停止します。\n真下は水源である必要があり、含水チェーンが要ります（最大 64 マスまで数えます）。\n25〜80 バケツ採油するごとに、機械を中心とした 10×10 チャンクの海洋油田が普通の海（凍った海 / 暖かい海 / 温帯の海…）に変わります。\n⚠ その範囲には機械自身も含まれるため、1 回汲み上げたら油田が残っている場所へ移してください。",
    u"ru_ru": u"Работает только в биоме морского нефтяного месторождения — в любом другом месте останавливается.\nПод машиной должна быть вода, и нужны цепи с водой (считается не более 64 блоков).\nКаждые 25-80 вёдер добычи морское месторождение в области 10x10 чанков вокруг машины превращается в обычный океан (замёрзший / тёплый / умеренный ...).\n⚠ Эта область включает саму машину, поэтому после одной откачки переставьте её туда, где месторождение ещё осталось.",
    u"lzh": u"唯於海洋油田群系開工 —— 腳下非海洋油田者一概停機。\n下方須是水源，且需含水鎖鏈（至多數 64 格）。\n每採出 25~80 桶，以機器為心 10×10 區塊之海洋油田，將化為普通海洋（凍洋 / 暖洋 / 溫帶海洋…）。\n⚠ 彼 100 區塊並含機器自身所在，抽一次之後，須移機器至尚有油田之處。",
}

T[u"tooltip.potato_s_t.lithium_battery_plant"] = {
    u"en_us": u"【Four inputs】: raw manganese/raw aluminum · nickel ingot/raw nickel · lithium carbonate · cobalt ingot/raw cobalt.\nFeed in sulfuric acid, and 30 seconds later one Lithium Battery Component comes out\n⚠ This machine uses no power at all - it is chemistry, not electricity. A redstone signal stops it (progress is kept).",
    u"ja_jp": u"【原料四つ】：マンガンの原石/アルミニウムの原石 · ニッケルインゴット/ニッケルの原石 · 炭酸リチウム · コバルトインゴット/コバルトの原石。\n硫酸を通すと、30 秒で「リチウム電池部品」が 1 つできます\n⚠ この機械は電力を消費しません —— 化学反応で動きます。レッドストーン信号で停止（進捗は保持）。",
    u"ru_ru": u"【Четыре входа】: сырой марганец/сырой алюминий · никелевый слиток/сырой никель · карбонат лития · кобальтовый слиток/сырой кобальт.\nПодайте серную кислоту — и через 30 секунд выйдет один компонент литиевой батареи\n⚠ Машина не потребляет энергию — здесь работает химия, а не электричество. Сигнал редстоуна останавливает её (прогресс сохраняется).",
    u"lzh": u"【原料四樣】：粗錳/粗鋁 · 鎳錠/粗鎳 · 碳酸鋰 · 鈷錠/粗鈷。\n通入硫酸，30 秒產「鋰電池元件」一件\n⚠ 此機不耗電 —— 所賴者化學，非電費也。有紅石信號即停機（進度猶存）。",
}

T[u"gui.potato_s_t.lithium_battery_plant.status.no_acid"] = {
    u"en_us": u"Not enough sulfuric acid: 1 mB per tick",
    u"ja_jp": u"硫酸が足りません：毎 tick 1 mB",
    u"ru_ru": u"Не хватает серной кислоты: 1 mB за тик",
    u"lzh": u"硫酸不足：每 tick 須 1 mB",
}

T[u"advancements.potato_s_t.clean_energy.description"] = {
    u"en_us": u"Daylight only, strongest at noon; a thunderstorm hater",
    u"ja_jp": u"昼だけ発電し、正午に最も強い。雷雨が怖い人",
    u"ru_ru": u"Только днём, сильнее всего в полдень; гроза — его страх",
    u"lzh": u"唯晝發電，近午則強；畏雷暴者也",
}

T[u"tooltip.potato_s_t.hydrodesulfurization_chamber"] = {
    u"en_us": u"A redstone signal halts it (progress kept)\n⚠ This machine draws no power at all - it runs on chemistry, not on your electricity bill",
    u"ja_jp": u"レッドストーン信号で停止（進捗は保持）\n⚠ このマシンは電力を一切消費しません —— 動くのは化学であって、電気代ではありません",
    u"ru_ru": u"Сигнал редстоуна останавливает (прогресс сохраняется)\n⚠ Эта машина вообще не потребляет энергию — она работает на химии, а не на счетах за электричество",
    u"lzh": u"有紅石信號即停機（進度猶存）\n⚠ 此機不耗電 —— 所賴者化學，非電費也",
}

T[u"tooltip.potato_s_t.air_separator"] = {
    u"en_us": u"A cheaper source of oxygen (allegedly awa) - the raw material is air, and there is no shortage of that.\nA redstone signal halts it (progress kept).",
    u"ja_jp": u"より安い（疑問あり awa）酸素の供給源 —— 原料は空気、いくらでもあります。\nレッドストーン信号で停止（進捗は保持）。",
    u"ru_ru": u"Более дешёвый (якобы awa) источник кислорода — сырьё это воздух, а его хватает всем.\nСигнал редстоуна останавливает (прогресс сохраняется).",
    u"lzh": u"更廉（存疑 awa）之氧氣來源 —— 原料即空氣，取之不竭。\n有紅石信號即停機（進度猶存）。",
}

T[u"tooltip.potato_s_t.ammonia_synthesis_chamber"] = {
    u"en_us": u"The catalyst slot takes Iron Dust.\nThe gas tank slots under the input tanks push nitrogen and hydrogen into the machine at 50 mB/t.\nThe gas tank slot under the output tank runs the other way: 50 mB/t, putting ammonia into a tank.\nPumps can only bring nitrogen and hydrogen in, and take ammonia out. A redstone signal halts it.",
    u"ja_jp": u"触媒スロットには鉄粉を入れてください。\n原料タンクの下のガスタンクスロットは 50 mB/t で、タンク内の窒素 / 水素を機械へ送り込みます。\n出力タンクの下のガスタンクスロットは逆方向：50 mB/t でアンモニアをタンクへ入れます。\nポンプでできるのは窒素 / 水素の注入とアンモニアの排出だけ。レッドストーン信号で停止します。",
    u"ru_ru": u"В слот катализатора нужна железная пыль.\nСлот баллона под входным баком подаёт азот и водород в машину со скоростью 50 mB/т.\nСлот баллона под выходным баком работает наоборот: 50 mB/т, закачивая аммиак в баллон.\nНасосы умеют только подавать азот и водород и откачивать аммиак. Сигнал редстоуна останавливает машину.",
    u"lzh": u"催化劑槽須置鐵粉。\n原料罐下方之氣罐槽，按 50 mB/t 以氣罐中之氮 / 氫灌入機器；\n輸出罐下方之氣罐槽則逆之：50 mB/t，以氨氣灌入氣罐。\n泵唯可泵入氮氣 / 氫氣、泵出氨氣；有紅石信號即停機。",
}

T[u"tooltip.potato_s_t.combustion_chamber"] = {
    u"en_us": u"The fuel slot takes anything a vanilla furnace burns (Lava Bucket 10 s, Diesel / Gasoline Bucket 30 s, everything else 3 s).\nOne batch of fuel + 10 mB Oxygen starts the reaction; while it runs it feeds 800 power per tick to the Power Capturer (diesel 1200 / gasoline 1000)\nLogs -> 10 mB Carbon Dioxide + 1 Charcoal; Diesel / Gasoline Buckets -> 200 mB Carbon Dioxide + 50 mB Water; anything else -> 5 mB Carbon Dioxide.\nThe oxygen tank is input-only (pipe in, or right-click with a gas tank); the carbon dioxide and water tanks are output-only (pump them out). A redstone signal halts it.",
    u"ja_jp": u"燃料スロットにはバニラのかまどが燃料と認めるもの（溶岩入りバケツは 10 秒、ディーゼル / ガソリン入りバケツは 30 秒、それ以外は 3 秒）。\n燃料 1 個 + 酸素 10 mB で反応が始まります。反応中は毎 tick、動力エネルギーキャプチャーへ 800 動力（ディーゼル 1200 / ガソリン 1000）\n原木 → 二酸化炭素 10 mB + 木炭 1 個。ディーゼル / ガソリン入りバケツ → 二酸化炭素 200 mB + 水 50 mB。それ以外 → 二酸化炭素 5 mB。\n酸素タンクは入るだけ（ポンプで送るか、ガスタンクで右クリック）。二酸化炭素と水のタンクは出るだけ（ポンプで抜く）。レッドストーン信号で停止します。",
    u"ru_ru": u"В слот топлива подходит всё, что принимает обычная печь (ведро лавы — 10 с, ведро дизеля или бензина — 30 с, остальное — 3 с).\nОдна единица топлива + 10 mB кислорода запускают реакцию; пока она идёт, машина отдаёт уловителю энергии 800 единиц за тик (дизель — 1200, бензин — 1000)\nБрёвна → 10 mB углекислого газа + 1 древесный уголь; вёдра дизеля и бензина → 200 mB углекислого газа + 50 mB воды; всё остальное → 5 mB углекислого газа.\nБак кислорода работает только на вход (насос или ПКМ баллоном); баки углекислого газа и воды — только на выход (откачивайте насосом). Сигнал редстоуна останавливает машину.",
    u"lzh": u"燃料槽置原版熔爐所認之燃料（岩漿桶 10 秒、柴油 / 汽油桶 30 秒，其餘 3 秒）。\n耗 1 份燃料 + 10 mB 氧氣乃始反應；反應之際每 tick 與動力能源捕獲器 800 點動力（柴油 1200 / 汽油 1000）\n原木 → 10 mB 二氧化碳 + 1 個木炭；柴油 / 汽油桶 → 200 mB 二氧化碳 + 50 mB 水；其餘 → 5 mB 二氧化碳。\n氧氣罐只進不出（接泵，或以氣罐右鍵倒）；二氧化碳罐與水罐只出不進（接泵抽走）。有紅石信號即停機。",
}

T[u"tooltip.potato_s_t.acidic_reaction_chamber"] = {
    u"en_us": u"Draws 500 FE/t\nFriendly advice: whatever comes out of here, do not drink it.",
    u"ja_jp": u"消費電力 500 FE/t\nひとつ忠告：ここでできたものは、飲まないでください。",
    u"ru_ru": u"Расход 500 FE/т\nДружеский совет: то, что здесь получается, пить не стоит.",
    u"lzh": u"耗電 500 FE/t\n友情之告：此中所產，請勿飲之。",
}

T[u"tooltip.potato_s_t.vibranium_set"] = {
    u"en_us": u"Vibranium set: a body that does not yield.\nUnbreakable, and it scarcely answers the enchanting table (enchantment weight 2, the lowest in the game) - it needs no adornment.\nWith all four: Resistance I at all times, in any hour and any dimension; immunity to fall damage; projectiles do nothing, and what flies at you returns along its own path at half speed; explosions are halved; knockback does not exist.\nAnd for every blow taken, there is a 10% chance it is given back exactly as it came - the body never takes; it only returns.",
    u"ja_jp": u"ヴィブラニウムセット：朽ちぬ身体。\n4 部位すべて耐久無限、エンチャント台とはほとんど共鳴しない（エンチャント適性 2、全ゲーム中最低）――飾られる必要がないのだ。\n4 部位がそろうと：耐性 I が常時、昼夜も次元も問わない。落下ダメージ無効。投射物ダメージ無効、飛来する弾は半速で来た道を戻る。爆発ダメージは半分。あらゆるノックバックを無効化。\n受け止めるたび、10% の確率でその一撃はあるがまま返される――この身体は奪わず、ただ返すだけ。",
    u"ru_ru": u"Набор вибраниума: тело, что не уступает.\nНеразрушим, и едва откликается столу зачаровывания (вес зачарования 2, самый низкий в игре) — ему не нужны украшения.\nВсе четыре вместе: Сопротивление I постоянно, в любой час и любом измерении; иммунитет к урону от падения; снаряды не вредят, а летящее в вас возвращается своим же путём на половинной скорости; взрывы вдвое слабее; отбрасывания нет.\nИ за каждый принятый удар есть 10% шанс вернуть его в точности таким, каким он пришёл — тело не отнимает, оно лишь возвращает.",
    u"lzh": u"振金套：不朽之軀。\n全套耐久無限，幾不與附魔臺共鳴（附魔權重 2，全遊戲最低）——固無須修飾。\n四件同在之時：抗性提升 I 常駐，不分晝夜與維度；摔落傷害免疫；彈射物傷害免疫，飛來之箭矢以半速循原路而退；爆炸傷害減半；一切擊退免疫。\n每一次承受，皆有 10% 之數原樣奉還 —— 此軀從不索取，唯還其力道耳。",
}

T[u"tooltip.potato_s_t.titanium_alloy_set"] = {
    u"en_us": u"Titanium Alloy set: a balance of temper and enchantment.\nIt answers the enchanting table more readily than gold, and endures more besides.",
    u"ja_jp": u"チタン合金セット：靭さとエンチャントの均衡。\n金よりエンチャント台に応え、金より耐える。",
    u"ru_ru": u"Титановый набор: равновесие закалки и зачарования.\nСтол зачаровывания отвечает охотнее, чем золоту, и держит удар крепче.",
    u"lzh": u"鈦合金套：堅韌與附魔之衡。\n較金更得附魔臺之青睞，亦較金更能當之。",
}

T[u"tooltip.potato_s_t.star_steel_set"] = {
    u"en_us": u"Star Steel set: in tune with the night.\nWhen darkness falls, every piece grants Resistance I, and the gear does not wear. The power of Star Steel goes further than that - the helmet opens a sight beyond sight.\nAll four in resonance reveal its true form: no wear in the End.\nThe void cannot take you either - it finds you solid ground within 20x20, catching you first and erasing the fall; where nothing stands, it trades your place with a creature nearby.",
    u"ja_jp": u"星燦鋼セット：夜と共鳴する。\n闇が下りると各部位が耐性 I を得て、装備は摩耗しない。星燦鋼の力はそれだけではない――ヘルメットは視界の外を照らす。\n4 部位が共振して初めて本来の姿になる：エンドでは摩耗しない。\nヴォイドもあなたを奪えない――20×20 内に足場を見つけ、まず受け止めてから落下を消す。何も無ければ、近くの生物と場所を交換する。",
    u"ru_ru": u"Набор звёздной стали: в лад с ночью.\nС наступлением тьмы каждая часть даёт Сопротивление I, и снаряжение не изнашивается. Сила звёздной стали на этом не кончается — шлем открывает зрение за пределами зрения.\nВсе четыре в резонансе являют истинную форму: в Крае прочность не тратится вовсе.\nИ пустота вас не заберёт — она найдёт опору в пределах 20×20, сначала подхватит, а после сотрёт падение; где опоры нет — обменяет вас местами с ближним существом.",
    u"lzh": u"星璨鋼套：與夜同頻。\n夜幕既落，每一件皆得抗性提升 I；此時裝備不損。星璨鋼之力不止於此 —— 胄亦照及形貌之外。\n四件共振，方是其真形：終界之中永不損。\n虛空亦奪爾不去 —— 其將於 20×20 內為爾尋一落腳之方塊，先托爾、再抹去墜落；若四下無物，則與近旁生物易位。",
}

T[u"advancements.potato_s_t.acid.description"] = {
    u"en_us": u"The strong backbone of the chemical industry - and by the way, when do we get carbonated drinks?",
    u"ja_jp": u"化学工業の強力な支え —— ところで炭酸飲料はいつ出るんですか？",
    u"ru_ru": u"Мощная опора химической промышленности — и кстати, когда уже будут газированные напитки?",
    u"lzh": u"化工之勁柱也，話說何時出碳酸飲料邪？",
}

T[u"advancements.potato_s_t.alloy_smelter.description"] = {
    u"en_us": u"Where the alloys begin",
    u"ja_jp": u"合金たちの起点",
    u"ru_ru": u"Начало всех сплавов",
    u"lzh": u"合金之起點",
}

T[u"advancements.potato_s_t.blast_furnace.description"] = {
    u"en_us": u"A 3×3×3 multiblock machine, and a step up in output",
    u"ja_jp": u"3×3×3 のマルチブロック機械、生産量の向上",
    u"ru_ru": u"Мультиблок 3×3×3: шаг вперёд по выработке",
    u"lzh": u"一棟 3×3×3 之多方塊機器，產能之進",
}

T[u"advancements.potato_s_t.capacitor.description"] = {
    u"en_us": u"This is a supercapacitor!",
    u"ja_jp": u"これはスーパーコンデンサです！",
    u"ru_ru": u"Это же суперконденсатор!",
    u"lzh": u"此乃超級電容也！",
}

T[u"advancements.potato_s_t.capacitor.title"] = {
    u"en_us": u"Faraday's Might",
    u"ja_jp": u"ファラデーの威力",
    u"ru_ru": u"Мощь Фарадея",
    u"lzh": u"法拉第之威",
}

T[u"advancements.potato_s_t.combustion.description"] = {
    u"en_us": u"A charcoal enthusiast",
    u"ja_jp": u"木炭の愛好家",
    u"ru_ru": u"Любитель древесного угля",
    u"lzh": u"木炭之青睞者",
}

T[u"advancements.potato_s_t.crushing.description"] = {
    u"en_us": u"Can a crusher crush a crusher that is crushing a crusher?",
    u"ja_jp": u"粉砕機を粉砕している粉砕機を、粉砕機で粉砕できますか？",
    u"ru_ru": u"Можно ли дробилкой раздробить дробилку, которая дробит дробилку?",
    u"lzh": u"可以粉碎機碎那正在碎粉碎機的粉碎機麼？",
}

T[u"advancements.potato_s_t.distillation.description"] = {
    u"en_us": u"By the power of physics, split crude oil into diesel, gasoline, naphtha....",
    u"ja_jp": u"物理学の力で、原油をディーゼル、ガソリン、ナフサに....",
    u"ru_ru": u"Силой физики разделите нефть на дизель, бензин, нафту....",
    u"lzh": u"賴物理之力，析原油為柴油、汽油、石腦油....",
}

T[u"advancements.potato_s_t.distillation.title"] = {
    u"en_us": u"Five Equal Parts of Crude Oil",
    u"ja_jp": u"五等分の原油",
    u"ru_ru": u"Нефть на пять равных частей",
    u"lzh": u"五等份之原油",
}

T[u"advancements.potato_s_t.electrolyzer.description"] = {
    u"en_us": u"In reality, this is a real power hog!",
    u"ja_jp": u"現実ではこれは電気の大食らい！",
    u"ru_ru": u"В реальности это настоящий обжора электричества!",
    u"lzh": u"此乃現實中之電老虎也！",
}

T[u"advancements.potato_s_t.first_power.description"] = {
    u"en_us": u"Industrial revolution!!",
    u"ja_jp": u"産業革命！！",
    u"ru_ru": u"Промышленная революция!!",
    u"lzh": u"工業革命！！",
}

T[u"advancements.potato_s_t.fuel.description"] = {
    u"en_us": u"Two liquid fuels, stubborn the elder, and the younger just as stubborn",
    u"ja_jp": u"2 種の液体燃料。兄貴は頑固、弟も頑固",
    u"ru_ru": u"Два жидких топлива: старший — упрямец, младший — тоже упрямец",
    u"lzh": u"二種液體燃料，長者性倔，次者亦倔",
}

T[u"advancements.potato_s_t.hard_alloy.description"] = {
    u"en_us": u"This stuff is actually aerospace material",
    u"ja_jp": u"これ、実は航空宇宙材料です",
    u"ru_ru": u"Вообще-то это авиационный материал",
    u"lzh": u"此物實乃航空之材",
}

T[u"advancements.potato_s_t.light_alloy.description"] = {
    u"en_us": u"A gear revolution",
    u"ja_jp": u"装備の改革",
    u"ru_ru": u"Революция в снаряжении",
    u"lzh": u"裝備之改革",
}

T[u"advancements.potato_s_t.music_disc_anvil.description"] = {
    u"en_us": u"The Republic shows no mercy to those who only know how to work the anvil",
    u"ja_jp": u"共和国は金床を打つだけのお前を憐れまない",
    u"ru_ru": u"Республика не помилует того, кто умеет только бить по наковальне",
    u"lzh": u"共和國不憫唯知打鐵之爾",
}

T[u"advancements.potato_s_t.music_disc_anvil.title"] = {
    u"en_us": u"Anvil of the Republic (or should that be Chastity?)",
    u"ja_jp": u"共和国の金床（あるいは 貞？）",
    u"ru_ru": u"Наковальня Республики (или всё-таки «целомудрие»?)",
    u"lzh": u"共和國之砧（抑或 貞？）",
}

T[u"advancements.potato_s_t.music_disc_jasmine.description"] = {
    u"en_us": u"What a beautiful jasmine flower~",
    u"ja_jp": u"なんと美しいジャスミンの花よ〜",
    u"ru_ru": u"Ах, какой прекрасный цветок жасмина~",
    u"lzh": u"好一朵美麗之茉莉花～",
}

T[u"advancements.potato_s_t.pressing.description"] = {
    u"en_us": u"The hydraulic press turns ingots into plates - the common part of nearly every machine",
    u"ja_jp": u"油圧プレスがインゴットを板に —— 板はほぼすべての機械の共通部品",
    u"ru_ru": u"Пресс превращает слитки в пластины — общая деталь почти любой машины",
    u"lzh": u"液壓機壓錠為板 —— 板者，幾乎諸機通用之件也",
}

T[u"advancements.potato_s_t.stable_block.description"] = {
    u"en_us": u"The Acidic Reaction Chamber wants it",
    u"ja_jp": u"酸性反応室が欲しがります",
    u"ru_ru": u"Нужен кислотной камере",
    u"lzh": u"酸性反應室需之",
}

T[u"advancements.potato_s_t.steel.description"] = {
    u"en_us": u"Steel is the skeleton of nearly everything that comes after",
    u"ja_jp": u"鋼はこの先ほぼすべての骨格です",
    u"ru_ru": u"Сталь — скелет почти всего дальнейшего",
    u"lzh": u"鋼者，此後百器之骨也",
}

T[u"advancements.potato_s_t.wiring.description"] = {
    u"en_us": u"Remote transmission!",
    u"ja_jp": u"遠隔送電！",
    u"ru_ru": u"Передача на расстояние!",
    u"lzh": u"遠程傳輸！",
}

T[u"advancements.potato_s_t.fluid_logistics.description"] = {
    u"en_us": u"Does this thing spray chocolate syrup?",
    u"ja_jp": u"ここからチョコレートシロップが噴き出すんですか？",
    u"ru_ru": u"А шоколадный сироп отсюда брызжет?",
    u"lzh": u"此中將噴巧克力漿乎？",
}

T[u"advancements.potato_s_t.lithium_battery.description"] = {
    u"en_us": u"Quantity turns into quality",
    u"ja_jp": u"量が質に変わる",
    u"ru_ru": u"Количество переходит в качество",
    u"lzh": u"量變而質變",
}

T[u"advancements.potato_s_t.lithium_battery_plant.description"] = {
    u"en_us": u"Energy storage is expensive, y'know",
    u"ja_jp": u"蓄電ってのは高いんですよ、はい",
    u"ru_ru": u"Накопитель энергии — удовольствие дорогое, да",
    u"lzh": u"儲能可是很貴噠",
}

T[u"advancements.potato_s_t.oil_pump.description"] = {
    u"en_us": u"In an Ocean Oilfield, with a waterlogged chain below: that chain is n - drawing 8n²+80n FE/t for 10n mB/s",
    u"ja_jp": u"海洋油田に設置、真下の含水チェーンが n：消費 8n²+80n FE/t、産油 10n mB/s",
    u"ru_ru": u"В морском месторождении, цепь с водой под ним — это n: расход 8n²+80n FE/т при добыче 10n mB/с",
    u"lzh": u"立於海洋油田、正下方含水鎖鏈為 n：耗電 8n² + 80n FE/t，產油 10n mB/s",
}
T[u"advancements.potato_s_t.salt.description"] = {
    u"en_us": u"Grandfather Sun is now squeezing the sea for its ingredients - maybe add some electricity?",
    u"ja_jp": u"太陽のおじいちゃんが海の成分を搾り取り始めました —— 電気でも足してみますか？",
    u"ru_ru": u"Дедушка Солнце принялся выжимать из моря его состав — может, добавить электричества?",
    u"lzh": u"太陽公公始榨大海之成分矣，或可加之以電？",
}

T[u"advancements.potato_s_t.salt.title"] = {
    u"en_us": u"Demand Salt from the Sea",
    u"ja_jp": u"海に塩を求めて",
    u"ru_ru": u"Потребуй соль у моря",
    u"lzh": u"向海索鹽",
}

T[u"advancements.potato_s_t.star_steel.description"] = {
    u"en_us": u"This is absolutely not a product of Earth",
    u"ja_jp": u"これは絶対に地球の産物ではありません",
    u"ru_ru": u"Это абсолютно не земное изделие",
    u"lzh": u"此絕非地球上之產物",
}

T[u"advancements.potato_s_t.starfall.description"] = {
    u"en_us": u"Right-click to toss the pendant: a 30-second countdown, cancellable in the first 10",
    u"ja_jp": u"右クリックでペンダントを放つ：30 秒のカウントダウン、最初の 10 秒は取消可",
    u"ru_ru": u"ПКМ подвеской: отсчёт 30 секунд, первые 10 можно отменить",
    u"lzh": u"右鍵擲出星軌墜：30 秒倒數、前 10 秒可撤",
}

T[u"advancements.potato_s_t.vibranium.description"] = {
    u"en_us": u"Expensive raw materials",
    u"ja_jp": u"高価な原材料",
    u"ru_ru": u"Дорогое сырьё",
    u"lzh": u"昂貴之原料",
}

T[u"advancements.potato_s_t.vibranium_armor.description"] = {
    u"en_us": u"Kinetic absorption! Kid",
    u"ja_jp": u"運動エネルギー吸収！だぜ",
    u"ru_ru": u"Поглощение кинетики! Малыш",
    u"lzh": u"動能吸收！小子",
}

T[u"advancements.potato_s_t.titanium_armor.description"] = {
    u"en_us": u"You need this before you can have the vibranium set",
    u"ja_jp": u"ヴィブラニウムセットが欲しければ、まずこれ",
    u"ru_ru": u"Хочешь набор вибраниума — сначала собери это",
    u"lzh": u"欲得振金之套，必先有此",
}

T[u"advancements.potato_s_t.star_steel_tools.title"] = {
    u"en_us": u"A Collector's Habit",
    u"ja_jp": u"収集癖",
    u"ru_ru": u"Коллекционная привычка",
    u"lzh": u"收集癖",
}

T[u"advancements.potato_s_t.star_steel_tools.description"] = {
    u"en_us": u"Obtain a full set of Star Steel tools",
    u"ja_jp": u"星燦鋼の道具一式を手に入れる",
    u"ru_ru": u"Получите полный набор инструментов из звёздной стали",
    u"lzh": u"獲得星璨鋼工具一套",
}

T[u"advancements.potato_s_t.star_steel_slash.description"] = {
    u"en_us": u"When can we summon the Starlight Reaper?",
    u"ja_jp": u"いつになったら星輝の死神を召喚できるんですか？",
    u"ru_ru": u"Когда уже можно будет призвать Звёздного жнеца?",
    u"lzh": u"何時可以召喚星輝死神邪？",
}

T[u"advancements.potato_s_t.star_chart_tome.title"] = {
    u"en_us": u"Your Subject Observes the Heavens",
    u"ja_jp": u"臣、夜に天象を観る",
    u"ru_ru": u"Ваш слуга наблюдает небеса",
    u"lzh": u"臣夜觀天象",
}

T[u"advancements.potato_s_t.star_chart_tome.description"] = {
    u"en_us": u"All you see is illusion, yet this is the first step toward a new world...",
    u"ja_jp": u"見えるものはすべて幻、だがこれは新しい世界への第一歩...",
    u"ru_ru": u"Всё, что ты видишь, — иллюзия, но это первый шаг в новый мир...",
    u"lzh": u"所見之景皆為虛幻，然此乃通往新世界之第一步...",
}

T[u"advancements.potato_s_t.silver_wire.description"] = {
    u"en_us": u"The best heat and electricity conductor in nature",
    u"ja_jp": u"自然界で最高の熱伝導・電気伝導の材料",
    u"ru_ru": u"Лучший проводник тепла и тока в природе",
    u"lzh": u"自然界最善導熱導電之材",
}

T[u"tooltip.potato_s_t.star_chart.3"] = {
    u"en_us": u"Only you see it - the ignorant will never understand art",
    u"ja_jp": u"見えるのは自分だけ ― 愚か者に芸術は分かりません",
    u"ru_ru": u"Видно только вам — невежды в искусстве не смыслят",
    u"lzh": u"唯爾自見 —— 愚昧之人不解藝術",
}

T[u"tooltip.potato_s_t.starfall_pendant.3"] = {
    u"en_us": u"Impact: an explosion of power 7-20 plus a spray of raw ores - the higher the power, the better and the more",
    u"ja_jp": u"着弾：威力 7〜20 の爆発と粗鉱の飛散。威力が高いほど良質で多くなります",
    u"ru_ru": u"Удар: взрыв силой 7–20 и разлёт руды — чем выше сила, тем лучше и больше",
    u"lzh": u"落地：7~20 威力之爆，並噴出粗礦一批 —— 威力愈高，礦愈佳亦愈多",
}

T[u"tooltip.potato_s_t.starfall_pendant.4"] = {
    u"en_us": u"· 7-12: nothing but scrap raw iron / raw copper · 13+: any raw ore · 15+: 3 extra raw vibranium",
    u"ja_jp": u"· 7〜12：ガラクタの鉄の原石 / 銅の原石だけ · 13 以上：すべての粗鉱 · 15 以上：ヴィブラニウムの原石 ×3 追加",
    u"ru_ru": u"· 7–12: только хлам — рудное железо / рудная медь · 13+: любая руда · 15+: ещё 3 рудного вибраниума",
    u"lzh": u"· 7~12：唯破爛粗鐵 / 粗銅 · 13 以上：盡是粗礦 · 15 以上：另加 3 粗振金",
}

T[u"tooltip.potato_s_t.diesel_generator_controller"] = {
    u"en_us": u"How to lay out the Diesel Generator:\n1 Heat-Resistant Metal Block  2 Common Metal Block  3 Fluid Pump  4 Low-Tier Generator\n5 Combustion Chamber  6 Block of Copper  7 Copper Grate  8 Wiring Block  9 Diesel Generator Controller\nLayer 1 (bottom) | Layer 2\n1 3 1 | 2 1 2\n1 4 1 | 6 7 6\n1 5 1 | 6 7 6\n1 4 1 | 6 7 6\n1 9 1 | 2 8 2\nWith the controller's facing as the front, the machine runs 5 rows back and 2 layers up - not a single cell less.\nCopper blocks and grates: any oxidation level, waxed or not (all 16 count).\nOnce complete, the Wiring Block directly above the controller becomes a port (same texture, drops back as a Wiring Block) - and that is the only place power comes out.\nGUI: an 8000 mB diesel tank and a status lamp; 1 mB of diesel per tick makes 7200 FE; a redstone signal halts it.\nGetting diesel in: hook up a pump (controller or port), or right-click the controller with a Diesel Bucket or an oil bucket holding diesel.\n⚠ The Fluid Pump / two Low-Tier Generators / Combustion Chamber inside stay as they are - they are not consumed.",
    u"ja_jp": u"大型ディーゼル発電機の配置：\n1 耐熱金属ブロック　2 一般金属ブロック　3 流体ポンプ　4 低級発電機\n5 燃焼反応室　6 銅ブロック　7 銅グレーチング　8 配線ブロック　9 ディーゼル発電機コントローラー\n第 1 層（底面）｜第 2 層\n1 3 1 ｜ 2 1 2\n1 4 1 ｜ 6 7 6\n1 5 1 ｜ 6 7 6\n1 4 1 ｜ 6 7 6\n1 9 1 ｜ 2 8 2\nコントローラーの向きを正面として、背後へ 5 列・上へ 2 層、1 マスも欠かさずに。\n銅ブロックと銅グレーチング：酸化の度合いも、ろうを塗ったかも問いません（16 種すべて可）。\n組み上がると、コントローラー真上の配線ブロックが接続口になります（貼図は同じ、掘ると配線ブロックに戻る）—— 電力はそこからしか出ません。\n界面：8000 mB のディーゼルタンク ＋ 動作ランプ。毎 tick ディーゼル 1 mB を燃やして 7200 FE を発電、レッドストーン信号で停止します。\nディーゼルの入れ方：ポンプで送る（コントローラー本体でも接続口でも可）、またはディーゼル入りバケツ / ディーゼル入りオイルバケツを持ってコントローラーを右クリック。\n⚠ 中の流体ポンプ / 低級発電機 2 台 / 燃焼反応室は、成型後もそのまま残ります（消えません）。",
    u"ru_ru": u"Как выложить большой дизель-генератор:\n1 Жаростойкий металлический блок　2 Обычный металлический блок　3 Жидкостный насос　4 Простой генератор\n5 Камера сгорания　6 Медный блок　7 Медная решётка　8 Соединительный блок　9 Контроллер дизель-генератора\nСлой 1 (низ) | Слой 2\n1 3 1 | 2 1 2\n1 4 1 | 6 7 6\n1 5 1 | 6 7 6\n1 4 1 | 6 7 6\n1 9 1 | 2 8 2\nПеред — сторона, куда смотрит контроллер; машина уходит на 5 рядов назад и на 2 слоя вверх, ни одной клеткой меньше.\nМедные блоки и решётки: любая степень окисления, вощёные или нет (подходят все 16).\nКогда всё выложено, соединительный блок прямо над контроллером становится портом (текстура та же, при разрушении возвращается соединительным блоком) — и энергия выходит только оттуда.\nИнтерфейс: бак дизеля на 8000 mB и лампа работы; 1 mB дизеля за тик даёт 7200 FE; сигнал редстоуна останавливает.\nКак подать дизель: насосом (в контроллер или в порт) либо щёлкнув ПКМ по контроллеру ведром дизеля или нефтяным ведром с дизелем.\n⚠ Жидкостный насос / два простых генератора / камера сгорания внутри остаются собой — их не съедает.",
    u"lzh": u"大型柴油發電機擺放之式：\n1 耐熱金屬塊　2 一般金屬塊　3 流體泵　4 低級發電機\n5 燃燒反應室　6 銅塊　7 銅格柵　8 接線塊　9 柴油發電機控制器\n第 1 層（底）｜第 2 層\n1 3 1 ｜ 2 1 2\n1 4 1 ｜ 6 7 6\n1 5 1 ｜ 6 7 6\n1 4 1 ｜ 6 7 6\n1 9 1 ｜ 2 8 2\n以控制器所向為正面，機器向其背後鋪 5 排、向上 2 層，一格不可少。\n銅塊與銅格柵：氧化至何度、曾打蠟否皆可（16 種全收）。\n擺齊之後，控制器正上方那格接線塊將化為接線口（貼圖相同，掘之則還為接線塊）—— 電只自彼處出。\n界面：一 8000 mB 柴油罐 ＋ 一盞作工之燈；每 tick 焚 1 mB 柴油發 7200 FE，有紅石信號即停機。\n柴油何入：接泵灌之（控制器本體或接線口皆可），或持柴油桶 / 盛柴油之油桶右鍵控制器。\n⚠ 內中流體泵 / 低級發電機二台 / 燃燒反應室一台，成型之後仍舊是其自身，不會被吞。",
}

T[u"gui.potato_s_t.diesel_generator.status.output_full"] = {
    u"en_us": u"Power has nowhere to go",
    u"ja_jp": u"電力を送り出せません",
    u"ru_ru": u"Энергию некуда девать",
    u"lzh": u"電送不出",
}


def read_val(loc, key):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)[key]


def main():
    edits = []
    lzh_pairs = []
    for key, per in sorted(T.items()):
        for loc, new in sorted(per.items()):
            old = read_val(loc, key)
            if old == new:
                continue
            if loc == u"lzh":
                lzh_pairs.append((key, old, new))
            else:
                edits.append((loc, key, old, new))

    import _rzh_fix_batch as fb
    fb.EDITS = edits
    rc = fb.main()

    if lzh_pairs:
        import _rzh_lzh_set as ls
        ls.apply(lzh_pairs, u"lzh 用户改动的四语同步")
    return rc


if __name__ == u"__main__":
    sys.exit(main())
