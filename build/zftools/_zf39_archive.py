# -*- coding: utf-8 -*-
"""ZF39 收尾：档案写 §5 行 + §9 待办 + §12.7 交付状态，并收尾 zf39_pre 备份。"""
import hashlib
import io
import os
import shutil

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf39_pre"
ARCH = os.path.join(PROJ, r"docs\开发档案.md")

ROW = u"""| ZF39 | `zf39_pre`（**动手前**建的；清单 13 项交叉核对通过） | 0.10：**电力高炉 —— 本项目第一个真正的多方块结构**（用户："重要的来了 真正意义的多方快结构"）。做法：空手 Shift + 右键原版高炉，结构成立就把 27 格换成一台机器并**加载用户给的 OBJ 模型**。新增 Java ×8（结构定义 / 配方表 / 控制器方块 / 部件方块 / 控制器方块实体 / 菜单 / 大面板界面 / 装配事件）+ 资源 ×15。**用户给的三个数**：储能 **320 FE**（ZF39 从 240 改的）、每槽 **3 秒**烧完（无论几个物品）、耗电 = **正在加工的物品数 × 80 FE/t**。配方三条：粗矿→**2 锭**、沙子→硅、矿石方块→**3~6 锭**（逐个随机）。**收录范围用户拍板**：「有锭的直接烧 没有的不需要新加」⇒ 粗铀排除、粗锰/粗锂因本项目无对应锭而不收录。**模型摆放变换** `p' = C + R(p + t − C)`（t=(0.5,0,−0.5)、C=(0.5,0,0.5)，局部 +X ↦ `facing.getCounterClockWise()`）—— 四个朝向的烘焙包围盒**数值实测全部吻合** 3×3×高 4.938（§12.6）。探针 `EbfCheck` 在世界里真的盖一遍再拆一遍：**24 项全 [OK]**，并抓出**一个真 bug**（空手 Shift 右键拆解只"跳过"控制器那格 ⇒ 方块留着、机器又掉出来 = 白送一台）；另外 4 项 Audit 失败（2 个未用 import、1 条硬编码中文、B 项的掉落检查）全部修掉。`Loaded 1306 recipes`（电力高炉**没有**合成配方，只能靠结构装配） | 见 §9 |
"""

