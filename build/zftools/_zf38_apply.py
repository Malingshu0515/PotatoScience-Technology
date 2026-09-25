# -*- coding: utf-8 -*-
"""ZF38：低级发电机的资源（模型 / 掉落表 / 配方 / lang / 两张原版标签）。

用户原话：
  「加一个低级发电机 第一行【铁锭】【铁块】【铁锭】第二行【银锭】【红石块】【银锭】
   第三行【铜块】【熔炉】【铜块】右键打开gui只有能量槽和输入槽
   放置煤炭或木炭 1个发电45s 100Fe/t发电量 储能1k」

⚠ 插行函数必须把**收尾字符**当参数传：lang 是 `}`、标签文件是 `]`（ZF34 在这踩过，§6.13 附近）。
"""
import io
import json
import os
import sys

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")
LANG = os.path.join(ASSETS, "lang")

BID = "low_generator"

BLOCK_NAME = {
    "zh_cn": u"低级发电机",
    "en_us": u"Low-Tier Generator",
    "ja_jp": u"低級発電機",
    "ru_ru": u"Простой генератор",
}
TOOLTIP = {
    "zh_cn": u"燃烧煤炭或木炭发电。\\n每块燃料燃烧 45 秒，发电 100 FE/t。\\n内部储能 1000 FE，存满时暂停燃烧。\\n红石信号通入时停机。",
    "en_us": u"Burns coal or charcoal to generate power.\\nEach fuel item burns for 45 seconds at 100 FE/t.\\nInternal storage is 1000 FE; burning pauses when full.\\nA redstone signal halts operation.",
    "ja_jp": u"石炭または木炭を燃やして発電します。\\n燃料 1 個につき 45 秒間、100 FE/t で発電します。\\n内部蓄電は 1000 FE で、満杯になると燃焼を一時停止します。\\nレッドストーン信号の入力中は停止します。",
    "ru_ru": u"Сжигает уголь или древесный уголь для выработки энергии.\\nОдна единица топлива горит 45 секунд при 100 FE/т.\\nВнутренний запас — 1000 FE; при заполнении горение приостанавливается.\\nСигнал красного камня останавливает работу.",
}

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


def write_json(path, obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    json.loads(text)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def insert_before_closer(path, new_lines, closer, expect_delta, what):
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)
    orig = before["values"] if isinstance(before, dict) and "values" in before else list(before)
    lines = text.split("\n")

    close_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == closer:
            close_idx = i
            break
    if close_idx is None:
        raise SystemExit("找不到收尾符号 %r: %s" % (closer, path))

    j = close_idx - 1
    while lines[j].strip() == "":
        j -= 1
    if not lines[j].rstrip().endswith(","):
        lines[j] = lines[j].rstrip() + ","

    lines[close_idx:close_idx] = new_lines
    out = "\n".join(lines)

    after = json.loads(out)
    now = after["values"] if isinstance(after, dict) and "values" in after else list(after)
    check(len(now) - len(orig) == expect_delta,
          "%s 条目 %d → %d（应 +%d）" % (what, len(orig), len(now), expect_delta))
    lost = [v for v in orig if v not in now]
    check(not lost, "%s 原有 %d 项全部保留（丢失 %d）" % (what, len(orig), len(lost)))

    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    return after


print("=" * 72)
print(u"① blockstate / block model / item model / loot table")
print("=" * 72)
write_json(os.path.join(ASSETS, "blockstates", BID + ".json"),
           {"variants": {"": {"model": "potato_s_t:block/" + BID}}})
check(True, "blockstates/%s.json" % BID)

# 与液压机 / 微型粉碎机 / 盐分解构器同一套写法：整块 16³ + side/top 两张贴图（对称无朝向）
faces = {}
for face in ("up", "down"):
    faces[face] = {"uv": [0, 0, 16, 16], "texture": "#top"}
