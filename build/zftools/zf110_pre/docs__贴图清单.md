# 贴图清单（待画 / 已完成）

> 由 `build/zftools/TextureCheck.py --plan` 生成。**你只要按「放哪」那一列把文件丢进去**，
> 我这边跑一遍 `TextureCheck.py` + `ModelCheck.py` 就能确认。

## 怎么放（三条规矩）

1. **文件名必须是 ASCII**（小写字母/数字/`_`）——`ResourceLocation` 只放行 `[a-z0-9/._-]`，
   中文文件名游戏直接报错（§4.24）。
2. **必须是真 PNG**（别把 webp/jpg 改个后缀）—— 检查会读文件头，不是 PNG 会 FAIL。
3. 方块贴图 **16×16**；物品贴图 **16×16 且背景透明**（32×32 也能用，但游戏按 16×16 渲染，会糊）。

## 放哪：两个目录

- 方块：`src\main\resources\assets\potato_s_t\textures\block\`
- 物品：`src\main\resources\assets\potato_s_t\textures\item\`

## 待画（5 个，现在借的是原版贴图）

| 放哪 | 文件名 | 是什么 | 现在借的 |
|---|---|---|---|
| `textures/item/` | `creative_cable.png` | creative_cable | `minecraft:block/redstone_block` |
| `textures/item/` | `lithium_concentrate.png` | 锂矿精粉 | `minecraft:item/sugar` |
| `textures/item/` | `test_fluid_tank.png` | test_fluid_tank | `minecraft:block/glass`, `minecraft:block/iron_block` |
| `textures/block/` | `creative_cable.png` | 创造模式线缆 | `minecraft:block/redstone_block` |
| `textures/block/` | `test_fluid_tank.png` | 测试流体储罐 | `minecraft:block/glass`, `minecraft:block/iron_block` |

## 已经有自己贴图的（列出来是方便你替换）

| 放哪 | 文件名 | 是什么 |
|---|---|---|
| `textures/block/` | `advanced_metal_block.png` | advanced_metal_block |
| `textures/block/` | `air_separator_side.png`, `air_separator_top.png` | air_separator |
| `textures/block/` | `alloy_smelter.png` | alloy_smelter |
| `textures/item/` | `aluminum_ingot.png` | 铝锭 |
| `textures/block/` | `aluminum_ore.png` | aluminum_ore |
| `textures/item/` | `iron_plate.png` | 铝板 |
| `textures/block/` | `ammonia_synthesis_chamber_side.png`, `ammonia_synthesis_chamber_top.png` | ammonia_synthesis_chamber |
| `textures/block/` | `asphalt_block.png` | asphalt_block |
| `textures/item/` | `bitumen.png` | 沥青 |
| `textures/item/` | `capacitor.png` | 电容 |
| `textures/item/` | `carbon.png` | 碳粉 |
| `textures/item/` | `cobalt_ingot.png` | 钴锭 |
| `textures/block/` | `cobalt_ore.png` | cobalt_ore |
| `textures/item/` | `iron_plate.png` | 钴板 |
| `textures/block/` | `common_metal_block.png` | common_metal_block |
| `textures/item/` | `copper_plate.png` | 铜板 |
| `textures/item/` | `copper_wire.png` | 铜线 |
| `textures/item/` | `copper_wire_spool.png` | 铜线轴 |
| `textures/block/` | `deepslate_cobalt_ore.png` | deepslate_cobalt_ore |
| `textures/block/` | `deepslate_manganese_ore.png` | deepslate_manganese_ore |
| `textures/block/` | `deepslate_nickel_ore.png` | deepslate_nickel_ore |
| `textures/block/` | `deepslate_silver_ore.png` | deepslate_silver_ore |
| `textures/block/` | `deepslate_titanium_ore.png` | deepslate_titanium_ore |
| `textures/block/` | `deepslate_uranium_ore.png` | deepslate_uranium_ore |
| `textures/block/` | `deepslate_wolframite_ore.png` | deepslate_wolframite_ore |
| `textures/item/` | `diesel_bucket.png` | 柴油桶 |
| `textures/block/` | `distillation_controller_side.png`, `distillation_controller_top.png` | distillation_controller |
| `textures/block/` | `distillation_operator_side.png`, `distillation_operator_top.png` | distillation_operator |
| `textures/item/` | `electric_blast_furnace.png` | electric_blast_furnace |
| `textures/block/` | `electrolyzer.png` | electrolyzer |
| `textures/item/` | `empty_spool.png` | 空线轴 |
| `textures/block/` | `filling_machine_front.png`, `filling_machine_side.png`, `filling_machine_top.png` | filling_machine |
| `textures/block/` | `fluid_exchanger.png` | fluid_exchanger |
| `textures/block/` | `fluid_pipe.png` | fluid_pipe |
| `textures/block/` | `fluid_pump.png` | fluid_pump |
| `textures/item/` | `gasoline_bucket.png` | 汽油桶 |
| `textures/block/` | `heat_resistant_metal_block.png` | heat_resistant_metal_block |
| `textures/block/` | `heat_sink.png` | heat_sink |
| `textures/block/` | `heater.png` | heater |
| `textures/item/` | `high_carbon_steel.png` | 高碳钢 |
| `textures/item/` | `high_pressure_tank.png` | 高压气罐 |
| `textures/block/` | `hydraulic_press_side.png`, `hydraulic_press_top.png` | hydraulic_press |
| `textures/block/` | `hydrodesulfurization_chamber_side.png`, `hydrodesulfurization_chamber_top.png` | hydrodesulfurization_chamber |
| `textures/item/` | `iron_plate.png` | 铁板 |
| `textures/item/` | `iron_powder.png` | 铁粉 |
| `textures/item/` | `titanium_ingot.png` | 轻质钛合金 |
| `textures/block/` | `lithium_battery_side.png`, `lithium_battery_top.png` | lithium_battery |
| `textures/item/` | `lithium_carbonate.png` | 碳酸锂 |
| `textures/block/` | `lithium_ore.png` | lithium_ore |
| `textures/block/` | `low_generator_side.png`, `low_generator_top.png` | low_generator |
| `textures/item/` | `magnet.png` | 磁铁 |
| `textures/block/` | `manganese_ore.png` | manganese_ore |
| `textures/block/` | `micro_crusher_side.png`, `micro_crusher_top.png` | micro_crusher |
| `textures/item/` | `music_disc_anvil_of_the_republic.png` | 音乐唱片 |
| `textures/item/` | `music_disc_jasmine_flower.png` | 音乐唱片 |
| `textures/item/` | `nickel_ingot.png` | 镍锭 |
| `textures/block/` | `nickel_ore.png` | nickel_ore |
| `textures/item/` | `iron_plate.png` | 镍板 |
| `textures/item/` | `oil_bucket.png` | 油桶 |
| `textures/item/` | `photovoltaic_component.png` | 光伏原件 |
| `textures/item/` | `power_cable_spool.png` | 动力线缆轴 |
| `textures/block/` | `power_capturer.png` | power_capturer |
| `textures/item/` | `raw_aluminum.png` | 粗铝 |
| `textures/item/` | `raw_cobalt.png` | 粗钴 |
| `textures/item/` | `raw_lithium.png` | 粗锂 |
| `textures/item/` | `raw_manganese.png` | 粗锰 |
| `textures/item/` | `raw_nickel.png` | 粗镍 |
| `textures/item/` | `raw_silver.png` | 粗银 |
| `textures/item/` | `raw_titanium.png` | 粗钛 |
| `textures/item/` | `raw_tungsten.png` | 粗钨 |
| `textures/item/` | `raw_uranium.png` | 粗铀 |
| `textures/block/` | `salt_decomposer_side.png`, `salt_decomposer_top.png` | salt_decomposer |
| `textures/block/` | `salt_dryer.png` | salt_dryer |
| `textures/item/` | `sea_salt.png` | 海盐 |
| `textures/item/` | `silicon.png` | 硅 |
| `textures/item/` | `silver_ingot.png` | 银锭 |
| `textures/block/` | `silver_ore.png` | silver_ore |
| `textures/item/` | `iron_plate.png` | 银板 |
| `textures/item/` | `sodium_chloride.png` | 氯化钠 |
| `textures/block/` | `solar_panel.png` | solar_panel |
| `textures/block/` | `stable_metal_block.png` | stable_metal_block |
| `textures/item/` | `steel_plate.png` | 钢板 |
| `textures/item/` | `sulfur.png` | 硫 |
| `textures/block/` | `terminal.png` | terminal |
| `textures/item/` | `thermal_metal.png` | 热力金属 |
| `textures/item/` | `titanium_alloy_pickaxe.png` | 钛合金镐 |
| `textures/item/` | `titanium_alloy_sword.png` | 钛合金剑 |
| `textures/item/` | `titanium_ingot.png` | 钛锭 |
| `textures/block/` | `titanium_ore.png` | titanium_ore |
| `textures/item/` | `titanium_powder.png` | 钛粉 |
| `textures/item/` | `toner.png` | 墨粉 |
| `textures/item/` | `uranium_ingot.png` | 铀锭 |
| `textures/block/` | `uranium_ore.png` | uranium_ore |
| `textures/block/` | `wiring_block.png` | wiring_block |
| `textures/block/` | `wolframite_ore.png` | wolframite_ore |
| `textures/item/` | `wrench.png` | 扳手 |
| `textures/block/` | `advanced_metal_block.png` | 高级金属块 |
| `textures/block/` | `air_separator_side.png`, `air_separator_top.png` | 空气分离器 |
| `textures/block/` | `alloy_smelter.png` | 合金炉主控 |
| `textures/block/` | `alloy_smelter_formed.png` | 合金冶炼炉（成型后的机体；ZF108 新画，原来借 `heat_resistant_metal_block`） |
| `textures/block/` | `wiring_block.png` | 合金炉接线口 |
| `textures/block/` | `aluminum_ore.png` | 铝矿石 |
| `textures/block/` | `ammonia_synthesis_chamber_side.png`, `ammonia_synthesis_chamber_top.png` | 氨气组成室 |
| `textures/block/` | `asphalt_block.png` | 柏油块 |
| `textures/block/` | `cobalt_ore.png` | 钴矿石 |
| `textures/block/` | `common_metal_block.png` | 一般金属块 |
| `textures/block/` | `crude_oil_still.png` | 原油 |
| `textures/block/` | `deepslate_cobalt_ore.png` | 深层钴矿石 |
| `textures/block/` | `deepslate_manganese_ore.png` | 深层锰矿石 |
| `textures/block/` | `deepslate_nickel_ore.png` | 深层镍矿石 |
| `textures/block/` | `deepslate_silver_ore.png` | 深层银矿石 |
| `textures/block/` | `deepslate_titanium_ore.png` | 深层钛矿 |
| `textures/block/` | `deepslate_uranium_ore.png` | 深层铀矿石 |
| `textures/block/` | `deepslate_wolframite_ore.png` | 深层黑钨矿 |
| `textures/block/` | `diesel_still.png` | 柴油 |
| `textures/block/` | `distillation_controller_side.png`, `distillation_controller_top.png` | 分馏塔控制器 |
| `textures/block/` | `distillation_operator_side.png`, `distillation_operator_top.png` | 分馏塔操作器 |
| `textures/block/` | `electrolyzer.png` | 电解器 |
| `textures/block/` | `filling_machine_front.png`, `filling_machine_side.png`, `filling_machine_top.png` | 灌装机 |
| `textures/block/` | `fluid_exchanger.png` | 容器换流器 |
| `textures/block/` | `fluid_pipe.png` | fluid_pipe_arm |
| `textures/block/` | `fluid_pipe.png` | fluid_pipe_core |
| `textures/block/` | `fluid_pump.png` | 流体泵 |
| `textures/block/` | `gasoline_still.png` | 汽油 |
| `textures/block/` | `terminal.png` | 发电机 |
| `textures/block/` | `heat_resistant_metal_block.png` | 耐热金属块 |
| `textures/block/` | `heat_sink.png` | 散热装置 |
| `textures/block/` | `heater.png` | 加热装置 |
| `textures/block/` | `hydraulic_press_side.png`, `hydraulic_press_top.png` | 液压机 |
| `textures/block/` | `hydrodesulfurization_chamber_side.png`, `hydrodesulfurization_chamber_top.png` | 加氢脱硫反应仓 |
| `textures/block/` | `lithium_battery_side.png`, `lithium_battery_top.png` | 三元聚合物锂电池 |
| `textures/block/` | `lithium_ore.png` | 锂矿石 |
| `textures/block/` | `low_generator_side.png`, `low_generator_top.png` | 低级发电机 |
| `textures/block/` | `manganese_ore.png` | 锰矿石 |
| `textures/block/` | `micro_crusher_side.png`, `micro_crusher_top.png` | 微型粉碎机 |
| `textures/block/` | `nickel_ore.png` | 镍矿石 |
| `textures/block/` | `power_capturer.png` | 动力能源捕获器 |
| `textures/block/` | `salt_decomposer_side.png`, `salt_decomposer_top.png` | 盐分解构器 |
| `textures/block/` | `salt_dryer.png` | 晒盐机 |
| `textures/block/` | `silver_ore.png` | 银矿石 |
| `textures/block/` | `solar_panel.png` | 太阳能板 |
| `textures/block/` | `stable_metal_block.png` | 稳定金属块 |
| `textures/block/` | `terminal.png` | 接线端子 |
| `textures/block/` | `terminal.png` | terminal_down |
| `textures/block/` | `terminal.png` | terminal_east |
| `textures/block/` | `terminal.png` | terminal_north |
| `textures/block/` | `terminal.png` | terminal_south |
| `textures/block/` | `terminal.png` | terminal_up |
| `textures/block/` | `terminal.png` | terminal_west |
| `textures/block/` | `titanium_ore.png` | 钛矿 |
| `textures/block/` | `uranium_ore.png` | 铀矿石 |
| `textures/block/` | `wiring_block.png` | 接线块 |
| `textures/block/` | `wolframite_ore.png` | 黑钨矿 |

> 同一个贴图被多个模型用到时，表里会出现多行同名 —— 那是**共用一张**，不是重复。


---

## ZF78 新增的占位贴图（**要画**）

> ⚠ 这一节是**手写**的：`TextureCheck.py --plan` 只按模型的文件名推贴图名，认不出"这张是占位"。
> **0.11 ZF90 起**重跑 `--plan` **不会**再冲掉它了：生成器改成"生成上半部分、把换行+`---`+空行+`## ZF`
> 之后的内容原样接回去"（ZF90 当场验过一遍：手写部分逐字符不变）。

