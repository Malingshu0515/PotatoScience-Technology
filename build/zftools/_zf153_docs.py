# -*- coding: utf-8 -*-
u"""_zf153_docs.py —— ZF153 的三份文档（**幂等**，锚点唯一才动手）

写四处：
  ① `docs\\开发档案.md` 台账表：在 ZF152 那一行之后加一行 ZF153；
  ② `docs\\开发档案.md` §9：在**文件末尾**追加本轮的整节（往轮也是这么加的）；
  ③ `docs\\开发档案.md` §4 课条：接在**编号最大**的那一条之后（本轮 = 4.161 / 4.162）；
  ④ `docs\\多会话协作交接.md` 末尾加 `## 8. ZF153 这一轮的交接`；
  ⑤ `docs\\贴图清单.md` 末尾加 `## ZF153（0.12）：振金剑`；
  ⑥ `docs\\UpdateAnnouncement_EN.md`：0.12 那一段末尾加一条（ZF147 立的日志纪律：
     每一轮改动都要在英文公告留一条）。

⚠ 三份文档**别的线也在写**（本轮开工时它们的 mtime 是 13:47~13:49）⇒
   一律"读取 → 精确锚点替换 → 立刻写回"，锚点必须**唯一**，找不到就停下报告，不猜。
跑法：python build\\zftools\\_zf153_docs.py
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

LEDGER = u"""| ZF153 | **新建 `zf153_pre`**（**238 份**改前件：`ModTiers.java` / `ModItems.java` / `PotatoST.java`（⚠ 探针挂载点，这次**动手前**就在清单里）/ 五份 lang / `_来源凭据.json` / **全部常驻门**（`_zf*_verify.py` + `_zf*_falsify*.py` + `_zf*_gates.py` + `_rzh_*.py`）/ 九道门本体 / 三份文档 / 旧成品 `PotatoST-0.12.jar` + `.sha1`；逐份核 sha1 + **回读**，238/238 逐字节相同，失败 0。⚠ 开工前查过轮号：`_zf153_*` 无人占、救援目录里没有 `zf153_pre`（§4.147）；开工时另一条线（ZF151/152）的探针还挂在 `PotatoST.java:78`，**等它撤了才动**） | **0.12：振金剑**（用户原话「加个振金剑材质在素材 无法破坏 拿在手里免疫凋零，缓慢，挖掘疲劳 24点伤害 1.4攻击速度 1附魔权重 shift+右键猛击地面 击飞6x6除自己的所有生物 并对其造成n+12点伤害 n为玩家基础伤害 和4s的失明 4s的缓慢效果 冷却6s」）。① **数值**：显示 24 = 1 + (参数 15 + 档位加成 8)、攻速 1.4 = 4.0 - 2.6（`SwordItem.createAttributes` 的算式是**从 sources.jar 抠出来的**，不是回忆）、**附魔权重 1** 落在档位第六格（`TieredItem.getEnchantmentValue()` 直接取档位 —— 这条也是抠出来的）；② **无法破坏** = `DataComponents.UNBREAKABLE`（与振金套 ZF120 同一个做法）⇒ `isDamageableItem()` 恒 false、**真扣 500 点耐久一动不动**（探针实测）；⚠ 物品注册处**故意不写 `.durability(...)`**（`TieredItem` 构造器里 `properties.durability(tier.getUses())` 会盖掉它 —— 本轮现抠的）；③ **手持免疫三种效果**走**两条路**：源头拦（`MobEffectEvent.Applicable` ⇒ `DO_NOT_APPLY`；`LivingEntity.addEffect` 的**第一行**就是这个 hook）+ 每 tick 清理（把已经挂在身上的抹掉）；④ **猛击**：`getEntitiesOfClass` 圈 6×6×6、排除自己与创造/观察者、`hurt` **之后**才写速度（原版 `hurt` 自己会推 0.4，写反就白推）、失明/缓慢各 80 tick、冷却走**原版物品冷却** 120 tick；⑤ **n 的口径复用** ZF133 已过探针的 `ShockwaveManager.baseAttackDamage`（不含手持装备）⇒ 空手 n=1、这一下税前 13；⑥ 贴图 `振金剑_001.png` 16x16/8 位 RGBA ⇒ **原字节复制**（形状 IoU 与原版六档**剑**均为 **1.0000**，最好的非剑只有 0.4271）；⑦ 真服务端探针 `Zf153Check`（husk 三近一远 + 三条灵敏度对照）**46 项 ALL OK**；常驻 `_zf153_verify.py` **58 项 0 失败**、反证 **27/27 把刀全咬住**（其中 K14b 反证出 A26 判据的缺口并顺手收紧）；⑧ 语言 **583 → 587** ×4（lzh 585 → **589**）⇒ **33 份写死键数的常驻门** + 英文公告 + 交接文档一起重定靶 | 见 §9 ｜ 见 §4.161\\~§4.162 |
"""

SECTION9 = u"""
### ZF153（0.12）振金剑：无法破坏 / 手持免疫三种效果 / Shift+右键猛击地面 —— **待你实测**

