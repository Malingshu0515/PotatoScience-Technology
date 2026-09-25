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

## 待画（9 个，现在借的是原版贴图）

| 放哪 | 文件名 | 是什么 | 现在借的 |
|---|---|---|---|
| `textures/item/` | `capacitor.png` | 电容 | `minecraft:item/iron_nugget` |
| `textures/item/` | `creative_cable.png` | creative_cable | `minecraft:block/redstone_block` |
| `textures/item/` | `lithium_carbonate.png` | 碳酸锂 | `minecraft:item/sugar` |
| `textures/item/` | `lithium_concentrate.png` | 锂矿精粉 | `minecraft:item/sugar` |
| `textures/item/` | `oil_bucket.png` | 油桶 | `minecraft:item/iron_ingot` |
| `textures/item/` | `sodium_chloride.png` | 氯化钠 | `minecraft:item/sugar` |
| `textures/item/` | `test_fluid_tank.png` | test_fluid_tank | `minecraft:block/glass`, `minecraft:block/iron_block` |
| `textures/block/` | `creative_cable.png` | 创造模式线缆 | `minecraft:block/redstone_block` |
| `textures/block/` | `test_fluid_tank.png` | 测试流体储罐 | `minecraft:block/glass`, `minecraft:block/iron_block` |

## 已经有自己贴图的（列出来是方便你替换）

