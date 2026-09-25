# -*- coding: utf-8 -*-
u"""_zf112_docs.py —— ZF112 的文档：§5 行 + §9 小节（0.11 锂电池构造间 + 三元锂配方）"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW5 = (u"| ZF112 | **新建 `zf112_pre`**（115 份改前件：8 个既有 Java（`ModBlocks`/`ModItems`/"
        u"`ModMenus`/`PotatoST`/`PotatoSTClient`/`StatusLampPart`/`MachineRecipes`/"
        u"`PotatoSTJeiPlugin`）+ 四份 lang + `recipe/lithium_battery.json` + 挖掘标签 "
        u"+ **全部常驻校验脚本**（一把全抄）+ 4 份文档 + 旧成品 jar 与 `.sha1`） | 0.11："
        u"**锂电池构造间（新机器）+ 三元锂配方改动**。用户原话：「加一个锂电池构造间 通入硫酸 "
        u"放入粗锰/粗铝and 镍/粗镍 and 碳酸锂 and钴/粗钴 每t消耗10mb硫酸 30s后产出一个锂电池原件 "
        u"不消耗电 三元锂配方里的碳酸锂改成锂电池原件 金属板统一换成纸 别的电容什么的不变」。"
        u"① **新中间物品 `lithium_battery_component`（锂电池原件）**—— 不新增它的话，三元锂配方会"
        u"自我循环（方块自己当自己的材料）；② **新机器不吃电**（用户末句「不消耗电」）：只挂物品 + "
        u"流体两个能力，**没有**能量能力（与加氢脱硫反应仓同一条路）；四个输入槽各认「或」"
        u"（粗锰/粗铝、镍锭/粗镍、碳酸锂、钴锭/粗钴），硫酸每 tick 10 mB、一炉 600 tick = **6000 mB**，"
        u"四样原料**最后一 tick** 才各扣 1；③ 新状态码 **17 硫酸不够 / 18 原料不齐**；"
        u"④ 三元锂配方：碳酸锂 → 锂电池原件、铝板+铜板 → **纸**（6 格），电容与一般金属块不动；"
        u"⑤ 四语言 +9 键（408 → **417**）⇒ 19 份键数耦合的校验器一起重定目标；"
        u"⚠ **探针当场抓到一个真 bug**：产物原本用 `ItemStackHandler#insertItem` 写输出槽，"
        u"而那个方法**会走 `isItemValid`**（输出槽按设计「只取不放」恒 false）⇒ 料扣了、货没出来 —— "
        u"改成直接写槽位（见 §4.83）；罐容量也从我定的 2000 改成 **8000**（探针：2000 装不下一炉的 6000） |")

SEC9 = u"""### ZF112（0.11）锂电池构造间：把硫酸变成锂电池原件（**新机器**）+ 三元锂配方改动 —— **未打包**

原话：「加一个锂电池构造间 通入硫酸 放入粗锰/粗铝and 镍/粗镍 and 碳酸锂 and钴/粗钴
每t消耗10mb硫酸 30s后产出一个锂电池原件 不消耗电
三元锂配方里的碳酸锂改成锂电池原件 金属板统一换成纸 别的电容什么的不变」

**① 为什么要新增「锂电池原件」这个物品**：「三元锂配方」就是**方块** `lithium_battery`
（显示名「三元聚合物锂电池」）的合成配方 —— 直接把碳酸锂换成"锂电池"会让**方块自己当自己的材料**
（循环配方，永远做不出来）。所以新机器产出的是一件**中间件**：`lithium_battery_component`
（显示名「锂电池原件」），方块配方再拿它去合成。这也是我理解你那句「改成锂电池原件」的落点。

**② 机器怎么开工**：

| | |
|---|---|
| 四个输入槽（每个槽认「或」） | 粗锰/粗铝 · 镍锭/粗镍 · 碳酸锂 · 钴锭/粗钴（**各 1 个**，最后一 tick 才扣） |
| 液体 | 硫酸：**每 tick 10 mB**，一炉 30 秒 = 600 tick ⇒ **一炉 6000 mB** |
| 产物 | **1 个锂电池原件**（30 秒一炉） |
| 电 | **不耗电**（用户末句「不消耗电」）⇒ 这台机器**没有能量能力**，靠化学 |
| 罐 | **8000 mB**（我定的：装满一罐正好跑完一炉还剩 2000 —— 见下面那条探针抓到的账） |

**③ 三元锂配方（`recipe/lithium_battery.json`）改成**：

