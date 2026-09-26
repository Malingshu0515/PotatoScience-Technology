package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;

/**
 * 大型柴油发电机的方块实体（0.11 ZF125）。
 *
 * <p><b>用户原话（逐条落实）</b>：</p>
 * <pre>
 *   「加一个大型柴油发电机 3x5x2 …（30 格图纸，见 DieselGeneratorStructure）
 *     以柴油发电机控制器为正方向 右键打开GUI 显示流体储罐（8000mB）工作指示灯
 *     检测到红石信号停机 可以用流体泵泵入柴油 或用柴油桶/含有柴油的油桶右键添加柴油
 *     每t消耗1mb柴油 7.2kFE」
 * </pre>
 *
 * <p><b>数值（用户给的，一个都不改）</b>：罐 {@value #TANK_CAPACITY} mB；
 * 每 tick 烧 {@value #MB_PER_TICK} mB 柴油、发 {@value #ENERGY_PER_TICK} FE。</p>
 *
 * <p><b>三处我替用户定的默认（都在 §9 挂着待确认，写在类注释里是为了下次一眼能改）</b>：</p>
 * <ol>
 *   <li><b>内部缓冲 {@value #MAX_ENERGY} FE = 正好 1 tick 的产量。</b>用户没给缓冲数。
 *       取 1 tick 的产量 ⇒ 这台机器是"过路式"的：缓冲一满就<b>暂停烧柴油</b>
 *       （{@link #hasRoom()}，与低级发电机同一条先例：「没地方存就暂停燃烧」），
 *       既不浪费玩家的柴油，也不需要发明一个界面外的巨大数字。</li>
 *   <li><b>结构不完整 = 停机</b>（{@code STATUS_NO_STRUCTURE}）。用户写的是一台多方块机器，
 *       30 格缺一格就烧柴油是不可想象的；但界面**照开**（用户原话"右键打开GUI"，
 *       没像合金炉那样要求"先激活"），缺哪几格打在聊天栏 + 灯变黄。</li>
 *   <li><b>电只从接线口出</b>（控制器正上方那一格，成型时由接线块换成
 *       {@code diesel_generator_port}）。这是本工程多方块机器的老规矩
 *       （电力高炉「原来接线块的地方传电」、合金炉同理），所以控制器本体
 *       <b>不</b>登记能量能力 —— 玩家在控制器正面贴端子是取不到电的，得贴在接线口旁边。</li>
 * </ol>
 *
 * <p><b>柴油怎么进</b>：① 流体泵 / 管道灌（控制器本体与接线口<b>都</b>收，
 * 六面同权、只收柴油）；② 拿柴油桶或装着柴油的油桶右键控制器（{@link DieselGeneratorBlock#pourFrom}）。</p>
 *
 * <p><b>红石</b>：{@code hasNeighborSignal} ⇒ 停机（罐里的柴油保留），与全工程 13 台机器同一口径。</p>
 */
