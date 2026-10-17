# -*- coding: utf-8 -*-
"""_zf201_docs.py —— 把 0.16 ZF201（钢套 + 钢制工具）写进开发档案 + 交接文档

跑法：
    python build/zftools/_zf201_docs.py            # 只体检
    python build/zftools/_zf201_docs.py --write
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJ = r"E:\PotatoST\PotatoSTneoforge1.21.1"
ARCH = os.path.join(PROJ, "docs", "开发档案.md")
HANDOFF = os.path.join(PROJ, "docs", "多会话协作交接.md")
HEAD = u"### ZF201（0.16）钢套 + 钢镐 / 钢剑 / 钢斧（两个工程都做了）—— **待你实测**"

SECTION = HEAD + u"""

用户原话：「做钢的全套盔甲 钢镐 钢剑 钢斧 全部套用铁套就可以 耐久多200-300 你自己决定
然后每件+0.1击退抗性 +1盔甲韧性 盔甲穿身上的材质先用下界合金凑合 贴图在工作区的 材质 文件夹里」。

#### 一、七件的数值（全部照铁套，只多耐久 + 用户点名的两个属性）

| 件 | 耐久 | 护甲值 | 韧性 | 击退抗性 | 附魔权重 | 修理材料 |
|---|---|---|---|---|---|---|
| 钢头盔 `steel_helmet` | **415**（铁 165 + 250） | +2 | +1 | +0.1 | 14 | 钢板 |
| 钢胸甲 `steel_chestplate` | **490**（240 + 250） | +6 | +1 | +0.1 | 14 | 钢板 |
| 钢护腿 `steel_leggings` | **475**（225 + 250） | +5 | +1 | +0.1 | 14 | 钢板 |
| 钢靴子 `steel_boots` | **445**（195 + 250） | +2 | +1 | +0.1 | 14 | 钢板 |
| 钢镐 `steel_pickaxe` | **500**（铁 250 + 250） | 显示伤害 4 | — | — | 14 | 钢板 |
| 钢剑 `steel_sword` | **500** | 显示伤害 6 | — | — | 14 | 钢板 |
| 钢斧 `steel_axe` | **500** | 显示伤害 9 | — | — | 14 | 钢板 |

- **耐久"多 200-300 你自己决定"** ⇒ 取 **+250**（区间正中）。七件都是"铁的原数 + 250"，
  没有一件是我另外拍的数字（盔甲 165/240/225/195、工具 250 都是原版铁那一行）。
- **工具"套用铁套"**：挖掘等级 = 铁（**挖不了钻石矿**）、速度 6.0、伤害加成 2.0、附魔权重 14
  ⇒ 三把的显示伤害与铁**一模一样**（剑 6 / 镐 4 / 斧 9），只有耐久翻倍。
- **每件 +1 韧性、+0.1 击退抗性** 落在**材料级**字段上（`toughness = 1.0F`、`knockbackResistance = 0.1F`）；
  这两个数正好是"每件都加这么多"的语义（原版 `ArmorItem` 构造器会把它们逐件拼成属性修饰符，
  取证见 `ModVibraniumPiece` 类注释里对 `ArmorItem.java:70-94` 的引用）⇒ **四件一个子类都不用**，
  直接用原版 `ArmorItem` + `Item.Properties().durability(n)`。
- 七个**没有任何套装效果**（用户没提，也没要 Shift 说明）—— 这点和钛合金 / 星璨钢 / 振金都不一样，
  别照着另外几套抄出一堆死逻辑。

#### 二、"贴图在工作区的 材质 文件夹里"怎么落的

`E:\\PotatoST\\材质\\` 里那 7 张（钢头盔_1 / 钢胸甲_3 / 钢护腿1 / 钢靴子_2 / 钢镐_4 / 钢剑_1 / 钢斧_1）
**逐字节复制**成两侧的 `textures/item/steel_*.png`（已验 7 张都是 16×16 RGBA，没有转档）。
文件名带数字后缀是**用户素材的原名**，落到工程里按 §4.24 改成 ASCII（`steel_helmet` 等）。
模型 `models/item/steel_*.json`：盔甲 4 件 `minecraft:item/generated`、工具 3 把 `minecraft:item/handheld`。

