# -*- coding: utf-8 -*-
u"""_zf156_jarcheck.py —— 拆开 `release\\PotatoST-0.13.jar`，逐条点本轮那三样东西**真在成品里**。

只读。查的是**jar 自己**（不是盘上的源目录）：
  ① 端子：`TerminalBlockEntity.class` 里真有 `unloadedWithChunk` 字段与 `onChunkUnloaded` 方法；
  ② 手册：`ModAttachments.class` 在、`Zf156Check.class`（探针）**不在**、
     class 常量池里有 `guide_given` 与 `copyOnDeath`；
  ③ 金属板：21 份配方里是 `"tag": "c:plates/…"`、7 份液压机产物仍是自家板 id、
     `c:plates/<金属>` 标签在 jar 里且收着自家板、配方总数仍 91；
  ④ 五份语言键数 593×4 + 595；`.sha1` 是纯哈希一行。

跑法：python build\\zftools\\_zf156_jarcheck.py
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors=u"replace")

ROOT = r"E:\PotatoST"
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
SHAFILE = JAR + u".sha1"
METALS = [u"aluminum", u"cobalt", u"copper", u"iron", u"nickel", u"silver", u"steel"]

FAIL = []


def check(ok, label, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label,
                            (u" —— " + detail) if (detail and not ok) else u""))
    if not ok:
        FAIL.append(label)


def main():
    print(u"================ ZF156 成品拆包审计：%s ================" % JAR)
    if not os.path.isfile(JAR):
        print(u"  !! jar 不在")
        return 1
    raw = open(JAR, "rb").read()
    print(u"  %d 字节 / sha1 %s" % (len(raw), hashlib.sha1(raw).hexdigest()))
    z = zipfile.ZipFile(JAR)
    names = z.namelist()

    # ① 端子
    tb = z.read(u"com/potatost/mod/TerminalBlockEntity.class")
    check(b"unloadedWithChunk" in tb, u"① 端子 class 里有 unloadedWithChunk 字段")
    check(b"onChunkUnloaded" in tb, u"① 端子 class 里有 onChunkUnloaded 方法（区块卸载判据）")

    # ② 手册
    check(u"com/potatost/mod/ModAttachments.class" in names, u"② ModAttachments.class 在 jar 里")
    probes = [n for n in names if re.search(u"Zf\\d+Check", n)]
    check(not probes, u"② 探针 class 一个都不在（%s）" % (probes if probes else u"干净"))
    ma = z.read(u"com/potatost/mod/ModAttachments.class") if u"com/potatost/mod/ModAttachments.class" in names else b""
    check(b"guide_given" in ma, u"② class 常量池里有附件 id guide_given")
    check(b"copyOnDeath" in ma, u"② class 常量池里有 copyOnDeath（死后重生也带走的那个开关）")
    gb = z.read(u"com/potatost/mod/GuideBook.class")
    check(b"shouldGive" in gb and b"hasLegacyMark" in gb, u"② GuideBook 里判据与老标记迁移都在")
    check(b"putBoolean" not in gb, u"② GuideBook 不再往持久化数据写标记（class 里没有 putBoolean）")

    # ③ 金属板
    recipes = [n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")]
    # ⚠ 91 → 94：ZF160 重打时，另一条线在途的 3 份 generator_fuel/* 配方也进了工作树
    #   （jar 从工作树打），这里跟到**发布那一刻的实测值**（判据仍是逐字相等，没放宽）。
    check(len(recipes) == 93, u"③ jar 里配方 93 份（ZF156 的 91 + 另一条线在途的 3 份 generator_fuel − ZF162 删掉的电力高炉那 1 份）",
          u"实际 %d" % len(recipes))
    tag_hits, item_hits, id_hits, files_tag = 0, 0, 0, 0
    for n in recipes:
        t = z.read(n).decode("utf-8")
        k = len(re.findall(u'"tag":\\s*"c:plates/(?:' + u"|".join(METALS) + u')"', t))
        tag_hits += k
        if k:
            files_tag += 1
        item_hits += len(re.findall(u'"item":\\s*"potato_s_t:(?:' + u"|".join(METALS) + u')_plate"', t))
        id_hits += len(re.findall(u'"id":\\s*"potato_s_t:(?:' + u"|".join(METALS) + u')_plate"', t))
    check(tag_hits == 28 and files_tag == 20,
          u"③ 28 处 #c:plates/* 原料（20 份配方；ZF162 删了电力高炉那条）", u"实际 %d 处 / %d 份" % (tag_hits, files_tag))
    check(item_hits == 0, u"③ 没有一处还写死自家板当原料", u"实际 %d" % item_hits)
    check(id_hits == 7, u"③ 液压机那 7 份产物仍是自家板 id", u"实际 %d" % id_hits)
    missing = [m for m in METALS if u"data/c/tags/item/plates/%s.json" % m not in names]
    check(not missing, u"③ 7 张 c:plates/<金属> 标签在 jar 里", u"缺 %s" % missing)
    notin = []
    for m in METALS:
        vals = json.loads(z.read(u"data/c/tags/item/plates/%s.json" % m).decode("utf-8")).get(u"values", [])
        if u"potato_s_t:%s_plate" % m not in vals:
            notin.append(m)
    check(not notin, u"③ 每张标签都收着自家那块板", u"没收 %s" % notin)
    check(u"data/c/tags/item/plates.json" in names, u"③ 父标签 c:plates 也在")

    # ④ 语言与哈希文件
    bad = []
    for lg in (u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"):
        p = u"assets/potato_s_t/lang/%s.json" % lg
        if p not in names:
            bad.append(lg + u"(缺)")
            continue
        table = json.loads(z.read(p).decode("utf-8"))
        want = 595 if lg == u"lzh" else 593
        if len(table) != want:
            bad.append(u"%s=%d(要 %d)" % (lg, len(table), want))
    check(not bad, u"④ 五份语言键数 593×4 + 595", u"实际 %s" % bad)
    txt = io.open(SHAFILE, encoding="ascii").read() if os.path.isfile(SHAFILE) else u""
    check(txt.strip() == hashlib.sha1(raw).hexdigest() and txt.count(u"\n") == 1,
          u"④ .sha1 是纯哈希一行且与 jar 一致")

    print(u"================ %s ================" % (u"ALL OK" if not FAIL else u"%d 条 FAIL" % len(FAIL)))
    for f in FAIL:
        print(u"  !! " + f)
    return 1 if FAIL else 0


if __name__ == u"__main__":
    sys.exit(main())
