package com.potatost.mod;

import java.util.HashSet;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.LongTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;

public class TerminalBlockEntity extends BlockEntity {

    public enum Mode {
        NONE("none"),
        INPUT("input"),
        OUTPUT("output");

        private final String name;

        Mode(String name) {
            this.name = name;
        }

        public String getName() {
            return this.name;
        }

        public Mode next() {
            Mode[] values = values();
            return values[(this.ordinal() + 1) % values.length];
        }
    }

    /**
     * 单个端子缓冲上限。
     * ★ 2024 调整：16384 -> 2048。端子是"过路件"，不承担储能职责。
     * 注意：端子间用"移动差额一半"的均衡规则 -> 单线稳态通过率 ≈ 本值 ÷ 2，
     * 即 2048 时约 1024 FE/t/线（与各机器单次能量 IO 上限 1024 对齐）。
     */
    public static final int MAX_ENERGY = 2048;
    /** 每根连接线每 tick 的最大传输量 */
    public static final int TRANSFER_RATE = 2048;
    /** 单个端子动力缓冲上限（动力 ≠ FE） */
    public static final int MAX_POWER = 8192;
    /** 每根紫色线缆每 tick 的最大动力传输量 */
    public static final int POWER_TRANSFER_RATE = 128;

    private Mode mode = Mode.NONE;
    private int energy = 0;
    /** 与本端子相连的其他端子坐标（双方各存一份） */
    private final Set<BlockPos> connections = new HashSet<>();
    /** 动力缓冲（紫色动力网络，与 FE 完全独立） */
    private int power = 0;
    /** 通过紫色线缆相连的端子坐标 */
    private final Set<BlockPos> powerConnections = new HashSet<>();

    /** FE 接口：INPUT 端子只能收，OUTPUT 端子只能放，NONE 不开放 */
    private final IEnergyStorage energyStorage = new IEnergyStorage() {
        @Override
        public int receiveEnergy(int maxReceive, boolean simulate) {
            if (mode != Mode.INPUT) return 0;
            int accepted = Math.min(Math.min(maxReceive, TRANSFER_RATE), MAX_ENERGY - energy);
            if (accepted <= 0) return 0;
            if (!simulate) {
                energy += accepted;
                setChanged();
            }
            return accepted;
        }

        @Override
        public int extractEnergy(int maxExtract, boolean simulate) {
            if (mode != Mode.OUTPUT) return 0;
            int extracted = Math.min(Math.min(maxExtract, TRANSFER_RATE), energy);
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
            return mode == Mode.OUTPUT;
        }

        @Override
        public boolean canReceive() {
            return mode == Mode.INPUT;
        }
    };

    public TerminalBlockEntity(BlockPos pos, BlockState blockState) {
        super(ModBlocks.TERMINAL_BE.get(), pos, blockState);
    }

    /** 供 RegisterCapabilitiesEvent 使用的 FE 接口 */
    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public Mode getMode() {
        return this.mode;
    }

    public String getModeName() {
        return this.mode.getName();
    }

    public int getEnergyStored() {
        return this.energy;
    }

    public Set<BlockPos> getConnections() {
        return this.connections;
    }

    // ========== 动力（紫色网络） ==========

    public int getPower() {
        return this.power;
    }

    public Set<BlockPos> getPowerConnections() {
        return this.powerConnections;
    }

    /** 捕获器注入动力；端子必须已接入紫色网络（至少一根紫线）才接收 */
    public int receivePower(int amount, boolean simulate) {
        if (this.powerConnections.isEmpty()) return 0;
        int accepted = Math.min(Math.min(amount, POWER_TRANSFER_RATE), MAX_POWER - power);
        if (accepted <= 0) return 0;
        if (!simulate) {
            power += accepted;
            setChanged();
        }
        return accepted;
    }

