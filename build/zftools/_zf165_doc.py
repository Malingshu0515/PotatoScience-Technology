#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ZF165 文档记账：往 docs/开发档案.md 插入
   ① §5 的 ZF165 行  ② §4.173 + §4.174 两条雷  ③ §9 的 ZF165 待实测段。

只读别的文件、只写开发档案.md 一份；写前把原文件另存一份到 build/tmp/zf165/ 留底。
⚠ 这里用的是**按行锚点**而不是字面块替换：档案是 10667 行的大文件，
   ZF159 那轮的教训就是「old_string 只写了标题行，结果把整节顶掉」——
   按行插入不存在那个风险（我只在锚点行**后面**加行，一个字都不删）。
"""

import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARCHIVE = r"E:\PotatoST\docs\开发档案.md"
BACKUP = r"E:\PotatoST\build\tmp\zf165\开发档案.md.before-zf165"

ROW_ZF164_MARK = "| ZF164 |"
ROW_ZF166_MARK = "| ZF166 |"

ROW_ZF165 = (
    "| ZF165 | **新建 `zf165_pre`**（**1073 份**：整个 `src` / `docs` / `build.gradle` / "
    "`gradle.properties` / `release` + `_manifest.txt`（git status 留底）；逐份抄完核过文件数。"
    "⚠ 开工前查过轮号：ZF166 已被另一条线占用（`FluidConverter*` / `_zf166_*`）⇒ 本轮用 **ZF165**；"
    "救援目录里没有 `zf165_pre`（§4.147）） "
    "| **0.13：Curios 饰品栏联动 —— 星璨钢头盔进头饰槽、Mek 喷气背包进背饰槽**（用户原话见 §9）。"
    "① **用户原话**：「做个小联动 检测到Curios API后 ①星璨钢头盔可以放在头饰槽位 只+2护甲值 "
    "一直给予夜视3 13s效果 ②如果还有mek 那么mek的喷气背包可以装在背饰上 起到喷气背包正常效果"
    "（正常起飞 消耗氢气）」。"
    "② **一个文件吃下全部 Curios 调用**：新建 `CuriosBridge.java`（**全工程唯一** import "
    "`top.theillusivec4.curios.*` 的文件，公开签名里一个 Curios 类型都没有，照 `MekChemicalBridge` "
    "那条已过验的先例）；编译期用 `libs/curios-neoforge-9.5.1+1.21.1.jar` + `compileOnly`（不进产物）。"
    "③ **「+2 护甲」是白拿的**：反编译取证 `CurioStacksHandler#activateSlot` —— Curios **只**把 "
    "`ICurio#getAttributeModifiers` 返回的东西加到玩家身上，物品自己那份 `ItemAttributeModifiers`"
    "（也就是头盔本体的 5.5）在饰品槽里**根本不参与结算** ⇒ 我们回报 +2 就是 +2，"
    "而戴在原版头盔槽上仍是 5.5 / +0.5 韧性、**一个字没改**。修饰符 id 是 `static final` 常量"
    "（`AttributeInstance#removeModifier` 按值相等匹配 ⇒ 每次换 id 会『摘不下来』、护甲一路涨）。"
    "④ **「能放进哪个槽」是纯数据，零代码**：Curios 槽位定义里的 `curios:tag` 判据 = "
    "「物品在 `curios:<槽位名>` 标签里」⇒ 我们自己的 "
    "`data/curios/tags/item/head.json`（头盔）与 `.../back.json`（喷气背包）。"
    "⚠ 这两个文件**不是**『往别人的文件里加一行』：原版 `TagLoader` 对同名标签是**合并**"
    "（`replace` 缺省 false）—— 探针实测合并后 `#curios:head = [create:goggles, "
    "potato_s_t:star_steel_helmet]`。"
    "⑤ **夜视没有第二份实现**：`ModArmorMaterials#hasStarSteelHelmet` 改成"
    "「原版头盔槽 **||** `CuriosBridge.hasEquipped`」，于是那条已经过很多轮实机验证的 "
    "`ModArmorSet` 续期逻辑（13 s / 余量 220 / 不闪）**原样生效**；`CuriosBridge` 里"
    "只留三个同值常量，由 `_zf165_gate.py` A1 钉住与 `ModArmorSet` 逐字相等。"
    "⑥ **喷气背包：我们一行飞行逻辑都不写** —— 反编译取证 `IJetpackItem#getJetpack`："
    "先看胸甲槽、再看 `CuriosIntegration.findFirstCurio`（**任意** Curios 槽），"
    "所以只要它进得去背饰槽，起飞/悬停/矢量三模式、氢气消耗（`useJetpackFuel` → "
    "`useChemical(stack, 1)`）、Mek 自己注册的 Curios 渲染器全都照旧；"
    "`canUseJetpack` = `hasChemical(stack)` ⇒ 没灌氢飞不起来。我们只做两件事："
    "给它挂 `curios:item` 能力 + 把它写进 `#curios:back`。"
    "⑦ ⚠⚠ **本轮最大的一个坑（少了它整个功能静默不生效）**：Curios 的槽位类型光有定义"
    "**不会**出现在玩家身上，还必须有『把槽位分给实体』的文件 "
    "`data/<命名空间>/curios/entities/*.json` —— Curios 自己的 jar 里**一个都没有**，"
    "整合包里只有 Create 写了、而且只给了 `head`。⇒ 我们自己写 "
    "`data/potato_s_t/curios/entities/players.json`（`head` + `back`，不带 replace ⇒ 与 Create 合并）。"
    "探针第一版就是这么红的：标签对、能力对、`isStackValid` 也 true，"
    "但 `getEntitySlots(PLAYER)` 里根本没有 `back`。立 **§4.173**。"
    "⑧ ⚠ **`neoforge:conditions` 在标签文件里是静默无效的**（`TagFile.CODEC` 只认 "
    "values/replace/remove，`TagLoader` 不走 `ConditionalOps`）⇒ 给喷气背包加 Mek 守卫改用"
    "元素级 `{\"id\": \"mekanism:jetpack\", \"required\": false}`；"
    "**必需项缺失会让整个标签被丢掉**（`TagLoader.build` 报 ERROR 后根本不注册）。立 **§4.174**。"
    "⑨ **真服务端探针 `Zf165Check` 36/2 → 修完 38/0**（Curios 9.5.1 + Mek 10.7.19 拷进 "
    "`run/server/mods` 跑、跑完删掉）：两个标签的存在与内容、两个物品的 `curios:item` 能力、"
    "泥土/石头/下界合金头盔三条负对照、真 `ServerPlayer` 里护甲正好 +2、戴上跑一遍**真** "
    "`ModArmorSet.onPlayerTick` 拿到夜视 III / 260 tick、反复穿脱 3 轮护甲不漂、摘下回到初值、"
    "原版头盔槽那条老路仍然生效、喷气背包能进背饰槽且 Mek 自己的 `findFirstCurio` / "
    "`getActiveJetpack` 都认它、没灌氢时 `canUseJetpack` 为假。"
    "⑩ 常驻门 `_zf165_gate.py` **43 项 0 失败**（5 组：Java 侧 / 数据侧 / 负面对照 / mods.toml / "
    "产物 jar）；**语言键数一个没动**（五份 lang 一个字节没改，说明文字复用 Curios 自己的 "
    "`curios.tooltip.slot` + `curios.modifiers.head` 两条词条，不新增键）。"
    "⑪ **`curios` 写进 `neoforge.mods.toml` 成硬依赖**（与 patchouli 同一条先例）："
    "`ICurioItem` 是**接口**，只要物品类 implements 它，任何模组的 "
    "`instanceof ICurioItem` 都会触发 JVM 解析 ⇒ 没装 Curios 的实例会当场崩；"
    "做成可选必须把实现类与注册类拆开、全程 `ModList` 挡，成本远大于收益。"
    "理由与代价都写进了 toml 的注释里。"
    "⑫ ⚠ **本轮没重打成品**（`release\\PotatoST-0.13.jar` 里还没有这一轮）—— 下次打包必须带上，"
    "§4.159 三处联动照旧。 | 见 §9 ｜ 见 §4.173 / §4.174 |"
)

L173 = """### 4.173 【兼容雷】Curios 的槽位"定义好了"≠"玩家身上有" —— 少了实体分配文件，一切看起来都对、功能就是不生效（0.13 ZF165）