| 放哪 | 文件名 | 是什么 | 现在是什么 |
|---|---|---|---|
| `textures/item/` | `bitumen.png` | 沥青 | **原版火药那张图的副本**（你要求「暂时用火药占位」） |
| `textures/block/` | `distillation_controller_side.png` / `_top.png` | 分馏塔控制器 | 程序生成的灰铁占位（带一道琥珀色热带 + 铆钉） |
| `textures/block/` | `distillation_operator_side.png` / `_top.png` | 分馏塔操作器 | 程序生成的灰铁占位（带青色屏 + 散热格栅） |

另外四种产品流体（柴油 / 石脑油 / 汽油 / 液化石油气）的贴图**是你给的**，
已转成本工程 PNG：`*_still.png` 与 `*_flow.png` 各 4 张（同一种流体两张逐字节相同 ——
与氧气/原油同一条老规矩）。

---

## ZF79 的贴图变动

> ⚠ 这一节是**手写**的：`TextureCheck.py --plan` 只按模型推名字，认不出"这张是占位/这张是手绘"。
> 下次重跑 `--plan` 会把它冲掉，我再补回来。

| 放哪 | 文件名 | 是什么 | 现在是什么 |
|---|---|---|---|
| `textures/block/` | `asphalt_block.png` | 柏油块 | **原版煤炭块那张图的副本**（你要求「先用煤炭块材质」），要换就把这个文件覆盖掉 |
| `textures/block/` | `electric_blast_furnace.png` | 电力高炉 | ✅ **已经是你的手绘 256×256**（原名件 `电力高炉.png` 已按 §4.24 改成 ASCII 名，原图留档为 `电力高炉.原名件`） |

