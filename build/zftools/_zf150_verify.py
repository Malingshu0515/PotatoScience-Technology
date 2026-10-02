# -*- coding: utf-8 -*-
r"""_zf150_verify.py —— ZF150 **常驻校验**：四种粒（0.12）

用户原话：「嗯嗯放素材了几张图 其中四种粒你先注册一下 配方就是原版的
（对应锭合成9个粒 9个粒合成1个锭 记得加标签兼容别的mod）重复一遍！现在是0.12版本」

判据分七组（不跑游戏就能查的全在这；能失败才算判据）：

A 注册：`ModItems.java` 里 4 个 `register("<材料>_nugget")` 都在，且都在创造页 `accept`。
B 资源：4 张贴图（16x16/8位/RGBA/有透明）、4 个模型（layer0 指向自己）。
C 配方 · 无序（锭→9粒）：8 份新配方都在；4 份 shapeless 的
   type/category/ingredients/result 逐字段对；**数量恰好 9**。
D 配方 · 定形（9粒→锭）：pattern 3×3 全 `#`、key `#` 指粒、`group` 与材料同名、
   `result.count` 恰好 1，且**与对应锭 id 一致**。
E 标签（用户点名的"兼容别的mod"）：单件 `c:nuggets/<材料>` 4 份 + 聚合 `c:nuggets`；
   **聚合里必须引用那 4 个 `#c:nuggets/…`**；且这些标签**能被解析到**
   （本模组自己声明的就算数）。
F 语言：五语言都有这 4 个键；四语言各 **593**、`lzh` **595**；
   与改前件比**只多这 4 个键**、旧键值一字未改。
G 跟平：往轮门里的活体数字（`EXPECT_KEYS` 等）都跟到 593；
   `_zf149_verify.py` 的**成品 jar 靶子**（579/581）**不许动**。
"""
import ast
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
TOOLS = os.path.join(ROOT, "build", "zftools")
SRC = os.path.join(ROOT, r"src\main\java\com\potatost\mod")
ASSETS = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t")
RECIPE = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
CTAGS = os.path.join(ROOT, r"src\main\resources\data\c\tags\item")
LANG = os.path.join(ASSETS, "lang")
PRE = os.path.join(TOOLS, "zf150_pre")

MATS = ["aluminum", "cobalt", "nickel", "silver"]
CN = {"aluminum": u"铝", "cobalt": u"钴", "nickel": u"镍", "silver": u"银"}
KEYS4, KEYS5 = 593, 595

fails = []
count = 0


def check(ok, label, detail=u""):
    global count
    count += 1
    if ok:
        print(u"  [OK] %s" % label)
    else:
        print(u"  [FAIL] %s%s" % (label, (u"   " + detail) if detail else u""))
        fails.append(label)
    return ok


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else None


def jload(p):
    t = read(p)
    return json.loads(t) if t else None


print(u"================ A 注册 ================")
mi = read(os.path.join(SRC, "ModItems.java")) or u""
for m in MATS:
    check(u'register("%s_nugget"' % m in mi or re.search(r'register\("%s_nugget"' % m, mi) is not None,
          u"A1 %s_nugget 已注册" % m)
    field = u"%s_NUGGET" % m.upper()
    check(field in mi and u"output.accept(%s.get())" % field in mi,
          u"A2 %s 进了创造页" % field)

print(u"\n================ B 资源 ================")
sys.path.insert(0, TOOLS)
from PngRecolor import read_png  # noqa: E402
for m in MATS:
    tp = os.path.join(ASSETS, "textures", "item", m + "_nugget.png")
    if not os.path.exists(tp):
        check(False, u"B1 textures/item/%s_nugget.png 在" % m)
        continue
    blob = open(tp, "rb").read()
    w, h, rgba = read_png(tp)
    op = sum(1 for i in range(w * h) if rgba[i * 4 + 3] == 255)
    check((w, h, blob[24], blob[25]) == (16, 16, 8, 6),
          u"B1 %s_nugget.png 规格 16x16/8位/RGBA" % m, u"实际 %dx%d" % (w, h))
    check(op > 0 and op < w * h, u"B2 %s_nugget.png 有透明底（不透明 %d）" % (m, op))
    mp = os.path.join(ASSETS, "models", "item", m + "_nugget.json")
    mo = jload(mp)
    check(mo is not None and mo.get("textures", {}).get("layer0") == u"potato_s_t:item/%s_nugget" % m,
          u"B3 models/item/%s_nugget.json 指向自己的贴图" % m)

