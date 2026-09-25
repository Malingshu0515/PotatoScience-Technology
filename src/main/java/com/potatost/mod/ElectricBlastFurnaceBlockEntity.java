package com.potatost.mod;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.nbt.StringTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemHandlerHelper;
import net.neoforged.neoforge.items.ItemStackHandler;

import com.potatost.mod.client.sound.MachineRunningSound;
import com.potatost.mod.sound.ModSounds;

/**
 * 电力高炉的控制器方块实体（0.10 ZF39）。
 *
 * <p><b>数值：</b>一个槽位无论几个物品都是 {@value #DURATION_TICKS} tick（10 秒）烧完；
 * 一件物品的总耗电 {@value #ENERGY_PER_ITEM} FE（摊到那 10 秒里）；
 * 储能 {@value #MAX_ENERGY} FE。
 * ⇒ 一摞 64 个 = 51200 FE 总价、约 256 FE/t；12 槽塞满 ≈ **3072 FE/t**（"接大电"的由来）。</p>
 *
 * <p><b>⚠ 为什么不是用户字面给的"320 储能 + 数量×80 每 tick"：</b>
 * 机器一 tick 最多只能花掉缓冲里现有的电（能量是电缆按 tick 推来的，攒不过上限），
 * 于是 <b>单 tick 耗电 &gt; 储能 ⇒ 永远凑不齐 ⇒ 永远不动</b>。
 * 按字面读法一摞 64 要 5120 FE/t、储能只有 320（够 4 个物品），塞满就是死机 ——
 * 用户报的「貌似不工作」正是这个。详见 {@link #MAX_ENERGY} 与 {@link #ENERGY_PER_ITEM} 的注释。</p>
 *
 * <p><b>槽位：</b>12 输入 + 32 输出 = 44。用户原话「有可能需要做成匠魂那样下拉式的」，
 * 但 ZF39 拍板改成**放大面板一次显示完**（沉浸工程那种大 GUI）。</p>
 *
 * <p><b>装配痕迹：</b>27 格的**原始方块状态**全部存在本方块实体的 NBT 里，
 * 拆解时原样还原（不含控制器自己那一格 —— 那一格是机器本体，拆解后变成物品）。
 * 不存的话玩家的 25 块建材就凭空没了。</p>
 */
public class ElectricBlastFurnaceBlockEntity extends BlockEntity implements MenuProvider {

    // ================= 数值 =================
    /**
     * 储能上限。
     *
     * <p><b>⚠⚠ 这个数字不能随便填 —— 它决定机器"转不转得动"。</b>
     * 硬约束是：<b>机器一 tick 最多只能花掉"缓冲里现有的电"</b>
     * （能量是电缆/端子按 tick 推来的，攒不过缓冲上限）⇒
     * <b>单 tick 耗电 &gt; 储能上限 ⇒ 永远凑不齐 ⇒ 永远不动，而且一点报错都没有。</b>
     * 用户 ZF42 报的「貌似不工作」就是这个。</p>
     *
     * <p><b>算法（改动 {@link #ENERGY_PER_ITEM} / {@link #DURATION_TICKS} / 槽数 / 堆叠上限时
     * 必须重算）：</b></p>
     * <pre>
     *   单 tick 最坏耗电 = 12 槽 × 64 件 × 800 FE ÷ 200 tick = 3072 FE/t
     *   ⇒ 储能必须 ≥ 3072，现在取 4096（留 1024 余量）
     * </pre>
     *
     * <p>ZF44 用户把每件从 80 提到 800，最坏值随之从 308 涨到 3072，
     * 所以储能也从 320 提到 4096 —— <b>不然又是"塞满了却一动不动"</b>。
     * 静态块里有一道自检会把这种配置直接打成一条 WARN 日志（见下）。</p>
     */
    public static final int MAX_ENERGY = 4096;

    /** 一个槽位无论几个物品都是 <b>10 秒</b>烧完（ZF43 用户：「改为10s一组吧」）。 */
    public static final int DURATION_TICKS = 10 * 20;

