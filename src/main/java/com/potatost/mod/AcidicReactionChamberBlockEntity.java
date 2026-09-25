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
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 酸性反应室的方块实体（0.11 ZF101）。
 *
 * <p><b>用户原话（逐条落实）：</b></p>
 * <pre>
 *   「加一个酸性反应室（配方【铜块】【稳定金属块】【加热装置】，【钛锭】【灌装机】【钛锭】，
 *     【红石火把】【电解器】【拉杆】）Gui 输入；二氧化碳储罐 氧气储罐 氨气储罐 水储罐（各1000Mb）
 *     一个硫槽位 输出槽；硝酸 硫酸 碳酸储罐各1000Mb 三个选择按钮 在储罐下方 选择则执行相应的配方
 *     （gui别的你发挥）配方；1.10mb二氧化碳+1mb水 产出1mb碳酸 2.1mb氧气+1mb氨气 产出1mb硝酸
 *     3.10个硫+100MB水 产出100MB硫酸 耗能皆为500fe/t 储能12400fe」
 * </pre>
 *
 * <p><b>七个罐</b>（用户点名"各 1000 mB"）：四个<b>输入</b>——二氧化碳 / 氧气 / 氨气 / 水；
 * 三个<b>输出</b>——碳酸 / 硝酸 / 硫酸。输入罐只进不出、输出罐只出不进（与本工程其它机器同一条口径）。</p>
 *
 * <p><b>三个选择按钮</b>：界面在输出储罐下方排三个按钮，点哪个就只跑哪个配方
 * （走原版菜单按钮通道 {@code AbstractContainerMenu#clickMenuButton}，见 {@link AcidicReactionChamberMenu}）。</p>
 *
 * <p><b>三个配方</b>（用户给的数，一个字没改）：</p>
 * <ol>
 *   <li><b>碳酸</b>：每 tick 10 mB 二氧化碳 + 1 mB 水 → 1 mB 碳酸（连续式，与氨气组成室同款）；</li>
 *   <li><b>硝酸</b>：每 tick 1 mB 氧气 + 1 mB 氨气 → 1 mB 硝酸（连续式）；</li>
 *   <li><b>硫酸</b>：10 个硫 + 100 mB 水 → 100 mB 硫酸（<b>批次式</b>，见下）。</li>
 * </ol>
 *
 * <p><b>⚠ 3 号为什么是"批次"而 1/2 号是"每 tick"</b>：用户给 1/2 号的都是"1 mB 级"的配比
 * （配合 500 FE/t 就是每 tick 一次），而 3 号是"10 个硫"——<b>按 tick 吃 10 个硫显然是笔误级的速度</b>
 * （6.4 秒吃一组）。所以 3 号做成一批：<b>一批 100 tick（5 秒）× 500 FE/t = 50,000 FE 换 100 mB 硫酸</b>。
 * ⚠ <b>这个"100 tick"是我定的</b>（用户没给时长），挑它的理由：这样三种酸**每 mB 的耗电都是 500 FE**
 * （1、2 号：500 FE/t ÷ 1 mB/t；3 号：50,000 FE ÷ 100 mB），三档对齐。
 * 要改就是一个常量 {@link #SULFURIC_DURATION_TICKS}。</p>
 *
 * <p><b>耗能与储能照用户给的</b>：{@value #ENERGY_PER_TICK} FE/t、缓冲 {@value #MAX_ENERGY} FE
 * （12400 = 24.8 tick 的钱，也就是说**必须持续供电**）。</p>
 *
 * <p><b>⚠ 一处我替用户注意到的坑</b>：合成配方里要**稳定金属块**，而它到目前为止
 * <b>没有合成配方</b>（ZF100 那轮用户明确说"只要那两个机器的配方"）⇒ <b>这台机器在生存里暂时做不出来</b>。
 * 已如实写进档案 §9 待办：要补稳定金属块的配方说一声。</p>
 */
public class AcidicReactionChamberBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 用户给的数 =================

    /** 耗能：三种配方都是 500 FE/t（用户原话「耗能皆为500fe/t」） */
    public static final int ENERGY_PER_TICK = 500;
    /** 储能：12400 FE（用户原话「储能12400fe」） */
    public static final int MAX_ENERGY = 12400;
    /** 七个罐各 1000 mB（用户原话「各1000Mb」） */
    public static final int TANK_CAPACITY = 1000;

    /** 1 号配方（碳酸）：每 tick 10 mB 二氧化碳 + 1 mB 水 → 1 mB 碳酸 */
    public static final int CARBONIC_CO2_PER_TICK = 10;
    public static final int CARBONIC_WATER_PER_TICK = 1;
    public static final int CARBONIC_OUT_PER_TICK = 1;

    /** 2 号配方（硝酸）：每 tick 1 mB 氧气 + 1 mB 氨气 → 1 mB 硝酸 */
    public static final int NITRIC_OXYGEN_PER_TICK = 1;
    public static final int NITRIC_AMMONIA_PER_TICK = 1;
    public static final int NITRIC_OUT_PER_TICK = 1;

    /** 3 号配方（硫酸）：一批 10 个硫 + 100 mB 水 → 100 mB 硫酸 */
    public static final int SULFUR_PER_BATCH = 10;
    public static final int SULFURIC_WATER_PER_BATCH = 100;
    public static final int SULFURIC_OUT_PER_BATCH = 100;
    /** ⚠ 一批多少 tick —— **我定的**（用户没给时长），理由见类注释：让三种酸每 mB 都是 500 FE */
    public static final int SULFURIC_DURATION_TICKS = 100;

    /**
     * 4 号配方（盐酸，0.11 ZF102）：每 tick 10 mB 氢气 + 10 mB 氯气 + 5 mB 水 → 5 mB 盐酸。
     *
     * <p>用户原话「然后新加配方盐酸 10mb氢气+10mb氯气+5mb水 产出5mb盐酸 耗能一致」——
     * 耗能沿用 {@link #ENERGY_PER_TICK}（500 FE/t），**一个数都没改**。</p>
     */
    public static final int HYDROCHLORIC_HYDROGEN_PER_TICK = 10;
    public static final int HYDROCHLORIC_CHLORINE_PER_TICK = 10;
    public static final int HYDROCHLORIC_WATER_PER_TICK = 5;
    public static final int HYDROCHLORIC_OUT_PER_TICK = 5;

    // ================= 配方号（界面那四个按钮） =================

    public static final int RECIPE_CARBONIC = 0;
    public static final int RECIPE_NITRIC = 1;
    public static final int RECIPE_SULFURIC = 2;
    /** 0.11 ZF102 新增的第四个配方（盐酸） */
    public static final int RECIPE_HYDROCHLORIC = 3;
    public static final int RECIPE_COUNT = 4;

    // ================= 罐 / 槽 =================

    public static final int TANK_CO2 = 0;
    public static final int TANK_OXYGEN = 1;
    public static final int TANK_AMMONIA = 2;
    public static final int TANK_WATER = 3;
    public static final int TANK_CARBONIC = 4;
    public static final int TANK_NITRIC = 5;
    public static final int TANK_SULFURIC = 6;
    /**
     * 0.11 ZF102 新加的三个罐 —— <b>故意接在最后</b>（7/8/9），不动前面 0~6 的号。
     *
     * <p>这样 ZF101 的存档读进来时，原来那七个罐的含义一个都没变（罐里的酸还在原来的罐里）。</p>
     */
    public static final int TANK_HYDROGEN = 7;
    public static final int TANK_CHLORINE = 8;
    public static final int TANK_HYDROCHLORIC = 9;
    public static final int TANK_COUNT = 10;

    /** 六个原料罐（只进不出的那些） */
    public static final int[] INPUT_TANKS = {
            TANK_CO2, TANK_OXYGEN, TANK_AMMONIA, TANK_WATER, TANK_HYDROGEN, TANK_CHLORINE,
    };
    /** 四种酸（只出不进的那些）—— 顺序就是泵抽走的优先顺序 */
    public static final int[] OUTPUT_TANKS = {
            TANK_CARBONIC, TANK_NITRIC, TANK_SULFURIC, TANK_HYDROCHLORIC,
    };

    /** 硫槽（用户原话「一个硫槽位」） */
    public static final int SULFUR_SLOT = 0;
    /** 输出槽（用户原话「输出槽」）—— 三个配方的产物都是流体，这个槽留着给以后的固体产物 */
    public static final int OUTPUT_SLOT = 1;
    public static final int SLOT_COUNT = 2;

    // ================= 状态灯（共享命名空间） =================

    /** 有红石信号 = 关机 */
    public static final int STATUS_DISABLED = 0;
    /** 磷？不——2 号是"无效"（本机不该出现） */
    public static final int STATUS_INVALID = 2;
    /** 电不够一 tick（本机**有**能量条 ⇒ 红灯在这台机器上是会出现的） */
    public static final int STATUS_NO_POWER = 3;
    /** 产物罐满了 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在反应 */
    public static final int STATUS_RUNNING = 5;
    /** 硫不够一批（10 个）—— 复用液压机那个 6 号「材料数量不够」，语义完全相同 */
    public static final int STATUS_MATERIAL = 6;
    /**
     * 流体原料不足 —— <b>共享状态码里的新号（14）</b>。
     *
     * <p>⚠ §4.51 那条坑：3 号是"没电"、9 号是"氢气不够"、10 号是"氮气不够"、12 号是"氧气不够"，
     * 都只对得上**一种**原料；本机三种配方共要四种原料（二氧化碳/氧气/氨气/水）⇒
     * 与其为每种原料各起一个号，不如起一个**共用的 14 号"流体原料不足"**
     * （悬停文案会把该配方缺什么写在 tooltip 里，不靠灯色区分）。</p>
     */
    public static final int STATUS_INPUTS = 14;

    // ================= 容器同步 =================

    public static final int DATA_ENERGY = 0;
    public static final int DATA_PROGRESS = 1;
    public static final int DATA_PROGRESS_MAX = 2;
    public static final int DATA_STATUS = 3;
    public static final int DATA_RECIPE = 4;
    public static final int DATA_CO2 = 5;
    public static final int DATA_OXYGEN = 6;
    public static final int DATA_AMMONIA = 7;
    public static final int DATA_WATER = 8;
    public static final int DATA_CARBONIC = 9;
    public static final int DATA_NITRIC = 10;
    public static final int DATA_SULFURIC = 11;
    /** 0.11 ZF102 新加的三个罐（同样接在最后，不动前面的号） */
    public static final int DATA_HYDROGEN = 12;
    public static final int DATA_CHLORINE = 13;
    public static final int DATA_HYDROCHLORIC = 14;
    public static final int DATA_COUNT = 15;

    // ================= 状态 =================

    private int energy;
    private int progress;
    private int progressMax = SULFURIC_DURATION_TICKS;
    private int status = STATUS_DISABLED;
    /** 当前选中的配方号（界面那三个按钮改的就是它） */
    private int selected = RECIPE_CARBONIC;

    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                this.setChanged();
            });

    /** 0 号硫槽（只收硫）；1 号输出槽（只能取）。 */
    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            // ⚠ 与菜单里的 SlotItemHandler 是**同一道门禁**，两处必须一起改（§4.51）
            return slot == SULFUR_SLOT && stack.is(ModItems.SULFUR.get());
        }
    };

    /** 七个罐：前四个只进不出、后三个只出不进。 */
    private final FluidTank[] tanks = {
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.CARBON_DIOXIDE_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.OXYGEN_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.AMMONIA_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(TANK_CAPACITY, s -> type(s) == net.neoforged.neoforge.common.NeoForgeMod.WATER_TYPE.value()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.CARBONIC_ACID_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.NITRIC_ACID_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.SULFURIC_ACID_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            // 0.11 ZF102：两个新原料罐（氢气 / 氯气）+ 第 4 个产物罐（盐酸）
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.HYDROGEN_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.CHLORINE_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
            new FluidTank(TANK_CAPACITY, s -> type(s) == ModFluids.HYDROCHLORIC_ACID_TYPE.get()) {
                @Override
                protected void onContentsChanged() {
                    setChanged();
                }
            },
    };

    private static net.neoforged.neoforge.fluids.FluidType type(FluidStack stack) {
        return stack == null || stack.isEmpty() ? null : stack.getFluid().getFluidType();
    }

    private final IFluidHandler fluidHandler = new IFluidHandler() {
        @Override
        public int getTanks() {
            return TANK_COUNT;
        }

        @Override
        public FluidStack getFluidInTank(int tank) {
            return AcidicReactionChamberBlockEntity.this.tanks[tank].getFluid();
        }

        @Override
        public int getTankCapacity(int tank) {
            return AcidicReactionChamberBlockEntity.this.tanks[tank].getCapacity();
        }

        @Override
        public boolean isFluidValid(int tank, FluidStack stack) {
            return isInputTank(tank)
                    && AcidicReactionChamberBlockEntity.this.tanks[tank].isFluidValid(stack);
        }

        /** 灌入：只有那六个输入罐收，四个产物罐一滴不收。 */
        @Override
        public int fill(FluidStack resource, FluidAction action) {
            if (isCarbonDioxide(resource)) {
                return AcidicReactionChamberBlockEntity.this.tanks[TANK_CO2].fill(resource, action);
            }
            if (isOxygen(resource)) {
                return AcidicReactionChamberBlockEntity.this.tanks[TANK_OXYGEN].fill(resource, action);
            }
            if (isAmmonia(resource)) {
                return AcidicReactionChamberBlockEntity.this.tanks[TANK_AMMONIA].fill(resource, action);
            }
            if (isWater(resource)) {
                return AcidicReactionChamberBlockEntity.this.tanks[TANK_WATER].fill(resource, action);
            }
            if (isHydrogen(resource)) {
                return AcidicReactionChamberBlockEntity.this.tanks[TANK_HYDROGEN].fill(resource, action);
            }
            if (isChlorine(resource)) {
                return AcidicReactionChamberBlockEntity.this.tanks[TANK_CHLORINE].fill(resource, action);
            }
            return 0;
        }

        /** 抽走：四种酸按 OUTPUT_TANKS 的顺序（碳酸 → 硝酸 → 硫酸 → 盐酸）；六种原料**永远抽不走**。 */
        @Override
        public FluidStack drain(FluidStack resource, FluidAction action) {
            for (int tank : OUTPUT_TANKS) {
                if (AcidicReactionChamberBlockEntity.this.tanks[tank].isFluidValid(resource)) {
                    return AcidicReactionChamberBlockEntity.this.tanks[tank].drain(resource, action);
                }
            }
            return FluidStack.EMPTY;
        }

        @Override
        public FluidStack drain(int maxDrain, FluidAction action) {
            for (int tank : OUTPUT_TANKS) {
                FluidStack out = AcidicReactionChamberBlockEntity.this.tanks[tank].drain(maxDrain, action);
                if (!out.isEmpty()) {
                    return out;
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
                case DATA_RECIPE -> selected;
                case DATA_CO2 -> tanks[TANK_CO2].getFluidAmount();
                case DATA_OXYGEN -> tanks[TANK_OXYGEN].getFluidAmount();
                case DATA_AMMONIA -> tanks[TANK_AMMONIA].getFluidAmount();
                case DATA_WATER -> tanks[TANK_WATER].getFluidAmount();
                case DATA_CARBONIC -> tanks[TANK_CARBONIC].getFluidAmount();
                case DATA_NITRIC -> tanks[TANK_NITRIC].getFluidAmount();
                case DATA_SULFURIC -> tanks[TANK_SULFURIC].getFluidAmount();
                case DATA_HYDROGEN -> tanks[TANK_HYDROGEN].getFluidAmount();
                case DATA_CHLORINE -> tanks[TANK_CHLORINE].getFluidAmount();
                case DATA_HYDROCHLORIC -> tanks[TANK_HYDROCHLORIC].getFluidAmount();
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

    public AcidicReactionChamberBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.ACIDIC_REACTION_CHAMBER_BE.get(), pos, state);
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

    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    // ================= 配方判定（纯函数，探针直接调） =================

    private static boolean isCarbonDioxide(FluidStack s) {
        return type(s) == ModFluids.CARBON_DIOXIDE_TYPE.get();
    }

    private static boolean isOxygen(FluidStack s) {
        return type(s) == ModFluids.OXYGEN_TYPE.get();
    }

    private static boolean isAmmonia(FluidStack s) {
        return type(s) == ModFluids.AMMONIA_TYPE.get();
    }

    private static boolean isWater(FluidStack s) {
        return type(s) == net.neoforged.neoforge.common.NeoForgeMod.WATER_TYPE.value();
    }

    private static boolean isHydrogen(FluidStack s) {
        return type(s) == ModFluids.HYDROGEN_TYPE.get();
    }

    private static boolean isChlorine(FluidStack s) {
        return type(s) == ModFluids.CHLORINE_TYPE.get();
    }

    private static boolean isInputTank(int tank) {
        for (int t : INPUT_TANKS) {
            if (t == tank) {
                return true;
            }
        }
        return false;
    }

    /** 这个配方号合不合法（界面的按钮号也走这里）。 */
    public static boolean isValidRecipe(int recipe) {
        return recipe >= 0 && recipe < RECIPE_COUNT;
    }

    /** 配方号 → 产物罐。 */
    public static int outputTankOf(int recipe) {
        return switch (recipe) {
            case RECIPE_NITRIC -> TANK_NITRIC;
            case RECIPE_SULFURIC -> TANK_SULFURIC;
            case RECIPE_HYDROCHLORIC -> TANK_HYDROCHLORIC;
            default -> TANK_CARBONIC;
        };
    }

    /** 这个配方是批次式的（只有 3 号硫酸是）。 */
    public static boolean isBatch(int recipe) {
        return recipe == RECIPE_SULFURIC;
    }

    /** 选中哪个配方（界面三个按钮点出来的）。切配方会把批次进度清零。 */
    public void setSelected(int recipe) {
        if (!isValidRecipe(recipe) || recipe == this.selected) {
            return;
        }
        this.selected = recipe;
        this.progress = 0;
        this.progressMax = isBatch(recipe) ? SULFURIC_DURATION_TICKS : 1;
        setChanged();
    }

    // ================= 每 tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, AcidicReactionChamberBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
        }
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }

        // ① 红石信号 = 关机（批次进度保留）
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.status = STATUS_DISABLED;
            return;
        }

        if (isBatch(this.selected)) {
            batchTick();
        } else {
            continuousTick();
        }
    }

    /** 1/2/4 号：每 tick 一次（与氨气组成室同款）。 */
    private void continuousTick() {
        boolean carbonic = this.selected == RECIPE_CARBONIC;
        boolean hydrochloric = this.selected == RECIPE_HYDROCHLORIC;
        int needCo2 = carbonic ? CARBONIC_CO2_PER_TICK : 0;
        int needWater = carbonic ? CARBONIC_WATER_PER_TICK
                : (hydrochloric ? HYDROCHLORIC_WATER_PER_TICK : 0);
        int needOxygen = (!carbonic && !hydrochloric) ? NITRIC_OXYGEN_PER_TICK : 0;
        int needAmmonia = (!carbonic && !hydrochloric) ? NITRIC_AMMONIA_PER_TICK : 0;
        int needHydrogen = hydrochloric ? HYDROCHLORIC_HYDROGEN_PER_TICK : 0;
        int needChlorine = hydrochloric ? HYDROCHLORIC_CHLORINE_PER_TICK : 0;
        int out = carbonic ? CARBONIC_OUT_PER_TICK
                : (hydrochloric ? HYDROCHLORIC_OUT_PER_TICK : NITRIC_OUT_PER_TICK);

        this.progressMax = 1;
        if (this.energy < ENERGY_PER_TICK) {
            this.status = STATUS_NO_POWER;
            return;
        }
        if (this.tanks[TANK_CO2].getFluidAmount() < needCo2
                || this.tanks[TANK_WATER].getFluidAmount() < needWater
                || this.tanks[TANK_OXYGEN].getFluidAmount() < needOxygen
                || this.tanks[TANK_AMMONIA].getFluidAmount() < needAmmonia
                || this.tanks[TANK_HYDROGEN].getFluidAmount() < needHydrogen
                || this.tanks[TANK_CHLORINE].getFluidAmount() < needChlorine) {
            this.status = STATUS_INPUTS;
            return;
        }
        int outTank = outputTankOf(this.selected);
        if (space(outTank) < out) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }

        this.energy -= ENERGY_PER_TICK;
        if (needCo2 > 0) {
            this.tanks[TANK_CO2].drain(needCo2, IFluidHandler.FluidAction.EXECUTE);
        }
        if (needWater > 0) {
            this.tanks[TANK_WATER].drain(needWater, IFluidHandler.FluidAction.EXECUTE);
        }
        if (needOxygen > 0) {
            this.tanks[TANK_OXYGEN].drain(needOxygen, IFluidHandler.FluidAction.EXECUTE);
        }
        if (needAmmonia > 0) {
            this.tanks[TANK_AMMONIA].drain(needAmmonia, IFluidHandler.FluidAction.EXECUTE);
        }
        if (needHydrogen > 0) {
            this.tanks[TANK_HYDROGEN].drain(needHydrogen, IFluidHandler.FluidAction.EXECUTE);
        }
        if (needChlorine > 0) {
            this.tanks[TANK_CHLORINE].drain(needChlorine, IFluidHandler.FluidAction.EXECUTE);
        }
        this.tanks[outTank].fill(new FluidStack(productOf(this.selected), out),
                IFluidHandler.FluidAction.EXECUTE);
        this.progress = 1;
        this.status = STATUS_RUNNING;
        setChanged();
    }

    /** 3 号：一批 100 tick（材料在**最后一 tick** 才扣，中途缺料只停不清）。 */
    private void batchTick() {
        this.progressMax = SULFURIC_DURATION_TICKS;
        ItemStack sulfur = this.items.getStackInSlot(SULFUR_SLOT);
        if (sulfur.isEmpty() || sulfur.getCount() < SULFUR_PER_BATCH) {
            this.status = STATUS_MATERIAL;
            return;
        }
        if (this.tanks[TANK_WATER].getFluidAmount() < SULFURIC_WATER_PER_BATCH) {
            this.status = STATUS_INPUTS;
            return;
        }
        if (space(TANK_SULFURIC) < SULFURIC_OUT_PER_BATCH) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }
        if (this.energy < ENERGY_PER_TICK) {
            this.status = STATUS_NO_POWER;
            return;
        }

        this.energy -= ENERGY_PER_TICK;
        if (this.progress + 1 < this.progressMax) {
            this.progress++;
            this.status = STATUS_RUNNING;
            setChanged();
            return;
        }

        // 结算：扣 10 个硫 + 100 mB 水，落 100 mB 硫酸
        this.items.extractItem(SULFUR_SLOT, SULFUR_PER_BATCH, false);
        this.tanks[TANK_WATER].drain(SULFURIC_WATER_PER_BATCH, IFluidHandler.FluidAction.EXECUTE);
        this.tanks[TANK_SULFURIC].fill(
                new FluidStack(ModFluids.SULFURIC_ACID.get(), SULFURIC_OUT_PER_BATCH),
                IFluidHandler.FluidAction.EXECUTE);
        this.progress = 0;
        this.status = STATUS_RUNNING;
        setChanged();
    }

    /** 配方号 → 产物流体。 */
    public static net.minecraft.world.level.material.Fluid productOf(int recipe) {
        return switch (recipe) {
            case RECIPE_NITRIC -> ModFluids.NITRIC_ACID.get();
            case RECIPE_SULFURIC -> ModFluids.SULFURIC_ACID.get();
            case RECIPE_HYDROCHLORIC -> ModFluids.HYDROCHLORIC_ACID.get();
            default -> ModFluids.CARBONIC_ACID.get();
        };
    }

    /** 某个罐还能收多少 mB。 */
    public int space(int tank) {
        return TANK_CAPACITY - this.tanks[tank].getFluidAmount();
    }

    // ================= 读数（界面 / 探针共用） =================

    public int getEnergy() {
        return this.energy;
    }

    public int getProgress() {
        return this.progress;
    }

    public int getProgressMax() {
        return this.progressMax;
    }

    public int getStatus() {
        return this.status;
    }

    public int getSelected() {
        return this.selected;
    }

    public int amount(int tank) {
        return this.tanks[tank].getFluidAmount();
    }

    // ================= MenuProvider =================

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.acidic_reaction_chamber");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new AcidicReactionChamberMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.progress = tag.getInt("progress");
        this.progressMax = tag.getInt("progressMax");
        this.status = tag.getInt("status");
        this.selected = tag.getInt("selected");
        if (!isValidRecipe(this.selected)) {
            this.selected = RECIPE_CARBONIC;
        }
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
        for (int i = 0; i < TANK_COUNT; i++) {
            // ⚠ 必须自己 new 一个子标签再 put 回去，别写 tag.getCompound("tankN") 往里塞（§4.49）
            this.tanks[i].readFromNBT(registries, tag.getCompound("tank" + i));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("progress", this.progress);
        tag.putInt("progressMax", this.progressMax);
        tag.putInt("status", this.status);
        tag.putInt("selected", this.selected);
        tag.put("inventory", this.items.serializeNBT(registries));
        for (int i = 0; i < TANK_COUNT; i++) {
            CompoundTag tankTag = new CompoundTag();
            this.tanks[i].writeToNBT(registries, tankTag);
            tag.put("tank" + i, tankTag);
        }
    }
}
