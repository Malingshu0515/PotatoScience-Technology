# -*- coding: utf-8 -*-
u"""_zf111_docs.py —— ZF111 的文档：§5 行 + §9 小节（0.11 星璨钢配方）

锚点要求正好命中 1 次，找不到/找到多处就报错退出。⚠ 中文里一律用「」。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW5 = (u"| ZF111 | **新建 `zf111_pre`**（103 份改前件：3 个既有 Java（`AlloySmelterRecipes`/"
        u"`AlloySmelterBlockEntity`/`MachineRecipes`）+ 四份 lang + **全部常驻校验脚本**（一把全抄）"
        u"+ 2 份文档 + 旧成品 jar 与 `.sha1`） | 0.11：**星璨钢的合金冶炼炉配方**。用户原话："
        u"「星璨钢加合金冶炼配方 下界合金锭+4高碳钢+钴锭+银锭+铜锭 再消耗1个深层钴矿石 1个末影水晶 "
        u"产出三个星璨钢钢 12000FE/t」。① **两处顺带改**（不改就实现不了）：**消耗槽第一次放开**"
        u"（ZF49 立的「以后出石墨电极那种东西再放开」）+ **每 tick 耗电第一次不是 800** ⇒ 方块实体改读"
        u"`smelt.energyPerTick()/durationTicks()`、静态守卫改读新的纯 int 常量 "
        u"`MAX_ENERGY_PER_TICK = 12000`（static 块里不能碰懒加载的配方表，§4.1）；"
        u"② **下界合金锭/铜锭走 NeoForge 自带的 `c:ingots/netherite`、`c:ingots/copper`**"
        u"（解包核过）—— 标签要是空的配方永远开不了工而静态检查看不出来，探针专门查了；"
        u"③ ⚠ **时长用户没给** ⇒ 沿用本机规格 30 秒 ⇒ 一件 **7,200,000 FE**（满缓冲 32768 只够 2.7 秒，"
        u"要持续供电）；④ **一个语言键都没加/删**（键数仍 408）⇒ 17 份键数耦合的校验器一份都不用动，"
        u"只改了两个**值**（消耗槽标签 + 介绍的脚注），摆放图那几行逐字未动（`_zf52/_zf55` 复跑仍绿） |")

SEC9 = u"""### ZF111（0.11）星璨钢的合金冶炼炉配方（**消耗槽第一次放开**）—— **未打包**

原话：「星璨钢加合金冶炼配方 下界合金锭+4高碳钢+钴锭+银锭+铜锭 再消耗1个深层钴矿石
1个末影水晶 产出三个星璨钢钢 12000FE/t」

| 输入（5 个输入槽，只收锭） | 消耗（2 个消耗槽） | 产物 | 耗电 |
|---|---|---|---|
| 下界合金锭 ×1 ＋ 高碳钢 **×4** ＋ 钴锭 ×1 ＋ 银锭 ×1 ＋ 铜锭 ×1 | 深层钴矿石 ×1 ＋ 末影水晶 ×1 | **星璨钢锭 ×3** | **12000 FE/t** |

**⚠ 时长你没给** ⇒ 沿用本机规格 **30 秒（600 tick）** ⇒ 一件总耗电 **12000 × 600 = 7,200,000 FE**。
这个数是**我按本机规格补的**（要改是一个参数，说一声）。顺带把账算给你看：机器储能 32768
⇒ 满缓冲只够 **2.7 秒**，也就是说星璨钢必须**持续供上 12000 FE/t** 才跑得完一轮
（低级发电机 100 FE/t ⇒ 得 120 台；合金炉自己的接线口能吃满就行）。

**两处顺带改（不改就实现不了这条配方）**：

1. **消耗槽第一次放开**（ZF49 立机器时说的"以后出类似于沉浸电弧炉石墨电极的东西"再放开）——
   `isItemValid` 从**恒 false** 改成"**某条配方真的会消耗它**才收"（垃圾照旧进不去，
   玩家也不能拿消耗槽当第二个背包）；
2. **每 tick 耗电第一次不是 800** ⇒ 方块实体不再读全局 `ENERGY_PER_TICK`，
   改成读**这条配方自己的** `energyPerTick()` / `durationTicks()`（ZF62 写表时就说过
   "多条配方各带各的"，只是当时只有一条配方没人去动）。ZF42 那条"单 tick 耗电不能超储能"
   的静态守卫改读新的**纯 int 常量** `MAX_ENERGY_PER_TICK = 12000` ——
   不能在 static 块里碰懒加载的配方表（§4.1 那个启动崩溃）。

