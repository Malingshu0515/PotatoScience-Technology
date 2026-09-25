# -*- coding: utf-8 -*-
"""_zf66_docs.py —— ZF66 档案落笔（钛合金剑 / 钛合金镐 + 闸门开关那个坑）"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = u'''| ZF66 | **新建 `zf66_pre`**（7 个改前件：`ModItems` + 4 个 lang + 用户给的两张工具贴图原名件；**这一轮是先抄后改**，ZF65 那次忘了抄的教训立刻用上） | 0.10：**钛合金剑 + 钛合金镐**（用户给数值与两张贴图：「剑；耐久2048点 伤害6.5（附魔权重如果能改的话比金高一点就行）镐；耐久4219点 伤害4 挖掘等级下界合金（附魔权重同理）」「配方按照原版的来 锭换成轻质钛合金就行」「工具就不需要shift查看详细介绍了」）。① 两张贴图**是用户自己放进 `textures/item` 的**（`钛合金剑_001.png` / `钛合金镐_001.png` —— 这次**都是真 PNG**：16×16 RGBA，各有 171 / 188 个全透明像素，不是前几轮那种"改名的 webp"）⇒ 按 §4.24 改名成 ASCII（`titanium_alloy_sword/pickaxe.png`，**改名前后 SHA1 一致**）；② 新写 `ModTiers.java`：**两个档位**（原版 `Tier` 把耐久与伤害加成写在档里，两把工具数值不同 ⇒ 只能各给一个），共同部分 = 挖掘等级 `INCORRECT_FOR_NETHERITE_TOOL`、速度 **9.0**（下界合金同款）、附魔权重 **25**（金 22）、修理材料 = 轻质钛合金（**懒取**，避开 §4.1 那条未绑定崩溃）；③ 伤害换算照原版公式反推：剑 = 玩家基础 1 + (3 + 档位 **2.5**) = **6.5**、镐 = 1 + (1 + 档位 **2.0**) = **4**；④ 两条配方照原版形状（`["X","X","S"]` / `["XXX"," S "," S "]`，X = 轻质钛合金、S = 木棍）；⑤ 模型用 `item/handheld`；四语言各 +2 键（202 → **204**）；⑥ **没有 Shift 说明**（不写 `appendHoverText` ⇒ 物品类恰好就是原版 `SwordItem` / `PickaxeItem`，探针按"类必须恰是原版类"来钉死这条）。**验证**：探针 `AlloyToolCheck` **36 项全 [OK]** —— 注册 / 耐久 2048·4219 / **显示伤害 6.5·4**（先用原版对照把算法钉死：钻石剑 7、铁剑 6、钻石镐 5）/ 附魔权重 25 > 金 22 / 挖掘等级标签 = 下界合金且 ≠ 钻石、**能挖黑曜石与古代残骸**（铁镐反向对照不能）/ 修理材料 = 轻质钛合金（铁锭不行）/ **两条配方真的摆进 3×3 合成格跑 `matches` + `assemble`**（各带一条"少一块料不许成立"的反向断言）；新写常驻 `_zf66_verify.py`（**49 项**：贴图改名与透明底 / 模型 handheld 且指向自己 / 配方形状与 §6.13 列数 / 四语言 204 键 / ModTiers 的数值与懒取 / 无 Shift 说明键）。反证 2 处：把剑的档位改成 `build(1024, 2.0F)` ⇒ 探针**精确 2 FAIL**（耐久 1024、伤害 6.0，其余全过）；把剑模型 layer0 指到钛锭 ⇒ 复核脚本 **1 FAIL**。⚠ **我自己踩的两个坑**：㈠ 探针第一版把"显示伤害"的基础取成 `Attributes.ATTACK_DAMAGE` 的**默认值 2.0**（那是通用生物的；**玩家是 1.0**）⇒ 钻石剑被算成 8、报 2 条假 FAIL（§4.30 又一次"先怀疑期望"）；㈡ **发现闸门脚本里 `RecipeCheck -All` 从来没生效过** —— 开关用 `@('-All')` 当字符串位置参数传，绑不到 `[switch]`，它把 '-All' 当文件名、**检查 0 个配方却打印"全部通过"**；已改成哈希表 splat 并在修好后补跑全量：**27 条定形配方全过、失败 0**（§4.38） | 见 §4.38 / §6.8 / §9 |'''

OLD9 = u'''      （最迟 1 个 tick）；② 重新围起来再开工 ⇒ 声音照常响（别修成"再也不响"）；③ 扳手 Shift 右键拆解 ⇒ 同样停。'''

NEW9 = OLD9 + u'''
- [ ] **ZF66：等你试钛合金剑 / 钛合金镐**（成品 `9239a74d…`）。要看的：① 创造页里两把都在、名字对；
      ② 拿在手里贴图是**竖着握**的（`item/handheld` 生效）；③ 物品面板显示剑 **6.5 攻击伤害**、镐 **4**；
      ④ 耐久是不是 2048 / 4219（高级提示 F3+H 能看到耐久）；⑤ **镐能挖黑曜石与古代残骸**；
      ⑥ 合成：剑 = 2 个轻质钛合金竖排 + 1 根木棍，镐 = 3 个轻质钛合金横排 + 2 根木棍；
      ⑦ 工具**不该有"按住 Shift"那一行**。
- [ ] **ZF66 我替你定的三个数**（你说"高一点就行"、速度没提）：挖掘速度 **9.0**（= 下界合金同款）、
      附魔权重 **25**（原版金 22）、修理材料 = **轻质钛合金**。想改说一声，都集中在 `ModTiers.java`。
- [ ] ZF66 起 `ModItems.java` 过了 400 行（422 行）⇒ Audit 的"文件规模"提示由 6 条变 **7 条**。
      想收拾的话把"工具"拆去 `ModTools.java` 即可（纯提示，不影响功能）。'''

M_ANCHOR = u"\n## 5. 版本与 [ZF] 流水线记录"

M_INSERT = u'''
### 4.38 【流程】把开关当字符串传给 scriptblock，等于**把这道门关掉了**（0.10 ZF66）

ZF66 收尾跑闸门时顺手看了一眼 RecipeCheck 那一段的**原文**，发现它长这样：

```
=== -All
Get-Content : Cannot find path '-All' because it does not exist.
    [SKIP] type = （只校验 crafting_shaped）
定形配方通过 = 0    跳过(非定形) = 1    失败项合计 = 0
结论: 全部通过
```

原因在闸门脚本自己身上：`& $sb @('-All')` —— **PowerShell 只有在命令文本里写出 `-All` 才会按名字绑到 `[switch]`**；
用数组 splat 传进去的只是一个**字符串参数**，于是它落到第一个位置参数（`$Files`）上，
RecipeCheck 拿 `-All` 当文件名去读、报一句"路径不存在"，然后**一个配方都没检查**，照样打印"全部通过"。

三件事记下来：

1. **这和 §4.32 那条 JsonCheck 的坑是同一族**："退出码 0" ≠ "检查过了"。
   每道门的输出里都必须能看见**它到底查了几个** —— RecipeCheck 现在会打印 `定形配方通过 = 27`，
   JsonCheck 必须带目录才会打印 `检查 334 个 JSON 文件`；看不见计数的"通过"一律当没跑；
2. **修法**：给 scriptblock 传命名参数用**哈希表 splat**（`& $sb @{ All = $true }`）或把 `-All` 直接写进命令文本。
   闸门脚本已经改成前者（`Run-Ps1` 的第三个参数从 `[string[]]` 改成 `[hashtable]`）；
3. **影响范围要如实说**：ZF62~ZF65 那几轮闸门日志里的 RecipeCheck 都是**空跑**
   （`定形配方通过 = 0`），也就是"配方结构"这一类检查近 5 轮没真正执行。修好后补跑全量：
   **27 条定形配方全过、失败 0** —— 结论没变，但"没变"必须是**查过之后**的结论，不是空跑出来的副产品。
'''

J_ANCHOR = u'''再把各模型的 `layer0` 指过去（锂矿那两张就是这么做的）。'''

J_INSERT = J_ANCHOR + u'''

**工具（剑 / 镐 / 斧…）比普通物品多三处联动（0.10 ZF66 实例：钛合金剑 / 钛合金镐）**：

| # | 位置 | 要点 |
|---|---|---|
| 6 | `ModTiers.java`（新建） | 原版的 `Tier` 把**耐久、挖掘等级、速度、伤害加成、附魔权重、修理材料**全写在档里 —— 两把工具数值不同就得**各给一个档位**。数值换算照原版公式反推：剑显示伤害 = 1 + (3 + 档位伤害)，镐 = 1 + (1 + 档位伤害)；"挖掘等级 = 下界合金"就是 `BlockTags.INCORRECT_FOR_NETHERITE_TOOL`（1.21 起等级就是这张标签） |
| 7 | `ModItems.java` | `new SwordItem(tier, new Item.Properties().attributes(SwordItem.createAttributes(tier, 3, -2.4F)))` / `new PickaxeItem(... PickaxeItem.createAttributes(tier, 1.0F, -2.8F))` —— **照抄原版那一行的写法**，只换档位 |
| 8 | `models/item/<id>.json` | 工具的 parent 是 **`minecraft:item/handheld`**（不是 `item/generated`）—— 否则拿在手里是"平铺"的 |
| 9 | 配方 | 形状照原版：剑 `["X","X","S"]`、镐 `["XXX"," S "," S "]`；列数规则见 §6.13 |

> **"工具不要 Shift 详细说明"怎么实现**：什么都不做就行（那行提示是**每个物品自己**在
> `appendHoverText` 里加的，不是全局行为）。验证方式是"物品类必须**恰好**是原版 `SwordItem` / `PickaxeItem`"
> —— 一旦有人给它套匿名子类写说明，这条断言立刻挂。'''


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF65 |") and not added:
            out.append(ROW)
            added = True
    if not added:
        problems.append(u"没找到 ZF65 行")
    text = u"\n".join(out)

    for name, old, new in ((u"§9 ZF65 复验条", OLD9, NEW9),
                           (u"§6.8 尾", J_ANCHOR, J_INSERT),
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
    print(u"§5 ZF66 行 + §9 三条 + §4.38 + §6.8 工具清单 已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
