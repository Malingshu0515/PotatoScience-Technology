# -*- coding: utf-8 -*-
r"""_zf102_publish.py —— ZF102 出成品（作废 ZF101 那版 `d2966bd5…`）+ 把 §9 的占位填实"""
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
PUB = os.path.join(ROOT, "build", "zftools", "_zf102_publish.py")
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
RDIR = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
BEFORE = os.path.join(r"C:\PotatoST救援\zf102_pre", "recipe_before.txt")
VOID = "48bc3358b1a68da81827b952ab4eb8b645415cc2"
PREV_ROUND_SHA = "d2966bd57d27681a6577e95adca74a1814284cee"
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

    if os.path.exists(BEFORE):
        before = [l.strip() for l in read(BEFORE).splitlines() if l.strip()]
        now = sorted(n for n in os.listdir(RDIR) if n.endswith(".json"))
        eq_ok = sorted(before) == now
        if not eq_ok:
            fails.append(u"配方目录与改前不一致：%s" % sorted(set(now) ^ set(before)))
        else:
            print(u"  [OK]   配方仍是那 %d 份（本轮只改机器、不增配方）" % len(now))

    with zipfile.ZipFile(SRC) as zf:
        names = zf.namelist()
        entries = len(names)
        if [n for n in names if "Check" in n.split("/")[-1] and n.endswith(".class")]:
            fails.append(u"成品里带探针")
        for rel in (u"assets/potato_s_t/textures/block/hydrochloric_acid_still.png",
                    u"assets/potato_s_t/textures/block/hydrochloric_acid_flow.png",
                    u"data/c/tags/fluid/hydrochloric_acid.json",
                    u"com/potatost/mod/AcidicReactionChamberBlockEntity.class"):
            if rel not in names:
                fails.append(u"成品里没有 %s" % rel)
        if not fails:
            print(u"  [OK]   盐酸的两张贴图 / c: 标签 / 机器 class 全在成品里")
        inside = json.loads(zf.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8"))
        if len(inside) != 335:
            fails.append(u"成品里 zh_cn 键数 %d ≠ 335" % len(inside))
        else:
            print(u"  [OK]   成品里 zh_cn 是 335 键")
        shaped = 0
        for n in names:
            if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json"):
                try:
                    if json.loads(zf.read(n).decode("utf-8")).get("type") == u"minecraft:crafting_shaped":
                        shaped += 1
                except Exception:
                    pass
        if shaped != 42:
            fails.append(u"成品里 crafting_shaped 配方 %d 条 ≠ 42" % shaped)
        else:
            print(u"  [OK]   成品里 crafting_shaped 配方 = 42 条")
        if b"HYDROCHLORIC_ACID" not in zf.read(u"com/potatost/mod/ModFluids.class"):
            fails.append(u"成品里的 ModFluids 还是旧的（找不到 HYDROCHLORIC_ACID）")
        else:
            print(u"  [OK]   成品里的 ModFluids 带着本轮的 HYDROCHLORIC_ACID")
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
    print(u"   作废 %s（ZF101）" % VOID[:8])
    patch(DOC, u"__ZF102_SHA1__", new, u"§9 ZF102 条目：哈希填实", optional=True)
    patch(DOC, u"__ZF102_BYTES__", str(size), u"§9 ZF102 条目：字节数填实", optional=True)
    patch(DOC, u"__ZF102_ENTRIES__", str(entries), u"§9 ZF102 条目：条目数填实", optional=True)
    patch(DOC, u"**成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"**当时的成品**：`release\\PotatoST-0.11.jar` = `%s`" % PREV_ROUND_SHA,
          u"§9 ZF101 条目：成品 → 当时的成品", optional=True)
    patch(PUB, u'VOID = "%s"' % VOID, u'VOID = "%s"' % new, u"发布脚本 VOID 跟到最新")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
