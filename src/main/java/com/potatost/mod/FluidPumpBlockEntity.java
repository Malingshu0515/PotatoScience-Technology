package com.potatost.mod;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
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
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;

/**
 * 流体泵：
 *  - ★ <b>0.11 ZF98：泵本身不存流体，只做传输</b>（用户原话「流体泵改一下 本身不能储存流体
 *    只做传输 且优先传输目标容器需要/能被接受 的流体」）。原先泵里有一个 8000 mB 的内部罐
 *    （"先抽进来、再送出去"两步走），现在**一 tick 内直接搬**：从源网络抽出来的那一笔，
 *    当场灌进目标网络 —— 泵里不再有任何液体存量，也不再对外暴露流体能力。
 *  - ★ <b>优先送目标收得下的流体</b>：对每个目标，先试"它罐里已经有那种流体"，
 *    再按源里出现的顺序逐个 `SIMULATE` 问它收不收；**收 0 就跳过、一滴都不抽**
 *    （老行为是抽进内部罐攒着，现在不会再有"抽了送不掉"的中间态）。
 *  - FE 基础缓冲 1024；实际缓冲 = max(1024, 单刻电费)。
 *    ★ 高速档修复：旧版缓冲恒为 1024，而电费 179% 起单刻就超过 1024
 *      （200% = 1200，800% = 102000 FE/t），能量永远凑不满 → 高速档永久待机。
 *      现在缓冲自动放大到"至少付得起一刻电"，供电跟得上就能全速跑。
 *  - 速率 0..800%（UI 调）。
 *  - 电费分档：1..100% 每 1% = 4 FE/t；101..200% 每 1% = 8 FE/t；201..300% = 16 FE/t；每 +100% 翻倍。
 *  - 流量 = 10 mB/t × 速率%。
 *  - 范围：≤200% 时前后两端"管道格数"合计 ≤32；>200% 每 +50% 加 1 格。
 *    （距离只数管道：紧贴泵面的第一根管道 = 1；紧贴泵面的容器/源方块 = 0；不含泵本身）
 *  - 速率 0 = 不耗电不搬运；>0 且供得上电 = 按规格持续耗电。
 *  - ★ 红石控制：被红石信号激活时停机——不耗电也不搬运；信号消失自动恢复。
 *  - ★ 输入端（泵正面及其管道网络）可以吸取"源头方块"（水/岩浆源）：
 *      每个源方块 = 1000 mB，抽满即移除方块；只认"液体方块本身"（LiquidBlock），
 *      含水方块（含水楼梯/管道/海草等）不算水源、不会被吸掉；
 *      进度记在 pump 的账本里并随存档保存——同一方块总共只出 1000 mB。
 *  - 输出端（泵背面及其网络）不会往世界液体里倒。
 *  - ⚠ <b>两台泵不能串成"接力"</b>：泵没有罐 ⇒ 它既不能当源、也不能当目标
 *      （以前"A 泵把液体推进 B 泵的内部罐"那条路随内部罐一起去掉了）。
 *      要跨更远距离就用更大的速率（范围随速率增长），或者中间放一个储罐。
 */
public class FluidPumpBlockEntity extends BlockEntity implements MenuProvider {

    // ================== 数值（改这里） ==================
    public static final int MAX_ENERGY = 1024;           // FE 基础缓冲上限（实际缓冲见 effectiveCapacity()）
    public static final int MAX_RATE = 800;              // 速率上限 %
    public static final int MB_PER_PERCENT = 10;         // 每 1% 每 tick 传输 mB
    public static final int FE_BASE_PER_PERCENT = 4;     // 第一档（1..100%）每 1% 每 tick 的 FE
    public static final int RANGE_FREE = 32;             // ≤200% 时的前后合计管道格数
    public static final int RANGE_STEP_PER = 50;         // >200% 每 +50% 加 1 格
    /**
     * 旧存档里那个内部罐的容量（0.11 ZF98 之前的 {@code TANK_CAPACITY}）。
     *
     * <p>⚠ 现在**只是读档用的探针容量**：泵已经没有内部罐了，这个数只用于把旧存档
     * {@code "tank"} 标签里残留的流体接住（见 {@link #legacy}），接住之后立刻吐进目标网络。</p>
     */
    public static final int LEGACY_TANK_CAPACITY = 8000;
    /** 一个世界源方块的液量（与桶一致）：抽满即把方块置为空气 */
    public static final int BLOCK_FLUID_AMOUNT = 1000;

