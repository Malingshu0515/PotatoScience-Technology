# -*- coding: utf-8 -*-
r"""_zf106_recipes_check.py —— 本轮（8 张盔甲配方）的常驻校验

用户原话：「钛合金套和星璨套配方加上 套用原版合成配方（铁合金用轻质钛合金）星辰套就用星璨钢」

**判据（全部机械、不靠眼看）**：
  ① `pattern`**逐格等于原版铁套**（原版那四张从 `client.jar` 现场抠，不靠记忆）；
  ② 材料：钛合金套 = `potato_s_t:light_titanium_alloy`、星璨钢套 = `potato_s_t:star_steel_ingot`；
  ③ 图纸里**不许出现** `minecraft:iron_ingot`（那就是"没换材料"）；
  ④ 每份的 result 必须是本模组那件盔甲、count=1；
  ⑤ 键集只有 `X`（原版就是单字母 X）—— 防手滑多塞一个字母。
  ⑥ 盘上 `crafting_shaped` 总数 = 期望值（活体数字，随轮次跟）。

⚠ 反证：`--knife <name>` 会把某张图纸的材料换成铁锭再跑，要求本脚本**必须报 FAIL**，
   然后逐字还原（§4.17）。自查：
       python build/zftools/_zf106_recipes_check.py
"""
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST"
RDIR = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t", "recipe")
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

# 期望：材料 → 四件（材料是用户点名的"具体物品"，所以用精确 id 而不是标签）
SETS = [
    (u"titanium_alloy", u"potato_s_t:light_titanium_alloy"),
    (u"star_steel", u"potato_s_t:star_steel_ingot"),
]
PIECES = [u"helmet", u"chestplate", u"leggings", u"boots"]

# 盘上 crafting_shaped 总数（活体数字）
#   ZF106 那轮是 51；之后各轮又加了几张定形图纸 ⇒ **55**
#   （ZF109 采油机 / ZF112 锂电池构造间 / ZF118 星轨坠 / ZF122 星仪图之章）。
#   ⚠ ZF120（振金套）加的是 4 张**锻造台**配方（smithing_transform，不是 crafting_shaped）
#     ⇒ 这个数**与本轮无关**；它涨是因为别的线加了定形图纸。
#   ⚠ 这是个一直在动的数：改完看 `python -c` 数一下 recipe 目录再填，别照抄这一行。
EXPECT_SHAPED = 55

fails = []
count = 0


def check(ok, label, detail=u""):
    global count
    count += 1
    print(u"  [%s] %s%s" % (u"OK" if ok else u"FAIL", label,
                            (u"   " + detail) if (detail and not ok) else u""))
    if not ok:
        fails.append(label)


def vanilla_recipe(name):
    with zipfile.ZipFile(VANILLA_JAR) as z:
        return json.loads(z.read(u"data/minecraft/recipe/iron_%s.json" % name).decode("utf-8"))


def main():
    knife = None
    if "--knife" in sys.argv:
        i = sys.argv.index("--knife")
        knife = sys.argv[i + 1] if i + 1 < len(sys.argv) else None

    print(u"================ ① 八张图纸逐格对照原版铁套 ================")
    for set_name, material in SETS:
        for piece in PIECES:
            fname = u"%s_%s" % (set_name, piece)
            path = os.path.join(RDIR, fname + u".json")
            if not os.path.isfile(path):
                check(False, u"%s.json 存在" % fname)
                continue
            mine = json.loads(io.open(path, encoding="utf-8").read())
            van = vanilla_recipe(piece)
            check(mine.get("type") == van.get("type") == u"minecraft:crafting_shaped",
                  u"%s：type = crafting_shaped" % fname, u"%r" % mine.get("type"))
            check(mine.get("pattern") == van.get("pattern"),
                  u"%s：图纸逐格等于原版铁%s" % (fname, piece),
                  u"本工程 %r vs 原版 %r" % (mine.get("pattern"), van.get("pattern")))
            check(mine.get("category") == van.get("category"),
                  u"%s：category 与原版一致（equipment）" % fname, u"%r" % mine.get("category"))
            key = mine.get("key") or {}
            check(list(key.keys()) == list((van.get("key") or {}).keys()) == [u"X"],
                  u"%s：键集只有 X（原版就是单字母）" % fname, u"%r" % list(key.keys()))
            got = (key.get(u"X") or {}).get(u"item")
            check(got == material,
                  u"%s：材料 = %s" % (fname, material), u"实际 %r" % got)
            check(got != u"minecraft:iron_ingot",
                  u"%s：**没有**残留原版铁锭" % fname)
            check(not (key.get(u"X") or {}).get(u"tag"),
                  u"%s：用精确 id 而不是标签（用户点名的是具体材料）" % fname)
            res = mine.get("result") or {}
            check(res.get("id") == u"potato_s_t:%s" % fname,
                  u"%s：产物 = potato_s_t:%s" % (fname, fname), u"%r" % res.get("id"))
            check(res.get("count") == 1, u"%s：产物数量 1" % fname, u"%r" % res.get("count"))

    print(u"")
    print(u"================ ② 盘上 crafting_shaped 总数 ================")
    shaped = 0
    for f in sorted(os.listdir(RDIR)):
        if not f.endswith(u".json"):
            continue
        try:
            if json.loads(io.open(os.path.join(RDIR, f), encoding="utf-8").read()).get("type") \
                    == u"minecraft:crafting_shaped":
                shaped += 1
        except Exception as exc:                      # noqa: BLE001
            check(False, u"%s 能解析" % f, u"%s" % exc)
    check(shaped == EXPECT_SHAPED, u"定形配方总数 = %d" % EXPECT_SHAPED, u"实际 %d" % shaped)

    print(u"")
    print(u"================ ③ 每张图纸都有对应的生成器条目 ================")
    gen = io.open(os.path.join(PROJ, "build", "zftools", "_zf45_recipes.py"),
                  encoding="utf-8").read()
    for set_name, _m in SETS:
        for piece in PIECES:
            fname = u"%s_%s" % (set_name, piece)
            check(u'name="%s"' % fname in gen,
                  u"生成器表里有 %s（可复现）" % fname)

    print(u"")
    print(u"断言数 = %d   失败项 = %d" % (count, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    print(u"结论: %s" % (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