用户原话（逐字）：「加个振金剑材质在素材 无法破坏 拿在手里免疫凋零，缓慢，挖掘疲劳 24点伤害
1.4攻击速度 1附魔权重 shift+右键猛击地面 击飞6x6除自己的所有生物 并对其造成n+12点伤害
n为玩家基础伤害 和4s的失明 4s的缓慢效果 冷却6s」。

#### 一、七条需求各自落在哪

| # | 用户的话 | 落点 | 数值/判据 |
|---|---|---|---|
| ① | 材质在素材 | `build/用户素材/振金剑_001.png` ⇒ `textures/item/vibranium_sword.png` | 16x16 / 8 位 RGBA / 无隔行 / 零半透明 ⇒ **原字节复制**（零转档）；身份：alpha 掩码与原版六档**剑**的 IoU 均 **1.0000**，最好的非剑（木锹）只有 0.4271 |
| ② | 无法破坏 | `DataComponents.UNBREAKABLE`（照振金套 ZF120） | `isDamageableItem()` 恒 false ⇒ `hurtAndBreak` 整个 no-op；探针**真扣 500 点**，耐久 0 → 0 |
| ③ | 拿在手里免疫凋零/缓慢/挖掘疲劳 | `VibraniumSwordItem.onEffectApplicable`（源头）+ `onPlayerTick`（清理） | 源头：`MobEffectEvent.Applicable` ⇒ `DO_NOT_APPLY`（`LivingEntity.addEffect` 的**第一行**就是这个 hook，` :972`）；清理：拿着剑时身上已有的三种立刻掉 |
| ④ | 24 点伤害 | `ModTiers.VIBRANIUM_SWORD_DAMAGE = 15.0F` | 显示 **24.0** = 玩家基础 1 + (15 + 档位加成 8) |
| ⑤ | 1.4 攻击速度 | `ModTiers.VIBRANIUM_SWORD_SPEED_MODIFIER = -2.6F` | **1.4** = 4.0 - 2.6（原版剑是 -2.4 ⇒ 1.6） |
| ⑥ | 1 附魔权重 | `ModTiers.VIBRANIUM_ENCHANTMENT_VALUE = 1` | `TieredItem.getEnchantmentValue()` 直接取档位那一格 ⇒ 物品类不用覆写 |
| ⑦ | Shift+右键猛击地面 | `VibraniumSwordItem.use` / `slam` / `launch` | 6×6×6 内除自己全部：击飞 + (n+12) 伤害 + 失明 4s + 缓慢 4s；冷却 **6s**（原版物品冷却 120 tick） |

#### 二、三处"写错就悄悄错"的地方（本轮全是从 sources.jar 抠出来的，不是回忆）