**症状**：`#curios:head` 标签对、`curios:item` 能力对、`CuriosApi.isStackValid(...)` 也返回 true，
但**玩家的饰品栏里根本没有那个格子**，放不进去任何东西 —— 而且**不报任何错**。

**根因**（反编译取证）：Curios 有三层数据，缺一层就静默失效：

| 层 | 文件 | Curios 自己的 jar 里有吗 | 少了会怎样 |
|---|---|---|---|
| ① 槽位类型 | `data/<任意命名空间>/curios/slots/<id>.json` | **有**（10 个：head/back/belt/body/charm/curio/hands/necklace/ring/bracelet） | 槽位不存在，`getSlot(id)` 为空 |
| ② 槽位 ↔ 物品 | `data/<命名空间>/tags/item/<id>.json`（`#curios:<id>`） | **一个都没有** | 物品放不进那个槽 |
| ③ 槽位 ↔ 实体 | `data/<命名空间>/curios/entities/*.json` | **一个都没有** | **玩家身上没有格子**（`getEntitySlots(PLAYER)` 为空 ⇒ `CuriosApi.getCuriosInventory` 直接返回 `null`） |

第 ③ 层是最容易漏的：`CuriosEntityManager` 只会去读数据包里的
`curios/entities/*.json`，`{"entities": ["minecraft:player"], "slots": ["head", "back"]}`，
`replace` 缺省 false ⇒ **与别的数据包合并**（本题里 Create 也写了一份，只给了 `head`）。
Curios 官方文档也明说 slot types "will not appear in-game until they are added to one or more entities"。

