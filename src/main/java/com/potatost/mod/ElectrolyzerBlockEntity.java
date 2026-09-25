package com.potatost.mod;

import com.potatost.mod.client.sound.MachineRunningSound;
import com.potatost.mod.sound.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup.Provider;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 电解器方块实体（双配方版）。
 *
 * 按电解质槽里有没有海盐自动切换配方：
 *   纯水制氧（原配方，无海盐）：每 tick 耗 1000 FE + 10 mB 水 -> 产 3 氧气 + 6 氢气
 *   盐水制氯（新配方，有海盐）：每 tick 耗 1000 FE + 10 mB 水 -> 产 3 氯气 + 6 氢气，
 *                              每处理 500 mB 水消耗 1 个海盐
 * 注意：放了海盐就锁定盐水模式（氯罐满了只会暂停，不会偷偷改产氧气）；想产氧把海盐拿走。
 * 输出罐满、缺水或缺电时自动暂停。想调数值：改下面配方参数区。
 *
 * <p><b>0.11 ZF81 改的数</b>（用户原话「电解器还是改成 1000Fe/t 吧」）：两个模式的
 * 能耗都从 <b>100 FE/t 抬到 1000 FE/t</b>（水/产物速度一个没动）。</p>
 *
 * <p>⚠ <b>一起看两个数</b>：缓冲仍是 {@link #MAX_ENERGY} = 20000 FE ⇒ 满载只够 <b>20 tick</b>
 * （100 FE/t 时是 200 tick）。缓冲 ≥ 单 tick 电费这条硬约束仍然满足（20000 ≥ 1000），
 * 机器不会像 ZF38 的泵那样"永久待机"；但供电必须真的跟得上 1000 FE/t，
 * 否则表现是"一充一停、走得极慢"。要不要把缓冲一起抬（例如照旧给 200 tick = 200000 FE）
 * 是**待用户拍板**的事，本轮没动。</p>
 */
public class ElectrolyzerBlockEntity extends BlockEntity implements MenuProvider {

    // ===== 配方参数（要调数字就改这里）=====
    public static final int INPUT_CAPACITY = 1000;
    public static final int OXYGEN_CAPACITY = 800;
    public static final int CHLORINE_CAPACITY = 800;
    public static final int HYDROGEN_CAPACITY = 800;
    public static final int MAX_ENERGY = 20000;

    public static final int WATER_PER_TICK = 10;             // 两种配方共用：耗水速度
    public static final int HYDROGEN_PER_TICK = 6;           // 两种配方共用：产氢速度

    public static final int ENERGY_PER_TICK_OXYGEN = 1000;   // 纯水制氧能耗（0.11 ZF81：100 → 1000）
    public static final int OXYGEN_PER_TICK = 3;             // 纯水制氧产氧速度

    public static final int ENERGY_PER_TICK_CHLORINE = 1000; // 盐水制氯能耗（0.11 ZF81：100 → 1000）
    public static final int CHLORINE_PER_TICK = 3;           // 盐水制氯产氯速度
    public static final int WATER_PER_SALT = 500;            // 每个海盐可处理的水量（mB）

    /** 兼容旧引用：等于盐水模式的能耗。 */
    public static final int ENERGY_PER_TICK = ENERGY_PER_TICK_CHLORINE;

    public static final int FLUID_SLOT = 0;
    public static final int ELECTROLYTE_SLOT = 1;
    public static final int SLOT_COUNT = 2;
    public static final int DATA_ENERGY = 0;
    public static final int DATA_INPUT = 1;
    public static final int DATA_CHLORINE = 2;
    public static final int DATA_HYDROGEN = 3;
    public static final int DATA_OXYGEN = 4;
    public static final int DATA_COUNT = 5;

    public static final TagKey<Item> ELECTROLYTE_TAG = TagKey.create(Registries.ITEM,
            ResourceLocation.fromNamespaceAndPath("potato_s_t", "electrolyte"));

    private int energy = 0;
    private final FluidTank inputTank = new FluidTank(INPUT_CAPACITY);
    private final FluidTank oxygenTank = new FluidTank(OXYGEN_CAPACITY);
    private final FluidTank chlorineTank = new FluidTank(CHLORINE_CAPACITY);
    private final FluidTank hydrogenTank = new FluidTank(HYDROGEN_CAPACITY);
    private int waterSinceSalt = 0;
    private int syncCooldown = -1;
    private int lastSyncedInput = -1;
    private boolean working = false;

    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            ElectrolyzerBlockEntity.this.setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return switch (slot) {
                case FLUID_SLOT -> stack.is(Items.WATER_BUCKET) || stack.is(Items.BUCKET);
                case ELECTROLYTE_SLOT -> stack.is(ELECTROLYTE_TAG);
                default -> true;
            };
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

    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return 4;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return ElectrolyzerBlockEntity.this.tankOf(tank).getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return ElectrolyzerBlockEntity.this.tankOf(tank).getCapacity();
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return tank == 0 && stack.getFluid().is(FluidTags.WATER);
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            return !resource.isEmpty() && resource.getFluid().is(FluidTags.WATER)
                    ? ElectrolyzerBlockEntity.this.inputTank.fill(resource, action)
                    : 0;
        }

        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return FluidStack.EMPTY;
            }
            for (int i = 1; i <= 3; i++) {
                FluidTank t = ElectrolyzerBlockEntity.this.tankOf(i);
                if (!t.drain(resource, FluidAction.SIMULATE).isEmpty()) {
                    return t.drain(resource, action);
                }
            }
            return !ElectrolyzerBlockEntity.this.inputTank.drain(resource, FluidAction.SIMULATE).isEmpty()
                    ? ElectrolyzerBlockEntity.this.inputTank.drain(resource, action)
                    : FluidStack.EMPTY;
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            for (int i = 1; i <= 3; i++) {
                FluidTank t = ElectrolyzerBlockEntity.this.tankOf(i);
                if (!t.isEmpty()) {
                    return t.drain(maxDrain, action);
                }
            }
            return ElectrolyzerBlockEntity.this.inputTank.drain(maxDrain, action);
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_ENERGY -> ElectrolyzerBlockEntity.this.energy;
                case DATA_INPUT -> ElectrolyzerBlockEntity.this.inputTank.getFluidAmount();
                case DATA_CHLORINE -> ElectrolyzerBlockEntity.this.chlorineTank.getFluidAmount();
                case DATA_HYDROGEN -> ElectrolyzerBlockEntity.this.hydrogenTank.getFluidAmount();
                case DATA_OXYGEN -> ElectrolyzerBlockEntity.this.oxygenTank.getFluidAmount();
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public ElectrolyzerBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.ELECTROLYZER_BE.get(), pos, state);
    }

    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public IFluidHandler getFluidHandler() {
        return this.fluidHandler;
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    public ContainerData getData() {
        return this.containerData;
    }

    public boolean isWorking() {
        return this.working;
    }

    private void sync() {
        this.setChanged();
        if (this.level != null && !this.level.isClientSide) {
            this.level.sendBlockUpdated(this.getBlockPos(), this.getBlockState(), this.getBlockState(), Block.UPDATE_CLIENTS);
        }
    }

    private FluidTank tankOf(int index) {
        return switch (index) {
            case 0 -> this.inputTank;
            case 1 -> this.oxygenTank;
            case 2 -> this.chlorineTank;
            case 3 -> this.hydrogenTank;
            default -> throw new IllegalArgumentException("Unknown tank index: " + index);
        };
    }

    public static void tick(Level level, BlockPos pos, BlockState state, ElectrolyzerBlockEntity electrolyzer) {
        if (level.isClientSide) {
            // client tick: drive the looping sound from the synced working flag
            MachineRunningSound.update(electrolyzer, electrolyzer.isWorking(), ModSounds.ELECTROLYZER_RUNNING.get());
        } else {
            electrolyzer.serverTick();
        }
    }

    private void serverTick() {
        if (this.level != null) {
            this.handleFluidSlot();
            boolean nowWorking = this.processRecipe();
            if (nowWorking != this.working) {
                this.working = nowWorking;
                this.sync();
            }
            if (this.syncCooldown > 0) {
                this.syncCooldown--;
            } else {
                this.syncCooldown = 20;
                if (this.inputTank.getFluidAmount() != this.lastSyncedInput) {
                    this.lastSyncedInput = this.inputTank.getFluidAmount();
                    this.level.sendBlockUpdated(this.getBlockPos(), this.getBlockState(), this.getBlockState(), 2);
                }
            }
        }
    }

    private void handleFluidSlot() {
        // 仅保留水桶注水变空桶的单向下行（空桶不回收，避免来回循环）
        ItemStack stack = this.items.getStackInSlot(FLUID_SLOT);
        if (stack.is(Items.WATER_BUCKET) && this.inputTank.getFluidAmount() + 1000 <= INPUT_CAPACITY) {
            this.inputTank.fill(new FluidStack(Fluids.WATER, 1000), FluidAction.EXECUTE);
            this.items.setStackInSlot(FLUID_SLOT, new ItemStack(Items.BUCKET));
        }
    }

    /** 模式选择：有海盐 -> 盐水制氯；没有 -> 纯水制氧（原配方） */
    private boolean processRecipe() {
        ItemStack salt = this.items.getStackInSlot(ELECTROLYTE_SLOT);
        if (!salt.isEmpty() && salt.is(ELECTROLYTE_TAG)) {
            return this.processChlorine(salt);
        }
        return this.processOxygen();
    }

    /** 纯水制氧（原配方）：10 mB 水 + 1000 FE/t -> 3 氧气 + 6 氢气 */
    private boolean processOxygen() {
        if (this.energy < ENERGY_PER_TICK_OXYGEN) {
            return false;
        }
        if (this.inputTank.getFluidAmount() < WATER_PER_TICK) {
            return false;
        }
        if (this.oxygenTank.getFluidAmount() + OXYGEN_PER_TICK > OXYGEN_CAPACITY) {
            return false;
        }
        if (this.hydrogenTank.getFluidAmount() + HYDROGEN_PER_TICK > HYDROGEN_CAPACITY) {
            return false;
        }

        this.energy -= ENERGY_PER_TICK_OXYGEN;
        this.inputTank.drain(WATER_PER_TICK, FluidAction.EXECUTE);
        this.oxygenTank.fill(new FluidStack(ModFluids.OXYGEN.get(), OXYGEN_PER_TICK), FluidAction.EXECUTE);
        this.hydrogenTank.fill(new FluidStack(ModFluids.HYDROGEN.get(), HYDROGEN_PER_TICK), FluidAction.EXECUTE);
        this.setChanged();
        return true;
    }

    /** 盐水制氯（新配方）：10 mB 水 + 1000 FE/t -> 3 氯气 + 6 氢气；每 500 mB 水消耗 1 个海盐 */
    private boolean processChlorine(ItemStack salt) {
        if (this.energy < ENERGY_PER_TICK_CHLORINE) {
            return false;
        }
        if (this.inputTank.getFluidAmount() < WATER_PER_TICK) {
            return false;
        }
        if (this.chlorineTank.getFluidAmount() + CHLORINE_PER_TICK > CHLORINE_CAPACITY) {
            return false;
        }
        if (this.hydrogenTank.getFluidAmount() + HYDROGEN_PER_TICK > HYDROGEN_CAPACITY) {
            return false;
        }

        this.energy -= ENERGY_PER_TICK_CHLORINE;
        this.inputTank.drain(WATER_PER_TICK, FluidAction.EXECUTE);
        this.chlorineTank.fill(new FluidStack(ModFluids.CHLORINE.get(), CHLORINE_PER_TICK), FluidAction.EXECUTE);
        this.hydrogenTank.fill(new FluidStack(ModFluids.HYDROGEN.get(), HYDROGEN_PER_TICK), FluidAction.EXECUTE);

        // 海盐消耗：每 500 mB 水扣 1 个（余数累计，不丢账）
        this.waterSinceSalt += WATER_PER_TICK;
        if (this.waterSinceSalt >= WATER_PER_SALT) {
            int salts = Math.min(this.waterSinceSalt / WATER_PER_SALT, salt.getCount());
            this.waterSinceSalt -= salts * WATER_PER_SALT;
            if (salts > 0) {
                salt.shrink(salts);
            }
        }
        this.setChanged();
        return true;
    }

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.electrolyzer");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new ElectrolyzerMenu(containerId, playerInventory, this);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.inputTank.readFromNBT(registries, tag.getCompound("input_tank"));
        this.oxygenTank.readFromNBT(registries, tag.getCompound("oxygen_tank"));
        if (tag.contains("chlorine_tank")) {
            this.chlorineTank.readFromNBT(registries, tag.getCompound("chlorine_tank"));
            // 修复过渡版痕迹：短命的"纯氯气版"曾把老氧气挪进 chlorine_tank，发现后搬回氧罐
            FluidStack inChlorine = this.chlorineTank.getFluid();
            if (!inChlorine.isEmpty()
                    && (inChlorine.getFluid() == ModFluids.OXYGEN.get()
                        || inChlorine.getFluid() == ModFluids.FLOWING_OXYGEN.get())) {
                FluidStack moved = this.chlorineTank.drain(this.chlorineTank.getFluidAmount(), FluidAction.EXECUTE);
                this.oxygenTank.fill(moved, FluidAction.EXECUTE);
            }
        }
        this.hydrogenTank.readFromNBT(registries, tag.getCompound("hydrogen_tank"));
        this.waterSinceSalt = tag.getInt("water_since_salt");
        this.working = tag.getBoolean("working");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
        this.syncCooldown = -1;
        this.lastSyncedInput = -1;
    }

    @Override
    protected void saveAdditional(CompoundTag tag, Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.put("input_tank", this.inputTank.writeToNBT(registries, new CompoundTag()));
        tag.put("oxygen_tank", this.oxygenTank.writeToNBT(registries, new CompoundTag()));
        tag.put("chlorine_tank", this.chlorineTank.writeToNBT(registries, new CompoundTag()));
        tag.put("hydrogen_tank", this.hydrogenTank.writeToNBT(registries, new CompoundTag()));
        tag.putInt("water_since_salt", this.waterSinceSalt);
        tag.putBoolean("working", this.working);
        tag.put("inventory", this.items.serializeNBT(registries));
    }

    @Override
    public CompoundTag getUpdateTag(Provider registries) {
        return this.saveWithoutMetadata(registries);
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}