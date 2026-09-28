# -*- coding: utf-8 -*-
u"""_zf155_assets.py —— ZF155：通用升级模板的物品资产 + 五语文案 + 配方改造。

产出的东西：
  ① `assets/potato_s_t/textures/item/universal_upgrade_template.png`（16x16 / 8 位 RGBA，脚本画）
  ② `assets/potato_s_t/models/item/universal_upgrade_template.json`（item/generated）
  ③ `data/potato_s_t/recipe/universal_upgrade_template.json`
     用户指定获取方式：「下界合金升级模板 围一圈铝锭」⇒ 3x3 八块铝锭围一圈 + 中间一张下界合金升级模板
  ④ `data/potato_s_t/recipe/vibranium_sword_smithing.json`
     用户指定：「给振金剑加个配方 钛合金剑用这个和振金升级」⇒ 钛合金剑 + 振金锭 + 通用升级模板
  ⑤ 4 件振金护甲的 smithing 配方：模板由 `minecraft:netherite_upgrade_smithing_template`
     换成 `potato_s_t:universal_upgrade_template`（用户「之前所有的振金装备下界合金模板也改成这个」）
  ⑥ 五份 lang 各加 **7 个键**（物品名 / 升级 / 适用于 / 原料 / 底物槽 / 材料槽 / 规则）

铁律（§4.53 同族）：**只加键、不动旧键**，脚本自带旧键值逐条断言；文件已存在且内容不同时打印改前改后字节数留痕。
跑法：python build\\zftools\\_zf155_assets.py
"""
import io
import json
import os
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJ = r"E:\PotatoST"
ASSETS = os.path.join(PROJ, "src", "main", "resources", "assets", "potato_s_t")
DATA = os.path.join(PROJ, "src", "main", "resources", "data", "potato_s_t")
LANG = os.path.join(ASSETS, "lang")
LANGS = ["zh_cn", "en_us", "ja_jp", "ru_ru", "lzh"]
RECIPE = os.path.join(DATA, "recipe")

FAILS = []


# ------------------------------------------------------------------ 贴图
# 调色板：外框=下界合金那口深灰；面板=铝白；箭头=深色（升级是往上走的）
PALETTE = {
    u".": None,
    u"B": (74, 70, 80, 255),        # 深灰外框
    u"D": (186, 193, 202, 255),     # 铝白面板
    u"d": (158, 166, 176, 255),     # 面板阴影（上下内边）
    u"H": (52, 48, 58, 255),        # 箭头上半
    u"S": (68, 63, 75, 255),        # 箭杆（略浅一点，免得整块死黑）
}
PIXELS = [
    u"................",
    u"..BBBBBBBBBBBB..",
    u"..BddddddddddB..",
    u"..BDDDDHHDDDDB..",
    u"..BDDDHHHHDDDB..",
    u"..BDDHHHHHHDDB..",
    u"..BDHHHHHHHHDB..",
    u"..BDDDDSSDDDDB..",
    u"..BDDDDSSDDDDB..",
    u"..BDDDDSSDDDDB..",
    u"..BDDDDSSDDDDB..",
    u"..BDDDDSSDDDDB..",
    u"..BDDDDDDDDDDB..",
    u"..BddddddddddB..",
    u"..BBBBBBBBBBBB..",
    u"................",
]


def png_bytes():
    if len(PIXELS) != 16:
        FAILS.append(u"贴图必须 16 行")
    raw = b""
    for row in PIXELS:
        if len(row) != 16:
            FAILS.append(u"每行必须 16 像素：%r" % row)
        raw += b"\x00"
        for ch in row:
            px = PALETTE[ch]
            raw += b"\x00\x00\x00\x00" if px is None else bytes(px)

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


