# -*- coding: utf-8 -*-
"""_zf201_docs2.py —— ZF201 第二轮补充（斧/镐的档位 + 钢剑自带附魔）写进开发档案

跑法：
    python build/zftools/_zf201_docs2.py            # 只体检
    python build/zftools/_zf201_docs2.py --write
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
HEAD = u"#### 八、⚠ 第二轮补充（用户同一天追加的三条）"

ADD = u"""

### ZF201 补（0.16）钢斧 / 钢镐各换一档 + 钢剑做出来自带锋利 II / 横扫 III

用户原话：「**钢剑做出来自带横扫3和锋利2 钢斧金挖掘速度铁等级 钢镐钻石挖掘等级 铁镐速度**」。

#### 一、三把从此各用一档（第一轮是三把共用 `ModTiers.STEEL`）

| 工具 | 耐久 | 显示伤害 | 挖掘速度 | 挖掘等级 | 附魔 |
|---|---|---|---|---|---|
| 钢剑 `STEEL_SWORD` | 500 | 6 | 铁 6.0 | 铁 | **做出来自带锋利 II + 横扫之刃 III** |
| 钢镐 `STEEL_PICKAXE` | 500 | 4 | **铁 6.0** | **钻石** | — |
| 钢斧 `STEEL_AXE` | 500 | 9 | **金 12.0** | **铁** | — |

- **钢斧"金挖掘速度铁等级"**：速度取金的 12.0（原版最快一档），等级仍是铁
  ⇒ 砍得飞快，但**挖不了钻石矿**（这是"铁等级"的字面结果，不是漏配）。
- **钢镐"钻石挖掘等级铁镐速度"**：1.21 里"挖掘等级"就是"挖不动的方块集合"那张标签
  ⇒ `BlockTags.INCORRECT_FOR_DIAMOND_TOOL`（钻石矿/黑曜石能挖，**古代残骸挖不了**）；
  1.20.1 那边是 int 等级 `LEVEL_DIAMOND = 3`。
- **钢剑用户没提档位** ⇒ 保持第一轮的"套用铁套"（速度 6.0、挖掘等级铁）。
  剑多出来的是**附魔**，不在档位上。
- 三把的伤害加成仍是铁的 2.0（显示伤害 6 / 4 / 9 没动过）—— 用户只点了速度与等级。

#### 二、钢剑"做出来自带"是怎么落的：`SteelSwordItem.onCraftedBy`

- 只有**真的在工作台合成出来的那一把**才带附魔；创造模式物品栏拿的、`/give` 给的都不带 ——
  这正是"做出来自带"与"全局默认附魔"的分界。
- 触发点**不是回忆**：本轮从 1.21.1 字节码核实 `CraftingMenu` 里有一处
  `invokevirtual Item.onCraftedBy(ItemStack, Level, Player)`（工作台把成品交给玩家时触发），
  `ItemStack.onCraftedBy(Level, Player, int)` 也转发到这里。两侧同一条路。
- 只在服务端加（`!level.isClientSide`），避免客户端本地预测出一个带附魔的假物品。
- 两个等级是**用户给的固定数**（`SHARPNESS_LEVEL = 2` / `SWEEPING_EDGE_LEVEL = 3`），
  不吃附魔台、不随机；重复合成不叠加（`ItemStack.enchant` 是"设成这个等级"）。
- ⚠ **两侧 API 差异**：1.21 的 `Enchantments.SHARPNESS` 是 `ResourceKey<Enchantment>`，
  要先从**当前世界的注册表**取 `Holder`（`registryOrThrow(Registries.ENCHANTMENT).getHolderOrThrow(key)`）
  再 `stack.enchant(holder, n)`；1.20.1 里它直接就是 `Enchantment` 对象，一步到位。
  **别在静态初始化期取注册表**（本工程 §4.1 那条老坑）。

#### 三、门

| 项 | 值 |
|---|---|
| 探针 | `_zf201_verify.py` **281 项 / 0 失败**（第一轮 247 + 本轮 34）：新增"三档各自的速度/等级"源码锚点、`STEEL_AXE_SPEED = 12.0` 的 javap 常量、物品真的用了对应档位、以及钢剑那组（`onCraftedBy` 覆写 / 常量池里同时有 `SHARPNESS` 与 `SWEEPING_EDGE` / 两个等级常量 / 只在服务端加 / 两侧各自的取 Holder 方式） |
| 反证刀 | `_zf201_falsify.py` **K1~K5 全中**：钢剑档位挖钻石 / 斧速度 12→6 / 镐等级钻石→铁 / 横扫 III→I / **删掉挂附魔那两行**（最后这把最像"改错了但游戏不报错"） |
| 编译 | 两侧 `compileJava` 均 BUILD SUCCESSFUL |

#### 四、要你实测

1. 工作台做一把**钢剑** → 工具提示里应当直接有 **锋利 II** 与 **横扫之刃 III**（不用附魔台）；
2. 从**创造模式物品栏**拿的钢剑 → **不该**带这两个附魔（这是"做出来自带"的对照面）；
3. 钢斧砍原木/木头 → 明显比钢镐快（12.0 对 6.0）；
4. 钢镐挖**钻石矿** → 掉钻石（钻石等级）；挖**远古残骸** → 挖不动（那是下界合金档）；
5. 钢斧挖钻石矿 → **挖不动**（铁等级，与钢镐的差别正在这里）。
"""

fails = []


def main(argv):
    write = u"--write" in argv
    text = io.open(ARCH, encoding="utf-8").read()
    if u"ZF201 补（0.16）钢斧 / 钢镐各换一档" in text:
        print(u"  [SKIP] 档案里已经有 ZF201 补那一节")
    else:
        print(u"  [%s] 开发档案.md 追加 ZF201 补一节（%d 行）"
              % (u"写" if write else u"将写", len(ADD.split(u"\n"))))
        if write:
            io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(
                text.rstrip(u"\n") + u"\n" + ADD)

    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