TODO = u"""- [ ] **0.10 ZF39 电力高炉未在游戏内验证**（用户："重要的来了 真正意义的多方快结构 电力高炉…"）：
      空手 Shift + 右键**原版高炉**，结构成立即成型并加载用户的 OBJ 模型。
      [x] ~~结构相对坐标 / 装配 / 拆解还原 / 配方数量 / 节拍 / 耗电门槛~~ → **已验**：探针 `EbfCheck`
            在 `ServerLevel` 里**真的盖一遍 27 格、成型、再拆解**，**24 项全 `[OK]`**
            （含"25 格变部件格 + 1 格空气""拆解后 26 格全部还原""12 个物品需求 960 FE/t > 缓冲 320 ⇒ 进度不动"
            "粗铀/粗锰/粗锂都没有配方"等反向断言）。取证 `build\\zftools\\check\\zf39_电力高炉取证.log`
      [x] ~~**探针抓到的真 bug**~~：空手 Shift 右键拆解时，控制器那一格原本只是"跳过" ⇒
            **方块原地留着、机器本体又掉出来 = 白送一台**。已改成显式清成空气（改了之后重跑探针仍 24/24）
      [x] ~~Audit 4 项失败~~：2 个未用 import、1 条**硬编码中文**（结构反馈文案改成回传结构化
            `Problem(i,j,y,expected)` + lang 四占位符）、B 项要求方块文件里**文本可见**地调 `MachineDrops`
            ⇒ 把"掉落"与"还原"拆成 `dropEverything()` / `disassemble()` 两个方法
      [x] ~~ModelCheck 误报~~：OBJ 的贴图写在 `.mtl` 的 `map_Kd` 里、不走模型 JSON ⇒
            给 `ModelCheck.py` 加了 `.mtl` 扫描，孤儿提示从 3 条回到 2 条（只剩那两张老孤儿）
      [x] ~~七项交付检查~~ → Audit 失败 0 / 提示 5；LangCheck 4×**174** 失败 0；RecipeCheck 定形 10 失败 0；
            ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
      [x] ~~产物~~ → `release\\PotatoST-0.10.jar` SHA1 `25cf9c4b…`（2,055,964 B），
            **上一版 `13594172…` 作废**
      [ ] **游戏内仍待你验证（这一台最需要你亲自看）**：
      [ ] 按图把 3×3×3 盖起来（一般金属块 / 加热装置 / 接线块 / 铁栏杆 / 铁活版门 + 中间一台原版高炉）
      [ ] 空手 Shift 右键**高炉** ⇒ 成型并**出现 OBJ 模型**；朝向对了没（高炉那一侧 = 模型正方向）
      [ ] ⚠ **模型是"单色渲染"**（你选的）：`model.obj` 里没有任何贴图信息，现在是灰金属色 + 面的明暗。
            想换成你画的样子，给我 `model.mtl` + 贴图 PNG 即可，**不用改代码**
      [ ] 右键 ⇒ 大面板：**12 输入 + 32 输出**，一次显示完（不做翻页）
      [ ] 丢**粗钴/粗镍/粗银/粗铝/原版粗铁铜金** ⇒ 每块出 **2 锭**；丢**矿石方块** ⇒ 出 **3~6 锭**；
            丢**沙子** ⇒ 出硅
      [ ] **粗铀 / 粗锰 / 粗锂放进去不加工**（前两个是数据缺口，见 §12.6 ③）
      [ ] 接大电：储能只有 **320 FE**，一个物品就要 80 FE/t ⇒ 电不够时**进度不动**（这是你要的"接大电"）
      [ ] 产物自动进**紧邻的容器**；空手 Shift 右键控制器 ⇒ 拆解并还原 27 格
      [ ] 破坏**任意一格**（含部件格）⇒ 整体拆解、还原建材、掉出机器与内容物
      [ ] ⓘ **已知代价**：整块模型挂在控制器那一格上，几何体会被塞进它所在的 **16³ 区块段**；
            控制器贴近段边界时可能出现"人在这头、模型在那头被整段剔除"的闪烁。真出现就换 BER（§12.6 ④）
      [ ] ⓘ 电力高炉**没有合成配方**（你只给了结构）：物品只能从拆解拿到，或创造模式取
"""

ADD12 = u"""
### 12.7 ZF39 交付状态

已经做完了。真东西在：`ElectricBlastFurnaceStructure`（结构定义 + 相对坐标）、
`BlastFurnaceRecipes`（三条配方，纯函数）、`ElectricBlastFurnaceBlock` / `...PartBlock`、
`ElectricBlastFurnaceBlockEntity`（12 入 32 出、320 FE、3 秒/槽、驱动邻接容器）、
`ElectricBlastFurnaceMenu` + `client/ElectricBlastFurnaceScreen`（196×234 大面板）、
`BlastFurnaceAssembly`（空手 Shift 右键）。

与 §12.3/§12.6 相比有三处**落地时的调整**，都记在上面 §5 的 ZF39 行里：
① 掉落与还原拆成两个方法（Audit B 项的文本检查要求）；
② 结构反馈改成回传结构化数据（Audit E 项禁止硬编码中文）；
③ `ModelCheck.py` 增加了 `.mtl` 扫描（OBJ 的贴图不走模型 JSON）。
"""

with io.open(ARCH, "r", encoding="utf-8") as f:
    cur = f.read()

if "| ZF39 |" in cur:
    print("[SKIP] 档案里已有 ZF39 行")
else:
    # §5 行：插在 ZF38 行之后
    idx = cur.find(u"| ZF38 |")
    end = cur.find("\n", idx) + 1
    cur = cur[:end] + ROW + cur[end:]
    # §9：插在 ZF38 待办之前
    idx = cur.find(u"- [ ] **0.10 ZF38 低级发电机未在游戏内验证**")
    cur = cur[:idx] + TODO + cur[idx:]
    # §12.7：追加到最后
    cur = cur + ADD12
    with io.open(ARCH, "w", encoding="utf-8", newline="") as f:
        f.write(cur)
    print("[OK] 档案已更新（§5 ZF39 行 + §9 待办 + §12.7）")

