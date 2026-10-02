# -*- coding: utf-8 -*-
u"""_zf167_data.py —— 本轮五份数据文件（配方 ×4 + 乙醇流体标签 ×1），生成 + 回读校验

用户原话里的两张图纸（一个字没改）：

  **空铝罐**（产出 2 个）：
      【】【铝粒】【】
      【】【铝板】【】
      【】【】【】

  **饮料罐装机**：
      【】【铁锭】【】
      【拉杆】【银板】【铁活板门】
      【轻质压力板】【高压气罐】【流体管道】

外加熔炉/高炉两条：**一个空铝罐 → 5 个铝粒**。

⚠ `light_weighted_pressure_plate` 是原版那块（轻质测重压力板）—— 本 mod **没有**压力板
   （把 `ModBlocks` 全扫过一遍，没有 pressure_plate），所以"轻质压力板"只能取原版那一块。
   已挂档案 §9 待用户确认（另一种读法是本 mod 的轻质钛合金做基底的板，但那件物品不存在）。
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
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
TAG = os.path.join(ROOT, r"src\main\resources\data\c\tags\fluid")


def shaped(pattern, key, result_id, count):
    return {
        u"type": u"minecraft:crafting_shaped",
        u"category": u"misc",
        u"pattern": pattern,
        u"key": {k: {u"item": v} for k, v in key.items()},
        u"result": {u"id": result_id, u"count": count},
    }


def cooking(kind, ingredient_id, result_id, count, time, xp=0.1):
    return {
        u"type": kind,
        u"category": u"misc",
        u"ingredient": {u"item": ingredient_id},
        u"result": {u"id": result_id, u"count": count},
        u"experience": xp,
        u"cookingtime": time,
    }


FILES = [
    # 空铝罐：铝粒在上、铝板在中 ⇒ 2 个
    (os.path.join(RECIPE, u"empty_aluminum_can.json"),
     shaped([u" N ", u" P ", u"   "],
            {u"N": u"potato_s_t:aluminum_nugget", u"P": u"potato_s_t:aluminum_plate"},
            u"potato_s_t:empty_aluminum_can", 2)),
    # 熔炉：1 个空铝罐 → 5 个铝粒（200 tick = 10 秒，原版熔炉节奏）
    (os.path.join(RECIPE, u"empty_aluminum_can_from_smelting.json"),
     cooking(u"minecraft:smelting", u"potato_s_t:empty_aluminum_can",
             u"potato_s_t:aluminum_nugget", 5, 200)),
    # 高炉：同上，100 tick（原版高炉是熔炉的一半时间）
    (os.path.join(RECIPE, u"empty_aluminum_can_from_blasting.json"),
     cooking(u"minecraft:blasting", u"potato_s_t:empty_aluminum_can",
             u"potato_s_t:aluminum_nugget", 5, 100)),
    # 机器本体（用户给的三行图纸）
    (os.path.join(RECIPE, u"beverage_canning_machine.json"),
     shaped([u" I ", u"LST", u"PHF"],
            {u"I": u"minecraft:iron_ingot",
             u"L": u"minecraft:lever",
             u"S": u"potato_s_t:silver_plate",
             u"T": u"minecraft:iron_trapdoor",
             u"P": u"minecraft:light_weighted_pressure_plate",
             u"H": u"potato_s_t:high_pressure_tank",
             u"F": u"potato_s_t:fluid_pipe"},
            u"potato_s_t:beverage_canning_machine", 1)),
    # 乙醇流体标签：本 mod 自己没有乙醇，空表 + replace:false ⇒ 装了 IE 时与它那份**合并**
    (os.path.join(TAG, u"ethanol.json"),
     {u"replace": False, u"values": []}),
]

fails, notes = [], []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def main():
    print(u"① 写出五份数据文件")
    for path, data in FILES:
        rel = os.path.relpath(path, ROOT)
        text = json.dumps(data, ensure_ascii=False, indent=2) + u"\n"
        if os.path.exists(path):
            cur = io.open(path, encoding="utf-8").read()
            check(u"%s 已存在且内容相同（幂等）" % os.path.basename(path), cur == text)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
        check(u"写出 %s" % rel, os.path.exists(path))

    print(u"\n② 回读：五份都能解析、且形状与用户给的一致")
    can = json.loads(io.open(os.path.join(RECIPE, u"empty_aluminum_can.json"), encoding="utf-8").read())
    check(u"空铝罐：图纸 3 行 x 3 列", all(len(r) == 3 for r in can[u"pattern"])
          and len(can[u"pattern"]) == 3)
    check(u"空铝罐：铝粒在上、铝板在中、第三行空",
          can[u"pattern"][0][1] == u"N" and can[u"pattern"][1][1] == u"P"
          and can[u"pattern"][2].strip() == u"")
    check(u"空铝罐：产物 2 个", can[u"result"][u"count"] == 2)
    mac = json.loads(io.open(os.path.join(RECIPE, u"beverage_canning_machine.json"),
                             encoding="utf-8").read())
    want = [[u" ", u"I", u" "], [u"L", u"S", u"T"], [u"P", u"H", u"F"]]
    check(u"机器：图纸与用户给的三行逐格相同", [list(r) for r in mac[u"pattern"]] == want,
          str(mac[u"pattern"]))
    for tag, item in ((u"I", u"minecraft:iron_ingot"), (u"L", u"minecraft:lever"),
                      (u"S", u"potato_s_t:silver_plate"), (u"T", u"minecraft:iron_trapdoor"),
                      (u"P", u"minecraft:light_weighted_pressure_plate"),
                      (u"H", u"potato_s_t:high_pressure_tank"), (u"F", u"potato_s_t:fluid_pipe")):
        check(u"机器：%s = %s" % (tag, item), mac[u"key"][tag][u"item"] == item)
    for name, kind, time in ((u"empty_aluminum_can_from_smelting.json", u"minecraft:smelting", 200),
                             (u"empty_aluminum_can_from_blasting.json", u"minecraft:blasting", 100)):
        d = json.loads(io.open(os.path.join(RECIPE, name), encoding="utf-8").read())
        check(u"%s：%s / 1 罐 → %d 个铝粒 / %d tick"
              % (name, kind, d[u"result"][u"count"], d[u"cookingtime"]),
              d[u"type"] == kind and d[u"result"][u"count"] == 5
              and d[u"result"][u"id"] == u"potato_s_t:aluminum_nugget"
              and d[u"cookingtime"] == time)
    eth = json.loads(io.open(os.path.join(TAG, u"ethanol.json"), encoding="utf-8").read())
    check(u"乙醇标签：replace=false + 空表（装了别的 mod 时与它那份合并）",
          eth.get(u"replace") is False and eth.get(u"values") == [])

    print(u"\n③ 交叉核对：图纸里点到的每一件都必须真实注册")
    item_src = io.open(os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModItems.java"),
                       encoding="utf-8").read()
    block_src = io.open(os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModBlocks.java"),
                        encoding="utf-8").read()
    ours = set()
    for src in (item_src, block_src):
        i = 0
        while True:
            i = src.find(u'ITEMS.register("', i + 1)
            if i < 0:
                break
            # ⚠ 下标别数错：`ITEMS.register("` 是 16 个字符（含那个引号），
            #   第一版写成 i+15 ⇒ 名字前面多带一个引号 ⇒ 七件全判"没注册"（假红）。
            j = src.find(u'"', i + 16)
            ours.add(u"potato_s_t:" + src[i + 16:j])
    used = set()
    for path, _d in FILES:
        if u"recipe" not in path:
            continue
        t = io.open(path, encoding="utf-8").read()
        for token in t.replace(u'"', u" ").split():
            if token.startswith(u"potato_s_t:") and token.endswith((u",", u"")):
                used.add(token.rstrip(u","))
    missing = sorted(x for x in used if x not in ours)
    check(u"图纸里用到的本 mod 物品都已注册（%d 件）" % len(used), not missing, u"、".join(missing))

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
