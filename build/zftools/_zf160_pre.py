# -*- coding: utf-8 -*-
u"""_zf160_pre.py —— ZF160 动手前备份（§10：第一个字节改动之前先备份）。

本轮（ZF160 = 0.13 第五笔，矿脉密度）要动：
  · `worldgen\\configured_feature\\ore_silver.json`（矿脉 size 3 → 10）
  · `worldgen\\placed_feature\\ore_silver_placed.json`（每区块次数 9 → 12）
  · `worldgen\\placed_feature\\ore_aluminum_placed.json`（每区块次数 12 → 10）
  · 三份文档 / 常驻门与打包脚本 / 成品 0.13 + `.sha1` + `build\\libs` 那份 / `PotatoST.java`（⚠ 探针挂载点）

落到 `C:\\PotatoST救援\\zf160_pre\\`，逐份核 sha1 + 回读。
跑法：python build\\zftools\\_zf160_pre.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf160_pre"

EXPLICIT = [
    r"src\main\resources\data\potato_s_t\worldgen\configured_feature\ore_silver.json",
    r"src\main\resources\data\potato_s_t\worldgen\placed_feature\ore_silver_placed.json",
    r"src\main\resources\data\potato_s_t\worldgen\placed_feature\ore_aluminum_placed.json",
    r"src\main\resources\data\potato_s_t\worldgen\configured_feature\ore_aluminum.json",
    r"src\main\resources\data\potato_s_t\neoforge\biome_modifier\potato_st_ores.json",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"build\zftools\_zf149_verify.py",
    r"build\zftools\_zf156_jarcheck.py",
    r"build\zftools\_zf156_pkg.py",
    r"build\zftools\_zf160_recon.py",
    r"gradle.properties",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.13.jar",
    r"release\PotatoST-0.13.jar.sha1",
    r"build\libs\potato_s_t-0.13.jar",
]


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    fails, total, lines = [], 0, []
    for rel in sorted(set(EXPLICIT)):
        src = os.path.join(PROJ, rel)
        if not os.path.isfile(src):
            fails.append(u"改前件不在：%s" % rel)
            continue
        dst = os.path.join(DST, rel)
        d = os.path.dirname(dst)
        if not os.path.isdir(d):
            os.makedirs(d)
        shutil.copy2(src, dst)
        if sha(src) != sha(dst):
            fails.append(u"%s 回读不一致" % rel)
            continue
        total += 1
        lines.append(u"%s  %s" % (sha(src), rel))
    with io.open(os.path.join(DST, u"_manifest.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(u"\n".join(lines) + u"\n")
    print(u"备份根：%s" % DST)
    print(u"备份成功 %d 份（清单 _manifest.txt）" % total)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
