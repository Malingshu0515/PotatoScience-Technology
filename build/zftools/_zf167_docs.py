# -*- coding: utf-8 -*-
u"""_zf167_docs.py —— ZF167 的四份文档 + 成品数字（**幂等**，锚点唯一才动手）

  ① 开发档案：台账行（追加在最后一行 ZF153 之后）+ §9 整节（追加到文件末尾）+ §4 两条课条
  ② 多会话协作交接：§9 这一轮的交接（追加到末尾）
  ③ 贴图清单：ZF167 那节（两张占位贴图 + 两个待画物品）
  ④ 英文公告：ZF167 那一条 + 成品 Download 段（新 sha1 + 作废的旧 sha1 + 389/98）

成品（本轮重打，0.13）：`release\\PotatoST-0.13.jar` = 6,002,511 字节，
sha1 `51e1c7c6cb380113ab3f7b3334f8ee9b50bf85d3`（⚠ **作废** `5d82faeaeae7a2651650f791e96b943adbdf85fa`）。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
ARCH = os.path.join(ROOT, r"docs\开发档案.md")
HAND = os.path.join(ROOT, r"docs\多会话协作交接.md")
TEXL = os.path.join(ROOT, r"docs\贴图清单.md")
ANN = os.path.join(ROOT, r"docs\UpdateAnnouncement_EN.md")
NEW_SHA = u"51e1c7c6cb380113ab3f7b3334f8ee9b50bf85d3"
OLD_SHA = u"5d82faeaeae7a2651650f791e96b943adbdf85fa"
NEW_SIZE = u"6,002,511"

LEDGER = u"""| ZF167 | **新建 `zf167_pre`**（**269 份**改前件：`ModItems.java` / `ModBlocks.java` / `ModMenus.java` / `PotatoST.java`（探针挂载点）/ `PotatoSTClient.java` / `MachineRecipes.java` / `PotatoSTJeiPlugin.java` / 五份 lang / 九道门本体 / **全部常驻门**（`_zf*_verify.py` + `_zf*_falsify*.py` + `_zf*_gates.py` + `_rzh_*.py`）/ 三份文档 / 旧成品；逐份核 sha1 + **回读**，269/269 逐字节相同，失败 0。⚠ 开工前查过轮号：`_zf167_*` 无人占、救援目录里没有 `zf167_pre`（§4.147）；⚠ 开工时另一条线的探针还挂在 `PotatoST.java` 上，等它撤了才动） | **0.13：空铝罐 + 可乐 + 饮料罐装机**（用户原话「先加个空铝罐配方；【】【铝粒】【】，【】【铝板】【】，【】【】【】合成2个空铝罐 熔炉/高炉烧制一个空铝罐产出5个铝粒；再加一个饮料罐装机（配方；【】【铁锭】【】，【拉杆】【银版】【铁活版门】，【轻质压力板】【高压气罐】【流体管道】）一个碳酸储罐（100MB）一个水储罐（1000mb）一个乙醇储罐（100mb 目前本mod没有乙醇 做个兼容别的mod的乙醇）三个输入槽 一个输出槽 耗电600fe/t 先做一个配方试试水 1.10mb碳酸+500mb水+2糖+1可可豆+1空铝罐 5s产出1罐可乐 可乐是食物 但是食用音效用蜂蜜瓶的 食用后给予120s的急迫 3s的生命恢复1 恢复3点饥饿值 9点饱和度 （食用后返还一个空铝罐）」）。① **两张图纸逐格照抄**（空铝罐：铝粒在上、铝板在中 → 2 个；机器：铁锭 / 拉杆-银板-铁活板门 / 轻质压力板-高压气罐-流体管道）；⚠ **「轻质压力板」取的是原版 `light_weighted_pressure_plate`** —— 本 mod 没有任何压力板（`ModBlocks` 全扫过），已挂 §9 待确认；② **熔炉/高炉**：1 空铝罐 → 5 铝粒（200 / 100 tick）；③ **机器**：三只**只进不出**的罐（碳酸 **100** / 水 **1000** / 乙醇 **100** mB）+ 三个输入槽（糖 / 可可豆 / 空铝罐）+ 一个输出槽 + **600 FE/t**、储能 **12,000 FE**（我定的：20 tick 的钱）、一条配方 **10 碳酸 + 500 水 + 2 糖 + 1 可可豆 + 1 空铝罐 = 1 可乐 / 100 tick = 60,000 FE**；④ **乙醇兼容**：不在 mod 里造乙醇，那只罐收 **`c:ethanol`** 流体标签 —— 名字是**从盘上那份沉浸工程 jar 里抠的**（`data/c/tags/fluid/ethanol.json` → `immersiveengineering:ethanol`），本仓库另附一份空标签（`replace:false`）好在没装 IE 时也存在；⑤ **可乐**：食物（营养 3、饱和度修饰 1.5 ⇒ **9 点**）、食用音效 = 蜂蜜瓶那一支（`HONEY_DRINK`）、急迫 **120 s** + 生命恢复 I **3 s**、**吃完返还空铝罐**走**原版** `usingConvertsTo`（不自己写返还逻辑）；⑥ **手倒**走 NeoForge 的物品流体能力（原版水桶天然认），与灌装机 ZF80 同一个口径（返回 `ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION` 再落回 `useWithoutItem` 开界面）；⑦ **状态灯新号 20**「缺流体」（6 被液压机占了，按 ZF82/ZF96/ZF97 那条规矩另起号并在 `StatusLampPart` 两处 switch 挂号）；⑧ 真服务端探针 `Zf167Check` **ALL OK**（跑一轮的账：扣 10/500/0 mB、三槽清空、喂 72,000 FE 净耗 60,000、四种流体互斥、红石停机、输出满 / 缺电 / 缺流体三态、可乐真吃一罐：饥饿 10→13、饱和 0→9、急迫 2400t、恢复 60t、返还空罐）；⑨ 常驻 `_zf167_verify.py` + 反证 **31 把刀**；⑩ 语言 **605 → 620** ×4（lzh 607 → **622**）⇒ **40 份常驻门** + 英文公告 + 交接文档一起重定靶；⑪ **重打成品**（振金剑…不，本轮改了 Java）：`PotatoST-0.13.jar` = **""" + NEW_SIZE + u""" 字节 / sha1 `""" + NEW_SHA + u"""`**，⚠ 作废 `""" + OLD_SHA + u"""` | 见 §9 |"""

SECTION9 = u"""
### ZF167（0.13）空铝罐 + 可乐 + 饮料罐装机 —— **待你实测**

