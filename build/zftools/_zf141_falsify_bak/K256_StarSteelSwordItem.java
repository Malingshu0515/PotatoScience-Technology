package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 星璨钢剑（0.11 ZF141）。
 *
 * <p><b>用户原话</b>：「还有几个星璨钢的工具你自己写一下呗（耐久 挖掘等级 技能...）
 * 剑和斧子差不多强度 其他的略低（要不要技能都无所谓）你参考一下斧子和星璨钢套
 * 你随便搞 配方就是原版工具一样（原材料换成星璨钢）」+「贴图在用户素材」。</p>
 *
 * <h2>数值（与斧子摆在一起看）</h2>
 * <pre>
 *   斧（ZF133，本轮一个字没动）  17.0 伤害 @ 0.9 次/秒 = 15.3 DPS  + 冲击波 / 急迫 / 夜晚免耐久
 *   剑（本轮）                  16.0 伤害 @ 1.6 次/秒 = 25.6 DPS
 *   镐（本轮）                  13.0 伤害 @ 1.2 次/秒 = 15.6 DPS
 *   锄（本轮）                  12.0 伤害 @ 1.0 次/秒 = 12.0 DPS
 * </pre>
 * <p>「差不多强度」落在**每击伤害只差 1 点**（16 vs 17）；剑挥得更快是原版剑/斧本来的关系
 * （原版钻石剑 7 @1.6 对钻石斧 9 @1.0），斧子那 1 点优势 + 三个技能是它的补偿。
 * 显示伤害的算式：{@code 1 + (参数 + 档位加成 8)} ⇒ {@link ModTiers#STAR_STEEL_SWORD_DAMAGE}
 * 取 7.0 得 16.0。</p>
 *
 * <h2>技能：与夜同频（跟斧子同一条）</h2>
 * <p>夜晚（主世界 13000~23000）**采掘与攻击都不消耗耐久**。剑这两个入口都真的会磨：
 * 攻击每击 1 点（{@code SwordItem.postHurtEnemy}）、采掘每方块 2 点
 * （剑的 TOOL 组件 {@code damagePerBlock = 2}）—— 所以剑这两条都覆写，理由与源码依据见
 * {@link StarSteelTools} 的类注释。</p>
 *
 * <p>⚠ <b>本类只有两个"一行"覆写</b>，逻辑全在 {@link StarSteelTools} / {@link ModTiers} 里。</p>
 */
public class StarSteelSwordItem extends SwordItem {

    public StarSteelSwordItem(Item.Properties properties) {
        super(ModTiers.STAR_STEEL_TOOL, properties);
    }

    /** 夜晚采掘不磨损；白天**原样**走原版（含 damagePerBlock = 2 那条）。 */
    @Override
    public boolean mineBlock(ItemStack stack, Level level, BlockState state, BlockPos pos, LivingEntity entity) {
        if (StarSteelTools.isNightWearFree(level)) {
            return StarSteelTools.nightMineBlockResult(stack);
        }
        return super.mineBlock(stack, level, state, pos, entity);
    }

    /** 夜晚攻击不磨损；白天**原样**走原版（每击 1 点）。 */
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