**下界合金锭与铜锭走的是 NeoForge 自己提供的 `c:ingots/netherite` / `c:ingots/copper`**
（解包 `neoforge-21.1.235.jar` 核过：`data/c/tags/item/ingots/` 里有这两个文件；
我们自己的 `c:ingots/` 只有 9 份、里面没有这两种）。这条是本轮**最危险**的地方：
标签要是空的或没绑上，配方就**永远开不了工**，而静态检查看不出来（表里写的只是个 TagKey）
⇒ 探针专门查了"非空 + 认得到预期物品"。

**证据**：

- [x] 探针 `Zf111Check.java`（真游戏 `runServer`）：**51 项全绿**，报告 `build\\zftools\\_zf111_probe_utf8.txt`；
      实测过的：五个锭标签**非空且认得到预期物品**（含原版下界合金锭/铜锭）/ 配方表逐项
      （5 输入含高碳钢 ×4、2 消耗品、产物 ×3、12000 FE/t、600 tick、7,200,000 FE）/
      **消耗槽门禁**（收钴矿石与末影水晶、不收圆石；输入槽仍只收锭）/
      **缺消耗品 ⇒ 不开工且一度电都不扣** / 只放一半消耗品也不开工 /
      齐了跑满 600 tick **正好扣 7,200,000 FE**、输入与消耗按数目扣干净、输出正好 3 个星璨钢锭 /
      **老两条配方仍是 800 FE/t（没被新字段弄坏）**
- [x] 探针存档：`build\\zftools\\check\\Zf111Check.java`（18152 B，sha1 `add48fb5…`，**先抄后删**）
- [x] `build\\zftools\\_zf111_verify.py`：常驻校验 **85 项**，其中一条是"四语言键集合与改前件
      **逐位相同**、只动了两个值、摆放图那几行**逐字未动**" —— **本环一个语言键都没加/删，键数仍是 408**
- [x] 反证刀 K123~K132（见汇报；每把都是"改一处语义 ⇒ 校验器必须 FAIL ⇒ 逐字节还原 ⇒ 回到全绿"）
- [x] 往轮的 `_zf52_verify.py`（介绍图逐格）与 `_zf55_verify.py`（介绍文案）**复跑仍绿**
- [x] 换行：本轮碰过的文件全 LF（§4.8）

**要你实测的**（进游戏）：摆一台成型合金炉，5 个输入槽放下界合金锭 / 高碳钢 ×4 / 钴锭 / 银锭 / 铜锭，
**2 个消耗槽**放深层钴矿石 + 末影水晶，接够电（≥12000 FE/t）⇒ 30 秒后输出槽里 3 个星璨钢锭。
**缺消耗品时它不会开工**（进度一动不动、也不扣电）—— 这是设计，不是 bug。

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF103 那版 `90510e18…`。

"""


def main():
    fails = []
    text = io.open(DOC, encoding="utf-8", newline="").read()
    if u"| ZF111 |" in text:
        fails.append(u"§5 行已经写过了")
    lines = text.split(u"\n")

    idx_row = [i for i, l in enumerate(lines) if l.startswith(u"| ZF109 |")]
    if len(idx_row) != 1:
        fails.append(u"§5 锚点 | ZF109 | 命中 %d 次" % len(idx_row))
    idx_sec = [i for i, l in enumerate(lines) if l.startswith(u"## 10. 备份策略")]
    if len(idx_sec) != 1:
        fails.append(u"§9 锚点（## 10.）命中 %d 次" % len(idx_sec))
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1

    sec_lines = SEC9.split(u"\n")
    if sec_lines and sec_lines[-1] == u"":
        sec_lines = sec_lines[:-1]
    out = (lines[:idx_row[0] + 1] + [ROW5]
           + lines[idx_row[0] + 1: idx_sec[0]] + sec_lines + [u""]
           + lines[idx_sec[0]:])
    after = u"\n".join(out)
    if u"\r" in after:
        fails.append(u"出现了 CR")
    for h in (u"| ZF111 |", u"### ZF111（0.11）"):
        if after.count(h) != 1:
            fails.append(u"核对 %r 出现 %d 次" % (h, after.count(h)))
    if u"7,200,000" not in after:
        fails.append(u"核对：档案里没写 7,200,000")
    if after.index(u"| ZF111 |") > after.index(u"### ZF111（0.11）"):
        fails.append(u"§5 行跑到 §9 后面去了")
    if fails:
        print(u"失败项 = %d（**没落盘**）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(after)
    print(u"档案：%d 行 → %d 行" % (len(lines), len(after.split(u"\n"))))
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