    // ContainerData 索引（GUI 同步）
    public static final int DATA_RATE = 0;
    public static final int DATA_ENERGY = 1;
    public static final int DATA_COUNT = 2;

    private int rate = 100;      // 默认 100%
    private int energy = 0;
    /**
     * 旧存档里内部罐残留的流体（0.11 ZF98 拆罐前存进去的）。
     *
     * <p>不凭空销毁玩家的东西：读档时把它接住，泵一旦恢复工作就<b>优先吐进目标网络</b>
     * （见 {@link #flushLegacy}），吐干净后这个字段就永远是空的。
     * 新存档不会再往里写任何东西 —— 泵运行时不再存流体。</p>
     */
    private FluidStack legacy = FluidStack.EMPTY;

    /** 世界源方块抽取账本：pos → 已抽走 mB（0 < taken < 1000 才有意义；抽满清账） */
    private final Map<BlockPos, Integer> worldPumpProgress = new HashMap<>();

    private final IEnergyStorage energyStorage = new IEnergyStorage() {
        @Override
        public int receiveEnergy(int maxReceive, boolean simulate) {
            int space = effectiveCapacity() - energy;
            if (maxReceive <= 0 || space <= 0) {
                return 0;
            }
            int accepted = Math.min(maxReceive, space);
            if (!simulate) {
                energy += accepted;
                setChanged();
            }
            return accepted;
        }

        @Override
        public int extractEnergy(int maxExtract, boolean simulate) {
            return 0;   // 泵只吃电，不吐电
        }

        @Override
        public int getEnergyStored() {
            return Math.min(energy, effectiveCapacity());
        }

        @Override
        public int getMaxEnergyStored() {
            return effectiveCapacity();
        }

        @Override
        public boolean canExtract() {
            return false;
        }

        @Override
        public boolean canReceive() {
            return true;
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_RATE -> rate;
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

    public FluidPumpBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.FLUID_PUMP_BE.get(), pos, state);
    }

    // ================== 供电缓冲（高速档修复） ==================

    /**
     * 实际能量缓冲上限 = max(基础缓冲 1024, 本刻电费)。
     * 为什么必须这样：若缓冲恒为 1024，而某速率的"单刻电费"大于 1024
     * （178% 时刚好 1024；179% 起就超），能量永远无法 ≥ cost，
     * 泵会永久待机——表现为"慢速能跑、快速一动不动"。
     * 放大后：缓冲至少"付得起一刻电"，只要外部供电 ≥ 单刻电费即可持续运行。
     */
    public int effectiveCapacity() {
        return Math.max(MAX_ENERGY, fePerTick(this.rate));
    }

    // ================== 静态公式（GUI 与服务端共用，纯算术，客户端安全） ==================

    /** 速率 r% 时每 tick 消耗的 FE（4/8/16/32… 每 100% 翻一倍的分档求和） */
    public static int fePerTick(int ratePercent) {
        if (ratePercent <= 0) {
            return 0;
        }
        int fullTiers = (ratePercent - 1) / 100;          // 已满的 100% 档数
        int remainder = ratePercent - fullTiers * 100;    // 当前档的百分比
        int cost = 0;
        int perPercent = FE_BASE_PER_PERCENT;
        for (int t = 0; t < fullTiers; t++) {
            cost += perPercent * 100;
            perPercent <<= 1;
        }
        cost += perPercent * remainder;
        return cost;
    }

    /** 速率 r% 时每 tick 传输的 mB */
    public static int mbPerTick(int ratePercent) {
        return ratePercent * MB_PER_PERCENT;
    }

    /** 速率 r% 时的前后合计管道格数上限 */
    public static int maxRange(int ratePercent) {
        if (ratePercent <= 200) {
            return RANGE_FREE;
        }
        return RANGE_FREE + (ratePercent - 200) / RANGE_STEP_PER;
    }

    // ================== 对外接口 ==================
    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    // ⚠ 0.11 ZF98 删掉了 getFluidHandler()：泵**不再存流体** ⇒ 没有内部罐可以暴露，
    //   `PotatoST` 里那条"正/背面暴露内部罐"的能力登记也一起去掉了。
    //   需要"泵能把容器里的东西抽出来"的场景（例如容器换流器）走的是**对方**的流体能力，
    //   与本类无关。

    public ContainerData getContainerData() {
        return this.containerData;
    }

    public int getRate() {
        return this.rate;
    }

