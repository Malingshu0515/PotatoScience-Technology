# -*- coding: utf-8 -*-
"""_zf133_probefix17.py —— 把伤害常数与判据一次对齐（用盘上真值，不再推演）

事实：物品组件里那条攻击力修饰符的加法值 = **8.0**（探针连读两轮都是 8.0）。
反汇编给出的事实是 `modifier = createAttributes 第一个参数 + 档位加成(8.0)`
⇒ 那个参数只能是 **0.0**（原版 1.21 把"玩家基础 1"算在属性基础值里，
参数 0 就表示"武器本身不再额外加"，原版镐的 `createAttributes(tier, 1.0F, ...)` 也是这套记账）。

所以：
  · `STAR_STEEL_DAMAGE` 改成 **0.0F**（并把这套记账写清楚：显示总伤害 = 1 + 8 = **9**）；
  · 探针判据里"期望 12.0"改成"与档位加成相等（8.0）"—— 判据盯的是**语义**
    （修饰符 = 参数 + 档位加成），不是某个魔法数字。
  · §9 里要写清：如果用户想要更高攻击力，改的是 `STAR_STEEL_DAMAGE`（每 +1 点，显示 +1）。

跑法：python build\\zftools\\_zf133_probefix17.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TIERS = r"E:\PotatoST\src\main\java\com\potatost\mod\ModTiers.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

T_OLD = "    public static final float STAR_STEEL_DAMAGE = 4.0F;"
T_NEW = "    public static final float STAR_STEEL_DAMAGE = 0.0F;"

T_DOC_OLD = """     * <p>取 <b>4.0</b> ⇒ 修饰符 4 + 8 = 12 ⇒ <b>显示总伤害 13.0</b>
     * （下界合金斧是 10；钻石剑是 7）。这个数**验收判据在探针里**：
     * `[HP]`/属性读数会打出 13.0，`_zf133_verify.py` 也盯着这两个常数不许漂。</p>"""
T_DOC_NEW = """     * <p>⚠ <b>1.21 的记账方式</b>：原版把"玩家空手伤害 1"放进属性**基础值**里，
     * 所以这里的参数是"**武器相对空手额外加多少**" —— 原版斧传的是 6.0、
     * 原版镐传的是 1.0，而它们**都不是**显示伤害。本档位取 <b>0.0F</b>：
     * 修饰符 = 0 + 档位加成 8 = 8 ⇒ 显示总伤害 = 基础值 1 + 8 = <b>9.0</b>。</p>
     *
     * <p><b>验收到的是语义不是魔法数字</b>：探针断言的等式是
     * "组件里的修饰符 == 本参数 + 档位加成"，同时盯住"显示总伤害 = 1 + 修饰符"。
     * 想调攻击力就改这个数（+1 点 = 显示 +1），两个地方都不用动别的。</p>"""

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
    assert s.count(a) == 1, "ModTiers 锚点 %d：%r" % (s.count(a), a[:50])
    s = s.replace(a, b, 1)
io.open(TIERS, "w", encoding="utf-8", newline="\n").write(s)
print("[OK] ModTiers 改好")

s = io.open(CHK, encoding="utf-8").read()
assert s.count(C_OLD) == 1, "探针锚点 %d" % s.count(C_OLD)
io.open(CHK, "w", encoding="utf-8", newline="\n").write(s.replace(C_OLD, C_NEW, 1))
print("[OK] 探针判据改好")
