# -*- coding: utf-8 -*-
"""ZF36 备份收尾：新增文件 + 改后副本 + _说明.txt + 改后成品 jar。

⚠ 文本一律用 Python 三引号原文写（不用 PowerShell 双引号串，那里的反引号是转义符，§8）。
"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf36_pre"

NEW_FILES = [
    r"src\main\resources\assets\potato_s_t\sounds\hydraulic_press_running.ogg",
    r"build\zftools\SoundCheck.py",
]

CHANGED = [
    r"src\main\java\com\potatost\mod\HydraulicPressBlockEntity.java",
    r"src\main\java\com\potatost\mod\HydraulicPressBlock.java",
    r"src\main\java\com\potatost\mod\sound\ModSounds.java",
    r"src\main\resources\assets\potato_s_t\sounds.json",
    r"docs\开发档案.md",
]

dst_new = os.path.join(BK, "新增文件")
for rel in NEW_FILES:
    dst = os.path.join(dst_new, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(os.path.join(PROJ, rel), dst)

for s in ("_zf36_backup.ps1", "_zf36_rebuild_pressblock.py", "_zf36_archive.py", "MakeSfx.py"):
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

txt = r"""ZF36：液压机运行中循环播放液压声
========================================================
备份时刻：2026-09-19 01:4x（**动手之前**建的）

用户原话
--------
  「液压机工作时候循环播放」+ 一段素材
  `freesound_community-hydraulicdoorsnd-107449.mp3`（120372 B，3.766s / 44100 Hz / 单声道）

做了什么
--------
  音效侧
    · `MakeSfx.py --loop --start 0.0 --end 3.761 --crossfade 200 --target-rms 0.10`
    · 素材是"开门…停顿…关门"一整段，**没有稳态段可切**，所以整段循环 ——
      好在首尾本来就安静（开头 -46 dB、结尾近静音），接缝天然干净
    · 成品 `hydraulic_press_running.ogg`：**3.56s / 44100 Hz / 单声道 Vorbis / 36421 B**
    · 工具回读：**接缝首尾差 0.0017**（越接近 0 越好）
    · 响度：想对齐 0.10 RMS 会削波 ⇒ 工具自动改用**峰值保护**（增益 4.848），
      实落 **0.0794 RMS / 峰值 0.995**。循环音的 volume 在代码里固定 1.0，音量只能靠文件本身。
    · 新增 `ModSounds.HYDRAULIC_PRESS_RUNNING` + `sounds.json` 里的 `hydraulic_press_running` 键
  方块侧
    · `HydraulicPressBlockEntity` 加 `isRunning()`、`sync()`，`tick` 拆成双端；
      补 `getUpdateTag` / `getUpdatePacket`（客户端靠更新包里的 `status` 判断响不响）
    · `HydraulicPressBlock.getTicker` **改成双端**（这是差点漏掉的那一刀，见下）
  新写的交付检查
    · `build\zftools\SoundCheck.py`（第 7 项）：注册名 ↔ sounds.json 键 ↔ ogg 三向一致，
      每个 ogg 必须 44100 Hz 单声道 Vorbis，反向找孤儿

⚠ 诚实记录一：这本来会是一个"完全静默"的 bug
--------------------------------------------
  `HydraulicPressBlock.getTicker` 是 ZF30 写的，那时这台机器没音效，所以是：
      if (level.isClientSide) { return null; }   // "省一次每 tick 的空转"
  加上循环音效之后**忘了改这里** ⇒ 客户端根本拿不到 ticker ⇒
  `HydraulicPressBlockEntity.tick` 的客户端分支永远不执行 ⇒
  **音效注册、sounds.json、ogg 文件、SoundCheck 全部正确，游戏里一点声音都没有，且不报任何错**。
  是写探针时才发现的（§4.26）。

⚠ 诚实记录二：备份清单又漏了一个文件（第五次）
--------------------------------------------
  `_zf36_backup.ps1` 的清单只有 4 个文件，**漏了 `HydraulicPressBlock.java`** ——
  写清单时我压根没想到要碰它（是改完 BlockEntity 才意识到 getTicker 必须一起改）。
  但这次**能逐字节反证**，补法值得记档：**逐字节反向替换**。
  ZF36 对这份文件的编辑只有 `edit` 工具的一次 `old_string → new_string`，两个串逐字节已知，
  于是拿当前文件做一次精确反向替换即得改前内容（`_zf36_rebuild_pressblock.py` 就是干这个的，
  它内置三条断言：新块必须出现且只出现一次、旧块必须不存在、替换后必须能看到改前特征）。
  **验证做到字节级**：把重建件塞回源码树编译，取 `HydraulicPressBlock.class`，
  与 `zf35_pre\_改后_PotatoST-0.10.jar` 里的同名 class 比 SHA256 ——
      **8a457538d6184e2cb55bec401dbbc348d276ae68f1d1955aeafa629d4389ab7a  两边完全相同**
  javac 会把行号写进 LineNumberTable，所以字节相同意味着**连空行位置与 javadoc 折行都对**，
  重建件就是原件（改前 87 行，与改前 `read` 出来的行数一致）。

改前 / 改后 对照
----------------
  ModSounds.java / HydraulicPressBlockEntity.java / sounds.json / 开发档案.md
      —— 改前（本目录根）；改后见 改后_<同名>
  HydraulicPressBlock.java     —— **改前（反向替换重建，已字节级验证）**
  改后_HydraulicPressBlock.java —— 改后
  新增文件\<相对路径>           —— 新 ogg + SoundCheck.py + 本阶段脚本
  _改前_PotatoST-0.10.jar      —— 改前成品（SHA1 4c065d20…，本次作废）
  _改后_PotatoST-0.10.jar      —— 改后成品（SHA1 402d3555…）
  _素材\                        —— 用户原始 mp3

验证到哪一步
------------
  [x] SoundCheck.py：19 项全过（6 个音效事件 ↔ 6 个 json 键 ↔ 6 个 ogg，格式全对，无孤儿）
  [x] 探针 PressSoundCheck 在真 runServer 上 **8 项全 [OK]**
      取证 build\zftools\check\zf36_音效链路取证.log
  [x] 探针**反证**：把改前的 HydraulicPressBlock 临时换回去重跑 ⇒ **7 过 1 挂**，
      挂的正是"getTicker(null,…) 返回非 null"那条（抛 NullPointerException）
      取证 build\zftools\check\zf36_音效链路取证_反证.log
  [x] runServer：Loaded 1303 recipes（不变）、Done (0.418s)、零 ERROR
  [x] 七项交付检查：Audit 失败 0 / 提示 4；LangCheck 4×168 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 探针已从源码树删除；产物 jar 内 PressSoundCheck / BlockRegCheck 条目数 = 0
  [ ] **游戏内未验（只能你验 —— 音效是纯客户端行为，runServer 永远验不到）**：
      压制时是否响起并循环、停机是否立刻停、走远是否变小、多台是否各响各的、挖掉是否停
      —— 清单在档案 §9「0.10 ZF36」

回退办法
--------
  删 `新增文件\src\...\hydraulic_press_running.ogg` 与 `SoundCheck.py`，
  再把本目录根部的 4 个改前副本 + `HydraulicPressBlock.java`（重建件）覆盖回原路径，
  成品 jar 用 `_改前_PotatoST-0.10.jar`。`sounds.json` 里的键删掉即可。
"""

io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(txt)
print("已写 _说明.txt")
print("新增文件目录: " + dst_new)
