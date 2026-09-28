# -*- coding: utf-8 -*-
u"""_zf155_pre.py —— ZF155 动手前备份（§10：第一个字节改动之前先备份）。

本轮（ZF155 通用升级模板）要动：
  · `ModItems.java`（注册物品 + 创造栏一行）
  · 新建 `UniversalUpgradeTemplate.java`（运行期加宽引擎）
  · 新建 `assets/potato_s_t/models/item/universal_upgrade_template.json`
  · 新建 `assets/potato_s_t/textures/item/universal_upgrade_template.png`
  · 五份 lang（各加 6 个键）
  · 新建 `data/potato_s_t/recipe/universal_upgrade_template.json`（八铝锭围一圈）
  · 新建 `data/potato_s_t/recipe/vibranium_sword_smithing.json`（振金剑）
  · 改 4 份 `vibranium_*_smithing.json`（模板换成通用模板）
  · 可能动帕秋莉手册（新增一条目）
  · `PotatoST.java`（⚠ 探针挂载点，动手前就写进清单）
  · 三份文档
  · 全部他线常驻门（活体数字/配方数/键数要跟平）
  · 成品：`release\\PotatoST-0.12.jar` + `.sha1` + `build\\libs\\potato_s_t-0.12.jar`

落到 `C:\\PotatoST救援\\zf155_pre\\`，逐份核 sha1 + 回读。
跑法：python build\\zftools\\_zf155_pre.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf155_pre"
ZT = os.path.join(PROJ, "build", "zftools")

EXPLICIT = [
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\assets\potato_s_t\lang\lzh.json",
    r"src\main\resources\data\potato_s_t\recipe\vibranium_helmet_smithing.json",
    r"src\main\resources\data\potato_s_t\recipe\vibranium_chestplate_smithing.json",
    r"src\main\resources\data\potato_s_t\recipe\vibranium_leggings_smithing.json",
    r"src\main\resources\data\potato_s_t\recipe\vibranium_boots_smithing.json",
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
        if fn.endswith(u"_verify.py") and fn.startswith(u"_zf") and not fn.startswith(u"_zf155_"):
            items.append(os.path.join(u"build", u"zftools", fn))
        if fn in (u"_zf104_gates.ps1", u"_zf104_gatecount.py", u"_zf104_gates.txt",
                  u"_zf149_jar.py", u"_zf153_gates.py", u"_zf154_gatefix.py",
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
