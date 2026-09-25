package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.util.Mth;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * 测试流体储罐 [BlockEntity]：
 *  - 6 个档位（STOCK_PRESETS）：★ 点一下只改容量；存量原地保留（超出新容量则夹到新容量）。
 *    本版修改：不再"自带水"——调容量不会灌任何液体。
 *  - "清空"：只清存量，容量保持当前档位。
 *  - "灌满"：把存量填到当前容量（罐里有液体就灌该液体，空罐默认水）。
 *  - 自实现 IFluidHandler（容量可变，不继承 FluidTank）：fill/drain 全部自己 clamp。
 *  - GUI 数据经 ContainerData：存量按 15 位×3 拆分同步（数据槽是 short，21 亿装不下）。
 */
public class TestFluidTankBlockEntity extends BlockEntity implements MenuProvider {

    // ================== 数值（改这里） ==================
    /** 6 个档位（mB）= 容量 */
    public static final int[] STOCK_PRESETS = {100, 1_000, 10_000, 100_000, 3_276_700, 2_100_000_000};
    public static final int MAX_TIER = STOCK_PRESETS.length - 1;
    /** "清空"按钮 id（= 档位数量） */
    public static final int BUTTON_CLEAR = STOCK_PRESETS.length;
    /** "灌满"按钮 id */
    public static final int BUTTON_FILL = STOCK_PRESETS.length + 1;

    // GUI 数据槽（数据槽同步上限是 short → 存量拆 3 段）
    public static final int DATA_TIER = 0;
    public static final int DATA_STOCK_LOW = 1;
    public static final int DATA_STOCK_MID = 2;
    public static final int DATA_STOCK_HIGH = 3;
    public static final int DATA_FLUID_ID = 4;
    public static final int DATA_COUNT = 5;

    private int tierIndex = 2;                     // 当前档位，默认 10,000
    private FluidStack fluid = FluidStack.EMPTY;   // 存量（amount ≤ 当前档位容量）

    /** 自实现的储罐：容量 = 当前档位；fill/drain 全部在这里 clamp */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return 1;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return TestFluidTankBlockEntity.this.fluid.copy();
        }

        @Override
        public int getTankCapacity(int tank) {
            return capacity();
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return true;
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return 0;
            }
            FluidStack current = TestFluidTankBlockEntity.this.fluid;
            if (!current.isEmpty() && current.getFluid() != resource.getFluid()) {
                return 0;   // 不允许混装
            }
            int space = capacity() - current.getAmount();
            if (space <= 0) {
                return 0;
            }
            int toFill = Math.min(space, resource.getAmount());
            if (action.execute() && toFill > 0) {
                setStock(new FluidStack(resource.getFluid(), current.getAmount() + toFill));
            }
            return toFill;
        }

        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return FluidStack.EMPTY;
            }
            FluidStack current = TestFluidTankBlockEntity.this.fluid;
            if (current.isEmpty() || current.getFluid() != resource.getFluid()) {
                return FluidStack.EMPTY;
            }
            return drain(resource.getAmount(), action);
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            FluidStack current = TestFluidTankBlockEntity.this.fluid;
            if (maxDrain <= 0 || current.isEmpty()) {
                return FluidStack.EMPTY;
            }
            int drained = Math.min(maxDrain, current.getAmount());
            if (action.execute()) {
                int left = current.getAmount() - drained;
                setStock(left <= 0 ? FluidStack.EMPTY : new FluidStack(current.getFluid(), left));
            }
            return new FluidStack(current.getFluid(), drained);
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            int amount = TestFluidTankBlockEntity.this.fluid.getAmount();
            return switch (index) {
                case DATA_TIER -> TestFluidTankBlockEntity.this.tierIndex;
                case DATA_STOCK_LOW -> amount & 0x7FFF;
                case DATA_STOCK_MID -> (amount >>> 15) & 0x7FFF;
                case DATA_STOCK_HIGH -> (amount >>> 30) & 0x7FFF;
                case DATA_FLUID_ID -> TestFluidTankBlockEntity.this.fluid.isEmpty()
                        ? -1
                        : BuiltInRegistries.FLUID.getId(TestFluidTankBlockEntity.this.fluid.getFluid());
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
            // 只读
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public TestFluidTankBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.TEST_FLUID_TANK_BE.get(), pos, state);
    }

    // ================== 对外接口 ==================
    public IFluidHandler getFluidHandler() {
        return this.fluidHandler;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    public int getTierIndex() {
        return this.tierIndex;
    }

    /** 当前容量 = 当前档位的值 */
    public int capacity() {
        return STOCK_PRESETS[this.tierIndex];
    }

    public int getStockAmount() {
        return this.fluid.getAmount();
    }

    /** 点档位：★ 只改容量——存量原地保留（超出新容量则夹到新容量），不会自动灌任何液体 */
    public void applyPreset(int index) {
        if (index < 0 || index > MAX_TIER) {
            return;
        }
        this.tierIndex = index;
        if (!this.fluid.isEmpty()) {
            setStock(this.fluid);   // 统一走 setStock 的"夹到容量"逻辑
        }
        setChanged();
    }

    /** "清空"：只清存量，容量（档位）保持不变 —— 方便测"往罐里灌到满" */
    public void clearStock() {
        setStock(FluidStack.EMPTY);
    }

    /** "灌满"：把存量填到当前容量；罐里有液体就灌该液体，空罐默认灌水 */
    public void fillToCapacity() {
        Fluid type = this.fluid.isEmpty() ? Fluids.WATER : this.fluid.getFluid();
        setStock(new FluidStack(type, capacity()));
    }

    private void setStock(FluidStack stack) {
        if (stack.isEmpty() || stack.getAmount() <= 0) {
            this.fluid = FluidStack.EMPTY;
        } else {
            this.fluid = new FluidStack(stack.getFluid(), Math.min(stack.getAmount(), capacity()));
        }
        setChanged();
    }

    // ================== MenuProvider ==================
    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.test_fluid_tank");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new TestFluidTankMenu(containerId, playerInventory, this);
    }

    // ================== 持久化 ==================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.tierIndex = Mth.clamp(tag.getInt("tier"), 0, MAX_TIER);
        int id = tag.getInt("fluid_id");
        int amount = tag.getInt("fluid_amount");
        Fluid type = id < 0 ? null : BuiltInRegistries.FLUID.byId(id);
        if (type == null || type == Fluids.EMPTY || amount <= 0) {
            this.fluid = FluidStack.EMPTY;
        } else {
            this.fluid = new FluidStack(type, Math.min(amount, capacity()));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("tier", this.tierIndex);
        tag.putInt("fluid_id", this.fluid.isEmpty() ? -1 : BuiltInRegistries.FLUID.getId(this.fluid.getFluid()));
        tag.putInt("fluid_amount", this.fluid.getAmount());
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