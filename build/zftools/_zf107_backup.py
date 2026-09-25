# -*- coding: utf-8 -*-
u"""_zf107_backup.py —— ZF107 **动手前**的改前件（§10）

用户原话：
  「你自己发挥一下 把进度（成就）做一点 最好能引导一下玩家 全流程
    但也不是非得一个步骤就冒一个成就那么烦琐」

本轮会动到的：
  · 数据：`data/potato_s_t/advancement/` —— 3 份老成就**改**（根节点换成"第一台机器"、
    两处父链改挂到 `first_power`）+ 新增 24 份
  · 资源：四语言各 +48 键（24 个成就 × 标题/说明）
  · Java：`PotatoST.java` **只加行**（挂本轮探针 `Zf107Check`）
  · 工具：本轮新脚本 + 下一轮门的模板；往轮校验器里的"活体数字"（350 → 398）
  · 文档 2 份 + 旧成品 jar 与 `.sha1`

⚠ 备份根已存在就直接退出（绝不覆盖上一次的改前件）。
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
BK = r"C:\PotatoST救援\zf107_pre"
JAVA = r"src\main\java\com\potatost\mod"
TOOLS = r"build\zftools"
DATA = r"src\main\resources\data\potato_s_t"
RES = r"src\main\resources"

FILES = [
    # ---- Java 汇合点（只加行，§4.7）
    JAVA + r"\PotatoST.java",
    # ---- 会被本轮的"活体数字"重定目标碰到的往轮校验器
    TOOLS + r"\_zf71_verify.py",
    TOOLS + r"\_zf73_verify.py",
    TOOLS + r"\_zf73_repro.py",
    TOOLS + r"\_zf75_verify.py",
    TOOLS + r"\_zf78_verify.py",
    TOOLS + r"\_zf79_verify.py",
    TOOLS + r"\_zf80_verify.py",
    TOOLS + r"\_zf95_verify.py",
    TOOLS + r"\_zf97_verify.py",
    TOOLS + r"\_zf100_verify.py",
    TOOLS + r"\_zf100_recipe_guard.py",
    TOOLS + r"\_zf101_verify.py",
    TOOLS + r"\_zf102_verify.py",
    TOOLS + r"\_zf103_verify.py",
    # ---- 门脚本模板（下一轮从这两份改；ZF103 那轮是复用 _zf102_gates.ps1，
    #      所以最新的一套现成模板是 ZF104 的；假刀同理取最新的 ZF105）
    TOOLS + r"\_zf104_gates.ps1",
    TOOLS + r"\_zf104_gatecount.py",
    TOOLS + r"\_zf105_falsify.py",
    # ---- 成就数据：会改的 3 份老成就
    DATA + r"\advancement\new_beginning.json",
    DATA + r"\advancement\clean_energy.json",
    DATA + r"\advancement\stronger_power.json",
    # ---- 四语言
    RES + r"\assets\potato_s_t\lang\zh_cn.json",
    RES + r"\assets\potato_s_t\lang\en_us.json",
    RES + r"\assets\potato_s_t\lang\ja_jp.json",
    RES + r"\assets\potato_s_t\lang\ru_ru.json",
    # ---- 文档 + 旧成品
    r"docs\开发档案.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

# 本轮开始前"盘上还没有"的路径：回退时一律删除
NEW = [DATA + r"\advancement\%s.json" % n for n in (
    "crushing", "pressing", "wiring", "first_power", "capacitor",
    "blast_furnace", "steel", "titanium", "electrolyzer", "gas_handling",
    "alloy_smelter", "light_alloy", "hard_alloy", "stable_block",
    "titanium_tools", "oil", "distillation", "fuel", "sulfur", "ammonia",
    "combustion", "acid", "music_disc_anvil", "music_disc_jasmine")]

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
    pre = [u"%s  %s" % (u"存在(异常)" if os.path.exists(os.path.join(ROOT, p)) else u"不存在(正常)", p)
           for p in NEW]
    io.open(os.path.join(BK, u"_zf107_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(
        u"本轮开始前，下列路径的**存在性**（回退时：不存在的一律删除；存在的别动）\n"
        + u"\n".join(pre) + u"\n")
    bad = [p for p in NEW if os.path.exists(os.path.join(ROOT, p))]
    if bad:
        fails.append(u"本轮要新建的成就已经有同名文件：%s" % bad)
    # 成就目录的改前清单（回退时按这张表核对目录里"多出来的是谁"）
    adir = os.path.join(ROOT, DATA, u"advancement")
    listing = sorted(os.listdir(adir))
    io.open(os.path.join(BK, u"_advancement_before.txt"), "w", encoding="utf-8",
            newline=u"\n").write(
        u"改前 advancement 目录 %d 份：\n" % len(listing)
        + u"\n".join(listing) + u"\n")
    print(u"  改前 achievement 目录 %d 份：%s" % (len(listing), u", ".join(listing)))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
