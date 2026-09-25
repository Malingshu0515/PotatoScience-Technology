package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * 接线口的方块实体（0.10 ZF49）。
 *
 * <p>存在理由与电力高炉的部件格一样：<b>能力只能挂在方块实体上</b>，
 * 而"只有接线块那两格能传电"这条规则需要逐格判定。这里自己不存任何数据 ——
 * 每次现找控制器，把它的收电接口原样交出去。</p>
 */
public class AlloySmelterPortBlockEntity extends BlockEntity {

    public AlloySmelterPortBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.ALLOY_SMELTER_PORT_BE.get(), pos, state);
    }

    /** 结构没成型就返回 {@code null}（没成型 = 不传电）。 */
    public IEnergyStorage getEnergyStorage() {
        if (this.level == null) {
            return null;
        }
        AlloySmelterBlockEntity master = AlloySmelterBlockEntity.findMaster(this.level, this.worldPosition);
        return master != null && master.isFormed() ? master.getEnergyStorage() : null;
    }
}
