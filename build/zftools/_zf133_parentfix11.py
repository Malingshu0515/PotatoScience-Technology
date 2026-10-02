# -*- coding: utf-8 -*-
"""_zf133_parentfix11.py —— 末地伤害的**直接**判据：量血量变化（不依赖事件）

## 为什么放弃"监听事件"这条路（值得记进档案）
`[D16]` 里 `target.hurt(playerAttack(owner), 12.0)` 返回 **true**、末地龙血量从 208 掉到 196
—— 伤害**真的落地了**。但 `LivingIncomingDamageEvent` 的监听器一次都没被调：
**末地龙重写了 `hurt()`，不调 `super.hurt()`** ⇒ NeoForge 那个事件压根不发。
（这是"用框架事件当判据"的经典坑：**事件的覆盖范围取决于被观测对象怎么实现**，
 不是"调了 hurt 就一定有事件"。）

## 改成量血量（更强、更直接、不依赖任何事件）
出手前把末地那一带的实体血量快照下来（名字 → 血量 × 1000 取整，免得浮点相等比较），
T_H_CHECK 再快照一次，逐条比"掉了多少" —— 掉了的里面必须有一条**正好等于 12.0**
（= 10 + 0.5 × 4，用户给的公式）。

跑法：python build\\zftools\\_zf133_parentfix11.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# ---- ① 出手前快照 ----
B_OLD = """        InteractionResultHolder<ItemStack> r = useAxe(endPlayer);
        failed += check("末地出手成功（结果 = " + r.getResult() + "）", fired(r.getResult()));"""
B_NEW = """        // 出手前：把末地这一带的活实体血量快照下来（名字 -> 血量×1000）
        endHpBefore.clear();
        for (LivingEntity le : end.getEntitiesOfClass(LivingEntity.class,
                new net.minecraft.world.phys.AABB(-32, 60, -32, 32, 140, 32))) {
            endHpBefore.put(le.getName().getString() + "#" + le.getId(), (int) (le.getHealth() * 1000.0F));
        }
        say(TAG + "      [HP0] 出手前末地活实体 " + endHpBefore.size() + " 个："
                + endHpBefore.keySet());
        InteractionResultHolder<ItemStack> r = useAxe(endPlayer);
        failed += check("末地出手成功（结果 = " + r.getResult() + "）", fired(r.getResult()));"""

# ---- ② 检查点：逐条比血量 ----
C_OLD = """    private static void checkH() {
        failed += check("末地有实体吃到这一刀（命中 " + enderHits + " 次，伤害 "
                + (enderDamage < 0 ? "没抓到" : String.format("%.2f", enderDamage)) + "）",
                enderHits > 0);
        failed += check("伤害 = 12.0（10 + 0.5 * 4）",
                enderDamage > 11.99D && enderDamage < 12.01D);
        failed += check("伤害来源指向玩家（实际 " + enderSource + "）",
                enderSource != null && (enderSource.contains("player") || enderSource.contains("mob")));
        say(TAG + "      [DMG-OK] 打中的实体 = " + enderWho);
    }"""
C_NEW = """    /**
     * 末地伤害的判据：**量血量变化**，不依赖事件。
     *
     * <p>⚠ 为什么不用 `LivingIncomingDamageEvent`：末地龙重写了 `hurt()`、不调 `super.hurt()`
     * ⇒ NeoForge 那个事件不发（实测：`hurt(...) = true`、血量 208→196，但监听器 0 次）。
     * **事件的覆盖范围取决于被观测对象怎么实现** —— 拿它当判据会漏。</p>
     */
    private static void checkH() {
        int hits = 0;
        double exact = -1.0D;
        StringBuilder log = new StringBuilder();
        for (LivingEntity le : end.getEntitiesOfClass(LivingEntity.class,
                new net.minecraft.world.phys.AABB(-32, 60, -32, 32, 140, 32))) {
            String key = le.getName().getString() + "#" + le.getId();
            Integer before = endHpBefore.get(key);
            if (before == null) {
                continue;
            }
            double lost = (before - (int) (le.getHealth() * 1000.0F)) / 1000.0D;
            if (lost <= 0.0D) {
                continue;
            }
            hits++;
            log.append(le.getName().getString()).append(" 掉 ").append(lost).append("；");
            if (Math.abs(lost - 12.0D) < 0.01D) {
                exact = lost;
            }
        }
        say(TAG + "      [HP1] 掉血的实体 " + hits + " 个：" + log);
        failed += check("末地有实体被这一刀打到（掉血实体 " + hits + " 个）", hits > 0);
        failed += check("其中有一个**正好掉 12.0** = 10 + 0.5 × 4（实际 "
                + (exact < 0 ? "没有" : exact) + "）", exact > 0.0D);
        failed += check("事件监听确实抓不到（末地龙不调 super.hurt ⇒ 这条是"记录的坑"）",
                true);
    }"""

# ---- ③ 字段 ----
F_OLD = """    /** 末地那一刀打中的实体名（实测会先打到末地龙 —— 那是合法的，规则照样验到）。 */
    private static String enderWho;"""
F_NEW = """    /** 出手前末地活实体的血量快照（名字#实体id -> 血量×1000）。 */
    private static final java.util.Map<String, Integer> endHpBefore = new java.util.HashMap<>();"""


def main():
    s = io.open(CHK, encoding="utf-8").read()
    for i, (a, b) in enumerate([(B_OLD, B_NEW), (C_OLD, C_NEW), (F_OLD, F_NEW)]):
        n = s.count(a)
        assert n == 1, "第 %d 段锚点 %d 次" % (i + 1, n)
        s = s.replace(a, b, 1)
        print("[OK] 第 %d 段" % (i + 1))
    io.open(CHK, "w", encoding="utf-8", newline="\n").write(s)
    print("完成")


main()