    public void setRate(int newRate) {
        int clamped = Mth.clamp(newRate, 0, MAX_RATE);
        if (clamped != this.rate) {
            this.rate = clamped;
            this.energy = Math.min(this.energy, effectiveCapacity());   // 降速后不超新上限
            setChanged();
        }
    }

    // ================== 每 tick ==================
    public static void tick(Level level, BlockPos pos, BlockState state, FluidPumpBlockEntity pump) {
        pump.serverTick();
    }

    private void serverTick() {
        if (this.level == null || this.level.isClientSide) {
            return;
        }
        // ★ 红石控制：被红石信号激活即"关"——不耗电、不搬运；信号消失自动恢复。
        //   判据与上游红石对所有方块一致（SignalGetter#hasNeighborSignal）：
        //   拉杆、按钮、红石块、指向本机的红石粉、贴着的红石火把等都会生效。
        if (this.level.hasNeighborSignal(this.getBlockPos())) {
            return;
        }
        if (this.rate <= 0) {
            return;   // 0%：不耗电、不搬运
        }
        int cost = fePerTick(this.rate);
        if (this.energy < cost) {
            return;   // 缺电待机：等能量攒到一刻的电费（供电不足时表现为断续/等待）
        }

        Direction front = this.getBlockState().getValue(FluidPumpBlock.FACING);
        Direction back = front.getOpposite();
        int range = maxRange(this.rate);

        // 先扣电：速率 > 0 且供电充足就持续耗电（0% 才完全不耗）
        this.energy -= cost;
        setChanged();

        // 输入端允许吸"源头方块"；输出端不允许往世界液体里倒
        List<Target> sources = scan(this.level, this.getBlockPos().relative(front), front, range, true);
        List<Target> outputsAll = scan(this.level, this.getBlockPos().relative(back), back, range, false);

        // ★ 防"左脚踩右脚"：把同时出现在"抽取侧"里的容器从"输送侧"候选中剔除
        Set<BlockPos> sourcePositions = new HashSet<>();
        for (Target source : sources) {
            sourcePositions.add(source.pos());
        }
        List<Target> outputs = new ArrayList<>();
        for (Target output : outputsAll) {
            if (!sourcePositions.contains(output.pos())) {
                outputs.add(output);
            }
        }

        if (sources.isEmpty() || outputs.isEmpty()) {
            return;
        }

        // 前后合计 ≤ range：每端可及距离 = range − 对端最近距离
        int maxInput = range - outputs.get(0).distance();
        int maxOutput = range - sources.get(0).distance();
        int budget = mbPerTick(this.rate);

        // ★ 0.11 ZF98：抽送**一体**、中间不落罐。
        //   优先级（用户原话「优先传输目标容器需要/能被接受 的流体」）：
        //     ① 目标罐里**已经有**的那种流体最优先（机器/储罐大多只收同一种，先喂它才吃得下）；
        //     ② 再按"源网络里出现了什么"逐个 SIMULATE 问目标 —— **目标是 0 就直接跳过、不抽**。
        //   ⇒ 收不下的流体一滴都不会被抽走；也不会再出现"抽进泵里、送不出去、攒着"的中间态。
        int moved = flushLegacy(outputs, budget);
        for (Target output : outputs) {
            if (moved >= budget) {
                break;
            }
            if (output.distance() > maxOutput) {
                continue;
            }
            for (Fluid fluid : preferenceOrder(output, sources, maxInput)) {
                if (moved >= budget) {
                    break;
                }
                moved += push(output, sources, fluid, budget - moved, maxInput);
            }
        }
        if (moved > 0) {
            setChanged();
        }
    }

    /**
     * 旧存档遗留的流体（拆罐前存在泵里的那些）：**优先吐进目标网络**，最多 {@code max} mB。
     *
     * <p>为什么要有这一段：拆掉内部罐之后，旧存档里 `"tank"` 标签里那点流体会变成"读得出来
     * 却没地方放"。直接丢掉 = 凭空销毁玩家的东西（本工程不允许），所以接住它、等泵一开工
     * 就按正常方向送出去。<b>不额外耗电</b>—— 这不是"泵送"，是把历史遗留倒干净。</p>
     *
     * @return 实际倒出去多少 mB
     */
    private int flushLegacy(List<Target> outputs, int max) {
        if (this.legacy.isEmpty() || max <= 0) {
            return 0;
        }
        int left = this.legacy.getAmount();
        int moved = 0;
        for (Target output : outputs) {
            if (left <= 0 || moved >= max) {
                break;
            }
            FluidStack offer = this.legacy.copyWithAmount(Math.min(left, max - moved));
            int accepted = output.handler().fill(offer, IFluidHandler.FluidAction.SIMULATE);
            if (accepted <= 0) {
                continue;
            }
            int filled = output.handler().fill(offer.copyWithAmount(accepted),
                    IFluidHandler.FluidAction.EXECUTE);
            if (filled > 0) {
                left -= filled;
                moved += filled;
            }
        }
        this.legacy = left <= 0 ? FluidStack.EMPTY : this.legacy.copyWithAmount(left);
        return moved;
    }

