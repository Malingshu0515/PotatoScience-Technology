package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 机器物品栏掉落工具（0.08 修复「破坏机器吞物品」）。
 *
 * <p><b>背景（真踩过的坑）：</b>原版<b>没有</b>任何「容器方块自动掉落内容物」的通用机制。
 * {@code ChestBlock}、{@code BarrelBlock}、{@code DispenserBlock}、{@code HopperBlock}、
 * {@code ShulkerBoxBlock}、{@code AbstractFurnaceBlock} 全都是<b>各自</b>在
 * {@code onRemove} 里显式调用 {@code Containers.dropContentsOnDestroy(...)} 才掉落的
 * （在反混淆映射里可以量出来：这些类的 onRemove 都只有 2~3 行）。
 * {@code BaseEntityBlock} <b>并未</b>覆写 {@code onRemove}，所以任何自带物品栏的方块实体
 * 只要自己不处理，破坏时内容物就<b>直接消失</b>。</p>
 *
 * <p>另外 NeoForge 的 {@link ItemStackHandler} <b>不是</b>原版 {@code Container}，
 * 所以即使照抄 {@code Containers.dropContentsOnDestroy} 也不会生效
 * （它内部判的是 {@code blockEntity instanceof Container}）。</p>
 */
public final class MachineDrops {

    private MachineDrops() {
    }

    /**
     * 把机器物品栏里的所有物品掉落到世界中，并清空该物品栏。
     *
     * <p><b>必须在 {@code super.onRemove(...)} 之前调用</b>——super 会把方块实体从区块里移除，
     * 之后再 {@code level.getBlockEntity(pos)} 就拿到 {@code null} 了。</p>
     *
     * @param level   世界（客户端调用会被直接忽略，避免生成幽灵掉落物）
     * @param pos     方块位置
     * @param handler 机器的物品栏
     */
    public static void dropInventory(Level level, BlockPos pos, ItemStackHandler handler) {
        if (level.isClientSide) {
            return;
        }
        for (int slot = 0; slot < handler.getSlots(); slot++) {
            ItemStack stack = handler.getStackInSlot(slot);
            if (stack.isEmpty()) {
                continue;
            }
            // copy()：掉落独立副本，避免与原栈共享引用；
            // 自定义数据（custom data）会被完整保留，例如气罐里的气体不会丢。
            Block.popResource(level, pos, stack.copy());
            handler.setStackInSlot(slot, ItemStack.EMPTY);
        }
    }
}
