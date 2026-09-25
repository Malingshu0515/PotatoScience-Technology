# -*- coding: utf-8 -*-
u"""_zf78_docs.py —— ZF78 的四份文档一次写完（锚点断言正好命中 1 次，不中就不写）

  ① `docs/开发档案.md`：§4.46~§4.50 五条新雷 + §5 ZF78 行 + §6.20 新章节 + §9 用户侧验证
  ② `docs/v0.11规划.md`：§5 待决表补第 12/13 条 + §6 记一句"分馏塔已交付"
  ③ `docs/贴图清单.md`：追加手写一节（本轮新增的 3 张占位贴图）
  ④ `docs/UpdateAnnouncement_EN.md`：§4 加分馏塔小节 + §9 Known gaps 补两条
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
DOCS = os.path.join(ROOT, "docs")
fails = []


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


def insert_before(path, anchor, block, label):
    t = read(path)
    hits = t.count(anchor)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    write(path, t.replace(anchor, block + anchor, 1))
    print(u"  [OK]   %s（+%d 字符）" % (label, len(block)))


def insert_after_line(path, anchor, block, label):
    t = read(path)
    hits = t.count(anchor)
    if hits != 1:
        fails.append(u"%s：锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    i = t.index(anchor)
    eol = t.index(u"\n", i) + 1
    write(path, t[:eol] + block + t[eol:])
    print(u"  [OK]   %s（+%d 字符）" % (label, len(block)))


def append(path, block, label):
    t = read(path)
    if not t.endswith(u"\n"):
        t += u"\n"
    write(path, t + block)
    print(u"  [OK]   %s（+%d 字符）" % (label, len(block)))


def replace_once(path, old, new, label):
    t = read(path)
    hits = t.count(old)
    if hits != 1:
        fails.append(u"%s：替换锚点命中 %d 次（必须 1 次）" % (label, hits))
        return
    write(path, t.replace(old, new, 1))
    print(u"  [OK]   %s" % label)


# ================= ① 开发档案 =================

TRAPS = u"""### 4.46 【编译雷】流体的 `Properties` **不能写在字段初始化式里** —— 自引用 + 非法前向引用（0.11 ZF78）

新增流体时最容易照抄的一行是三种气体那两行：

```java
public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> DIESEL =
        FLUIDS.register("diesel", () -> new BaseFlowingFluid.Source(
                new BaseFlowingFluid.Properties(DIESEL_TYPE, DIESEL, FLOWING_DIESEL)));
```

javac 当场两条错：**「自引用」**（`DIESEL` 的初始化式里用了 `DIESEL`）与
**「非法前向引用」**（`FLOWING_DIESEL` 还没声明）。**同一行里同时踩两个**。

⇒ 规矩：照气体那套老写法，走一个**私有静态方法**（方法体里的前向引用是合法的）：

```java
private static BaseFlowingFluid.Properties dieselProperties() {
    return new BaseFlowingFluid.Properties(DIESEL_TYPE, DIESEL, FLOWING_DIESEL);
}
```

ZF78 一次加四种流体，这条错**连报四遍**（8 个注册项全红），别以为是别的问题。

### 4.47 【实现雷】`FluidTank.fill()` 读的是**构造时钉死的 `capacity` 字段**，不是 `getCapacity()`（0.11 ZF78）

分馏塔的罐容量随结构变（石油 12 桶 × 塔数、产品 2.5 桶 × 塔数）⇒ 第一反应是"继承
NeoForge 的 `FluidTank`、重写 `getCapacity()`"。**不够**：`FluidTank` 里写的是

```java
if (fluid.isEmpty()) return Math.min(capacity, resource.getAmount());   // ← 字段，不是 getter
int filled = capacity - fluid.getAmount();
public int getSpace() { return Math.max(0, capacity - fluid.getAmount()); }
```

⇒ 只重写 getter 的话：界面显示 12000、实际能灌 12000×4（界面与真实容量不一致，
而且**看不出来**，因为两边都不报错）。

