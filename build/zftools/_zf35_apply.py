# -*- coding: utf-8 -*-
"""ZF35：`接线块` → 方块 `wiring_block`。

用户原话：「再加个接线块」+ 一张 `接线块_001.png`（160×160 webp）。
沿用 ZF34 定下的做法：**中文不能当 ResourceLocation**（§4.24），
所以 id 用 ASCII（`wiring_block`），中文只留在 lang 显示名里；
定位同 ZF34 那 6 个（普通装饰方块、无功能、不加配方、不挂 c: 标签）——
用户当时说过「就是普通装饰 后面用于组合多方快结构的机器」。

⚠ 插行函数**必须把收尾字符当参数传**：lang 是 `}`、标签文件是 `]`。
   ZF34 就是在这里踩过（把逗号加到了 `]` 后面），详见 `_zf34_tags.py` 顶部注释。
"""
import io
import json
import os
import sys

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")
LANG = os.path.join(ASSETS, "lang")

BID = "wiring_block"
NAMES = {
    "zh_cn": u"接线块",
    "en_us": u"Wiring Block",
    "ja_jp": u"配線ブロック",
    "ru_ru": u"Соединительный блок",
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
print(u"① 生成 blockstate / block model / item model / loot table")
print("=" * 72)
write_json(os.path.join(ASSETS, "blockstates", BID + ".json"),
           {"variants": {"": {"model": "potato_s_t:block/" + BID}}})
check(True, "blockstates/%s.json" % BID)

write_json(os.path.join(ASSETS, "models", "block", BID + ".json"),
           {"parent": "minecraft:block/cube_all",
            "textures": {"all": "potato_s_t:block/" + BID}})
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
print(u"② lang ×4 各插 1 个 block.potato_s_t.wiring_block（收尾字符 = '}'）")
print("=" * 72)
for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(LANG, code + ".json")
    after = insert_before_closer(
        path, [u'    "block.potato_s_t.%s":  "%s"' % (BID, NAMES[code])], "}", 1, code + ".json")
    key = "block.potato_s_t." + BID
    check(after.get(key) == NAMES[code], "%s: %s = %s" % (code, key, after.get(key)))

print()
print("=" * 72)
print(u"③ 原版标签 ×2 各插 1 个值（收尾字符 = ']'）")
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
