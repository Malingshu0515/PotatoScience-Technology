# -*- coding: utf-8 -*-
u"""_zf79_backup.py —— ZF79 **动手前**的改前件（这次记得先抄：ZF78 漏过一次，见 §5 那行的自述）

本轮预计改动：
  · `PressRecipes.java`（配方表扩成"带输入数量"）
  · `HydraulicPressBlockEntity.java`（按数量消耗 + 新状态"材料不足"）
  · `client/HydraulicPressScreen.java`（新状态灯颜色/文案）
  · `ModBlocks.java` / `ModItems.java`（新方块 柏油块）
  · 四份 lang
  · `data/minecraft/tags/block/mineable/pickaxe.json`
  · `textures/block/electric_blast_furnace.png`（用户给的 256×256 新材质覆盖旧的生成器产物）
  · 用户原图 `textures/block/电力高炉.png`（原名件，存档用）
  · 往轮校验脚本（`_zf71_verify.py` 等）与四份文档
  · 成品 jar 与 `.sha1`

逐份核哈希；文件不在就记 MISS（不静默跳过）。
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
BK = r"C:\PotatoST救援\zf79_pre"

FILES = [
    r"src\main\java\com\potatost\mod\PressRecipes.java",
    r"src\main\java\com\potatost\mod\HydraulicPressBlockEntity.java",
    r"src\main\java\com\potatost\mod\client\HydraulicPressScreen.java",
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json",
    r"src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png",
    u"src\\main\\resources\\assets\\potato_s_t\\textures\\block\\电力高炉.png",
    r"build\zftools\_zf71_verify.py",
    r"build\zftools\_zf73_verify.py",
    r"build\zftools\_zf75_verify.py",
    r"build\zftools\_zf78_verify.py",
    r"docs\开发档案.md",
    r"docs\v0.11规划.md",
    r"docs\贴图清单.md",
    r"docs\UpdateAnnouncement_EN.md",
    r"release\PotatoST-0.11.jar",
    r"release\PotatoST-0.11.jar.sha1",
]

fails = []


def sha1(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def main():
    if os.path.isdir(BK):
        print(u"  [SKIP] 备份根已存在：%s（不覆盖）" % BK)
    lines = []
    ok = 0
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
    io.open(os.path.join(BK, "_sha1.txt"), "w", encoding="utf-8",
            newline=u"\n").write(u"\n".join(lines) + u"\n")
    print(u"改前件 %d 份 → %s" % (ok, BK))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
