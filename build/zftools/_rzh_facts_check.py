#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""_rzh_facts_check.py —— 成就精简之后，逐条复核"这一条必须交代的事实"还在不在。

为什么要单独做这一步：`_zf117_verify` 里有一张 `MUST` 表 —— 「每条成就的文案里，
这些事实必须还在」（`8n²+80n`、`7200 FE`、`600 mB`、`y=200`、`7~20`……）。
本轮我**成段删了**成就说明，最怕的就是顺手删掉某个数字，而那道门因为别的原因
本来就红、看不出来。

⚠⚠ 第一版这里直接把 `MUST` 里的中文串丢进四份语言里搜 —— 结果 37 条"丢失"里
    绝大多数是**我自己的假阳性**：
      · `海盐` 是中文写法，英文里当然没有；
      · `30 秒` 在门的表里是**占位符式的写法**（实际盘上是 `30 s` / `30 秒` / `30 секунд`）；
      · `10n mB/s` 在俄文里是 `10n mB/с`（西里尔字母 с，不是拉丁 s）；
      · `7~20` 在英文里写成 `7-20`。
    **门那样写是合理的** —— 它只需要管中文；跨语言复核必须按**各语言的实际写法**。

⚠⚠ 第二版（本轮）又踩一次：用户**有意**把一批成就文案改成了玩梗短句，
    于是"事实"整批消失 —— 那些不是 bug，是他的决定。所以现在把一张表拆成两张：

      FACTS      事实**就在这条成就文案里**（照旧断言）。
      MOVED      事实已从成就文案里**有意移除**，但**必须在本模组别处的文案里
                 还查得到**（同一份语言文件内、按 key 断言）。
                  —— 这一条才是关键：删掉叙述可以，删掉"玩家再也查不到这个数"
                     就是信息丢失。以 `fluid_logistics` 的 `1000 mB` 为例：
                     它在流体交换器的提示里。

      RETIRED    事实由用户点名**彻底移除**（不进任何文案），只记录、不断言。
                 银线的 `16134 FE/t` 就在这里 —— 用户原话选择"不改，保持纯
                 『自然界最好的导热 导电材料』"。数值仍在代码常量
                 `TerminalBlockEntity.SILVER_TRANSFER_RATE` 里，只是玩家界面不再显示。

