# -*- coding: utf-8 -*-
u"""_zf151_docs.py —— ZF151 文档落地（幂等，默认 dry-run）。

  ① 档案 **§4.160**：两条实测口径（标签只管速度 / 探针看不见新加实体）；
  ② 档案 **§5** 加 ZF151 行；
  ③ 档案 **§9** 加 ZF151 小节（**待用户实测**）；
  ④ 交接 **§6** 加第 30 条；
  ⑤ 英文公告末尾加一条（§4.150 日志纪律）。

跑法：python build\\zftools\\_zf151_docs.py [--write]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", "开发档案.md")
HAND = os.path.join(ROOT, "docs", "多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")

notes, fails, plan = [], [], []


def want(text, old, new, label):
    if new in text:
        notes.append(u"  [跳过] %s（已经在，幂等）" % label)
        return text
    if text.count(old) != 1:
        fails.append(u"%s：锚点命中 %d 次（应为 1）" % (label, text.count(old)))
        return text
    notes.append(u"  [改] %s" % label)
    return text.replace(old, new, 1)


D4_TITLE = u"### 4.160 【工具雷】`mineable/pickaxe` 只管**速度**、不管**掉落**；服务端探针也**看不见新加的实体**（0.12 ZF151）"
D4 = u"""### 4.160 【工具雷】`mineable/pickaxe` 只管**速度**、不管**掉落**；服务端探针也**看不见新加的实体**（0.12 ZF151）

用户报的是一句很短的话：「**太阳能板挖掘不掉落**」。查下去是两个各自独立、都很容易记错的口径：

**① 标签 ≠ 掉落。** 太阳能板一直**在** `minecraft:mineable/pickaxe` 里，
但它既没有 `data/potato_s_t/loot_table/blocks/solar_panel.json`，也没覆写 `getDrops`
⇒ 原版**两样都没有 = 掉空**。那张标签决定的是"镐子算不算正确工具（有没有速度加成）"，
**与掉落无关**（反例就在原版：石头既在标签里、又 `requiresCorrectToolForDrops = true`）。

**② `requiresCorrectToolForDrops()` 卡的比想象的狠。**
1.21.1 `ServerPlayerGameMode.destroyBlock` 第 274~278 行（本轮从 sources.jar 抠的原文）：

```java
boolean flag1 = blockstate.canHarvestBlock(this.level, pos, this.player); // = !requiresCorrectToolForDrops || 手上是对的
boolean flag  = removeBlock(pos, blockstate, flag1);
if (flag1 && flag) { block.playerDestroy(...); }     // ← 掉落**只**在这里发生
```

手上没拿对工具 ⇒ `flag1 = false` ⇒ `playerDestroy` **根本不被调用** ⇒ 一个掉落物都没有
（连 `onRemove` 里 `popResource` 那种"自己塞掉落"的写法也与此无关，别混为一谈）。
本轮据此把两个接线口（合金炉 / 柴油机）上的 `requiresCorrectToolForDrops()` 去掉了 ——
它们本来是"空手挖 → 接线块白白消失"。

**③ 服务端探针看不见"新加进世界的实体"。** 想验"挖了到底掉不掉"，第一版探针写成
"放一块 → `playerDestroy` → 数周边 `ItemEntity`"，结果恒为 0，报告里差点写成"挖了不掉"。
分层定位后真相是：**探针没有真玩家**（`players = 0`）⇒ 没有任何"实体刻"区块 ⇒
新 `addFreshEntity` 的实体留在实体管理器的 pending 队列里：
`addFreshEntity` 返回 `true`、`isAlive()` 也是 `true`，但 `getEntitiesOfClass`（2.5 格、
甚至 64 格）与 `getAllEntities()` **一律数不到**（实测那 3 个是世界里原有的实体）。
⇒ 端到端判据只能**逐段跑原版那条链**：`canHarvestBlock`（空手也要 true）
→ `Block.getDrops`（要返回正主）→ `level.addFreshEntity`（`popResource` 的内核）。
**"世界里出现掉落物"这种判据在服务端探针里不成立**，写了就是假红/假绿。
"""

D5_ROW = (u"| ZF151 | **新建 `zf151_pre`**（**91 份**：`SolarPanelBlock.java` / `ModBlocks.java` / "
          u"`PotatoST.java`（探针挂载点）/ `mineable/pickaxe.json` / 三份文档 / 全部常驻门 / "
          u"成品 0.12 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。"
          u"⚠ 开工前查过轮号：`_zf151_*` 没人占、救援目录里没有 `zf151_pre`（§4.147））"
          u" | 0.12：**修「太阳能板挖掘不掉落」+ 统一全机器挖掘口径**（用户原话「然后 太阳能板挖掘不掉落 "
          u"所有机器加个挖掘标签（镐子能加速挖掘 空手挖也掉落机器）」）。① 根因：太阳能板**在** pickaxe 标签里，"
          u"但既无 loot_table 也无 `getDrops` ⇒ 掉空（**标签只管速度**，§4.160）；修法：`SolarPanelBlock` "
          u"补 `getDrops` → `List.of(new ItemStack(this))`，与另外 29 台机器逐字一致。"
          u"② `mineable/pickaxe` 补 3 个漏项（`fluid_exchanger` / `electric_blast_furnace_part` / "
          u"`alloy_smelter_part` ⇒ 54 → 57），**只追加不重排**（`_zf125` 的 D15 `only_inserted` 在盯着）。"
          u"③ 两个接线口去掉 `requiresCorrectToolForDrops()`（空手挖不再白丢接线块）。"
          u"④ 探针 `Zf151Check`（真开服 + 假玩家）**21 项 ALL OK**：33 台机器全部在标签里、"
          u"一个都不需要工具；太阳能板 空手 canHarvestBlock=true → getDrops=1 个 → popResource 成立；"
          u"矿（负对照）仍然要正确工具 | 见 §9 ｜ 见 §4.160 |\n")

D9_ANCHOR = u"### ZF149（0.12）重打成品：把手册装进 `PotatoST-0.12.jar`"
D9 = u"""### ZF151（0.12）挖掘口径：太阳能板掉了 + 全机器「镐子加速、空手也掉」 —— **待你实测**