**规矩**：容量要动，就必须把**所有读 `capacity` 的地方**一起重写 —— ZF78 的
`ScaledTank` 重写了 `getCapacity()` + `getSpace()` + `fill()` 三处，`drain`/存读可以继承。

**顺带一条设计口径**：塔数变少时**不销毁**已存的流体（存量可以一时高于容量，
`getSpace()` 返回 0 ⇒ 只进不出地"堵住"，等抽走就恢复）。

### 4.48 【实现雷】`ContainerData` 的载荷是**短整型**（`writeShort`）⇒ 超过 32767 必须分片（0.11 ZF78）

`AbstractContainerMenu` 同步 `ContainerData` 走的是 `ClientboundContainerSetDataPacket`，
它 `writeShort(value)` ⇒ **值域只有 ±32767**，超了客户端读到的是负数（界面显示负的液量）。

ZF78 的实际算账：石油罐 `12 桶 × 最多 4 塔 = 48000` ⇒ **必须分片**；
能量 `8096 × 4 = 32384` 刚好还在范围内 ⇒ **不用分**（顺手多拆两个键反而更难维护）。

本工程早有先例（测试储罐的 `DATA_STOCK_LOW/MID/HIGH`，各 15 位），ZF78 照做：
`DATA_OIL_LOW` + `DATA_OIL_HIGH`（`& 0x7FFF` / `>>> 15`），界面侧拼回来。

⇒ 规矩：**任何要塞进 `ContainerData` 的量，先算「上限 × 最大倍率」**，>32767 就分片。

### 4.49 【实现雷】`CompoundTag#getCompound("k")` 在**缺键**时返回一个**没挂到父标签上的新对象**（0.11 ZF78）

存罐时最顺手的写法是

```java
tanks[i].writeToNBT(registries, tag.getCompound("Tank" + i));   // ⚠ 静默丢数据
```

缺键时 `getCompound` 会**新建**一个空的 `CompoundTag` 返回给你 —— 它没被挂到 `tag` 上，
你往里写的东西**随写随扔**：存档里没有罐、读档回来全空，**不报任何错**。
正确写法是"自己 new 一个，写完再 put 回去"：

```java
CompoundTag child = new CompoundTag();
tanks[i].writeToNBT(registries, child);
tag.put("Tank" + i, child);
```

`readFromNBT(registries, tag.getCompound(key))` 那一侧**没有这个坑**（它只读不写回）。
本工程之前那批机器的 `saveAdditional` 全是平铺的 int/string，一直没碰到；
ZF78 第一次用 `writeToNBT/readFromNBT` 就踩上了 ⇒ 探针里专门加了一条**存读往返**断言。

### 4.50 【工具雷】探针的中文输出会被 JVM 按 GBK 打乱 ⇒ 自己写 UTF-8 报告，且**必须用绝对路径**（0.11 ZF78）

`runServer` 重定向出来的日志里，探针那几百行中文全变成 `锟斤拷`（JVM 的 stdout 用平台默认
编码 = GBK），英文与数字没事 ⇒ FAIL 条目只能靠数字与上下文猜，**证据质量直接掉档**。
改法：探针自己持一个 `StringBuilder`，结束时用
`new OutputStreamWriter(new FileOutputStream(path), StandardCharsets.UTF_8)` 落一份报告。
两个坑：① 路径必须**绝对**（`runServer` 的 JVM 工作目录不是工程根 ⇒ 相对路径直接
`FileNotFoundException`，报告根本没落下来，而控制台只会多一行英文报错）；
② 报告要在 `server.halt()` **之前**写。