1. **`createAttributes` 的算式**：`BASE_ATTACK_DAMAGE_ID, 参数 + tier.getAttackDamageBonus()`，
   而"玩家空手 1 点"在属性**基础值**里 ⇒ 想要 24，参数必须是 24 - 1 - 8 = **15**。
   攻速同理：原版剑传 -2.4 得 1.6 ⇒ 想要 1.4 就得传 **-2.6**。
2. **附魔权重不在物品上**：`TieredItem.getEnchantmentValue()` 的实现就是 `return this.tier.getEnchantmentValue();`
   ⇒「1附魔权重」= 档位第六个字段写 1，物品类里一个字都不用改。
3. **耐久也不在物品上**：`TieredItem(Tier, Properties)` 的构造器里有
   `super(properties.durability(tier.getUses()))` ⇒ 注册处再写一遍 `.durability(...)` 只会被盖掉。
   本轮**故意不写**，并让常驻判据 `A11` 把"写了"判红（免得下一个人以为那里能动）。

#### 三、免疫为什么是两条路，而不是"每 tick 抹掉"

`LivingEntity.addEffect` 的**第一行**就是 `CommonHooks.canMobEffectBeApplied(...)`
（1.21.1 的 `:972`），而这个 hook 里抛的正是 `MobEffectEvent.Applicable`
（结果枚举是 `APPLY / DEFAULT / DO_NOT_APPLY`，不是 DENY）。**从源头拒绝**意味着
凋零那 40 tick 一跳的伤害压根不会发生；`onPlayerTick` 那条只管另一半场景：
"我已经中毒/被凋零了，此时才把剑抽出来" —— 玩家那一刻的预期是"拿在手里就该免疫"。

#### 四、`n` 的口径（这条最容易被读成另一个意思，写清楚）

用户给的「n 为玩家基础伤害」在本工程**已经有先例**：ZF133 斧子冲击波的「10 + 0.5n」
用的就是 `ShockwaveManager.baseAttackDamage(player)` —— 它的注释写得很清楚：
1.21 起物品攻击力就是普通属性修饰符，直接读 `getAttributeValue(ATTACK_DAMAGE)`
拿到的是"这把武器的伤害"、换把武器就变，**与"玩家基础伤害"对不上**。
所以本轮**复用同一个方法**（不另写一份），空手站着的玩家 **n = 1** ⇒ 这一下**税前 13 点**；
喝了力量药水会跟着涨。
⚠ 如果你要的其实是"剑面 24 + 12 = 36"，改一个调用点即可（`slam` 里那一行），说一声。

#### 五、刻意保留的连带后果（免得下轮当 bug 修）

- **伤害走 `playerAttack`**（与 ZF133 冲击波同一条）⇒ 照样吃目标护甲与附魔，
  **n+12 是税前**。探针实测：husk 自带 2 点护甲 ⇒ 13 点税前掉 **12.792**
  （正是原版 `CombatRules.getDamageAfterAbsorb` 的结果，探针直接调原版那个方法当期望值）。
- **被击飞的目标落地会吃摔落伤害**：竖直初速 0.8 会把人抬到约 3.9 格高，
  落地扣掉原版"头 3 格免伤"那一档大约再吃 1 点上下。
- **创造模式 / 观察者玩家整只跳过**（照 ZF133 那条已过探针的口径）。
- **出手不扣耐久**（物品是无法破坏的，用户也没说要代价）。
- **没有配方**：用户没给 ⇒ 与 ZF119 振金锭同一条口径，常驻判据 `B14` 盯着
  "盘上任何配方/进度都不许提到它"，等哪天给配方再改成正向断言。

#### 六、证据

