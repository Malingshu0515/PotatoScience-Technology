package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;

/**
 * 空气分离器的方块实体（0.11 ZF97）。
 *
 * <p><b>用户原话（逐条落实）：</b></p>
 * <pre>
 *   「空气分离器：gui只有两个储罐（不接受被灌入 只能泵出）一个工作指示灯
 *     储能5000fe 耗能 200fe/t 30s产出 8mB 氮气 2mB氧气」
 * </pre>
 * ⇒ 一批（30 秒 = 600 tick）：消耗 200 FE/t × 600 = <b>120,000 FE</b>，
 * 产出 <b>8 mB 氮气 + 2 mB 氧气</b>（进 0 出 10 —— 原料是空气，白拿）。
 *
 * <p><b>两个储罐只出不进</b>：{@code fill()} 一律返回 0（管道/泵/手倒都灌不进去），
 * {@code drain()} 按「氮气 → 氧气」的顺序抽。这是用户明确点名的行为，不是漏写。</p>
 *
 * <p><b>这台机器没有物品槽</b>（{@value #SLOT_COUNT} = 0）：界面里只有两个储罐 +
 * 一盏状态灯（用户原话「gui只有两个储罐…一个工作指示灯」）。所以它<b>没有</b>物品栏能力，
 * 破坏时也没有内容物要掉。</p>
 *
 * <p><b>红石信号 = 关机</b>（进度保留）—— 与本工程其它机器一致；用户没提红石，
 * 这条是照惯例来的，要改成"有信号才跑"是一行。</p>
 */
