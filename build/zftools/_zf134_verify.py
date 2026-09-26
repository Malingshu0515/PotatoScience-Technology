# -*- coding: utf-8 -*-
u"""_zf134_verify.py —— 本轮（星璨钢斧的合成配方）的常驻校验

用户原话：「星璨钢斧头加个配方 **原版斧头配方 原材料换成星璨钢**就行」。

**这一轮的全部风险就在"原版斧头配方"这六个字上**：斧子那张图纸不是方方正正的 2×2，
而是三行、且**第三行第一格是空的**：

```
XX          X = 材料锭（本例换成星璨钢锭）
X#          # = 木棍
 #
```

写错一格（比如写成 2×2、或把第三行的空格补上、或把两根棍摆在同一列）——
游戏里只是"摆上去做不出来"，不报任何错；而 `RecipeCheck.ps1` 只查"模式里的字符在不在 key 里"，
**形状语义它管不着**。所以本探针的核心是**逐格、逐字符地跟 client.jar 里那张原版斧头对照**，
而且不只对铁那一张（铁 / 钻石 / 金 / 下界合金四张的 pattern 必须**完全一致**，
这才能证明我们抄的是"原版斧头"而不是"碰巧对上了铁那一张"）。

证据来源：
  · 原版配方 —— `E:\\gradle-home\\caches\\minecraft\\versions\\1.21.1\\client.jar`
    的 `data/minecraft/recipe/<material>_axe.json`（**现抠**，不靠记忆）；
  · 本模组 —— 盘上 `data/potato_s_t/recipe/star_steel_axe.json` + `ModItems.java`；
  · 「表与盘一致」—— 直接 `import` 生成器 `_zf45_recipes.py`，把表里那条渲染出来跟盘上比
    （§4.93：手改 JSON 会在下次 `--write` 时被**静默打回**，这条断言就是防它的）。

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python E:\\PotatoST\\build\\zftools\\_zf134_verify.py      # 退出码 0 = 全过
"""
import importlib.util
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

PROJ = r"E:\PotatoST"
ZT = os.path.join(PROJ, "build", "zftools")
RDIR = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t", "recipe")
JAVA = os.path.join(PROJ, "src", "main", "java", "com", "potatost", "mod")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

RECIPE_NAME = u"star_steel_axe"
RESULT = u"potato_s_t:star_steel_axe"
MATERIAL = u"potato_s_t:star_steel_ingot"
# 原版**五张**斧头图纸（`wooden/stone/iron/golden/diamond`）pattern 完全一样；
#   ⚠ **下界合金斧没有 shaped 配方**（它走锻造台），所以名单里不能有它 ——
#     第一版写了 `netherite`，`zipfile` 当场 `KeyError`（这也算"现抠"的好处：名字对不对立刻见分晓）。
#   `X` 那一格：木斧/石斧用的是**标签**（`minecraft:planks` / `minecraft:stone_tool_materials`），
#   本模组用精确 id —— 所以下面只把"这一格是材料"的事实钉住，不要求它跟某一张原版同形。
VANILLA_MATERIALS = [u"wooden", u"stone", u"iron", u"golden", u"diamond"]
# 活体数字：盘上 crafting_shaped 总数（加上本轮这一张）
# ⚠ ZF141：星璨钢剑/镐/锄 +3 张 shaped（59 → 62）；活体数字，加配方就要跟
# ⚠ ZF143：星璨钢锹 +1（62 → 63）；活体数字，加配方就要跟
EXPECT_SHAPED = 63

fails = []
count = 0


def check(ok, label, detail=u""):
    global count
    count += 1
    if ok:
        print(u"  [OK]   " + label)
    else:
        print(u"  [FAIL] " + label + (u"   " + detail if detail else u""))
        fails.append(label)
    return ok


def read(p):
    return io.open(p, encoding="utf-8").read()


def read_json(p):
    return json.loads(read(p))


