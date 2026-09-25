# -*- coding: utf-8 -*-
"""ZF34：6 个装饰方块落地（用户：普通装饰，后面用于组合多方块结构的机器）。

用户确认：
  · id 用我提的那套（common/advanced/stable/heat_resistant *_metal_block + heater + heat_sink）
  · 「就是普通装饰 后面用于组合多方快结构的机器」⇒ 6 个都是普通完整方块，无 BE、无功能
  · 不加配方（ZF33 就说了「这几个先不加配方」）
  · 不挂 c: 标签（既定规则：默认兼容范围只有粗矿/矿石/锭）

本脚本干四件事，每件都带**能失败的**断言：
  1) 把 6 张中文名贴图改名成 ASCII，并证明**内容没变**（改名前后 SHA256 必须相等）
  2) 生成 6×blockstate + 6×block model + 6×item model + 6×loot table
  3) 4 个 lang 各插 6 个 `block.potato_s_t.<id>` 键（插入后 JSON 必须仍合法、键数必须 +6）
  4) 2 个原版标签（mineable/pickaxe、needs_stone_tool）各插 6 个值（同上）

⚠ 插 lang 时**不要**用 json.load→json.dump：那会把 `"key":  "value"` 的双空格
   改成单空格、整个文件全变动。这里一律**按行插**，插完再 json.loads 校验。
"""
import hashlib
import io
import json
import os
import sys

ROOT = r"E:\PotatoST"
TEX = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures\block")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")
LANG = os.path.join(ASSETS, "lang")

# (新 id, 旧中文贴图名, zh, en, ja, ru)
BLOCKS = [
    ("common_metal_block",         "一般金属块.png", "一般金属块", "Common Metal Block",        "一般金属ブロック", "Обычный металлический блок"),
    ("advanced_metal_block",       "高级金属块.png", "高级金属块", "Advanced Metal Block",      "高級金属ブロック", "Улучшенный металлический блок"),
    ("stable_metal_block",         "稳定金属块.png", "稳定金属块", "Stable Metal Block",        "安定金属ブロック", "Стабильный металлический блок"),
    ("heat_resistant_metal_block", "耐热金属块.png", "耐热金属块", "Heat-Resistant Metal Block", "耐熱金属ブロック", "Жаростойкий металлический блок"),
    ("heater",                     "加热装置.png",   "加热装置",   "Heater",                    "加熱装置",         "Нагреватель"),
    ("heat_sink",                  "散热装置.png",   "散热装置",   "Heat Sink",                 "放熱装置",         "Радиатор"),
]

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


