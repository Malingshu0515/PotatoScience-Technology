# -*- coding: utf-8 -*-
u"""_zf178_verify.py —— ZF178 **常驻校验**：磁铁块 + 6 个粗矿块（9 ↔ 1 双向配方，贴图自己画）。

用户原话：「先搞一个磁铁块9磁铁合1个（反过来也一样1块分解9磁铁）然后把所有粗矿都加个块形式
（锂和锰钛振金不需要）参考粗矿本来的风格和原版粗矿块的风格 可以自己画吧」。

  A 注册：磁铁块（ModBlocks，装饰金属块属性）+ 6 个粗矿块（PotatoSTOres.rawBlock 工厂，自动上创造页）
  B 配方：14 份（7 条 3×3 的 9→1 + 7 条 shapeless 的 1→9），内容与产物 id 逐份核
  C 资源：7 张贴图（16×16 RGBA）+ 21 份 JSON（blockstate/方块模型/物品模型）+ 7 份 loot table + 2 个 tag
  D 语言：7 个 block.<id> 键在五份里都非空
  E 生成器表：只校验模式 0 失败（表 ↔ 盘同口径）

跑法：python build\\zftools\\_zf178_verify.py
"""
import io
import json
import os
import struct
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
JAVA = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
DATA = os.path.join(ROOT, r"src\main\resources\data")
LANGDIR = os.path.join(ASSETS, "lang")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
LOCALES = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

RAW_METALS = [u"aluminum", u"cobalt", u"nickel", u"silver", u"tungsten", u"uranium"]
BLOCK_IDS = [u"magnet_block"] + [u"raw_%s_block" % m for m in RAW_METALS]
ITEM_OF = {u"magnet_block": u"magnet"}
for m in RAW_METALS:
    ITEM_OF[u"raw_%s_block" % m] = u"raw_%s" % m

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


def png_size(p):
    with open(p, "rb") as f:
        head = f.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    depth, color = head[24], head[25]
    return w, h, depth, color


print(u"=== A 段：注册 ===")
mb = read(os.path.join(JAVA, u"ModBlocks.java"))
ores = read(os.path.join(JAVA, u"PotatoSTOres.java"))
items = read(os.path.join(JAVA, u"ModItems.java"))
check(u'BLOCKS.register("magnet_block"' in mb and u"MAGNET_BLOCK_ITEM" in mb,
      u"A1 磁铁块在 ModBlocks 里注册（方块 + 块物品）")
check(u"decorativeMetalBlock()" in mb.split(u"MAGNET_BLOCK")[1][:400], u"A2 磁铁块用的是装饰金属块那套属性")
check(ores.count(u"rawBlock(\"raw_") == 6, u"A3 6 个粗矿块都走 rawBlock() 工厂",
      u"实际 %d 个" % ores.count(u'rawBlock("raw_'))
check(u"private static DeferredBlock<Block> rawBlock(" in ores and u"ALL_ORE_ITEMS.add" in ores,
      u"A4 工厂把块物品塞进 ALL_ORE_ITEMS ⇒ 自动上创造页")
check(u"ModBlocks.MAGNET_BLOCK_ITEM.get()" in items, u"A5 磁铁块进了创造页（ModItems 一行）")
for bad in (u"raw_lithium_block", u"raw_manganese_block", u"raw_titanium_block", u"raw_vibranium_block"):
    check(bad not in ores, u"A6 按用户要求**没有** %s" % bad)

print(u"\n=== B 段：14 条配方 ===")
RECIPE = os.path.join(DATA, u"potato_s_t", u"recipe")
problems = []
for bid, item in ITEM_OF.items():
    up = os.path.join(RECIPE, bid + u".json")
    down = os.path.join(RECIPE, item + u"_from_" + bid + u".json")
    if not (os.path.isfile(up) and os.path.isfile(down)):
        problems.append(bid)
        continue
    a = json.loads(read(up))
    b = json.loads(read(down))
    pat = a.get(u"pattern") or []
    ok_up = (a.get(u"type") == u"minecraft:crafting_shaped" and len(pat) == 3
             and all(len(r) == 3 and len(set(r)) == 1 for r in pat)
             and a.get(u"result", {}).get(u"id") == u"potato_s_t:" + bid
             and a.get(u"result", {}).get(u"count") == 1
             and a.get(u"key", {}).get(pat[0][0], {}).get(u"item") == u"potato_s_t:" + item)
    ok_down = (b.get(u"type") == u"minecraft:crafting_shapeless"
               and len(b.get(u"ingredients") or []) == 1
               and b[u"ingredients"][0].get(u"item") == u"potato_s_t:" + bid
               and b.get(u"result", {}).get(u"id") == u"potato_s_t:" + item
               and b.get(u"result", {}).get(u"count") == 9)
    if not (ok_up and ok_down):
        problems.append(bid + u"(内容)")
