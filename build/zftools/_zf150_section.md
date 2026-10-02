
## ZF150（0.12）：四种「粒」（铝 / 钴 / 镍 / 银）

用户原话：「嗯嗯放素材了几张图 其中四种粒你先注册一下 配方就是原版的
（对应锭合成9个粒 9个粒合成1个锭 记得加标签兼容别的mod）重复一遍！现在是0.12版本」

素材：`铝粒_001.png` / `银粒_001.png` / `钴粒_001.png` / `镍粒_001.png`（13:19~13:20 放的）。

### 一、素材

四张**形状完全相同**（不透明都恰好 34 像素）、**共用同一套描边色**
（`#585f68` 深描边 + `#393c40` 阴影），只有高光色按金属变 ⇒ 一整套同模的粒。
16×16 / 8 位 RGBA / **零半透明** ⇒ 原字节复制，零重编码。

### 二、注册（Java）

| 项 | 落点 |
|---|---|
| 物品 | `ModItems.java` 四个 `register("<材料>_nugget")` + 创造页 `accept`（跟在对应锭后面，与原版排法一致） |
| 贴图 | `textures/item/{aluminum,cobalt,nickel,silver}_nugget.png` |
| 模型 | `models/item/*_nugget.json`（`parent: minecraft:item/generated`，指自己） |
| 语言 | **五**语言各 +4 键（含 ZF148 之后新增的文言 `lzh`） |

### 三、配方（**逐字照抄原版**，从 client.jar 现抠）

原版 `data/minecraft/recipe/iron_nugget.json` 与 `iron_ingot_from_nuggets.json`：

| 方向 | 类型 | 结构 |
|---|---|---|
| 锭 → **9** 粒 | `minecraft:crafting_shapeless`（**无序**） | `type / category(misc) / ingredients / result(count 9)` |
| **9** 粒 → 锭 | `minecraft:crafting_shaped` | 3×3 全 `#`、`group = "<材料>_ingot"`、`result(count 1)` |

⇒ 8 份新配方：`<材料>_nugget.json`（无序，锭→9粒）
+ `<材料>_ingot_from_nuggets.json`（定形，9粒→锭）。

**写进了生成器表**（本工程"配方只有一个来源"的规矩）：`build/zftools/_zf45_recipes.py`
新增了一个 `SHAPELESS` 表 + `build_shapeless()`，并给 `build()` 补上了 `group` 字段
（原版那条有、老 35 条没有 ⇒ 只在配方自己带 `group` 时才输出，老配方一个字节没动）。
跑完 `--write` 复核：**老 74 份逐字节未变**（先记录哈希再比）。

### 四、标签（用户点名的「兼容别的 mod」）

结构**照 NeoForge 21.1.235 自带的那份现抠**（`data/c/tags/item/nuggets.json`）——
它是**聚合标签**，引用 `#c:nuggets/<材料>`：

| 文件 | 内容 |
|---|---|
| `data/c/tags/item/nuggets/{aluminum,cobalt,nickel,silver}.json` | 各放本模组那一颗粒 |
| `data/c/tags/item/nuggets.json` | 引用上面 4 个 `#c:nuggets/…` + `#forge:nuggets` 与 `#forge:nuggets/<材料>` 的 `required:false` 回退（NeoForge 自己就这么写，老 Forge 系别的 mod 也能互通） |

> 同 id 标签在数据包合并时是**合并**语义，所以在本模组 `data/c/` 下复写 `c:nuggets` 是安全的
> —— 这正是工程里 `c:ingots` 的既有做法。

### 五、⚠ 连带：语言键数是**活体数字**（579 → 583）

四种粒 × 1 键 = **每份语言文件 +4**（16 是四份合计，我一开始口算成"每份 +16"，
脚本里把 `579 + 4 = 583` 写成了断言，免得下次再错）。

这个数被**二十多份常驻门**写死在 `EXPECT_KEYS` / `KEY_NEW` / `KEYS` / `counts == N` 里
⇒ 全部跟到 **583**（`lzh` 581 → **585**）。

**不该动的**：`_zf149_verify.py` 里那两个数（579/581）指的是
**已发布 jar**（`release\PotatoST-0.12.jar`，ZF149 打的）里的事实 —— 本轮**没打包**，
动它就是改事实。门里专门留了一条断言钉住"这两处没被动"。

### 六、⚠ 顺带修了 3 份**本来就坏**的门（不是本轮造成的）

`_zf73_verify.py` / `_zf78_verify.py` / `_zf79_verify.py` 在**本轮开始之前**
语法就不过（`ast.parse` 失败）。根因是另一条线的 **ZF147**（版本线抬到 0.12）
那次改写**丢了缩进**：

- `_zf73:237`、`_zf79:283`、`_zf78:557` —— `check(...)` 被写到了**第 0 列**
- `_zf78:315/345` —— 中文串里用了 **ASCII 双引号**（`按"错格数最少"挑`）⇒ 字符串被截断
- `_zf78` 的 `section_c()` 里 `tower` 只在 373 行赋值、284 行就用了 ⇒ 运行到那儿 `UnboundLocalError`

**证据**：`_zf150_retarget3.py` 写盘前有 `ast.parse` 自检，它报这三份"改后语法错误**没写盘**"，
而**同一行号**在"原样自检"里也报 ⇒ 改之前就坏。我那两个脚本**只替换含 579 的行**，
坏的那几行里**一个 579 都没有** ⇒ 不可能是它们碰的。

顺手还把 `_zf79` 一处自相矛盾的断言修了（标签写「0.12」、断言却查 `mod_version=0.11`）。

### 七、验收

| 项 | 结果 |
|---|---|
| `_zf150_verify.py`（**常驻**，7 组） | **131 项 0 失败**：注册 / 资源 / 无序配方 / 定形配方 / 标签 / 语言 / 跟平 |
| `_zf45_recipes.py --write` | 47 条（39 定形 + 4 无序 + 4 锻造台），**老 74 份逐字节未变** |
| 五语言 | 583×4 + lzh **585**；键集合对齐；四语言相对改前件**只多这 4 个键**、旧键值一字未改 |
| `compileJava` / `processResources` | **BUILD SUCCESSFUL** |
| `TextureCheck` / `ModelCheck` / `SoundCheck` / `JsonCheck` | 全 **0 失败** |
| 全部 `_zf*_verify.py` | **80 份语法全可解析** |

> ⚠ 两点如实说明：
> ① 本轮的"改前件" `zf150_pre/` 是**改完之后**建的（语言文件的 579 版已被我改掉）
>    ⇒ `_zf150_verify.py` 的 F5/F6（"相对改前件只多这 4 个键"）目前只能与**自身**比，
>    这条判据**下一轮才真正有牙**。这一轮它靠的是"键数 + 键集合"两条硬判据。
> ② `RecipeCheck.ps1` **只校验 `crafting_shaped` 与 `smithing_transform`**，无序配方它 `[SKIP]`
>    ⇒ 那 4 条「锭→9粒」走的是 `_zf150_verify.py` 的 C 组（逐字段比 type/category/ingredients/result）。
>    要把 shapeless 也纳入 `RecipeCheck`，得改那份 PowerShell（本就是坏的：PS 5.1 按 GBK 读 UTF-8）。
