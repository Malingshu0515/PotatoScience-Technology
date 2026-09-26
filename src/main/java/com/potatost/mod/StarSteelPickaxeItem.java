package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.PickaxeItem;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 星璨钢镐（0.11 ZF141）。
 *
 * <p><b>显示伤害 13.0</b>（用户「其他的略低」）@ 1.2 次/秒 = 15.6 DPS，
 * 与斧子（15.3）几乎同档，但每击比剑/斧低 —— 它是矿工的主力，不是武器。
 * 算式：{@code 1 + (1.0 + 8)} 里那个 1.0 换成 {@link ModTiers#STAR_STEEL_PICKAXE_DAMAGE} = 4.0
 * ⇒ 13.0（原版镐的参数是 1.0，本轮把整档抬起来之后按用户"略低"重新给了数）。</p>
 *
 * <h2>技能：与夜同频</h2>
 * <p>夜晚采掘与攻击都不消耗耐久。**对镐来说这条是真有用的** —— 采掘就是镐的全部磨损来源，
 * 而它的攻击磨损是每击 2 点（{@code DiggerItem.postHurtEnemy}）。
 * 判据与斧子逐字同一条（{@link StarSteelTools#isNightWearFree}）。</p>
 *
 * <p>⚠ 挖掘等级与挖掘速度**不在这里**：它们由 {@link ModTiers#STAR_STEEL_TOOL} 决定
 * （钻石级标签 + 速度 9.0），与原版一样走 {@code Tier.createToolProperties}。
 * 所以"挖不动的方块照旧挖不动"这条原版语义不用额外写代码。</p>
 */
public class StarSteelPickaxeItem extends PickaxeItem {

    public StarSteelPickaxeItem(Item.Properties properties) {
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