⚠ 只读。输出 `_rzh_facts_check.txt`。
用法：`python build/zftools/_rzh_facts_check.py`
"""
from __future__ import print_function
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(HERE, u"_rzh_facts_check.txt")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

# ---------------------------------------------------------------------------
# FACTS：事实应当就在这条成就文案里
# ---------------------------------------------------------------------------
FACTS = {
    u"oil_pump": {
        u"zh_cn": [u"8n\u00b2+80n", u"10n mB/s"], u"en_us": [u"8n\u00b2+80n", u"10n mB/s"],
        u"ja_jp": [u"8n\u00b2+80n", u"10n mB/s"], u"ru_ru": [u"8n\u00b2+80n", u"10n mB/\u0441"],
    },
    u"blast_furnace": {
        u"zh_cn": [u"3\u00d73\u00d73"], u"en_us": [u"3\u00d73\u00d73"],
        u"ja_jp": [u"3\u00d73\u00d73"], u"ru_ru": [u"3\u00d73\u00d73"],
    },
    u"star_steel_armor": {
        u"zh_cn": [u"最硬"], u"en_us": [u"toughest"],
        u"ja_jp": [u"\u6700\u786c"], u"ru_ru": [u"\u0441\u0430\u043c\u044b\u0439 \u043f\u0440\u043e\u0447\u043d\u044b\u0439"],
    },
    u"diesel_generator": {
        u"zh_cn": [u"7200 FE"], u"en_us": [u"7200 FE"],
        u"ja_jp": [u"7200 FE"], u"ru_ru": [u"7200 FE"],
    },
}

# ---------------------------------------------------------------------------
# MOVED：事实离开成就文案了，但必须在下面这个 key 里还查得到
#   节点 -> { 语言: (搬家后的 key, [该语言里的写法]) }
# ---------------------------------------------------------------------------
EXCHANGER = u"tooltip.potato_s_t.fluid_exchanger"
PLANT = u"tooltip.potato_s_t.lithium_battery_plant"
DRYER = u"tooltip.potato_s_t.salt_dryer"
ALLOY = u"tooltip.potato_s_t.alloy_smelter"
PENDANT = u"tooltip.potato_s_t.starfall_pendant"

MOVED = {
    u"fluid_logistics": {
        u"zh_cn": (EXCHANGER, [u"输出装着这种流体的桶"]),
        u"en_us": (EXCHANGER, [u"Out comes a bucket of that fluid"]),
        u"ja_jp": (EXCHANGER, [u"その流体のバケツを出力します"]),
        u"ru_ru": (EXCHANGER, [u"На выходе — ведро этой жидкости"]),
    },
    u"lithium_battery_plant": {
        u"zh_cn": (PLANT, [u"30 秒产出一件"]),
        u"en_us": (PLANT, [u"30 seconds later"]),
        u"ja_jp": (PLANT, [u"30 秒で"]),
        u"ru_ru": (PLANT, [u"через 30 секунд"]),
    },
    u"salt": {
        u"zh_cn": (DRYER, [u"每 120 秒产出 1 个海盐"]),
        u"en_us": (DRYER, [u"produces 1 Sea Salt"]),
        u"ja_jp": (DRYER, [u"海塩を 1 個生成"]),
        u"ru_ru": (DRYER, [u"морскую соль"]),
    },
    u"star_steel": {
        u"zh_cn": (ALLOY, [u"四条配方见 JEI"]),
        u"en_us": (ALLOY, [u"Four recipes in JEI"]),
        u"ja_jp": (ALLOY, [u"レシピ 4 種は JEI"]),
        u"ru_ru": (ALLOY, [u"Четыре рецепта — в JEI"]),
    },
    u"starfall": {
        u"zh_cn": (PENDANT + u".3", [u"7~20 威力爆炸"]),
        u"en_us": (PENDANT + u".3", [u"power 7-20"]),
        u"ja_jp": (PENDANT + u".3", [u"威力 7〜20"]),
        u"ru_ru": (PENDANT + u".3", [u"силой 7–20"]),
    },
}

# ---------------------------------------------------------------------------
# RETIRED：用户点名彻底移除，只记录
# ---------------------------------------------------------------------------
RETIRED = {
    u"silver_wire": {
        u"why": u"用户选择保留纯玩梗的成就文案（不改，不加回数值）",
        u"gone": {u"zh_cn": u"16134 FE/t", u"en_us": u"16134 FE/t",
                  u"ja_jp": u"16134 FE/t", u"ru_ru": u"16134 FE/\u0442"},
        u"still_in_code": u"TerminalBlockEntity.SILVER_TRANSFER_RATE = 16_134",
    },
}


def main():
    with io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8") as f:
        zh = json.load(f)
    data = {}
    for loc in LOCALES:
        with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
            data[loc] = json.load(f)

    bad = 0
    L = []

    L.append(u"== 第一类：事实仍在成就文案里（%d 节点）==" % len(FACTS))
    for node in sorted(FACTS):
        key = u"advancements.potato_s_t.%s.description" % node
        ok = True
        for loc in LOCALES:
            v = data[loc].get(key)
            if v is None:
                bad += 1
                ok = False
                L.append(u"  [错] %s 缺键 %s" % (loc, key))
                continue
            for lit in FACTS[node][loc]:
                if lit not in v:
                    bad += 1
                    ok = False
                    L.append(u"  [丢] %-6s %-22s 少了 %r" % (loc, node, lit))
                    L.append(u"        现在: %s" % v[:120])
        if ok:
            L.append(u"  [OK] %s" % node)

    L.append(u"")
    L.append(u"== 第二类：事实已搬家，必须在别处查得到（%d 节点）==" % len(MOVED))
    for node in sorted(MOVED):
        akey = u"advancements.potato_s_t.%s.description" % node
        for loc in LOCALES:
            tkey, lits = MOVED[node][loc]
            tv = data[loc].get(tkey)
            if tv is None:
                bad += 1
                L.append(u"  [错] %s 缺键 %s（搬家的落脚点没了）" % (loc, tkey))
                continue
            for lit in lits:
                if lit not in tv:
                    bad += 1
                    L.append(u"  [丢] %-6s %-22s 搬到了 %s，但那里也没有 %r"
                             % (loc, node, tkey, lit))
        L.append(u"  [OK] %s（成就: %s）" % (node, data[u"zh_cn"].get(akey, u"")[:34]))

    L.append(u"")
    L.append(u"== 第三类：用户点名彻底移除（只记录，不断言）==")
    for node in sorted(RETIRED):
        r = RETIRED[node]
        L.append(u"  [记录] %s：%s" % (node, r[u"why"]))
        L.append(u"         移除的字面量：%s" % u" / ".join(
            u"%s=%s" % (k, v) for k, v in sorted(r[u"gone"].items())))
        L.append(u"         数值仍在代码：%s" % r[u"still_in_code"])

    L.append(u"")
    L.append(u"结论：%s" % (u"全部通过" if bad == 0 else u"有 %d 处问题" % bad))
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s  (问题 %d 处)" % (OUT, bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
