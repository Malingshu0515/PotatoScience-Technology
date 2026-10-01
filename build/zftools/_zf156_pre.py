# -*- coding: utf-8 -*-
u"""_zf156_pre.py —— ZF156 动手前备份（§10：第一个字节改动之前先备份）。

本轮（ZF156 = 0.13 三个小修）要动：
  · `TerminalBlockEntity.java`（① 端子连线不再因区块卸载被断开）
  · `GuideBook.java` + 新建 `ModAttachments.java`（② 手册只发一次：附件 + copyOnDeath）
  · `PotatoST.java`（注册附件表；⚠ 也是探针挂载点，动手前就在清单里）
  · `ModItems.java`（只是把「板子不挂 c: 标签」那两句注释改成现行口径）
  · 28 份配方 JSON（金属板原料 `{"item": ...}` → `{"tag": "c:plates/<金属>"}`）
  · `data\\c\\tags\\item\\plates\\*.json`（备着：万一要给别的 mod 补可选条目）
  · `gradle.properties`（0.12 → 0.13）
  · 三份文档
  · 全部常驻门（版本常量 / 成品名 / 键数 / 配方数要跟平）
  · 成品：`release\\PotatoST-0.12.jar` + `.sha1` + `build\\libs\\potato_s_t-0.12.jar`

落到 `C:\\PotatoST救援\\zf156_pre\\`，逐份核 sha1 + 回读。
跑法：python build\\zftools\\_zf156_pre.py
"""
import hashlib
import io
import os
import re
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf156_pre"
ZT = os.path.join(PROJ, "build", "zftools")
RECIPE_DIR = os.path.join(PROJ, r"src\main\resources\data\potato_s_t\recipe")

EXPLICIT = [
    r"src\main\java\com\potatost\mod\TerminalBlockEntity.java",
    r"src\main\java\com\potatost\mod\GuideBook.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"gradle.properties",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.12.jar",
    r"release\PotatoST-0.12.jar.sha1",
    r"build\libs\potato_s_t-0.12.jar",
]

PLATE = re.compile(r"potato_s_t:(?:aluminum|cobalt|copper|iron|nickel|silver|steel)_plate")


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    items = list(EXPLICIT)
    # 用到自家金属板的配方（含 pressing 的产物那 7 份：一起备着，免得改错地方）
    for dirpath, _d, filenames in os.walk(RECIPE_DIR):
        for fn in filenames:
            if not fn.endswith(".json"):
                continue
            p = os.path.join(dirpath, fn)
            if PLATE.search(io.open(p, encoding="utf-8").read()):
                items.append(os.path.relpath(p, PROJ))
    # 板子标签
    for fn in sorted(os.listdir(os.path.join(PROJ, r"src\main\resources\data\c\tags\item\plates"))):
        items.append(os.path.join(r"src\main\resources\data\c\tags\item\plates", fn))
    items.append(r"src\main\resources\data\c\tags\item\plates.json")
    # 常驻门
    for fn in sorted(os.listdir(ZT)):
        if fn.endswith(u"_verify.py") and fn.startswith(u"_zf") and not fn.startswith(u"_zf156_"):
            items.append(os.path.join(u"build", u"zftools", fn))
        if fn in (u"_zf104_gates.ps1", u"_zf104_gatecount.py", u"_zf104_gates.txt",
                  u"_zf149_jar.py", u"_zf155_jarcheck.py", u"_zf155_verify.py",
                  u"_zf153_gates.py", u"_zf154_gatefix.py",
                  u"TextureCheck.py", u"_rzh_facts_check.py"):
            items.append(os.path.join(u"build", u"zftools", fn))
    items = sorted(set(items))
    if not os.path.isdir(DST):
        os.makedirs(DST)
    fails, total = [], 0
    lines = []
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