    /** 发电机提取动力 */
    public int extractPower(int amount, boolean simulate) {
        if (this.powerConnections.isEmpty()) return 0;
        int extracted = Math.min(Math.min(amount, POWER_TRANSFER_RATE), power);
        if (extracted <= 0) return 0;
        if (!simulate) {
            power -= extracted;
            setChanged();
        }
        return extracted;
    }

    public boolean addPowerConnection(BlockPos other) {
        if (other.equals(this.getBlockPos())) return false;
        if (this.powerConnections.add(other)) {
            sync();
            return true;
        }
        return false;
    }

    public void removePowerConnection(BlockPos other) {
        if (this.powerConnections.remove(other)) {
            sync();
        }
    }

    // ========== FE（铜线网络） ==========

    public void cycleMode() {
        this.mode = this.mode.next();
        sync();
    }

    /** 返回 true 表示新连接建立成功 */
    public boolean addConnection(BlockPos other) {
        if (other.equals(this.getBlockPos())) return false;
        if (this.connections.add(other)) {
            sync();
            return true;
        }
        return false;
    }

    public void removeConnection(BlockPos other) {
        if (this.connections.remove(other)) {
            sync();
        }
    }

    /** 每个游戏刻由 TerminalBlock 的 ticker 调用 */
    public static void tick(Level level, BlockPos pos, BlockState state, TerminalBlockEntity terminal) {
        terminal.serverTick();
    }

    private void serverTick() {
        if (level == null || level.isClientSide) return;

        // 清理失效连接（对面端子被挖掉了）
        if (!connections.isEmpty()) {
            connections.removeIf(otherPos -> !(level.getBlockEntity(otherPos) instanceof TerminalBlockEntity));
        }

        // 与每个相连端子做能量均衡（每根线传输 = 差额一半，受 TRANSFER_RATE 封顶）
        for (BlockPos otherPos : connections) {
            if (!(level.getBlockEntity(otherPos) instanceof TerminalBlockEntity other)) continue;
            int mine = this.energy;
            int theirs = other.energy;
            if (mine > theirs) {
                int delta = Math.min(TRANSFER_RATE, (mine - theirs + 1) / 2);
                this.energy -= delta;
                other.energy += delta;
                this.setChanged();
                other.setChanged();
            } else if (theirs > mine) {
                int delta = Math.min(TRANSFER_RATE, (theirs - mine + 1) / 2);
                this.energy += delta;
                other.energy -= delta;
                this.setChanged();
                other.setChanged();
            }
        }

        // ★ 输入模式：主动从相邻能源方块抽取（应对只会"被抽"的发电机）
        if (mode == Mode.INPUT && energy < MAX_ENERGY) {
            for (Direction side : Direction.values()) {
                if (energy >= MAX_ENERGY) break;
                BlockPos neighborPos = getBlockPos().relative(side);
                // 相邻是端子就跳过（端子之间走上面的网络均衡）
                if (level.getBlockEntity(neighborPos) instanceof TerminalBlockEntity) continue;
                IEnergyStorage storage = level.getCapability(
                        Capabilities.EnergyStorage.BLOCK, neighborPos, side.getOpposite());
                if (storage == null || !storage.canExtract()) continue;
                int amount = Math.min(TRANSFER_RATE, MAX_ENERGY - energy);
                int received = storage.extractEnergy(amount, false);
                if (received > 0) {
                    this.energy += received;
                    setChanged();
                }
            }
        }

        // ★ 输出模式：主动向相邻机器输送（应对只等别人"推"的机器）
        if (mode == Mode.OUTPUT && energy > 0) {
            for (Direction side : Direction.values()) {
                if (energy <= 0) break;
                BlockPos neighborPos = getBlockPos().relative(side);
                if (level.getBlockEntity(neighborPos) instanceof TerminalBlockEntity) continue;
                IEnergyStorage storage = level.getCapability(
                        Capabilities.EnergyStorage.BLOCK, neighborPos, side.getOpposite());
                if (storage == null || !storage.canReceive()) continue;
                int amount = Math.min(TRANSFER_RATE, energy);
                int accepted = storage.receiveEnergy(amount, true);
                if (accepted > 0) {
                    int actuallyAccepted = storage.receiveEnergy(accepted, false);
                    if (actuallyAccepted > 0) {
                        this.energy -= actuallyAccepted;
                        setChanged();
                    }
                }
            }
        }

        // 清理失效动力连接
        if (!powerConnections.isEmpty()) {
            powerConnections.removeIf(otherPos -> !(level.getBlockEntity(otherPos) instanceof TerminalBlockEntity));
        }
        // 动力沿紫色线缆均衡（速率 128/tick/根）
        for (BlockPos otherPos : powerConnections) {
            if (!(level.getBlockEntity(otherPos) instanceof TerminalBlockEntity other)) continue;
            int mine = this.power;
            int theirs = other.power;
            if (mine > theirs) {
                int delta = Math.min(POWER_TRANSFER_RATE, (mine - theirs + 1) / 2);
                this.power -= delta;
                other.power += delta;
                this.setChanged();
                other.setChanged();
            } else if (theirs > mine) {
                int delta = Math.min(POWER_TRANSFER_RATE, (theirs - mine + 1) / 2);
                this.power += delta;
                other.power -= delta;
                this.setChanged();
                other.setChanged();
            }
        }
    }

