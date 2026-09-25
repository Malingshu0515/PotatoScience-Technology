package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.Item;
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
 * 合金冶炼炉的控制器方块实体（0.10 ZF49）。
 *
 * <p><b>用户给的数</b>：储能 <b>32k FE</b>（{@value #MAX_ENERGY}）、
 * <b>5 个输入槽</b>（只能放"锭"，按 {@code c:ingots} 标签认）、<b>3 个输出槽</b>、
 * <b>2 个消耗槽</b>（用户原话「目前放不了东西 以后出类似于沉浸电弧炉石墨电极的东西」——
 * 所以这两个槽现在 {@code isItemValid} 恒为 false）。</p>
 *
 * <p><b>本阶段不做配方</b>（用户原话：「先不做配方」）⇒ tick 里目前什么都不烧，
 * 只有"结构还在不在"的复查。配方的位置已经留好：见 {@link #serverTick}。</p>
 */
public class AlloySmelterBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 数值 =================
    /** 储能 32k（用户指定）。 */
    public static final int MAX_ENERGY = 32 * 1024;

    /**
     * 配方参数（0.10 ZF62）：一轮 {@value #DURATION_TICKS} tick（30 秒）、每 tick {@value #ENERGY_PER_TICK} FE。
     * 数值来自用户原话「铝+钛+银在合金冶炼炉 30s 5800fe/t产出一个 轻质钛合金」——
     * 一件总耗电 5800 × 600 = <b>3,480,000 FE</b>（照字面值实现）。
     */
    public static final int DURATION_TICKS = AlloySmelterRecipes.DURATION_TICKS;
    public static final int ENERGY_PER_TICK = AlloySmelterRecipes.ENERGY_PER_TICK;

    /**
     * ⚠ <b>单 tick 耗电绝不能超过储能</b>（ZF42 的教训：电力高炉曾经"满负载永远跑不起来"）。
     *
     * <p>本机一次只做一份（不并行），所以最坏情况就是这一条配方的每 tick 耗电：
     * {@code 5800 ≤ 32768} ✓。仍然写成静态断言 —— 以后加并行或调大数字时，一旦越界，
     * 控制台会直接喊出来（英文：Audit 的 E 项是文本级检查，不许出现中文字符串）。</p>
     */
    static {
        long worstDemand = ENERGY_PER_TICK;
        if (worstDemand > MAX_ENERGY) {
            System.err.println("[potato_s_t] Alloy Smelter is misconfigured: worst-case draw "
                    + worstDemand + " FE/t exceeds its " + MAX_ENERGY + " FE buffer, so a craft "
                    + "will never run. Raise MAX_ENERGY or lower ENERGY_PER_TICK.");
        }
    }

    // ================= 槽位 =================
    public static final int INPUT_FIRST = 0;
    public static final int INPUT_COUNT = 5;
    public static final int OUTPUT_FIRST = INPUT_FIRST + INPUT_COUNT;
    public static final int OUTPUT_COUNT = 3;
    /** 消耗槽（石墨电极那种）：**现在锁死**，以后放开。 */
    public static final int CONSUME_FIRST = OUTPUT_FIRST + OUTPUT_COUNT;
    public static final int CONSUME_COUNT = 2;
    public static final int SLOT_COUNT = CONSUME_FIRST + CONSUME_COUNT;   // = 10

    // ================= 同步字段 =================
    public static final int DATA_ENERGY = 0;
    public static final int DATA_ENERGY_MAX = 1;
    public static final int DATA_FORMED = 2;
    public static final int DATA_PROGRESS = 3;
    public static final int DATA_COUNT = 4;

    /**
     * "只能放锭"用的标签：{@code #c:ingots}。
     *
     * <p>用通用标签而不是自己列一串 id —— 用户原话就是「只能接受<b>锭标签</b>」，
     * 而且本项目自己的 7 种锭本来就在这个标签里（见 {@code GenCommonTags.py}）。</p>
     */
    private static final TagKey<Item> INGOTS = TagKey.create(Registries.ITEM,
            ResourceLocation.fromNamespaceAndPath("c", "ingots"));

    private int energy = 0;
    /** 结构是否成立（成型才开界面/才收电，破坏任意一格就自动失效）。 */
    private boolean formed = false;
    /** 当前这一轮的进度（0..{@link #DURATION_TICKS}）；没配方/产出堵住时归零，<b>电不够时原地不动</b>。 */
    private int progress = 0;

    /**
     * 这一 tick 真的在烧（扣了电、推进了进度）——<b>客户端据此决定循环电机声响不响</b>（ZF64）。
     *
     * <p>客户端看不到服务端的 {@link #progress}：{@code ContainerData} 只在界面开着的时候同步，
     * 而循环音效<b>不开界面也得响</b>。所以运行状态得像微型粉碎机那样另走一次方块更新
     * （{@code getUpdateTag} 里带上它，见 {@link #sync()}），并且只在"运行 ⇄ 停止"翻转时发包。</p>
     */
    private boolean running = false;
    /** 拆解期间的重入闸门（换方块会触发它们自己的 onRemove）。 */
    private boolean disassembling = false;
    /** 外壳 68 格的位置与它们**成型前**的方块状态（拆解时原样还原；ZF55 起内部 12 格不入表）。 */
    private final List<BlockPos> cells = new ArrayList<>();
    private final List<BlockState> originals = new ArrayList<>();

    private final IEnergyStorage energyStorage = MachineEnergyStorage.receiveOnly(
            () -> MAX_ENERGY,
            () -> this.energy,
            value -> {
                this.energy = value;
                setChanged();
            });

    private final ItemStackHandler items = new ItemStackHandler(SLOT_COUNT) {
        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            // 没激活 = 一个槽都不收（用户 ZF51：控制器要先激活才能用，匠魂那种）
            if (!formed) {
                return false;
            }
            if (slot >= INPUT_FIRST && slot < INPUT_FIRST + INPUT_COUNT) {
                return stack.is(INGOTS);        // 用户指定：输入槽只收"锭标签"
            }
            return false;                       // 输出槽与消耗槽都不收
        }

        @Override
        protected void onContentsChanged(int slot) {
            setChanged();
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            switch (index) {
                case DATA_ENERGY: return energy;
                case DATA_ENERGY_MAX: return MAX_ENERGY;
                case DATA_FORMED: return formed ? 1 : 0;
                case DATA_PROGRESS: return progress;
                default: return 0;
            }
        }

        @Override
        public void set(int index, int value) {
            // 服务端 -> 客户端单向
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public AlloySmelterBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.ALLOY_SMELTER_BE.get(), pos, state);
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

    /**
     * 没激活就<b>连电都进不来</b>（用户 ZF51：「需要先激活他」）。
     *
     * <p>能力注册那边是 {@code (machine, side) -> machine.getEnergyStorage()}，
     * 返回 {@code null} 就等于"这一面没有能量能力" —— 没激活的控制器灌不进电。</p>
     */
    public IEnergyStorage getEnergyStorage() {
        return this.formed ? this.energyStorage : null;
    }

    public boolean isFormed() {
        return this.formed;
    }

    public boolean isDisassembling() {
        return this.disassembling;
    }

    public Direction facing() {
        return this.getBlockState().getValue(AlloySmelterBlock.FACING);
    }

    /**
     * 成型状态（<b>ZF56 起同时管模型</b>）。
     *
     * <p>数据这一半存在 NBT（{@code formed}），模型那一半存在方块状态
     * （{@link AlloySmelterBlock#FORMED}）—— <b>没成型 = 主控小方块，成型 = 整台 4×5×4 合金炉</b>。
     * 两边必须一起动，所以这里不管值变没变都对齐一次（{@link #applyFormedState}）。</p>
     */
    public void setFormed(boolean value) {
        boolean changed = this.formed != value;
        this.formed = value;
        if (changed) {
            setChanged();
            sync();
        }
        applyFormedState();
    }

    /**
     * 把方块状态里的 {@link AlloySmelterBlock#FORMED} 拉成和 {@link #formed} 一致（模型切换）。
     *
     * <p>⚠ 两个坑：</p>
     * <ol>
     *   <li><b>控制器那格已经不是控制器了就什么都不做</b> —— 这个方法会在
     *       {@code disassemble()} 里被调用，而"挖掉控制器"那条路是
     *       {@code setBlock(空气)} 已经生效后才回调 {@code onRemove} 的，
     *       这里再 {@code setBlock} 一次会把方块**复活**（凭空多一个主控）。</li>
     *   <li>这次 {@code setBlock} 会触发 {@code onPlace} → {@code tryAutoForm}。
     *       成型方向没关系（{@code isFormed()} 已经是 true）；<b>拆解方向很危险</b>：
     *       拆完外壳是"完整"的，自动成型会当场把机器重新装回去
     *       ⇒ 所以 {@link #disassemble} 必须在 {@code disassembling} 还是 true 的时候调它。</li>
     * </ol>
     */
    private void applyFormedState() {
        if (this.level == null || this.level.isClientSide) {
            return;
        }
        BlockState state = this.level.getBlockState(this.worldPosition);
        if (!state.is(ModBlocks.ALLOY_SMELTER.get())) {
            return;                                     // 控制器已经不在了，绝不复活
        }
        if (state.getValue(AlloySmelterBlock.FORMED) != this.formed) {
            // 只发客户端（flag 2）：模型要换，但不必再通知一圈邻居
            this.level.setBlock(this.worldPosition,
                    state.setValue(AlloySmelterBlock.FORMED, this.formed), Block.UPDATE_CLIENTS);
        }
    }

    // ================= 结构 =================
    /**
     * 接线口的位置（<b>ZF55 起由数据推，不再由图纸推</b>）。
     *
     * <p>图纸时代这里是"图上写着 W 的那两格"；现在外壳上<b>任何一个接线块</b>都会变成接线口，
     * 所以直接翻 {@link #cells}/{@link #originals}：成型前是接线块的那些格就是接线口。</p>
     */
    public List<BlockPos> portPositions() {
        List<BlockPos> out = new ArrayList<>(2);
        for (int k = 0; k < this.cells.size(); k++) {
            BlockState original = this.originals.get(k);
            if (original != null && AlloySmelterStructure.isWiring(original)) {
                out.add(this.cells.get(k));
            }
        }
        return out;
    }

    /** 全部 80 格的位置。 */
    public List<BlockPos> allPositions() {
        return AlloySmelterStructure.positions(this.worldPosition, facing());
    }

    /** 这一格**成型前**是什么方块（拆解还原与"破坏掉落原方块"都靠它）。 */
    public BlockState originalAt(BlockPos pos) {
        int k = this.cells.indexOf(pos);
        return k < 0 ? null : this.originals.get(k);
    }

    public boolean isPartOfStructure(BlockPos pos) {
        return this.cells.contains(pos);
    }

    /** 找控制器：给部件格/接线口用（它们自己不存数据，每次现找）。 */
    public static AlloySmelterBlockEntity findMaster(Level level, BlockPos portPos) {
        return findMaster(level, portPos, true);
    }

    /** 任意一格（含部件格）找控制器。 */
    public static AlloySmelterBlockEntity findMasterAt(Level level, BlockPos anyPos) {
        return findMaster(level, anyPos, false);
    }

    private static AlloySmelterBlockEntity findMaster(Level level, BlockPos p, boolean portOnly) {
        for (int dx = -5; dx <= 5; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                for (int dy = -4; dy <= 4; dy++) {
                    BlockPos q = p.offset(dx, dy, dz);
                    if (level.getBlockEntity(q) instanceof AlloySmelterBlockEntity be
                            && (portOnly ? be.portPositions().contains(p) : be.isPartOfStructure(p))) {
                        return be;
                    }
                }
            }
        }
        return null;
    }

    /** 现在就验一遍外壳（成型/复查共用）。 */
    public boolean structureOk() {
        return this.level != null
                && AlloySmelterStructure.shellComplete(this.level, this.worldPosition, facing());
    }

    /**
     * 成型（ZF55 起只动<b>长方体的表面 68 格</b>，而且只动"机器方块"）。
     *
     * <p>逐个换：表面格上每一个<b>接线块</b> → 接线口（贴图一样，但带方块实体 ⇒ 才能挂能量能力）；
     * 其余机器方块 → 部件格（不渲染，整台机器由控制器的 OBJ 长方体画）。</p>
     *
     * <p>三种格<b>不碰也不记账</b>：</p>
     * <ol>
     *   <li><b>内部 12 格</b> —— 判定本来就不看它们，玩家在空腔里放什么就留什么；</li>
     *   <li><b>空着的表面格</b>（图纸的顶面就是个敞口：[空][耐热][耐热][空] + 中间两列也是空的）
     *       —— 没东西可换，换成了部件格反而会凭空多出一层"隐形墙"；</li>
     *   <li><b>控制器自己那格</b> —— 拆解时也不该被还原/清掉（谁挖的谁来清）。</li>
     * </ol>
     *
     * <p>只在<b>结构已经验过</b>（{@link AlloySmelterStructure#inspect} 的 {@code ok()}）之后调用。</p>
     */
    public void form() {
        if (this.level == null || this.level.isClientSide) {
            return;
        }
        // 上一轮的记录要留到最后再丢：记原始方块时要用它解"上一轮留下的部件格"（见 originalFor）。
        List<BlockPos> oldCells = new ArrayList<>(this.cells);
        List<BlockState> oldOriginals = new ArrayList<>(this.originals);
        this.cells.clear();
        this.originals.clear();
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    if (!AlloySmelterStructure.isHull(y, j, i)) {
                        continue;                       // 内部 12 格：不碰也不记
                    }
                    BlockPos p = AlloySmelterStructure.offset(this.worldPosition, facing(), y, j, i);
                    if (p.equals(this.worldPosition)) {
                        continue;                       // 控制器自己那格
                    }
                    BlockState current = this.level.getBlockState(p);
                    if (!AlloySmelterStructure.isWiring(current) && !AlloySmelterStructure.isCasing(current)) {
                        continue;                       // 空着的表面格 / 玩家摆的别的东西
                    }
                    this.cells.add(p);
                    this.originals.add(originalFor(p, oldCells, oldOriginals));
                }
            }
        }
        this.disassembling = true;
        try {
            for (int k = 0; k < this.cells.size(); k++) {
                BlockPos p = this.cells.get(k);
                boolean port = AlloySmelterStructure.isWiring(this.originals.get(k));
                this.level.setBlock(p, port
                        ? ModBlocks.ALLOY_SMELTER_PORT.get().defaultBlockState()
                                .setValue(AlloySmelterPortBlock.FACING, facing())
                        : ModBlocks.ALLOY_SMELTER_PART.get().defaultBlockState(), Block.UPDATE_ALL);
            }
        } finally {
            this.disassembling = false;
        }
        setFormed(true);
    }

    /**
     * 这一格该记成什么"原始方块"。
     *
     * <p>正常情况就是当下那个方块。但有一种脏状态：**上一轮成型留下的部件格还在地图上**
     * ——例如控制器方块实体没加载时那一格被挖掉，{@code findMasterAt} 找不到控制器，
     * 于是只失效没还原。这时<b>绝不能</b>把"部件格/接线口"记成原始方块：
     * 拆解会还出一片**隐形方块**（挖不出、看不见、还占着位置）。
     * 拿上一轮记下的原始方块顶上；记不清就当空气——宁可留个洞，也不留隐形方块。</p>
     */
    private BlockState originalFor(BlockPos p, List<BlockPos> oldCells, List<BlockState> oldOriginals) {
        BlockState current = this.level.getBlockState(p);
        if (current.is(ModBlocks.ALLOY_SMELTER_PART.get()) || current.is(ModBlocks.ALLOY_SMELTER_PORT.get())) {
            int k = oldCells.indexOf(p);
            BlockState remembered = k < 0 ? null : oldOriginals.get(k);
            return remembered != null
                    ? remembered
                    : net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
        }
        return current;
    }

    /**
     * 把<b>成型之后</b>才摆到表面上来的机器方块吸收成部件格（0.10 ZF57）。
     *
     * <p>为什么保留这一步（ZF59 起已经很少用得上）：ZF55 那会儿"底面 + 三格墙"一围满就自动成型，
     * 而玩家是照图纸**从下往上**搭的 ⇒ 第 4 层往往在成型之后才摆上去。ZF59 把顶面那 10 格也纳入判定
     * 之后，"成型"＝"图纸 4 层全摆完"，正常流程不会再出现晚摆的方块；但玩家成型后**又往表面的空格
     * 补一块机器方块**（比如把顶面那两列加宽）时，还是得吸收掉，否则它和 OBJ 盒子<b>面贴面 z-fighting</b>。</p>
     *
     * <p>只吸收"机器方块"：<b>空气不换</b>（顶面本来就敞口，换了会凭空多出隐形格），
     * 玩家摆的别的东西（火把、箱子）也不动。被吸收的方块照样进 {@link #cells}/{@link #originals}，
     * 拆解时原样还回去，挖掉时掉回它自己。</p>
     */
    public void absorbNewHullBlocks() {
        if (this.level == null || this.level.isClientSide || !this.formed || this.disassembling) {
            return;
        }
        boolean changed = false;
        this.disassembling = true;
        try {
            for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
                for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                    for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                        if (!AlloySmelterStructure.isHull(y, j, i)) {
                            continue;                       // 内部 12 格一律不碰
                        }
                        BlockPos p = AlloySmelterStructure.offset(this.worldPosition, facing(), y, j, i);
                        if (p.equals(this.worldPosition) || this.cells.contains(p)) {
                            continue;                       // 控制器自己那格 / 已经收过的
                        }
                        BlockState current = this.level.getBlockState(p);
                        boolean port = AlloySmelterStructure.isWiring(current);
                        if (!port && !AlloySmelterStructure.isCasing(current)) {
                            continue;                       // 空气与"玩家摆的别的东西"都不动
                        }
                        this.cells.add(p);
                        this.originals.add(current);
                        this.level.setBlock(p, port
                                ? ModBlocks.ALLOY_SMELTER_PORT.get().defaultBlockState()
                                        .setValue(AlloySmelterPortBlock.FACING, facing())
                                : ModBlocks.ALLOY_SMELTER_PART.get().defaultBlockState(), Block.UPDATE_ALL);
                        changed = true;
                    }
                }
            }
        } finally {
            this.disassembling = false;
        }
        if (changed) {
            setChanged();
        }
    }

    /**
     * 拆解：把 80 格**原样还原**（控制器那一格清成空气）。
     *
     * @param skip 这一格留空不还原 —— 传被玩家挖掉的那一格（ZF40 的教训：
     *             那一格的方块已经作为掉落物给出去了，再还原就是白送）。
     */
    public void disassemble(BlockPos skip) {
        if (this.level == null || this.level.isClientSide || this.disassembling) {
            return;
        }
        this.disassembling = true;
        try {
            for (int k = 0; k < this.cells.size(); k++) {
                BlockPos p = this.cells.get(k);
                if (p.equals(this.worldPosition)) {
                    this.level.setBlock(p, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(),
                            Block.UPDATE_ALL);
                    continue;
                }
                if (skip != null && p.equals(skip)) {
                    continue;
                }
                BlockState original = this.originals.get(k);
                if (original != null) {
                    this.level.setBlock(p, original, Block.UPDATE_ALL);
                }
            }
            // ⚠ ZF56：这句话会 setBlock 换模型，而 setBlock 会触发 onPlace → tryAutoForm。
            //    此刻外壳刚被还原成"完整"的，自动成型会当场把机器重新装回去 ⇒
            //    **必须趁 disassembling 还是 true 的时候做**（tryAutoForm 会看这个闸门）。
            //    （反证验过：挪到 finally 之后 ⇒ 拆解时整台机器自己装回来，残留 67 格部件格。）
            setFormed(false);
        } finally {
            this.disassembling = false;
        }
        this.cells.clear();
        this.originals.clear();
    }

    /** 满还原（没什么被挖掉时）。 */
    public void disassemble() {
        disassemble(null);
    }

    /** 掉出 GUI 里那 10 个槽位的内容物（不含机器本体）。 */
    public void dropContents() {
        if (this.level == null || this.level.isClientSide) {
            return;
        }
        MachineDrops.dropInventory(this.level, this.worldPosition, this.items);
    }

    // ================= 配方（0.10 ZF62） =================
    /**
     * 推进一格配方进度（从 {@link #serverTick} 每 tick 调一次）。
     *
     * <p><b>包级可见是故意的</b>：探针不用去等 20 tick，可以直接连着调 600 次把一轮跑完
     * （与电力高炉那条"探针能直接验"的路子一致）。</p>
     *
     * <p>四种情况分得很清楚（别把它们混成一种）：</p>
     * <ul>
     *   <li><b>没成型 / 没配方 / 产物放不下</b> ⇒ 进度<b>归零</b>（玩家把原料拿走了，这一轮就不算数了）；</li>
     *   <li><b>电不够</b> ⇒ 进度<b>原地不动</b>（停电不该把做了 29 秒的活清掉）；</li>
     *   <li>电够 ⇒ 扣 {@value #ENERGY_PER_TICK} FE、进度 +1；</li>
     *   <li>进度满 ⇒ 扣料、出产物、进度归零。</li>
     * </ul>
     *
     * <p>每 tick 都会重算 {@link #running}（ZF64 的循环音效看它）：<b>只有"扣了电、进度 +1"那一支算在跑</b>
     * —— 断电停住的时候机器不响，和微型粉碎机 / 液压机一致（停止就是停止，别用声音骗玩家）。</p>
     */
    void craftTick() {
        if (this.level == null) {
            return;
        }
        // ZF64：先当"这一 tick 没在烧"，只有真的扣了电、推进了进度才置真 —— 循环电机声看这个标记。
        //（ZF65 起每 tick 的**权威清零**在 serverTickBody() 开头，因为"拆解"根本不走这个函数；
        //  这里再清一次是为了"探针直接连调 craftTick()"时语义仍然完整）
        this.running = false;
        if (!this.formed) {
            resetProgress();
            return;
        }
        AlloySmelterRecipes.Smelt smelt = findRecipe();
        if (smelt == null || !canOutput(smelt)) {
            resetProgress();
            return;
        }
        if (this.energy < ENERGY_PER_TICK) {
            return;                                     // 电不够：停在原地（不清进度 —— 反证验过）
        }
        this.energy -= ENERGY_PER_TICK;
        this.progress++;
        this.running = true;                            // 真的烧起来了（音效/将来别的"运行中"表现都看它）
        if (this.progress >= DURATION_TICKS) {
            consumeIngredients(smelt);
            addOutput(smelt);
            this.progress = 0;
        }
        setChanged();
    }

    private void resetProgress() {
        if (this.progress != 0) {
            this.progress = 0;
            setChanged();
        }
    }

    /** 当前输入槽能不能凑出一条配方；凑得出就返回它。 */
    private AlloySmelterRecipes.Smelt findRecipe() {
        for (AlloySmelterRecipes.Smelt smelt : AlloySmelterRecipes.all()) {
            boolean ok = true;
            for (AlloySmelterRecipes.Need need : smelt.needs()) {
                if (countInInputs(need.tag()) < need.count()) {
                    ok = false;
                    break;
                }
            }
            if (ok) {
                return smelt;
            }
        }
        return null;
    }

    /** 输入槽里属于这个标签的东西一共有几个。 */
    private int countInInputs(net.minecraft.tags.TagKey<Item> tag) {
        int total = 0;
        for (int slot = INPUT_FIRST; slot < INPUT_FIRST + INPUT_COUNT; slot++) {
            ItemStack stack = this.items.getStackInSlot(slot);
            if (!stack.isEmpty() && stack.is(tag)) {
                total += stack.getCount();
            }
        }
        return total;
    }

    /** 产物放得下吗（有空格子，或已有同样的东西且没堆满）。 */
    private boolean canOutput(AlloySmelterRecipes.Smelt smelt) {
        ItemStack result = smelt.result();
        for (int slot = OUTPUT_FIRST; slot < OUTPUT_FIRST + OUTPUT_COUNT; slot++) {
            ItemStack stack = this.items.getStackInSlot(slot);
            if (stack.isEmpty()) {
                return true;
            }
            if (ItemStack.isSameItemSameComponents(stack, result)
                    && stack.getCount() + result.getCount() <= stack.getMaxStackSize()) {
                return true;
            }
        }
        return false;
    }

    /** 扣原料（调用前先 {@link #findRecipe} 确认够了）。 */
    private void consumeIngredients(AlloySmelterRecipes.Smelt smelt) {
        for (AlloySmelterRecipes.Need need : smelt.needs()) {
            int left = need.count();
            for (int slot = INPUT_FIRST; slot < INPUT_FIRST + INPUT_COUNT && left > 0; slot++) {
                ItemStack stack = this.items.getStackInSlot(slot);
                if (stack.isEmpty() || !stack.is(need.tag())) {
                    continue;
                }
                int take = Math.min(left, stack.getCount());
                stack.shrink(take);
                left -= take;
                this.items.setStackInSlot(slot, stack.isEmpty() ? ItemStack.EMPTY : stack);
            }
        }
    }

    /** 出产物（找第一个放得下的输出槽）。 */
    private void addOutput(AlloySmelterRecipes.Smelt smelt) {
        ItemStack result = smelt.result().copy();
        for (int slot = OUTPUT_FIRST; slot < OUTPUT_FIRST + OUTPUT_COUNT; slot++) {
            ItemStack stack = this.items.getStackInSlot(slot);
            if (stack.isEmpty()) {
                this.items.setStackInSlot(slot, result);
                return;
            }
            if (ItemStack.isSameItemSameComponents(stack, result)
                    && stack.getCount() + result.getCount() <= stack.getMaxStackSize()) {
                stack.grow(result.getCount());
                this.items.setStackInSlot(slot, stack);
                return;
            }
        }
    }

    /** 当前进度（GUI / 探针）。 */
    public int getProgress() {
        return this.progress;
    }

    /** 正在熔炼中（= 这一 tick 真的推进了进度）——客户端据它决定循环电机声响不响（ZF64）。 */
    public boolean isRunning() {
        return this.running;
    }

    // ================= 每 tick =================
    /**
     * 双端都会跑：服务端算逻辑，客户端只负责驱动"运行中"的循环电机声（ZF64）。
     *
     * <p>客户端 tick 读的 {@link #running} 是服务端经 {@link #getUpdateTag()} 同步过来的
     * （见 {@link #sync()}）；方块那边（{@code AlloySmelterBlock#getTicker}）本来就是双端 ticker。</p>
     */
    public static void tick(Level level, BlockPos pos, BlockState state, AlloySmelterBlockEntity be) {
        if (level.isClientSide) {
            be.clientTick();
        } else {
            be.serverTick();
        }
    }

    /** 客户端每 tick 只干一件事：跟着机器响/停（本体在 {@code MachineRunningSound}，那里按坐标去重）。 */
    private void clientTick() {
        MachineRunningSound.update(this, this.running, ModSounds.ALLOY_SMELTER_RUNNING.get());
    }

    /** 只在"运行 ⇄ 停止"真的翻转时发包，免得状态抖动把网络刷爆（与微型粉碎机同一套做法）。 */
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
        // ⚠ ZF65（用户实测报的 bug）：**每 tick 先把"在烧"清掉**，只有下面 craftTick() 真的扣了电、
        //    推进了进度才会再置真。这一句必须待在 `formed` 分支的**外面** ——
        //    拆解（挖部件格 / 挖接线口 / 扳手 / 控制器被挖）走的是 `disassemble()` → `setFormed(false)`，
        //    那条路**不经过 craftTick()**；上一版把清零交给 craftTick() ⇒ 拆完之后 `running` 永远停在 true，
        //    客户端每 tick 都收到"在烧"⇒ **循环电机声一直响到重新建一台为止**。
        this.running = false;
        // 自愈（ZF56）：模型存在方块状态里、成型标记存在 NBT 里，两者万一不一致
        //（旧存档 / 半途断电 / 别的手段换过方块）每秒拉一次；拆解途中不碰（那会儿由 disassemble 自己管）
        if (!this.disassembling && this.level.getGameTime() % 20 == 0) {
            applyFormedState();
        }
        if (this.formed) {
            // 成型后每秒复查一次外壳（破坏任意一格 ⇒ 自动失效；不用满世界挂监听），
            // 顺手把"成型之后才摆上来的表面方块"吸收进来（ZF57，见 absorbNewHullBlocks）
            if (this.level.getGameTime() % 20 == 0) {
                if (!structureOk()) {
                    setFormed(false);
                } else {
                    absorbNewHullBlocks();
                }
            }
            craftTick();                                    // 配方推进（每 tick，真的烧起来了它会把 running 置真）
            return;
        }
        // ZF55「直接激活」：**没激活的控制器每半秒自己试一次**，外壳围满就直接成型
        // （用户原话：「像沉浸改成那样的 直接激活的不行吗」⇒ 不必右键，也不必逐格对图纸）
        if (this.level.getGameTime() % 10 == 0) {
            AlloySmelterBlock.tryAutoForm(this.level, this.worldPosition);
        }
    }

    private void sync() {
        setChanged();
        if (this.level != null && !this.level.isClientSide) {
            this.level.sendBlockUpdated(this.getBlockPos(), this.getBlockState(), this.getBlockState(),
                    Block.UPDATE_CLIENTS);
        }
    }

    // ================= 菜单 =================
    /**
     * 界面标题：<b>没激活时显示"合金炉主控"，激活之后才叫"合金冶炼炉"</b>（匠魂那种读法）。
     */
    @Override
    public Component getDisplayName() {
        return Component.translatable(this.formed
                ? "gui.potato_s_t.alloy_smelter.name"
                : "block.potato_s_t.alloy_smelter");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new AlloySmelterMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.formed = tag.getBoolean("formed");
        this.progress = tag.getInt("progress");
        this.running = tag.getBoolean("running");
        this.items.deserializeNBT(registries, tag.getCompound("inventory"));
        this.cells.clear();
        this.originals.clear();
        long[] packed = tag.getLongArray("cells");
        ListTag states = tag.getList("cellStates", CompoundTag.TAG_COMPOUND);
        var blocks = registries.lookupOrThrow(Registries.BLOCK);
        for (int k = 0; k < packed.length && k < states.size(); k++) {
            this.cells.add(BlockPos.of(packed[k]));
            this.originals.add(NbtUtils.readBlockState(blocks, states.getCompound(k)));
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
        tag.putBoolean("formed", this.formed);
        tag.putInt("progress", this.progress);
        tag.putBoolean("running", this.running);
        tag.put("inventory", this.items.serializeNBT(registries));
        long[] packed = new long[this.cells.size()];
        ListTag states = new ListTag();
        for (int k = 0; k < this.cells.size(); k++) {
            packed[k] = this.cells.get(k).asLong();
            states.add(NbtUtils.writeBlockState(this.originals.get(k)));
        }
        tag.putLongArray("cells", packed);
        tag.put("cellStates", states);
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
