# -*- coding: utf-8 -*-
u"""_zf81_archive.py —— 把 ZF81 的改动/新增归档到 `C:\\PotatoST救援\\zf81_pre\\新增文件\\`

规矩同往轮：逐份核哈希、每类断言"至少拷到 N 份"（防 glob 写错静默少拷）、清单写 `新增文件_清单.txt`。
"""
import glob
import hashlib
import io
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf81_pre"
NEW = os.path.join(BK, u"新增文件")

GROUPS = [
    (u"Java：本轮改过的 2 个",
     [r"src\main\java\com\potatost\mod\ElectrolyzerBlockEntity.java",
      r"src\main\java\com\potatost\mod\MachineRecipes.java"], 2),
    (u"资源：四语言", [r"src\main\resources\assets\potato_s_t\lang\*.json"], 4),
    (u"工具：本轮脚本 + 探针源 + 证据",
     [r"build\zftools\_zf81_*.py",
      r"build\zftools\_zf81_*.ps1",
      r"build\zftools\_zf81_*.log",
      r"build\zftools\_zf81_probe.txt",
      r"build\zftools\_zf81_gates.txt",
      r"build\zftools\check\ElectrolyzerCheck.java",
      r"build\zftools\_zf80_gates.ps1",
      r"build\zftools\_zf78_falsify.py"], 16),
    (u"文档", [r"docs\开发档案.md", r"docs\UpdateAnnouncement_EN.md"], 2),
    (u"成品", [r"release\PotatoST-0.11.jar", r"release\PotatoST-0.11.jar.sha1"], 2),
]

fails = []
lines = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    total = 0
    size = 0
    for title, patterns, minimum in GROUPS:
        files = []
        for pat in patterns:
            files += [p for p in glob.glob(os.path.join(ROOT, pat)) if os.path.isfile(p)]
        files = sorted(set(files))
        if len(files) < minimum:
            fails.append(u"%s：只找到 %d 份（至少应有 %d）" % (title, len(files), minimum))
        print(u"== %s：%d 份 ==" % (title, len(files)))
        for src in files:
            rel = os.path.relpath(src, ROOT)
            dst = os.path.join(NEW, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            before = sha1(src)
            shutil.copy2(src, dst)
            after = sha1(dst)
            if before != after:
                fails.append(u"%s：拷贝后哈希不一致" % rel)
            else:
                total += 1
                size += os.path.getsize(dst)
                lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
    print(u"\n归档 %d 份 / %.1f KB" % (total, size / 1024.0))
    io.open(os.path.join(BK, u"新增文件_清单.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"# ZF81 归档（%d 份，逐份核过哈希）\n\n" % total
                                 + u"\n".join(lines) + u"\n")
    print(u"清单已写：zf81_pre\\新增文件_清单.txt")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
