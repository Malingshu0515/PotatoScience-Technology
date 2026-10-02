# -*- coding: utf-8 -*-
u"""_zf169_docs.py —— ZF169 的档案两段（台账行 + §9）+ 贴图清单追记（幂等）"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
ARCH = os.path.join(ROOT, r"docs\开发档案.md")
TEXL = os.path.join(ROOT, r"docs\贴图清单.md")

LEDGER = u"""| ZF169 | **没建备份**（⚠ 本轮开工时上下文已经很紧：直接改 + 每步编译；改前状态由 ZF167/ZF168 那两次提交兜底 —— **这条要如实记着**，别当成"本来就不需要备份"） | **0.13+：矿物探测器 + 手持式引力装置**（用户原话两段：①「加一个【矿物探测器】……本身有能量条（黄色）（1200FE）右键识别最近的（xz3x3区块y45格内寻找 没有则提示附近没有任何矿物）矿物并标注出来（这个你自由发挥 是做成矿透那样的直接穿过别的方块显示矿物 或者 title/聊天栏告诉玩家矿物的方位都可以）右键一次消耗600FE」；②「引力装置配方；【锂电池】【磁铁块】【锂电池】，【星璨钢】【信标】【星璨钢】，【稳定金属块】【浅层钻石原矿】【稳定金属块】作用；储能8mFE 副手放一个方块 长按右键开始蓄力 25s后召唤出一个黑洞 把3x3区块内所有副手方块 全部吸引到黑洞的位置（单次最多1200个方块）单次消耗全部8m电力并损坏 （黑洞还会吸引周围的生物 进入黑洞范围内会持续受到虚空伤害）黑洞特效竭尽你自己的知识储备 尽你最大可能给我做的炫酷一点 不需要你省token」）。① **本工程第一次做"带储能的物品"**：能量写在物品自己的 `CustomData`（不动注册表）+ NeoForge 物品能量能力（`RegisterCapabilitiesEvent.registerItem`），物品条走原版 `isBarVisible/getBarWidth/getBarColor`（黄 `0xFFE0C040`，引力装置充满转紫）；② 探测器：「y45格内」按 **y ≤ 45** 读（我的读法，已挂牌）；标注走**聊天栏 + 标题 + 方位箭头 + 距离 + 坐标 + 目标处粒子柱**（矿透式穿墙高亮要自写渲染层，本轮没做，理由写在类注释里）；扫的是 NeoForge 的 **`c:ores` 标签**（别的模组的原矿挂了标签就自动能探到）；③ 引力装置：副手方块 = 要吸的那一种，长按右键蓄力 **500 tick**（粒子往里收 + 音调随进度升 + 每 10 tick 报百分比），蓄满扣光 **8,000,000 FE** 并**把装置耐久打空（当场损坏）**；④ 黑洞（`BlackHoleManager`，静态管理器 + 每 tick，与 ZF153 冲击波同一条路）：3×3 区块内同种方块按"由近到远、每 tick 24 个"的预算搬过来（上限 **1200**），**真的码在黑洞脚下**（金螺旋分层，只放在可替换处）；生物被拉向奇点（切向分量让它绕转），进 **6 格**内每 **10 tick** 吃一次 `fellOutOfWorld`（原版"虚空"伤害类型）；特效 = 三层吸积盘（SOUL_FIRE_FLAME / END_ROD / ELECTRIC_SPARK，各带倾角反向自转）+ 内落流粒子雨 + 视界光环（REVERSE_PORTAL / PORTAL 双层）+ 引力透镜光弧（随时间收缩）+ 核心闪白 + 生成时的 SONIC_BOOM 冲击环 + 坍缩大爆炸；音效 = 生成 `END_PORTAL_SPAWN`+`PORTAL_TRIGGER`、心跳 `WARDEN_HEARTBEAT`、充能 `RESPAWN_ANCHOR_CHARGE`、坍缩 `GENERIC_EXPLODE`+`WARDEN_SONIC_BOOM`（⚠ 1.21.1 **没有** `END_CRYSTAL_DEATH` 这个音效 —— 照着旧版本名字写会编译不过，已改用音爆）；⑤ 语言 **620 → 645 键** ×4（lzh 622 → **647**）⇒ **40 份常驻门** + 交接文档一起重定靶；⑥ 成品重打：`PotatoST-0.13.jar` = **6,057,289 字节 / sha1 `31b47539ade37ddb578437be36e598b3494ab0b8`**（⚠ 作废 `13f72c06463117e45281f3adc4b4b8ed651543bd`）。⚠⚠ **本轮没跑真服务端探针**（上下文耗尽）：编译通过、静态判据与门都跟平了，但"右键到底扣没扣 600 FE、黑洞真吸不吸"**只有源码级证据**，要下一轮补探针 —— 已写进 §9 的"待验" | 见 §9 |"""

SECTION9 = u"""
### ZF169（0.13+）矿物探测器 + 手持式引力装置 —— **待你实测（本轮没跑探针）**

⚠ **先把话说在前面**：这一轮我**没有**跑真服务端探针（上下文用尽了，跑探针要起服 + 写
`Zf169Check` + 反复迭代）。所以下面的"能干什么"是**按源码写的**，编译通过、门也跟平了，
但**行为级的证据缺席** —— 请你在游戏里按下面几条过一遍，不对的地方我下一轮修。

#### 一、矿物探测器 `potato_s_t:ore_detector`

