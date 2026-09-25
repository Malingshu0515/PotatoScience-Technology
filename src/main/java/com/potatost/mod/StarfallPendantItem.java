package com.potatost.mod;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

/**
 * 星轨坠（0.11 ZF114）—— 右键召唤一颗陨石的道具。
 *
 * <p>用户原话：「加一个 星轨坠 道具 右键使用（一共四点耐久右键一次扣1点 不可附魔）
 * 快捷栏上方显示30s红色倒计时 10s之前再次右键可以取消 10s之后聊天栏通报倒计时 不可取消
 * 最后1s聊天栏显示 星轨坠使用者 坐标 作用：召唤出1个陨石 从y=200砸下来 伴随粒子效果
 * 落地后产生7~20power的爆炸 带火 并喷射出一些粗矿 7-12只有铁铜 12以上所有粗矿标签都有
 * 15以上固定产出3个粗振金」</p>
 *
 * <p>本类只负责"右键"这一个决定：把活交给 {@link StarfallRitualManager}；
 * 耐久只在**成功起手**时扣 1 点（取消与"已锁定"的无效右键都不扣）。</p>
 *
 * <p><b>不可附魔</b>：1.21.1 的 {@code Item.Properties} 里**没有** {@code enchantable(int)}
 * （已用 javap 核过 {@code Item$Properties} 的方法表），所以靠两件事一起做：
 * ① {@link #isEnchantable(ItemStack)} 恒 false；② 本物品**不挂**
 * {@code #minecraft:enchantable/*} 任何一条标签。附魔台的候选表是按标签挑的
 * （档案 §4.39 那次出血记录），所以不挂标签 = 台子上根本不会出现它。</p>
 *
 * <p><b>为什么没有合成配方</b>：用户明确说"先不给配方"，所以它现在只能从创造模式拿 ——
 * 已记进档案 §9 的"还没有配方"名单。</p>
 */
public class StarfallPendantItem extends Item {

    /** 用户给的数：一共四点耐久，右键一次扣 1 点。 */
    public static final int DURABILITY = 4;

    /** Shift 详细说明的行数（与四语言的 tooltip 键一一对应）。 */
    private static final int TOOLTIP_LINES = 5;

    public StarfallPendantItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) {
            // 客户端不判定，只把"用过了"这个动作回给动画系统（挥手）
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        if (player instanceof ServerPlayer serverPlayer) {
            StarfallRitualManager.Outcome outcome = StarfallRitualManager.use(serverPlayer, stack);
            if (outcome == StarfallRitualManager.Outcome.STARTED) {
                EquipmentSlot slot = hand == InteractionHand.MAIN_HAND ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND;
                stack.hurtAndBreak(1, serverPlayer, slot);
            }
        }
        return InteractionResultHolder.sidedSuccess(stack, false);
    }

    @Override
    public boolean isEnchantable(ItemStack stack) {
        return false;
    }

    @Override
    public int getEnchantmentValue() {
        return 0;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        if (flag.hasShiftDown() || flag.isAdvanced()) {
            for (int i = 1; i <= TOOLTIP_LINES; i++) {
                tooltip.add(Component.translatable("tooltip.potato_s_t.starfall_pendant." + i)
                        .withStyle(ChatFormatting.GRAY));
            }
        } else {
            tooltip.add(Component.translatable("tooltip.potato_s_t.hold_shift")
                    .withStyle(ChatFormatting.DARK_GRAY));
        }
    }
}
