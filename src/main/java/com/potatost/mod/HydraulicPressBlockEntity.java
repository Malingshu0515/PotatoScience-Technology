package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.items.ItemStackHandler;

import com.potatost.mod.client.sound.MachineRunningSound;
import com.potatost.mod.sound.ModSounds;

/**
 * 液压机（0.10 ZF30）：把<b>矿物锭锻压成板材</b>。
 *
 * <p><b>数值（用户指定）：</b>400 FE/t × 3 秒 = {@value #DURATION_TICKS} tick 一块板，
 * 一块板共 {@code 400 × 60 = 24000} FE。内部缓冲正好 {@value #MAX_ENERGY} FE
 * ⇒ <b>满电刚好能压完一整块板</b>，中途断供就停在当前进度等电（进度保留）。</p>
 *
 * <p><b>结构照抄微型粉碎机</b>（那台已经把"吞产物"的坑踩平了）：
 * 1 个输入槽 + 1 个输出槽；红石信号 = 关机；输出放不下就卡在满进度等位置、
 * <b>绝不吞产物</b>；换输入物品则进度清零。</p>
 *
 * <p><b>⚠ 两条必须照抄的理由（都是本项目流过的血）：</b></p>
 * <ol>
 *   <li>{@code ItemStackHandler#insertItem} <b>内部会查 {@code isItemValid}</b>，
 *       而本类为了挡住自动化往输出槽塞东西把那道门禁关上了 ⇒ 自己写产物<b>必须</b>走
 *       {@link #planInsert} + {@code setStackInSlot}，否则产物静默消失（§4.14）；</li>
 *   <li>{@code onRemove} 里必须把两个槽都掉出来，且**要在 {@code super.onRemove} 之前**
 *       取到方块实体（§4.13）。</li>
 * </ol>
 */
