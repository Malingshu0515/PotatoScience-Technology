# -*- coding: utf-8 -*-
u"""_zf162_docs.py —— ZF162 的文档落笔（§4.169/§4.170 + §5 台账行 + §9 小节 + 交接 + 公告）。

⚠ 成品哈希/体积**从盘上那份 jar 现读**（§4.159 三处联动的前两处在这里）：
  · 档案 §5 的 ZF162 行
  · 交接 §1 的成品行
  · 英文公告的 Download 段 + 新小节
跑法：python build\\zftools\\_zf162_docs.py [--write]
"""
import hashlib
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.13.jar")

S4 = u"""### 4.169 【探针雷】NeoForge **不给假玩家发进度** —— 用 `FakePlayerFactory` 验「装配给进度」永远验不出来（0.13 ZF162）

**症状**：本轮把「砌一座高炉」这条进度从"拿到电力高炉物品"改成"装配成功"（自建触发器
`potato_s_t:ebf_formed`）之后，探针里真搭了 3×3×3、真造了一个
`PlayerInteractEvent.RightClickBlock` 交给 `BlastFurnaceAssembly.onRightClickBlock` ——
结构成型了（B3/B4 绿）、判据挂的确实是我们的触发器（A6 绿），**进度就是不完成**。
连跑四轮、加两次隔离实验才定位：

| 实验 | 结果 |
|---|---|
| 假玩家 + 真事件（走 `onRightClickBlock` 全路） | 成型 ✓ / 进度 ✗ |
| 直接调 `EBF_FORMED.get().trigger(fake)` | 进度 ✗ |
| 手工 `addPlayerListener(...)` 再触发 | 进度 ✗ |
| `fake.getAdvancements().award(adv, "got0")` | **返回 false** ← 决定性证据 |

**根因就一行**：`net.minecraft.server.PlayerAdvancements#award` 开头
`if (this.player instanceof net.neoforged.neoforge.common.util.FakePlayer) return false;`
—— NeoForge 自己的注释原文是 `// Forge: don't grant advancements for fake players`。
而 `CriterionTrigger.Listener#run` 干的就是 `playerAdvancements.award(...)`
⇒ **监听器跑到了、被 `award` 拒了**。所以"直接触发也没反应"这个现象**看着像触发器写错了，其实与触发器无关**
（这也是为什么它值得立一条雷：这种误判会让人去改对的代码）。

**正解**：造一个**不是 `FakePlayer` 的 `ServerPlayer`** —— 匿名子类、只把 `displayClientMessage`
变成空操作（探针不真的发包）、UUID 唯一 ⇒ 它的 `PlayerAdvancements` 绑的是它自己，
走的就是真玩家登录那一刻的同一条路。换上去之后 B5 当场绿。
⚠ 真玩家**不受影响**（登录时数据包装好了，而且不是 FakePlayer），所以这是"探针的坑"，不是产品缺陷。

"""

S5 = u"""### 4.170 【判据雷】"槽位不把关"这种**口径改动**会同时掀翻好几道老门 —— 门要跟着改口径，绝不许放宽（0.13 ZF162）

用户「**所有物品都可以放进去 只不过检测到能被罐装的才可以罐装**」把灌装机的**三道门**
（方块实体 `isItemValid` / 菜单手放 `mayPlace` / Shift 快移 `getMachineSlotFor`）从
"只认 `FluidContainerItem`"改成"**全都放行**，能不能灌改由灌装那一步判"。代码只动了三处，
可盘上四道常驻门当场变红 —— 它们把**旧口径逐字**钉死了：

| 门 | 钉的是什么 | 跟平之后（判据没放宽） |
|---|---|---|
| `_zf73_verify.py` A28 | 菜单里必须有 `stack.getItem() instanceof FluidContainerItem` | 改成"菜单**代码里不再出现** `FluidContainerItem` + 放行一切"（更严：连注释都要绕开） |
| `_zf79_verify.py` | `mayPlace` / `isItemValid` 逐字认接口 | 改成"两处都 `return true`，且**不许**写死高压气罐" |
| `_zf80_verify.py` B 段 | 灌装与诊断的**四道判据串**、`SlotState` 六状态、`stateOf` 六条 `return` | 换成 ZF162 的形状：**自家那一支**四道判据一字不变（tank → slot → space → energy）+ 跨 mod 支路另算；七状态 / 十一条 `return` |
| `_zf80_verify.py` C 段 | 菜单里两处认接口 | 改成"三道门都不把关 + 灌装那一步必须出现 `Capabilities.FluidHandler.ITEM`" |

口径：**换一组同样硬的断言，绝不放宽**。另外本轮语言键 **594 → 593（lzh 596 → 595）**
（删扳手键 + 删电力高炉 tooltip 键 + 加灌装机诊断键），**40 份写死键数的门**由
`_zf162_retarget.py` 跟平：只动数字与那几处口径，历史叙述一个字不碰；改完 76 份门逐份
`ast.parse` 自检 **0 语法错**（`_zf162_syntaxcheck.py`）。

"""