| 项 | 结果 |
|---|---|
| 真服务端探针 `Zf153Check`（挂载 → runServer → 摘除） | **ALL OK**：属性 24/1.4、附魔权重 1、真扣 500 不动、三条免疫**各配一条灵敏度对照**（空手挂得上 / 拿着挂不上）、急迫与速度不被误伤、三个近目标各掉血+失明80+缓慢80+被向上击飞、**10 tick 后真离地**、范围外第四只一动不动、自己没掉血、冷却中被拒、冷却清掉后立刻又能用 |
| 常驻 `_zf153_verify.py` | **58 项 0 失败**（A 源码 34 / B 资源 15 / C 探针报告 19 / D 往轮门 5 / E 记录） |
| 反证 `_zf153_falsify.py` | **27 / 27 把刀全咬住**（数值 / 组件 / 顺序 / 排除名单 / 资源 / 语言 / 配方 / 命名） |
| 往轮门 | `_zf114`（星轨坠 188 项）/ `_zf142` / `_zf145` / `_zf148` / `_zf150` 全 exit 0 |
| 语言 | 四语言 **583 → 587 键**（587 键 × 4）、`lzh` 585 → **589 键**；33 份写死键数的常驻门 + 英文公告 + 交接文档一起重定靶 |

#### 七、要你实测的（进游戏）

1. 创造页最后应当有**振金剑**（24 伤害 / 1.4 攻速 / 紫色附魔光效**没有** —— 用户只说了无法破坏，
   没说自带光效；振金**套**那四件才有，要的话补一个组件的事）。
2. Shift 看说明：三行（数值 / 手持免疫 / 猛击）。
3. 拿在手里吃一口**凋零药水**或让凋灵打一下：**不该**上凋零；身上已有的凋零应当**立刻掉**。
   同样试缓慢（史莱姆/药水）与挖掘疲劳（远古守卫者）。
4. 6×6 内放几只怪，**Shift + 右键**：全体被击飞（看得见飞起来）、失明 4 秒、缓慢 4 秒，
   快捷栏上出现 **6 秒**冷却圈；范围外那只**一点事都没有**。
5. 拿它去附魔台：附魔权重 1 ⇒ 几乎点不出好东西（这是用户要的）。
"""

LESSONS = u"""
### 4.161 【工具雷】探针挂载/摘除的三个坑：结构猜测、基准选错、只认一半标记（0.12 ZF153）

1. **挂载点不能用"从后往前找 `    }`"这种结构猜测**：第一版按"最后一行缩进 4 格的闭括号"
   找构造函数收尾，结果插进了**最后一个方法**里 —— 编译能过、`register()` 却只在那个方法
   被调用时才跑（探针永远不注册）。改成**点名唯一锚点**（`…onPlayerLogin);` 那一行），
   并加一条**结构守卫**：插入位置必须在第一个方法定义之前（"那才叫在构造函数里"）——
   守卫生效后才敢继续。
2. **"摘干净"的基准有两份，别选错**：拿**改前件**当基准是错的 —— 本轮功能本身就在那份文件里
   （两处监听 11 行），摘掉探针也不会变回改前件。要另存一份"功能改完、探针未挂"的快照，
   摘除后与**它**逐字节比；与改前件的差则要求"正好是功能那几行"。
3. **摘除的过滤器要把挂载块每一行都认出来**：第一版只认了三行里的两行，
   于是反复挂/摘会把漏掉的那行**一层层叠起来**（第三次挂完，那一行出现了 3 份），
   而且**连基准快照也把残留拍了进去**。发现之后没有继续做减法，而是**确定性重建**：
   `改前件（剔掉别人探针的残留） + 本轮功能块` ⇒ 与改前件逐字核那 11 行。
   ⚠ 附带发现：改前件里带着**另一条线探针的残留**（他们 13:47 挂、13:52 之后才撤），
   重建时必须一起剔掉，否则会引用一个已经不存在的类。
"""

LESSONS2 = u"""
### 4.162 【判据雷】反证刀不够狠，判据的缺口就永远看不见（0.12 ZF153）

