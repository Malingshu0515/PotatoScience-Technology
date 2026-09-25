# -*- coding: utf-8 -*-
"""ZF42 收尾：档案补记 §12.10 + §4.28（断言又写错的第二次）+ 备份收尾。"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf42_pre"
ARCH = os.path.join(PROJ, r"docs\开发档案.md")

ADD = u"""
### 4.28 【方法论】"转义换行"又骗了我一次 —— 断言里的期望值要和**解析后**的类型对齐（0.10 ZF38 / ZF42 两次同款）

**现象**：给 lang 写补丁脚本，期望值写成 Python 字面量 `u"...\\n..."`（反斜杠 + n 两个字符），
写完用 `after[key] == NEW[code]` 复核 —— **恒为假**；再数 `after[key].count("\\n")` —— **恒为 0**。
于是每次改完都报一串假 FAIL（ZF38 四条、ZF42 八条），而**文件其实完全正确**
（写盘前 `json.loads` 已经校验过，且"旧数字 320 不在了"那条是过的）。

**原因**：JSON 文件里写的是**转义序列** `\\n`，`json.loads` 会把它还原成**真换行 `\\x0a`**。
拿"字面反斜杠+n"去比"真换行"，当然不等。

**规矩**：
1. **断言里的期望值要写成"解析之后"的样子**：比 `\\n` 就写 `"\\n"`（一个字符），
   要检查文件里的转义形式就**去读原始文本**（`raw.split("\\n")` 那一行），别混着用。
2. **同一类错犯第二次就说明它不是手滑，是流程缺一环**：改文本类资源时，
   **写完必须只读复核一遍**（本项目的做法：另写一个 `_verify.py`，只读、不写、逐条打印），
   而且复核脚本里的期望值**独立照用户原话再写一遍**，不要复用补丁脚本里的变量。
3. 顺带一条：**"旧值不在了"这种否定式断言好用**（`320 not in text`），
   它不受转义影响，可以当交叉验证。

---

### 12.10 ZF42：用户报「貌似不工作」—— 数值本身自相矛盾

用户发来界面截图：12 个输入槽塞满 64 一摞的矿石、**能量条满格**、产物一个没有。

**根因不是代码写错，是三个数凑不到一起。** 有一条硬约束：

> **机器一 tick 最多只能花掉"缓冲里现有的电"** ——
> 能量是电缆/端子按 tick 推来的，攒不过缓冲上限。
> ⇒ **单 tick 耗电 > 储能上限 ⇒ 永远凑不齐 ⇒ 永远不动。**

按原来字面的读法（耗电 = 物品数 × 80 **每 tick**）：
一摞 64 就是 **5120 FE/t**，而储能只有 **320**（够 4 个物品）⇒ 塞满就是死机。

**改法**：把 80 FE 理解成**一件物品整批的电**（摊到那 3 秒里），并把储能提到能扛住最坏情况：

| | 原来（字面） | 现在 |
|---|---|---|
| 一件物品 | 80 FE **每 tick** | 80 FE **整批** |
| 一摞 64 | 5120 FE/t | 5120 FE 总价 ≈ 86 FE/t |
| 12 槽塞满 | 61440 FE/t | ≈ **1024 FE/t** |
| 储能 | 320（永远凑不齐） | **4096** |

"是要接大电"这条意图**依然成立**（满载 1024 FE/t，比本项目其它机器高一个档次），
而且数字回到了合理量级。**⚠ 储能从 320 改成 4096、以及"80 是整批不是每 tick"这两条是替用户定的，
已挂 §9 待确认**；要改回字面读法的话，储能得跟着提到 61440 以上（每 tick 一档）。