柏油块的方块模型是 `cube_all`（一张图铺六面），所以**只有这一个 png 要画**。

## ZF82（0.11）：柴油桶 / 汽油桶 + 容器换流器

| 文件 | 状态 | 说明 |
|---|---|---|
| `models/item/diesel_bucket.json` | **借贴图** | `layer0 = minecraft:item/water_bucket`（用户原话「先用水桶贴图」） |
| `models/item/gasoline_bucket.json` | **借贴图** | 同上 |
| `textures/block/fluid_exchanger.png` | **占位（我生成）** | 16×16 / 8 位 RGBA：金属灰底 + 上下两个青色口 + 中间横缝 |
| `textures/block/diesel_still.png` / `_flow.png` | 已有 | ZF78 用户给的贴图，本轮起被**液体方块**用上了 |
| `textures/block/gasoline_still.png` / `_flow.png` | 已有 | 同上 |

### 顺带一件（门炸出来的）：用户新放进 `textures/item` 的三张素材

`钢板.jpg` / `铁板.jpg` / `铜板.jpg`（09-23、09-24 放进来的）被 ZF66 那条
「textures/item 下不许有中文文件名」检查逮住。处理：**原样挪出资源目录**、逐字节留档到
`build/用户素材/`（ASCII 名 `steel_plate.jpg` / `iron_plate.jpg` / `copper_plate.jpg`
+ `_来源凭据.json` 记哈希）。

⚠ **没有动任何在用的贴图**：铜板/钢板早就有 ASCII PNG（`copper_plate.png` / `steel_plate.png`，
09-19），铁板目前仍借原版贴图。**要不要把这三张 jpg 转成 16×16 RGBA 用上去（尤其铁板）**——
说一声就做，属一个生成器 + 三个模型的事。

## ZF83（0.11）：三张板子贴图换新

| 文件 | 状态 | 来源 / 说明 |
|---|---|---|
| `textures/item/steel_plate.png` | ✅ **换新** | 用户原图 `钢板.jpg`（白底描边板）转档：四边泛洪去背景 |
| `textures/item/iron_plate.png` | ✅ **新建** | 用户原图 `铁板.jpg` 同上（**铁板原先借通用 `plate.png`**，本轮换掉） |
| `textures/item/copper_plate.png` | ✅ **换新** | 用户原图 `铜板.jpg`（深底亮板）同上 |
| `textures/item/plate.png` | 保留 | 银/铝/镍/钴四件仍在用；**删了那四件会变紫黑块**，等它们各自的图 ⟶ **⚠ ZF90 已删**（四件改指 `iron_plate.png`，见下节） |
| `build/用户素材/{steel,iron,copper}_plate.jpg` | 留档 | §4.24 原名件（不进 jar），哈希在 `_来源凭据.json` |

⚠ 转档规则（§4.56）：**白底素材不能一刀切"白色全透明"** ⇒ 从四边泛洪 + 只保留最大连通域。