ROW = u"""| ZF162 | **新建 `zf162_pre`**（**1411 份**：11 个 java + 五份 lang + 4 份手册 JSON + 模型 / 贴图 / 配方 / 进度 + 三份文档 + **整个 `build\\zftools\\*.py`**（本轮要跟平的门有 40 份）+ 成品 0.13 + `.sha1` + `build\\libs` 那份；逐份核 sha1 + 回读，失败 0。⚠ 开工前查过轮号：`_zf162_*` 没人占、救援目录里没有 `zf162_pre`（§4.147）） | **0.13：删扳手 + 删电力高炉的物品形态 + 灌装机「什么都能放」**（用户原话见 §9）。① **扳手 `potato_s_t:wrench` 整个删掉**：物品注册 / 模型 / 贴图 / 五语语言键 / **三处「手持扳手 Shift 右键拆解」入口**（电力高炉控制器 / 部件格 / 合金冶炼炉）+ `ElectricBlastFurnaceWrench.java` 整份删；手册那三个拿扳手当图标的条目换成灌装机与手册本体。② **电力高炉的物品形态删掉**：`ELECTRIC_BLAST_FURNACE_ITEM`（BlockItem + tooltip）/ 物品模型与贴图 / 创造页那一行 / 那条 `crafting_shaped` 配方（**生成器表一起删**，§4.93）/ JEI 分类图标换成**原版高炉**；**方块本体与它的方块贴图一个字节没动**（`_zf162_verify.py` B3/B4 钉住）。③ **进度「砌一座高炉」**：老判据（拿到那个物品）随物品失效 ⇒ 新建自建触发器 `potato_s_t:ebf_formed`（`EbfFormedTrigger`，挂 `BuiltInRegistries.TRIGGER_TYPES`），两个装配入口各点一次；探针**真搭结构 + 真造事件 + 真完成进度**（定位过程见 §4.169）。④ **灌装机**：三道门全部放行（什么都能放），"能不能灌"改由 `tryFillSlot` 判 —— 自家 `FluidContainerItem`（气罐只收气体 / 油桶只收液体，**那五个文件逐字节未动**）或**别的 mod 的物品流体能力**（`Capabilities.FluidHandler.ITEM`：拷贝上灌 → `getContainer()` 写回槽位，两道"绝不吞东西 / 绝不吞流体"的闸门）；诊断新增 `UNSUPPORTED`（有东西但灌不了）。⑤ 探针 `Zf162Check`（真开服）**27 项 ALL OK**：注册表事实 11 项 / 装配→进度 5 项 / 灌装机 11 项（含 3 条负对照 + 跨 mod 正路 + Shift 快移）；常驻 `_zf162_verify.py`；反证刀 **10/10**。⑥ 跟平 **40 份门**（键数 + 24 处口径，见 §4.170）。⑦ **重打成品**：`release\\PotatoST-0.13.jar` = **{size} 字节 / sha1 `{sha}`**（§4.159 三处联动：门 / 公告 / 交接一起跟）。 | 见 §9 ｜ 见 §4.169 / §4.170 |
"""

