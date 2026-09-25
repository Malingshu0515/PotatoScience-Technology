package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
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
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 加氢脱硫反应仓的方块实体（0.11 ZF96）。
 *
 * <p><b>用户原话（逐条落实）：</b></p>
 * <pre>
 *   「加一个 加氢脱硫反应仓 GUI 一个氢气罐 左侧放沥青
 *     每16个沥青 消耗1000mB氢气 10s  产出一个 硫」
 * </pre>
 * ⇒ 一次操作（一批）：<b>16 个沥青 + 1000 mB 氢气 → 200 tick（10 秒）→ 1 个硫</b>。
 *
 * <p><b>界面就是用户描述的那两样</b>：一个氢气罐（{@link #TANK_CAPACITY} mB，
 * 只收氢气）+ 左侧一个沥青槽 + 右侧一个硫输出槽 + 一支进度箭头 + 一盏状态灯。</p>
 *
 * <p><b>⚠ 这台机器不吃电</b>：用户没给能耗数 ⇒ 本轮<b>不耗电</b>（与容器换流器 ZF82
 * 同一条先例：没给的数不自己发明）。所以它没有能量条、没有能量能力，
 * 状态灯上的<b>红灯（"没电"）在这台机器上永远不会出现</b> —— 两种缺料（沥青不够 / 氢气不够）
 * 都是黄灯。</p>
 *
 * <p><b>为什么"批"而不是"每 tick 持续产出"</b>：用户给的是「每 16 个沥青 … 10s 产出一个硫」，
 * 是一批一批的节奏（与盐分解构器/液压机同一类），不是电解器那种每 tick 出流体的连续配方。</p>
 *
 * <p><b>三条硬规矩（照抄本工程踩平过的那几套）：</b></p>
 * <ol>
 *   <li><b>放不下就原地等</b>：最后一 tick 先看输出槽装不装得下 1 个硫，
 *       装不下就<b>既不扣料也不产出</b>（§4.14 的原事故：扣了输入却没落产物 = 吞东西）；</li>
 *   <li><b>缺料不重置进度</b>：玩家分两批凑够 16 个沥青、或者中途罐里氢气掉到 1000 以下，
 *       已经跑过的进度<b>保留</b>（与盐分解构器同一条口径）；</li>
 *   <li><b>最后一 tick 才扣料</b>：前面每一 tick 只推进度、不动沥青也不动氢气
 *       ⇒ 中途被拆机/停电不会吃掉材料。</li>
 * </ol>
 */
public class HydrodesulfurizationChamberBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数 =================

    /** 一批要几个沥青（用户原话「每16个沥青」） */
    public static final int BITUMEN_PER_OPERATION = 16;
    /** 一批要多少 mB 氢气（用户原话「消耗1000mB氢气」） */
    public static final int HYDROGEN_PER_OPERATION = 1000;
    /** 一批出几个硫（用户原话「产出一个 硫」） */
    public static final int SULFUR_PER_OPERATION = 1;
    /** 一批要多久（用户原话「10s」= 200 tick） */
    public static final int DURATION_TICKS = 200;

    /**
     * 氢气罐容量 —— <b>用户没给这个数</b>，我按"4 批"取 4000 mB。
     *
     * <p>取这个值的理由：一个灌满的高压气罐是 3500 mB（{@code TankContents} 里钉死的），
     * 4000 的罐刚好能把它<b>整个倒进去</b>（倒 3500），够跑 3 批半；
     * 若取 1000（正好一批）则每跑一批都得重新接管道/倒一次，10 秒一批的节奏下太碎。
     * <b>这只是我选的数，要改说一声</b>（一个常量）。</p>
     */
    public static final int TANK_CAPACITY = 4000;

    /**
     * 手倒：手里拿着装氢气的容器右键机器，一次最多倒进去多少 mB
     * （与分馏塔操作器/灌装机同一个口径：{@code POUR_PER_CLICK = 1000}）。
     */
    public static final int POUR_PER_CLICK = 1000;

    // ================= 槽位 =================

    /** 沥青槽（界面左侧那一个） */
    public static final int INPUT_SLOT = 0;
    /** 硫输出槽 */
    public static final int OUTPUT_SLOT = 1;
    public static final int SLOT_COUNT = 2;

    // ================= 状态灯（共享命名空间，取值与其它机器对齐） =================

    /** 有红石信号 = 关机（与微型粉碎机/盐分解构器/液压机一致） */
    public static final int STATUS_DISABLED = 0;
    /** 沥青槽是空的 */
    public static final int STATUS_EMPTY = 1;
    /** 沥青不够一批（16 个）—— 语义与液压机的 6 号「材料数量不够」相同 */
    public static final int STATUS_MATERIAL = 6;
    /** 产物放不下 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在反应 */
    public static final int STATUS_RUNNING = 5;
    /**
     * 氢气不够一批（1000 mB）—— <b>本工程共享状态码里的新号（9）</b>。
     *
     * <p>⚠ 与 §4.51 那条同一个坑：{@code StatusLampPart} 的状态码是<b>所有机器共用</b>的一张表，
     * 加号之前先看语义能不能共用 —— 3 号是「没电」，这台机器根本不吃电，
     * 拿它当"没氢气"会让灯光提示与代码语义对不上；所以另起 9 号，
     * 并在 {@code StatusLampPart} 里补上黄灯 + 文案后缀。</p>
     */
    public static final int STATUS_NO_HYDROGEN = 9;

    // ================= 容器同步（ContainerData） =================

    public static final int DATA_PROGRESS = 0;
    public static final int DATA_PROGRESS_MAX = 1;
    public static final int DATA_STATUS = 2;
    /** 罐里有多少 mB 氢气（上限 4000 ≪ 32767 ⇒ 不用分片，见 §4.48） */
    public static final int DATA_TANK = 3;
    /** 罐里是哪种流体（传**流体注册表 id**，0 = 空；与灌装机同一条口径） */
    public static final int DATA_TANK_FLUID = 4;
    public static final int DATA_COUNT = 5;

    // ================= 状态 =================

    private int progress;
    private int progressMax = DURATION_TICKS;
    /** 服务端每 tick 刷新，仅供界面（不存盘） */
    private int status = STATUS_EMPTY;

    /** 0 号沥青（只收沥青）；1 号硫（只能取，不能放）。 */
    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            // 沥青槽只收沥青（别的物品塞不进来；取出随便取）。
            // ⚠ 与菜单里的 SlotItemHandler 是**同一道门禁**，两处必须一起改（§4.51 的原事故）。
            return slot == INPUT_SLOT && stack.is(ModItems.BITUMEN.get());
        }
    };

    /** 一个只装氢气的罐（按**流体类型**判，source/flowing 两个本体都收）。 */
    private final FluidTank tank = new FluidTank(TANK_CAPACITY,
            stack -> stack != null && !stack.isEmpty()
                    && stack.getFluid().getFluidType() == ModFluids.HYDROGEN_TYPE.get()) {
        @Override
        protected void onContentsChanged() {
            setChanged();
        }
    };

    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return 1;
        }

        @Override
        public FluidStack getFluidInTank(int tankIndex) {
            return HydrodesulfurizationChamberBlockEntity.this.tank.getFluid();
        }

        @Override
        public int getTankCapacity(int tankIndex) {
            return HydrodesulfurizationChamberBlockEntity.this.tank.getCapacity();
        }

        @Override
        public boolean isFluidValid(int tankIndex, FluidStack stack) {
            return HydrodesulfurizationChamberBlockEntity.this.tank.isFluidValid(stack);
        }

        /** 灌入：只收氢气（管道/泵接上来就能用）。 */
        @Override
        public int fill(FluidStack resource, FluidAction action) {
            return HydrodesulfurizationChamberBlockEntity.this.tank.fill(resource, action);
        }

        /**
         * 抽走：按流体找罐（罐只有一个，且只装氢气）——
         * 留出这个方向是为了让玩家/自动化能把罐抽空（拆机前先抽干，见方块类的 onRemove 注释）。
         */
        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            return HydrodesulfurizationChamberBlockEntity.this.tank.drain(resource, action);
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            return HydrodesulfurizationChamberBlockEntity.this.tank.drain(maxDrain, action);
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_PROGRESS -> progress;
                case DATA_PROGRESS_MAX -> progressMax;
                case DATA_STATUS -> status;
                case DATA_TANK -> tank.getFluidAmount();
                case DATA_TANK_FLUID -> BuiltInRegistries.FLUID.getId(tank.getFluid().getFluid());
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

    public HydrodesulfurizationChamberBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.HYDRODESULFURIZATION_CHAMBER_BE.get(), pos, state);
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public FluidTank getTank() {
        return this.tank;
    }

    public IFluidHandler getFluidHandler() {
        return this.fluidHandler;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, HydrodesulfurizationChamberBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
        }
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }

        // ① 红石信号 = 关机（进度保留）
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.status = STATUS_DISABLED;
            return;
        }

        // ② 沥青槽：空了就清进度；不够一批则**只停不清**（玩家分两批凑料不该白跑）
        ItemStack input = this.items.getStackInSlot(INPUT_SLOT);
        if (input.isEmpty()) {
            resetProgress();
            this.status = STATUS_EMPTY;
            return;
        }
        if (input.getCount() < BITUMEN_PER_OPERATION) {
            this.status = STATUS_MATERIAL;
            return;
        }

        // ③ 氢气不够一批 —— 同样只停不清
        if (this.tank.getFluidAmount() < HYDROGEN_PER_OPERATION) {
            this.status = STATUS_NO_HYDROGEN;
            return;
        }

        this.progressMax = DURATION_TICKS;

        // ④ 没到点：推进度。
        //    ⚠ 前面每一 tick **只推进度、不动料**：中途拆机/断料绝不会吃掉沥青或氢气。
        if (this.progress + 1 < this.progressMax) {
            this.progress++;
            this.status = STATUS_RUNNING;
            setChanged();
            return;
        }

        // ⑤ 最后一 tick：先确认产物放得下（放不下就原地等，不扣料不产出）
        if (sulfurSpace() < SULFUR_PER_OPERATION) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }

        // ⑥ 结算：扣 16 个沥青 + 1000 mB 氢气，落 1 个硫
        ItemStack out = this.items.getStackInSlot(OUTPUT_SLOT);
        if (out.isEmpty()) {
            this.items.setStackInSlot(OUTPUT_SLOT,
                    new ItemStack(ModItems.SULFUR.get(), SULFUR_PER_OPERATION));
        } else {
            // 走到这里 out 必定是硫（spaceFor 已经判过同物品同组件）
            out.grow(SULFUR_PER_OPERATION);
            this.items.setStackInSlot(OUTPUT_SLOT, out);
        }
        this.items.extractItem(INPUT_SLOT, BITUMEN_PER_OPERATION, false);
        this.tank.drain(HYDROGEN_PER_OPERATION, IFluidHandler.FluidAction.EXECUTE);
        this.progress = 0;
        this.status = STATUS_RUNNING;
        setChanged();
    }

    private void resetProgress() {
        if (this.progress != 0 || this.progressMax != 0) {
            this.progress = 0;
            this.progressMax = 0;
            setChanged();
        }
    }

    /**
     * 输出槽还能放几个硫。
     *
     * <p>空槽 = 槽位上限；装着硫 = 剩余空间；装着别的东西 = 0（理论上进不来）。</p>
     */
    public int sulfurSpace() {
        ItemStack out = this.items.getStackInSlot(OUTPUT_SLOT);
        int limit = Math.min(new ItemStack(ModItems.SULFUR.get()).getMaxStackSize(),
                this.items.getSlotLimit(OUTPUT_SLOT));
        if (out.isEmpty()) {
            return limit;
        }
        if (!out.is(ModItems.SULFUR.get())) {
            return 0;
        }
        return Math.max(0, limit - out.getCount());
    }

    // ================= 读数（界面 / 探针共用） =================

    public int getProgress() {
        return this.progress;
    }

    public int getProgressMax() {
        return this.progressMax;
    }

    public int getStatus() {
        return this.status;
    }

    /** 罐里现在有多少 mB 氢气。 */
    public int hydrogenAmount() {
        return this.tank.getFluidAmount();
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.hydrodesulfurization_chamber");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new HydrodesulfurizationChamberMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.progress = tag.getInt("progress");
        this.progressMax = tag.getInt("progressMax");
        this.status = tag.getInt("status");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
        this.tank.readFromNBT(registries, tag.getCompound("tank"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("progress", this.progress);
        tag.putInt("progressMax", this.progressMax);
        tag.putInt("status", this.status);
        tag.put("inventory", this.items.serializeNBT(registries));
        // ⚠ 必须自己 new 一个子标签再 put 回去，别写 tag.getCompound("tank") 往里塞（§4.49）
        CompoundTag tankTag = new CompoundTag();
        this.tank.writeToNBT(registries, tankTag);
        tag.put("tank", tankTag);
    }
}
