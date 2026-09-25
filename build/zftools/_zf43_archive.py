# -*- coding: utf-8 -*-
"""ZF43 收尾：档案补记 §12.11 + 备份收尾。"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf43_pre"
ARCH = os.path.join(PROJ, r"docs\开发档案.md")

ADD = u"""
### 12.11 ZF43：节拍改 10 秒 + 接上所有原版高炉配方（顺手把储能换回用户给的 320）

**① 节拍 3 秒 → 10 秒**（用户：「改为10s一组吧」）。`DURATION_TICKS = 200`。

这一步**顺手救了储能**：最坏情况的单 tick 耗电 = 12 槽 × 64 件 × 80 FE ÷ 200 tick
= **308 FE/t**，于是**用户原本给的 320 又能用了**（见 ② 的算术），
ZF42 我临时提上去的 4096 就换回 320 了。余量只有 12 —— 这条算术已经写进
`MAX_ENERGY` 的注释：**以后要是把节拍改短、或允许超过 64 的堆叠，必须先重算。**

**② 接上所有原版高炉配方**（用户：「并且加上所有的原版高炉配方」）。

原版 1.21.1 一共 **24 条** `minecraft:blasting`（从 `client.jar` 里现数出来的）：
铁/铜/金锭（矿石 + 粗矿两种）、**钻石、绿宝石、青金石、红石、煤炭、石英**（各自的矿石）、
**下界合金碎片**（远古残骸）、以及 **铁粒/金粒**（工具盔甲回炉）那些。

**实现方式是走 `RecipeManager` 动态查，不是把那 24 条抄进来**：

```java
this.level.getRecipeManager()
    .getRecipeFor(RecipeType.BLASTING, new SingleRecipeInput(in), this.level)
    .map(h -> h.value().getResultItem(this.level.registryAccess()))
```

三个理由：① 抄一遍就得跟着版本更新；② 动态查**顺带吃下别的 mod 加的高炉配方**；
③ 原版那些"工具烧成粒"的配方带的是**标签**，手抄极容易漏。

**优先级**：本模组自己的表排在最前面，所以矿石方块仍然是 3~6 锭、粗矿仍然是 2 锭 ——
不会被原版的"1 锭"盖掉（探针里专门有一条反向断言盯这个）。

**探针取证**：`build\\zftools\\check\\zf43_十秒与原版配方取证.log`（**16 项全过**）：
· 常量与算术（200 tick、最坏 308 ≤ 320）
· 满载 12 槽 × 64 = **768 件恰好 200 tick 走完**，总耗电 61600 FE（≈768×80）
· 原版配方八连：钻石矿石→钻石、远古残骸→下界合金碎片、**铁镐→铁粒**、
  下界石英矿石→石英、红石矿石→红石、青金石矿石→青金石、煤矿石→煤炭、绿宝石矿石→绿宝石
· 反向：粗钴 ×3 → **6 锭**（本模组的表优先）；泥土 → **什么都不出**
"""

with io.open(ARCH, "r", encoding="utf-8") as f:
    cur = f.read()
if "### 12.11" in cur:
    print("[SKIP] 已有 12.11")
else:
    with io.open(ARCH, "w", encoding="utf-8", newline="") as f:
        f.write(cur + ADD)
    print("[OK] 档案已补记 12.11")

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
for s in ("_zf43_lang.py", "_zf43_verify.py", "EbfVanillaCheck.java"):
    for base in ("build/zftools", "build/zftools/check"):
        p = os.path.join(PROJ, base.replace("/", os.sep), s)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(BK, "新增文件", s))
            break
shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))

note = u"""ZF43：节拍改 10 秒 + 所有原版高炉配方 + 储能换回 320
========================================================
备份时刻：2026-09-19 03:4x（动手前建的）

用户原话
--------
  「改为10s一组吧 并且加上所有的原版高炉配方」

改了什么
--------
  ① `DURATION_TICKS` 60 → **200**（10 秒一组）。
     顺手救了储能：最坏情况单 tick 耗电 = 12×64×80 ÷ 200 = **308 FE/t**，
     于是 **ZF42 我临时提上去的 4096 换回用户原本给的 320**（余量只有 12）。
  ② 加工范围接上**原版高炉的全部 24 条 `minecraft:blasting`**：
     钻石/绿宝石/青金石/红石/煤炭/石英各自的矿石、下界合金碎片、铁粒/金粒（工具盔甲回炉）。
     实现走 `RecipeManager` 动态查（不是抄 24 条）—— 顺带也吃下别的 mod 加的高炉配方。
     优先级：**本模组自己的表在前**，矿石方块仍是 3~6 锭、粗矿仍是 2 锭，不被原版的 1 锭盖掉。
  ③ 4 个语言的 Shift 说明同步（10 秒 / 320 FE / 支持高炉能烧的一切）。

验证到哪一步
------------
  [x] 探针 EbfVanillaCheck：**16 项全 [OK]**
      · 常量与算术：200 tick、最坏 308 ≤ 320
      · 满载 12 槽 × 64 = **768 件恰好 200 tick 走完**，总耗电 61600 FE（≈768×80）
      · 原版配方八连全过（钻石矿石→钻石、**远古残骸→下界合金碎片**、**铁镐→铁粒**、
        石英、红石、青金石、煤炭、绿宝石）
      · 反向：粗钴 ×3 → **6 锭**（本模组表优先）；泥土 → **什么都不出**
      取证 build\\zftools\\check\\zf43_十秒与原版配方取证.log
  [x] 语言文案按 §4.28 的规矩：补丁脚本只改，**另写只读复核** `_zf43_verify.py`，
      期望值在那里独立再写一遍 ⇒ 20 项全过（这次没再栽在转义换行上）
  [x] 七项：Audit 失败 0 / 提示 5；LangCheck 4×176 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 探针已删；jar 内 *Check.class = 0
  [x] 产物 release\\PotatoST-0.10.jar SHA1 9c7ce56a…（2,062,692 B）；上一版 38ac964e… 作废
  [ ] **游戏内未验**：10 秒一组的节奏、满载能不能跑起来、拿工具/宝石矿试原版配方

⚠ 一条必须记住的算术
--------------------
  **单 tick 耗电 = 槽数 × 每槽件数 × 80 ÷ DURATION_TICKS 必须 ≤ MAX_ENERGY(320)。**
  现在最坏 308 ≤ 320，余量 12。改节拍或改堆叠上限**必须重算**，否则机器会静默不动
  （ZF42 就是这么"貌似不工作"的）。
"""
io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(note)
print("[OK] 已写 zf43_pre\\_说明.txt")
