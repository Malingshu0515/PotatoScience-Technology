package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
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
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 饮料罐装机的方块实体（0.13 ZF167）。
 *
 * <p><b>用户原话</b>：「再加一个饮料罐装机…一个碳酸储罐（100MB）一个水储罐（1000mb）
 * 一个乙醇储罐（100mb 目前本mod没有乙醇 做个兼容别的mod的乙醇）三个输入槽 一个输出槽
 * 耗电600fe/t 先做一个配方试试水 1.10mb碳酸+500mb水+2糖+1可可豆+1空铝罐 5s产出1罐可乐」。</p>
 *
 * <h2>用户给的数（一个字没改）</h2>
 * <pre>
 *   三种罐容量：碳酸 100 mB ／ 水 1000 mB ／ 乙醇 100 mB
 *   槽位：三个输入 + 一个输出（槽 0 糖 / 槽 1 可可豆 / 槽 2 空铝罐 / 槽 3 输出）
 *   耗电：600 FE/t；一轮 5 秒 = 100 tick ⇒ 一轮 <b>60,000 FE</b>
 *   一条配方：10 mB 碳酸 + 500 mB 水 + 2 糖 + 1 可可豆 + 1 空铝罐 → 1 可乐
 * </pre>
 *
 * <h2>⚠ 三个"用户没给、我定的"数（要改都是一行）</h2>
 * <ol>
 *   <li><b>储能 {@value #MAX_ENERGY} FE</b>：正好 20 tick 的钱（600 × 20）。
 *       本工程其它机器的缓冲也都在"几 tick 到一两个"之间（酸性反应室 12400 / 500 = 24.8 tick、
 *       合金炉 32768 / 14500 = 2.26 秒）⇒ 取 20 tick 与它们同量级。缓冲小于一轮是**故意的**：
 *       这台机器必须持续供电，一轮跑不完就停在原地等电（进度保留）。</li>
 *   <li><b>"缺流体"是独立状态 {@link #STATUS_NO_FLUID}</b>：本工程的微型粉碎机那五个状态里
 *       没有"缺流体"这一格（它没有罐）。这里补一格，界面上的状态灯才说得清"到底缺什么"
 *       —— 缺料 / 缺电 / 缺流体 / 输出满，四件事不该共用一个灯。</li>
 *   <li><b>流体在"完成那一刻"整批扣</b>（不是每 tick 扣一点）：10 mB ÷ 100 tick = 0.1 mB/tick
 *       除不尽，整数运算会一路丢余数。每 tick 只查够不够，见 {@link #serverTickBody()}。</li>
 * </ol>
 *
 * <h2>乙醇那只罐：兼容别的 mod</h2>
 * <p>用户明说「目前本mod没有乙醇 做个兼容别的mod的乙醇」⇒ 这只罐收的是
 * <b>{@code c:ethanol} 流体标签</b>，不是某个具体流体 id。这个标签名不是我猜的：
 * 盘上那份沉浸工程 jar 里就是 {@code data/c/tags/fluid/ethanol.json} 指着
 * {@code immersiveengineering:ethanol}（见 {@code _zf167_recon_ethanol.py} 的输出）
 * —— 也就是说装了 IE 的整合包里，本机的乙醇罐**直接就能收 IE 的乙醇**。
 * 本 mod 自己没有乙醇，所以 <b>这一条配方不用它</b>（用户说"先做一个配方试试水"）。</p>
 *
 * <h2>流体只进不出</h2>
 * <p>三只罐都是<b>输入罐</b>（本工程同一条口径：输入罐只进不出、输出罐只出不进）⇒
 * {@link #getFluidHandler()} 的 {@code drain} 永远返回空。想清罐请用管道/换流器，
 * 或者把机器拆了（拆了罐里的流体会留在方块里消失 —— 与本工程其它机器一致）。</p>
 */
public class BeverageCanningMachineBlockEntity extends net.minecraft.world.level.block.entity.BlockEntity
        implements MenuProvider {

    // ================= 罐 =================

    public static final int TANK_CARBONIC = 0;
    public static final int TANK_WATER = 1;
    public static final int TANK_ETHANOL = 2;
    public static final int TANK_COUNT = 3;

    /** 碳酸罐 100 mB（用户给的）。 */
    public static final int TANK_CAPACITY_CARBONIC = 100;
    /** 水罐 1000 mB（用户给的）。 */
    public static final int TANK_CAPACITY_WATER = 1000;
    /** 乙醇罐 100 mB（用户给的）。 */
    public static final int TANK_CAPACITY_ETHANOL = 100;

    /**
     * 别的 mod 的乙醇挂的那张标签（本机乙醇罐只收它）。
     *
     * <p>⚠ 名字是**从盘上的沉浸工程 jar 里抠出来的**，不是记忆：
     * {@code data/c/tags/fluid/ethanol.json} → {@code ["immersiveengineering:ethanol"]}。</p>
     */
    public static final TagKey<Fluid> ETHANOL_TAG =
            FluidTags.create(ResourceLocation.fromNamespaceAndPath("c", "ethanol"));

    /** 手倒：手里拿着流体容器右键机器，一次最多倒进罐里多少 mB（与灌装机/蒸馏塔操作器同一个口径）。 */
    public static final int POUR_PER_CLICK = 1000;

    // ================= 槽 =================

    public static final int SLOT_SUGAR = 0;
    public static final int SLOT_COCOA = 1;
    public static final int SLOT_CAN = 2;
    public static final int SLOT_OUTPUT = 3;
    public static final int SLOT_COUNT = 4;

    // ================= 能量 =================

    /** 储能：20 tick 的钱（见类注释）。 */
    public static final int MAX_ENERGY = 600 * 20;

    // ================= 界面数据槽 =================

    public static final int DATA_ENERGY = 0;
    public static final int DATA_PROGRESS = 1;
    public static final int DATA_PROGRESS_MAX = 2;
    public static final int DATA_STATUS = 3;
    public static final int DATA_TANK_0 = 4;
    public static final int DATA_TANK_FLUID_0 = DATA_TANK_0 + TANK_COUNT;
    public static final int DATA_COUNT = DATA_TANK_FLUID_0 + TANK_COUNT;

    public static final int STATUS_DISABLED = 0;
    public static final int STATUS_EMPTY = 1;
    public static final int STATUS_INVALID = 2;
    public static final int STATUS_NO_POWER = 3;
    public static final int STATUS_OUTPUT_FULL = 4;
    public static final int STATUS_RUNNING = 5;
    /**
     * 本机独有：料齐了、但某只罐里的流体不够。
     *
     * <p>⚠ <b>20 是"捡的号"</b>：6 已经被液压机占了（{@code STATUS_MATERIAL}「材料数量不够」），
     * 7/8 是容器换流器、9~19 也各有其主（见 {@code StatusLampPart} 的注释）。
     * "材料不够"与"流体不够"语义对不上，所以按那条规矩**另起一个号**，
     * 并在 {@code StatusLampPart} 的 {@code colorOf}/{@code suffixOf} 里各挂一行
     * （界面上的灯与悬停文案都靠那两处）。</p>
     */
    public static final int STATUS_NO_FLUID = 20;

    private int energy = 0;
    private int progress = 0;
    private int progressMax = 0;
    /** 三个输入槽的"物品签名"；换了料就把进度清零（与微型粉碎机的 progressItem 同一条口径）。 */
    private String progressKey = "";
    private int status = STATUS_EMPTY;

    private final FluidTank[] tanks = new FluidTank[TANK_COUNT];

    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return switch (slot) {
                case SLOT_SUGAR -> stack.is(net.minecraft.world.item.Items.SUGAR);
                case SLOT_COCOA -> stack.is(net.minecraft.world.item.Items.COCOA_BEANS);
                case SLOT_CAN -> stack.is(ModItems.EMPTY_ALUMINUM_CAN.get());
                default -> false;   // 输出槽：自动化不许往里塞（本工程同一条口径）
            };
        }

        @Override
        public int getSlotLimit(int slot) {
            return 64;
        }
    };

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
            if (index == DATA_ENERGY) {
                return energy;
            }
            if (index == DATA_PROGRESS) {
                return progress;
            }
            if (index == DATA_PROGRESS_MAX) {
                return progressMax;
            }
            if (index == DATA_STATUS) {
                return status;
            }
            if (index >= DATA_TANK_0 && index < DATA_TANK_FLUID_0) {
                return tanks[index - DATA_TANK_0].getFluidAmount();
            }
            if (index >= DATA_TANK_FLUID_0 && index < DATA_COUNT) {
                Fluid f = tanks[index - DATA_TANK_FLUID_0].getFluid().getFluid();
                return f == null ? 0 : BuiltInRegistries.FLUID.getId(f);
            }
            return 0;
        }

        @Override
        public void set(int index, int value) {
            if (index == DATA_ENERGY) {
                energy = value;
            } else if (index == DATA_PROGRESS) {
                progress = value;
            } else if (index == DATA_PROGRESS_MAX) {
                progressMax = value;
            } else if (index == DATA_STATUS) {
                status = value;
            }
            // 罐的液面在客户端只读（服务端每 tick 推的是真值），不回写
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public BeverageCanningMachineBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.BEVERAGE_CANNING_MACHINE_BE.get(), pos, state);
        this.tanks[TANK_CARBONIC] =
                new FluidTank(TANK_CAPACITY_CARBONIC, s -> type(s) == ModFluids.CARBONIC_ACID_TYPE.get());
        this.tanks[TANK_WATER] =
                new FluidTank(TANK_CAPACITY_WATER, s -> type(s) == net.neoforged.neoforge.common.NeoForgeMod.WATER_TYPE.value());
        this.tanks[TANK_ETHANOL] =
                new FluidTank(TANK_CAPACITY_ETHANOL, s -> s != null && !s.isEmpty() && s.getFluid().is(ETHANOL_TAG));
    }

    /** 流体类型助手（与酸性反应室那份同一行写法）。 */
    private static net.neoforged.neoforge.fluids.FluidType type(FluidStack stack) {
        return stack == null || stack.isEmpty() ? null : stack.getFluid().getFluidType();
    }

    /** 某只罐的容量。 */
    public static int capacityOf(int tank) {
        return switch (tank) {
            case TANK_CARBONIC -> TANK_CAPACITY_CARBONIC;
            case TANK_WATER -> TANK_CAPACITY_WATER;
            default -> TANK_CAPACITY_ETHANOL;
        };
    }

    // ================= 对外句柄 =================

    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public FluidTank getTank(int index) {
        return this.tanks[index];
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    public int getStatus() {
        return this.status;
    }

    public int getProgress() {
        return this.progress;
    }

    public int getProgressMax() {
        return this.progressMax;
    }

    /**
     * 三只罐合起来的对外句柄：**只进不出**（输入罐口径，见类注释）。
     *
     * <p>构造期建一次、之后一直复用 —— 与灌装机 2026-09-26 那次修正同一条口径
     * （每次查能力都新建匿名对象会让管道每问一次就多一个对象）。</p>
     */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return TANK_COUNT;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return tanks[tank].getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return tanks[tank].getCapacity();
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return tanks[tank].isFluidValid(stack);
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return 0;
            }
            if (action.simulate()) {
                int total = 0;
                for (FluidTank tank : tanks) {
                    total += tank.fill(resource, FluidAction.SIMULATE);
                }
                return total;
            }
            FluidStack remaining = resource.copy();
            int filled = 0;
            for (FluidTank tank : tanks) {
                if (remaining.isEmpty()) {
                    break;
                }
                int moved = tank.fill(remaining, FluidAction.EXECUTE);
                if (moved > 0) {
                    filled += moved;
                    remaining.shrink(moved);
                }
            }
            if (filled > 0) {
                setChanged();
            }
            return filled;
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

    public IFluidHandler getFluidHandler() {
        return this.fluidHandler;
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, BeverageCanningMachineBlockEntity machine) {
        if (level.isClientSide) {
            return;   // 这台机器本轮没有循环音效，客户端不需要做事
        }
        machine.serverTickBody();
    }

    private void serverTickBody() {
        if (this.level == null) {
            return;
        }

        // ① 红石信号 = 关机（进度保留）
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.status = STATUS_DISABLED;
            return;
        }

        // ② 三个输入槽决定配方
        ItemStack sugar = this.items.getStackInSlot(SLOT_SUGAR);
        ItemStack cocoa = this.items.getStackInSlot(SLOT_COCOA);
        ItemStack canStack = this.items.getStackInSlot(SLOT_CAN);
        if (sugar.isEmpty() && cocoa.isEmpty() && canStack.isEmpty()) {
            resetProgress();
            this.status = STATUS_EMPTY;
            return;
        }
        CanningMachineRecipes.Can can = CanningMachineRecipes.find(sugar, cocoa, canStack);
        if (can == null) {
            resetProgress();
            this.status = STATUS_INVALID;
            return;
        }

        // ③ 换了料 → 进度清零
        String key = keyOf(sugar, cocoa, canStack);
        if (!key.equals(this.progressKey)) {
            this.progress = 0;
            this.progressKey = key;
        }
        this.progressMax = can.durationTicks();

        // ④ 已到点：只等输出腾位置（不扣电、不扣料）
        if (this.progress >= this.progressMax) {
            this.status = finish(can) ? STATUS_RUNNING : STATUS_OUTPUT_FULL;
            setChanged();
            return;
        }

        // ⑤ 未到点：先看电、再看流体、再看输出余量
        if (this.energy < can.energyPerTick()) {
            this.status = STATUS_NO_POWER;
            return;
        }
        if (!hasFluids(can)) {
            this.status = STATUS_NO_FLUID;
            return;
        }
        if (!canInsert(can.createOutput())) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }

        this.energy -= can.energyPerTick();
        this.progress++;
        this.status = STATUS_RUNNING;
        if (this.progress >= this.progressMax && !finish(can)) {
            this.status = STATUS_OUTPUT_FULL;
        }
        setChanged();
    }

    /** 三个输入槽的物品签名（只认物品 id，不认数量 —— 数量抖动不该把进度打回零）。 */
    private static String keyOf(ItemStack sugar, ItemStack cocoa, ItemStack can) {
        return idOf(sugar) + "|" + idOf(cocoa) + "|" + idOf(can);
    }

    private static String idOf(ItemStack stack) {
        return stack.isEmpty() ? "-" : BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
    }

    /** 三只罐里的流体够不够这一条配方。 */
    public boolean hasFluids(CanningMachineRecipes.Can can) {
        return this.tanks[TANK_CARBONIC].getFluidAmount() >= can.carbonicMb()
                && this.tanks[TANK_WATER].getFluidAmount() >= can.waterMb()
                && this.tanks[TANK_ETHANOL].getFluidAmount() >= can.ethanolMb();
    }

    /** 输入槽没了/配方不成立时把进度归零（只在真需要时落盘）。 */
    private void resetProgress() {
        if (this.progress != 0 || this.progressMax != 0) {
            this.progress = 0;
            this.progressMax = 0;
            setChanged();
        }
        this.progressKey = "";
    }

    /**
     * 结算一轮：放得下才扣料扣流体。
     *
     * @return true = 成功产出并扣掉了三种流体与三样物品；false = 输出槽放不下，进度停在满格等位置
     */
    private boolean finish(CanningMachineRecipes.Can can) {
        if (this.level == null) {
            return false;
        }
        if (!canInsert(can.createOutput())) {
            return false;
        }
        // ① 扣流体（整批扣；每 tick 的检查保证这里一定够）
        this.tanks[TANK_CARBONIC].drain(can.carbonicMb(), IFluidHandler.FluidAction.EXECUTE);
        this.tanks[TANK_WATER].drain(can.waterMb(), IFluidHandler.FluidAction.EXECUTE);
        this.tanks[TANK_ETHANOL].drain(can.ethanolMb(), IFluidHandler.FluidAction.EXECUTE);
        // ② 扣物品
        this.items.extractItem(SLOT_SUGAR, can.sugar(), false);
        this.items.extractItem(SLOT_COCOA, can.cocoa(), false);
        this.items.extractItem(SLOT_CAN, can.cans(), false);
        // ③ 放产物（直写，不查 isItemValid —— 输出槽的那道门是给自动化看的，§4.13 同族坑）
        ItemStack existing = this.items.getStackInSlot(SLOT_OUTPUT);
        if (existing.isEmpty()) {
            this.items.setStackInSlot(SLOT_OUTPUT, can.createOutput());
        } else {
            this.items.setStackInSlot(SLOT_OUTPUT,
                    existing.copyWithCount(existing.getCount() + can.resultCount()));
        }
        this.progress = 0;
        this.progressKey = "";
        return true;
    }

    /** 输出槽能不能装下这一栈（空槽或同种物品且有位置）。 */
    public boolean canInsert(ItemStack stack) {
        ItemStack existing = this.items.getStackInSlot(SLOT_OUTPUT);
        if (existing.isEmpty()) {
            return true;
        }
        if (!ItemStack.isSameItemSameComponents(existing, stack)) {
            return false;
        }
        return existing.getCount() + stack.getCount() <= Math.min(existing.getMaxStackSize(),
                this.items.getSlotLimit(SLOT_OUTPUT));
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.beverage_canning_machine");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new BeverageCanningMachineMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.progress = tag.getInt("progress");
        this.progressMax = tag.getInt("progressMax");
        this.progressKey = tag.getString("progressKey");
        this.status = tag.getInt("status");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
        for (int i = 0; i < TANK_COUNT; i++) {
            this.tanks[i].readFromNBT(registries, tag.getCompound("tank" + i));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("progress", this.progress);
        tag.putInt("progressMax", this.progressMax);
        tag.putString("progressKey", this.progressKey);
        tag.putInt("status", this.status);
        tag.put("inventory", this.items.serializeNBT(registries));
        for (int i = 0; i < TANK_COUNT; i++) {
            tag.put("tank" + i, this.tanks[i].writeToNBT(registries, new CompoundTag()));
        }
    }

    /** 探针/校验用：三只罐的液面快照（不参与玩法）。 */
    public List<Integer> tankAmounts() {
        return List.of(this.tanks[TANK_CARBONIC].getFluidAmount(),
                this.tanks[TANK_WATER].getFluidAmount(),
                this.tanks[TANK_ETHANOL].getFluidAmount());
    }
}
