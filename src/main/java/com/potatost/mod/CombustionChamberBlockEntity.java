package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 燃烧反应室的方块实体（0.11 ZF100）。
 *
 * <p><b>用户原话（逐条落实）：</b></p>
 * <pre>
 *   「加一个燃烧反应室（配方；【】【高压气罐】【】，【散热装置】【铁板】【耐热金属块】，
 *     【电容】【加热装置】【打火石】） 一个二氧化碳罐10000mB（输出） 一个氧气罐1200mb（为必须输入端）
 *     一个其他产物罐（目前配方只有水） 一个其他产物槽（燃烧副产物） 一个燃料槽
 *     可以放入原版所有可以被熔炉识别的燃料（一桶岩浆可反应10s 其余皆为3s）
 *     消耗一份燃料和10mB氧气开始反应 开始反应后有黑色的烟粒子产生
 *     所有原木单个反应后生成10mB二氧化碳 1个木炭 一桶柴油/汽油反应30s 产生200mB二氧化碳 50mB水
 *     其余物品只产出5mb二氧化碳 所有燃料反应后 燃烧反应室产出800点动力 可被 动力能源捕获器识别
 *     其中柴油为1200点动力」
 * </pre>
 *
 * <p><b>用户后来当场拍板的两条</b>（我问了才动手）：</p>
 * <ol>
 *   <li>动力是<b>「反应期间每 tick +800」</b>（不是"一次反应给一坨"）—— 由
 *       {@link PowerCapturerBlockEntity} 的 6 面扫描把本机器当成一台"超强火炉"识别
 *       （火炉 +8/t、高炉 +16/t，本机 +800/t）；汽油给 <b>1000</b>（用户原话「1000吧」）。</li>
 *   <li>所以三个动力档：<b>柴油 1200 / 汽油 1000 / 其余 800</b>。</li>
 * </ol>
 *
 * <p><b>三个罐的角色</b>（照用户给的方向，一处都不能反）：</p>
 * <ul>
 *   <li>0 号<b>氧气罐</b> 1200 mB：<b>只进不出</b>（"必须输入端"）—— 管道/泵能灌进来、
 *       手里拿装氧气的气罐右键也能倒；机器永远不会把它抽出去；</li>
 *   <li>1 号<b>二氧化碳罐</b> 10000 mB：<b>只出不进</b>（"输出"）—— 接泵/管道抽走；</li>
 *   <li>2 号<b>其他产物罐</b> 4000 mB：同样只出不进，目前配方只产<b>水</b>。</li>
 * </ul>
 * ⚠ 2 号罐的容量<b>用户没给</b>，我按本工程其它机器的惯例取 4000 mB（与加氢脱硫反应仓/氨气组成室同档）。
 *
 * <p><b>这台机器不吃电</b>：用户没给能耗数 ⇒ 不耗电（与加氢脱硫反应仓 ZF96 同一条先例：
 * 没给的数不自己发明）。它<b>产出的是"动力"</b>（Power），由相邻的动力能源捕获器采集，
 * 这条路与本模组既有的"火炉/高炉/流水 ⇒ 捕获器 ⇒ 端子 ⇒ 发电机 ⇒ FE"完全同源。</p>
 *
 * <p><b>燃料怎么认</b>：{@code ItemStack#getBurnTime(RecipeType.SMELTING) > 0} = <b>原版熔炉认的燃料</b>
 * （煤/木炭/木板/木棍/岩浆桶/烈焰棒/干海带块…），再额外认本模组的柴油桶与汽油桶
 * （它们是本模组物品，原版当然不认识）。</p>
 *
 * <p><b>三条硬规矩（照抄本工程踩平过的那几套）：</b></p>
 * <ol>
 *   <li><b>结算前先看放不放得下</b>：二氧化碳罐 / 水罐 / 副产物槽任何一处放不下 ⇒
 *       停在最后一 tick <b>等</b>，产物一件不丢（§4.14 的原事故：扣了输入却没落产物 = 吞东西）；</li>
 *   <li><b>燃料与氧气在"开始反应"那一刻就扣掉</b>（用户原话「消耗一份燃料和10mB氧气开始反应」）
 *       ⇒ 中途被拆机/停机，这一份就没了 —— 这是用户指定的语义，不是漏洞；</li>
 *   <li><b>反应档案在开始时定死并存盘</b>：中途换燃料不会改变这一批的产物与动力
 *       （否则"最后 1 tick 换成柴油"就能白拿 200 mB 二氧化碳 + 50 mB 水 + 1200 动力）。</li>
 * </ol>
 */
public class CombustionChamberBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数 =================

    /** 开始反应要多少 mB 氧气（用户原话「消耗一份燃料和10mB氧气开始反应」） */
    public static final int OXYGEN_PER_OPERATION = 10;
    /** 原木：一次反应出多少 mB 二氧化碳（用户原话「所有原木单个反应后生成10mB二氧化碳」） */
    public static final int CO2_PER_LOG = 10;
    /** 原木：一次反应出几个木炭（用户原话「1个木炭」） */
    public static final int CHARCOAL_PER_LOG = 1;
    /** 一桶柴油/汽油：出多少 mB 二氧化碳（用户原话「产生200mB二氧化碳」） */
    public static final int CO2_PER_LIQUID_FUEL = 200;
    /** 一桶柴油/汽油：出多少 mB 水（用户原话「50mB水」） */
    public static final int WATER_PER_LIQUID_FUEL = 50;
    /** 其余物品：只出 5 mB 二氧化碳（用户原话「其余物品只产出5mb二氧化碳」） */
    public static final int CO2_PER_FUEL = 5;

    /** 默认反应时长 3 秒（用户原话「其余皆为3s」） */
    public static final int DURATION_DEFAULT = 3 * 20;
    /** 一桶岩浆 10 秒（用户原话「一桶岩浆可反应10s」） */
    public static final int DURATION_LAVA = 10 * 20;
    /** 一桶柴油/汽油 30 秒（用户原话「一桶柴油/汽油反应30s」） */
    public static final int DURATION_LIQUID_FUEL = 30 * 20;

    /** 动力：默认每 tick 800 点（用户原话「产出800点动力」） */
    public static final int POWER_DEFAULT = 800;
    /** 动力：柴油每 tick 1200 点（用户原话「其中柴油为1200点动力」） */
    public static final int POWER_DIESEL = 1200;
    /** 动力：汽油每 tick 1000 点（用户当场拍板「1000吧」） */
    public static final int POWER_GASOLINE = 1000;

    /** 氧气罐 1200 mB（用户原话「一个氧气罐1200mb」） */
    public static final int OXYGEN_CAPACITY = 1200;
    /** 二氧化碳罐 10000 mB（用户原话「一个二氧化碳罐10000mB」） */
    public static final int CO2_CAPACITY = 10000;
    /** 其他产物罐 4000 mB —— ⚠ **用户没给这个数**，按本工程其它机器的惯例取 4 批的余量 */
    public static final int WATER_CAPACITY = 4000;

    /** 手倒：手里拿着装氧气的容器右键机器，一次最多倒进去多少 mB */
    public static final int POUR_PER_CLICK = 1000;

    // ================= 黑烟粒子（用户原话「开始反应后有黑色的烟粒子产生」） =================

    /** 每隔几 tick 冒一次（照 ZF99 那台机器的口径，5 tick = 每秒 4 次） */
    public static final int PARTICLE_INTERVAL = 5;
    /** 每次几粒 */
    public static final int PARTICLES_PER_EMIT = 3;
    /** 铺开半径 */
    public static final double PARTICLE_SPREAD = 0.3;
    /** 初速 */
    public static final double PARTICLE_SPEED = 0.01;

    // ================= 罐 / 槽 =================

    public static final int TANK_OXYGEN = 0;
    public static final int TANK_CO2 = 1;
    public static final int TANK_WATER = 2;
    public static final int TANK_COUNT = 3;

    /** 燃料槽（界面左边那个） */
    public static final int FUEL_SLOT = 0;
    /** 燃烧副产物槽（木炭 / 空桶） */
    public static final int BYPRODUCT_SLOT = 1;
    public static final int SLOT_COUNT = 2;

    // ================= 状态灯（共享命名空间，取值与其它机器对齐） =================

    /** 有红石信号 = 关机（与其它机器一致） */
    public static final int STATUS_DISABLED = 0;
    /** 燃料槽是空的 */
    public static final int STATUS_EMPTY = 1;
    /** 燃料槽里那个东西不是燃料 */
    public static final int STATUS_INVALID = 2;
    /** 产物放不下（二氧化碳罐 / 水罐满了） */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在反应 */
    public static final int STATUS_RUNNING = 5;
    /**
     * 氧气不够一次反应（10 mB）—— <b>本工程共享状态码里的新号（12）</b>。
     *
     * <p>⚠ §4.51 那条坑：{@code StatusLampPart} 的状态码是所有机器共用的表。
     * 3 号是"没电"（本机不吃电）、9 号是"氢气不够"（本机不用氢）⇒ 语义都对不上，另起 12 号。</p>
     */
    public static final int STATUS_NO_OXYGEN = 12;
    /** 副产物槽放不下这一批的副产物（木炭 / 空桶）—— 同样是共享命名空间里的新号（13） */
    public static final int STATUS_BYPRODUCT = 13;

    // ================= 容器同步（ContainerData） =================

    public static final int DATA_PROGRESS = 0;
    public static final int DATA_PROGRESS_MAX = 1;
    public static final int DATA_STATUS = 2;
    public static final int DATA_OXYGEN = 3;
    public static final int DATA_CO2 = 4;
    public static final int DATA_WATER = 5;
    public static final int DATA_COUNT = 6;

    // ================= 状态 =================

    private int progress;
    private int progressMax;
    /** 服务端每 tick 刷新，仅供界面（不存盘） */
    private int status = STATUS_EMPTY;
    /** 黑烟的节拍器（不存盘） */
    private int particleTimer;

    // ---- 反应档案：开始那一刻定死，存盘（第 3 条硬规矩）----
    private int activeCo2;
    private int activeWater;
    private int activePower;
    private ItemStack activeByproduct = ItemStack.EMPTY;

    /** 0 号燃料槽（只收燃料）；1 号副产物槽（只能取）。 */
    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            // 燃料槽只收"原版熔炉认的燃料"（+ 本模组的柴油/汽油桶）。
            // ⚠ 与菜单里的 SlotItemHandler 是**同一道门禁**，两处必须一起改（§4.51）。
            return slot == FUEL_SLOT && isFuel(stack);
        }
    };

    /** 0 号氧气罐（只收氧气，**只进不出**）、1 号二氧化碳罐、2 号其他产物罐（水）。 */
    private final FluidTank[] tanks = {
            new FluidTank(OXYGEN_CAPACITY, s -> isOxygen(s)) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(CO2_CAPACITY, s -> isCarbonDioxide(s)) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(WATER_CAPACITY, s -> isWater(s)) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
    };

    private static boolean isOxygen(FluidStack stack) {
        return stack != null && !stack.isEmpty()
                && stack.getFluid().getFluidType() == ModFluids.OXYGEN_TYPE.get();
    }

    private static boolean isCarbonDioxide(FluidStack stack) {
        return stack != null && !stack.isEmpty()
                && stack.getFluid().getFluidType() == ModFluids.CARBON_DIOXIDE_TYPE.get();
    }

    private static boolean isWater(FluidStack stack) {
        return stack != null && !stack.isEmpty()
                && stack.getFluid().getFluidType() == net.neoforged.neoforge.common.NeoForgeMod.WATER_TYPE.value();
    }

    /**
     * 对外流体能力（六面）：<b>只准往氧气罐灌、只准从二氧化碳罐/水罐抽</b>。
     *
     * <p>顺序照用户的描述：二氧化碳（输出）在前，其他产物罐在后 —— 泵先抽二氧化碳。</p>
     */
    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return TANK_COUNT;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return CombustionChamberBlockEntity.this.tanks[tank].getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return CombustionChamberBlockEntity.this.tanks[tank].getCapacity();
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return tank == TANK_OXYGEN && CombustionChamberBlockEntity.this.tanks[TANK_OXYGEN].isFluidValid(stack);
        }

        /** 灌入：只有氧气罐收，别的流体一滴不收。 */
        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (!isOxygen(resource)) {
                return 0;
            }
            return CombustionChamberBlockEntity.this.tanks[TANK_OXYGEN].fill(resource, action);
        }

        /** 抽走：二氧化碳优先，然后水；氧气**永远抽不走**（用户原话"必须输入端"）。 */
        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            if (isCarbonDioxide(resource)) {
                return CombustionChamberBlockEntity.this.tanks[TANK_CO2].drain(resource, action);
            }
            if (isWater(resource)) {
                return CombustionChamberBlockEntity.this.tanks[TANK_WATER].drain(resource, action);
            }
            return FluidStack.EMPTY;
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            FluidStack out = CombustionChamberBlockEntity.this.tanks[TANK_CO2].drain(maxDrain, action);
            if (!out.isEmpty()) {
                return out;
            }
            return CombustionChamberBlockEntity.this.tanks[TANK_WATER].drain(maxDrain, action);
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_PROGRESS -> progress;
                case DATA_PROGRESS_MAX -> progressMax;
                case DATA_STATUS -> status;
                case DATA_OXYGEN -> tanks[TANK_OXYGEN].getFluidAmount();
                case DATA_CO2 -> tanks[TANK_CO2].getFluidAmount();
                case DATA_WATER -> tanks[TANK_WATER].getFluidAmount();
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

    public CombustionChamberBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.COMBUSTION_CHAMBER_BE.get(), pos, state);
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public FluidTank getTank(int tank) {
        return this.tanks[tank];
    }

    public IFluidHandler getFluidHandler() {
        return this.fluidHandler;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    // ================= 燃料与反应档案 =================

    /**
     * 这个物品是不是燃料。
     *
     * <p>判据一：<b>原版熔炉认它</b>（{@code getBurnTime(SMELTING) > 0}）—— 用户原话
     * 「可以放入原版所有可以被熔炉识别的燃料」；判据二：本模组的柴油桶 / 汽油桶
     * （它们是本模组物品，原版燃料表里当然没有）。</p>
     */
    public static boolean isFuel(ItemStack stack) {
        if (stack == null || stack.isEmpty()) {
            return false;
        }
        if (stack.is(ModItems.DIESEL_BUCKET.get()) || stack.is(ModItems.GASOLINE_BUCKET.get())) {
            return true;
        }
        return stack.getBurnTime(RecipeType.SMELTING) > 0;
    }

    /** 是不是"原木"（用户原话「所有原木」⇒ 原版 {@code #minecraft:logs} 标签）。 */
    public static boolean isLog(ItemStack stack) {
        return !stack.isEmpty() && stack.is(ItemTags.LOGS);
    }

    /**
     * 一份燃料的反应档案：时长 / 二氧化碳 / 水 / 动力 / 副产物。
     *
     * <p>判定顺序要紧：柴油/汽油 → 岩浆桶 → 原木 → 其余燃料（岩浆桶与原木本来也都是原版燃料，
     * 放到最后就会被"其余"那条吃掉）。</p>
     */
    public static FuelProfile profileOf(ItemStack fuel) {
        if (fuel.is(ModItems.DIESEL_BUCKET.get())) {
            return new FuelProfile(DURATION_LIQUID_FUEL, CO2_PER_LIQUID_FUEL, WATER_PER_LIQUID_FUEL,
                    POWER_DIESEL, new ItemStack(Items.BUCKET));
        }
        if (fuel.is(ModItems.GASOLINE_BUCKET.get())) {
            return new FuelProfile(DURATION_LIQUID_FUEL, CO2_PER_LIQUID_FUEL, WATER_PER_LIQUID_FUEL,
                    POWER_GASOLINE, new ItemStack(Items.BUCKET));
        }
        if (fuel.is(Items.LAVA_BUCKET)) {
            // 岩浆桶按原版规矩退还空桶（不然玩家每烧一桶就亏一个铁桶）
            return new FuelProfile(DURATION_LAVA, CO2_PER_FUEL, 0, POWER_DEFAULT,
                    new ItemStack(Items.BUCKET));
        }
        if (isLog(fuel)) {
            return new FuelProfile(DURATION_DEFAULT, CO2_PER_LOG, 0, POWER_DEFAULT,
                    new ItemStack(Items.CHARCOAL, CHARCOAL_PER_LOG));
        }
        return new FuelProfile(DURATION_DEFAULT, CO2_PER_FUEL, 0, POWER_DEFAULT, ItemStack.EMPTY);
    }

    /**
     * 一份燃料的反应档案。
     *
     * @param durationTicks 反应时长（tick）
     * @param co2           出多少 mB 二氧化碳
     * @param water         出多少 mB 水
     * @param power         反应期间每 tick 给捕获器的动力
     * @param byproduct     副产物（木炭 / 空桶；没有就是空）
     */
    public record FuelProfile(int durationTicks, int co2, int water, int power, ItemStack byproduct) {
    }

    /** 反应期间每 tick 的动力；没在反应就是 0（{@link PowerCapturerBlockEntity} 读这个数）。 */
    public int powerPerTick() {
        return this.progress > 0 && this.progressMax > 0 ? this.activePower : 0;
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, CombustionChamberBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
            machine.smokeTick();
        }
    }

    /**
     * 黑烟：<b>只在"真在反应"时冒</b>（ZF99 立的口径 —— 调用点必须在工作那一支里，
     * 别另开一个状态判断，否则两边迟早不一致）。
     *
     * <p>判据两条一起看：{@code status == STATUS_RUNNING} 且 {@code progress > 0}
     * —— 后者把"刚结算完、还没开下一批"的那一 tick 排除掉。</p>
     */
    private void smokeTick() {
        if (this.status != STATUS_RUNNING || this.progress <= 0) {
            this.particleTimer = 0;
            return;
        }
        if (--this.particleTimer > 0) {
            return;
        }
        this.particleTimer = PARTICLE_INTERVAL;
        spawnSmoke();
    }

    /**
     * 从顶面冒几缕<b>黑烟</b>（原版 {@code ParticleTypes.SMOKE}）。
     *
     * <p>⚠ §4.67：机器只有服务端 tick ⇒ 必须用 {@code ServerLevel#sendParticles} 广播，
     * 在服务端调 {@code Level#addParticle} 是空操作（写了也一缕烟都看不到）。</p>
     */
    private void spawnSmoke() {
        if (!(this.level instanceof ServerLevel server)) {
            return;
        }
        double x = this.worldPosition.getX() + 0.5;
        double y = this.worldPosition.getY() + 1.05;
        double z = this.worldPosition.getZ() + 0.5;
        server.sendParticles(ParticleTypes.SMOKE, x, y, z, PARTICLES_PER_EMIT,
                PARTICLE_SPREAD, 0.02, PARTICLE_SPREAD, PARTICLE_SPEED);
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

        // ② 反应中
        if (this.progress > 0) {
            if (this.progress + 1 < this.progressMax) {
                this.progress++;
                this.status = STATUS_RUNNING;
                setChanged();
                return;
            }
            // 最后一 tick：先确认产物放得下（放不下就原地等，产物一件不丢）
            if (co2Space() < this.activeCo2 || waterSpace() < this.activeWater) {
                this.status = STATUS_OUTPUT_FULL;
                return;
            }
            if (!byproductFits(this.activeByproduct)) {
                this.status = STATUS_BYPRODUCT;
                return;
            }
            emit();
            this.progress = 0;
            this.progressMax = 0;
            this.status = STATUS_RUNNING;
            setChanged();
            return;
        }

        // ③ 没在反应：看燃料槽
        ItemStack fuel = this.items.getStackInSlot(FUEL_SLOT);
        if (fuel.isEmpty()) {
            this.status = STATUS_EMPTY;
            return;
        }
        if (!isFuel(fuel)) {
            this.status = STATUS_INVALID;
            return;
        }

        // ④ 氧气不够（只停不清）
        if (this.tanks[TANK_OXYGEN].getFluidAmount() < OXYGEN_PER_OPERATION) {
            this.status = STATUS_NO_OXYGEN;
            return;
        }

        FuelProfile profile = profileOf(fuel);
        if (!byproductFits(profile.byproduct())) {
            this.status = STATUS_BYPRODUCT;
            return;
        }

        // ⑤ 开始反应：**这一刻**扣 1 份燃料 + 10 mB 氧气（用户原话「消耗一份燃料和10mB氧气开始反应」）
        this.items.extractItem(FUEL_SLOT, 1, false);
        this.tanks[TANK_OXYGEN].drain(OXYGEN_PER_OPERATION, IFluidHandler.FluidAction.EXECUTE);
        this.activeCo2 = profile.co2();
        this.activeWater = profile.water();
        this.activePower = profile.power();
        this.activeByproduct = profile.byproduct().copy();
        this.progressMax = profile.durationTicks();
        this.progress = 1;
        this.status = STATUS_RUNNING;
        setChanged();
    }

    /** 结算：落二氧化碳 / 水 / 副产物（调用前已经确认过放得下）。 */
    private void emit() {
        if (this.activeCo2 > 0) {
            this.tanks[TANK_CO2].fill(new FluidStack(ModFluids.CARBON_DIOXIDE.get(), this.activeCo2),
                    IFluidHandler.FluidAction.EXECUTE);
        }
        if (this.activeWater > 0) {
            this.tanks[TANK_WATER].fill(new FluidStack(net.minecraft.world.level.material.Fluids.WATER, this.activeWater),
                    IFluidHandler.FluidAction.EXECUTE);
        }
        if (!this.activeByproduct.isEmpty() && byproductFits(this.activeByproduct)) {
            ItemStack out = this.items.getStackInSlot(BYPRODUCT_SLOT);
            if (out.isEmpty()) {
                this.items.setStackInSlot(BYPRODUCT_SLOT, this.activeByproduct.copy());
            } else {
                out.grow(this.activeByproduct.getCount());
                this.items.setStackInSlot(BYPRODUCT_SLOT, out);
            }
        }
        this.activeByproduct = ItemStack.EMPTY;
    }

    /** 二氧化碳罐还能收多少 mB。 */
    public int co2Space() {
        return CO2_CAPACITY - this.tanks[TANK_CO2].getFluidAmount();
    }

    /** 水罐还能收多少 mB。 */
    public int waterSpace() {
        return WATER_CAPACITY - this.tanks[TANK_WATER].getFluidAmount();
    }

    /** 副产物槽放不放得下这一件（空槽 / 同物品且没满 / 空物品永远放得下）。 */
    public boolean byproductFits(ItemStack byproduct) {
        if (byproduct == null || byproduct.isEmpty()) {
            return true;
        }
        ItemStack out = this.items.getStackInSlot(BYPRODUCT_SLOT);
        if (out.isEmpty()) {
            return true;
        }
        if (!ItemStack.isSameItemSameComponents(out, byproduct)) {
            return false;
        }
        int limit = Math.min(out.getMaxStackSize(), this.items.getSlotLimit(BYPRODUCT_SLOT));
        return out.getCount() + byproduct.getCount() <= limit;
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

    public int oxygenAmount() {
        return this.tanks[TANK_OXYGEN].getFluidAmount();
    }

    public int co2Amount() {
        return this.tanks[TANK_CO2].getFluidAmount();
    }

    public int waterAmount() {
        return this.tanks[TANK_WATER].getFluidAmount();
    }

    /** 反应档案里的动力档（探针用；没在反应时也有值 = 上一批的档位）。 */
    public int activePower() {
        return this.activePower;
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.combustion_chamber");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new CombustionChamberMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.progress = tag.getInt("progress");
        this.progressMax = tag.getInt("progressMax");
        this.status = tag.getInt("status");
        this.activeCo2 = tag.getInt("activeCo2");
        this.activeWater = tag.getInt("activeWater");
        this.activePower = tag.getInt("activePower");
        this.activeByproduct = tag.contains("activeByproduct")
                ? ItemStack.parseOptional(registries, tag.getCompound("activeByproduct"))
                : ItemStack.EMPTY;
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
        for (int i = 0; i < TANK_COUNT; i++) {
            // ⚠ 必须自己 new 一个子标签再 put 回去，别写 tag.getCompound("tankN") 往里塞（§4.49）
            this.tanks[i].readFromNBT(registries, tag.getCompound("tank" + i));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("progress", this.progress);
        tag.putInt("progressMax", this.progressMax);
        tag.putInt("status", this.status);
        tag.putInt("activeCo2", this.activeCo2);
        tag.putInt("activeWater", this.activeWater);
        tag.putInt("activePower", this.activePower);
        if (!this.activeByproduct.isEmpty()) {
            tag.put("activeByproduct", this.activeByproduct.save(registries));
        }
        tag.put("inventory", this.items.serializeNBT(registries));
        for (int i = 0; i < TANK_COUNT; i++) {
            CompoundTag tankTag = new CompoundTag();
            this.tanks[i].writeToNBT(registries, tankTag);
            tag.put("tank" + i, tankTag);
        }
    }
}
