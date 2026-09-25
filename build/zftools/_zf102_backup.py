# -*- coding: utf-8 -*-
u"""_zf102_backup.py —— ZF102 **动手前**的改前件（§10）

用户原话（一条）：

  「酸性反应器再加两个罐子（氢气和氯气）1000MB 然后新加配方盐酸
    10mb氢气+10mb氯气+5mb水 产出5mb盐酸 耗能一致」

⇒ 给 ZF101 那台酸性反应室**加两个原料罐**（氢气 / 氯气，各 1000 mB）、
  **加一个新产物罐**（盐酸 1000 mB —— 用户没明说，但前三个配方各有自己的产物罐，
  第四个配方没有罐就没地方放，所以要加）、**加第四个配方与第四个按钮**，
  耗能沿用 500 FE/t。

会动到的：
  · Java：`ModFluids`（+盐酸）/ `PotatoSTClient`（+贴图注册）
    + 酸性反应室的方块实体 / 菜单 / 界面（罐 7→10、配方 3→4、版面加宽 196→214）
  · 资源：`data/c/tags/fluid/` 一份新标签、两张新贴图、四语言
  · 工具：全部 `_zf*_verify.py`（流体数 14→15、键数 332→335）+ `_zf78_falsify.py`
    + `_zf101_gates.ps1`（下一轮门的模板）
  · 3 份文档 + 旧成品 jar 与 `.sha1`
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
BK = r"C:\PotatoST救援\zf102_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"
RDIR = r"src\main\resources\data\potato_s_t\recipe"
FILES = [
    JAVA + r"\ModFluids.java",
    JAVA + r"\PotatoSTClient.java",
    JAVA + r"\AcidicReactionChamberBlockEntity.java",
    JAVA + r"\AcidicReactionChamberMenu.java",
    JAVA + r"\client\AcidicReactionChamberScreen.java",
    JAVA + r"\PotatoST.java",
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
    TOOLS + r"\_zf85_verify.py",
    TOOLS + r"\_zf93_verify.py",
    TOOLS + r"\_zf95_verify.py",
    TOOLS + r"\_zf96_verify.py",
    TOOLS + r"\_zf97_verify.py",
    TOOLS + r"\_zf98_verify.py",
    TOOLS + r"\_zf100_verify.py",
    TOOLS + r"\_zf100_recipe_guard.py",
    TOOLS + r"\_zf101_verify.py",
    TOOLS + r"\_zf101_gates.ps1",
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
        print(u"  [STOP] 备份根已存在：%s" % BK)
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
    print(u"  改前配方 %d 份" % len(cur))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
