# -*- coding: utf-8 -*-
u"""_zf206_iron_rod.py —— 加「铁棒」：物品 + 模型 + 贴图（用 材质\\铁棒_2.png）+ 五语种 + 竖排 3 铁锭配方 + 标签。

用户原话：「再加一个铁棒 材质在文件夹 三个铁竖直摆放 合成6个铁棒（挂标签）」
  ⇒ 1x3 竖直摆放 3 个铁锭（走 `c:ingots/iron` 标签）→ 6 个铁棒；
  ⇒ 「挂标签」：物品挂进 `c:rods/iron`，并把 `#c:rods/iron` 挂进 `c:rods`。

跑法：python build\\zftools\\_zf206_iron_rod.py [--write]
"""
import io
import json
import os
import re
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

NEW = r"E:\PotatoST\PotatoSTneoforge1.21.1"
MAT = r"E:\PotatoST\材质\铁棒_2.png"
SRC = os.path.join(NEW, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(NEW, "src", "main", "resources")
LANG = os.path.join(RES, "assets", "potato_s_t", "lang")
TEX = os.path.join(RES, "assets", "potato_s_t", "textures", "item", "iron_rod.png")
MODEL = os.path.join(RES, "assets", "potato_s_t", "models", "item", "iron_rod.json")
RECIPE = os.path.join(RES, "data", "potato_s_t", "recipe", "iron_rod.json")
TAG1 = os.path.join(RES, "data", "c", "tags", "item", "rods", "iron.json")
TAG2 = os.path.join(RES, "data", "c", "tags", "item", "rods.json")
ZT = os.path.join(NEW, "build", "zftools")
GATES = [u"_zf186_verify.py", u"_zf188_verify.py", u"_zf190_verify.py", u"_zf192_verify.py",
         u"_zf194_verify.py", u"_zf196_verify.py", u"_zf202_repack.py"]

ZH = {u"zh_cn.json": u"铁棒", u"en_us.json": u"Iron Rod", u"lzh.json": u"鐵棒",
      u"ja_jp.json": u"鉄の棒", u"ru_ru.json": u"Железный стержень"}

ITEM_REG = u'''
    public static final DeferredItem<Item> IRON_ROD =
            ITEMS.register("iron_rod", () -> new Item(new Item.Properties()));
'''

MODEL_JSON = u'{\n  "parent": "minecraft:item/generated",\n  "textures": {\n    "layer0": "potato_s_t:item/iron_rod"\n  }\n}\n'

RECIPE_JSON = u'''{
  "type": "minecraft:crafting_shaped",
  "category": "misc",
  "pattern": [
    "X",
    "X",
    "X"
  ],
  "key": {
    "X": {
      "tag": "c:ingots/iron"
    }
  },
  "result": {
    "id": "potato_s_t:iron_rod",
    "count": 6
  }
}
'''

TAG1_JSON = u'{\n  "values": [\n    "potato_s_t:iron_rod"\n  ]\n}\n'
TAG2_JSON = u'{\n  "values": [\n    "#c:rods/iron"\n  ]\n}\n'


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def put(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def main(argv):
    write = u"--write" in argv
    fails = []

    # ① 物品注册
    p = os.path.join(SRC, "ModItems.java")
    t = read(p)
    if u'"iron_rod"' not in t:
        anchor = u'    public static final DeferredItem<Item> URANIUM_INGOT ='
        if anchor not in t:
            fails.append(u"ModItems：URANIUM_INGOT 锚点找不到")
        else:
            t = t.replace(anchor, ITEM_REG.strip(u"\n") + u"\n\n" + anchor, 1)
            print(u"  ModItems：已插入 IRON_ROD")
            if write:
                put(p, t)
    else:
        print(u"  ModItems：已有 iron_rod，跳过")

    # ② 创意标签
    t = read(p)
    m = re.search(u"(?m)^([ \t]*)output\\.accept\\(TUNGSTEN_INGOT\\.get\\(\\)\\);", t)
    if not m:
        m = re.search(u"(?m)^([ \t]*)output\\.accept\\(URANIUM_INGOT\\.get\\(\\)\\);", t)
    if not m:
        fails.append(u"ModItems：创意标签锚点找不到")
    elif u"output.accept(IRON_ROD.get());" not in t:
        t = t.replace(m.group(0), m.group(0) + u"\n" + m.group(1) + u"output.accept(IRON_ROD.get());", 1)
        print(u"  ModItems：创意标签已加")
        if write:
            put(p, t)
    else:
        print(u"  ModItems：创意标签已有，跳过")

    # ③ 模型 / 配方 / 两个标签
    for path, text, label in ((MODEL, MODEL_JSON, u"物品模型"),
                              (RECIPE, RECIPE_JSON, u"1x3 竖直铁锭→6 铁棒 配方"),
                              (TAG1, TAG1_JSON, u"c:rods/iron 标签"),
                              (TAG2, TAG2_JSON, u"c:rods 标签（挂 c:rods/iron）")):
        if os.path.isfile(path):
            print(u"  %s 已存在，跳过" % label)
            continue
        print(u"  %s 已写" % label)
        if write:
            put(path, text)

    # ④ 贴图（用户 材质 文件夹里的原图）
    if not os.path.isfile(MAT):
        fails.append(u"材质贴图不在：%s" % MAT)
    elif os.path.isfile(TEX):
        print(u"  贴图已存在，跳过")
    else:
        if write:
            os.makedirs(os.path.dirname(TEX), exist_ok=True)
            shutil.copy2(MAT, TEX)
        print(u"  贴图：已从 材质\\铁棒_2.png 拷入")

    # ⑤ 五语种
    for fn, text in ZH.items():
        p = os.path.join(LANG, fn)
        t = read(p)
        key = u'"item.potato_s_t.iron_rod"'
        if key in t:
            print(u"  %-12s 已有，跳过" % fn)
            continue
        m = re.search(u'(?m)^([ \t]*)"item\\.potato_s_t\\.titanium_ingot"\\s*:\\s*"[^"]*"\\s*,?\\s*$', t)
        if not m:
            fails.append(u"%s：titanium_ingot 锚点找不到" % fn)
            continue
        line = m.group(0)
        newline = m.group(1) + key + u': "' + text + u'",'
        t = t.replace(line, line.rstrip(u",") + u",\n" + newline, 1)
        try:
            json.loads(t)
        except Exception as e:  # noqa: BLE001
            fails.append(u"%s：插入后 JSON 不合法（%s）" % (fn, e))
            continue
        print(u"  %-12s 已加 %s" % (fn, text))
        if write:
            put(p, t)

    # ⑥ 键数跟平：699/701 → 700/702
    for fn in GATES:
        p = os.path.join(ZT, fn)
        if not os.path.isfile(p):
            continue
        t = read(p)
        out, n = [], 0
        for line in t.split(u"\n"):
            if any(k in line for k in (u"zh_cn", u"en_us", u"lzh", u"ja_jp", u"ru_ru", u"keys_jar",
                                       u"五语种", u"语言键", u"键数")):
                nl, k = re.subn(u"(?<![0-9a-zA-Z])(699|701)(?![0-9a-zA-Z])",
                                lambda mm: u"700" if mm.group(0) == u"699" else u"702", line)
                if k and nl != line:
                    line, n = nl, n + k
            out.append(line)
        if n:
            print(u"  %-22s 键数跟平 %d 处" % (fn, n))
            if write:
                put(p, u"\n".join(out))

    print(u"结果：%s；失败 %d" % (u"落盘" if write else u"干跑", len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
