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

    /**
     * 懒取修理材料：只有真的被问到（铁砧 / {@code isValidRepairItem}）才去碰 {@code ModItems}。
     *
     * <p>写成 static 方法而不是常量，就是为了避开"注册表还没填完就被取用"那类崩溃。</p>
     */
    private static Ingredient repair() {
        return Ingredient.of(ModItems.LIGHT_TITANIUM_ALLOY.get());
    }

    private static Tier build(int uses, float damageBonus) {
        return new Tier() {
            @Override
            public int getUses() {
                return uses;
            }

            @Override
            public float getSpeed() {
                return SPEED;
            }

            @Override
            public float getAttackDamageBonus() {
                return damageBonus;
            }

            @Override
            public TagKey<Block> getIncorrectBlocksForDrops() {
                return INCORRECT_FOR_NETHERITE;
            }

            @Override
            public int getEnchantmentValue() {
                return ENCHANTMENT_VALUE;
            }

            @Override
            public Ingredient getRepairIngredient() {
                return repair();
            }
        };
    }
}