| | 改前 | 改后 |
|---|---|---|
| 中间那格（L） | 碳酸锂 | **锂电池原件** |
| A 与 P（4 格铝板 + 2 格铜板） | 铝板 / 铜板 | **纸**（`minecraft:paper`，共 6 格） |
| C / M | 电容 / 一般金属块 | **不动**（用户原话「别的电容什么的不变」） |

**④ 探针当场抓到的两件事（都是我的错，不是用户的）**：

1. **产物写不进去**：第一版用 `ItemStackHandler#insertItem(OUTPUT_SLOT, …)` 出货 ——
   这个方法**会走 `isItemValid`**，而输出槽按设计是"只取不放"（`isItemValid` 恒 false）
   ⇒ 表现是**料扣了、货没出来**（一炉跑完输出槽还是空的）。改成直接 `setStackInSlot`
   （能不能放由 `canOutput()` 先保证），与合金炉 `addOutput()` 同一条做法。
2. **罐容量 2000 装不下一炉**：一炉要 6000 mB，我最初按"够缓冲 200 tick"取的 2000
   ⇒ 玩家必须先架好持续供酸的管道才敢开机。改成 **8000 mB**（一炉 + 2000 余量）。

**⑤ 证据**：

- [x] 探针 `Zf112Check.java`（真游戏）：**50 项全绿**，`build\\zftools\\_zf112_probe_utf8.txt`；
      含"**没有**能量能力"、「或」槽门禁（槽 0/1/3 两支都认、槽 2 只认碳酸锂、输出槽不收）、
      缺一样原料 ⇒ 进度 0 且**一滴酸不扣**、断酸 ⇒ 状态 17 且进度原地不动、
      跑满 600 tick 正好扣 **6000 mB** 酸、四样各扣 1、输出正好 1 个锂电池原件、存档往返一致、
      以及**三元锂配方真的加载成了"纸 ×6 + 原件 ×1 + 电容 ×1 + 一般金属块 ×1"**
- [x] 探针存档：`build\\zftools\\check\\Zf112Check.java`（13991 B，sha1 `2a89457b…`，先抄后删）
- [x] `_zf112_verify.py`：常驻校验（含**每个方块物品都进了创造页**那条 §4.82 的老账）
- [x] 反证刀（见汇报）
- [x] 四语言 408 → **417**（9 个新键）；19 份键数耦合校验器的锚点一起重定目标

**要你实测的**：摆一台（配方：铝板 / 电容 / 铝板、流体管道 / 一般金属块 / 流体管道、
铁板 / 加热装置 / 铁板 —— ⚠ **这条机器配方是我照家族风格替你写的，你没给**，说一声就改），
灌硫酸、四样料各放一份 ⇒ 30 秒后输出槽出 1 个锂电池原件；再拿它去合三元聚合物锂电池
（纸 ×6 + 原件 + 电容 + 一般金属块）。

**成品**：**本轮没有新成品** —— `release\\PotatoST-0.11.jar` 仍是 ZF103 那版 `90510e18…`。

"""


def main():
    fails = []
    text = io.open(DOC, encoding="utf-8", newline="").read()
    if u"| ZF112 |" in text:
        fails.append(u"§5 行已经写过了")
    lines = text.split(u"\n")
    idx_row = [i for i, l in enumerate(lines) if l.startswith(u"| ZF111 |")]
    idx_sec = [i for i, l in enumerate(lines) if l.startswith(u"## 10. 备份策略")]
    if len(idx_row) != 1:
        fails.append(u"§5 锚点命中 %d 次" % len(idx_row))
    if len(idx_sec) != 1:
        fails.append(u"§9 锚点命中 %d 次" % len(idx_sec))
    if fails:
        for f in fails:
            print(u"  !! " + f)
        return 1
    sec_lines = SEC9.split(u"\n")
    if sec_lines and sec_lines[-1] == u"":
        sec_lines = sec_lines[:-1]
    out = (lines[:idx_row[0] + 1] + [ROW5] + lines[idx_row[0] + 1: idx_sec[0]]
           + sec_lines + [u""] + lines[idx_sec[0]:])
    after = u"\n".join(out)
    if u"\r" in after:
        fails.append(u"有 CR")
    for h in (u"| ZF112 |", u"### ZF112（0.11）"):
        if after.count(h) != 1:
            fails.append(u"%r 出现 %d 次" % (h, after.count(h)))
    if fails:
        print(u"失败项 = %d（没落盘）" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1
    io.open(DOC, "w", encoding="utf-8", newline=u"\n").write(after)
    print(u"档案：%d 行 → %d 行" % (len(lines), len(after.split(u"\n"))))
    print(u"失败项 = 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
