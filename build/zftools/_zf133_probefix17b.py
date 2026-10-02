# -*- coding: utf-8 -*-
"""_zf133_probefix17b.py —— 按盘上实际文本改（差一个全角括号）"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TIERS = r"E:\PotatoST\src\main\java\com\potatost\mod\ModTiers.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

T_OLD = "    public static final float STAR_STEEL_DAMAGE = 4.0F;"
T_NEW = "    public static final float STAR_STEEL_DAMAGE = 0.0F;"

T_DOC_OLD = """     * 取 <b>4.0</b> ⇒ 修饰符 4 + 8 = 12 ⇒ <b>显示总伤害 13.0</b>
     * （下界合金斧是 10；钻石剑是 7）。这个数**验收判据在探针里**：
     * `[HP]`/属性读数会打出 13.0，`_zf133_verify.py` 也盯着这两个常数不许漂。</p>"""
T_DOC_NEW = """     * ⚠ <b>1.21 的记账方式</b>：原版把"玩家空手伤害 1"放进属性**基础值**里，
     * 所以这个参数是"**武器相对空手额外加多少**" —— 原版斧传 6.0、原版镐传 1.0，
     * 它们都**不是**显示伤害。本档位取 <b>0.0F</b>：
     * 修饰符 = 0 + 档位加成 8 = 8 ⇒ 显示总伤害 = 基础值 1 + 8 = <b>9.0</b>。</p>
     *
     * <p><b>判据盯的是语义不是魔法数字</b>：探针断言的等式是
     * "组件里的修饰符 == 本参数 + 档位加成"，并把算出来的显示伤害打出来。
     * 想调攻击力只改这个数（+1 点 = 显示 +1），别处不用动。</p>"""

C_OLD = """            failed += check("斧子自带一条攻击力修饰符（加法值 " + (gearMod == null ? "?" : gearMod.amount())
                    + "，期望 12.0）",
                    gearMod != null && Math.abs(gearMod.amount() - 12.0D) < 1e-6);"""
C_NEW = """            // 判据盯语义：修饰符 == createAttributes 参数 + 档位加成（原版 DiggerItem 的算式）
            double expectMod = ModTiers.STAR_STEEL_DAMAGE + ModTiers.STAR_STEEL_AXE.getAttackDamageBonus();
            failed += check("斧子自带一条攻击力修饰符（加法值 "
                    + (gearMod == null ? "?" : gearMod.amount()) + "，= 参数 "
                    + ModTiers.STAR_STEEL_DAMAGE + " + 档位加成 "
                    + ModTiers.STAR_STEEL_AXE.getAttackDamageBonus() + " = " + expectMod + "）",
                    gearMod != null && Math.abs(gearMod.amount() - expectMod) < 1e-6);
            say(TAG + "      [ATTR] 按 1.21 的记账，游戏里显示的总伤害 = 1 + " + expectMod
                    + " = " + (1.0D + expectMod));"""

s = io.open(TIERS, encoding="utf-8").read()
for a, b in [(T_OLD, T_NEW), (T_DOC_OLD, T_DOC_NEW)]:
    n = s.count(a)
    assert n == 1, "ModTiers 锚点 %d：%r" % (n, a[:40])
    s = s.replace(a, b, 1)
io.open(TIERS, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] ModTiers 改好")

s = io.open(CHK, encoding="utf-8").read()
n = s.count(C_OLD)
assert n == 1, "探针锚点 %d" % n
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(C_OLD, C_NEW, 1))
print("[OK] 探针判据改好")
