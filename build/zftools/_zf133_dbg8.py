# -*- coding: utf-8 -*-
"""_zf133_dbg8.py —— 最后一刀：把 `destroyBlock` 的**返回值**打出来

DBG7 已经证明：波内部读到的树叶 `choppable=true`、tags 里有 `leaves`、坐标也对
（`102,161,97..102`），`DBG5` 那 6 条"挡住"是**别的位置**留下的（上一轮的旧结论）。
所以现在只剩一个问题：`destroyBlock(pos, true, owner)` 到底返回了什么、叶子为什么还在。

跑法：python build\\zftools\\_zf133_dbg8.py  /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """                boolean destroyed = wave.level.destroyBlock(pos, true, owner);"""
NEW = """                boolean destroyed = wave.level.destroyBlock(pos, true, owner);
                if (Zf133Check.DBG) {
                    System.out.println("[A133DBG8] destroy " + pos.toShortString() + "=" + destroyed
                            + " 之后读到 " + wave.level.getBlockState(pos).getBlock().getName().getString()
                            + " （isAir=" + wave.level.getBlockState(pos).isAir() + "）");
                }"""


def main():
    off = "--off" in sys.argv
    s = io.open(SHOCK, encoding="utf-8").read()
    a, b = (NEW, OLD) if off else (OLD, NEW)
    n = s.count(a)
    assert n == 1, "锚点 %d 次" % n
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
    print("[OK] %s" % ("撤销" if off else "插入"))


main()
