package com.potatost.mod;

import com.potatost.mod.client.sound.MachineRunningSound;
import com.potatost.mod.sound.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;

/** 发电机：吸动力 -> 转 FE -> 推给紧邻 INPUT 端子；转化时 active=true 驱动客户端动画 */
public class GeneratorBlockEntity extends BlockEntity {
    public static final int MAX_POWER = 512;            // 动力缓冲
    public static final int MAX_ENERGY = 100_000;       // FE 缓冲
    public static final int MAX_POWER_INTAKE = 128;     // 每 tick 吸动力上限
    public static final int MAX_POWER_CONSUME = 128;    // 每 tick 转化上限（128*2=256 FE/t）
    /**
     * 1 动力 → {@value} FE。
     *
     * <p><b>0.10 ZF27 从 16 下调到 2</b>（用户："发电机太超模了改成每点动力 2FE/t"）。
     * 旧值下光一台捕获器（六面流动水，每格 16 动力/t）就能顶到 16 动力 × 16 = <b>256 FE/t</b>，
     * 而同时期的机器耗电是两位数（微型粉碎机 20 FE/t、灌装机 60 FE/t/罐）——
     * 一台捕获器直接养半个工厂，这就是"超模"。
     * 改成 2 之后同样的捕获器只有 <b>32 FE/t</b>，跟其它发电手段同一量级。</p>
     */
    public static final int FE_PER_POWER = 2;
    public static final int PUSH_RATE = 2048;           // 向单个 INPUT 端子推 FE 上限

    private int power = 0;
    private int energy = 0;
    private boolean active = false;

    /** FE 接口：只出不进（供管道/导线抽取） */
    private final IEnergyStorage energyStorage = new IEnergyStorage() {
        @Override
        public int receiveEnergy(int maxReceive, boolean simulate) {
            return 0;
        }
        @Override
        public int extractEnergy(int maxExtract, boolean simulate) {
            int extracted = Math.min(Math.min(maxExtract, PUSH_RATE), energy);
            if (extracted <= 0) return 0;
            if (!simulate) {
                energy -= extracted;
                setChanged();
            }
            return extracted;
        }
        @Override
        public int getEnergyStored() {
            return energy;
        }
        @Override
        public int getMaxEnergyStored() {
            return MAX_ENERGY;
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

    public GeneratorBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.GENERATOR_BE.get(), pos, state);
    }

    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public boolean isActive() {
        return this.active;
    }

    public int getPower() {
        return this.power;
    }

    public int getEnergyStored() {
        return this.energy;
    }

    public static void tick(Level level, BlockPos pos, BlockState state, GeneratorBlockEntity generator) {
        if (level.isClientSide) {
            // client tick: drive the looping sound from the synced active flag
            MachineRunningSound.update(generator, generator.isActive(), ModSounds.GENERATOR_RUNNING.get());
        } else {
            generator.serverTick();
        }
    }

    private void serverTick() {
        if (level == null || level.isClientSide) return;
        boolean dirty = false;

        // 1. 从紧邻端子吸动力（只吸已接紫色网络的端子）
        int need = MAX_POWER_INTAKE;
        for (Direction direction : Direction.values()) {
            if (need <= 0) break;
            if (level.getBlockEntity(getBlockPos().relative(direction)) instanceof TerminalBlockEntity terminal) {
                int taken = terminal.extractPower(need, false);
                if (taken > 0) {
                    this.power = Math.min(MAX_POWER, this.power + taken);
                    need -= taken;
                    dirty = true;
                }
            }
        }

        // 2. 转化：1 动力 -> FE_PER_POWER FE（ZF27 起是 2）
        int consumed = Math.min(this.power, MAX_POWER_CONSUME);
        if (consumed > 0) {
            this.power -= consumed;
            this.energy = (int) Math.min(MAX_ENERGY, this.energy + (long) consumed * FE_PER_POWER);
            dirty = true;
        }

        // 3. 推 FE 给紧邻 INPUT 模式端子（铜线网络自动接管后续）
        for (Direction direction : Direction.values()) {
            if (this.energy <= 0) break;
            if (level.getBlockEntity(getBlockPos().relative(direction)) instanceof TerminalBlockEntity terminal
                    && terminal.getMode() == TerminalBlockEntity.Mode.INPUT) {
                int sent = terminal.getEnergyStorage().receiveEnergy(Math.min(PUSH_RATE, this.energy), false);
                if (sent > 0) {
                    this.energy -= sent;
                    dirty = true;
                }
            }
        }

        // 4. 动画开关翻转时同步一次（旋转由客户端用 gameTime 驱动，不需要每 tick 同步）
        boolean nowActive = consumed > 0;
        if (nowActive != this.active) {
            this.active = nowActive;
            sync();
        }

        if (dirty) setChanged();
    }

    public void sync() {
        setChanged();
        if (level != null && !level.isClientSide) {
            level.sendBlockUpdated(getBlockPos(), getBlockState(), getBlockState(), Block.UPDATE_CLIENTS);
        }
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.power = tag.getInt("power");
        this.energy = tag.getInt("energy");
        this.active = tag.getBoolean("active");
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("power", this.power);
        tag.putInt("energy", this.energy);
        tag.putBoolean("active", this.active);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        return saveWithoutMetadata(registries);
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}