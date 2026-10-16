package com.potatost.mod;

import java.util.HashSet;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.tags.TagKey;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;

/**
 * 流体转化器（0.13 ZF166）。
 *
 * <p><b>干什么</b>：把<b>输入罐</b>里的流体按<b>同名 c: 标签</b>1:1 转成<b>输出罐</b>里那一种。
 * 用户原话（对上一轮报告的答复）：「3.可以做」—— 指的就是"一台把本 mod 的流体转成同标签的别的 mod
 * 流体的机器"。</p>
 *
 * <p><b>样板 = 输出罐里现有的流体</b>（这一条是我定的口径，见档案 §4.172③）：不新增物品槽，
 * 玩家用管道或手倒先把目标流体（比如沉浸工程的柴油）放一点进输出罐，机器就把输入罐里与它
 * <b>共享至少一个 {@code c:} 标签</b>的流体搬过去。于是"转成什么"完全由玩家说了算，
 * 机器不需要在几个同标签流体之间做任意选择。</p>
 *
 * <p><b>三条硬规矩</b>：① 标签判据<b>只认 {@code c:} 命名空间</b>（各自模组的私有标签不算），
 * 而且<b>不缓存</b>（标签是数据包给的，{@code /reload} 之后可能整批变样，缓在 static Map 里会一直用陈旧标签）；
 * ② 先算出这一步能搬多少
 * （{@code Math.min(RATE, 输入量, 输出余量)}），再 {@code drain}/{@code fill} <b>同一个量</b>
 * —— 绝不凭空多出/吞掉流体；③ 只有<b>真的搬了</b>的那一 tick 才扣电。</p>
 *
 * <p>锁定数字（用户没给，我定的，一处就能改）：两罐各 {@link #TANK_CAPACITY} mB、
 * {@link #RATE} mB/t、{@link #ENERGY_PER_TICK} FE/t、缓冲 {@link #MAX_ENERGY} FE。</p>
 */
public class FluidConverterBlockEntity extends BlockEntity implements MenuProvider {

    public static final int TANK_CAPACITY = 5000;
    public static final int RATE = 50;
    public static final int ENERGY_PER_TICK = 30;
    public static final int MAX_ENERGY = 2000;

    /** 手倒：手里那件容器一次最多倒进罐里多少 mB（与灌装机 {@code POUR_PER_CLICK} 同一个口径）。 */
    public static final int POUR_PER_CLICK = 1000;

    /** 手倒的结果：倒进去多少 mB + 该放回玩家手里的那件容器（我们的容器就是原对象）。 */
    public record Pour(int moved, net.minecraft.world.item.ItemStack container) {
    }

    // ContainerData 布局：能量 / 两个罐的量 / 两个罐的流体注册表 id / 状态序数
    public static final int DATA_ENERGY = 0;
    public static final int DATA_INPUT = 1;
    public static final int DATA_OUTPUT = 2;
    public static final int DATA_INPUT_FLUID = 3;
    public static final int DATA_OUTPUT_FLUID = 4;
    /**
     * 状态码 = {@link State#ordinal()} + 1（见 {@link #stateCode()}）。
     *
     * <p>状态<b>由服务端算好再同步</b>：界面不许自己再判一遍（§4.51「界面说的必须就是代码做的」）。
     * 0 留给「服务端还没算过」那一档 ⇒ 界面显示 {@code status.idle}（待机），
     * 于是 lang 里那个 {@code .idle} 键有正经去处。</p>
     */
    public static final int DATA_STATE = 5;
    public static final int DATA_COUNT = 6;

    /** 这台机器此刻为什么没在转（顺序与 {@link #tryConvert()} 的判据逐条对齐）。 */
    public enum State {
        /** 输入罐是空的。 */
        INPUT_EMPTY,
        /** 输出罐是空的 —— 还没有"样板"。 */
        TARGET_EMPTY,
        /** 两边是同一种流体。 */
        SAME_FLUID,
        /** 两种流体没有共同的 {@code c:} 标签。 */
        NO_SHARED_TAG,
        /** 输出罐满了。 */
        OUTPUT_FULL,
        /** 缺电。 */
        NO_POWER,
        /** 正在转。 */
        RUNNING
    }

