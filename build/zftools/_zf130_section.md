
## ZF130（0.11）：两个方块加**顶/底渲染** + 银线两件上线

用户原话：「东西放用户素材了 有些方块6个面用的都是一个贴图 你加个顶面底面渲染 然后再用相应的贴图」

### 一、方块：`cube_all` -> `cube_bottom_top`

这两个方块原来是 `parent: minecraft:block/cube_all` —— **六个面都取同一张 `all` 贴图**，
正是用户说的「6 个面用的都是一个贴图」。现在改成 `minecraft:block/cube_bottom_top`
（**与本工程既有的 `lithium_battery` 同一个父级、同一套写法**）：

| 方块 | top / bottom（你新给的） | side（现有那张，**一个字节没动**） |
|---|---|---|
| `lithium_battery_plant`（锂电池构造器） | `lithium_battery_plant_top.png`（2949 B / sha1 `351dd13e…`） | `lithium_battery_plant.png`（sha1 `09a039f5…`） |
| `diesel_generator_controller`（柴油发电机控制器） | `diesel_generator_controller_top.png`（2947 B / sha1 `98ee845f…`） | `diesel_generator_controller.png`（sha1 `dad66213…`） |

- 顶与底**用同一张**（`top` / `bottom` 两个槽指同一个文件）。
- **凭什么断定「现有那张就是侧面」**（不是猜的）：① 你这两张文件名分别叫「上和下面」「顶部&底部」，
  明说了是顶/底；② `lithium_battery_plant.png` 下半截是绿/蓝**竖条纹**（电芯柱面的样子）、
  `diesel_generator_controller.png` 是灰格栅 —— 都是侧面的画法；③ 后者 blockstate **有 facing**，
  侧面本来就该是「转过去看的那一面」。
- 复核方式：`build/zftools/_zf130_show.py` **直接读模型 JSON** 展开六个面再渲染
  （父级 `cube_bottom_top` ⇒ up→top / down→bottom / 四侧→side），图上看到的就是游戏里看到的。

### 二、物品：银线 / 银线轴（**原先借原版贴图**）

| 物品 | 上线贴图 | 原先借的 |
|---|---|---|
| `silver_wire` | `textures/item/silver_wire.png`（2900 B / sha1 `060f8ee8…`，不透明 51 px） | `minecraft:item/iron_nugget` |
| `silver_wire_spool` | `textures/item/silver_wire_spool.png`（3174 B / sha1 `d130d63a…`） | `minecraft:item/iron_ingot` |

两张都是 **16×16 / 8 位 RGBA / 零半透明** ⇒ **原字节复制**。

### 三、活体数字：不是 9 → 7，而是 **15 → 13**

⚠ 本轮差点记错账。我上一轮（ZF116）留给盘上的是 **9**，但**另一条线**在这期间
新增了 `vibranium_*` **四件盔甲**（借原版铁套）⇒ 变成 13；我这轮把银线两件改成自己的图
⇒ 仍是 **13**（一件 +1 一件 −1 抵掉了）。

**权威是第 8 道门现数的结果，不是我的推算**：`TextureCheck.py` 报「待画 = 13」，
清单里没有 `silver_wire` / `silver_wire_spool`（改成功了）⇒ 13 才是盘上事实；
门与公告里当时写的 **15 是改早了**（那条线把自己那 4 件加上去时，我这两件还没改完）。
`_zf130_live.py` 先跑 `TextureCheck` 互核、对得上才动手，三处一起收到 **13**。

### 四、⚠ 本轮踩的自己的坑（见档案 §4.111）

我用「按前缀批量改名」给自己的脚本换 ZF 号，把**别人同前缀的 25 个文件**一起改了名
（117 这个号本来就是他们的）⇒ 已**逐个还原**；其中 3 个同名 scratch 输出
（`_zf117_intake.txt` / `_zf117_show.png` / `_zf117_faces.png`）在改过去时被我的同名文件挤掉，
**源脚本与改前件目录都完好**，那几个报告可重跑。
