package com.potatost.mod;

import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.block.Block;

/**
 * 钛合金（轻质钛合金）工具的**档位**（0.10 ZF66）。
 *
 * <p><b>为什么是两个档位而不是一个</b>：原版的 {@link Tier} 是"一整套工具共用一个档"，
 * 而耐久与攻击加成<b>都写在档位里</b>（{@code TieredItem} 直接拿 {@code tier.getUses()} 当耐久、
 * {@code createAttributes()} 拿 {@code tier.getAttackDamageBonus()} 当伤害加成）。
 * 用户给的两把工具数值不同（剑 2048 / 伤害 6.5，镐 4219 / 伤害 4）⇒ 只能各给一个档位。
 * 两个档位除"耐久 + 伤害加成"以外<b>其余全部相同</b>（挖掘等级 / 速度 / 附魔权重 / 修理材料）。</p>
 *
 * <p><b>用户给的数（原话）</b>：剑「耐久2048点 伤害6.5 附魔权重如果能改的话比金高一点就行」、
 * 镐「耐久4219点 伤害4 挖掘等级下界合金」。落到代码里的换算（照原版的算法反推，不是拍脑袋）：</p>
 * <ul>
 *   <li>剑的"伤害 6.5"＝游戏里显示的<b>总攻击伤害</b>（原版钻石剑 7、铁剑 6 那个数）＝
 *       玩家基础 1 + 物品加成。原版剑的加成是 {@code 3 + 档位伤害}⇒ 想让总伤害 6.5，
 *       档位伤害要 <b>2.5</b>（{@code SwordItem.createAttributes(tier, 3, -2.4F)}）；</li>
 *   <li>镐同理：{@code PickaxeItem.createAttributes(tier, 1.0F, -2.8F)} ⇒ 总伤害 = 1 + 1 + 档位伤害，
 *       要 4 ⇒ 档位伤害 <b>2.0</b>（与原版铁镐同档，正好对得上"镐伤害 4"）；</li>
 *   <li>"挖掘等级下界合金"＝用 {@code BlockTags.INCORRECT_FOR_NETHERITE_TOOL} 当"挖不动的方块"集合
 *       （1.21 起 {@code Tier} 不再有 level 整数，等级就是这张标签）⇒ 古代残骸等"只有下界合金能挖"的方块照挖；</li>
 *   <li>"附魔权重比金高一点"：原版金 = <b>22</b>（全套最高），这里取 <b>25</b>；</li>
 *   <li>挖掘速度用户没给 ⇒ 取<b>下界合金同款 9.0</b>（"等级照下界合金"的自然读法，已挂 §9 待确认）；</li>
 *   <li>修理材料＝轻质钛合金本身（铁砧修理、{@code isValidRepairItem} 都走这里）。</li>
 * </ul>
 *
 * <p>⚠ <b>本文件里不许出现 "new 一次就好的静态常量" 这种想当然</b>：两个档位对象是静态常量，
 * 但它们的<b>修理材料是懒取的</b>（{@link #repair()}）—— 静态初始化阶段就去 {@code ModItems.X.get()}
 * 会撞上 §4.1 那条"Trying to access unbound value"（注册表还没填完）。</p>
 */
public final class ModTiers {

    private ModTiers() {
    }

    /** "挖不动的方块"集合 = 下界合金那一档（1.21 起这就是"挖掘等级"本身）。 */
    private static final TagKey<Block> INCORRECT_FOR_NETHERITE = BlockTags.INCORRECT_FOR_NETHERITE_TOOL;

    /** 挖掘速度：取下界合金同款（用户没给数，见类注释）。 */
    public static final float SPEED = 9.0F;

    /** 附魔权重：原版金 22，用户要"比金高一点" ⇒ 25。 */
    public static final int ENCHANTMENT_VALUE = 25;

    /** 剑的档位：耐久 2048（用户给的），伤害加成 2.5 ⇒ 显示总伤害 6.5。 */
    public static final Tier TITANIUM_ALLOY_SWORD = build(2048, 2.5F);

    /** 镐的档位：耐久 4219（用户给的），伤害加成 2.0 ⇒ 显示总伤害 4。 */
    public static final Tier TITANIUM_ALLOY_PICKAXE = build(4219, 2.0F);