    /**
     * 这一个目标**先试哪些流体**：
     *   ① 目标自己罐里已有的流体（它"需要"的就是这一种）；
     *   ② 再按源网络里出现的顺序补上别的（去重）。
     *
     * <p>顺序就是优先级：① 里的那种一定先喂 —— 一个装着 3000/4000 mB 氮气的罐只收氮气，
     * 先试氨气只会白问一轮。</p>
     */
    private List<Fluid> preferenceOrder(Target output, List<Target> sources, int maxInput) {
        List<Fluid> order = new ArrayList<>();
        for (int t = 0; t < output.handler().getTanks(); t++) {
            FluidStack held = output.handler().getFluidInTank(t);
            if (!held.isEmpty() && !order.contains(held.getFluid())) {
                order.add(held.getFluid());
            }
        }
        for (Target source : sources) {
            if (source.distance() > maxInput) {
                continue;
            }
            for (int t = 0; t < source.handler().getTanks(); t++) {
                FluidStack held = source.handler().getFluidInTank(t);
                if (!held.isEmpty() && !order.contains(held.getFluid())) {
                    order.add(held.getFluid());
                }
            }
        }
        return order;
    }

    /**
     * 把 {@code fluid} 从源网络搬进**这一个**目标，最多 {@code max} mB。
     *
     * <p>三步：① 先 SIMULATE 问目标收不收（收 0 = 这种流体它不要，立刻放弃这一种）；
     * ② 按它**答应收的量**去源那里抽；③ 灌进去。若实际灌进去的比抽出来的少，
     * <b>把多出来的塞回源里</b>（绝不凭空吞流体 —— 本工程的老规矩）。</p>
     */
    private int push(Target output, List<Target> sources, Fluid fluid, int max, int maxInput) {
        int moved = 0;
        for (Target source : sources) {
            if (moved >= max) {
                break;
            }
            if (source.distance() > maxInput) {
                continue;
            }
            for (int t = 0; t < source.handler().getTanks(); t++) {
                if (moved >= max) {
                    break;
                }
                FluidStack held = source.handler().getFluidInTank(t);
                if (held.isEmpty() || held.getFluid() != fluid) {
                    continue;                       // 这一格不是要找的那种流体
                }
                int want = Math.min(max - moved, held.getAmount());
                if (want <= 0) {
                    continue;
                }
                FluidStack offer = held.copyWithAmount(want);
                int accepted = output.handler().fill(offer, IFluidHandler.FluidAction.SIMULATE);
                if (accepted <= 0) {
                    return moved;                   // 目标不要这种流体 ⇒ 别再抽了
                }
                FluidStack drained = source.handler().drain(offer.copyWithAmount(accepted),
                        IFluidHandler.FluidAction.EXECUTE);
                if (drained.isEmpty()) {
                    continue;
                }
                int filled = output.handler().fill(drained, IFluidHandler.FluidAction.EXECUTE);
                if (filled < drained.getAmount()) {
                    // 刚 SIMULATE 过、理论上不会少；真少了就把多取的那点塞回源，绝不凭空吞
                    FluidStack back = drained.copyWithAmount(drained.getAmount() - Math.max(filled, 0));
                    source.handler().fill(back, IFluidHandler.FluidAction.EXECUTE);
                }
                moved += Math.max(filled, 0);
            }
        }
        return moved;
    }

    /** 搜索记录：distance = 途径的管道格数（紧贴泵面的容器/源方块 = 0，第一根管道 = 1） */
    private record Target(IFluidHandler handler, BlockPos pos, int distance) {
    }

