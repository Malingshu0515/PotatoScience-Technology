# -*- coding: utf-8 -*-
u"""_zf95_recipes.py —— ZF95：用户给的 5 条合成配方上线

用户原话（一条到底）：
    「配方 茉莉花唱片；四角灵魂灯笼 最中间一个火把花 火把花紧挨着四个粗金块 共和国之砧；
      最左 最右一列皆为红石粉 最中间一个铁砧 上下各一个钛锭 合金炉主控；
      【铝板】【铁板】【铝板】，【镍板】【电容】【镍板】，【加热装置】【一般金属块】【散热装置】 分馏塔控制器；
      【钢板】【钢板】【钢板】，【耐热金属块】【铜块】【耐热金属块】，【高碳钢】【黑曜石】【高碳钢】 分馏塔操作器；
      【钴锭】【钢板】【钴锭】，【流体泵】【钻石块】【灌装机】，【油罐】【分馏塔控制器】【油罐】」

**切法**：按「**名字在前、九宫格在后**」用 `；` 切开（`配方` 是表头）——
切开后**五段的前半都是"某件的摆法"、后半都是"某件东西"，而且每段摆法都正好填满 9 格**，
没有一格落空、也没有一件东西多出来 ⇒ 这个切法自带证据（另一种切法会把「共和国之砧」当成材料）。

**材料对照表**（逐个核过 id 存在）：
  灵魂灯笼 = minecraft:soul_lantern        火把花 = minecraft:torchflower
  粗金块   = minecraft:raw_gold_block      红石粉 = minecraft:redstone
  铁砧     = minecraft:anvil               铜块   = minecraft:copper_block
  黑曜石   = minecraft:obsidian            钻石块 = minecraft:diamond_block
  钛锭 = #c:ingots/titanium  钴锭 = #c:ingots/cobalt  高碳钢 = #c:ingots/steel
  （三个都是本工程自己挂的 `c:` 标签 ⇒ 一定解析得出；锭按长期规则走 `c:`，与灌装机那条一致）
  其余全用 `item:` 直指本工程自己的东西（与本工程既有配方同款）

⚠ 「**油罐**」我按 **`potato_s_t:high_pressure_tank`（高压气罐）** 理解：它是本工程唯一能用配方做出来的"罐"，
  另外四条机器配方也都拿它当罐体；而 `测试流体储罐` **自己没有配方**，拿它当材料会把这条配方**锁死**。
  要是你指的是别的东西，说一声换一个 id（一行）。

用法：
    python _zf95_recipes.py            # 预演
    python _zf95_recipes.py --write    # 真写
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
ITEMD = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\models\item")
TOOLS = os.path.join(ROOT, "build", "zftools")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

# 材料 -> key 字母（同一条配方里一个字母只对应一种材料）
MAT = {
    "soul_lantern": {"item": "minecraft:soul_lantern"},
    "torchflower": {"item": "minecraft:torchflower"},
    "raw_gold_block": {"item": "minecraft:raw_gold_block"},
    "redstone": {"item": "minecraft:redstone"},
    "anvil": {"item": "minecraft:anvil"},
    "copper_block": {"item": "minecraft:copper_block"},
    "obsidian": {"item": "minecraft:obsidian"},
    "diamond_block": {"item": "minecraft:diamond_block"},
    "titanium": {"tag": "c:ingots/titanium"},
    "cobalt": {"tag": "c:ingots/cobalt"},
    "steel": {"tag": "c:ingots/steel"},
    "aluminum_plate": {"item": "potato_s_t:aluminum_plate"},
    "iron_plate": {"item": "potato_s_t:iron_plate"},
    "nickel_plate": {"item": "potato_s_t:nickel_plate"},
    "steel_plate": {"item": "potato_s_t:steel_plate"},
    "capacitor": {"item": "potato_s_t:capacitor"},
    "heater": {"item": "potato_s_t:heater"},
    "common_metal_block": {"item": "potato_s_t:common_metal_block"},
    "heat_sink": {"item": "potato_s_t:heat_sink"},
    "heat_resistant_metal_block": {"item": "potato_s_t:heat_resistant_metal_block"},
    "fluid_pump": {"item": "potato_s_t:fluid_pump"},
    "filling_machine": {"item": "potato_s_t:filling_machine"},
    "high_pressure_tank": {"item": "potato_s_t:high_pressure_tank"},
    "distillation_controller": {"item": "potato_s_t:distillation_controller"},
}

# 五条配方：**九宫格逐格写死**（就是用户那句话的那 9 格），再给字母表
RECIPES = [
    {
        "file": "music_disc_jasmine_flower",
        "zh": u"茉莉花唱片",
        "origin": u"四角灵魂灯笼；最中间火把花；紧挨火把花的四格是粗金块",
        "grid": [["soul_lantern", "raw_gold_block", "soul_lantern"],
                 ["raw_gold_block", "torchflower", "raw_gold_block"],
                 ["soul_lantern", "raw_gold_block", "soul_lantern"]],
        "keys": {"L": "soul_lantern", "G": "raw_gold_block", "T": "torchflower"},
        "result": "potato_s_t:music_disc_jasmine_flower",
        "category": "misc",
    },
    {
        "file": "music_disc_anvil_of_the_republic",
        "zh": u"共和国之砧",
        "origin": u"最左与最右一列都是红石粉；最中间铁砧；铁砧上下各一个钛锭",
        "grid": [["redstone", "titanium", "redstone"],
                 ["redstone", "anvil", "redstone"],
                 ["redstone", "titanium", "redstone"]],
        "keys": {"R": "redstone", "T": "titanium", "A": "anvil"},
        "result": "potato_s_t:music_disc_anvil_of_the_republic",
        "category": "misc",
    },
    {
        "file": "alloy_smelter",
        "zh": u"合金炉主控",
        "origin": u"铝板/铁板/铝板 · 镍板/电容/镍板 · 加热装置/一般金属块/散热装置",
        "grid": [["aluminum_plate", "iron_plate", "aluminum_plate"],
                 ["nickel_plate", "capacitor", "nickel_plate"],
                 ["heater", "common_metal_block", "heat_sink"]],
        "keys": {"A": "aluminum_plate", "I": "iron_plate", "N": "nickel_plate",
                 "C": "capacitor", "H": "heater", "M": "common_metal_block", "K": "heat_sink"},
        "result": "potato_s_t:alloy_smelter",
        "category": "misc",
    },
    {
        "file": "distillation_controller",
        "zh": u"分馏塔控制器",
        "origin": u"钢板×3 · 耐热金属块/铜块/耐热金属块 · 高碳钢/黑曜石/高碳钢",
        "grid": [["steel_plate", "steel_plate", "steel_plate"],
                 ["heat_resistant_metal_block", "copper_block", "heat_resistant_metal_block"],
                 ["steel", "obsidian", "steel"]],
        "keys": {"S": "steel_plate", "H": "heat_resistant_metal_block", "C": "copper_block",
                 "K": "steel", "O": "obsidian"},
        "result": "potato_s_t:distillation_controller",
        "category": "misc",
    },
    {
        "file": "distillation_operator",
        "zh": u"分馏塔操作器",
        "origin": u"钴锭/钢板/钴锭 · 流体泵/钻石块/灌装机 · 油罐(=高压气罐)/分馏塔控制器/油罐",
        "grid": [["cobalt", "steel_plate", "cobalt"],
                 ["fluid_pump", "diamond_block", "filling_machine"],
                 ["high_pressure_tank", "distillation_controller", "high_pressure_tank"]],
        "keys": {"C": "cobalt", "S": "steel_plate", "P": "fluid_pump", "D": "diamond_block",
                 "F": "filling_machine", "T": "high_pressure_tank", "R": "distillation_controller"},
        "result": "potato_s_t:distillation_operator",
        "category": "misc",
    },
]
fails = []


def build(rec):
    letter = {}
    for k, mat in rec["keys"].items():
        if mat in letter:
            fails.append(u"%s：材料 %s 有两个字母" % (rec["file"], mat))
        letter[mat] = k
    pattern = []
    for row in rec["grid"]:
        pattern.append(u"".join(letter[m] for m in row))
    key = {letter[m]: MAT[m] for m in rec["keys"].values()}
    return {
        "type": "minecraft:crafting_shaped",
        "category": rec["category"],
        "pattern": pattern,
        "key": {k: key[k] for k in sorted(key)},
        "result": {"id": rec["result"], "count": 1},
    }


def main(argv):
    write = "--write" in argv
    print(u"== ① 逐条核对：九宫格 vs 用户原话 ==")
    docs = []
    for rec in RECIPES:
        d = build(rec)
        docs.append(d)
        cells = [c for row in rec["grid"] for c in row]
        print(u"\n  %s（%s）" % (rec["zh"], rec["file"]))
        print(u"    用户原话：%s" % rec["origin"])
        for row in rec["grid"]:
            print(u"      " + u"  ".join(u"%-26s" % m for m in row))
        assert len(cells) == 9, rec["file"]
        # 逐格核：每个材料都在 MAT 里、且字母表覆盖全部 9 格
        for c in cells:
            if c not in MAT:
                fails.append(u"%s：材料 %s 不在材料表里" % (rec["file"], c))
        used = set(rec["keys"].values())
        if used != set(cells):
            fails.append(u"%s：字母表用了 %s，九宫格用了 %s" % (rec["file"], sorted(used), sorted(set(cells))))
        print(u"    pattern = %s" % d["pattern"])
        print(u"    key     = %s" % u", ".join(u"%s=%s" % (k, v.get("item") or v.get("tag"))
                                              for k, v in d["key"].items()))

    print(u"\n== ② 结果与材料 id 都得真的存在 ==")
    for rec in RECIPES:
        rid = rec["result"].split(":")[1]
        ok = os.path.exists(os.path.join(ITEMD, rid + ".json"))
        print(u"  %-34s %s" % (rec["result"], u"OK（models/item 里有）" if ok else u"**缺**"))
        if not ok:
            fails.append(u"结果 %s 没有 models/item" % rec["result"])
        for k, mat in rec["keys"].items():
            v = MAT[mat]
            if v.get("item", "").startswith("potato_s_t:"):
                nm = v["item"].split(":")[1]
                if not os.path.exists(os.path.join(ITEMD, nm + ".json")):
                    fails.append(u"%s：材料 %s 没有 models/item" % (rec["file"], v["item"]))

    print(u"\n== ③ 三条 `c:` 标签本工程自己挂着（一定解析得出）==")
    tags = os.path.join(ROOT, r"src\main\resources\data\c\tags\item\ingots")
    for t in ("cobalt", "titanium", "steel"):
        p = os.path.join(tags, t + ".json")
        ok = os.path.exists(p)
        print(u"  #c:ingots/%-9s %s" % (t, u"OK" if ok else u"**缺**"))
        if not ok:
            fails.append(u"标签 c:ingots/%s 不在本工程里" % t)

    print(u"\n== ④ 写盘 ==")
    if fails:
        print(u"  [STOP] %d 条不过 ⇒ 什么都不写" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    if not write:
        print(u"  预演：没加 --write，未写盘")
        return 0
    for rec, d in zip(RECIPES, docs):
        p = os.path.join(RDIR, rec["file"] + ".json")
        if os.path.exists(p):
            fails.append(u"%s 已存在（本轮只新增，不覆盖）" % p)
            continue
        io.open(p, "w", encoding="utf-8", newline=u"\n").write(
            json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        json.loads(io.open(p, encoding="utf-8").read())
        print(u"  [OK]   %s.json（%d 字节）" % (rec["file"], os.path.getsize(p)))

    print(u"\n== ⑤ 活体数字：crafting_shaped 30 → 35 ==")
    vp = os.path.join(TOOLS, "_zf71_verify.py")
    t = io.open(vp, encoding="utf-8").read()
    old = u"check(craft == 30, u\"合成配方 %d 条\" % craft)"
    new = u"check(craft == 35, u\"合成配方 %d 条\" % craft)  # ZF95 起 35（用户给的 5 条：两张唱片 + 合金炉主控 + 分馏塔控制器/操作器）"
    if t.count(old) != 1:
        fails.append(u"_zf71_verify.py 锚点命中 %d 次" % t.count(old))
    else:
        io.open(vp, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
        print(u"  [OK]   _zf71_verify.py：合成配方 30 → 35")

    print(u"\n== ⑥ 英文公告：这三件不再是「没有配方」 ==")
    a = io.open(ANN, encoding="utf-8").read()
    old = (u"- **A few blocks are still creative-only**: the Alloy Smelter Controller, the Lithium Battery,\n"
           u"  the Advanced Metal Block, the Stable Metal Block, the Distillation Tower Controller and the\n"
           u"  Distillation Tower Operator have no crafting recipe yet.")
    new = (u"- **A few blocks are still creative-only**: the Lithium Battery, the Advanced Metal Block and\n"
           u"  the Stable Metal Block have no crafting recipe yet. (The Alloy Smelter Controller, the\n"
           u"  Distillation Tower Controller and the Distillation Tower Operator **got their recipes in\n"
           u"  this build**, and so did both music discs.)")
    if a.count(old) != 1:
        fails.append(u"公告那段「creative-only」锚点命中 %d 次" % a.count(old))
    else:
        io.open(ANN, "w", encoding="utf-8", newline=u"\n").write(a.replace(old, new, 1))
        print(u"  [OK]   公告 §9 那段已改")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