# ------------------------------------------------------------------ 文案
NAME = u"item.potato_s_t.universal_upgrade_template"
TEXT = {
    NAME: {
        "zh_cn": u"通用升级模板", "en_us": u"Universal Upgrade Template",
        "ja_jp": u"汎用アップグレードテンプレート",
        "ru_ru": u"Универсальный шаблон улучшения", "lzh": u"通用升級模板"},
    NAME + ".desc": {
        "zh_cn": u"通用升级", "en_us": u"Universal Upgrade",
        "ja_jp": u"汎用アップグレード", "ru_ru": u"Универсальное улучшение",
        "lzh": u"通用升級"},
    NAME + ".applies_to": {
        "zh_cn": u"一切要在锻造台模板槽里放东西的升级（原版下界合金、本模组振金、其他模组）",
        "en_us": u"Every upgrade that wants something in the smithing template slot (netherite, vibranium, other mods)",
        "ja_jp": u"鍛冶台のテンプレート枠に物を要するあらゆるアップグレード（ネザライト・ヴィブラニウム・他Mod）",
        "ru_ru": u"Любое улучшение, которому нужен предмет в слоте шаблона (незерит, вибраниум, другие моды)",
        "lzh": u"凡鍛造臺模板槽需物之升級（原版下界合金、本模組振金、他模組）"},
    NAME + ".ingredients": {
        "zh_cn": u"那套升级原本要的材料（下界合金锭 / 振金锭 / ……）",
        "en_us": u"Whatever that upgrade originally asked for (netherite ingot / vibranium ingot / ...)",
        "ja_jp": u"そのアップグレードが本来要求する材料（ネザライトインゴット／ヴィブラニウムインゴット／…）",
        "ru_ru": u"То, что это улучшение требовало раньше (слиток незерита / вибраниума / ...)",
        "lzh": u"該升級本需之料（下界合金錠 / 振金錠 / ……）"},
    NAME + ".base_slot": {
        "zh_cn": u"放要升级的装备", "en_us": u"Put the gear you want to upgrade",
        "ja_jp": u"アップグレードする装備を入れる",
        "ru_ru": u"Положите снаряжение для улучшения", "lzh": u"置所欲升級之器"},
    NAME + ".additions_slot": {
        "zh_cn": u"放那套升级原本要的材料",
        "en_us": u"Put whatever that upgrade originally asked for",
        "ja_jp": u"そのアップグレードが本来要求する材料を入れる",
        "ru_ru": u"Положите то, что улучшение требовало раньше",
        "lzh": u"置該升級本需之料"},
    NAME + ".rule": {
        "zh_cn": u"盔甲纹饰不吃它（图案与模板绑死）。两条升级若底物与材料完全相同，则两边都不认它 —— 这就是「有冲突就不许用」。",
        "en_us": u"Armour trims will not take it (a pattern is bound to one template item). If two upgrades share the exact same base and material, neither accepts it - conflicts are refused.",
        "ja_jp": u"防具の装飾には使えない（模様は特定のテンプレートと結び付いている）。二つのアップグレードが同じベースと材料を要求する場合、どちらもこれを受け付けない。",
        "ru_ru": u"Отделка брони его не примет (узор привязан к своему шаблону). Если два улучшения требуют одно и то же, ни одно из них его не примет.",
        "lzh": u"甲飾弗納此（紋樣與模板相繫）。二升級若底料俱同，則兩皆不納 —— 此即「有爭則弗用」。"},
}


# ------------------------------------------------------------------ 工具
def jdump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + u"\n"


def put(path, text, label=u""):
    rel = os.path.relpath(path, PROJ)
    old = None
    if os.path.exists(path):
        old = io.open(path, encoding=u"utf-8", newline=u"").read()
        if old == text:
            print(u"  [同] %s（内容一致，跳过）" % rel)
            return False
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    if old is None:
        print(u"  [新] %s（%d 字节）%s" % (rel, len(text.encode(u"utf-8")), label))
    else:
        print(u"  [改] %s（%d → %d 字节）%s"
              % (rel, len(old.encode(u"utf-8")), len(text.encode(u"utf-8")), label))
    return True


def sha1(b):
    import hashlib
    return hashlib.sha1(b).hexdigest()


