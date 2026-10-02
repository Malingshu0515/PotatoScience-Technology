package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.IFluidHandlerItem;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

import com.potatost.mod.sound.ModSounds;

/**
 * Filling machine (0.03).
 *
 *   - five independent fluid tanks, 5000 mB each
 *   - one container slot per tank, directly below it
 *   - fills a gas tank at FILL_RATE mB per tick, costing ENERGY_PER_TANK FE per
 *     tick per tank that is actually filling
 *   - internal buffer MAX_ENERGY FE, accepts energy from any side, never outputs
 *
 * Locked numbers (agreed with the project owner):
 *   ENERGY_PER_TANK = 60 FE/t per tank (five tanks running = 300 FE/t)
 *   MAX_ENERGY      = 3000 FE
 *   FILL_RATE       = 5 mB/t per tank
 */
public class FillingMachineBlockEntity extends BlockEntity implements MenuProvider {

    public static final int TANK_COUNT = 5;
    public static final int TANK_CAPACITY = 5000;
    public static final int FILL_RATE = 5;
    public static final int ENERGY_PER_TANK = 60;
    public static final int MAX_ENERGY = 3000;

    /**
     * 手倒：手里拿着流体容器右键机器，一次最多倒进罐里多少 mB
     * （0.11 ZF80；与蒸馏塔操作器的 {@code POUR_PER_CLICK} 同一个口径）。
     */
    public static final int POUR_PER_CLICK = 1000;

    /** Container slot i belongs to fluid tank i. */
    public static final int SLOT_COUNT = TANK_COUNT;
    public static final int SLOT_0 = 0;

    // ContainerData layout. The five tank amounts live at DATA_TANK_0 .. DATA_TANK_0+4,
    // so slot i maps to data index (DATA_TANK_0 + i).
    public static final int DATA_ENERGY = 0;
    public static final int DATA_TANK_0 = 1;
    /** WHICH fluid each tank holds（**流体注册表 id**，不再是 ModFluids 的 1..3 紧凑编号）。 */
    public static final int DATA_TANK_FLUID_0 = DATA_TANK_0 + TANK_COUNT;
    public static final int DATA_COUNT = DATA_TANK_FLUID_0 + TANK_COUNT;

    /** NBT key prefix for the five tanks. */
    private static final String TANK_KEY_PREFIX = "tank";

    private int energy = 0;

    /**
     * 上一 tick 各个槽位是否真的灌进去了（0.10 完成音效用）。
     * 不存盘：区块卸载/读档后从 false 重新开始，代价只是那次不出声。
     */
    private final boolean[] wasFilling = new boolean[TANK_COUNT];

