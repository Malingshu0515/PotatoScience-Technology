package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * 创造模式线缆（方块实体）：
 *  - 无限 FE 电源（测试专用）：贴着机器放即可。
 *  - 5 档传输速率：1k / 10k / 1M / 100M / 21.4G FE/t（shift+右键切换，见方块类）。
 *  - 供能方式①：每 tick 主动向 6 个相邻方块的能量能力"推送"；全 tick 总推送量 ≤ 当前档位。
 *  - 供能方式②：自身暴露能量能力（无限存量），供"主动来抽"的机器使用；单次抽取 ≤ 当前档位。
 *  - 21.4G = 21,400,000,000 > int 上限（21.4 亿 = 2.14G 才在 int 内），所以档位用 long 存；
 *    跨能力调用时按 int 分块（每块 ≤ Integer.MAX_VALUE，21.4G 也就 10 块），并有每方向调用次数封顶。
 *  - 每根线缆都是独立电源：线缆之间互推会得到"0 接收"，没有倒灌/接力问题。
 */
public class CreativeCableBlockEntity extends BlockEntity {

    // ================== 数值（改这里） ==================
    /** 5 档传输速率（FE/t）★ 21_400_000_000L 超出 int，末尾 L 别丢；想要 2.14G 就改成 2_140_000_000L */
    public static final long[] RATES = {1_000L, 10_000L, 1_000_000L, 100_000_000L, 2_140_000_000L};
    /** 档位显示标签 */
    public static final String[] RATE_LABELS = {"1k", "10k", "1M", "100M", "21.4G"};
    /** 每个方向每 tick 最多调用多少次 receiveEnergy（防"一次只收一点"的目标把 tick 拖慢） */
    private static final int MAX_CALLS_PER_SIDE = 32;

    private int rateIndex = 0;   // 默认第 1 档：1k FE/t

    private final IEnergyStorage energyStorage = new IEnergyStorage() {
        @Override
        public int receiveEnergy(int maxReceive, boolean simulate) {
            return 0;   // 创造线缆不接受充电
        }

        @Override
        public int extractEnergy(int maxExtract, boolean simulate) {
            if (maxExtract <= 0) {
                return 0;
            }
            int cap = (int) Math.min(RATES[rateIndex], Integer.MAX_VALUE);   // 单次抽取上限 = 当前档位
            return Math.min(maxExtract, cap);
        }

        @Override
        public int getEnergyStored() {
            return Integer.MAX_VALUE;   // 显示为无限
        }

        @Override
        public int getMaxEnergyStored() {
            return Integer.MAX_VALUE;
        }

        @Override
        public boolean canExtract() {
            return true;
        }

        @Override
        public boolean canReceive() {
            return false;
        }
    };

    public CreativeCableBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.CREATIVE_CABLE_BE.get(), pos, state);
    }

    // ================== 对外接口 ==================
    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public long getCurrentRate() {
        return RATES[this.rateIndex];
    }

    public String getRateLabel() {
        return RATE_LABELS[this.rateIndex];
    }

    public int getRateIndex() {
        return this.rateIndex;
    }

    /** shift+右键：切到下一档（循环） */
    public void cycleRate() {
        this.rateIndex = (this.rateIndex + 1) % RATES.length;
        setChanged();
    }

    // ================== 每 tick ==================
    public static void tick(Level level, BlockPos pos, BlockState state, CreativeCableBlockEntity cable) {
        cable.serverTick();
    }

    private void serverTick() {
        if (this.level == null || this.level.isClientSide) {
            return;
        }
        long budget = RATES[this.rateIndex];   // 本 tick 还能推多少 FE
        for (Direction dir : Direction.values()) {
            if (budget <= 0) {
                break;
            }
            BlockPos targetPos = this.getBlockPos().relative(dir);
            IEnergyStorage target = this.level.getCapability(Capabilities.EnergyStorage.BLOCK, targetPos, dir.getOpposite());
            if (target == null || !target.canReceive()) {
                continue;
            }
            int calls = 0;
            while (budget > 0 && calls < MAX_CALLS_PER_SIDE) {
                calls++;
                int chunk = (int) Math.min(budget, Integer.MAX_VALUE);
                int accepted = target.receiveEnergy(chunk, false);
                if (accepted <= 0) {
                    break;   // 收满了/不收 → 换下一个方向
                }
                budget -= accepted;
            }
        }
    }

    // ================== 持久化（只存档位） ==================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        int idx = tag.getInt("rate_index");
        this.rateIndex = Math.max(0, Math.min(idx, RATES.length - 1));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("rate_index", this.rateIndex);
    }
}