print(u"\n================ C 配方 · 无序（锭 → 9 粒）================")
for m in MATS:
    p = os.path.join(RECIPE, m + "_nugget.json")
    o = jload(p)
    if not check(o is not None, u"C1 %s_nugget.json 在" % m):
        continue
    check(o.get("type") == "minecraft:crafting_shapeless",
          u"C2 %s：type = crafting_shapeless（原版口径）" % m, str(o.get("type")))
    check(o.get("category") == "misc", u"C3 %s：category = misc" % m, str(o.get("category")))
    ing = o.get("ingredients") or []
    check(len(ing) == 1 and ing[0].get("item") == u"potato_s_t:%s_ingot" % m,
          u"C4 %s：原料 = 对应的锭" % m, json.dumps(ing, ensure_ascii=False))
    res = o.get("result") or {}
    check(res.get("id") == u"potato_s_t:%s_nugget" % m and res.get("count") == 9,
          u"C5 %s：产出 9 个粒" % m, json.dumps(res, ensure_ascii=False))

print(u"\n================ D 配方 · 定形（9 粒 → 锭）================")
for m in MATS:
    p = os.path.join(RECIPE, m + "_ingot_from_nuggets.json")
    o = jload(p)
    if not check(o is not None, u"D1 %s_ingot_from_nuggets.json 在" % m):
        continue
    check(o.get("type") == "minecraft:crafting_shaped",
          u"D2 %s：type = crafting_shaped" % m, str(o.get("type")))
    check(o.get("pattern") == ["###", "###", "###"],
          u"D3 %s：pattern 3×3 全 #" % m, json.dumps(o.get("pattern")))
    check(o.get("key", {}).get("#", {}).get("item") == u"potato_s_t:%s_nugget" % m,
          u"D4 %s：key # = 对应的粒" % m)
    check(o.get("group") == u"%s_ingot" % m,
          u"D5 %s：group = %s_ingot（照原版 iron_ingot_from_nuggets）" % (m, m), str(o.get("group")))
    res = o.get("result") or {}
    check(res.get("id") == u"potato_s_t:%s_ingot" % m and res.get("count") == 1,
          u"D6 %s：产出 1 个锭" % m, json.dumps(res, ensure_ascii=False))

print(u"\n================ E 标签（兼容别的 mod）================")
for m in MATS:
    o = jload(os.path.join(CTAGS, "nuggets", m + ".json"))
    check(o is not None and o.get("values") == [u"potato_s_t:%s_nugget" % m],
          u"E1 c:nuggets/%s 存在且指本模组的粒" % m,
          json.dumps(o, ensure_ascii=False) if o else u"文件不在")
agg = jload(os.path.join(CTAGS, "nuggets.json"))
check(agg is not None, u"E2 聚合标签 c:nuggets 存在")
if agg:
    vals = agg.get("values") or []
    for m in MATS:
        check(u"#c:nuggets/%s" % m in vals, u"E3 c:nuggets 引用了 #c:nuggets/%s" % m)
    # 与 NeoForge 自带的同 id 标签合并后不会互相顶掉（同 id 标签是**合并**语义）
    check(any(isinstance(v, dict) and str(v.get("id", "")).startswith("#forge:nuggets")
              for v in vals), u"E4 带了 #forge:nuggets 的 required:false 回退（老 Forge 系互通）")

print(u"\n================ F 语言 ================")
tables = {}
for lg in ("zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"):
    tables[lg] = jload(os.path.join(LANG, lg + ".json")) or {}
    want = KEYS5 if lg == "lzh" else KEYS4
    check(len(tables[lg]) == want, u"F1 %s = %d 键" % (lg, want), u"实际 %d" % len(tables[lg]))
    for m in MATS:
        k = u"item.potato_s_t.%s_nugget" % m
        check(k in tables[lg] and tables[lg][k].strip() != u"",
              u"F2 %s 有 %s 且非空" % (lg, k))
# 四语言键集合一致；lzh = 四语言 + 2
base = set(tables["zh_cn"])
for lg in ("en_us", "ja_jp", "ru_ru"):
    check(set(tables[lg]) == base, u"F3 %s 键集合与 zh_cn 一致" % lg,
          u"差 %s" % sorted(set(tables[lg]) ^ base)[:4])
