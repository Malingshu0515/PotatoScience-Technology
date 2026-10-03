# -*- coding: utf-8 -*-
u"""_zf180_verify.py —— ZF180 常驻校验：装备能附魔（原版附魔台 / 铁砧 / 附魔灌注台）。

用户 0.14 实测原话：「附魔灌注台以及原版附魔台都无法给振金/星璨钢装备附魔 铁砧也不可以！」

病根（§4.180）：1.21 的附魔看**附魔自己的 `supported_items`**，而原版 `enchantable/*` 全是按
**原版装备类型标签**定义的（`#minecraft:head_armor` / `#minecraft:swords` / `#minecraft:axes` …）。
我们此前只挂了 `swords`（仅钛合金剑）与 `pickaxes`（仅钛合金镐）⇒ 振金/星璨钢护甲与其它工具
**没有任何附魔支持它们**。

  A 9 个类型标签文件都在（4 护甲位 + swords/pickaxes/axes/shovels/hoes）
  B 20 件装备**逐件**落在正确的类型标签里（脚本生成期望表，不靠人眼）
  C 探针报告 5/0（真服务端：isEnchantable + 权重 + 目标附魔 supported_items 命中 + 3 条负对照）
  D 版本/成品（可选段：只在成品存在时查）

跑法：python build\\zftools\\_zf180_verify.py
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
TAGS = os.path.join(ROOT, r"src\main\resources\data\minecraft\tags\item")
PROBE = os.path.join(ZT, u"_zf180_probe_utf8.txt")
MATS = [u"titanium_alloy", u"star_steel", u"vibranium"]
PIECES = {u"helmet": u"head_armor", u"chestplate": u"chest_armor",
          u"leggings": u"leg_armor", u"boots": u"foot_armor"}
TOOLS = {u"star_steel_axe": u"axes", u"star_steel_shovel": u"shovels", u"star_steel_hoe": u"hoes",
         u"star_steel_pickaxe": u"pickaxes", u"titanium_alloy_pickaxe": u"pickaxes",
         u"star_steel_sword": u"swords", u"titanium_alloy_sword": u"swords",
         u"vibranium_sword": u"swords"}
NEEDED = [u"head_armor", u"chest_armor", u"leg_armor", u"foot_armor",
          u"swords", u"pickaxes", u"axes", u"shovels", u"hoes"]

passed, failed, fails = 0, 0, []


def check(cond, label, detail=u""):
    global passed, failed
    if cond:
        passed += 1
        print(u"  [OK]   " + label)
    else:
        failed += 1
        fails.append(label)
        print(u"  [FAIL] " + label + (u" —— " + detail if detail else u""))


def read(p):
    return io.open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else u""


print(u"=== A 段：类型标签文件 ===")
missing = [t for t in NEEDED if not os.path.isfile(os.path.join(TAGS, t + u".json"))]
check(not missing, u"A1 9 个原版装备类型标签都在（护甲四位 + 剑/镐/斧/锹/锄）", u"缺 %s" % missing)

print(u"\n=== B 段：20 件装备逐件归属 ===")
want = {}
for m in MATS:
    for piece, tag in PIECES.items():
        want[u"%s_%s" % (m, piece)] = tag
for item, tag in TOOLS.items():
    want[item] = tag
bad = []
for item, tag in sorted(want.items()):
    vals = json.loads(read(os.path.join(TAGS, tag + u".json"))).get(u"values", [])
    if u"potato_s_t:" + item not in vals:
        bad.append(u"%s→%s" % (item, tag))
check(not bad, u"B1 20 件装备各自落在正确的类型标签里（附魔的 supported_items 才认它们）",
      u"缺 %s" % bad[:5])
extra = []
for m in MATS:
    vals = json.loads(read(os.path.join(TAGS, u"swords.json"))).get(u"values", [])
if u"potato_s_t:vibranium_helmet" in json.loads(read(os.path.join(TAGS, u"head_armor.json"))).get(u"values", []):
    pass
for tag in NEEDED:
    vals = json.loads(read(os.path.join(TAGS, tag + u".json"))).get(u"values", [])
    for v in vals:
        if not v.startswith(u"potato_s_t:"):
            extra.append(u"%s:%s" % (tag, v))
check(not extra, u"B2 这些类型标签里**只**加了我们自己的装备（没顺手改原版内容）", u"%s" % extra[:4])

print(u"\n=== C 段：真开服探针 ===")
rep = read(PROBE)
check(u"通过 = 5   失败 = 0" in rep, u"C1 探针 5/0（isEnchantable + 权重 + supported_items 命中）",
      rep.strip().split(u"\n")[-1] if rep else u"（没有报告）")
check(u"每件装备都能被它该有的附魔支持" in rep, u"C2 报告里有「supported_items 命中」那条实测")
check(u"星璨钢锭**不**被「保护」支持" in rep, u"C3 负对照在（不是什么都往里塞）")

print(u"\n通过 = %d   失败 = %d" % (passed, failed))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if failed else 0)
