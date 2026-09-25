# -*- coding: utf-8 -*-
"""ZF40 收尾：档案补记 + 备份收尾。"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf40_pre"
ARCH = os.path.join(PROJ, r"docs\开发档案.md")

ADD = u"""
### 12.8 ZF40：用户实测反馈后的三条改动（两个真 bug）

用户看了实机截图后提了四条。逐条：

**① 「挖掘后会掉落两个电力高炉」—— 真 bug，已修，两个独立原因叠在一起。**

- **原因 A：`onRemove` 被自己触发第二次。**
  `disassemble()` 要把控制器那一格清成空气，而这一步又会触发**方块自己的 `onRemove`**，
  于是"掉一份机器本体"的代码走了两遍。修法：方块 `onRemove` 里加
  `!be.isDisassembling()` 闸门。
- **原因 B：被挖掉的那一格"又掉又还原"。**
  掉落走 `onRemove`（把这一格的**原方块**作为物品给玩家），
  可 `disassemble()` 又会把**包括这一格在内的所有格**还原回原方块 ⇒
  玩家既拿到掉落物、世界上又长回来一块 = **白送一格建材**。
  修法：`disassemble(BlockPos skip)` 多一个"这一格留空"的参数。
  **这条是探针抓出来的**（断言"被挖的那格现在应当是空气"直接 [FAIL]）。

**② 破坏语义按用户要求改了**：「被破坏后只会毁坏结构和掉落被挖掉的方块以及 gui 内部物品」
⇒ 破坏时**不再掉"电力高炉"这个物品**，改成掉**被挖那一格原来的方块**
（挖接线块得接线块、挖控制器得原版高炉），外加 GUI 里那 44 个槽位的内容物。
`dropEverything()` 相应改名 `dropContents()`（只掉内容物）。
物品本身**保留**（用户：「电力高炉这个物品可以不删」）：
还没成型的裸控制器被破坏时仍然把它还回来，否则凭空吞一个。

**③ 右键任意部位都能开 GUI。** 部件格的 `useWithoutItem` 现在会就近找控制器
（±2 格，最远的角格也在范围内）并打开它的菜单；空手 Shift 右键任意部位 = 整体拆解。

**④ 「一个模型是一个整体」。** 这一条查下来**已经是这样**：
部件格 `getRenderShape()` 返回 `RenderShape.INVISIBLE`、控制器返回 `MODEL`，
成型后画面上只有那一整块 OBJ，探针把这两个返回值也钉成了断言。
如果实机里还看得见一格格的建材，最可能是**当时那台并没有成型**
（结构不成立时会有一条 actionbar 提示，容易错过），而不是渲染没生效。

取证：`build\\zftools\\check\\zf40_破坏语义取证.log`（14 项全过）与
`..._反证.log`（修复前，13 过 **1 挂** —— 挂的正是"被挖的那格应当是空气"）。
"""

with io.open(ARCH, "r", encoding="utf-8") as f:
    cur = f.read()
if "### 12.8" in cur:
    print("[SKIP] 已有 12.8")
else:
    with io.open(ARCH, "w", encoding="utf-8", newline="") as f:
        f.write(cur + ADD)
    print("[OK] 档案已补记 12.8")

# ---- 备份收尾 ----
CHANGED = [
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceBlock.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnacePartBlock.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceBlockEntity.java",
    r"src\main\java\com\potatost\mod\PotatoST.java",
    r"docs\开发档案.md",
]
os.makedirs(os.path.join(BK, "新增文件"), exist_ok=True)
for rel in CHANGED:
    shutil.copy2(os.path.join(PROJ, rel), os.path.join(BK, "改后_" + os.path.basename(rel)))
for s in ("EbfDropCheck.java",):
    p = os.path.join(PROJ, "build", "zftools", "check", s)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(BK, "新增文件", s))
shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))


def sha(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


note = u"""ZF40：按用户实机反馈修的两个真 bug + 三条行为改动
========================================================
备份时刻：2026-09-19 03:1x（动手前建的）

用户原话
--------
  「挖掘后会掉落两个电力高炉 改成像沉浸工程那样子一个模型是一个整体
   任意部位右键都可以打开gui 被破坏后只会毁坏结构和掉落被挖掉的方块以及gui内部物品
   可以嘛 电力高炉这个物品可以不删」

改了什么
--------
  Java 3 个文件（ElectricBlastFurnaceBlock / ...PartBlock / ...BlockEntity）+ PotatoST（探针注册）

  ① **修"掉两个"**（两个独立原因叠在一起）
     A. disassemble() 清控制器那格 → 触发方块自己的 onRemove → 掉落代码走第二遍
        ⇒ 加 !be.isDisassembling() 闸门
     B. 被挖的那格"既掉又还原" ⇒ disassemble(BlockPos skip) 多一个"这格留空"
        **这条是探针抓的**（"被挖的那格应当是空气"直接 [FAIL]）
  ② **破坏语义**：不再掉"电力高炉"物品，改掉**被挖那一格的原方块** + GUI 内容物。
     dropEverything() → dropContents()（只掉内容物）。物品本身保留；
     还没成型的裸控制器被破坏时仍还回物品（否则凭空吞一个）。
  ③ **右键任意部位开 GUI**：部件格就近找控制器（±2 格）并打开它的菜单；
     空手 Shift 右键任意部位 = 整体拆解。
  ④ **"一个模型是一个整体"查下来已经是这样**：部件格 RenderShape.INVISIBLE、
     控制器 MODEL，成型后只有那一整块 OBJ。探针把这两个返回值也钉成了断言。
     实机若还看得见一格格的建材，最可能是**当时那台并没有成型**。

验证到哪一步
------------
  [x] 探针 EbfDropCheck（**数掉落实体**，不是读代码猜）：**14 项全 [OK]**
      · 破坏部件格 → 掉 **1 × 铁栏杆**（不是 2 件、不是电力高炉），那格变空气，其余 26 格还原
      · 破坏控制器 → 掉 **1 × 原版高炉**
      · GUI 里的 7 粗钴 + 5 钴锭都掉出来，且**没有任何一件是电力高炉本体**
      · 25 个部件格全在控制器的 2 格搜索半径内（右键任意部位能开 GUI 的前提）
      取证 build\\zftools\\check\\zf40_破坏语义取证.log
  [x] **修复前的反证**（同一份探针）：13 过 **1 挂**，挂的正是"被挖的那格应当是空气"
      取证 ..._反证.log
  [x] runServer：Loaded 1306 recipes（不变）、Done (0.473s)、零 ERROR
  [x] 七项：Audit 失败 0 / 提示 5；LangCheck 4×174 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 探针已删；产物 jar 内 *Check.class 条目 = 0
  [x] 产物 release\\PotatoST-0.10.jar SHA1 1fd7b558…（2,056,841 B）；上一版 25cf9c4b… 作废
  [ ] **游戏内未验**：再来一次 —— 成型后应当只看到一整块模型；
      挖任意一格只掉那一格的方块；右键任意一格开 GUI；Shift 右键拆解

回退办法
--------
  本目录根部的 4 个改前副本覆盖回去即可（另有 EbfCheck 时代的 12 个副本在 zf39_pre）。
  成品 jar 用 _改前_PotatoST-0.10.jar。
"""
io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(note)
print("[OK] 已写 zf40_pre\\_说明.txt")
