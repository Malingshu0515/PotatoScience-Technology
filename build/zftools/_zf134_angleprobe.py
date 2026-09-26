# -*- coding: utf-8 -*-
"""_zf134_angleprobe.py —— 给探针加一个**斜角场景**（这是本次改动的正面证据）

用户要的是"东南 21° 这种"，所以判据不能只验"正方向没坏"，必须有一条**斜着**的。
做法（放进 (b) 那一场的后面，新开一场 (j)）：

  在 (b) 的那排原木旁边，把玩家朝向设成 **21°**（yaw 使水平方向 = (cos21°, sin21°) 那一支），
  然后在玩家正前方 6 格外、沿**斜线**摆 3 根原木，出手后断言：
    ① 这 3 根全被拆（原来只朝 4 个正方向时，斜线目标一根都拆不到）；
    ② 破坏**没有**跑到"正东那一列"上（证明它真的按斜方向走，不是退化成正方向）。

摆法用同一套数学（法线/朝向）算坐标，**不用手写整数**：
    目标 = 玩家位置 + dir × 6 + perp × k     (k = -1, 0, +1)
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# ① 时间线常量
T_OLD = "    private static final int T_END = 1000;"
T_NEW = """    private static final int T_ANGLE = 900;      // ⑩ 斜角场景（ZF134：21°）
    private static final int T_ANGLE_CHECK = 940;
    private static final int T_END = 1000;"""

# ② 派发
D_OLD = """            } else if (t == T_END) {
                finish(event);"""
D_NEW = """            } else if (t == T_ANGLE) {
                buildAngle();
            } else if (t == T_ANGLE_CHECK) {
                checkAngle();
            } else if (t == T_END) {
                finish(event);"""

# ③ 场景实现（挂在 checkG2 之前）
IMPL_ANCHOR = "    private static void checkG2() {"
IMPL = '''    // ------------------------------------------------------------ ⑩ 斜角（21°）
    /** 斜角场景的靶子坐标（buildAngle 摆、checkAngle 验）。 */
    private static final java.util.List<BlockPos> angleTargets = new java.util.ArrayList<>();
    /** 斜角场景里"正东那一列"的对照点（那几格**不该**被拆）。 */
    private static final java.util.List<BlockPos> angleControl = new java.util.ArrayList<>();

    /** 用户要的「东南 21° 这种」：把朝向设成 21°，沿斜线摆 3 根原木。 */
    private static void buildAngle() {
        say(TAG + "⑩ (j) 斜角 21°：斜线上的原木必须被拆、正东那一列必须没事");
        ShockwaveManager.clearAll();
        player.getCooldowns().removeCooldown(axe.getItem());
        clearAbove();

        // 21°：水平方向 = (cos21°, sin21°)（MC 里 yaw 与水平方向的关系见下）
        double rad = Math.toRadians(21.0D);
        double dirX = Math.cos(rad);
        double dirZ = Math.sin(rad);
        double perpX = -dirZ;
        double perpZ = dirX;

        // 玩家朝向：MC 的 yaw 0 = +Z，90 = -X ⇒ yaw = -atan2(dirX, dirZ)（度）
        float yaw = (float) -Math.toDegrees(Math.atan2(dirX, dirZ));
        player.moveTo(X0 + 0.5D, Y0, Z0 + 0.5D, yaw, 0.0F);
        player.tick();
        say(TAG + "      [J] 朝向设成 yaw=" + String.format("%.2f", yaw)
                + " ⇒ 视线 " + String.format("%.3f,%.3f", player.getLookAngle().x, player.getLookAngle().z));

        angleTargets.clear();
        angleControl.clear();
        // 正前方 6 格、横向偏 -1/0/+1 三根（这三根都在 6 格宽之内）
        for (int k = -1; k <= 1; k++) {
            BlockPos p = new BlockPos(
                    (int) Math.floor(X0 + 0.5D + dirX * 6.0D + perpX * k),
                    Y0,
                    (int) Math.floor(Z0 + 0.5D + dirZ * 6.0D + perpZ * k));
            level.setBlockAndUpdate(p, Blocks.OAK_LOG.defaultBlockState());
            angleTargets.add(p);
        }
        // 对照：正东（+X）那一列、与玩家同 z 的 6 格外那两格 —— 斜着走时**不该**被碰
        for (int d = 5; d <= 6; d++) {
            BlockPos p = new BlockPos(X0 + d, Y0, Z0 + 2 * d);
            angleControl.add(p);
            level.setBlockAndUpdate(p, Blocks.OAK_LOG.defaultBlockState());
        }
        say(TAG + "      [J] 斜线靶子 " + angleTargets.size() + " 根：" + angleTargets);
        say(TAG + "      [J] 对照（不该被拆）" + angleControl.size() + " 根：" + angleControl);
        useAxe(player);
    }

    /** 斜角场景的检查：斜线靶子全拆、对照点原样。 */
    private static void checkAngle() {
        int leftTargets = 0;
        for (BlockPos p : angleTargets) {
            if (!level.getBlockState(p).isAir()) {
                leftTargets++;
            }
        }
        int brokenControl = 0;
        for (BlockPos p : angleControl) {
            if (level.getBlockState(p).isAir()) {
                brokenControl++;
            }
        }
        failed += check("斜线靶子 " + angleTargets.size() + " 根全拆（剩 " + leftTargets + " 根）",
                leftTargets == 0);
        failed += check("正东那一列的对照点没被碰（被拆 " + brokenControl + " 根）",
                brokenControl == 0);
    }

'''

s = io.open(CHK, encoding="utf-8").read()
for i, (a, b) in enumerate([(T_OLD, T_NEW), (D_OLD, D_NEW), (IMPL_ANCHOR, IMPL + IMPL_ANCHOR)]):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
print("探针已加斜角场景；注意 T_ANGLE=%d 与 T_G2=%d 不撞车" % (900, 850))
