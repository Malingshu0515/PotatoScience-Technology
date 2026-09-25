# -*- coding: utf-8 -*-
"""ZF44 收尾：档案补记 §12.12 + §4.29（Audit E 项会拦开发者日志）+ 备份收尾。"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf44_pre"
ARCH = os.path.join(PROJ, r"docs\开发档案.md")

ADD = u"""
### 4.29 【流程】Audit 的 E 项会连**开发者日志**一起拦 —— 日志文案用英文（0.10 ZF44）

**现象**：给电力高炉加了一道"配置自检"（单 tick 耗电超过储能就打一条警告），
文案是中文，结果 Audit 直接报 **3 项失败**（把它按行拆成了三条）：

```
[FAIL] ElectricBlastFurnaceBlockEntity.java:130  System.err.println("[potato_s_t] 电力高炉配置有问题：…
```

**原因**：Audit 的 **E 项是文本级检查** —— "Java 里不许出现用户可见的硬编码中文"。
它分不清"给玩家看的文案"和"给开发者看的日志"。

**规矩**：
1. **Java 里的日志文案一律用英文。** 那是给开发者/排错看的，不是玩家可见文本；
   为它造一个 lang 键没有意义，用中文又会被 E 项拦。
   想在代码里解释"为什么用英文"，就写在**上一行的注释**里（注释不受影响）。
2. 顺带一条流程教训：**这次我是先发布、后看 Audit，结果发布了一个 Audit 没过的 jar**
   （SHA1 `d5242d04…`，当场作废、重发了一次）。标准顺序永远是
   **改 → 编译 → 七项检查 → 再发布**，§11.1 那七项是**发布前**的门，不是事后补充材料。

---

### 12.12 ZF44：每件 800 FE（储能跟着提到 4096 + 加了配置自检）

用户：「每件800Fe吧」。**先算再改**，因为这条算术 ZF42 已经咬过一次：

```
单 tick 最坏耗电 = 12 槽 × 64 件 × 800 FE ÷ 200 tick = 3072 FE/t
储能 320  <  3072   ⇒ **满载一动不动**（和 ZF42 同一个死法）
⇒ 储能 320 → 4096
```

| | ZF43 | ZF44 |
|---|---|---|
| 每件物品 | 80 FE | **800 FE** |
| 一摞 64 | 5120 FE 整批 | **51200 FE 整批** |
| 12 槽满载 | 308 FE/t | **3072 FE/t** |
| 储能 | 320 | **4096** |

**另加一道"配置自检"**（`ElectricBlastFurnaceBlockEntity` 的静态块）：
构建时把 `槽数 × 堆叠上限 × 每件耗电 ÷ 节拍` 和储能比一下，超了就往 stderr 打一条警告。
ZF42 那次是**靠用户截图 + 我手算**才发现的，代价是一轮往返；现在它变成启动时的一行字。

**这道自检做了反证**（§4.27 的规矩）：把 `MAX_ENERGY` 临时改回 320 重跑，
警告**确实打了出来**，同时探针那条"储能 ≥ 最坏单 tick 耗电"也**确实 [FAIL]**；
改回 4096 后两者都安静。取证 `build\\zftools\\check\\zf44_配置自检反证.log`。