# ------------------------------------------------------------------ 主流程
def main():
    # ① 贴图
    png_path = os.path.join(ASSETS, "textures", "item", "universal_upgrade_template.png")
    rel = os.path.relpath(png_path, PROJ)
    data = png_bytes()
    old = io.open(png_path, "rb").read() if os.path.exists(png_path) else None
    if old != data:
        d = os.path.dirname(png_path)
        if not os.path.isdir(d):
            os.makedirs(d)
        with open(png_path, "wb") as fh:
            fh.write(data)
        print(u"  [%s] %s（%d 字节 / sha1 %s）"
              % (u"新" if old is None else u"改", rel, len(data), sha1(data)))
    else:
        print(u"  [同] %s" % rel)

    # ② 模型
    put(os.path.join(ASSETS, "models", "item", "universal_upgrade_template.json"),
        jdump({"parent": "item/generated",
               "textures": {"layer0": "potato_s_t:item/universal_upgrade_template"}}))

    # ③ 获取方式：八铝锭围一圈 + 中间一张下界合金升级模板
    put(os.path.join(RECIPE, "universal_upgrade_template.json"), jdump({
        "type": "minecraft:crafting_shaped",
        "category": "misc",
        "pattern": ["AAA", "ANA", "AAA"],
        "key": {
            "A": {"item": "potato_s_t:aluminum_ingot"},
            "N": {"item": "minecraft:netherite_upgrade_smithing_template"},
        },
        "result": {"id": "potato_s_t:universal_upgrade_template", "count": 1},
    }))

    # ④ 振金剑：钛合金剑 + 振金锭 + 通用升级模板
    put(os.path.join(RECIPE, "vibranium_sword_smithing.json"), jdump({
        "type": "minecraft:smithing_transform",
        "addition": {"item": "potato_s_t:vibranium_ingot"},
        "base": {"item": "potato_s_t:titanium_alloy_sword"},
        "result": {"count": 1, "id": "potato_s_t:vibranium_sword"},
        "template": {"item": "potato_s_t:universal_upgrade_template"},
    }))

    # ⑤ 4 件振金护甲：模板换掉
    swapped = 0
    for piece in ("helmet", "chestplate", "leggings", "boots"):
        p = os.path.join(RECIPE, u"vibranium_%s_smithing.json" % piece)
        raw = io.open(p, encoding=u"utf-8").read()
        obj = json.loads(raw)
        data = obj.get("template", {})
        if data.get("item") == "minecraft:netherite_upgrade_smithing_template":
            data["item"] = "potato_s_t:universal_upgrade_template"
            obj["template"] = data
            put(p, jdump(obj), u"模板 → 通用升级模板")
            swapped += 1
        elif data.get("item") == "potato_s_t:universal_upgrade_template":
            print(u"  [同] %s（模板已是通用升级模板）" % os.path.relpath(p, PROJ))
        else:
            FAILS.append(u"%s 的模板槽不是预期值：%r" % (os.path.relpath(p, PROJ), data))
    if swapped not in (0, 4):
        FAILS.append(u"只换了 %d 件护甲（应为 4 或 0）" % swapped)

    # ⑥ 五语文案：锚在振金剑的名字后面追加，只加不改
    for lg in LANGS:
        p = os.path.join(LANG, lg + u".json")
        raw = io.open(p, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            FAILS.append(u"%s 有 BOM" % lg)
        if b"\r\n" in raw:
            FAILS.append(u"%s 是 CRLF（既有是 LF）" % lg)
        data = json.loads(raw.decode("utf-8"))
        before = len(data)
        anchor = u"item.potato_s_t.vibranium_sword"
        if anchor not in data:
            FAILS.append(u"%s 里找不到锚点 %s" % (lg, anchor))
            continue
        out, added = {}, []
        for k, v in data.items():
            out[k] = v
            if k == anchor:
                for key, table in TEXT.items():
                    if key in data:
                        continue
                    out[key] = table[lg]
                    added.append(key)
        io.open(p, "w", encoding="utf-8", newline="\n").write(
            json.dumps(out, indent=2, ensure_ascii=False) + "\n")
        back = json.loads(io.open(p, encoding="utf-8").read())
        kept = all(back[k] == v for k, v in data.items())
        ok = (len(back) == before + len(added) and len(added) == len(TEXT) and kept)
        print(u"  %s %-7s %d → %d 键（+%d）  旧键值全未动=%s"
              % (u"[OK]" if ok else u"[!!]", lg, before, len(back), len(added), kept))
        if not ok:
            FAILS.append(u"%s 写回校验失败" % lg)

    sets = {lg: set(json.loads(io.open(os.path.join(LANG, lg + u".json"),
                                       encoding="utf-8").read())) for lg in LANGS}
    base = sets["lzh"]
    for lg in LANGS:
        if lg == "zh_cn":
            continue
        diff = sets[lg] ^ sets["zh_cn"]
        if diff:
            print(u"  ⚠ %s 与 zh_cn 键集合差 %d：%s" % (lg, len(diff), sorted(diff)[:4]))
    print(u"  五份语言都有这 7 个键：%s"
          % all(all(k in sets[lg] for k in TEXT) for lg in LANGS))

    print(u"\n失败项 = %d" % len(FAILS))
    for f in FAILS:
        print(u"  !! " + f)
    return 1 if FAILS else 0


if __name__ == u"__main__":
    sys.exit(main())