check(set(tables["lzh"]) ^ base == {u"language.name", u"language.region"},
      u"F4 lzh = 四语言 + language.name/region 两个", u"差 %s" % sorted(set(tables["lzh"]) ^ base))

if os.path.isdir(PRE):
    for lg in tables:
        old = jload(os.path.join(PRE, "src", "main", "resources", "assets",
                                 "potato_s_t", "lang", lg + ".json"))
        if not old:
            continue
        newkeys = set(tables[lg]) - set(old)
        want = {u"item.potato_s_t:%s" % "" }
        added = {k for k in newkeys}
        expect = {u"item.potato_s_t.%s_nugget" % m for m in MATS}
        check(added == expect, u"F5 %s 相对改前件只多了这 4 个键" % lg,
              u"多了 %s" % sorted(added - expect))
        changed = [k for k in old if k in tables[lg] and tables[lg][k] != old[k]]
        check(not changed, u"F6 %s 旧键的值一字未改" % lg, u"变了 %s" % changed[:4])
else:
    check(False, u"F5/F6 改前件 zf150_pre 不在盘上，没法比")

print(u"\n================ G 跟平 ================")
GUARDS = {
    "_zf100_verify.py": u"EXPECT_KEYS = %d",
    "_zf101_verify.py": u"EXPECT_KEYS = %d",
    "_zf102_verify.py": u"EXPECT_KEYS = %d",
    "_zf103_verify.py": u"len(table) == %d",
    "_zf107_verify.py": u"EXPECT_KEYS = %d",
    "_zf109_verify.py": u"EXPECT_KEYS = %d",
    "_zf111_verify.py": u"EXPECT_KEYS = %d",
    "_zf112_verify.py": u"EXPECT_KEYS = %d",
    "_zf114_verify.py": u"EXPECT_KEYS = %d",
    "_zf117_verify.py": u"KEY_OLD, KEY_NEW = 432, %d",
    "_zf118_verify.py": u"KEY_NEW = %d",
    "_zf119_verify.py": u"KEY_OLD, KEY_NEW = 448, %d",
    "_zf122_verify.py": u"EXPECT_KEYS = %d",
    "_zf139_verify.py": u"KEYS_BEFORE, KEYS_AFTER = 482, %d",
    "_zf141_verify.py": u"KEYS = %d",
    "_zf145_verify.py": u"KEYS_ALL, N_NEW = %d, 8",
    "_zf73_verify.py": u"all(v == %d for v in counts.values())",
    "_zf75_verify.py": u"all(v == %d for v in counts.values())",
    "_zf78_verify.py": u"list(counts.values())[0] == %d",
    "_zf79_verify.py": u"list(counts.values())[0] == %d",
    "_zf80_verify.py": u"EXPECT_KEYS = %d",
    "_zf82_verify.py": u"EXPECT_KEYS = %d",
    "_zf93_verify.py": u"EXPECT_KEYS = %d",
    "_zf96_verify.py": u"EXPECT_KEYS = %d",
    "_zf97_verify.py": u"EXPECT_KEYS = %d",
    "_zf98_verify.py": u"EXPECT_KEYS = %d",
}
for f, tmpl in sorted(GUARDS.items()):
    p = os.path.join(TOOLS, f)
    needle = tmpl % KEYS4
    check(os.path.exists(p) and needle in read(p), u"G1 %s 跟到 %d" % (f, KEYS4), needle)

# 成品 jar 的靶子**不许动**
z149 = read(os.path.join(TOOLS, "_zf149_verify.py")) or u""
check(u"579" in z149 and u"581" in z149,
      u"G2 _zf149_verify.py 的成品 jar 靶子（579/581）**没动**（本轮不打包）")

# 全部门语法自检
bad = []
for f in sorted(os.listdir(TOOLS)):
    if not (f.startswith("_zf") and f.endswith("_verify.py")):
        continue
    try:
        ast.parse(io.open(os.path.join(TOOLS, f), encoding="utf-8").read())
    except SyntaxError as e:
        bad.append((f, str(e)))
check(not bad, u"G3 全部 _zf*_verify.py 语法可解析", u"%s" % bad[:3])

print(u"\n" + u"=" * 46)
print(u"断言数 = %d   失败项 = %d" % (count, len(fails)))
for f in fails:
    print(u"  !! " + f)
print(u"结论: %s" % (u"通过" if not fails else u"有失败项"))
sys.exit(1 if fails else 0)
