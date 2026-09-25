# -*- coding: utf-8 -*-
"""_zf47_archive.py —— 归档 zf47_pre（改后件 + 新增件 + 哈希）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf47_pre"

CHANGED = [
    r"docs\开发档案.md",
    r"build\zftools\_zf45_recipes.py",
    r"src\main\java\com\potatost\mod\PotatoST.java",      # 探针注册行加了又删，净变化为零
]

ADDED = [
    r"src\main\resources\data\potato_s_t\recipe\heat_resistant_metal_block.json",
    r"build\zftools\_zf47_backup.ps1",
    r"build\zftools\_zf47_inject.py",
    r"build\zftools\_zf47_archive.py",
    r"build\zftools\_zf47_notes.py",
    r"build\zftools\check\RecipeProbe.java",
    r"build\zftools\check\zf47_探针.log",
    r"build\zftools\check\zf47_反证.log",
    r"build\zftools\zf47_gates.txt",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def main():
    newdir = os.path.join(BK, "新增文件")
    os.makedirs(newdir, exist_ok=True)
    rows, bad = [], 0
    for rel in CHANGED:
        src = os.path.join(PROJ, rel)
        dst = os.path.join(BK, "改后_" + os.path.basename(rel))
        shutil.copy2(src, dst)
        a, b = sha(src), sha(dst)
        rows.append((rel, a, b))
        if a != b:
            print(u"!! 改后副本不一致: " + rel)
            bad += 1
    for rel in ADDED:
        src = os.path.join(PROJ, rel)
        if not os.path.isfile(src):
            print(u"!! 新增文件不存在: " + rel)
            bad += 1
            continue
        dst = os.path.join(newdir, os.path.basename(rel))
        shutil.copy2(src, dst)
        a, b = sha(src), sha(dst)
        rows.append((rel, a, b))
        if a != b:
            print(u"!! 新增副本不一致: " + rel)
            bad += 1
    with io.open(os.path.join(BK, "_sha256_改后与新增.txt"), "w", encoding="utf-8", newline="\n") as fh:
        for rel, a, b in rows:
            fh.write(u"{0}  {1}  {2}\n".format(a, u"一致" if a == b else u"不一致", rel))
    print(u"改后件 {0} 个、新增件 {1} 个，合计 {2} 份".format(len(CHANGED), len(ADDED), len(rows)))
    on_disk = len([f for f in os.listdir(newdir) if os.path.isfile(os.path.join(newdir, f))])
    print(u"新增文件目录实际文件数 = {0}".format(on_disk))
    if on_disk != len(ADDED):
        print(u"!! 目录文件数与清单不符")
        bad += 1
    print(u"哈希不一致 = {0}".format(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
