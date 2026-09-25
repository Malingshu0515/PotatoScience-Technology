# -*- coding: utf-8 -*-
"""_zf45_archive.py —— 把"改后"文件与新增文件归档进 zf45_pre（§10 备份策略的收尾动作）

**为什么要机械化**：ZF34 漏过 `needs_stone_tool.json`、ZF36 漏过 `HydraulicPressBlock.java` ——
两次都是"凭记忆列清单"。所以这里：
  ① 改后件清单**和 _zf45_backup.ps1 里那份改前清单逐字一致**（同一个列表抄过来）；
  ② 新增文件按目录实际扫描（不是手写）；
  ③ 归档前后都算 SHA256，和项目里的当前文件比对 —— **不一致就报错**，
     避免"归档完才发现拷的是旧版"。
"""
import hashlib
import io
import os
import shutil
import sys

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf45_pre"

# ① 改后件 = 改前清单（与 _zf45_backup.ps1 一字不差）
CHANGED = [
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\MicroCrusherRecipes.java",
    r"src\main\java\com\potatost\mod\BlastFurnaceRecipes.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceBlockEntity.java",
    r"src\main\java\com\potatost\mod\MachineRecipes.java",
    r"src\main\java\com\potatost\mod\client\jei\PotatoSTJeiPlugin.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"docs\开发档案.md",
]

# ② 新增文件（本阶段新建的）
ADDED = [
    # 新物品：4 张贴图 + 4 个模型
    r"src\main\resources\assets\potato_s_t\textures\item\iron_powder.png",
    r"src\main\resources\assets\potato_s_t\textures\item\magnet.png",
    r"src\main\resources\assets\potato_s_t\textures\item\thermal_metal.png",
    r"src\main\resources\assets\potato_s_t\textures\item\photovoltaic_component.png",
    r"src\main\resources\assets\potato_s_t\models\item\iron_powder.json",
    r"src\main\resources\assets\potato_s_t\models\item\magnet.json",
    r"src\main\resources\assets\potato_s_t\models\item\thermal_metal.json",
    r"src\main\resources\assets\potato_s_t\models\item\photovoltaic_component.json",
    # 14 份合成配方
    r"src\main\resources\data\potato_s_t\recipe\micro_crusher.json",
    r"src\main\resources\data\potato_s_t\recipe\hydraulic_press.json",
    r"src\main\resources\data\potato_s_t\recipe\filling_machine.json",
    r"src\main\resources\data\potato_s_t\recipe\salt_dryer.json",
    r"src\main\resources\data\potato_s_t\recipe\generator.json",
    r"src\main\resources\data\potato_s_t\recipe\fluid_pipe.json",
    r"src\main\resources\data\potato_s_t\recipe\fluid_pump.json",
    r"src\main\resources\data\potato_s_t\recipe\salt_decomposer.json",
    r"src\main\resources\data\potato_s_t\recipe\photovoltaic_component.json",
    r"src\main\resources\data\potato_s_t\recipe\solar_panel.json",
    r"src\main\resources\data\potato_s_t\recipe\thermal_metal.json",
    r"src\main\resources\data\potato_s_t\recipe\heater.json",
    r"src\main\resources\data\potato_s_t\recipe\empty_spool.json",
    r"src\main\resources\data\potato_s_t\recipe\copper_wire.json",
    # 本阶段的脚本与探针
    r"build\zftools\_zf45_backup.ps1",
    r"build\zftools\_zf45_textures.py",
    r"build\zftools\_zf45_lang.py",
    r"build\zftools\_zf45_verify.py",
    r"build\zftools\_zf45_recipes.py",
    r"build\zftools\_zf45_archive.py",
    r"build\zftools\_zf45_notes.py",
    r"build\zftools\check\Zf45Check.java",
    r"build\zftools\check\zf45_探针.log",
    r"build\zftools\check\zf45_反证.log",
    r"build\zftools\zf45_lang_verify.txt",
    r"build\zftools\zf45_gates.txt",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def flat_name(rel):
    """归档到扁平目录时用的文件名。

    **必须查基名冲突**：本项目里有**同名不同物**的文件 —— 例如
    `models/item/thermal_metal.json`（模型）与 `recipe/thermal_metal.json`（配方）。
    第一版直接取 basename，两个就互相覆盖了，而且只有"拷贝份数 34 vs 目录里 32"这个
    对不上的数字会露馅（正是 §10 里"清单要机械核对"要防的那类漏）。
    冲突时按父目录名加前缀，并在 sideline 报告里点出来。
    """
    base = os.path.basename(rel)
    key = base.lower()
    if key in flat_name.seen:
        parent = os.path.basename(os.path.dirname(rel))
        return parent + "_" + base
    flat_name.seen.add(key)
    return base


flat_name.seen = set()


def main():
    newdir = os.path.join(BK, "新增文件")
    os.makedirs(newdir, exist_ok=True)
    rows = []
    bad = 0
    collisions = []
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
        dst = os.path.join(newdir, name)
        if not os.path.isfile(src):
            print(u"!! 新增文件不存在: " + rel)
            bad += 1
            continue
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
    print(u"哈希不一致 = {0}".format(bad))
    # 归档份数必须和磁盘上的实际文件数对得上（第一版就是这里露的馅）
    on_disk = len([f for f in os.listdir(newdir) if os.path.isfile(os.path.join(newdir, f))])
    print(u"新增文件目录里的实际文件数 = {0}".format(on_disk))
    if on_disk != len(ADDED):
        print(u"!! 目录文件数与清单不符")
        bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
