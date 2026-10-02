# -*- coding: utf-8 -*-
u"""_zf162_pre.py —— ZF162 动手前备份（§10：第一个字节改动之前先备份）。

本轮（ZF162 = 0.13 第六笔）要动：
  · **删扳手**：`ModItems`（注册 + 创造页）/ `models\\item\\wrench.json` / `textures\\item\\wrench.png`
    / `ElectricBlastFurnaceWrench.java`（整份删）/ 三处拆解入口
    （`ElectricBlastFurnaceBlock` / `ElectricBlastFurnacePartBlock` / `AlloySmelterBlock`）
    / 五份 lang 的 `item.potato_s_t.wrench` / 三个手册图标
  · **删电力高炉的物品形态**：`ModBlocks`（BlockItem）/ `models\\item\\electric_blast_furnace.json`
    / `textures\\item\\electric_blast_furnace.png` / `recipe\\electric_blast_furnace.json`
    / 进度 `blast_furnace.json`（改挂「装配成功」触发）/ `PotatoSTJeiPlugin` / 手册图标
  · **灌装机**：`FillingMachineBlockEntity` / `FillingMachineMenu` / `FillingMachineBlock`
    （什么都能放 + 只灌「能灌装」的容器 + 诊断新状态）+ 五份 lang
  · 生成器表 `_zf45_recipes.py` / 手册生成器 `_zf148_book.py`
  · `build\\zftools\\*.py`（整目录，本轮要跟平的门很多）
  · 三份文档 / 成品 0.13 + `.sha1` + `build\\libs` 那份

落到 `C:\\PotatoST救援\\zf162_pre\\`，逐份核 sha1 + 回读。
跑法：python build\\zftools\\_zf162_pre.py
"""
import glob
import hashlib
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

PROJ = r"E:\PotatoST"
DST = r"C:\PotatoST救援\zf162_pre"

JAVA = r"src\main\java\com\potatost\mod"
LANG = r"src\main\resources\assets\potato_s_t\lang"

EXPLICIT = [
    # ---- 删扳手 ----
    JAVA + r"\ModItems.java",
    JAVA + r"\ElectricBlastFurnaceBlock.java",
    JAVA + r"\ElectricBlastFurnacePartBlock.java",
    JAVA + r"\ElectricBlastFurnaceWrench.java",
    JAVA + r"\AlloySmelterBlock.java",
    r"src\main\resources\assets\potato_s_t\models\item\wrench.json",
    r"src\main\resources\assets\potato_s_t\textures\item\wrench.png",
    # ---- 删电力高炉物品形态 ----
    JAVA + r"\ModBlocks.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\BlastFurnaceAssembly.java",
    JAVA + r"\client\jei\PotatoSTJeiPlugin.java",
    r"src\main\resources\assets\potato_s_t\models\item\electric_blast_furnace.json",
    r"src\main\resources\assets\potato_s_t\textures\item\electric_blast_furnace.png",
    r"src\main\resources\data\potato_s_t\recipe\electric_blast_furnace.json",
    r"src\main\resources\data\potato_s_t\advancement\blast_furnace.json",
    # ---- 灌装机 ----
    JAVA + r"\FillingMachineBlockEntity.java",
    JAVA + r"\FillingMachineMenu.java",
    JAVA + r"\FillingMachineBlock.java",
    # ---- 五份 lang ----
    LANG + r"\zh_cn.json",
    LANG + r"\en_us.json",
    LANG + r"\ja_jp.json",
    LANG + r"\ru_ru.json",
    LANG + r"\lzh.json",
    # ---- 手册（图标 + 生成器）----
    r"src\main\resources\assets\potato_s_t\patchouli_books\guide\en_us\categories\faq.json",
    r"src\main\resources\assets\potato_s_t\patchouli_books\guide\en_us\entries\faq\machine.json",
    r"src\main\resources\assets\potato_s_t\patchouli_books\guide\en_us\entries\getting_started\rules.json",
    r"src\main\resources\assets\potato_s_t\patchouli_books\guide\en_us\entries\materials\blast_alloy.json",
    r"build\zftools\_zf45_recipes.py",
    r"build\zftools\_zf148_book.py",
    # ---- 文档 ----
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"docs\贴图清单.md",
    # ---- 成品 ----
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


def copy_one(rel, fails, lines):
    src = os.path.join(PROJ, rel)
    if not os.path.isfile(src):
        fails.append(u"改前件不在：%s" % rel)
        return 0
    dst = os.path.join(DST, rel)
    d = os.path.dirname(dst)
    if not os.path.isdir(d):
        os.makedirs(d)
    shutil.copy2(src, dst)
    if sha(src) != sha(dst):
        fails.append(u"%s 回读不一致" % rel)
        return 0
    lines.append(u"%s  %s" % (sha(src), rel))
    return 1


def main():
    if not os.path.isdir(DST):
        os.makedirs(DST)
    fails, total, lines = [], 0, []
    for rel in sorted(set(EXPLICIT)):
        total += copy_one(rel, fails, lines)
    # 工具目录：整目录 *.py（本轮要跟平的门有几十份）
    tools = sorted(glob.glob(os.path.join(PROJ, u"build", u"zftools", u"*.py")))
    for p in tools:
        rel = os.path.relpath(p, PROJ)
        if rel in EXPLICIT:
            continue
        total += copy_one(rel, fails, lines)
    lines.append(u"# 工具目录 *.py 共 %d 份（含上面已列的）" % len(tools))
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
