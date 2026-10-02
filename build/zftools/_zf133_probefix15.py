# -*- coding: utf-8 -*-
"""_zf133_probefix15.py —— 把**末地伤害**补上（这一块我压根没写，探针报"命中 0 次"是对的）

`ShockwaveManager` 里只有 `rangedDamage(n)` 这个纯函数，**没有任何地方调用它** ——
用户要的"在末地时冲击波将具有 10+0.5n 的远程伤害"整块缺失。
这不是探针的账，是产品代码的真缺口（而且探针一开就抓到了，正是它存在的意义）。

补法：在 `tick()` 的每格采样里，**末地**才做一次实体结算：
  · AABB = 该格方块（6 宽的那一列 × 该格高度）向外 0.5 格；
  · 排除发射者本人（用户没说要自伤）与已经被打的（每 tick 每格只打一次）；
  · 伤害源的直接实体是**发射者**（这样飘字/击杀归属都对），`playerAttack` 自带击退；
  · 伤害走 `LivingEntity#hurt`（与 `Player#attack` 同一条路，附魔/无敌帧都按原版规则走）。

⚠ 为什么放在 tick 的采样循环里而不是另起一套：波是"每 tick 扫一排"，
   实体结算跟着同一排走，代码只有一处、时序天然对齐。

跑法：python build\\zftools\\_zf133_probefix15.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"

# ---- 1) 采样循环里按格做实体结算 ----
OLD1 = """                BlockState state = wave.level.getBlockState(pos);
                if (state.isAir()) {
                    continue;
                }"""
NEW1 = """                BlockState state = wave.level.getBlockState(pos);
                // 末地才有的远程伤害（用户给的公式 10 + 0.5n）——实体结算与前缘同步推进
                if (wave.level.dimension() == Level.END) {
                    damageAt(wave, owner, pos);
                }
                if (state.isAir()) {
                    continue;
                }"""

# ---- 2) damageAt 实现 ----
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
     * 玩家基础伤害（{@link Wave#baseDamage}，快照 —— 用户说的是"n 为玩家基础伤害"，
     * 取发射时的值才不会一边打一边变）。</p>
     *
     * <p>几点刻意的选择（都写在这里，免得下次有人"顺手改"）：</p>
     * <ul>
     *   <li><b>直接实体是发射者</b>：飘字与击杀归属归他，与原版 {@code playerAttack} 一致；</li>
     *   <li><b>排除发射者自己</b>：用户没说要自伤，波从脚下出发、第一格就扫到自己；</li>
     *   <li>每格只对范围内的实体结算一次（同一 tick 里同一实体可能落在相邻采样格里，
     *       原版的无敌帧会挡掉重复伤害，但显式跳过一次更省事）。</li>
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
                continue;   // 创造模式玩家不吃伤害（原版规则）
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
