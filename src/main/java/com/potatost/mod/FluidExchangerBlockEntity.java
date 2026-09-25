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
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 容器换流器（0.11 ZF82）。用户原话：
 *
 * <blockquote>「右键打开 GUI 左侧放装有液体的油桶/高压气罐 右边放空桶
 * （高压气罐必须接泵泵出）3s 后 消耗油罐内 1000mb 的液体 <b>把桶变成相应的流体桶</b>
 * （别的 mod 的流体也可以，<b>前提是流体有对应桶的形式</b>）流体泵也可以把液体泵出
 * 这个是<b>直接消耗油罐的流体容量</b>然后泵出 有多少泵多少（取决于泵的速率）」</blockquote>
 *
 * <p>两条互不相干的功能，都长在这台机器上：</p>
 * <ol>
 *   <li><b>GUI 换桶</b>（3 秒 / 一次）：左槽容器里 1000 mB 液体 ⇒ 右槽那个空桶变成
 *       «那种流体的官方桶»。官方桶就是 NeoForge 的 {@link Fluid#getBucket()}：
 *       原版水 → 水桶、本模组柴油 → {@code potato_s_t:diesel_bucket}、
 *       别的 mod 的流体 → 那个 mod 自己的桶。<b>没有桶形式的流体（原油 / 石脑油 / 液化石油气）
 *       会被拒绝并说明原因</b> —— 用户那句"前提是流体有对应桶的形式"就是这条判据，
 *       不需要按名字或标签去猜（NeoForge 已经把这层映射做成了 API）。</li>
 *   <li><b>泵直接抽取</b>：{@link #getFluidHandler()} 暴露的不是内部罐，而是<b>左槽容器本身</b>
 *       —— 泵抽多少、左槽那件容器就少多少（"直接消耗油罐的流体容量"）。气体也走这条路
 *       （用户："高压气罐必须接泵泵出"），所以<b>泵这条路不挑液体还是气体</b>。</li>
 * </ol>
 *
 * <p><b>⚠ 没有耗电</b>：用户没给这台机器的能耗数，所以本轮**不扣电**（也就没有能量缓冲与
 * 能量条）。要加就是给个数的事，见 `docs/开发档案.md` 的 ZF82 决策清单。</p>
 */
public class FluidExchangerBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 数值 =================
    /** 左槽：装着流体的容器（油桶 / 高压气罐）。 */
    public static final int LEFT_SLOT = 0;
    /** 右槽：一个**空**桶（原版空桶），它会被换成"那种流体的桶"。 */
    public static final int RIGHT_SLOT = 1;
    public static final int SLOT_COUNT = 2;

    /** 一次换桶的时间：3 秒（用户指定）。 */
    public static final int DURATION_TICKS = 60;
    /** 一次换桶从容器里取走多少 mB（用户指定 1000）。 */
    public static final int AMOUNT_PER_OPERATION = 1000;

    // ContainerData 索引
    public static final int DATA_PROGRESS = 0;
    public static final int DATA_PROGRESS_MAX = 1;
    public static final int DATA_STATUS = 2;
    public static final int DATA_COUNT = 3;

    // ================= 状态灯码 =================
    // ⚠ 状态码沿用全模组那一套（见 client.gui.parts.StatusLampPart）：
    //   1=空 2=无效 4=输出不可用 5=运行中 6=数量不够，只有 7/8 是本机新加的。
    /** 左槽空 / 容器里没流体：黄灯 */
    public static final int STATUS_EMPTY = 1;
    /** 左槽那件东西不是流体容器：黄灯 */
    public static final int STATUS_INVALID = 2;
    /** 右槽不是"刚好 1 个空桶"：黄灯 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在换：绿灯 */
    public static final int STATUS_RUNNING = 5;
    /** 左槽液体不到 1000 mB：黄灯（进度保留，够了一秒都不用等） */
    public static final int STATUS_MATERIAL = 6;
    /** 这种流体没有官方桶（原油 / 石脑油 / 液化石油气）：黄灯 */
    public static final int STATUS_NO_BUCKET = 7;
    /** 左槽是气体（气罐）—— 界面不做气体，请接泵抽：黄灯 */
    public static final int STATUS_GAS = 8;

    private int progress;
    private int progressMax;
    /** 服务端每 tick 刷新，仅供 GUI（不存盘） */
    private int status = STATUS_EMPTY;

    /**
     * 0 号左槽（容器）、1 号右槽（空桶）。
     *
     * <p>两道门禁与菜单里的 {@code mayPlace} **必须同口径**（§4.51 那次的教训是三道门只改了两道）。</p>
     */
    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            if (slot == LEFT_SLOT) {
                return stack.getItem() instanceof FluidContainerItem;
            }
            return stack.is(Items.BUCKET);
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_PROGRESS -> progress;
                case DATA_PROGRESS_MAX -> progressMax;
                case DATA_STATUS -> status;
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

    public FluidExchangerBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.FLUID_EXCHANGER_BE.get(), pos, state);
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    // ================= 左槽那件容器（读 / 取） =================

    /** 左槽里那件东西如果是流体容器就返回它，否则 null。 */
    private FluidContainerItem leftContainer() {
        ItemStack stack = this.items.getStackInSlot(LEFT_SLOT);
        return stack.getItem() instanceof FluidContainerItem container ? container : null;
    }

    /** 左槽容器里现在装着什么（空 / 不是容器 ⇒ {@link FluidStack#EMPTY}）。 */
    public FluidStack leftContents() {
        FluidContainerItem container = leftContainer();
        return container == null ? FluidStack.EMPTY
                : container.contents(this.items.getStackInSlot(LEFT_SLOT));
    }

    /**
     * 从<b>左槽容器</b>里直接取走最多 {@code maxAmount} mB —— 泵那条路走的就是这里。
     *
     * <p>{@code SIMULATE} 只算不取（容器内容物存在物品组件里，取了就真没了，
     * 所以模拟必须绕开真正的 {@code drain}）。</p>
     */
    public FluidStack drainFromLeftContainer(int maxAmount, IFluidHandler.FluidAction action) {
        FluidContainerItem container = leftContainer();
        if (container == null || maxAmount <= 0) {
            return FluidStack.EMPTY;
        }
        ItemStack stack = this.items.getStackInSlot(LEFT_SLOT);
        FluidStack held = container.contents(stack);
        if (held.isEmpty()) {
            return FluidStack.EMPTY;
        }
        int take = Math.min(maxAmount, held.getAmount());
        if (action.simulate()) {
            return held.copyWithAmount(take);
        }
        FluidStack drained = container.drain(stack, take);
        if (!drained.isEmpty()) {
            this.items.setStackInSlot(LEFT_SLOT, stack);
            setChanged();
        }
        return drained;
    }

    /**
     * 对外暴露的"泵接口"：<b>抽的是左槽那件容器的流体，不是机器自己的罐</b>（用户原话
     * 「直接消耗油罐的流体容量 然后泵出 有多少泵多少」）。
     *
     * <p>只出不进（{@code fill} 恒 0）：往容器里灌流体是灌装机的活，本机不做。</p>
     */
    public IFluidHandler getFluidHandler() {
        return new IFluidHandler() {
            @Override
            public int getTanks() {
                return 1;
            }

            @Override
            public FluidStack getFluidInTank(int tank) {
                return leftContents();
            }

            @Override
            public int getTankCapacity(int tank) {
                // 容器总容量 = 装着多少 + 还能装多少（油桶 3000、气罐 3500）
                FluidContainerItem container = leftContainer();
                if (container == null) {
                    return 0;
                }
                ItemStack stack = items.getStackInSlot(LEFT_SLOT);
                return container.contents(stack).getAmount() + container.space(stack);
            }

            @Override
            public boolean isFluidValid(int tank, FluidStack stack) {
                return false;   // 只抽不倒
            }

            @Override
            public int fill(FluidStack resource, FluidAction action) {
                return 0;
            }

            @Override
            public FluidStack drain(FluidStack resource, FluidAction action) {
                if (resource.isEmpty()) {
                    return FluidStack.EMPTY;
                }
                FluidStack held = leftContents();
                if (held.isEmpty() || held.getFluid() != resource.getFluid()) {
                    return FluidStack.EMPTY;
                }
                return drainFromLeftContainer(resource.getAmount(), action);
            }

            @Override
            public FluidStack drain(int maxDrain, FluidAction action) {
                return drainFromLeftContainer(maxDrain, action);
            }
        };
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, FluidExchangerBlockEntity be) {
        if (!level.isClientSide) {
            be.serverTick();
        }
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }

        // ① 左槽必须有装着东西的流体容器
        FluidContainerItem container = leftContainer();
        if (container == null) {
            resetProgress(this.items.getStackInSlot(LEFT_SLOT).isEmpty() ? STATUS_EMPTY : STATUS_INVALID);
            return;
        }
        FluidStack held = leftContents();
        if (held.isEmpty()) {
            resetProgress(STATUS_EMPTY);
            return;
        }

        // ② 气体不在这里换（用户：「高压气罐必须接泵泵出」）
        if (ModFluids.isGas(held.getFluid())) {
            resetProgress(STATUS_GAS);
            return;
        }

        // ③ 那种流体得**有官方桶**（用户：「前提是流体有对应桶的形式」）
        Item bucket = held.getFluid().getBucket();
        if (bucket == Items.AIR) {
            resetProgress(STATUS_NO_BUCKET);
            return;
        }

        // ④ 量够不够换一次：不够就等（进度保留，跟断电一个性质）
        if (held.getAmount() < AMOUNT_PER_OPERATION) {
            this.progressMax = DURATION_TICKS;
            this.status = STATUS_MATERIAL;
            setChanged();
            return;
        }

        // ⑤ 右槽必须是"刚好 1 个空桶"
        ItemStack right = this.items.getStackInSlot(RIGHT_SLOT);
        if (!right.is(Items.BUCKET) || right.getCount() != 1) {
            resetProgress(STATUS_OUTPUT_FULL);
            return;
        }

        // ⑥ 攒进度；满 3 秒**当 tick 就结算**
        //    ⚠ 第一版写成"下一 tick 才结算"，于是实际是 61 tick —— 与液压机（加满即结算）也不一致。
        //       探针第 60 tick 抓到的就是这个（进度 60 但右槽还没变）。
        this.progressMax = DURATION_TICKS;
        this.progress++;
        if (this.progress >= this.progressMax) {
            finish(container, bucket);
        }
        this.status = STATUS_RUNNING;
        setChanged();
    }

    /**
     * 结算一次换桶：从左槽容器取 1000 mB，右槽那个空桶变成"那种流体的桶"。
     *
     * <p>顺序上**先取后放**：取不到 1000 mB 就原地不动（理论上到不了这里，前面已经查过量），
     * 绝不会出现"桶变了、液体没扣"。</p>
     */
    private void finish(FluidContainerItem container, Item bucket) {
        ItemStack left = this.items.getStackInSlot(LEFT_SLOT);
        FluidStack drained = container.drain(left, AMOUNT_PER_OPERATION);
        if (drained.getAmount() < AMOUNT_PER_OPERATION) {
            // 理论上不会发生；真发生了就把取出来的还回去，宁可不动也不吞流体
            if (!drained.isEmpty()) {
                container.fill(left, drained, drained.getAmount());
            }
            this.progress = 0;
            setChanged();
            return;
        }
        this.items.setStackInSlot(LEFT_SLOT, left);
        // 空桶 → 那种流体的桶（一次一个：右槽那一个正好被替换掉）
        this.items.setStackInSlot(RIGHT_SLOT, new ItemStack(bucket));
        this.progress = 0;
        setChanged();
    }

    /** 条件不成立时清零进度并记下状态（只在真的需要落盘时 setChanged）。 */
    private void resetProgress(int newStatus) {
        boolean dirty = this.progress != 0 || this.progressMax != 0 || this.status != newStatus;
        this.progress = 0;
        this.progressMax = 0;
        this.status = newStatus;
        if (dirty) {
            setChanged();
        }
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.fluid_exchanger");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new FluidExchangerMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.progress = tag.getInt("progress");
        this.progressMax = tag.getInt("progressMax");
        this.status = tag.getInt("status");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("progress", this.progress);
        tag.putInt("progressMax", this.progressMax);
        tag.putInt("status", this.status);
        tag.put("inventory", this.items.serializeNBT(registries));
    }
}
