# ZF164 轮 计划：灌装机 × Mekanism 气体兼容（0.13）

> 用户原话（2026-10-02）：「**mek喷气背包还是不可以灌本mod的氢 你看看能不能做一下兼容
> 或者搞一个流体转化装置 可以把本mod的流体转成同标签的别的mod流体**」
> 承接 ZF162（灌装机已"什么都能放"，`Capabilities.FluidHandler.ITEM` 那条跨 mod 路已通）。

## 一、已查清的事实（recon 2026-10-02，全部有出处）

| 事实 | 出处 |
|---|---|
| Mekanism 10.7.19 的**气体已经并进"化学品"API**：没有 `IGasHandler`/`GasStack` | jar 里只有 `mekanism/api/chemical/*`；`javap mekanism.api.gas.IGasHandler` 报"找不到" |
| 物品侧的能力名是 **`mekanism:chemical_handler`**（不是 `gas_handler`） | `javap -c -p mekanism.common.capabilities.Capabilities`：`ldc "chemical_handler"` + `Mekanism.rl(...)` + `class mekanism/api/chemical/IChemicalHandler` |
| 关键类型 | `mekanism.api.chemical.{IChemicalHandler, ChemicalStack, Chemical, ChemicalUtils}`；`ChemicalStack(Chemical, long)` / `(Holder<Chemical>, long)` |
| "我们的流体 → Mek 气体"的**官方映射**就是旋转冷凝器配方：`mekanism.api.recipes.FluidChemicalToChemicalRecipe` | jar 里的 `mekanism/api/recipes/` 列表；ZF159 探针已实测 `RotaryRecipe#test(我们的氧气)` = true、`getChemicalOutput` = `1 mekanism:oxygen` |
| jar 位置（12.0 MB，MIT 许可——待从 jar 内 `mods.toml` 复核） | `E:\PotatoST\run\client\mods\[通用机械] Mekanism-1.21.1-10.7.19.85.jar`；用户包 `E:\game\pcl快照\.minecraft\versions\科技mod乱炖\mods\` 同名件 |
| ⚠ `run/server/mods` 里**没有** Mek（只有 Patchouli + Create）⇒ 探针要先把 Mek 拷进 `run/server/mods`（跑完删掉、并核对目录回到原样） | 目录实测 |

**结论：用户提的"流体转化装置"解决不了喷气背包** —— 喷气背包吃的是 Mek 的**化学品（气体）**，
而 Mek 里没有"氢气液体"这种东西可转（旋转冷凝器就是把 `#c:hydrogen` 流体 ↔ `mekanism:hydrogen` 气体）。
所以正解是**在灌装机里加第三条路：物品的 `mekanism:chemical_handler`**，把罐里的我们的氢
按 Mek 自己的旋转配方 1:1 变成 `mekanism:hydrogen` 灌进去。

## 二、方案（待办清单）

1. **软依赖**：`libs/Mekanism-1.21.1-10.7.19.85.jar` + `build.gradle` 的 `compileOnly files(...)`
   （照 JEI 那套；**不进产物 jar**，`_zf149_jar.py` 已有"libs 没被打进包"的判据先例）。
2. 新类 `MekanismChemicalBridge.java`（**只有 Mek 在时才加载**）：
   - `present()` = `ModList.get().isLoaded("mekanism")`；
   - `spaceFor(ItemStack, FluidStack)` / `accepts(...)` / `fill(ItemStack, FluidStack, max)`：
     取 `Capabilities.CHEMICAL`（Mek 的物品能力）→ 用**Mek 自己的** `FluidChemicalToChemicalRecipe`
     （`RecipeManager` 按类型查）把我们的流体映成 `ChemicalStack` → 插入。
     ⚠ 映射**查一次就缓存**（`Map<Fluid, Holder<Chemical>>` + 一份倍率），别每 tick 扫配方表。
   - 安全闸门与 ZF162 那条一样：拷贝上试 → 失败/没变化就**不扣罐、不扣电**。
3. `FillingMachineBlockEntity` 的第三条支路（`tryFillSlot` / `stateOf` / `spaceFor`）：
   顺序 = 自家 `FluidContainerItem` → `Capabilities.FluidHandler.ITEM` → **Mek 化学品**（仅当 Mek 在）。
   诊断说明：能灌时照旧 `FILLING`；Mek 不在/物品不是化学品容器 ⇒ `UNSUPPORTED`（**预计不用加语言键**，
   但如果要区分"这台机器不认识的气体容器"，再议）。
4. **探针 `Zf164Check`**（真开服，**带 Mek 跑**）：假玩家 + 灌装机；
   - 正路：罐里 5000 mB 我们的氢 ＋ 槽里 Mek 喷气背包（`mekanism:jetpack`）⇒ N tick 后
     物品里的 `mekanism:hydrogen` 化学品增加、罐按同量减少、电按罐计扣；
   - 映射判据：直接问 Mek 的旋转配方 `test(我们的氢)` / `getChemicalOutput`；
   - 负对照：Mek 不在时不加载桥（`ModList` 判据）、不是化学品容器的物品照旧 `UNSUPPORTED`、
     气罐/油桶规矩不变；
   - 全物品扫一遍"现在还有哪些物品能被我方氢灌进化学品"（含喷气背包那几个 id）。
5. 常驻门 `_zf164_verify.py` + 反证刀 + 跟平（`_zf162_verify.py` 的 C 段可能要加一条"第三条路"；
   `_zf149_jar.py` 的 class 数会变；语言键预计不变 ⇒ 键数门不用动）。
6. 文档（§4.171 + §5 行 + §9 + 交接 §6 第 36 条 + 英文公告）+ 重打成品 + 哈希三处联动 + 提交推送。

## 三、要用户拍板 / 已按默认走的两点

1. **把 Mekanism 作为编译期依赖**（`libs/` 里放 12 MB 的 jar，MIT）：照 JEI 的先例走；
   若用户不想把 jar 进仓，可改成"构建脚本从 `run/client/mods` 或用户包路径取"，但那样别人机器上编不过。
   → **默认：进 `libs/` 并提交**（与 JEI 同口径）。
2. **Mek 的什么气体能灌**：默认**只认 Mek 自己的旋转配方给得出的那些**（我们的氢/氧/氯/硫酸），
   不硬写气体名 —— "同标签"这条口径由 Mek 自己的配方说了算。
