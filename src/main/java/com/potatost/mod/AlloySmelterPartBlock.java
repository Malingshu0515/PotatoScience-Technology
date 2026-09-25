package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 合金冶炼炉的<b>部件格</b>（0.10 ZF54）：成型时把结构里 77 格换成它。
 *
 * <p>与电力高炉的部件格同一个思路 —— <b>不渲染</b>（{@link RenderShape#INVISIBLE}），
 * 整台机器由控制器那一格挂的 OBJ 长方体负责画。挖掉任意一格 = 结构失效，
 * 并且<b>掉回它原来那个方块</b>（不是掉部件格，那东西挖不出来）。
 *
 * <p>不需要方块实体：接电仍然由那两处 {@code alloy_smelter_port} 负责。</p>
 */
public class AlloySmelterPartBlock extends Block {

    public AlloySmelterPartBlock(Properties properties) {
        super(properties);
    }

    @Override
    public RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    /**
     * 被挖掉：掉回原来的方块，并让整台机器失效（含 GUI 内容物掉落）。
     *
     * <p>⚠ 拆解期间（{@code isDisassembling()}）什么都不做 —— 那是控制器自己在换方块，
     * 否则会递归（ZF40 那个"白送一台机器"的坑）。</p>
     */
    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean movedByPiston) {
        if (!state.is(newState.getBlock())) {
            AlloySmelterBlockEntity master = AlloySmelterBlockEntity.findMasterAt(level, pos);
            if (master != null && !master.isDisassembling()) {
                BlockState original = master.originalAt(pos);
                if (original != null) {
                    Block.popResource(level, pos, new ItemStack(original.getBlock()));
                }
                master.dropContents();
                master.disassemble(pos);
            }
        }
        super.onRemove(state, level, pos, newState, movedByPiston);
    }
}
