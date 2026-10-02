package com.potatost.mod;

import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * 手持式引力装置（0.14 ZF169）：副手放方块 ⇒ 长按右键蓄力 25 秒 ⇒ 放一个黑洞。
 *
 * <p><b>用户原话</b>：「储能8mFE 副手放一个方块 长按右键开始蓄力 25s后召唤出一个黑洞
 * 把3x3区块内所有副手方块 全部吸引到黑洞的位置（单次最多1200个方块）单次消耗全部8m电力并损坏
 * （黑洞还会吸引周围的生物 进入黑洞范围内会持续受到虚空伤害）」。</p>
 *
 * <h2>怎么用</h2>
 * <ol>
 *   <li>把要吸的那种**方块**放进<b>副手</b>（主手拿本装置）；</li>
 *   <li>把储能充到满（{@link #CAPACITY} = 8,000,000 FE，用充电站/别的模组的充电器都行 ——
 *       本装置实现了 NeoForge 的物品能量能力）；</li>
 *   <li><b>按住右键 25 秒</b>（{@link #CHARGE_TICKS}）不动：手会像拉弓一样收着，
 *       脚下有粒子往身上卷、每 10 tick 报一次百分比；</li>
 *   <li>蓄满 ⇒ 一次性扣光 8 MFE、装置**当场损坏**（耐久打空），在原地召唤黑洞
 *       （见 {@link BlackHoleManager}）。中途松手 = 作废重来。</li>
 * </ol>
 *
 * <p>⚠ 蓄力过程中副手方块被拿走 ⇒ 立刻中断（不许"空手放大招"）。
 * 储能与探测器一样写在物品自己的 {@code CustomData} 里（不动注册表）。</p>
 */
public class GravityDeviceItem extends Item {

    /** 储能 8 MFE（用户给的"8mFE"）。 */
    public static final int CAPACITY = 8_000_000;
    /** 蓄力 25 秒（用户给的）。 */
    public static final int CHARGE_TICKS = 20 * 25;
    /** 每多少 tick 报一次进度（顺带一声"充能"）。 */
    public static final int FEEDBACK_INTERVAL = 10;

    private static final String ENERGY_KEY = "potatost:energy";

    public GravityDeviceItem(Properties properties) {
        super(properties);
    }

    // ============================================================
    //  能量
    // ============================================================
    public static int getEnergy(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        return tag.getInt(ENERGY_KEY);
    }

    public static void setEnergy(ItemStack stack, int value) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        tag.putInt(ENERGY_KEY, Math.max(0, Math.min(CAPACITY, value)));
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    public static IEnergyStorage energyStorage(ItemStack stack) {
        return new IEnergyStorage() {
            @Override
            public int receiveEnergy(int toReceive, boolean simulate) {
                int now = getEnergy(stack);
                int taken = Math.min(CAPACITY - now, Math.max(0, toReceive));
                if (!simulate && taken > 0) {
                    setEnergy(stack, now + taken);
                }
                return taken;
            }

            @Override
            public int extractEnergy(int toExtract, boolean simulate) {
                int now = getEnergy(stack);
                int given = Math.min(now, Math.max(0, toExtract));
                if (!simulate && given > 0) {
                    setEnergy(stack, now - given);
                }
                return given;
            }

            @Override
            public int getEnergyStored() {
                return getEnergy(stack);
            }

            @Override
            public int getMaxEnergyStored() {
                return CAPACITY;
            }

            @Override
            public boolean canExtract() {
                return true;
            }

            @Override
            public boolean canReceive() {
                return true;
            }
        };
    }

    // ============================================================
    //  物品条（蓄能 = 黄，满 = 紫，一眼看出能不能放）
    // ============================================================
    @Override
    public boolean isBarVisible(ItemStack stack) {
        return true;
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        return Math.round(13.0F * getEnergy(stack) / CAPACITY);
    }

    @Override
    public int getBarColor(ItemStack stack) {
        return getEnergy(stack) >= CAPACITY ? 0xFF9B30FF : 0xFFE0C040;
    }

    // ============================================================
    //  蓄力
    // ============================================================
    @Override
    public int getUseDuration(ItemStack stack, LivingEntity entity) {
        return CHARGE_TICKS;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.BOW;
    }

    /** 副手那种方块（没有就 null）。 */
    public static Block offhandBlock(Player player) {
        ItemStack off = player.getOffhandItem();
        return off.getItem() instanceof BlockItem bi ? bi.getBlock() : null;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (offhandBlock(player) == null) {
            if (!level.isClientSide) {
                player.displayClientMessage(
                        Component.translatable("message.potato_s_t.gravity.need_offhand"), true);
            }
            return InteractionResultHolder.fail(stack);
        }
        if (getEnergy(stack) < CAPACITY) {
            if (!level.isClientSide) {
                player.displayClientMessage(Component.translatable(
                        "message.potato_s_t.gravity.not_full", getEnergy(stack), CAPACITY), true);
            }
            return InteractionResultHolder.fail(stack);
        }
        player.startUsingItem(hand);
        if (!level.isClientSide) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.0F, 0.6F);
        }
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public void onUseTick(Level level, LivingEntity living, ItemStack stack, int remaining) {
        if (!(living instanceof Player player)) {
            return;
        }
        int charged = CHARGE_TICKS - remaining;
        if (offhandBlock(player) == null) {
            // 副手方块被拿走了 ⇒ 立刻中断（并说清为什么）
            if (!level.isClientSide) {
                player.displayClientMessage(
                        Component.translatable("message.potato_s_t.gravity.cancel_offhand"), true);
                player.stopUsingItem();
            }
            return;
        }
        if (level.isClientSide) {
            return;
        }
        if (charged % FEEDBACK_INTERVAL == 0) {
            int percent = charged * 100 / CHARGE_TICKS;
            player.displayClientMessage(Component.translatable(
                    "message.potato_s_t.gravity.charging", percent), true);
            // 音调随进度升高：听得出"快好了"
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS,
                    0.6F + 1.4F * charged / CHARGE_TICKS, 0.8F + 1.2F * charged / CHARGE_TICKS);
        }
        // 粒子：脚下的方块碎屑 + 一圈往身上卷的传送门粒子（半径随蓄力收小 = "吸进来了"）
        if (level instanceof ServerLevel serverLevel) {
            double t = (double) charged / CHARGE_TICKS;
            double radius = 3.0D - 2.0D * t;
            int count = 8 + (int) (t * 16);
            for (int i = 0; i < count; i++) {
                double a = i * (Math.PI * 2.0D / count) + charged * 0.25D;
                serverLevel.sendParticles(net.minecraft.core.particles.ParticleTypes.REVERSE_PORTAL,
                        player.getX() + Math.cos(a) * radius, player.getY() + 0.2D + t * 1.2D,
                        player.getZ() + Math.sin(a) * radius, 1, 0.0D, 0.02D, 0.0D, 0.0D);
            }
            if (charged % 5 == 0) {
                serverLevel.sendParticles(net.minecraft.core.particles.ParticleTypes.ELECTRIC_SPARK,
                        player.getX(), player.getY() + 1.0D, player.getZ(), 3, 0.5D, 0.8D, 0.5D, 0.05D);
            }
        }
    }

    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity living, int timeLeft) {
        if (level.isClientSide || !(living instanceof ServerPlayer player)
                || !(level instanceof ServerLevel serverLevel)) {
            return;
        }
        if (timeLeft > 0) {
            // 没蓄满就松手 —— 作废（不扣电、不损坏）
            serverLevel.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 1.0F, 0.6F);
            player.displayClientMessage(
                    Component.translatable("message.potato_s_t.gravity.interrupted"), true);
            return;
        }
        Block block = offhandBlock(player);
        if (block == null) {
            player.displayClientMessage(
                    Component.translatable("message.potato_s_t.gravity.cancel_offhand"), true);
            return;
        }
        // 成交：扣光 8 MFE + 当场损坏
        setEnergy(stack, 0);
        stack.hurtAndBreak(stack.getMaxDamage(), player, EquipmentSlot.MAINHAND);
        serverLevel.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 2.0F, 0.5F);
        BlackHoleManager.spawn(serverLevel, player.position().add(0.0D, 1.0D, 0.0D), block, player);
        player.displayClientMessage(Component.translatable(
                "message.potato_s_t.gravity.fired", block.getName()), true);
    }
}
