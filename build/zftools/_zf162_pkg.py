# -*- coding: utf-8 -*-
u"""_zf162_pkg.py —— ZF162 打包：把 `build\\libs` 那份拷成 `release\\PotatoST-0.13.jar` + `.sha1`，
并当场审计（class / 配方 / 语言键 / 探针残留 / CRC）。

跑法：python build\\zftools\\_zf162_pkg.py [--write]
"""
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
LIB = os.path.join(ROOT, "build", "libs", u"potato_s_t-0.13.jar")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")
SHA = JAR + u".sha1"
LANGS = [u"zh_cn", u"en_us", u"ja_jp", u"ru_ru", u"lzh"]


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main(argv):
    write = u"--write" in argv
    if not os.path.isfile(LIB):
        print(u"!! 构建产物不在：%s" % LIB)
        return 1
    old_sha = sha(JAR) if os.path.isfile(JAR) else u"(无)"
    print(u"旧成品：%s  %d B" % (old_sha[:16], os.path.getsize(JAR) if os.path.isfile(JAR) else 0))
    print(u"新构建：%s  %d B" % (sha(LIB)[:16], os.path.getsize(LIB)))
    if not write:
        print(u"（没加 --write，只算不写）")
        return 0
    shutil.copy2(LIB, JAR)
    h = sha(JAR)
    with io.open(SHA, "w", encoding="ascii", newline=u"\n") as fh:
        fh.write(h + u"\n")
    print(u"已写 %s（%d B / sha1 %s）" % (os.path.basename(JAR), os.path.getsize(JAR), h))

    # ---- 当场审计 ----
    fails = []
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = [n for n in names if n.endswith(u".class")]
    recipes = [n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")]
    advs = [n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")]
    probes = [n for n in names if u"Check" in os.path.basename(n) and u"Zf1" in n]
    counts = {}
    for lg in LANGS:
        p = u"assets/potato_s_t/lang/%s.json" % lg
        if p in names:
            counts[lg] = len(json.loads(z.read(p).decode(u"utf-8")))
    print(u"class=%d 配方=%d 进度=%d 探针残留=%d 语言=%s" % (len(cls), len(recipes), len(advs), len(probes), counts))
    if len(recipes) != 93:
        fails.append(u"配方份数 %d ≠ 93" % len(recipes))
    if len(advs) != 43:
        fails.append(u"进度份数 %d ≠ 43" % len(advs))
    if probes:
        fails.append(u"jar 里有探针 class：%s" % probes[:3])
    if counts.get(u"zh_cn") != 593 or counts.get(u"lzh") != 595:
        fails.append(u"语言键数不对：%s" % counts)
    for n in (u"assets/potato_s_t/models/item/wrench.json",
              u"assets/potato_s_t/textures/item/wrench.png",
              u"assets/potato_s_t/models/item/electric_blast_furnace.json",
              u"assets/potato_s_t/textures/item/electric_blast_furnace.png",
              u"data/potato_s_t/recipe/electric_blast_furnace.json"):
        if n in names:
            fails.append(u"该删的还在 jar 里：%s" % n)
    if u"assets/potato_s_t/textures/block/electric_blast_furnace.png" not in names:
        fails.append(u"方块贴图不见了（不该动）")
    bad_crc = z.testzip()
    if bad_crc:
        fails.append(u"CRC 坏：%s" % bad_crc)
    print(u"审计失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    # 分类计数写一份小抄给文档脚本用
    io.open(os.path.join(ROOT, "build", "zftools", u"_zf162_jarfacts.txt"), "w",
            encoding="utf-8", newline=u"\n").write(
        u"classes=%d recipes=%d advancements=%d langs=%s\n"
        % (len(cls), len(recipes), len(advs), counts))
    print(u"class 数 %d（文档脚本要用）" % len(cls))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