    /**
     * 从一个紧贴泵面的方块出发：
     *  - 若它是管道 → 沿管道蔓延，把"从管道能摸到的流体容器"和"源头方块"都找出来；
     *  - 若它本身就是容器/源头方块（距离 0）→ 直接收。
     * allowWorldSources：输入端传 true（可吸水源/岩浆源），输出端传 false（不乱倒）。
     * 不穿过泵（对面的泵会作为"容器"被收进来 —— 泵接力、"速率相加"的来路）；
     * 不会把自己收进来（防自身循环）。
     */
    private List<Target> scan(Level level, BlockPos firstPos, Direction side, int range, boolean allowWorldSources) {
        List<Target> result = new ArrayList<>();
        Set<BlockPos> visited = new HashSet<>();
        Set<BlockPos> seenTargets = new HashSet<>();
        BlockPos selfPos = this.getBlockPos();

        if (!firstPos.equals(selfPos) && !(level.getBlockState(firstPos).getBlock() instanceof FluidPipeBlock)) {
            IFluidHandler direct = level.getCapability(Capabilities.FluidHandler.BLOCK, firstPos, side.getOpposite());
            if (direct != null) {
                if (seenTargets.add(firstPos)) {
                    result.add(new Target(direct, firstPos, 0));
                }
            } else if (allowWorldSources && isWorldSource(level, firstPos) && seenTargets.add(firstPos)) {
                result.add(new Target(new WorldFluidSourceHandler(level, firstPos, this.worldPumpProgress), firstPos, 0));
            }
        }

        if (!(level.getBlockState(firstPos).getBlock() instanceof FluidPipeBlock)) {
            result.sort(Comparator.comparingInt(Target::distance));
            return result;
        }

        record Node(BlockPos pos, int dist) {
        }
        List<Node> queue = new ArrayList<>();
        queue.add(new Node(firstPos, 1));
        visited.add(firstPos);
        for (int head = 0; head < queue.size(); head++) {
            Node node = queue.get(head);
            for (Direction dir : Direction.values()) {
                BlockPos next = node.pos().relative(dir);
                if (next.equals(selfPos) || !visited.add(next)) {
                    continue;
                }
                BlockState nextState = level.getBlockState(next);
                if (nextState.getBlock() instanceof FluidPipeBlock) {
                    if (node.dist() < range) {
                        queue.add(new Node(next, node.dist() + 1));
                    }
                } else if (seenTargets.add(next)) {
                    IFluidHandler handler = level.getCapability(Capabilities.FluidHandler.BLOCK, next, dir.getOpposite());
                    if (handler != null) {
                        result.add(new Target(handler, next, node.dist()));
                    } else if (allowWorldSources && isWorldSource(level, next)) {
                        result.add(new Target(new WorldFluidSourceHandler(level, next, this.worldPumpProgress), next, node.dist()));
                    }
                }
            }
        }
        result.sort(Comparator.comparingInt(Target::distance));
        return result;
    }

    /**
     * ★ 只认"液体方块本身"（Water/Lava 等 LiquidBlock 且为源液体）。
     * 含水方块（含水楼梯、含水管道、海草等）的流体状态也可能报"源水"，
     * 但它们不是液体——不吸，也避免"把方块整个删掉"的数据事故。
     */
    private static boolean isWorldSource(Level level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (!(state.getBlock() instanceof LiquidBlock)) {
            return false;
        }
        FluidState fluid = state.getFluidState();
        return !fluid.isEmpty() && fluid.isSource();
    }

    /**
     * 世界"源头方块"（水源、岩浆源等）的虚拟流体接口：
     * 一个源方块按 BLOCK_FLUID_AMOUNT = 1000 mB 计；抽满时把方块置为空气并清账。
     * 账本 key = 方块坐标，value = 已抽走的 mB —— 模拟/执行两步调用下也保证
     * "一个方块总共只出 1000 mB"；方块被换成别的东西时探测到就顺手清账（自愈）。
     */
    private static class WorldFluidSourceHandler implements IFluidHandler {

        private final Level level;
        private final BlockPos pos;
        private final Map<BlockPos, Integer> progress;

        WorldFluidSourceHandler(Level level, BlockPos pos, Map<BlockPos, Integer> progress) {
            this.level = level;
            this.pos = pos;
            this.progress = progress;
        }

        /** 当前该方块还能提供的流体（不可抽时 EMPTY 并清账） */
        private FluidStack remaining() {
            FluidState fluid = this.level.getFluidState(this.pos);
            if (fluid.isEmpty() || !fluid.isSource()) {
                this.progress.remove(this.pos);
                return FluidStack.EMPTY;
            }
            int taken = this.progress.getOrDefault(this.pos, 0);
            int left = BLOCK_FLUID_AMOUNT - taken;
            if (left <= 0) {
                this.progress.remove(this.pos);
                return FluidStack.EMPTY;
            }
            return new FluidStack(fluid.getType(), left);
        }

