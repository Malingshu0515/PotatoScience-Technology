# -*- coding: utf-8 -*-
"""ZF35 备份收尾：新增文件（保留目录结构）+ 改后副本 + _说明.txt + 改后成品 jar。

⚠ 文本一律用 Python 三引号原文写 —— 不用 PowerShell 双引号串（那里的反引号是转义符，
   ZF34 因此把 `_说明.txt` 写坏过一次，见 §8）。
"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf35_pre"
BID = "wiring_block"

NEW_FILES = [
    r"src\main\resources\assets\potato_s_t\blockstates\%s.json" % BID,
    r"src\main\resources\assets\potato_s_t\models\block\%s.json" % BID,
    r"src\main\resources\assets\potato_s_t\models\item\%s.json" % BID,
    r"src\main\resources\data\potato_s_t\loot_table\blocks\%s.json" % BID,
    r"src\main\resources\assets\potato_s_t\textures\block\%s.png" % BID,
]

CHANGED = [
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"src\main\resources\data\minecraft\tags\block\mineable\pickaxe.json",
    r"src\main\resources\data\minecraft\tags\block\needs_stone_tool.json",
    r"docs\开发档案.md",
]

dst_new = os.path.join(BK, "新增文件")
for rel in NEW_FILES:
    dst = os.path.join(dst_new, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(os.path.join(PROJ, rel), dst)

for s in ("_zf35_apply.py", "_zf35_texture.py", "_zf34_apply.py", "_zf34_tags.py",
          "_zf34_archive.py", "_zf34_note.py"):
    p = os.path.join(PROJ, "build", "zftools", s)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(dst_new, s))

for rel in CHANGED:
    shutil.copy2(os.path.join(PROJ, rel), os.path.join(BK, "改后_" + os.path.basename(rel)))

shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))


def sha(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


bad = 0
for rel in NEW_FILES:
    if sha(os.path.join(PROJ, rel)) != sha(os.path.join(dst_new, rel)):
        print("[FAIL] 副本不一致: " + rel)
        bad += 1
print("新增文件 %d 个，副本校验不一致 %d 个" % (len(NEW_FILES), bad))

txt = r"""ZF35：接线块（wiring_block）
========================================================
备份时刻：2026-09-19 01:3x（**动手之前**建的）

用户原话
--------
  「再加个接线块」+ 一张 `接线块_001.png`（160×160 webp）

做了什么
--------
  · id = **wiring_block**（我按 ZF34 的先例定的 ASCII id —— 中文不能当 ResourceLocation，
    见档案 §4.24 的反汇编取证）。中文"接线块"进 lang 显示名。
  · 定位沿用 ZF34 那 6 个（用户当时说「就是普通装饰 后面用于组合多方快结构的机器」）：
    普通完整方块、无方块实体、无功能、**不加配方、不挂 c: 标签**。
  · 性质：strength(5.0F, 6.0F) + SoundType.METAL + requiresCorrectToolForDrops()
    ⇒ 同步登记两张原版标签：mineable/pickaxe（33→34）、needs_stone_tool（9→10）
  · 贴图：160×160 webp **面积平均降到 16×16** → `wiring_block.png`（408 字节，16×16）
  · lang 各 167→**168** 键

通道顺序（§4.23 的做法：先打原始字节，再判）
--------------------------------------------
  `_zf35_decode.ps1` 用 WPF BitmapDecoder → Bgra32 → CopyPixels 导出裸像素，并**原样打印**：
      最饱和不透明像素（字节序原样）= (0,187,255,255)
  · 按 R,G,B,A 读 ⇒ (0,187,255) = 青蓝
  · 按 B,G,R,A 读 ⇒ (255,187,0) = 橙
  你发来的预览图里那道框是**橙黄**的 ⇒ **这份裸像素是 BGRA**，写 PNG 时换回 R,G,B。
  落盘后**回读 PNG 再断言**：最饱和像素 (252,187,10)、暖 36 / 冷 0、均色 (208,203,186)
  —— 4 条断言全过（"最饱和像素必须 R>G>B"这条是能失败的）。

改前 / 改后 对照
----------------
  *.java / *.json        —— 改前（本目录根，共 9 个，清单写在 `_sha256.txt` 顶部）
  改后_<同名>             —— 改后
  新增文件\<相对路径>      —— 4 个新 JSON + 1 张贴图 + 生成脚本（保留目录结构）
  _改前_PotatoST-0.10.jar —— 改前成品（SHA1 c7a9abd1…，本次作废）
  _改后_PotatoST-0.10.jar —— 改后成品（SHA1 4c065d20…）
  _素材\                  —— 用户原始 `接线块.webp` 与解出的裸像素 `接线块.rgba`

验证到哪一步
------------
  [x] 探针 BlockRegCheck（扩到 7 个 id）在真 runServer 上 **63 项全 [OK]**
      （含"木镐不算正确工具""空手不算"两条反向断言）
      取证：build\zftools\check\zf35_方块注册取证.log
  [x] runServer：Loaded 1303 recipes（**不变**）、Done (0.492s)、零 ERROR
  [x] 贴图回读断言 4 条全过（见上）
  [x] 六项交付检查：Audit 失败 0 / 提示 4；LangCheck 4×168 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2（模型 109 / blockstate 34 / 注册物品 68 / 贴图 72，各 +1）；
      JsonCheck 非法 0
  [x] 探针已从源码树删除（BlockRegCheck.java + PotatoST 里的注册行）；产物 jar 内
      BlockRegCheck 条目 = 0、中文名条目 = 0
  [ ] **游戏内未验**：创造页里有没有、贴图对不对、能不能挖出东西 —— 清单在档案 §9「0.10 ZF35」

回退办法
--------
  删 `新增文件\` 里的 5 个文件，再把本目录根部的 9 个改前副本覆盖回原来的相对路径
  （对照 `_sha256.txt` 顶部的清单），成品 jar 用 `_改前_PotatoST-0.10.jar`。

本阶段没再漏文件（ZF34 的教训已落成机制）
------------------------------------------
  本目录的 `_sha256.txt` 顶部**就是**"本阶段将修改的既有文件清单"，
  备份脚本跑完会**逐条交叉核对**"清单条数 vs 备份根目录里的改前副本数"，
  数量对不上直接报错退出 —— ZF34 凭记忆列清单漏了 needs_stone_tool.json，这次 9/9 通过。
"""

io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(txt)
print("已写 _说明.txt")
print("新增文件目录: " + dst_new)
