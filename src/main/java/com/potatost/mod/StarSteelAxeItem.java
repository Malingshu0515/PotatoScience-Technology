package com.potatost.mod;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.core.BlockPos;

/**
 * 星璨钢斧（0.11 ZF133）。
 *
 * <p><b>用户原话</b>：「加个星璨钢斧 贴图E:\PotatoST\build\用户素材 1192耐久 挖掘等级钻石
 * 1：夜晚时不消耗耐久 手持时获得急迫1 1s
 * 2：shift+右键 扣除120点耐久 发射一道冲击波 15s冷却（玩家朝向 宽度6格就可以）
 * 破坏沿途所有原木/去皮原木 和树叶 碰到斧子不可以开采的方块 或 10s内未碰到任何原木 则冲击波消失
 * 在末地时 冲击波将具有10+0.5n的远程伤害（n为玩家基础伤害）」</p>
 *
 * <p><b>本类只负责两件"物品自己的事"</b>：① 夜晚免耐久（覆写 {@link #mineBlock}）；
 * ② 右键这一下该不该出手（冷却 / 耐久够不够）。冲击波本身的推进、破坏、伤害全在
 * {@link ShockwaveManager}，手持的急迫在 {@link #applyHoldEffect}（由 {@code PotatoST} 挂在
 * {@code PlayerTickEvent.Post} 上，服务端跑）。</p>
 *
 * <p><b>为什么急迫是"每 tick 刷新"而不是"进背包时给一次"</b>：用户说的是"手持时获得"，
 * 那就是一条**持续状态** —— 每 tick 检查手上有没有这把斧，有就把 1 秒的急迫续上。
 * 这样切换物品 / 丢出去 / 死亡都会在下 1 秒内自然到期，不需要任何"离开时清掉"的回调
 * （那种回调最容易漏：死亡、换维度、被活塞推…）。</p>
 *
 * <p><b>"夜晚"的判据</b>取原版刷怪那条（{@code level.getDayTime() % 24000} 在
 * {@code [13000, 23000)} 之间 = 天黑），并且**限定主世界** —— 下界/末地没有昼夜循环，
 * 那边的 {@code getDayTime()} 是主世界时间，用它会在"主世界恰好是白天"时把末地判成白天，
 * 反之亦然。用户这条要求写在第 1 条（斧子的通用属性）里，没有跨维度语义，
 * 限定主世界是唯一说得通的读法（已挂 §9 待确认）。</p>
 */
public class StarSteelAxeItem extends AxeItem {

    /** 冲击波一次扣的耐久（用户给的数）。 */
    public static final int SHOCKWAVE_COST = 120;

    /** 冲击波冷却：15 秒（用户给的数）。用原版物品冷却（快捷栏上那圈灰罩）。 */
    public static final int SHOCKWAVE_COOLDOWN_TICKS = 20 * 15;

    /** 手持给的急迫时长：1 秒（用户给的数），每 tick 续期。 */
    public static final int HOLD_EFFECT_TICKS = 20;

    /** 急迫的等级：0 = 急迫 I（用户写的"急迫1"）。 */
    public static final int HOLD_EFFECT_AMPLIFIER = 0;

    /** Shift 详细说明的行数（与四语言的 tooltip 键一一对应）。 */
    private static final int TOOLTIP_LINES = 3;

    public StarSteelAxeItem(Item.Properties properties) {
        super(ModTiers.STAR_STEEL_AXE, properties);
    }

    /**
     * 修理材料 = **星璨钢锭**（用户没提，这是"它自己叫什么就用什么修"的自然读法）。
     *
     * <p>⚠ 必须覆写：档位里的 {@code getRepairIngredient()} 是**共用**的那个
     * （钛合金那两把工具/镐用的是轻质钛合金），不覆写的话星璨钢斧会要轻质钛合金 ——
     * <b>这条是探针抓出来的</b>（第一版我漏了覆写，探针直接报「修理材料不是星璨钢锭」）。</p>
     */
    @Override
    public boolean isValidRepairItem(ItemStack toRepair, ItemStack repair) {
        return repair.is(ModArmorItems.STAR_STEEL_INGOT.get()) || super.isValidRepairItem(toRepair, repair);
    }