for face in ("north", "south", "east", "west"):
    faces[face] = {"uv": [0, 0, 16, 16], "texture": "#side"}
write_json(os.path.join(ASSETS, "models", "block", BID + ".json"), {
    "parent": "minecraft:block/block",
    "textures": {
        "top": "potato_s_t:block/%s_top" % BID,
        "side": "potato_s_t:block/%s_side" % BID,
        "particle": "potato_s_t:block/%s_side" % BID,
    },
    "elements": [{"from": [0, 0, 0], "to": [16, 16, 16], "faces": faces}],
})
check(True, "models/block/%s.json" % BID)

write_json(os.path.join(ASSETS, "models", "item", BID + ".json"),
           {"parent": "potato_s_t:block/" + BID})
check(True, "models/item/%s.json" % BID)

write_json(os.path.join(DATA, "potato_s_t", "loot_table", "blocks", BID + ".json"), {
    "type": "minecraft:block",
    "pools": [{
        "bonus_rolls": 0.0,
        "conditions": [{"condition": "minecraft:survives_explosion"}],
        "entries": [{"type": "minecraft:item", "name": "potato_s_t:" + BID}],
        "rolls": 1.0
    }],
    "random_sequence": "potato_s_t:blocks/" + BID
})
check(True, "loot_table/blocks/%s.json" % BID)

print()
print("=" * 72)
print(u"② 合成配方：铁锭 铁块 铁锭 / 银锭 红石块 银锭 / 铜块 熔炉 铜块")
print("=" * 72)
write_json(os.path.join(DATA, "potato_s_t", "recipe", BID + ".json"), {
    "type": "minecraft:crafting_shaped",
    "category": "misc",
    "pattern": ["IBI", "SRS", "CFC"],
    "key": {
        "I": {"tag": "c:ingots/iron"},          # 铁锭（走 c: 标签，别的 mod 的铁锭也行）
        "B": {"item": "minecraft:iron_block"},  # 铁块（原版方块全 mod 共用）
        "S": {"tag": "c:ingots/silver"},        # 银锭
        "R": {"item": "minecraft:redstone_block"},
        "C": {"item": "minecraft:copper_block"},
        "F": {"item": "minecraft:furnace"},
    },
    "result": {"id": "potato_s_t:" + BID, "count": 1}
})
check(True, "recipe/%s.json" % BID)

print()
print("=" * 72)
print(u"③ lang ×4：block 名 + Shift 说明（收尾字符 = '}'）")
print("=" * 72)
for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    lines = [
        u'    "block.potato_s_t.%s":  "%s",' % (BID, BLOCK_NAME[code]),
        u'    "tooltip.potato_s_t.%s":  "%s"' % (BID, TOOLTIP[code]),
    ]
    after = insert_before_closer(path, lines, "}", 2, code + ".json")
    check(after.get("block.potato_s_t." + BID) == BLOCK_NAME[code],
          "%s block 名 = %s" % (code, after.get("block.potato_s_t." + BID)))
    tip = after.get("tooltip.potato_s_t." + BID, "")
    check(tip.count("\\n") == 3, "%s 说明是 4 行（3 个 \\n）" % code)

print()
print("=" * 72)
print(u"④ 原版标签 ×2：mineable/pickaxe + needs_stone_tool（收尾字符 = ']'）")
print("=" * 72)
for rel, label in ((r"minecraft\tags\block\mineable\pickaxe.json", "mineable/pickaxe"),
                   (r"minecraft\tags\block\needs_stone_tool.json", "needs_stone_tool")):
    path = os.path.join(DATA, rel)
    after = insert_before_closer(path, [u'    "potato_s_t:%s"' % BID], "]", 1, label)
    check("potato_s_t:" + BID in after["values"], "%s 含 potato_s_t:%s" % (label, BID))

print()
if fail:
    print("有 %d 项失败：" % len(fail))
    for m in fail:
        print("   - " + m)
    sys.exit(1)
print(u"全部通过。")
