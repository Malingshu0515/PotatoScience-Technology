# -*- coding: utf-8 -*-
"""_zf56_docs.py —— ZF56 档案落笔（用户纠正：4×5×4 是成型后的合金炉，不是主控本体）

四处插入：① §4.33（两个"运行时改方块状态"的坑）② §5 ZF56 行 ③ §9 待办 ④ §12.15 更正

⚠ 这个脚本类炸过 3 次（中文引号写成 ASCII 引号），这里一律用 u''' ... ''' + 「」。
"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

S433 = u'''### 4.33 【方法论】"改模型"会顺手改掉方块状态，而方块状态一动就触发 `onPlace`（0.10 ZF56）

用户纠正：「**不是主控变成4x5x4是合金炉！合金炉成型后模型！**」——
ZF54 把 4×5×4 的 OBJ 直接挂在 `facing` 变体上，于是**一放下控制器就是个 4×5×4 大盒子**。
改法本身很简单（加 `formed` 方块状态：`false` 用小方块模型、`true` 才用 OBJ），
但这一改把"模型层"和"状态层"接在了一起，冒出两个**只在运行时改方块状态才会出现**的坑：

| 坑 | 症状（都实测过） | 根因 | 规矩 |
|---|---|---|---|
| **拆解时自己重新成型** | 反证实测：把 `setFormed(false)` 从 `try` 里挪到 `finally` 之后 ⇒ 扳手一拆，**整台机器当场自己装回去**，残留 **67 格**部件格 | 切状态要 `setBlock`，而 `setBlock` 会调 `onPlace` ⇒ `tryAutoForm`；此刻外壳**刚被还原成完整的**，自动激活当然把它重新装回去 —— ZF55 那套"三条路自动成型"在这儿反咬一口 | 切模型的那次 `setBlock` **必须发生在 `disassembling` 还是 true 的窗口里**（自动成型会看这个闸门）；探针专门有一条"拆完不许自己成型" |
| **把方块复活** | 挖掉控制器那格 ⇒ 那格又变回控制器（凭空多一个主控） | "挖掉控制器"是 `setBlock(空气)` **先生效**、再回调 `onRemove` ⇒ `disassemble()` ⇒ `setFormed(false)` ⇒ 又 `setBlock` 一次 ⇒ 把空气覆盖回控制器 | 切状态前先确认「那格现在还是不是控制器」，不是就什么都不做 |

**共同点**：两条都不是"逻辑写错了"，而是**新加的一次 `setBlock` 落进了别人已经搭好的回调链里**。
凡是"某个数据变化要顺带改方块状态"，先问两句：这次 `setBlock` 会触发谁的 `onPlace`/`onRemove`？
此刻那条回调链正处在什么中间状态？

> 附带一条正面经验：模型切在**方块状态**上、成型标记存在 **NBT** 上，两者可能对不上
> （旧存档、半途断电）⇒ 每秒自愈一次（只在真的不一致时才 `setBlock`）。
> 探针里"同一个方块实体实例"那条检查也是必需的：切状态要是把 BE 重建了，槽位里的东西就没了。

'''

ROW = u'''| ZF56 | **新建 `zf56_pre`**（4 个改前件：`AlloySmelterBlock` / `AlloySmelterBlockEntity` / `blockstates/alloy_smelter.json` / `_zf54_verify.py`） | 0.10：**4×5×4 是"成型后的合金炉"，不是主控本体**（用户纠正：「不是主控变成4x5x4是合金炉！合金炉成型后模型！」）。ZF54 把 OBJ 挂在 `facing` 上 ⇒ **一放下控制器就是个大盒子**。改法：① `AlloySmelterBlock` 加方块状态 `formed`（默认 false）；② blockstate 拆两种变体 —— `formed=false` → `block/alloy_smelter`（就是物品栏那个 cube_all），`facing=X,formed=true` → 四份 OBJ；③ `AlloySmelterBlockEntity.setFormed()` 同时改 NBT 与方块状态（`applyFormedState`），并把这次 `setBlock` **放在 `disassemble` 的 `disassembling` 窗口内**（否则扳手一拆就自己重新成型）；④ `applyFormedState` 先确认"那格还是控制器"再改（否则挖控制器会把方块复活）；⑤ 每秒自愈一次，防方块状态与 NBT 不一致。探针 `AlloyFormedCheck` **19 项全 [OK]**（未成型=小方块 / 成型=大盒子 / **同一个方块实体实例且槽位物品还在** / 挖一格退回小方块 / 扳手拆解不自己成型 / 挖控制器那格保持空气）；反证两次：把 `formed=false` 指向 OBJ ⇒ `_zf56_verify.py` **1 FAIL**；把 `setFormed(false)` 挪出 try ⇒ 探针 **3 FAIL**（含 `shell really restored, nothing left (got 67)`）。新写 `_zf56_verify.py`，把"两种变体 + 小方块模型不能是 obj + 物品模型指向小方块 + 切换时机/防复活/自愈"钉成断言 | 见 §9 |
'''

SEC9 = u'''- [ ] **ZF56：等用户看模型**（成品 `b0c86fcd…`）。现在：**没成型 = 主控那个小方块**（和物品栏里一样），
      围满自动成型那一刻才变成**整台 4×5×4 合金炉**；挖任意一格、或扳手拆解 ⇒ 退回小方块。
      要看的四件事：① 放下主控是不是小方块；② 成型那一下是不是整台变大盒子（不是只有主控那格变大）；
      ③ 拆解后回到小方块；④ **成型后槽位里的东西还在**（切模型不该重建方块实体）。
'''

TAIL = u'''
**ZF56 更正（模型归属）**：4×5×4 的 OBJ 是**成型后那台合金炉**的模型，**不是主控本体**的模型 ——
未成型时主控用 `block/alloy_smelter`（就是物品栏里那个 cube_all）。所以 blockstate 现在有两个变体：
`formed=false` 与 `facing=X,formed=true`。上面第 2/3 条"4 朝向烘 OBJ"仍然成立，只是挂在 `formed=true` 上。
'''


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    anchor5 = u"## 5. 版本与 [ZF] 流水线记录"
    if text.count(anchor5) != 1:
        problems.append(u"§5 标题不唯一")
    else:
        text = text.replace(anchor5, S433 + anchor5, 1)

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF55 |") and not added:
            out.append(ROW.rstrip(u"\n"))
            added = True
    if not added:
        problems.append(u"没找到 ZF55 行")
    text = u"\n".join(out)

    anchor9 = u"## 9. 待办与已知限制\n\n"
    if text.count(anchor9) != 1:
        problems.append(u"§9 标题不唯一")
    else:
        text = text.replace(anchor9, anchor9 + SEC9, 1)

    tail = u"（空格不换、控制器那格不记），否则图纸那种敞口顶面会凭空多出一层隐形格。\n"
    if text.count(tail) != 1:
        problems.append(u"§12.15 尾巴不唯一")
    else:
        text = text.replace(tail, tail + TAIL, 1)

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§4.33 / ZF56 行 / §9 / §12.15 全部写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
