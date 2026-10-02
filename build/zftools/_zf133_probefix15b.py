# -*- coding: utf-8 -*-
"""_zf133_probefix15b.py —— 末地伤害补丁（按盘上实际的 trace 版锚点）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

OLD1 = """                BlockState state = wave.level.getBlockState(pos);
                boolean tr = TRACE;"""
NEW1 = """                BlockState state = wave.level.getBlockState(pos);
                // 末地才有的远程伤害（用户给的公式 10 + 0.5n）：实体结算与前缘同步推进
                if (wave.level.dimension() == Level.END) {
                    damageAt(wave, owner, pos);
                }
                boolean tr = TRACE;"""

OLD2 = """    /** 冲击波在末地的远程伤害：{@code 10 + 0.5n}（用户给的公式）。 */
    public static double rangedDamage(double baseAttackDamage) {
        return 10.0D + 0.5D * baseAttackDamage;
    }"""
NEW2 = """    /** 冲击波在末地的远程伤害：{@code 10 + 0.5n}（用户给的公式）。 */
    public static double rangedDamage(double baseAttackDamage) {
        return 10.0D + 0.5D * baseAttackDamage;
    }

    /**
     * 在某一格上结算一次冲击波伤害（**只在末地调用**）。
     *
     * <p>伤害值 = {@link #rangedDamage}{@code (n)}，其中 {@code n} 是**发射那一刻**读到的
     * 玩家基础伤害（{@link Wave#baseDamage} 是快照 —— 用户说的是"n 为玩家基础伤害"，
     * 取发射时的值才不会一边打一边变）。</p>
     *
     * <p>几点刻意的选择（写在这里，免得下次有人顺手改）：</p>
     * <ul>
     *   <li><b>直接实体是发射者</b>：飘字与击杀归属归他，与原版 {@code playerAttack} 一致；</li>
     *   <li><b>排除发射者自己</b>：用户没说要自伤，而波从脚下出发、第一格就扫到自己；</li>
     *   <li><b>创造模式玩家不吃伤害</b>：原版规则；</li>
     *   <li>同一 tick 里相邻采样格可能框住同一个实体，原版无敌帧会挡掉重复伤害。</li>
     * </ul>
     */
    private static void damageAt(Wave wave, ServerPlayer owner, BlockPos pos) {
        double damage = rangedDamage(wave.baseDamage);
        AABB box = new AABB(pos).inflate(0.5D);
        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {
            if (target.getUUID().equals(wave.owner) || !target.isAlive()) {
                continue;
            }
            if (target instanceof Player other && other.isCreative()) {
                continue;
            }
            target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);
        }
    }"""

s = io.open(SHOCK, encoding="utf-8").read()
for i, (a, b) in enumerate([(OLD1, NEW1), (OLD2, NEW2)]):
    n = s.count(a)
    assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
    s = s.replace(a, b, 1)
    print("[OK] 第 %d 段" % (i + 1))
io.open(SHOCK, "w", encoding="utf-8", newline="\n").write(s)
print("末地伤害已补上")
