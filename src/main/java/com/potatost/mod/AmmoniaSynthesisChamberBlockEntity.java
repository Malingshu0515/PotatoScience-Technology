package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
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
import net.neoforged.neoforge.fluids.FluidType;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 氨气组成室的方块实体（0.11 ZF97）。
 *
 * <p><b>用户原话（逐条落实）：</b></p>
 * <pre>
 *   「氨气组成室 GUi左侧为原料储罐和一个放催化剂（铁粉）的槽位（在槽位上文字标一下: [催化剂(铁粉)]）
 *     右侧则为输出 每t消耗1mB氮气 1mB氢气 200Fe/t 产出1mB氨气 催化剂不消耗
 *     原料储罐下方各有一个放高压气罐的槽位 可以把高压气罐内的氮/氢 50mb/t的速率灌到储罐里
 *     输出储罐的高压气罐槽为反向（氨气罐50mb/t输出给高压气罐）泵只能泵入 氮气 氢气 泵出氨气」
 * </pre>
 *
 * <p><b>① 反应（每 tick）</b>：1 mB 氮气 + 1 mB 氢气 + 200 FE → 1 mB 氨气
 * （进 2 出 1，物质不守恒 —— 这是用户给的数，不是笔误）。</p>
 *
 * <p><b>② 催化剂</b>：槽里必须有<b>铁粉</b>才开工，但<b>永不消耗</b>
 * （用户原话「催化剂不消耗」）⇒ 一台机器放一次就够了。</p>
 *
 * <p><b>③ 三个高压气罐槽</b>（原料罐下方两个 + 输出罐下方一个）：</p>
 * <ul>
 *   <li>氮/氢那两个是<b>气罐 → 储罐</b>（{@value #CONTAINER_RATE} mB/t 灌进机器）；</li>
 *   <li>氨气那个是<b>反向</b>（机器 → 气罐，同速率）。</li>
 * </ul>
 *
 * <p><b>④ 管道接口</b>：{@code fill()} 只收<b>氮气与氢气</b>（氨气灌不进来），
 * {@code drain()} 只给<b>氨气</b> —— 用户原话「泵只能泵入 氮气 氢气 泵出氨气」。</p>
 *
 * <p><b>⑤ ⚠ 两处我自己定的数</b>（用户没给）：储能 {@value #MAX_ENERGY} FE
 * （200 FE/t × 约 20 tick 的缓冲，与本工程其它机器同量级）与每个罐
 * {@value #TANK_CAPACITY} mB（一口气罐 3500 mB 刚好整个倒得进去）。
 * 要改是两个常量。</p>
 */
public class AmmoniaSynthesisChamberBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数 =================

    /** 每 tick 耗能（用户原话「200Fe/t」） */
    public static final int ENERGY_PER_TICK = 200;
    /** 每 tick 耗氮气（用户原话「每t消耗1mB氮气」） */
    public static final int NITROGEN_PER_TICK = 1;
    /** 每 tick 耗氢气（用户原话「1mB氢气」） */
    public static final int HYDROGEN_PER_TICK = 1;
    /** 每 tick 产氨气（用户原话「产出1mB氨气」） */
    public static final int AMMONIA_PER_TICK = 1;
    /** 气罐槽的搬运速率（用户原话「50mb/t的速率」「氨气罐50mb/t输出给高压气罐」） */
    public static final int CONTAINER_RATE = 50;

    /**
     * 储能 —— <b>用户没给这个数</b>，我按 4096 FE 取（200 FE/t × 约 20 tick）。
     * 与本工程其它机器同量级（电力高炉 4096 / 合金炉 32768 / 灌装机 3000）。
     */
    public static final int MAX_ENERGY = 4096;

    /**
     * 每个罐的容量 —— <b>用户没给这个数</b>，我按 4000 mB 取：
     * 一个灌满的高压气罐是 3500 mB，4000 刚好整个倒得进去（与 ZF96 那台同数）。
     */
    public static final int TANK_CAPACITY = 4000;

    // ================= 槽位 =================

    /** 催化剂槽（铁粉；只标记不消耗） */
    public static final int CATALYST_SLOT = 0;
    /** 氮气罐下方那个高压气罐槽（气罐 → 储罐） */
    public static final int NITROGEN_TANK_SLOT = 1;
    /** 氢气罐下方的气罐槽（气罐 → 储罐） */
    public static final int HYDROGEN_TANK_SLOT = 2;
    /** 氨气输出罐下方的气罐槽（**反向**：储罐 → 气罐） */
    public static final int AMMONIA_TANK_SLOT = 3;
    public static final int SLOT_COUNT = 4;

    // ================= 三个罐 =================

    public static final int TANK_COUNT = 3;
    public static final int TANK_NITROGEN = 0;
    public static final int TANK_HYDROGEN = 1;
    public static final int TANK_AMMONIA = 2;

    private static final String[] TANK_KEYS = {"Nitrogen", "Hydrogen", "Ammonia"};

    // ================= 状态灯（共享状态码） =================

    /** 有红石信号 = 关机 */
    public static final int STATUS_DISABLED = 0;
    /** 电不够 */
    public static final int STATUS_NO_POWER = 3;
    /** 氨气罐装不下了 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在合成 */
    public static final int STATUS_RUNNING = 5;
    /**
     * 氢气不够 —— <b>复用 ZF96 立的 9 号</b>：那边的语义就是「氢气不足」，
     * 两台机器说的完全是同一件事 ⇒ 不再另起新号。
     */
    public static final int STATUS_NO_HYDROGEN = 9;
    /** 氮气不够（<b>共享状态码里的新号 10</b>，ZF97 立） */
    public static final int STATUS_NO_NITROGEN = 10;
    /** 催化剂槽里没有铁粉（<b>新号 11</b>，ZF97 立） */
    public static final int STATUS_NO_CATALYST = 11;

    // ================= 容器同步（ContainerData） =================

    public static final int DATA_ENERGY = 0;
    public static final int DATA_STATUS = 1;
    public static final int DATA_NITROGEN = 2;
    public static final int DATA_HYDROGEN = 3;
    public static final int DATA_AMMONIA = 4;
    /** 催化剂槽里那件东西是不是铁粉（0/1，给界面画提示用） */
    public static final int DATA_CATALYST = 5;
    public static final int DATA_COUNT = 6;

    private int energy;
    /** 服务端每 tick 刷新，仅供界面（不存盘） */
    private int status = STATUS_RUNNING;

    private final FluidTank[] tanks = new FluidTank[TANK_COUNT];

    /**
     * 四个槽：催化剂（只收铁粉）+ 三个气罐槽（只收流体容器）。
     *
     * <p>⚠ 与菜单里的 {@code SlotItemHandler} 是**同一道门禁**，两处必须一起改（§4.51）。</p>
     */
    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            if (slot == CATALYST_SLOT) {
                return stack.is(ModItems.IRON_POWDER.get());
            }
            // 三个气罐槽：只认流体容器接口（高压气罐/油桶都算，收不收某种流体由容器自己判）
            return stack.getItem() instanceof FluidContainerItem;
        }
    };

    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                this.setChanged();
            });

    /**
     * 管道接口：<b>只进氮/氢、只出氨</b>（用户原话「泵只能泵入 氮气 氢气 泵出氨气」）。
     */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return TANK_COUNT;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return AmmoniaSynthesisChamberBlockEntity.this.tanks[tank].getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return AmmoniaSynthesisChamberBlockEntity.this.tanks[tank].getCapacity();
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return AmmoniaSynthesisChamberBlockEntity.this.tanks[tank].isFluidValid(stack);
        }

        /** 灌入：只有氮气罐与氢气罐收料；**氨气灌不进来**。 */
        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return 0;
            }
            FluidType type = resource.getFluid().getFluidType();
            if (type == ModFluids.NITROGEN_TYPE.get()) {
                return AmmoniaSynthesisChamberBlockEntity.this.tanks[TANK_NITROGEN].fill(resource, action);
            }
            if (type == ModFluids.HYDROGEN_TYPE.get()) {
                return AmmoniaSynthesisChamberBlockEntity.this.tanks[TANK_HYDROGEN].fill(resource, action);
            }
            return 0;
        }

        /** 抽走：**只有氨气**能被抽走（氮/氢是进料，泵抽不走）。 */
        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return FluidStack.EMPTY;
            }
            return AmmoniaSynthesisChamberBlockEntity.this.tanks[TANK_AMMONIA].drain(resource, action);
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            return AmmoniaSynthesisChamberBlockEntity.this.tanks[TANK_AMMONIA].drain(maxDrain, action);
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_ENERGY -> energy;
                case DATA_STATUS -> status;
                case DATA_NITROGEN -> tanks[TANK_NITROGEN].getFluidAmount();
                case DATA_HYDROGEN -> tanks[TANK_HYDROGEN].getFluidAmount();
                case DATA_AMMONIA -> tanks[TANK_AMMONIA].getFluidAmount();
                case DATA_CATALYST -> hasCatalyst() ? 1 : 0;
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

    public AmmoniaSynthesisChamberBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.AMMONIA_SYNTHESIS_CHAMBER_BE.get(), pos, state);
        this.tanks[TANK_NITROGEN] = new FluidTank(TANK_CAPACITY,
                stack -> isType(stack, ModFluids.NITROGEN_TYPE.get()));
        this.tanks[TANK_HYDROGEN] = new FluidTank(TANK_CAPACITY,
                stack -> isType(stack, ModFluids.HYDROGEN_TYPE.get()));
        this.tanks[TANK_AMMONIA] = new FluidTank(TANK_CAPACITY,
                stack -> isType(stack, ModFluids.AMMONIA_TYPE.get()));
    }

    private static boolean isType(FluidStack stack, FluidType type) {
        return stack != null && !stack.isEmpty() && stack.getFluid().getFluidType() == type;
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public FluidTank getTank(int index) {
        return this.tanks[index];
    }

    public IFluidHandler getFluidHandler() {
        return this.fluidHandler;
    }

    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state,
                            AmmoniaSynthesisChamberBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
        }
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }

        // ① 三个气罐槽的搬运（与反应无关，随时都搬 —— 用户原话只给了速率，没说要在反应时才搬）
        boolean moved = transferFromContainer(NITROGEN_TANK_SLOT, TANK_NITROGEN);
        moved |= transferFromContainer(HYDROGEN_TANK_SLOT, TANK_HYDROGEN);
        moved |= transferToContainer(AMMONIA_TANK_SLOT, TANK_AMMONIA);
        if (moved) {
            setChanged();
        }

        // ② 红石信号 = 关机
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.status = STATUS_DISABLED;
            return;
        }
        // ③ 催化剂：槽里必须有铁粉（**不消耗**）
        if (!hasCatalyst()) {
            this.status = STATUS_NO_CATALYST;
            return;
        }
        // ④ 两种原料都得有
        if (this.tanks[TANK_NITROGEN].getFluidAmount() < NITROGEN_PER_TICK) {
            this.status = STATUS_NO_NITROGEN;
            return;
        }
        if (this.tanks[TANK_HYDROGEN].getFluidAmount() < HYDROGEN_PER_TICK) {
            this.status = STATUS_NO_HYDROGEN;
            return;
        }
        // ⑤ 氨气罐要装得下
        if (this.tanks[TANK_AMMONIA].getSpace() < AMMONIA_PER_TICK) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }
        // ⑥ 付电
        if (this.energy < ENERGY_PER_TICK) {
            this.status = STATUS_NO_POWER;
            return;
        }
        this.energy -= ENERGY_PER_TICK;
        this.tanks[TANK_NITROGEN].drain(NITROGEN_PER_TICK, IFluidHandler.FluidAction.EXECUTE);
        this.tanks[TANK_HYDROGEN].drain(HYDROGEN_PER_TICK, IFluidHandler.FluidAction.EXECUTE);
        this.tanks[TANK_AMMONIA].fill(new FluidStack(ModFluids.AMMONIA.get(), AMMONIA_PER_TICK),
                IFluidHandler.FluidAction.EXECUTE);
        this.status = STATUS_RUNNING;
        setChanged();
    }

    /** 催化剂槽里是铁粉吗（数量 ≥ 1 即可；**永不消耗**）。 */
    public boolean hasCatalyst() {
        ItemStack stack = this.items.getStackInSlot(CATALYST_SLOT);
        return !stack.isEmpty() && stack.is(ModItems.IRON_POWDER.get());
    }

    /**
     * 把气罐里的流体灌进机器罐（氮/氢那两个槽）。
     *
     * <p>三步走（照 {@code FillingMachineBlockEntity#tryFillSlot} 的反方向）：
     * ① 容器里是不是这种气体 ⇒ ② 机器罐还有多少空间 ⇒ ③ 取多少灌多少，
     * 全程用真实数量，不会出现"取多了塞不回去"。</p>
     *
     * @return 真的搬动了就 true（调用方据此标脏）
     */
    private boolean transferFromContainer(int slot, int tankIndex) {
        FluidContainerItem container = containerOf(this.items.getStackInSlot(slot));
        if (container == null) {
            return false;
        }
        ItemStack stack = this.items.getStackInSlot(slot);
        FluidStack held = container.contents(stack);
        if (held.isEmpty()) {
            return false;
        }
        FluidTank tank = this.tanks[tankIndex];
        if (!tank.isFluidValid(held)) {
            return false;                     // 槽里是别的气体（例如把氨气罐塞进氮气槽）
        }
        int want = Math.min(CONTAINER_RATE, held.getAmount());
        int accepted = tank.fill(held.copyWithAmount(want), IFluidHandler.FluidAction.SIMULATE);
        if (accepted <= 0) {
            return false;
        }
        FluidStack drained = container.drain(stack, accepted);
        if (drained.isEmpty()) {
            return false;
        }
        int filled = tank.fill(drained, IFluidHandler.FluidAction.EXECUTE);
        if (filled < drained.getAmount()) {
            // 理论上不会发生（刚 SIMULATE 过）；真发生了就把多取的塞回容器，绝不凭空吞流体
            container.fill(stack, drained.copyWithAmount(drained.getAmount() - Math.max(filled, 0)),
                    drained.getAmount());
        }
        this.items.setStackInSlot(slot, stack);
        return filled > 0;
    }

    /**
     * 把机器罐里的流体灌进气罐（**氨气那个槽是反向的** —— 用户原话
     * 「输出储罐的高压气罐槽为反向（氨气罐50mb/t输出给高压气罐）」）。
     */
    private boolean transferToContainer(int slot, int tankIndex) {
        FluidContainerItem container = containerOf(this.items.getStackInSlot(slot));
        if (container == null) {
            return false;
        }
        ItemStack stack = this.items.getStackInSlot(slot);
        FluidTank tank = this.tanks[tankIndex];
        if (tank.isEmpty() || container.space(stack) <= 0) {
            return false;
        }
        int want = Math.min(CONTAINER_RATE, tank.getFluidAmount());
        int moved = container.fill(stack, tank.getFluid().copyWithAmount(want), want);
        if (moved <= 0) {
            return false;
        }
        tank.drain(moved, IFluidHandler.FluidAction.EXECUTE);
        this.items.setStackInSlot(slot, stack);
        return true;
    }

    /** 槽里那件物品如果是流体容器就返回它，否则 null。 */
    private static FluidContainerItem containerOf(ItemStack stack) {
        return stack.getItem() instanceof FluidContainerItem container ? container : null;
    }

    // ================= 读数（界面 / 探针共用） =================

    public int getEnergy() {
        return this.energy;
    }

    public int getStatus() {
        return this.status;
    }

    public int amountOf(int tank) {
        return this.tanks[tank].getFluidAmount();
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.ammonia_synthesis_chamber");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new AmmoniaSynthesisChamberMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.status = tag.getInt("status");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
        for (int i = 0; i < TANK_COUNT; i++) {
            this.tanks[i].readFromNBT(registries, tag.getCompound(TANK_KEYS[i]));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("status", this.status);
        tag.put("inventory", this.items.serializeNBT(registries));
        for (int i = 0; i < TANK_COUNT; i++) {
            // ⚠ 必须自己 new 一个子标签再 put 回去（§4.49）
            CompoundTag child = new CompoundTag();
            this.tanks[i].writeToNBT(registries, child);
            tag.put(TANK_KEYS[i], child);
        }
    }
}
