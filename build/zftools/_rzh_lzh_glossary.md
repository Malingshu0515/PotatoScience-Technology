# 文言文（lzh）术语表 —— 三份译稿的**共同契约**

Minecraft 1.21.1 原版自带 `lzh` 语言（`language.name = 文言`，`language.region = 華夏`）。
本模组只要在 `assets/potato_s_t/lang/lzh.json` 放一份**键集与 zh_cn 相同**的译文，
玩家把游戏语言切到「文言」就能看到它。

## ⚠ 字形：**用繁体**

这一条是取证来的，不是偏好：把原版 `minecraft/lang/lzh.json` 从 launcher 资源索引里
读出来（见 `_rzh_vanilla_names.txt` / `_rzh_probe_lzh_meta.txt`），它是

```
block.minecraft.iron_ore   鐵礦
item.minecraft.raw_iron    鐵璞
item.minecraft.iron_ingot  鐵錠
item.minecraft.diamond_sword 金剛劍
item.minecraft.iron_helmet 鐵胄
```

**全是繁体**（原版这个语言就叫「文言」，用繁体才配得上；而且 zh_cn 已经是简体，
再来一份简体没有意义）。所以本文件：

- 字形用**繁体**：鈦、鎢、鈾、鋁、鈷、鎳、錳、鋰、矽、礦、錠、鐵、銅、銀、鋼、
  電、氣、機、器、層、數、這、來、時、為、與、產、爐、熱、溫、體、結構、殼、線。
- 词汇沿用**原版 lzh 的风格**：之、者、也、乃、凡、即、須、勿、莫、無、其、焉。
- 顺带的：`它` → `其`，`的` → `之`（能改就改），`了` → `矣 / 也`。

## 硬规矩

1. **键一个不改、一个不增、一个不减。** 输出 JSON 的键集必须和给你的输入文件**逐字相同**。
2. **`%s`、`%%`、`%1$s` 一个不动。** 数量和顺序都不能变；`%%` 在游戏里显示成一个 `%`，**不要写成 `%`**。
3. **`\n` 原样保留**（那是游戏里的换行）。JSON 里写 `\n` 两个字符，不是真换行。
4. **`§` 颜色代码**若原文有就照搬。
5. **术语表是命令，不是建议。** 表里有的，必须一字不差地用表里的写法。

## 语体：怎么算"够文言"

- 虚词照用：之、者、也、矣、焉、其、乃、皆、凡、即、故、若、莫、勿、可、須、則。
- 动词收古：無、有、得、入、出、成、破、壞、取、與、置、觀、察、過、通、竭、滿、盡。
- 数词收古：一、二、三……十、百、千、萬；量词尽量省。
- **不要通篇「之乎者也」硬堆**。目标是"读起来像古书，但玩家一眼看懂"：
  关键数字、坐标、层数、FE/mB 数值**必须和原文一样清楚**。
- 现代借词照留：FE、mB、tick、JEI、Shift、右键、mod、群系、多方块、缓存。
  这些换成"刻度""机巧"会让玩家看不懂 —— **宁可白，不可玄**。

## 材料 / 物品（**必须照抄**）

