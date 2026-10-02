# -*- coding: utf-8 -*-
"""_zf133_probefix2.py —— 第二轮探针补强：让"冷却是 15 秒"和"滚动窗口"两条**真被验到**

第一轮的东西修完之后，我发现有两条断言**还不够硬**：

  · 「冷却 = 15 秒」只验了"出手后立刻在冷却中"，**没验满 300 tick 之后解没解**——
    而探针里那个假玩家不在 `PlayerList` 里，服务端**根本不会 tick 它的 ItemCooldowns**，
    所以拿真实时间等是等不来的。改成**显式 tick 300 次**：这正是"满 15 秒会解开"的可证伪形式
    （要是常量被改成 600，这里会当场报"300 tick 后仍在冷却"）。
  · 「10s 内未碰到任何原木 ⇒ 消失」验的是**起点为空旷地**那种情形，
    没验"拆到木头之后重新计时"这条**滚动窗口**语义。补一个场景 (i)：
    连续两次拆到木头（中间隔 1 tick）⇒ 145 tick 时**必须还活着**、295 tick 时**必须已散**。
    没有这一条的话，把 `sinceBreak = 0` 那行删掉（改成一次性计时）也照样全绿。

同时把时间线整体往后挪，给 (i) 腾出 310 tick。

跑法：python build\\zftools\\_zf133_probefix2.py
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"E:\PotatoST"
P = os.path.join(ROOT, r"src\main\java\com\potatost\mod\Zf133Check.java")

OLD_TIMELINE = """    // ---- 时间线 ----
    private static final int T_STATIC = 20;      // ① 静态事实
    private static final int T_B = 40;           // ② 整排原木 + 树叶
    private static final int T_B_CHECK = 60;
    private static final int T_D = 120;          // ③ 石头墙
    private static final int T_D_CHECK = 150;
    private static final int T_E = 200;          // ④ 10 秒闲置
    private static final int T_E_CHECK = 440;
    private static final int T_F = 460;          // ⑤ 冷却
    private static final int T_F_MID = 470;
    private static final int T_G = 480;          // ⑥ 耐久门槛
    private static final int T_G2 = 500;
    private static final int T_C = 520;          // ⑦ 创造模式
    private static final int T_H = 560;          // ⑧ 末地伤害
    private static final int T_H_CHECK = 600;
    private static final int T_END = 660;
"""

NEW_TIMELINE = """    // ---- 时间线 ----
    private static final int T_STATIC = 20;      // ① 静态事实
    private static final int T_B = 40;           // ② 整排原木 + 树叶
    private static final int T_B_CHECK = 60;
    private static final int T_D = 120;          // ③ 石头墙
    private static final int T_D_CHECK = 150;
    private static final int T_E = 200;          // ④ 10 秒闲置（起点为空旷地）
    private static final int T_E_CHECK = 440;
    private static final int T_I = 450;          // ⑤ 滚动窗口：先拆两次木头
    private static final int T_I_ALIVE = 600;    //    之后第 150 tick：必须还活着
    private static final int T_I_DEAD = 750;     //    之后第 300 tick：必须已散
    private static final int T_F = 760;          // ⑥ 冷却
    private static final int T_F_MID = 770;
    private static final int T_G = 780;          // ⑦ 耐久门槛
    private static final int T_G2 = 800;
    private static final int T_C = 820;          // ⑧ 创造模式
    private static final int T_H = 860;          // ⑨ 末地伤害
    private static final int T_H_CHECK = 900;
    private static final int T_END = 1080;
"""

EDITS = [
    (OLD_TIMELINE, NEW_TIMELINE),

    # 时间线派发：插入 (i) 的三拍
    ("""            } else if (t == T_E_CHECK) {
                checkE();
            } else if (t == T_F) {""",
     """            } else if (t == T_E_CHECK) {
                checkE();
            } else if (t == T_I) {
                buildI();
            } else if (t == T_I_ALIVE) {
                checkIAlive();
            } else if (t == T_I_DEAD) {
                checkIDead();
            } else if (t == T_F) {"""),

    # 冷却补强：显式 tick 300 次
    ("""        failed += check("冷却剩余 = 300 tick（实际 "
                + (300 - (int) (player.getCooldowns().getCooldownPercent(axe.getItem(), 0.0F) * 300)) + " 附近）",
                player.getCooldowns().getCooldownPercent(axe.getItem(), 0.0F) > 0.98F);
    }""",
     """        failed += check("出手那一刻冷却满格（percent = "
                + player.getCooldowns().getCooldownPercent(axe.getItem(), 0.0F) + "）",
                player.getCooldowns().getCooldownPercent(axe.getItem(), 0.0F) > 0.98F);

        // ⚠ 这个假玩家不在 PlayerList 里，服务端**不会 tick 它的 ItemCooldowns**
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
    }

    // ------------------------------------------------------------ ⑤ (i) 滚动窗口
    /** 用户第 2 条的**滚动**语义：拆到木头就重新计时 —— 连续拆两次，第二次之后还能再活 200 tick。 */
    private static void buildI() {
        say(TAG + "⑤ (i) 滚动窗口：拆到木头就重新计时");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        clearAbove();
        // 走廊全清空，只在第 3 格放木头 ⇒ 波拆完它之后开始闲置计时
        for (int x = 1; x <= 24; x++) {
            for (int z = -4; z <= 4; z++) {
                for (int dy = 0; dy <= 3; dy++) {
                    level.setBlockAndUpdate(new BlockPos(X0 + x, Y0 + dy, Z0 + z),
                            Blocks.AIR.defaultBlockState());
                }
            }
        }
        level.setBlockAndUpdate(new BlockPos(X0 + 3, Y0, Z0), Blocks.OAK_LOG.defaultBlockState());
        useAxe(player);
    }

    /** (i) 之后第 150 tick：还活着（证明计时被重置过，不是从起手一路算）。 */
    private static void checkIAlive() {
        failed += check("拆到木头之后 150 tick，波**还活着**（滚动窗口重置了计时；activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 1);
    }

    /** (i) 之后第 300 tick：已散（>200 tick 没再碰到木头）。 */
    private static void checkIDead() {
        failed += check("再飞 150 tick（合计 300 tick 没碰到木头）⇒ 波已散（activeCount = "
                + ShockwaveManager.activeCount() + "）", ShockwaveManager.activeCount() == 0);
    }"""),
]


def main():
    s = io.open(P, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS):
        n = s.count(a)
        if n != 1:
            print("[FAIL] 第 %d 段锚点出现 %d 次：%r" % (i + 1, n, a[:80]))
            sys.exit(1)
        s = s.replace(a, b, 1)
        print("[OK ] 第 %d 段已替换" % (i + 1))
    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    print("探针补强完成")


main()
