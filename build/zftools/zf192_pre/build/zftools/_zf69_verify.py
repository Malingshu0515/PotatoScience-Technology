# -*- coding: utf-8 -*-
"""_zf69_verify.py —— ZF69 常驻校验：散热装置配方（加热装置围一圈青金石）

用户原话：「给散热装置加一个配方 加热装置围一圈青金石」。

验的是"用户那句话"本身，而不是"我写出来的 JSON 长什么样"：
  · 把九格 pattern **翻译成物品 id**，要求 中心=加热装置、其余 8 格=青金石
    —— 不看字符叫什么（L/H 还是 A/B 都行），只看摆出来是什么；
  · 青金石必须是原版的（打错一个字母 ⇒ 配方静默做不出来，见 RecipeCheck 注释）；
  · 与生成器表 `_zf45_recipes.py` **逐字节**一致（防以后手改 JSON 和表脱钩）；
  · 全目录只有一条配方出散热装置（防重复配方）；
  · 档案里"装饰方块还剩 N 个没有配方"这类**逐条清点**的话必须跟着改（§4.36：文档断言会腐坏）；
  · 产物 jar 里带着这一份、且没混进探针类。

退出码 0 = 全过。
"""
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import zipfile

ROOT = r"E:\PotatoST"
RECIPE_DIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
MODBLOCKS = os.path.join(ROOT, r"src\main\java\com\potatost\mod\ModBlocks.java")
GEN = os.path.join(ROOT, r"build\zftools\_zf45_recipes.py")
DOCS = os.path.join(ROOT, r"docs\开发档案.md")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"
def _mod_version():
    """从 gradle.properties 读版本 —— 0.10 之后产物名跟着版本走，别再写死。"""
    try:
        with io.open(os.path.join(ROOT, "gradle.properties"), "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("mod_version="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return "0.10"


def _newest(patterns):
    hits = []
    for p in patterns:
        hits.extend(glob.glob(p))
    hits = [h for h in hits if os.path.isfile(h)]
    hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return hits[0] if hits else patterns[0]


MOD_VERSION = _mod_version()
BUILD_JAR = _newest([os.path.join(ROOT, r"build\libs\potato_s_t-%s.jar" % MOD_VERSION),
                     os.path.join(ROOT, r"build\libs\potato_s_t-*.jar")])

NAME = "heat_sink"
CENTER_ITEM = "potato_s_t:heater"
RING_ITEM = "minecraft:lapis_lazuli"
RESULT = "potato_s_t:heat_sink"
MIN_CRAFTING = 29             # 0.11 ZF73 起是 29（28 合成 + 油桶）—— 改成下界：
                              # 语义是「不许变少」，以后再加配方不用每次都来改这一行
MIN_TOTAL_JSON = 35   # 同上：34 → 35（+oil_bucket.json）

fails = []
examined = 0


def check(ok, msg):
    global examined
    examined += 1
    print(("  [OK]   " if ok else "  [FAIL] ") + msg)
    if not ok:
        fails.append(msg)
    return ok


def read(path, mode="r"):
    if mode == "rb":
        with io.open(path, "rb") as fh:
            return fh.read()
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def sha1(data):
    return hashlib.sha1(data).hexdigest()


# ============================================================
#  ① 配方语义：把九格翻译成 id 再对
# ============================================================
print("== ① 配方文件：九格摆出来是什么 ==")
path = os.path.join(RECIPE_DIR, NAME + ".json")
if not os.path.isfile(path):
    check(False, "缺 %s.json" % NAME)
    print("\n失败项 = %d" % len(fails))
    sys.exit(1)

raw = read(path)
obj = json.loads(raw)
check(obj.get("type") == "minecraft:crafting_shaped", "type = crafting_shaped（实际 %s）" % obj.get("type"))
check(obj.get("category") == "misc", "category = misc（与另外 15 条生成器配方一致，实际 %s）" % obj.get("category"))

pattern = obj.get("pattern", [])
key = obj.get("key", {})
check(len(pattern) == 3 and all(len(r) == 3 for r in pattern), "3x3 图纸（实际 %s）" % pattern)

# 字符 -> 物品 id
flat = "".join(pattern)
ch_map = {}
for ch in sorted(key):
    entry = key[ch]
    ch_map[ch] = entry.get("item") or ("#" + entry.get("tag", ""))
    check("item" in entry, "key '%s' 用 item 而不是 tag（青金石/加热装置都是具体物品，实际 %s）" % (ch, entry))

center_ch = pattern[1][1] if len(pattern) == 3 and len(pattern[1]) == 3 else None
cells = [ch_map.get(c, "?<未定义>") for c in flat]
print("     翻译后：" + " / ".join(" ".join(cells[i * 3:i * 3 + 3]) for i in range(3)))

check(center_ch is not None and center_ch != pattern[0][0],
      "中心与外圈用的是**两个不同字符**（否则同一个字符要同时当加热装置和青金石，物理上做不到）")
check(len(cells) == 9 and cells[4] == CENTER_ITEM,
      "正中间 = %s（实际 %s）" % (CENTER_ITEM, cells[4] if len(cells) == 9 else "?"))
ring = [cells[i] for i in range(9) if i != 4] if len(cells) == 9 else []
check(len(ring) == 8 and all(c == RING_ITEM for c in ring),
      "外圈 8 格全是 %s（实际 %s）" % (RING_ITEM, sorted(set(ring))))
check(len(key) == 2, "key 恰好 2 个字符（实际 %d 个：%s）" % (len(key), ",".join(sorted(key))))
check(all(ch in flat for ch in key), "key 里没有用不到的字符")

res = obj.get("result", {})
check(res.get("id") == RESULT, "产物 id = %s（实际 %s）" % (RESULT, res.get("id")))
check(res.get("count") == 1, "产物 1 个（实际 %s）" % res.get("count"))

# ============================================================
#  ② 三个 id 真的存在
# ============================================================
print()
print("== ② 用到的三个 id 真实存在 ==")
blocks = read(MODBLOCKS)
for bid in (NAME, "heater"):
    check(re.search(r'BLOCKS\.register\("%s"' % bid, blocks) is not None,
          "ModBlocks 注册了方块 %s" % bid)
    check(re.search(r'register\("%s",\s*\n?\s*\(\) -> new BlockItem\(' % bid, blocks) is not None,
          "%s 有物品形态（配方产物必须是物品）" % bid)
if os.path.isfile(VANILLA_JAR):
    with zipfile.ZipFile(VANILLA_JAR) as z:
        names = set(z.namelist())
    check("assets/minecraft/models/item/lapis_lazuli.json" in names,
          "原版真的有 minecraft:lapis_lazuli（client.jar 里有它的模型）")
else:
    check(False, "找不到原版 client.jar，无法核对青金石 id")

# ============================================================
#  ③ 与生成器表逐字节一致（防手改 JSON 漂移）
# ============================================================
print()
print("== ③ 磁盘上的 JSON == 生成器表重跑出来的字节 ==")
spec = importlib.util.spec_from_file_location("zf45_recipes", GEN)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
entry = [r for r in gen.RECIPES if r["name"] == NAME]
check(len(entry) == 1, "生成器表里有且仅有一条 %s（实际 %d 条）" % (NAME, len(entry)))
if entry:
    problems = []
    gen_name, gen_obj = gen.build(entry[0], problems)
    check(not problems, "生成器自检无问题（%s）" % ("; ".join(problems) if problems else "0 项"))
    gen_text = json.dumps(gen_obj, ensure_ascii=False, indent=2) + "\n"
    check(gen_text == raw, "文件 %s == 表重跑 %s（%s）" % (sha1(raw.encode("utf-8"))[:12],
                                                          sha1(gen_text.encode("utf-8"))[:12],
                                                          "一致" if gen_text == raw else "不一致"))
    check(entry[0]["pattern"] == pattern, "表里的 pattern 与文件一致（%s）" % " / ".join(entry[0]["pattern"]))

# ============================================================
#  ④ 账目：配方总数 / 唯一性
# ============================================================
print()
print("== ④ 账目 ==")
all_json = sorted(n for n in os.listdir(RECIPE_DIR) if n.endswith(".json"))
crafting, producers = [], {}
for n in all_json:
    d = json.loads(read(os.path.join(RECIPE_DIR, n)))
    if d.get("type") == "minecraft:crafting_shaped":
        crafting.append(n)
        rid = d.get("result", {}).get("id")
        producers.setdefault(rid, []).append(n)
check(len(all_json) >= MIN_TOTAL_JSON, "recipe/ 下 JSON = %d 份（实际 %d）" % (MIN_TOTAL_JSON, len(all_json)))
check(len(crafting) >= MIN_CRAFTING, "定形配方 = %d 条（实际 %d）" % (MIN_CRAFTING, len(crafting)))
check(producers.get(RESULT) == [NAME + ".json"],
      "只有 %s.json 出 %s（实际 %s）" % (NAME, RESULT, producers.get(RESULT)))
dups = {k: v for k, v in producers.items() if len(v) > 1}
check(not dups, "没有任何产物被两条配方重复定义（实际 %s）" % (dups if dups else "0 处"))

# ============================================================
#  ⑤ 档案里的"逐条清点"必须跟着改（§4.36）
# ============================================================
print()
print("== ⑤ 档案不再说『散热装置没有配方』==")
docs = read(DOCS)
lines = docs.split("\n")
hits = [(i, m.group(1)) for i, ln in enumerate(lines)
        for m in [re.search(r"还剩\s*(\d+)\s*个没有配方", ln)] if m]
check(len(hits) == 1, "档案里只有一处『还剩 N 个没有配方』（实际 %d 处）" % len(hits))
if hits:
    i, n = hits[0]
    check(n == "2", "那个数字已经改成 2（实际 %s）" % n)
    window = "\n".join(lines[i:i + 3])
    check(NAME not in window, "这份名单里不再有 heat_sink（窗口内实际%s）" % ("没有" if NAME not in window else "还有"))
check(re.search(r"\|\s*ZF69\s*\|", docs) is not None, "§5 表里有 ZF69 这一行")
check("heat_resistant_metal_block" in docs, "对照组还在（已有配方的耐热金属块仍在名单里）")

# ============================================================
#  ⑥ 产物 jar
# ============================================================
print()
print("== ⑥ 产物 jar ==")
if not os.path.isfile(BUILD_JAR):
    check(False, "找不到 %s（先跑 build）" % BUILD_JAR)
else:
    with zipfile.ZipFile(BUILD_JAR) as z:
        names = z.namelist()
        rel = "data/potato_s_t/recipe/%s.json" % NAME
        check(rel in names, "jar 里有 %s" % rel)
        if rel in names:
            check(z.read(rel) == raw.encode("utf-8"), "jar 里那份与源文件逐字节一致")
        check(not [n for n in names if "Check" in n], "jar 里没混进探针类（实际 %s）"
              % [n for n in names if "Check" in n])
        jar_crafting = 0
        for n in names:
            if re.match(r"data/potato_s_t/recipe/.*\.json$", n):
                try:
                    d = json.loads(z.read(n).decode("utf-8"))
                except Exception:
                    continue
                if d.get("type") == "minecraft:crafting_shaped":
                    jar_crafting += 1
        check(jar_crafting >= MIN_CRAFTING, "jar 里定形配方 = %d 条（实际 %d）" % (MIN_CRAFTING, jar_crafting))

release = _newest([os.path.join(ROOT, r"release\PotatoST-%s.jar" % MOD_VERSION),
                        os.path.join(ROOT, r"release\PotatoST-*.jar")])
if os.path.isfile(release):
    same = sha1(read(release, "rb")) == sha1(read(BUILD_JAR, "rb"))
    print("     [INFO] release 成品与 build 产物%s（%s）" % ("一致" if same else "**还不一致**（出成品前正常）",
                                                            sha1(read(release, "rb"))[:12]))

print()
print("检查项 = %d" % examined)
print("失败项 = %d" % len(fails))
for m in fails:
    print("   - " + m)
sys.exit(1 if fails else 0)
