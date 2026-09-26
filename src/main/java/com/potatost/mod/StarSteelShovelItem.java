package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ShovelItem;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 星璨钢锹（0.11 ZF142）。用户原话：「锹现在放用户素材了」。
 *
 * <p><b>显示伤害 13.5</b> @ 1.0 次/秒 = 13.5 DPS，落在镐（13.0）与剑（16.0）之间 ——
 * 这正是**原版**的相对关系：原版钻石锹 {@code createAttributes(Tiers.DIAMOND, 1.5F, -3.0F)}
 * 对钻石镐 {@code (1.0F, -2.8F)}，锹比镐高 0.5 点、但挥得慢（1.0 对 1.2 次/秒）。
 * 算式：{@code 1 + (4.5 + 8)} ⇒ 13.5（见 {@link ModTiers#STAR_STEEL_SHOVEL_DAMAGE}）。</p>
 *
 * <h2>技能：与夜同频</h2>
 * <p>夜晚采掘与攻击都不消耗耐久 —— 与锹/镐/锄/斧同一条判据
 * （{@link StarSteelTools#isNightWearFree}，最终转调到 {@code StarSteelAxeItem.isNight}）。
 * 说明共用 {@code tooltip.potato_s_t.star_steel_tool.1} 那一句。</p>
 *
 * <h2>挖掘等级</h2>
 * <p>不在这里：由 {@link ModTiers#STAR_STEEL_TOOL} 决定（钻石级标签 + 速度 9.0），
 * 与原版一样走 {@code Tier.createToolProperties(MINEABLE_WITH_SHOVEL)}。</p>
 */
public class StarSteelShovelItem extends ShovelItem {

    public StarSteelShovelItem(Item.Properties properties) {
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