    // ================= 星璨钢（0.11 ZF133） =================

    /** 星璨钢斧的挖掘速度：与钛合金 / 下界合金同款 9.0（用户没给，见 §9 待确认）。 */
    public static final float STAR_STEEL_SPEED = 9.0F;

    /**
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
     * ⚠ <b>1.21 的记账方式</b>：原版把"玩家空手伤害 1"放进属性**基础值**里，
     * 所以这个参数是"**武器相对空手额外加多少**" —— 原版斧传 6.0、原版镐传 1.0，
     * 它们都**不是**显示伤害。本档位取 <b>8.0F</b>：
     * 修饰符 = 8 + 档位加成 8 = 16 ⇒ 显示总伤害 = 属性基础值 1 + 16 = <b>17.0</b>
     * （全模组最高一档；对照：下界合金斧 10、钻石剑 7）。
     * ⚠ 这个数是**探针打印出来的**，不是我推的 —— 探针会打出
     * `[ATTR] ... 显示的总伤害 = 1 + 16.0 = 17.0`，`_zf133_verify.py` 也盯着它。</p>
     *
     * <p><b>判据盯的是语义不是魔法数字</b>：探针断言的等式是
     * "组件里的修饰符 == 本参数 + 档位加成"，并把算出来的显示伤害打出来。
     * 想调攻击力只改这个数（+1 点 = 显示 +1），别处不用动。</p>
     *
     * <p>攻速照样照原版斧：{@link #STAR_STEEL_SPEED_MODIFIER} = -3.1（比剑慢，这是斧的定位）。</p>
     *
     * <p>⚠ 这个数与"冲击波在末地的远程伤害 10 + 0.5n"里的 {@code n} 有关。
     * 实现把 {@code n} 读成"玩家的**基础攻击伤害**属性（含力量等玩家自身加成、不含手持武器）"，
     * 因为那正是"玩家基础伤害"逐字的读法 —— 已挂 §9 待用户确认（换个读法只改一个方法）。</p>
     */
    public static final float STAR_STEEL_DAMAGE = 8.0F;

    /** 星璨钢斧的攻速修正：原版斧同款 -3.1（1.0 - (-3.1) = 4.1 秒一刀）。 */
    public static final float STAR_STEEL_SPEED_MODIFIER = -3.1F;

    /** 星璨钢斧的档位：耐久 1192（用户给的），挖掘等级钻石。 */
    public static final Tier STAR_STEEL_AXE = build(1192, STAR_STEEL_DAMAGE, STAR_STEEL_SPEED,
            BlockTags.INCORRECT_FOR_DIAMOND_TOOL, 22);

    /**
     * 懒取修理材料：只有真的被问到（铁砧 / {@code isValidRepairItem}）才去碰 {@code ModItems}。
     *
     * <p>写成 static 方法而不是常量，就是为了避开"注册表还没填完就被取用"那类崩溃。</p>
     */
    private static Ingredient repair() {
        return Ingredient.of(ModItems.LIGHT_TITANIUM_ALLOY.get());
    }

    private static Tier build(int uses, float damageBonus) {
        return build(uses, damageBonus, SPEED, INCORRECT_FOR_NETHERITE, ENCHANTMENT_VALUE);
    }

    /**
     * ZF133 起 {@link #build(int, float)} 的通用版（多两个"挖掘等级 / 附魔权重"参数）。
     *
     * <p>加这两个参数而不是复制一整份匿名类：两个档位除这四个数以外**其余行为完全一样**，
     * 复制一份就等于以后修一处漏一处（§11.4 复用优先）。</p>
     */
    private static Tier build(int uses, float damageBonus, float speed,
                              TagKey<Block> incorrectForDrops, int enchantmentValue) {
        return new Tier() {
            @Override
            public int getUses() {
                return uses;
            }

            @Override
            public float getSpeed() {
                return speed;
            }

            @Override
            public float getAttackDamageBonus() {
                return damageBonus;
            }

            @Override
            public TagKey<Block> getIncorrectBlocksForDrops() {
                return incorrectForDrops;
            }

            @Override
            public int getEnchantmentValue() {
                return enchantmentValue;
            }

            @Override
            public Ingredient getRepairIngredient() {
                return repair();
            }
        };
    }
}