"""

ROW_ZF78 = u"""| ZF78 | **补建 `zf78_pre`**（⚠ **本轮我漏了"动第一个字节前先抄一份"**：8 个改前件是改完**反向套用本次编辑**重建的，并按 ZF65 先例用「换回源码树编译 → 与 ZF77 成品 jar 逐字节比」证明忠实 —— `_zf78_precheck.py` 实测 **8 个类 / 31 个 class 全部相同、0 不同、0 缺失**；第一版 `ModBlocks` 只删了标题行、编译当场报「找不到符号」⇒ 错的重建活不过编译。改后 16 份 java 另存 `新增文件\\`，`MANIFEST.md` 里如实写清"注释不参与字节码 ⇒ 逐字节相同只证明逻辑一致"） | 0.11：**分馏塔三件套**（用户给了完整规格：「分馏塔操作器 / 分馏塔控制器 / 分馏塔：多方块结构 4×4×7」）。① **分馏塔**：4×4×7 的**纯形状**多方块（第 1/2 层四角一般金属块、第 3/5 层角=一般+边=耐热+正中 2×2 加热装置、第 4/6 层一圈耐热、第 7 层整块一般金属，图纸上画空的格子必须是空气）——**不换方块、不建部件格、没有方块实体**，只由控制器逐格比对（与电力高炉那套"换部件格 + 挂 OBJ"完全不同，因为用户对控制器的要求只有"数数量"这一条）；图纸四向对称 ⇒ 天然不需要朝向。② **控制器** `distillation_controller`：每 20 tick 在 **32×32×10**（水平 ±16、竖直 −3..+6）窗口里数塔，把**数量**推给**所有相邻**操作器；**先看有没有相邻操作器、没有就不扫**（省掉 3364 个锚点）；邻居一变立刻重扫；数量**不存盘**（算出来的，旧存档不会残留假数字）；**故意没有 GUI、没有登记任何能力**（用户原话「控制器只负责发送检测的分馏塔数量给操作器」）。③ **操作器** `distillation_operator`：用户拍板**每座塔各跑一份**（我按候选给他选，他选了缩放那版）⇒ 每 tick **每塔** 8 mB 石油 + 8096 FE → 3 柴油 + 2 石脑油 + 2 汽油 + 1 液化石油气（进 8 出 8 物料平衡）、每 **5 tick 每塔**出 1 块**沥青**；容量**按塔数缩放**：能量 8096 FE、石油 12 桶、每种产品 2.5 桶（最多认 **4 座**塔，控制器报多少都夹到 4）；**有红石信号才分馏**（与粉碎机/盐分解构器相反）；沥青槽满 64 就**停机**（快满时只出装得下的那几块，**不销毁物品**）；五罐暴露成一个 `IFluidHandler`：**只有石油罐收料、四个产品罐是出口**。④ **四种新流体**（用户给了 4 张 16×16 贴图，我转成本工程 PNG）：`diesel` / `naphtha` / `gasoline` / `lpg`，共用**一个** `liquidType` 工厂（不抄四遍 `initializeClient`：审计 D 项盯复制粘贴）、**不注册液体方块也不给桶**（只在罐/管道里）、各挂一张 `c:` 标签（ZF74 立的那条硬规矩）；**液化石油气按"液体"注册**（"液化"二字），要改成气体只需把它的标签挪进 `c:gaseous`。⑤ **大 UI**（用户原话「类似于电力高炉的大 UI」）：196×202 零贴图面板，从左到右 **能量条(26) → 石油(44) → 柴油(66) → 石脑油(88) → 汽油(110) → 液化石油气(132)**，**沥青槽在右下角靠里 (158,92)**、玩家背包 y=118，左上两行字显示「分馏塔：N / 4 座」+ 七种状态之一；为此给 `EnergyBarPart` / `FluidTankPart` 各加了**一个上限/容量 supplier 的重载**（容量随塔数变，不能是常量）。⑥ **首次遇到的三个雷**（都已立条）：`FluidTank.fill()` 读的是字段不是 getter（§4.47）、`ContainerData` 是短整型 ⇒ 48000 的石油必须分片（§4.48）、`CompoundTag#getCompound` 缺键时返回游离对象 ⇒ 存盘静默丢数据（§4.49）；另外两条工具/编译雷见 §4.46（流体 `Properties` 自引用）与 §4.50（探针中文被 GBK 打乱 ⇒ 自己写 UTF-8 报告且要绝对路径）。⑦ **探针 `DistillationCheck` 99 项全 [OK]**：图纸 7 层 × 16 格逐格（含 32/40/8/32 的材料账）、窗口边界（+12 进 / +13 出、−3 进 / −4 出、+1 出）、空腔塞石头即失效、实心金属不误判、控制器→操作器推送、5 座塔夹到 4、拆掉控制器 20 tick 内自愈归零、容量缩放（0/2/4 塔 × 石油/产品/能量）、每 tick 公式逐项、物料平衡、5 tick 出沥青、沥青 64 停机、62+4 塔只出 2 块不销毁、产品罐满/没油/没电/没红石/没塔五种停机、存读往返、石油 48000 分片还原；**第一轮 6 条 FAIL 全是我探针自己写错**（塔摆在窗口外、实心金属那组控制器位置、`8096×2` 算成 16128、沥青状态晚一拍），修完复跑 0 失败。⑧ 新写常驻 `_zf78_verify.py`；发布见 §9 | 见 §6.20 / §9 |

