# -*- coding: utf-8 -*-
r"""_zf95_verify.py —— ZF95 常驻校验：用户给的 5 条合成配方

这 5 条是**用户口述的九宫格**，所以最要紧的一条断言是：
**把 JSON 解回来，逐格与"用户原话"那张表比**（不是拿 JSON 与 JSON 自比）。
另外核：材料 id / `c:` 标签真的存在（打错一个字母 ⇒ 配方静默做不出来）、
旧的 36 份配方一份不少、活体数字（定形配方 ZF95 起 35、**ZF96 起 36**）、文档、成品 jar。
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
ITEMD = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
TAGS = os.path.join(ROOT, r"src\main\resources\data\c\tags\item\ingots")
DOCS = os.path.join(ROOT, "docs")
TOOLS = os.path.join(ROOT, "build", "zftools")
JAR = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
BEFORE = os.path.join(r"C:\PotatoST救援\zf95_pre", "recipe_before.txt")
EXPECT_SHAPED = 43
# 用户原话 -> 逐格表（这张表就是"规格"，JSON 只是它的实现）
SPEC = {
    "music_disc_jasmine_flower": {
        "zh": u"茉莉花唱片",
        "quote": u"四角灵魂灯笼 最中间一个火把花 火把花紧挨着四个粗金块",
        "grid": [["minecraft:soul_lantern", "minecraft:raw_gold_block", "minecraft:soul_lantern"],
                 ["minecraft:raw_gold_block", "minecraft:torchflower", "minecraft:raw_gold_block"],
                 ["minecraft:soul_lantern", "minecraft:raw_gold_block", "minecraft:soul_lantern"]],
    },
    "music_disc_anvil_of_the_republic": {
        "zh": u"共和国之砧",
        "quote": u"最左 最右一列皆为红石粉 最中间一个铁砧 上下各一个钛锭",
        "grid": [["minecraft:redstone", "c:ingots/titanium", "minecraft:redstone"],
                 ["minecraft:redstone", "minecraft:anvil", "minecraft:redstone"],
                 ["minecraft:redstone", "c:ingots/titanium", "minecraft:redstone"]],
    },
    "alloy_smelter": {
        "zh": u"合金炉主控",
        "quote": u"【铝板】【铁板】【铝板】，【镍板】【电容】【镍板】，【加热装置】【一般金属块】【散热装置】",
        "grid": [["potato_s_t:aluminum_plate", "potato_s_t:iron_plate", "potato_s_t:aluminum_plate"],
                 ["potato_s_t:nickel_plate", "potato_s_t:capacitor", "potato_s_t:nickel_plate"],
                 ["potato_s_t:heater", "potato_s_t:common_metal_block", "potato_s_t:heat_sink"]],
    },
    "distillation_controller": {
        "zh": u"分馏塔控制器",
        "quote": u"【钢板】×3，【耐热金属块】【铜块】【耐热金属块】，【高碳钢】【黑曜石】【高碳钢】",
        "grid": [["potato_s_t:steel_plate", "potato_s_t:steel_plate", "potato_s_t:steel_plate"],
                 ["potato_s_t:heat_resistant_metal_block", "minecraft:copper_block",
                  "potato_s_t:heat_resistant_metal_block"],
                 ["c:ingots/steel", "minecraft:obsidian", "c:ingots/steel"]],
    },
    "distillation_operator": {
        "zh": u"分馏塔操作器",
        "quote": u"【钴锭】【钢板】【钴锭】，【流体泵】【钻石块】【灌装机】，【油罐】【分馏塔控制器】【油罐】",
        "grid": [["c:ingots/cobalt", "potato_s_t:steel_plate", "c:ingots/cobalt"],
                 ["potato_s_t:fluid_pump", "minecraft:diamond_block", "potato_s_t:filling_machine"],
                 ["potato_s_t:high_pressure_tank", "potato_s_t:distillation_controller",
                  "potato_s_t:high_pressure_tank"]],
    },
}
passed = 0
failed = 0
fails = []


def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label)


def eq(label, want, got):
    check(u"%s（期望 %r，实际 %r）" % (label, want, got), want == got)


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def sha1f(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    print(u"=========== ZF95 校验：用户给的 5 条合成配方 ===========")

    print(u"\n== A 把 JSON 解回九宫格，逐格与用户原话比 ==")
    for rid, spec in SPEC.items():
        p = os.path.join(RDIR, rid + ".json")
        check(u"%s.json 在" % rid, os.path.exists(p))
        if not os.path.exists(p):
            continue
        d = json.loads(read(p))
        eq(u"%s 类型" % rid, u"minecraft:crafting_shaped", d.get("type"))
        eq(u"%s 产物" % rid, {u"id": u"potato_s_t:" + rid, u"count": 1}, d.get("result"))
        pat = d.get("pattern") or []
        key = d.get("key") or {}
        # 用 key 把 pattern 解回"材料 id/tag"
        got = []
        bad = False
        for row in pat:
            line = []
            for ch in row:
                if ch == u" ":
                    line.append(u" ")
                    continue
                ent = key.get(ch)
                if not ent:
                    line.append(u"?%s" % ch)
                    bad = True
                else:
                    line.append(ent.get("item") or ent.get("tag") or u"?" + ch)
            got.append(line)
        check(u"%s（%s）：九宫格与用户原话逐格一致（%s）" % (rid, spec["zh"], spec["quote"]),
              (not bad) and got == spec["grid"])
        if got != spec["grid"]:
            for i in range(max(len(got), 3)):
                print(u"         第 %d 行 解出 %s / 规格 %s"
                      % (i + 1, got[i] if i < len(got) else None, spec["grid"][i]))

    print(u"\n== B 材料与产物都得真的存在 ==")
    vanilla = set()
    for rid, spec in SPEC.items():
        for row in spec["grid"]:
            for cell in row:
                if cell.startswith(u"c:"):
                    t = cell.split(u"/")[-1]
                    check(u"标签 #%s 由本工程提供" % cell, os.path.exists(os.path.join(TAGS, t + ".json")))
                elif cell.startswith(u"potato_s_t:"):
                    nm = cell.split(u":")[1]
                    check(u"材料 %s 有 models/item" % cell,
                          os.path.exists(os.path.join(ITEMD, nm + ".json")))
                else:
                    vanilla.add(cell)
        check(u"产物 potato_s_t:%s 有 models/item" % rid,
              os.path.exists(os.path.join(ITEMD, rid + ".json")))
    print(u"        用到的原版物品 %d 种：%s" % (len(vanilla), u", ".join(sorted(vanilla))))

    print(u"\n== C 旧配方一份不少 + 活体数字 ==")
    names = sorted(n for n in os.listdir(RDIR) if n.endswith(".json"))
    if os.path.exists(BEFORE):
        old = [l.strip() for l in read(BEFORE).splitlines() if l.strip()]
        missing = [n for n in old if n not in names]
        eq(u"改前那 %d 份配方一份不少（缺 %s）" % (len(old), missing or u"无"), [], missing)
        added = [n for n in names if n not in old]
        # ⚠ ZF96 又加了 1 条（加氢脱硫反应仓）—— 名单随轮次增长，"其余逐字节未变"才是内容
        later = [u"hydrodesulfurization_chamber.json", u"air_separator.json",
                 u"ammonia_synthesis_chamber.json",
                 u"lithium_battery.json", u"electric_blast_furnace.json",
                 u"combustion_chamber.json", u"acidic_reaction_chamber.json"]
        eq(u"本轮只新增这 5 份（+ 后续轮次的 %d 份）" % len(later),
           sorted(sorted(SPEC[i] and (i + u".json") for i in SPEC) + later), sorted(added))
    shaped = [n for n in names
              if json.loads(read(os.path.join(RDIR, n))).get("type") == "minecraft:crafting_shaped"]
    eq(u"定形配方总数", EXPECT_SHAPED, len(shaped))
    zf71 = read(os.path.join(TOOLS, "_zf71_verify.py")) or u""
    check(u"_zf71_verify.py 的活体数字已跟到 %d" % EXPECT_SHAPED,
          u"check(craft == %d," % EXPECT_SHAPED in zf71)

    print(u"\n== D 文档 ==")
    arch = read(os.path.join(DOCS, u"开发档案.md")) or u""
    ann = read(os.path.join(DOCS, "UpdateAnnouncement_EN.md")) or u""
    check(u"档案里有 ZF95 那一行", u"| ZF95 |" in arch)
    check(u"档案里记了「油罐 = 高压气罐」这条判断",
          u"high_pressure_tank" in arch and u"油罐" in arch)
    check(u"英文公告已把三件从「没有配方」挪出来",
          u"got their recipes in" in ann and u"the Distillation Tower Operator have no crafting recipe yet" not in ann)

    print(u"\n== E 成品 jar ==")
    if not os.path.exists(JAR):
        check(u"成品 jar 在", False)
    else:
        sha = sha1f(JAR)
        check(u".sha1 与 jar 一致（%s…）" % sha[:8], (read(JAR + u".sha1") or u"").strip() == sha)
        with zipfile.ZipFile(JAR) as zf:
            names_in = zf.namelist()
            same = 0
            for rid in SPEC:
                rel = u"data/potato_s_t/recipe/%s.json" % rid
                disk = os.path.join(RDIR, rid + ".json")
                if rel in names_in and zf.read(rel) == open(disk, "rb").read():
                    same += 1
            eq(u"成品里 5 份新配方与盘上逐字节一致", 5, same)
            check(u"成品里 assets/ 与 data/ 条目名全合法",
                  not [n for n in names_in if (n.startswith(u"assets/") or n.startswith(u"data/"))
                       and not re.fullmatch(u"[a-z0-9/._-]+", n)])

    print(u"\n通过 = %d   失败 = %d" % (passed, failed))
    for f in fails:
        print(u"  !! " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
