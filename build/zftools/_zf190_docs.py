# -*- coding: utf-8 -*-
u"""_zf190_docs.py —— ZF190 文档落笔（§4.190 + §5 行 + §9 段 + 交接第 47 条 + 英文公告 +
中英双语公告）+ 哈希三处联动 + **两道老门的判据跟平**。

主题：① 召唤费 bug（固定 8M）；② 第三模式「坍缩模式-危险」。
跑法：python build\\zftools\\_zf190_docs.py [--write]
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=u"utf-8", errors="replace")

ROOT = r"E:\PotatoST"
DOC = os.path.join(ROOT, "docs", u"开发档案.md")
HAND = os.path.join(ROOT, "docs", u"多会话协作交接.md")
ANN = os.path.join(ROOT, "docs", "UpdateAnnouncement_EN.md")
BIL = os.path.join(ROOT, "docs", u"0.13_0.14更新公告与介绍_中英.md")
V149 = os.path.join(ROOT, "build", "zftools", u"_zf149_verify.py")
V186 = os.path.join(ROOT, "build", "zftools", u"_zf186_verify.py")
V188 = os.path.join(ROOT, "build", "zftools", u"_zf188_verify.py")
JAR = os.path.join(ROOT, "release", u"PotatoST-0.14.jar")

S4 = u"""### 4.190 【黑洞雷】召唤费要「按次」不要「抽干」；危险模式三件事：电价、边界、保险丝（0.14 ZF190）

用户原话：「**修一下bug 黑洞正常单次召唤应该只消耗8m电力（配置改成64m之后充满一次性把全部电力都消耗完了）**
然后 引力装置再加一个模式【坍缩模式-危险】（红色字体）开启后无差别吸引最近所有的生物以及方块（振金免疫）
吸引到的掉落物会销毁 然后吸引时间越长吸引强度越高伤害也越高（召唤这个不是一次性消耗8m电力 而是召唤出来
消耗4m 然后黑洞每存在1tick消耗50kFE没有电力时候黑洞消失）（一个黑洞存在超过2分钟也会销毁 并产生30power
的爆炸）」。

**① `setEnergy(stack, 0)` 是「抽干整条」，不是「收 8M 费用」。** ZF186 把容量做成可配（1M~64M）之后，
这一行的语义就炸了：容量 64M 时一次召唤扣 64M。修法是引入**召唤费**：
`SUMMON_COST = 8M`，`fire()` 扣 `getEnergy(stack) - cost`；`use()` 的闸门也从「必须充满」改成
「至少够这一次」（不然 64M 的装置得先充满才肯花 8M）。
⚠ 边界：容量下限是 1M，而费用是 8M ⇒ 不封顶的话那种配置**永远放不出来**，
所以 `summonCost()` 用 `Math.min(费用, 容量)`（小容量也能用，放完就精光）。

**② 「一次性」要和「电费制」分开。** 坍缩模式靠装置**每 tick 供电**（50k FE）：装置要是照旧当场损坏，
黑洞下一 tick 就没电可扣、立刻消失 ⇒ 一次性那一刀对它**豁免**（`&& mode != MODE_COLLAPSE`）。

**③ 「无差别」必须自己划边界。** 坍缩模式吸一切 —— 但**空气/流体不是方块**、
**不可破坏的（`defaultDestroyTime() < 0`：基岩 / 屏障 / 命令方块 / 末地传送门框架）不吸**
（把地基啃穿 = 坏存档）；而且「搬过去」的必须是**原位那一种方块**
（`Block moved = collapse ? state.getBlock() : hole.block`），否则就成了「吸石头变钻石」。

**④ 2 分钟保险丝要**真爆炸**。** 电费制理论上能边充边放养到天荒地老 ⇒ 加 `HARD_CAP_TICKS = 2400`
（用户给的 2 分钟），到点 `level.explode(..., 30.0F, ExplosionInteraction.TNT)`。
⚠ 用 `NONE` 就只是特效；用户要的是「危险」，所以用 `TNT`（炸方块、掉落物照常）。
⚠ 顺带一个视觉雷：**长寿命黑洞会把前兆期的环半径按年龄线性放大到几百格**
（`(age - FX_OMEN)/(lifetime - FX_OMEN)` 在 `age > lifetime` 时 > 1）⇒ 那处 `k` 必须
`Mth.clamp(k, 0, 1)`；心跳音量同理夹到 2.0。