"""

SEC_620 = u"""### 6.20 加一台「多方块检测型 + 大 UI」的机器（0.11 ZF78 实例：分馏塔三件套）

与电力高炉/合金炉那两套（**换部件格 + 挂 OBJ 模型**）不同，这一套是"**只检测、不动世界**"的
多方块 —— 结构里全是普通方块，机器自己只负责**数**。要动的地方（照 ZF78 抄）：

| # | 动什么 | 落点 |
|---|---|---|
| 1 | 结构定义（图纸 + 检测窗口 + 去重） | `DistillationTowerStructure.java`：`Kind` 枚举 + `kindOf(x,z,y)` 解析式图纸 + `isValidTower` + `findTowers`（锚点只取整塔放得下的位置，先到先得去重） |
| 2 | 控制器方块 | `DistillationControllerBlock.java`：`BaseEntityBlock` + `newBlockEntity` + `getTicker` + `getDrops` + `neighborChanged`（**没有 GUI**：不写 `useWithoutItem`） |
| 3 | 控制器方块实体 | `DistillationControllerBlockEntity.java`：`SCAN_INTERVAL` 节流 + `requestRescan()` + **先找相邻操作器、一个都没有就不扫** + `operator.setTowerCount(n)` |
| 4 | 操作器方块 | `DistillationOperatorBlock.java`：`useWithoutItem` → `openMenu`、`onRemove` → `MachineDrops.dropInventory` |
| 5 | 操作器方块实体 | `DistillationOperatorBlockEntity.java`：罐（容量随结构变 ⇒ 见 §4.47）+ `MachineEnergyStorage.receiveOnly` + 红石判定 + 每 tick 公式 + 停机状态机 + `ContainerData`（>32767 要分片，§4.48）+ `saveAdditional/loadAdditional`（§4.49 的坑） |
| 6 | 菜单 / 界面 | `DistillationOperatorMenu.java`（槽位坐标与界面共用常量）+ `client/DistillationOperatorScreen.java`（`MachineScreen` 的 `parts` 清单） |
| 7 | 注册 5 处 | `ModBlocks`（方块 ×2 + 方块实体类型 ×2）、`ModItems`（物品 ×2~3 + 创造页）、`ModMenus`、`PotatoST`（能力，**控制器不给**）、`PotatoSTClient`（界面） |
| 8 | 资源 | `blockstates/` ×2、`models/block/` ×2、`models/item/` ×2（+ 新物品的模型）、方块贴图 ×2（顶/侧） |
| 9 | 语言 ×4 | 方块名 / 物品名 / 流体名（`fluid_type.` 与 `fluid.`）/ GUI 状态行 / Shift 说明 —— **四份键数必须相等**（LangCheck） |
| 10 | 标签 | 新方块进 `mineable/pickaxe`；新流体**必须**各挂一张 `c:` 标签（ZF74 的硬规矩） |
| 11 | 界面部件 | 如果**容量/上限随结构变**，给部件加一个 supplier 重载（ZF78 给 `EnergyBarPart` 与 `FluidTankPart` 各加一个），别新写一份 |
| 12 | 验收 | 探针（世界建/拆/边界/公式/停机/存读）+ 常驻 `_zf78_verify.py`（图纸常量、窗口边界、每 tick 常量、能力条数、语言键数、成品内容） |