    /** 破坏端子时，通知所有对端移除连接 */
    @Override
    public void setRemoved() {
        super.setRemoved();
        if (level != null && !level.isClientSide) {
            for (BlockPos otherPos : connections) {
                if (level.getBlockEntity(otherPos) instanceof TerminalBlockEntity other) {
                    other.removeConnection(this.getBlockPos());
                }
            }
            for (BlockPos otherPos : powerConnections) {
                if (level.getBlockEntity(otherPos) instanceof TerminalBlockEntity other) {
                    other.removePowerConnection(this.getBlockPos());
                }
            }
        }
    }

    /** 标记改变并同步给客户端（渲染连线用），同时刷新能力缓存 */
    public void sync() {
        setChanged();
        if (level != null && !level.isClientSide) {
            level.sendBlockUpdated(getBlockPos(), getBlockState(), getBlockState(), Block.UPDATE_CLIENTS);
            // ★ 让相邻机器重新查询本端子的 FE 能力（模式变了之后必须刷新）
            level.invalidateCapabilities(getBlockPos());
        }
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains("mode")) {
            try {
                this.mode = Mode.valueOf(tag.getString("mode"));
            } catch (IllegalArgumentException ignored) {
                this.mode = Mode.NONE;
            }
        }
        // ★ 上限 16384 -> 2048 后，老存档里可能存着超过新上限的电量：加载时夹住，
        //   否则会出现"现存电量 > 上限"的显示/逻辑异常（超出的部分丢弃）
        this.energy = Mth.clamp(tag.getInt("energy"), 0, MAX_ENERGY);

        this.connections.clear();
        ListTag list = tag.getList("connections", Tag.TAG_LONG);
        for (Tag entry : list) {
            this.connections.add(BlockPos.of(((LongTag) entry).getAsLong()));
        }

        this.power = tag.getInt("power");
        this.powerConnections.clear();
        ListTag powerList = tag.getList("power_connections", Tag.TAG_LONG);
        for (Tag entry : powerList) {
            this.powerConnections.add(BlockPos.of(((LongTag) entry).getAsLong()));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putString("mode", this.mode.name());
        tag.putInt("energy", this.energy);
        ListTag list = new ListTag();
        for (BlockPos pos : this.connections) {
            list.add(LongTag.valueOf(pos.asLong()));
        }
        tag.put("connections", list);

        tag.putInt("power", this.power);
        ListTag powerList = new ListTag();
        for (BlockPos pos : this.powerConnections) {
            powerList.add(LongTag.valueOf(pos.asLong()));
        }
        tag.put("power_connections", powerList);
    }

    /** 方块进入世界时把数据同步给客户端 */
    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        return saveWithoutMetadata(registries);
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}