**探针取证**：`build\\zftools\\check\\zf42_满载运行取证.log`（9 项全过）——
按用户那天的真实负载 11 槽 × 64 = **704 件**跑：**恰好 60 tick 走完**、
总耗电 **56340 FE**（≈ 704×80，差 20 是逐 tick 向上取整的零头）、
共出 **1408 个钴锭**（跨多个输出槽）；反向断言"一点电都不给时进度停在 0"。
`..._反证.log` 是探针第一版（8 过 1 挂，挂的是"只数了第一个输出槽"——128 个锭一个槽装不下）。
"""

with io.open(ARCH, "r", encoding="utf-8") as f:
    cur = f.read()
if "### 12.10" in cur:
    print("[SKIP] 已有 12.10")
else:
    # §4.28 插到 §5 之前；§12.10 追加到末尾
    marker = u"## 5. 版本与 [ZF] 流水线记录"
    i = cur.find(marker)
    cur = cur[:i] + ADD.split(u"### 12.10")[0] + u"\n---\n\n" + marker + cur[i + len(marker):]
    cur = cur + u"\n### 12.10" + ADD.split(u"### 12.10")[1]
    with io.open(ARCH, "w", encoding="utf-8", newline="") as f:
        f.write(cur)
    print("[OK] 档案已补记 §4.28 与 §12.10")

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
for s in ("_zf42_lang.py", "_zf42_verify.py", "EbfLoadCheck.java"):
    for base in ("build/zftools", "build/zftools/check"):
        p = os.path.join(PROJ, base.replace("/", os.sep), s)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(BK, "新增文件", s))
            break
shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))

note = u"""ZF42：修「貌似不工作」—— 数值自相矛盾
========================================================
备份时刻：2026-09-19 03:3x（动手前建的）

用户现象
--------
  发来界面截图：12 个输入槽塞满 64 一摞的矿石、**能量条满格**、产物一个没有。

根因（不是代码写错，是三个数凑不到一起）
----------------------------------------
  硬约束：**机器一 tick 最多只能花掉缓冲里现有的电**（能量按 tick 推来、攒不过上限）
  ⇒ **单 tick 耗电 > 储能上限 ⇒ 永远凑不齐 ⇒ 永远不动**。
  按字面「耗电 = 数量 × 80 **每 tick**」：一摞 64 = 5120 FE/t，储能只有 320（够 4 个）⇒ 死机。

改了什么
--------
  · 80 FE 改成**一件物品整批的电**（摊到 3 秒里）：一摞 64 = 5120 FE 总价 ≈ 86 FE/t
  · 储能 320 → **4096**（12 槽塞满 ≈ 1024 FE/t，扛得住）
  · 4 个语言的 Shift 说明同步更新（提到扳手、新数字）
  ⚠ **这两条是替用户定的**，已挂 §9 待确认：要改回字面读法，储能得提到 61440 以上。

验证
----
  [x] 探针 EbfLoadCheck：**9 项全 [OK]**。按用户那天的真实负载 11 槽 × 64 = **704 件**：
      **恰好 60 tick 走完**、总耗电 **56340 FE**（≈704×80）、共出 **1408 个钴锭**（跨多个输出槽）；
      反向断言"一点电都不给时进度停在 0"。
      取证 build\\zftools\\check\\zf42_满载运行取证.log
  [x] 探针第一版 8 过 1 挂：**只数了第一个输出槽**（128 个锭一个槽装不下）⇒ 假 FAIL。..._反证.log
  [x] 语言文案另写只读复核 `_zf42_verify.py` 逐条打印，20 项全过
      （⚠ 补丁脚本自己的断言又栽在"转义换行 vs 真换行"上，第二次了 —— 已写成档案 §4.28）
  [x] 七项：Audit 失败 0 / 提示 5；LangCheck 4×176 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 探针已删；jar 内 *Check.class = 0
  [x] 产物 release\\PotatoST-0.10.jar SHA1 38ac964e…（2,062,049 B）；上一版 c7e91247… 作废
  [ ] **游戏内未验**：塞满 12 槽能不能真的跑起来、3 秒出一批、满载耗电体感

回退办法
--------
  本目录根部的 7 个改前副本覆盖回去；成品 jar 用 _改前_PotatoST-0.10.jar
  （⚠ zf42_pre 没有单独备份 jar 之外的东西，数值回退请改 ElectricBlastFurnaceBlockEntity 的两个常量）。
"""
io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(note)
print("[OK] 已写 zf42_pre\\_说明.txt")
