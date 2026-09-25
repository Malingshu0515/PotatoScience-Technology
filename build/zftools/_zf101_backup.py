# -*- coding: utf-8 -*-
u"""_zf101_backup.py —— ZF101 **动手前**的改前件（§10）

用户原话（一条到底）：

  「加一个酸性反应室（配方【铜块】【稳定金属块】【加热装置】，【钛锭】【灌装机】【钛锭】，
    【红石火把】【电解器】【拉杆】）Gui 输入；二氧化碳储罐 氧气储罐 氨气储罐 水储罐（各1000Mb）
    一个硫槽位 输出槽；硝酸 硫酸 碳酸储罐各1000Mb 三个选择按钮 在储罐下方 选择则执行相应的配方
    （gui别的你发挥）配方；1.10mb二氧化碳+1mb水 产出1mb碳酸 2.1mb氧气+1mb氨气 产出1mb硝酸
    3.10个硫+100MB水 产出100MB硫酸 耗能皆为500fe/t 储能12400fe」

⇒ 新机器「酸性反应室」+ **三种新流体**（碳酸 / 硝酸 / 硫酸，都是**液体不是气体**）。

会动到的（本轮范围大，一次抄全）：
  · Java：`ModFluids` / `PotatoSTClient` / `ModBlocks` / `ModMenus` / `PotatoST` / `ModItems`
    + 界面基类两件（`MachineScreen` / `GuiPart`：三个选择按钮需要**点击**通路，基类原本只有画与悬停）
    + `StatusLampPart`（新状态码 14）
  · 资源：`data/c/tags/fluid/` 三份新标签、`data/minecraft/tags/block/mineable/pickaxe.json`、
    8 张程序生成的占位贴图、方块/物品模型与 blockstate、四语言
  · 工具：`_zf45_recipes.py`（配方表）+ 全部 `_zf*_verify.py`（活体数字要跟着改）
    + `_zf78_falsify.py` + `_zf100_gates.ps1`（下一轮门的模板）
  · 3 份文档 + 旧成品 jar 与 `.sha1`
  · 另存 `recipe_before.txt` = 改前配方目录的 **47** 个文件名
"""
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
BK = r"C:\PotatoST救援\zf101_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"
RDIR = r"src\main\resources\data\potato_s_t\recipe"
FILES = [
    JAVA + r"\ModFluids.java",
    JAVA + r"\PotatoSTClient.java",
    JAVA + r"\ModBlocks.java",
    JAVA + r"\ModMenus.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\ModItems.java",
    JAVA + r"\client\gui\MachineScreen.java",
    JAVA + r"\client\gui\GuiPart.java",
    JAVA + r"\client\gui\parts\StatusLampPart.java",
    TOOLS + r"\_zf45_recipes.py",
    TOOLS + r"\_zf71_verify.py",
    TOOLS + r"\_zf73_repro.py",
    TOOLS + r"\_zf73_verify.py",
    TOOLS + r"\_zf74_verify.py",
    TOOLS + r"\_zf75_verify.py",
    TOOLS + r"\_zf78_falsify.py",
    TOOLS + r"\_zf78_verify.py",
    TOOLS + r"\_zf79_verify.py",
    TOOLS + r"\_zf80_verify.py",
    TOOLS + r"\_zf81_verify.py",
    TOOLS + r"\_zf82_verify.py",
    TOOLS + r"\_zf93_verify.py",
    TOOLS + r"\_zf95_verify.py",
    TOOLS + r"\_zf96_verify.py",
    TOOLS + r"\_zf97_verify.py",
    TOOLS + r"\_zf98_verify.py",
    TOOLS + r"\_zf100_verify.py",
    TOOLS + r"\_zf100_gates.ps1",
    r"docs\开发档案.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"docs\贴图清单.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]
fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s（重跑会覆盖改前件，直接中止）" % BK)
        return 1
    lines, ok = [], 0
    for rel in FILES:
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

    cur = sorted(n for n in os.listdir(os.path.join(ROOT, RDIR)) if n.endswith(u".json"))
    io.open(os.path.join(BK, u"recipe_before.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(cur) + u"\n")
    lines.append(u"（附）recipe_before.txt：改前配方 %d 份" % len(cur))
    print(u"  改前配方 %d 份 → recipe_before.txt" % len(cur))

    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