| 键里的词 | 文言（繁体） |
|---|---|
| titanium | 鈦 |
| tungsten / wolframite | 鎢 / 黑鎢 |
| uranium | 鈾 |
| aluminum / aluminium | 鋁 |
| cobalt | 鈷 |
| nickel | 鎳 |
| manganese | 錳 |
| silver | 銀 |
| lithium | 鋰 |
| silicon | 矽 |
| sulfur | 硫 |
| carbon | 碳 |
| vibranium | 振金 |
| star steel | 星璨鋼 |
| titanium alloy | 鈦合金 |
| high carbon steel | 高碳鋼 |
| thermal metal | 熱力金屬 |
| light / hard (alloy) | 輕質 / 硬質 |
| raw X（粗X） | 粗X（粗鐵、粗銅、粗鋁…） |
| X ingot | X錠 |
| X plate | X板 |
| X ore | X礦 |
| deepslate X ore | 深X礦 |
| X powder / dust | X粉 |
| X bucket | X桶 |
| magnet | 磁石 |
| asphalt block | 柏油塊 |
| bitumen | 瀝青 |
| crude oil | 原油 |
| naphtha | 石腦油 |
| gasoline / diesel | 汽油 / 柴油 |
| LPG | 液化石油氣 |
| capacitor | 電容 |
| empty spool / cable spool | 空線軸 / 線纜軸 |
| copper wire / silver wire | 銅線 / 銀線 |
| terminal block | 接線端子 |
| wiring block | 接線塊 |
| heat sink / heater | 散熱裝置 / 加熱裝置 |
| common / advanced / stable / heat-resistant metal block | 一般 / 高級 / 穩定 / 耐熱金屬塊 |
| solar panel | 太陽能板 |
| salt dryer | 曬鹽機 |
| lithium battery | 鋰電池 |
| music disc | 音樂唱片 |
| star chart tome | 星儀圖之章 |
| starfall pendant | 星軌墜 |

## 机器 / 结构（**必须照抄**）

| 键里的词 | 文言（繁体） |
|---|---|
| electrolyzer | 電解器 |
| distillation tower controller / operator | 分餾塔控制器 / 分餾塔操作器 |
| alloy smelter controller / port / furnace | 合金爐主控 / 合金爐接線口 / 合金冶煉爐 |
| electric blast furnace | 電力高爐 |
| micro crusher | 微型粉碎機 |
| hydraulic press | 液壓機 |
| filling machine | 灌裝機 |
| fluid pump / fluid pipe / fluid exchanger | 流體泵 / 流體管道 / 容器換流器 |
| oil pump | 採油機 |
| diesel generator controller / port | 柴油發電機控制器 / 柴油發電機接線口 |
| lithium battery plant | 鋰電池構造間 |
| salt decomposer | 鹽分解器 |
| air separator | 空氣分離器 |
| ammonia synthesis chamber | 合成氨反應室 |
| combustion chamber | 燃燒反應室 |
| acidic reaction chamber | 酸性反應室 |
| hydrodesulfurization chamber | 加氫脫硫反應室 |
| generator / low-tier generator | 發電機 / 低級發電機 |
| power capturer | 動力能源捕獲器 |
| high pressure tank | 高壓氣罐 |
| oil bucket | 油桶 |
| end crystal | 終界水晶 |
| netherite / netherite scrap | 獄髓 / 獄髓碎片 |
| charcoal / gravel / quartz / log | 木炭 / 砂礫 / 石英 / 原木 |

## 化学式与单位（照抄表里的写法）

氫、氧、氮、氯、氨、二氧化碳、碳酸、硝酸、硫酸、鹽酸、氯化鈉、碳酸鋰、
海鹽、FE、mB、tick、FE/t、mB/s、B（桶）、Y=、層、排、列、格、座、塊、個。

## 成就标题（**必须照抄**）

| 键 | 文言标题 |
|---|---|
| advancements.…electrolyzer.title | 析水為二氣 |
| advancements.…distillation.title | 一油分五品 |
| advancements.…alloy_smelter.title | 配成一爐 |
| advancements.…blast_furnace.title | 築高爐 |
| advancements.…starfall.title | 召星墜地 |
| advancements.…salt.title | 向海取鹽 |
| advancements.…star_steel.title | 煉得星璨鋼 |
| advancements.…oil_pump.title | 海底取油 |
| advancements.…capacitor.title | 攢得一電容 |
| advancements.…sulfur.title | 瀝青中取硫 |

（`acid` / `combustion` / `hard_alloy` / `light_alloy` / `stable_block` / `lithium_battery`
六个成就的标题**与物品同名**，按材料表写即可。）