    /**
     * <b>一件物品的总耗电</b>（整批摊到 {@link #DURATION_TICKS} 上，不是每 tick）。
     *
     * <p>用户原话是「耗电量=熔炼物品数量*80Fe/t」，ZF44 又改成「每件800Fe吧」。
     * 字面读成"每 tick 每件"会和储能打架（见 {@link #MAX_ENERGY}），所以按
     * "<b>数量 × 这个数 = 整批总电</b>"实现：一件粗矿 800 FE，一摞 64 个 51200 FE。</p>
     */
    public static final int ENERGY_PER_ITEM = 800;

    public static final int ENERGY_PUSH_RATE = 1024;

    /** 单槽堆叠上限的保守估计（原版是 64）—— 自检用的最坏情况按它算。 */
    private static final int MAX_STACK = 64;

    // ================= 槽位 =================
    public static final int INPUT_FIRST = 0;
    public static final int INPUT_COUNT = 12;
    public static final int OUTPUT_FIRST = INPUT_FIRST + INPUT_COUNT;
    public static final int OUTPUT_COUNT = 32;
    public static final int SLOT_COUNT = INPUT_FIRST + INPUT_COUNT + OUTPUT_COUNT;

    // ================= 同步字段 =================
    public static final int DATA_ENERGY = 0;
    public static final int DATA_ENERGY_MAX = 1;
    /** 12 个进度紧跟在后面：{@code DATA_PROGRESS_FIRST + k} */
    public static final int DATA_PROGRESS_FIRST = 2;
    public static final int DATA_COUNT = DATA_PROGRESS_FIRST + INPUT_COUNT;

    /**
     * 配置自检：<b>把"单 tick 耗电超过储能"这种会让机器静默停摆的配置打成一条日志。</b>
     *
     * <p>ZF42 那次是靠用户截图 + 我手算才发现的，代价是一轮往返。这道自检让它变成启动时的一行字。</p>
     *
     * <p>（放在这里而不是数值那一节，是因为 Java 禁止 static 块**前向引用**后面才声明的
     * {@code INPUT_COUNT} —— 第一次写就栽在这上面。）</p>
     */
    static {
        long worstBatch = (long) INPUT_COUNT * MAX_STACK * ENERGY_PER_ITEM;
        long worstDemand = (worstBatch + DURATION_TICKS - 1) / DURATION_TICKS;
        if (worstDemand > MAX_ENERGY) {
            // ⚠ 这条日志**故意写英文**：Audit 的 E 项是**文本级**检查，Java 里出现中文就报
            //   "用户可见文本必须走 lang"。而这是一条开发者向的启动自检、不是给玩家看的文案，
            //   为它造一个 lang 键没有意义 —— 所以用英文，并在这里说明原因。
            System.err.println("[potato_s_t] Electric Blast Furnace is misconfigured: worst-case draw "
                    + worstDemand + " FE/t exceeds its " + MAX_ENERGY + " FE buffer, so a full load "
                    + "will never run. Raise MAX_ENERGY or lengthen DURATION_TICKS.");
        }
    }

    private int energy = 0;
    private final int[] progress = new int[INPUT_COUNT];
    private boolean running = false;

    /**
     * 每个槽作为<b>配对任务的 driver</b> 时，那一对的另一半当时长什么样
     * （{@code 物品注册名:数量}）。
     *
     * <p><b>为什么需要它：</b>配对任务的进度只记在 driver 那个槽上，而
     * {@code onContentsChanged} 只清"被改的那个槽"的进度 —— 于是
     * <b>把烤到一半的碳粉换成沙砾，进度不清零</b>，下一 tick 就白拿一炉磁铁。
     * 记录另一半的签名后，"换料"这个动作照样会把整对任务的进度打回 0，
     * 与单槽任务的规矩一致（那边的规矩由 {@code ItemStackHandler} 保证）。</p>
     *
     * <p>与 {@link #progress} 一起存盘：不然读档/区块卸载会把进度凭空归零。</p>
     */
    private final String[] pairPartner = new String[INPUT_COUNT];

