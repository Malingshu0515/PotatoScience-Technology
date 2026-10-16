# -*- coding: utf-8 -*-
r"""_rzh_zverify2.py —— 第二批（19 键 + 3 条拼写）的收口验证。

三条硬判据：
  Z0 **用户的中文文件一个字节都没被我碰** —— 用 `git diff --numstat` 读盘上事实，
     断言仍是「19 增 19 删」（这是他这轮改动的签名；我若碰过，行数必然变）。
  Z1/Z2 逐 key 的"旧文案必须消失"与"新文案/梗/机制必须在"，**按 key 作用域**
     （§4.154 的教训：文件级扫描会把通用词扫到无关键上，那种命中不是残留）。
  Z3 结构只查**本轮动过的键**（我的活儿的结构正确性），并单独把那条
     **属于别的线、不是本轮**的占位符问题报成「已知既有」（见 KNOWN_OTHER）。

⚠ 挑"必须消失"的锚点时，先拿去**新值**里搜一遍 —— 搜得到就说明锚点不够长
  （§4.155；这一轮又复现了三次：`Charging gravity:` 是新值的前缀、
  `吸い始めました` 也在新值里、ja/ru 的 `no_power` 压根没改）。

用法：`python build/zftools/_rzh_zverify2.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
GIT = r"C:\Program Files\Git\cmd\git.exe"
OUT = os.path.join(HERE, u"_rzh_zverify2.txt")
LOCS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

T_TOOL_OD = u"tooltip.potato_s_t.ore_detector"
T_TOOL_GD = u"tooltip.potato_s_t.gravity_device"
M_NO_POWER = u"message.potato_s_t.ore_detector.no_power"
M_ARROW = u"message.potato_s_t.ore_detector.arrow"
M_OFFHAND = u"message.potato_s_t.gravity.need_offhand"
M_NOTFULL = u"message.potato_s_t.gravity.not_full"
M_CANCEL = u"message.potato_s_t.gravity.cancel_offhand"
M_CHARGING = u"message.potato_s_t.gravity.charging"
M_INTERRUPT = u"message.potato_s_t.gravity.interrupted"
M_FIRED = u"message.potato_s_t.gravity.fired"
M_DONE = u"message.potato_s_t.gravity_done"
M_MODE_SW = u"message.potato_s_t.gravity.mode.swallow"
M_MODE_TOW = u"message.potato_s_t.gravity.mode.tow"
A_CAN_T = u"advancements.potato_s_t.beverage_canning_machine.title"
A_CAN_D = u"advancements.potato_s_t.beverage_canning_machine.description"
A_OD_T = u"advancements.potato_s_t.ore_detector.title"
A_OD_D = u"advancements.potato_s_t.ore_detector.description"
A_GD_T = u"advancements.potato_s_t.gravity_device.title"
A_GD_D = u"advancements.potato_s_t.gravity_device.description"
G_GUIDE1 = u"potato_s_t.guide.entry.power.storage.p2"
G_GUIDE2 = u"potato_s_t.guide.entry.materials.ore_chain.p1"
G_GUIDE3 = u"potato_s_t.guide.entry.materials.ore_chain.p2"

# 本条线动过的键（Z3 的结构检查只查这些）
TOUCHED = [T_TOOL_OD, T_TOOL_GD, M_NO_POWER, M_ARROW, M_OFFHAND, M_NOTFULL, M_CANCEL,
           M_CHARGING, M_INTERRUPT, M_FIRED, M_DONE, M_MODE_SW, M_MODE_TOW,
           A_CAN_T, A_CAN_D, A_OD_T, A_OD_D, A_GD_T, A_GD_D,
           G_GUIDE1, G_GUIDE2, G_GUIDE3]

# 已知既有、**不是本轮**：别的线留下的，记档而不断言 —— 不是我的活儿，
# 也不该由我的门替它们长期背红。每一条都写清"是谁的、证据在哪"。
KNOWN_OTHER = {
    u"gui.potato_s_t.canning.pour.poured":
        u"en/ja/ru 用 %1$s %2$s，zh 用 %s %s（别的线新增饮料罐装机时留下的；本轮未碰）",
    u"tooltip.potato_s_t.electric_blast_furnace（_rzh_touched 台账漂移）":
        u"台账自检报『4 语言的值都不等于台账』⇒ HEAD 之后有别的线又改过这条提示。"
        u"本轮 19 键里没有它（`git diff` 可证），装配线的 D7 会因此变红 —— 需要那条线跟一版台账。",
    u"tooltip.potato_s_t.fluid_converter（B4 判据本身写错了）":
        u"`_rzh_lzh_verify.py` 的 B4 判据是 `zv.count('\\\\n') != lv.count('\\\\n')`，"
        u"而 zv/lv 是**已解析**的值（转义换行早已变成真换行）⇒ 两边恒为 0，这条判据一直没在干活。"
        u"它这次之所以红，是 lzh 值里真的含有**字面** `\\n` 两个字符（见下）。"
        u"⚑ 顺带查出：按它**本意**（真换行数）比，zh 与 lzh 有 **12 条**不一致 —— 全是别的线"
        u"早前把中文提示缩成一行、文言文还留多行造成的既有漂移，源头不在本轮。",
    u"lzh tooltip.potato_s_t.fluid_converter 含有字面 \\n":
        u"lzh 的值是 `…儲能二千 FE。\\n**管：…**\\n手注：…` —— 那两处是**两个字符**的反斜杠+n，"
        u"不是真换行 ⇒ 游戏里会把 `\\n` 原样显示出来。HEAD 里就是这样，本轮未碰。",
}

GONE = [
    (u"en_us", T_TOOL_OD, u"below y=45"), (u"ja_jp", T_TOOL_OD, u"y45 以下"),
    (u"ru_ru", T_TOOL_OD, u"ниже y=45"), (u"lzh", T_TOOL_OD, u"y 四十五以下"),
    (u"en_us", T_TOOL_OD, u"Holds 1200 FE"), (u"ja_jp", T_TOOL_OD, u"蓄電 1200 FE"),
    (u"ru_ru", T_TOOL_OD, u"Хранит 1200 FE"), (u"lzh", T_TOOL_OD, u"儲能千二百 FE"),

    (u"en_us", T_TOOL_GD, u"hold right-click for 25 s"),
    (u"ja_jp", T_TOOL_GD, u"右クリック長押し 25 秒"),
    (u"ru_ru", T_TOOL_GD, u"удерживайте ПКМ 25 с"),
    (u"lzh", T_TOOL_GD, u"長按右鍵二十五息"),

    (u"en_us", M_NO_POWER, u"needs %s FE"), (u"en_us", M_NO_POWER, u"one scan costs"),
    (u"lzh", M_NO_POWER, u"一用須 %s FE"),
    # ⚠ ja_jp / ru_ru 的 no_power **这轮没变**（那两个语言本来就用「必要 %s FE」/
    #   「нужно %s FE」）⇒ 不进 GONE 也不进 KEEP。第一版写进 GONE 报了两条假残留。

    (u"en_us", M_ARROW, u"(x/z offset)"), (u"ja_jp", M_ARROW, u"（x/z 差）"),
    (u"ru_ru", M_ARROW, u"(смещение x/z)"), (u"lzh", M_ARROW, u"（x/z 之差）"),

    (u"en_us", M_OFFHAND, u"the black hole pulls that block"),
    (u"ja_jp", M_OFFHAND, u"（それが吸い込まれます）"),
    (u"ru_ru", M_OFFHAND, u"дыра втягивает именно его"),
    (u"lzh", M_OFFHAND, u"黑洞所吸者即此"),

    (u"en_us", M_NOTFULL, u"(must be full)"), (u"ja_jp", M_NOTFULL, u"（満充電が必要）"),
    (u"ru_ru", M_NOTFULL, u"(нужен полный заряд)"), (u"lzh", M_NOTFULL, u"（須滿方可放）"),

    (u"en_us", M_CANCEL, u"is gone - charge interrupted"),
    (u"ja_jp", M_CANCEL, u"無くなりました —— 中断"),
    (u"ru_ru", M_CANCEL, u"исчез — зарядка прервана"), (u"lzh", M_CANCEL, u"已失 —— 蓄力中斷"),

    # ⚠ charging 这条要**按语言分别写锚点**：
    #   · ja 词变了（重力充填 → 重力チャージ中）、lzh 词变了（引力蓄力 → 引力蓄力中）⇒ GONE
    #   · **en 与 ru 的值一字未动**（本来就是 Charging gravity: / Зарядка гравитации:，
    #     与中文新义等价）⇒ 只能在 KEEP，放进 GONE 就是假残留（§4.155 复现）
    (u"ja_jp", M_CHARGING, u"重力充填："), (u"lzh", M_CHARGING, u"引力蓄力："),

    (u"en_us", M_INTERRUPT, u"Released too early"), (u"ja_jp", M_INTERRUPT, u"途中で離しました"),
    (u"ru_ru", M_INTERRUPT, u"Отпущено рано"), (u"lzh", M_INTERRUPT, u"未滿而釋"),

    # ⚠ ja 的 fired **词没变**（旧值就是「%s を吸い始めました」= 中文新义的等价说法），
    #   本轮它不该出现在 GONE 里 —— 第一版报了假残留，改到 KEEP。

    (u"en_us", M_DONE, u"blocks pulled, %s placed, %s dropped as items"),
    (u"ja_jp", M_DONE, u"%s 個吸引、%s 個設置"),
    (u"ru_ru", M_DONE, u"втянуто %s, размещено %s"),
    (u"lzh", M_DONE, u"吸 %s 塊，碼 %s 塊"),

    (u"en_us", M_MODE_SW, u"blocks are moved to the black hole"),
    (u"ja_jp", M_MODE_SW, u"ブラックホールの下に積まれます"),
    (u"ru_ru", M_MODE_SW, u"переносятся и складываются"),
    (u"lzh", M_MODE_SW, u"方塊移於黑洞之下而積之"),
    (u"en_us", M_MODE_TOW, u"blocks fly over as falling blocks"),
    (u"ja_jp", M_MODE_TOW, u"落下ブロックとして飛び"),
    (u"ru_ru", M_MODE_TOW, u"летят как падающие"),
    (u"lzh", M_MODE_TOW, u"方塊化為墜塊飛來"),

    (u"en_us", A_CAN_T, u"One Can of Cola"), (u"ja_jp", A_CAN_T, u"コーラ一本"),
    (u"ru_ru", A_CAN_T, u"Банка колы"), (u"lzh", A_CAN_T, u"可樂一罐"),
    (u"en_us", A_CAN_D, u"Craft the Beverage Canning Machine"),
    (u"ja_jp", A_CAN_D, u"飲料缶詰機を作る"), (u"ru_ru", A_CAN_D, u"машину для розлива"),
    (u"lzh", A_CAN_D, u"成飲料罐裝機"),

    (u"en_us", A_OD_T, u"What Lies Below"), (u"ja_jp", A_OD_T, u"地下に何が"),
    (u"ru_ru", A_OD_T, u"Что под землёй"), (u"lzh", A_OD_T, u"地下何有"),
    (u"en_us", A_OD_D, u"600 FE per scan"), (u"ja_jp", A_OD_D, u"600 FE で"),
    (u"ru_ru", A_OD_D, u"600 FE за скан"), (u"lzh", A_OD_D, u"費六百 FE 一探"),

    (u"en_us", A_GD_T, u"A Black Hole in Hand"), (u"ja_jp", A_GD_T, u"手の中のブラックホール"),
    (u"ru_ru", A_GD_T, u"Чёрная дыра в руке"), (u"lzh", A_GD_T, u"手中有黑洞"),
    (u"en_us", A_GD_D, u"then stand back"), (u"ja_jp", A_GD_D, u"25 秒。⚠"),
    (u"ru_ru", A_GD_D, u"удерживайте ПКМ 25 с"), (u"lzh", A_GD_D, u"而後遠立"),

    (u"en_us", G_GUIDE1, u"aluminium"), (u"en_us", G_GUIDE2, u"aluminium"),
    (u"en_us", G_GUIDE3, u"aluminium"),
]

KEEP = [
    (u"en_us", T_TOOL_OD, u"3x3 chunks"), (u"ja_jp", T_TOOL_OD, u"3×3 チャンク"),
    (u"ru_ru", T_TOOL_OD, u"3x3 чанках"), (u"lzh", T_TOOL_OD, u"三乘三區"),

    (u"en_us", T_TOOL_GD, u"Single-use item"), (u"ja_jp", T_TOOL_GD, u"使い切りの品"),
    (u"ru_ru", T_TOOL_GD, u"Одноразовый"), (u"lzh", T_TOOL_GD, u"一次性之物"),
    (u"en_us", T_TOOL_GD, u"Shift + left-click"), (u"ja_jp", T_TOOL_GD, u"Shift + 左クリック"),
    (u"ru_ru", T_TOOL_GD, u"Shift + ЛКМ"), (u"lzh", T_TOOL_GD, u"Shift + 左鍵"),
    (u"en_us", T_TOOL_GD, u"8 million FE"), (u"ja_jp", T_TOOL_GD, u"800 万 FE"),
    (u"ru_ru", T_TOOL_GD, u"8 миллионов FE"), (u"lzh", T_TOOL_GD, u"八百萬 FE"),
    (u"en_us", T_TOOL_GD, u"offhand"), (u"ja_jp", T_TOOL_GD, u"オフハンド"),
    (u"ru_ru", T_TOOL_GD, u"вторую руку"), (u"lzh", T_TOOL_GD, u"副手"),

    # 这轮加的玩梗 —— 必须真的译出来了
    (u"en_us", M_NOTFULL, u"insatiably greedy"), (u"ja_jp", M_NOTFULL, u"底なしに貪欲"),
    (u"ru_ru", M_NOTFULL, u"бездонно жаден"), (u"lzh", M_NOTFULL, u"吾貪得無厭"),
    (u"en_us", M_NOTFULL, u"8M FE"), (u"ja_jp", M_NOTFULL, u"8M FE"),
    (u"ru_ru", M_NOTFULL, u"8M FE"), (u"lzh", M_NOTFULL, u"八百萬 FE"),

    (u"en_us", M_INTERRUPT, u"no regrets"), (u"ja_jp", M_INTERRUPT, u"後悔するな"),
    (u"ru_ru", M_INTERRUPT, u"не жалей"), (u"lzh", M_INTERRUPT, u"勿悔"),

    (u"en_us", A_CAN_D, u"Coca"), (u"ja_jp", A_CAN_D, u"コカ"),
    (u"ru_ru", A_CAN_D, u"Кока"), (u"lzh", A_CAN_D, u"可口"),
    (u"en_us", A_CAN_T, u"Chugging"), (u"ja_jp", A_CAN_T, u"一気にいく"),
    (u"ru_ru", A_CAN_T, u"залпом"), (u"lzh", A_CAN_T, u"直爽飲之"),

    (u"en_us", A_OD_T, u"Ore Magnet"), (u"ja_jp", A_OD_T, u"鉱物磁石"),
    (u"ru_ru", A_OD_T, u"Родня рудного магнита"), (u"lzh", A_OD_T, u"礦物磁鐵"),
    (u"en_us", A_OD_D, u"Craft an Ore Detector"), (u"ja_jp", A_OD_D, u"鉱物探知機を作る"),
    (u"ru_ru", A_OD_D, u"детектор руды"), (u"lzh", A_OD_D, u"合出礦物探測器"),

    (u"en_us", A_GD_T, u"Become Death"), (u"ja_jp", A_GD_T, u"死神になった"),
    (u"ru_ru", A_GD_T, u"Я стал смертью"), (u"lzh", A_GD_T, u"成為死神"),
    (u"en_us", A_GD_D, u"cuts both ways"), (u"ja_jp", A_GD_D, u"二面性"),
    (u"ru_ru", A_GD_D, u"две стороны"), (u"lzh", A_GD_D, u"恆有兩面"),

    # 旧值里那些"必须留下"的机制（别删过头）
    (u"en_us", M_ARROW, u"x/z"), (u"ja_jp", M_ARROW, u"x/z"),
    (u"ru_ru", M_ARROW, u"x/z"), (u"lzh", M_ARROW, u"x/z"),
    (u"en_us", M_OFFHAND, u"offhand"), (u"ja_jp", M_OFFHAND, u"オフハンド"),
    (u"ru_ru", M_OFFHAND, u"вторую руку"), (u"lzh", M_OFFHAND, u"副手"),
    (u"en_us", M_MODE_SW, u"Swallow"), (u"ja_jp", M_MODE_SW, u"捕食搬送"),
    (u"ru_ru", M_MODE_SW, u"поглощение"), (u"lzh", M_MODE_SW, u"吞噬搬運"),
    (u"en_us", M_MODE_TOW, u"Gravity Tow"), (u"ja_jp", M_MODE_TOW, u"重力牽引"),
    (u"ru_ru", M_MODE_TOW, u"гравитационная тяга"), (u"lzh", M_MODE_TOW, u"引力牽引"),
    # ⚠ 这三条**词本身没变**，本轮只动了空白（中文才是词变了）：
    #   en 旧/新都是 `Charging gravity:`，ru 旧/新都是 `Зарядка гравитации:`，
    #   ja 的 fired 旧值就是「を吸い始めました」。所以它们属于 KEEP（必须是这个），
    #   不属于 GONE —— 第一版放进 GONE，报了三条**假残留**。
    (u"en_us", M_CHARGING, u"Charging gravity:"), (u"ru_ru", M_CHARGING, u"Зарядка гравитации:"),
    (u"ja_jp", M_CHARGING, u"重力チャージ中："), (u"lzh", M_CHARGING, u"引力蓄力中："),
    (u"ja_jp", M_FIRED, u"を吸い始めました"), (u"en_us", M_FIRED, u"pulling in %s"),
    (u"ru_ru", M_FIRED, u"втягивать %s"), (u"lzh", M_FIRED, u"始吸取 %s"),
    (u"en_us", M_DONE, u"%s"), (u"lzh", M_DONE, u"墮為掉落物"),
    (u"en_us", M_CHARGING, u"%s%%"), (u"ja_jp", M_CHARGING, u"%s%%"),
    (u"ru_ru", M_CHARGING, u"%s%%"), (u"lzh", M_CHARGING, u"%s%%"),
    (u"en_us", M_NO_POWER, u"%s FE"), (u"lzh", M_NO_POWER, u"%s FE"),
    (u"en_us", G_GUIDE2, u"aluminum"), (u"en_us", G_GUIDE3, u"aluminum"),
    (u"en_us", G_GUIDE1, u"aluminum"),
]


def main():
    data = {}
    for loc in LOCS:
        data[loc] = json.load(io.open(os.path.join(LANGDIR, loc + u".json"), encoding="utf-8"))

    bad = 0
    L = []

    # ---- Z0 ----
    L.append(u"== Z0 用户的中文文件没被我碰 ==")
    numstat = subprocess.run([GIT, u"diff", u"--numstat", u"--",
                              u"src/main/resources/assets/potato_s_t/lang/zh_cn.json"],
                             cwd=ROOT, capture_output=True).stdout.decode(u"utf-8").strip()
    L.append(u"  git diff --numstat zh_cn: %s" % (numstat or u"(空)"))
    parts = numstat.split()
    if len(parts) >= 2 and parts[0] == u"19" and parts[1] == u"19":
        L.append(u"  OK   仍是「19 增 19 删」—— 正是用户这轮改动的签名")
    else:
        bad += 1
        L.append(u"  [错] 不是 19/19 ⇒ 我可能动过这个文件（或用户又改了）")

    # ---- Z1 ----
    L.append(u"")
    L.append(u"== Z1 旧文案必须消失（按 key）==")
    n = 0
    for loc, key, needle in GONE:
        v = data[loc].get(key)
        if v is None:
            bad += 1
            L.append(u"  [错] %s 缺键 %s" % (loc, key))
        elif needle in v:
            bad += 1
            L.append(u"  [错] %s / %s 仍有「%s」" % (loc, key, needle))
        else:
            n += 1
    L.append(u"  %s（%d / %d）" % (u"OK   全部消失" if n == len(GONE) else u"有残留",
                                  n, len(GONE)))

    # ---- Z2 ----
    L.append(u"")
    L.append(u"== Z2 新文案 / 梗 / 机制必须留下（按 key）==")
    m = 0
    for loc, key, needle in KEEP:
        v = data[loc].get(key)
        if v is None or needle not in v:
            bad += 1
            L.append(u"  [错] %s / %s 缺「%s」" % (loc, key, needle))
        else:
            m += 1
    L.append(u"  %s（%d / %d）" % (u"OK   全部在" if m == len(KEEP) else u"有缺失",
                                  m, len(KEEP)))

    # ---- Z3：只查本轮动过的键 ----
    L.append(u"")
    L.append(u"== Z3 结构（只查本轮动过的 %d 个键）==" % len(TOUCHED))
    zh = data[u"zh_cn"]
    for loc in LOCS:
        raw = io.open(os.path.join(LANGDIR, loc + u".json"), u"rb").read()
        problems = []
        if raw.startswith(b"\xef\xbb\xbf"):
            problems.append(u"有 BOM")
        if b"\r" in raw:
            problems.append(u"有 CR")
        for k in TOUCHED:
            v = data[loc].get(k)
            if v is None:
                problems.append(u"缺键 %s" % k)
                continue
            a = sorted(re.findall(r"%[0-9$]*s", v))
            b = sorted(re.findall(r"%[0-9$]*s", zh.get(k, u"")))
            if a != b:
                problems.append(u"占位符 %s: %s != zh %s" % (k, a, b))
            if v.strip() == u"" and zh.get(k, u"").strip() != u"":
                problems.append(u"空值 %s" % k)
            if v != v.rstrip():
                problems.append(u"行尾空白 %s" % k)
        if problems:
            bad += 1
            L.append(u"  [错] %s：%d 处" % (loc, len(problems)))
            for s in problems[:8]:
                L.append(u"       %s" % s)
        else:
            L.append(u"  OK   %s：这 %d 个键无 BOM/CR、占位符与 zh 一致、无空值/行尾空白"
                     % (loc, len(TOUCHED)))

    # ---- Z4：已知既有（不是本轮）----
    L.append(u"")
    L.append(u"== Z4 已知既有、不属于本轮（只记档，不计红）==")
    for k, why in sorted(KNOWN_OTHER.items()):
        L.append(u"  %s" % k)
        L.append(u"      %s" % why)

    L.append(u"")
    L.append(u"== 结论 ==")
    L.append(u"  全部通过（消失 %d / 必备 %d / 结构 %d 键 × %d 语）"
             % (len(GONE), len(KEEP), len(TOUCHED), len(LOCS))
             if bad == 0 else u"  有 %d 处问题" % bad)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"bad=%d gone=%d/%d keep=%d/%d -> %s" % (bad, n, len(GONE), m, len(KEEP), OUT))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
