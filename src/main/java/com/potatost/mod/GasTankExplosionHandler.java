package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * Gas tank hazard (0.03, phase ZF3).
 *
 * A high-pressure tank carrying at least HYDROGEN_EXPLOSION_THRESHOLD mB of
 * hydrogen detonates on contact with fire, soul fire, lava, a lit campfire or a
 * lit soul campfire. The blast is power 2 and sets fire.
 *
 * Two things make the shot land reliably:
 *   - the tank item is registered fireResistant, so lava sets it alight instead
 *     of destroying the item entity outright, which buys the ticks needed here;
 *   - detonation is idempotent: the entity is discarded immediately and every
 *     later tick returns early, so one tank can only ever explode once.
 *
 * Hook choice follows the existing sea-salt dissolve rule in ModEvents, which
 * already uses EntityTickEvent.Post on the game bus.
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class GasTankExplosionHandler {

    /** Blast radius agreed for a detonating tank ("power = 2"). */
    public static final float EXPLOSION_POWER = 2.0F;

    private GasTankExplosionHandler() {
    }

    @SubscribeEvent
    public static void onEntityTick(EntityTickEvent.Post event) {
        if (!(event.getEntity() instanceof ItemEntity item)) {
            return;
        }
        if (item.isRemoved()) {
            return;
        }
        Level level = item.level();
        if (level.isClientSide()) {
            return;
        }
        ItemStack stack = item.getItem();
        if (!(stack.getItem() instanceof HighPressureTankItem)) {
            return;
        }
        if (!HighPressureTankItem.hasHydrogenAtLeast(stack, HighPressureTankItem.HYDROGEN_EXPLOSION_THRESHOLD)) {
            return;
        }
        if (!touchingHazard(level, item)) {
            return;
        }
        detonate(level, item);
    }

    /** Fire, soul fire, lava, or a LIT campfire / soul campfire in contact with the item. */
    private static boolean touchingHazard(Level level, ItemEntity item) {
        if (item.isOnFire() || item.isInLava()) {
            return true;
        }
        BlockPos base = item.blockPosition();
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) {
                    BlockState state = level.getBlockState(base.offset(dx, dy, dz));
                    if (state.is(Blocks.FIRE) || state.is(Blocks.SOUL_FIRE) || state.is(Blocks.LAVA)) {
                        return true;
                    }
                    if ((state.is(Blocks.CAMPFIRE) || state.is(Blocks.SOUL_CAMPFIRE))
                            && state.getValue(CampfireBlock.LIT)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    /**
     * Power-2 blast with fire. BLOCK interaction so the blast behaves like TNT
     * rather than a purely cosmetic trigger explosion.
     */
    private static void detonate(Level level, ItemEntity item) {
        double x = item.getX();
        double y = item.getY();
        double z = item.getZ();
        item.discard();
        level.explode(item, x, y, z, EXPLOSION_POWER, true, Level.ExplosionInteraction.BLOCK);
    }
}