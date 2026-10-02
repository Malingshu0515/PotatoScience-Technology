# -*- coding: utf-8 -*-
"""_zf133_probefix9.py —— 产品代码的真缺陷：「工具对不对」那条判据把树叶也一起挡了

## 事实链（全部来自探针打印，不是推演）
`[A133DBG7] 102,161,97 = Oak Leaves choppable=true`
但紧接着 `[A133DBG5] 挡住(工具不对) 102,161,97 = Oak Leaves`
⇒ 波走到 `!owner.getMainHandItem().isCorrectToolForDrops(state)` 那条**停了**。

## 为什么这条判据是错的
`isCorrectToolForDrops` 要求"**正确的工具种类** + 等级够"。树叶的正确工具是**锄/剪刀**，
斧子在原版里挖得动树叶但**不掉落**（`isCorrectToolForDrops=false`）。
用户的话是「破坏沿途所有**原木/去皮原木 和树叶**」——
树叶属于**明说要拆的那一类**，它不该被"工具对不对"挡住；
那条"碰到斧子不可以开采的方块就消失"说的是**原木/树叶以外的方块**。

## 修法（语义拆开，两条规则各归各位）
    if 是原木或树叶        → 拆（工具种类不参与判定）
    else if 斧子挖不动它   → 挡（用户那条）
    else                  → 穿过（比如草、花这种斧子不"正确"但根本不是墙的东西）

跑法：python build\\zftools\\_zf133_probefix9.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"
AXE = r"E:\PotatoST\src\main\java\com\potatost\mod\StarSteelAxeItem.java"

OLD_BLOCK = """                if (!isChoppable(state)) {
                    // 斧子挖不动的方块（石头、泥土、矿石…）⇒ 波被挡住
                    if (Zf133Check.DBG) {
                        System.out.println("[A133DBG5] 挡住(非原木/树叶) " + pos.toShortString()
                                + " = " + state.getBlock().getName().getString());
                    }
                    blocked = true;
                    continue;
                }
                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                    if (Zf133Check.DBG) {
                        System.out.println("[A133DBG5] 挡住(工具不对) " + pos.toShortString()
                                + " = " + state.getBlock().getName().getString());
                    }
                    blocked = true;
                    continue;
                }"""

NEW_BLOCK = """                if (!isChoppable(state)) {
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
                }"""

EDITS = [(SHOCK, OLD_BLOCK, NEW_BLOCK)]


def main():
    for path, old, new in EDITS:
        s = io.open(path, encoding="utf-8").read()
        n = s.count(old)
        assert n == 1, "%s 锚点 %d 次" % (path, n)
        io.open(path, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
        print("[OK] 已修 %s" % path)


main()