    private final FluidTank input = new FluidTank(TANK_CAPACITY, FluidConverterBlockEntity::acceptsAnyFluid);
    private final FluidTank output = new FluidTank(TANK_CAPACITY, FluidConverterBlockEntity::acceptsAnyFluid);
    private int energy = 0;

    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                this.setChanged();
            });

    /**
     * 对外句柄：<b>两个罐都收任何非空流体，抽的一律从输出罐走</b>。
     *
     * <p>规则（管道/泵不用管自己接的是哪一面）：</p>
     * <ol>
     *   <li>接着<b>同一种</b>流体倒 —— 输入罐里是这种就进输入罐（原料），否则输出罐里是这种就进输出罐；</li>
     *   <li>输入罐空着 ⇒ 进输入罐（先有原料）；</li>
     *   <li>输入罐装着别的流体、输出罐空着 ⇒ 这一笔就是<b>样板</b>，进输出罐 ——
     *       用户说的「输出罐里先放一点目标流体」于是<b>管道灌和手倒都行</b>
     *       （手倒那条见 {@link #pourFrom(net.minecraft.world.item.ItemStack, boolean, int)}）；</li>
     *   <li>两个罐都装着别的流体 ⇒ 收不下，返回 0。</li>
     * </ol>
     *
     * <p>抽（drain）一律从<b>输出罐</b>出 —— 那才是产物，原料留在输入罐里继续转。</p>
     */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return 2;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return tank == 0 ? input.getFluid() : output.getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return TANK_CAPACITY;
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            // 两个罐都收任何非空流体（用户规格：两个都收任何非空流体）——
            // "是不是同一种"由 fill 逐罐判，这里不预设名单
            return acceptsAnyFluid(stack);
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            return fillRouted(resource, action);
        }

        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            return output.drain(resource, action);
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            return output.drain(maxDrain, action);
        }
    };

    /**
     * 外来的流体该进哪个罐（规则见 {@link #getFluidHandler()}）。
     *
     * <p>⚠ 顺序有讲究：输入罐里<b>已经是这一种</b>时，哪怕它满了也<b>绝不放行到输出罐</b> ——
     * 否则管子一冲，输出罐里就被灌进原料，机器随即只会报「两边同一种」，看着像坏了。</p>
     */
    private int fillRouted(FluidStack resource, IFluidHandler.FluidAction action) {
        if (resource.isEmpty()) {
            return 0;
        }
        if (holdsSameFluid(this.input, resource)) {
            return this.input.fill(resource, action);
        }
        if (holdsSameFluid(this.output, resource)) {
            return this.output.fill(resource, action);
        }
        if (this.input.isEmpty()) {
            return this.input.fill(resource, action);
        }
        if (this.output.isEmpty()) {
            // 输入罐里有别的流体、输出罐空着 ⇒ 这一笔就是样板
            return this.output.fill(resource, action);
        }
        return 0;
    }

    /** 这个罐里装的是不是 {@code resource} 那一种流体（空罐 = 否）。 */
    private static boolean holdsSameFluid(FluidTank tank, FluidStack resource) {
        return !tank.isEmpty() && tank.getFluid().getFluid() == resource.getFluid();
    }

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_ENERGY -> energy;
                case DATA_INPUT -> input.getFluidAmount();
                case DATA_OUTPUT -> output.getFluidAmount();
                case DATA_INPUT_FLUID -> BuiltInRegistries.FLUID.getId(input.getFluid().getFluid());
                case DATA_OUTPUT_FLUID -> BuiltInRegistries.FLUID.getId(output.getFluid().getFluid());
                // ordinal + 1：0 留给"服务端还没算过"（界面显示待机）
                case DATA_STATE -> stateOf().ordinal() + 1;
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
            // 服务端读自己的字段；客户端照 SimpleContainerData 镜像
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public FluidConverterBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.FLUID_CONVERTER_BE.get(), pos, state);
    }

    /** 两个罐都收"任何非空流体"—— 收不收由对面那个罐的同名标签说了算（机器不预设名单）。 */
    public static boolean acceptsAnyFluid(FluidStack stack) {
        return stack != null && !stack.isEmpty();
    }

    public FluidTank getInputTank() {
        return this.input;
    }

    public FluidTank getOutputTank() {
        return this.output;
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

    public int getEnergy() {
        return this.energy;
    }

    /** 机器此刻的状态码（0 = 服务端还没算过 = 待机；诊断与界面共用，见 {@link #DATA_STATE}）。 */
    public int stateCode() {
        return stateOf().ordinal() + 1;
    }

    /** 这个状态码是不是"正在转"（界面拿它决定那一行字的颜色）。 */
    public static boolean isRunning(int code) {
        return code == State.RUNNING.ordinal() + 1;
    }

    // ================= 文案（诊断与界面共用同一份） =================

    /** 输入罐那一行的标签 lang 键（诊断与界面共用）。 */
    public static final String LANG_TANK_INPUT = "gui.potato_s_t.fluid_converter.tank.input";
    /** 输出罐（样板）那一行的标签 lang 键。 */
    public static final String LANG_TANK_OUTPUT = "gui.potato_s_t.fluid_converter.tank.output";

    /**
     * 状态那一行的完整文案（Shift 诊断与界面<b>共用同一个 switch</b>，
     * 免得出现"界面上写的"和"聊天栏里说的"不一样，§4.51）。
     *
     * <p>占位符口径（与 lang 逐字对应）：{@code no_shared_tag} = (输入流体名, 样板流体名)；
     * {@code no_power} = (每 tick 电费, 机器里现有的 FE)；{@code running} = (输入流体名, 样板流体名, 速率 mB/t)；
     * 其余状态与 {@code idle} 没有占位符。</p>
     */
    public static Component statusLine(int code, FluidStack input, FluidStack output, int energy) {
        State[] all = State.values();
        State state = code >= 1 && code <= all.length ? all[code - 1] : null;
        if (state == null) {
            // 0（服务端还没算过）或越界 ⇒ 待机
            return Component.translatable("gui.potato_s_t.fluid_converter.status.idle");
        }
        return switch (state) {
            case INPUT_EMPTY -> Component.translatable("gui.potato_s_t.fluid_converter.status.input_empty");
            case TARGET_EMPTY -> Component.translatable("gui.potato_s_t.fluid_converter.status.target_empty");
            case SAME_FLUID -> Component.translatable("gui.potato_s_t.fluid_converter.status.same_fluid");
            case NO_SHARED_TAG -> Component.translatable("gui.potato_s_t.fluid_converter.status.no_shared_tag",
                    fluidName(input), fluidName(output));
            case OUTPUT_FULL -> Component.translatable("gui.potato_s_t.fluid_converter.status.output_full");
            case NO_POWER -> Component.translatable("gui.potato_s_t.fluid_converter.status.no_power",
                    ENERGY_PER_TICK, energy);
            case RUNNING -> Component.translatable("gui.potato_s_t.fluid_converter.status.running",
                    fluidName(input), fluidName(output), RATE);
        };
    }

    /**
     * 一个罐那一行：{@code <标签>：<流体名> / <量> mB}。
     *
     * <p>复用 lang 里现成的两个通用键（{@code gui.potato_s_t.tank} 与
     * {@code gui.potato_s_t.test_fluid_tank.none}）—— 本机器不新增语言键，
     * 空罐那半句也需要一个现成的「空」字。</p>
     *
     * @param labelKey 这一行给哪个罐（{@link #LANG_TANK_INPUT} / {@link #LANG_TANK_OUTPUT}）
     */
    public static Component tankLine(String labelKey, FluidStack fluid) {
        return Component.translatable("gui.potato_s_t.tank",
                Component.translatable(labelKey), fluidName(fluid), fluid.getAmount());
    }

    /** 一种流体的显示名（空罐用现成的通用「空」字键，不去问空流体要名字）。 */
    public static Component fluidName(FluidStack fluid) {
        return fluid.isEmpty()
                ? Component.translatable("gui.potato_s_t.test_fluid_tank.none")
                : fluid.getHoverName();
    }

    // ================= tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, FluidConverterBlockEntity machine) {
        if (level.isClientSide) {
            return;
        }
        if (machine.tryConvert()) {
            machine.setChanged();
        }
    }

    /**
     * 这一 tick 试着转一次。<b>判据顺序必须与 {@link #stateOf()} 逐条一致</b>
     * （诊断说的话必须就是真正拦住它的那一条，§4.51）。
     */
    private boolean tryConvert() {
        if (this.input.isEmpty()) {
            return false;
        }
        if (this.output.isEmpty()) {
            return false;
        }
        Fluid in = this.input.getFluid().getFluid();
        Fluid out = this.output.getFluid().getFluid();
        if (in == out) {
            return false;
        }
        if (!sharesCTag(in, out)) {
            return false;
        }
        int room = this.output.getCapacity() - this.output.getFluidAmount();
        if (room <= 0) {
            return false;
        }
        if (this.energy < ENERGY_PER_TICK) {
            return false;
        }
        int moved = Math.min(RATE, Math.min(this.input.getFluidAmount(), room));
        if (moved <= 0) {
            return false;
        }
        FluidStack drained = this.input.drain(moved, IFluidHandler.FluidAction.EXECUTE);
        if (drained.isEmpty()) {
            return false;
        }
        // ⚠ 这里是"转化"两个字本身：**输出罐要灌的是样品那一种流体**，不是输入罐那种。
        //   写成 output.fill(drained, …) 的话 FluidTank 会因异种流体恒回 0 ⇒ 机器一辈子一动不动
        //   （ZF166 自审 + 独立复核各抓到一次，见档案 §4.172④）。
        FluidStack produced = new FluidStack(out, drained.getAmount());
        int filled = this.output.fill(produced, IFluidHandler.FluidAction.EXECUTE);
        if (filled < drained.getAmount()) {
            // 理论上不会发生（余量刚算过）；真发生了就把**没转成的那部分输入流体**塞回输入罐，绝不凭空吞
            FluidStack back = new FluidStack(in, drained.getAmount() - Math.max(filled, 0));
            this.input.fill(back, IFluidHandler.FluidAction.EXECUTE);
        }
        if (filled <= 0) {
            return false;
        }
        this.energy -= ENERGY_PER_TICK;
        return true;
    }

    /** 这台机器此刻是什么状态（顺序与 {@link #tryConvert()} 一致）。 */
    public State stateOf() {
        if (this.input.isEmpty()) {
            return State.INPUT_EMPTY;
        }
        if (this.output.isEmpty()) {
            return State.TARGET_EMPTY;
        }
        Fluid in = this.input.getFluid().getFluid();
        Fluid out = this.output.getFluid().getFluid();
        if (in == out) {
            return State.SAME_FLUID;
        }
        if (!sharesCTag(in, out)) {
            return State.NO_SHARED_TAG;
        }
        if (this.output.getCapacity() - this.output.getFluidAmount() <= 0) {
            return State.OUTPUT_FULL;
        }
        if (this.energy < ENERGY_PER_TICK) {
            return State.NO_POWER;
        }
        return State.RUNNING;
    }

    /**
     * 本机器**没有物品槽**（{@code SLOT_COUNT = 0}）—— 这个空句柄存在的唯一理由，是让
     * {@link FluidConverterBlock#onRemove} 能照全模组那条**文本级**判据（Audit B：带物品栏的方块实体
     * 必须在 {@code onRemove} 里显式调 {@code MachineDrops.dropInventory}）写同一行字；
     * 它永远是空的，一个物品都不会掉。
     */
    public static final int SLOT_COUNT = 0;

    private final net.neoforged.neoforge.items.ItemStackHandler inventory =
            new net.neoforged.neoforge.items.ItemStackHandler(SLOT_COUNT);

    public net.neoforged.neoforge.items.ItemStackHandler getInventory() {
        return this.inventory;
    }

    /**
     * 两种流体有没有共同的 {@code c:} 标签（**只认 c: 命名空间**：各模组自己的私有标签不算，
     * 否则会出现"因为都挂着某个模组标签而被判成可转"的荒唐转换，见档案 §4.172②）。
     *
     * <p>⚠ 这里**故意不缓存**：标签是数据包给的，`/reload` 之后可能整批变样；把结果缓存在 static Map 里
     * 会一直用陈旧标签（宁可每次现算 —— 一次交集就几个元素，代价可以忽略）。</p>
     */
    public static boolean sharesCTag(Fluid a, Fluid b) {
        for (TagKey<Fluid> tag : cTagsOf(a)) {
            if (cTagsOf(b).contains(tag)) {
                return true;
            }
        }
        return false;
    }

    private static Set<TagKey<Fluid>> cTagsOf(Fluid fluid) {
        Set<TagKey<Fluid>> set = new HashSet<>();
        for (TagKey<Fluid> tag : BuiltInRegistries.FLUID.wrapAsHolder(fluid).tags().toList()) {
            if ("c".equals(tag.location().getNamespace())) {
                set.add(tag);
            }
        }
        return set;
    }

    // ================= 手倒 =================

    /**
     * 手拿容器右键机器时的"倒流体"（0.13 ZF166）：<b>普通右键倒进输出罐（= 设样板），
     * 潜行右键倒进输入罐（= 喂料）</b>。
     *
     * <p>两条路都只按"<b>真的倒进罐里的量</b>"结算，倒不进去的那部分<b>原样留在容器里</b>
     * （与灌装机"绝不凭空吞流体"同一条规矩）。</p>
     *
     * <p>容器有两类：① 我们自己的 {@link FluidContainerItem}（气罐/油桶，就地改物品）；
     * ② 别的 mod 的流体容器（含原版水桶）—— 走 NeoForge 的物品流体能力，最后用
     * {@code getContainer()} 拿回"倒完之后的那件物品"（可能是空桶）。</p>
     */
    public Pour pourFrom(net.minecraft.world.item.ItemStack stack, boolean toOutput, int max) {
        FluidTank tank = toOutput ? this.output : this.input;
        int room = tank.getCapacity() - tank.getFluidAmount();
        if (stack.isEmpty() || room <= 0) {
            return new Pour(0, stack);
        }
        int limit = Math.min(max, room);
        // ① 我们自己的容器
        if (containerOf(stack) instanceof FluidContainerItem container) {
            FluidStack held = container.contents(stack);
            if (held.isEmpty()) {
                return new Pour(0, stack);
            }
            FluidStack drained = container.drain(stack, limit);
            if (drained.isEmpty()) {
                return new Pour(0, stack);
            }
            int filled = tank.fill(drained, IFluidHandler.FluidAction.EXECUTE);
            if (filled < drained.getAmount()) {
                // 罐里塞不下的部分**还回容器**（绝不凭空吞掉）
                container.fill(stack, drained.copyWithAmount(drained.getAmount() - filled), Integer.MAX_VALUE);
            }
            if (filled > 0) {
                this.setChanged();
            }
            return new Pour(filled, stack);
        }
        // ② 别的 mod 的流体容器（含原版水桶：NeoForge 给"装着的桶"挂物品流体能力）
        if (stack.getCount() != 1) {
            return new Pour(0, stack);
        }
        net.minecraft.world.item.ItemStack copy = stack.copyWithCount(1);
        net.neoforged.neoforge.fluids.capability.IFluidHandlerItem handler =
                copy.getCapability(net.neoforged.neoforge.capabilities.Capabilities.FluidHandler.ITEM);
        if (handler == null) {
            return new Pour(0, stack);
        }
        // ⚠【0.13 ZF168 实测的 API 雷】NeoForge 的**桶包装器**（`FluidBucketWrapper`）在
        //   "要取出的量 < 一整桶" 时会**返回空**（它只按整桶结算）⇒ 这里必须**先按整桶模拟、
        //   按整桶取**，再把自己罐里塞不下的那部分 `fill` 回容器（下面那两行）——
        //   否则"罐里只剩不到 1000 mB 余量"时，一整桶水会**倒不进去**（看着像机器坏了）。
        FluidStack sim = handler.drain(Integer.MAX_VALUE, IFluidHandler.FluidAction.SIMULATE);
        if (sim.isEmpty()) {
            return new Pour(0, stack);
        }
        FluidStack drained = handler.drain(sim.getAmount(), IFluidHandler.FluidAction.EXECUTE);
        if (drained.isEmpty()) {
            return new Pour(0, stack);
        }
        int filled = tank.fill(drained, IFluidHandler.FluidAction.EXECUTE);
        if (filled < drained.getAmount()) {
            handler.fill(drained.copyWithAmount(drained.getAmount() - filled), IFluidHandler.FluidAction.EXECUTE);
        }
        if (filled > 0) {
            this.setChanged();
        }
        net.minecraft.world.item.ItemStack out = handler.getContainer();
        return new Pour(filled, out.isEmpty() ? stack : out);
    }

    /**
     * 机器 → 容器（0.13 ZF168）：手拿**空**容器右键 = 把罐里的流体装进容器。
     *
     * <p><b>为什么必须有这条</b>：用户实测报「转换器的输出储罐好像改不了」。病根是
     * {@link FluidTank} 的语义 —— 罐里已经有流体时**异种流体一律拒收**（{@code isFluidEqual} 不过），
     * 而原来只有"容器 → 机器"一条路 ⇒ 样板一旦定下就**再也换不掉**（管道也换不掉：能力那条路
     * 只在罐空时才收别的流体）。加上这条以后换样板的流程是：
     * <b>手拿空桶右键把旧样板装走 → 罐空了 → 再倒新样板</b>，全程一滴流体都不凭空消失。</p>
     *
     * <p>口径与 {@code pourFrom} 对称：<b>普通右键 = 输出罐</b>（样板），<b>潜行右键 = 输入罐</b>（原料）。
     * 两条都只按"<b>真的装进容器的量</b>"从罐里扣（先装容器、再按实际量抽罐；万一罐里少了就把多装的
     * 还给容器），绝不凭空吞流体。</p>
     */
    public Pour fillContainerFrom(net.minecraft.world.item.ItemStack stack, boolean fromOutput, int max) {
        FluidTank tank = fromOutput ? this.output : this.input;
        if (stack.isEmpty() || tank.isEmpty()) {
            return new Pour(0, stack);
        }
        int limit = Math.min(max, tank.getFluidAmount());
        Fluid toGive = tank.getFluid().getFluid();
        // ① 我们自己的容器
        if (containerOf(stack) instanceof FluidContainerItem container) {
            int space = Math.min(container.space(stack), limit);
            if (space <= 0 || !container.accepts(toGive)) {
                return new Pour(0, stack);
            }
            int put = container.fill(stack, new FluidStack(toGive, space), Integer.MAX_VALUE);
            if (put <= 0) {
                return new Pour(0, stack);
            }
            FluidStack taken = tank.drain(put, IFluidHandler.FluidAction.EXECUTE);
            if (taken.getAmount() < put) {
                // 理论上不会（量刚算过）；真发生了就把多装的退回去，绝不凭空吞
                container.drain(stack, put - taken.getAmount());
            }
            if (!taken.isEmpty()) {
                this.setChanged();
            }
            return new Pour(taken.getAmount(), stack);
        }
        // ② 别的 mod 的容器（含原版空桶：NeoForge 给"空桶"也挂物品流体能力）
        if (stack.getCount() != 1) {
            return new Pour(0, stack);
        }
        net.minecraft.world.item.ItemStack copy = stack.copyWithCount(1);
        net.neoforged.neoforge.fluids.capability.IFluidHandlerItem handler =
                copy.getCapability(net.neoforged.neoforge.capabilities.Capabilities.FluidHandler.ITEM);
        if (handler == null) {
            return new Pour(0, stack);
        }
        int put = handler.fill(new FluidStack(toGive, limit), IFluidHandler.FluidAction.EXECUTE);
        if (put <= 0) {
            return new Pour(0, stack);
        }
        FluidStack taken = tank.drain(put, IFluidHandler.FluidAction.EXECUTE);
        if (taken.getAmount() < put) {
            handler.drain(put - taken.getAmount(), IFluidHandler.FluidAction.EXECUTE);
        }
        if (!taken.isEmpty()) {
            this.setChanged();
        }
        net.minecraft.world.item.ItemStack out = handler.getContainer();
        return new Pour(taken.getAmount(), out.isEmpty() ? stack : out);
    }

    /** 槽里那件物品如果是**我们自己的**流体容器就返回它（与灌装机同一个判据）。 */
    private static FluidContainerItem containerOf(net.minecraft.world.item.ItemStack stack) {
        return stack.getItem() instanceof FluidContainerItem container ? container : null;
    }

    /**
     * 手里这件是不是**流体容器**（我们的气罐/油桶，或任何挂了 NeoForge 物品流体能力的容器，
     * 含**空桶**）。0.13 ZF170 加：机器"这次没吃下"时要用它决定该不该把交互**吞掉** ——
     * 手里是流体容器却返回 PASS，原版就会接着跑 {@code BucketItem.useOn}，**把桶里的流体倒进世界**
     * （用户实测「shift+右键会把流体倒出来 而不是倒进版样」，凭空丢流体）。
     */
    public static boolean isFluidContainer(net.minecraft.world.item.ItemStack stack) {
        if (stack.isEmpty()) {
            return false;
        }
        if (containerOf(stack) != null) {
            return true;
        }
        return stack.copyWithCount(1)
                .getCapability(net.neoforged.neoforge.capabilities.Capabilities.FluidHandler.ITEM) != null;
    }

    /** 手里这件容器里现在是哪种流体（空的 / 不是容器 ⇒ null）。 */
    public static Fluid heldFluid(net.minecraft.world.item.ItemStack stack) {
        if (containerOf(stack) instanceof FluidContainerItem container) {
            FluidStack held = container.contents(stack);
            return held.isEmpty() ? null : held.getFluid();
        }
        if (stack.getCount() != 1) {
            return null;
        }
        net.neoforged.neoforge.fluids.capability.IFluidHandlerItem handler = stack.copyWithCount(1)
                .getCapability(net.neoforged.neoforge.capabilities.Capabilities.FluidHandler.ITEM);
        if (handler == null) {
            return null;
        }
        FluidStack sim = handler.drain(Integer.MAX_VALUE, IFluidHandler.FluidAction.SIMULATE);
        if (sim.isEmpty()) {
            return null;
        }
        return sim.getFluid();
    }

    /**
     * 「手里这件容器里的流体，目标罐**收不下**」—— 也就是罐里已经装着**另一种**流体
     * （{@link FluidTank} 的异种流体拒收语义）。这一条专门用来给玩家**说清楚怎么换样板**
     * （用户实测报「输出罐改不了」时，缺的就是这句话）。
     */
    public boolean targetBlocked(net.minecraft.world.item.ItemStack stack, boolean toOutput) {
        FluidTank tank = toOutput ? this.output : this.input;
        if (tank.isEmpty()) {
            return false;
        }
        Fluid held = heldFluid(stack);
        return held != null && held != tank.getFluid().getFluid();
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.fluid_converter");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new FluidConverterMenu(containerId, playerInventory, this);
    }

    // ================= 存档 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.input.readFromNBT(registries, tag.getCompound("input"));
        this.output.readFromNBT(registries, tag.getCompound("output"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.put("input", this.input.writeToNBT(registries, new CompoundTag()));
        tag.put("output", this.output.writeToNBT(registries, new CompoundTag()));
    }
}
