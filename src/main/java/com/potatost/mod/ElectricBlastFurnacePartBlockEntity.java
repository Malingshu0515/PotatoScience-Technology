package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * 电力高炉部件格的方块实体（0.10 ZF41）。
 *
 * <p><b>它唯一的职责是当"接电口"。</b>用户定的规矩（ZF37 提出、ZF41 指出问题）：
 * 「多方块结构只有接线块的地方可以用端子传输电力」——
 * 可装配之后原来那两格接线块被换成了部件格，于是**整台机器一处都接不上电**。
 * 这里让"原本是接线块"的那两格继续把电导给控制器，其余部件格一律不给电。</p>
 *
 * <p>它自己不存任何东西，只是就近找控制器（±2 格，见 {@link #findMaster}）并转发。</p>
 */
public class ElectricBlastFurnacePartBlockEntity extends BlockEntity {

    /** 找控制器时向外搜索的半径：控制器离最远的角格是 2 格，所以 2 够用。 */
    private static final int SEARCH = 2;

    public ElectricBlastFurnacePartBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.ELECTRIC_BLAST_FURNACE_PART_BE.get(), pos, state);
    }

    /**
     * 就近找控制器。
     *
     * <p>{@code isDisassembling} 那道判断同时挡住两件事：装配过程中（正在换成部件格）
     * 与拆解过程中（正在还原）都不许回头再触发一次。</p>
     */
    public static ElectricBlastFurnaceBlockEntity findMaster(Level level, BlockPos pos) {
        for (BlockPos p : BlockPos.betweenClosed(pos.offset(-SEARCH, -SEARCH, -SEARCH),
                pos.offset(SEARCH, SEARCH, SEARCH))) {
            if (level.getBlockEntity(p) instanceof ElectricBlastFurnaceBlockEntity be && !be.isDisassembling()) {
                return be;
            }
        }
        return null;
    }

    /** 这一格是不是"接电口"（装配前原本是接线块）。 */
    public boolean isPowerPort() {
        if (this.level == null) {
            return false;
        }
        ElectricBlastFurnaceBlockEntity master = findMaster(this.level, this.worldPosition);
        if (master == null) {
            return false;
        }
        BlockState original = master.originalAt(this.worldPosition);
        return original != null && original.is(ModBlocks.WIRING_BLOCK.get());
    }

    /**
     * 对外暴露的能量接口：**只有接电口才返回非 null**，其余部件格返回 {@code null}，
     * 也就是"这些格子不导电" —— 规则是用户定的，不是省事。
     */
    public IEnergyStorage getEnergyStorage() {
        if (!isPowerPort()) {
            return null;
        }
        return findMaster(this.level, this.worldPosition).getEnergyStorage();
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        // 本方块实体不存任何东西：控制器的位置是**就近找**出来的，
        // 这样控制器被拆掉/换位置时不会留下悬空引用。
    }
}
