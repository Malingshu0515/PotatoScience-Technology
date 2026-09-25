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
 * 微型粉碎机（0.10 新增）：左侧 1 个输入槽，右侧 3 个输出槽，内置 2500 FE 缓冲。
 *
 * <p><b>工作规则：</b>
 * <ul>
 *   <li><b>红石信号 = 关机</b>（有信号停机，进度保留；无信号才工作）；</li>
 *   <li>每个 tick 扣 {@code energyPerTick} FE，进度 +1；电不够就停住等电（进度保留）；</li>
 *   <li>产物数量在完成那一刻随机（见 {@link MicroCrusherRecipes.Crush}）；</li>
 *   <li>输出槽放不下时卡在满进度等位置，<b>不会吞产物</b>；</li>
 *   <li>换掉输入物品 → 进度清零（防止半途换料白嫖进度）。</li>
 * </ul>
 *
 * <p>缓冲只有 2500 FE，而最费的配方 400 FE/t，所以必须持续供电才跑得动——
 * 这是设计意图（对应"有信号时关闭/没电亮红灯"的玩法）。</p>
 */
public class MicroCrusherBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 数值 =================
    public static final int MAX_ENERGY = 2500;              // 2.5k FE 缓冲

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

    // ================= 状态灯（客户端据此上色，见 client.gui.parts.StatusLampPart） =================
    /** 红石信号 → 关机：黄灯 */
    public static final int STATUS_DISABLED = 0;
    /** 输入槽空：黄灯 */
    public static final int STATUS_EMPTY = 1;
    /** 输入槽物品不可粉碎：黄灯 */
    public static final int STATUS_INVALID = 2;
    /** 配方有效但电不够：红灯 */
    public static final int STATUS_NO_POWER = 3;
    /** 输出槽放不下：黄灯 */
    public static final int STATUS_OUTPUT_FULL = 4;
    /** 正在粉碎：绿灯 */
    public static final int STATUS_RUNNING = 5;

    private int energy;
    private int progress;
    private int progressMax;
    /** 服务端每 tick 刷新，仅供 GUI（不存盘） */
    private int status = STATUS_EMPTY;
    /**
     * 当前进度对应的输入物品（注册名字符串）。换物品要清零进度；
     * <b>存盘</b>是为了避免读档/区块卸载后进度凭空归零。
     */
    private String progressItem = "";

    /**
     * 0 号槽是输入，1~3 号槽是输出（输出槽不接受玩家放置，也不接受自动化灌入）。
     *
     * <p><b>⚠ 这个覆写对"自己也生效"：</b>{@code ItemStackHandler#insertItem} 内部会查
     * {@code isItemValid}，所以本类自己往输出槽写产物时<b>绝不能用 {@code insertItem}</b>
     * ——会被静默拒绝，产物没进去但输入已经扣掉了（= 吞物品）。必须走
     * {@link #planInsert} + {@code setStackInSlot}。Audit 的 I 项专盯这个组合。</p>
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

    /** 只收不放的能量缓冲（复用 0.09 提取的公共件，别再抄匿名实现）。 */
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

    public MicroCrusherBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.MICRO_CRUSHER_BE.get(), pos, state);
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
     * 双端都会跑：服务端算逻辑，客户端只负责驱动"运行中"的循环音效。
     *
     * <p>客户端 tick 读的 {@link #status} 是服务端经 {@link #getUpdateTag()} 同步过来的（见 {@link #sync()}）。</p>
     */
    public static void tick(Level level, BlockPos pos, BlockState state, MicroCrusherBlockEntity crusher) {
        if (level.isClientSide) {
            MachineRunningSound.update(crusher, crusher.isRunning(), ModSounds.MICRO_CRUSHER_RUNNING.get());
        } else {
            crusher.serverTick();
        }
    }

    /** 正在粉碎中——客户端据此决定循环音效响不响。 */
    public boolean isRunning() {
        return this.status == STATUS_RUNNING;
    }

    /**
     * 把运行状态推给客户端。
     *
     * <p>GUI 状态灯走的是 {@code ContainerData}（只在界面打开时同步），而循环音效**没开界面也要响**，
     * 所以运行状态得另外走一次方块更新——与电解器 / 发电机同一套做法。</p>
     */
    private void sync() {
        this.setChanged();
        if (this.level != null && !this.level.isClientSide) {
            this.level.sendBlockUpdated(this.getBlockPos(), this.getBlockState(), this.getBlockState(),
                    Block.UPDATE_CLIENTS);
        }
    }

    /** 只在"运行 ⇄ 停止"真的翻转时发包，免得状态抖动把网络刷爆。 */
    private void serverTick() {
        boolean before = isRunning();
        serverTickBody();
        if (before != isRunning()) {
            sync();
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
        MicroCrusherRecipes.Crush crush = MicroCrusherRecipes.find(input);
        if (crush == null) {
            resetProgress();
            this.status = STATUS_INVALID;
            return;
        }

        // ③ 换了输入物品 → 进度清零
        String id = BuiltInRegistries.ITEM.getKey(input.getItem()).toString();
        if (!id.equals(this.progressItem)) {
            this.progress = 0;
            this.progressItem = id;
        }
        this.progressMax = crush.durationTicks();

        // ④ 已到点：只等输出腾位置（不扣电、不丢产物）
        if (this.progress >= this.progressMax) {
            this.status = finish(crush) ? STATUS_RUNNING : STATUS_OUTPUT_FULL;
            setChanged();
            return;
        }

        // ⑤ 未到点：先看电，再看输出余量
        if (this.energy < crush.energyPerTick()) {
            this.status = STATUS_NO_POWER;
            return;
        }
        if (!canInsert(new ItemStack(crush.result(), crush.countMin()))) {
            this.status = STATUS_OUTPUT_FULL;
            return;
        }

        this.energy -= crush.energyPerTick();
        this.progress++;
        this.status = STATUS_RUNNING;
        if (this.progress >= this.progressMax && !finish(crush)) {
            this.status = STATUS_OUTPUT_FULL;
        }
        setChanged();
    }

    /** 输入槽没了/不可粉碎时把进度归零（只在真的需要时落盘）。 */
    private void resetProgress() {
        if (this.progress != 0 || this.progressMax != 0) {
            this.progress = 0;
            this.progressMax = 0;
            setChanged();
        }
        this.progressItem = "";
    }

    /**
     * 结算一轮：滚产物 → 放得下才消耗输入。
     *
     * @return true = 成功产出并消耗了 1 个输入；false = 输出槽放不下，进度停在满格等位置
     */
    private boolean finish(MicroCrusherRecipes.Crush crush) {
        if (this.level == null) {
            return false;
        }
        ItemStack output = crush.createOutput(this.level.random);
        // ★ 先算好每一槽放几件，算不下就原地不动（既不扣输入也不吞产物）
        int[] plan = planInsert(output);
        if (plan == null) {
            return false;
        }
        applyInsert(output, plan);
        this.items.extractItem(INPUT_SLOT, 1, false);
        this.progress = 0;
        this.progressItem = "";
        return true;
    }

    /** 这 3 个输出槽能不能完整装下这堆东西（= {@link #planInsert} 算得出方案）。 */
    private boolean canInsert(ItemStack stack) {
        return planInsert(stack) != null;
    }

    /**
     * 第一遍只算不写：每个输出槽各放多少件；放不下返回 {@code null}。
     *
     * <p><b>⚠ 为什么不用 {@code ItemStackHandler#insertItem}（0.10 出过的血）：</b>
     * {@code insertItem} <b>内部会查 {@code isItemValid}</b>，而本机器为了挡住自动化往产物槽塞东西，
     * 把 {@code isItemValid} 写成了"只有输入槽为真"。于是往输出槽 {@code insertItem} 会<b>静默失败</b>：
     * 返回的 remainder 原封不动，产物没进去，但 {@code finish()} 已经扣掉了输入 —— 直接吞物品。
     * 改成自己算 + {@code setStackInSlot} 直写（和电解器/晒盐机的做法一致）。
     * 同一份空间公式既用于"算得下吗"也用于"实际写入"，从结构上不可能两边打架。</p>
     */
    private int[] planInsert(ItemStack stack) {
        int[] plan = new int[SLOT_COUNT];
        int remaining = stack.getCount();
        for (int slot = OUTPUT_FIRST; slot < SLOT_COUNT && remaining > 0; slot++) {
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

    /** 第二遍按方案落盘；{@code setStackInSlot} 不查 isItemValid，所以不会被门禁挡掉。 */
    private void applyInsert(ItemStack stack, int[] plan) {
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

    // ================= MenuProvider =================
    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.micro_crusher");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new MicroCrusherMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.progress = tag.getInt("progress");
        this.progressMax = tag.getInt("progressMax");
        this.progressItem = tag.getString("progressItem");
        // status 也要存：它同时是"运行中"的同步载体——getUpdateTag() 走的就是这里，
        // 漏掉它客户端永远看不到运行状态，循环音效一次都不会响（0.10 自查时抓到的坑）。
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