用户原话（逐字）：「先加个空铝罐配方；【】【铝粒】【】，【】【铝板】【】，【】【】【】合成2个空铝罐
熔炉/高炉烧制一个空铝罐产出5个铝粒；再加一个饮料罐装机（配方；【】【铁锭】【】，【拉杆】【银版】
【铁活版门】，【轻质压力板】【高压气罐】【流体管道】）一个碳酸储罐（100MB）一个水储罐（1000mb）
一个乙醇储罐（100mb 目前本mod没有乙醇 做个兼容别的mod的乙醇）三个输入槽 一个输出槽 耗电600fe/t
先做一个配方试试水 1.10mb碳酸+500mb水+2糖+1可可豆+1空铝罐 5s产出1罐可乐 可乐是食物
但是食用音效用蜂蜜瓶的 食用后给予120s的急迫 3s的生命恢复1 恢复3点饥饿值 9点饱和度
（食用后返还一个空铝罐）」。

#### 一、逐条对账

| # | 用户的话 | 落点 |
|---|---|---|
| ① | 空铝罐图纸 → 2 个 | `empty_aluminum_can.json`（铝粒在上、铝板在中；第三行空） |
| ② | 熔炉/高炉 1 罐 → 5 铝粒 | `empty_aluminum_can_from_smelting.json`（200t）/ `..._from_blasting.json`（100t） |
| ③ | 机器图纸 | `beverage_canning_machine.json`（I / LST / PHF 三行逐格照抄） |
| ④ | 碳酸 100 / 水 1000 / 乙醇 100 mB | 三只**只进不出**的输入罐（`TANK_CAPACITY_*`） |
| ⑤ | 三个输入槽 + 一个输出槽 | 槽 0 糖 / 槽 1 可可豆 / 槽 2 空铝罐 / 槽 3 输出 |
| ⑥ | 600 FE/t | `ENERGY_PER_TICK = 600`；一轮 100 tick ⇒ **60,000 FE** |
| ⑦ | 一条配方试试水 | `CanningMachineRecipes`：10 碳酸 + 500 水 + 2 糖 + 1 可可豆 + 1 空铝罐 → 1 可乐 |
| ⑧ | 可乐是食物 + 蜂蜜瓶音效 | 食物组件 + `getEatingSound/getDrinkingSound = HONEY_DRINK` |
| ⑨ | 120s 急迫 / 3s 生命恢复 I | 食物效果两条（2400t / 60t） |
| ⑩ | 3 点饥饿 / 9 点饱和度 | `nutrition(3)` + `saturationModifier(1.5F)`（**原版这里收的是修饰值**，`build()` 里换算成 9 点） |
| ⑪ | 吃完返还空铝罐 | **原版** `usingConvertsTo`（`Player.eat` 里生效，蘑菇煲还碗同一条路） |