S9 = u"""### ZF162（0.13）删扳手 / 删电力高炉物品形态 / 灌装机「什么都能放」—— **待你实测**

用户原话：「**删除一下 1.扳手 2.物品形式的电力高炉（这两个有bug没必要修了）
然后给罐装机改一下 所有物品都可以放进去 只不过检测到能被罐装的才可以罐装
（例如mek的喷气背包 目前好像不可以放进去罐咱们mod里的氢）（高压气罐只支持气体 油桶只支持液体 这两个不要动）**」

**① 扳手整个删掉了。** 创造页、物品注册、模型、贴图、五份语言文件里的名字、
以及**三处「手持扳手 Shift 右键拆解」**（电力高炉控制器 / 电力高炉部件格 / 合金冶炼炉主控）
全部拿掉，`ElectricBlastFurnaceWrench.java` 整份删除。
**拆解只剩「挖掉方块」这一条路**（那条路本来就在：挖任意一格 = 整体还原 + 掉 GUI 内容物，一格都不会白丢）。
手册里原本拿扳手当图标的三个条目，换成「灌装机」与「手册本体」。

**② 电力高炉的"物品形态"删掉了。** 也就是说：**创造页里不再有「电力高炉」这个物品**，
那条合成配方也一起删了。**方块本身没动** —— 电力高炉照旧是**围着原版高炉搭 3×3×3、空手 Shift 右键点成型**
（这条主路一直存在，也是官方推荐的那条）。
连带换了两处：JEI 里电力高炉分类的图标 → **原版高炉**；进度「砌一座高炉」的图标 → 原版高炉。
⚠ 老存档里如果还有"从物品摆出来的裸控制器"，它**仍能成型**，但挖掉时不再返还那个（已经不存在的）物品。

**③ 灌装机：什么都能放，只有"能被罐装"的才灌。**
- **槽位不再把关**：手放、Shift 快移、机器内部三道门全放行 —— 你点名的 Mek 喷气背包**现在能放进去了**。
- **灌装只认能力**：① 我们自己的容器（高压气罐 / 油桶，规矩**一个字没改**）；② **别的 mod 的液体容器**
  （NeoForge 的"物品流体能力"）：在拷贝上灌、再把结果写回槽位，且有两道保险
  （结果空栈、或结果与灌之前逐字节相同 ⇒ 这一次**不灌也不扣罐**，绝不凭空吞东西/吞流体）。
- **灌不了的东西会说清楚**：诊断多了一种状态「**这个东西灌不了**」（不是流体容器），
  而不是像以前那样"什么都没发生"。
- ⚠ **原版空桶**：NeoForge 只给"装着的桶"挂能力，**空桶是普通物品、没有能力** ⇒ 现在这台机器灌不了原版空桶
  （我们的油桶/气罐不受影响）。这条我没动，等你说要不要单独特判。

**④ Mek 喷气背包那件事，我查清了：它装的是 Mekanism 自己的"气体"，不是我们的"流体"。**
Mek 的喷气背包用的是 `mekanism:gas_handler`（另一种能力），我们的氢是**流体**
（`potato_s_t:hydrogen`）—— 两条系统。灌装机现在认的是"物品流体能力"，
所以喷气背包会**如实**被判成"灌不了"（能放进去、但诊断说灌不了）。
要真把我们的氢灌进它，只有一条路：**挂 Mekanism 的 API 软依赖**，在"我们的氢（流体）"与
"`mekanism:hydrogen`（气体）"之间搭个桥。ZF159 那轮已经实测过 Mek 自己的**旋转冷凝器能吃我们的氢**
（`RotaryRecipe#test(我们的氧气)` = true、`getChemicalOutput` = `1 mekanism:oxygen`），
所以这条桥是通的 —— 但那要加编译期依赖 + 运行时存在才加载，**属于要不要做的决定，我不擅自加**。
**要做的话你说一句，下轮我加。**

**⑤ 要你实测的三条**
1. 创造页里搜不到「扳手」和「电力高炉」这两个物品了；**围着原版高炉搭壳 + 空手 Shift 右键仍能装配**，
   而且装配成功会跳「砌一座高炉」这条进度（图标是原版高炉）。
2. 往灌装机槽里塞**随便什么东西**（钻石、别的 mod 的容器都行）：槽位都收；
   能灌的会开始灌，灌不了的按 **Shift + 空手右键**看逐槽诊断，它会说「这个东西灌不了」。
3. 气罐/油桶的老规矩没变：**气罐只收气体、油桶只收液体**（罐里放错种类会被拒收，诊断说"不收这种流体"）。

"""