    private final FluidTank[] tanks = new FluidTank[TANK_COUNT];

    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            // 0.13 ZF162：**什么都能放**（用户：「所有物品都可以放进去 只不过检测到能被罐装的才可以罐装」）。
            //   三道门（方块实体 / 菜单手放 / Shift 快移）从此都不把关"能不能灌"，
            //   那一刀改由灌装那一步判（tryFillSlot + stateOf）—— 否则像 Mek 的喷气背包这种
            //   "机器目前灌不了"的东西**连放都放不进去**，玩家只看到"没反应"，
            //   分不清是"放不进去"还是"灌不进"（这正是用户报的现象）。
            return true;
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
            if (index == DATA_ENERGY) {
                return energy;
            }
            int tankIndex = index - DATA_TANK_0;
            if (tankIndex >= 0 && tankIndex < TANK_COUNT) {
                return tanks[tankIndex].getFluidAmount();
            }
            int fluidIndex = index - DATA_TANK_FLUID_0;
            if (fluidIndex >= 0 && fluidIndex < TANK_COUNT) {
                // 0.11 ZF73：改传**流体注册表 id**（原来传 ModFluids 的 1..3 紧凑编号，
                // 只认那 3 种气体 ⇒ 罐里装了原油时界面会显示成「空」）。
                // 注册表 id 里 0 恰好是 minecraft:empty，语义自洽。
                return BuiltInRegistries.FLUID.getId(tanks[fluidIndex].getFluid().getFluid());
            }
            return 0;
        }

        @Override
        public void set(int index, int value) {
            // The server reads its own fields; the client mirrors via SimpleContainerData.
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public FillingMachineBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.FILLING_MACHINE_BE.get(), pos, state);
        for (int i = 0; i < TANK_COUNT; i++) {
            this.tanks[i] = new FluidTank(TANK_CAPACITY, FillingMachineBlockEntity::acceptsAnyFluid);
        }
    }

    /**
     * 水箱收什么流体：**什么都收**（空的不算）。
     *
     * <p>0.11 ZF73 按用户拍板改的（v0.11 规划 §5 待决 4）：原先只收气体，那样
     * **油桶在机器里根本灌不到油**（油进不了机器的罐子）。改成"机器不把关、
     * 由容器说了算"之后：高压气罐只收气体、油桶只收液体、还拒绝混装
     * —— 三条规则分别落在 {@link TankContents#isGas} 与 {@link OilBucketContents} 里。</p>
     */
    public static boolean acceptsAnyFluid(FluidStack stack) {
        return stack != null && !stack.isEmpty();
    }

    /**
     * 是不是"气体"（供界面/调试用的公开判定）。
     *
     * <p>⚠ 0.11 ZF73：原实现是负向的「非水非岩浆 ⇒ 气体」，一加原油就会把原油当气体
     * （档案 §4.44）。现在委托 {@link ModFluids#isGas}，**正向列举**那 3 种气体。</p>
     */
    public static boolean isGasFluid(Fluid fluid) {
        return ModFluids.isGas(fluid);
    }

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

    /**
     * 五个罐合起来的那一个对外句柄（2026-09-26 起**构造期建一次、之后一直复用**）。
     *
     * <p>原先 {@link #getFluidHandler()} 是 {@code return new IFluidHandler(){…}} —— 而 NeoForge
     * 每次查能力都会重跑方块实体那条 provider lambda ⇒ 管道/泵每问一次就多一个匿名对象。
     * 本工程另外四十多处同类句柄都是构造期缓存（如 {@code DistillationOperatorBlockEntity}），
     * 这里跟上同一条口径。<b>行为完全不变</b>：句柄内部读的仍然是 {@link #tanks} 的实时内容。</p>
     */
    private final IFluidHandler fluidHandler = createFluidHandler();

    /** The five tanks exposed as one handler, so pipes and pumps can feed the machine. */
    public IFluidHandler getFluidHandler() {
        return this.fluidHandler;
    }

    private IFluidHandler createFluidHandler() {
        return new IFluidHandler() {
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
    }

    // ================= tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, FillingMachineBlockEntity machine) {
        if (level.isClientSide) {
            return;
        }
        machine.serverTick();
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }
        boolean dirty = false;
        boolean sessionEnded = false;
        for (int i = 0; i < TANK_COUNT; i++) {
            boolean filling = tryFillSlot(i);
            // 「这一段灌装结束了」= 上一 tick 在灌、这一 tick 不灌了，且停下来的原因属于
            // 罐满 / 流体耗尽 / 容器被拿走这三种（见 isDoneFilling）。
            // 「没电」不算结束——那只是暂停，不该响。
            if (this.wasFilling[i] && !filling && isDoneFilling(i)) {
                sessionEnded = true;
            }
            this.wasFilling[i] = filling;
            if (filling) {
                dirty = true;
            }
        }
        if (sessionEnded) {
            // 同一 tick 里多罐一起结束也只响一次，免得五个声音叠成一坨
            playCompleteSound();
        }
        if (dirty) {
            setChanged();
        }
    }

    /**
     * 这一槽的灌装是不是"做完了"（而不是"暂时没电 / 暂时动不了"）。
     *
     * <p>三种情形正是要出声的三种：<b>罐满</b>、<b>流体耗尽</b>、<b>容器被拿走或换成别的</b>
     * ——0.13 ZF162 起"换成别的"还包括"换成了一件根本灌不了的东西"（{@link #spaceFor} 回 −1）。</p>
     */
    private boolean isDoneFilling(int index) {
        if (this.tanks[index].isEmpty()) {
            return true;
        }
        ItemStack inSlot = this.items.getStackInSlot(index);
        if (inSlot.isEmpty()) {
            return true;
        }
        return spaceFor(inSlot, this.tanks[index].getFluid()) <= 0;
    }

    /** 槽里那件物品如果是**我们自己的**流体容器就返回它（0.11 ZF73 起机器只认接口）。 */
    private static FluidContainerItem containerOf(ItemStack stack) {
        return stack.getItem() instanceof FluidContainerItem container ? container : null;
    }

    // ================= 0.13 ZF162：槽位不再把关，改由这里判"能不能灌" =================

    /**
     * 一件物品**能装多少 mB 的 {@code fluid}**（−1 = 它根本不是一个能灌的容器）。
     *
     * <p>两条路：</p>
     * <ol>
     *   <li><b>我们自己的容器</b>（{@link FluidContainerItem}：高压气罐 / 油桶）——
     *       直接问它自己（{@code space()}）；</li>
     *   <li><b>别的 mod 的流体容器</b>——NeoForge 的**物品流体能力**
     *       （{@code Capabilities.FluidHandler.ITEM}），拿**一份拷贝**上的句柄做一次 SIMULATE，
     *       回多少就是还能装多少。<b>只读</b>：模拟发生在拷贝上，槽里那份一个字节都不会动。</li>
     * </ol>
     *
     * <p>⚠ 这就是用户那句「检测到能被罐装的才可以罐装」的落点：一件物品算不算"能被罐装"，
     * 判据是<b>能力</b>而不是物品 id —— 所以别的 mod 的液体容器天然支持，
     * 而 Mek 喷气背包那种走"气体系统"的物品会如实被判为"灌不了"（见 §9 的说明）。</p>
     */
    private static int spaceFor(ItemStack stack, FluidStack fluid) {
        FluidContainerItem container = containerOf(stack);
        if (container != null) {
            return container.space(stack);
        }
        IFluidHandlerItem handler = readHandler(stack);
        if (handler != null && !fluid.isEmpty()) {
            return handler.fill(fluid.copyWithAmount(TANK_CAPACITY), IFluidHandler.FluidAction.SIMULATE);
        }
        // 0.13 ZF164：第三条路 —— **Mek 的化学品容器**（喷气背包就是这一路）。Mek 不在时一个字都不问。
        if (MekChemicalBridge.present()) {
            return MekChemicalBridge.spaceFor(stack, fluid);
        }
        return -1;
    }

    /** 一件物品**收不收** {@code fluid} 这一种流体（判据同样是"能力说了算"，机器不替容器把关）。 */
    private static boolean acceptsFluid(ItemStack stack, FluidStack fluid) {
        FluidContainerItem container = containerOf(stack);
        if (container != null) {
            return container.accepts(fluid.getFluid());
        }
        IFluidHandlerItem handler = readHandler(stack);
        if (handler != null) {
            return handler.fill(fluid.copyWithAmount(1), IFluidHandler.FluidAction.SIMULATE) > 0;
        }
        if (MekChemicalBridge.present()) {
            return MekChemicalBridge.accepts(stack, fluid);
        }
        return false;
    }

    /**
     * 取**只读用**的"别的 mod 的流体容器"句柄：句柄绑在**一份拷贝**上，随便模拟都不会碰到槽里那份。
     *
     * <p>堆叠数必须恰好是 1 —— 能力句柄的语义按"一件物品"算，堆叠物品我们一概不碰
     * （槽位本身也限 1 件，见 {@code FillingMachineMenu} 的 {@code getMaxStackSize}）。</p>
     */
    private static IFluidHandlerItem readHandler(ItemStack stack) {
        if (stack.isEmpty() || stack.getCount() != 1) {
            return null;
        }
        return stack.copyWithCount(1).getCapability(Capabilities.FluidHandler.ITEM);
    }

    /** 完成音效：服务端广播（{@code player = null}），客户端按距离衰减，音源挂在方块位置。 */
    private void playCompleteSound() {
        if (this.level == null) {
            return;
        }
        this.level.playSound(null, this.worldPosition, ModSounds.FILLING_MACHINE_COMPLETE.get(),
                SoundSource.BLOCKS, 0.8F, 1.0F);
    }

    /**
     * One tank: pull FILL_RATE out of the tank and push it into the container in the
     * slot below. Energy is charged per tank, and only for tanks that really moved fluid.
     *
     * <p>0.11 ZF73：容器从"写死高压气罐"改成 {@link FluidContainerItem} 接口，
     * 所以气罐与油桶走同一条路，而"收不收这种流体"由容器自己判
     * （气罐拒液体、油桶拒气体与异种流体）。</p>
     *
     * <p>0.13 ZF162：槽位不再把关（什么都能放）⇒ 这里多一条<b>只认能力</b>的路：
     * 不是我们那两种容器时，问 NeoForge 的 {@code Capabilities.FluidHandler.ITEM}
     * （别的 mod 的液体容器）。两条路都只把"真的进了容器的那部分"从罐里扣掉。</p>
     */
    private boolean tryFillSlot(int index) {
        FluidTank tank = this.tanks[index];
        if (tank.isEmpty()) {
            return false;
        }
        ItemStack inSlot = this.items.getStackInSlot(index);
        if (inSlot.isEmpty()) {
            return false;
        }
        FluidContainerItem container = containerOf(inSlot);
        if (container != null) {
            if (container.space(inSlot) <= 0) {
                return false;
            }
            if (this.energy < ENERGY_PER_TANK) {
                return false;
            }
            int moved = container.fill(inSlot, tank.getFluid(), FILL_RATE);
            if (moved <= 0) {
                return false;
            }
            tank.drain(moved, IFluidHandler.FluidAction.EXECUTE);
            this.energy -= ENERGY_PER_TANK;
            this.items.setStackInSlot(index, inSlot);
            return true;
        }
        if (tryFillForeignContainer(index, tank, inSlot)) {
            return true;
        }
        return tryFillMekChemical(index, tank, inSlot);
    }

    /**
     * 灌装 **Mekanism 的化学品容器**（0.13 ZF164 的第三条路）—— 用户的喷气背包就是这一路。
     *
     * <p>映射与安全都在 {@link MekChemicalBridge} 里：我们的流体按 {@code c:<名字>} 同名标签
     * 换成 Mek 的同名化学品（1:1，与 Mek 旋转冷凝器同口径），先 SIMULATE 再 EXECUTE，
     * <b>灌装机只按"真的进去了多少"扣罐扣电</b>。Mek 没装时这一条路整条不存在。</p>
     */
    private boolean tryFillMekChemical(int index, FluidTank tank, ItemStack inSlot) {
        if (this.energy < ENERGY_PER_TANK || !MekChemicalBridge.present()) {
            return false;
        }
        int moved = MekChemicalBridge.fill(inSlot, tank.getFluid(), FILL_RATE);
        if (moved <= 0) {
            return false;
        }
        tank.drain(moved, IFluidHandler.FluidAction.EXECUTE);
        this.energy -= ENERGY_PER_TANK;
        this.items.setStackInSlot(index, inSlot);
        return true;
    }

    /**
     * 灌装**别的 mod 的流体容器**（0.13 ZF162 新路）。
     *
     * <p>顺序刻意与"绝不凭空吞流体"这条老规矩对齐（见 {@link #pourFrom}）：</p>
     * <ol>
     *   <li>在**一份拷贝**上 EXECUTE 灌 FILL_RATE；</li>
     *   <li>取回灌完的容器（{@code getContainer()}）。<b>空栈 = 放弃这一次</b>
     *       （真发生了说明对方的句柄坏了）—— 宁可这一 tick 不灌，也不许把物品吞掉；</li>
     *   <li><b>结果与灌之前逐字节相同 = 说明这次灌装根本没落到物品上</b>（对方句柄没写回）
     *       ⇒ 同样放弃：罐里一滴不扣，绝不出现"流体凭空消失"；</li>
     *   <li>只有前三步都过了，才真的从罐里扣、扣电、把新容器写回槽位。</li>
     * </ol>
     */
    private boolean tryFillForeignContainer(int index, FluidTank tank, ItemStack inSlot) {
        if (this.energy < ENERGY_PER_TANK) {
            return false;
        }
        ItemStack copy = inSlot.copyWithCount(1);
        IFluidHandlerItem handler = copy.getCapability(Capabilities.FluidHandler.ITEM);
        if (handler == null) {
            return false;
        }
        int moved = handler.fill(tank.getFluid().copyWithAmount(FILL_RATE), IFluidHandler.FluidAction.EXECUTE);
        if (moved <= 0) {
            return false;
        }
        ItemStack result = handler.getContainer();
        if (result.isEmpty() || ItemStack.isSameItemSameComponents(result, inSlot)) {
            return false;
        }
        tank.drain(moved, IFluidHandler.FluidAction.EXECUTE);
        this.energy -= ENERGY_PER_TANK;
        this.items.setStackInSlot(index, result.copyWithCount(1));
        return true;
    }

    // ================= 0.11 ZF80：手倒 + 逐槽诊断 =================

    /** 手倒的结果。 */
    public enum PourResult {
        /** 手里那件东西不是流体容器。 */
        NO_CONTAINER,
        /** 容器是空的。 */
        EMPTY,
        /** 五个罐都满了、或者装的都是别的流体（一个罐只装一种）。 */
        NO_ROOM,
        /** 倒进去了。 */
        POURED
    }

    /**
     * 一次手倒的完整结果（给提示文案用）。
     *
     * @param result 结果码
     * @param tank   倒进了几号罐（0 起；没倒成是 −1）
     * @param amount 实际倒进去多少 mB
     * @param fluid  倒完之后那个罐里是什么（没倒成是空）
     */
    public record PourOutcome(PourResult result, int tank, int amount, FluidStack fluid) {
        static PourOutcome of(PourResult result) {
            return new PourOutcome(result, -1, 0, FluidStack.EMPTY);
        }
    }

    /**
     * 把手里容器中的流体倒进罐里 —— <b>纯逻辑</b>（不碰聊天栏、不放音效），探针直接调它。
     *
     * <p><b>为什么要有它</b>（0.11 ZF80）：灌装机的五个罐原先<b>只能靠管道/泵灌</b>，
     * 玩家拿油桶右键机器毫无反应 —— 用户实测「灌装机不往油桶灌液体」的四种成因里，
     * 「罐里根本没有液体」是最常见的一种，而当时玩家没有任何办法用手补上。
     * 现在与蒸馏塔操作器同一个操作：<b>手里拿容器右键 = 倒进罐</b>（空手右键仍是开界面）。</p>
     *
     * <p><b>倒进哪个罐</b>：① 先找已经装着<b>同种</b>流体且还有余量的罐（接着倒）；
     * ② 否则找第一个空罐；③ 都不行 = {@link PourResult#NO_ROOM}。
     * 一个罐只装一种流体这条规矩不动（异种不混装）。</p>
     */
    public PourOutcome pourFrom(ItemStack stack) {
        if (!(stack.getItem() instanceof FluidContainerItem container)) {
            return PourOutcome.of(PourResult.NO_CONTAINER);
        }
        FluidStack held = container.contents(stack);
        if (held.isEmpty()) {
            return PourOutcome.of(PourResult.EMPTY);
        }
        int target = pickTankFor(held);
        if (target < 0) {
            return PourOutcome.of(PourResult.NO_ROOM);
        }
        FluidTank tank = this.tanks[target];
        int want = Math.min(POUR_PER_CLICK, held.getAmount());
        int accepted = tank.fill(held.copyWithAmount(want), IFluidHandler.FluidAction.SIMULATE);
        if (accepted <= 0) {
            return PourOutcome.of(PourResult.NO_ROOM);
        }
        FluidStack drained = container.drain(stack, accepted);
        if (drained.isEmpty()) {
            return PourOutcome.of(PourResult.NO_ROOM);
        }
        int moved = tank.fill(drained, IFluidHandler.FluidAction.EXECUTE);
        if (moved < drained.getAmount()) {
            // 理论上不会发生（刚 SIMULATE 过）；真发生了就把多取的塞回容器，绝不凭空吞流体
            FluidStack back = drained.copyWithAmount(drained.getAmount() - Math.max(moved, 0));
            container.fill(stack, back, back.getAmount());
        }
        if (moved <= 0) {
            return PourOutcome.of(PourResult.NO_ROOM);
        }
        setChanged();
        return new PourOutcome(PourResult.POURED, target, moved, tank.getFluid().copy());
    }

    /** 这一份流体该倒进哪个罐：同种且有空间 ⇒ 第一个空罐 ⇒ −1（倒不进去）。 */
    private int pickTankFor(FluidStack held) {
        for (int i = 0; i < TANK_COUNT; i++) {
            if (!this.tanks[i].isEmpty()
                    && this.tanks[i].getFluid().getFluid() == held.getFluid()
                    && this.tanks[i].getFluidAmount() < this.tanks[i].getCapacity()) {
                return i;
            }
        }
        for (int i = 0; i < TANK_COUNT; i++) {
            if (this.tanks[i].isEmpty()) {
                return i;
            }
        }
        return -1;
    }

    /**
     * 单个槽<b>此刻为什么没在灌</b>（0.11 ZF80）。
     *
     * <p>判据顺序与 {@link #tryFillSlot(int)} <b>逐条对齐</b> —— 诊断说的原因必须就是真正拦住它的那一条，
     * 否则又是一处"界面说的和代码做的不一样"（本工程 §4.51 的教训）。</p>
     */
    public enum SlotState {
        /** 罐是空的，没液体可灌。 */
        TANK_EMPTY,
        /** 槽里没放东西。 */
        SLOT_EMPTY,
        /**
         * 槽里有东西，但那件东西**灌不了**（0.13 ZF162 新增）。
         *
         * <p>它不是流体容器：既不是我们的气罐/油桶（{@link FluidContainerItem}），
         * 也没有物品流体能力（{@code Capabilities.FluidHandler.ITEM}）。
         * 槽位现在什么都能放，所以这一种状态必须有名字 —— 否则玩家看到的又是
         * "明明放了东西，机器却像没看见"（§4.51 那条老账）。</p>
         */
        UNSUPPORTED,
        /** 容器已经满了。 */
        FULL,
        /** 电不够（每个槽每 tick 要 {@link #ENERGY_PER_TANK} FE）。 */
        NO_POWER,
        /** 容器不收罐里那种流体（油桶不收气体、气罐不收液体、油桶不混装）。 */
        REJECTED,
        /** 条件齐了，正在灌。 */
        FILLING
    }

    /**
     * 第 {@code index} 个槽此刻的状态（顺序与灌装逻辑一致，见 {@link SlotState}）。
     *
     * <p>0.13 ZF162：槽位不把关了 ⇒ 判据分成两条路，但<b>每一条都与 {@link #tryFillSlot(int)} 逐条对齐</b>
     * （诊断说的原因必须就是真正拦住它的那一条，§4.51）：</p>
     * <ul>
     *   <li><b>我们自己的容器</b>（{@link FluidContainerItem}）：判据与 ZF73 起的一字未动
     *       —— 满 → 没电 → 不收这种流体 —— 用户明确说这俩「不要动」；</li>
     *   <li><b>别的 mod 的容器</b>：先问"收不收这一种"（模拟 1 mB），再问"还装得下吗"（模拟一整罐）。
     *       两问都走拷贝上的句柄，槽里那份不动；</li>
     *   <li><b>两样都不是</b> ⇒ {@link SlotState#UNSUPPORTED}。</li>
     * </ul>
     */
    public SlotState stateOf(int index) {
        FluidTank tank = this.tanks[index];
        if (tank.isEmpty()) {
            return SlotState.TANK_EMPTY;
        }
        ItemStack inSlot = this.items.getStackInSlot(index);
        if (inSlot.isEmpty()) {
            return SlotState.SLOT_EMPTY;
        }
        FluidContainerItem container = containerOf(inSlot);
        if (container != null) {
            if (container.space(inSlot) <= 0) {
                return SlotState.FULL;
            }
            if (this.energy < ENERGY_PER_TANK) {
                return SlotState.NO_POWER;
            }
            if (!container.accepts(tank.getFluid().getFluid())) {
                return SlotState.REJECTED;
            }
            return SlotState.FILLING;
        }
        IFluidHandlerItem foreign = readHandler(inSlot);
        // 0.13 ZF164：第三条路（Mek 化学品容器）也要有名字，否则喷气背包会显示成「没放东西」那一档
        boolean mek = foreign == null && MekChemicalBridge.present() && MekChemicalBridge.canHandle(inSlot);
        if (foreign == null && !mek) {
            return SlotState.UNSUPPORTED;
        }
        if (!acceptsFluid(inSlot, tank.getFluid())) {
            return SlotState.REJECTED;
        }
        if (spaceFor(inSlot, tank.getFluid()) <= 0) {
            return SlotState.FULL;
        }
        if (this.energy < ENERGY_PER_TANK) {
            return SlotState.NO_POWER;
        }
        return SlotState.FILLING;
    }

    /** 诊断用：这个槽罐里是什么（TANK_EMPTY 时是空）。 */
    public FluidStack fluidOf(int index) {
        return this.tanks[index].getFluid();
    }

    /** 诊断用：机器里现在有多少 FE。 */
    public int getEnergy() {
        return this.energy;
    }

    /** 诊断用：第 {@code index} 个槽里的容器还能装多少 mB（没东西 / 灌不了 = −1）。 */
    public int spaceOf(int index) {
        ItemStack inSlot = this.items.getStackInSlot(index);
        if (inSlot.isEmpty()) {
            return -1;
        }
        return spaceFor(inSlot, this.tanks[index].getFluid());
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.filling_machine");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new FillingMachineMenu(containerId, playerInventory, this);
    }

    // ================= persistence =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        for (int i = 0; i < TANK_COUNT; i++) {
            this.tanks[i].readFromNBT(registries, tag.getCompound(TANK_KEY_PREFIX + i));
        }
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        for (int i = 0; i < TANK_COUNT; i++) {
            tag.put(TANK_KEY_PREFIX + i, this.tanks[i].writeToNBT(registries, new CompoundTag()));
        }
        tag.put("inventory", this.items.serializeNBT(registries));
    }
}