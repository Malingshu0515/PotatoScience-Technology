# -*- coding: utf-8 -*-
"""_zf201_verify.py —— 0.16 ZF201 钢套 / 钢制工具的常驻校验（**两个工程都查**）

用户原话：「做钢的全套盔甲 钢镐 钢剑 钢斧 全部套用铁套就可以 耐久多200-300 你自己决定
然后每件+0.1击退抗性 +1盔甲韧性 盔甲穿身上的材质先用下界合金凑合 贴图在工作区的 材质 文件夹里」。

这一轮真正要钉住的是**七条"用户说了"和三条"用户没说但不说清就做错"的口径**：

  ① 七件都在：钢头盔 / 钢胸甲 / 钢护腿 / 钢靴子 / 钢镐 / 钢剑 / 钢斧（各有贴图、模型、五语言名、配方）；
  ② **套用铁套**：护甲值 2/6/5/2、附魔权重 14、装备音效铁、工具伤害/攻速/挖掘等级全部照铁；
  ③ **耐久多 250**（用户给 200~300，本轮取正中）：盔甲 415/490/475/445、工具 500；
  ④ **每件 +1 盔甲韧性**（材料级 toughness 1.0）与 **+0.1 击退抗性**（材料级 0.1）；
  ⑤ **穿身上的材质用下界合金**：图层名 `minecraft:netherite`（背包图标另算，用用户给的钢贴图）；
  ⑥ 配方**逐格照抄原版铁那七张**，只把材料换成钢板 —— 形状错一格就是"摆上去做不出来"；
  ⑦ 两个工程（NeoForge 1.21.1 / Forge 1.20.1）的**配方内容必须一致**（只有产物字段名 item/id 不同）。

取证口：
  · 编译产物 —— `build/classes/.../ModItems.class` 等的常量池（证明"真的编进去了"）；
  · `javap -constants` —— 数字常量（耐久 / 速度 / 伤害加成 / 附魔权重）；
  · 源码结构 —— "那一行写的是哪个标签 / 哪个图层 / 哪个数字"，只有读源码才判得了；
  · `client.jar` 里的原版铁配方 —— 逐格对照（不靠记忆）。

跑法：
    $env:PYTHONIOENCODING='utf-8'
    python build/zftools/_zf201_verify.py       # 退出码 0 = 全过
"""
import io
import json
import os
import re
import subprocess
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NEO = r"E:\PotatoST\PotatoSTneoforge1.21.1"
FORGE = r"E:\PotatoST\PotatoSTforge1.20.1"
VANILLA_JAR = r"E:\gradle-home\caches\minecraft\versions\1.21.1\client.jar"

# 用户给的数（照原话抄）+ 本轮拍板的换算
ARMOR_DURABILITY = {u"helmet": 415, u"chestplate": 490, u"leggings": 475, u"boots": 445}
TOOL_USES = 500
ARMOR_POINTS = [2, 6, 5, 2]          # 铁套的护甲值（头/胸/腿/靴）
TOUGHNESS = u"1.0F"                  # 每件 +1 韧性
KNOCKBACK = u"0.1F"                  # 每件 +0.1 击退抗性
ENCHANT = 14                         # 铁套的附魔权重
LAYER = u"netherite"                 # 「穿身上的材质先用下界合金凑合」
MATERIAL = u"potato_s_t:steel_plate"  # 配方/修理材料（本轮与用户确认）
ARMOR_IDS = [u"helmet", u"chestplate", u"leggings", u"boots"]
TOOL_IDS = [u"pickaxe", u"sword", u"axe"]
ALL_IDS = [u"steel_" + x for x in ARMOR_IDS + TOOL_IDS]

# 原版铁那七张（本轮从 client.jar 现抠；1.20.1 的原版配方与 1.21.1 逐格相同）
VANILLA = [u"iron_helmet", u"iron_chestplate", u"iron_leggings", u"iron_boots",
           u"iron_pickaxe", u"iron_sword", u"iron_axe"]

fails = []
count = 0


def check(ok, label, detail=u""):
    global count
    count += 1
    print(u"  [%s] %s%s" % (u"OK" if ok else u"FAIL", label,
                            (u"   " + detail) if (detail and not ok) else (u"   " + detail if detail else u"")))
    if not ok:
        fails.append(label)
    return ok


