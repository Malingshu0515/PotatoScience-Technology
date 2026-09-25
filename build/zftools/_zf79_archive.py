# -*- coding: utf-8 -*-
u"""_zf79_archive.py —— 把 ZF79 的新增/改动文件归档到 `C:\\PotatoST救援\\zf79_pre\\新增文件\\`

规矩同往轮：逐份**核哈希**、每类都断言"至少拷到 N 份"（防 glob 写错静默少拷）、
清单追加进 MANIFEST/`_sha1.txt`。
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
BK = r"C:\PotatoST救援\zf79_pre"
NEW = os.path.join(BK, u"新增文件")

GROUPS = [
    (u"Java：本轮改过的 7 个",
     [r"src\main\java\com\potatost\mod\PressRecipes.java",
      r"src\main\java\com\potatost\mod\HydraulicPressBlockEntity.java",
      r"src\main\java\com\potatost\mod\MachineRecipes.java",
      r"src\main\java\com\potatost\mod\ModBlocks.java",
      r"src\main\java\com\potatost\mod\ModItems.java",
      r"src\main\java\com\potatost\mod\client\gui\parts\StatusLampPart.java",
      r"src\main\java\com\potatost\mod\PotatoST.java"], 7),
    (u"资源：柏油块（贴图 + blockstate + 2 个模型）",
     [r"src\main\resources\assets\potato_s_t\textures\block\asphalt_block.png",
      r"src\main\resources\assets\potato_s_t\blockstates\asphalt_block.json",
      r"src\main\resources\assets\potato_s_t\models\block\asphalt_block.json",
      r"src\main\resources\assets\potato_s_t\models\item\asphalt_block.json"], 4),
    (u"资源：电力高炉新材质（含用户原名件留档）",
     [u"src\\main\\resources\\assets\\potato_s_t\\textures\\block\\electric_blast_furnace.png",
      u"src\\main\\resources\\assets\\potato_s_t\\textures\\block\\电力高炉.原名件"], 2),
    (u"资源：四语言 + 挖掘标签",
     [r"src\main\resources\assets\potato_s_t\lang\*.json",
      r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json"], 5),
    (u"工具：本轮脚本 + 探针源 + 证据",
     [r"build\zftools\_zf79_*.py",
      r"build\zftools\_zf79_*.ps1",
      r"build\zftools\check\AsphaltCheck.java",
      r"build\zftools\_zf79_server.log",
      r"build\zftools\_zf79_server.log.utf8.txt",
      r"build\zftools\_zf79_gates.txt",
      r"build\zftools\_zf79_gates.txt.utf8.txt",
      r"build\zftools\_zf79_compile.log.utf8.txt",
      r"build\zftools\_zf79_asphalt_provenance.json",
      r"build\zftools\_zf78_falsify.py"], 12),
    (u"文档", [r"docs\开发档案.md", r"docs\v0.11规划.md", r"docs\贴图清单.md",
              r"docs\UpdateAnnouncement_EN.md"], 4),
    (u"成品", [r"release\PotatoST-0.11.jar", r"release\PotatoST-0.11.jar.sha1"], 2),
]

fails = []
lines = []


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


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
            newline=u"\n").write(u"# ZF79 归档（%d 份，逐份核过哈希）\n\n" % total
                                 + u"\n".join(lines) + u"\n")
    print(u"清单已写：zf79_pre\\新增文件_清单.txt")
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
