# -*- coding: utf-8 -*-
u"""_zf208_tungsten_pickaxe.py —— 加「钨镐」：档位 + 物品 + 模型贴图 + 五语种 + 两条配方 + 镐子标签。

用户原话：「做个钨镐 需要下界合金镐配合通用升级模板升级 三个钨锭两个铁棒也可以合成（原版镐合成样式）
8192耐久 金的挖掘速度 下界合金挖掘等级 12伤害」

落码口径（照 ModTiers 里已经写死的换算，不是拍脑袋）：
- 耐久 8192 ⇒ `build(8192, ...)` 的 uses；
- 挖掘速度"金的" ⇒ 12.0F（原版金镐 12.0）；
- 挖掘等级"下界合金" ⇒ 1.21 的等级就是标签 `BlockTags.INCORRECT_FOR_NETHERITE_TOOL`；
- 显示总伤害 12 ⇒ 档位加成取 10、注册时仍照原版镐那一行 `createAttributes(tier, 1.0F, -2.8F)`
  ⇒ 1 + 1 + 10 = 12（与 ModTiers 类注释里"显示伤害 = 1 + 参数 + 档位加成"的记账一致）；
- 升级：`smithing_transform`，template=`universal_upgrade_template`、base=`minecraft:netherite_pickaxe`、
  addition=`tungsten_ingot`（用户没点明"外加什么材料"，按现有振金那几条的写法用本材料的锭）；
- 合成：原版镐样式 `XXX / .Y. / .Y.`，X=`c:ingots/tungsten`、Y=`c:rods/iron`（3 钨锭 + 2 铁棒）。

跑法：python build\\zftools\\_zf208_tungsten_pickaxe.py [--write]
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NEW = r"E:\PotatoST\PotatoSTneoforge1.21.1"
SRC = os.path.join(NEW, "src", "main", "java", "com", "potatost", "mod")
RES = os.path.join(NEW, "src", "main", "resources")
LANG = os.path.join(RES, "assets", "potato_s_t", "lang")
TEX = os.path.join(RES, "assets", "potato_s_t", "textures", "item", "tungsten_pickaxe.png")
TEX_SRC = os.path.join(RES, "assets", "potato_s_t", "textures", "item", "titanium_alloy_pickaxe.png")
MODEL = os.path.join(RES, "assets", "potato_s_t", "models", "item", "tungsten_pickaxe.json")
REC_CRAFT = os.path.join(RES, "data", "potato_s_t", "recipe", "tungsten_pickaxe.json")
REC_SMITH = os.path.join(RES, "data", "potato_s_t", "recipe", "tungsten_pickaxe_smithing.json")
PICK_TAG = os.path.join(RES, "data", "minecraft", "tags", "item", "pickaxes.json")
ZT = os.path.join(NEW, "build", "zftools")
GATES = [u"_zf186_verify.py", u"_zf188_verify.py", u"_zf190_verify.py", u"_zf192_verify.py",
         u"_zf194_verify.py", u"_zf196_verify.py", u"_zf202_repack.py"]

ZH = {u"zh_cn.json": u"钨镐", u"en_us.json": u"Tungsten Pickaxe", u"lzh.json": u"鎢鎬",
      u"ja_jp.json": u"タングステンのツルハシ", u"ru_ru.json": u"Вольфрамовая кирка"}

TIER_CODE = u'''
    // ================= 钨镐（0.16 ZF208） =================
    // 用户原话：「做个钨镐 ... 8192耐久 金的挖掘速度 下界合金挖掘等级 12伤害」
    // 换算照本类里已写死的记账：显示总伤害 = 1 + createAttributes 的第一个参数 + 本档位加成
    // ⇒ 要 12 就把加成写 10、注册时沿用原版镐那一行（参数 1.0F）。
    /** 钨镐的挖掘速度：**金的 12.0F**（用户原话）。 */
    public static final float TUNGSTEN_PICKAXE_SPEED = 12.0F;
    /** 钨镐的档位加成：显示总伤害 = 1 + 1 + 10 = 12（用户给的 12）。 */
    public static final float TUNGSTEN_PICKAXE_DAMAGE = 10.0F;
    /** 钨镐档位：耐久 8192 / 速度 12 / 下界合金级标签 / 附魔权重 22（与下界合金同款）。 */
    public static final Tier TUNGSTEN_PICKAXE = build(8192, TUNGSTEN_PICKAXE_DAMAGE,
            TUNGSTEN_PICKAXE_SPEED, BlockTags.INCORRECT_FOR_NETHERITE_TOOL, 22);
'''

ITEM_CODE = u'''    /**
     * 钨镐（0.16 ZF208，用户原话见 {@link ModTiers#TUNGSTEN_PICKAXE}）。
     *
     * <p>属性照原版镐那一行：{@code 1 + 1 + 档位加成 10 = 12} 点显示总伤害；
     * 挖掘等级走档位里的下界合金标签、速度走金的 12.0。</p>
     */
    public static final DeferredItem<Item> TUNGSTEN_PICKAXE =
            ITEMS.register("tungsten_pickaxe",
                    () -> new PickaxeItem(ModTiers.TUNGSTEN_PICKAXE, new Item.Properties()
                            .attributes(PickaxeItem.createAttributes(ModTiers.TUNGSTEN_PICKAXE, 1.0F, -2.8F))));

'''

MODEL_JSON = u'{\n  "parent": "minecraft:item/handheld",\n  "textures": {\n    "layer0": "potato_s_t:item/tungsten_pickaxe"\n  }\n}\n'

CRAFT_JSON = u'''{
  "type": "minecraft:crafting_shaped",
  "category": "equipment",
  "pattern": [
    "XXX",
    " Y ",
    " Y "
  ],
  "key": {
    "X": {
      "tag": "c:ingots/tungsten"
    },
    "Y": {
      "tag": "c:rods/iron"
    }
  },
  "result": {
    "id": "potato_s_t:tungsten_pickaxe",
    "count": 1
  }
}
'''

SMITH_JSON = u'''{
  "type": "minecraft:smithing_transform",
  "addition": {
    "item": "potato_s_t:tungsten_ingot"
  },
  "base": {
    "item": "minecraft:netherite_pickaxe"
  },
  "result": {
    "count": 1,
    "id": "potato_s_t:tungsten_pickaxe"
  },
  "template": {
    "item": "potato_s_t:universal_upgrade_template"
  }
}
'''


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def put(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline=u"").write(t)


def main(argv):
    write = u"--write" in argv
    fails = []

    # ① 档位
    p = os.path.join(SRC, "ModTiers.java")
    t = read(p)
    if u"TUNGSTEN_PICKAXE =" in t:
        print(u"  ModTiers：已有钨镐档位，跳过")
    else:
        anchor = (u"    public static final Tier STAR_STEEL_AXE = build(1192, STAR_STEEL_DAMAGE, STAR_STEEL_SPEED,\n"
                  u"            BlockTags.INCORRECT_FOR_DIAMOND_TOOL, 22);")
        if anchor not in t:
            fails.append(u"ModTiers：STAR_STEEL_AXE 锚点找不到")
        else:
            t = t.replace(anchor, anchor + u"\n" + TIER_CODE.rstrip(u"\n"), 1)
            print(u"  ModTiers：已加钨镐档位")
            if write:
                put(p, t)

    # ② 物品 + 创意标签
    p = os.path.join(SRC, "ModItems.java")
    t = read(p)
    if u'"tungsten_pickaxe"' not in t:
        anchor = u"    public static final DeferredItem<Item> TITANIUM_ALLOY_PICKAXE ="
        if anchor not in t:
            fails.append(u"ModItems：TITANIUM_ALLOY_PICKAXE 锚点找不到")
        else:
            t = t.replace(anchor, ITEM_CODE + anchor, 1)
            print(u"  ModItems：已加钨镐物品")
            if write:
                put(p, t)
    else:
        print(u"  ModItems：已有钨镐，跳过")
    t = read(p)
    m = re.search(u"(?m)^([ \t]*)output\\.accept\\(IRON_ROD\\.get\\(\\)\\);", t)
    if not m:
        m = re.search(u"(?m)^([ \t]*)output\\.accept\\(TUNGSTEN_INGOT\\.get\\(\\)\\);", t)
    if not m:
        fails.append(u"ModItems：创意标签锚点找不到")
    elif u"output.accept(TUNGSTEN_PICKAXE.get());" not in t:
        t = t.replace(m.group(0), m.group(0) + u"\n" + m.group(1) + u"output.accept(TUNGSTEN_PICKAXE.get());", 1)
        print(u"  ModItems：创意标签已加")
        if write:
            put(p, t)

    # ③ 模型 + 两条配方
    for path, text, label in ((MODEL, MODEL_JSON, u"物品模型"),
                              (REC_CRAFT, CRAFT_JSON, u"合成配方（3 钨锭 + 2 铁棒）"),
                              (REC_SMITH, SMITH_JSON, u"升级配方（下界合金镐 + 通用升级模板）")):
        if os.path.isfile(path):
            print(u"  %s 已存在，跳过" % label)
            continue
        print(u"  %s 已写" % label)
        if write:
            put(path, text)

    # ④ 镐子标签
    t = read(PICK_TAG)
    if u"potato_s_t:tungsten_pickaxe" in t:
        print(u"  pickaxes 标签已有，跳过")
    else:
        t2 = t.replace(u'"potato_s_t:star_steel_pickaxe"',
                       u'"potato_s_t:star_steel_pickaxe",\n    "potato_s_t:tungsten_pickaxe"', 1)
        if t2 == t:
            fails.append(u"pickaxes 标签锚点找不到")
        else:
            json.loads(t2)
            print(u"  pickaxes 标签已加")
            if write:
                put(PICK_TAG, t2)

    # ⑤ 贴图：钛合金镐改色（钢蓝灰；材质 文件夹里没有钨镐原图）
    if os.path.isfile(TEX):
        print(u"  贴图已存在，跳过")
    elif not os.path.isfile(TEX_SRC):
        fails.append(u"贴图源 titanium_alloy_pickaxe.png 不在")
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
                    px[x, y] = (int(r * 0.82), int(g * 0.86), min(255, int(b * 1.08)), a)
            if write:
                im.save(TEX)
            print(u"  贴图：%dx%d 改色生成（材质 里没有钨镐原图）" % (im.width, im.height))
        except Exception as e:  # noqa: BLE001
            fails.append(u"贴图生成失败：%s" % e)

    # ⑥ 五语种
    for fn, text in ZH.items():
        p = os.path.join(LANG, fn)
        t = read(p)
        key = u'"item.potato_s_t.tungsten_pickaxe"'
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

    # ⑦ 键数跟平：700/702 → 701/703
    for fn in GATES:
        p = os.path.join(ZT, fn)
        if not os.path.isfile(p):
            continue
        t = read(p)
        out, n = [], 0
        for line in t.split(u"\n"):
            if any(k in line for k in (u"zh_cn", u"en_us", u"lzh", u"ja_jp", u"ru_ru", u"keys_jar",
                                       u"五语种", u"语言键", u"键数")):
                nl, k = re.subn(u"(?<![0-9a-zA-Z])(700|702)(?![0-9a-zA-Z])",
                                lambda mm: u"701" if mm.group(0) == u"700" else u"703", line)
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