| 项 | 值 |
|---|---|
| 配方 | 磁铁 / 铁锭 / 磁铁 ・ 铜线轴 / 电容 / 铜线轴 ・ 空 / 木棍 / 空 |
| 储能 | **1200 FE**（物品条黄色），一次扫描 **600 FE** ⇒ 满电正好两次 |
| 范围 | 以你所在区块为中心的 **3×3 区块**、**y ≤ 45**（⚠ "y45格内"我按"45 层以下"读；要改成"上下 45 格"就是一个常量） |
| 找什么 | 挂了 NeoForge **`c:ores`** 标签的方块（原版各种矿 + 别的模组挂了这个标签的原矿） |
| 怎么标 | 标题 + 聊天栏：**最近那一处**的名字 / 方位箭头 / 距离 / 坐标；后面再列最多 2 处"附近还有"；目标处升起粒子柱 |
| 找不到 | 标题一句「**附近没有任何矿物**」（你给的原话，一个字没改）+ 聊天栏一行说明 600 FE 已消耗 |

⚠ 没做**矿透式穿墙高亮**（那要自己写渲染层 + 每帧发包，本轮验不到画面）；
要的话下一轮做，方案我先写在这儿：`RenderLevelStageEvent` 里对候选矿物画自发光轮廓。

#### 二、手持式引力装置 `potato_s_t:gravity_device`

| 项 | 值 |
|---|---|
| 配方 | 锂电池 / 磁铁块 / 锂电池 ・ 星璨钢锭 / 信标 / 星璨钢锭 ・ 稳定金属块 / **浅层钻石原矿** / 稳定金属块 |
| ⚠ 材料 | 盘上**没有「浅层钻石原矿」这件方块**（`ModBlocks` 里与 diamond 有关的注册是空的）⇒ 我暂时用了**原版 `minecraft:diamond_ore`**。**请告诉我那件方块的真名**（或者它还没做），我立刻换 |
| 储能 | **8,000,000 FE**（充满时物品条转紫）；用充电站/别的模组的充电器充（本装置实现了 NeoForge 物品能量能力） |
| 怎么用 | 副手放**要吸的那种方块**（空手/非方块会提示）⇒ 主手按住右键 **25 秒** ⇒ 扣光 8 MFE、装置**当场损坏**、原地开黑洞 |
| 中断 | 中途松手 = 作废（不扣电）；蓄力中副手方块被拿走 = 立刻中断并提示 |
| 黑洞 | 20 秒；3×3 区块内同种方块被逐个搬过来（每 tick 24 个、上限 **1200**，**真的码在黑洞脚下**成一座螺旋小丘）；生物被拉向奇点并绕转，进 **6 格**每 0.5 秒吃一次**虚空伤害**（原版 `fellOutOfWorld`） |
| 特效 | 三层反向自转吸积盘 + 内落粒子雨 + 双层视界光环 + 收缩的透镜光弧 + 核心闪白 + 生成冲击环 + 坍缩大爆炸；音效五套（生成 / 心跳 / 充能 / 坍缩 / 中断） |

#### 三、下一轮必须补的（我自己列，不藏）

1. **真服务端探针 `Zf169Check`**：仪器扣电与"没矿"那句；引力装置的蓄力→扣 8 MFE→损坏→黑洞
   真的把方块搬走（数出来的）、生物真的被拉、虚空伤害真的掉了血。
2. 黑洞目前**不存档**（服务器重启就没了）—— 要"跨重启"就得做成实体，下一轮再定。
3. 搬运是**每 tick 现扫**（就近的壳）：方块种类rare时很省，但"整片同种方块"（比如 1200 个石头）
   会连续 50 tick 满预算跑 —— 真机上要看一次 TPS（探针里加一条 tick 耗时断言）。
"""

TEXADD = u"""
### ZF169 追记：矿物探测器 / 手持式引力装置（**两张待画**）

| 项 | 值 |
|---|---|
| 矿物探测器 | `models/item/ore_detector.json` **借原版** `minecraft:item/compass`（待画 `textures/item/ore_detector.png`） |
| 手持式引力装置 | `models/item/gravity_device.json` **借原版** `minecraft:item/ender_eye`（待画 `textures/item/gravity_device.png`） |

⚠ 两张都是占位；把 16×16 的图丢进 `textures/item/`（PNG，名字就用上面那两个）我接上。
"""

fails = []


def check(label, ok):
    print(u"  [%s] %s" % (u"OK" if ok else u"!!", label))
    if not ok:
        fails.append(label)


def main():
    arch = io.open(ARCH, encoding="utf-8").read()
    if u"| ZF169 |" in arch:
        print(u"  [幂等] 台账行已在")
    else:
        anchor = u"| ZF168 |"
        if anchor in arch:
            i = arch.rindex(anchor)
            j = arch.index(u"\n", i) + 1
            arch = arch[:j] + LEDGER + arch[j:]
        else:
            anchor2 = u"| ZF167 |"
            i = arch.rindex(anchor2)
            j = arch.index(u"\n", i) + 1
            arch = arch[:j] + LEDGER + arch[j:]
        io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(arch)
        check(u"台账行已加", True)
    arch = io.open(ARCH, encoding="utf-8").read()
    if u"### ZF169（0.13+）矿物探测器" in arch:
        print(u"  [幂等] §9 已在")
    else:
        if not arch.endswith(u"\n"):
            arch += u"\n"
        io.open(ARCH, "w", encoding="utf-8", newline=u"\n").write(arch + SECTION9)
        check(u"§9 已追加", True)
    tex = io.open(TEXL, encoding="utf-8").read()
    if u"ZF169 追记" in tex:
        print(u"  [幂等] 贴图清单已在")
    else:
        if not tex.endswith(u"\n"):
            tex += u"\n"
        io.open(TEXL, "w", encoding="utf-8", newline=u"\n").write(tex + TEXADD)
        check(u"贴图清单追记已加", True)
    print(u"失败项 = %d" % len(fails))
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main())
