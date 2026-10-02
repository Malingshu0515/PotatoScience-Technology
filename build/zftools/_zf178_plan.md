# ZF178 计划：磁铁块 + 粗矿块（用户原话见下）

> 用户原话：「**先搞一个磁铁块9磁铁合1个（反过来也一样1块分解9磁铁）然后把所有粗矿都加个块形式
> （锂和锰钛振金不需要）参考粗矿本来的风格和原版粗矿块的风格 可以自己画吧（不要吃白饭了）**」

## 一、要做什么（清单）

| # | 方块 id | 配方（双向） |
|---|---|---|
| 1 | `magnet_block`（磁铁块） | 9 `magnet` ↔ 1 块；1 块 → 9 `magnet` |
| 2 | `raw_aluminum_block`（粗铝块） | 9 `raw_aluminum` ↔ 1 块；1 块 → 9 |
| 3 | `raw_cobalt_block`（粗钴块） | 9 `raw_cobalt` ↔ 1 块；1 块 → 9 |
| 4 | `raw_nickel_block`（粗镍块） | 9 `raw_nickel` ↔ 1 块；1 块 → 9 |
| 5 | `raw_silver_block`（粗银块） | 9 `raw_silver` ↔ 1 块；1 块 → 9 |
| 6 | `raw_tungsten_block`（粗钨块） | 9 `raw_tungsten` ↔ 1 块；1 块 → 9 |
| 7 | `raw_uranium_block`（粗铀块） | 9 `raw_uranium` ↔ 1 块；1 块 → 9 |

**不做块**：`raw_lithium` / `raw_manganese` / `raw_titanium` / `raw_vibranium`（用户点名不需要）。

⇒ 共 **7 个方块 + 14 条配方 + 7 张贴图（自己画）+ 7 份 loot table + 7 个语言键 ×5 + tag**。

## 二、已侦察到的事实（下一轮直接用，不用再查）

- **粗矿物品**是 `PotatoSTOres` 里 `raw("raw_<metal>")` 注册的（`ModItems` 只管振金那份）：
  `raw_aluminum` / `raw_cobalt` / `raw_nickel` / `raw_silver` / `raw_tungsten` / `raw_uranium` /
  `raw_lithium` / `raw_manganese` / `raw_titanium` / `raw_vibranium`（贴图都在 `textures\item\raw_*.png`）。
- `PotatoSTOres` 已有：`ORES` / `ORE_ITEMS` 两个 DeferredRegister、`ALL_ORE_ITEMS`（**创造页自动收**）、
  `ore(name, sound, hardness)` 与 `raw(name)` 两个私有工厂 ★ **新方块就照 `ore()` 写一个 `rawBlock()`，
  注册进 `ALL_ORE_ITEMS` 即可自动上创造页**。
- **装饰金属块**（磁铁块照它）：`ModBlocks.decorativeMetalBlock()` = `strength(5.0F, 6.0F)` +
  `SoundType.METAL` + `requiresCorrectToolForDrops()`；块物品是裸 `BlockItem`；创造页要在 `ModItems` 里加一行。
- **loot table**：每个方块一份 `data\potato_s_t\loot_table\blocks\<id>.json`，照
  `advanced_metal_block.json` 抄（`survives_explosion` + `minecraft:item` + `random_sequence: potato_s_t:blocks/<id>`）。
- **配方生成器** `build\zftools\_zf45_recipes.py`：
  - 9→1 走 `RECIPES`（shaped，3×3 同一种料）；
  - 1→9 走 `SHAPELESS`（`dict(name=..., category="misc", ingredients=[("item", "potato_s_t:<item>")], result=("potato_s_t:<item>", 9))`，
    现成例子就是 `%s_nugget` 那批）；
  - 生成器会自检"同一个产物写了两条配方" —— 9→1 与 1→9 的**产物不同**（块 vs 9 个），不会冲突。
  - 加完跑 `python build\zftools\_zf45_recipes.py --write`，并**逐字节核对只多出这 14 份**。
- **方块 tag**（两条，都是简单 `{"values": [...]}`）：
  `data\minecraft\tags\block\mineable\pickaxe.json`（镐可挖）、
  `data\minecraft\tags\block\needs_stone_tool.json`（要石镐以上）—— 7 个新方块都加进去。
- **语言键**：`block.potato_s_t.<id>`（7 个 ×5 份 lang）；工程有 `_zf123_langaudit.py` 会查"每个注册 id 都有键"。

## 三、贴图（用户要求：自己画）

- 7 张 16×16 RGBA PNG，放 `textures\block\`：`magnet_block.png` + `raw_{aluminum,cobalt,nickel,silver,tungsten,uranium}_block.png`。
- 风格：**石头底 + 矿物团块**（原版粗矿块的感觉），矿斑配色**从对应 `textures\item\raw_<metal>.png` 采样**，
  磁铁块采样 `magnet.png`（建议深灰铁底 + 红色磁极斑）。
- ⚠ 工程有门会查贴图必须 **16×16 / 8 位 / 不透明**（`_zf73_verify.py` B1/B2 那类）。
- 已交给子代理（`build\zftools\_zf178_textures.py` 生成，附带自检）；**收到后我要用 `read_image` 亲眼验**。

## 四、收尾（照 ZF166~ZF176 那套）

1. 编译 → 2. 常驻门 `_zf178_verify.py`（7 方块注册/模型/贴图/loot/14 配方/7 键/创造页）→ 3. 反证刀 →
4. 跟平（`_zf178_retarget.py`：方块物品数 +7、配方数 +14、键数 +7）→ 5. 文档（§4.178 + §5 行 + §9 + 交接 + 公告）
→ 6. 重打成品 + 哈希三处联动 → 7. 提交推送（网络间歇，必要时"逐个提交推"）。

## 五、当前状态

- ✅ 侦察完成（本文件）
- 🔄 贴图与 21 份资源 JSON：子代理在做
- ⬜ Java（7 方块 + 7 块物品 + 创造页）、7 loot table、14 配方、7×5 语言键、2 个 tag
- ⬜ 门/反证刀/跟平/文档/重打/提交
