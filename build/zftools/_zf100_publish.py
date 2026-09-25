# -*- coding: utf-8 -*-
r"""_zf100_publish.py —— ZF100 出成品（作废 ZF99 那版 `533749f3…`）+ 把 §9 的占位填实

照老规矩：**先核对旧哈希、再核对新产物内容，全过了才动文件**；
§4.59 ④ 的两条硬化照旧（重命名用独立的 `PREV_ROUND_SHA`；占位补丁幂等）。
本轮额外核：成品里 zh_cn 是 **315** 键、crafting_shaped = **41**、改前那 44 份配方一件不少、
以及本轮三件新东西**真的进了 jar**（三条配方 JSON / 燃烧反应室的 class / 二氧化碳的两张贴图）。
"""
import hashlib
import io
import json
import os
import re
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
PUB = os.path.join(ROOT, "build", "zftools", "_zf100_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
BEFORE = os.path.join(r"C:\PotatoST救援\zf100_pre", "recipe_before.txt")
VOID = "d47203540f4d8da703ee01a8764bdcf5de363f01"
PREV_ROUND_SHA = "533749f3053558f8f201fc397f1c72725f80a40d"
NEW_RECIPES = ("lithium_battery.json", "electric_blast_furnace.json", "combustion_chamber.json")
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def read(p):
    return io.open(p, encoding="utf-8").read() if os.path.exists(p) else u""


def patch(path, old, new, label, expect=1, optional=False):
    t = io.open(path, encoding="utf-8").read()
    hits = t.count(old)
    if hits != expect:
        if optional and hits == 0:
            print(u"  [SKIP] %s（锚点已不在 = 之前填过了，幂等放行）" % label)
            return
        fails.append(u"%s：锚点命中 %d 次（必须 %d 次）" % (label, hits, expect))
        return
    io.open(path, "w", encoding="utf-8", newline=u"\n").write(t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


def main():
    old = sha1(DST) if os.path.exists(DST) else u"(缺)"
    if old != VOID:
        fails.append(u"当前成品 %s ≠ 预期要作废的 %s" % (old, VOID))
    if not os.path.exists(SRC):
        fails.append(u"没有构建产物 %s" % SRC)
        print(u"  [FAIL] 缺构建产物 ⇒ 一个字节都不动")
        return 1
    new = sha1(SRC)
    size = os.path.getsize(SRC)

    if os.path.exists(BEFORE):
        before = [l.strip() for l in read(BEFORE).splitlines() if l.strip()]
        now = sorted(n for n in os.listdir(RDIR) if n.endswith(".json"))
        missing = [n for n in before if n not in now]
        if missing:
            fails.append(u"改前配方丢了：%s" % missing)
        else:
            print(u"  [OK]   改前那 %d 份配方一件不少（现共 %d 份）" % (len(before), len(now)))
        extra = sorted(set(now) - set(before))
        if extra != sorted(NEW_RECIPES):
            fails.append(u"新增配方不是预期的三份：%s" % extra)
        else:
            print(u"  [OK]   新增的正好是本轮那三份：%s" % u"、".join(NEW_RECIPES))

    with zipfile.ZipFile(SRC) as zf:
        names = zf.namelist()
        entries = len(names)
        bad = [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]
        if bad:
            fails.append(u"成品里带探针：%s" % bad)
        evil = [n for n in names
                if (n.startswith(u"assets/") or n.startswith(u"data/"))
                and not re.fullmatch(u"[a-z0-9/._-]+", n)]
        if evil:
            fails.append(u"成品里有非 ASCII 条目：%s" % evil)
        else:
            print(u"  [OK]   assets/ 与 data/ 的条目名全合法")
        for n in sorted(NEW_RECIPES):
            rel = u"data/potato_s_t/recipe/" + n
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
            else:
                print(u"  [OK]   成品里有 %s" % rel)
        for rel in (u"com/potatost/mod/CombustionChamberBlockEntity.class",
                    u"com/potatost/mod/CombustionChamberBlock.class",
                    u"com/potatost/mod/CombustionChamberMenu.class",
                    u"com/potatost/mod/client/CombustionChamberScreen.class",
                    u"com/potatost/mod/CombustionChamberBlockEntity$FuelProfile.class",
                    u"assets/potato_s_t/textures/block/carbon_dioxide_still.png",
                    u"assets/potato_s_t/textures/block/carbon_dioxide_flow.png",
                    u"assets/potato_s_t/textures/block/combustion_chamber_side.png",
                    u"data/c/tags/fluid/carbon_dioxide.json",
                    u"assets/potato_s_t/blockstates/combustion_chamber.json"):
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
        if not fails:
            print(u"  [OK]   燃烧反应室那一套（class / 贴图 / 标签 / blockstate）全在成品里")
        inside = json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        if len(inside) != 315:
            fails.append(u"成品里 zh_cn 键数 %d ≠ 315" % len(inside))
        else:
            print(u"  [OK]   成品里 zh_cn 是 315 键")
        shaped = 0
        for n in names:
            if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json"):
                try:
                    if json.loads(zf.read(n).decode("utf-8")).get("type") == u"minecraft:crafting_shaped":
                        shaped += 1
                except Exception:
                    pass
        if shaped != 41:
            fails.append(u"成品里 crafting_shaped 配方 %d 条 ≠ 41" % shaped)
        else:
            print(u"  [OK]   成品里 crafting_shaped 配方 = 41 条")
        # ★ 本轮的关键自证：class 常量池里必须有"二氧化碳"那条流体类型字段名
        raw = zf.read(u"com/potatost/mod/ModFluids.class")
        if b"CARBON_DIOXIDE" not in raw:
            fails.append(u"成品里的 ModFluids 还是旧的（找不到 CARBON_DIOXIDE）⇒ 忘了重新构建？")
        else:
            print(u"  [OK]   成品里的 ModFluids 带着本轮新加的 CARBON_DIOXIDE")
    if new == old:
        fails.append(u"新旧哈希相同 ⇒ 源码没变？")

    if fails:
        print(u"  [FAIL] 以上 %d 条没过 ⇒ 一个字节都不动" % len(fails))
        for f in fails:
            print(u"    !! " + f)
        return 1

    shutil.copy2(SRC, DST)
    io.open(SHA, "w", encoding="ascii", newline=u"\n").write(new + u"\n")
    print(u"① 已发布 release\\PotatoST-0.11.jar = %s（%d B / %d 条目）" % (new, size, entries))
    print(u"   作废 %s（ZF99）" % VOID[:8])

    patch(DOC, u"__ZF100_SHA1__", new, u"§9 ZF100 条目：成品哈希填实", optional=True)
    patch(DOC, u"__ZF100_BYTES__", str(size), u"§9 ZF100 条目：字节数填实", optional=True)
    patch(DOC, u"__ZF100_ENTRIES__", str(entries), u"§9 ZF100 条目：条目数填实", optional=True)
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"§9 ZF99 条目：成品 → 当时的成品", optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
