# -*- coding: utf-8 -*-
"""_zf133_probefix12.py —— 把三件事一次改对：伤害常数 / 波的高度基准 / 末地顺序

## ① 攻击力：原版公式是 `modifier = createAttributes 的第一个参数 + 档位加成`
（javap 反汇编 `DiggerItem.createAttributes` 得到：`fload_1` 后 `getAttackDamageBonus()` 再 `fadd`）
⇒ 我原先写的 8.0 + 档位 8.0 = 16 ⇒ 显示总伤害 1 + 16 = **17**（那是我文档里"14"的三倍偏差）。
改成 **4.0**：modifier = 4 + 8 = 12 ⇒ 显示总伤害 **13.0**（比下界合金斧的 10 高 3，符合"星璨钢在振金之下"的定位）。
顺带把 `ModTiers` 的注释改成**照反汇编写的事实**，不再写我记错的"斧基础 5"。

## ② 波的高度基准漂移（这是"波不拆方块"的**第二个**真因）
`tick()` 每 tick 现读 `owner.getBlockY()`。假玩家会把脚下那格拆掉 ⇒ 重力把它拉下去 /
（或者被别的东西顶起来）⇒ 采样原点跟着人跑，于是采到石台或空气。
用户要的语义是"**发射那一刻的高度**"，所以把高度**冻结**在 fire 那一刻。

## ③ 末地那一场挪到冷却/耐久门槛**之前**
末地那台玩家是用 `GameProfile` 新造的，跑完之后主玩家的状态会被带乱
（(g) 那条"耐久正好 120 ⇒ 出手"从 CONSUME 变成了 PASS）。
把末地放到时间线前半段（拆完石头墙之后、动冷却之前），主玩家就不会被中途换掉。

跑法：python build\\zftools\\_zf133_probefix12.py
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TIERS = r"E:\PotatoST\src\main\java\com\potatost\mod\ModTiers.java"
SHOCK = r"E:\PotatoST\src\main\java\com\potatost\mod\ShockwaveManager.java"
CHK = r"E:\PotatoST\src\main\java\com\potatost\mod\Zf133Check.java"

# ---------------- ① 伤害常数 + 注释 ----------------
TIERS_OLD = """    /**
     * 星璨钢斧的**档位伤害加成**（= {@code AxeItem.createAttributes} 的第一个数）。
     *
     * <p><b>用户给的数（原话）</b>：「1192耐久 挖掘等级钻石」。1192 直接就是耐久；
     * "挖掘等级钻石"＝"挖不动的方块"集合取 {@link BlockTags#INCORRECT_FOR_DIAMOND_TOOL}
     * （1.21 起档位里没有 level 整数，等级就是这张标签，与 ZF66 那两把同一条道理）。</p>
     *
     * <p>用户**没给攻击力**，这里按原版斧的写法取值：原版
     * {@code AxeItem.createAttributes(tier, 6.0F, -3.1F)} ⇒ 5 种原版斧的<b>总伤害都是 6 + 档位加成</b>
     * （木 7 / 石 8 / 铁 9 / 金 7 / 钻 9 / 下界合金 10）。本档位取 <b>8.0</b>
     * （介于下界合金 3.0 与"再高一档"之间，且是 6 的整数倍数感），
     * 于是游戏里显示 **14.0 = 玩家基础 1 + 斧基础 5 + 档位 8.0**；
     * 速度取原版斧同款 **-3.1**（比剑慢，这是斧的定位）。</p>
     *
     * <p>⚠ 这个数与"冲击波在末地的远程伤害 10 + 0.5n"里的 {@code n} 有关。
     * 实现把 {@code n} 读成"玩家的**基础攻击伤害**属性（含力量等玩家自身加成、不含手持武器）"，
     * 因为那正是"玩家基础伤害"逐字的读法 —— 已挂 §9 待用户确认（换个读法只改一个方法）。</p>
     */
    public static final float STAR_STEEL_DAMAGE = 8.0F;"""

TIERS_NEW = """    /**
     * 交给 {@code AxeItem.createAttributes(tier, 这个数, -3.1F)} 的**第一个参数**。
     *
     * <p><b>用户给的数（原话）</b>：「1192耐久 挖掘等级钻石」。1192 直接就是耐久；
     * "挖掘等级钻石"＝"挖不动的方块"集合取 {@link BlockTags#INCORRECT_FOR_DIAMOND_TOOL}
     * （1.21 起档位里没有 level 整数，等级就是这张标签，与 ZF66 那两把同一条道理）。
     * 攻击力用户没给，是本档位自己定的。</p>
     *
     * <p><b>⚠⚠ 这个参数不是"斧基础伤害"</b>（我第一版按记忆写成"6 + 档位"是错的）：
     * 反汇编 {@code DiggerItem.createAttributes} 得到的事实是</p>
     * <pre>
     *   new AttributeModifier(BASE_ATTACK_DAMAGE_ID, attackDamage + tier.getAttackDamageBonus(),
     *                         ADD_VALUE)
     * </pre>
     * <p>也就是说物品挂在主手上的**攻击力修饰符** = 这个参数 + 档位加成，
     * 而游戏里显示的总伤害 = 属性基础值 1 + 那个修饰符。
     * 取 <b>4.0</b> ⇒ 修饰符 4 + 8 = 12 ⇒ <b>显示总伤害 13.0</b>
     * （下界合金斧是 10；钻石剑是 7）。这个数**验收判据在探针里**：
     * `[HP]`/属性读数会打出 13.0，`_zf133_verify.py` 也盯着这两个常数不许漂。</p>
     *
     * <p>攻速照样照原版斧：{@link #STAR_STEEL_SPEED_MODIFIER} = -3.1（比剑慢，这是斧的定位）。</p>
     *
     * <p>⚠ 这个数与"冲击波在末地的远程伤害 10 + 0.5n"里的 {@code n} 有关。
     * 实现把 {@code n} 读成"玩家的**基础攻击伤害**属性（含力量等玩家自身加成、不含手持武器）"，
     * 因为那正是"玩家基础伤害"逐字的读法 —— 已挂 §9 待用户确认（换个读法只改一个方法）。</p>
     */
    public static final float STAR_STEEL_DAMAGE = 4.0F;"""

# ---------------- ② 波的高度冻结 ----------------
SHOCK_OLD = """        /** 主轴正负号：+1 / -1。 */
        private final int sign;"""
SHOCK_NEW = """        /** 主轴正负号：+1 / -1。 */
        private final int sign;

        /**
         * 采样的**高度基准**（发射那一刻玩家脚下的 y）。
         *
         * <p>⚠ 这是必须冻结的值：`tick()` 里如果每 tick 现读 `owner.getBlockY()`，
         * 玩家一被自己拆掉脚下的方块（重力）或被顶起来，采样层就跟着人跑 ——
         * 于是采到石台（被挡住）或空气（什么都拆不到）。探针实测过这两条，
         * 用户要的语义本来就是"**从我发射那一刻的高度**往前推"。</p>
         */
        private final int originY;"""

SHOCK_OLD2 = """        private Wave(ServerLevel level, UUID owner, double baseDamage,
                     boolean alongX, int sign) {
            this.level = level;
            this.owner = owner;
            this.baseDamage = baseDamage;
            this.alongX = alongX;
            this.sign = sign;
        }"""
SHOCK_NEW2 = """        private Wave(ServerLevel level, UUID owner, double baseDamage,
                     boolean alongX, int sign, int originY) {
            this.level = level;
            this.owner = owner;
            this.baseDamage = baseDamage;
            this.alongX = alongX;
            this.sign = sign;
            this.originY = originY;
        }"""

SHOCK_OLD3 = """        Wave wave = new Wave(level, player.getUUID(), baseAttackDamage(player), alongX, sign);"""
SHOCK_NEW3 = """        Wave wave = new Wave(level, player.getUUID(), baseAttackDamage(player), alongX, sign, y);"""

SHOCK_OLD4 = """        int ox = owner.getBlockX();
        int oy = owner.getBlockY();
        int oz = owner.getBlockZ();"""
SHOCK_NEW4 = """        int ox = owner.getBlockX();
        // ⚠ 高度用**发射那一刻冻结的 originY**，不是每 tick 现读玩家 Y（见 Wave#originY）
        int oy = wave.originY;
        int oz = owner.getBlockZ();"""

# ---------------- ③ 末地顺序 ----------------
CHK_ORDER_OLD = """            } else if (t == T_F) {
                buildF();"""
CHK_ORDER_NEW = """            } else if (t == T_H) {
                buildH();
            } else if (t == T_H_CHECK) {
                checkH();
            } else if (t == T_F) {
                buildF();"""

CHK_ORDER_OLD2 = """            } else if (t == T_H) {
                buildH();
            } else if (t == T_H_CHECK) {
                checkH();
            } else if (t == T_END) {"""
CHK_ORDER_NEW2 = """            } else if (t == T_END) {"""

CHK_TIME_OLD = """    private static final int T_I = 450;          // ⑤ 滚动窗口：先拆两次木头
    private static final int T_I_ALIVE = 600;    //    之后第 150 tick：必须还活着
    private static final int T_I_DEAD = 750;     //    之后第 300 tick：必须已散
    private static final int T_F = 760;          // ⑥ 冷却
    private static final int T_F_MID = 770;
    private static final int T_G = 780;          // ⑦ 耐久门槛
    private static final int T_G2 = 800;
    private static final int T_C = 820;          // ⑧ 创造模式
    private static final int T_H = 860;          // ⑨ 末地伤害
    private static final int T_H_CHECK = 900;
    private static final int T_END = 1080;"""
CHK_TIME_NEW = """    private static final int T_I = 450;          // ⑤ 滚动窗口：先拆两次木头
    private static final int T_I_ALIVE = 600;    //    之后第 150 tick：必须还活着
    private static final int T_I_DEAD = 750;     //    之后第 300 tick：必须已散
    // ⚠ 末地那一场必须在"冷却/耐久门槛"**之前**：它要另造一台假玩家，
    //   跑完之后主玩家的状态会被带乱（实测：(g) 的出手从 CONSUME 变成 PASS）。
    private static final int T_H = 760;          // ⑥ 末地伤害（另起一台玩家）
    private static final int T_H_CHECK = 800;
    private static final int T_F = 810;          // ⑦ 冷却
    private static final int T_F_MID = 820;
    private static final int T_G = 830;          // ⑧ 耐久门槛
    private static final int T_G2 = 850;
    private static final int T_C = 870;          // ⑨ 创造模式
    private static final int T_END = 1000;"""

# ---------------- ④ 探针里的两条判据改成"照反汇编的事实" ----------------
CHK_ATTR_OLD = """        failed += check("那一条的加法值 = 8.0（显示总伤害 = 1 + 5 + 8 = 14，实际 " + dmgSum + "）",
                Math.abs(dmgSum - 8.0D) < 1e-6);"""
CHK_ATTR_NEW = """        // 反汇编 DiggerItem.createAttributes 的事实：修饰符 = 参数(4.0) + 档位加成(8.0) = 12.0
        // 显示总伤害 = 属性基础值 1 + 12 = 13.0
        failed += check("那一条的加法值 = 4 + 档位 8 = 12.0（显示总伤害 13.0，实际 " + dmgSum + "）",
                Math.abs(dmgSum - 12.0D) < 1e-6);"""

CHK_END_OLD = """        double endAttr = endPlayer.getAttributeValue(Attributes.ATTACK_DAMAGE);
        failed += check("持斧：属性总值 = 4 + 斧基础 5 + 档位 8 = 17.0（力量 I 的 +3 也算，实际 "
                + endAttr + "）", Math.abs(endAttr - 17.0D) < 1e-6);"""
CHK_END_NEW = """        double endAttr = endPlayer.getAttributeValue(Attributes.ATTACK_DAMAGE);
        failed += check("持斧属性总值 = 1（基础）+ 12（武器修饰符）+ 3（力量 I）= 16.0（实际 "
                + endAttr + "）", Math.abs(endAttr - 16.0D) < 1e-6);"""


def main():
    jobs = [
        (TIERS, TIERS_OLD, TIERS_NEW, "① 伤害常数 8.0 -> 4.0 + 注释改成反汇编事实"),
        (SHOCK, SHOCK_OLD, SHOCK_NEW, "② Wave 加 originY 字段"),
        (SHOCK, SHOCK_OLD2, SHOCK_NEW2, "② Wave 构造器加参数"),
        (SHOCK, SHOCK_OLD3, SHOCK_NEW3, "② fire 传入冻结高度"),
        (SHOCK, SHOCK_OLD4, SHOCK_NEW4, "② tick 用冻结高度"),
        (CHK, CHK_TIME_OLD, CHK_TIME_NEW, "③ 时间线重排"),
        (CHK, CHK_ORDER_OLD, CHK_ORDER_NEW, "③ 末地提前派发"),
        (CHK, CHK_ORDER_OLD2, CHK_ORDER_NEW2, "③ 删掉原末地派发位置"),
        (CHK, CHK_ATTR_OLD, CHK_ATTR_NEW, "④ 属性判据改成 12.0"),
        (CHK, CHK_END_OLD, CHK_END_NEW, "④ 末地属性判据改成 16.0"),
    ]
    cache = {}
    for path, old, new, desc in jobs:
        s = cache.get(path) or io.open(path, encoding="utf-8").read()
        n = s.count(old)
        if n != 1:
            print("[FAIL] %s —— 锚点 %d 次：%r" % (desc, n, old.strip().split("\n")[0][:60]))
            sys.exit(1)
        cache[path] = s.replace(old, new, 1)
        print("[OK ] %s" % desc)
    for path, s in cache.items():
        io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    print("三件事都改完")


main()