`A26`（"先 hurt 再写速度"）本来是这样验的：在 `launch()` 切片里找 `target.hurt(` 与
`setDeltaMovement(` 的**首次出现**位置，要求前者在前。反证时我写的刀是"把 hurt 那一行
**插入**到写速度之后"—— 结果 `find()` 拿到的还是原来那一处（前面的那份还在），
**判据判对、刀没咬住**。

两件事同时做才算收工：
1. **把刀改成真搬移**（删原处 + 插新处）—— 刀必须真的把被测性质破坏掉；
2. **顺手把判据收紧**：`launch.count("target.hurt(") == 1`（只许出现一次）——
   这样"插一份新的在别处"这种半吊子改动也咬得住。

> 记一笔：反证的价值不只是"证明判据有效"，它还能**发现判据自己漏了什么**。
> 本轮 27 把刀里唯一没咬住的那一把，最后换来的是判据本身变严 —— 这比"27 把全绿"更值钱。
"""

ANNOUNCE = u"""
## New in 0.12 ZF153 - the Vibranium Sword

A **Vibranium Sword** joins the top of the weapon line:

- **Unbreakable** (the `UNBREAKABLE` component, same as the Vibranium armour), **24 attack
  damage**, **1.4 attacks per second**, and **enchantment weight 1** - it barely answers the
  enchanting table.
- **While held**: immunity to **Wither, Slowness and Mining Fatigue**. This is denied at the
  source (`MobEffectEvent.Applicable` -> `DO_NOT_APPLY`, the first thing `addEffect` asks),
  plus a per-tick cleanup that strips an effect you already had the moment you draw the sword.
- **Shift + right-click: slam the ground.** Every creature within **6x6** (except you) is
  launched into the air, takes **your base damage + 12**, and is **blinded and slowed for 4 s**.
  **6 s cooldown** (the vanilla item cooldown, the grey ring on your hotbar).
- The damage is dealt through the vanilla armour formula, so the `+12` is the **pre-armour**
  number; the launch also means a landing - fall damage included.
- **No recipe yet** - it is in the creative tab only (same account as the Vibranium Ingot).