#### 二、三处"用户没给、我定的"（要改都是一行 / 一条）

1. **储能 12,000 FE** = 20 tick 的钱（本工程其它机器也都在"几 tick"量级）。
   缓冲小于一轮是**故意的**：必须持续供电，跑不完就停在原地等电。
2. **「缺流体」用新号 20**（6 是液压机的「材料数量不够」；7~19 也各有其主）。
   界面状态灯的黄灯与悬停文案都在 `StatusLampPart` 里挂好了。
3. **「轻质压力板」= 原版 `minecraft:light_weighted_pressure_plate`** ——
   本 mod 没有压力板（把 `ModBlocks` 全扫过），另一种读法「用轻质钛合金做基底的板」
   那件物品不存在。**这条要你确认**。

#### 三、乙醇兼容是怎么做的（有据可查，不是猜标签名）

用户说「目前本mod没有乙醇 做个兼容别的mod的乙醇」⇒ 那只罐的校验器认
**`c:ethanol` 流体标签**。这个名字不是我编的：盘上那份沉浸工程
（`release/ImmersiveEngineering-1.21.1-12.4.2-194.jar`）里就有
`data/c/tags/fluid/ethanol.json` → `["immersiveengineering:ethanol"]`
（见 `_zf167_recon_ethanol.py` 的输出）。本 mod 另附一份**空**的同名标签
（`replace:false`），所以没装 IE 时标签也存在、装了 IE 时两边自动合并。
⚠ 本轮的探针环境里**没装 IE**（`run/server/mods` 只有 Mekanism / Create / Patchouli / Curios），
所以正向那条只能静态看，负向（水与碳酸进不去乙醇罐）是**真跑**过的。

#### 四、证据

| 项 | 结果 |
|---|---|
| 真服务端探针 `Zf167Check` | **ALL OK**：跑一轮（扣 10/500/0 mB、三槽清空、净耗 60,000 FE、进度归零）／四种流体互斥／红石停机／输出满·缺电·缺流体三态／可乐真吃一罐（饥饿 10→13、饱和 0→9、急迫 2400t、恢复 60t、返还空罐） |
| 常驻 `_zf167_verify.py` | A 源码 38 项 + B 资源数据 15 项 + C 探针报告 25 项 |
| 反证 `_zf167_falsify.py` | **31 把刀**（含 ZF123 那个"加了 MACHINES 却漏 iconFor case"的真坑） |
| 往轮门 | `_zf114` / `_zf142` / `_zf145` / `_zf148` / `_zf149` / `_zf150` / `_zf153`（`_zf153` 本轮跟平过一次：素材被清、用户自己改了剑的说明、振金剑有了锻造配方） |
| 语言 | 四语言 **605 → 620 键**（620 键 × 4）、`lzh` 607 → **622 键**；40 份常驻门 + 英文公告 + 交接文档一起重定靶 |
| 成品 | `release\\PotatoST-0.13.jar` = **""" + NEW_SIZE + u""" 字节 / `""" + NEW_SHA + u"""`（⚠ 作废 `""" + OLD_SHA + u"""`）；产物 389 class / 98 配方 / 43 进度、探针 class 不在里面 |

#### 五、要你实测的（进游戏）

1. **空铝罐**：铝粒 + 铝板 合成 2 个；丢熔炉烧 10 秒 → 5 个铝粒（高炉 5 秒）。
2. **饮料罐装机**：按图纸合出来（铁锭 / 拉杆 + 银板 + 铁活板门 / 轻质压力板 + 高压气罐 + 流体管道）。
3. **灌流体**：手拿**水桶**右键机器 → 水进罐（一次最多 1000 mB）；碳酸要靠管道/换流器接到碳酸罐；
   乙醇罐拿任何挂 `c:ethanol` 的模组的乙醇去灌。