## ZF84（0.11）：汽油流体贴图换新

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/block/gasoline_still.png` | ✅ **换新** | 用户 2026-09-24 发来的「汽油的新贴图」（16×16 JPEG）转档：16×16 / 8 位 / RGBA / 全不透明，平均 RGB (187,174,106) |
| `textures/block/gasoline_flow.png` | ✅ **换新** | 同上（ZF78 起的约定：still 与 flow 用**同一张**图） |
| `build/用户素材/gasoline_new.jpg` | 留档 | §4.24 原名件（不进 jar），哈希在 `_来源凭据.json` |

## ZF86（0.11）：四张素材转档（铜板 / 氯化钠 / 电容 / 碳酸锂）

| 文件 | 状态 | 来源 / 说明 |
|---|---|---|
| `textures/item/copper_plate.png` | ✅ **重存** | 内容其实是 JPEG（扩展名骗人）⇒ 解出来重写成真 PNG，保留用户的画 |
| `textures/item/sodium_chloride.png` | ✅ **新建** | 用户 `氯化钠.jpg`（原先借原版**糖**） |
| `textures/item/capacitor.png` | ✅ **新建** | 用户 `电容.jpg`（原先借原版**铁粒**） |
| `textures/item/lithium_carbonate.png` | ✅ **新建** | 用户给的 **20×20** 图 ⇒ 按非透明包围盒最近邻缩到 16×16 |
| `build/用户素材/{sodium_chloride,capacitor,lithium_carbonate}.jpg/.png` | 留档 | §4.24 原名件（不进 jar），哈希在 `_来源凭据.json` |

## ZF87（0.11）：油桶贴图

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/item/oil_bucket.png` | ✅ **新建** | 用户给的 `油桶.jpg`（16×16）⇒ 转档（四边泛洪去背景）；油桶图标此前借**原版铁锭** |
| `build/用户素材/oil_bucket.jpg` | 留档 | §4.24 原名件（不进 jar） |

## ZF88（0.11）：原油 / 柴油流体贴图

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/block/crude_oil_still.png` + `_flow.png` | ✅ **换新** | 用户 `石油.png`（16×16/8/RGBA，平均 RGB 35,35,35）原样转写 |
| `textures/block/diesel_still.png` + `_flow.png` | ✅ **换新** | 用户 `柴油.png`（平均 RGB 172,116,42）原样转写 |
| `build/用户素材/{crude_oil,diesel}.png` | 留档 | §4.24 原名件（不进 jar） |

## ZF89（0.11）：汽油 / 石脑油流体贴图 + 电力高炉贴图问题记一笔

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/block/gasoline_still.png` + `_flow.png` | ✅ **换新** | 用户 `汽油.png`（16×16/8/RGBA，平均 RGB 201,201,140）原样转写；顶掉 ZF84 那版（187,174,106） |
| `textures/block/naphtha_still.png` + `_flow.png` | ✅ **换新** | 用户 `石脑油.png`（平均 RGB 236,236,186）原样转写 |
| `build/用户素材/{gasoline,naphtha}.png` | 留档 | §4.24 原名件（不进 jar），哈希在 `_来源凭据.json` |
| `textures/block/electric_blast_furnace.png` | ⚠ **本轮没动，但有问题** | 用户 ZF79 放的 256×256 是**给模型展开的 UV 图集**（61 个岛 / 32903 不透明像素）；而模型 OBJ 的 114 个面**只有 4 个 UV 点**（整张贴图铺每个面）⇒ 每个面把整张图集铺一遍。详见 §4.58；用户已拍板**重新导出带 UV 的模型**，到手后换模型（贴图不动） |

⚠ 用户这一批是**一张一张丢**（石油 → 柴油 → 汽油 → 石脑油），所以 `_zf89_convert.py` 是**表驱动 + 幂等**的：
`JOBS` 里加一行就能再收一张；源图已被挪走时会改用留档原图复查盘上成品（256/256）。

## ZF90（0.11）：其它锭板子一律用铁板那张（+ 中途又收了两样）

用户原话：「**其它锭板子贴图都换成铁板的**」。还在用通用 `plate.png` 的正是四件 —— 银 / 铝 / 镍 / 钴。

| 文件 | 状态 | 说明 |
|---|---|---|
| `models/item/silver_plate.json` 等**四个** | ✅ **改指向** | `layer0` 从 `potato_s_t:item/plate` → **`potato_s_t:item/iron_plate`**（排版照 `iron_plate.json`） |
| `textures/item/plate.png` | 🗑 **已删** | 679 B / sha1 `a28b0654…`；删前断言过"没有任何模型再引用它"，改前件里留了一份（`zf90_pre`），成品里也还有上一版可回退 |
| `textures/item/{iron,steel,copper}_plate.png` | 不动 | 铁 / 钢 / 铜三件仍是各自的图（ZF83/ZF86） |
| `textures/item/diesel_bucket.png` | ✅ **新建** | 本轮进行到一半用户又丢来 `柴油桶_001.png`（16×16 RGBA 真 PNG）⇒ 转档，并把 `diesel_bucket.json` 从借原版水桶（`minecraft:item/water_bucket`）改成指向自己 ⇒ **借原版贴图的模型 7 → 6**（英文公告与 `_zf71_verify.py` 那句活体数字同步改成 6） |
| `textures/item/copper_plate.png` | ✅ **换新（第二版）** | 用户重导出的一块铜板（929 → 3297 字节；画面同一块板、边缘更细）⇒ 原字节留档为 `copper_plate_v2.png`，按本工程规格重编码（逐像素 256/256 一致，用户的画一个像素没改） |
| `textures/item/gasoline_bucket.png` | ✅ **新建** | 用户又丢来 `汽油桶.png`（16×16 RGBA 真 PNG）⇒ 转档 + 模型改指自己 ⇒ **借原版贴图的模型 6 → 5** |
| `build/用户素材/{diesel_bucket.png,copper_plate_v2.png,gasoline_bucket.png}` | 留档 | §4.24 原名件（不进 jar），哈希在 `_来源凭据.json` |
| `build/用户素材/electric_blast_furnace_original.png` | ⚠ **挪出资源目录** | ZF79 的用户原图（256×256，原名 `电力高炉.png`）当时以 `电力高炉.原名件` **留在了 `textures/block` 里** ⇒ 那 18 KB、非 ASCII 文件名从 ZF79 起**一直被打进 jar**（四轮没人发现）。ZF90 新加的"成品里 `assets/` + `data/` 的条目名必须全合法"这条断言当场抓到，已按 §4.24 挪到这里并记进凭据；**资源目录里不再留任何 `.原名件`** |

