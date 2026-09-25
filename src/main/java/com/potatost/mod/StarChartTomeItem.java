package com.potatost.mod;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

/**
 * 星仪图之章（0.11 ZF122）—— 右键顺次切换**主世界**的天空盒。
 *
 * <p>用户原话：「星仪图之章 右键顺次切换主世界的天空盒 你看看怎么好做 图我给你了
 * 你想怎么编辑都可以 我感觉这个图真的很好看！」</p>
 *
 * <p><b>切换范围</b>：0（原版）→ 1 → 2 → 3 → 4 → 0 循环；<b>潜行右键 = 往回切</b>（顺手加的，
 * 不然切过头要按四遍）。</p>
 *
 * <p><b>只有自己看得见</b>（用户拍板）：天空盒编号存在书自己的
 * {@link ModDataComponents#SKY_INDEX} 组件里，渲染发生在客户端（见
 * {@code client/SkyboxRenderer}）—— 不发任何自定义包、不改服务器状态、也不会打扰同服的人。</p>
 *
 * <p>没有耐久（它不是一次性道具）、不可堆叠（书本来就该是一本）。</p>
 */
public class StarChartTomeItem extends Item {

    /** 四张星图；编号 0 表示"原版星空"，所以总数是 5 种状态。 */
    public static final int SKY_COUNT = 4;
    public static final int STATES = SKY_COUNT + 1;

    /** Shift 说明的行数（与四语言的 tooltip 键一一对应）。 */
    private static final int TOOLTIP_LINES = 3;

    public StarChartTomeItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!level.isClientSide) {
            int current = currentIndex(stack);
            int next = player.isShiftKeyDown()
                    ? Math.floorMod(current - 1, STATES)
                    : (current + 1) % STATES;
            stack.set(ModDataComponents.SKY_INDEX.get(), next);
            player.displayClientMessage(Component.translatable("message.potato_s_t.star_chart.switched",
                    Component.translatable("sky.potato_s_t." + next)).withStyle(
                    next == 0 ? ChatFormatting.GRAY : ChatFormatting.AQUA), true);
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }

    /** 这本书当前选中的编号（缺省 = 原版）。 */
    public static int currentIndex(ItemStack stack) {
        return stack.getOrDefault(ModDataComponents.SKY_INDEX.get(), 0);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        if (flag.hasShiftDown() || flag.isAdvanced()) {
            for (int i = 1; i <= TOOLTIP_LINES; i++) {
                tooltip.add(Component.translatable("tooltip.potato_s_t.star_chart." + i)
                        .withStyle(ChatFormatting.GRAY));
            }
        } else {
            tooltip.add(Component.translatable("tooltip.potato_s_t.hold_shift")
                    .withStyle(ChatFormatting.DARK_GRAY));
        }
    }
}
