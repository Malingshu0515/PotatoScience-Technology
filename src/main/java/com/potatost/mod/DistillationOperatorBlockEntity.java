package com.potatost.mod;

import java.util.function.IntSupplier;
import java.util.function.Predicate;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 分馏塔操作器的方块实体（0.11 ZF78）：把原油裂成柴油 / 石脑油 / 汽油 / 液化石油气 + 沥青。
 *
 * <p><b>用户给的数（逐条落实，全部是本文件的常量）</b>：</p>
 * <ul>
 *   <li>容量<b>按塔数缩放</b>：一座塔 → 能量 8096 FE、石油 12 桶（12000 mB）、
 *       每种产品 2.5 桶（2500 mB）；</li>
 *   <li>速率<b>每座塔各跑一份</b>（ZF78 用户拍板）：每 tick、每塔消耗
 *       8 mB 石油 + 8096 FE，产出 3 mB 柴油 + 2 mB 石脑油 + 2 mB 汽油 + 1 mB 液化石油气
 *       （进 8 出 8，物料是平的）；</li>
 *   <li>每 5 tick、每塔出 1 块<b>沥青</b>；沥青槽满 64 且没清理 ⇒ <b>整台停机</b>；</li>
 *   <li><b>有红石信号才分馏</b>（与微型粉碎机/盐分解构器相反：那几个是"有信号就停"）。</li>
 * </ul>
 *
 * <p>塔数由相邻的 {@link DistillationControllerBlockEntity} 推过来
 * （用户原话「控制器只负责发送检测的分馏塔数量给操作器」），这里再夹到
 * {@link #MAX_TOWERS} 座（用户原话「最多识别 4 个分馏塔」）。</p>
 *
 * <p><b>为什么塔数每 20 tick 还要复核一次</b>：控制器被拆掉以后没人会通知这台操作器，
 * 不复核的话它会拿着一个永远不过期的塔数一直分馏下去。</p>
 */
public class DistillationOperatorBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数 =================

    /** 一座塔提供的能量缓冲（FE） */
    public static final int FE_PER_TOWER = 8096;
    /** 一座塔提供的石油罐容量（12 桶 = 12000 mB） */
    public static final int OIL_PER_TOWER = 12 * 1000;
    /** 一座塔提供的每种产品罐容量（2.5 桶 = 2500 mB） */
    public static final int PRODUCT_PER_TOWER = 2500;

    /** 每 tick、每座塔的进料：8 mB 石油 + 8096 FE */
    public static final int OIL_PER_TICK = 8;
    public static final int FE_PER_TICK = 8096;

    /** 每 tick、每座塔的产物 */
    public static final int DIESEL_PER_TICK = 3;
    public static final int NAPHTHA_PER_TICK = 2;
    public static final int GASOLINE_PER_TICK = 2;
    public static final int LPG_PER_TICK = 1;

    /** 每 5 tick、每座塔出 1 块沥青 */
    public static final int BITUMEN_INTERVAL = 5;
    /** 沥青槽位上限（用户原话「沥青满 64 不清理则会停止分馏」） */
    public static final int BITUMEN_LIMIT = 64;

    /** 最多认几座塔（用户原话「最多识别4个分馏塔」） */
    public static final int MAX_TOWERS = DistillationTowerStructure.MAX_TOWERS;

    /** 「相邻控制器」的复核周期（tick） */
    public static final int CONTROLLER_CHECK_INTERVAL = 20;

    // ================= 槽位 =================

    public static final int SLOT_COUNT = 1;
    /** 沥青槽位（界面右下角那一个） */
    public static final int BITUMEN_SLOT = 0;

    // ================= 罐 =================

    public static final int TANK_COUNT = 5;
    /** 总石油储罐（进料） */
    public static final int TANK_OIL = 0;
    public static final int TANK_DIESEL = 1;
    public static final int TANK_NAPHTHA = 2;
    public static final int TANK_GASOLINE = 3;
    public static final int TANK_LPG = 4;

    private static final String[] TANK_KEYS = {"Oil", "Diesel", "Naphtha", "Gasoline", "Lpg"};

    // ================= 界面状态码 =================

    public static final int STATUS_RUNNING = 0;
    public static final int STATUS_NO_CONTROLLER = 1;
    public static final int STATUS_NO_TOWER = 2;
    public static final int STATUS_NO_REDSTONE = 3;
    public static final int STATUS_BITUMEN_FULL = 4;
    public static final int STATUS_NO_OIL = 5;
    public static final int STATUS_NO_POWER = 6;
    public static final int STATUS_PRODUCT_FULL = 7;

    // ================= 容器同步（ContainerData）=================

    public static final int DATA_ENERGY = 0;
    public static final int DATA_TOWERS = 1;
    public static final int DATA_STATUS = 2;
    public static final int DATA_PROGRESS = 3;
    public static final int DATA_DIESEL = 4;
    public static final int DATA_NAPHTHA = 5;
    public static final int DATA_GASOLINE = 6;
    public static final int DATA_LPG = 7;
    /**
     * 石油量拆两个槽位传：低 15 位 + 高 15 位。
     *
     * <p>⚠ 载荷是<b>短整型</b>（{@code ClientboundContainerSetDataPacket} 写的是
     * {@code writeShort}），石油上限 12000×4 = 48000 早就超了 32767 ——
     * 不分片的话界面会看到负数。产品罐最多 10000、能量最多 32384，都还在范围内，
     * 所以只有石油需要拆（拆法照抄测试储罐 {@code DATA_STOCK_LOW/MID/HIGH}）。</p>
     */
    public static final int DATA_OIL_LOW = 8;
    public static final int DATA_OIL_HIGH = 9;
    public static final int DATA_COUNT = 10;

    /** 每个分片 15 位（与测试储罐同一口径） */
    public static final int DATA_CHUNK_BITS = 15;
    public static final int DATA_CHUNK_MASK = (1 << DATA_CHUNK_BITS) - 1;

    // ================= 状态 =================

    private int energy;
    private int towerCount;
    private int status = STATUS_NO_CONTROLLER;
    private int progress;
    private int controllerCheckTimer;
    private boolean controllerPresent;

    private final FluidTank[] tanks = new FluidTank[TANK_COUNT];

    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            // 沥青槽位只收沥青（别的物品塞不进来；取出随便取）
            return stack.is(ModItems.BITUMEN.get());
        }
    };

    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(
            this::maxEnergy,
            () -> this.energy,
            value -> {
                this.energy = value;
                this.setChanged();
            });

    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return TANK_COUNT;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return DistillationOperatorBlockEntity.this.tanks[tank].getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return DistillationOperatorBlockEntity.this.tanks[tank].getCapacity();
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return DistillationOperatorBlockEntity.this.tanks[tank].isFluidValid(stack);
        }

        /**
         * 灌入：<b>只有石油罐收料</b>。四个产品罐是出口 —— 管道/泵往里灌柴油会被拒，
         * 免得把"产物"和"进料"搅在一起（这也是自动化最容易接错的地方）。
         */
        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return 0;
            }
            return DistillationOperatorBlockEntity.this.tanks[TANK_OIL].fill(resource, action);
        }

        /** 抽走：按流体种类找到对应那个罐（抽石油也行，方便手动/自动化清罐）。 */
        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return FluidStack.EMPTY;
            }
            for (FluidTank tank : DistillationOperatorBlockEntity.this.tanks) {
                FluidStack held = tank.getFluid();
                if (!held.isEmpty()
                        && FluidStack.isSameFluidSameComponents(held, resource)) {
                    return tank.drain(resource.getAmount(), action);
                }
            }
            return FluidStack.EMPTY;
        }

        /** 不指定流体时按「石油 → 柴油 → 石脑油 → 汽油 → 液化石油气」的顺序抽第一个有货的罐。 */
        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            for (FluidTank tank : DistillationOperatorBlockEntity.this.tanks) {
                if (tank.getFluidAmount() > 0) {
                    return tank.drain(maxDrain, action);
                }
            }
            return FluidStack.EMPTY;
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            switch (index) {
                case DATA_ENERGY:
                    return DistillationOperatorBlockEntity.this.energy;
                case DATA_TOWERS:
                    return DistillationOperatorBlockEntity.this.towerCount;
                case DATA_STATUS:
                    return DistillationOperatorBlockEntity.this.status;
                case DATA_PROGRESS:
                    return DistillationOperatorBlockEntity.this.progress;
                case DATA_DIESEL:
                    return DistillationOperatorBlockEntity.this.tanks[TANK_DIESEL].getFluidAmount();
                case DATA_NAPHTHA:
                    return DistillationOperatorBlockEntity.this.tanks[TANK_NAPHTHA].getFluidAmount();
                case DATA_GASOLINE:
                    return DistillationOperatorBlockEntity.this.tanks[TANK_GASOLINE].getFluidAmount();
                case DATA_LPG:
                    return DistillationOperatorBlockEntity.this.tanks[TANK_LPG].getFluidAmount();
                case DATA_OIL_LOW:
                    return DistillationOperatorBlockEntity.this.oilAmount() & DATA_CHUNK_MASK;
                case DATA_OIL_HIGH:
                    return (DistillationOperatorBlockEntity.this.oilAmount() >>> DATA_CHUNK_BITS) & DATA_CHUNK_MASK;
                default:
                    return 0;
            }
        }

        @Override
        public void set(int index, int value) {
            // 服务端读自己的字段，客户端由 SimpleContainerData 镜像（本模组一贯写法）
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public DistillationOperatorBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.DISTILLATION_OPERATOR_BE.get(), pos, state);
        this.tanks[TANK_OIL] = new ScaledTank(OIL_PER_TOWER, () -> this.towerCount,
                stack -> isType(stack, ModFluids.CRUDE_OIL_TYPE.get()), this::setChanged);
        this.tanks[TANK_DIESEL] = new ScaledTank(PRODUCT_PER_TOWER, () -> this.towerCount,
                stack -> isType(stack, ModFluids.DIESEL_TYPE.get()), this::setChanged);
        this.tanks[TANK_NAPHTHA] = new ScaledTank(PRODUCT_PER_TOWER, () -> this.towerCount,
                stack -> isType(stack, ModFluids.NAPHTHA_TYPE.get()), this::setChanged);
        this.tanks[TANK_GASOLINE] = new ScaledTank(PRODUCT_PER_TOWER, () -> this.towerCount,
                stack -> isType(stack, ModFluids.GASOLINE_TYPE.get()), this::setChanged);
        this.tanks[TANK_LPG] = new ScaledTank(PRODUCT_PER_TOWER, () -> this.towerCount,
                stack -> isType(stack, ModFluids.LPG_TYPE.get()), this::setChanged);
    }

    /**
     * 罐里收不收这种流体：比的是<b>流体类型</b>而不是流体本体 ——
     * 这样 source 与 flowing 两个本体都收（管道里跑的可能就是 flowing 那个）。
     */
    private static boolean isType(FluidStack stack, net.neoforged.neoforge.fluids.FluidType type) {
        return stack != null && !stack.isEmpty() && stack.getFluid().getFluidType() == type;
    }

    // ================= tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, DistillationOperatorBlockEntity operator) {
        if (level.isClientSide) {
            return;
        }
        operator.serverTick();
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }

        // ① 定期复核"旁边还有没有控制器"（拆了控制器就没人通知我们了）
        if (this.controllerCheckTimer > 0) {
            this.controllerCheckTimer--;
        } else {
            this.controllerCheckTimer = CONTROLLER_CHECK_INTERVAL;
            this.controllerPresent = hasAdjacentController();
            if (!this.controllerPresent) {
                this.towerCount = 0;
            }
        }

        int towers = this.towerCount;
        int next;
        boolean working = false;
        if (!this.controllerPresent) {
            next = STATUS_NO_CONTROLLER;
        } else if (towers <= 0) {
            next = STATUS_NO_TOWER;
        } else if (!this.level.hasNeighborSignal(this.worldPosition)) {
            next = STATUS_NO_REDSTONE;
        } else if (bitumenSpace() <= 0) {
            next = STATUS_BITUMEN_FULL;
        } else if (this.tanks[TANK_OIL].getFluidAmount() < OIL_PER_TICK * towers) {
            next = STATUS_NO_OIL;
        } else if (this.energy < FE_PER_TICK * towers) {
            next = STATUS_NO_POWER;
        } else if (!hasProductRoom(towers)) {
            next = STATUS_PRODUCT_FULL;
        } else {
            next = STATUS_RUNNING;
            working = true;
        }

        if (working) {
            processTick(towers);
        }
        if (next != this.status) {
            this.status = next;
            this.setChanged();
        }
    }

    /** 一 tick 的分馏：扣 8×N mB 石油与 8096×N FE，加 3/2/2/1×N mB 产品；每 5 tick 出 N 块沥青。 */
    private void processTick(int towers) {
        this.tanks[TANK_OIL].drain(OIL_PER_TICK * towers, IFluidHandler.FluidAction.EXECUTE);
        this.energy -= FE_PER_TICK * towers;

        this.tanks[TANK_DIESEL].fill(
                new FluidStack(ModFluids.DIESEL.get(), DIESEL_PER_TICK * towers),
                IFluidHandler.FluidAction.EXECUTE);
        this.tanks[TANK_NAPHTHA].fill(
                new FluidStack(ModFluids.NAPHTHA.get(), NAPHTHA_PER_TICK * towers),
                IFluidHandler.FluidAction.EXECUTE);
        this.tanks[TANK_GASOLINE].fill(
                new FluidStack(ModFluids.GASOLINE.get(), GASOLINE_PER_TICK * towers),
                IFluidHandler.FluidAction.EXECUTE);
        this.tanks[TANK_LPG].fill(
                new FluidStack(ModFluids.LPG.get(), LPG_PER_TICK * towers),
                IFluidHandler.FluidAction.EXECUTE);

        this.progress++;
        if (this.progress >= BITUMEN_INTERVAL) {
            this.progress = 0;
            // 一次最多出 N 块；槽位快满时只出装得下的那几块（宁可少出，也不把沥青凭空销毁）
            int made = Math.min(towers, bitumenSpace());
            if (made > 0) {
                this.items.insertItem(BITUMEN_SLOT, new ItemStack(ModItems.BITUMEN.get(), made), false);
            }
        }
        this.setChanged();
    }

    /** 四个产品罐都得装得下这一 tick 的产出，否则整台停机（不够放就一滴都不炼）。 */
    private boolean hasProductRoom(int towers) {
        return roomFor(this.tanks[TANK_DIESEL], DIESEL_PER_TICK * towers)
                && roomFor(this.tanks[TANK_NAPHTHA], NAPHTHA_PER_TICK * towers)
                && roomFor(this.tanks[TANK_GASOLINE], GASOLINE_PER_TICK * towers)
                && roomFor(this.tanks[TANK_LPG], LPG_PER_TICK * towers);
    }

    private static boolean roomFor(FluidTank tank, int amount) {
        return tank.getSpace() >= amount;
    }

    /** 沥青槽位还能塞几块（空槽 = 64；槽里是别的物品 = 0 —— 理论上进不来）。 */
    public int bitumenSpace() {
        ItemStack stack = this.items.getStackInSlot(BITUMEN_SLOT);
        if (stack.isEmpty()) {
            return BITUMEN_LIMIT;
        }
        if (!stack.is(ModItems.BITUMEN.get())) {
            return 0;
        }
        return Math.max(0, BITUMEN_LIMIT - stack.getCount());
    }

    /** 六面里有没有分馏塔控制器。 */
    public boolean hasAdjacentController() {
        if (this.level == null) {
            return false;
        }
        for (Direction dir : Direction.values()) {
            if (this.level.getBlockEntity(this.worldPosition.relative(dir))
                    instanceof DistillationControllerBlockEntity) {
                return true;
            }
        }
        return false;
    }

    /** 控制器推过来的塔数：这里夹到 {@link #MAX_TOWERS} 座（用户原话「最多识别4个分馏塔」）。 */
    public void setTowerCount(int count) {
        int clamped = Mth.clamp(count, 0, MAX_TOWERS);
        if (clamped != this.towerCount) {
            this.towerCount = clamped;
            this.setChanged();
        }
    }

    // ================= 读数（界面 / 探针共用）=================

    public int getEnergy() {
        return this.energy;
    }

    /** 能量上限 = 8096 × 塔数。 */
    public int maxEnergy() {
        return FE_PER_TOWER * this.towerCount;
    }

    public int getTowerCount() {
        return this.towerCount;
    }

    public int getStatus() {
        return this.status;
    }

    public int getProgress() {
        return this.progress;
    }

    /** 已消耗的石油（mB，供探针核对"每 tick 正好扣 8×塔数"）。 */
    public int oilAmount() {
        return this.tanks[TANK_OIL].getFluidAmount();
    }

    public FluidTank getTank(int index) {
        return this.tanks[index];
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public IFluidHandler getFluidHandler() {
        return this.fluidHandler;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    // ================= 存盘 =================

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("Energy", this.energy);
        tag.putInt("Progress", this.progress);
        tag.put("Items", this.items.serializeNBT(registries));
        for (int i = 0; i < TANK_COUNT; i++) {
            CompoundTag child = new CompoundTag();
            // ⚠ 必须自己 new 一个子标签再 put 回去：CompoundTag#getCompound 在没有键时
            //   返回的是一个**没挂到父标签上**的新对象，往里写等于扔掉。
            this.tanks[i].writeToNBT(registries, child);
            tag.put(TANK_KEYS[i], child);
        }
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("Energy");
        this.progress = tag.getInt("Progress");
        this.items.deserializeNBT(registries, tag.getCompound("Items"));
        for (int i = 0; i < TANK_COUNT; i++) {
            this.tanks[i].readFromNBT(registries, tag.getCompound(TANK_KEYS[i]));
        }
    }

    // ================= 菜单 =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.distillation_operator");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new DistillationOperatorMenu(containerId, playerInventory, this);
    }

    /**
     * 容量随塔数缩放的罐。
     *
     * <p>NeoForge 的 {@link FluidTank} 把容量钉在构造时的 {@code capacity} 字段里，
     * {@code fill()} 读的也是那个字段 ⇒ <b>只重写 {@code getCapacity()} 是不够的</b>，
     * {@code fill}/{@code getSpace} 必须一起重写（这是本类最容易写错的一处）。</p>
     *
     * <p>塔数变少时<b>不销毁已存的流体</b>：存量可能一时高于新容量，
     * 那时 {@code getSpace()} 为 0 ⇒ 只进不出地"堵住"，等抽走就恢复。</p>
     */
    private static final class ScaledTank extends FluidTank {

        private final int perTower;
        private final IntSupplier towers;
        private final Runnable onChanged;

        ScaledTank(int perTower, IntSupplier towers, Predicate<FluidStack> validator, Runnable onChanged) {
            super(perTower, validator);
            this.perTower = perTower;
            this.towers = towers;
            this.onChanged = onChanged;
        }

        @Override
        public int getCapacity() {
            return Math.max(0, this.perTower * this.towers.getAsInt());
        }

        @Override
        public int getSpace() {
            return Math.max(0, getCapacity() - getFluidAmount());
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (resource.isEmpty() || !isFluidValid(resource)) {
                return 0;
            }
            if (!this.fluid.isEmpty() && !FluidStack.isSameFluidSameComponents(this.fluid, resource)) {
                return 0;
            }
            int accepted = Math.min(getSpace(), resource.getAmount());
            if (accepted <= 0) {
                return 0;
            }
            if (action.execute()) {
                if (this.fluid.isEmpty()) {
                    this.fluid = resource.copyWithAmount(accepted);
                } else {
                    this.fluid.grow(accepted);
                }
                onContentsChanged();
            }
            return accepted;
        }

        @Override
        protected void onContentsChanged() {
            // ScaledTank 是静态内部类，拿不到外层方块实体的 this ⇒ 由构造时传进来的 Runnable 标脏
            this.onChanged.run();
        }
    }
}