def read(p):
    return io.open(p, encoding="utf-8").read()


def javap_constants(proj, cls, classpath):
    p = subprocess.run(["javap", "-p", "-constants", "-classpath", classpath,
                        "com.potatost.mod.%s" % cls],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace")
    d = {}
    for line in out.split(u"\n"):
        m = re.search(r"static final (?:int|float|double|long|java\.lang\.String) (\w+) = (.+);", line)
        if m:
            d[m.group(1)] = m.group(2).strip()
    return d, out


def class_strings(path):
    u"""从 .class 的常量池里捞出所有可见字符串（够判"这个 id 真的编进去了"）。"""
    if not os.path.isfile(path):
        return None
    raw = io.open(path, "rb").read()
    # 粗暴但够用：把可打印 ASCII 段切出来
    return set(m.group(0).decode("ascii") for m in re.finditer(rb"[ -~]{4,}", raw))


def vanilla_patterns():
    out = {}
    with zipfile.ZipFile(VANILLA_JAR) as z:
        for name in VANILLA:
            d = json.loads(z.read("data/minecraft/recipe/%s.json" % name).decode("utf-8"))
            out[name] = (d.get("pattern"), {k: v.get("item") for k, v in d.get("key", {}).items()})
    return out


def main():
    print(u"================ ① 原版铁那七张（对照基准） ================")
    vp = vanilla_patterns()
    for name in VANILLA:
        pat, key = vp[name]
        check(pat is not None and set(key.values()) - {u"minecraft:stick"} == {u"minecraft:iron_ingot"},
              u"%s：%s，材料只有铁锭" % (name, pat))

    for proj in (NEO, FORGE):
        tag = os.path.basename(proj)
        print(u"")
        print(u"=================== %s ===================" % tag)
        java = os.path.join(proj, "src", "main", "java", "com", "potatost", "mod")
        res = os.path.join(proj, "src", "main", "resources")
        classes = os.path.join(proj, "build", "classes", "java", "main")
        recipe_dir = os.path.join(res, "data", "potato_s_t",
                                  u"recipe" if proj == NEO else u"recipes")
        src_items = read(os.path.join(java, "ModItems.java"))
        src_armor = read(os.path.join(java, "ModArmorItems.java"))
        src_mats = read(os.path.join(java, "ModArmorMaterials.java"))
        src_tiers = read(os.path.join(java, "ModTiers.java"))

        # ---------- ② 七件都注册了（源码 + 编译产物双查） ----------
        print(u"\n---- ② 七件都注册了 ----")
        cls_items = class_strings(os.path.join(classes, "com", "potatost", "mod", "ModItems.class"))
        cls_armor = class_strings(os.path.join(classes, "com", "potatost", "mod",
                                               "ModArmorItems.class"))
        if check(cls_items is not None and cls_armor is not None,
                 u"两个注册类的 .class 都在（说明编译过）"):
            for rid in TOOL_IDS:
                check(u"steel_" + rid in cls_items, u"ModItems 编译产物里有 steel_%s" % rid)
            for rid in ARMOR_IDS:
                check(u"steel_" + rid in cls_armor, u"ModArmorItems 编译产物里有 steel_%s" % rid)
                check(u"registerSteel(\"steel_%s\"" % rid in src_armor,
                      u"源码里用 registerSteel 注册了 steel_%s（走原版 ArmorItem，没有多余子类）" % rid)
            for rid in TOOL_IDS:
                check(u'ITEMS.register("steel_%s"' % rid in src_items,
                      u"源码里注册了 steel_%s" % rid)

        # ---------- ③ 创造页 ----------
        print(u"\n---- ③ 创造模式物品栏里有它们 ----")
        for rid in ALL_IDS:
            holder = (u"ModArmorItems." + rid.replace(u"steel_", u"STEEL_").upper()) \
                if rid in [u"steel_" + x for x in ARMOR_IDS] else rid.upper()
            check(u"output.accept(%s.get())" % holder in src_items,
                  u"创造页 output.accept(%s)" % holder)

        # ---------- ④ 套用铁套：护甲值 / 附魔权重 / 音效 / 图层 / 韧性 / 击退 ----------
        print(u"\n---- ④ 套用铁套 + 用户点的三个数 ----")
        check(u'registerBorrowingLayer("steel", STEEL_ENCHANTMENT_VALUE, %s, %s' % (TOUGHNESS, KNOCKBACK)
              in src_mats, u"材料：韧性 %s、击退抗性 %s（每件各一份）" % (TOUGHNESS, KNOCKBACK))
        check(u"STEEL_ENCHANTMENT_VALUE = %d;" % ENCHANT in src_mats,
              u"附魔权重 = %d（铁同款）" % ENCHANT)
        check(u"SoundEvents.ARMOR_EQUIP_IRON" in src_mats.split(u"public static final ArmorMaterial STEEL")[-1][:600]
              or u"SoundEvents.ARMOR_EQUIP_IRON" in src_mats.split(u"public static final DeferredHolder<ArmorMaterial, ArmorMaterial> STEEL")[-1][:600],
              u"装备音效用的是铁的")
        check(LAYER in src_mats.split(u"STEEL =")[-1][:700],
              u"穿身上的图层 = %s（用户：先用下界合金凑合）" % LAYER)
        defense_line = u"%d, %d, %d, %d," % tuple(ARMOR_POINTS)
        check(defense_line in src_mats.split(u"STEEL =")[-1][:900],
              u"护甲值 %s（铁同款）" % (u"/".join(str(x) for x in ARMOR_POINTS),))
        check(u"() -> Ingredient.of(ModItems.STEEL_PLATE.get())" in src_mats,
              u"修理材料 = 钢板（与配方材料一致）")

        # ---------- ⑤ 耐久 ----------
        print(u"\n---- ⑤ 耐久（铁 + 250） ----")
        for rid in ARMOR_IDS:
            want = ARMOR_DURABILITY[rid]
            check(u'registerSteel("steel_%s", ArmorItem.Type.%s, %d)' % (rid, rid.upper(), want)
                  in src_armor, u"钢%s 耐久 %d（铁 + 250）" % (rid, want))
        check(u"STEEL_USES = %d;" % TOOL_USES in src_tiers, u"钢工具耐久 = %d（铁 250 + 250）" % TOOL_USES)

        print(u"\n---- ⑥ 三把工具各一档（第二轮：斧=金速度/铁等级，镐=钻石等级/铁速度） ----")
        cst, _raw = javap_constants(proj, "ModTiers", classes)
        check(cst.get(u"STEEL_USES") == str(TOOL_USES), u"javap：STEEL_USES = %s" % cst.get(u"STEEL_USES"))
        check(cst.get(u"STEEL_ENCHANTMENT_VALUE") == str(ENCHANT),
              u"javap：STEEL_ENCHANTMENT_VALUE = %s" % cst.get(u"STEEL_ENCHANTMENT_VALUE"))
        check(cst.get(u"STEEL_SPEED", u"").rstrip(u"fF") == u"6.0",
              u"javap：STEEL_SPEED = %s（铁 6.0，钢镐 / 钢剑用）" % cst.get(u"STEEL_SPEED"))
        check(cst.get(u"STEEL_AXE_SPEED", u"").rstrip(u"fF") == u"12.0",
              u"javap：STEEL_AXE_SPEED = %s（金的 12.0，钢斧用）" % cst.get(u"STEEL_AXE_SPEED"))
        check(cst.get(u"STEEL_DAMAGE_BONUS", u"").rstrip(u"fF") == u"2.0",
              u"javap：STEEL_DAMAGE_BONUS = %s（铁 2.0，三把共用的伤害加成）" % cst.get(u"STEEL_DAMAGE_BONUS"))
        # 三个档位对象在不在（它们不是编译期常量，javap -constants 看不到 ⇒ 读源码字段）
        for tier in (u"STEEL_SWORD", u"STEEL_AXE", u"STEEL_PICKAXE"):
            check(u"public static final Tier %s = build(" % tier in src_tiers,
                  u"ModTiers 里有一档 %s" % tier)
        if proj == NEO:
            check(u"STEEL_SWORD = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_SPEED,\n"
                  u"            BlockTags.INCORRECT_FOR_IRON_TOOL" in src_tiers,
                  u"钢剑：铁速度 + 铁等级（用户第二轮没提剑，保持第一轮口径）")
            check(u"STEEL_AXE = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_AXE_SPEED,\n"
                  u"            BlockTags.INCORRECT_FOR_IRON_TOOL" in src_tiers,
                  u"钢斧：**金速度 12.0** + **铁等级**")
            check(u"STEEL_PICKAXE = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_SPEED,\n"
                  u"            BlockTags.INCORRECT_FOR_DIAMOND_TOOL" in src_tiers,
                  u"钢镐：**铁速度 6.0** + **钻石等级**")
        else:
            check(u"LEVEL_IRON = 2;" in src_tiers, u"1.20.1 的 int 刻度：铁 = 2")
            check(u"STEEL_SWORD = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_SPEED,\n"
                  u"            LEVEL_IRON" in src_tiers,
                  u"钢剑：铁速度 + 铁等级（LEVEL_IRON）")
            check(u"STEEL_AXE = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_AXE_SPEED,\n"
                  u"            LEVEL_IRON" in src_tiers,
                  u"钢斧：金速度 12.0 + 铁等级（LEVEL_IRON）")
            check(u"STEEL_PICKAXE = build(STEEL_USES, STEEL_DAMAGE_BONUS, STEEL_SPEED,\n"
                  u"            LEVEL_DIAMOND" in src_tiers,
                  u"钢镐：铁速度 + 钻石等级（LEVEL_DIAMOND = 3）")
        # 物品真的用了对应那一档
        check(u"new SteelSwordItem(ModTiers.STEEL_SWORD" in src_items, u"钢剑用 STEEL_SWORD 档")
        check(u"new PickaxeItem(ModTiers.STEEL_PICKAXE" in src_items, u"钢镐用 STEEL_PICKAXE 档")
        check(u"new AxeItem(ModTiers.STEEL_AXE" in src_items, u"钢斧用 STEEL_AXE 档")

        # ---------- ⑥b 钢剑自带附魔 ----------
        print(u"\n---- ⑥b 钢剑做出来自带锋利 II + 横扫之刃 III ----")
        sword_src = read(os.path.join(java, "SteelSwordItem.java"))
        sword_cls = class_strings(os.path.join(classes, "com", "potatost", "mod",
                                              "SteelSwordItem.class"))
        check(sword_cls is not None, u"SteelSwordItem.class 编出来了")
        check(sword_cls is not None and u"SHARPNESS" in sword_cls and u"SWEEPING_EDGE" in sword_cls,
              u"常量池里同时有 SHARPNESS 与 SWEEPING_EDGE（引用了这两个附魔）")
        cst_s, raw_s = javap_constants(proj, "SteelSwordItem", classes)
        check(cst_s.get(u"SHARPNESS_LEVEL") == u"2",
              u"javap：SHARPNESS_LEVEL = %s（用户要的 II）" % cst_s.get(u"SHARPNESS_LEVEL"))
        check(cst_s.get(u"SWEEPING_EDGE_LEVEL") == u"3",
              u"javap：SWEEPING_EDGE_LEVEL = %s（用户要的 III）" % cst_s.get(u"SWEEPING_EDGE_LEVEL"))
        check(u"public void onCraftedBy(ItemStack stack, Level level, Player player)" in sword_src,
              u"覆写的是 onCraftedBy（工作台交成品时触发；创造拿的不带）")
        check(u"super.onCraftedBy(stack, level, player);" in sword_src,
              u"先调 super（不吞掉父类行为）")
        check(u"if (level.isClientSide)" in sword_src, u"只在服务端加（避免客户端本地预测出假物品）")
        if proj == NEO:
            check(u"registryOrThrow(Registries.ENCHANTMENT)" in sword_src
                  and u"getHolderOrThrow(key)" in sword_src,
                  u"1.21：从注册表取 Holder 再 enchant（不在静态期取，§4.1）")
        else:
            check(u"stack.enchant(Enchantments.SHARPNESS, SHARPNESS_LEVEL);" in sword_src,
                  u"1.20.1：Enchantments.SHARPNESS 直接是 Enchantment，enchant 一步到位")

        # ---------- ⑦ 贴图与模型 ----------
        print(u"\n---- ⑦ 贴图 与 模型 ----")
        tex_dir = os.path.join(res, "assets", "potato_s_t", "textures", "item")
        mod_dir = os.path.join(res, "assets", "potato_s_t", "models", "item")
        for rid in ALL_IDS:
            png = os.path.join(tex_dir, rid + u".png")
            ok = os.path.isfile(png)
            size = None
            if ok:
                head = io.open(png, "rb").read(24)
                import struct
                size = struct.unpack(">II", head[16:24])
                ok = size == (16, 16)
            check(ok, u"%s.png 存在且 16×16" % rid, u"实际 %s" % (size,))
            mp = os.path.join(mod_dir, rid + u".json")
            parent = u"minecraft:item/handheld" if rid in [u"steel_" + x for x in TOOL_IDS] \
                else u"minecraft:item/generated"
            ok = os.path.isfile(mp) and json.loads(read(mp)).get("parent") == parent
            check(ok, u"%s.json 父级 = %s" % (rid, parent))

        # ---------- ⑧ 配方：逐格对照原版铁 ----------
        print(u"\n---- ⑧ 配方（照抄原版铁，材料换钢板） ----")
        for i, rid in enumerate(ALL_IDS):
            vname = VANILLA[i]
            vpat, vkey = vp[vname]
            path = os.path.join(recipe_dir, rid + u".json")
            if not check(os.path.isfile(path), u"%s.json 在盘上" % rid):
                continue
            doc = json.loads(read(path))
            check(doc.get("type") == u"minecraft:crafting_shaped", u"%s：type = crafting_shaped" % rid)
            check(doc.get("category") == u"equipment", u"%s：category = equipment" % rid)
            # 形状逐格
            check(doc.get("pattern") == vpat, u"%s：pattern 与原版 %s 逐格相同（%s）"
                  % (rid, vname, vpat))
            # key：字符集合同、材料换成钢板、木棍仍是木棍
            key = {k: v.get("item") for k, v in doc.get("key", {}).items()}
            check(set(key) == set(vkey), u"%s：key 的字符集合与原版相同 %s" % (rid, sorted(vkey)))
            for ch, item in key.items():
                if item == u"minecraft:stick":
                    check(vkey.get(ch) == u"minecraft:stick", u"%s：%r 仍是木棍" % (rid, ch))
                else:
                    check(item == MATERIAL, u"%s：%r 材料 = %s" % (rid, ch, MATERIAL))
            # 产物 + 数量
            result = doc.get("result", {})
            got = result.get("item") or result.get("id")
            check(got == u"potato_s_t:%s" % rid, u"%s：产物 = %s" % (rid, got))
            check(result.get("count") == 1, u"%s：数量 1" % rid)

        # ---------- ⑨ 五语言名 ----------
        print(u"\n---- ⑨ 五语言名 ----")
        for lang in (u"zh_cn.json", u"en_us.json", u"ja_jp.json", u"lzh.json", u"ru_ru.json"):
            path = os.path.join(res, "assets", "potato_s_t", "lang", lang)
            table = json.loads(read(path))
            miss = [rid for rid in ALL_IDS if not table.get(u"item.potato_s_t.%s" % rid)]
            check(not miss, u"%s：七件名字齐全" % lang, u"缺 %s" % miss)

    # ---------- ⑩ 两个工程的配方必须一致（只有 item/id 字段名不同） ----------
    print(u"")
    print(u"================ ⑩ 两个工程的配方一致 ================")
    for rid in ALL_IDS:
        a = json.loads(read(os.path.join(NEO, "src", "main", "resources", "data", "potato_s_t",
                                         "recipe", rid + u".json")))
        b = json.loads(read(os.path.join(FORGE, "src", "main", "resources", "data", "potato_s_t",
                                         "recipes", rid + u".json")))
        norm_a = dict(a, result={"item": a["result"]["id"], "count": a["result"]["count"]})
        check(norm_a == b, u"%s：两侧配方逐字段相同" % rid)

    print(u"")
    print(u"==============================")
    print(u"断言数 = %d   失败项 = %d" % (count, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    print(u"结论: %s" % (u"通过" if not fails else u"有失败项"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