public class AirSeparatorBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数 =================

    /** 储能（用户原话「储能5000fe」） */
    public static final int MAX_ENERGY = 5000;
    /** 耗能（用户原话「耗能 200fe/t」） */
    public static final int ENERGY_PER_TICK = 200;
    /** 一批要多久（用户原话「30s」= 600 tick） */
    public static final int DURATION_TICKS = 30 * 20;
    /** 一批出多少氮气（用户原话「30s产出 8mB 氮气」） */
    public static final int NITROGEN_PER_BATCH = 8;
    /** 一批出多少氧气（用户原话「2mB氧气」） */
    public static final int OXYGEN_PER_BATCH = 2;

    /**
     * 每个储罐的容量 —— <b>用户没给这个数</b>，我按 4000 mB 取。
     *
     * <p>理由：一个灌满的高压气罐是 3500 mB（{@code TankContents.CAPACITY}），
     * 4000 刚好能把整罐接下来、又不用为了"接一罐"把机器做得特别大；
     * 与本轮另一台机器（加氢脱硫反应仓的氢气罐）同一个数。
     * <b>要改是一个常量。</b></p>
     */
    public static final int TANK_CAPACITY = 4000;

    /** 这台机器**没有物品槽**（用户原话「gui只有两个储罐…一个工作指示灯」）。 */
    public static final int SLOT_COUNT = 0;

    // ================= 两个储罐 =================

    public static final int TANK_COUNT = 2;
    /** 氮气（先抽的那一个） */
    public static final int TANK_NITROGEN = 0;
    /** 氧气 */
    public static final int TANK_OXYGEN = 1;

    private static final String[] TANK_KEYS = {"Nitrogen", "Oxygen"};

    // ================= 状态灯（沿用共享状态码，不新增） =================

    /** 有红石信号 = 关机 */
    public static final int STATUS_DISABLED = 0;
    /** 电不够（每 tick 200 FE） */
    public static final int STATUS_NO_POWER = 3;
    /** 两个储罐里有一个装不下这一批了 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在分离空气 */
    public static final int STATUS_RUNNING = 5;

    // ================= 工作时的白烟（0.11 ZF99） =================

    /**
     * 工作时每几 tick 冒一次烟（用户原话「空气分离器工作时加一点白色的烟雾粒子」）。
     *
     * <p>5 tick = 每秒 4 次、每次 3 粒 ⇒ 约 12 粒/秒。这个量在"看得出在冒烟"和
     * "不挡视线、不费性能"之间；要更淡/更浓就调这两个常量（以及 {@link #PARTICLE_SPREAD}）。</p>
     */
    public static final int PARTICLE_INTERVAL = 5;
    /** 一次冒几粒 */
    public static final int PARTICLES_PER_EMIT = 3;
    /** 粒子在顶面铺开的半径（格） */
    public static final double PARTICLE_SPREAD = 0.3;
    /** 粒子初速（0 = 原地散开；给一点点让它慢慢往上散） */
    public static final double PARTICLE_SPEED = 0.01;

    // ================= 容器同步（ContainerData） =================

    public static final int DATA_ENERGY = 0;
    public static final int DATA_PROGRESS = 1;
    public static final int DATA_PROGRESS_MAX = 2;
    public static final int DATA_STATUS = 3;
    /** 氮气量（≤4000 ⇒ 不用分片，§4.48） */
    public static final int DATA_NITROGEN = 4;
    /** 氧气量 */
    public static final int DATA_OXYGEN = 5;
    public static final int DATA_COUNT = 6;

    private int energy;
    private int progress;
    private int progressMax = DURATION_TICKS;
    /** 服务端每 tick 刷新，仅供界面（不存盘） */
    private int status = STATUS_RUNNING;
    /** 白烟的节拍器（不存盘：读档后最多晚 {@link #PARTICLE_INTERVAL} tick 冒第一缕） */
    private int particleTimer;

    private final FluidTank[] tanks = new FluidTank[TANK_COUNT];

    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                this.setChanged();
            });

    /**
     * 六面流体接口：<b>只抽不灌</b>（用户原话「不接受被灌入 只能泵出」）。
     *
     * <p>{@code fill} 恒定 0、{@code drain} 按氮气 → 氧气的顺序抽 —— 泵接上来就能抽走，
     * 想往回灌一滴都灌不进。</p>
     */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return TANK_COUNT;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return AirSeparatorBlockEntity.this.tanks[tank].getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return AirSeparatorBlockEntity.this.tanks[tank].getCapacity();
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return false;                     // 见类注释：这两个罐只出不进
        }

        @Override
        public int fill(FluidStack resource, FluidAction action) {
            return 0;                         // 用户原话「不接受被灌入」
        }

        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            if (resource.isEmpty()) {
                return FluidStack.EMPTY;
            }
            for (FluidTank tank : AirSeparatorBlockEntity.this.tanks) {
                FluidStack held = tank.getFluid();
                if (!held.isEmpty() && FluidStack.isSameFluidSameComponents(held, resource)) {
                    return tank.drain(resource.getAmount(), action);
                }
            }
            return FluidStack.EMPTY;
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            for (FluidTank tank : AirSeparatorBlockEntity.this.tanks) {
                if (tank.getFluidAmount() > 0) {
                    return tank.drain(maxDrain, action);
                }
            }
            return FluidStack.EMPTY;
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_ENERGY -> energy;
                case DATA_PROGRESS -> progress;
                case DATA_PROGRESS_MAX -> progressMax;
                case DATA_STATUS -> status;
                case DATA_NITROGEN -> tanks[TANK_NITROGEN].getFluidAmount();
                case DATA_OXYGEN -> tanks[TANK_OXYGEN].getFluidAmount();
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

    public AirSeparatorBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.AIR_SEPARATOR_BE.get(), pos, state);
        // 两个罐都按**流体类型**认（source/flowing 两个本体都收）
        this.tanks[TANK_NITROGEN] = new FluidTank(TANK_CAPACITY,
                stack -> isType(stack, ModFluids.NITROGEN_TYPE.get()));
        this.tanks[TANK_OXYGEN] = new FluidTank(TANK_CAPACITY,
                stack -> isType(stack, ModFluids.OXYGEN_TYPE.get()));
    }

    private static boolean isType(FluidStack stack, net.neoforged.neoforge.fluids.FluidType type) {
        return stack != null && !stack.isEmpty() && stack.getFluid().getFluidType() == type;
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

    public static void tick(Level level, BlockPos pos, BlockState state, AirSeparatorBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
        }
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }
        this.progressMax = DURATION_TICKS;

        // ① 红石信号 = 关机（进度保留）
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.status = STATUS_DISABLED;
            return;
        }
        // ② 两个罐都得装得下这一批（装不下就原地等，电与进度都留着）
        if (!hasRoomForBatch()) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }
        // ③ 付电
        if (this.energy < ENERGY_PER_TICK) {
            this.status = STATUS_NO_POWER;
            return;
        }
        this.energy -= ENERGY_PER_TICK;
        this.progress++;
        this.status = STATUS_RUNNING;

        // ★ 0.11 ZF99：真干活时才冒白烟（缺电/储罐满/红石停机那几条岔路都提前 return 了，
        //   所以粒子天然只在"正在分离空气"时出现 —— 用户原话「工作时加一点白色的烟雾粒子」）
        if (--this.particleTimer <= 0) {
            this.particleTimer = PARTICLE_INTERVAL;
            spawnWorkParticles();
        }

        // ④ 到点结算：一批 8 mB 氮气 + 2 mB 氧气
        if (this.progress >= DURATION_TICKS) {
            this.progress = 0;
            this.tanks[TANK_NITROGEN].fill(new FluidStack(ModFluids.NITROGEN.get(), NITROGEN_PER_BATCH),
                    IFluidHandler.FluidAction.EXECUTE);
            this.tanks[TANK_OXYGEN].fill(new FluidStack(ModFluids.OXYGEN.get(), OXYGEN_PER_BATCH),
                    IFluidHandler.FluidAction.EXECUTE);
        }
        setChanged();
    }

    /** 两个罐都还装得下**一整批**吗（氮 8 / 氧 2）。 */
    private boolean hasRoomForBatch() {
        return this.tanks[TANK_NITROGEN].getSpace() >= NITROGEN_PER_BATCH
                && this.tanks[TANK_OXYGEN].getSpace() >= OXYGEN_PER_BATCH;
    }

    /**
     * 工作时从顶面冒几缕**白色烟雾**（0.11 ZF99，用户原话「空气分离器工作时加一点白色的烟雾粒子」）。
     *
     * <p>用原版 {@code ParticleTypes.CLOUD}（白色烟团）。这是本工程**第一次用粒子**，
     * 两条要点记在这里，也写进了档案 §4.67：</p>
     * <ul>
     *   <li><b>必须在服务端发</b>：{@code Level#addParticle} 在服务端是**空操作**（只有客户端会画），
     *       而这台机器只跑服务端 tick ⇒ 只能走 {@code ServerLevel#sendParticles}，
     *       由服务端广播给附近的玩家（原版自带距离裁剪）；</li>
     *   <li><b>只管"发"、不管"画"</b>：粒子由原版客户端渲染，不需要我们写渲染器/注册任何东西。</li>
     * </ul>
     */
    private void spawnWorkParticles() {
        if (!(this.level instanceof ServerLevel server)) {
            return;                        // 双保险：客户端就算调到也不画（见上面第 ① 条）
        }
        double x = this.worldPosition.getX() + 0.5;
        double y = this.worldPosition.getY() + 1.05;      // 顶面略高一点点，像从机顶冒出来
        double z = this.worldPosition.getZ() + 0.5;
        // 参数顺序：类型 / 坐标 / 数量 / 三个方向的随机铺开 / 初速
        server.sendParticles(ParticleTypes.CLOUD, x, y, z, PARTICLES_PER_EMIT,
                PARTICLE_SPREAD, 0.02, PARTICLE_SPREAD, PARTICLE_SPEED);
    }

    // ================= 读数（界面 / 探针共用） =================

    public int getEnergy() {
        return this.energy;
    }

    public int getProgress() {
        return this.progress;
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
        return Component.translatable("block.potato_s_t.air_separator");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new AirSeparatorMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.progress = tag.getInt("progress");
        this.status = tag.getInt("status");
        for (int i = 0; i < TANK_COUNT; i++) {
            this.tanks[i].readFromNBT(registries, tag.getCompound(TANK_KEYS[i]));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("progress", this.progress);
        tag.putInt("status", this.status);
        for (int i = 0; i < TANK_COUNT; i++) {
            // ⚠ 必须自己 new 一个子标签再 put 回去（§4.49）
            CompoundTag child = new CompoundTag();
            this.tanks[i].writeToNBT(registries, child);
            tag.put(TANK_KEYS[i], child);
        }
    }
}
