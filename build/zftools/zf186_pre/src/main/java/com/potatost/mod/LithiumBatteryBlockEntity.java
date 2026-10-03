package com.potatost.mod;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

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

/**
 * 锂电池多方块：成型后能量集中在结构最小角（控制器），容量 = 块数 × 4M FE。
 * 只有 UP 面可以真正充放电；其它面返回只读视图（Jade 等能读到电量，但传输为 0）。
 */
public class LithiumBatteryBlockEntity extends BlockEntity {

    public static final long PER_BLOCK = 4_000_000L;
    public static final int TRANSFER_RATE = 65_536;
    public static final int MAX_BLOCKS = 800;

    /** 批量放置期间为 true：邻居变更不再触发成型判定，避免一次放下 25~800 块时 O(n²) */
    private static boolean bulkPlacing = false;

    public static void beginBulkPlacing() {
        bulkPlacing = true;
    }

    public static void endBulkPlacing() {
        bulkPlacing = false;
    }

    public static boolean isBulkPlacing() {
        return bulkPlacing;
    }

    private long energy = 0;
    private boolean formed = false;
    private BlockPos controller = null;
    private int sizeX = 0;
    private int sizeZ = 0;
    private int height = 0;
    private int blockCount = 0;

    private int syncCooldown = 0;
    private long lastSyncedEnergy = -1L;