**探针取证**：`build\\zftools\\check\\zf44_八百FE取证.log`（9 项全过）：
满载 12 槽 × 64 = **768 件恰好 200 tick 走完**、总耗电 **614400 FE = 768×800（分毫不差）**、
产出 1536 个钴锭；单件时单 tick 只花 4 FE（800÷200）；不给电进度停在 0。
"""

with io.open(ARCH, "r", encoding="utf-8") as f:
    cur = f.read()
if "### 12.12" in cur:
    print("[SKIP] 已有 12.12")
else:
    marker = u"## 5. 版本与 [ZF] 流水线记录"
    i = cur.find(marker)
    cur = cur[:i] + ADD.split(u"### 12.12")[0] + u"\n---\n\n" + marker + cur[i + len(marker):]
    cur = cur + u"\n### 12.12" + ADD.split(u"### 12.12")[1]
    with io.open(ARCH, "w", encoding="utf-8", newline="") as f:
        f.write(cur)
    print("[OK] 档案已补记 §4.29 与 §12.12")

CHANGED = [
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceBlockEntity.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"src\main\resources\assets\potato_s_t\lang\zh_cn.json",
    r"src\main\resources\assets\potato_s_t\lang\en_us.json",
    r"src\main\resources\assets\potato_s_t\lang\ja_jp.json",
    r"src\main\resources\assets\potato_s_t\lang\ru_ru.json",
    r"docs\开发档案.md",
]
os.makedirs(os.path.join(BK, "新增文件"), exist_ok=True)
for rel in CHANGED:
    shutil.copy2(os.path.join(PROJ, rel), os.path.join(BK, "改后_" + os.path.basename(rel)))
for s in ("_zf44_backup.ps1", "_zf44_lang.py", "_zf44_verify.py", "Ebf800Check.java", "_zf44_archive.py"):
    for base in ("build/zftools", "build/zftools/check"):
        p = os.path.join(PROJ, base.replace("/", os.sep), s)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(BK, "新增文件", s))
            break
shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))

note = u"""ZF44：每件 800 FE（储能 320 → 4096 + 新增配置自检）
========================================================
备份时刻：2026-09-19 03:5x（动手前建的，清单 7 项交叉核对通过）

用户原话
--------
  「每件800Fe吧」

先算再改（这条算术 ZF42 已经咬过一次）
--------------------------------------
  单 tick 最坏耗电 = 12 槽 × 64 件 × 800 FE ÷ 200 tick = **3072 FE/t**
  储能 320 < 3072 ⇒ **满载一动不动**（和 ZF42 同一个死法）⇒ 储能改 **4096**

改了什么
--------
  · `ENERGY_PER_ITEM` 80 → **800**
  · `MAX_ENERGY` 320 → **4096**
  · 新增**配置自检**（静态块）：把"槽数 × 堆叠上限 × 每件耗电 ÷ 节拍"和储能比一下，
    超了就往 stderr 打一条英文警告（英文的原因见档案 §4.29）
  · 4 个语言的 Shift 说明同步（800 FE / 4096 FE / 满载约 3072 FE/t）

验证到哪一步
------------
  [x] 探针 Ebf800Check：**9 项全 [OK]**
      · 满载 768 件**恰好 200 tick 走完**，总耗电 **614400 FE = 768×800（分毫不差）**，产出 1536 锭
      · 单件时单 tick 只花 4 FE（800÷200）；不给电进度停在 0（反向断言）
      取证 build\\zftools\\check\\zf44_八百FE取证.log
  [x] **配置自检做了反证**：把 MAX_ENERGY 临时改回 320 重跑 ⇒
      警告**确实打了出来**、探针那条也**确实 [FAIL]**；改回 4096 后两者都安静。
      取证 build\\zftools\\check\\zf44_配置自检反证.log
  [x] 语言文案按 §4.28：补丁脚本只改，另写只读复核，期望值独立再写 ⇒ 20 项全过
  [x] 七项：Audit 失败 0 / 提示 5；LangCheck 4×176 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 探针已删；jar 内 *Check.class = 0
  [x] 产物 release\\PotatoST-0.10.jar SHA1 750b97c2…（2,063,198 B）
  [ ] **游戏内未验**：800 FE 一件的成本体感、满载够不够电

⚠ 两个过程中的教训（已写进档案）
--------------------------------
  ① **先发布后看 Audit，发了一个 Audit 没过的 jar**（SHA1 d5242d04…，当场作废重发）。
     标准顺序永远是 **改 → 编译 → 七项检查 → 再发布**。
  ② Audit 的 E 项**会连开发者日志一起拦**（它是文本级检查，分不清玩家文案与日志）
     ⇒ Java 里的日志文案一律用英文，理由写在注释里。见 §4.29。

（作废清单：d5242d04… 为"Audit 未过"的那一版；更早的 9c7ce56a… 是 ZF43。）
"""
io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(note)
print("[OK] 已写 zf44_pre\\_说明.txt")