Language files grew to **587 keys each** (Literary Chinese: 589).
"""


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline=u"\n").write(t)


fails, notes = [], []


def check(label, ok, detail=u""):
    print(u"  [%s] %s%s" % (u"OK" if ok else u"!!", label, (u"   " + detail) if detail else u""))
    if not ok:
        fails.append(label)
    return ok


def main():
    # ---------- ① 台账表 ----------
    print(u"① 开发档案：台账表加一行")
    arch = read(ARCH)
    if u"| ZF153 |" in arch:
        notes.append(u"台账行已在（幂等）")
    else:
        anchor = u"| ZF152 | ⚠ **本轮不改源码"
        n = arch.count(anchor)
        if n != 1:
            check(u"台账锚点（ZF152 行）唯一", False, u"出现 %d 次" % n)
        else:
            i = arch.index(anchor)
            j = arch.index(u"\n", i) + 1
            arch = arch[:j] + LEDGER + arch[j:]
            write(ARCH, arch)
            check(u"台账行已加在 ZF152 之后", True)

    # ---------- ② §9（追加到文件末尾）----------
    print(u"② 开发档案：§9 本轮整节")
    arch = read(ARCH)
    if u"### ZF153（0.12）振金剑" in arch:
        notes.append(u"§9 那节已在（幂等）")
    else:
        if not arch.endswith(u"\n"):
            arch += u"\n"
        arch += SECTION9
        write(ARCH, arch)
        check(u"§9 已追加", True)

    # ---------- ③ §4 课条 ----------
    print(u"③ 开发档案：§4 课条（接在编号最大那条之后）")
    arch = read(ARCH)
    if u"### 4.161 " in arch:
        notes.append(u"课条已在（幂等）")
    else:
        heads = [(int(m.group(1)), m.start()) for m in
                 re.finditer(u"(?m)^### 4\\.(\\d+) ", arch)]
        if not heads:
            check(u"找得到 §4 课条", False)
        else:
            top = max(heads)[0]
            if top >= 161:
                check(u"课条编号 4.161 没被别人先占", False, u"场上最大是 4.%d" % top)
            else:
                # 接在**编号最大**那一条的整块之后（到下一个 ### 标题为止）
                start = [pos for num, pos in heads if num == top][0]
                nxt = arch.find(u"\n### ", start + 1)
                at = len(arch) if nxt < 0 else nxt + 1
                arch = arch[:at] + LESSONS + LESSONS2 + arch[at:]
                write(ARCH, arch)
                check(u"课条 4.161 / 4.162 已接在 4.%d 之后" % top, True)

    # ---------- ④ 交接文档 ----------
    print(u"④ 交接文档：## 8")
    hand = read(HAND)
    if u"## 8. ZF153 这一轮的交接" in hand:
        notes.append(u"交接 §8 已在（幂等）")
    else:
        if not hand.endswith(u"\n"):
            hand += u"\n"
        hand += HANDOFF
        write(HAND, hand)
        check(u"交接 §8 已追加", True)

    # ---------- ⑤ 贴图清单 ----------
    print(u"⑤ 贴图清单：本轮那节")
    tex = read(TEXL)
    if u"## ZF153（0.12）：振金剑" in tex:
        notes.append(u"贴图清单那节已在（幂等）")
    else:
        if not tex.endswith(u"\n"):
            tex += u"\n"
        tex += TEXSECTION
        write(TEXL, tex)
        check(u"贴图清单那节已追加", True)

    # ---------- ⑥ 英文公告 ----------
    print(u"⑥ 英文公告：加一条（ZF147 立的日志纪律）")
    ann = read(ANN)
    if u"## New in 0.12 ZF153" in ann:
        notes.append(u"公告那条已在（幂等）")
    else:
        if not ann.endswith(u"\n"):
            ann += u"\n"
        ann += ANNOUNCE
        write(ANN, ann)
        check(u"公告那条已追加", True)
    check(u"公告回读：587 keys each 在、ZF153 那条在",
          u"(587 keys each)" in read(ANN) and u"ZF153" in read(ANN))

    print(u"\n备注：")
    for n in notes:
        print(u"  - " + n)
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


TEXSECTION = u"""
## ZF153（0.12）：振金剑（新增 **1 张**，规格本来就对 ⇒ 原字节复制）

用户原话：「加个振金剑材质在素材 …」——素材是他放进 `build\\用户素材` 的
**`振金剑_001.png`**（与 ZF141 四把工具、ZF144 锹、ZF150 四种粒同一条路）。

| 项 | 值 |
|---|---|
| 源素材 | `build\\用户素材\\振金剑_001.png`，2929 字节，sha1 `2495b1e27dd57251897d35745f50803d18892917` |
| 体检 | 16×16 / **8 位** / **颜色类型 6（RGBA）** / 无隔行 / 全不透明 84 像素 / 全透明 172 / **半透明 0** / 独立颜色 17 —— 正是本工程要的规格 ⇒ **原字节复制**（零重采样、零转档） |
| 落位 | `textures/item/vibranium_sword.png`（回读：字节相同 + 逐像素相同） |
| 模型 | `models/item/vibranium_sword.json`：`parent = minecraft:item/handheld`、`layer0 = potato_s_t:item/vibranium_sword`（**不借原版**） |
| 身份核实 | alpha 掩码 vs 原版六档 × 五种工具：**六把剑全是 IoU 1.0000**，最好的非剑（木锹）只有 **0.4271** ⇒ 与文件名一致、没有歧义 |
| 对照 | 盘上 `star_steel_sword.png` 与它是 0.8571（同一族的剑形，但不是同一张） |
| 借原版数 | **不动**（本次是"从借改为自有"的反面：新物品从一开始就用自己的图） |
"""

HANDOFF = u"""
## 8. ZF153 这一轮的交接（振金剑）

