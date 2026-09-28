# -*- coding: utf-8 -*-
u"""_zf155_falsify.py —— ZF155 反证刀（静态，**不开游戏**）：改一处 ⇒ 指定那一项必须变红 ⇒ 还原必须回绿。

刀的口径照 ZF151/ZF153：多行锚点一律用 `\\n` 写，脚本按文件自带换行翻译再匹配
（这棵树换行不统一）；`count=0` 表示"全部替换"。

跑法：python build\\zftools\\_zf155_falsify.py
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
ZT = os.path.join(ROOT, "build", "zftools")
V = os.path.join(ZT, u"_zf155_verify.py")
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "potatost", "mod")
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "potato_s_t")
RECIPE = os.path.join(ROOT, "src", "main", "resources", "data", "potato_s_t", "recipe")
DOC = os.path.join(ROOT, "docs", "开发档案.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

MODITEMS = os.path.join(JAVA, u"ModItems.java")
ENGINE = os.path.join(JAVA, u"UniversalUpgradeTemplate.java")
MODEL = os.path.join(ASSETS, "models", "item", "universal_upgrade_template.json")
TEX = os.path.join(ASSETS, "textures", "item", "universal_upgrade_template.png")
TEX_OTHER = os.path.join(ASSETS, "textures", "item", "guide_book.png")
LANG_ZH = os.path.join(ASSETS, "lang", "zh_cn.json")
LANG_EN = os.path.join(ASSETS, "lang", "en_us.json")
R_RING = os.path.join(RECIPE, u"universal_upgrade_template.json")
R_SWORD = os.path.join(RECIPE, u"vibranium_sword_smithing.json")
R_HELMET = os.path.join(RECIPE, u"vibranium_helmet_smithing.json")
R_BOOTS = os.path.join(RECIPE, u"vibranium_boots_smithing.json")

# (刀名, 文件, 改前, 改后, 期望变红的那一项里的标记, 替换次数 0=全部)
KNIVES = [
    (u"K1 创造栏那一行换成别的物品", MODITEMS,
     u"output.accept(UNIVERSAL_UPGRADE_TEMPLATE.get());",
     u"output.accept(VIBRANIUM_INGOT.get());", u"A2 创造栏里有它", 1),
    (u"K2 模型 layer0 指错贴图", MODEL,
     u'"layer0": "potato_s_t:item/universal_upgrade_template"',
     u'"layer0": "potato_s_t:item/nonexistent"', u"A3 物品模型", 1),
    (u"K3 贴图被换成另一张 16x16（规格过、哈希不过）", TEX,
     u"@@binary@@", u"@@other-texture@@", u"A4b 贴图哈希与字节数钉死", 1),
    (u"K4 改一个**旧**键的值（不该动的动了）", LANG_ZH,
     u'"item.potato_s_t.vibranium_ingot": "振金锭"',
     u'"item.potato_s_t.vibranium_ingot": "振金锭改坏了"', u"B7 打包方案对照备份", 1),
    (u"K5 英文那把 .rule 键抽掉", LANG_EN,
     u'  "item.potato_s_t.universal_upgrade_template.rule": "Armour trims will not take it',
     u'  "item.potato_s_t.universal_upgrade_template.ruleX": "Armour trims will not take it',
     u"B1 en_us 七个新键齐全", 1),
    (u"K6 获取方式的中心换成铝锭（= 不要下界合金模板）", R_RING,
     u'    "N": {\n      "item": "minecraft:netherite_upgrade_smithing_template"\n    }',
     u'    "N": {\n      "item": "potato_s_t:aluminum_ingot"\n    }', u"C1 获取方式", 1),
    (u"K7 振金剑的底物换成钛合金镐", R_SWORD,
     u'"item": "potato_s_t:titanium_alloy_sword"',
     u'"item": "potato_s_t:titanium_alloy_pickaxe"', u"C2 振金剑", 1),
    (u"K8 振金头盔的模板改回下界合金模板", R_HELMET,
     u'"item": "potato_s_t:universal_upgrade_template"',
     u'"item": "minecraft:netherite_upgrade_smithing_template"', u"C3 四件振金护甲", 1),
    (u"K9 振金靴子夹带私货（附加物也改了）", R_BOOTS,
     u'"addition": {\n    "item": "potato_s_t:vibranium_ingot"\n  }',
     u'"addition": {\n    "item": "potato_s_t:raw_vibranium"\n  }', u"C4 四份配方除 template 一项外", 1),
    (u"K10 换表的官方口子被换掉", ENGINE,
     u"manager.replaceRecipes(byId.values());", u"manager.getRecipes();",
     u"D3 用 NeoForge 的官方口子", 1),
    (u"K11 偷偷上反射", ENGINE,
     u"        Plan plan = plan(current, server.registryAccess());",
     u"        try {\n"
     u"            java.lang.reflect.Field f = RecipeManager.class.getDeclaredField(\"byType\");\n"
     u"            f.setAccessible(true);\n"
     u"        } catch (Throwable t) {\n"
     u"        }\n"
     u"        Plan plan = plan(current, server.registryAccess());", u"D4 全程零反射", 1),
    (u"K12 加宽时不再并上原模板", ENGINE,
     u"CompoundIngredient.of(candidate.template(), universalIngredient)",
     u"Ingredient.of(universalItem)", u"D5 加宽 = 原模板", 1),
    (u"K13 纹饰跳过码改名（日志契约与文档脱钩）", ENGINE,
     u"trim-pattern-bound", u"trim-pattern-X", u"D6 冲突判据", 0),
    (u"K14 事件注解的 modid 抽掉", ENGINE,
     u"@EventBusSubscriber(modid = PotatoST.MODID)", u"@EventBusSubscriber", u"D1 引擎挂在模组事件总线", 1),
    (u"K15 /reload 挂点的参数名被改（挂点还是不是那个事件）", ENGINE,
     u"OnDatapackSyncEvent event", u"OnDatapackSyncEvent ev", u"D2 两个挂点", 1),
    (u"K16 档案 §5 的 ZF155 行标记改掉", DOC,
     u"| ZF155 |", u"| ZF155x |", u"E3 档案 §5 有 ZF155 行", 1),
    (u"K17 公告里 ZF155 那一条标题删掉", ANN,
     u"## New in 0.12 ZF155", u"## (deleted)", u"E5 英文公告有 ZF155 那一条", 1),
]
# K18 的锚点在运行期按"本轮 §4 号"算出来（见 main）
fails, rows = [], []


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def run_verify():
    r = subprocess.run([sys.executable, V], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    return r.returncode, r.stdout.decode(u"utf-8", "replace")


def apply_knife(path, old, new, count):
    if old == u"@@binary@@":
        shutil.copy2(TEX_OTHER, path)
        return True
    text = io.open(path, encoding=u"utf-8", newline=u"").read()
    eol = u"\r\n" if u"\r\n" in text else u"\n"
    old_e, new_e = old.replace(u"\n", eol), new.replace(u"\n", eol)
    hits = text.count(old_e)
    if hits == 0 or (count == 1 and hits != 1):
        return False
    io.open(path, u"w", encoding=u"utf-8", newline=u"").write(
        text.replace(old_e, new_e) if count == 0 else text.replace(old_e, new_e, count))
    return True


def main():
    # K18：把本轮 §4 小节的编号改成一个已经用过的号 ⇒ E1/E2 必须红
    doc = io.open(DOC, encoding=u"utf-8").read() if os.path.isfile(DOC) else u""
    m = None
    for mm in re.finditer(r"### (4\.\d+) [^\n]*ZF155", doc):
        m = mm
    knives = list(KNIVES)
    if m:
        knives.append((u"K18 本轮 §4 号改成已有号（撞号）", DOC,
                       u"### " + m.group(1) + u" ", u"### 4.1 ", u"E2 本轮 §4 号", 1))
    else:
        fails.append(u"K18 找不到带 ZF155 的 §4 小节标题（文档还没写？）")

    for label, path, old, new, marker, count in knives:
        original = open(path, "rb").read()
        h0 = hashlib.sha1(original).hexdigest()
        if not apply_knife(path, old, new, count):
            fails.append(u"%s：改前串命中数不对" % label)
            open(path, "wb").write(original)
            continue
        rc, out = run_verify()
        hit = any(marker in l and u"[FAIL]" in l for l in out.split(u"\n"))
        red = (rc != 0) and hit
        open(path, "wb").write(original)
        restored = sha(path) == h0
        rc2, _ = run_verify()
        green = rc2 == 0
        rows.append((label, red, restored, green))
        if not red:
            fails.append(u"%s：改坏后**没红**（rc=%d，命中=%s）" % (label, rc, hit))
        if not restored:
            fails.append(u"%s：还原后不是逐字节相同" % label)
        if not green:
            fails.append(u"%s：还原后没回绿" % label)

    print(u"================ ZF155 反证刀（静态 %d 把） ================" % len(knives))
    print(u"%-56s %-6s %-10s %-6s" % (u"刀", u"变红", u"逐字节还原", u"回绿"))
    for label, a, b, c in rows:
        print(u"%-56s %-6s %-10s %-6s" % (label[:54], u"OK" if a else u"!!",
                                          u"OK" if b else u"!!", u"OK" if c else u"!!"))
    ok = len([r for r in rows if r[1] and r[2] and r[3]])
    print(u"")
    print(u"刀数 = %d   全中 = %d   失败 = %d" % (len(knives), ok, len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
