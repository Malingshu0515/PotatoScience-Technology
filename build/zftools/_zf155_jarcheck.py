# -*- coding: utf-8 -*-
u"""_zf155_jarcheck.py —— 拆开 `release\\PotatoST-0.13.jar`，逐条点本轮那 7 样东西在不在。"""
import hashlib
import io
import json
import os
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"E:\PotatoST"
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
RES = os.path.join(ROOT, "src", "main", "resources")

WANT = [
    u"com/potatost/mod/UniversalUpgradeTemplate.class",
    u"assets/potato_s_t/models/item/universal_upgrade_template.json",
    u"assets/potato_s_t/textures/item/universal_upgrade_template.png",
    u"data/potato_s_t/recipe/universal_upgrade_template.json",
    u"data/potato_s_t/recipe/vibranium_sword_smithing.json",
]
LANGS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]

fails = []


def main():
    raw = open(JAR, "rb").read()
    print(u"成品：%s" % JAR)
    print(u"  %d 字节 / sha1 %s" % (len(raw), hashlib.sha1(raw).hexdigest()))
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    for w in WANT:
        ok = w in names
        print(u"  [%s] %s" % (u"OK" if ok else u"!!", w))
        if not ok:
            fails.append(w)

    # 贴图与源逐字节相同
    tex = u"assets/potato_s_t/textures/item/universal_upgrade_template.png"
    src = os.path.join(RES, u"assets", u"potato_s_t", u"textures", u"item",
                       u"universal_upgrade_template.png")
    same = z.read(tex) == open(src, "rb").read()
    print(u"  [%s] 贴图与源逐字节相同" % (u"OK" if same else u"!!"))
    if not same:
        fails.append(u"贴图不一致")

    # 五份语言：7 个键齐全 + 键数
    keys = [u"item.potato_s_t.universal_upgrade_template",
            u"item.potato_s_t.universal_upgrade_template.desc",
            u"item.potato_s_t.universal_upgrade_template.applies_to",
            u"item.potato_s_t.universal_upgrade_template.ingredients",
            u"item.potato_s_t.universal_upgrade_template.base_slot",
            u"item.potato_s_t.universal_upgrade_template.additions_slot",
            u"item.potato_s_t.universal_upgrade_template.rule"]
    for lg in LANGS:
        entry = u"assets/potato_s_t/lang/%s.json" % lg
        table = json.loads(z.read(entry).decode(u"utf-8"))
        miss = [k for k in keys if k not in table]
        exp = 596 if lg == u"lzh" else 594
        ok = not miss and len(table) == exp
        print(u"  [%s] %-6s %d 键（期望 %d）缺 %s" % (u"OK" if ok else u"!!", lg, len(table), exp,
                                                     miss if miss else u"无"))
        if not ok:
            fails.append(u"%s 语言" % lg)

    # 两条配方真的指到通用模板
    ring = json.loads(z.read(u"data/potato_s_t/recipe/universal_upgrade_template.json").decode(u"utf-8"))
    sword = json.loads(z.read(u"data/potato_s_t/recipe/vibranium_sword_smithing.json").decode(u"utf-8"))
    ok = (ring.get(u"key", {}).get(u"N", {}).get(u"item") == u"minecraft:netherite_upgrade_smithing_template"
          and ring.get(u"result", {}).get(u"id") == u"potato_s_t:universal_upgrade_template"
          and sword.get(u"template", {}).get(u"item") == u"potato_s_t:universal_upgrade_template"
          and sword.get(u"base", {}).get(u"item") == u"potato_s_t:titanium_alloy_sword"
          and sword.get(u"result", {}).get(u"id") == u"potato_s_t:vibranium_sword")
    print(u"  [%s] jar 里那两条配方内容对（八铝锭围模板 / 钛合金剑升振金剑）" % (u"OK" if ok else u"!!"))
    if not ok:
        fails.append(u"配方内容")

    # 四条护甲配方都换了模板
    swapped = 0
    for piece in (u"helmet", u"chestplate", u"leggings", u"boots"):
        o = json.loads(z.read(u"data/potato_s_t/recipe/vibranium_%s_smithing.json" % piece)
                       .decode(u"utf-8"))
        if o.get(u"template", {}).get(u"item") == u"potato_s_t:universal_upgrade_template":
            swapped += 1
    print(u"  [%s] jar 里 4 件振金护甲的模板都换过了（%d/4）" % (u"OK" if swapped == 4 else u"!!", swapped))
    if swapped != 4:
        fails.append(u"护甲模板")

    print(u"\n判词：%s（失败 %d 项）" % (u"ALL OK" if not fails else u"**有失败**", len(fails)))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
