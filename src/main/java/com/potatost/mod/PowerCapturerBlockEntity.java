package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AbstractFurnaceBlock;
import net.minecraft.world.level.block.BlastFurnaceBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;

/**
 * 动力能源捕获器：每 tick 检测紧邻 6 格 ——
 * 流动水 +{@value #WATER_POWER}、燃烧的熔炉/烟熏炉 +{@value #FURNACE_POWER}、
 * 燃烧的高炉 +{@value #BLAST_FURNACE_POWER}，
 * 动力先入自身缓冲，再注入紧邻的已接入紫色网络的接线端子。
 *
 * <p><b>0.10 ZF28 调整</b>（用户："熔炉高炉烟熏炉动力翻 2 倍，然后水变成 8 吧"）：
 * 熔炉/烟熏炉 4 → 8、高炉 8 → 16（各翻倍），流动水 16 → 8。
 * 于是三种来源换算成 FE 后（发电机 ×2，见 §6.11）变成
 * <b>高炉 32、熔炉/烟熏炉 16、流动水 16 FE/t</b> ——
 * 单台炉子终于不再只是水的零头，而水仍然是最容易铺开的那种。</p>
 */
public class PowerCapturerBlockEntity extends BlockEntity {
    public static final int MAX_POWER = 1000;       // 自身动力缓冲上限
    /** 每 tick 向单个紧邻端子注入上限。六面各一台炉子时总产 96，端子侧上限是 128，都不撞这道闸 */
    public static final int EXPORT_PER_FACE = 32;
    /** 每格流动水的动力产出（ZF28 由 16 降到 8） */
    public static final int WATER_POWER = 8;
    /** 燃烧的熔炉 / 烟熏炉（ZF28 由 4 翻倍到 8） */
    public static final int FURNACE_POWER = 8;
    /** 燃烧的高炉（ZF28 由 8 翻倍到 16） */
    public static final int BLAST_FURNACE_POWER = 16;

    private int power = 0;
    /** 上一 tick 产量（调试用，不存盘） */
    private int production = 0;

    public PowerCapturerBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.POWER_CAPTURER_BE.get(), pos, state);
    }

    public int getPower() {
        return this.power;
    }

    public int getProduction() {
        return this.production;
    }

    public static void tick(Level level, BlockPos pos, BlockState state, PowerCapturerBlockEntity capturer) {
        capturer.serverTick();
    }

    private void serverTick() {
        if (level == null || level.isClientSide) return;
        this.production = detectProduction();
        if (this.production > 0) {
            int old = this.power;
            this.power = Math.min(MAX_POWER, this.power + this.production);
            if (this.power != old) setChanged();
        }
        // 注入紧邻端子（端子没接紫色线缆时 receivePower 直接拒绝）
        for (Direction direction : Direction.values()) {
            if (this.power <= 0) break;
            BlockPos neighbor = this.getBlockPos().relative(direction);
            if (level.getBlockEntity(neighbor) instanceof TerminalBlockEntity terminal) {
                int sent = terminal.receivePower(Math.min(EXPORT_PER_FACE, this.power), false);
                if (sent > 0) {
                    this.power -= sent;
                    setChanged();
                }
            }
        }
    }

    /** 6 面检测 */
    private int detectProduction() {
        int total = 0;
        for (Direction direction : Direction.values()) {
            BlockPos neighbor = this.getBlockPos().relative(direction);
            // ① 燃烧反应室（0.11 ZF100）：用户原话「所有燃料反应后 燃烧反应室产出800点动力
            //    可被 动力能源捕获器识别 其中柴油为1200点动力」（汽油 1000，用户当场拍板）。
            //    ⇒ 把相邻的燃烧反应室当成一台"超强火炉"来识别：反应期间每 tick 加它的动力档。
            if (level.getBlockEntity(neighbor) instanceof CombustionChamberBlockEntity chamber) {
                total += chamber.powerPerTick();
                continue;
            }
            BlockState state = level.getBlockState(neighbor);
            FluidState fluid = state.getFluidState();
            // 流动水 = 非满格水（满格水源不算）
            if (fluid.is(Fluids.FLOWING_WATER)
                    || (fluid.is(Fluids.WATER) && fluid.getAmount() < 8)) {
                total += WATER_POWER;
                continue;
            }
            if (state.getBlock() instanceof AbstractFurnaceBlock && state.getValue(AbstractFurnaceBlock.LIT)) {
                total += state.getBlock() instanceof BlastFurnaceBlock ? BLAST_FURNACE_POWER : FURNACE_POWER;
            }
        }
        return total;
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.power = tag.getInt("power");
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("power", this.power);
    }
}