package com.potatost.mod;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

/**
 * 可乐（0.13 ZF167）。
 *
 * <p><b>用户原话</b>：「可乐是食物 但是食用音效用蜂蜜瓶的 食用后给予120s的急迫
 * 3s的生命恢复1 恢复3点饥饿值 9点饱和度 （食用后返还一个空铝罐）」。</p>
 *
 * <h2>五条需求各自落在哪</h2>
 * <table border="1">
 *   <tr><th>用户的话</th><th>落在哪</th></tr>
 *   <tr><td>是食物</td><td>{@code Item.Properties#food(...)}（在 {@code ModItems} 里挂），
 *       沿用原版的**进食**动画与「只在饿的时候能吃」这条默认规矩</td></tr>
 *   <tr><td>食用音效用蜂蜜瓶的</td><td>{@link #getEatingSound()}/{@link #getDrinkingSound()}
 *       → {@code SoundEvents.HONEY_DRINK}（原版蜂蜜瓶那一支，{@code item.honey_bottle.drink}；
 *       两个方法都覆写：吃东西时游戏问的是 eating，喝东西时问的是 drinking）</td></tr>
 *   <tr><td>120s 急迫 / 3s 生命恢复 I</td><td>食物组件里的两条 effect，
 *       时长常量 {@link #HASTE_TICKS} / {@link #REGENERATION_TICKS}</td></tr>
 *   <tr><td>3 点饥饿值、9 点饱和度</td><td>{@code nutrition(3)} + {@code saturationModifier(1.5F)}
 *       —— ⚠ 原版的 saturation 是**修饰值不是点数**：点数 = 饥饿值 × 修饰值 × 2 = 3 × 1.5 × 2 = <b>9</b></td></tr>
 *   <tr><td>食用后返还一个空铝罐</td><td>{@code FoodProperties.Builder#usingConvertsTo(空铝罐)}
 *       —— 这是**原版**那条「吃完把容器还给你」的机制（{@code Player.eat} 里读它；
 *       蘑菇煲还碗、蜂蜜瓶还玻璃瓶走的是同一条路），所以这里**不写**自己的返还逻辑</td></tr>
 * </table>
 *
 * <p><b>为什么音效要自己覆写</b>：{@code Item#getEatingSound} 默认是 {@code GENERIC_EAT}
 * （「嚼」的那一声），蜂蜜瓶那一声是 {@code HONEY_DRINK}（「咕咚」）。用户点名要后者，
 * 所以这里只能开一个子类 —— 顺带把 {@link #getDrinkingSound()} 也覆写掉，
 * 理由是"饮料"以后要是改成 {@code UseAnim.DRINK}，那一声才不会退回默认的喝水音。</p>
 */
public class ColaItem extends Item {

    /** 急迫时长：120 秒（用户给的）。 */
    public static final int HASTE_TICKS = 20 * 120;

    /** 生命恢复 I 的时长：3 秒（用户给的）。 */
    public static final int REGENERATION_TICKS = 20 * 3;

    /** Shift 说明的行数（两行：数值 / 返还）。 */
    private static final int TOOLTIP_LINES = 2;

    /** 说明键前缀（与别的物品分开各一组）。 */
    private static final String TOOLTIP_PREFIX = "tooltip.potato_s_t.cola.";

    public ColaItem(Item.Properties properties) {
        super(properties);
    }

    /** 「食用音效用蜂蜜瓶的」——吃东西时游戏问的是这一支。 */
    @Override
    public SoundEvent getEatingSound() {
        return SoundEvents.HONEY_DRINK;
    }

    /** 喝东西时游戏问的是这一支；一起覆写，免得以后改成 DRINK 动画时那一声退回默认。 */
    @Override
    public SoundEvent getDrinkingSound() {
        return SoundEvents.HONEY_DRINK;
    }

    /**
     * Shift 说明：数值与"返还空罐"。
     *
     * <p>没有复用 {@code StarSteelTools.appendHoverText}：那个助手虽然只有六行，
     * 但它属于"星璨钢工具"那一族（名字与注释都写的是工具），食物借它会让人误以为两者有关系。
     * 这里照斧子 ZF133 那份自己写一遍（同一条口径：按住 Shift 看详情）。</p>
     */
    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip,
                                TooltipFlag flag) {
        if (flag.hasShiftDown() || flag.isAdvanced()) {
            for (int i = 1; i <= TOOLTIP_LINES; i++) {
                tooltip.add(Component.translatable(TOOLTIP_PREFIX + i).withStyle(ChatFormatting.GRAY));
            }
        } else {
            tooltip.add(Component.translatable("tooltip.potato_s_t.hold_shift")
                    .withStyle(ChatFormatting.DARK_GRAY));
        }
    }
}
