# -*- coding: utf-8 -*-
"""ZF39：把这一轮**已经证实的事实**补进档案 §12，并写 zf39_pre\\_说明.txt。

本阶段没有交付任何改动（源码树已逐字节回到 ZF38，重建 jar SHA1 与已发布的一致），
所以档案只更新「设计稿」那一节，不写 §5 流水线行、不写 §9 待办。
"""
import io
import os

PROJ = r"E:\PotatoST"
BK = r"C:\Users\Administrator\Desktop\PotatoST救援_20260917_183054\zf39_pre"
ARCH = os.path.join(PROJ, r"docs\开发档案.md")

ADD = u"""
### 12.5 用户已确认的三条（ZF39 问过、已答复）

| 问题 | 答复 |
|---|---|
| 模型没有贴图怎么办 | **先用单色渲染**（以后要换贴图只需换 `.mtl` + 贴图，不动代码） |
| 80 个槽位怎么放 | **放大面板一次显示完**（约 200×250，沉浸工程那种），不做滚动/翻页 |
| 「原矿」指什么 | **矿石方块 → 3~6 个对应锭（随机）**，深板岩变体同样对待 |

### 12.6 ZF39 已实测/已推导的硬事实（下一轮直接照这个写，不用再查）

**① NeoForge 的 OBJ 单位与坐标系**（读 `neoforge-21.1.235-sources.jar` 里的
`ObjModel.java` / `ObjLoader.java` / `ObjMaterialLibrary.java`）：

- `ObjModel` 把 OBJ 顶点**原样**塞进 `QuadBakingVertexConsumer`，源码注释写明
  `// The incoming transform is referenced on the center of the block, but our coords are
  referenced on the corner` ⇒ **OBJ 坐标 = 方块角点空间，1 单位 = 1 格**。
  所以实测的 X −1.5…1.5 / Y 0…4.9375 / Z −1.5…1.5 **就是** 3×4.94×3 格。
- 模型 JSON 的 `"model"` 与 `"mtl_override"` 都走 `ResourceLocation.parse` ⇒
  要写**全路径**：`potato_s_t:models/block/<名>.obj` / `.mtl`。
- MTL 的 `map_Kd` 取**该行最后一个 token** 当贴图位置 ⇒ 写 `potato_s_t:block/<名>`。
- 想贴图**不**放在 models 目录下面，必须用 `mtl_override`（否则按 `mtllib` 的名字相对解析）。

**② 摆放变换（数值已验证，不是推的）**

结构在"控制器角点为原点"的局部坐标里是 X∈[−1,2]、Z∈[−2,1]、Y∈[0,3]；
而模型是**居中建模**（X/Z 都是 ±1.5，原点落在控制器角点）。所以烘焙公式是：

```
p' = C + R(p + t − C)
t  = (0.5, 0, −0.5)        # 把模型平移进结构坐标
C  = (0.5, 0, 0.5)         # 控制器方块自身的中心——旋转必须绕它，不能绕角点
R  = 绕 Y 轴，把模型局部 +Z（= 高炉那一侧 = 正方向）转到 facing
```

**⚠ 顺序不能颠倒**：先平移、再绕**方块中心**旋转。绕角点转会把控制器自己转出自己的格子。

`R` 在 Minecraft 方向上的等价说法：**局部 +X ↦ `facing.getCounterClockWise()`**
（实测四种朝向都对：south→EAST、north→WEST、east→NORTH、west→SOUTH）。

`build\\zftools\\MakeBlastFurnaceModel.py` 按这个公式烘出 4 个朝向变体，实测包围盒：

| 变体 | 世界包围盒（相对控制器角点） | 期望 |
|---|---|---|
| `_south` | X −1…2，Z **−2…1** | 往 −Z 长 ✓ |
| `_north` | X −1…2，Z **0…3** | 往 +Z 长 ✓ |
| `_east`  | X **−2…1**，Z −1…2 | 往 −X 长 ✓ |
| `_west`  | X **0…3**，Z −1…2 | 往 +X 长 ✓ |

四个都是正好 3×3、高 0…4.938 ⇒ **变换是对的**（这是能失败的检查：公式错一格，表就不对称）。

**③ 配方表的数据缺口（本项目矿石体系自身的洞，不是疏忽）**

- `raw_manganese` / `manganese_ore` —— **本项目没有"锰锭"这个物品**；
- `raw_lithium` / `lithium_ore` —— 同样**没有锂锭**（锂走的是
  粗锂 → 粉碎 → 锂矿精粉 → 高炉 → 碳酸锂）。
⇒ 用户说的「包括之前没有配方的钴等」= **有锭但没配方**的那批（钴/镍/银），已全部覆盖；
锰与锂**要靠凭空造一个锭才能进配方**，不在本轮范围内。
`raw_uranium` 是用户点名排除的。

**④ 渲染路线的已知代价**

26 个部件格 `RenderShape.INVISIBLE`，整块模型挂在控制器那一格的 blockstate 上
（4 个朝向各一个模型 JSON，`"automatic_culling": false`）。**代价**：
几何体会被塞进控制器所在的那个 **16³ 区块段**，控制器贴近段边界时可能出现
"人在这头、模型在那头却被整段剔除"的闪烁。真出现的话再换成 BER
（`BlockEntityRenderer` 的视锥剔除是按方块实体算的，能绕开）。
"""