4. **跑一轮**：三槽放 2 糖 / 1 可可豆 / 1 空铝罐，接上 600 FE/t 的电，5 秒后输出槽出 1 罐可乐。
5. **喝可乐**：饥饿 +3、饱和度 +9、急迫 120 秒、生命恢复 I 3 秒，**喝完还你一个空铝罐**，音效是蜂蜜瓶那一声。
6. ⚠ 顺手确认一下第 2 条那张图纸里的「轻质压力板」是不是你要的那块。
"""

LESSONS = u"""
### 4.175 【判据雷】"先剥注释再切片"会把锚点一起剃掉 —— 同一个坑第二轮又踩（0.13 ZF167）

`_zf167_verify.py` 里我用 `strip_comments(read(f))` 之后再去 `cut(text, 起点, 终点)`，
而**终点锚点是注释行**（`// ===== 创造模式标签页 =====`）与 javadoc。
注释一剃，`cut()` 就找不到终点 ⇒ 返回空串 ⇒ 六条判据全红（`A4/A5/A6/A20/A21/A22`）。

**规矩**：切片一律"**从原文切、切完再剥**"。ZF153 的 A11 已经踩过一次并在那一轮写进了教训，
这一轮**同一个坑又踩**——说明"在别的文件里写过教训"不等于"写新文件时会想起来"：
判据脚本的骨架应当**先把 `cut_from_raw()` 这种助手定下来**，再往上堆断言。

### 4.176 【工具雷】探针判据要"跟着原版语义走"，别把**修饰值**当点数（0.13 ZF167）

探针里读可乐的食物组件，拿注册时写的 `1.5F` 去比 `food.saturation()`，报假红（实测 9.0）。
根因：`FoodProperties.Builder.build()` 里有一句
`FoodConstants.saturationByModifier(nutrition, saturationModifier)`
——**注册时给的是修饰值，record 里存的是绝对点数**（3 × 1.5 × 2 = 9）。
同理 `Mob.isEffectiveAi()`（NoAI 恒 false）与 `LivingEntity.travel()` 的第一行
（`isControlledByLocalInstance()`）合起来意味着"**NoAI 的生物根本不物理位移**"——
ZF153 的探针就是这么把"击飞"验废的（速度设上了、十 tick 后原地不动）。

**规矩**：探针的期望值要么**调原版那个方法**算出来（`CombatRules.getDamageAfterAbsorb` 就是这么用的），
要么先把原版语义从 `sources.jar` 抠清楚；**凭常识写期望值**是探针假红/假绿的主要来源。
"""

ANNOUNCE = u"""
## New in 0.13 ZF167 - empty cans, cola, and a beverage canning machine

- **Empty Aluminum Can**: 1 aluminum nugget over 1 aluminum plate crafts **2 cans**;
  smelt or blast one can back into **5 aluminum nuggets**.
- **Beverage Canning Machine**: three input slots (sugar / cocoa beans / empty can), one output
  slot, and **three input-only tanks** - carbonic acid **100 mB**, water **1000 mB**, ethanol
  **100 mB**. It runs on **600 FE/t** and holds 12,000 FE. Right-click with a bucket or gas tank
  to pour; right-click empty-handed to open the GUI.
- **Ethanol compatibility**: the machine does not add its own ethanol - that tank accepts the
  **`c:ethanol` fluid tag**, which is exactly what Immersive Engineering ships
  (`immersiveengineering:ethanol`), so other mods' ethanol works out of the box.
- **First recipe**: 10 mB carbonic acid + 500 mB water + 2 sugar + 1 cocoa bean + 1 empty can
  = **1 Cola** in 5 seconds (60,000 FE).
- **Cola** is food: **3 hunger / 9 saturation**, **Haste for 120 s**, **Regeneration I for 3 s**,
  the honey-bottle drink sound, and it **gives the empty can back** (vanilla container return).

### Download: the 0.13 jar has been rebuilt (ZF167)

**`release/PotatoST-0.13.jar`** - **""" + NEW_SIZE + u""" bytes**, sha1 **`""" + NEW_SHA + u"""`**
(**389 classes / 98 recipes / 43 advancements**, five languages, **620 keys each**, Literary Chinese 622).

\u26a0 The previous 0.13 jar (sha1 `""" + OLD_SHA + u"""`) is **void**: it was built before the
canning machine existed. Use the new one.

