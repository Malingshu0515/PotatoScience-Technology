package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.HoeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 星璨钢锄（0.11 ZF141）。
 *
 * <p><b>显示伤害 12.0</b>（用户「其他的略低」里最低的一把）@ 1.0 次/秒 = 12.0 DPS。
 * 算式：{@code 1 + (3.0 + 8)} ⇒ 12.0。</p>
 *
 * <h2>⚠ 攻速**没有**照抄原版锄头那一套 —— 这是有意偏离，理由写在下面</h2>
 * <p>原版锄头的写法是「<b>总伤害恒为 1</b>、攻速随档位往上涨」：
 * {@code Items.java} 里木锄 {@code (0.0F, -3.0F)}、石锄 {@code (-1.0F, -2.0F)}、
 * 铁锄 {@code (-2.0F, -1.0F)}、钻石锄 {@code (-3.0F, 0.0F)}、下界锄 {@code (-4.0F, 0.0F)}
 * —— 参数一路变负，正好把档位加成抵掉，所以显示伤害永远是 1，而攻速从 1.0 涨到 4.0。
 * 那套刻度是给 0~4 的档位加成设计的。</p>
 * <p>星璨钢这一档的加成是 {@code 8.0}（与斧子同一个档位对象），照抄的话：
 * 伤害 {@code 1 + (-3 + 8) = 6}、攻速 4.0 ⇒ <b>24 DPS，全模组最高的武器</b> ——
 * 一把锄头成了最强武器，显然不是"略低"。所以这里**取原版锄头最低那两档的攻速**
 * （{@code -3.0F} ⇒ 1.0 次/秒，与木锄/金锄相同），伤害按"略低"给 12.0。
 * 也就是说：偏离的只有"攻速随档位上涨"这一条，而它正是与本档位不兼容的那一条。</p>
 *
 * <h2>技能：与夜同频</h2>
 * <p>夜晚采掘与攻击都不消耗耐久（{@link StarSteelTools#isNightWearFree}）。</p>
 * <p>⚠ <b>「锄地」那一下不在这条里</b>：锄头开地走的是 {@code HoeItem.useOn}，里面是
 * 独立的一次 {@code hurtAndBreak(1, ...)}，<b>本轮一个字没动</b>（要覆写就得把原版
 * 那段"查 toolModifiedState + Predicate/Consumer"整段抄一遍，抄错的风险远大于收益）。
 * 所以夜晚锄地照旧扣 1 点 —— 说明文案写的是"采掘与攻击"，与实际一致，没有多吹。</p>
 */
public class StarSteelHoeItem extends HoeItem {

    public StarSteelHoeItem(Item.Properties properties) {
        super(ModTiers.STAR_STEEL_TOOL, properties);
    }

    /** 夜晚采掘不磨损；白天**原样**走原版（DiggerItem 的 damagePerBlock = 1）。 */
    @Override
    public boolean mineBlock(ItemStack stack, Level level, BlockState state, BlockPos pos, LivingEntity entity) {
        if (StarSteelTools.isNightWearFree(level)) {
            return StarSteelTools.nightMineBlockResult(stack);
        }
        return super.mineBlock(stack, level, state, pos, entity);
    }

    /** 夜晚攻击不磨损；白天**原样**走原版（每击 2 点）。 */
    @Override
    public void postHurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        if (StarSteelTools.isNightWearFree(attacker.level())) {
            return;
        }
        super.postHurtEnemy(stack, target, attacker);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        StarSteelTools.appendHoverText(tooltip, flag);
    }
}
