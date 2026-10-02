# -*- coding: utf-8 -*-
"""_zf133_dbg5.py —— 临时：把"被哪一格挡住"打出来 + 末地平台抬高一层

① **主世界树叶之谜**：波拆完 x=101 那一排、又在 x=102 拆掉**一格**树叶之后就停了
   ⇒ 有一格判成"挡住"。打印出挡住它的到底是哪一格、什么方块（不猜）。
② **末地**：平台铺在 y=99（玩家站 y=100），可 `dy=0` 采样的正好是**脚下的黑曜石**
   ⇒ 波第一步就被自己的地板挡住（主世界那边地板铺在 Y0-1，所以没踩到）。
   修法：把末地平台也铺在 **99 层**、并把 100~102 三层清空（与主世界同一套布局）。

跑法：python build\\zftools\\_zf133_dbg5.py
      python build\\zftools\\_zf133_dbg5.py --off
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

SHOCK_OLD = """                if (!isChoppable(state)) {
                    // 斧子挖不动的方块（石头、泥土、矿石…）⇒ 波被挡住
                    blocked = true;
                    continue;
                }
                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                    blocked = true;
                    continue;
                }"""
SHOCK_NEW = """                if (!isChoppable(state)) {
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

CHK_OLD = """        for (int x = -6; x <= 16; x++) {
            for (int z = -4; z <= 4; z++) {
                end.setBlockAndUpdate(new BlockPos(x, 99, z), Blocks.OBSIDIAN.defaultBlockState());
                for (int dy = 0; dy <= 3; dy++) {
                    end.setBlockAndUpdate(new BlockPos(x, 100 + dy, z), Blocks.AIR.defaultBlockState());
                }
            }
        }"""
CHK_NEW = """        // ⚠ 平台铺在 99 层（玩家站 y=100），100~102 清空 —— 与主世界同一套布局。
        //   第一版把地板铺在 100 层，于是 `dy=0` 采样到的正是玩家脚下的黑曜石 ⇒
        //   波第一步就被自己的地板挡住，一次都没打到末影人（探针当场报 0 次命中）。
        for (int x = -6; x <= 16; x++) {
            for (int z = -4; z <= 4; z++) {
                for (int dy = 0; dy <= 4; dy++) {
                    end.setBlockAndUpdate(new BlockPos(x, 100 + dy, z), Blocks.AIR.defaultBlockState());
                }
                end.setBlockAndUpdate(new BlockPos(x, 99, z), Blocks.OBSIDIAN.defaultBlockState());
            }
        }"""


def main():
    off = "--off" in sys.argv
    for path, pairs in ((SHOCK, [(SHOCK_OLD, SHOCK_NEW)]), (CHK, [(CHK_OLD, CHK_NEW)])):
        s = io.open(path, encoding="utf-8").read()
        for a, b in ([(y, x) for x, y in pairs] if off else pairs):
            n = s.count(a)
            assert n == 1, "%s 锚点 %d 次" % (path, n)
            s = s.replace(a, b, 1)
        io.open(path, "w", encoding="utf-8", newline="\n").write(s)
        print("[OK] %s %s" % ("撤销" if off else "插入", path))


main()