        @Override
        public int getTanks() {
            return 1;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return remaining();
        }

        @Override
        public int getTankCapacity(int tank) {
            return BLOCK_FLUID_AMOUNT;
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return false;   // 只能抽，不能倒
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
            FluidStack left = remaining();
            if (left.isEmpty() || left.getFluid() != resource.getFluid()) {
                return FluidStack.EMPTY;
            }
            return drainInternal(Math.min(resource.getAmount(), left.getAmount()), action);
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            FluidStack left = remaining();
            if (left.isEmpty() || maxDrain <= 0) {
                return FluidStack.EMPTY;
            }
            return drainInternal(Math.min(maxDrain, left.getAmount()), action);
        }

        private FluidStack drainInternal(int amount, FluidAction action) {
            FluidStack left = remaining();
            if (left.isEmpty() || amount <= 0) {
                return FluidStack.EMPTY;
            }
            Fluid fluid = left.getFluid();
            int taken = Math.min(amount, left.getAmount());
            if (action == FluidAction.SIMULATE) {
                return new FluidStack(fluid, taken);
            }
            // 执行前再确认方块还是该源流体（防中途被换掉）
            FluidState current = this.level.getFluidState(this.pos);
            if (current.isEmpty() || !current.isSource() || current.getType() != fluid) {
                this.progress.remove(this.pos);
                return FluidStack.EMPTY;
            }
            int total = this.progress.getOrDefault(this.pos, 0) + taken;
            if (total >= BLOCK_FLUID_AMOUNT) {
                this.progress.remove(this.pos);
                this.level.setBlock(this.pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
            } else {
                this.progress.put(this.pos, total);
            }
            return new FluidStack(fluid, taken);
        }
    }

    // ================== MenuProvider ==================
    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.fluid_pump");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new FluidPumpMenu(containerId, playerInventory, this);
    }

    // ================== 持久化 ==================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        // 注意顺序：先读速率，再按"该速率下的实际缓冲"夹存量
        this.rate = Mth.clamp(tag.getInt("rate"), 0, MAX_RATE);
        this.energy = Mth.clamp(tag.getInt("energy"), 0, effectiveCapacity());
        // ★ 0.11 ZF98：泵不再有内部罐。旧存档里的 `"tank"` 标签（ZF98 之前写的）现在只当成
        //   "待倒空的遗留"接住 —— 不丢掉玩家东西，工作一 tick 就吐进目标网络。
        this.legacy = FluidStack.EMPTY;
        CompoundTag oldTank = tag.getCompound("tank");
        if (!oldTank.isEmpty()) {
            FluidTank probe = new FluidTank(LEGACY_TANK_CAPACITY);
            probe.readFromNBT(registries, oldTank);
            if (!probe.isEmpty()) {
                this.legacy = probe.getFluid().copy();
            }
        }
        this.worldPumpProgress.clear();
        ListTag list = tag.getList("world_pump", Tag.TAG_COMPOUND);
        for (int i = 0; i < list.size(); i++) {
            CompoundTag entry = list.getCompound(i);
            BlockPos pos = new BlockPos(entry.getInt("x"), entry.getInt("y"), entry.getInt("z"));
            int taken = entry.getInt("taken");
            if (taken > 0 && taken < BLOCK_FLUID_AMOUNT) {
                this.worldPumpProgress.put(pos, taken);
            }
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("rate", this.rate);
        // ⚠ 不再写 `"tank"`（泵没有内部罐了）。只在**旧存档遗留还没倒完**时写 "legacy"，
        //   倒干净之后这个键就是空的 —— 新存档里泵不存任何流体。
        if (!this.legacy.isEmpty()) {
            FluidTank probe = new FluidTank(LEGACY_TANK_CAPACITY);
            probe.fill(this.legacy, IFluidHandler.FluidAction.EXECUTE);
            tag.put("legacy", probe.writeToNBT(registries, new CompoundTag()));
        }
        ListTag list = new ListTag();
        for (Map.Entry<BlockPos, Integer> entry : this.worldPumpProgress.entrySet()) {
            CompoundTag e = new CompoundTag();
            e.putInt("x", entry.getKey().getX());
            e.putInt("y", entry.getKey().getY());
            e.putInt("z", entry.getKey().getZ());
            e.putInt("taken", entry.getValue());
            list.add(e);
        }
        tag.put("world_pump", list);
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