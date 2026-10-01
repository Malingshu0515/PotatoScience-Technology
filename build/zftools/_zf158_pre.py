# -*- coding: utf-8 -*-
u"""_zf158_pre.py —— ZF158 动手前备份（§10：第一个字节改动之前先备份）。

本轮（ZF158 = 0.13 的第四笔）要动：
  · `build\\zftools\\_zf45_recipes.py`（**生成器表**：13 行 15 处「自家板当物品」→ `#c:plates/*`；
    外加 thermal_metal 那条图纸换成「铜板夹银锭」）
  · `src\\main\\resources\\data\\potato_s_t\\recipe\\**`（整目录 —— 因为要用生成器 `--write` 重出，
    必须能证明"除了 thermal_metal 谁都没动"）
  · 三份文档
  · 常驻门与打包脚本（键数/配方数/成品名/哈希要跟平）
  · 成品：`release\\PotatoST-0.13.jar` + `.sha1` + `build\\libs\\potato_s_t-0.13.jar`

落到 `C:\\PotatoST救援\\zf158_pre\\`，逐份核 sha1 + 回读。
跑法：python build\\zftools\\_zf158_pre.py
"""
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf158_pre"
ZT = os.path.join(PROJ, "build", "zftools")
RECIPE = os.path.join(PROJ, r"src\main\resources\data\potato_s_t\recipe")

EXPLICIT = [
    r"build\zftools\_zf45_recipes.py",
    r"build\zftools\_zf156_verify.py",
    r"build\zftools\_zf149_verify.py",
    r"build\zftools\_zf149_jar.py",
    r"build\zftools\_zf155_jarcheck.py",
    r"build\zftools\_zf156_jarcheck.py",
    r"build\zftools\_zf156_pkg.py",
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
    items = list(EXPLICIT)
    for dirpath, _d, filenames in os.walk(RECIPE):
        for fn in filenames:
            items.append(os.path.relpath(os.path.join(dirpath, fn), PROJ))
    items = sorted(set(items))
    if not os.path.isdir(DST):
        os.makedirs(DST)
    fails, total, lines = [], 0, []
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
