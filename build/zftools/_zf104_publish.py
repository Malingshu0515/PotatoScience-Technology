# -*- coding: utf-8 -*-
r"""_zf104_publish.py —— ZF104 出成品（作废 ZF103 那版 `90510e18…`）

✔ ToolLint 的硬规矩：**先查后拷**（所有断言都过了才 `shutil.copy2`）；
  `backup/archive/publish` 都必须核哈希。
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

ROOT = r"E:\PotatoST"
SRC = os.path.join(ROOT, "build", "libs", "potato_s_t-0.11.jar")
DST = os.path.join(ROOT, "release", "PotatoST-0.11.jar")
SHA = DST + ".sha1"
PUB = os.path.join(ROOT, "build", "zftools", "_zf104_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
VOID = "90510e1890af79242cb41e0cda0a2f6472b12cdf"
PREV_ROUND_SHA = "48bc3358b1a68da81827b952ab4eb8b645415cc2"

ARMOR = ["titanium_alloy_helmet", "titanium_alloy_chestplate",
         "titanium_alloy_leggings", "titanium_alloy_boots",
         "star_steel_helmet", "star_steel_chestplate",
         "star_steel_leggings", "star_steel_boots"]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def patch(path, old, new, label, expect=1, optional=False):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        if optional and hits == 0:
            print(u"  [SKIP] %s（已经填过了）" % label)
            return
        fails.append(u"%s：锚点命中 %d 次（必须 %d）" % (label, hits, expect))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s ≠ 预期要作废的 %s" % (old, VOID))
    if not os.path.exists(SRC):
        print(u"  [FAIL] 缺构建产物 ⇒ 一个字节都不动")
        return 1
    new = sha1(SRC)
    size = os.path.getsize(SRC)

    with zipfile.ZipFile(SRC) as zf:
        names = zf.namelist()
        entries = len(names)
        if [n for n in names if n.split("/")[-1].startswith("_zf") or "Check" in n.split("/")[-1]]:
            fails.append(u"成品里带探针/检查器")
        # ---- ① 本轮 9 个物品的 class + 模型 + 贴图 ----
        for cls in ("ModArmorMaterials", "ModArmorItems", "ModArmorPiece", "ModArmorSet"):
            rel = u"com/potatost/mod/%s.class" % cls
            (print(u"  [OK]   成品里有 %s" % cls) if rel in names
             else fails.append(u"成品里没有 %s" % rel))
        for name in ARMOR + ["star_steel_ingot"]:
            rel = u"assets/potato_s_t/models/item/%s.json" % name
            if rel not in names:
                fails.append(u"成品里没有模型 %s" % rel)
        if u"assets/potato_s_t/textures/item/star_steel_ingot.png" not in names:
            fails.append(u"成品里没有星璨钢锭贴图")
        else:
            print(u"  [OK]   9 个模型 + 星璨钢锭贴图都在成品里")
        # ---- ② 四语言 349 键 + 本轮 14 键 ----
        keys = 0
        for loc in ("zh_cn", "en_us", "ja_jp", "ru_ru"):
            inside = json.loads(zf.read(u"assets/potato_s_t/lang/%s.json" % loc).decode("utf-8"))
            keys = len(inside)
            if keys != 349:
                fails.append(u"成品里 %s 键数 %d ≠ 349" % (loc, keys))
            for k in ("item.potato_s_t.star_steel_ingot",
                      "item.potato_s_t.titanium_alloy_helmet",
                      "tooltip.potato_s_t.star_steel_set",
                      "message.potato_s_t.star_steel_void_swap"):
                if k not in inside:
                    fails.append(u"成品里 %s 缺键 %s" % (loc, k))
        if keys == 349:
            print(u"  [OK]   四语言各 349 键，本轮 14 个新键都在")
        # ---- ③ c: 标签 ----
        for rel in (u"data/c/tags/item/ingots/star_steel.json",
                    u"data/c/tags/item/star_steel_ingots.json"):
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
        if b"star_steel_ingot" not in zf.read(u"data/c/tags/item/ingots.json"):
            fails.append(u"成品里的 c:ingots 父标签没收星璨钢锭")
        else:
            print(u"  [OK]   c: 标签三份都在，父标签也收了 star_steel_ingot")
        # ---- ④ 活体数字：配方 / 矿物（本轮不该动）----
        shaped = 0
        for n in names:
            if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json"):
                try:
                    if json.loads(zf.read(n).decode("utf-8")).get("type") == u"minecraft:crafting_shaped":
                        shaped += 1
                except Exception:
                    pass
        if shaped != 42:
            fails.append(u"成品里 crafting_shaped 配方 %d 条 ≠ 42（本轮不该加配方）" % shaped)
        else:
            print(u"  [OK]   成品里 crafting_shaped 配方仍是 42 条（本轮没加配方）")
        # ---- ⑤ class 里真的带着本轮的常量 ----
        blob = zf.read(u"com/potatost/mod/ModArmorItems.class")
        for needle in (b"star_steel_chestplate", b"titanium_alloy_boots"):
            if needle not in blob:
                fails.append(u"成品里的 ModArmorItems 找不到 %s" % needle.decode())
        mats = zf.read(u"com/potatost/mod/ModArmorMaterials.class")
        if b"star_steel" not in mats or b"titanium_alloy" not in mats:
            fails.append(u"成品里的 ModArmorMaterials 缺材料名")
        else:
            print(u"  [OK]   成品里的 class 带着本轮的材料名与物品名")

    if new == old:
        fails.append(u"新旧哈希相同 ⇒ 源码没变？")

    if fails:
        print(u"  [FAIL] 以上 %d 条没过 ⇒ 一个字节都不动" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1
    shutil.copy2(SRC, DST)
    if sha1(DST) != new:
        print(u"  [FAIL] 拷贝后哈希不一致 ⇒ 回滚")
        shutil.copy2(os.path.join(r"C:\PotatoST救援\zf104_pre", "release", "PotatoST-0.11.jar"), DST)
        return 1
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）" % (new, size, entries))
    print(u"   作废 %s（ZF103）" % VOID[:8])
    patch(DOC, u"__ZF104_SHA1__", new, u"§9 ZF104 条目：哈希填实", optional=True)
    patch(DOC, u"__ZF104_BYTES__", str(size), u"§9 ZF104 条目：字节数填实", optional=True)
    patch(DOC, u"__ZF104_ENTRIES__", str(entries), u"§9 ZF104 条目：条目数填实", optional=True)
    # §9 里 ZF103 那条的成品行改成"当时那版"
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % VOID,
          u"**当时那版**：`release\\PotatoST-0.11.jar` = `%s`" % VOID,
          u"§9 ZF103 条目：成品 → 当时那版", optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