    /**
     * 夜晚挖方块不扣耐久（用户第 1 条）。
     *
     * <p>原版 {@code DiggerItem.mineBlock} 只做一件事：{@code stack.hurtAndBreak(1, ...)}。
     * 这里把那一下原样搬过来、外面套一层"是不是夜晚"的判断 —— 白天的时间与
     * 挖掘等级判定（{@code isCorrectToolForDrops}）照原版，所以"挖不动的方块照旧挖不动"。</p>
     */
    @Override
    public boolean mineBlock(ItemStack stack, Level level, BlockState state, BlockPos pos, LivingEntity entity) {
        if (!level.isClientSide && isNight(level)) {
            return true;
        }
        if (state.getDestroySpeed(level, pos) != 0.0F) {
            stack.hurtAndBreak(1, entity, EquipmentSlot.MAINHAND);
        }
        return true;
    }

    /** 主世界 + 天黑 = 用户说的"夜晚"。 */
    public static boolean isNight(Level level) {
        if (level.dimension() != Level.OVERWORLD) {
            return false;
        }
        long dayTime = level.getDayTime() % 24000L;
        return dayTime >= 13000L && dayTime < 23000L;
    }

    /**
     * 手持时续 1 秒急迫 I（用户第 1 条）。
     *
     * <p>由 {@code PotatoST} 挂在 {@code PlayerTickEvent.Post} 上：**只在服务端跑**
     * （isClientSide 早退），靠效果同步把图标送进 HUD —— 与 ZF131 那条"双端 ticker"
     * 的教训同源：客户端也跑一遍只会白刷一次本地效果。</p>
     *
     * <p>"还有 1 秒以上就不重给"是省包：不这么写的话每 tick 都会重发一次效果更新，
     * 20 个玩家 = 每秒 400 个无用的效果包（用户要求过「不要太卡」）。</p>
     */
    public static void applyHoldEffect(Player player) {
        if (player.level().isClientSide()) {
            return;
        }
        if (!(player.getMainHandItem().getItem() instanceof StarSteelAxeItem)
                && !(player.getOffhandItem().getItem() instanceof StarSteelAxeItem)) {
            return;
        }
        MobEffectInstance current = player.getEffect(MobEffects.DIG_SPEED);
        if (current != null && current.getDuration() > HOLD_EFFECT_TICKS) {
            return;
        }
        player.addEffect(new MobEffectInstance(MobEffects.DIG_SPEED, HOLD_EFFECT_TICKS,
                HOLD_EFFECT_AMPLIFIER, false, false, true));
    }

    /**
     * Shift + 右键：放冲击波。
     *
     * <p>三个"不出手"的情形都不扣耐久、不进冷却：冷却中、没按 Shift、耐久不够一次 120。
     * 出手那一下按用户说的扣满 120（{@code hurtAndBreak} 与原版一样吃耐久附魔、
     * 扣穿了会正常爆掉并走 {@code onBroken}），然后交给 {@link ShockwaveManager#fire}。</p>
     */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) {
            // 客户端不判定，只把"用过了"这个动作回给动画系统（挥手）
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        if (!player.isShiftKeyDown()) {
            return InteractionResultHolder.pass(stack);
        }
        if (player.getCooldowns().isOnCooldown(this)) {
            return InteractionResultHolder.pass(stack);
        }
        if (stack.getMaxDamage() - stack.getDamageValue() < SHOCKWAVE_COST) {
            return InteractionResultHolder.fail(stack);
        }
        if (player instanceof ServerPlayer serverPlayer) {
            EquipmentSlot slot = hand == InteractionHand.MAIN_HAND ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND;
            stack.hurtAndBreak(SHOCKWAVE_COST, serverPlayer, slot);
            ShockwaveManager.fire(serverPlayer, stack);
            player.getCooldowns().addCooldown(this, SHOCKWAVE_COOLDOWN_TICKS);
            player.swing(hand, true);
        }
        return InteractionResultHolder.sidedSuccess(stack, false);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        if (flag.hasShiftDown() || flag.isAdvanced()) {
            for (int i = 1; i <= TOOLTIP_LINES; i++) {
                tooltip.add(Component.translatable("tooltip.potato_s_t.star_steel_axe." + i)
                        .withStyle(ChatFormatting.GRAY));
            }
        } else {
            tooltip.add(Component.translatable("tooltip.potato_s_t.hold_shift")
                    .withStyle(ChatFormatting.DARK_GRAY));
        }
    }
}
