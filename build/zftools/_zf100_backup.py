# -*- coding: utf-8 -*-
u"""_zf100_backup.py —— ZF100 **动手前**的改前件（§10）

用户原话（一条）：

  「前面那几个没配方的机器你看着加吧 可以略微难一点 参考别的」

⇒ 给**一直没配方**的那几件补合成配方（我定的图纸，照现有配方的手感与价位）：

  ① `lithium_battery` 三元聚合物锂电池（机器，ZF02 就注册了、从没配方）
  ② `electric_blast_furnace` 电力高炉控制器（ZF39 就注册了、从没配方）
  ③ `wrench` 扳手（ZF41 就注册了、从没配方 —— 档案 §12.9 自己写着"只能创造取"）
  ④ `advanced_metal_block` 高级金属块（ZF34 起就没配方）
  ⑤ `stable_metal_block` 稳定金属块（ZF34 起就没配方）

⚠ **本轮会动一行机器代码**：电力高炉的成型判定 `ElectricBlastFurnaceStructure.matches`。
   理由：`ElectricBlastFurnaceBlock.useWithoutItem` 里那条"从物品摆出来的裸控制器 + 空手 Shift"
   的成型路**本来就在**，但锚点那格被写死要原版高炉 ⇒ 那条路永远走不通。
   不放开它，新配方的产物就是个**摆下去没用的方块**（陷阱）。放开后两条路都能装：
   老路（围着原版高炉搭 + 对着高炉 Shift 右键）不动，新路（摆自己造的主控 + 围着它搭 + 对着主控 Shift 右键）。

会动到的：
  · `_zf45_recipes.py`（配方生成器表，加 5 条 —— 白拿"id 真实存在"的机械核对）
  · `ElectricBlastFurnaceStructure.java`（锚点接受两种方块）
  · `PotatoST.java`（探针挂钩，跑完摘掉）
  · 6 个往轮校验脚本（活体数字 38 → 43 + 新增配方名单）
  · `_zf78_falsify.py`（下一轮的刀）+ `_zf99_gates.ps1`（下一轮门的模板）
  · 3 份文档（开发档案 / 贴图清单 / 英文公告 —— 后两份只是同步清点）
  · 旧成品 jar 与 `.sha1`
  · 另存一份 `recipe_before.txt` = **改前配方目录的 45 个文件名**（用来证明"本轮只新增、没改旧"）
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
BK = r"C:\PotatoST救援\zf100_pre"
JAVA = r"src\main\java\com\potatost\mod"
RDIR = r"src\main\resources\data\potato_s_t\recipe"
FILES = [
    r"build\zftools\_zf45_recipes.py",
    JAVA + r"\ElectricBlastFurnaceStructure.java",
    JAVA + r"\PotatoST.java",
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf73_repro.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"build\zftools\_zf95_verify.py",
    r"build\zftools\_zf96_verify.py",
    r"build\zftools\_zf97_verify.py",
    r"build\zftools\_zf99_gates.ps1",
    r"docs\开发档案.md",
    r"docs\UpdateAnnouncement_EN.md",
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

    # 改前配方目录的**文件名清单**：本轮只准新增，不许改名/删旧（ZF95 立的口径）
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