def load_generator():
    u"""把生成器表 import 进来（它自己在 `__main__` 里才跑 main，import 是安全的）。"""
    spec = importlib.util.spec_from_file_location(
        "gen", os.path.join(ZT, u"_zf45_recipes.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    spec.loader.exec_module(mod)
    return mod


def key_of(keydict, ch):
    u"""把 {'X': {'item': '...'}} 这种取成 '...'（item 或 #tag 都认）。"""
    entry = keydict.get(ch) or {}
    return entry.get(u"item") or (u"#" + entry[u"tag"] if entry.get(u"tag") else None)


def main():
    disk = os.path.join(RDIR, RECIPE_NAME + u".json")
    with zipfile.ZipFile(VANILLA_JAR) as zf:
        vanilla = {m: json.loads(zf.read(u"data/minecraft/recipe/%s_axe.json" % m))
                   for m in VANILLA_MATERIALS}

    print(u"")
    print(u"================ ① 产物本身：注册 + 创造页 ================")
    items = read(os.path.join(JAVA, u"ModItems.java"))
    check(u'register("star_steel_axe"' in items,
          u"ModItems 注册了 star_steel_axe（ZF133 那一轮加的物品）")
    check(u"output.accept(STAR_STEEL_AXE.get())" in items,
          u"创造页里有它（§4.82：漏了就是「物品栏看不见、JEI 搜不到」，但配方还在）")
    check(u'register("star_steel_ingot"' in items
          or u'register("star_steel_ingot"' in read(os.path.join(JAVA, u"ModArmorItems.java")),
          u"材料 star_steel_ingot 也真的注册了")

    print(u"")
    print(u"================ ② 配方文件：类型 / 分类 / 产物 ================")
    if not check(os.path.isfile(disk), u"盘上有 %s.json" % RECIPE_NAME):
        print(u"\n断言数 = %d   失败项 = %d" % (count, len(fails)))
        return 1
    mine = read_json(disk)
    van_iron = vanilla[u"iron"]
    check(mine.get(u"type") == u"minecraft:crafting_shaped" == van_iron.get(u"type"),
          u"type = crafting_shaped（与原版一致）")
    check(mine.get(u"category") == van_iron.get(u"category") == u"equipment",
          u"category = equipment（与原版一致）",
          u"实际 %r / 原版 %r" % (mine.get(u"category"), van_iron.get(u"category")))
    check(mine.get(u"result") == {u"id": RESULT, u"count": 1},
          u"产物 = %s ×1" % RESULT, u"实际 %s" % mine.get(u"result"))

    print(u"")
    print(u"================ ③ 逐格对照原版斧头（本轮的核心） ================")
    check(mine.get(u"pattern") == van_iron.get(u"pattern"),
          u"pattern 与原版斧头**逐格相同**（%s）" % van_iron.get(u"pattern"),
          u"本工程 %s vs 原版 %s" % (mine.get(u"pattern"), van_iron.get(u"pattern")))
    mine_key, van_key = mine.get(u"key") or {}, van_iron.get(u"key") or {}
    check(set(mine_key) == set(van_key),
          u"key 的字符集合与原版相同（%s）" % sorted(van_key),
          u"本工程 %s vs 原版 %s" % (sorted(mine_key), sorted(van_key)))
    for ch in sorted(van_key):
        want = key_of(van_key, ch)
        got = key_of(mine_key, ch)
        if want == u"minecraft:stick":
            check(got == want, u"key[%s] = %s（照抄原版，没动）" % (ch, want),
                  u"实际 %r" % got)
        else:
            check(got == MATERIAL,
                  u"key[%s]：原版 %s → 本模组 %s（用户点名要换的那一处）" % (ch, want, MATERIAL),
                  u"实际 %r" % got)
    # 「原材料换成星璨钢就行」——除了那一处，**不许**再有任何差异
    diff = [ch for ch in sorted(van_key) if key_of(van_key, ch) != key_of(mine_key, ch)]
    check(diff == [u"X"],
          u"与原版的差异**只有 X 那一格**（实际差异 %s）" % diff)

    print(u"")
    print(u"================ ④ 形状语义：三行、第三行第一格是空的 ================")
    pat = mine.get(u"pattern") or []
    check(len(pat) == 3, u"三行（原版斧头就是三行，不是 2×2）", u"实际 %d 行" % len(pat))
    check(all(len(r) == 2 for r in pat), u"每行两列", u"实际 %s" % [len(r) for r in pat])
    if len(pat) == 3 and all(len(r) == 2 for r in pat):
        check(pat[2][0] == u" ",
              u"第三行第一格是**空格**（补上就成了另一张图纸）", u"实际 %r" % pat[2][0])
        check(pat[1][1] == u"#" and pat[2][1] == u"#",
              u"两根木棍在**同一列**（第二列）", u"实际 %r" % [pat[1][1], pat[2][1]])

    print(u"")
    print(u"================ ⑤ 「原版斧头」不是只对上了铁那一张 ================")
    for m in VANILLA_MATERIALS:
        check(vanilla[m].get(u"pattern") == van_iron.get(u"pattern"),
              u"原版 %s 斧的 pattern 与铁斧相同（所以「照抄原版斧头」这张图纸是唯一的）" % m)
        check(vanilla[m].get(u"category") == u"equipment",
              u"原版 %s 斧的 category 也是 equipment" % m)

    print(u"")
    print(u"================ ⑥ 生成器表与盘上**逐字节一致**（§4.93） ================")
    gen = load_generator()
    entry = [r for r in gen.RECIPES if r.get(u"name") == RECIPE_NAME]
    if check(len(entry) == 1, u"生成器表 `_zf45_recipes.py` 里有且只有一条 %s" % RECIPE_NAME):
        problems = []
        _name, obj = gen.build(entry[0], problems)
        check(not problems, u"生成器自己校验这条配方没有毛病", u"%s" % problems)
        rendered = json.dumps(obj, ensure_ascii=False, indent=2) + u"\n"
        check(rendered == read(disk),
              u"表里渲染出来的那一份与盘上**逐字节相同**（手改 JSON 会被下次 --write 打回）")
    else:
        check(False, u"表里有这条配方", u"找到 %d 条" % len(entry))

    print(u"")
    print(u"================ ⑦ 活体数字：盘上 crafting_shaped = %d ================" % EXPECT_SHAPED)
    names = sorted(n for n in os.listdir(RDIR) if n.endswith(u".json"))
    shaped = [n for n in names
              if (read_json(os.path.join(RDIR, n)) or {}).get(u"type") == u"minecraft:crafting_shaped"]
    check(len(shaped) == EXPECT_SHAPED,
          u"盘上 crafting_shaped = %d 条（活体数字，加配方就要跟）" % EXPECT_SHAPED,
          u"实际 %d" % len(shaped))

    print(u"")
    print(u"==============================")
    print(u"断言数 = %d   失败项 = %d" % (count, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    print(u"结论: %s" % (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
