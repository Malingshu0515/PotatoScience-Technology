# -*- coding: utf-8 -*-
"""_zf134_apply.py —— 一次性把 ShockwaveManager 改成任意角度（带"行边界"修正）

## 前面五次为什么都没成（逐条如实记，都是同一类问题）
| 次 | 现象 | 真因 |
|---|---|---|
| 1 | 锚点 0 命中、静默不动 | **凭记忆写长锚点**，一个 `**` 之差（§4.90 老坑） |
| 2 | 四处切片成功、断言拦下、没写盘 | 漏了 `spawnParticles`（断言**正确**地拦住了半成品） |
| 3/4 | 同上 | 每次从盘上重读 ⇒ 上一次的成果丢掉 |
| 5 | `alongX（1 次）` 拦下 | 我在**新 javadoc 里**写了旧字段名 ⇒ 判据自己撞自己 |
| 6 | `mainCoord（1 次）` 拦下 | 替换文本以 `}\n` 结尾，而切片**不含终点那一行的换行** ⇒ 两行被粘成一行、`mainCoord` 方法没被吃掉 |

## 这一版的规矩
① 复核前**先剥注释**（javadoc 里提旧字段是合法的）；
② 切片**连终点行的换行一起吃掉**（`end` 用带 `\n` 的形式）；
③ 每条禁令都断言"代码里 0 次"，任何一条不过就**整体不写盘**。

跑法：python build\\zftools\\_zf134_apply.py
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

WAVE = '''    /**
     * 一道冲击波。字段全是**值**（Level 引用只在服务端活着时用，玩家一退就丢）。
     *
     * <p><b>方向用单位向量表示</b>（0.11 ZF134 起）—— 用户原话
     * 「冲击目前只会朝正方向（正东西南北）改成可以有角度的（比如东南 21° 这种）」。
     * 旧版只存了「主轴 + 正负号」两个字段，采样点只能落在 8 个方格方向上。</p>
     */
    private static final class Wave {

        private final ServerLevel level;
        private final UUID owner;
        /** 玩家基础攻击伤害的快照（发射那一刻算一次，见类注释）。 */
        private final double baseDamage;

        /** 水平朝向的**单位向量**（`dirX * dirX + dirZ * dirZ = 1`）。 */
        private final double dirX;
        private final double dirZ;

        /**
         * 采样的**高度基准**（发射那一刻**玩家脚下**的 y）。
         *
         * <p>⚠ 这是必须冻结的值：`tick()` 里如果每 tick 现读 `owner.getBlockY()`，
         * 玩家一被自己拆掉脚下的方块（重力）或被顶起来，采样层就跟着人跑 ——
         * 于是采到石台（被挡住）或空气（什么都拆不到）。探针实测过这两条，
         * 用户要的语义本来就是「从我发射那一刻的高度往前推」。</p>
         */
        private final int originY;

        /** 已经走过几格（0 = 起手那一格）。 */
        private int travelled;
        /** 从上一次拆到东西起过了几 tick。 */
        private int sinceBreak;
        /** 总共活了几 tick（兜底用）。 */
        private int totalTicks;

        private Wave(ServerLevel level, UUID owner, double baseDamage,
                     double dirX, double dirZ, int originY) {
            this.level = level;
            this.owner = owner;
            this.baseDamage = baseDamage;
            this.dirX = dirX;
            this.dirZ = dirZ;
            this.originY = originY;
        }

        /** 阵面前缘中心的 X（格，**双精度** —— 斜着走才有意义）。 */
        private double frontX(double originX) {
            return originX + dirX * travelled * STEP_PER_TICK;
        }

        /** 阵面前缘中心的 Z。 */
        private double frontZ(double originZ) {
            return originZ + dirZ * travelled * STEP_PER_TICK;
        }
    }

'''

FIRE = '''    public static boolean fire(ServerPlayer player, ItemStack axe) {
        ServerLevel level = player.serverLevel();
        double ox = player.getX();
        double oz = player.getZ();
        int x = player.getBlockX();
        int y = player.getBlockY();
        int z = player.getBlockZ();

        // 水平朝向：取视线在水平面上的投影再归一化 ⇒ **任意角度**（ZF134）。
        // ⚠ 丢掉竖直分量是刻意的：这是「朝面向横推一道墙」，不是弹道。
        double dx = player.getLookAngle().x;
        double dz = player.getLookAngle().z;
        double len = Math.sqrt(dx * dx + dz * dz);
        if (len < 1.0E-4D) {
            // 垂直往上/往下看时水平投影退化 ⇒ 退到「玩家朝向那一面」（用 yaw 算单位向量）
            float yaw = player.getYRot() * ((float) Math.PI / 180.0F);
            dx = -Math.sin(yaw);
            dz = Math.cos(yaw);
            len = 1.0D;
        }
        double dirX = dx / len;
        double dirZ = dz / len;

        Wave wave = new Wave(level, player.getUUID(), baseAttackDamage(player), dirX, dirZ, y);
        WAVES.add(wave);

        // 起手的视听：一声闷响 + 一排粒子（用户要「炫酷」，但起手只发一批）
        level.playSound(null, x + 0.5D, y + 0.5D, z + 0.5D,
                SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 1.1F, 1.4F);
        spawnParticles(wave, ox, oz, y, true);
        ShockwaveNetworking.broadcastWave(player, x, y, z, dirX, dirZ);
        return true;
    }

'''

TICK = '''        // ⚠ 高度用**发射那一刻冻结的 originY**，不是每 tick 现读玩家 Y（见 Wave#originY）
        int oy = wave.originY;

        // 阵面前缘中心（双精度）；每条采样线 = 前缘 + 法线 × 横向偏移（ZF134：任意角度）
        double frontX = wave.frontX(owner.getX());
        double frontZ = wave.frontZ(owner.getZ());
        // 左手法线：把朝向转 90°。朝向为 +X 时它是 (0, +1) —— 与旧版「沿 z 铺 -3..+2」逐字一致。
        double perpX = -wave.dirZ;
        double perpZ = wave.dirX;

        boolean broke = false;
        boolean blocked = false;
        for (int lateral = 0; lateral < WIDTH; lateral++) {
            double lat = lateral - HALF_WIDTH;      // -3 .. +2（偶数宽的对称铺法）
            for (int dy = 0; dy < HEIGHT; dy++) {
                int bx = (int) Math.floor(frontX + perpX * lat);
                int bz = (int) Math.floor(frontZ + perpZ * lat);
                int by = oy + dy;
                BlockPos pos = new BlockPos(bx, by, bz);
                BlockState state = wave.level.getBlockState(pos);
'''

BREAK = '''        if (broke) {
            wave.sinceBreak = 0;
            wave.level.playSound(null, frontX, oy + 1.0D, frontZ,
                    SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 0.7F, 0.7F);
'''

PARTICLES = '''    /**
     * 每 2 tick 一批粒子：前缘一道弧 + 上下两条星屑（全走服务端标准粒子包）。
     *
     * <p>采样线与 {@code tick()} **用同一套公式**（前缘 + 法线 × 横向偏移）——
     * 这样「斜着放」时粒子也跟着斜，视觉与破坏范围对得上。</p>
     */
    private static void spawnParticles(Wave wave, double originX, double originZ, int oy, boolean launch) {
        double frontX = wave.frontX(originX);
        double frontZ = wave.frontZ(originZ);
        double perpX = -wave.dirZ;
        double perpZ = wave.dirX;
        boolean inEnd = wave.level.dimension() == Level.END;
        boolean anyWood = false;
        BlockState woodState = null;
        double woodX = 0.0D;
        double woodZ = 0.0D;

        for (int lateral = 0; lateral < WIDTH; lateral++) {
            double lat = lateral - HALF_WIDTH;
            double px = frontX + perpX * lat;
            double pz = frontZ + perpZ * lat;
            double py = oy + 0.5D;

            // 前缘：横扫粒子（原版剑气那个）
            wave.level.sendParticles(ParticleTypes.SWEEP_ATTACK, px, py + 0.6D, pz, 1, 0.0D, 0.0D, 0.0D, 0.0D);
            // 星屑：上下各一颗（「星璨」的那点意思）
            ParticleOptions star = (lateral % 3 == 0 && inEnd) ? ParticleTypes.END_ROD : ParticleTypes.CRIT;
            wave.level.sendParticles(star, px, py + 0.2D, pz, 1, 0.15D, 0.15D, 0.15D, 0.0D);
            wave.level.sendParticles(ParticleTypes.END_ROD, px, py + HEIGHT - 0.3D, pz, 1, 0.1D, 0.1D, 0.1D, 0.0D);
            if (launch || lateral % 2 == 0) {
                wave.level.sendParticles(ParticleTypes.CLOUD, px, py + 0.05D, pz, 1, 0.2D, 0.05D, 0.2D, 0.01D);
            }
        }

        // 拆到木头时补一点木屑（视觉上「这排树被啃掉了」）——
        // ⚠ 沿 6 条采样线找**第一处**木头：斜着走时「前缘正中那一格」未必有东西
        if (!launch) {
            for (int lateral = 0; lateral < WIDTH && !anyWood; lateral++) {
                double lat = lateral - HALF_WIDTH;
                BlockPos probe = new BlockPos(
                        (int) Math.floor(frontX + perpX * lat), oy + 1,
                        (int) Math.floor(frontZ + perpZ * lat));
                BlockState state = wave.level.getBlockState(probe);
                if (isChoppable(state)) {
                    anyWood = true;
                    woodState = state;
                    woodX = probe.getX() + 0.5D;
                    woodZ = probe.getZ() + 0.5D;
                }
            }
            if (anyWood) {
                wave.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, woodState),
                        woodX, oy + 1.5D, woodZ, 6, 0.4D, 0.4D, 0.4D, 0.05D);
            }
        }
    }

'''

# (起点, 终点, 新文本, 标签) —— 终点按"整行含换行"匹配，避免粘行
JOBS = [
    ("    /** 一道冲击波。字段全是**值**",
     "        /** 主轴坐标（当前采样位置）。 */\n", WAVE, "Wave 整段"),
    ("    public static boolean fire(ServerPlayer player",
     "    /** 推进所有冲击波；由", FIRE, "fire() 整段"),
    ("        int ox = owner.getBlockX();",
     "                BlockState state = wave.level.getBlockState(pos);\n", TICK, "tick() 采样头"),
    ("        if (broke) {",
     "        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {", BREAK, "break 音效"),
    ("    /** 每 2 tick 一批粒子",
     "    /** 当前还有几道波", PARTICLES, "spawnParticles 整段"),
]


def strip_comments(src):
    out = re.sub(r"/\*[\s\S]*?\*/", "", src)
    return re.sub(r"//[^\n]*", "", out)


def main():
    s = io.open(M, encoding="utf-8").read()
    print("原始：%d 字符" % len(s))

    for start, end, new, label in JOBS:
        assert s.count(start) == 1, "%s 起点 %d 次" % (label, s.count(start))
        assert s.count(end) == 1, "%s 终点 %d 次" % (label, s.count(end))
        i, j = s.index(start), s.index(end) + len(end)
        assert j > i, "%s 终点在起点前" % label
        s = s[:i] + new + s[j:]
        print("[OK ] %-20s -> %d 字符" % (label, len(s)))

    code = strip_comments(s)
    # ⚠ 残留的 mainCoord 方法体 + 旧类收尾的 } 由 _zf134_apply2.py 吃掉（见那个脚本的注释）。
    #   这一刀只保证"这一刀该管的"都干净，跨刀的尾巴交给下一刀 —— 否则一刀永远过不去。
    for dead in ("alongX", "int main =", "wave.sign"):
        assert dead not in code, "代码里还残留：%s（%d 次）" % (dead, code.count(dead))
    for live in ("dirX", "dirZ", "frontX(", "frontZ(", "perpX", "perpZ"):
        assert live in s, "新字段没出现：%s" % live
    print("[OK ] 代码里旧字段全清、新字段齐全（注释里提到旧字段是合法的）")

    io.open(M, "w", encoding="utf-8", newline="\n").write(s)
    body = io.open(M, encoding="utf-8").read()
    assert strip_comments(body).count("alongX") == 0, "写盘后复核失败"
    print("已写盘：%d 字符（dirX %d 次 / perpX %d 次）" % (len(body), body.count("dirX"), body.count("perpX")))


main()
