# -*- coding: utf-8 -*-
u"""_zf111_backup.py —— ZF111 **动手前**的改前件（§10）

用户原话：
  「星璨钢加合金冶炼配方 下界合金锭+4高碳钢+钴锭+银锭+铜锭 再消耗1个深层钴矿石
    1个末影水晶 产出三个星璨钢钢 12000FE/t」

本轮会动到的：
  · Java **改** 3 个：`AlloySmelterRecipes`（加 Consume + 第三条配方）、
    `AlloySmelterBlockEntity`（消耗槽放开 + 每配方各带自己的耗时/耗电）、
    `MachineRecipes`（JEI 里把两样消耗品也画出来）
  · Java **新** 1 个：本轮临时探针 `Zf111Check.java`
  · 资源**改** 4 个：四语言里 `tooltip.potato_s_t.alloy_smelter` 的**末行**与
    `gui.potato_s_t.alloy_smelter.consume_slot` 的**值**（⚠ **不加/删键** ⇒ 键数仍是 408，
    17 份键数耦合的校验器一份都不用动）
  · 工具：本轮新脚本 + **全部常驻校验脚本**（一把全抄，不赌"我记得改过哪几份"）
  · 文档 2 份 + 旧成品 jar 与 `.sha1`

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
BK = r"C:\PotatoST救援\zf111_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"
RES = r"src\main\resources"

FILES = [
    JAVA + r"\AlloySmelterRecipes.java",
    JAVA + r"\AlloySmelterBlockEntity.java",
    JAVA + r"\MachineRecipes.java",
    RES + r"\assets\potato_s_t\lang\zh_cn.json",
    RES + r"\assets\potato_s_t\lang\en_us.json",
    RES + r"\assets\potato_s_t\lang\ja_jp.json",
    RES + r"\assets\potato_s_t\lang\ru_ru.json",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

NEW = [
    JAVA + r"\Zf111Check.java",
    TOOLS + r"\_zf111_verify.py",
    TOOLS + r"\_zf111_falsify.py",
    TOOLS + r"\_zf111_lang.py",
    TOOLS + r"\_zf111_docs.py",
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
    io.open(os.path.join(BK, u"_zf111_newfiles.txt"), "w", encoding="utf-8", newline=u"\n").write(
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