HAND35 = u"""35. **ZF162 的账（0.13：删扳手 + 删电力高炉物品形态 + 灌装机「什么都能放」）**：
    ① 用户原话与逐条落实见档案 §9；两条工具雷见 **§4.169**（NeoForge **不给假玩家发进度** ——
    `PlayerAdvancements.award` 第 170 行 `if (this.player instanceof FakePlayer) return false;`，
    所以验"装配给进度"必须造一个**不是 FakePlayer 的 `ServerPlayer`**）与 **§4.170**（"槽位不把关"
    这种口径改动会同时掀翻四道老门，门要跟着改口径、不许放宽）。
    ② **活体数字**：语言键 **594 → 593**（lzh **596 → 595**；删 `item.potato_s_t.wrench` +
    `tooltip.potato_s_t.electric_blast_furnace`，加 `gui.potato_s_t.filling.diag.unsupported`）；
    配方 **94 → 93**（电力高炉那条 `crafting_shaped` 删了）；`#c:plates/*` 原料 **29 处/21 份 → 28 处/20 份**。
    ③ **跟平 40 份门**（`_zf162_retarget.py`，24 处语义 + 键数），改完 76 份门 `ast.parse` 全过
    （`_zf162_syntaxcheck.py`）；全门快照对照见 `_zf162_gatediff.py`。
    ④ 探针 `Zf162Check` **27/0**：A 段读**服务端真注册表**（扳手/电力高炉物品 = air、方块仍在、
    配方已消失、进度仍解析且挂自建触发器）、B 段**真搭结构 + 真造 `RightClickBlock` 事件 + 真完成进度**、
    C 段灌装机（三道门放行 / 自家气罐 / **探针当场注册的"别的 mod 的流体容器"** / 三条负对照）。
    ⑤ ⚠ **气罐与油桶那五个文件逐字节未动**（`_zf162_verify.py` C13 钉住）—— 用户点名"这两个不要动"。
    ⑥ ⚠ **没做的、留给你的决定**：Mek 喷气背包走的是 Mek 自己的**气体**系统，要灌我们的氢得**挂 Mek API 软依赖**
    搭"流体↔气体"的桥（ZF159 已证明 Mek 的旋转冷凝器吃我们的氢）；本轮**没有**擅自加依赖。
    原版**空桶**同样灌不了（NeoForge 只给"装着的桶"挂物品流体能力，空桶是普通物品）。
"""


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def main(argv):
    write = u"--write" in argv
    if not os.path.isfile(JAR):
        print(u"!! 成品不在：%s（先打包）" % JAR)
        return 1
    size, h = os.path.getsize(JAR), sha(JAR)
    print(u"成品：%s = %d 字节 / sha1 %s" % (os.path.basename(JAR), size, h))
    fails = []

    doc = read(DOC)
    if u"### 4.169 " not in doc:
        anchor = u"| ZF147 |"
        if doc.count(anchor) < 1:
            fails.append(u"档案：找不到 §5 表头锚点")
        else:
            doc = doc.replace(anchor, S4 + S5 + anchor, 1)
    if u"| ZF162 |" not in doc:
        a2 = u"| 见 §9 ｜ 见 §4.168 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案：ZF160 行尾锚点出现 %d 次" % doc.count(a2))
        else:
            doc = doc.replace(a2, a2 + ROW.format(size=u"{:,}".format(size), sha=h) + u"\n", 1)
    if u"### ZF162（0.13）" not in doc:
        a3 = u"\n---\n\n## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案：§10 锚点出现 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, u"\n" + S9 + u"---\n\n## 10. 备份策略", 1)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"35. **ZF162 的账" not in hand:
        a4 = u"\n---\n\n## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接：§7 锚点出现 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, u"\n" + HAND35 + u"\n---\n\n## 7. ZF146 这一轮的交接", 1)
    # 交接 §1 的活体数字
    hand = hand.replace(u"**594 键 × 4**", u"**593 键 × 4**")
    hand = hand.replace(
        u"→ **594**（ZF155 通用升级模板：物品名 / 升级 / 适用于 / 原料 / 底物槽 / 材料槽 / 规则 = **+7**）。",
        u"→ **594**（ZF155 通用升级模板 = **+7**）→ **593**（ZF162：删扳手键 + 删电力高炉 tooltip 键"
        u" − 加灌装机诊断键 = −2 + 1；lzh 596 → **595**）。")
    hand = hand.replace(u"`data\\potato_s_t\\recipe\\` **91 份**",
                        u"`data\\potato_s_t\\recipe\\` **93 份**（ZF162 实测）")
    # 交接 §1 成品行：旧哈希/体积 → 新的（§4.159 第二处）
    hand = hand.replace(u"`b3688162332a3e5e8a65000d40b09e53f0e578e1`（5,886,943 B",
                        u"`%s`（%s B" % (h, u"{:,}".format(size)))
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    # 常驻门 `_zf149_verify.py` 的两个靶子（§4.159 第一处）
    v149p = os.path.join(ROOT, "build", "zftools", u"_zf149_verify.py")
    v149 = read(v149p)
    import re as _re
    v149n = _re.sub(u'WANT_SHA = u"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    v149n = _re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, v149n, count=1)
    if v149n == v149:
        fails.append(u"_zf149_verify.py：WANT_SHA/WANT_SIZE 没换成（正则没命中）")
    elif write and not fails:
        io.open(v149p, "w", encoding="utf-8", newline=u"").write(v149n)

    ann = read(ANN)
    if u"## New in 0.13 ZF162" not in ann:
        a5 = u"## New in 0.13 ZF159 - Fluids and dusts now interoperate"
        if ann.count(a5) != 1:
            fails.append(u"公告：ZF159 小节锚点出现 %d 次" % ann.count(a5))
        else:
            block = DOC_BLOCK.format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = ann.replace(u"5,886,943 bytes, sha1 `b3688162332a3e5e8a65000d40b09e53f0e578e1`",
                      u"%s bytes, sha1 `%s`" % (u"{:,}".format(size), h))
    ann = ann.replace(u"**5,886,943 bytes**, sha1 **`b3688162332a3e5e8a65000d40b09e53f0e578e1`**",
                      u"**%s bytes**, sha1 **`%s`**" % (u"{:,}".format(size), h))
    if u"**365 classes, 43 advancements, 94 recipes**" in ann:
        ann = ann.replace(u"**365 classes, 43 advancements, 94 recipes**",
                          u"**{cls} classes, 43 advancements, 93 recipes**".format(cls=CLASSES))
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    print(u"模式：%s" % (u"落盘" if write else u"干跑（不写）"))
    print(u"失败 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


CLASSES = u"364"

DOC_BLOCK = u"""## New in 0.13 ZF162 - Wrench and blast-furnace item removed, filling machine accepts anything

- **The wrench is gone.** The item, its model and texture, and its name in all five languages have been
  removed, together with the three "hold a wrench and sneak-right-click to take it apart" entry points
  (electric blast furnace controller, its casing blocks, and the alloy smelter controller).
  **Taking a machine apart now means breaking a block** - which always did a full teardown and gave
  every block and every GUI item back.
- **The electric blast furnace no longer has an item form.** There is nothing to craft and nothing in
  the creative tab; the recipe is gone too. The **block** is untouched: you still build the 3x3x3
  around a vanilla blast furnace and sneak-right-click it with an empty hand. The "Build a blast
  furnace" advancement now completes when you **assemble** it (its icon is a vanilla blast furnace),
  and JEI's category icon for the machine follows.
- **The Filling Machine now accepts any item in its slots** (hand, shift-click, hoppers) - and only
  actually fills containers it can recognise:
  - our own **High-Pressure Gas Tank** (gases only) and **Oil Bucket** (liquids only) - both behave
    exactly as before, by request;
  - **other mods' fluid containers** through NeoForge's item fluid capability: filled on a copy and
    written back, with two safety gates so an item can never be voided and fluid can never vanish.
  - Anything that cannot be filled says so: the sneak-right-click diagnosis reports
    "this item cannot be filled".
- **About Mekanism's jetpack** (the example you gave): it stores Mekanism's own **gas**, which is a
  different capability from the **fluid** our machine handles, so the machine reports it as
  "cannot be filled" - but it **can be put in the slot now**. Filling it with our hydrogen would need
  a soft dependency on Mekanism's API to bridge our hydrogen fluid to `mekanism:hydrogen`; that is a
  decision for you, so it was **not** added this round.
- **Download:** `release/PotatoST-0.13.jar` - **{size} bytes**, sha1 **`{sha}`**.

"""


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
