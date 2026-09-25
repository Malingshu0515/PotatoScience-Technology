# -*- coding: utf-8 -*-
"""ZF34 备份收尾：把新增文件（保留目录结构）与改后副本归档，并写 _说明.txt。

⚠ 新增文件里 **block model 与 item model 同名**（都叫 `<id>.json`），
   平铺到同一个目录会互相覆盖 —— 所以必须**保留相对路径**。
"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf34_pre"

IDS = ["common_metal_block", "advanced_metal_block", "stable_metal_block",
       "heat_resistant_metal_block", "heater", "heat_sink"]

NEW_FILES = []
for i in IDS:
    NEW_FILES.append(r"src\main\resources\assets\potato_s_t\blockstates\%s.json" % i)
    NEW_FILES.append(r"src\main\resources\assets\potato_s_t\models\block\%s.json" % i)
    NEW_FILES.append(r"src\main\resources\assets\potato_s_t\models\item\%s.json" % i)
    NEW_FILES.append(r"src\main\resources\data\potato_s_t\loot_table\blocks\%s.json" % i)

CHANGED = [
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json",
    r"src\main\resources\data\minecraft\tags\block\needs_stone_tool.json",
]

dst_new = os.path.join(BK, "新增文件")
for rel in NEW_FILES:
    src = os.path.join(PROJ, rel)
    dst = os.path.join(dst_new, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)

# 生成脚本也留档
for s in ("_zf34_apply.py", "_zf34_tags.py", "_zf34_backup.ps1"):
    p = os.path.join(PROJ, "build", "zftools", s)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(dst_new, s))

# 改后副本（拍平，命名加前缀）
for rel in CHANGED + [r"docs\开发档案.md"]:
    src = os.path.join(PROJ, rel)
    shutil.copy2(src, os.path.join(BK, "改后_" + os.path.basename(rel)))

shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))


def sha(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


# 自检：新增文件副本必须与源逐字节一致；block/item 模型不能串
bad = 0
for rel in NEW_FILES:
    a = sha(os.path.join(PROJ, rel))
    b = sha(os.path.join(dst_new, rel))
    if a != b:
        print("[FAIL] 副本不一致: " + rel)
        bad += 1
print("新增文件 %d 个，副本校验不一致 %d 个" % (len(NEW_FILES), bad))

bm = io.open(os.path.join(dst_new, r"src\main\resources\assets\potato_s_t\models\block\heater.json"),
             encoding="utf-8").read()
im = io.open(os.path.join(dst_new, r"src\main\resources\assets\potato_s_t\models\item\heater.json"),
             encoding="utf-8").read()
print("block/item 模型没串: " + str("cube_all" in bm and "cube_all" not in im))

txt = u"""ZF34：6 个装饰方块落地（中文贴图改名 + 注册 + 标签 + 掉落表）
========================================================
备份时刻：2026-09-19 01:2x（**动手之前**建的）
备份副本自身的 SHA256 见 `_sha256.txt`（那是**改前**快照，已逐份复核）。

用户原话
--------
  1)「那几个金属块什么的是不是没加」
  2)（我问 id 与定位后）「就用上面这套 id，直接做」+「就是普通装饰 后面用于组合多方快结构的机器」

做了什么
--------
  · 6 个方块 id（我提议、用户点头）：common_metal_block / advanced_metal_block /
    stable_metal_block / heat_resistant_metal_block / heater / heat_sink
  · 中文名原样进 lang 显示名；**贴图文件同时改名成 ASCII**
    （中文不能当 ResourceLocation，反汇编取证见档案 §4.24）
    改名前后 SHA256 逐一相等 —— 只改名，没改像素
  · 性质对齐原版铁块：strength(5.0F, 6.0F) + SoundType.METAL + requiresCorrectToolForDrops()
    ⇒ 同步登记两张原版标签：mineable/pickaxe（27→33）、needs_stone_tool（3→9）
  · 掉落表走 JSON（原版 iron_block 那种：survives_explosion + 掉自己）
    ⚠ 本项目**机器**走的是方块类里覆写 getDrops，没有 JSON 掉落表 —— 两条路都对，别混
  · **不加配方、不挂 c: 标签**（用户说"先不加配方"；既定规则默认兼容范围只有粗矿/矿石/锭）

改前 / 改后 对照
----------------
  `*.java` / `*.json`          —— 改前（本目录根）
  `改后_<同名>`                 —— 改后
  `新增文件/<相对路径>`          —— 30 个新 JSON + 生成脚本（**保留目录结构**，
                                  因为 block model 与 item model 同名，平铺会互相覆盖）
  `_改前_PotatoST-0.10.jar`    —— 改前成品（SHA1 8dcf1a86…，本次作废）
  `_改后_PotatoST-0.10.jar`    —— 改后成品（SHA1 c7a9abd1…）
  `_素材\`                      —— 6 张**改名前**的中文名 PNG + 用户原始 webp 素材

验证到哪一步
------------
  [x] build：BUILD SUCCESSFUL；jar 内 6×5=30 个新 JSON + 6 张贴图逐条确认在包
  [x] 中文名条目在 jar 内**归零**（改名前 build\\resources\\main 里有 6 个陈旧副本，已手动清掉）
  [x] 临时探针 `BlockRegCheck` 在真 runServer 上量行为：**54 项全 [OK]**
      （含"木镐不算正确工具""空手不算"两条反向断言）取证 build\\zftools\\check\\zf34_方块注册取证.log
  [x] runServer：Loaded 1303 recipes（**没变**，这 6 个块不带配方）、Done (0.440s)、零 ERROR
  [x] 六项交付检查：Audit 失败 0 / 提示 4；LangCheck 4×167 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 **8→2**；JsonCheck 非法 0
  [x] 探针已从源码树删除（`BlockRegCheck.java` + `PotatoST` 里的注册行），
      产物 jar 内 `BlockRegCheck` 条目数 = 0
  [ ] **游戏内未验**：贴图对不对、能不能挖出东西、创造页里有没有 —— 清单在档案 §9「0.10 ZF34」

回退办法
--------
  删 `新增文件\\` 里的 30 个 JSON，再把本目录根部的 8 个改前副本 + `docs\\开发档案.md`
  覆盖回去（各自放回原来的相对路径，对照 `_sha256.txt` 的清单）；
  6 张贴图从 `_素材\\` 取回并改回中文名。成品 jar 用 `_改前_PotatoST-0.10.jar`。

⚠ 诚实记录
----------
  探针 `BlockRegCheck` **第一版是错的**：拿 `Block.getDrops` 去验工具等级，
  12 项 [FAIL] 全是探针自己的锅（那道门在 ServerPlayerGameMode → canHarvestBlock
  → Player.hasCorrectToolForDrops，不在掉落表里）。详见档案 §4.25。
"""
io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(txt)
print("已写 _说明.txt")
print("新增文件副本目录: " + dst_new)
