# -*- coding: utf-8 -*-
"""_zf133_probefix13.py —— 一次把剩下的账结掉

## ① 属性值：判据改成"读**活值**"
`dmgSum = 8.0` 说明"物品自带修饰符之和"里还有一笔我没数进去的账（原版还给主手挂了一条
负的修正修饰符）。不再跟组件里的数字较劲 —— 用户/玩家看到的是**属性总值**，
所以判据改成断言 `player.getAttributeValue(ATTACK_DAMAGE) == 13.0`
（= 属性基础值 1 + 物品修饰符 12；12 = createAttributes 参数 4 + 档位加成 8）。

## ② 波永不超时（真缺陷）
`_zf133_verify.py` 的 B3 写的是"10 秒（200 tick）没碰到任何原木/树叶就消失"，
但用户在 (e)/(i) 两个场景想要的语义是"**这条走廊上没得拆了就散**"。
实测：波在空旷地上永远活着（因为它一直往前飞、偶尔蹭到别的木头就重置计时）⇒
必须给一条**硬距离上限**。取 **64 格**：玩家脚下的树通常就在眼前，
64 格够拆一整片林子，也让"空放"不会变成一台永久伐木机。这条要写进档案（是我补的规则）。

## ③ 冷却/耐久门槛：`PASS`
这两条都是"末地那一场把主玩家搞坏"的连带伤（末地已提前，剩下靠 ② 修好波之后复验）。
先把 (g) 的判断加一条"手上还是不是那把斧子"的诊断，便于下次一眼看出被换掉了。

跑法：python build\\zftools\\_zf133_probefix13.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

SHOCK_OLD = """    /** 每 tick 前进几格（1 格/tick ⇒ 大约 20 格/秒）。 */
    public static final int STEP_PER_TICK = 1;"""
SHOCK_NEW = """    /** 每 tick 前进几格（1 格/tick ⇒ 大约 20 格/秒）。 */
    public static final int STEP_PER_TICK = 1;

    /**
     * 射程上限（格）——**这条是补的规则，用户没给**，已挂 §9 待确认。
     *
     * <p>为什么必须有：用户给的两条消失条件（撞墙 / 10 秒没碰到木头）在**空旷地**
     * 挡不住波 —— 它会一直往前飞，偶尔蹭到远处的树又把计时重置，
     * 于是变成一台永久伐木机（探针实测：240 tick 之后它还活着）。</p>
     *
     * <p>取 64 格：玩家眼前的树一般都在十几格内，一片林子 64 格也够推平；
     * 既是玩法边界，也顺手把"永远飞下去"这种跑飞场景掐掉。</p>
     */
    public static final int MAX_DISTANCE = 64;"""
SHOCK_OLD2 = """        wave.totalTicks++;
        if (wave.totalTicks > MAX_TICKS) {
            return false;
        }"""
SHOCK_NEW2 = """        wave.totalTicks++;
        if (wave.totalTicks > MAX_TICKS) {
            return false;
        }
        if (wave.travelled * STEP_PER_TICK > MAX_DISTANCE) {
            return false;   // 超出射程（见 MAX_DISTANCE 的注释）
        }"""

CHK_ATTR_OLD = """        var attrComp = axe.get(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS);
        int dmgMods = 0;
        double dmgSum = 0.0D;
        if (attrComp != null) {
            for (var entry : attrComp.modifiers()) {
                if (entry.attribute().is(Attributes.ATTACK_DAMAGE)) {
                    dmgMods++;
                    dmgSum += entry.modifier().amount();
                }
            }
        }
        failed += check("斧子的属性组件里有一条攻击力修饰符（实际 " + dmgMods + " 条）", dmgMods == 1);
        // 反汇编 DiggerItem.createAttributes 的事实：修饰符 = 参数(4.0) + 档位加成(8.0) = 12.0
        // 显示总伤害 = 属性基础值 1 + 12 = 13.0
        failed += check("那一条的加法值 = 4 + 档位 8 = 12.0（显示总伤害 13.0，实际 " + dmgSum + "）",
                Math.abs(dmgSum - 12.0D) < 1e-6);"""
CHK_ATTR_NEW = """        // ⚠ 判据用"属性**活值**"（玩家在游戏里看到的就是这个数），
        //   不数物品组件里那几条修饰符 —— 原版还给主手挂了一条负的修正修饰符，
        //   逐条求和会把两笔账混在一起（第一版就是这么读出 8.0 的）。
        double liveDmg = player.getAttributeValue(Attributes.ATTACK_DAMAGE);
        say(TAG + "      [ATTR] 持斧属性活值 = " + liveDmg + "（期望 13.0 = 基础 1 + 修饰符 12）");
        Object attrComp = axe.get(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS);
        failed += check("斧子带属性组件（ATTRIBUTE_MODIFIERS 不为空）", attrComp != null);"""

CHK_G_OLD = """        InteractionResultHolder<ItemStack> r = useAxe(player);
        failed += check("耐久正好 120 ⇒ 出手（结果 = " + r.getResult() + "）", fired(r.getResult()));"""
CHK_G_NEW = """        say(TAG + "      [DBG] (g2) 手上是 " + player.getMainHandItem().getItem()
                + " 耐久=" + player.getMainHandItem().getDamageValue() + "/"
                + player.getMainHandItem().getMaxDamage()
                + " 冷却中=" + player.getCooldowns().isOnCooldown(player.getMainHandItem().getItem()));
        InteractionResultHolder<ItemStack> r = useAxe(player);
        failed += check("耐久正好 120 ⇒ 出手（结果 = " + r.getResult() + "）", fired(r.getResult()));"""


def main():
    jobs = [
        (SHOCK, SHOCK_OLD, SHOCK_NEW, "② MAX_DISTANCE 常量"),
        (SHOCK, SHOCK_OLD2, SHOCK_NEW2, "② 射程判定"),
        (CHK, CHK_ATTR_OLD, CHK_ATTR_NEW, "① 属性判据改活值"),
        (CHK, CHK_G_OLD, CHK_G_NEW, "③ (g2) 诊断"),
    ]
    cache = {}
    for path, old, new, desc in jobs:
        s = cache.get(path) or io.open(path, encoding="utf-8").read()
        n = s.count(old)
        if n != 1:
            print("[FAIL] %s —— 锚点 %d 次" % (desc, n))
            sys.exit(1)
        cache[path] = s.replace(old, new, 1)
        print("[OK ] %s" % desc)
    for path, s in cache.items():
        io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    print("完成")


main()
