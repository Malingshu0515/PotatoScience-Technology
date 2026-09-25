# -*- coding: utf-8 -*-
"""_zf67_docs.py —— ZF67 档案落笔（工具挂原版"能附魔"标签）"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"
SHA = u"95c970e41c764f729df4ec100a20f100b4236bb2"

ROW = u'''| ZF67 | 无改前件（本轮**只新增两个原版物品标签 JSON**，一个既有文件都没动；探针与脚本在 `新增文件\\` 里） | 0.10：**修用户实测报的问题**「附魔台不给钛合金附魔」（原话：「附魔台附魔能力32还是提示 附魔能力受限 不可以给钛合金附魔 要不然略微调小一点？还是怎么办」）。**根因不是附魔能力**：附魔台挑附魔走 `EnchantmentHelper.getAvailableEnchantmentResults()`，里面那句 `stack.isPrimaryItemFor(enchantment)` 的判据是**原版物品标签**（`#minecraft:swords` / `#minecraft:pickaxes`，再串到 `enchantable/sword`、`sharp_weapon`、`fire_aspect`、`mining`、`mining_loot`、`durability`、`vanishing`），而 ZF66 那两把工具**一个都没挂** ⇒ 附魔能力再高也挑不出任何一条附魔。**实测（探针把标签文件拿掉即可复现）**：`enchantable=true`、`enchantmentValue=25`、`花费=30 级`、**候选 0 条** —— 花费算得出来，就是一条附魔都挑不出来。修法：新增 `data/minecraft/tags/item/swords.json` 与 `pickaxes.json`（`"replace": false`，各只加自己那一条）⇒ 整条附魔链一次性接通。**所以不用把附魔能力调小**（25 比金的 22 高没问题；原版对照里钻石剑才 10 也照样能附）。**验证**：探针 `AlloyEnchantCheck` **43 项全 [OK]**（9 张标签归属 + 16 条逐附魔的 `isPrimaryItemFor`（锋利/亡灵杀手/节肢杀手/击退/火焰附加/抢夺/横扫之刃/耐久/经验修补/消失诅咒；镐：效率/时运/精准采集/耐久/经验修补/消失诅咒）+ 2 条反向断言（剑吃不到效率、镐吃不到锋利）+ 附魔台那条路：剑 30 级时 **8 条候选**、镐 **4 条**，与钻石剑/钻石镐**完全同数** + 4 组原版对照）；新写常驻 `_zf67_verify.py`（**12 项**：标签文件在、`replace:false`、只加自己那一条、id 反查）；反证 2 处：把 `swords.json` 移走 ⇒ 探针 **17 FAIL**（全在剑那条链上、镐全过，且 `candidates@30=0` 正好复现用户的 bug）；把 `replace` 改成 `true` ⇒ 复核 **1 FAIL**。⚠ **上一轮为什么漏了**：ZF66 我把"工具不挂 `c:` 标签"那条**跨 mod 兼容**规则照搬到了**原版功能标签**上 —— 这两类标签根本不是一回事（§4.39） | 见 §4.39 / §6.8 / §9 |'''

OLD9 = u'''      ⑦ 工具**不该有"按住 Shift"那一行**。'''

NEW9 = OLD9 + u'''
- [ ] **ZF67：再试附魔台**（成品 `95c970e4…`）。两把工具现在都挂在原版 `#minecraft:swords` /
      `#minecraft:pickaxes` 上，附魔台应当能正常出选项（剑 30 级时 8 条候选、镐 4 条，与钻石剑/镐同数）。
      要看的：① 放上剑/镐能不能出三条附魔、能不能真的附上；② 铁砧 + 附魔书也能用；
      ③ 你看到的那句提示如果是**别的 mod** 弹的，把原文/来源告诉我 —— 我按原版代码查到的现象是
      "花费算得出来、候选 0 条"（附魔台什么也不显示），跟我修好后应当不一样。
- [ ] ZF67 说明：**没有**给工具挂 `c:` 那类兼容标签（`c:tools/melee_weapon` 等）——
      按长期规则，要跨 mod 兼容得你点名。这次挂的 `minecraft:swords` / `minecraft:pickaxes`
      是**原版功能标签**（不挂 = 原版附魔都用不了），不是兼容性取舍。'''

M_ANCHOR = u"\n## 5. 版本与 [ZF] 流水线记录"

M_INSERT = u'''
### 4.39 【致命】"工具不挂标签"顺手把**原版附魔**也关掉了 —— `c:` 兼容标签 ≠ 原版功能标签（0.10 ZF67）

用户报「附魔台不给钛合金附魔」，他还以为是附魔能力太高，问要不要调小。查下来是这么回事。

附魔台挑附魔的代码在 `EnchantmentHelper.getAvailableEnchantmentResults(level, stack, possible)`：

```java
possibleEnchantments.filter(stack::isPrimaryItemFor).forEach(...)
```

`isPrimaryItemFor` 问的是"这个物品在不在**这条附魔**的 `primary_items`（没有就看 `supported_items`）里"，
而原版那些附魔声明的是**物品标签**：锋利 / 亡灵杀手 / 节肢杀手 → `#minecraft:enchantable/sharp_weapon`、
效率 → `enchantable/mining`、时运 / 精准采集 → `enchantable/mining_loot`、耐久 / 经验修补 →
`enchantable/durability`…… 而这些标签又都挂在 **`#minecraft:swords` / `#minecraft:pickaxes`** 上。

ZF66 加那两把工具时，我把"矿物 / 合金 / 锭之外的东西默认不挂标签"这条**跨 mod 兼容**规则也套到了这里
⇒ 两把工具不在任何原版功能标签里 ⇒ **不是"别的 mod 不认"，是原版自己就不给附魔**。
实测（探针把标签文件拿掉即可复现）：`enchantable=true`、`enchantmentValue=25`、`花费 30 级`、
**候选 0 条** —— 花费算得出来、就是一条附魔都挑不出来。

三条结论：

1. **`c:` 兼容标签和原版功能标签是两码事**：前者决定"要不要跟别的 mod 互通"，后者决定"原版机制认不认你"。
   `minecraft:swords` / `minecraft:pickaxes` / `minecraft:enchantable/*` / `minecraft:mineable/*` /
   `minecraft:needs_*_tool` 这一类**必须挂**，不挂就是功能缺失；
2. **加新工具 / 新装备时，标签清单要照"原版同类物品挂了哪些"抄一遍**：剑 → `swords`、镐 → `pickaxes`
   （这两张一挂，整条附魔链自动接通）；别只想着 `c:`；
3. **数值不是万能的**：用户直觉是"附魔能力太高被限制"，但附魔能力只决定**花费多少级**，
   "能不能附、能附什么"由**标签**决定。修之前先按代码找判据，别先调数值。
'''

J_ANCHOR = u'''| 9 | 配方 | 形状照原版：剑 `["X","X","S"]`、镐 `["XXX"," S "," S "]`；列数规则见 §6.13 |'''

J_INSERT = J_ANCHOR + u'''
| 10 | **原版功能标签**（`data/minecraft/tags/item/`） | 剑 → `swords.json`、镐 → `pickaxes.json`（`"replace": false`，只加自己那一条）。**不挂 = 原版附魔台一条附魔都挑不出来**（ZF67 实测：附魔能力 25、花费 30 级、候选 **0** 条）。这张表是"原版机制认不认你"，与 `c:` 兼容标签不是一回事（§4.39） |'''


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF66 |") and not added:
            out.append(ROW)
            added = True
    if not added:
        problems.append(u"没找到 ZF66 行")
    text = u"\n".join(out)

    for name, old, new in ((u"§9 ZF66 复验条尾", OLD9, NEW9),
                           (u"§6.8 工具表尾", J_ANCHOR, J_INSERT),
                           (u"§5 标题锚点", M_ANCHOR, M_INSERT + M_ANCHOR)):
        n = text.count(old)
        if n != 1:
            problems.append(u"%s 命中 %d 次（应为 1）" % (name, n))
        else:
            text = text.replace(old, new, 1)

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§5 ZF67 行（成品 %s）+ §9 两条 + §4.39 + §6.8 第 10 行 已写入" % SHA[:8])
    return 0


if __name__ == "__main__":
    sys.exit(main())