**穿在身上**的图层是 `minecraft:netherite`（用户原话"盔甲穿身上的材质先用下界合金凑合"）——
渲染读 `minecraft:textures/models/armor/netherite_layer_1.png` / `_layer_2.png`，
**背包图标不归这一条管**（那走 `models/item` 的 layer0，已经是用户给的钢贴图）。
以后要自绘，只改 `ModArmorMaterials.STEEL` 里那一行 `ResourceLocation`。

#### 三、配方：逐格照抄原版铁那七张，只换材料

本轮从 `client.jar` 现抠 `data/minecraft/recipe/iron_*.json` 七张（不是回忆）：

| 件 | 图纸 | 材料 |
|---|---|---|
| 头盔 | `XXX` / `X X` | 钢板 ×5 |
| 胸甲 | `X X` / `XXX` / `XXX` | 钢板 ×8 |
| 护腿 | `XXX` / `X X` / `X X` | 钢板 ×7 |
| 靴子 | `X X` / `X X` | 钢板 ×4 |
| 镐 | `XXX` / ` # ` / ` # ` | 钢板 ×3 + 木棍 ×2 |
| 剑 | `X` / `X` / `#` | 钢板 ×2 + 木棍 ×1 |
| 斧 | `XX` / `X#` / ` #` | 钢板 ×3 + 木棍 ×2 |

⚠ **工具那三条的空格是有意义的**：镐的 ` # ` 左右各一个空格、斧第三行第一格是空的。
抄错一格就是"摆上去做不出来"，而 RecipeCheck 只查"字符在不在 key 里"，抓不到形状 ⇒
`_zf201_verify.py` 的 ⑧ 组**逐格对照**原版那七张（pattern 完全相等才算过）。

配方材料 = **钢板 `potato_s_t:steel_plate`**（本轮与用户确认："套用铁套"的图纸，材料用钢板；
模组里没有 `steel_ingot` 这件东西，只有 `steel_plate` 与 `high_carbon_steel`）。
修理材料也用它 ⇒ 玩家拿钢板在铁砧上就能修。

#### 四、两个工程都做了（1.20.1 ↔ 1.21.1 的四处真差异）

| 处 | NeoForge 1.21.1 | Forge 1.20.1 |
|---|---|---|
| 挖掘等级 | `BlockTags.INCORRECT_FOR_IRON_TOOL`（1.21 没有 level 整数） | `int` 等级 **2**（新增 `ModTiers.LEVEL_IRON`） |
| 盔甲材料耐久 | 材料不管耐久（只有物品属性） | 接口多一道 `getDurabilityForType`（但 `properties.durability(n)` 先写死就赢） |
| 附魔光效 / 无限耐久 | 数据组件 | 物品类覆写（振金那条，本轮钢套用不到） |
| 配方产物字段 | `result: {"id": ...}` | `result: {"item": ...}` |

⇒ **配方 JSON 不能从源工程照抄文本**：字段名不同，抄过去游戏里会变成"空配方"。
Forge 侧那 7 张由 `_zf201_forge_recipes.py` 从同一张表生成（脚本里把这条差异写死了）。

#### 五、门

| 项 | 值 |
|---|---|
| 探针 | `_zf201_verify.py` **247 项 / 0 失败**，**两个工程都查**：七件注册（源码 + 编译产物常量池）/ 创造页 / 材料六个数 / 耐久七个数 / 工具档位六个数（`javap -constants`）/ 贴图 16×16 / 模型父级 / 配方逐格对照原版 / 五语言名 / **两侧配方逐字段相同** |
| 资产 | `_zf201_assets.py`（7 张贴图 + 7 个模型，两侧） |
| 语言 | `_zf201_lang.py`（**五语言**：zh_cn / en_us / ja_jp / **lzh（文言）** / ru_ru，各 +7 键） |
| 配方 | 源工程走 `_zf45_recipes.py` 总表 +7 条（`--write` 生成，重跑其它 61 份一字不变）；Forge 侧 `_zf201_forge_recipes.py` |
| 编译 | 两侧 `compileJava` 均 BUILD SUCCESSFUL |

