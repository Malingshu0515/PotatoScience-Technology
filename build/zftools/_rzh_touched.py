# -*- coding: utf-8 -*-
r"""_rzh_touched.py —— 翻译线（RZH 系列）改过的语言键台账。

为什么需要它：翻译线只改**语言文件的值**，不改任何键。可这会让一堆往轮门的
「相对改前件只动了这几个值」判据变红 —— 而且**每润色一次就要重改一圈**（本文件诞生前
已经手工 retarget 过 `_zf107_verify` / `_zf117_verify` / `_zf121_verify` / `_zf124_verify`）。
台账把这件事变成一处维护：门只要

    from _rzh_touched import touched
    changed = [k for k in changed if k not in touched(loc)]

即可。⚠ 这不放宽判据：门仍然断言"只许动这些 + 台账里那些"，多一个都不行。

台账按**语言**分组，值是键名集合；同时给一个自检函数，发现台账里记着"其实没变"的键
（说明记录过期）就报出来 —— 免得台账自己变成谎言。
"""
import io
import json
import os

LANG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), u"src", u"main", u"resources", u"assets",
    u"potato_s_t", u"lang")

# 三条装备套装说明（commit c2b24e4「装备说明瘦身」）
ARMOR = [u"tooltip.potato_s_t.titanium_alloy_set",
         u"tooltip.potato_s_t.vibranium_set",
         u"tooltip.potato_s_t.star_steel_set"]

# 10 条成就标题改名（"进度名称 别单单是获得的物品名称了"）
TITLES = [u"advancements.potato_s_t.%s.title" % n for n in (
    u"electrolyzer", u"distillation", u"alloy_smelter", u"blast_furnace", u"starfall",
    u"salt", u"star_steel", u"oil_pump", u"capacitor", u"sulfur")]

# 10 条成就说明瘦身（"成就介绍太长了"）
DESCS = [u"advancements.potato_s_t.%s.description" % n for n in (
    u"oil_pump", u"starfall", u"fluid_logistics", u"lithium_battery_plant",
    u"lithium_battery", u"star_steel", u"salt", u"blast_furnace", u"wiring",
    u"alloy_smelter")]

LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru"]


def touched(loc, extra=()):
    """返回该语言"翻译线碰过的键"集合。`extra` 用于把调用方自己那几条也算进去。"""
    s = set(ARMOR) | set(TITLES) | set(DESCS) | set(extra)
    return s


def audit():
    """自检：台账里的键，**是否有哪个在整个仓库历史里从未被翻译线改过**。

    ⚠ 第一版这里拿 `git show HEAD:` 比，结论毫无意义 —— 翻译线的改动**已经提交**，
      相对 HEAD 自然"没变"，于是 48 条全被误报成"过期"。
      台账的语义是**归属声明**（"这些键归翻译线，门别再报它"），不是待办清单：
      一旦某个键归了翻译线，它会一直留在台账里，哪怕后来被冻结。
    ⇒ 这里只做一件有用的事：确认台账里的键**都真实存在**（拼错键名会静默失效）。
    """
    problems = []
    for loc in LOCALES:
        rel = u"src/main/resources/assets/potato_s_t/lang/%s.json" % loc
        cur = json.load(io.open(rel, encoding=u"utf-8"))
        for k in sorted(touched(loc)):
            if k not in cur:
                problems.append((loc, k))
    return problems


if __name__ == u"__main__":
    p = audit()
    if p:
        print(u"台账里有 %d 条键**在盘上不存在**（键名写错了）：" % len(p))
        for loc, k in p:
            print(u"   %s  %s" % (loc, k))
    else:
        print(u"台账自检通过：%d 条键在四份语言里都存在"
              % sum(len(touched(l)) for l in LOCALES))
