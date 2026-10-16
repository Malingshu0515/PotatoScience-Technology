# -*- coding: utf-8 -*-
r"""_rzh_ztrans2.py —— 第二批：把用户又一次手改的中文（19 键）铺到 en / ja / ru / lzh。

用户原话：「同步一下翻译吧~ 中文是我改了一边的 参考就行**不要改中文文件**」。

所以这一轮**一个字节都不写 zh_cn.json** —— 它只当参考。脚本自己也不碰它：
表里根本没有 zh_cn 这一项，`_rzh_fix_batch` 只按 EDITS 里的语言写盘。

旧值一律**运行时读盘**（`read_val`），绝不手抄 —— 上一轮手抄过一次，
因并行会话重润色而对不上，整批被拒。

语气照用户的写法走（他这轮加了玩梗，就译出玩梗；他砍掉的解释，四语也一并砍）：
  · `gravity.not_full` 的「我是贪得无厌的必须给我8mFE的电力，吃不饱不干活，就这样，免谈！！」
  · `gravity.interrupted` 的「孩子你拉完了，不要后悔啊」
  · 成就标题「就这个饮料我直接爽吃」「我成为了死神」「矿物磁铁的亲戚」
  · 成就说明「可乐还是可口的好！你们不准喝别的！！！」
  · 引力装置说明「技术总是有两面性，破坏性与帮助性，区别为人们该怎样使用它」

⚠ 事实核对（翻之前查过代码，不然会把错的翻进四语）：
  · `OreDetectorItem`：`CAPACITY=1200` / `COST=600` / `CHUNK_RADIUS=1`（⇒ 3×3 区块）/ `MAX_Y=45`
  · `GravityDeviceItem`：`CAPACITY=8_000_000` / `CHARGE_TICKS=20*25`（25 秒）/ `toggleMode` = **Shift+左键**
  用户新写的 tooltip 只提 3×3 与 8M FE/模式切换，**y≤45 与 25 秒仍是真的**，
  它们仍在别的键里（`ore_detector.none.chat` 写着 y≤45；`gravity_device` 的 25 秒在代码与其它提示里），
  所以按用户写的翻，不给他加回他没写的字。

用法：`python build/zftools/_rzh_ztrans2.py`
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

T = {}

# --- 01/02 工具提示 ---------------------------------------------------------
T[u"tooltip.potato_s_t.ore_detector"] = {
    u"en_us": u"Spends power to detect the nearest ore within 3x3 chunks",
    u"ja_jp": u"電力を消費し、3×3 チャンク内で最も近い鉱物を探知します",
    u"ru_ru": u"Расходует энергию, чтобы найти ближайшую руду в 3x3 чанках",
    u"lzh": u"耗電以探三乘三區內最近之一礦",
}

T[u"tooltip.potato_s_t.gravity_device"] = {
    u"en_us": u"Single-use item, holds 8 million FE when full. Before use, put the target block in your offhand; Shift + left-click to switch modes",
    u"ja_jp": u"使い切りの品。満充電で 800 万 FE。使う前にオフハンドへ目標ブロックを置き、Shift + 左クリックでモード切替",
    u"ru_ru": u"Одноразовый предмет, в полном заряде 8 миллионов FE. Перед использованием положите нужный блок во вторую руку; Shift + ЛКМ переключает режимы",
    u"lzh": u"一次性之物，滿電八百萬 FE。用之前須置目標方塊於副手，Shift + 左鍵切換其模",
}

# --- 03..11 消息 ------------------------------------------------------------
T[u"message.potato_s_t.ore_detector.no_power"] = {
    u"en_us": u"Not enough power: %s FE, %s FE required",
    u"ja_jp": u"電力不足：現在 %s FE、必要 %s FE",
    u"ru_ru": u"Не хватает энергии: %s FE, нужно %s FE",
    u"lzh": u"電力不足：今 %s FE，所需 %s FE",
}

T[u"message.potato_s_t.ore_detector.arrow"] = {
    u"en_us": u"It is %s (x/z)",
    u"ja_jp": u"それは %s （x/z）",
    u"ru_ru": u"Оно %s (x/z)",
    u"lzh": u"其在 %s （x/z）",
}

T[u"message.potato_s_t.gravity.need_offhand"] = {
    u"en_us": u"Put the target block in your offhand first",
    u"ja_jp": u"まずオフハンドに目標ブロックを置いてください",
    u"ru_ru": u"Сначала положите нужный блок во вторую руку",
    u"lzh": u"須先置目標方塊於副手",
}

# 用户把「要充满才能放」改成一段撒泼式玩笑 —— 照着译，别翻成正经说明
T[u"message.potato_s_t.gravity.not_full"] = {
    u"en_us": u"Not enough juice: %s / %s FE (I am insatiably greedy - hand me a full 8M FE or I do not work, and that is that. No deal!!)",
    u"ja_jp": u"蓄電不足：%s / %s FE（私は底なしに貪欲です —— 8M FE を満タンで寄越さない限り働きません。以上、交渉の余地なし！！）",
    u"ru_ru": u"Недостаточно заряда: %s / %s FE (я бездонно жаден — подавай полные 8M FE, иначе не работаю. Вот и всё, разговор окончен!!)",
    u"lzh": u"儲能不足：%s / %s FE（吾貪得無厭，必與我八百萬 FE 之滿電，不飽則不作，如是而已，毋庸再議！！）",
}

T[u"message.potato_s_t.gravity.cancel_offhand"] = {
    u"en_us": u"The offhand block is gone, charge interrupted",
    u"ja_jp": u"オフハンドのブロックが消え、チャージ中断",
    u"ru_ru": u"Блок из второй руки пропал, зарядка прервана",
    u"lzh": u"副手方塊已失，蓄力中斷",
}

T[u"message.potato_s_t.gravity.charging"] = {
    u"en_us": u"Charging gravity: %s%%",
    u"ja_jp": u"重力チャージ中：%s%%",
    u"ru_ru": u"Зарядка гравитации: %s%%",
    u"lzh": u"引力蓄力中：%s%%",
}

T[u"message.potato_s_t.gravity.interrupted"] = {
    u"en_us": u"There, you pulled it and let go - no regrets now",
    u"ja_jp": u"引いて離したな、後悔するなよ",
    u"ru_ru": u"Ну вот, натянул и отпустил — не жалей теперь",
    u"lzh": u"孺子既引而釋矣，勿悔也",
}

T[u"message.potato_s_t.gravity.fired"] = {
    u"en_us": u"A black hole forms: it starts pulling in %s",
    u"ja_jp": u"ブラックホール発生：%s を吸い始めました",
    u"ru_ru": u"Чёрная дыра сформирована: начинает втягивать %s",
    u"lzh": u"黑洞既成：始吸取 %s",
}

T[u"message.potato_s_t.gravity_done"] = {
    u"en_us": u"Black hole collapsed: %s blocks pulled in, %s stacked, %s blocks turned into item drops for lack of space",
    u"ja_jp": u"ブラックホール崩壊：%s 個を吸引、%s 個を積み上げ、置き場所がなくドロップになったブロック %s 個",
    u"ru_ru": u"Чёрная дыра схлопнулась: втянуто %s блоков, уложено %s, %s блоков выпали предметами из-за нехватки места",
    u"lzh": u"黑洞坍縮：吸引 %s 塊，堆放 %s 塊，無處可置而墮為掉落物者 %s 塊",
}

# --- 12/13 模式名（用户砍掉了尾随解释）-------------------------------------
T[u"message.potato_s_t.gravity.mode.swallow"] = {
    u"en_us": u"Mode: Swallow",
    u"ja_jp": u"モード：捕食搬送",
    u"ru_ru": u"Режим: поглощение",
    u"lzh": u"模式：吞噬搬運",
}

T[u"message.potato_s_t.gravity.mode.tow"] = {
    u"en_us": u"Mode: Gravity Tow",
    u"ja_jp": u"モード：重力牽引",
    u"ru_ru": u"Режим: гравитационная тяга",
    u"lzh": u"模式：引力牽引",
}

# --- 14..19 成就 ------------------------------------------------------------
T[u"advancements.potato_s_t.beverage_canning_machine.title"] = {
    u"en_us": u"I'm Chugging This One Straight Down",
    u"ja_jp": u"この飲み物は一気にいく",
    u"ru_ru": u"Эту банку я выпью залпом",
    u"lzh": u"此飲吾直爽飲之",
}

T[u"advancements.potato_s_t.beverage_canning_machine.description"] = {
    u"en_us": u"Cola is best when it is Coca! None of you are allowed to drink anything else!!!",
    u"ja_jp": u"コーラはやっぱりコカのが一番！他のを飲むのは禁止！！！",
    u"ru_ru": u"Кола хороша только «Кока»! Всем запрещено пить что-либо другое!!!",
    u"lzh": u"可樂還是可口者佳！爾等不許飲他物！！！",
}

T[u"advancements.potato_s_t.ore_detector.title"] = {
    u"en_us": u"A Relative of the Ore Magnet",
    u"ja_jp": u"鉱物磁石の親戚",
    u"ru_ru": u"Родня рудного магнита",
    u"lzh": u"礦物磁鐵之親戚",
}

T[u"advancements.potato_s_t.ore_detector.description"] = {
    u"en_us": u"Craft an Ore Detector",
    u"ja_jp": u"鉱物探知機を作る",
    u"ru_ru": u"Создайте детектор руды",
    u"lzh": u"合出礦物探測器",
}

T[u"advancements.potato_s_t.gravity_device.title"] = {
    u"en_us": u"I Have Become Death",
    u"ja_jp": u"私は死神になった",
    u"ru_ru": u"Я стал смертью",
    u"lzh": u"我成為死神矣",
}

T[u"advancements.potato_s_t.gravity_device.description"] = {
    u"en_us": u"Technology always cuts both ways, destructive and helpful; the difference is how people choose to use it",
    u"ja_jp": u"技術には常に二面性がある。破壊と救済、その違いは人がどう使うかにある",
    u"ru_ru": u"У технологии всегда две стороны — разрушительная и полезная; разница лишь в том, как люди решат её использовать",
    u"lzh": u"技藝恆有兩面，破壞也，扶助也，其別在人之何以用之",
}

# --- 20..22 英式拼写收口 -----------------------------------------------------
# ⚠ 这三条**不是用户这轮改的**，是别的线新加的 `guide.*` 词条。它们是英文文案，
#   落在我的语言文件里，而 `_rzh_fix_batch` 的禁用词表本来就有 `aluminium` 这一条
#   （历史：user 的那批里 en_us 出现 5 处英式拼写）。盘上现状是：
#     · **所有物品名**都是美式 —— Aluminum Ingot / Aluminum Ore / Aluminum Plate /
#       Block of Raw Aluminum / Raw Aluminum / Aluminum Nugget / Empty Aluminum Can
#     · 连成就与其他提示也都是 Aluminum
#     · 只有这 3 条 guide 词条写成了英式 ⇒ 同一个材质在同一份语言文件里两种拼法。
#   按既有规则收口成美式（**只动这一个词，句子其余部分一字不改**）。
_GUIDE_AL = [
    u"potato_s_t.guide.entry.power.storage.p2",
    u"potato_s_t.guide.entry.materials.ore_chain.p1",
    u"potato_s_t.guide.entry.materials.ore_chain.p2",
]


def read_val(loc, key):
    with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
        return json.load(f)[key]


def main():
    if u"zh_cn" in set(loc for per in T.values() for loc in per):
        raise SystemExit(u"[拒绝] 表里出现了 zh_cn —— 用户明确说不要改中文文件")

    edits, lzh_pairs = [], []
    for key, per in sorted(T.items()):
        for loc, new in sorted(per.items()):
            old = read_val(loc, key)
            if old == new:
                continue
            if loc == u"lzh":
                lzh_pairs.append((key, old, new))
            else:
                edits.append((loc, key, old, new))

    # 英式拼写收口：只把那一个词换掉，句子其余部分**一字不改**（所以新值必须
    # 从盘上读出来的旧值派生，不能手抄 —— 手抄就是上一轮被整批拒绝的那个坑）。
    for key in _GUIDE_AL:
        old = read_val(u"en_us", key)
        new = old.replace(u"aluminium", u"aluminum")
        if new == old:
            continue
        if u"aluminium" not in old:
            raise SystemExit(u"[拒绝] %s 里没有 aluminium —— 与我以为的不一样" % key)
        edits.append((u"en_us", key, old, new))

    import _rzh_fix_batch as fb
    # 旧替换表的命中数会被别的线加的内容搅动（本轮不涉及那些串）⇒ 显式跳过，
    # 改由 _rzh_zverify2.py 按 key 逐条复核"该消失的消失了"。
    fb.SUBSTITUTIONS = []
    fb.REGEX_SUBST = []
    fb.EDITS = edits
    rc = fb.main()

    if lzh_pairs:
        import _rzh_lzh_set as ls
        ls.apply(lzh_pairs, u"lzh 第二批同步")
    return rc


if __name__ == u"__main__":
    sys.exit(main())