⇒ 现在**五件板共用 `iron_plate.png`**（铁 / 银 / 铝 / 镍 / 钴），它们在背包里长得一模一样 —— 这是照做的结果。
你哪天想给银/铝/镍/钴各自一张，把图丢进 `textures/item/`（ASCII 名）说一声，我给它们各开文件并改指向
（`PngRecolor.py` 也能按金属色一键改色）。**汽油桶**还在借原版水桶，你丢一张 `汽油桶.png`（或任意 ASCII 名）我就照柴油桶这套接上。

⚠ 顺带修了 `TextureCheck.py --plan` 的两个真问题（都记在档案 §4.59）：
① 清单表原来写的是**模型名** + `.png`，不是模型真正引用的贴图 ⇒ 表里曾列出四个**不存在的文件**；
② `--plan` 原来是**整份覆盖** `docs/贴图清单.md`，会把上面这些手写小节冲掉 —— 现在会把 `---` 之后原样接回去
（本轮验过两次：5587 / 4611 字符**逐字符不变**）。

## ZF91（0.11）：电力高炉换成带真 UV 的模型（**贴图没动**）

用户把 Blockbench 工程 `.bbmodel` 发来了（41423 字节 / sha256 `15028bf3…`）。查清三件事：

| 项 | 实测 |
|---|---|
| 工程类型 | **Free / mesh**（19 个 `type:"mesh"`，各 8 顶点 / 6 面 = **114 个面**）；顶点是**相对元素 `origin` 的局部坐标**，世界坐标 = `origin + R(rotation)·v` |
| UV | **逐顶点给的真 UV**：456 个不同取值 / 114 个不同矩形 ⇒ 直接照抄即可，不用猜角点顺序 |
| 工程里内嵌的贴图 | 是 **UV 模板**（sha256 `139264fb…`），**不是**用户的画；**用户的画 = 成品里在用的那张** `electric_blast_furnace.png`（与用户发来的「图一」**逐字节相同**） |

| 文件 | 状态 | 说明 |
|---|---|---|
| `models/block/electric_blast_furnace_{north,south,east,west}.obj` | ✅ **换新** | 由 `.bbmodel` 烘出：152 顶点 / 456 vt / 114 面；四朝向包围盒与旧模型逐个吻合（3×3×4.9375） |
| `textures/block/electric_blast_furnace.png` | **不动** | sha1 `598c2d82…`，一个字节没改（`_zf91_verify.py` B 段盯着） |
| `electric_blast_furnace.mtl` / 四个 model JSON | **不动** | `map_Kd` / `flip_v: false` / `automatic_culling: false` 照旧；v 方向已按 NeoForge 源码 `ObjModel.java:374-376` 核过 |
| `zf91_pre\user\electric_blast_furnace.bbmodel` | 留档 | 用户工程原件（sha256 记在 `_zf91_verify.py` 与 §9） |

验收两条硬指标（`_zf91_verify.py`）：**逐面 UV 矩形在贴图上 0 个透明像素**；
**每个面 UV 矩形的尺寸 = 该面的世界尺寸 ×16**。这两条同时成立才说明"UV 真的与面对上了"。

## ZF92（0.11）：电力高炉两根接线柱的 UV 归属修正（**贴图依然一个字节没动**）

你回了两张实机截图：「第一张这个接线的 顶面和正面贴图对调一下 第二张接线的是高炉贴图
和旁边的接线块改一下 顶部也移」。查下来**不是画的问题，是模型 UV 的分配错位**：

| 项 | 实测 |
|---|---|
| "接线柱"是哪两个元素 | 塔的 **±X 两侧、y 1..2 格的 1×1×1**（按世界包围盒认出来，不按下标） |
| 一共有几张画 | **5 张**：盖板（铆钉+内凹方板）/ 金框（暗底+金方框）/ 素板（浅灰横纹）/ 深灰 / 格栅 —— 贴图里 16 张 16×16 瓦片**归成 6 组**（`_zf92_tilecmp.py` 逐像素比） |
| 错在哪 | 两根柱子用**同一套画**却分配相反：一根 上=盖板、下=金框；另一根 上=金框、下=盖板 ⇒ 必有一根错位 |
| 改法 | **只改 UV 的"取哪一块瓦片"**：每个顶点在瓦片内的偏移原样保留，只换瓦片原点 ⇒ 各面自己的 UV 朝向不变 |

| 文件 | 状态 | 说明 |
|---|---|---|
| `models/block/electric_blast_furnace_{north,south,east,west}.obj` | ✅ **UV 修正** | 两根柱子都改成 **顶面=素板 / 正面(南)=金框 / 底面=盖板**；四份各 **841 行不变、差异 20 行全是 `vt`**（顶点/法线/面一个字节没动，`_zf92_diff.py` 逐行证明） |
| `textures/block/electric_blast_furnace.png` | **不动** | sha1 `598c2d82…`；本次**没有新增/替换任何贴图**，所以上面的"待画"数量不变 |
| `electric_blast_furnace.mtl` / 四个 model JSON | **不动** | 同上 |

⚠ 两根柱子的**东/西面仍然不一样**（一根格栅、一根素板）—— 那是原本就画得不一样，**本轮没动**；
要它们也一致说一声。

