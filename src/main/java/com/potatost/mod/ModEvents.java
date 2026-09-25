package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/** 全局事件：海盐作为掉落物碰到水（含流动水）就溶解销毁 */
@EventBusSubscriber(modid = PotatoST.MODID)
// 修复：此前这个类没有任何事件注册（海盐入水不溶的根因），2026-09-13 补上
public final class ModEvents {

    private ModEvents() {
    }

    @SubscribeEvent
    public static void onEntityTick(EntityTickEvent.Post event) {
        if (!(event.getEntity() instanceof ItemEntity item)) {
            return;
        }
        Level level = item.level();
        if (level.isClientSide() || !item.isAlive()) {
            return;
        }
        if (!item.getItem().is(ModItems.SEA_SALT.get())) {
            return;
        }
        if (!touchingWater(level, item)) {
            return;
        }
        item.discard();
        level.playSound(null, item.getX(), item.getY(), item.getZ(),
                SoundEvents.FIRE_EXTINGUISH, SoundSource.NEUTRAL, 0.4F, 1.5F);
    }

    private static boolean touchingWater(Level level, ItemEntity item) {
        if (item.isInWater()) {
            return true;
        }
        BlockPos pos = item.blockPosition();
        return level.getFluidState(pos).is(FluidTags.WATER);
    }
}