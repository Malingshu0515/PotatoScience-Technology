# -*- coding: utf-8 -*-
u"""_zf96_backup.py —— ZF96 **动手前**的改前件（§10）

本轮（用户原话一条到底）：

  「加一个 加氢脱硫反应仓 GUI 一个氢气罐 左侧放沥青 每16个沥青 消耗1000mB氢气 10s  产出一个 硫
    配方；【铁锭】【银锭】【银锭】，【铁块】【高压气罐】【铁块】，【红石块】【一般金属块】【红石块】」

⇒ 两件事：
  ① **新机器「加氢脱硫反应仓」**（`hydrodesulfurization_chamber`）：界面里一个氢气罐 +
     左侧沥青槽；机器配方 = 16 沥青 + 1000 mB 氢气 → 10 秒 → 1 硫；
  ② **新物品「硫」**（本工程以前**根本没有**这个物品，是这一轮新加的）+
     机器的合成配方（九宫格：铁锭/银锭/银锭 · 铁块/高压气罐/铁块 · 红石块/一般金属块/红石块）。

会动到的：
  · 新建 4 个 Java 文件（方块 / 方块实体 / 菜单 / 界面）+ 1 个硫物品不需要新类（ModItems 里注册）
  · 改 8 个既有 Java 文件（ModItems / ModBlocks / ModMenus / PotatoST / PotatoSTClient /
    MachineRecipes / PotatoSTJeiPlugin / gui\\parts\\StatusLampPart）
  · 新建贴图 3 张（机器侧面 / 机器顶面 / 硫）+ 模型 3 份 JSON + 合成配方 1 份 JSON
  · 四份 lang（+键）
  · **活体数字一起改**：272 键 → 284、定形配方 35 → 36、JEI 分类 8 → 9
    ⇒ 10 份往轮校验脚本要跟着改（_zf71/_zf73_repro/_zf73/_zf75/_zf78/_zf79/_zf80/_zf81/_zf82/_zf93）
    + `_zf95_verify.py`（它钉着"改前 36 份配方一份不少、本轮只新增 5 份"）
  · `_zf78_falsify.py`（VERIFIERS 名单 + 新刀）
  · 三份文档 + 旧成品 jar 与 `.sha1`
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
BK = r"C:\PotatoST救援\zf96_pre"
JAVA = r"src\main\java\com\potatost\mod"
FILES = [
    # ---- 要改的既有 Java ----
    JAVA + r"\ModItems.java",
    JAVA + r"\ModBlocks.java",
    JAVA + r"\ModMenus.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\PotatoSTClient.java",
    JAVA + r"\MachineRecipes.java",
    JAVA + r"\client\jei\PotatoSTJeiPlugin.java",
    JAVA + r"\client\gui\parts\StatusLampPart.java",
    # ---- 四份语言（活体键数）----
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    # ---- 往轮校验脚本（活体数字：键数 / 配方数 / JEI 分类 / 配方名单）----
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf73_repro.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf75_verify.py",
    r"build\zftools\_zf78_verify.py",
    r"build\zftools\_zf79_verify.py",
    r"build\zftools\_zf80_verify.py",
    r"build\zftools\_zf81_verify.py",
    r"build\zftools\_zf82_verify.py",
    r"build\zftools\_zf93_verify.py",
    r"build\zftools\_zf95_verify.py",
    r"build\zftools\_zf78_falsify.py",
    r"build\zftools\_zf95_gates.ps1",
    # 本轮要**用**的公共件（只读，但按 ZF92 的教训一起留档：那轮动手后才发现改过它）
    r"build\zftools\_zf66_png.py",
    # ---- 文档 ----
    r"docs\开发档案.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    # ---- 旧成品 ----
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
    # 顺手记下"改前配方目录"的清单（本轮只会**新增**，不会改旧的 —— 新增前先留一份名字表）
    rdir = os.path.join(ROOT, r"src\main\resources\data\potato_s_t\recipe")
    names = sorted(n for n in os.listdir(rdir) if n.endswith(".json"))
    dst = os.path.join(BK, "recipe_before.txt")
    io.open(dst, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(names) + u"\n")
    ok += 1
    lines.append(u"%s  %10d  %s" % (sha1(dst), os.path.getsize(dst), u"recipe_before.txt（%d 份）" % len(names)))
    # 顺手记下"改前贴图目录"的清单（本轮要新增 3 张，旧的一张都不许动）
    tdir = os.path.join(ROOT, r"src\main\resources\assets\potato_s_t\textures")
    tex = []
    for sub in ("block", "item"):
        for n in sorted(os.listdir(os.path.join(tdir, sub))):
            tex.append(u"%s/%s  %s" % (sub, n, sha1(os.path.join(tdir, sub, n))))
    dst = os.path.join(BK, "textures_before.txt")
    io.open(dst, "w", encoding="utf-8", newline=u"\n").write(u"\n".join(tex) + u"\n")
    ok += 1
    lines.append(u"%s  %10d  %s" % (sha1(dst), os.path.getsize(dst), u"textures_before.txt（%d 张）" % len(tex)))
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"  配方目录改前 %d 份；贴图目录改前 %d 张" % (len(names), len(tex)))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
