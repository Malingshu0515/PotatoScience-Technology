# -*- coding: utf-8 -*-
"""ZF38 事后校验（**不改任何文件**，只读）。
上一版 `_zf38_apply.py` 的最后一条断言写错了 —— 它数的是"字面反斜杠+n"，
而 `json.loads` 早就把 JSON 的 `\n` 转义还原成**真换行**了，所以 4 条全挂。
数据本身是对的（JSON 合法、键都在），错的是断言。这里改成数量换行符，并顺带把
"文件里到底是转义还是真换行"直接看一眼打印出来。
"""
import io
import json
import os
import sys

ROOT = r"E:\PotatoST"
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")
BID = "low_generator"

fail = []


def check(ok, msg):
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fail.append(msg)


print("== ① lang ×4 ==")
for code in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
    path = os.path.join(ASSETS, "lang", code + ".json")
    raw = io.open(path, encoding="utf-8").read()
    data = json.loads(raw)
    bk = "block.potato_s_t." + BID
    tk = "tooltip.potato_s_t." + BID
    check(bk in data, "%s 有 %s = %s" % (code, bk, data.get(bk)))
    tip = data.get(tk, "")
    check(tip.count("\n") == 3, "%s 说明 4 行（真换行数 = %d）" % (code, tip.count("\n")))
    # 直接看文件里的原始形态：应当是 JSON 转义 \n（两个字符），不是真的换行
    line = [l for l in raw.split("\n") if '"' + tk + '"' in l]
    check(len(line) == 1 and "\\n" in line[0] and line[0].count("\\n") == 3,
          "%s 文件里是 JSON 转义 \\n ×3（单行合法 JSON）" % code)

print()
print("== ② 原版标签 ×2 ==")
for rel, label in ((r"minecraft\tags\block\mineable\pickaxe.json", "mineable/pickaxe"),
                   (r"minecraft\tags\block\needs_stone_tool.json", "needs_stone_tool")):
    obj = json.loads(io.open(os.path.join(DATA, rel), encoding="utf-8").read())
    check("potato_s_t:" + BID in obj["values"], "%s 含 potato_s_t:%s（共 %d 项）"
          % (label, BID, len(obj["values"])))

print()
print("== ③ 模型 / 掉落表 / 配方 ==")
bs = json.loads(io.open(os.path.join(ASSETS, "blockstates", BID + ".json"), encoding="utf-8").read())
check(bs["variants"][""]["model"] == "potato_s_t:block/" + BID, "blockstate 指向 potato_s_t:block/" + BID)

bm = json.loads(io.open(os.path.join(ASSETS, "models", "block", BID + ".json"), encoding="utf-8").read())
check(bm["textures"]["side"] == "potato_s_t:block/%s_side" % BID, "block model side 贴图")
check(bm["textures"]["top"] == "potato_s_t:block/%s_top" % BID, "block model top 贴图")
for t in ("side", "top"):
    p = os.path.join(ASSETS, "textures", "block", "%s_%s.png" % (BID, t))
    check(os.path.exists(p), "贴图存在 %s_%s.png（%d 字节）" % (BID, t, os.path.getsize(p)))

im = json.loads(io.open(os.path.join(ASSETS, "models", "item", BID + ".json"), encoding="utf-8").read())
check(im["parent"] == "potato_s_t:block/" + BID, "item model parent 正确")

lt = json.loads(io.open(os.path.join(DATA, "potato_s_t", "loot_table", "blocks", BID + ".json"),
                        encoding="utf-8").read())
check(lt["pools"][0]["entries"][0]["name"] == "potato_s_t:" + BID, "掉落表掉自己")
check(lt["random_sequence"] == "potato_s_t:blocks/" + BID, "掉落表 random_sequence 正确")

rc = json.loads(io.open(os.path.join(DATA, "potato_s_t", "recipe", BID + ".json"), encoding="utf-8").read())
print("      pattern = " + " | ".join(rc["pattern"]))
for k in sorted(rc["key"]):
    v = rc["key"][k]
    print("      %s = %s" % (k, v.get("item") or ("#" + v["tag"])))
print("      result  = %s x%d" % (rc["result"]["id"], rc["result"]["count"]))
check(rc["pattern"] == ["IBI", "SRS", "CFC"], "pattern = IBI / SRS / CFC")
check(rc["key"]["I"] == {"tag": "c:ingots/iron"}, "I = #c:ingots/iron（别的 mod 的铁锭也行）")
check(rc["key"]["B"] == {"item": "minecraft:iron_block"}, "B = 原版铁块")
check(rc["key"]["S"] == {"tag": "c:ingots/silver"}, "S = #c:ingots/silver")
check(rc["key"]["R"] == {"item": "minecraft:redstone_block"}, "R = 红石块")
check(rc["key"]["C"] == {"item": "minecraft:copper_block"}, "C = 铜块")
check(rc["key"]["F"] == {"item": "minecraft:furnace"}, "F = 熔炉")
check(rc["result"] == {"id": "potato_s_t:" + BID, "count": 1}, "result = 1 个低级发电机")

print()
if fail:
    print("有 %d 项失败：" % len(fail))
    for m in fail:
        print("   - " + m)
    sys.exit(1)
print("全部通过。")