**⑤ 顺手修的真 bug：先塌后摘 = 存档复活。** `collapse()` 里会 `saveInto()`，而旧代码是
「先 `collapse(hole)` 再 `it.remove()`」⇒ 刚结束的黑洞被**写回存档**，每次重启都会「复活一次再塌」。
本轮改成一律**先 `it.remove()`、后 `collapse()/boom()`**（门 B8 用正则钉住调用顺序）。

**⑥ ⚠ 判据的「位置 / 顺序 / 容量」也会骗人 —— 探针三连假红（都是判据错，不是被测代码错）：**
  · 量「扣了多少电」必须先把「一次性」关掉：默认开着时装置放完就没了，剩下的电跟着物品一起消失
    （读出来还是 0）—— A2 第一版就这么假红；
  · 坍缩模式要跑 600 tick = 30M 电费，而 B2 为了量价格把容量设成了 8M ⇒ 装置半路没电、洞当场消失
    （诊断行「老装置电量 0 / 活跃黑洞 1」是铁证）；
  · **±140 格那种距离上 `isLoaded()` 是 true，但 `getEntitiesOfClass()` 一个生物都看不到**
    （诊断行「老洞可见生物 0」）⇒ 拉不动也打不到；把试验洞挪到 ±60 格（出生点实打实的区块范围）才好。
  教训：**假红先打印诊断行**（活跃黑洞数 / 装置电量 / 距离 / 可见生物数），别急着改被测代码。

**⑦ 语言键只加一个。** 用户说「语言键都不需要改和加（**除了显示模式的**）」⇒ 只加
`message.potato_s_t.gravity.mode.collapse`（五语种补齐：690 / lzh 692）；
模式的**红色**是代码里 `withStyle(ChatFormatting.RED)` 上的色，不是文案。

"""

ROW = u"""| ZF190 | **新建 `zf190_pre`**（**125 份**改前件：2 份将改源码 + `neoforge.mods.toml` + 五份 lang + 4 份文档 + 6 份脚本 + 前两轮两道门与三个探针 + 旧成品与 `.sha1` + **全部常驻门 103 份**；逐份核 sha1 + 回读，失败 0。⚠ 轮号 `_zf190_*` / §4.190 查过没人占（§4.147）） | **0.14：召唤费 bug 修复 + 引力装置第三模式「坍缩模式-危险」**（用户原话见 §9）。① **召唤费**：`SUMMON_COST = 8M`、`fire()` 扣 `getEnergy - cost`（旧代码 `setEnergy(stack, 0)` 抽干整条 ⇒ 容量 64M 时一次吃 64M，用户报的就是这个）、`use()` 闸门改成「够这一次就行」、`summonCost()` 按容量封顶（§4.190①）。② **坍缩模式（第 3 档，Shift+左键循环，模式名红色）**：召唤 4M + **每 tick 50k**（没电即消失）、**无差别**吸一切可破坏方块与生物（基岩/流体/空气不动，搬走的是原位那种方块）、**掉落物销毁**、强度与伤害随年龄递增（`RAMP_PER_TICK = 1/400`）、**一次性豁免**（§4.190②③）。③ **2 分钟硬上限** = 2400 tick ⇒ `level.explode(30 威力, TNT)`（§4.190④）。④ **顺手修**：坍缩时「先摘后播报」（旧顺序会把刚结束的黑洞写回存档 ⇒ 每次重启复活一次，§4.190⑤）；长寿命黑洞的 FX 环半径 `k` 夹到 [0,1]、心跳音量夹到 2.0。⑤ **真服务端探针 `Zf190Check` 16/0** + 回归 `Zf186Check` 20/0、`Zf188Check` 4/0。⑥ 门 `_zf190_verify.py` **22/0**、反证刀 **17/17**；并**跟平两道老门的判据**（`_zf186_verify.py` 的 fire 结构、`_zf188_verify.py` 的键数）。⑦ 语言键只加 1 个（五语种 690 / lzh 692）。⑧ **重打**：`release\\PotatoST-0.14.jar` = **{size} 字节 / sha1 `{sha}`**（class {cls}；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.190 |
"""

S9 = u"""### ZF190（0.14）黑洞召唤费修好了 + 新玩法「坍缩模式-危险」