public class HydraulicPressBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 数值 =================
    /** 内部缓冲（= 一块板的全部耗电，满电刚好压完一块） */
    public static final int MAX_ENERGY = PressRecipes.DURATION_TICKS * PressRecipes.ENERGY_PER_TICK;

    public static final int INPUT_SLOT = 0;
    public static final int OUTPUT_SLOT = 1;
    public static final int SLOT_COUNT = 2;

    // ContainerData 索引
    public static final int DATA_ENERGY = 0;
    public static final int DATA_PROGRESS = 1;
    public static final int DATA_PROGRESS_MAX = 2;
    public static final int DATA_STATUS = 3;
    public static final int DATA_COUNT = 4;

    // ================= 状态灯（客户端据此上色，见 client.gui.parts.StatusLampPart） =================
    /** 红石信号 → 关机：黄灯 */
    public static final int STATUS_DISABLED = 0;
    /** 输入槽空：黄灯 */
    public static final int STATUS_EMPTY = 1;
    /** 输入物品不是可压的锭：黄灯 */
    public static final int STATUS_INVALID = 2;
    /** 有配方但电不够：红灯 */
    public static final int STATUS_NO_POWER = 3;
    /** 输出槽放不下：黄灯 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在压：绿灯 */
    public static final int STATUS_RUNNING = 5;
    /**
     * 材料数量不够（0.11 ZF79：沥青要 12 个才能压一块柏油块）：黄灯。
     *
     * <p>语义与"输入槽空"不同 —— 那是没东西、进度清零；这里是**有东西但还不够**，
     * 所以进度**保留**（跟断电一样，摆够了接着压）。</p>
     */
    public static final int STATUS_MATERIAL = 6;

    private int energy;
    private int progress;
    private int progressMax;
    /** 服务端每 tick 刷新，仅供 GUI（不存盘） */
    private int status = STATUS_EMPTY;
    /** 当前进度对应的输入物品（注册名）。换物品要清零进度；存盘避免读档后进度凭空归零。 */
    private String progressItem = "";

    /**
     * 0 号输入、1 号输出。输出槽不接受玩家放置，也不接受自动化灌入 ——
     * 理由见类注释第 1 条（这条门禁正是"必须自己算产物落哪"的根源）。
     */
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

    /** 只收不放的能量缓冲（复用 0.09 的公共件，别再抄匿名实现）。 */
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

    public HydraulicPressBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.HYDRAULIC_PRESS_BE.get(), pos, state);
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
    /**
     * 双端都会跑：服务端算逻辑，客户端只负责驱动"运行中"的循环液压声（0.10 ZF36）。
     *
     * <p>客户端 tick 读的 {@link #status} 是服务端经 {@link #getUpdateTag()} 同步过来的（见 {@link #sync()}）
     * —— 与微型粉碎机 / 电解器 / 发电机同一套做法。</p>
     */
    public static void tick(Level level, BlockPos pos, BlockState state, HydraulicPressBlockEntity press) {
        if (level.isClientSide) {
            MachineRunningSound.update(press, press.isRunning(), ModSounds.HYDRAULIC_PRESS_RUNNING.get());
        } else {
            press.serverTick();
        }
    }

    /** 正在压制中——客户端据此决定循环音效响不响。 */
    public boolean isRunning() {
        return this.status == STATUS_RUNNING;
    }

    /** 只在"运行 ⇄ 停止"真的翻转时发包，免得状态抖动把网络刷爆。 */
    private void serverTick() {
        boolean before = isRunning();
        serverTickBody();
        if (before != isRunning()) {
            sync();
        }
    }

    /**
     * 把运行状态推给客户端。
     *
     * <p>GUI 状态灯走的是 {@code ContainerData}（只在界面打开时同步），而循环音效**没开界面也要响**，
     * 所以运行状态得另外走一次方块更新。</p>
     */
    private void sync() {
        this.setChanged();
        if (this.level != null && !this.level.isClientSide) {
            this.level.sendBlockUpdated(this.getBlockPos(), this.getBlockState(), this.getBlockState(),
                    Block.UPDATE_CLIENTS);
        }
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

        // ② 输入槽决定配方
        ItemStack input = this.items.getStackInSlot(INPUT_SLOT);
        if (input.isEmpty()) {
            resetProgress();
            this.status = STATUS_EMPTY;
            return;
        }
        PressRecipes.Recipe recipe = PressRecipes.find(input);
        if (recipe == null) {
            resetProgress();
            this.status = STATUS_INVALID;
            return;
        }

        // ②b 数量够不够（ZF79：沥青要 12 个）——不够就等，**进度保留**
        if (!recipe.hasEnough(input)) {
            this.status = STATUS_MATERIAL;
            return;
        }

        // ③ 换了输入物品 → 进度清零（防止半途换料白嫖进度）
        String id = BuiltInRegistries.ITEM.getKey(input.getItem()).toString();
        if (!id.equals(this.progressItem)) {
            this.progress = 0;
            this.progressItem = id;
        }
        this.progressMax = PressRecipes.DURATION_TICKS;

        // ④ 已到点：只等输出腾位置（不扣电、不丢产物）
        if (this.progress >= this.progressMax) {
            this.status = finish(recipe) ? STATUS_RUNNING : STATUS_OUTPUT_FULL;
            setChanged();
            return;
        }

        // ⑤ 未到点：先看电，再看输出余量
        if (this.energy < PressRecipes.ENERGY_PER_TICK) {
            this.status = STATUS_NO_POWER;
            return;
        }
        if (!canInsert(recipe.createOutput())) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }

        this.energy -= PressRecipes.ENERGY_PER_TICK;
        this.progress++;
        this.status = STATUS_RUNNING;
        if (this.progress >= this.progressMax && !finish(recipe)) {
            this.status = STATUS_OUTPUT_FULL;
        }
        setChanged();
    }

    /** 输入槽没了/不可压时把进度归零（只在真的需要时落盘）。 */
    private void resetProgress() {
        if (this.progress != 0 || this.progressMax != 0) {
            this.progress = 0;
            this.progressMax = 0;
            setChanged();
        }
        this.progressItem = "";
    }

    /**
     * 结算一轮：放得下才消耗输入。
     *
     * @return true = 成功产出并消耗了 {@code recipe.inputCount()} 个输入；
     *         false = 输出槽放不下，进度停在满格等位置
     */
    private boolean finish(PressRecipes.Recipe recipe) {
        if (this.level == null) {
            return false;
        }
        ItemStack output = recipe.createOutput();
        // ★ 先算好放几件，算不下就原地不动（既不扣输入也不吞产物）
        int[] plan = planInsert(output);
        if (plan == null) {
            return false;
        }
        for (int slot = OUTPUT_SLOT; slot < SLOT_COUNT; slot++) {
            if (plan[slot] <= 0) {
                continue;
            }
            ItemStack existing = this.items.getStackInSlot(slot);
            if (existing.isEmpty()) {
                this.items.setStackInSlot(slot, output.copyWithCount(plan[slot]));
            } else {
                this.items.setStackInSlot(slot, existing.copyWithCount(existing.getCount() + plan[slot]));
            }
        }
        // ⚠ 消耗的数量跟着配方走（ZF79 起 1 或 12）—— 原先写死 1
        this.items.extractItem(INPUT_SLOT, recipe.inputCount(), false);
        this.progress = 0;
        this.progressItem = "";
        return true;
    }

    /** 输出槽能不能完整装下这堆东西（= {@link #planInsert} 算得出方案）。 */
    private boolean canInsert(ItemStack stack) {
        return planInsert(stack) != null;
    }

    /**
     * 第一遍只算不写：每个输出槽各放多少件；放不下返回 {@code null}。
     *
     * <p><b>⚠ 为什么不用 {@code ItemStackHandler#insertItem}</b>：它内部会查
     * {@code isItemValid}，而本机器把输出槽那道门禁关上了 ⇒ 会**静默失败**：
     * 返回的 remainder 原封不动，产物没进去，但输入已被扣掉 = 吞物品（§4.14 的原始事故）。
     * 同一份空间公式既用于"算得下吗"也用于"实际写入"，从结构上不可能两边打架。</p>
     */
    private int[] planInsert(ItemStack stack) {
        int[] plan = new int[SLOT_COUNT];
        int remaining = stack.getCount();
        for (int slot = OUTPUT_SLOT; slot < SLOT_COUNT && remaining > 0; slot++) {
            ItemStack existing = this.items.getStackInSlot(slot);
            int space;
            if (existing.isEmpty()) {
                space = Math.min(stack.getMaxStackSize(), this.items.getSlotLimit(slot));
            } else if (ItemStack.isSameItemSameComponents(existing, stack)) {
                space = Math.min(existing.getMaxStackSize(), this.items.getSlotLimit(slot)) - existing.getCount();
            } else {
                space = 0;
            }
            int moved = Math.min(space, remaining);
            plan[slot] = moved;
            remaining -= moved;
        }
        return remaining > 0 ? null : plan;
    }

    // ================= MenuProvider =================
    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.hydraulic_press");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new HydraulicPressMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.progress = tag.getInt("progress");
        this.progressMax = tag.getInt("progressMax");
        this.progressItem = tag.getString("progressItem");
        this.status = tag.getInt("status");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("progress", this.progress);
        tag.putInt("progressMax", this.progressMax);
        tag.putString("progressItem", this.progressItem);
        tag.putInt("status", this.status);
        tag.put("inventory", this.items.serializeNBT(registries));
    }

    /**
     * 方块更新包带上完整存档数据（含 {@code status}）——客户端 tick 靠它判断循环音效该不该响。
     * 只在运行状态翻转时才会发（见 {@link #serverTick()}）。
     *
     * <p>⚠ {@code status} 必须同时在 {@link #loadAdditional} 里读回来，否则客户端永远看到默认值，
     * 循环音效一次都不会响（微型粉碎机 0.10 自查时抓到过这个坑）。</p>
     */
    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        return saveWithoutMetadata(registries);
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
