# -*- coding: utf-8 -*-
u"""_zf151_pre.py —— ZF151 动手前备份（§10：第一个字节改动之前先备份）。

本轮要动：
  · `SolarPanelBlock.java`（加 getDrops）
  · `ModBlocks.java`（两个接线口去掉 requiresCorrectToolForDrops）
  · `data\\minecraft\\tags\\block\\mineable\\pickaxe.json`（补 3 个漏项）
  · `PotatoST.java`（⚠ 探针挂载点，动手前就写进清单）
  · 三份文档 + 全部常驻门（活体数字/成品哈希要跟平）
  · 成品：`release\\PotatoST-0.12.jar` + `.sha1` + `build\\libs\\potato_s_t-0.12.jar`（本轮末尾要重打）

落到 `C:\\PotatoST救援\\zf151_pre\\`，逐份核 sha1 + 回读。
跑法：python build\\zftools\\_zf151_pre.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf151_pre"
ZT = os.path.join(PROJ, "build", "zftools")

EXPLICIT = [
    r"src\main\java\com\potatost\mod\SolarPanelBlock.java",
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.12.jar",
    r"release\PotatoST-0.12.jar.sha1",
    r"build\libs\potato_s_t-0.12.jar",
]


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    items = list(EXPLICIT)
    for fn in sorted(os.listdir(ZT)):
        if fn.endswith(u"_verify.py") and fn.startswith(u"_zf") and not fn.startswith(u"_zf151_"):
            items.append(os.path.join(u"build", u"zftools", fn))
    items = sorted(set(items))
    if not os.path.isdir(DST):
        os.makedirs(DST)
    fails, total = [], 0
    for rel in items:
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
    print(u"备份根：%s" % DST)
    print(u"备份成功 %d 份" % total)
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
