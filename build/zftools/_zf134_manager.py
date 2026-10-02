# -*- coding: utf-8 -*-
"""_zf134_manager.py —— 冲击波改成**任意水平角度**（不再是正东南西北）

用户原话：「冲击目前只会朝正方向（正东西南北）改成可以有角度的（比如东南 21° 这种）」。

## 原来的结构为什么只有四个方向
`Wave` 里存的是 `boolean alongX` + `int sign`（"主轴 + 正负"），
`mainCoord()` 直接在主轴上加减整数 ⇒ 采样点只能落在 8 个方格方向之一。

## 新结构：**方向向量 + 垂直方向的固定网格**（关键：正方向的行为一模一样）
```java
double dirX, dirZ;                 // 归一化的水平朝向（|dir| = 1）
double perpX = -dirZ, perpZ = dirX;  // 左手法线 = 波阵面横铺的方向
double frontX = originX + dirX * travelled;
double frontZ = originZ + dirZ * travelled;
// 6 条采样线：横向偏移走**固定单位网格**（-3..+2），再整体旋转到朝向
double lat = lateral - HALF_WIDTH;            // -3 .. +2
double sx = frontX + perpX * lat;
double sz = frontZ + perpZ * lat;
```
**为什么正方向仍然精确等价**：朝向为 +X 时 `perp = (0, +1)`（因为 `perp = (-dirZ, dirX)`），
于是 `sx = frontX`、`sz = frontZ + lat` —— 与旧代码逐字一致。
朝向为 +Z 时 `perp = (-1, 0)` ⇒ `sx = frontX - lat`，与旧的 `ox + offset` 同构（整体对称）。
⇒ 旧探针的那些断言（宽度 6 / 撞墙 / 末地伤害）一个字都不用改就该继续过。

## 顺带改的两处（都与"方向"有关）
- `ShockwaveNetworking`：包里原来带 `alongX + sign`，现在带 `dirX + dirZ`（两个 double）；
- `client/ShockwaveRenderer`：光墙原来是"沿 x 或沿 z 的一面平板"，现在按
  `(front ± perp * half)` 直接算出两个端点 ⇒ **斜着也能正对朝向**。

跑法：python build\\zftools\\_zf134_manager.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
M = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD_WAVE = """    /** 一道冲击波。字段全是**值**（Level 引用只在服务端活着时用，玩家一退就丢）。 */
    private static final class Wave {

        private final ServerLevel level;
        private final UUID owner;
        /** 玩家基础攻击伤害的快照（发射那一刻算一次，见类注释）。 */
        private final double baseDamage;

        /** 主轴：true = 沿 x（东西向），false = 沿 z（南北向）。 */
        private final boolean alongX;
        /** 主轴正负号：+1 / -1。 */
        private final int sign;

        /**
         * 采样的**高度基准**（发射那一刻玩家脚下的 y）。
         *
         * <p>⚠ 这是必须冻结的值：`tick()` 里如果每 tick 现读 `owner.getBlockY()`，
         * 玩家一被自己拆掉脚下的方块（重力）或被顶起来，采样层就跟着人跑 ——
         * 于是采到石台（被挡住）或空气（什么都拆不到）。探针实测过这两条，
         * 用户要的语义本来就是"**从我发射那一刻的高度**往前推"。</p>
         */
        private final int originY;

        /** 已经走过几格（0 = 起手那一格）。 */
        private int travelled;
        /** 从上一次拆到东西起过了几 tick。 */
        private int sinceBreak;
        /** 总共活了几 tick（兜底用）。 */
        private int totalTicks;

        private Wave(ServerLevel level, UUID owner, double baseDamage,
                     boolean alongX, int sign, int originY) {
            this.level = level;
            this.owner = owner;
            this.baseDamage = baseDamage;
            this.alongX = alongX;
            this.sign = sign;
            this.originY = originY;
        }

        /** 主轴坐标（当前采样位置）。 */
        private int mainCoord(int origin) {
            return origin + sign * travelled * STEP_PER_TICK;
        }
    }"""

NEW_WAVE = """    /**
     * 一道冲击波。字段全是**值**（Level 引用只在服务端活着时用，玩家一退就丢）。
     *
     * <p><b>方向用单位向量表示</b>（0.11 ZF134 起）—— 用户原话
     * 「冲击目前只会朝正方向（正东西南北）改成可以有角度的（比如东南 21° 这种）」。
     * 旧版存的是 `alongX + sign`（主轴 + 正负），采样点只能落在 8 个方格方向上。</p>
     */
    private static final class Wave {

        private final ServerLevel level;
        private final UUID owner;
        /** 玩家基础攻击伤害的快照（发射那一刻算一次，见类注释）。 */
        private final double baseDamage;

        /** 水平朝向的**单位向量**（{@code dirX² + dirZ² = 1}）。 */
        private final double dirX;
        private final double dirZ;

        /**
         * 采样的**高度基准**（发射那一刻玩家脚下的 y）。
         *
         * <p>⚠ 这是必须冻结的值：`tick()` 里如果每 tick 现读 `owner.getBlockY()`，
         * 玩家一被自己拆掉脚下的方块（重力）或被顶起来，采样层就跟着人跑 ——
         * 于是采到石台（被挡住）或空气（什么都拆不到）。探针实测过这两条，
         * 用户要的语义本来就是"**从我发射那一刻的高度**往前推**"。</p>
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

        /** 阵面前缘的中心（世界坐标，格；**双精度** —— 斜着走才有意义）。 */
        private double frontX(double originX) {
            return originX + dirX * travelled * STEP_PER_TICK;
        }

        private double frontZ(double originZ) {
            return originZ + dirZ * travelled * STEP_PER_TICK;
        }
    }"""

OLD_FIRE = """    public static boolean fire(ServerPlayer player, ItemStack axe) {
        ServerLevel level = player.serverLevel();
        int x = player.getBlockX();
        int y = player.getBlockY();
        int z = player.getBlockZ();
        double dx = player.getLookAngle().x;
        double dz = player.getLookAngle().z;
        boolean alongX = Math.abs(dx) >= Math.abs(dz);
        int sign = (alongX ? dx : dz) >= 0.0D ? 1 : -1;

        Wave wave = new Wave(level, player.getUUID(), baseAttackDamage(player), alongX, sign, y);
        WAVES.add(wave);

        // 起手的视听：一声闷响 + 一排粒子（用户要"炫酷"，但起手只发一批）
        level.playSound(null, x + 0.5D, y + 0.5D, z + 0.5D,
                SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 1.1F, 1.4F);
        spawnParticles(wave, player, x, y, z, true);
        ShockwaveNetworking.broadcastWave(player, x, y, z, alongX, sign);
        return true;
    }"""

NEW_FIRE = """    public static boolean fire(ServerPlayer player, ItemStack axe) {
        ServerLevel level = player.serverLevel();
        double ox = player.getX();
        double oz = player.getZ();
        int x = player.getBlockX();
        int y = player.getBlockY();
        int z = player.getBlockZ();

        // 水平朝向：取视线在水平面上的投影再归一化 ⇒ **任意角度**（ZF134）。
        // ⚠ 竖直分量丢掉是刻意的：这是"朝面向横推一道墙"，不是弹道。
        double dx = player.getLookAngle().x;
        double dz = player.getLookAngle().z;
        double len = Math.sqrt(dx * dx + dz * dz);
        if (len < 1.0E-4D) {
            // 垂直往下/上看时水平投影退化 ⇒ 退到"玩家朝向的那一面"（用 yaw 算单位向量）
            float yaw = player.getYRot() * ((float) Math.PI / 180.0F);
            dx = -Math.sin(yaw);
            dz = Math.cos(yaw);
            len = 1.0D;
        }
        double dirX = dx / len;
        double dirZ = dz / len;

        Wave wave = new Wave(level, player.getUUID(), baseAttackDamage(player), dirX, dirZ, y);
        WAVES.add(wave);

        // 起手的视听：一声闷响 + 一排粒子（用户要"炫酷"，但起手只发一批）
        level.playSound(null, x + 0.5D, y + 0.5D, z + 0.5D,
                SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 1.1F, 1.4F);
        spawnParticles(wave, ox, oz, y, true);
        ShockwaveNetworking.broadcastWave(player, x, y, z, dirX, dirZ);
        return true;
    }"""

OLD_TICK_HEAD = """        int ox = owner.getBlockX();
        // ⚠ 高度用**发射那一刻冻结的 originY**，不是每 tick 现读玩家 Y（见 Wave#originY）
        int oy = wave.originY;
        int oz = owner.getBlockZ();

        boolean broke = false;
        boolean blocked = false;
        for (int lateral = 0; lateral < WIDTH; lateral++) {
            int offset = lateral - HALF_WIDTH;      // -3 .. +2（偶数宽的对称铺法）
            for (int dy = 0; dy < HEIGHT; dy++) {
                int bx = wave.alongX ? wave.mainCoord(ox) : ox + offset;
                int bz = wave.alongX ? oz + offset : wave.mainCoord(oz);
                int by = oy + dy;
                BlockPos pos = new BlockPos(bx, by, bz);"""

NEW_TICK_HEAD = """        // ⚠ 高度用**发射那一刻冻结的 originY**，不是每 tick 现读玩家 Y（见 Wave#originY）
        int oy = wave.originY;

        // 阵面前缘中心（双精度）；采样线 = 前缘 + 法线 × 横向偏移（ZF134：任意角度）
        double frontX = wave.frontX(owner.getX());
        double frontZ = wave.frontZ(owner.getZ());
        // 左手法线：把朝向转 90°。朝向为 +X 时它是 (0, +1)，与旧版"沿 z 铺 -3..+2"逐字一致。
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
                BlockPos pos = new BlockPos(bx, by, bz);"""

OLD_BREAK = """        if (broke) {
            wave.sinceBreak = 0;
            wave.level.playSound(null, wave.mainCoord(ox), oy + 1.0D,
                    wave.alongX ? oz : wave.mainCoord(oz),
                    SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 0.7F, 0.7F);
        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {"""

NEW_BREAK = """        if (broke) {
            wave.sinceBreak = 0;
            wave.level.playSound(null, frontX, oy + 1.0D, frontZ,
                    SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 0.7F, 0.7F);
        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {"""

OLD_PARTICLES = """    /** 每 2 tick 一批粒子：前缘一道弧 + 上下两条星屑（全走服务端标准粒子包）。 */
    private static void spawnParticles(Wave wave, ServerPlayer owner, int ox, int oy, int oz, boolean launch) {
        int main = wave.alongX ? wave.mainCoord(ox) : wave.mainCoord(oz);
        int lateralBase = wave.alongX ? oz : ox;
        boolean inEnd = wave.level.dimension() == Level.END;

        for (int lateral = 0; lateral < WIDTH; lateral++) {
            int offset = lateral - HALF_WIDTH;
            double px = wave.alongX ? main + 0.5D : ox + offset + 0.5D;
            double pz = wave.alongX ? lateralBase + offset + 0.5D : main + 0.5D;
            double py = oy + 0.5D;"""

NEW_PARTICLES = """    /** 每 2 tick 一批粒子：前缘一道弧 + 上下两条星屑（全走服务端标准粒子包）。 */
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
            double py = oy + 0.5D;"""

OLD_WOOD = """        // 拆到木头时补一点木屑（视觉上"这排树被啃掉了"）
        if (!launch) {
            BlockPos below = new BlockPos(
                    wave.alongX ? main : lateralBase,
                    oy + 1,
                    wave.alongX ? lateralBase : main);
            BlockState state = wave.level.getBlockState(below);
            if (isChoppable(state)) {
                wave.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state),
                        below.getX() + 0.5D, below.getY() + 0.5D, below.getZ() + 0.5D,
                        6, 0.4D, 0.4D, 0.4D, 0.05D);
            }
        }
    }"""

NEW_WOOD = """        // 拆到木头时补一点木屑（视觉上"这排树被啃掉了"）——
        // ⚠ 沿着 6 条采样线找**第一处**木头（斜着走时"前缘正中那一格"未必有东西）
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
    }"""


def main():
    s = io.open(M, encoding="utf-8").read()
    jobs = [(OLD_WAVE, NEW_WAVE, "Wave：alongX+sign → dirX/dirZ 单位向量"),
            (OLD_FIRE, NEW_FIRE, "fire：视线水平投影归一化 + 退化兜底"),
            (OLD_TICK_HEAD, NEW_TICK_HEAD, "tick：前缘 + 法线 × 横向偏移"),
            (OLD_BREAK, NEW_BREAK, "拆到木头的音效位置"),
            (OLD_PARTICLES, NEW_PARTICLES, "粒子：按法线铺"),
            (OLD_WOOD, NEW_WOOD, "木屑：沿采样线找第一处木头")]
    for a, b, desc in jobs:
        n = s.count(a)
        assert n == 1, "%s 锚点 %d 次" % (desc, n)
        s = s.replace(a, b, 1)
        print("[OK ] %s" % desc)

    # 复核：旧字段一个都不许剩
    for dead in ("alongX", "mainCoord(", "wave.alongX", "int main ="):
        assert dead not in s, "还残留旧字段：%s" % dead
    print("[OK ] 旧字段已清干净（alongX / mainCoord 都不在了）")

    io.open(M, "w", encoding="utf-8", newline="\n").write(s)
    print("ShockwaveManager 已改成任意角度")