**① 你报的 bug 修好了**：正常召唤现在**固定扣 8M 电力**（配置把容量改成 64M 也不会一次吃光，
剩的 56M 还在装置里）。闸门也跟着改成「**够这一次的费用**就能放」，不必先充满整条；
容量如果调到 8M 以下，费用按容量算（不然永远攒不够）。

**② 新模式「坍缩模式-危险」（Shift+左键循环：吞噬 → 牵引 → 坍缩 → 吞噬）**，模式名在动作栏是**红色**的：

| 它做什么 | 说明 |
| --- | --- |
| **无差别吸** | 附近**所有方块 + 所有生物**（玩家穿任意一件振金装备仍然免疫） |
| **销毁掉落物** | 被吸到的掉落物**直接销毁**（不掉落、不留痕） |
| **越吸越猛** | 吸引强度与伤害随存活时间递增（约**每 20 秒翻一倍**，2 分钟时约 7 倍） |
| **电价** | 召唤扣 **4M**，之后**每存在 1 tick 扣 50k FE**；**电没了黑洞当场消失** |
| **不损坏装置** | 它靠装置每 tick 供电 ⇒ 一次性那一刀对它豁免（装置坏了就没电可扣） |
| **不吃三样东西** | 空气 / 流体 / **不可破坏的方块**（基岩、屏障、命令方块…）；搬走的方块**保持原本种类** |

**③ 2 分钟保险丝**：任何黑洞活过 **2 分钟**会被销毁，并**真的炸一下 30 威力**（对照：原版 TNT 是 4）。

**④ 顺手修的一个老 bug**：坍缩的黑洞曾经被**写回存档**（每次重启都会「复活一下再坍缩」）；
现在一律先摘除、再播报。

**要你实测**（三条）：① 容量调 64M、充满放一次 ⇒ 看是不是只掉 8M；② Shift+左键切到红色的「坍缩模式-危险」，
放一个看它**无差别**吃方块/生物、掉落物消失、时间越久越猛；③ 不管它（或一直给它充电）到 2 分钟 ⇒ 那一记
30 威力的爆炸。⚠ 它真的很危险：**别在基地里放**。
"""

HAND47 = u"""47. **ZF190 的账（0.14：召唤费 bug + 第三模式「坍缩模式-危险」）**：① 用户原话见档案 §9；全部设计决定见 §4.190
    —— **`setEnergy(stack, 0)` 是「抽干整条」不是「收 8M 费用」**（ZF186 把容量做成可配之后这一行就炸了）、
    **费用按容量封顶**（容量下限 1M < 费用 8M）、**「一次性」对电费制模式豁免**、
    **「无差别」要自己划边界**（空气/流体/`defaultDestroyTime() < 0` 不动）、
    **硬上限要真爆炸**（`ExplosionInteraction.TNT`，30 威力）、**先摘后播报**（旧顺序会把结束的黑洞写回存档）。
    ② 探针 `Zf190Check` **16/0** + 回归 `Zf186Check` 20/0、`Zf188Check` 4/0；门 `_zf190_verify.py` **19/0**、
    反证刀 **17/17**；并跟平两道老门（`_zf186_verify.py` 的 fire 结构判据、`_zf188_verify.py` 的键数判据）。
    ③ ⚠ **探针假红三连全是判据自己的坑**：量电费要先关「一次性」；跑 600 tick 的洞要真 64M 装置
    （B2 把容量设成 8M 就半路没电）；**±140 格处 `isLoaded()` 为真但 `getEntitiesOfClass()` 看不到生物**
    （挪到 ±60 格）。**假红先打印诊断行**（活跃黑洞 / 装置电量 / 距离 / 可见生物数）。
    ④ 语言键只加 `gravity.mode.collapse` 一个（用户明说只许加显示模式的那个），红色是 `withStyle` 上的色。
