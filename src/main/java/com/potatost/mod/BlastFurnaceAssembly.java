package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BlastFurnaceBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/**
 * 电力高炉的装配（0.10 ZF39）：<b>空手 Shift + 右键</b>。
 *
 * <p>两条入口，都支持（用户原话「空手shift+高炉」，而"高炉"在本项目里既是原版高炉、
 * 也是装配之后占着那一格的控制器，所以两边都要能用）：
 * <ol>
 *   <li>原版高炉 —— 结构成立就把它和 25 格建材一起变成电力高炉；</li>
 *   <li>已经放下的电力高炉（从物品摆出来的、还没成型的）—— 结构成立就吸收周围建材成型。</li>
 * </ol></p>
 *
 * <p>⚠ <b>装配过程中必须把控制器置为"忙"</b>：把建材格换成部件格会触发它们的
 * {@code onRemove}，而那些 {@code onRemove} 会回头找控制器要求拆解 ——
 * 不挡就是"刚装好立刻自己拆掉"。{@link ElectricBlastFurnaceBlockEntity#setDisassembling} 就是这道闸门。</p>
 */
public final class BlastFurnaceAssembly {

    private BlastFurnaceAssembly() {
    }

    @SubscribeEvent
    public static void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        Level level = event.getLevel();
        Player player = event.getEntity();
        if (level.isClientSide() || !player.isShiftKeyDown() || !player.getMainHandItem().isEmpty()) {
            return;
        }
        BlockPos pos = event.getPos();
        BlockState state = level.getBlockState(pos);
        if (!state.is(Blocks.BLAST_FURNACE)) {
            return;
        }
        event.setCanceled(true);   // 别让原版高炉界面打开

        Direction facing = state.getValue(BlastFurnaceBlock.FACING);
        ElectricBlastFurnaceStructure.Problem problem =
                ElectricBlastFurnaceStructure.validate(level, pos, facing);
        if (problem != null) {
            player.displayClientMessage(ElectricBlastFurnaceBlock.invalidMessage(problem), true);
            return;
        }
        form((ServerLevel) level, pos, facing);
        player.displayClientMessage(Component.translatable("gui.potato_s_t.ebf.formed"), true);
    }

    /**
     * 把结构"点成型"：控制器那一格换成电力高炉，其余格换成部件格，并记下 27 格的原始状态。
     *
     * @return 成功返回 true
     */
    public static boolean form(ServerLevel level, BlockPos controller, Direction facing) {
        List<BlockPos> positions = ElectricBlastFurnaceStructure.positions(controller, facing);
        List<BlockState> originals = new ArrayList<>(positions.size());
        for (BlockPos p : positions) {
            originals.add(level.getBlockState(p));   // 必须在动手之前全抓下来
        }

        level.setBlock(controller, ModBlocks.ELECTRIC_BLAST_FURNACE.get().defaultBlockState()
                .setValue(ElectricBlastFurnaceBlock.FACING, facing), Block.UPDATE_ALL);
        if (!(level.getBlockEntity(controller) instanceof ElectricBlastFurnaceBlockEntity be)) {
            return false;
        }

        // 闸门：换部件格会触发它们的 onRemove，"忙"的时候不许回头拆解
        be.setDisassembling(true);
        try {
            be.recordStructure(positions, originals);
            for (BlockPos p : positions) {
                if (p.equals(controller) || level.getBlockState(p).isAir()) {
                    continue;   // 控制器自己那格已经换好了；第二层中间那格本来就是空气
                }
                level.setBlock(p, ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get().defaultBlockState(),
                        Block.UPDATE_ALL);
            }
        } finally {
            be.setDisassembling(false);
        }
        return true;
    }
}