Language files grew to **620 keys each** (Literary Chinese: 622).
"""

TEXSECTION = u"""
## ZF167（0.13）：饮料罐装机（**两张占位**）+ 空铝罐 / 可乐（**两张待画**）

用户这一轮**只给了配方与数值、没给贴图** ⇒ 按本工程的老规矩："自己起名字的占位文件 +
在待画表挂号"，而不是让模型去指别人的图。

| 项 | 值 |
|---|---|
| 机器顶面 | `textures/block/beverage_canning_machine_top.png` = `micro_crusher_top.png` 的**逐字节副本**（181 字节，占位） |
| 机器侧面 | `textures/block/beverage_canning_machine_side.png` = `micro_crusher_side.png` 的**逐字节副本**（193 字节，占位） |
| 机器模型 | `blockstates/beverage_canning_machine.json` + `models/block/beverage_canning_machine.json`（cube，顶/侧两张自己的图）+ `models/item/...`（parent 方块模型） |
| 空铝罐（待画） | `models/item/empty_aluminum_can.json` 借原版 `minecraft:item/glass_bottle` |
| 可乐（待画） | `models/item/cola.json` 借原版 `minecraft:item/honey_bottle` |
| 借原版数 | 物品模型里借原版的从 5 涨到 **7**（本轮 +2）—— 门已跟平 |

⚠ 四张都不是最终美术：机器两张是"换个名字的占位"、两个物品借的原版图。
"""


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


fails = []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def main():
    print(u"① 开发档案：台账行 + §9 + 课条")
    arch = read(ARCH)
    if u"| ZF167 |" in arch:
        print(u"  [幂等] 台账行已在")
    else:
        anchor = u"| ZF153 | **新建 `zf153_pre`**"
        n = arch.count(anchor)
        if n != 1:
            check(u"台账锚点唯一", False, u"%d 次" % n)
        else:
            i = arch.index(anchor)
            j = arch.index(u"\n", i) + 1
            arch = arch[:j] + LEDGER + arch[j:]
            write(ARCH, arch)
            check(u"台账行已加在 ZF153 之后", True)
    arch = read(ARCH)
    if u"### ZF167（0.13）空铝罐" not in arch:
        if not arch.endswith(u"\n"):
            arch += u"\n"
        write(ARCH, arch + SECTION9)
        check(u"§9 已追加", True)
    else:
        print(u"  [幂等] §9 已在")
    arch = read(ARCH)
    if u"### 4.175 " not in arch:
        heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^### 4\\.(\\d+) ", arch)]
        if not heads:
            check(u"找得到 §4 课条", False)
        else:
            top = max(heads)[0]
            start = [pos for num, pos in heads if num == top][0]
            nxt = arch.find(u"\n### ", start + 1)
            at = len(arch) if nxt < 0 else nxt + 1
            write(ARCH, arch[:at] + LESSONS + arch[at:])
            check(u"课条 4.173 / 4.174 已接在 4.%d 之后" % top, True)
    else:
        print(u"  [幂等] 课条已在")

    print(u"\n② 交接文档：§9 这一轮")
    hand = read(HAND)
    if u"## 9. ZF167 这一轮的交接" in hand or u"ZF167 这一轮的交接" in hand:
        print(u"  [幂等] 已在")
    else:
        if not hand.endswith(u"\n"):
            hand += u"\n"
        hand += HANDOFF
        write(HAND, hand)
        check(u"交接那节已追加", True)

    print(u"\n③ 贴图清单：ZF167 那节")
    tex = read(TEXL)
    if u"## ZF167（0.13）：饮料罐装机" in tex:
        print(u"  [幂等] 已在")
    else:
        if not tex.endswith(u"\n"):
            tex += u"\n"
        write(TEXL, tex + TEXSECTION)
        check(u"贴图清单那节已追加", True)

    print(u"\n④ 英文公告：ZF167 那条 + 成品 Download 段（新/旧 sha1 与 389/98）")
    ann = read(ANN)
    if u"## New in 0.13 ZF167" not in ann:
        if not ann.endswith(u"\n"):
            ann += u"\n"
        write(ANN, ann + ANNOUNCE)
        check(u"公告那条已追加", True)
    else:
        print(u"  [幂等] 公告那条已在")
    back = read(ANN)
    check(u"公告回读：新 sha1 / 作废 sha1 / 620 keys each / 389",
          NEW_SHA in back and OLD_SHA in back and u"(620 keys each)" in back and u"389 classes" in back)
    print(u"\n失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


HANDOFF = u"""
## 9. ZF167 这一轮的交接（空铝罐 + 可乐 + 饮料罐装机）

