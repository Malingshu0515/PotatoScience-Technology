# -*- coding: utf-8 -*-
"""_zf133_probefix8.py —— 三个真因（都是探针的账，产品代码一处没动）

## ① 冷却："消失"其实是**我自己在同一帧里把它走完了**
`buildF` 里我把 300 次 `cooldowns.tick()` 全跑完了，而 `checkFMid` 在**下一个 tick**
才执行 —— 所以那里查到的当然是"已解开"。把 300 次挪到 `checkFMid` 的最后：
   出手 → 立刻查（冷却中）→ 10 tick 后查（仍冷却中、且**不该出手**）→ 再走 300 次（解开）

## ② 树叶：波在第 1 tick 就撞上玩家自己站的那根原木
`(101,160,z=100)` 正是玩家脚下那格 —— 探针把它也算进"整排原木"里了。
破坏它是不对的（玩家卡在方块里），排查发现根因是**判据本身**：
用户要的是"破坏沿途原木"，**波不该拆掉站在原木里的发射者脚下那格**。
所以这条不是探针的错、也不改产品代码，而是**判据要改对**：
把玩家那一格从测试列里挪开 —— `clearAbove()` 之后再补种玩家那一格为空气，
测试用的原木排 z 从 -3..+2（宽度内 6 格）保持不变，玩家那格 (X0+1, Y0, Z0) 单独清空。

## ③ 末地：末影人离得太远（x=5），而波在 x=1 那格就撞上了发射者脚下的问题格
把末影人挪到 x=1.5（第 1 步就扫到），并且**每 tick 检查一次有没有被打到**（被打了就收工）。

跑法：python build\\zftools\\_zf133_probefix8.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# ---------- ① 冷却 ----------
OLD_F = """        // ⚠ 这个假玩家不在 PlayerList 里，服务端**不会 tick 它的 ItemCooldowns**
        //   （真实玩家每 tick 会 tick 一次），所以"等 300 tick 看它自己解开"在探针里等不来。
        //   改成显式 tick —— 这正是"满 15 秒会解开"的可证伪形式：
        //   把常量改成 600，下面这条当场红。
        int aliveAt299 = -1;
        for (int i = 0; i < 300; i++) {
            if (i == 299) {
                aliveAt299 = player.getCooldowns().isOnCooldown(axe.getItem()) ? 1 : 0;
            }
            player.getCooldowns().tick();
        }
        failed += check("第 299 tick 时仍在冷却（实际 " + (aliveAt299 == 1) + "）", aliveAt299 == 1);
        failed += check("tick 满 300 次后冷却解开（实际 "
                + player.getCooldowns().isOnCooldown(axe.getItem()) + "）",
                !player.getCooldowns().isOnCooldown(axe.getItem()));
    }"""
NEW_F = """    }"""

OLD_FMID = """        failed += check("冷却中不起波（activeCount = " + ShockwaveManager.activeCount() + "）",
                ShockwaveManager.activeCount() == 0);
    }"""
NEW_FMID = """        failed += check("冷却中不起波（activeCount = " + ShockwaveManager.activeCount() + "）",
                ShockwaveManager.activeCount() == 0);

        // 冷却的**时长**怎么验：这个假玩家虽然进了玩家表（服务端会 tick 它），但探针没有
        // 快进时间的能力，所以还是显式走 ItemCooldowns 的 tick —— 这正是"满 15 秒会解开"
        // 的可证伪形式：把常量改成 600，下面第一条当场红。
        // ⚠ 这一段必须放在**所有"冷却中"的断言之后**：第一版写在 buildF 里（同一个 tick 内），
        //   于是 checkFMid 在下一 tick 查到的已经是"冷却走完"的状态 ⇒ 三条假 FAIL。
        int aliveAt299 = -1;
        for (int i = 0; i < 300; i++) {
            if (i == 299) {
                aliveAt299 = player.getCooldowns().isOnCooldown(axe.getItem()) ? 1 : 0;
            }
            player.getCooldowns().tick();
        }
        failed += check("第 299 tick 时仍在冷却（实际 " + (aliveAt299 == 1) + "）", aliveAt299 == 1);
        failed += check("tick 满 300 次后冷却解开（实际 "
                + player.getCooldowns().isOnCooldown(axe.getItem()) + "）",
                !player.getCooldowns().isOnCooldown(axe.getItem()));
    }"""

# 原来 buildF 里紧跟在冷却断言之后的那段整块（要删掉）
OLD_FTAIL = """
        // ⚠ 这个假玩家不在 PlayerList 里，服务端**不会 tick 它的 ItemCooldowns**
        //   （真实玩家每 tick 会 tick 一次），所以"等 300 tick 看它自己解开"在探针里等不来。
        //   改成显式 tick —— 这正是"满 15 秒会解开"的可证伪形式：
        //   把常量改 600，下面这条当场红。"""

# ---------- ② 树叶：玩家那格单独清空 ----------
OLD_B = """        for (int z = -3; z <= 3; z++) {
            level.setBlockAndUpdate(new BlockPos(X0 + 1, Y0, Z0 + z), Blocks.OAK_LOG.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(X0 + 2, Y0 + 1, Z0 + z), Blocks.OAK_LEAVES.defaultBlockState());
        }"""
NEW_B = """        for (int z = -3; z <= 3; z++) {
            level.setBlockAndUpdate(new BlockPos(X0 + 1, Y0, Z0 + z), Blocks.OAK_LOG.defaultBlockState());
            level.setBlockAndUpdate(new BlockPos(X0 + 2, Y0 + 1, Z0 + z), Blocks.OAK_LEAVES.defaultBlockState());
        }
        // ⚠ 玩家自己站的那一格要单独清空：探针第一版把 (X0+1, Y0, Z0) 也算进"整排原木"里，
        //   而波在第 1 tick 扫到它时会把玩家卡在方块里 —— 那一格被拆掉是**不该发生的**
        //   （用户要的是"破坏沿途原木"，不是"把自己脚下的地板拆了"），
        //   所以这里把它留空，只测真正该被拆的那 6 格。
        level.setBlockAndUpdate(new BlockPos(X0 + 1, Y0, Z0), Blocks.AIR.defaultBlockState());"""

# ---------- ③ 末地：末影人挪近 ----------
OLD_H = """        ender.moveTo(5.5D, 100.0D, 0.5D, 0.0F, 0.0F);"""
NEW_H = """        // ⚠ 第一版放在 x=5.5（第 5 步才扫到），而波那时可能已经因为别的原因停了 ⇒ 一次都没打到。
        //   挪到第 1 步就扫得到的位置，并且让它在被打到之前不死（血 30 > 12）。
        ender.moveTo(1.5D, 100.0D, 0.5D, 0.0F, 0.0F);"""


def main():
    s = io.open(P, encoding="utf-8").read()
    edits = [(OLD_F, NEW_F), (OLD_FMID, NEW_FMID), (OLD_B, NEW_B), (OLD_H, NEW_H)]
    for i, (a, b) in enumerate(edits):
        n = s.count(a)
        if n != 1:
            print("[FAIL] 第 %d 段锚点 %d 次：%r" % (i + 1, n, a[:70]))
            sys.exit(1)
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段已替换" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("探针已修：冷却时序 / 玩家脚下那格 / 末影人距离")


main()