**本轮怎么抓到的**：探针第一版在真服务端上红了 C5/D6 两项 ——
`#curios:head` 有、`isStackValid` 也 true，但 `getStacksHandler("back")` 是空、
放进头饰槽后护甲没变。把 `CuriosApi.getSlots(false)` 与 `getEntitySlots(PLAYER, false)`
两张表打出来才看清：**槽位表 10 个，实体表只有 Create 给的 `head` 一个**。

**规矩**：以后接任何"数据驱动槽位/栏位"的模组，**先打两张表**——
"系统知道的类型"与"这个实体真的有的类型"，别只打一张就当接通了。

**⚠ 同一条雷的第二个面（探针侧）**：Curios 的 `CurioStacksHandler` 是**懒建**的
（`CurioInventory#init` 按 `getEntitySlots` 铺，只在 `CurioInventoryCapability#reset()` 里被调，
正常游戏里那次 reset 发生在玩家数据反序列化时）。凭空 `new ServerPlayer(...)` 没有存档数据
⇒ `asMap()` 一直是空的。**先 `getCuriosInventory(player).get().getCurios()` 把槽位铺出来**，
再 `getStacksHandler(id)`；属性修饰符那条路还要手动跑一次 `ICurioStacksHandler#update()`
（正常游戏里那一步由 `CuriosEventHandler#tick` 每 tick 做，`update()` 比较
`activeStates`/`previousActiveStates`，变了才走 `activateSlot` ——
**属性修饰符正是在那里加到玩家身上的**）。
"""

L174 = """### 4.174 【数据雷】`neoforge:conditions` 在**标签文件**里是静默无效的；而必需项缺失会让**整个标签**被丢掉（0.13 ZF165）

**两个事实，都是本轮从 NeoForge 21.1.235 / 原版 1.21.1 源码核出来的**：