**一条口径**：这类机器"塔本身"没有方块实体、也不会被换掉 ⇒ 玩家随便拆一格，下一秒塔数自己变，
**不需要** `disassemble`/还原那套（那是换部件格那两台的复杂度）。

"""

SEC_9 = u"""- [ ] **ZF78：等你试分馏塔三件套**（成品见本轮汇报）。要看的：
      ① **塔**：4×4×7 按图纸摆（第 1/2 层**四角**一般金属块；第 3/5 层＝角一般金属块 + 边耐热金属块 +
         正中 2×2 加热装置；第 4/6 层＝一圈耐热金属块；第 7 层＝4×4 全一般金属块；
         **图纸画空的格子必须是空气**）；② **控制器**贴着塔放（32×32×10 格内）、**操作器贴着控制器**放
         （六面相邻），右击操作器开界面 ⇒ 左上应写「分馏塔：N / 4 座」；③ **给红石信号**才开始分馏
         （拉杆/红石块都行），界面第二行会写状态（分馏中 / 无红石信号 / 石油不足 / 电力不足……）；
      ④ 界面从左到右＝**能量条 · 石油 · 柴油 · 石脑油 · 汽油 · 液化石油气**，**沥青槽在右下角**；
      ⑤ 数字：每座塔每 tick 吃 **8 mB 原油 + 8096 FE**、出 **3 柴油 + 2 石脑油 + 2 汽油 + 1 液化石油气**，
         每 **5 tick 出 1 块沥青**（每塔）；容量是**每塔** 能量 8096 FE / 石油 12 桶 / 每种产品 2.5 桶；
      ⑥ **接管道**：石油罐能进料，四个产品罐只能抽（往里灌会被拒），罐能连泵/管道/JEI 里能看到四种流体。
- [ ] ZF78 说明：**这两个新方块现在都没有合成配方**（创造模式可取，`alloy_smelter` 那台当年也是这样）。
      要配方就把材料告诉我，走生成器加一条（§6.3）。
- [ ] ZF78 说明：**沥青目前没有任何用途** —— 你只说了"产出来、满 64 停机"，没说能干什么，
      所以我**故意没给它挂任何原版功能标签**（当燃料烧、当合成材料都要你点名）。
- [ ] ZF78 说明：四种产品流体**没有桶、也不能倒进世界**（故意不注册液体方块）—— 只能待在罐/管道里；
      要"能装桶/能倒地上"说一声（原油那套是现成的模板）。
- [ ] ZF78 说明：**拆操作器会丢掉罐里的流体**（本模组所有机器一贯如此，没有"把罐装进掉落物"的机制），
      但**沥青槽里的沥青会掉出来**。拆机前先把罐抽空。
- [ ] ZF78 提醒：能量缓冲**正好等于一 tick 的消耗**（8096 FE × 塔数）⇒ 供电必须**连续**，
      断续供电会走走停停（这是你给的数：一座塔提供 8096 FE、每 tick 也正好吃 8096 FE）。
      觉得太苛刻（比如想要 10 tick 的缓冲）说一声，改一个常量。
