# -*- coding: utf-8 -*-
u"""_zf73_backup.py —— ZF73 改前件（v0.11 第一轮：原油流体 + 液体方块 + 油桶 + 两刀白名单）

§10：动手前先抄一份并核哈希。**清单不凭记忆写**：配方目录整个 glob 进来（要拿"除新增那一份，
其余逐字节没动"的复现性证据），其余逐个列路径。

本轮会改到的老文件（预估，改完若发现多碰了谁，按 §10 的「可逆精确替换」规矩补）：
  · ModFluids / ModBlocks / ModItems / TankContents / HighPressureTankItem
  · FillingMachineBlockEntity / FillingMachineMenu
  · gradle.properties（0.10 → 0.11）
  · 四份 lang
  · build/zftools/_zf45_recipes.py（配方的唯一来源）+ _zf69_repro.py（把"备份根不见了"改成响的）
  · docs/开发档案.md、docs/贴图清单.md
  · release/PotatoST-0.10.jar 与 .sha1（留档以证明本轮**没动**旧成品）
"""
import glob
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
ROOT = r"C:\PotatoST救援\zf73_pre"

FILES = [
    r"gradle.properties",
    r"src\main\java\com\potatost\mod\ModFluids.java",
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\TankContents.java",
    r"src\main\java\com\potatost\mod\HighPressureTankItem.java",
    r"src\main\java\com\potatost\mod\FillingMachineBlockEntity.java",
    r"src\main\java\com\potatost\mod\FillingMachineMenu.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\zftools\_zf45_recipes.py",
    r"build\zftools\_zf69_repro.py",
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.10.jar",
    r"release\PotatoST-0.10.jar.sha1",
]

fails = []


def sha1(path):
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def main():
    files = list(FILES)
    # 配方目录整个进来（glob，不凭记忆）
    for p in sorted(glob.glob(os.path.join(PROJ, u"src", u"main", u"resources", u"data",
                                           u"potato_s_t", u"recipe", u"*.json"))):
        files.append(os.path.relpath(p, PROJ))
    print(u"本轮改前件 %d 个（其中配方 %d 份）" % (len(files), len(files) - len(FILES)))
    for rel in files:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            fails.append(u"源文件不存在: %s" % rel)
            continue
        folder = os.path.dirname(dst)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        if os.path.isfile(dst):
            a, b = sha1(src), sha1(dst)
            print(u"  [%s] %-58s 改前件已在，不覆盖" % (u"SKIP" if a == b else u"KEEP", rel))
            continue
        shutil.copy2(src, dst)
        a, b = sha1(src), sha1(dst)
        ok = a == b
        if not ok:
            fails.append(u"拷贝后哈希不一致: %s" % rel)
        print(u"  [%s] %-58s %s  %d B" % (u"OK" if ok else u"FAIL", rel, a[:12],
                                          os.path.getsize(dst)))
    print(u"\n改前件目录: %s" % ROOT)
    print(u"文件数 = %d   失败项 = %d" % (len(files), len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
