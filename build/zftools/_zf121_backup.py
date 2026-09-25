# -*- coding: utf-8 -*-
u"""_zf121_backup.py —— ZF121 的改前件（§10：**先建备份，再动第一个字节**）

用户原话：「振金合金冶炼炉配方；1硬质钛合金+8热力金属+2高碳钢+3银锭+12金锭 粗振金+钻石+
2下界合金碎片+1红石粉 14500Fe/t 产出1振金」

⚠ **轮号说明**：`ZF120` 已经被**并行的那条线**（振金套：`_zf120_lang.py` / `_zf120_src.py` /
`ModVibraniumSet.java`…，lang 已 449 → 454）占用 ⇒ 本轮取 **ZF121**，绝不碰 `_zf120_*` 任何文件。

⚠ **共用文件**：四份 lang 里已经有并行那条线的 5 个振金套键（我核过：四语言键集合完全一致、
每份 454 键）。我本轮只**改一个值**（`tooltip.potato_s_t.alloy_smelter` 的脚注），
所以备份里存的是"2026-09-26 01:01 那一刻"的共用状态 —— 校验时按"相对这份备份只动了那一个值"判。

跑法：
    python build\\zftools\\_zf121_backup.py
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
BK = r"C:\PotatoST救援\zf121_pre"
JAVA = r"src\main\java\com\potatost\mod"
LANGD = r"src\main\resources\assets\potato_s_t\lang"
TAGS = r"src\main\resources\data\c\tags"
TOOLS = r"build\zftools"
CHECK = TOOLS + r"\check"

# 本轮**会改盘**的文件（一个都不能漏；§4.94 的教训：PotatoST.java 连着两轮漏抄）
FILES = [
    JAVA + r"\AlloySmelterRecipes.java",
    JAVA + r"\AlloySmelterBlockEntity.java",
    JAVA + r"\AlloySmelterMenu.java",
    JAVA + r"\MachineRecipes.java",
    JAVA + r"\PotatoST.java",
    JAVA + r"\client\AlloySmelterScreen.java",
    JAVA + r"\client\jei\MachineRecipeCategory.java",
    JAVA + r"\client\jei\PotatoSTJeiPlugin.java",
    LANGD + r"\zh_cn.json",
    LANGD + r"\en_us.json",
    LANGD + r"\ja_jp.json",
    LANGD + r"\ru_ru.json",
    TOOLS + r"\GenCommonTags.py",
    r"docs\开发档案.md",
    r"docs\多会话协作交接.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

# 整棵 c: 标签树（生成器会重写其中的 ingots.json 并新增 4 份）
for p in sorted(glob.glob(os.path.join(ROOT, TAGS, "**", "*.json"), recursive=True)):
    FILES.append(os.path.relpath(p, ROOT))

# 本轮开始前**应当不存在**的路径
NEW = ([TAGS + r"\item\ingots\hard_titanium_alloy.json",
        TAGS + r"\item\ingots\thermal_metal.json",
        TAGS + r"\item\hard_titanium_alloy_ingots.json",
        TAGS + r"\item\thermal_metal_ingots.json",
        CHECK + r"\Zf121Check.java"]
       + [TOOLS + r"\_zf121_%s.py" % s for s in
          ("tags", "java", "lang", "verify", "falsify", "docs", "gatesnap",
           "unprobe", "retarget", "backup")])

fails, notes, lines = [], [], []
ok = 0


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    global ok
    if os.path.isdir(BK):
        print(u"  [STOP] 备份根已存在：%s" % BK)
        return 1
    todo = list(FILES)
    # 全部常驻校验 / 反证 / 快照脚本（一把全抄，改前基线）
    for pat in ("_zf*_verify.py", "_zf*_falsify.py", "_zf*_gatesnap.py", "_zf*gates.ps1"):
        for p in sorted(glob.glob(os.path.join(ROOT, TOOLS, pat))):
            rel = os.path.relpath(p, ROOT)
            if rel not in todo:
                todo.append(rel)

    for rel in todo:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            fails.append(u"缺文件：%s" % rel)
            continue
        dst = os.path.join(BK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        b = sha1(src)
        shutil.copy2(src, dst)
        if b != sha1(dst):
            fails.append(u"%s：哈希不一致" % rel)
        else:
            ok += 1
            lines.append(u"%s  %10d  %s" % (b, os.path.getsize(dst), rel))

    # ---- 等级③ 回读证明：备份里的每一份都真的等于现在盘上那份 ----
    bad = []
    for rel in todo:
        src = os.path.join(ROOT, rel)
        dst = os.path.join(BK, rel)
        if os.path.exists(src) and os.path.exists(dst) and sha1(src) != sha1(dst):
            bad.append(rel)
    if bad:
        fails.append(u"回读不一致：%s" % u"、".join(bad))
    else:
        notes.append(u"回读证明：%d 份备份与盘上逐字节相同" % ok)

    # ---- 关键件点名（§4.94：漏抄过一次 PotatoST.java，这里硬点名）----
    MUST = [JAVA + r"\PotatoST.java", JAVA + r"\AlloySmelterRecipes.java",
            JAVA + r"\AlloySmelterBlockEntity.java", JAVA + r"\AlloySmelterMenu.java",
            JAVA + r"\MachineRecipes.java", TOOLS + r"\GenCommonTags.py"]
    for rel in MUST:
        if not os.path.exists(os.path.join(BK, rel)):
            fails.append(u"点名件没抄到：%s" % rel)
    notes.append(u"点名件 %d 份全在（含 PotatoST.java）" % len(MUST))

    io.open(os.path.join(BK, u"_zf121_newfiles.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"本轮开始前这些路径应当不存在：\n" + u"\n".join(NEW) + u"\n")
    io.open(os.path.join(BK, u"_sha1.txt"), "w", encoding="utf-8", newline=u"\n").write(
        u"\n".join(lines) + u"\n")
    print(u"\n".join(u"  [OK] " + n for n in notes))
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