check(not problems, u"B1 7 组双向配方都在且内容对（9 → 1 shaped；1 → 9 shapeless）",
      u"问题 %s" % problems)
n_rec = sum(len(fs) for _r, _d, fs in os.walk(RECIPE) if True)
check(n_rec >= 112, u"B2 盘上配方 ≥ 112 份（ZF176 的 98 + 本轮 14）", u"实际 %d" % n_rec)

print(u"\n=== C 段：贴图 / 模型 / loot table / tag ===")
tex_bad = []
for bid in BLOCK_IDS:
    p = os.path.join(ASSETS, "textures", "block", bid + u".png")
    if not os.path.isfile(p):
        tex_bad.append(bid + u"(缺)")
        continue
    info = png_size(p)
    if info != (16, 16, 8, 6):
        tex_bad.append(u"%s(%s)" % (bid, info))
check(not tex_bad, u"C1 7 张方块贴图都在，且是 16×16 / 8 位 / RGBA", u"%s" % tex_bad)
json_bad = []
for bid in BLOCK_IDS:
    for rel in (os.path.join("blockstates", bid + u".json"),
                os.path.join("models", "block", bid + u".json"),
                os.path.join("models", "item", bid + u".json")):
        p = os.path.join(ASSETS, rel)
        if not os.path.isfile(p):
            json_bad.append(rel + u"(缺)")
            continue
        try:
            obj = json.loads(read(p))
        except Exception:      # noqa: BLE001
            json_bad.append(rel + u"(解析失败)")
            continue
        if rel.startswith(u"models"):
            blob = json.dumps(obj)
            if u"potato_s_t:block/" + bid not in blob:
                json_bad.append(rel + u"(没引用自己的贴图)")
check(not json_bad, u"C2 21 份 JSON（blockstate + 方块模型 + 物品模型）都在且引用自己的贴图",
      u"%s" % json_bad[:4])
loot_bad = []
for bid in BLOCK_IDS:
    p = os.path.join(DATA, u"potato_s_t", u"loot_table", "blocks", bid + u".json")
    if not os.path.isfile(p):
        loot_bad.append(bid)
        continue
    obj = json.loads(read(p))
    if obj[u"pools"][0][u"entries"][0][u"name"] != u"potato_s_t:" + bid:
        loot_bad.append(bid + u"(掉落对不上)")
check(not loot_bad, u"C3 7 份 loot table 都在且掉落自己", u"%s" % loot_bad)
tag_bad = []
for rel in (os.path.join(u"minecraft", u"tags", u"block", u"mineable", u"pickaxe.json"),
            os.path.join(u"minecraft", u"tags", u"block", u"needs_stone_tool.json")):
    p = os.path.join(DATA, rel)
    vals = json.loads(read(p)).get(u"values", []) if os.path.isfile(p) else []
    miss = [b for b in BLOCK_IDS if u"potato_s_t:" + b not in vals]
    if miss:
        tag_bad.append(u"%s 缺 %s" % (os.path.basename(rel), miss))
check(not tag_bad, u"C4 两个方块 tag 里 7 个新方块都齐（镐可挖 + 要石镐以上）", u"%s" % tag_bad)

print(u"\n=== D 段：语言 ===")
lang_bad = []
for lg in LOCALES:
    p = os.path.join(LANGDIR, lg + u".json")
    obj = json.loads(io.open(p, encoding="utf-8").read())
    for bid in BLOCK_IDS:
        if not (obj.get(u"block.potato_s_t." + bid) or u"").strip():
            lang_bad.append(u"%s/%s" % (lg, bid))
check(not lang_bad, u"D1 7 个 block.<id> 键在五份语言里都非空", u"%s" % lang_bad[:4])
counts = {lg: len(json.loads(io.open(os.path.join(LANGDIR, lg + u".json"), encoding="utf-8").read()))
          for lg in LOCALES}
check(all(counts[k] >= 628 for k in LOCALES[:4]) and counts[u"lzh"] >= 630,
      u"D2 键数 ≥ 628×4 + 630（ZF176 的 621/623 + 本轮 7）", repr(counts))

print(u"\n=== E 段：生成器表 ===")
r = subprocess.run([sys.executable, os.path.join(ZT, u"_zf45_recipes.py")],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
check(r.returncode == 0, u"E1 生成器「只校验」0 失败（表 ↔ 盘同口径）",
      r.stdout.decode("gbk", "replace").strip().split(u"\n")[-1][:80])

print(u"\n通过 = %d   失败 = %d" % (passed, failed))
for f in fails:
    print(u"  !! " + f)
sys.exit(1 if failed else 0)
