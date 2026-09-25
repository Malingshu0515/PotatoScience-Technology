package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChainBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;

/**
 * 采油机的方块实体（0.11 ZF109）。
 *
 * <p><b>用户原话（逐条落实）：</b></p>
 * <pre>
 *   「在海洋油田群系工作
 *     gui为一个大罐子25B储量（不是那种竖直的了 是一个横过来的矩形罐子）和一个工作指示灯
 *     能量条不需要 下方必须有水源方块 检测下方连接的 含水锁链的数量
 *     耗能公式为 80n*1/10n+80n FE/t 原油获取为 10n mb/s （n为下方含水锁链个数）
 *     每开采25~80桶原油 附近10*10的海洋油桶群系会变成符合旁边群系的海洋（冻洋 暖洋 温带海洋...）」
 * </pre>
 *
 * <p><b>① 耗能公式的读法是用户拍板的</b>（原话给了三种可能，我列了数值表让他选）：
 * 选的是 <b>B = 从左到右算 {@code 80×n×1÷10×n} ⇒ 8n² + 80n FE/t</b>
 * （n=1/2/3/10 → 88 / 192 / 312 / 1600）。见 {@link #fePerTick(int)}。</p>
 *
 * <p><b>② 转化范围也是用户拍板的</b>：{@code 10*10} = <b>10×10 个区块</b>
 * （以机器为中心 160×160 格），不是 100 格方块。见 {@link #CONVERT_CHUNKS}。</p>
 *
 * <p><b>③ n 怎么数</b>（把"下方必须有水源方块"和"含水锁链"两条合成一次下探）：
 * 从机器正下方那格开始一格一格往下走，<b>只要这一格的流体状态是水源</b>就继续走、
 * 一旦不是就停（干的锁链、石头、空气都算断）。走的过程中：
 * <ul>
 *   <li>是原版锁链且 {@code waterlogged=true} ⇒ <b>n + 1</b>（这就是"含水锁链"）；</li>
 *   <li>是普通水源方块 ⇒ n 不加，但它让这一格算"有水"（所以"下方必须有水源方块"是
 *       <b>由构造保证的</b>：整段必须全是有水的格子，机器站在干地上一定 n = 0）。</li>
 * </ul>
 * ⚠ 一个细节：含水锁链的流体状态本来就是<b>水源</b>（原版 waterlogged 给的就是 source），
 * 所以"上面挂着锁链"和"下面是水"这两条不冲突 —— 玩家从机器正下方直接挂链子下水也能开工。</p>
 *
 * <p><b>④ 只在海洋油田群系开工</b>：每 tick 读一次自己脚下的群系
 * （{@code Level#getBiome}），不是 {@code potato_s_t:ocean_oilfield} 就黄灯停机（状态码 15）。</p>
 *
 * <p><b>⑤ 抽干油田</b>：本机累计采出的油每够一次"欠账"（25~80 桶，每次随机）
 * 就把<b>以自己为中心的 10×10 区块</b>里所有"海洋油田"格子改成<b>旁边那种海洋群系</b>
 * （冻洋/暖洋/温带海洋…由周边群系投票决定，见 {@link OilfieldDepletion}）。
 * ⚠ 因为这 100 个区块<b>包含机器自己所在的那一格</b>，所以<b>转化完成后这台机器会立刻停机</b>
 * —— 要接着抽得把它挪到还剩油田的地方。这是用户拍板时明确接受的行为（原话选项：
 * "转换后油机会因为不再是油田而停机，等于把油田抽干"）。</p>
 */
