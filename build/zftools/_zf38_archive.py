# -*- coding: utf-8 -*-
"""ZF38 备份收尾：新增文件（保留目录结构）+ 改后副本 + _说明.txt + 改后成品 jar。
文本一律用 Python 三引号原文写（不用 PowerShell 双引号串，那里的反引号是转义符，§8）。
"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf38_pre"

NEW_FILES = [
    r"src\main\java\com\potatost\mod\LowGeneratorBlock.java",
    r"src\main\java\com\potatost\mod\LowGeneratorBlockEntity.java",
    r"src\main\java\com\potatost\mod\LowGeneratorMenu.java",
    r"src\main\java\com\potatost\mod\client\LowGeneratorScreen.java",
    r"src\main\resources\assets\potato_s_t\blockstates\low_generator.json",
    r"src\main\resources\assets\potato_s_t\models\block\low_generator.json",
    r"src\main\resources\assets\potato_s_t\models\item\low_generator.json",
    r"src\main\resources\assets\potato_s_t\textures\block\low_generator_side.png",
    r"src\main\resources\assets\potato_s_t\textures\block\low_generator_top.png",
    r"src\main\resources\data\potato_s_t\loot_table\blocks\low_generator.json",
    r"src\main\resources\data\potato_s_t\recipe\low_generator.json",
]

CHANGED = [
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\java\com\potatost\mod\PotatoSTClient.java",
    r"src\main\java\com\potatost\mod\ModBlocks.java",
    r"src\main\java\com\potatost\mod\ModItems.java",
    r"src\main\java\com\potatost\mod\ModMenus.java",
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

for s in ("_zf38_backup.ps1", "_zf38_apply.py", "_zf38_verify.py", "_zf38_archive.py",
          "MakeLowGeneratorTexture.py"):
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

txt = r"""ZF38：低级发电机（整台机器）
========================================================
备份时刻：2026-09-19 02:0x（**动手之前**建的）

用户原话
--------
  「加一个低级发电机 第一行【铁锭】【铁块】【铁锭】第二行【银锭】【红石块】【银锭】
   第三行【铜块】【熔炉】【铜块】右键打开gui只有能量槽和输入槽
   放置煤炭或木炭 1个发电45s 100Fe/t发电量 储能1k」

做了什么
--------
  Java ×4（新增）
    `LowGeneratorBlock`        方块：双端 ticker / 右键开 GUI / onRemove 掉燃料 / 掉落表掉自己
    `LowGeneratorBlockEntity`  数值与发电逻辑
    `LowGeneratorMenu`         1 个燃料槽 + 玩家背包
    `client/LowGeneratorScreen` 只有一根能量条（按你说的"只有能量槽和输入槽"）
  资源 ×7（新增）
    blockstate / block model（整块 16³，side+top）/ item model / 掉落表 / 配方 / 2 张贴图
  改 8 个既有文件
    ModBlocks（方块+物品+方块实体）、ModItems（创造页）、ModMenus（菜单类型）、
    PotatoST（能力 ㉑㉒）、PotatoSTClient（Screen 登记）、4 个 lang、2 张原版标签

数值（用户指定，探针逐条钉住）
------------------------------
  45 秒 = 900 tick、100 FE/t、储能 1000 FE  ⇒  一块燃料 = 90000 FE
  配方：`铁锭 铁块 铁锭 / 银锭 红石块 银锭 / 铜块 熔炉 铜块` ⇒ 1 个
        铁锭走 `#c:ingots/iron`、银锭走 `#c:ingots/silver`（别的 mod 的锭也能用）；
        铁块 / 红石块 / 铜块 / 熔炉都是原版物品（"块"不在默认兼容范围内）