1. **标签文件不吃 `neoforge:conditions`**。`TagFile.CODEC` 只认 `values` / `replace` / `remove`
   三个字段，`TagLoader` 也**没有**被包进 `ConditionalOps`（把 NeoForge 里所有
   `ConditionalOps` 的使用点列一遍，标签这条路不在其中）⇒ 写进去的条件被 DFU
   当未知字段**直接丢弃**，**不报错、也不生效**。本轮第一版就给
   `data/curios/tags/item/back.json` 写了 `neoforge:conditions: [mod_loaded mekanism]`，
   纯属自我安慰。
2. **没法用 required 的条目会连累整张标签**。`TagLoader#build` 把没解析出来的条目收集起来，
   `list` 非空时走 `Either.left` ⇒ 只打一行 `Couldn't load tag ... as it is missing
   following references` 的 ERROR，然后**根本不注册这个标签**。
   `required` 缺省是 **true** ⇒ 只写 `"mekanism:jetpack"` 而 Mek 没装的话，
   整个 `#curios:back` 标签都不存在。

**正确写法**（本轮采用的）：

```json
{
  "values": [
    { "id": "mekanism:jetpack", "required": false }
  ]
}
```

**顺带记住**：同一个标签 id 的文件会被**所有数据包合并**（`replace` 缺省 false 就是追加），
所以"给别的模组的标签加东西"根本不需要运行期注入 —— 前提是你知道对端**用不用这个标签**
（Curios 的槽位判据恰好就是 `curios:tag`，所以这条在本题里成立；换一个"把名单写死在代码里"
的对端就未必了 —— 那正是 §4.166 的教训）。
"""

SEC9 = """### ZF165（0.13）Curios 饰品栏联动：头盔进头饰槽 / Mek 喷气背包进背饰槽 —— **待你实测**

**要你做的**（都在游戏里，几秒就能看出对不对）：

1. 打开**饰品栏**（默认按 `E` 旁边的饰品按钮，或键位里那个"打开/关闭饰品栏"）：
   应当能看到 **"首饰"** 与 **"背饰"** 两个格子（这是我们这轮新给玩家开的；
   之前整合包里只有 Create 给的"首饰"一个）。
2. **星璨钢头盔**放进**"首饰"**格：
   - 属性栏 / 物品提示里应当出现 **"佩戴首饰时：+2 护甲"**（**不是** 5.5）；
   - 视野**一直**是夜视 III（不闪、不过期），摘下后最多再亮 13 秒；
   - 同时它**仍然可以正常戴在头盔槽**上（那条老路一个字没改：5.5 护甲 / +0.5 韧性）。
3. **通用机械的喷气背包**（先用我们的**灌装机**灌氢，或者直接用 Mek 的充能台）放进**"背饰"**格：
   - 正常起飞（默认 NORMAL 模式：按跳跃键上升）、正常耗氢；
   - 背上**看得见**喷气背包模型（Mek 自己往 Curios 注册的渲染器）。
4. 反面对照（确认没有连带）：没灌氢的喷气背包飞不起来；头盔塞不进背饰槽。

**我这边已知的两处"和戴在胸甲槽时不一样"**（都写清楚了，不是 bug）：

| 项 | 戴在**胸甲槽** | 放进**背饰槽** |
|---|---|---|
| 护甲值 | 有（护甲物品本身那份属性） | **0** —— Curios 只认 `ICurio#getAttributeModifiers`，物品自己那份不参与（反编译取证） |
| HUD | 右上角显示模式与氢气余量 | **不显示** —— Mek 的 `ItemJetpack#addHUDStrings` 有一道 `slotType == getEquipmentSlot()` 的门，且它没实现 `addCurioHUDStrings` |

切换模式（默认键）在饰品槽里**照样能用**。

**数值口径**（要改就改这几处，改完跑 `_zf165_gate.py`）：