public class OilPumpBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数（一个都没改） =================

    /** 用户原话「一个大罐子25B储量」⇒ 25 桶 × 1000 mB */
    public static final int TANK_CAPACITY = 25 * 1000;
    /** 用户原话「原油获取为 10n mb/s」 */
    public static final int MB_PER_SECOND_PER_CHAIN = 10;
    /** 用户原话「每开采25~80桶原油」——下限（桶） */
    public static final int DEBT_MIN_BUCKETS = 25;
    /** 上限（桶）；每次到点后重新在 25~80 之间抽一个 */
    public static final int DEBT_MAX_BUCKETS = 80;
    /** 用户原话「附近10*10的…群系」+ 拍板"区块"⇒ 10×10 个区块 */
    public static final int CONVERT_CHUNKS = 10;

    // ================= 我定的数（用户没给；要改都是一行） =================

    /**
     * 储能。用户<b>没给</b>这个数（他只说了"能量条不需要"，那是界面的事）。
     * 取 <b>32768</b>：与本工程合金冶炼炉同一个数（现有机器里最大的缓冲），
     * n=10（1600 FE/t）时够撑 20 秒。
     */
    public static final int MAX_ENERGY = 32768;
    /**
     * 下探最多扫几格。用户<b>没给</b>。取 64：比任何一片海的深度都深，
     * 又让 n 有上界（n=64 时 37888 FE/t，还在 int 里）。
     */
    public static final int MAX_CHAIN_SCAN = 64;
    /**
     * 每几 tick 重扫一次结构。用户<b>没给</b>。取 20（= 1 秒）：
     * 产量本来就是"每秒"的量，扫描跟着秒走最自然，也不会每 tick 去数 64 格。
     */
    public static final int SCAN_INTERVAL = 20;

    /** 这台机器**没有物品槽**（用户只点名了罐子和灯）。 */
    public static final int SLOT_COUNT = 0;

    // ================= 状态灯（沿用共享状态码，新起两个号） =================

    /** 有红石信号 = 关机 */
    public static final int STATUS_DISABLED = 0;
    /** 电力不足（每 tick 8n²+80n FE） */
    public static final int STATUS_NO_POWER = 3;
    /** 罐满了（25B 装不下） */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在采油 */
    public static final int STATUS_RUNNING = 5;
    /**
     * 15 = <b>不在海洋油田群系</b>（0.11 ZF109 新起）。
     * 旧的 2 号是"无效"，在这台机器上说不清是"群系不对"还是别的；这台机器的头号
     * 故障就是这个，所以另起一号（照 ZF96/ZF97 那条"先看能不能共用、不能就新起"的规矩）。
     */
    public static final int STATUS_NOT_OILFIELD = 15;
    /** 16 = <b>下方没有含水锁链</b>（0.11 ZF109 新起；扫到的 n = 0 时用它） */
    public static final int STATUS_NO_CHAIN = 16;

    // ================= 容器同步（ContainerData） =================

    public static final int DATA_STATUS = 0;
    public static final int DATA_ENERGY = 1;
    /** 罐里有多少原油（≤25000 ⇒ 不用分片，§4.48） */
    public static final int DATA_OIL = 2;
    /** n */
    public static final int DATA_CHAINS = 3;
    public static final int DATA_COUNT = 4;

    // ================= 字段 =================

    private int energy;
    /** 服务端每 tick 刷新，仅供界面（不存盘也存，读档瞬间灯不会跳） */
    private int status = STATUS_NO_CHAIN;
    /** n：下方含水锁链根数（缓存，每 {@link #SCAN_INTERVAL} tick 重扫） */
    private int chains;
    /** 不足 1 mB 的零头（n/2 mB/t 天然是分数） */
    private int mbAccum;
    /** 本机累计采出多少 mB（算"欠账"用） */
    private long pumpedMb;
    /** 下一次触发的门槛（mB）；≤0 表示还没抽过 */
    private int convertAtMb;
    /** 扫描节拍器（不存盘：读档后最多晚 1 秒重扫） */
    private int scanTimer;

    private final FluidTank tank = new FluidTank(TANK_CAPACITY,
            stack -> stack != null && !stack.isEmpty()
                    && stack.getFluid().getFluidType() == ModFluids.CRUDE_OIL_TYPE.get());

    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                this.setChanged();
            });

    /**
     * 单罐流体接口：<b>只抽不灌</b>。
     *
     * <p>这台机器是<b>产油</b>的（不是储油罐）：管道 / 流体泵能把它抽走，
     * 但一滴都灌不进来 —— 否则玩家会拿它当 25B 的通用储罐用。
     * 与空气分离器那两个"只出不进"的罐同一条规矩。</p>
     */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return 1;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return OilPumpBlockEntity.this.tank.getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return TANK_CAPACITY;
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return false;                     // 只出不进
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
            FluidStack held = OilPumpBlockEntity.this.tank.getFluid();
            if (held.isEmpty() || !FluidStack.isSameFluidSameComponents(held, resource)) {
                return FluidStack.EMPTY;
            }
            return OilPumpBlockEntity.this.tank.drain(resource.getAmount(), action);
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            return OilPumpBlockEntity.this.tank.drain(maxDrain, action);
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_STATUS -> status;
                case DATA_ENERGY -> energy;
                case DATA_OIL -> tank.getFluidAmount();
                case DATA_CHAINS -> chains;
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

    public OilPumpBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.OIL_PUMP_BE.get(), pos, state);
    }

    // ================= 公式（界面与探针共用；用户拍板的 B 读法） =================

    /**
     * 耗能公式：用户原话「80n*1/10n+80n FE/t」，按<b>从左到右</b>算
     * （{@code 80×n×1÷10×n + 80×n}）= <b>8n² + 80n</b>。
     *
     * <p>n = 0/1/2/3/10/64 → 0 / 88 / 192 / 312 / 1600 / 37888 FE/t。
     * n 有上界 {@link #MAX_CHAIN_SCAN} = 64 ⇒ 不会溢出 int。</p>
     */
    public static int fePerTick(int chains) {
        return 8 * chains * chains + 80 * chains;
    }

    /** 产量：用户原话「原油获取为 10n mb/s」。 */
    public static int mbPerSecond(int chains) {
        return MB_PER_SECOND_PER_CHAIN * chains;
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, OilPumpBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
        }
    }

    private void serverTick() {
        if (!(this.level instanceof ServerLevel server)) {
            return;
        }
        // ① 红石信号 = 关机
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.status = STATUS_DISABLED;
            return;
        }
        // ② 只在海洋油田群系开工
        if (!server.getBiome(this.worldPosition).is(SaltyRiverBiomeSource.OCEAN_OILFIELD)) {
            this.status = STATUS_NOT_OILFIELD;
            return;
        }
        // ③ 结构：往下数含水锁链（每秒重扫一次）
        if (--this.scanTimer <= 0) {
            this.scanTimer = SCAN_INTERVAL;
            this.rescanStructure();
        }
        int n = this.chains;
        if (n <= 0) {
            this.status = STATUS_NO_CHAIN;
            return;
        }
        // ④ 罐满了就原地等（不扣电、零头留着）
        int space = TANK_CAPACITY - this.tank.getFluidAmount();
        if (space <= 0) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }
        // ⑤ 付电
        int cost = fePerTick(n);
        if (this.energy < cost) {
            this.status = STATUS_NO_POWER;
            return;
        }
        this.energy -= cost;
        this.status = STATUS_RUNNING;

        // ⑥ 出油：每 tick 攒 n 个"半点" ⇒ n/2 mB/t = 10n mB/s（整数运算，不丢精度）
        if (this.mbAccum > 2 * (space + 1)) {
            this.mbAccum = 2 * (space + 1);      // 罐快满时别把零头攒成雪球
        }
        this.mbAccum += n;
        int want = this.mbAccum / 2;
        if (want > 0) {
            int made = Math.min(want, space);
            this.tank.fill(new FluidStack(ModFluids.CRUDE_OIL.get(), made),
                    IFluidHandler.FluidAction.EXECUTE);
            this.mbAccum -= made * 2;
            this.pumpedMb += made;
        }

        // ⑦ 欠账到点 ⇒ 把这一片海洋油田变成旁边的海洋
        if (this.convertAtMb <= 0) {
            this.convertAtMb = this.rollConvertThreshold();
        }
        if (this.pumpedMb >= this.convertAtMb) {
            this.pumpedMb -= this.convertAtMb;
            this.convertAtMb = this.rollConvertThreshold();
            OilfieldDepletion.convertAround(server, this.worldPosition, CONVERT_CHUNKS);
        }
        setChanged();
    }

    /** 抽一个 25~80 桶的门槛（含两端）。 */
    private int rollConvertThreshold() {
        int buckets = DEBT_MIN_BUCKETS
                + this.level.random.nextInt(DEBT_MAX_BUCKETS - DEBT_MIN_BUCKETS + 1);
        return buckets * 1000;
    }

    /**
     * 往下数含水锁链（见类注释 ③）。
     *
     * <p>只看流体状态是"水源"的格子：原版纯水方块、含水锁链都是水源；
     * 干锁链 / 石头 / 空气都会让下探当场停住。</p>
     */
    private void rescanStructure() {
        int n = 0;
        BlockPos p = this.worldPosition.below();
        for (int i = 0; i < MAX_CHAIN_SCAN; i++) {
            BlockState state = this.level.getBlockState(p);
            FluidState fluid = state.getFluidState();
            if (fluid.isEmpty() || !fluid.isSource() || !fluid.getType().isSame(Fluids.WATER)) {
                break;
            }
            if (state.is(Blocks.CHAIN) && state.getValue(ChainBlock.WATERLOGGED)) {
                n++;
            }
            p = p.below();
        }
        this.chains = n;
    }

    // ================= 读数（界面 / 探针共用） =================

    public int getEnergy() {
        return this.energy;
    }

    public int getStatus() {
        return this.status;
    }

    /** n：下方含水锁链根数 */
    public int getChains() {
        return this.chains;
    }

    public int getOil() {
        return this.tank.getFluidAmount();
    }

    public long getPumpedMb() {
        return this.pumpedMb;
    }

    public int getConvertAtMb() {
        return this.convertAtMb;
    }

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

    /** 探针用：立刻按当前世界状态重扫一次并返回 n。 */
    public int rescanNow() {
        this.rescanStructure();
        return this.chains;
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.oil_pump");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new OilPumpMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.status = tag.contains("status") ? tag.getInt("status") : STATUS_NO_CHAIN;
        this.mbAccum = tag.getInt("mbAccum");
        this.pumpedMb = tag.getLong("pumpedMb");
        this.convertAtMb = tag.getInt("convertAtMb");
        this.tank.readFromNBT(registries, tag.getCompound("Tank"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("status", this.status);
        tag.putInt("mbAccum", this.mbAccum);
        tag.putLong("pumpedMb", this.pumpedMb);
        tag.putInt("convertAtMb", this.convertAtMb);
        // ⚠ 必须自己 new 一个子标签再 put 回去（§4.49）
        CompoundTag child = new CompoundTag();
        this.tank.writeToNBT(registries, child);
        tag.put("Tank", child);
    }
}