### 顺带：你 09-25 00:07 丢进来的 `音乐唱片茉莉花.png`

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/item/音乐唱片茉莉花.png` | ⚠ **已移出资源目录** | 3170 字节，16×16 真 PNG（用户原图）。文件名带中文 ⇒ §4.24 不允许留在资源目录里，而且本轮**没有**对应物品 ⇒ 它会变成一张没人引用的孤儿图 **+ 一个非 ASCII 的 jar 条目**（ZF90 加的成品侧断言当场抓到） |
| `build/用户素材/music_disc_jasmine_flower.png` | 留档 | 字节未动（sha1 `0b1bf5f4…`），已在 `_来源凭据.json` 里记原名 |

**要我做成一整张唱片的话说一声**（§6.1 那 6 处联动都要动，其中**音效 .ogg 得你给** ——
现有那张《共和国之砧》是这么接的）。本轮**不猜、不建物品**。

## ZF93（0.11）：第二张音乐唱片《茉莉花（管弦乐）》

你随后把音频也给了（`Jasmine_Flower_Strings_mono.ogg`）⇒ 这两样东西**上线了**：

| 文件 | 状态 | 说明 |
|---|---|---|
| `textures/item/music_disc_jasmine_flower.png` | ✅ **上线** | 就是你那张（3170 字节 / 16×16 RGBA）**原字节复制**，sha1 `0b1bf5f4…` |
| `sounds/music_disc_jasmine_flower.ogg` | ✅ **上线** | 你给的原文件**一个字节没动**：1691739 字节 / sha256 `ca2493b0…`；实测 **单声道 44100 Hz Ogg Vorbis，147.102132 s**（两条算法互核）⇒ **不转码** |
| `models/item/music_disc_jasmine_flower.json` | ✅ 新建 | 走原版 `minecraft:item/template_music_disc`（与第一张唱片一致） |
| `data/potato_s_t/jukebox_song/jasmine_flower.json` | ✅ 新建 | `length_in_seconds` = **147.1**、比较器输出 **15**、`sound_event` 用 1.21.1 的**纯字符串**写法 |

四语言各 **+2 键（270 → 272）**：`item.potato_s_t.music_disc_jasmine_flower`（"音乐唱片"）与
`jukebox_song.potato_s_t.jasmine_flower`（曲名，会自动显示在 tooltip 上）。
**没有合成配方**（第一张唱片也没有；要的话说一声）。

⚠ 本轮的"待画（5 个，借原版贴图）"**没动**。

## ZF94（0.11）：电力高炉两根接线柱的东/西统一（**贴图没动**）

用户第 3 条：「电力高炉 接线方块还是对称一致一下吧」。ZF92 之后两根柱子**每面都是同一张画**，
**只有东/西不一致**（一根格栅、一根素板）。

| 项 | 说明 |
|---|---|
| 改了什么 | 第二根柱子的**东/西**从「素板副本 (149,17)/(149,34)」换成与第一根相同的「格栅 (47,144)/(64,144)」 |
| 怎么改的 | 只在**瓦片**这一层重新基准化（每个顶点在瓦片内的偏移不变、只换瓦片原点）⇒ 只动 8 行 `vt` |
| 往哪边一致 | 两条路都说得通；选了"格栅"（专用画只有那对、你 ZF92 截图里看到的就是格栅那面、接线口带格栅更像机器接口）—— 要另一种是**一行改动** |
| 副作用 | 贴图里那两张素板副本（149,17）/（149,34）**从此没人用**（它们是通用素板的第 5、6 份副本，不影响任何东西） |
| 没动 | `electric_blast_furnace.png`（sha1 `598c2d82…`）、`.mtl`、四个 model JSON、顶点/法线/面数 |


## ZF96（0.11）：加氢脱硫反应仓 + 硫（**三张全是程序生成的占位**）

用户这一轮**没有给任何贴图**（原话只有机器与配方），所以三张都由 `build/zftools/_zf96_textures.py`
生成 —— 与 ZF78 的分馏塔控制器/操作器、ZF82 的容器换流器同一套做法（机身灰沿用那一套
74,74,82 / 110,110,120 / 154,162,172 / 48,48,56，再各加一样"这台机器的记号色"：琥珀黄 222,186,42）。

| 放哪 | 文件名 | 是什么 | 现在长什么样 |
|---|---|---|---|
| `textures/block/` | `hydrodesulfurization_chamber_side.png` | 加氢脱硫反应仓·侧 | 灰钢机身 + 左右两根**氢气竖管** + 中间一条**琥珀黄反应窗**（147 B） |
| `textures/block/` | `hydrodesulfurization_chamber_top.png` | 加氢脱硫反应仓·顶 | 灰钢顶盖 + 中央**圆形进气口**（外圈法兰 + 内圈琥珀黄，138 B） |
| `textures/item/` | `sulfur.png` | **硫**（新物品） | 透明底上一堆**黄色粉末**（136 B） |

- 三张都是**真 PNG / 16×16 / 8 位 RGBA**，脚本里带"写-读往返自证"（写完立刻读回来逐字节比）。
- 预览图：`build/zftools/_zf96_preview.png`（放大 8 倍拼成一张，肉眼复核用，不进 jar）。
- ⚠ 因为是**我们自己的贴图**（不是借原版），英文公告里「还在借原版贴图的模型 = **5**」**不变**；
  `TextureCheck.py` 报的"待画 = 5"也不变。
- `TextureCheck.py --plan` 重跑过了：上半部分自动多出这三行，**手写部分（`## ZF78` 起）逐字符保留**。
- 要换成手绘的：把对应文件覆盖掉即可，**不用改任何模型 JSON**（文件名就是注册名）。


## ZF97（0.11）：两台新机器 + 两种新气体（**8 张全是程序生成的占位**）

用户这一轮同样没给贴图（只有机器与数值），8 张全部由 `build/zftools/_zf97_textures.py` 生成，
配色沿用本工程占位那套灰，各加一样"记号色"：

| 放哪 | 文件名 | 是什么 | 现在长什么样 |
|---|---|---|---|
| `textures/block/` | `nitrogen_still.png` / `nitrogen_flow.png` | **氮气**（新流体） | 淡蓝灰底 + 两道横向波纹（各 105 B，**两张逐字节相同**） |
| `textures/block/` | `ammonia_still.png` / `ammonia_flow.png` | **氨气**（新流体） | 淡青绿底 + 两道横向波纹（各 105 B，**两张逐字节相同**） |
| `textures/block/` | `air_separator_side.png` / `_top.png` | 空气分离器·侧 / 顶 | 灰钢机身 + 两根冷媒竖管 + **淡蓝冷雾窗**（148 B）；顶面是进气格栅（127 B） |
| `textures/block/` | `ammonia_synthesis_chamber_side.png` / `_top.png` | 氨气组成室·侧 / 顶 | 灰钢机身 + 两根进料管 + **青绿反应窗**（147 B）；顶面是催化剂投料口（138 B） |

- 八张都是**真 PNG / 16×16 / 8 位 RGBA**；脚本里带两条自证：**写-读往返逐字节相同** +
  **still 与 flow 逐字节相同**（后者是本工程流体贴图的老规矩）。
- 预览图：`build/zftools/_zf97_preview.png`（贴图，放大 6 倍）、
  `build/zftools/_zf97_layout.png`（**界面版面示意图**，放大 3 倍，用来肉眼查"有没有压在一起"）。
- ⚠ 都是我们自己的贴图 ⇒ 公告里「还在借原版贴图的模型 = **5**」与 `TextureCheck` 的"待画 = 5"**都不变**。
- `TextureCheck.py --plan` 重跑过了：上半部分自动多出四行（两台机器各一行 × 两张表），
  手写部分（`## ZF78` 起）逐字符保留。