#### 六、要你实测

1. 物品栏创造页最后面七件都在（钢盔甲四件 + 钢镐/钢剑/钢斧），**背包图标是 材质 里那 7 张**；
2. 合成：钢板按铁套图纸摆 → 七件都出得来；**空着的那一格**（斧第三行左）塞钢板应当**做不出来**；
3. 穿满四件看面板：护甲值 2/6/5/2（**与铁套一样**）、韧性每件 +1（四件共 4）、击退抗性每件 +0.1；
4. **穿身上看外观**：现在借用的是**下界合金**的盔甲图层（深色带纹），不是你给的贴图 —— 这是你说的"先用下界合金凑合"，要换成自绘的随时说；
5. 耐久：钢剑/镐/斧都该是 **500**（铁是 250）；钢盔甲 415/490/475/445；
6. 钢镐**挖不了钻石矿**（挖掘等级是铁那一档）—— 这是"套用铁套"的直接结果，不是你挖错了。

#### 七、⚠ 两件没做 / 要你知道的

1. **版本号没有动**（两个工程都还是 `mod_version=0.15`）。"顶到 0.16"在本工程是一条**独立的
   版本线**（照 ZF198 的先例：`gradle.properties` + 17 份活体门/脚本 + 3 份文档，共 25 份一起改，
   因为 143 处脚本里钉着 `0.15` 的 jar 名与版本断言）。要我现在顶上去，说一声，我按那条先例做。
2. Forge 1.20.1 工程**没有 git 仓库**（工作区里只有 NeoForge 那个是）。所以本轮 Forge 侧的改动
   **不会被提交**，只落在盘上；要纳入版本管理得先给它 `git init` 或者并进主仓。
"""

HANDBOFF_ADD = u"""
## 0.16 ZF201（钢套 + 钢制工具）

- 两个工程（`PotatoSTneoforge1.21.1` / `PotatoSTforge1.20.1`）都做了七件：钢盔甲四件 + 钢镐/钢剑/钢斧，
  数值照铁套 + 耐久各 +250 + 每件 +1 韧性 / +0.1 击退抗性；穿身上的图层借用下界合金。
- 工具链：`_zf201_assets.py`（贴图/模型）/ `_zf201_lang.py`（五语言）/ `_zf201_forge_recipes.py`（Forge 侧配方）/
  `_zf201_verify.py`（247 项，两侧都查）；源工程配方总表 `_zf45_recipes.py` 加了 7 条。
- ⚠ **版本号仍是 0.15**：顶到 0.16 是一条独立版本线（照 ZF198 先例要一起改 25 份）。
- ⚠ Forge 1.20.1 工程**没有 .git**，那边的改动只在盘上。
"""

fails = []


def main(argv):
    write = u"--write" in argv
    arch = io.open(ARCH, encoding="utf-8").read()
    if HEAD in arch:
        print(u"  [SKIP] 开发档案里已经有 ZF201 那一节")
    else:
        n = len(SECTION.split(u"\n"))
        print(u"  [%s] 开发档案.md 追加 ZF201 一节（%d 行）" % (u"写" if write else u"将写", n))
        if write:
            io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(
                arch.rstrip(u"\n") + u"\n\n" + SECTION)

    ho = io.open(HANDOFF, encoding="utf-8").read()
    if u"ZF201（钢套 + 钢制工具）" in ho:
        print(u"  [SKIP] 交接文档里已经有 ZF201 那一条")
    else:
        print(u"  [%s] 交接文档 追加一条" % (u"写" if write else u"将写"))
        if write:
            io.open(HANDOFF, "w", encoding="utf-8", newline=u"\n").write(
                ho.rstrip(u"\n") + u"\n" + HANDBOFF_ADD)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
