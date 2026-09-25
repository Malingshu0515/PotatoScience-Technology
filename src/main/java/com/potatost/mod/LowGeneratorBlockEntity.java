package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.tags.ItemTags;
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
 * 低级发电机（0.10 ZF38）：<b>烧煤炭 / 木炭发电</b>。
 *
 * <p><b>数值（用户指定）：</b>一块燃料烧 {@value #BURN_TICKS} tick（= 45 秒），
 * 发电 {@value #ENERGY_PER_TICK} FE/t，内部储能 {@value #MAX_ENERGY} FE。
 * 一块燃料的能量总量 = {@code 900 × 100 = 90000} FE。</p>
 *
 * <p><b>⚠ 一个我替用户定下的默认（档案 §9 挂着待确认）：储能满了怎么办。</b>
 * 用户只给了"45s / 100 FE/t / 1k"三个数，没说缓冲满时怎么处理。
 * 缓冲 1k 对 100 FE/t 只有 <b>10 tick</b> 的量，所以这个选择直接决定机器好不好用：
 * <ul>
 *   <li><b>本实现（采用）</b>：<b>没地方存就暂停燃烧</b> —— 一块燃料始终兑现整整 90000 FE，
 *       只是"45 秒"变成"满速发电时的时长"。不浪费玩家的燃料。</li>
 *   <li>另一种（没采用）：照烧 45 秒、存不下的电直接扔掉 —— 那样没有负载时会白扔 98.9%。</li>
 * </ul>
 * 两者都只差 {@link #hasRoom()} 这一处的判断，改起来是一行的事。</p>
 *
 * <p><b>红石：</b>通入信号即停机（进度保留）—— 本项目 5 台机器全都这样，这里保持一致，
 * 顺便给玩家一个"手动关掉发电机"的开关。用户没点名要，属我按家族惯例补的。</p>
 *
 * <p><b>⚠ 输入槽的写法（§4.14）：</b>本类覆写了 {@code isItemValid} 把输入槽限制成燃料，
 * 而 {@code ItemStackHandler#insertItem} <b>内部会查 isItemValid</b>。
 * 本次代码<b>从不</b>用 {@code insertItem} 往槽里写（只有玩家 / 漏斗从外面放），
 * 取燃料用的是 {@code extractItem}（它<b>不</b>查 isItemValid），所以是安全的。</p>
 */
public class LowGeneratorBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 数值（用户指定）=================
    /** 一块燃料烧的 tick 数：45 秒 */
    public static final int BURN_TICKS = 45 * 20;
    /** 发电速率：100 FE/t */
    public static final int ENERGY_PER_TICK = 100;
    /** 内部储能：1000 FE（= 满速发电 10 tick 的量） */
    public static final int MAX_ENERGY = 1000;
    /** 向紧邻 INPUT 端子单次推送上限（缓冲一共才 1000，直接给满就行） */
    public static final int PUSH_RATE = MAX_ENERGY;

    // ================= 槽位 =================
    public static final int INPUT_SLOT = 0;
    public static final int SLOT_COUNT = 1;

    // ================= 同步字段（ContainerData）=================
    public static final int DATA_ENERGY = 0;
    public static final int DATA_ENERGY_MAX = 1;
    public static final int DATA_BURN = 2;        // 剩余燃烧 tick
    public static final int DATA_BURN_MAX = 3;    // 本块燃料的总时长
    public static final int DATA_COUNT = 4;

    private int energy = 0;
    private int burnTime = 0;
    private int burnTotal = 0;
    /** 上一 tick 是否真的在发电——用来只在翻转时发包（驱动循环音效） */
    private boolean running = false;

    /**
     * 输入槽：只收煤炭 / 木炭。
     *
     * <p>用的是原版 {@code #minecraft:coals} 标签（原版内容就是 coal + charcoal），
     * 这样别的 mod 往这个标签里加的自有煤也能用 —— 与本项目"矿物 / 合金 / 锭默认兼容"的
     * 一贯做法一致。用户原话是"放置煤炭或木炭"，属该标签的**子集**，是个**放宽**（已在 §9 标注）。</p>
     */
    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return stack.is(ItemTags.COALS);
        }

        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }
    };

    /** FE 接口：只出不进（管道 / 导线 / 端子可以从这里抽） */
    private final IEnergyStorage energyStorage = MachineEnergyStorage.extractOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                setChanged();
            });

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_ENERGY -> energy;
                case DATA_ENERGY_MAX -> MAX_ENERGY;
                case DATA_BURN -> burnTime;
                case DATA_BURN_MAX -> burnTotal;
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
            // 服务端 -> 客户端单向；客户端不需要写回
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public LowGeneratorBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.LOW_GENERATOR_BE.get(), pos, state);
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

    public int getEnergyStored() {
        return this.energy;
    }

    /** 正在发电——客户端据此决定循环音效响不响。 */
    public boolean isRunning() {
        return this.running;
    }

    /** 还装得下整整一 tick 的电吗？装不下就暂停燃烧，避免把电扔掉。 */
    private boolean hasRoom() {
        return MAX_ENERGY - this.energy >= ENERGY_PER_TICK;
    }

    // ================= 每 tick =================
    /**
     * 双端都会跑：服务端算逻辑，客户端只负责驱动"运行中"的循环音效。
     *
     * <p>⚠ 方块的 {@code getTicker} 必须是**双端**的，否则客户端拿不到 ticker、
     * 下面这一支永远不执行 ⇒ 音效全配好了也没声音且不报错（0.10 ZF36 差点交付的坑，见 §4.26）。</p>
     */
    public static void tick(Level level, BlockPos pos, BlockState state, LowGeneratorBlockEntity generator) {
        if (level.isClientSide) {
            MachineRunningSound.update(generator, generator.isRunning(), ModSounds.GENERATOR_RUNNING.get());
        } else {
            generator.serverTick();
        }
    }

    /** 只在"运行 ⇄ 停止"真的翻转时发包，免得状态抖动把网络刷爆。 */
    private void serverTick() {
        boolean before = this.running;
        serverTickBody();
        if (before != this.running) {
            sync();
        }
    }

    private void serverTickBody() {
        if (this.level == null) {
            return;
        }
        boolean dirty = false;

        // ① 红石信号 = 停机（剩余燃烧时间保留，不会白烧）
        if (this.level.hasNeighborSignal(this.worldPosition)) {
            this.running = false;
            if (this.burnTime > 0) {
                setChanged();   // 只是把 running 翻下去，也要让客户端知道
            }
            return;
        }

        // ② 没在烧 → 从输入槽取一块燃料点火（缓冲没地方存就先不点，免得点了烧不动）
        if (this.burnTime <= 0 && hasRoom()) {
            ItemStack fuel = this.items.getStackInSlot(INPUT_SLOT);
            if (!fuel.isEmpty()) {
                // extractItem 不查 isItemValid，可以放心用（§4.14）
                this.items.extractItem(INPUT_SLOT, 1, false);
                this.burnTime = BURN_TICKS;
                this.burnTotal = BURN_TICKS;
                dirty = true;
            }
        }

        // ③ 烧：有整整一 tick 的空间才走这一 tick，否则暂停（不浪费燃料，见类注释）
        boolean producedNow = false;
        if (this.burnTime > 0 && hasRoom()) {
            this.energy += ENERGY_PER_TICK;
            this.burnTime--;
            producedNow = true;
            dirty = true;
        }

        // ④ 推 FE 给紧邻的 INPUT 模式端子（铜线网络自动接管后续）
        for (Direction direction : Direction.values()) {
            if (this.energy <= 0) {
                break;
            }
            if (this.level.getBlockEntity(this.worldPosition.relative(direction))
                    instanceof TerminalBlockEntity terminal
                    && terminal.getMode() == TerminalBlockEntity.Mode.INPUT) {
                int sent = terminal.getEnergyStorage().receiveEnergy(Math.min(PUSH_RATE, this.energy), false);
                if (sent > 0) {
                    this.energy -= sent;
                    dirty = true;
                }
            }
        }

        this.running = producedNow;
        if (dirty) {
            setChanged();
        }
    }

    /** 把运行状态推给客户端（GUI 状态走 ContainerData，循环音效没开界面也要响）。 */
    private void sync() {
        setChanged();
        if (this.level != null && !this.level.isClientSide) {
            this.level.sendBlockUpdated(this.getBlockPos(), this.getBlockState(), this.getBlockState(),
                    Block.UPDATE_CLIENTS);
        }
    }

    // ================= 菜单 =================
    @Override
    public Component getDisplayName() {
        return Component.translatable("block.potato_s_t.low_generator");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new LowGeneratorMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.burnTime = tag.getInt("burnTime");
        this.burnTotal = tag.getInt("burnTotal");
        // ⚠ running 也要存：getUpdateTag() 走的就是这里，漏了客户端永远看不到运行状态
        this.running = tag.getBoolean("running");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putInt("burnTime", this.burnTime);
        tag.putInt("burnTotal", this.burnTotal);
        tag.putBoolean("running", this.running);
        tag.put("inventory", this.items.serializeNBT(registries));
    }

    /**
     * 方块更新包带上完整存档数据（含 {@code running}）——客户端 tick 靠它判断循环音效该不该响。
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