- 要换成手绘的：把对应文件覆盖掉即可 —— **流体**换 `block/<名字>_still.png` 与 `_flow.png` 两张，
  **机器**换 `block/<方块名>_side.png` 与 `_top.png` 两张，都不用改模型 JSON。


## ZF104（0.11）：两套盔甲（钛合金 / 星璨钢）+ 星璨钢锭

用户原话：「物品栏贴图先用铁套的」，并且**真的给了一张素材**：
`build/用户素材/star_steel.png`（160×160，3975 B，SHA256 `e3833ca5…`）——
是星璨钢**锭子**那张（紫蓝渐变的锭形，**本来就是透明底**，不是白底素材）。

| 放哪 | 文件名 | 是什么 | 现在长什么样 |
|---|---|---|---|
| `textures/item/` | `star_steel_ingot.png` | **星璨钢锭**（新物品） | 用户素材缩到 16×16（214 B）：紫蓝渐变锭形，粉紫高光 + 深靛阴影，**透明底** |
| `textures/item/` | `titanium_alloy_{helmet,chestplate,leggings,boots}.png` | 钛合金套的背包图标 | **没有这张文件** —— 8 个模型直接写 `minecraft:item/iron_*`（借原版铁套），游戏里显示的就是铁套图标 |
| `textures/item/` | `star_steel_{helmet,chestplate,leggings,boots}.png` | 星璨钢套的背包图标 | 同上，也借原版铁套 |
| `textures/models/armor/` | `titanium_alloy_layer_1.png` / `_layer_2.png` | **钛合金套穿在身上**的外观（外层 / 内层） | **用户给的 `钛合金套装.png`**（64×32，本来就带 alpha）→ `_zf106_armor.py` 定尺后原样写出（1077 B ×2） |
| `textures/models/armor/` | `star_steel_layer_1.png` / `_layer_2.png` | **星璨钢套穿在身上**的外观 | **用户给的 `星璨钢套装.png`**（64×32）→ 同一条流水线（1038 B ×2） |

- ✅ **两套盔甲的图层贴图已经是用户自己的素材了**（ZF106）。命名走 `ArmorMaterial.Layer` 的约定：
  `<材料名>_layer_1.png` = 外层（头/胸/靴）、`<材料名>_layer_2.png` = 内层（护腿）；
  Java 侧 `ModArmorMaterials` 的 Layer 资源名 = `potato_s_t:<材料名>`。
- ⚠ 目前**外层与内层用的是同一张图**（用户只给了一张套装图）。
  真盔甲的 layer_1/layer_2 通常不同（内层专给护腿）——要分开就再给一张，按名字收。
- ⚠ 用户那两张图**不在标准盔甲 UV 部位上**（量过：只有左半边有内容，右侧与下半是空的）。
  ⇒ 穿上是"整张图铺上去"的效果，和原版铁套的 UV 布局不一样；不满意就再调。

- ✅ **原图找到了（ZF106 更正）**：`build\用户素材\钛合金套装.png`（1936 B）与
  `星璨钢套装.png`（2080 B）**一直都在**（09-23 / 09-24 就建好了）。
  我前两轮说"原图没到"是**我自己的取证方法错了**：
  ① 列目录时用了 `Select-Object -First 6/12`（按时间倒序）⇒ 中文名的旧文件被截掉；
  ② 按 `星璨` 搜文件名 ⇒ 实际文件名是 `星璨钢套装.png`（能搜到）但我搜的是 `星璨` 相关组合，
     加上 `-match '套装'` 那条被 `-First` 截断在前面就退出了。
  **教训**：找素材不许截断列表、不许只看最近改动的若干条（已补进档案 §4.73）。
- ⚠ **贴图生成/换图脚本**：`build/zftools/_zf103_textures.py`
  （用户素材优先、面积平均缩放到 16×16、alpha 加权；没有素材时**默认不落盘**，
  要程序占位得显式加 `--placeholder` —— 免得占掉用户素材的位置）。
- ⚠ 缩放算法**用面积平均而不是最近邻**：160→16 是 10:1，最近邻只能"挑一个像素代表 100 个"，
  轮廓会掉锯齿；实现里按 alpha 加权平均，边缘也不会出现半透明脏边
  （`_zf103_verify.py` 有一条断言专门查"半透明像素 = 0"）。
- ⇒ 公告里「还在借原版贴图的模型」从 **5** 涨到 **13**（+8 件盔甲的背包图标）；
  `TextureCheck.py` 的"待画"同样从 5 → 13。**要画的其实是 8 张背包图标 + 4 张盔甲层贴图**。


## ZF101（0.11）：酸性反应室 + 三种酸（**8 张全是程序生成的占位**）

用户这一轮没给贴图 ⇒ 8 张由 `build/zftools/_zf101_textures.py` 生成：

| 放哪 | 文件名 | 是什么 | 现在长什么样 |
|---|---|---|---|
| `textures/block/` | `acidic_reaction_chamber_side.png` / `_top.png` | 酸性反应室·侧 / 顶 | 灰钢壳（每 4 格拼装线）+ **两个玻璃视窗**（下半截是黄绿酸液）+ 两根进出料管（183 B）；顶面是圆形投料口（174 B） |
| `textures/block/` | `carbonic_acid_still/_flow.png` | **碳酸**（新流体） | 淡青白 + 细波纹（各 137 B，**两张逐字节相同**） |
| `textures/block/` | `nitric_acid_still/_flow.png` | **硝酸** | 淡黄 + 细波纹（各 137 B，相同） |
| `textures/block/` | `sulfuric_acid_still/_flow.png` | **硫酸** | 琥珀 + 细波纹（各 137 B，相同） |

- 八张都是**真 PNG / 16×16 / 8 位 RGBA**。
- ⚠ 六张流体贴图**跟老规矩**（still 与 flow 逐字节相同）；ZF100 的二氧化碳是**唯一**画了独立流动版的那张。
- ⚠ 都是**我们自己的占位图** ⇒ 公告的「还在借原版贴图的模型 = **5**」与 `TextureCheck` 的"待画 = **5**"都不变。
- 要换手绘的：机器换两张 `_side/_top`，流体换每种两张 `_still/_flow`，都不用改模型 JSON。


## ZF100（0.11）：燃烧反应室 + 二氧化碳（**4 张全是程序生成的占位**）

用户这一轮只给了机器图纸与数值、没给贴图 ⇒ 4 张全部由 `build/zftools/_zf100_textures.py` 生成：