- 护甲 **+2**：`CuriosBridge.ARMOR_BONUS`（用户原话「只+2护甲值」）
- 夜视 **III / 13 s**：与头盔槽**共用** `ModArmorSet` 的
  `NIGHT_VISION_III` / `HELMET_NIGHT_VISION_TICKS` / `NIGHT_VISION_MARGIN`
  （`CuriosBridge` 里是三个同值常量，门 A1 钉住相等）

**依赖变化（这一条要知道）**：0.13 起本模组**需要 Curios**（`neoforge.mods.toml` 里是
`required`）。理由写在 `CuriosBridge` 的类注释与 toml 的注释里：`ICurioItem` 是接口，
做成"可选"必须把实现类与注册类拆开、全程 `ModList` 挡，成本远大于收益。
"""


def main():
    src = io.open(ARCHIVE, "r", encoding="utf-8", newline="").read()
    if "\r\n" in src:
        print("!! 档案是 CRLF，本脚本按 LF 处理 —— 先确认再跑")
        return 1
    lines = src.split("\n")

    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    if not os.path.exists(BACKUP):
        io.open(BACKUP, "w", encoding="utf-8", newline="").write(src)
        print("留底 -> " + BACKUP)

    # ---- ① §5 的 ZF165 行（插在 ZF164 行之后）----
    idx164 = [i for i, l in enumerate(lines) if l.startswith(ROW_ZF164_MARK)]
    idx166 = [i for i, l in enumerate(lines) if l.startswith(ROW_ZF166_MARK)]
    if len(idx164) != 1 or len(idx166) != 1:
        print("!! 锚点不唯一：ZF164=%d 处 / ZF166=%d 处" % (len(idx164), len(idx166)))
        return 2
    if any(l.startswith("| ZF165 |") for l in lines):
        print("!! 已经有一行 ZF165 了，拒绝重复插入")
        return 3
    lines.insert(idx164[0] + 1, ROW_ZF165)
    print("① 已插入 §5 的 ZF165 行（在 ZF164 之后）")

    # ---- ② §4.173 / §4.174（插在 §4.166 之后那一组雷区的末尾：挑 4.172 之后）----
    idx172 = [i for i, l in enumerate(lines) if l.startswith("### 4.172 ")]
    if len(idx172) != 1:
        print("!! 锚点 4.172 不唯一：%d 处" % len(idx172))
        return 4
    if any(l.startswith("### 4.173 ") for l in lines):
        print("!! 已经有 §4.173 了，拒绝重复插入")
        return 5
    # 4.172 那一节到下一个 "### " 或 "## " 之前是它的正文，插在它正文结束处
    j = idx172[0] + 1
    while j < len(lines) and not (lines[j].startswith("### ") or lines[j].startswith("## ")):
        j += 1
    block = (L173 + "\n" + L174).split("\n")
    lines[j:j] = [""] + block
    print("② 已插入 §4.173 / §4.174（在 §4.172 之后）")

    # ---- ③ §9 的 ZF165 待实测段（插在 ZF166 那段之后）----
    idx9 = [i for i, l in enumerate(lines) if l.startswith("### ZF166（0.13）")]
    if len(idx9) != 1:
        print("!! §9 锚点 ZF166 不唯一：%d 处" % len(idx9))
        return 6
    if any(l.startswith("### ZF165（0.13）") for l in lines):
        print("!! §9 里已经有 ZF165 了，拒绝重复插入")
        return 7
    j = idx9[0] + 1
    while j < len(lines) and not (lines[j].startswith("### ") or lines[j].startswith("## ")):
        j += 1
    lines[j:j] = [""] + SEC9.split("\n")
    print("③ 已插入 §9 的 ZF165 待实测段")

    out = "\n".join(lines)
    io.open(ARCHIVE, "w", encoding="utf-8", newline="").write(out)
    print("写完：%d 行 -> %d 行（+%d）" % (len(src.split("\n")), len(lines),
                                          len(lines) - len(src.split("\n"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
