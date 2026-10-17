# -*- coding: utf-8 -*-
u"""_zf204_tungsten.py —— 加「钨锭」：物品注册 + 模型 + 贴图 + 五语种 + c:ingots 标签 + 合金炉配方。

用户原话：「加个钨锭 用合金冶炼炉炼制 配方 耐热金属+铁+金 +粗钨」

口径（用户没给的沿用本机规格，和 ①② 同一条口径）：
- 配方 = 3 个 NEED（`c:ingots/thermal_metal` / `c:ingots/iron` / `c:ingots/gold`，各 1）
        + 1 个 CONSUME（`potato_s_t:raw_tungsten` 1 个，合金炉正好 2 个消耗槽）
        → 1 个 `potato_s_t:tungsten_ingot`，时长/能耗 = 本机基准 30 秒 / 800 FE/t。
- ⚠ 「耐热金属」按本 MOD 的**热力金属锭**（`thermal_metal`）认：耐热金属块是结构方块，
  合金炉输入槽吃的是物品标签；要改成"消耗 1 块耐热金属块"只需把 Need 换成 Consume 一行。
- 已有的 `raw_tungsten`（粗钨）直接用 `PotatoSTOres.RAW_TUNGSTEN`。

跑法：python build\\zftools\\_zf204_tungsten.py [--write]
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

NEW = r"E:\PotatoST\PotatoSTneoforge1.21.1"
SRC = os.path.join(NEW, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(NEW, "src", "main", "resources")
LANG = os.path.join(RES, "assets", "potato_s_t", "lang")
ITEM_MODEL = os.path.join(RES, "assets", "potato_s_t", "models", "item", "tungsten_ingot.json")
TEX = os.path.join(RES, "assets", "potato_s_t", "textures", "item", "tungsten_ingot.png")
TEX_SRC = os.path.join(RES, "assets", "potato_s_t", "textures", "item", "titanium_ingot.png")
TAG = os.path.join(RES, "data", "c", "tags", "item", "ingots", "tungsten.json")
ZT = os.path.join(NEW, "build", "zftools")
GATES = [u"_zf186_verify.py", u"_zf188_verify.py", u"_zf190_verify.py", u"_zf192_verify.py",
         u"_zf194_verify.py", u"_zf196_verify.py", u"_zf202_repack.py"]

ZH = {u"zh_cn.json": u"钨锭", u"en_us.json": u"Tungsten Ingot", u"lzh.json": u"鎢錠",
      u"ja_jp.json": u"タングステンインゴット", u"ru_ru.json": u"Вольфрамовый слиток"}

VALUES = [u'  "values": [', u'    "potato_s_t:tungsten_ingot"', u'  ]', u'}']

RECIPE = u'''
        // ⑤ 1 耐热金属 + 1 铁锭 + 1 金锭，再消耗 1 粗钨 → 1 钨锭（0.16 ZF204，用户口述）
        //    用户原话：「加个钨锭 用合金冶炼炉炼制 配方 耐热金属+铁+金 +粗钨」
        //    ⚠ 用户没给时长/能耗 ⇒ 沿用本机规格（30 秒、800 FE/t），与 ①② 同一条口径。
        //    ⚠ 「耐热金属」按本 MOD 的**热力金属锭**（c:ingots/thermal_metal）认：耐热金属块是结构方块，
        //      而合金炉的输入槽吃的是物品标签（5 NEED / 2 CONSUME 槽，这里是 3 NEED + 1 CONSUME，正好）。
        //      要改成"消耗 1 块耐热金属块"只需把第一条 Need 换成
        //      `new Consume(ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get().asItem(), 1)` 并移到 consumes 里。
        list.add(new Smelt(
                List.of(new Need(ingot("thermal_metal"), 1),
                        new Need(ingot("iron"), 1),
                        new Need(ingot("gold"), 1)),
                List.of(new Consume(PotatoSTOres.RAW_TUNGSTEN.get().asItem(), 1)),
                new ItemStack(ModItems.TUNGSTEN_INGOT.get()),
                DURATION_TICKS, ENERGY_PER_PATCH));
'''.replace(u"ENERGY_PER_PATCH", u"ENERGY_PER_TICK")

ITEM_REG = u'''
    public static final DeferredItem<Item> TUNGSTEN_INGOT =
            ITEMS.register("tungsten_ingot", () -> new Item(new Item.Properties()));
'''


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def put(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def main(argv):
    write = u"--write" in argv
    fails = []

    # ① 物品注册
    p = os.path.join(SRC, "ModItems.java")
    t = read(p)
    if u'"tungsten_ingot"' not in t:
        anchor = u'    public static final DeferredItem<Item> URANIUM_INGOT ='
        if anchor not in t:
            fails.append(u"ModItems：URANIUM_INGOT 锚点找不到")
        else:
            t = t.replace(anchor, ITEM_REG.strip(u"\n") + u"\n\n" + anchor, 1)
            print(u"  ModItems：已插入 TUNGSTEN_INGOT")
            if write:
                put(p, t)
    else:
        print(u"  ModItems：已有 tungsten_ingot，跳过")

    # ② 创意标签
    t = read(p)
    m = re.search(u"(?m)^([ \t]*)output\\.accept\\(URANIUM_INGOT\\.get\\(\\)\\);", t)
    if not m:
        fails.append(u"ModItems：创意标签 output.accept(URANIUM_INGOT) 锚点找不到")
    elif u"output.accept(TUNGSTEN_INGOT.get());" not in t:
        t = t.replace(m.group(0), m.group(0) + u"\n" + m.group(1) + u"output.accept(TUNGSTEN_INGOT.get());", 1)
        print(u"  ModItems：创意标签已加")
        if write:
            put(p, t)
    else:
        print(u"  ModItems：创意标签已有，跳过")

    # ③ 合金炉配方
    p = os.path.join(SRC, "AlloySmelterRecipes.java")
    t = read(p)
    anchor = u"        table = List.copyOf(list);"
    if u'ingot("thermal_metal"), 1),\n                        new Need(ingot("iron"), 1)' in t:
        print(u"  AlloySmelterRecipes：钨锭配方已有，跳过")
    elif anchor not in t:
        fails.append(u"AlloySmelterRecipes：table 锚点找不到")
    else:
        t = t.replace(anchor, RECIPE.strip(u"\n") + u"\n\n" + anchor, 1)
        print(u"  AlloySmelterRecipes：已插入钨锭配方")
        if write:
            put(p, t)

    # ④ 模型 + 标签
    model = u'{\n  "parent": "minecraft:item/generated",\n  "textures": {\n    "layer0": "potato_s_t:item/tungsten_ingot"\n  }\n}\n'
    for path, text, label in ((ITEM_MODEL, model, u"物品模型"), (TAG, u"\n".join(VALUES) + u"\n", u"c:ingots/tungsten 标签")):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.isfile(path):
            print(u"  %s 已存在，跳过" % label)
        else:
            print(u"  %s 已写" % label)
            if write:
                put(path, text)

    # ⑤ 贴图：拿钛锭改色（钢蓝灰）
    if os.path.isfile(TEX):
        print(u"  贴图已存在，跳过")
    elif not os.path.isfile(TEX_SRC):
        fails.append(u"贴图源 titanium_ingot.png 不在")
    else:
        try:
            from PIL import Image
            im = Image.open(TEX_SRC).convert("RGBA")
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    r, g, b, a = px[x, y]
                    if a == 0:
                        continue
                    # 钢蓝灰：压一点红/绿、抬一点蓝，做出"钨"的冷色
                    px[x, y] = (int(r * 0.82), int(g * 0.86), min(255, int(b * 1.08)), a)
            if write:
                im.save(TEX)
            print(u"  贴图：%dx%d 改色生成" % (im.width, im.height))
        except Exception as e:  # noqa: BLE001
            fails.append(u"贴图生成失败：%s" % e)

    # ⑥ 五语种
    for fn, text in ZH.items():
        p = os.path.join(LANG, fn)
        t = read(p)
        key = u'"item.potato_s_t.tungsten_ingot"'
        if key in t:
            print(u"  %-12s 已有，跳过" % fn)
            continue
        m = re.search(u'(?m)^([ \t]*)"item\\.potato_s_t\\.titanium_ingot"\\s*:\\s*"[^"]*"\\s*,?\\s*$', t)
        if not m:
            fails.append(u"%s：titanium_ingot 锚点找不到" % fn)
            continue
        indent = m.group(1)
        line = m.group(0)
        newline = indent + key + u': "' + text + u'",'
        t = t.replace(line, line.rstrip(u",") + u",\n" + newline, 1)
        if not line.rstrip().endswith(u","):
            t = t.replace(newline + u"\n", newline + u"\n", 1)
        try:
            json.loads(t)
        except Exception as e:  # noqa: BLE001
            fails.append(u"%s：插入后 JSON 不合法（%s）" % (fn, e))
            continue
        print(u"  %-12s 已加 %s" % (fn, text))
        if write:
            put(p, t)

    # ⑦ 跟平常驻门的键数：698/700 → 699/701（多了一个 item 键）
    for fn in GATES:
        p = os.path.join(ZT, fn)
        if not os.path.isfile(p):
            continue
        t = read(p)
        out, n = [], 0
        for line in t.split(u"\n"):
            if any(k in line for k in (u"zh_cn", u"en_us", u"lzh", u"ja_jp", u"ru_ru", u"keys_jar",
                                       u"五语种", u"语言键", u"键数")):
                nl, k = re.subn(u"(?<![0-9a-zA-Z])(698|700)(?![0-9a-zA-Z])",
                                lambda mm: u"699" if mm.group(0) == u"698" else u"701", line)
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