⚠ 诚实记录一：两个我替用户定的默认（档案 §9 挂着待确认）
-------------------------------------------------------
  ① **储能满了暂停燃烧**（不浪费燃料，一块煤始终兑现 90000 FE，"45 秒"= 满速发电时的时长）。
     另一种是"照烧 45 秒、存不下的电扔掉" —— 缓冲 1k 对 100 FE/t 只有 10 tick 的量，
     没有负载时会白扔 98.9%。**改起来只差 `hasRoom()` 那一处判断。**
  ② 燃料收的是原版 `#minecraft:coals` 标签（原版内容 = 煤炭 + 木炭），
     比用户说的"煤炭或木炭"**放宽**了一点：别的 mod 往这个标签里加的自有煤也能烧。
  另按本项目家族惯例补了两样用户没点名的东西：**红石信号停机**、**运行中循环音效**
  （复用发电机那一段 `generator_running`，没新增音频文件）。

⚠ 诚实记录二：探针第一版**假通过**（本阶段最有价值的一条）
--------------------------------------------------------
  探针 `LowGenCheck` 在正版代码上 32 项全过。为确认"它真的能失败"，我往代码里**注入**了
  最经典的 bug：`BURN_TICKS = 45 * 20` → `BURN_TICKS = 45`（"45 秒写成 45 tick"）。
  重跑：**29 项依然全绿，一项都没抓到**。
  原因：期望值是从**被测常量本身**算出来的（`BURN_TICKS * ENERGY_PER_TICK`），
  常量改了等式两边一起改 ⇒ 同义反复。更阴的是它打印的数字也跟着变，看起来"完全对得上"。
  修法：探针里**照用户原话硬写规格常量**（SPEC_BURN_SECONDS = 45 等），再显式断言
  "实现常量 == 规格值"。改完后同一个注入 bug 立刻被抓到 **4 处**（28 过 4 挂）。
  ⇒ 已写成档案 §4.27 的规矩：**探针里不许出现被测常量；写完必须注入 bug 试着让它失败。**

⚠ 诚实记录三：一个 Java 侧的坑
------------------------------
  注入实验时我用 PowerShell 的 `Set-Content -Encoding UTF8` 改 .java —— 它会写 **BOM**，
  而本项目要求无 BOM（Audit C 项），当场编译失败（`错误: 非法字符: '\ufeff'`）。
  已回滚并用编辑工具重做。**改源码一律用编辑工具，改完确认前三字节不是 239,187,191。**

验证到哪一步
------------
  [x] 资源事后校验 `_zf38_verify.py`：lang ×4（键 + 4 行说明 + JSON 转义正确）、
      2 张标签、blockstate / 两个模型 / 2 张贴图 / 掉落表 / 配方内容，全过
  [x] 探针 `LowGenCheck`：**32 项全 [OK]**（含把方块真的放进 ServerLevel 手动 tick 900 次量总量）
      取证 build\zftools\check\zf38_低级发电机取证.log
  [x] 探针**反证**：注入 bug 后 28 过 **4 挂**（修正断言之后）
      取证 build\zftools\check\zf38_低级发电机取证_反证.log
  [x] runServer：`Loaded 1305 → **1306**`（+1，正好是这一条配方）、`Done (0.433s)`、零 ERROR
  [x] 七项交付检查：Audit 失败 0 / 提示 4；LangCheck 4×**170** 失败 0；
      RecipeCheck 定形 9→**10** 失败 0；ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 探针已从源码树删除；产物 jar 内 LowGenCheck / PressSoundCheck / BlockRegCheck 条目数 = 0
  [x] 产物 `release\PotatoST-0.10.jar` SHA1 `13594172…`（2,006,920 B）；
      **上一版 `9ce9acd0…` 作废**
  [ ] **游戏内未验**：配方、GUI 只有能量条+输入槽、煤炭/木炭能不能烧、
      不接负载时燃料是否暂停、红石停机、破坏掉落、音效 —— 清单在档案 §9「0.10 ZF38」

回退办法
--------
  删 `新增文件\` 里的 11 个文件，再把本目录根部的 12 个改前副本覆盖回原路径
  （对照 `_sha256.txt` 顶部的清单），成品 jar 用 `_改前_PotatoST-0.10.jar`。

本阶段没漏文件
--------------
  清单 12 项，备份脚本跑完逐条交叉核对通过（数量 + 每份副本的 SHA256），
  并且**额外列了"本阶段将新建的 11 个文件"**，免得日后回退时不知道多了什么。
"""

io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(txt)
print("已写 _说明.txt")
print("新增文件目录: " + dst_new)
