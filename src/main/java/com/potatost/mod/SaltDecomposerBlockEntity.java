package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.util.RandomSource;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.items.ItemStackHandler;

/**
 * 盐分解构器（0.10 ZF32）：左侧 1 个输入槽、右侧 3 个输出槽，通电工作。
 *
 * <p><b>配方（用户指定）：</b>消耗 {@value SaltDecomposerRecipes#SALT_INPUT} 个海盐，
 * 40 秒后结算 —— <b>60%</b> 返还 64 个海盐、<b>5%</b> 出一个随机粗矿、<b>100%</b> 出氯化钠。
 * 三条**各自独立掷骰**，所以一轮可能同时拿到好几样。</p>
 *
 * <p><b>储能"极其低"（用户指定 20 FE）</b>：缓冲只有 {@value #MAX_ENERGY} FE，
 * 而每 tick 要 {@value SaltDecomposerRecipes#ENERGY_PER_TICK} FE ——
 * <b>缓冲恰好是 1 tick 的量</b>，也就是说这台机器必须<b>持续通电</b>才跑得动，
 * 断一下电进度就停在那里。这是设计意图，不是配置失误。</p>
 *
 * <p><b>三个输出槽的用途</b>：一轮最多同时产出三样东西（海盐返还 + 氯化钠 + 粗矿），
 * 每样各占一个槽。结算前会用"模拟占用"一次性算好三样各落哪几槽（见 {@link #planAll}）。</p>
 *
 * <p><b>产物结算的硬规矩（照抄微型粉碎机踩平过的那套）：</b>
 * 放不下就<b>原地等</b>（既不扣输入也不产出），落盘一律走 {@code setStackInSlot}
 * 而**不是** {@code insertItem} —— 后者内部会查 {@code isItemValid}，
 * 而本类把输出槽的门禁关上了，用它 = 产物静默消失（§4.14 的原事故）。</p>
 */
