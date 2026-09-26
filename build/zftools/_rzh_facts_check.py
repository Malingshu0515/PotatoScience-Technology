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
    所以下面这张表是"事实 → 四种语言各自的写法"，而不是照抄门的表。

⚠ 只读。输出 `_rzh_facts_check.txt`。
用法：`python build/zftools/_rzh_facts_check.py`
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LANGDIR = os.path.join(ROOT, u"src", u"main", u"resources", u"assets", u"potato_s_t", u"lang")
OUT = os.path.join(HERE, u"_rzh_facts_check.txt")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]

# ---------------------------------------------------------------------------
# 每条成就"必须交代的事实"，按语言给出各自的写法。
# 语料来源：这些事实本轮之前就在文案里，我只搬动了**叙述**，没有搬动数字。
# ---------------------------------------------------------------------------
FACTS = {
    u"fluid_logistics": {
        u"zh_cn": [u"1000 mB"], u"en_us": [u"1000 mB"],
        u"ja_jp": [u"1000 mB"], u"ru_ru": [u"1000 mB"],
    },
    u"lithium_battery_plant": {
        u"zh_cn": [u"30 秒"], u"en_us": [u"30 seconds"],
        u"ja_jp": [u"30 秒"], u"ru_ru": [u"30 секунд"],
    },
    u"oil_pump": {
        u"zh_cn": [u"8n²+80n", u"10n mB/s"], u"en_us": [u"8n²+80n", u"10n mB/s"],
        u"ja_jp": [u"8n²+80n", u"10n mB/s"], u"ru_ru": [u"8n²+80n", u"10n mB/\u0441"],
    },
    u"salt": {
        u"zh_cn": [u"海盐"], u"en_us": [u"sea salt"],
        u"ja_jp": [u"海塩"], u"ru_ru": [u"\u043c\u043e\u0440"],
    },
    u"star_steel": {
        u"zh_cn": [u"3 个星璨钢锭"], u"en_us": [u"3 Star Steel Ingots"],
        u"ja_jp": [u"星燦鋼 3 個"], u"ru_ru": [u"3 слитка"],
    },
    u"star_steel_armor": {
        u"zh_cn": [u"最硬"], u"en_us": [u"toughest"],
        u"ja_jp": [u"\u6700\u786c"], u"ru_ru": [u"\u0441\u0430\u043c\u044b\u0439 \u043f\u0440\u043e\u0447\u043d\u044b\u0439"],
    },
    u"starfall": {
        u"zh_cn": [u"y=200", u"7~20"], u"en_us": [u"y=200", u"7-20"],
        u"ja_jp": [u"y=200", u"7\u301c20"], u"ru_ru": [u"y=200", u"7\u201320"],
    },
    u"blast_furnace": {
        u"zh_cn": [u"3\u00d73\u00d73"], u"en_us": [u"3\u00d73\u00d73"],
        u"ja_jp": [u"3\u00d73\u00d73"], u"ru_ru": [u"3\u00d73\u00d73"],
    },
    u"diesel_generator": {
        u"zh_cn": [u"7200 FE"], u"en_us": [u"7200 FE"],
        u"ja_jp": [u"7200 FE"], u"ru_ru": [u"7200 FE"],
    },
    u"silver_wire": {
        u"zh_cn": [u"16134 FE/t"], u"en_us": [u"16134 FE/t"],
        u"ja_jp": [u"16134 FE/t"], u"ru_ru": [u"16134 FE/\u0442"],
    },
}


def main():
    with io.open(os.path.join(LANGDIR, u"zh_cn.json"), encoding=u"utf-8") as f:
        zh = json.load(f)
    data = {}
    for loc in LOCALES:
        with io.open(os.path.join(LANGDIR, loc + u".json"), encoding=u"utf-8") as f:
            data[loc] = json.load(f)

    L = [u"成就精简后的事实复核：%d 条节点 × %d 语 = %d 项"
         % (len(FACTS), len(LOCALES), len(FACTS) * len(LOCALES))]
    bad = 0
    for node in sorted(FACTS):
        key = u"advancements.potato_s_t.%s.description" % node
        for loc in LOCALES:
            v = data[loc].get(key)
            if v is None:
                bad += 1
                L.append(u"  [错] %s 缺键 %s" % (loc, key))
                continue
            for lit in FACTS[node][loc]:
                if lit not in v:
                    bad += 1
                    L.append(u"  [丢] %-6s %-22s 少了 %r" % (loc, node, lit))
                    L.append(u"        现在: %s" % v[:120])
        if all(FACTS[node][l] and all(x in data[l].get(key, u"") for x in FACTS[node][l])
               for l in LOCALES):
            L.append(u"  [OK] %s" % node)
    L.append(u"")
    L.append(u"合计丢失 %d 处" % bad)
    io.open(OUT, u"w", encoding=u"utf-8", newline=u"\n").write(u"\n".join(L) + u"\n")
    print(u"wrote %s  (丢失 %d 处)" % (OUT, bad))
    return 1 if bad else 0


if __name__ == u"__main__":
    sys.exit(main())
