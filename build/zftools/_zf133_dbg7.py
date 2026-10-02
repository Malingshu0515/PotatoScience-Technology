# -*- coding: utf-8 -*-
"""_zf133_dbg7.py —— 把"波内部看到的那一格"逐字节打出来（对象 identity + 标签 + 坐标）

已知事实（探针报告）：
  · 探针在 checkB 里读同一格：`isLEAVES=true`、tags 里有 `minecraft:leaves`；
  · 波内部在同一批坐标上却判成"非原木/树叶"，并把波停掉。
⇒ 同一个 tag 查询，两处结果不同。要么**读的不是同一格**，要么**不是同一个 BlockState 实例**。
所以这一刀打印：采样坐标、方块、`state.is(LEAVES)`、`state.getTags()`、
以及 `System.identityHashCode(state)` 与注册表里那一份 state 的 identity（对不上就是实例不同）。

跑法：python build\\zftools\\_zf133_dbg7.py     /  --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD = """                if (!isChoppable(state)) {"""
NEW = """                if (Zf133Check.DBG) {
                    System.out.println("[A133DBG7] 采样 " + pos.toShortString()
                            + " block=" + state.getBlock().getName().getString()
                            + " isLEAVES=" + state.is(BlockTags.LEAVES)
                            + " isLOGS=" + state.is(BlockTags.LOGS)
                            + " choppable=" + isChoppable(state)
                            + " stateId=" + System.identityHashCode(state)
                            + " regId=" + System.identityHashCode(
                                    state.getBlock().defaultBlockState())
                            + " tags=" + state.getTags()
                                    .map(t -> t.location().getPath())
                                    .collect(java.util.stream.Collectors.joining("|")));
                }
                if (!isChoppable(state)) {"""


def main():
    off = "--off" in sys.argv
    s = io.open(SHOCK, encoding="utf-8").read()
    a, b = (NEW, OLD) if off else (OLD, NEW)
    n = s.count(a)
    assert n == 1, "锚点 %d 次" % n
    io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
    print("[OK] %s" % ("撤销" if off else "插入"))


main()