public class SaltDecomposerBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 数值 =================
    /** 内部缓冲：用户指定"极其低，只有 20 FE" */
    public static final int MAX_ENERGY = 20;

    public static final int INPUT_SLOT = 0;
    public static final int OUTPUT_FIRST = 1;
    public static final int OUTPUT_COUNT = 3;
    public static final int SLOT_COUNT = OUTPUT_FIRST + OUTPUT_COUNT;   // = 4

    // ContainerData 索引
    public static final int DATA_ENERGY = 0;
    public static final int DATA_PROGRESS = 1;
    public static final int DATA_PROGRESS_MAX = 2;
    public static final int DATA_STATUS = 3;
    public static final int DATA_COUNT = 4;

    // ================= 状态灯（取值与微型粉碎机一致 ⇒ StatusLampPart 的颜色映射直接可用） =================
    public static final int STATUS_DISABLED = 0;
    public static final int STATUS_EMPTY = 1;
    public static final int STATUS_INVALID = 2;
    public static final int STATUS_NO_POWER = 3;
    public static final int STATUS_OUTPUT_FULL = 4;
    public static final int STATUS_RUNNING = 5;

    private int energy;
    private int progress;
    private int progressMax;
    /** 服务端每 tick 刷新，仅供 GUI（不存盘） */
    private int status = STATUS_EMPTY;

    /** 0 号输入；1~3 号输出（输出槽不接受玩家放置，也不接受自动化灌入）。 */
    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public void onContentsChanged(int slot) {
            setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return slot == INPUT_SLOT;
        }
    };

    /** 只收不放的能量缓冲（复用公共件，别再抄匿名实现 —— Audit 的 D 项盯着这个）。 */
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
            return switch (index) {
                case DATA_ENERGY -> energy;
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

    public SaltDecomposerBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.SALT_DECOMPOSER_BE.get(), pos, state);
    }

    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public ItemStackHandler getInventory() {
        return this.items;
    }

    public ContainerData getContainerData() {
        return this.containerData;
    }

    // ================= 每 tick =================
    public static void tick(Level level, BlockPos pos, BlockState state, SaltDecomposerBlockEntity machine) {
        if (!level.isClientSide) {
            machine.serverTick();
        }
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

        // ② 输入槽必须是海盐，而且一次要够 64 个
        ItemStack input = this.items.getStackInSlot(INPUT_SLOT);
        if (input.isEmpty()) {
            resetProgress();
            this.status = STATUS_EMPTY;
            return;
        }
        if (!input.is(ModItems.SEA_SALT.get()) || input.getCount() < SaltDecomposerRecipes.SALT_INPUT) {
            // ⚠ 数量不够**不重置进度**（只是没料开工）：玩家分两批凑够 64 个，
            //   不该把已经跑了一大半的进度清零。
            this.status = STATUS_INVALID;
            return;
        }
        this.progressMax = SaltDecomposerRecipes.DURATION_TICKS;

        // ③ 每 tick 都走同一条"付电 → 推进"的路，**包括最后一 tick**。
        //    ⚠ 常见写错法是把"到点结算"写成独立分支，那样最后一 tick 的电就白送了。
        //      这里统一成：先确认这一 tick 有电、且这一 tick 的产物放得下，再付电推进；
        //      推到满的那一刻同 tick 结算（付的是这一 tick 的电，不多不少）。
        if (this.energy < SaltDecomposerRecipes.ENERGY_PER_TICK) {
            this.status = STATUS_NO_POWER;
            return;
        }

        if (this.progress + 1 < this.progressMax) {
            this.energy -= SaltDecomposerRecipes.ENERGY_PER_TICK;
            this.progress++;
            this.status = STATUS_RUNNING;
            setChanged();
            return;
        }

        // ④ 最后一 tick：先掷骰拿到这一轮的产物（只掷一次），再按**模拟占用**算落槽
        List<ItemStack> produced = rollProducts();
        int[][] plan = planAll(produced);
        if (plan == null) {
            // 产物放不下：停在满进度之前等玩家腾位置。这一 tick 的电**不扣**（不产出就不收费）
            this.status = STATUS_OUTPUT_FULL;
            return;
        }
        this.energy -= SaltDecomposerRecipes.ENERGY_PER_TICK;
        for (int i = 0; i < produced.size(); i++) {
            applyPlan(produced.get(i), plan[i]);
        }
        this.items.extractItem(INPUT_SLOT, SaltDecomposerRecipes.SALT_INPUT, false);
        this.progress = 0;
        this.status = STATUS_RUNNING;
        setChanged();
    }

    /**
     * 掷骰定下这一轮的产物（<b>只掷一次</b>，结果既用于"放得下吗"也用于"真的写入"）。
     *
     * <p>氯化钠必定有 ⇒ 列表永不为空。</p>
     */
    private List<ItemStack> rollProducts() {
        RandomSource random = this.level.random;
        SaltDecomposerRecipes.Rolls rolls = SaltDecomposerRecipes.roll(random);
        List<ItemStack> out = new java.util.ArrayList<>(3);
        if (rolls.saltReturned()) {
            out.add(new ItemStack(ModItems.SEA_SALT.get(), SaltDecomposerRecipes.SALT_INPUT));
        }
        out.add(new ItemStack(ModItems.SODIUM_CHLORIDE.get()));
        if (rolls.rawOre()) {
            out.add(SaltDecomposerRecipes.rollRawOre(random));
        }
        return out;
    }

    private void resetProgress() {
        if (this.progress != 0 || this.progressMax != 0) {
            this.progress = 0;
            this.progressMax = 0;
            setChanged();
        }
    }

    /** 按方案把一样产物写进输出槽（{@code setStackInSlot} 不查 {@code isItemValid}）。 */
    private void applyPlan(ItemStack stack, int[] plan) {
        if (stack.isEmpty()) {
            return;
        }
        for (int slot = OUTPUT_FIRST; slot < SLOT_COUNT; slot++) {
            if (plan[slot] <= 0) {
                continue;
            }
            ItemStack existing = this.items.getStackInSlot(slot);
            if (existing.isEmpty()) {
                this.items.setStackInSlot(slot, stack.copyWithCount(plan[slot]));
            } else {
                this.items.setStackInSlot(slot, existing.copyWithCount(existing.getCount() + plan[slot]));
            }
        }
    }

    /**
     * 一次性给几样产物**算好各自落哪几个槽**（模拟占用，不写盘）；任一样放不下就返回 {@code null}。
     *
     * <p><b>为什么要"模拟占用"而不是每样单独问一遍"现在放得下吗"</b>（第一版就是这么写的，是错的）：
     * 单独问的话三样都会看到<b>同一批空槽</b>，于是"三样都放得下"可能是假象 ——
     * 实际写入时第一样把空槽占了、后两样没地方，而调用方已经扣掉了输入 = <b>吞产物</b>。
     * 这里用 {@code used[槽][第几样]} 记账，判断与写入用的是同一套账。</p>
     *
     * @return 与 {@code stacks} 等长的计划数组；放不下返回 {@code null}
     */
    private int[][] planAll(List<ItemStack> stacks) {
        int[][] plans = new int[stacks.size()][];
        int[][] used = new int[SLOT_COUNT][];
        for (int s = 0; s < stacks.size(); s++) {
            ItemStack stack = stacks.get(s);
            int[] plan = new int[SLOT_COUNT];
            if (stack.isEmpty()) {
                plans[s] = plan;
                continue;
            }
            int remaining = stack.getCount();
            for (int slot = OUTPUT_FIRST; slot < SLOT_COUNT && remaining > 0; slot++) {
                ItemStack existing = this.items.getStackInSlot(slot);
                int takenHere = 0;
                if (used[slot] != null) {
                    for (int v : used[slot]) {
                        takenHere += v;
                    }
                }
                int space;
                if (existing.isEmpty()) {
                    space = Math.min(stack.getMaxStackSize(), this.items.getSlotLimit(slot)) - takenHere;
                } else if (ItemStack.isSameItemSameComponents(existing, stack)) {
                    space = Math.min(existing.getMaxStackSize(), this.items.getSlotLimit(slot))
                            - existing.getCount() - takenHere;
                } else {
                    space = 0;
                }
                int moved = Math.max(0, Math.min(space, remaining));
                plan[slot] = moved;
                remaining -= moved;
                if (moved > 0) {
                    if (used[slot] == null) {
                        used[slot] = new int[stacks.size()];
                    }
                    used[slot][s] = moved;
                }
            }
            if (remaining > 0) {
                return null;
            }
            plans[s] = plan;
        }
        return plans;
    }

    // ================= MenuProvider =================
    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.salt_decomposer");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new SaltDecomposerMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.progress = tag.getInt("progress");
        this.progressMax = tag.getInt("progressMax");
        this.status = tag.getInt("status");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("progress", this.progress);
        tag.putInt("progressMax", this.progressMax);
        tag.putInt("status", this.status);
        tag.put("inventory", this.items.serializeNBT(registries));
    }
}