"""

BIL_ZH = u"""
- **0.14 追加（ZF190）黑洞召唤费修好了 + 新模式「坍缩模式-危险」**：正常召唤**固定扣 8M**
  （容量改 64M 也不会一次吃光，这是你报的 bug）；新模式的**模式名是红色**的，能**无差别**吸所有方块与生物
  （振金免疫）、**销毁掉落物**、**越吸越猛**；它的电价是**召唤 4M + 每 tick 50k**，**没电就消失**，
  而且**不损坏装置**；任何黑洞活过 **2 分钟**会**真炸一下 30 威力**。⚠ 别在基地里放。
"""

BIL_EN = u"""
- **0.14 follow-up (ZF190) - the summon cost is fixed and there is a new "Collapse mode - DANGER":**
  one summon now costs a flat 8,000,000 FE (changing the buffer to 64M no longer eats all of it -
  that was the reported bug). The new mode's name is shown **in red**; it pulls **everything**
  (all blocks and mobs, vibranium still protects players), **destroys item drops**, and gets
  **stronger the longer it lives**. It costs 4M to summon plus 50k FE per tick and vanishes when the
  power runs out - and it never breaks the device. Any black hole older than **2 minutes** goes off
  with a real 30-power explosion. Do not use it next to your base.
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
    size, h = os.path.getsize(JAR), sha(JAR)
    z = zipfile.ZipFile(JAR)
    names = z.namelist()
    cls = len([n for n in names if n.endswith(u".class")])
    recipes = len([n for n in names if n.startswith(u"data/potato_s_t/recipe/") and n.endswith(u".json")])
    adv = len([n for n in names if n.startswith(u"data/potato_s_t/advancement/") and n.endswith(u".json")])
    keys_zh = len(json.loads(z.read(u"assets/potato_s_t/lang/zh_cn.json").decode("utf-8")))
    z.close()
    print(u"成品：%d 字节 / sha1 %s / class %d / 配方 %d / 进度 %d / 键 %d" % (size, h, cls, recipes, adv, keys_zh))

    v149 = read(V149)
    m = re.search(u'WANT_SHA = u?"([0-9a-f]{40})"', v149)
    old_sha = m.group(1) if m else u""
    m = re.search(u"WANT_SIZE = (\\d+)", v149)
    old_size = u"{:,}".format(int(m.group(1))) if m else u""
    fails = []

    def refresh(text):
        if old_sha:
            text = text.replace(old_sha, h)
        if old_size:
            for unit in (u" 字节", u" bytes", u" B"):
                text = text.replace(old_size + unit, u"{:,}{}".format(size, unit))
        text = re.sub(u"\\*\\*\\d+ classes, \\d+ advancements, \\d+ recipes\\*\\*",
                      u"**%d classes, %d advancements, %d recipes**" % (cls, adv, recipes), text)
        return text

    doc = read(DOC)
    if u"### 4.190 " not in doc:
        a = u"| ZF147 |"
        if doc.count(a) != 1:
            fails.append(u"档案 §5 表头锚点 %d 次" % doc.count(a))
        else:
            doc = doc.replace(a, S4 + a, 1)
    if u"| ZF190 |" not in doc:
        a2 = u"（class 410；§4.159 三处联动）。 | 见 §9 ｜ 见 §4.188 |\n"
        if doc.count(a2) != 1:
            fails.append(u"档案 ZF188 行尾锚点 %d 次" % doc.count(a2))
        else:
            row = ROW.replace(u"{size}", u"{:,}".format(size)).replace(u"{sha}", h).replace(u"{cls}", str(cls))
            doc = doc.replace(a2, a2 + row + u"\n", 1)
    if u"### ZF190（0.14）" not in doc:
        a3 = u"## 10. 备份策略"
        if doc.count(a3) != 1:
            fails.append(u"档案 §10 锚点 %d 次" % doc.count(a3))
        else:
            doc = doc.replace(a3, S9 + u"\n" + a3, 1)
    doc = refresh(doc)
    if write and not fails:
        io.open(DOC, "w", encoding="utf-8", newline=u"").write(doc)

    hand = read(HAND)
    if u"47. **ZF190 的账" not in hand:
        a4 = u"## 7. ZF146 这一轮的交接"
        if hand.count(a4) != 1:
            fails.append(u"交接 §7 锚点 %d 次" % hand.count(a4))
        else:
            hand = hand.replace(a4, HAND47 + u"\n" + a4, 1)
    hand = refresh(hand)
    if write and not fails:
        io.open(HAND, "w", encoding="utf-8", newline=u"").write(hand)

    # ── ① `_zf149_verify.py`：哈希/体积靶子 ──
    vn = re.sub(u'WANT_SHA = u?"[0-9a-f]{40}"', u'WANT_SHA = u"%s"' % h, v149, count=1)
    vn = re.sub(u"WANT_SIZE = \\d+", u"WANT_SIZE = %d" % size, vn, count=1)
    if vn == v149:
        if (u'WANT_SHA = u"%s"' % h) in v149:
            print(u"  （_zf149_verify.py 的靶子已经就是这份成品，跳过）")
        else:
            fails.append(u"_zf149_verify.py：靶子没换到")
    elif write and not fails:
        io.open(V149, "w", encoding="utf-8", newline=u"").write(vn)

    # ── ② `_zf186_verify.py` 的 B2 跟平：fire() 从「扣光」变成「扣这一次的费用」──
    v186 = read(V186)
    old186 = (u'    b2 = (u"setEnergy(stack, 0);" in fire\n'
              u'          and u"if (PotatoSTConfig.oneShotBlackHole()) {" in fire\n'
              u'          and fire.index(u"if (PotatoSTConfig.oneShotBlackHole()) {") < fire.index(u"hurtAndBreak"))')
    new186 = (u'    # 0.14 ZF190 跟平：扣电从「抽干整条」改成「扣这一次的召唤费」，一次性那一刀照旧受\n'
              u'    # oneShotBlackHole() 管（坍缩模式的豁免由 `_zf190_verify.py` 单独钉）。判据强度没降。\n'
              u'    b2 = (u"setEnergy(stack, getEnergy(stack) - cost);" in fire\n'
              u'          and u"if (PotatoSTConfig.oneShotBlackHole()" in fire\n'
              u'          and fire.index(u"if (PotatoSTConfig.oneShotBlackHole()") < fire.index(u"hurtAndBreak"))')
    if old186 in v186:
        v186 = v186.replace(old186, new186, 1)
        print(u"  `_zf186_verify.py`：B2 判据已跟平（扣费用 + 一次性条件）")
        if write and not fails:
            io.open(V186, "w", encoding="utf-8", newline=u"").write(v186)
    elif new186 in v186:
        print(u"  `_zf186_verify.py`：B2 已经是新判据，跳过")
    else:
        fails.append(u"_zf186_verify.py：B2 锚点找不到（跟平失败）")

    # ── ③ `_zf188_verify.py` 的键数跟平（689/691 → 690/692）──
    v188 = read(V188)
    new188 = v188.replace(u'{u"zh_cn.json": 689, u"en_us.json": 689, u"lzh.json": 691,\n'
                          u'                   u"ja_jp.json": 689, u"ru_ru.json": 689}',
                          u'{u"zh_cn.json": 690, u"en_us.json": 690, u"lzh.json": 692,\n'
                          u'                   u"ja_jp.json": 690, u"ru_ru.json": 690}')
    if new188 != v188:
        print(u"  `_zf188_verify.py`：C1 键数已跟平（690 / lzh 692）")
        if write and not fails:
            io.open(V188, "w", encoding="utf-8", newline=u"").write(new188)
    elif u'{u"zh_cn.json": 690' in v188:
        print(u"  `_zf188_verify.py`：键数已经是 690，跳过")
    else:
        fails.append(u"_zf188_verify.py：键数锚点找不到（跟平失败）")

    ann = read(ANN)
    if u"## New in 0.14 ZF190" not in ann:
        a5 = u"## New in 0.14 ZF188 - Configured takes over the Config button when it is installed"
        if ann.count(a5) != 1:
            fails.append(u"公告 ZF188 段锚点 %d 次" % ann.count(a5))
        else:
            block = (u"## New in 0.14 ZF190 - A flat summon price, and a third mode that eats everything\n\n"
                     u"- **Fixed: one summon now costs a flat 8,000,000 FE** instead of draining the whole\n"
                     u"  energy bar. With the buffer configured to 64M FE one black hole used to eat all\n"
                     u"  64M; now it costs 8M and the rest stays in the device. The gate changed too: you\n"
                     u"  need at least the price to fire, not a full bar; if the buffer is configured below\n"
                     u"  8M the price is capped to the buffer so a small device can still fire.\n"
                     u"- **New mode: Collapse mode - DANGER** (cycle modes with sneak + left-click; its name\n"
                     u"  is shown **in red**):\n"
                     u"  - pulls **everything** nearby - every block and every mob - instead of a single block\n"
                     u"    type. Vibranium gear still protects players.\n"
                     u"  - **item drops that get caught are destroyed.**\n"
                     u"  - **pull strength and damage grow with age** (roughly doubling every 20 seconds).\n"
                     u"  - costs **4,000,000 FE to summon and 50,000 FE per tick**; when the device runs out\n"
                     u"    of power the black hole simply disappears. Because it is powered per tick this\n"
                     u"    mode never breaks the device.\n"
                     u"  - it leaves air, fluids and unbreakable blocks (bedrock, barriers, command blocks)\n"
                     u"    alone, and blocks keep their own type when they are moved.\n"
                     u"- **A black hole older than 2 minutes is destroyed with a real 30-power explosion**\n"
                     u"  (for comparison, vanilla TNT is 4).\n"
                     u"- Fixed along the way: a collapsing black hole was written back into the save file and\n"
                     u"  could come back for a tick on every server start; it is now removed before saving.\n"
                     u"- Measured on a real server (16 checks, all green): a 64M buffer keeps 56M after one\n"
                     u"  summon; 4M drops to 3.5M after 10 ticks; cutting the power makes the hole vanish;\n"
                     u"  stone, dirt and planks are all moved in collapse mode while bedrock stays put; a\n"
                     u"  dropped diamond stack is destroyed; at equal distance an aged hole gives a cow 1.77\n"
                     u"  speed versus 0.72 for a fresh one and hits for 10.0 versus 4.2 damage; after 2400\n"
                     u"  ticks the hole is gone, a marker block is blown up and a cow 5 blocks away is hit.\n"
                     u"- **Download:** `release/PotatoST-0.14.jar` - **{size} bytes**, sha1 **`{sha}`**.\n\n"
                     ).format(size=u"{:,}".format(size), sha=h)
            ann = ann.replace(a5, block + a5, 1)
    ann = refresh(ann)
    if write and not fails:
        io.open(ANN, "w", encoding="utf-8", newline=u"").write(ann)

    bil = read(BIL)
    if u"0.14 追加（ZF190）" not in bil:
        az = u"  5 s charge-up is 100 ticks.\n"
        ae = u"  Note: with Configured installed, NeoForge's own screen is no longer reachable - turn off Configured's\n"
        # ⚠ 双语文件里 ZF188 那两段的结尾（zh 在前、en 在后）
        az2 = u"  ⚠ 装了它之后，NeoForge 自带那个界面就点不到了 —— 想回去就在 Configured 里关掉强制接管或卸掉它。\n"
        ae2 = u"  forced menu or remove it if you want it back.\n"
        if bil.count(az2) != 1 or bil.count(ae2) != 1:
            fails.append(u"双语公告锚点 zh=%d en=%d" % (bil.count(az2), bil.count(ae2)))
        else:
            bil = bil.replace(az2, az2 + BIL_ZH, 1)
            bil = bil.replace(ae2, ae2 + BIL_EN, 1)
    bil = refresh(bil)
    if write and not fails:
        io.open(BIL, "w", encoding="utf-8", newline=u"").write(bil)

    print(u"模式：%s ｜ 失败 = %d" % (u"落盘" if write else u"干跑", len(fails)))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
