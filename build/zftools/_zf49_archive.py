# -*- coding: utf-8 -*-
"""_zf49_archive.py —— 归档 zf49_pre（改后件 + 新增件 + 哈希；带基名冲突改名）"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf49_pre"

CHANGED = [
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\ModMenus.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\java\com\potatost\mod\PotatoSTClient.java",
    r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json",
    r"src\main\resources\data\minecraft\tags\block\needs_stone_tool.json",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"build\zftools\_zf46_verify.py",
    r"build\zftools\_zf48_verify.py",
    r"docs\开发档案.md",
]

ADDED = [
    # Java
    r"src\main\java\com\potatost\mod\AlloySmelterStructure.java",
    r"src\main\java\com\potatost\mod\AlloySmelterBlock.java",
    r"src\main\java\com\potatost\mod\AlloySmelterBlockEntity.java",
    r"src\main\java\com\potatost\mod\AlloySmelterPortBlock.java",
    r"src\main\java\com\potatost\mod\AlloySmelterPortBlockEntity.java",
    r"src\main\java\com\potatost\mod\AlloySmelterMenu.java",
    r"src\main\java\com\potatost\mod\client\AlloySmelterScreen.java",
    # 资源
    r"src\main\resources\assets\potato_s_t\blockstates\alloy_smelter.json",
    r"src\main\resources\assets\potato_s_t\blockstates\alloy_smelter_port.json",
    r"src\main\resources\assets\potato_s_t\models\block\alloy_smelter.json",
    r"src\main\resources\assets\potato_s_t\models\block\alloy_smelter_port.json",
    r"src\main\resources\assets\potato_s_t\models\item\alloy_smelter.json",
    r"src\main\resources\assets\potato_s_t\textures\block\alloy_smelter_front.png",
    r"src\main\resources\data\potato_s_t\loot_table\blocks\alloy_smelter.json",
    # 脚本 / 探针 / 取证
    r"build\zftools\_zf49_backup.ps1",
    r"build\zftools\_zf49_texture.py",
    r"build\zftools\_zf49_lang.py",
    r"build\zftools\_zf49_archive.py",
    r"build\zftools\_zf49_notes.py",
    r"build\zftools\check\AlloySmelterCheck.java",
    r"build\zftools\check\zf49_探针.log",
    r"build\zftools\check\zf49_反证.log",
    r"build\zftools\zf49_gates.txt",
    r"build\zftools\zf49_regression__zf48.txt",
    r"build\zftools\zf49_regression__zf46.txt",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def flat_name(rel):
    base = os.path.basename(rel)
    if base.lower() in flat_name.seen:
        return os.path.basename(os.path.dirname(rel)) + "_" + base
    flat_name.seen.add(base.lower())
    return base


flat_name.seen = set()


def main():
    newdir = os.path.join(BK, "新增文件")
    os.makedirs(newdir, exist_ok=True)
    rows, collisions, bad = [], [], 0
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
        base = os.path.basename(rel)
        name = flat_name(rel)
        if name != base:
            collisions.append((rel, name))
        if not os.path.isfile(src):
            print(u"!! 新增文件不存在: " + rel)
            bad += 1
            continue
        dst = os.path.join(newdir, name)
        shutil.copy2(src, dst)
        a, b = sha(src), sha(dst)
        rows.append((rel, a, b))
        if a != b:
            print(u"!! 新增副本不一致: " + rel)
            bad += 1
    with io.open(os.path.join(BK, "_sha256_改后与新增.txt"), "w", encoding="utf-8", newline="\n") as fh:
        for rel, a, b in rows:
            fh.write(u"{0}  {1}  {2}\n".format(a, u"一致" if a == b else u"不一致", rel))
    for rel, name in collisions:
        print(u"基名冲突 -> 改名归档: {0}  ==>  {1}".format(rel, name))
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