    public LithiumBatteryBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.LITHIUM_BATTERY_BE.get(), pos, state);
    }

    public boolean isFormed() {
        return this.formed;
    }

    public boolean isController() {
        return this.formed && this.controller != null && this.controller.equals(this.getBlockPos());
    }

    public BlockPos getController() {
        return this.controller;
    }

    public int getSizeX() {
        return this.sizeX;
    }

    public int getSizeZ() {
        return this.sizeZ;
    }

    public int getHeight() {
        return this.height;
    }

    public long getEnergyStoredLong() {
        return this.energy;
    }

    private long capacityLong() {
        if (isController()) {
            return (long) this.blockCount * PER_BLOCK;
        }
        return PER_BLOCK;
    }

    // ================= 真实存储（仅顶面） =================

    private final IEnergyStorage ownStorage = new IEnergyStorage() {
        @Override
        public int receiveEnergy(int maxReceive, boolean simulate) {
            long space = Math.max(0, capacityLong() - energy);
            long accepted = Math.min(Math.min(maxReceive, TRANSFER_RATE), space);
            if (accepted <= 0) return 0;
            if (!simulate) {
                energy += accepted;
                setChanged();
            }
            return (int) accepted;
        }

        @Override
        public int extractEnergy(int maxExtract, boolean simulate) {
            long extracted = Math.min(Math.min(maxExtract, TRANSFER_RATE), energy);
            if (extracted <= 0) return 0;
            if (!simulate) {
                energy -= extracted;
                setChanged();
            }
            return (int) extracted;
        }

        @Override
        public int getEnergyStored() {
            return (int) Math.min(energy, Integer.MAX_VALUE);
        }

        @Override
        public int getMaxEnergyStored() {
            return (int) Math.min(capacityLong(), Integer.MAX_VALUE);
        }

        @Override
        public boolean canExtract() {
            return energy > 0;
        }

        @Override
        public boolean canReceive() {
            return energy < capacityLong();
        }
    };

    // ================= 只读视图（除顶面外的所有查询） =================

    private final IEnergyStorage readOnlyView = new IEnergyStorage() {
        private LithiumBatteryBlockEntity owner() {
            LithiumBatteryBlockEntity self = LithiumBatteryBlockEntity.this;
            if (self.formed && self.controller != null && self.level != null
                    && self.level.getBlockEntity(self.controller) instanceof LithiumBatteryBlockEntity c
                    && c.isController()) {
                return c;
            }
            return self;
        }

        @Override
        public int receiveEnergy(int maxReceive, boolean simulate) {
            return 0;
        }

        @Override
        public int extractEnergy(int maxExtract, boolean simulate) {
            return 0;
        }

        @Override
        public int getEnergyStored() {
            return (int) Math.min(owner().energy, Integer.MAX_VALUE);
        }

        @Override
        public int getMaxEnergyStored() {
            return (int) Math.min(owner().capacityLong(), Integer.MAX_VALUE);
        }

        @Override
        public boolean canExtract() {
            return owner().energy > 0;
        }

        @Override
        public boolean canReceive() {
            return owner().energy < owner().capacityLong();
        }
    };

    /** side == UP：真实存储（成型时转发控制器）；其它面/未指定面：只读视图 */
    public IEnergyStorage getEnergyStorage(Direction side) {
        if (side == Direction.UP) {
            if (this.formed && !isController()) {
                if (this.level != null && this.controller != null
                        && this.level.getBlockEntity(this.controller) instanceof LithiumBatteryBlockEntity ctrl
                        && ctrl.isController()) {
                    return ctrl.ownStorage;
                }
                return null;
            }
            return this.ownStorage;
        }
        return this.readOnlyView;
    }

    // ================= 每 tick：低频同步 =================

    public static void tick(Level level, BlockPos pos, BlockState state, LithiumBatteryBlockEntity battery) {
        battery.serverTick();
    }

    private void serverTick() {
        if (level == null || level.isClientSide) return;
        if (++this.syncCooldown < 20) return;
        this.syncCooldown = 0;
        if (this.energy != this.lastSyncedEnergy) {
            this.lastSyncedEnergy = this.energy;
            BlockState state = this.getBlockState();
            this.level.sendBlockUpdated(this.getBlockPos(), state, state, Block.UPDATE_CLIENTS);
        }
    }

    // ================= 成型规则 =================

    /** 底面积允许的最大高度；返回 0 表示该底面积不合法 */
    public static int maxHeightForBase(int sx, int sz) {
        int a = Math.min(sx, sz);
        int b = Math.max(sx, sz);
        if (a == 1 && b == 1) return 1;
        if (a == 2 && b == 2) return 6;
        if (a == 2 && b == 3) return 12;
        if (a == 3 && b == 3) return 12;
        if (a == 3 && b == 4) return 12;
        if (a == 4 && b == 4) return 32;
        if (a == 5 && b == 5) return 32;
        return 0;
    }

    private static boolean isValidConfig(int sx, int sy, int sz) {
        int maxH = maxHeightForBase(sx, sz);
        return maxH > 0 && sy >= 1 && sy <= maxH;
    }

    /** BFS 找连通电池块：必须是完整长方体且尺寸合法 → 成型 */
    public static boolean tryForm(Level level, BlockPos start) {
        if (level.isClientSide) return false;

        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        Set<BlockPos> seen = new HashSet<>();
        List<BlockPos> blocks = new ArrayList<>();
        int minX = start.getX(), maxX = start.getX();
        int minY = start.getY(), maxY = start.getY();
        int minZ = start.getZ(), maxZ = start.getZ();

        queue.add(start);
        seen.add(start);
        while (!queue.isEmpty()) {
            BlockPos p = queue.poll();
            if (!(level.getBlockState(p).getBlock() instanceof LithiumBatteryBlock)) continue;
            blocks.add(p);
            if (blocks.size() > MAX_BLOCKS) return false;
            minX = Math.min(minX, p.getX()); maxX = Math.max(maxX, p.getX());
            minY = Math.min(minY, p.getY()); maxY = Math.max(maxY, p.getY());
            minZ = Math.min(minZ, p.getZ()); maxZ = Math.max(maxZ, p.getZ());
            for (Direction d : Direction.values()) {
                BlockPos n = p.relative(d);
                if (seen.add(n)) queue.add(n);
            }
        }

        int sx = maxX - minX + 1;
        int sy = maxY - minY + 1;
        int sz = maxZ - minZ + 1;
        if ((long) sx * sy * sz != blocks.size()) return false;
        if (!isValidConfig(sx, sy, sz)) return false;

        BlockPos origin = new BlockPos(minX, minY, minZ);
        List<LithiumBatteryBlockEntity> members = new ArrayList<>();
        for (BlockPos p : blocks) {
            if (level.getBlockEntity(p) instanceof LithiumBatteryBlockEntity be) {
                members.add(be);
            }
        }
        if (members.isEmpty()) return false;

        long sum = 0;
        for (LithiumBatteryBlockEntity be : members) sum += be.energy;

        for (LithiumBatteryBlockEntity be : members) {
            be.energy = 0;
            be.formed = true;
            be.controller = origin;
            be.sizeX = sx;
            be.sizeZ = sz;
            be.height = sy;
            be.blockCount = members.size();
        }
        for (LithiumBatteryBlockEntity be : members) {
            if (be.getBlockPos().equals(origin)) {
                be.energy = Math.min(sum, (long) members.size() * PER_BLOCK);
                break;
            }
        }
        for (LithiumBatteryBlockEntity be : members) {
            be.setChanged();
            level.sendBlockUpdated(be.getBlockPos(), be.getBlockState(), be.getBlockState(), Block.UPDATE_CLIENTS);
            level.invalidateCapabilities(be.getBlockPos());
        }
        return true;
    }

    /** 结构内方块被移除：均分能量并解散；剩余部分若仍是合法长方体则自动重新成型 */
    public static void handleRemoval(Level level, BlockPos removed, LithiumBatteryBlockEntity removedBe) {
        if (level.isClientSide || removedBe == null || !removedBe.formed || removedBe.controller == null) return;

        BlockPos origin = removedBe.controller;
        int sx = removedBe.sizeX;
        int sy = removedBe.height;
        int sz = removedBe.sizeZ;

        LithiumBatteryBlockEntity ctrlBe;
        if (origin.equals(removed)) {
            ctrlBe = removedBe;
        } else {
            ctrlBe = level.getBlockEntity(origin) instanceof LithiumBatteryBlockEntity c ? c : null;
        }
        if (ctrlBe == null) return;
        long total = ctrlBe.energy;

        List<LithiumBatteryBlockEntity> remain = new ArrayList<>();
        for (int dx = 0; dx < sx; dx++) {
            for (int dz = 0; dz < sz; dz++) {
                for (int dy = 0; dy < sy; dy++) {
                    BlockPos p = origin.offset(dx, dy, dz);
                    if (p.equals(removed)) continue;
                    if (level.getBlockEntity(p) instanceof LithiumBatteryBlockEntity be
                            && be.formed && origin.equals(be.controller)) {
                        remain.add(be);
                    }
                }
            }
        }

        long share = remain.isEmpty() ? 0 : Math.min(total / remain.size(), PER_BLOCK);
        for (LithiumBatteryBlockEntity be : remain) {
            be.formed = false;
            be.controller = null;
            be.sizeX = 0;
            be.sizeZ = 0;
            be.height = 0;
            be.blockCount = 0;
            be.energy = share;
            be.setChanged();
            level.sendBlockUpdated(be.getBlockPos(), be.getBlockState(), be.getBlockState(), Block.UPDATE_CLIENTS);
            level.invalidateCapabilities(be.getBlockPos());
        }

        if (!remain.isEmpty()) {
            tryForm(level, remain.get(0).getBlockPos());
        }
    }

    // ================= 持久化 / 同步 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getLong("energy");
        this.formed = tag.getBoolean("formed");
        this.controller = tag.contains("controller") ? BlockPos.of(tag.getLong("controller")) : null;
        this.sizeX = tag.getInt("size_x");
        this.sizeZ = tag.getInt("size_z");
        this.height = tag.getInt("height");
        this.blockCount = tag.getInt("blocks");
        this.lastSyncedEnergy = -1L;
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putLong("energy", this.energy);
        tag.putBoolean("formed", this.formed);
        if (this.controller != null) {
            tag.putLong("controller", this.controller.asLong());
        }
        tag.putInt("size_x", this.sizeX);
        tag.putInt("size_z", this.sizeZ);
        tag.putInt("height", this.height);
        tag.putInt("blocks", this.blockCount);
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