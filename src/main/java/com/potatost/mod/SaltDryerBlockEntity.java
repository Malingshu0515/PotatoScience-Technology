package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 晒盐机：
 *   被动：环境满足时每 2400 tick（120s）产出 1 个海盐；
 *   通电：有 >=70 FE 时吃 70 FE/t、进度 +6/t，即 400 tick（20s）产出 1 个。
 *   环境 = 海洋或咸水河群系 + Y 0~64 + 下方水源方块；输出槽满 / 环境不满足则暂停（进度保留）。
 *   FE 缓冲仅 210。
 */
public class SaltDryerBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 数值 =================
    public static final int MAX_ENERGY = 210;          // 最多存 210 FE
    public static final int ENERGY_PER_TICK = 70;      // 通电时每 tick 消耗
    public static final int PROGRESS_MAX = 2400;       // 被动 120s 一轮
    public static final int POWERED_SPEED = PROGRESS_MAX / 400; // = 6/tick，通电 20s 一轮
    public static final int MIN_Y = 0;
    public static final int MAX_Y = 64;

    public static final int OUTPUT_SLOT = 0;
    public static final int SLOT_COUNT = 1;

    // ContainerData 索引
    public static final int DATA_ENERGY = 0;
    public static final int DATA_PROGRESS = 1;
    public static final int DATA_STATE = 2;
    public static final int DATA_REASON = 3;
    public static final int DATA_COUNT = 4;

    // 状态
    public static final int STATE_IDLE = 0;
    public static final int STATE_PASSIVE = 1;
    public static final int STATE_POWERED = 2;

    // 未工作原因
    public static final int REASON_NONE = 0;
    public static final int REASON_BIOME = 1;
    public static final int REASON_HEIGHT = 2;
    public static final int REASON_WATER = 3;
    public static final int REASON_OUTPUT = 4;

    /** 可工作群系标签：data/potato_s_t/tags/worldgen/biome/salt_water.json（含 #minecraft:is_ocean 与咸水河） */
    public static final TagKey<Biome> SALT_WATER_BIOMES = TagKey.create(Registries.BIOME,
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "salt_water"));

    private int energy = 0;
    private int progress = 0;
    /** 服务端每 tick 刷新，仅供 GUI（不存盘） */
    private int state = STATE_IDLE;
    private int reason = REASON_NONE;

    /** 输出槽：只能拿，不能放 */
    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return false;
        }
    };

    /**
     * 只收不放的能量缓冲。0.09 起三台机器共用 {@link MachineEnergyStorage}，
     * 不再各自维护一份逐字相同的匿名实现（原先 8 个方块实体共约 500 行重复）。
     */
    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                this.setChanged();
            });

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_ENERGY -> energy;
                case DATA_PROGRESS -> progress;
                case DATA_STATE -> state;
                case DATA_REASON -> reason;
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
            // 服务端直读字段；客户端由 SimpleContainerData 承接同步
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public SaltDryerBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.SALT_DRYER_BE.get(), pos, state);
    }

    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    // ================= 每 tick =================
    public static void tick(Level level, BlockPos pos, BlockState state, SaltDryerBlockEntity dryer) {
        if (level.isClientSide) {
            return;
        }
        dryer.serverTick();
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }

        int env = evaluateEnvironment();
        boolean outputRoom = hasOutputRoom();

        if (env != REASON_NONE || !outputRoom) {
            this.state = STATE_IDLE;
            this.reason = env != REASON_NONE ? env : REASON_OUTPUT;
            return; // 暂停，进度保留
        }

        this.reason = REASON_NONE;

        if (this.energy >= ENERGY_PER_TICK) {
            // 通电模式（若想让通电无视环境要求，把环境判定移到这个分支之外即可）
            this.energy -= ENERGY_PER_TICK;
            this.progress += POWERED_SPEED;
            this.state = STATE_POWERED;
        } else {
            // 被动晒盐模式
            this.progress += 1;
            this.state = STATE_PASSIVE;
        }

        if (this.progress >= PROGRESS_MAX) {
            this.progress -= PROGRESS_MAX;
            produceSalt();
        }
        setChanged();
    }

    private int evaluateEnvironment() {
        BlockPos pos = this.getBlockPos();
        if (!this.level.getBiome(pos).is(SALT_WATER_BIOMES)) {
            return REASON_BIOME;
        }
        if (pos.getY() < MIN_Y || pos.getY() > MAX_Y) {
            return REASON_HEIGHT;
        }
        FluidState below = this.level.getFluidState(pos.below());
        if (!below.is(FluidTags.WATER) || !below.isSource()) {
            return REASON_WATER;
        }
        return REASON_NONE;
    }

    private boolean hasOutputRoom() {
        ItemStack out = this.items.getStackInSlot(OUTPUT_SLOT);
        return out.isEmpty()
                || (out.is(ModItems.SEA_SALT.get()) && out.getCount() < out.getMaxStackSize());
    }

    private void produceSalt() {
        ItemStack out = this.items.getStackInSlot(OUTPUT_SLOT);
        if (out.isEmpty()) {
            this.items.setStackInSlot(OUTPUT_SLOT, new ItemStack(ModItems.SEA_SALT.get()));
        } else if (out.is(ModItems.SEA_SALT.get()) && out.getCount() < out.getMaxStackSize()) {
            out.grow(1);
            this.items.setStackInSlot(OUTPUT_SLOT, out);
        }
    }

    // ================= MenuProvider =================
    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.salt_dryer");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new SaltDryerMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.progress = tag.getInt("progress");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("progress", this.progress);
        tag.put("inventory", this.items.serializeNBT(registries));
    }
}