with io.open(ARCH, "r", encoding="utf-8") as f:
    cur = f.read()

if "### 12.5" in cur:
    print("[SKIP] 档案里已有 12.5")
else:
    with io.open(ARCH, "w", encoding="utf-8", newline="") as f:
        f.write(cur + ADD)
    print("[OK] 已把 12.5 / 12.6 追加到档案")

note = u"""ZF39：电力高炉（**本轮没有交付改动**）
========================================================
备份时刻：2026-09-19 02:3x（动手前建的，清单 13 项交叉核对通过）

本阶段做了什么
--------------
只做了**勘查与设计**，没有往产物里加任何东西。原因是这台机器比本项目之前
任何一次都大得多（3×3×3 多方块 + 结构检测 + 装配/拆解 + OBJ 渲染 +
44 槽位大面板 + 三族配方），**一轮写不完，硬写会交付一个没验证过的核心功能** ——
那正是 §4.27 刚记下的"假通过"，不能自己再犯一次。

源码树已**逐字节**回到 ZF38
--------------------------
半成品（1 个 Java + 4 个烘焙 OBJ + MTL + 贴图）已移出 `src\\`，
落在 `E:\\PotatoST\\build\\zftools\\_ebf_baked\\`（可用
`build\\zftools\\MakeBlastFurnaceModel.py` 重新生成）。
**验证方式**：重新 `gradlew build` 出来的 jar SHA1 =
`13594172eb68ad909161b0a67face32841ede3ee`，与已发布的 ZF38 **完全相同**
⇒ 树确实干净，产物没有任何变化，`release\\PotatoST-0.10.jar` 不需要重发。

本轮证实的硬事实（都写进档案 §12.5 / §12.6 了，下一轮不用再查）
--------------------------------------------------------------
  · NeoForge 的 OBJ 坐标 = **方块角点空间，1 单位 = 1 格**（读源码得到的）；
    `model` / `mtl_override` 要写全路径；`map_Kd` 取该行最后一个 token。
  · 摆放变换 **p' = C + R(p + t − C)**，t=(0.5,0,−0.5)、C=(0.5,0,0.5)，
    R 的等价说法是"局部 +X ↦ facing.getCounterClockWise()"。
    **四个朝向的包围盒数值实测全部吻合**（3×3、高 0…4.938）—— 这是能失败的检查。
  · 配方表的数据缺口：本项目**没有锰锭、也没有锂锭** ⇒ 锰/锂进不了"粗矿→锭"配方；
    用户说的"包括之前没有配方的钴等"指有锭没配方的那批（钴/镍/银），已能全覆盖。
  · 用户已确认：单色渲染 / 放大面板一次显示完 / 原矿=矿石方块→3~6 锭随机。

下一轮要做的（顺序已排好）
--------------------------
  1 `BlastFurnaceRecipes`（三条配方，纯函数 + 可脱离游戏验算）
  2 `ElectricBlastFurnaceStructure`（27 格模式 + 相对坐标 = masterPos.relative(back,j).relative(right,i−1)）
  3 `ElectricBlastFurnaceBlock`（主方块，带 FACING）/ `...PartBlock`（26 个部件，INVISIBLE）
  4 `ElectricBlastFurnaceBlockEntity`（12 入 + 32 出、240 FE、3s/槽、耗电 = 物品数×80 FE/t、
    产物推给紧邻容器、27 格原始状态存 NBT 以便拆解还原）
  5 `ElectricBlastFurnaceMenu` + `client/ElectricBlastFurnaceScreen`（大面板）
  6 装配：`PlayerInteractEvent.RightClickBlock` 拦原版高炉的空手 Shift 右键
  7 资源：blockstate（4 朝向）/ 模型 JSON（`neoforge:obj`）/ 掉落表 / lang×4 / 两张标签
  8 探针：结构检测 + 配方表 + 节拍 + 耗电，**并且注入 bug 反证**

⚠ 一个量级问题留给用户拍板（也写进 §9 了）
------------------------------------------
「储能 240 FE」配上「耗电 = 熔炼物品数量 × 80 FE/t」⇒ 单个物品时缓冲只有 **3 tick**；
一摞 64 个就是 **5120 FE/t**。这是刻意的"必须接大电"，还是笔误（比如想说 240k）？

回退办法
--------
不需要回退 —— 本阶段没有改动任何既有文件。要清掉痕迹就删
`build\\zftools\\_ebf_baked\\` 与那两个新脚本。
"""

with io.open(os.path.join(BK, "_说明.txt"), "w", encoding="utf-8", newline="\r\n") as f:
    f.write(note)
print("[OK] 已写 zf39_pre\\_说明.txt")
