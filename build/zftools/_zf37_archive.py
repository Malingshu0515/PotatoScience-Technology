# -*- coding: utf-8 -*-
"""ZF37 备份收尾：新增配方 + 改后副本 + _说明.txt + 改后成品 jar。
文本一律用 Python 三引号原文写（不用 PowerShell 双引号串，那里的反引号是转义符，§8）。
"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf37_pre"

NEW_FILES = [
    r"src\main\resources\data\potato_s_t\recipe\wiring_block.json",
    r"src\main\resources\data\potato_s_t\recipe\common_metal_block.json",
]

dst_new = os.path.join(BK, "新增文件")
for rel in NEW_FILES:
    dst = os.path.join(dst_new, os.path.basename(rel))
    shutil.copy2(os.path.join(PROJ, rel), dst)

for s in ("_zf37_backup.ps1", "_zf37_archive.py"):
    p = os.path.join(PROJ, "build", "zftools", s)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(dst_new, s))

shutil.copy2(os.path.join(PROJ, r"docs\开发档案.md"),
             os.path.join(BK, "改后_开发档案.md"))
shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))


def sha(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


bad = 0
for rel in NEW_FILES:
    if sha(os.path.join(PROJ, rel)) != sha(os.path.join(dst_new, os.path.basename(rel))):
        print("[FAIL] 副本不一致: " + rel)
        bad += 1
print("新增文件 %d 个，副本校验不一致 %d 个" % (len(NEW_FILES), bad))

txt = r"""ZF37：接线块配方 + 一般金属块配方
========================================================
备份时刻：2026-09-19 01:5x（**动手之前**建的）

用户原话
--------
  「接线块配方；中间一个铁块 上下左右各一个接线端子 输出2个接线块
   （以后多方快结构只有接线块的地方可以用端子传输电力）
   一般金属块；一圈铁锭围上一个铝锭」

做了什么
--------
  新配方 JSON ×2（**没有动任何 Java / 贴图 / 标签**）
    · `wiring_block.json`        `" T " / "TIT" / " T "`   T=potato_s_t:terminal  I=minecraft:iron_block
                                 result = potato_s_t:wiring_block × **2**
    · `common_metal_block.json`  `"III" / "IAI" / "III"`   I=#c:ingots/iron       A=#c:ingots/aluminum
                                 result = potato_s_t:common_metal_block × 1
  两条的 category 都取 `misc`（本项目 13 条里 9 条是 misc）。
  铁锭 / 铝锭**都走 c: 通用标签**（既定规则：矿物 / 合金 / 锭默认兼容别的 mod）。
  铁块用原版 `minecraft:iron_block`（铁"块"不在默认兼容范围内，而且原版方块本来就全 mod 共用）。

验证到哪一步
------------
  [x] RecipeCheck：两条都 `[OK] 尺寸 3x3`；`#c:ingots/iron` 与 `#c:ingots/aluminum` 都能解析；
      定形配方通过 7 → **9**、跳过 6、失败 0
  [x] runServer：`Loaded 1303 → **1305**`（**正好 +2**）、`Done (0.407s)`、零 ERROR
  [x] jar 内配方 JSON 13 → **15**，两条逐一确认在包
  [x] 七项交付检查：Audit 失败 0 / 提示 4；LangCheck 4×168 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 产物 `release\PotatoST-0.10.jar` SHA1 `9ce9acd0…`（1,991,112 B）；
      **上一版 `402d3555…` 作废**
  [ ] **游戏内未验**：两条配方在工作台里合不合得出来、接线块是不是出 2 个 —— 档案 §9「0.10 ZF37」

顺带记下的未来需求（**本次不动**）
----------------------------------
  「以后多方快结构只有接线块的地方可以用端子传输电力」
  ⇒ 做多方块结构时，"这一格能不能接电"的判据是**那一格有没有接线块**。
  `wiring_block` = 允许接电的占位，`terminal` = 接口。结构校验要同时看**类型与相对位置**，别只看数量。

回退办法
--------
  删 `新增文件\` 里的 2 个配方 JSON 即回到改前；档案用 `_改前_...` 那份
  （本目录根的 `开发档案.md`）覆盖回去；成品 jar 用 `_改前_PotatoST-0.10.jar`。

本阶段没漏文件
--------------
  本阶段只改 1 个既有文件（档案），清单 1 项交叉核对通过。
"""

io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(txt)
print("已写 _说明.txt")
