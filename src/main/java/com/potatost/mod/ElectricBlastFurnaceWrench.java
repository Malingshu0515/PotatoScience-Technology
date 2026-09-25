package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 电力高炉的"扳手拆解"共用逻辑（0.10 ZF41）。
 *
 * <p>用户 ZF41：「不要改成 shift+空手拆掉了 加个扳手 手持扳手 shift+右键拆掉」——
 * 所以拆解统一走这里，控制器与部件格两条入口都调它，免得两份逻辑走偏。</p>
 */
public final class ElectricBlastFurnaceWrench {

    private ElectricBlastFurnaceWrench() {
    }

    /**
     * 用扳手拆解整台机器。
     *
     * <p>掉落规则（用户 ZF39）：「只会毁坏结构和掉落被挖掉的方块以及 gui 内部物品」。
     * 这里是**主动拆解**、没有任何一格被挖掉，所以：
     * 控制器那一格的**原方块**（= 装配时吃掉的那台原版高炉）还给玩家，其余 26 格原地还原。</p>
     *
     * @param touched 玩家手里扳手点到的那一格（只是用来找控制器，不影响掉落）
     */
    public static void disassembleByWrench(Level level, ElectricBlastFurnaceBlockEntity master, BlockPos touched) {
        if (level.isClientSide || !master.isFormed()) {
            return;
        }
        BlockState original = master.originalAt(master.getBlockPos());
        if (original != null && !original.isAir()) {
            Block.popResource(level, master.getBlockPos(), new ItemStack(original.getBlock().asItem()));
        }
        MachineDrops.dropInventory(level, master.getBlockPos(), master.getInventory());
        master.disassemble();   // 满还原：什么都没被挖掉
        if (level.getBlockState(touched).is(ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get())) {
            // 正常不会走到这里：disassemble 已经把这一格还原成原方块了
            level.destroyBlock(touched, false);
        }
    }

    /** 结构不成立时的（可选）提示。控制器那条入口在成型失败时才用得上。 */
    public static void tellIfPresent(Player player, Component message) {
        if (player != null) {
            player.displayClientMessage(message, true);
        }
    }
}
