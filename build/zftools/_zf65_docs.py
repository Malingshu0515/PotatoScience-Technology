# -*- coding: utf-8 -*-
"""_zf65_docs.py —— ZF65 档案落笔（循环音停不下来的 bug 修复）"""
import io
import sys

DOC = r"E:\PotatoST\docs\开发档案.md"

ROW = u'''| ZF65 | **新建 `zf65_pre`**（3 个改前件：`AlloySmelterBlockEntity` / `client/sound/MachineRunningSound` / `PotatoST`）。⚠ **本轮我忘了"动第一个字节之前先抄一份"**（§10 的规矩），这三份是改完才**反向套用本次编辑**重建的 —— 为了不让"重建"变成"猜"，用 `_zf65_precheck.py` 把它们换回源码树编译，与 **ZF64 成品 jar 里的同名 class 逐字节比对：3/3 相同**（字节码等价 ⇒ 重建忠实） | 0.10：**修用户实测报的 bug**（原话：「冶炼中的合金炉被破坏还是会循环播放音效 重新创建刷新一下才好」）。根因（读代码 + 探针反证定的）：挖掉外壳任意一格走 `AlloySmelterPartBlock.onRemove → master.disassemble(pos) → setFormed(false)`，而**控制器方块本身还在**；ZF64 那版把 `running` 的清零写在 `craftTick()` 里，`formed == false` 之后每 tick 都走不到 `craftTick()` ⇒ **`running` 永远停在 true**，客户端每 tick 都收到"在烧"⇒ 循环音一直响到重新建一台。修法：`serverTickBody()` 开头**无条件** `this.running = false;`，而且必须放在 `if (this.formed)` **之外**；只有 `craftTick()` 真的扣电推进才再置真。顺手给公共件 `MachineRunningSound` 加两条防呆：① 从 `ACTIVE` 表里摘掉旧实例之前先 `stop()`（**删表 ≠ 消音**）；② `tick()` 除了 `isRemoved()` 还看"那格是不是还是这个方块实体"（方块没了就再没有 tick 来纠正它），并用 `isLoaded` 挡住"区块没加载"的误判。**验证**：新探针 `AlloySoundStopCheck` **18 项全 [OK]**（基线：真在烧的机器连走 5 个 tick 保持 true —— 防这次修过头把工作中的机器静音；挖掉一格部件格**走真的 `destroyBlock`**⇒**1 tick 内** running 变假且更新包带 false；直接 `disassemble()` 同款）；**反证**：把那一行注释掉 ⇒ **4 FAIL**，全部落在"拆解后 running 该为假"那几条上，基线仍全过（精确命中，也**复现了用户的 bug**）。新写常驻 `_zf65_verify.py`（**13 项**：那个清零必须在 `if (this.formed)` **之前** + 公共件两条防呆 + ZF64 那条链子回归），反证：把它挪进分支里 ⇒ **1 FAIL**（`@692 < @661`）。⚠ **上一轮为什么没验出来**：ZF64 的探针写了 22 条，全是"有配方/没配方/没电/产出堵住"，**一条都没试过"把机器拆掉"**（§4.37） | 见 §4.37 / §9 |'''

OLD9 = u'''- [ ] **ZF62/ZF63/ZF64：等用户试合金炉**（ZF64 后的新成品是你手上这一版）。'''

NEW9 = u'''- [x] ~~ZF64 交付后发现：冶炼中的合金炉被破坏，循环音停不下来~~ → **ZF65 已修**（成品 `c71dfa48…`）：
      根因是 `running` 的清零只写在 `craftTick()` 里，而拆解那条路（`disassemble()` → `setFormed(false)`）
      根本不经过它 ⇒ 标记卡在 true、客户端每 tick 被续一次。详见 §4.37。
- [ ] **ZF65：等你复验循环音**（成品 `c71dfa48…`）。要看的：① **冶炼中挖掉外壳任意一格** ⇒ 声音应当**马上停**
      （最迟 1 个 tick）；② 重新围起来再开工 ⇒ 声音照常响（别修成"再也不响"）；③ 扳手 Shift 右键拆解 ⇒ 同样停。
- [ ] **ZF62/ZF63/ZF64：等用户试合金炉**（当前成品 `c71dfa48…`，ZF65）。'''