**用户原话**：「加个振金剑材质在素材 无法破坏 拿在手里免疫凋零，缓慢，挖掘疲劳 24点伤害
1.4攻击速度 1附魔权重 shift+右键猛击地面 击飞6x6除自己的所有生物 并对其造成n+12点伤害
n为玩家基础伤害 和4s的失明 4s的缓慢效果 冷却6s」。

### 8.1 这一轮动了什么

| 类别 | 文件 |
|---|---|
| 新增 Java | `VibraniumSwordItem.java`（一次性把七条需求全写在类注释里） |
| 改 Java | `ModTiers.java`（振金档：**附魔权重 1** / 加成 8 / 耐久 2031 / 洗振金锭）、`ModItems.java`（注册 + 创造页）、`PotatoST.java`（两处 game 总线监听） |
| 新增资源 | `textures/item/vibranium_sword.png`（原字节复制）、`models/item/vibranium_sword.json` |
| 改资源 | 五份 `lang`（+4 键 ×5） |
| 改门 | **33 份写死语言键数的常驻门**（583 → 587 / 585 → 589）+ 英文公告的当前值那句 + 本文件的 §1 活体数字 |
| 文档 | 档案台账 + §9 + §4.161/§4.162、本文件 §8、`贴图清单.md`、英文公告 |

### 8.2 你们接手前必须知道的三件事

1. **`n` 的口径**：复用 `ShockwaveManager.baseAttackDamage`（**不含手持装备**）⇒ 空手 n=1、
   这一下**税前 13**。用户原话是「n为玩家基础伤害」，与 ZF133 斧子那条是同一句；
   若他其实要"剑面 24 + 12 = 36"，改 `slam` 里那一行即可。
2. **`ModItems` 里**故意不写 `.durability(...)`：`TieredItem` 构造器会用档位耐久盖掉它
   （本轮从 sources.jar 核实）。常驻判据 `A11` 会把"写了"判红。
3. **没有配方**（用户没给）⇒ 判据 `B14` 盯着"任何配方/进度都不许提到 `vibranium_sword`"，
   哪天给配方要把那条改成正向断言（ZF119 振金锭同一条账）。

### 8.3 本轮踩到并已立规矩的坑（详见档案 §4.161 / §4.162）

- 探针挂载点**不能靠结构猜测**（`    }` 从后往前找 ⇒ 插进了最后一个方法里）；
  要**点名唯一锚点 + 结构守卫**（必须在第一个方法之前）。
- "摘干净"要两份基准：**改前件**与**功能改完、探针未挂**（后者才是摘除后该等于的那份）。
- 摘除过滤器要把挂载块**每一行**都认出来，否则反复挂/摘会叠层（第一版就叠了）。
- 反证刀不狠，判据的缺口看不见（K14b）⇒ 刀要**真搬移**，顺手把判据收紧成"只许一处"。

### 8.4 环境上的两件实事（不留给下一个人猜）

- 本轮开工时**另一条线（ZF151/152）的探针挂在 `PotatoST.java:78`**，我等它撤了才动；
  而我的 `zf153_pre` 备份里**带着他们探针那两行**（残留），重建功能块时已按"剔掉别人探针"
  处理并逐字核过 —— 你们看到 `_zf153_repair_main.py` 别误以为是多此一举。
- 我的第一次探针**绑定 25565 失败**：当时另一条线的专用服务端（`forgeserverdev`）正占着那个端口。
  **没有掐别人的进程** —— 给自己的探针换到 **25566**（`_zf153_probe.py set-port`），
  跑完把 `run\\server\\server.properties`（连同 `level-name=zf77_newtest`，那是他们留下的）
  **逐字节还原**。
"""

if __name__ == u"__main__":
    sys.exit(main())
