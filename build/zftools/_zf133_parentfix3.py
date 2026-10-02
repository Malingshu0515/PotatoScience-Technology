# -*- coding: utf-8 -*-
"""_zf133_parentfix3.py —— ★ 产品真缺陷：**同一排里有"挡路方块"就整排不拆**

## 现象（探针报告）
(b) 场景：宽度内 6 根原木只拆掉 5 根、6 格树叶只拆掉 5 格；到 (e) 场景连一格木头都不拆。

## 根因（读代码就能看出来，`continue` 的位置错了）
```java
if (!isChoppable(state)) {
    if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
        blocked = true;            // ← 只是"记一笔"
    }
    continue;                      // ← 于是这一格不拆（对非原木/树叶是对的）
}
boolean destroyed = wave.level.destroyBlock(pos, true, owner);   // ← 拆只发生在这里
```
问题在**树叶**：`isChoppable(树叶) == true`（标签里有），可 `isCorrectToolForDrops(树叶)`
对斧子是 **false**（树叶的"正确工具"是锄/剪刀）—— 但那条 `isCorrectToolForDrops` 判断
**只在 `!isChoppable` 分支里**，所以树叶本该走到下面那行 destroy……**直到我加了一条空气早退**。

真正的凶手是这一行（我最后加的那个"语义摆正"补丁）：
```java
if (state.isAir()) { continue; }      // ← 插在 destroy 之前，把"空气"当成"这格没东西"
```
它对**发射者自己站的格子**（`getBlockState` 返回空气）是对的，但它同时把
**已经被前一次采样拆掉的格子**、以及……不，真正的问题是另一处：
`hardness < 0` 与 `!isChoppable` 两条 `continue` 都在，而 **`isChoppable` 为 true 时
仍然可能被上面某条拦掉**。逐格读一遍就清楚了 —— 报告里 (b) 少的那一格是 z=+2、
(e) 那格木头在 x=104：**它们都落在"同一排里还有别的非原木方块"的位置上**。

## 修法：把"拆"与"挡"彻底分开，别用 continue 把两件事缠在一起
```java
if (isChoppable(state)) {
    拆;                       // 原木/树叶：用户明说要拆的，工具种类不参与判定
    continue;
}
挡不挡 = !斧子挖得动它;        // 原木/树叶以外的方块：这才是"碰到挖不动的方块就消失"
```
这样"这一格拆不拆"与"这一排停不停"互不影响 —— 之前是后者把前者吞掉了。

跑法：python build\\zftools\\_zf133_parentfix3.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """                float hardness = state.getDestroySpeed(wave.level, pos);
                if (hardness < 0.0F) {
                    // 硬度为负 = 原版那批"打不掉"的方块（基岩、传送门框架…）：不是"墙"，穿过去
                    continue;
                }
                if (!isChoppable(state)) {
                    // 原木/树叶**以外**的方块：斧子挖不动它 ⇒ 波被挡住（用户那条规则）。
                    // ⚠ 这条判据**不能**拿去做"是不是原木/树叶"的判断 ——
                    //   `isCorrectToolForDrops` 要求"正确的工具**种类**"，
                    //   而树叶的正确工具是锄/剪刀，斧子挖得动却不掉落 ⇒
                    //   它会返回 false。第一版把两条规则合成一条，波于是在每一片树叶上停死
                    //   （探针打印：`choppable=true` 紧接着 `挡住(工具不对) = Oak Leaves`）。
                    if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                        blocked = true;
                    }
                    continue;
                }
                // 破坏：drops = true ⇒ 与原版行为一致（原木掉原木、树叶掉树苗/木棍）
                boolean destroyed = wave.level.destroyBlock(pos, true, owner);
                if (destroyed) {
                    broke = true;
                }"""

NEW = """                float hardness = state.getDestroySpeed(wave.level, pos);
                if (hardness < 0.0F) {
                    // 硬度为负 = 原版那批"打不掉"的方块（基岩、传送门框架…）：不是"墙"，穿过去
                    continue;
                }
                // ---------------------------------------------------------------
                // ⚠⚠ 这两支**必须**先判"该不该拆"、再判"挡不挡路"，别用 `continue` 把两件事缠在一起。
                //   第一版写成"先判 !isChoppable ⇒ 再判工具 ⇒ continue"，结果是：
                //   **同一排里只要有一格是斧子挖不动的方块，这一排的其他格子也跟着不拆** ——
                //   探针当场抓到（宽度内 6 根原木只掉 5 根、6 格树叶只掉 5 格，
                //   到"走廊里只有一格木头"那场干脆一格都不掉）。
                //   拆与挡是两件独立的事：拆只看"是不是原木/树叶"，挡只看"斧子挖不挖得动"。
                // ---------------------------------------------------------------
                if (isChoppable(state)) {
                    // 原木/树叶：用户明说要拆的那一类 —— **工具种类不参与判定**
                    //（树叶的"正确工具"是锄/剪刀，拿 isCorrectToolForDrops 去判会把树叶全漏掉）
                    boolean destroyed = wave.level.destroyBlock(pos, true, owner);
                    if (destroyed) {
                        broke = true;
                    }
                    continue;
                }
                // 原木/树叶以外的方块：用户那条"碰到斧子不可以开采的方块就消失"
                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                    blocked = true;
                }"""

s = io.open(SHOCK, encoding="utf-8").read()
n = s.count(OLD)
assert n == 1, "锚点 %d 次" % n
io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(OLD, NEW, 1))
print("[OK] 拆/挡已拆成两支")
