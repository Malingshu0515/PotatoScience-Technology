# -*- coding: utf-8 -*-
u"""_zf112_backup.py —— ZF112 **动手前**的改前件（§10）

用户原话（两条消息一起给的）：
  「加一个锂电池构造间 通入硫酸 放入粗锰/粗铝and 镍/粗镍 and 碳酸锂 and钴/粗钴
    每t消耗10mb硫酸 30s后产出一个锂电池原件 不消耗电
    三元锂配方里的碳酸锂改成锂电池原件 金属板统一换成纸 别的电容什么的不变」

本轮会动到的：
  · Java **改** 8 个：`ModBlocks`（三件套）/ `ModItems`（新物品 + 创造页一行）/
    `ModMenus` / `PotatoST`（两个能力）/ `PotatoSTClient`（界面）/
    `client/gui/parts/StatusLampPart`（新状态码 17、18）/ `MachineRecipes`（JEI 一条）/
    `client/jei/PotatoSTJeiPlugin`（MACHINES 加一行 id）
  · Java **新** 4 个 + 探针 1 个：方块 / 方块实体 / 菜单 / 界面 + `Zf112Check`
  · 资源**改** 5 个：四语言 + `data/minecraft/tags/block/mineable/pickaxe.json`（§4.52）
    + `recipe/lithium_battery.json`（**三元锂那条配方**）
  · 资源**新** 7 个：blockstate / 方块模型 / 物品模型 / 方块贴图 / 新物品模型 / 新物品贴图 /
    机器的合成配方 JSON
  · 工具：本轮新脚本 + **全部常驻校验脚本**（一把全抄）
  · 文档 4 份 + 旧成品 jar 与 `.sha1`

⚠ 备份根已存在就直接退出（绝不覆盖上一次的改前件）。
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
BK = r"C:\PotatoST救援\zf112_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"
RES = r"src\main\resources"

FILES = [
    JAVA + r"\ModBlocks.java",
    JAVA + r"\ModItems.java",
    JAVA + r"\ModMenus.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\PotatoSTClient.java",
    JAVA + r"\client\gui\parts\StatusLampPart.java",
    JAVA + r"\MachineRecipes.java",
    JAVA + r"\client\jei\PotatoSTJeiPlugin.java",
    RES + r"\assets\potato_s_t\lang\zh_cn.json",
    RES + r"\assets\potato_s_t\lang\en_us.json",
    RES + r"\assets\potato_s_t\lang\ja_jp.json",
    RES + r"\assets\potato_s_t\lang\ru_ru.json",
    RES + r"\data\potato_s_t\recipe\lithium_battery.json",
    RES + r"\data\minecraft\tags\block\mineable\pickaxe.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [
    JAVA + r"\LithiumBatteryPlantBlock.java",
    JAVA + r"\LithiumBatteryPlantBlockEntity.java",
    JAVA + r"\LithiumBatteryPlantMenu.java",
    JAVA + r"\client\LithiumBatteryPlantScreen.java",
    JAVA + r"\Zf112Check.java",
    RES + r"\assets\potato_s_t\blockstates\lithium_battery_plant.json",
    RES + r"\assets\potato_s_t\models\block\lithium_battery_plant.json",
    RES + r"\assets\potato_s_t\models\item\lithium_battery_plant.json",
    RES + r"\assets\potato_s_t\textures\block\lithium_battery_plant.png",
    RES + r"\assets\potato_s_t\models\item\lithium_battery_component.json",
    RES + r"\assets\potato_s_t\textures\item\lithium_battery_component.png",
    RES + r"\data\potato_s_t\recipe\lithium_battery_plant.json",
    TOOLS + r"\_zf112_verify.py",
    TOOLS + r"\_zf112_falsify.py",
    TOOLS + r"\_zf112_lang.py",
    TOOLS + r"\_zf112_textures.py",
    TOOLS + r"\_zf112_retarget.py",
]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    lines, ok = [], 0
    todo = list(FILES)
    for pat in ("_zf*_verify.py", "_zf*_repro.py", "_zf*_guard.py", "_zf*_falsify.py",
                "_zf*_gatesnap.py", "_zf*_gatecount.py"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            rel = os.path.relpath(p, ROOT)
            if rel not in todo:
                todo.append(rel)
    for rel in todo:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            lines.append(u"MISSING  %s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = sha1(src)
        shutil.copy2(src, dst)
        after = sha1(dst)
        if before != after:
            fails.append(u"%s：拷贝后哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (after, os.path.getsize(dst), rel))
    pre = [u"%s  %s" % (u"存在(异常)" if os.path.exists(os.path.join(ROOT, p)) else u"不存在(正常)", p)
           for p in NEW]
    io.open(os.path.join(BK, u"_zf112_newfiles.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"本轮开始前，下列路径的**存在性**（回退时：不存在的一律删除；存在的别动）\n"
        + u"\n".join(pre) + u"\n")
    bad = [p for p in NEW if os.path.exists(os.path.join(ROOT, p))]
    if bad:
        fails.append(u"本轮要新建的文件已经有同名：%s" % bad)
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