| 放哪 | 文件名 | 是什么 | 现在长什么样 |
|---|---|---|---|
| `textures/block/` | `combustion_chamber_side.png` | 燃烧反应室·侧 | 深灰铁壳（每 4 格一道拼装线 + 6 颗铆钉）+ 正中竖长**黑炉膛** + 炉膛里一道**火色**横档（168 B） |
| `textures/block/` | `combustion_chamber_top.png` | 燃烧反应室·顶 | 同样的铁壳 + 中间**圆形排气口**（黑心 + 一圈火色）（164 B） |
| `textures/block/` | `carbon_dioxide_still.png` | **二氧化碳**（新流体）·静止 | 淡灰白雾（**故意做得比氮气/氨气更"白"一点**，因为二氧化碳本身无色）（121 B） |
| `textures/block/` | `carbon_dioxide_flow.png` | 二氧化碳·流动 | 同上 + 斜向条纹（209 B） |

- 四张都是**真 PNG / 16×16 / 8 位 RGBA**（`PngRecolor.write_png` 写盘）。
- ⚠ 它们都是**我们自己的占位图** ⇒ 公告里「还在借原版贴图的模型 = **5**」与
  `TextureCheck` 的"待画 = **5**"**都不变**（这两处数的是"借原版"的那一档）。
- ⚠ 与其它流体不同：二氧化碳的 still/flow **不是逐字节相同的**（流动版多一层斜纹，121 B / 209 B）。
  我核过全表：**其余 10 种流体**（氧/氢/氯/原油/柴油/石脑油/汽油/液化石油气/氮/氨）的两张贴图
  **全部逐字节相同** —— 那是本工程"没有流动版素材时的省事做法"。
  二氧化碳这张是本工程**第一次画出真正的流动版**（有意为之，不是漏改）；
  要让两张一样也简单：`_zf100_textures.py` 里把 `gas_texture(True)` 的斜纹那段去掉重跑即可。
- 要换手绘的：机器换 `combustion_chamber_side.png` / `_top.png`，
  流体换 `carbon_dioxide_still.png` / `_flow.png`，都不用改模型 JSON。


## ZF108（0.11）：合金冶炼炉的两张贴图（**重画 + 机体第一次有自己的画**）

用户原话：「你看看您不能发挥一下 简单画一下合金冶炼炉的材质（不用太好 凑活都可以）现在的太丑了谢谢啦」

**丑在哪（量过，不是感觉）**：

- 旧 `alloy_smelter.png` 有 **228 种颜色**；本工程好看的机器图都是 **5~19 色**的平涂
  （微型粉碎机侧面 8 色、燃烧反应室 6 色）—— 旧图放大后就是噪声；
- 成型后的机体**根本没有自己的画**：`alloy_smelter.mtl` 借的是 `heat_resistant_metal_block`；
- 更要命的是那 4 个 OBJ 只有 **4 个唯一 `vt`**（u 0~0.25 / v 0.75~1.0）⇒ 贴图上 **4×4 像素**
  被**放大**铺满每一个面（**不是平铺**）。所以这支模型借谁的图都一样糊 —— 这条今天才量出来（§4.78）。

| 放哪 | 文件名 | 是什么 | 现在长什么样 |
|---|---|---|---|
| `textures/block/` | `alloy_smelter.png` | 主控（未成型）+ **12 块外壳** + 物品图标 | **重画**：152 B / 16×16 / **7 色**。灰底板 + 四角铆钉 + 中间凹槽里四根熔融竖条 + 下面一个小出料口 |
| `textures/block/` | `alloy_smelter_formed.png` | 成型后的多方块机体（4 个 OBJ 用） | **新画**：118 B / 16×16 / **5 色**。四角铆钉 + 中央观察窗 + 一条熔融亮带；**上下镜像对称** ⇒ OBJ 的 v 朝哪边都不影响观感 |
| `models/block/` | `alloy_smelter_{north,east,south,west}.obj` | 机体四朝向模型 | 只改 `vt`：那 4 个点从"4×4 像素小格"**等比放大到整张贴图**；`v` / `vn` / `f` / `usemtl` 一个字节没动（校验里逐行比过改前件） |
| `models/block/` | `alloy_smelter.mtl` | 材质 | `map_Kd`：`heat_resistant_metal_block` → `alloy_smelter_formed` |

**配色**全部取自本工程机器家族的实测值：`#4a4a52`（底）、`#34363b`/`#23232a`（深框 / 凹槽）、
`#6e6e78`/`#9aa2ac`（亮边 / 铆钉）、`#c46022`/`#e8912f`（熔融，与燃烧反应室同一支）。
生成脚本：`build/zftools/_zf108_textures.py`（`--write` 才落盘；不带参数会生成 6× 预览图
`build/zftools/_zf108_preview.png`）；改 UV 的脚本：`build/zftools/_zf108_reuv.py`。
**要换手绘的**：直接覆盖这两个 PNG 即可（16×16、RGBA、不透明），模型一个字都不用改。

## ZF109（0.11）：采油机（**1 张新方块贴图，程序生成占位**）

用户没给贴图也没要求画（原话里只有机器 / 界面 / 数值），但新方块没有 PNG 就是紫黑格 ⇒
照 ZF97 / ZF100 / ZF101 / ZF108 的先例先用程序生成一张能看的。

| 放哪 | 文件名 | 是什么 | 现在长什么样 |
|---|---|---|---|
| `textures/block/` | `oil_pump.png` | 采油机（六面同一张） | 深灰钢板 + 四角铆钉（`#9aa2ac`）+ 中间一台**横躺的油罐**（罐里是熔融亮色 `#e8912f`）+ 下面一个**朝下的吸油管口**。16×16 / **5 色** / 151 B |
| `blockstates/` | `oil_pump.json` | 方块状态 | 只有一种变体（**没有朝向**，与空气分离器 / 酸性反应室同款） |
| `models/block/` | `oil_pump.json` | 方块模型 | `parent = minecraft:block/cube_all`，六面都取上面那张图 |
| `models/item/` | `oil_pump.json` | 物品图标 | 直接父级到方块模型 |

生成脚本：`build\zftools\_zf109_textures.py`（顶部一张 16×16 的**字符图例表**；
不带 `--write` 只出预览 `build\zftools\_zf109_preview.png`，带 `--write` 才落盘 PNG）。

**要换手绘的**：直接覆盖 `textures/block/oil_pump.png`（16×16、RGBA、不透明），
**模型一个字不用改**；想在手绘之前先调我这张，就改图例表里那几个字符。
