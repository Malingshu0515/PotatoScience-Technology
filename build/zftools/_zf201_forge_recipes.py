# -*- coding: utf-8 -*-
"""_zf201_forge_recipes.py —— 0.16 ZF201 **Forge 1.20.1 侧**的 7 张钢配方

源工程（NeoForge 1.21.1）那边这 7 条走的是 `_zf45_recipes.py` 那张总表 + `--write`。
**Forge 1.20.1 工程没有那套 Python 工具链**（它的 tools/ 全是 JS 移植脚本），
所以这一份是"同一张表、换一处落盘格式"的最小版本：

  · 图纸逐格照抄原版铁套那七张（与源工程同一张表，本轮从 client.jar 现抠）；
  · 材料 `minecraft:iron_ingot` → `potato_s_t:steel_plate`（钢板）；
  · **1.20.1 的产物字段是 `"item"`**，1.21 才是 `"id"` —— 这是两侧 JSON 唯一的差异，
    所以生成器里不能照抄源工程那份 JSON 文本（本轮实测：直接抄过去游戏里全变成"空配方"）。

跑法：
    python build/zftools/_zf201_forge_recipes.py            # 只体检
    python build/zftools/_zf201_forge_recipes.py --write
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NEOSRC = r"E:\PotatoST\PotatoSTneoforge1.21.1"
FORGE = r"E:\PotatoST\PotatoSTforge1.20.1"
OUT = os.path.join(FORGE, "src", "main", "resources", "data", "potato_s_t", "recipes")
JAVA = os.path.join(FORGE, "src", "main", "java", "com", "potatost", "mod")

MATERIAL = u"potato_s_t:steel_plate"
STICK = u"minecraft:stick"

# 与源工程 `_zf45_recipes.py` 的 ZF201 那七条逐字段相同（唯二差别：产物字段名、文件名后缀无）
RECIPES = [
    (u"steel_helmet", [u"XXX", u"X X"], {u"X": MATERIAL}),
    (u"steel_chestplate", [u"X X", u"XXX", u"XXX"], {u"X": MATERIAL}),
    (u"steel_leggings", [u"XXX", u"X X", u"X X"], {u"X": MATERIAL}),
    (u"steel_boots", [u"X X", u"X X"], {u"X": MATERIAL}),
    (u"steel_pickaxe", [u"XXX", u" # ", u" # "], {u"X": MATERIAL, u"#": STICK}),
    (u"steel_sword", [u"X", u"X", u"#"], {u"X": MATERIAL, u"#": STICK}),
    (u"steel_axe", [u"XX", u"X#", u" #"], {u"X": MATERIAL, u"#": STICK}),
]

fails = []


def registered_ids():
    u"""Forge 工程里真正注册过的物品 id（grep 所有含 register 的调用 + 三个工厂方法）。"""
    ids = set()
    for fn in sorted(os.listdir(JAVA)):
        if not fn.endswith(u".java"):
            continue
        src = io.open(os.path.join(JAVA, fn), encoding="utf-8").read()
        for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*"([a-z0-9_]+)"', src):
            if u"register" in m.group(1).lower() or m.group(1) in (u"ore", u"raw", u"rawBlock"):
                ids.add(m.group(2))
    return ids


def build(name, pattern, keymap):
    return {
        "type": u"minecraft:crafting_shaped",
        "category": u"equipment",
        "pattern": pattern,
        "key": {ch: {"item": item} for ch, item in keymap.items()},
        "result": {"item": u"potato_s_t:%s" % name, "count": 1},
    }


def main(argv):
    write = u"--write" in argv
    ids = registered_ids()
    print(u"Forge 工程里扫到 %d 个已注册 id" % len(ids))
    if not os.path.isdir(OUT):
        fails.append(u"配方目录不存在：%s" % OUT)
        print(u"  [FAIL] %s" % fails[-1])
        return 1

    for name, pattern, keymap in RECIPES:
        rid = u"steel_" + name[len(u"steel_"):]
        if u"steel_" + name[6:] != name:
            pass
        # ① 产物与材料都得真的注册过
        for item in list(keymap.values()) + [u"potato_s_t:%s" % name]:
            if item.startswith(u"potato_s_t:"):
                short = item.split(u":", 1)[1]
                if short not in ids and short != u"steel_plate":
                    fails.append(u"%s：本模组没有注册 %s" % (name, item))
            elif item == STICK:
                pass
        # ② 形状：每格字符都在 key 里、key 无冗余
        chars = set(u"".join(pattern)) - {u" "}
        if chars != set(keymap):
            fails.append(u"%s：图纸用到的字符 %s 与 key %s 不一致"
                         % (name, sorted(chars), sorted(keymap)))
        widths = set(len(r) for r in pattern)
        if len(widths) != 1 or not (1 <= widths.pop() <= 3):
            fails.append(u"%s：行列宽不一致或超 3：%s" % (name, pattern))
        # ③ 产物必须在盘上真的能被合成出来（id 存在性已查）
        doc = build(name, pattern, keymap)
        path = os.path.join(OUT, u"%s.json" % name)
        text = json.dumps(doc, ensure_ascii=False, indent=2) + u"\n"
        if os.path.exists(path):
            fails.append(u"%s：盘上已经有同名文件（不该覆盖）" % path)
            continue
        if write:
            io.open(path, "w", encoding="utf-8", newline=u"\n").write(text)
            back = json.loads(io.open(path, encoding="utf-8").read())
            if back != doc:
                fails.append(u"%s：写出来的内容与预期不一致" % path)
        print(u"  [%s] %-16s %s  %s" % (u"写出" if write else u"将写", name, pattern,
                                        u"材料 " + MATERIAL))

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
