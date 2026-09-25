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
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 锂电池构造间的方块实体（0.11 ZF112）。
 *
 * <pre>
 * 用户原话：「加一个锂电池构造间 通入硫酸 放入粗锰/粗铝and 镍/粗镍 and 碳酸锂 and钴/粗钴
 *           每t消耗10mb硫酸 30s后产出一个锂电池原件 不消耗电」
 * </pre>
 *
 * <table>
 *   <caption>四个输入槽（每个槽认"或"：粗料或锭）</caption>
 *   <tr><td>槽 0</td><td>粗锰 / 粗铝</td></tr>
 *   <tr><td>槽 1</td><td>镍锭 / 粗镍</td></tr>
 *   <tr><td>槽 2</td><td>碳酸锂</td></tr>
 *   <tr><td>槽 3</td><td>钴锭 / 粗钴</td></tr>
 * </table>
 *
 * <p><b>① 不吃电</b>（用户原话末四个字「不消耗电」⇒ 这台机器<b>没有</b>能量能力，
 * 与加氢脱硫反应仓同一条路：靠化学，不靠电费）。</p>
 *
 * <p><b>② 酸按 tick 扣、料最后扣</b>：硫酸 <b>每 tick 10 mB</b>（用户指定），
 * 一炉 30 秒 ⇒ 一件共 <b>6000 mB</b> 硫酸；四样原料在<b>最后一 tick</b> 才各扣 1 个
 * （与酸性反应室那条"材料最后才扣"一致）—— 中途拔料/断酸只会让进度停住或归零，不会白吃料。</p>
 *
 * <p><b>③ 硫酸罐容量 2000 mB 是我定的</b>（用户没给）：够缓冲 200 tick 的连续消耗，
 * 断供时状态 17 黄灯、进度<b>原地不动</b>（不清零 —— 停电/断料的语义与别的机器一致）。
 * 要改是一个常量。罐子<b>只进不出</b>（管道 / 泵能灌进来，抽不出去）—— 与酸性反应室那四个原料罐一致。</p>
 *
 * <p><b>④ 门禁只有一处</b>：{@link #acceptsInput}（菜单里的 {@code SlotItemHandler} 默认就问
 * handler 的 {@code isItemValid}）⇒ 不会出现"界面放得进、机器不认"那种两处不一致（§4.51）。</p>
 */
public class LithiumBatteryPlantBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数 =================

    /** 一炉 30 秒（用户原话「30s后」）。 */
    public static final int DURATION_TICKS = 30 * 20;
    /** 硫酸消耗。用户原话「每t消耗10mb硫酸」；**0.11 ZF115 用户又要求砍到原来的十分之一** ⇒ 1 mB/t。 */
    public static final int ACID_PER_TICK = 1;
    /** 一炉一共要多少硫酸 = 1 × 600 = **600 mB**（据此算出，不是用户另给的数）。 */
    public static final int ACID_PER_OPERATION = ACID_PER_TICK * DURATION_TICKS;
    /** 一炉出一个（用户原话「30s后产出一个锂电池原件」）。 */
    public static final int OUTPUT_COUNT = 1;

    // ================= 我定的数（用户没给；要改都是一行） =================

    /**
     * 硫酸罐容量。用户没给 ⇒ 取 <b>8000 mB</b>。
     *
     * <p>⚠ 第一版我取的是 2000，<b>探针当场把这条打回来了</b>：一炉要 6000 mB（10 mB/t × 600 t），
     * 罐子装不下一炉 ⇒ 玩家必须先架好持续供酸的管道才敢开机，装满一罐连半炉都跑不完。
     * 8000 = 一炉 6000 再留 2000 的余量，<b>装满一罐就能空手走开</b>。</p>
    /**
     * 硫酸罐容量。用户没给 ⇒ <b>800 mB</b>（0.11 ZF115：与每 tick 消耗一起砍到原来的十分之一）。
     *
     * <p>⚠ 这条数改过两次，但**性质一直是同一条**：一炉 = {@link #ACID_PER_TICK} ×
     * {@link #DURATION_TICKS}，罐子要**装得下一炉** —— 现在是 1 × 600 = 600 mB，800 的罐
     * 装满就够跑完一炉（还剩 200）。第一版我取 2000 时正因为装不下一炉（当时一炉 6000）
     * 被探针打回来过。</p>
     */
    public static final int TANK_CAPACITY = 800;

    // ================= 槽位 =================

    public static final int INPUT_FIRST = 0;
    /** 四个输入槽：粗锰/粗铝、镍/粗镍、碳酸锂、钴/粗钴。 */
    public static final int INPUT_COUNT = 4;
    public static final int OUTPUT_SLOT = INPUT_FIRST + INPUT_COUNT;
    public static final int SLOT_COUNT = OUTPUT_SLOT + 1;      // = 5

    // ================= 状态灯（沿用共享码，新起 17、18） =================

    /** 有红石信号 = 停机 */
    public static final int STATUS_DISABLED = 0;
    /** 空（默认档） */
    public static final int STATUS_EMPTY = 1;
    /** 输出槽放不下 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在构造 */
    public static final int STATUS_RUNNING = 5;
    /** 17 = 硫酸不够（0.11 ZF112 新起） */
    public static final int STATUS_NO_ACID = 17;
    /** 18 = 四样原料不齐（0.11 ZF112 新起） */
    public static final int STATUS_INPUTS = 18;

    // ================= 容器同步 =================

    public static final int DATA_PROGRESS = 0;
    public static final int DATA_PROGRESS_MAX = 1;
    public static final int DATA_STATUS = 2;
    /** 罐容量（恒定，界面用） */
    public static final int DATA_TANK = 3;
    /** 罐里现有多少 mB（≤2000 ⇒ 不用分片，§4.48） */
    public static final int DATA_TANK_FLUID = 4;
    public static final int DATA_COUNT = 5;

    private int progress;
    private int status = STATUS_EMPTY;

    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            if (slot >= INPUT_FIRST && slot < INPUT_FIRST + INPUT_COUNT) {
                return acceptsInput(slot, stack);
            }
            return false;                       // 输出槽不收
        }

        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }
    };

    private final FluidTank tank = new FluidTank(TANK_CAPACITY,
            stack -> stack != null && !stack.isEmpty()
                    && stack.getFluid().getFluidType() == ModFluids.SULFURIC_ACID_TYPE.get());

    /** 六面流体口：**只进不出**（灌硫酸用；抽不走 —— 与酸性反应室那四个原料罐同一条规矩）。 */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return 1;
        }

        @Override
        public FluidStack getFluidInTank(int index) {
            return LithiumBatteryPlantBlockEntity.this.tank.getFluid();
        }

        @Override
        public int getTankCapacity(int index) {
            return TANK_CAPACITY;
        }

        @Override
        public boolean isFluidValid(int index, FluidStack stack) {
            return LithiumBatteryPlantBlockEntity.this.tank.isFluidValid(stack);
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            return LithiumBatteryPlantBlockEntity.this.tank.fill(resource, action);
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
                case DATA_PROGRESS -> progress;
                case DATA_PROGRESS_MAX -> DURATION_TICKS;
                case DATA_STATUS -> status;
                case DATA_TANK -> TANK_CAPACITY;
                case DATA_TANK_FLUID -> tank.getFluidAmount();
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

    public LithiumBatteryPlantBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.LITHIUM_BATTERY_PLANT_BE.get(), pos, state);
    }

    /**
     * 第 {@code slot} 个输入槽认不认这件东西（用户给的"或"关系）。
     *
     * <p>⚠ 写成**运行时**方法而不是 static 字段表：类初始化期取 {@code ModItems.X.get()}
     * 会踩 §4.1 那个"注册表还没填就取值"的启动崩溃。</p>
     */
    public static boolean acceptsInput(int slot, ItemStack stack) {
        if (stack.isEmpty()) {
            return false;
        }
        return switch (slot) {
            case 0 -> stack.is(PotatoSTOres.RAW_MANGANESE.get())
                    || stack.is(PotatoSTOres.RAW_ALUMINUM.get());
            case 1 -> stack.is(ModItems.NICKEL_INGOT.get())
                    || stack.is(PotatoSTOres.RAW_NICKEL.get());
            case 2 -> stack.is(ModItems.LITHIUM_CARBONATE.get());
            case 3 -> stack.is(ModItems.COBALT_INGOT.get())
                    || stack.is(PotatoSTOres.RAW_COBALT.get());
            default -> false;
        };
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, LithiumBatteryPlantBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
        }
    }

    void serverTick() {
        if (this.level == null) {
            return;
        }
        // ① 红石信号 = 停机（进度保留）
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.status = STATUS_DISABLED;
            return;
        }
        // ② 输出槽放不下 ⇒ 原地等（不扣酸、不扣料）
        if (!canOutput()) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }
        // ③ 四样原料齐不齐
        if (!hasAllInputs()) {
            this.status = STATUS_INPUTS;
            return;
        }
        // ④ 酸够不够这一 tick
        if (this.tank.getFluidAmount() < ACID_PER_TICK) {
            this.status = STATUS_NO_ACID;
            return;                                  // 断酸：进度原地不动（不清零）
        }
        // ⑤ 真干活：扣酸、推进度
        this.tank.drain(ACID_PER_TICK, IFluidHandler.FluidAction.EXECUTE);
        this.progress++;
        this.status = STATUS_RUNNING;
        // ⑥ 到点结算：四样原料各扣 1、出 1 个锂电池原件
        if (this.progress >= DURATION_TICKS) {
            consumeInputs();
            addOutput();
            this.progress = 0;
        }
        setChanged();
    }

    /**
     * 出产物。
     *
     * <p>⚠ <b>不能用 {@code ItemStackHandler#insertItem}</b>：那个方法**会走 {@code isItemValid}**，
     * 而输出槽按设计是"只取不放"（{@code isItemValid} 恒 false）⇒ 产物会被原样退回来
     * —— 表现就是"料扣了、东西没出来"。这里直接写槽位（能不能放由 {@link #canOutput} 先保证）。
     * 这条是 ZF112 探针当场抓出来的。</p>
     */
    private void addOutput() {
        ItemStack out = this.items.getStackInSlot(OUTPUT_SLOT);
        if (out.isEmpty()) {
            this.items.setStackInSlot(OUTPUT_SLOT,
                    new ItemStack(ModItems.LITHIUM_BATTERY_COMPONENT.get(), OUTPUT_COUNT));
            return;
        }
        out.grow(OUTPUT_COUNT);
        this.items.setStackInSlot(OUTPUT_SLOT, out);
    }

    /** 四样原料各至少 1 个。 */
    private boolean hasAllInputs() {
        for (int slot = INPUT_FIRST; slot < INPUT_FIRST + INPUT_COUNT; slot++) {
            if (this.items.getStackInSlot(slot).isEmpty()) {
                return false;
            }
        }
        return true;
    }

    /** 输出槽放得下这一件吗（空槽，或同样的东西没堆满）。 */
    private boolean canOutput() {
        ItemStack out = this.items.getStackInSlot(OUTPUT_SLOT);
        if (out.isEmpty()) {
            return true;
        }
        return out.is(ModItems.LITHIUM_BATTERY_COMPONENT.get())
                && out.getCount() + OUTPUT_COUNT <= out.getMaxStackSize();
    }

    /** 四样原料各扣 1 个。 */
    private void consumeInputs() {
        for (int slot = INPUT_FIRST; slot < INPUT_FIRST + INPUT_COUNT; slot++) {
            ItemStack stack = this.items.getStackInSlot(slot);
            stack.shrink(1);
            this.items.setStackInSlot(slot, stack.isEmpty() ? ItemStack.EMPTY : stack);
        }
    }

    // ================= 读数（界面 / 探针共用） =================

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

    public int getProgress() {
        return this.progress;
    }

    public int getStatus() {
        return this.status;
    }

    /** 探针用：这一炉一共要多少硫酸。 */
    public static int acidPerOperation() {
        return ACID_PER_OPERATION;
    }

    /** 探针用：某样东西能不能进这个槽。 */
    public static boolean probeAccepts(int slot, Item item) {
        return acceptsInput(slot, new ItemStack(item));
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.lithium_battery_plant");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new LithiumBatteryPlantMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.progress = tag.getInt("progress");
        this.status = tag.contains("status") ? tag.getInt("status") : STATUS_EMPTY;
        this.items.deserializeNBT(registries, tag.getCompound("Items"));
        this.tank.readFromNBT(registries, tag.getCompound("Tank"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("progress", this.progress);
        tag.putInt("status", this.status);
        tag.put("Items", this.items.serializeNBT(registries));
        // ⚠ 必须自己 new 一个子标签再 put 回去（§4.49）
        CompoundTag child = new CompoundTag();
        this.tank.writeToNBT(registries, child);
        tag.put("Tank", child);
    }
}