- [ ] **ZF78 补记（我的失误）**：本轮**漏了"动手前先建 `zf78_pre`"**（§10 的规矩）。
      8 个改前件是改完**反向套用编辑**重建的 —— 用「换回源码树编译 → 与 ZF77 成品 jar 逐字节比」
      证明忠实（`_zf78_precheck.py`：8 个类 / **31 个 class 全部相同**）。
      如实边界：**注释不参与字节码**，所以只证明"逻辑一致"；`新增文件\\` 里是本轮**改后**的 16 份 java。
      详见 `C:\\PotatoST救援\\zf78_pre\\MANIFEST.md`。
"""

PLAN_HEAD_OLD = u"## 5. 待你拍板（11 条：**⑤⑩ 已于 2026-09-24 拍板**，其余 9 条不回复就按括号里的默认值走）"
PLAN_HEAD_NEW = u"## 5. 待你拍板（13 条：**⑤⑩⑫ 已于 2026-09-24 拍板**，其余 10 条不回复就按括号里的默认值走）"

PLAN_ROWS = u"""| 12 | 分馏速率：**每座塔各跑一份**还是**总速率固定** | ✅ **已定（你 09-24）**：每座塔各跑一份 ⇒ N 塔 = 8N mB 石油 + 8096N FE/t、产物 3N/2N/2N/1N、沥青每 5t 出 N 块；容量也按「一个分馏塔提供 X」× N |
| 13 | 四种产品（柴油/石脑油/汽油/液化石油气）要不要桶 / 能不能倒进世界 | **本轮不做**（只在罐与管道里）；要"能装桶/能倒地上"照原油那套加一遍即可 |
"""

PLAN_TAIL_NOTE = u"""
**ZF78 已交付**：分馏塔三件套（结构检测型多方块 + 控制器 + 操作器大 UI）+ 四种产品流体 + 沥青，
详见 `开发档案.md` §5 的 ZF78 行与 §6.20。**后续部分（分馏塔的更多产物/用途）等你下一段规格。**
"""

ANNOUNCE_TOWER = u"""### Fractional Distillation Tower (new in 0.11)

Three pieces: the **tower** itself, a **controller**, and an **operator** (the machine with the GUI).

- **The tower** is a 4×4×7 shape you build out of ordinary blocks — you need the Common Metal Block
  (layer 1–2 corners, and layer 7 as a full 4×4 cap), the Heat-Resistant Metal Block (the ring on
  layers 4 and 6, plus the edges of layers 3 and 5) and 8 Heaters (the 2×2 centre of layers 3 and 5).
  Every cell that the blueprint draws as empty must really be air. It is rotation-agnostic.
- **The Controller** scans a 32×32×10 box around itself, counts the completed towers and reports that
  number to every Operator placed next to it. It has no GUI and stores nothing.
- **The Operator** is the machine: right-click it for a large, zero-texture panel with five tanks
  (oil → diesel → naphtha → gasoline → LPG, left to right), a vertical energy bar, a bitumen slot in
  the bottom-right corner and a status line. **It only distills while it has a redstone signal.**
- **Numbers (per tower):** every tick it consumes **8 mB of crude oil and 8096 FE**, and produces
  **3 mB diesel + 2 mB naphtha + 2 mB gasoline + 1 mB LPG** (8 in, 8 out). Every 5 ticks it also
  makes **1 Bitumen**. Buffers scale with the tower count: **8096 FE**, **12 buckets of oil** and
  **2.5 buckets per product tank** — up to **4 towers** are recognised.
- **It stops** when the bitumen slot is full (64 and no room left), when a product tank is full, when
  the oil or the power runs out, or when the redstone signal goes away.
- Pipes can feed crude oil in and pull the four products out; the four product fluids are new
  (diesel / naphtha / gasoline / LPG) and each carries its `c:` common tag.