def sha256(path):
    h = hashlib.sha256()
    with io.open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def write_json(path, obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    json.loads(text)  # 自校验：写之前先证明它是合法 JSON
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return len(text)


def insert_lines(path, new_lines, expect_delta, what):
    """在文件里"最后一条数据行"后面插行，返回插完后的 JSON。

    通用做法：先 json.loads 确认改前是合法的，再找到收尾符号那一行
    （']' 或 '}'），把它前面最后一条非空数据行补上逗号，然后插入新行。
    """
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    before = json.loads(text)          # 改前就必须合法
    lines = text.split("\n")

    close_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() in ("]", "}"):
            close_idx = i
            break
    if close_idx is None:
        raise SystemExit("找不到收尾符号: " + path)

    j = close_idx - 1
    while lines[j].strip() == "":
        j -= 1
    if not lines[j].rstrip().endswith(","):
        lines[j] = lines[j].rstrip() + ","

    lines[close_idx:close_idx] = new_lines
    out = "\n".join(lines)

    after = json.loads(out)            # 改后也必须合法，否则等于写坏文件
    n_before = len(before["values"]) if isinstance(before, dict) and "values" in before else len(before)
    n_after = len(after["values"]) if isinstance(after, dict) and "values" in after else len(after)
    check(n_after - n_before == expect_delta,
          "%s 条目 %d → %d（应 +%d）" % (what, n_before, n_after, expect_delta))

    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    return after


print("=" * 72)
print("① 贴图改名（中文 → ASCII），并证明内容没变")
print("=" * 72)
for bid, old_name, *_ in BLOCKS:
    src = os.path.join(TEX, old_name)
    dst = os.path.join(TEX, bid + ".png")
    if not os.path.exists(src):
        check(False, "缺素材: " + src)
        continue
    h_before = sha256(src)
    os.replace(src, dst)
    h_after = sha256(dst)
    check(h_before == h_after and os.path.exists(dst),
          "%-26s %s → %s.png  sha256 %s" % (old_name, old_name, bid, "未变" if h_before == h_after else "变了!!"))

print()
print("=" * 72)
print("② 生成 blockstate / block model / item model / loot table")
print("=" * 72)
for bid, _old, *_ in BLOCKS:
    d = os.path.join(ASSETS, "blockstates", bid + ".json")
    write_json(d, {"variants": {"": {"model": "potato_s_t:block/" + bid}}})
    check(True, "blockstates/" + bid + ".json")

    d = os.path.join(ASSETS, "models", "block", bid + ".json")
    write_json(d, {"parent": "minecraft:block/cube_all",
                   "textures": {"all": "potato_s_t:block/" + bid}})
    check(True, "models/block/" + bid + ".json")

    d = os.path.join(ASSETS, "models", "item", bid + ".json")
    write_json(d, {"parent": "potato_s_t:block/" + bid})
    check(True, "models/item/" + bid + ".json")

    # 原版 iron_block 那种最简自掉落：survives_explosion + 掉自己
    d = os.path.join(DATA, "potato_s_t", "loot_table", "blocks", bid + ".json")
    write_json(d, {
        "type": "minecraft:block",
        "pools": [{
            "bonus_rolls": 0.0,
            "conditions": [{"condition": "minecraft:survives_explosion"}],
            "entries": [{"type": "minecraft:item", "name": "potato_s_t:" + bid}],
            "rolls": 1.0
        }],
        "random_sequence": "potato_s_t:blocks/" + bid
    })
    check(True, "loot_table/blocks/" + bid + ".json")

print()
print("=" * 72)
print("③ lang ×4 各插 6 个 block.potato_s_t.<id>")
print("=" * 72)
for idx, code in enumerate(("zh_cn", "en_us", "ja_jp", "ru_ru")):
    path = os.path.join(LANG, code + ".json")
    new_lines = []
    for k, row in enumerate(BLOCKS):
        bid = row[0]
        name = row[2 + idx]
        comma = "," if k < len(BLOCKS) - 1 else ""
        new_lines.append(u'    "block.potato_s_t.%s":  "%s"%s' % (bid, name, comma))
    after = insert_lines(path, new_lines, len(BLOCKS), code + ".json")
    for row in BLOCKS:
        key = "block.potato_s_t." + row[0]
        check(key in after, "%s 含 %s = %s" % (code, key, after.get(key)))

print()
print("=" * 72)
print("④ 原版标签：mineable/pickaxe + needs_stone_tool（否则 requiresCorrectToolForDrops 挖了不掉）")
print("=" * 72)
for rel, label in ((r"minecraft\tags\block\mineable\pickaxe.json", "mineable/pickaxe"),
                   (r"minecraft\tags\block\needs_stone_tool.json", "needs_stone_tool")):
    path = os.path.join(DATA, rel)
    new_lines = []
    for k, row in enumerate(BLOCKS):
        comma = "," if k < len(BLOCKS) - 1 else ""
        new_lines.append(u'    "potato_s_t:%s"%s' % (row[0], comma))
    after = insert_lines(path, new_lines, len(BLOCKS), label)
    vals = after["values"]
    for row in BLOCKS:
        check("potato_s_t:" + row[0] in vals, "%s 含 potato_s_t:%s" % (label, row[0]))

print()
print("=" * 72)
if fail:
    print("有 %d 项失败：" % len(fail))
    for m in fail:
        print("   - " + m)
    sys.exit(1)
print("全部通过。")