    /** 27 格的世界坐标与它们**装配前**的方块状态（拆解时原样还原）。 */
    private final List<BlockPos> cells = new ArrayList<>();
    private final List<BlockState> originals = new ArrayList<>();
    private boolean disassembling = false;

    /**
     * 收电接口（只收不放）。容量就是 {@value #MAX_ENERGY} —— 用户 ZF39 定的"要接大电"，
     * 缓冲故意很小。
     */
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
            // 输入槽什么都收（放错只是不加工，不该被槽位挡住）；输出槽一律不收
            return slot < OUTPUT_FIRST;
        }

        @Override
        protected void onContentsChanged(int slot) {
            // 输入槽内容变了 ⇒ 这一槽的进度作废（防止半途换料白嫖进度）
            if (slot < OUTPUT_FIRST) {
                progress[slot - INPUT_FIRST] = 0;
            }
            setChanged();
        }
    };

    private final ContainerData containerData = new ContainerData() {
        @Override
        public int get(int index) {
            if (index == DATA_ENERGY) {
                return energy;
            }
            if (index == DATA_ENERGY_MAX) {
                return MAX_ENERGY;
            }
            int k = index - DATA_PROGRESS_FIRST;
            return k >= 0 && k < INPUT_COUNT ? progress[k] : 0;
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

    public ElectricBlastFurnaceBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.ELECTRIC_BLAST_FURNACE_BE.get(), pos, state);
        Arrays.fill(this.pairPartner, "");
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
     * 对外暴露的收电接口（只收不放）。
     *
     * <p>⚠ ZF41 才发现：这台机器之前**压根没注册能量能力** —— 电缆/端子接上去一点电都进不来。
     * 用户原话「原来接线块的地方也不传电」。</p>
     */
    public IEnergyStorage getEnergyStorage() {
        return this.energyStorage;
    }

    public boolean isRunning() {
        return this.running;
    }

    public boolean isDisassembling() {
        return this.disassembling;
    }

    /**
     * 装配/拆解期间置为 true 的闸门。
     *
     * <p>换部件格会触发它们的 {@code onRemove}，那些 {@code onRemove} 会回头找控制器要求拆解 ——
     * 装配时不挡就会"刚装好立刻自己拆掉"。</p>
     */
    public void setDisassembling(boolean value) {
        this.disassembling = value;
    }

    /** 是否已经成型（NBT 里记了 27 格就是成型状态）。 */
    public boolean isFormed() {
        return !this.cells.isEmpty();
    }

    // ================= 装配痕迹 =================
    public void recordStructure(List<BlockPos> positions, List<BlockState> states) {
        this.cells.clear();
        this.originals.clear();
        this.cells.addAll(positions);
        this.originals.addAll(states);
        setChanged();
    }

    /**
     * 掉出**内容物**（GUI 里那 44 个槽位）。<b>不</b>掉机器本体 ——
     * 用户 ZF39 改的规矩：「被破坏后只会毁坏结构和掉落被挖掉的方块以及 gui 内部物品」。
     *
     * <p>与 {@link #disassemble()} 分开还有一个 Audit 上的理由：B 项要求
     * "带物品栏的方块实体，其**方块**必须显式调 {@code MachineDrops}"，
     * 而那道检查是文本级的，所以 {@code MachineDrops.dropInventory} 那句话必须写在方块文件里。</p>
     */
    public void dropContents() {
        if (this.level == null || this.level.isClientSide) {
            return;
        }
        MachineDrops.dropInventory(this.level, this.worldPosition, this.items);
    }

    /** 这一格**装配前**是什么方块（拆解还原与"破坏掉落原方块"都靠它）。 */
    public BlockState originalAt(BlockPos pos) {
        int k = this.cells.indexOf(pos);
        return k < 0 ? null : this.originals.get(k);
    }

    /**
     * 拆解：还原 27 格（**控制器自己那一格清成空气**）。
     *
     * @param skip 这一格**留空不还原** —— 传被玩家挖掉的那一格。
     *             不传的话会出现"这一格的方块既作为掉落物给了玩家、又在世界上被还原回去" ⇒
     *             **白送一格建材**（ZF40 探针抓出来的：破坏部件格后那一格没有变成空气）。
     *             传 {@code null} = 满还原（空手 Shift 右键那种"主动拆解，什么都没被挖掉"的情况）。
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
                    // ⚠ 控制器那一格**必须显式清成空气**，不能只是"跳过"：
                    // 走 onRemove 进来的话它本来就是空气（跳过与否都一样），
                    // 但**空手 Shift 右键**是直接在方块还在的时候调过来的 ——
                    // 只跳过的话方块会原地留着，而机器本体又已经掉出来了 ⇒ 白送一台。
                    // （这条是探针抓出来的：拆解还原那一条 [FAIL]。）
                    this.level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
                    continue;
                }
                if (skip != null && p.equals(skip)) {
                    continue;   // 被挖掉的那一格留空（原方块已经作为掉落物给出去了）
                }
                this.level.setBlock(p, this.originals.get(k), Block.UPDATE_ALL);
            }
        } finally {
            this.disassembling = false;
        }
    }

    /** 满还原（什么都没被挖掉时的主动拆解）。 */
    public void disassemble() {
        disassemble(null);
    }

    // ================= 每 tick =================
    /** 双端都会跑：服务端算逻辑，客户端驱动循环音效。 */
    public static void tick(Level level, BlockPos pos, BlockState state, ElectricBlastFurnaceBlockEntity be) {
        if (level.isClientSide) {
            MachineRunningSound.update(be, be.isRunning(), ModSounds.GENERATOR_RUNNING.get());
        } else {
            be.serverTick();
        }
    }

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

        // ⓪ 配对任务（0.10 ZF45）：铁粉 + 碳粉 → 高碳钢、铁粉 + 沙砾 → 磁铁。
        //    「检测到有1份铁和一分碳粉 自动开始熔炼」—— 玩家把两样放进**任意两个输入槽**即可。
        List<PairJob> jobs = findPairJobs();
        boolean[] paired = new boolean[INPUT_COUNT];
        for (PairJob job : jobs) {
            paired[job.driver()] = true;
            paired[job.partner()] = true;
            if (this.progress[job.partner()] != 0) {
                // 配对任务只有一个进度，记在 driver 上；另一半那格永远是 0
                this.progress[job.partner()] = 0;
                dirty = true;
            }
            String key = partnerKey(job);
            if (!key.equals(this.pairPartner[job.driver()])) {
                // 另一半换料了（碳粉 → 沙砾之类）⇒ 整对任务的进度作废
                this.progress[job.driver()] = 0;
                this.pairPartner[job.driver()] = key;
                dirty = true;
            }
        }

        // ① 找出"正在加工"的单槽（有配方 且 进度还没到点），算**整批**要多少电
        long batch = 0;
        for (int k = 0; k < INPUT_COUNT; k++) {
            if (paired[k]) {
                continue;   // 参加配对的槽不走单槽路线（否则电和进度都要算两遍）
            }
            ItemStack in = this.items.getStackInSlot(INPUT_FIRST + k);
            if (!canProcess(in) || this.progress[k] >= DURATION_TICKS) {
                if (!canProcess(in)) {
                    this.progress[k] = 0;
                }
                continue;
            }
            batch += (long) in.getCount() * ENERGY_PER_ITEM;
        }
        // 配对任务的一批 = min(两个槽的数量) 份，每份照样 ENERGY_PER_ITEM FE
        for (PairJob job : jobs) {
            if (this.progress[job.driver()] < DURATION_TICKS) {
                batch += (long) job.batch() * ENERGY_PER_ITEM;
            }
        }
        // 整批的电摊到整段时间上：一槽 64 个就是 64×800/200 = 256 FE/t，而不是 51200 FE/t。
        // ⚠ 这里踩过一次大坑，见 MAX_ENERGY 的注释「单 tick 耗电不能超过储能」。
        long demand = batch == 0 ? 0 : (batch + DURATION_TICKS - 1) / DURATION_TICKS;

        // ② 电够就推进
        boolean advanced = false;
        if (demand > 0 && this.energy >= demand) {
            this.energy -= (int) demand;
            for (int k = 0; k < INPUT_COUNT; k++) {
                if (paired[k]) {
                    continue;
                }
                ItemStack in = this.items.getStackInSlot(INPUT_FIRST + k);
                if (canProcess(in) && this.progress[k] < DURATION_TICKS) {
                    this.progress[k]++;
                }
            }
            for (PairJob job : jobs) {
                if (this.progress[job.driver()] < DURATION_TICKS) {
                    this.progress[job.driver()]++;
                }
            }
            advanced = true;
            dirty = true;
        }

        // ③ 到点的任务结算（本 tick 可能好几个同时到点，所以**一次性**算好占用再写）
        List<Task> done = new ArrayList<>();
        for (int k = 0; k < INPUT_COUNT; k++) {
            if (paired[k] || this.progress[k] < DURATION_TICKS) {
                continue;
            }
            ItemStack in = this.items.getStackInSlot(INPUT_FIRST + k);
            if (!canProcess(in)) {
                this.progress[k] = 0;
                continue;
            }
            done.add(new Task(List.of(k), List.of(in.getCount()), outputFor(in)));
        }
        for (PairJob job : jobs) {
            if (this.progress[job.driver()] < DURATION_TICKS) {
                continue;
            }
            // 消耗：两个槽各扣 batch 个（各自扣各自的，所以铁粉多出来的部分留在原槽）；
            // 产出：batch 份配方产物。
            done.add(new Task(List.of(job.driver(), job.partner()),
                    List.of(job.batch(), job.batch()),
                    new ItemStack(job.recipe().output(), job.batch() * job.recipe().count())));
        }
        if (!done.isEmpty()) {
            List<ItemStack> products = new ArrayList<>();
            for (Task task : done) {
                products.add(task.product());
            }
            if (fits(products)) {
                for (Task task : done) {
                    insertOutput(task.product());
                    for (int n = 0; n < task.slots().size(); n++) {
                        int k = task.slots().get(n);
                        int take = task.amounts().get(n);
                        ItemStack stack = this.items.getStackInSlot(INPUT_FIRST + k);
                        this.items.setStackInSlot(INPUT_FIRST + k, take >= stack.getCount()
                                ? ItemStack.EMPTY
                                : stack.copyWithCount(stack.getCount() - take));
                        this.progress[k] = 0;
                    }
                }
                dirty = true;
            }
        }

        // ④ 把产物推给紧邻的容器（用户：「检测有紧邻的容器会把输出物放在容器里」）
        if (pushOutput()) {
            dirty = true;
        }

        this.running = advanced;
        if (dirty) {
            setChanged();
        }
    }

    /**
     * 本 tick 的一个<b>配对任务</b>（0.10 ZF45）。
     *
     * @param driver  进度记在这个槽上（GUI 里那一格的进度条画的就是这个任务的进度）
     * @param partner 另一个槽（它的进度恒为 0）
     * @param recipe  配对配方
     * @param batch   这一批做几份 = {@code min(两个槽的数量)}
     */
    private record PairJob(int driver, int partner, BlastFurnaceRecipes.Pair recipe, int batch) {
    }

    /**
     * 一个到点、等待结算的任务。
     *
     * @param slots   要从哪些槽扣东西（单槽任务只有一个，配对任务两个）
     * @param amounts 每个槽各扣多少个
     * @param product 整批产出
     */
    private record Task(List<Integer> slots, List<Integer> amounts, ItemStack product) {
    }

    /**
     * 把输入槽按配对配方**贪心配对**：按槽位顺序，每个还没被占的槽去找第一个没被占的另一半。
     *
     * <p>于是 6 个铁粉槽 + 6 个碳粉槽 = <b>6 个任务同时在跑</b>，而不是"一次只跑一对"。
     * 每个任务的进度各自记在自己的 driver 槽上，互不干扰。</p>
     */
    private List<PairJob> findPairJobs() {
        List<PairJob> jobs = new ArrayList<>();
        boolean[] used = new boolean[INPUT_COUNT];
        for (int a = 0; a < INPUT_COUNT; a++) {
            if (used[a]) {
                continue;
            }
            ItemStack sa = this.items.getStackInSlot(INPUT_FIRST + a);
            if (sa.isEmpty()) {
                continue;
            }
            for (int b = a + 1; b < INPUT_COUNT; b++) {
                if (used[b]) {
                    continue;
                }
                ItemStack sb = this.items.getStackInSlot(INPUT_FIRST + b);
                BlastFurnaceRecipes.Pair recipe = BlastFurnaceRecipes.findPair(sa, sb);
                if (recipe == null) {
                    continue;
                }
                used[a] = true;
                used[b] = true;
                jobs.add(new PairJob(a, b, recipe, Math.min(sa.getCount(), sb.getCount())));
                break;
            }
        }
        return jobs;
    }

    /** 配对任务里"另一半"的签名（物品 + 数量）—— 换料时用它判断要不要清进度。 */
    private String partnerKey(PairJob job) {
        ItemStack partner = this.items.getStackInSlot(INPUT_FIRST + job.partner());
        return BuiltInRegistries.ITEM.getKey(partner.getItem()) + ":" + partner.getCount();
    }

    /**
     * 这一槽能不能加工。
     *
     * <p><b>先查本模组自己的表，再退回"原版高炉配方"。</b>用户 ZF43：「并且加上所有的原版高炉配方」
     * —— 原版 1.21.1 一共 24 条 `minecraft:blasting`，含钻石/绿宝石/青金石/红石/石英/
     * 下界合金碎片，以及"铁/金工具盔甲烧成粒"那些。</p>
     *
     * <p><b>为什么走 {@code RecipeManager} 动态查、而不是把 24 条抄进来</b>：
     * ① 抄一遍就要跟着版本更新；② 走配方管理器还能**顺带吃下别的 mod 加的高炉配方**；
     * ③ 原版的"工具烧成粒"那种配方带的是**标签**，手抄极容易漏。</p>
     *
     * <p>本模组自己的表排在最前面，所以矿石方块仍然是 3~6 锭、粗矿仍然是 2 锭 —— 不会被原版的 1 锭盖掉。</p>
     */
    private boolean canProcess(ItemStack in) {
        if (in.isEmpty()) {
            return false;
        }
        if (BlastFurnaceRecipes.find(in) != null) {
            return true;
        }
        return !vanillaBlasting(in).isEmpty();
    }

    /** 原版（以及别的 mod 注册的）高炉配方对**一个**输入物品的产物；没有就返回空。 */
    private ItemStack vanillaBlasting(ItemStack in) {
        if (this.level == null || in.isEmpty()) {
            return ItemStack.EMPTY;
        }
        return this.level.getRecipeManager()
                .getRecipeFor(RecipeType.BLASTING, new SingleRecipeInput(in), this.level)
                .map(holder -> holder.value().getResultItem(this.level.registryAccess()))
                .orElse(ItemStack.EMPTY);
    }

    /** 一整槽烧完的产物：本模组的表优先，否则按原版配方 × 数量。 */
    private ItemStack outputFor(ItemStack in) {
        if (BlastFurnaceRecipes.find(in) != null) {
            return BlastFurnaceRecipes.produce(in, this.level.random);
        }
        ItemStack one = vanillaBlasting(in);
        if (one.isEmpty()) {
            return ItemStack.EMPTY;
        }
        return one.copyWithCount((int) Math.min((long) one.getCount() * in.getCount(), Integer.MAX_VALUE));
    }

    /**
     * 这些产物**全部**放得下吗？用"模拟占用"一次性算 ——
     * 一个一个独立问"放得下吗"会让它们都看到同一批空槽（§4.14 吞产物的老坑）。
     */
    private boolean fits(List<ItemStack> products) {
        ItemStack[] sim = new ItemStack[OUTPUT_COUNT];
        for (int k = 0; k < OUTPUT_COUNT; k++) {
            sim[k] = this.items.getStackInSlot(OUTPUT_FIRST + k).copy();
        }
        for (ItemStack prod : products) {
            int remaining = prod.getCount();
            int max = prod.getMaxStackSize();
            for (int k = 0; k < OUTPUT_COUNT && remaining > 0; k++) {
                if (!sim[k].isEmpty() && ItemStack.isSameItemSameComponents(sim[k], prod)) {
                    int move = Math.min(max - sim[k].getCount(), remaining);
                    if (move > 0) {
                        sim[k].grow(move);
                        remaining -= move;
                    }
                }
            }
            for (int k = 0; k < OUTPUT_COUNT && remaining > 0; k++) {
                if (sim[k].isEmpty()) {
                    int move = Math.min(max, remaining);
                    sim[k] = prod.copyWithCount(move);
                    remaining -= move;
                }
            }
            if (remaining > 0) {
                return false;
            }
        }
        return true;
    }

    private void insertOutput(ItemStack stack) {
        ItemStack remaining = stack.copy();
        int max = remaining.getMaxStackSize();
        for (int k = 0; k < OUTPUT_COUNT && !remaining.isEmpty(); k++) {
            ItemStack slot = this.items.getStackInSlot(OUTPUT_FIRST + k);
            if (!slot.isEmpty() && ItemStack.isSameItemSameComponents(slot, remaining)
                    && slot.getCount() < max) {
                int move = Math.min(max - slot.getCount(), remaining.getCount());
                slot.grow(move);
                remaining.shrink(move);
            }
        }
        for (int k = 0; k < OUTPUT_COUNT && !remaining.isEmpty(); k++) {
            if (this.items.getStackInSlot(OUTPUT_FIRST + k).isEmpty()) {
                int move = Math.min(max, remaining.getCount());
                this.items.setStackInSlot(OUTPUT_FIRST + k, remaining.copyWithCount(move));
                remaining.shrink(move);
            }
        }
    }

    /** 把输出槽推进紧邻容器的各自物品栏。 */
    private boolean pushOutput() {
        boolean moved = false;
        for (Direction d : Direction.values()) {
            IItemHandler target = this.level.getCapability(
                    Capabilities.ItemHandler.BLOCK, this.worldPosition.relative(d), d.getOpposite());
            if (target == null) {
                continue;
            }
            for (int k = 0; k < OUTPUT_COUNT; k++) {
                ItemStack stack = this.items.getStackInSlot(OUTPUT_FIRST + k);
                if (stack.isEmpty()) {
                    continue;
                }
                ItemStack remainder = ItemHandlerHelper.insertItemStacked(target, stack.copy(), false);
                if (remainder.getCount() != stack.getCount()) {
                    this.items.setStackInSlot(OUTPUT_FIRST + k, remainder);
                    moved = true;
                }
            }
        }
        return moved;
    }

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
        return Component.translatable("block.potato_s_t.electric_blast_furnace");
    }

    @Override
    public AbstractContainerMenu createMenu(int containerId, Inventory playerInventory, Player player) {
        return new ElectricBlastFurnaceMenu(containerId, playerInventory, this);
    }

    // ================= 持久化 =================
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.running = tag.getBoolean("running");
        int[] p = tag.getIntArray("progress");
        for (int k = 0; k < INPUT_COUNT && k < p.length; k++) {
            this.progress[k] = p[k];
        }
        Arrays.fill(this.pairPartner, "");
        ListTag pairTags = tag.getList("pairPartner", CompoundTag.TAG_STRING);
        for (int k = 0; k < INPUT_COUNT && k < pairTags.size(); k++) {
            this.pairPartner[k] = pairTags.getString(k);
        }
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
        tag.putBoolean("running", this.running);
        tag.putIntArray("progress", this.progress.clone());
        ListTag pairTags = new ListTag();
        for (String s : this.pairPartner) {
            pairTags.add(StringTag.valueOf(s));
        }
        tag.put("pairPartner", pairTags);
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

    /** 给装配逻辑用的世界类型便利方法（调用方已经判过 isClientSide）。 */
    public ServerLevel serverLevel() {
        return (ServerLevel) this.level;
    }
}