public class DieselGeneratorBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数 =================

    /** 柴油罐 8000 mB（用户原话「显示流体储罐（8000mB）」） */
    public static final int TANK_CAPACITY = 8000;
    /** 每 tick 烧 1 mB 柴油（用户原话「每t消耗1mb柴油」） */
    public static final int MB_PER_TICK = 1;
    /** 每 tick 发 7200 FE（用户原话「7.2kFE」） */
    public static final int ENERGY_PER_TICK = 7200;

    /** 内部缓冲：正好 1 tick 的产量（用户没给，见类注释第 1 条） */
    public static final int MAX_ENERGY = ENERGY_PER_TICK;
    /** 向紧邻 INPUT 端子单次推送上限（缓冲就这么大，直接给满） */
    public static final int PUSH_RATE = MAX_ENERGY;

    /** 结构复查周期（tick）：半秒一次，与合金炉的心跳同档 */
    public static final int STRUCTURE_PERIOD = 10;

    // ================= 状态灯（共享命名空间，取值与其它机器对齐）=================

    /** 有红石信号 = 停机（与其它机器一致） */
    public static final int STATUS_DISABLED = 0;
    /** 罐里没有柴油 */
    public static final int STATUS_EMPTY = 1;
    /** 电送不出去（缓冲满）—— 共用 4 号「产物没地方放」的语义，文案是本机自己的 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在发电 */
    public static final int STATUS_RUNNING = 5;
    /**
     * 结构不完整 —— <b>共享状态码里的新号（19）</b>。
     *
     * <p>⚠ §4.51 那条坑：{@code StatusLampPart} 的状态码是所有机器共用的表。
     * 6~18 全被占了（材料不够 / 没有官方桶 / 左槽是气体 / 缺氢气 / 缺氮气 / 缺催化剂 /
     * 缺氧气 / 副产物放不下 / 原料不足 / 不在油田 / 没有含水锁链 / 硫酸不够 / 原料不齐），
     * 语义都对不上"这台机器的壳没搭完" ⇒ 另起 19 号。</p>
     */
    public static final int STATUS_NO_STRUCTURE = 19;

    /**
     * 物品槽数 = 0（这台机器一个槽都没有：用户原话只给了"一个 8000 mB 的柴油罐 + 一盏工作指示灯"）。
     *
     * <p>留着这个常量是为了与其它机器同构（菜单里 {@code super(..., SLOT_COUNT, ...)}），
     * 也让 Audit 的"菜单槽数 = 方块实体槽数"那条对得上。</p>
     */
    public static final int SLOT_COUNT = 0;

    // ================= 容器同步（ContainerData）=================

    public static final int DATA_STATUS = 0;
    public static final int DATA_DIESEL = 1;
    public static final int DATA_STRUCTURE = 2;
    public static final int DATA_ENERGY = 3;
    public static final int DATA_COUNT = 4;

    // ================= 状态 =================

    private int energy;
    /** 服务端每 tick 刷新，仅供界面（不存盘） */
    private int status = STATUS_NO_STRUCTURE;
    /** 结构是否完整（每 {@value #STRUCTURE_PERIOD} tick 复查一次；不存盘，读盘后第一 tick 立刻算） */
    private boolean formed;
    /** 还有几 tick 复查结构（0 = 立刻查） */
    private int structureTimer;
    /** 正在换接线口/接线块 —— 防止 setBlock 触发的邻居更新又绕回自己 */
    private boolean swapping;

    /** 柴油罐：只收柴油（含流动变体，二者共用同一个 FluidType）。 */
    private final FluidTank tank = new FluidTank(TANK_CAPACITY, s -> isDiesel(s)) {
        @Override
        protected void onContentsChanged() {
            setChanged();
        }
    };

    /** FE 接口：<b>只出不进</b>（接在接线口上由端子来抽）。 */
    private final IEnergyStorage energyStorage = MachineEnergyStorage.extractOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                setChanged();
            });

    /**
     * 对外流体能力（六面，控制器本体）：<b>只准灌柴油、一滴都不许抽</b>。
     *
     * <p>「可以用流体泵泵入柴油」⇒ 泵的 {@code fill} 必须收；机器自己不往外吐流体，
     * 所以 {@code drain} 两个重载都返回空（与锂电池构造间"只进不出"同一个写法）。</p>
     */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return 1;
        }

        @Override
        public FluidStack getFluidInTank(int tankIndex) {
            return DieselGeneratorBlockEntity.this.tank.getFluid();
        }

        @Override
        public int getTankCapacity(int tankIndex) {
            return TANK_CAPACITY;
        }

        @Override
        public boolean isFluidValid(int tankIndex, FluidStack stack) {
            return isDiesel(stack);
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (!isDiesel(resource)) {
                return 0;
            }
            return DieselGeneratorBlockEntity.this.tank.fill(resource, action);
        }

        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            return FluidStack.EMPTY;
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            return FluidStack.EMPTY;
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_STATUS -> status;
                case DATA_DIESEL -> tank.getFluidAmount();
                case DATA_STRUCTURE -> formed ? 1 : 0;
                case DATA_ENERGY -> energy;
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

    public DieselGeneratorBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.DIESEL_GENERATOR_BE.get(), pos, state);
    }

    // ================= 读数（界面 / 探针共用）=================

    public FluidTank getTank() {
        return this.tank;
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

    public int getStatus() {
        return this.status;
    }

    public int getEnergyStored() {
        return this.energy;
    }

    public int dieselAmount() {
        return this.tank.getFluidAmount();
    }

    /** 结构是不是完整的（成型）。 */
    public boolean isFormed() {
        return this.formed;
    }

    /** 让下一次 tick 立刻复查结构（摆下方块 / 挖掉方块时调）。 */
    public void markStructureDirty() {
        this.structureTimer = 0;
    }

    /** 机器正面朝向 = 方块的 {@code FACING}。 */
    public Direction facing() {
        return this.getBlockState().getValue(DieselGeneratorBlock.FACING);
    }

    /** 这个物品是不是柴油（含流动变体）。 */
    public static boolean isDiesel(FluidStack stack) {
        return stack != null && !stack.isEmpty()
                && stack.getFluid().getFluidType() == ModFluids.DIESEL_TYPE.get();
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, DieselGeneratorBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
        }
    }

    /**
     * 服务端每 tick：先<b>把上一 tick 的电推出去</b>，再复查结构、看红石、看罐、看缓冲，
     * 最后才扣油发电。
     *
     * <p>顺序要紧：推电必须在判断"缓冲有没有地方"<b>之前</b>，否则端子明明在抽、
     * 这一 tick 也会被误判成"送不出去"而白停一 tick。</p>
     */
    private void serverTick() {
        if (this.level == null) {
            return;
        }
        pushEnergy();

        // ① 每半秒（或被邻居更新点名时）复查一次结构 —— 结构一变就换/还接线口
        if (this.structureTimer > 0) {
            this.structureTimer--;
        } else {
            this.structureTimer = STRUCTURE_PERIOD;
            recheckStructure();
        }

        // ② 红石信号 = 停机（罐里的柴油保留）
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.status = STATUS_DISABLED;
            return;
        }

        // ③ 壳没搭完 = 不烧油（界面照开，缺格打在聊天栏）
        if (!this.formed) {
            this.status = STATUS_NO_STRUCTURE;
            return;
        }

        // ④ 缓冲装不下整整一 tick 的量 ⇒ 暂停烧油（不浪费玩家的柴油）
        if (!hasRoom()) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }

        // ⑤ 罐里不足 1 mB 柴油
        if (this.tank.getFluidAmount() < MB_PER_TICK) {
            this.status = STATUS_EMPTY;
            return;
        }

        // ⑥ 扣油、发电
        this.tank.drain(MB_PER_TICK, IFluidHandler.FluidAction.EXECUTE);
        this.energy += ENERGY_PER_TICK;
        this.status = STATUS_RUNNING;
        setChanged();

        // ⑦ 立刻再推一次（刚发出来的电不必等到下一 tick）
        pushEnergy();
    }

    /** 缓冲还装得下整整一 tick 的电吗？装不下就暂停烧油。 */
    private boolean hasRoom() {
        return MAX_ENERGY - this.energy >= ENERGY_PER_TICK;
    }

    /** 推 FE 给接线口四周紧邻的 INPUT 模式端子（端子自己也会主动来抽，这里是双保险）。 */
    private void pushEnergy() {
        if (this.level == null || this.energy <= 0) {
            return;
        }
        BlockPos port = DieselGeneratorStructure.portPos(this.worldPosition);
        for (Direction direction : Direction.values()) {
            if (this.energy <= 0) {
                break;
            }
            if (this.level.getBlockEntity(port.relative(direction)) instanceof TerminalBlockEntity terminal
                    && terminal.getMode() == TerminalBlockEntity.Mode.INPUT) {
                int sent = terminal.getEnergyStorage().receiveEnergy(Math.min(PUSH_RATE, this.energy), false);
                if (sent > 0) {
                    this.energy -= sent;
                    setChanged();
                }
            }
        }
    }

    // ================= 结构复查与接线口 =================

    private void recheckStructure() {
        boolean now = DieselGeneratorStructure.complete(this.level, this.worldPosition, facing());
        if (now == this.formed) {
            return;
        }
        this.formed = now;
        this.status = now ? STATUS_EMPTY : STATUS_NO_STRUCTURE;
        setChanged();
        applyPort(now);
    }

    /**
     * 把控制器正上方那一格在【接线块】⇄【接线口】之间换。
     *
     * <p>与合金炉的接线口同一套做法：贴图完全一样（玩家看不出被换过）、挖掉掉回一个接线块。
     * 区别只有一个 —— 这里<b>只有一格</b>，而且结构散架时它会自己换回接线块
     * （合金炉是"整片外壳"那套，动一次就是 68 格）。</p>
     *
     * <p>⚠ {@code swapping} 那道锁是必须的：{@code setBlock} 会触发邻居更新，
     * 邻居里的控制器又会被点名复查结构 ⇒ 去掉锁就是自己套自己。</p>
     */
    private void applyPort(boolean toPort) {
        if (this.level == null || this.level.isClientSide || this.swapping) {
            return;
        }
        BlockPos pos = DieselGeneratorStructure.portPos(this.worldPosition);
        BlockState state = this.level.getBlockState(pos);
        if (toPort && state.is(ModBlocks.WIRING_BLOCK.get())) {
            this.swapping = true;
            try {
                this.level.setBlock(pos, ModBlocks.DIESEL_GENERATOR_PORT.get().defaultBlockState(),
                        Block.UPDATE_ALL);
            } finally {
                this.swapping = false;
            }
        } else if (!toPort && DieselGeneratorStructure.isPort(state)) {
            this.swapping = true;
            try {
                this.level.setBlock(pos, ModBlocks.WIRING_BLOCK.get().defaultBlockState(),
                        Block.UPDATE_ALL);
            } finally {
                this.swapping = false;
            }
        }
    }

    /**
     * 缺哪几格（右击控制器时打在聊天栏）。
     *
     * <p>返回 {@code null} 表示结构是完整的（调用方据此决定要不要报错）。</p>
     */
    public List<DieselGeneratorStructure.Problem> findHoles(int limit) {
        if (this.level == null) {
            return List.of();
        }
        return DieselGeneratorStructure.inspect(this.level, this.worldPosition, facing(), limit).holes();
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.diesel_generator_controller");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new DieselGeneratorMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        // ⚠ 必须自己 new 一个子标签再 put 回去，别写 tag.getCompound("tank") 往里塞（§4.49）
        this.tank.readFromNBT(registries, tag.getCompound("tank"));
        // 结构不存盘：读盘后第一 tick 会自己算（存了反而会和世界不一致）
        this.structureTimer = 0;
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        CompoundTag tankTag = new CompoundTag();
        this.tank.writeToNBT(registries, tankTag);
        tag.put("tank", tankTag);
    }
}