"""

GAPS_OLD_1 = u"- **A few blocks are still creative-only**: the Alloy Smelter Controller, the Lithium Battery,\n  the Advanced Metal Block and the Stable Metal Block have no crafting recipe yet."
GAPS_NEW_1 = u"- **A few blocks are still creative-only**: the Alloy Smelter Controller, the Lithium Battery,\n  the Advanced Metal Block, the Stable Metal Block, the Distillation Tower Controller and the\n  Distillation Tower Operator have no crafting recipe yet."
GAPS_OLD_2 = u"- **Some textures are placeholders** borrowed from vanilla (9 models still do this)."
GAPS_NEW_2 = (u"- **Some textures are placeholders** borrowed from vanilla (9 models still do this); on top of\n"
              u"  that the three new distillation assets are placeholders too — Bitumen is a copy of the vanilla\n"
              u"  gunpowder sprite and the Tower Controller / Operator block textures are generated grey metal.\n"
              u"- **Bitumen has no use yet** (it is deliberately not a fuel and has no recipe).")


def main():
    arch = os.path.join(DOCS, u"开发档案.md")
    print(u"== ① 开发档案 ==")
    insert_before(arch, u"## 5. 版本与 [ZF] 流水线记录", TRAPS, u"§4.46~§4.50 五条新雷")
    insert_after_line(arch, u"| ZF75 | **新建 `zf75_pre`**", ROW_ZF78, u"§5 ZF78 行")
    insert_before(arch, u"## 7. 权威情报来源（怎么查原版行为，别靠记忆）", SEC_620, u"§6.20 新章节")
    insert_after_line(arch,
                      u"      **服务端实测**：新世界正常跑起来 —— `Done (8.183s)!`（修复前是崩在区块生成、客户端卡 0%）。",
                      SEC_9, u"§9 ZF78 用户侧验证")

    plan = os.path.join(DOCS, u"v0.11规划.md")
    print(u"== ② v0.11 规划 ==")
    replace_once(plan, PLAN_HEAD_OLD, PLAN_HEAD_NEW, u"§5 标题（11 条 → 13 条）")
    insert_after_line(plan, u"| 11 | **流体泵允不允许抽原油**", PLAN_ROWS, u"§5 补第 12/13 条")
    insert_before(plan, u"## 7. 贴图需求（预发，你随时可以画；现在先用借的）", PLAN_TAIL_NOTE, u"§6 记一句已交付")

    tex = os.path.join(DOCS, u"贴图清单.md")
    print(u"== ③ 贴图清单 ==")
    append(tex, u"""
---

## ZF78 新增的占位贴图（**要画**）

> ⚠ 这一节是**手写**的：`TextureCheck.py --plan` 只按模型推名字，认不出"这张是占位"。
> 下次重跑 `--plan` 会把它冲掉，我再补回来。

| 放哪 | 文件名 | 是什么 | 现在是什么 |
|---|---|---|---|
| `textures/item/` | `bitumen.png` | 沥青 | **原版火药那张图的副本**（你要求「暂时用火药占位」） |
| `textures/block/` | `distillation_controller_side.png` / `_top.png` | 分馏塔控制器 | 程序生成的灰铁占位（带一道琥珀色热带 + 铆钉） |
| `textures/block/` | `distillation_operator_side.png` / `_top.png` | 分馏塔操作器 | 程序生成的灰铁占位（带青色屏 + 散热格栅） |

另外四种产品流体（柴油 / 石脑油 / 汽油 / 液化石油气）的贴图**是你给的**，
已转成本工程 PNG：`*_still.png` 与 `*_flow.png` 各 4 张（同一种流体两张逐字节相同 ——
与氧气/原油同一条老规矩）。
""", u"追加 ZF78 占位贴图一节")

    ann = os.path.join(DOCS, u"UpdateAnnouncement_EN.md")
    print(u"== ④ 英文公告 ==")
    insert_before(ann, u"### Lithium Battery", ANNOUNCE_TOWER, u"§4 加分馏塔小节")
    replace_once(ann, GAPS_OLD_1, GAPS_NEW_1, u"§9 creative-only 补两个方块")
    replace_once(ann, GAPS_OLD_2, GAPS_NEW_2, u"§9 占位贴图 + 沥青无用途")

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
