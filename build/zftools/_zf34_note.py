# -*- coding: utf-8 -*-
"""重写 zf34_pre\\_说明.txt。

⚠ 上一版是用 PowerShell 的**双引号 here-string** 写的，正文里我用了 Markdown 反引号
   （`needs_stone_tool.json`）—— 而 PowerShell 双引号串里**反引号是转义符**，
   于是 `` `n `` 变成了换行、其余反引号被吞掉，正文被写坏（"本目录\\needs_stone_tool.json"
   变成"本目录<换行>eeds_stone_tool.json"）。
   ⇒ 凡是要写带反引号的文本，**别用 PowerShell 双引号串**，改用 Python（本脚本）或单引号 here-string。

本脚本用 Python 的三引号原文书写，反引号与反斜杠都按字面处理。
"""
import io

BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf34_pre"

txt = r"""ZF34：6 个装饰方块落地（中文贴图改名 + 注册 + 标签 + 掉落表）
========================================================
备份时刻：2026-09-19 01:2x（**动手之前**建的）
备份副本自身的 SHA256 见 `_sha256.txt`（那是**改前**快照，已逐份复核）。

用户原话
--------
  1)「那几个金属块什么的是不是没加」
  2)（我给出 id 方案并问定位后）「就用上面这套 id，直接做」+「就是普通装饰 后面用于组合多方快结构的机器」

做了什么
--------
  · 6 个方块 id（我提议、用户点头）：
      common_metal_block / advanced_metal_block / stable_metal_block /
      heat_resistant_metal_block / heater / heat_sink
    中文名原样进 lang 显示名（`block.potato_s_t.<id>`），**贴图文件同时改名成 ASCII**
    —— 中文不能当 ResourceLocation（反汇编取证见档案 §4.24）。
    改名前后 SHA256 逐一相等：只改名，一个像素都没动。
  · 性质对齐原版铁块：strength(5.0F, 6.0F) + SoundType.METAL + requiresCorrectToolForDrops()
    ⇒ 同步登记两张原版标签：mineable/pickaxe（27→33）、needs_stone_tool（3→9）
  · 掉落表走 JSON（原版 iron_block 那种：survives_explosion + 掉自己）
    ⚠ 本项目**机器**走的是方块类里覆写 getDrops，没有 JSON 掉落表 —— 两条路都对，别混（§6.14）
  · **不加配方、不挂 c: 标签**（用户说"先不加配方"；既定规则默认兼容范围只有粗矿/矿石/锭）

改前 / 改后 对照
----------------
  *.java / *.json              —— 改前（本目录根）
  改后_<同名>                   —— 改后
  新增文件\<相对路径>            —— 24 个新 JSON + 生成脚本（**保留目录结构**：
                                   因为 block model 与 item model 同名，平铺会互相覆盖）
  _改前_PotatoST-0.10.jar      —— 改前成品（SHA1 8dcf1a86…，本次作废）
  _改后_PotatoST-0.10.jar      —— 改后成品（SHA1 c7a9abd1…）
  _素材\                        —— 6 张**改名前**的中文名 PNG + 用户原始 webp 素材

验证到哪一步
------------
  [x] build：BUILD SUCCESSFUL；jar 内 24 个新 JSON + 6 张贴图逐条确认在包
  [x] 中文名条目在 jar 内**归零**
      （改名前 build\resources\main 里还留着 6 个陈旧副本，已手动清掉再打包）
  [x] 临时探针 BlockRegCheck 在真 runServer 上量行为：**54 项全 [OK]**
      （含"木镐不算正确工具""空手不算"两条反向断言）
      取证：build\zftools\check\zf34_方块注册取证.log
  [x] runServer：Loaded 1303 recipes（**没变**，这 6 个块不带配方）、Done (0.440s)、零 ERROR
  [x] 六项交付检查：Audit 失败 0 / 提示 4；LangCheck 4×167 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 **8→2**；JsonCheck 非法 0
  [x] 探针已从源码树删除（BlockRegCheck.java + PotatoST 里的注册行）
      产物 jar 内 BlockRegCheck 条目数 = 0
  [ ] **游戏内未验**：贴图对不对、能不能挖出东西、创造页里有没有 —— 清单在档案 §9「0.10 ZF34」

回退办法
--------
  删 `新增文件\` 里的 24 个 JSON，再把本目录根部的 9 个改前副本 + 开发档案.md
  覆盖回原来的相对路径（对照 `_sha256.txt` 的清单）；
  6 张贴图从 `_素材\` 取回并改回中文名。成品 jar 用 `_改前_PotatoST-0.10.jar`。

⚠ 诚实记录一：探针第一版是错的
------------------------------
  拿 `Block.getDrops` 去验工具等级 ⇒ 12 项 [FAIL]，全是探针自己的锅。
  那道门在 ServerPlayerGameMode → BlockState.canHarvestBlock → IBlockExtension.canHarvestBlock
  → EventHooks.doPlayerHarvestCheck → Player.hasCorrectToolForDrops，**不在掉落表里**。
  详见档案 §4.25。

⚠ 诚实记录二：备份漏了一个待改文件（事后补齐）
----------------------------------------------
  **漏的是 `src\main\resources\data\minecraft\tags\block\needs_stone_tool.json`。**
  我列"即将改动的文件"时是凭记忆写的，pickaxe.json 在、它不在。
  这正是 §10 记着的老毛病 —— ZF30 漏过 StatusLampPart.java，这次又漏一个。

  补法：从 `_改前_PotatoST-0.10.jar`（改前已发布的成品）里把
  `data/minecraft/tags/block/needs_stone_tool.json` 原样取出来，落到本目录
  `needs_stone_tool.json`。
  可靠性依据：**已发布产物就是权威原件**（同 §4.22 用发布 jar 重建 zf29_pre 的做法）。
  交叉验证：重建件 7 行、当前源文件 13 行，**只差我加的那 6 行**；
  且改前独有的行只有 `"potato_s_t:deepslate_manganese_ore"`（它因为我追加了逗号而变化）
  ⇒ 差异正好等于本次改动，不多不少。

  另外 `src\main\java\com\potatost\mod\PotatoST.java` 本阶段也被动过
  （加了一行临时探针注册 `BlockRegCheck.register();`，验完已删），**净变化为零**，
  所以没进本目录的改前清单；一并说明。

⚠ 诚实记录三：写这份说明时踩的 PowerShell 坑
--------------------------------------------
  上一版 `_说明.txt` 是我用 PowerShell 的**双引号 here-string** 写的，正文里带了 Markdown 反引号。
  PowerShell 双引号串里**反引号是转义符** ⇒ `` `n `` 变成换行、其余反引号被吞，
  正文被写坏（"落到本目录\needs_stone_tool.json" 变成两行且 `n` 丢失）。
  本文件改用 Python 三引号原文重写。**要写带反引号的文本就别用 PowerShell 双引号串。**
"""

io.open(BK + r"\_说明.txt", "w", encoding="utf-8", newline="\r\n").write(txt)
print("已用 Python 重写 _说明.txt")
print("字节数:", len(txt.encode("utf-8")))