| 放哪 | 文件名 | 是什么 |
|---|---|---|
| `textures/item/` | `advanced_metal_block.png` | advanced_metal_block |
| `textures/item/` | `alloy_smelter.png` | alloy_smelter |
| `textures/item/` | `aluminum_ingot.png` | 铝锭 |
| `textures/item/` | `aluminum_ore.png` | aluminum_ore |
| `textures/item/` | `aluminum_plate.png` | 铝板 |
| `textures/item/` | `carbon.png` | 碳粉 |
| `textures/item/` | `cobalt_ingot.png` | 钴锭 |
| `textures/item/` | `cobalt_ore.png` | cobalt_ore |
| `textures/item/` | `cobalt_plate.png` | 钴板 |
| `textures/item/` | `common_metal_block.png` | common_metal_block |
| `textures/item/` | `copper_plate.png` | 铜板 |
| `textures/item/` | `copper_wire.png` | 铜线 |
| `textures/item/` | `copper_wire_spool.png` | 铜线轴 |
| `textures/item/` | `deepslate_cobalt_ore.png` | deepslate_cobalt_ore |
| `textures/item/` | `deepslate_manganese_ore.png` | deepslate_manganese_ore |
| `textures/item/` | `deepslate_nickel_ore.png` | deepslate_nickel_ore |
| `textures/item/` | `deepslate_silver_ore.png` | deepslate_silver_ore |
| `textures/item/` | `deepslate_titanium_ore.png` | deepslate_titanium_ore |
| `textures/item/` | `deepslate_uranium_ore.png` | deepslate_uranium_ore |
| `textures/item/` | `deepslate_wolframite_ore.png` | deepslate_wolframite_ore |
| `textures/item/` | `electric_blast_furnace.png` | electric_blast_furnace |
| `textures/item/` | `electrolyzer.png` | electrolyzer |
| `textures/item/` | `empty_spool.png` | 空线轴 |
| `textures/item/` | `filling_machine.png` | filling_machine |
| `textures/item/` | `fluid_pipe.png` | fluid_pipe |
| `textures/item/` | `fluid_pump.png` | fluid_pump |
| `textures/item/` | `heat_resistant_metal_block.png` | heat_resistant_metal_block |
| `textures/item/` | `heat_sink.png` | heat_sink |
| `textures/item/` | `heater.png` | heater |
| `textures/item/` | `high_carbon_steel.png` | 高碳钢 |
| `textures/item/` | `high_pressure_tank.png` | 高压气罐 |
| `textures/item/` | `hydraulic_press.png` | hydraulic_press |
| `textures/item/` | `iron_plate.png` | 铁板 |
| `textures/item/` | `iron_powder.png` | 铁粉 |
| `textures/item/` | `light_titanium_alloy.png` | 轻质钛合金 |
| `textures/item/` | `lithium_battery.png` | lithium_battery |
| `textures/item/` | `lithium_ore.png` | lithium_ore |
| `textures/item/` | `low_generator.png` | low_generator |
| `textures/item/` | `magnet.png` | 磁铁 |
| `textures/item/` | `manganese_ore.png` | manganese_ore |
| `textures/item/` | `micro_crusher.png` | micro_crusher |
| `textures/item/` | `music_disc_anvil_of_the_republic.png` | 音乐唱片 |
| `textures/item/` | `nickel_ingot.png` | 镍锭 |
| `textures/item/` | `nickel_ore.png` | nickel_ore |
| `textures/item/` | `nickel_plate.png` | 镍板 |
| `textures/item/` | `photovoltaic_component.png` | 光伏原件 |
| `textures/item/` | `power_cable_spool.png` | 动力线缆轴 |
| `textures/item/` | `power_capturer.png` | power_capturer |
| `textures/item/` | `raw_aluminum.png` | 粗铝 |
| `textures/item/` | `raw_cobalt.png` | 粗钴 |
| `textures/item/` | `raw_lithium.png` | 粗锂 |
| `textures/item/` | `raw_manganese.png` | 粗锰 |
| `textures/item/` | `raw_nickel.png` | 粗镍 |
| `textures/item/` | `raw_silver.png` | 粗银 |
| `textures/item/` | `raw_titanium.png` | 粗钛 |
| `textures/item/` | `raw_tungsten.png` | 粗钨 |
| `textures/item/` | `raw_uranium.png` | 粗铀 |
| `textures/item/` | `salt_decomposer.png` | salt_decomposer |
| `textures/item/` | `salt_dryer.png` | salt_dryer |
| `textures/item/` | `sea_salt.png` | 海盐 |
| `textures/item/` | `silicon.png` | 硅 |
| `textures/item/` | `silver_ingot.png` | 银锭 |
| `textures/item/` | `silver_ore.png` | silver_ore |
| `textures/item/` | `silver_plate.png` | 银板 |
| `textures/item/` | `solar_panel.png` | solar_panel |
| `textures/item/` | `stable_metal_block.png` | stable_metal_block |
| `textures/item/` | `steel_plate.png` | 钢板 |
| `textures/item/` | `terminal.png` | terminal |
| `textures/item/` | `thermal_metal.png` | 热力金属 |
| `textures/item/` | `titanium_alloy_pickaxe.png` | 钛合金镐 |
| `textures/item/` | `titanium_alloy_sword.png` | 钛合金剑 |
| `textures/item/` | `titanium_ingot.png` | 钛锭 |
| `textures/item/` | `titanium_ore.png` | titanium_ore |
| `textures/item/` | `titanium_powder.png` | 钛粉 |
| `textures/item/` | `toner.png` | 墨粉 |
| `textures/item/` | `uranium_ingot.png` | 铀锭 |
| `textures/item/` | `uranium_ore.png` | uranium_ore |
| `textures/item/` | `wiring_block.png` | wiring_block |
| `textures/item/` | `wolframite_ore.png` | wolframite_ore |
| `textures/item/` | `wrench.png` | 扳手 |
| `textures/block/` | `advanced_metal_block.png` | 高级金属块 |
| `textures/block/` | `alloy_smelter.png` | 合金炉主控 |
| `textures/block/` | `alloy_smelter_part.png` | 合金冶炼炉 |
| `textures/block/` | `alloy_smelter_port.png` | 合金炉接线口 |
| `textures/block/` | `aluminum_ore.png` | 铝矿石 |
| `textures/block/` | `cobalt_ore.png` | 钴矿石 |
| `textures/block/` | `common_metal_block.png` | 一般金属块 |
| `textures/block/` | `crude_oil.png` | 原油 |
| `textures/block/` | `deepslate_cobalt_ore.png` | 深层钴矿石 |
| `textures/block/` | `deepslate_manganese_ore.png` | 深层锰矿石 |
| `textures/block/` | `deepslate_nickel_ore.png` | 深层镍矿石 |
| `textures/block/` | `deepslate_silver_ore.png` | 深层银矿石 |
| `textures/block/` | `deepslate_titanium_ore.png` | 深层钛矿 |
| `textures/block/` | `deepslate_uranium_ore.png` | 深层铀矿石 |
| `textures/block/` | `deepslate_wolframite_ore.png` | 深层黑钨矿 |
| `textures/block/` | `electrolyzer.png` | 电解器 |
| `textures/block/` | `filling_machine.png` | 灌装机 |
| `textures/block/` | `fluid_pipe_arm.png` | fluid_pipe_arm |
| `textures/block/` | `fluid_pipe_core.png` | fluid_pipe_core |
| `textures/block/` | `fluid_pump.png` | 流体泵 |
| `textures/block/` | `generator.png` | 发电机 |
| `textures/block/` | `heat_resistant_metal_block.png` | 耐热金属块 |
| `textures/block/` | `heat_sink.png` | 散热装置 |
| `textures/block/` | `heater.png` | 加热装置 |
| `textures/block/` | `hydraulic_press.png` | 液压机 |
| `textures/block/` | `lithium_battery.png` | 三元聚合物锂电池 |
| `textures/block/` | `lithium_ore.png` | 锂矿石 |
| `textures/block/` | `low_generator.png` | 低级发电机 |
| `textures/block/` | `manganese_ore.png` | 锰矿石 |
| `textures/block/` | `micro_crusher.png` | 微型粉碎机 |
| `textures/block/` | `nickel_ore.png` | 镍矿石 |
| `textures/block/` | `power_capturer.png` | 动力能源捕获器 |
| `textures/block/` | `salt_decomposer.png` | 盐分解构器 |
| `textures/block/` | `salt_dryer.png` | 晒盐机 |
| `textures/block/` | `silver_ore.png` | 银矿石 |
| `textures/block/` | `solar_panel.png` | 太阳能板 |
| `textures/block/` | `stable_metal_block.png` | 稳定金属块 |
| `textures/block/` | `terminal.png` | 接线端子 |
| `textures/block/` | `terminal_down.png` | terminal_down |
| `textures/block/` | `terminal_east.png` | terminal_east |
| `textures/block/` | `terminal_north.png` | terminal_north |
| `textures/block/` | `terminal_south.png` | terminal_south |
| `textures/block/` | `terminal_up.png` | terminal_up |
| `textures/block/` | `terminal_west.png` | terminal_west |
| `textures/block/` | `titanium_ore.png` | 钛矿 |
| `textures/block/` | `uranium_ore.png` | 铀矿石 |
| `textures/block/` | `wiring_block.png` | 接线块 |
| `textures/block/` | `wolframite_ore.png` | 黑钨矿 |