M_ANCHOR = u"\n## 5. 版本与 [ZF] 流水线记录"

M_INSERT = u'''
### 4.37 【方法论】"运行中"标记必须有**唯一的重算出口**（0.10 ZF65）

用户报：「冶炼中的合金炉被破坏还是会循环播放音效 重新创建刷新一下才好」。ZF64 给这台机器加循环音时，
`running` 是这样维护的：`craftTick()` 开头清零、真的扣电推进了再置真。看着挺对称，实际有个洞 ——
**`formed == false` 的时候根本不会调用 `craftTick()`**。而"挖掉外壳任意一格"走的正是
`AlloySmelterPartBlock.onRemove → master.disassemble(pos) → setFormed(false)`，**控制器方块还在**：

| 谁 | 状态 | 后果 |
|---|---|---|
| 服务端控制器 | `formed=false`，`running` **停在 true** | 每 tick 都 `sendBlockUpdated` 说"我在烧" |
| 客户端控制器 | 方块实体没被移除 ⇒ `clientTick()` 照常跑 | 每 tick 把循环音"续"着，永远等不到 false |
| 循环音实例 | 只等 `update(be, false)` 或 `tick()` 判方块没了 | **一直响**，直到重新建一台机器 |

四条结论，以后所有机器都照这个来：

1. **"运行中"这类标记必须在服务端每 tick 的同一个出口重算**（本机是 `serverTickBody()` 开头无条件清零，
   再由"真的干了活"的分支置真），**不能只在某个子函数里维护** —— 子函数会因为别的前置条件
   （成型 / 有配方 / 有电）根本不被调用；
2. **"外部原因导致的停止"最容易漏**：拆解/失效往往由**别的方块**触发（部件格、接线口、扳手），
   它们只切换一个旗标（`setFormed(false)`），跟配方推进那条路径不搭界；
3. **验证必须覆盖"把机器拆掉"这条时间线**。ZF64 的探针写了 22 条断言，全是"有配方 / 没配方 / 没电 /
   产出堵住"，**一条都没试过拆解** ⇒ 交付时全绿、用户一拆就复现。反证（注释掉那一行）⇒ **4 FAIL**，
   全部落在拆解那几条上 —— 说明"能失败"和"覆盖到了"是两件事；
4. 公共件顺手修的是同一个道理：`MachineRunningSound` 原来从 `ACTIVE` 表里摘掉旧实例时**只删表、不 `stop()`**
   —— **表和声音引擎是两回事**，删表不等于消音；`tick()` 现在也不只看 `isRemoved()`，还看"那格是不是
   还是这个方块实体"（方块没了就再没有 tick 来纠正它），并用 `isLoaded` 挡住"区块没加载"的误判。
'''

M2_ANCHOR = u"\n## 5. 版本与 [ZF] 流水线记录"
M2_INSERT = M_INSERT


def main():
    text = io.open(DOC, encoding="utf-8").read()
    before = len(text)
    problems = []

    lines = text.split(u"\n")
    out = []
    added = False
    for line in lines:
        out.append(line)
        if line.startswith(u"| ZF64 |") and not added:
            out.append(ROW)
            added = True
    if not added:
        problems.append(u"没找到 ZF64 行")
    text = u"\n".join(out)

    if text.count(OLD9) != 1:
        problems.append(u"§9 那条待验命中 %d 次（应为 1）" % text.count(OLD9))
    else:
        text = text.replace(OLD9, NEW9, 1)

    if text.count(M_ANCHOR) != 1:
        problems.append(u"§5 标题锚点命中 %d 次（应为 1）" % text.count(M_ANCHOR))
    else:
        text = text.replace(M_ANCHOR, M_INSERT + M_ANCHOR, 1)

    if problems:
        print(u"有失败项，**不落盘**：")
        for p in problems:
            print(u"  !! " + p)
        return 1

    io.open(DOC, "w", encoding="utf-8", newline="\n").write(text)
    print(u"字数 %d -> %d（+%d）" % (before, len(text), len(text) - before))
    print(u"§5 ZF65 行 + §9 两条 + §4.37 已写入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
