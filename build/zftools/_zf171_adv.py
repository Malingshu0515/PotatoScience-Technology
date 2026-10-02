# -*- coding: utf-8 -*-
u"""_zf171_adv.py —— ZF171：给新内容补进度节点（成就）

用户原话：「成就和帕秋莉手册是时候更新一下了」。

本轮加 **3 个节点**（都要「拿到/合出来」就能达成，用**原版触发器**，不新增代码）：
  ① `beverage_canning_machine` —— 合出饮料罐装机（0.13 ZF167）
  ② `ore_detector`             —— 合出矿物探测器（0.14 ZF169）
  ③ `gravity_device`           —— 合出手持式引力装置（0.14 ZF169）

⚠ 没加"第一次放黑洞"那条：本工程**没有**自定义触发器（`CriterionTrigger`）的现成写法，
  要新增就得注册一个触发器 + 在开火处 `trigger(...)` —— 那是**代码活**，留给下一轮
  （记在档案里，别当成"忘了"）。

格式**照抄盘上现成的那份**（`blast_furnace.json`）：`parent` / `display`(icon,title,description,
frame,show_toast,announce_to_chat,hidden) / `criteria` / `requirements` / `sends_telemetry_event`。
"""
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ADV = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\advancement")
LANG = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\lang")
TOOLS = os.path.join(ROOT, r"build", "zftools")
CODES = (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh")

fails = []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def node(nid, parent, icon, trigger, item, frame):
    return {
        u"parent": parent,
        u"display": {
            u"icon": {u"count": 1, u"id": icon},
            u"title": {u"translate": u"advancements.potato_s_t.%s.title" % nid},
            u"description": {u"translate": u"advancements.potato_s_t.%s.description" % nid},
            u"frame": frame,
            u"show_toast": True,
            u"announce_to_chat": True,
            u"hidden": False,
        },
        u"criteria": {
            u"got0": {
                u"trigger": trigger,
                u"conditions": {u"items": [{u"items": item}]},
            } if trigger == u"minecraft:inventory_changed" else {
                u"trigger": trigger,
                u"conditions": {u"item": {u"items": item}},
            },
        },
        u"requirements": [[u"got0"]],
        u"sends_telemetry_event": False,
    }


def main():
    print(u"① 选父节点（挑一个**已经在树上**的）")
    existing = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ADV, u"*.json"))}
    print(u"      现有 %d 个节点" % len(existing))
    parent = None
    for cand in (u"aluminum", u"micro_crusher", u"capacitor", u"wiring"):
        if cand in existing:
            parent = u"potato_s_t:" + cand
            break
    check(u"找到父节点", parent is not None, str(parent))

    nodes = {
        u"beverage_canning_machine": node(u"beverage_canning_machine", parent,
                                          u"potato_s_t:beverage_canning_machine",
                                          u"minecraft:inventory_changed",
                                          u"potato_s_t:beverage_canning_machine", u"task"),
        u"ore_detector": node(u"ore_detector", parent, u"potato_s_t:ore_detector",
                              u"minecraft:inventory_changed", u"potato_s_t:ore_detector", u"task"),
        u"gravity_device": node(u"gravity_device", parent, u"potato_s_t:gravity_device",
                                u"minecraft:inventory_changed", u"potato_s_t:gravity_device", u"goal"),
    }
    print(u"\n② 写出 3 份进度 JSON")
    for nid, data in nodes.items():
        p = os.path.join(ADV, nid + u".json")
        text = json.dumps(data, ensure_ascii=False, indent=2) + u"\n"
        if os.path.exists(p):
            check(u"%s 已在且相同（幂等）" % nid, io.open(p, encoding="utf-8").read() == text)
        else:
            io.open(p, "w", encoding="utf-8", newline=u"\n").write(text)
            check(u"%s 已写出" % nid, os.path.exists(p))
        back = json.loads(io.open(p, encoding="utf-8").read())
        check(u"%s 形状对（parent/display/criteria/requirements）" % nid,
              all(k in back for k in (u"parent", u"display", u"criteria", u"requirements"))
              and back[u"display"][u"icon"][u"id"] == data[u"display"][u"icon"][u"id"])

    print(u"\n③ 语言：每节点两键（标题 + 说明）× 5 份")
    KEYS = {
        u"beverage_canning_machine": {
            u"zh_cn": (u"来一罐可乐", u"合出饮料罐装机：碳酸、水、糖、可可豆和一只空铝罐，五秒钟出一罐。"),
            u"en_us": (u"One Can of Cola", u"Craft the Beverage Canning Machine: carbonic acid, water, "
                                        u"sugar, cocoa and an empty can - one cola every five seconds."),
            u"ja_jp": (u"コーラ一本", u"飲料缶詰機を作る：炭酸・水・砂糖・カカオ・空き缶で 5 秒に 1 本。"),
            u"ru_ru": (u"Банка колы", u"Создайте машину для розлива: кислота, вода, сахар, какао "
                                      u"и пустая банка — банка колы за пять секунд."),
            u"lzh": (u"可樂一罐", u"成飲料罐裝機：碳酸、水、糖、可可與空罐，五息得一罐。"),
        },
        u"ore_detector": {
            u"zh_cn": (u"地下有什么", u"合出矿物探测器：花 600 FE 探一次，3×3 区块、y45 以下的矿无所遁形。"),
            u"en_us": (u"What Lies Below", u"Craft the Ore Detector: 600 FE per scan, nothing hides "
                                           u"within 3x3 chunks below y=45."),
            u"ja_jp": (u"地下に何が", u"鉱物探知機を作る：600 FE で 3×3 チャンク・y45 以下の鉱物を探る。"),
            u"ru_ru": (u"Что под землёй", u"Создайте детектор руды: 600 FE за скан, руда не спрячется "
                                          u"в 3x3 чанках ниже y=45."),
            u"lzh": (u"地下何有", u"成礦物探测器：費六百 FE 一探，三乘三區、y 四十五以下無所遁形。"),
        },
        u"gravity_device": {
            u"zh_cn": (u"手上有个黑洞", u"合出手持式引力装置：装满 8,000,000 FE，按住右键 25 秒 —— "
                                       u"然后站远点。⚠ 穿一件振金装备再去试，你不会被自己吸进去。"),
            u"en_us": (u"A Black Hole in Hand", u"Craft the Handheld Gravity Device: charge it to "
                                                u"8,000,000 FE and hold right-click for 25 s - then stand back. "
                                                u"Wear one piece of vibranium so it does not eat you."),
            u"ja_jp": (u"手の中のブラックホール", u"携帯重力装置を作る：8,000,000 FE を満たし、"
                                                  u"右クリックを 25 秒。⚠ 振金を一つ身につけておくこと。"),
            u"ru_ru": (u"Чёрная дыра в руке", u"Создайте ручное гравитационное устройство: зарядите "
                                              u"8 000 000 FE и удерживайте ПКМ 25 с. ⚠ Наденьте вибраниум."),
            u"lzh": (u"手中有黑洞", u"成手持引力之器：儲八百萬 FE，長按右鍵二十五息 —— 而後遠立。"
                                    u"⚠ 着一振金之具，方不為所吞。"),
        },
    }
    tables = {}
    for c in CODES:
        p = os.path.join(LANG, c + u".json")
        d = json.loads(io.open(p, encoding="utf-8").read())
        added = 0
        for nid, vals in KEYS.items():
            for suffix, idx in ((u"title", 0), (u"description", 1)):
                k = u"advancements.potato_s_t.%s.%s" % (nid, suffix)
                if k not in d:
                    d[k] = vals[c][idx]
                    added += 1
        if added:
            io.open(p, "w", encoding="utf-8", newline=u"\n").write(
                json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        tables[c] = json.loads(io.open(p, encoding="utf-8").read())
        print(u"      %-6s +%d 键（现 %d）" % (c, added, len(tables[c])))
    allk = [u"advancements.potato_s_t.%s.%s" % (n, s) for n in KEYS for s in (u"title", u"description")]
    check(u"6 个键五份齐全", all(all(k in tables[c] for k in allk) for c in CODES))
    check(u"四语言键集合一致", len(set(frozenset(tables[c]) for c in CODES[:4])) == 1,
          u" / ".join(u"%s %d" % (c, len(tables[c])) for c in CODES))

    print(u"\n④ 跟平「写死进度条数」的常驻门（43 → %d）" % (len(existing) + 3))
    new_count = len(existing) + 3
    touched = 0
    for p in sorted(glob.glob(os.path.join(TOOLS, u"_zf*_verify.py"))):
        t = io.open(p, encoding="utf-8").read()
        if not re.search(u"\\b43\\b", t):
            continue
        new = re.sub(u"(进度|advancement|成就)[^\\n]{0,24}\\b43\\b", lambda m: m.group(0).replace(u"43", str(new_count)), t)
        if new != t:
            io.open(p, "w", encoding="utf-8", newline=u"\n").write(new)
            touched += 1
    print(u"      改了 %d 份（只动「进度 + 43」挨着的那种行）" % touched)
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