用户原话：「**然后 太阳能板挖掘不掉落 所有机器加个挖掘标签（镐子能加速挖掘 空手挖也掉落机器）**」。

**根因（一句话）**：太阳能板**在** `minecraft:mineable/pickaxe` 标签里，但**既没有 loot_table、
也没有覆写 `getDrops`** —— 那张标签只管**速度**，掉落是另一条链（§4.160 记了口径）。

**改了什么**
1. `SolarPanelBlock.getDrops` → `List.of(new ItemStack(this))`（与本工程另外 29 台机器逐字一致）；
2. `mineable/pickaxe.json` 补 3 个漏项：`fluid_exchanger`（有物品有掉落，就是漏登记）、
   `electric_blast_furnace_part`、`alloy_smelter_part`（结构件，拆解时也给镐速加成）——**54 → 57**；
3. 两个接线口（`alloy_smelter_port` / `diesel_generator_port`）去掉
   `requiresCorrectToolForDrops()`：源码实证它会让**空手挖掘时 `playerDestroy` 整段被跳过**
   ⇒ 接线块白白消失（掉落的开关闸门，§4.160）。

**口径边界（重要，别误会）**：机器家族（33 台）现在**全部**"镐子加速 + 空手也掉"；
但**建材家族 8 个**（一般/高级/稳定/耐热金属块、加热装置、散热装置、接线块、沥青块）
**刻意保留"必须用镐"**——它们是照原版铁块/煤炭块的口径做的（设计如此，代码注释里写着）。
要改成"空手也掉"的话是 8 行的事，**你说一声我就改**。

**证据**
- 探针 `Zf151Check`（真 `runServer` + 假玩家）：**21 项 ALL OK**，报告 `build\\zftools\\_zf151_probe_utf8.txt`，
  归档件 `build\\zftools\\check\\Zf151Check.java`。关键几项：
  ① 33 台机器 **漏标签 0 个**、**要工具的例外 0 个**；
  ② 太阳能板：空手 `canHarvestBlock = true` → `getDrops = 1xsolar_panel` → `popResource` 成立；
  ③ 负对照：钴矿石空手 `canHarvestBlock = false`（判据有区分度）；
  ④ 原版石头**既**在 pickaxe 标签里**又**要正确工具（把"标签≠掉落"钉成一条断言）。
- 常驻门 `_zf151_verify.py`（静态）：标签覆盖、`getDrops` 源码、接线口已清、建材家族照旧、文档。
- 反证 `_zf151_falsify.py`：逐把刀"改坏必红 / 逐字节还原 / 还原回绿"。

**要你实测的**
1. 挖一块**太阳能板** → 应当掉回一块（空手也行）；
2. 随便挖几台机器（微型粉碎机 / 液压机 / 容器换流器）→ 都应当掉；
3. 顺带：**空手**挖柴油机接线口 → 掉的是**接线块**（以前是白丢）。

