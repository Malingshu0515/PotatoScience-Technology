# -*- coding: utf-8 -*-
"""_zf133_whichblock.py —— 最后一次：把"挡住波的那一格"打出来

`[E]` 已经证明那一格木头**摆上了**（`104, 160, 100 = Oak Log`），玩家也在场、手上就是斧子。
所以只剩一个可能：波在走到 x=104 之前就被某格挡掉了。
这一刀就在 `blocked = true` 那一行旁边把 (坐标, 方块) 打出来 —— 一次跑就能看到凶手。

跑法：python build\\zftools\\_zf133_whichblock.py   /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """                // 原木/树叶以外的方块：用户那条"碰到斧子不可以开采的方块就消失"
                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                    blocked = true;
                }"""
NEW = """                // 原木/树叶以外的方块：用户那条"碰到斧子不可以开采的方块就消失"
                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                    System.out.println("[WB] 挡住 t=" + wave.totalTicks + " " + pos.toShortString()
                            + " = " + state.getBlock().getName().getString()
                            + " hard=" + hardness);
                    blocked = true;
                }"""


def main():
    off = "--off" in sys.argv
    s = io.open(SHOCK, encoding="utf-8").read()
    a, b = (NEW, OLD) if off else (OLD, NEW)
    n = s.count(a)
    assert n == 1, "锚点 %d" % n
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
    print("[OK] %s" % ("撤销" if off else "插入 [WB] 诊断"))


main()
