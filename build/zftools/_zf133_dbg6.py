# -*- coding: utf-8 -*-
"""_zf133_dbg6.py —— 临时：把"树叶到底认不认 #minecraft:leaves"在运行时问清楚

事实：波把 `102,161,97..102 = Oak Leaves` 判成**非原木/树叶**（被挡住）⇒
`state.is(BlockTags.LEAVES)` 在那个时刻返回了 false。可同样这段代码在放置之后的
[DBG] 打印里却能看出方块是 Oak Leaves（那一步只读了方块名，没查标签）。

要问清三件事（都在运行时，不猜）：
  ① `state.is(BlockTags.LEAVES)` 到底是 true 还是 false？
  ② 这个 BlockState 身上**所有**的 Block 标签是哪些（把 tags 列出来）？
  ③ `BuiltInRegistries.BLOCK.getTag(BlockTags.LEAVES)` 这个表里有没有 oak_leaves？

跑法：python build\\zftools\\_zf133_dbg6.py
      python build\\zftools\\_zf133_dbg6.py --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

OLD = """            BlockPos lp = new BlockPos(X0 + 2, Y0 + 1, Z0 + z);
            say(TAG + "      [DBG] 树叶位 " + lp.toShortString() + " = "
                    + level.getBlockState(lp).getBlock().getName().getString());"""
NEW = """            BlockPos lp = new BlockPos(X0 + 2, Y0 + 1, Z0 + z);
            net.minecraft.world.level.block.state.BlockState ls = level.getBlockState(lp);
            say(TAG + "      [DBG] 树叶位 " + lp.toShortString() + " = "
                    + ls.getBlock().getName().getString()
                    + " isLEAVES=" + ls.is(BlockTags.LEAVES)
                    + " isLOGS=" + ls.is(BlockTags.LOGS)
                    + " tags=" + ls.getTags().map(t -> t.location().toString())
                            .collect(java.util.stream.Collectors.joining(",")));
            {
                var tag = net.minecraft.core.registries.BuiltInRegistries.BLOCK.getTag(BlockTags.LEAVES);
                int n = tag.map(t -> (int) t.size()).orElse(-1);
                boolean hasOak = tag.map(t -> t.stream().anyMatch(h ->
                        h.value() == net.minecraft.world.level.block.Blocks.OAK_LEAVES)).orElse(false);
                say(TAG + "      [DBG] 注册表里 #minecraft:leaves 共 " + n
                        + " 项，含 oak_leaves = " + hasOak);
            }"""


def main():
    off = "--off" in sys.argv
    s = io.open(CHK, encoding="utf-8").read()
    a, b = (NEW, OLD) if off else (OLD, NEW)
    n = s.count(a)
    assert n == 1, "锚点 %d 次" % n
    io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(a, b, 1))
    print("[OK] %s" % ("撤销" if off else "插入"))


main()