# ---------- 收尾备份 ----------
NEW_FILES = [
    r"src\main\java\com\potatost\mod\BlastFurnaceRecipes.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceStructure.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceBlock.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnacePartBlock.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceBlockEntity.java",
    r"src\main\java\com\potatost\mod\ElectricBlastFurnaceMenu.java",
    r"src\main\java\com\potatost\mod\client\ElectricBlastFurnaceScreen.java",
    r"src\main\java\com\potatost\mod\BlastFurnaceAssembly.java",
    r"src\main\resources\assets\potato_s_t\blockstates\electric_blast_furnace.json",
    r"src\main\resources\assets\potato_s_t\blockstates\electric_blast_furnace_part.json",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace.mtl",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_south.obj",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.obj",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_east.obj",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_west.obj",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_south.json",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_north.json",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_east.json",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_west.json",
    r"src\main\resources\assets\potato_s_t\models\block\electric_blast_furnace_part.json",
    r"src\main\resources\assets\potato_s_t\models\item\electric_blast_furnace.json",
    r"src\main\resources\assets\potato_s_t\textures\block\electric_blast_furnace.png",
    r"src\main\resources\assets\potato_s_t\textures\item\electric_blast_furnace.png",
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
dst = os.path.join(BK, "新增文件")
for rel in NEW_FILES:
    d = os.path.join(dst, rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(os.path.join(PROJ, rel), d)
for s in ("_zf39_backup.ps1", "_zf39_apply.py", "_zf39_fix_lang.py", "_zf39_notes.py",
          "_zf39_archive.py", "MakeBlastFurnaceModel.py", "EbfCheck.java"):
    src = os.path.join(PROJ, "build", "zftools", s)
    if not os.path.exists(src):
        src = os.path.join(PROJ, "build", "zftools", "check", s)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(dst, s))
for rel in CHANGED:
    shutil.copy2(os.path.join(PROJ, rel), os.path.join(BK, "改后_" + os.path.basename(rel)))
shutil.copy2(os.path.join(PROJ, "release", "PotatoST-0.10.jar"),
             os.path.join(BK, "_改后_PotatoST-0.10.jar"))


def sha(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


bad = sum(1 for rel in NEW_FILES
          if sha(os.path.join(PROJ, rel)) != sha(os.path.join(dst, rel)))
print("新增文件 %d 个，副本校验不一致 %d 个" % (len(NEW_FILES), bad))

note = u"""ZF39：电力高炉（本项目第一个真正的多方块结构）
========================================================
备份时刻：2026-09-19 02:5x（**动手之前**建的，清单 13 项交叉核对通过）

用户原话
--------
  「重要的来了 真正意义的多方快结构 电力高炉 …（三层 3×3 的九宫格，高炉在最前排正中）…
   空手shift+高炉如果成立则这些方块变成 电力高炉 加载此模型 obj为模型文件 （高炉那一侧为正方向）
   电力高炉储能240Fe（ZF39 改成 **320 FE**）整体还是借鉴沉浸工程
   右键打开gui 12个输入槽 32个输出槽 可能要做成下拉式 要不然显示不全
   当然检测有紧邻的容器会把输出物放在容器里
   配方暂且 1全粗矿 变成 2份对应的锭 3s一组 耗电量=熔炼物品数量*80Fe/t
   2硅（同原版高炉）3全粗矿补充 包括之前没有配方的钴等（不包括粗铀）
   4.原矿 一个烧制成3-6个原矿对应的锭」

交付了什么
----------
  Java ×8：BlastFurnaceRecipes / ElectricBlastFurnaceStructure / ...Block / ...PartBlock /
           ...BlockEntity / ...Menu / client/...Screen / BlastFurnaceAssembly
  资源 ×23：4 朝向的烘焙 OBJ + MTL + 贴图、5 个模型 JSON、2 个 blockstate、
           物品图标 + 物品模型、lang ×4（各 +4 键）、两张原版标签
  改既有 12 个文件

用户拍板的三条（ZF39）
----------------------
  ① 模型**先用单色渲染**（obj 里没有贴图信息）；
  ② GUI **放大面板一次显示完**（196×234），不做滚动/翻页；
  ③ 「原矿」= **矿石方块 → 3~6 个锭（随机）**，深板岩变体同样对待。
  另：储能 **320 FE**（原话 240 改成 320，确认"是要接大电"）。

探针抓到的真 bug（值得记）
--------------------------
  空手 Shift 右键拆解时，控制器那一格原本在还原循环里 `continue` 跳过 ——
  走 `onRemove` 进来时它本来就是空气，看不出问题；但**直接调用**那条路径下方块还在，
  于是"方块原地留着 + 机器本体又掉出来" = **白送一台**。
  是"拆解后 26 格全部还原"这条断言把它抓出来的。改成显式清成空气后重跑仍 24/24。
  ⇒ 又一次印证 §4.27：**能失败的断言才值钱**。

四道 Audit 失败（都已修）
------------------------
  ① ② 两个未用 import（从模板抄来的 MachineRunningSound / ModSounds）；
  ③ 结构反馈里**硬编码了中文** ⇒ 违反 Audit E 项。改成回传结构化
     `Problem(i, j, y, expected)`，文案走 lang 的四占位符；
  ④ Audit B 项要求"带物品栏的方块实体，其**方块**必须显式调 MachineDrops"（文本级检查）
     ⇒ 把"掉落"与"还原"拆成 `dropEverything()` / `disassemble()`，
     真正那一次 `MachineDrops.dropInventory` 写在 `ElectricBlastFurnaceBlock` 里。

顺带修好的工具问题
------------------
  `ModelCheck.py` 原来只把"模型 JSON + Java 直接引用"算成贴图被引用，
  而 **OBJ 的贴图写在 `.mtl` 的 `map_Kd` 里** ⇒ 新贴图被误报成孤儿。
  已加 `.mtl` 扫描，孤儿提示从 3 条回到 2 条（只剩那两张老孤儿）。

验证到哪一步
------------
  [x] 摆放变换**数值实测**：4 个朝向的烘焙包围盒全部吻合 3×3×高 4.938（§12.6 ②）
  [x] 探针 `EbfCheck`：在 ServerLevel 里真盖一遍再拆一遍，**24 项全 [OK]**
      含"25 格部件格 + 1 格空气""拆解后 26 格全部还原""12 物品需求 960>320 ⇒ 进度不动"
      "粗铀/粗锰/粗锂都没有配方""一槽 3 个粗钴恰好 60 tick 出 6 锭"
      取证 build\\zftools\\check\\zf39_电力高炉取证.log
  [x] runServer：Loaded 1306 recipes（**没变** —— 电力高炉没有合成配方）、Done (0.459s)、零 ERROR
  [x] 七项交付检查：Audit 失败 0 / 提示 5；LangCheck 4×174 失败 0；RecipeCheck 失败 0；
      ModelCheck 失败 0 / 提示 2；JsonCheck 非法 0；SoundCheck 失败 0
  [x] 探针已从源码树删除；产物 jar 内 EbfCheck 条目 = 0
  [x] 产物 release\\PotatoST-0.10.jar SHA1 25cf9c4b…（2,055,964 B）；上一版 13594172… 作废
  [ ] **游戏内未验**：造型朝向、单色模型好不好看、大面板、各条配方、接大电、
      产物进邻接容器、拆解还原 —— 清单在档案 §9「0.10 ZF39」

已知代价 / 留给下一轮
---------------------
  · 整块 OBJ 挂在控制器那一格上 ⇒ 几何体会被分到它所在的 16³ 区块段，
    控制器贴近段边界时可能出现"人在这头、模型在那头被整段剔除"的闪烁。
    真出现就换 BER（§12.6 ④ 有说明）。
  · 模型是单色占位；用户补 `.mtl` + 贴图即可换皮，不用改代码。
  · 电力高炉**没有合成配方**（用户只给了结构），物品只能拆解获得或创造取。

回退办法
--------
  删 新增文件\\ 里的 23 个文件（Java 8 + 资源 15），把本目录根部的 12 个改前副本覆盖回去，
  成品 jar 用 _改前_PotatoST-0.10.jar。
"""
io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n").write(note)
print("[OK] 已写 _说明.txt")