""" + D9_ANCHOR

H6_ANCHOR = u"29. **ZF148 的账（帕秋莉教程手册）**"
H6_NEW = u"""30. **ZF151 的账（挖掘口径）**：① 用户原话「然后 太阳能板挖掘不掉落 所有机器加个挖掘标签
    （镐子能加速挖掘 空手挖也掉落机器）」。② 根因：太阳能板**在** pickaxe 标签里，但无 loot_table
    也无 `getDrops` ⇒ 掉空；**标签只管速度**（§4.160）。③ 改动三处：`SolarPanelBlock` 补 `getDrops`；
    `mineable/pickaxe.json` 54 → 57（补 `fluid_exchanger` / `electric_blast_furnace_part` /
    `alloy_smelter_part`，**只追加**）；两个接线口去掉 `requiresCorrectToolForDrops()`。
    ④ ⚠ **建材家族 8 个仍保留"必须用镐"**（照原版铁块/煤炭块），要改一句话的事。
    ⑤ ⚠ **成品要重打**：本轮改了 Java ⇒ `release\\PotatoST-0.12.jar` 又落后于源目录，
    打包时把新哈希同步到 `_zf149_verify.py` 的 `WANT_SHA` + 档案/交接/公告三处（§4.159 的三处联动）。
""" + H6_ANCHOR

ANN_ADD = u"""

## New in 0.12 ZF151 — mining fixes for machines

- **The Solar Panel now drops itself when mined.** It was already in the `mineable/pickaxe` tag —
  but that tag only controls **mining speed**, never drops; the block had neither a loot table nor a
  `getDrops` override, so it dropped nothing at all.
- **Every machine is now uniform: a pickaxe speeds it up, and mining by hand still drops it.**
  Three blocks were missing from the pickaxe tag (`fluid_exchanger`, the blast-furnace shell and the
  alloy-smelter shell), and the two machine ports no longer require a correct tool — mining a diesel
  generator port barehanded used to destroy the wiring block inside it.
- ⚠ Deliberately unchanged: the **decorative metal blocks, heater, heat sink, wiring block and
  asphalt block still need a pickaxe** (they mirror vanilla iron/coal block behaviour).
- ⚠ This build changes Java code, so `release/PotatoST-0.12.jar` has been rebuilt again — use the
  newest jar, and remember **Patchouli `1.21.1-93`+ is required**.
"""


def main(argv):
    write = u"--write" in argv

    doc = io.open(DOC, encoding=u"utf-8", newline=u"").read()
    nums = [int(m.group(1)) for m in re.finditer(u"(?m)^#{3,4} 4\\.([0-9]+)", doc)]
    mx = max(nums)
    already = D4_TITLE in doc
    print(u"档案 §4 最大编号 = %d（目标 §4.160；已写入 = %s）" % (mx, already))
    if not already and mx + 1 != 160:
        fails.append(u"§4 编号不是 160（实测 max=%d）—— 停手先看清" % mx)
    doc2 = want(doc, D9_ANCHOR, D9, u"档案 §9 加 ZF151 小节")
    if D4_TITLE not in doc2:
        j = doc2.find(u"\n| ZF15")
        if j < 0:
            fails.append(u"档案：找不到 §5 的 ZF15x 行，没处插 §4.160")
        else:
            k = doc2.rfind(u"\n", 0, j)
            doc2 = doc2[:k] + u"\n" + D4 + doc2[k:]
            notes.append(u"  [改] 档案 §4.160")
    i = doc2.find(u"| ZF149 |")
    if u"| ZF151 |" in doc2:
        notes.append(u"  [跳过] 档案 §5 的 ZF151 行（已经在，幂等）")
    elif i < 0:
        fails.append(u"档案：找不到 §5 的 ZF149 行")
    else:
        j = doc2.find(u"\n", i)
        doc2 = doc2[:j + 1] + D5_ROW + doc2[j + 1:]
        notes.append(u"  [改] 档案 §5 加 ZF151 行")
    if doc2 != doc:
        plan.append((DOC, doc, doc2))

    hand = io.open(HAND, encoding=u"utf-8", newline=u"").read()
    h2 = want(hand, H6_ANCHOR, H6_NEW, u"交接 §6 加第 30 条")
    if h2 != hand:
        plan.append((HAND, hand, h2))

    ann = io.open(ANN, encoding=u"utf-8", newline=u"").read()
    if u"## New in 0.12 ZF151" in ann:
        notes.append(u"  [跳过] 公告 ZF151 那一条（已经在，幂等）")
    else:
        plan.append((ANN, ann, ann.rstrip(u"\n") + u"\n" + ANN_ADD))
        notes.append(u"  [改] 公告末尾加 ZF151 那一条")

    print(u"\n".join(notes))
    print(u"")
    print(u"计划写盘 %d 份" % len(plan))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    if fails or not write:
        if not write:
            print(u"（没加 --write，只算不写）")
        return 1 if fails else 0
    for p, old, new in plan:
        io.open(p, u"w", encoding=u"utf-8", newline=u"").write(new)
        assert io.open(p, encoding=u"utf-8", newline=u"").read() == new, p
    print(u"已写盘 %d 份" % len(plan))
    return 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