**用户原话**：「先加个空铝罐配方；【】【铝粒】【】，【】【铝板】【】，【】【】【】合成2个空铝罐
熔炉/高炉烧制一个空铝罐产出5个铝粒；再加一个饮料罐装机（配方；【】【铁锭】【】，【拉杆】【银版】
【铁活版门】，【轻质压力板】【高压气罐】【流体管道】）一个碳酸储罐（100MB）一个水储罐（1000mb）
一个乙醇储罐（100mb 目前本mod没有乙醇 做个兼容别的mod的乙醇）三个输入槽 一个输出槽 耗电600fe/t
先做一个配方试试水 1.10mb碳酸+500mb水+2糖+1可可豆+1空铝罐 5s产出1罐可乐 可乐是食物
但是食用音效用蜂蜜瓶的 食用后给予120s的急迫 3s的生命恢复1 恢复3点饥饿值 9点饱和度
（食用后返还一个空铝罐）」。

### 9.1 动了什么

| 类别 | 文件 |
|---|---|
| 新增 Java | `ColaItem.java`、`CanningMachineRecipes.java`、`BeverageCanningMachine{Block,BlockEntity,Menu}.java`、`client/BeverageCanningMachineScreen.java` |
| 改 Java | `ModItems`（两个物品 + 创造页两行）、`ModBlocks`（方块 + 物品 + 方块实体）、`ModMenus`、`PotatoST`（三条能力）、`PotatoSTClient`、`client/jei/PotatoSTJeiPlugin`（MACHINES + iconFor case）、`MachineRecipes`（JEI 那条展示）、`client/gui/parts/StatusLampPart`（新状态号 20） |
| 新增资源 | 机器 blockstate + 模型 ×3 + 两张**占位**贴图；两个物品模型（借原版） |
| 新增数据 | 四份配方 JSON + `data/c/tags/fluid/ethanol.json`（空标签，`replace:false`） |
| 语言 | 五份各 +15 键：**605 → 620**（lzh 607 → **622**） |
| 门 | **40 份**写死键数的常驻门跟平；`_zf153_verify.py` 跟平三处（B3 素材被清 → 改比 HEAD、B10/B11 用户自己改了说明 → 改盯机制词、B14 振金剑有锻造配方了 → 翻成正向） |
| 成品 | `release\\PotatoST-0.13.jar` = **""" + NEW_SIZE + u""" 字节 / `""" + NEW_SHA + u"""`，⚠ 作废 `""" + OLD_SHA + u"""` |

### 9.2 你们接手前必须知道的三件

1. **乙醇不造，只认标签**：那只罐收 `c:ethanol`（沉浸工程自己的标签名，从盘上 jar 里抠的）。
   探针环境里没装 IE ⇒ 正向只能静态看，负向（水/碳酸进不去）是真跑过的。
2. **「轻质压力板」按原版 `light_weighted_pressure_plate` 走**（本 mod 没有压力板）。
   这条**要用户确认**，换成别的材料只改那一个 JSON。
3. **储能 12,000 FE / "缺流体"= 状态号 20** 都是我定的（用户没给）：前者是 20 tick 的钱，
   后者是因为 6 被液压机占了（按 ZF82/ZF96/ZF97 那条"不能共用就另起号并说清为什么"的规矩）。

### 9.3 本轮踩到的两个新坑（详见档案 §4.173 / §4.174）

- **"先剥注释再切片"又栽一次**：终点锚点是注释行 ⇒ `cut()` 返回空串 ⇒ 六条判据假红。
  规矩：**从原文切、切完再剥**。
- **探针的期望值要跟着原版语义走**：`FoodProperties.Builder` 收的是**修饰值**、record 存的是
  **绝对点数**（1.5 ⇒ 9.0），拿 1.5 比 `saturation()` 会假红；NoAI 的生物因为
  `isEffectiveAi()` 恒 false + `travel()` 第一行的守卫 ⇒ **根本不物理位移**（ZF153 就是这样
  把"击飞"验废的）。
"""

if __name__ == u"__main__":
    sys.exit(main())
