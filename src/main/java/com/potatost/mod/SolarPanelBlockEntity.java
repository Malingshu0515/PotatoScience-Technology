package com.potatost.mod;

import java.util.ArrayList;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.jetbrains.annotations.Nullable;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * 太阳能板（0.10 ZF22 加入；ZF24 改为<b>共享储能</b>；ZF29 发电量 ×3）。
 *
 * <p><b>发电规则（全部来自用户指定）：</b></p>
 * <ul>
 *   <li><b>只在白天发电</b>：日出/傍晚 {@value #RATE_DAWN_DUSK}、上午/下午 {@value #RATE_MORNING}、
 *       正午 {@value #RATE_NOON} FE/t；</li>
 *   <li><b>天气系数</b>：雨天 = 晴天的 {@value #RAIN_PERCENT}%，雷暴 = {@value #THUNDER_PERCENT}%；</li>
 *   <li><b>上方必须"见天"</b>：正上方是空气或<b>无色玻璃</b>（{@code #c:glass_blocks/colorless}
 *       —— 染色玻璃与遮光玻璃都<b>不算</b>，因为用户说的是"透明玻璃"）才算，否则这块不发电；</li>
 *   <li>每 tick 把能量<b>推给正下方的设备</b>。</li>
 * </ul>
 *
 * <p><b>ZF29：发电量变成原来的 300%</b>（用户："太阳能板发电量变成原来300%"）。
 * 三档 <b>20/45/60 → 60/135/180 FE/t</b>。⚠ 注意 <b>{@value #MAX_ENERGY} FE 的储能没动</b> ——
 * 于是"攒满"从约 26 tick（1.3 秒）变成约 9 tick（0.4 秒），
 * 也就是说<b>它现在几乎总是满的，真正的瓶颈变成了下方设备能抽多快</b>。
 * 这是用户只要"发电量"三个字时**有意不动储能**的结果，写在档案 §9 里而不是自作主张改容量。</p>
 *
 * <p><b>并联（用户 2026-09-18 修正后的要求）：</b>
 * 「<i>共享储能吧和锂电一样，只不过没有方块底面积限制，贴图也不用变成一整个，各自单独就可以</i>」。
 * 也就是说，水平四邻连通的太阳能板是<b>一个整体</b>：</p>
 * <ul>
 *   <li><b>共享发电量</b>：每块按自己的朝向/遮挡/天气算出自身速率，组内求和再平分
 *       （{@code 每块速率 = 组内速率之和 ÷ 组内块数}）—— 于是"被遮住的那块也能分到电"；</li>
 *   <li><b>共享储能</b>：全组的电进<b>同一个池子</b>，容量 = 块数 × {@value #MAX_ENERGY} FE，
 *       任何一块的任一方向都能抽到全组的电；</li>
 *   <li><b>没有形状限制</b>：不像锂电池那样要求"完整长方体 + 合法底面积"，
 *       只要水平相邻就连上（这一点是用户明确要求的差别）；</li>
 *   <li><b>贴图/模型不合并</b>：每块照旧画自己那一格的贴图，组只是逻辑概念，不生成多方块渲染。</li>
 * </ul>
 *
 * <p><b>共享池怎么实现（关键设计）：</b>没有"整组一个数字"那种存储 ——
 * 电仍然<b>逐块存在各自的 {@code energy} 里</b>（存档格式与单块版一致），
 * 但对外表现出来的是<b>池子</b>：</p>
 * <ul>
 *   <li>组内推举一个<b>控制器</b>（选坐标最小的那块，规则确定性，与放置顺序无关）；
 *       只有控制器负责"发电并往组里充"；</li>
 *   <li>{@code getEnergyStored()} / {@code getMaxEnergyStored()} 返回<b>全组合计</b>，
 *       所以从任何一块下面抽电，抽到的都是全组的电；</li>
 *   <li>抽取时按顺序从各块的 512 里扣；充电时按顺序往各块里补 —— 池子内部怎么摊不影响总量；</li>
 *   <li>控制器每 {@value #GROUP_REFRESH} tick 重算一次组（BFS），组员变动后自然收敛。</li>
 * </ul>
 *
 * <p><b>性能：</b>组是每 {@value #GROUP_REFRESH} tick 用一次 BFS 重算的（不是每 tick），
 * 并且单次 BFS 最多走 {@value #MAX_GROUP} 块。速率本身是"时刻 + 天气"的阶梯函数，
 * 一秒的滞后肉眼看不出。控制器额外缓存一份<b>组员坐标快照</b>，避免每 tick 都 BFS。</p>
 */
public class SolarPanelBlockEntity extends BlockEntity {

    /** 单块储能（用户指定；组容量 = 块数 × 此值） */
    public static final int MAX_ENERGY = 512;

    /** 晴天三档（FE/t）。ZF29 起 = 原值 × 3（用户："太阳能板发电量变成原来300%"） */
    public static final int RATE_DAWN_DUSK = 60;
    public static final int RATE_MORNING = 135;
    public static final int RATE_NOON = 180;

    /** 天气系数（百分比） */
    public static final int RAIN_PERCENT = 60;
    public static final int THUNDER_PERCENT = 20;

    // 白天时间带（tick；0 = 日出，6000 = 正午，12000 = 日落）
    private static final int DAWN_END = 2000;
    private static final int MORNING_END = 5000;
    private static final int NOON_END = 7000;
    private static final int AFTERNOON_END = 10000;
    private static final int DAY_END = 12000;

    /** 并联组重算间隔（tick） */
    private static final int GROUP_REFRESH = 20;
    /** 单次 BFS 的规模上限，防止有人盖出天文数字的阵列把服务器拖死 */
    public static final int MAX_GROUP = 512;

    /** 本块自己那 512 FE 的存量。组内每块各存各的，对外合起来看就是"一个池子"。 */
    private int energy;

    // ================= 共享组状态 =================

    /** 组控制器：坐标最小的那块（不落盘，每次重算时选出） */
    private BlockPos groupController;
    /** 组员快照（仅控制器维护，见 {@link #membersUpToDate()}） */
    private final List<BlockPos> members = new ArrayList<>();
    /** 组内速率总和（FE/t，"共享之前"的原始值） */
    private int groupTotalRate;
    /** 倒计时到 0 就重算并联组（初值 1 ⇒ 第一次 tick 立刻算） */
    private int groupTimer = 1;
    /** {@link #members} 对应的组员数（0 = 还没建过）。仅当快照失效时才重建。 */
    private int cachedMemberCount;

    public SolarPanelBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.SOLAR_PANEL_BE.get(), pos, state);
    }

    /**
     * 本块自带的 FE 接口（单块时对外就用它）。
     *
     * <p>ZF24 之前这里是 {@link MachineEnergyStorage#extractOnly}；改成共享储能后语义变了
     * （读写都要摊到组员、还要跨块回写），所以改成下面这个<b>具名</b>内部类。
     * 用<b>具名类而不是匿名类</b>是有原因的：Audit 的 <b>D 项</b>专抓"新写的匿名
     * {@code IEnergyStorage}"（基准 5 个），ZF22 就是这么被当场点名的 —— 见 §11.4。</p>
     */
    private final IEnergyStorage blockStorage = new BlockStorage();

    /** 本块自己的 512 FE 存取（单块对外 + {@link #pushToDeviceBelow()} 都走这里） */
    private final class BlockStorage implements IEnergyStorage {
        @Override
        public int receiveEnergy(int maxReceive, boolean simulate) {
            if (SolarPanelBlockEntity.this.level == null) {
                return 0;
            }
            return (int) fillSlots(SolarPanelBlockEntity.this.level,
                    List.<BlockPos>of(SolarPanelBlockEntity.this.worldPosition), maxReceive, simulate);
        }

        @Override
        public int extractEnergy(int maxExtract, boolean simulate) {
            if (SolarPanelBlockEntity.this.level == null) {
                return 0;
            }
            return (int) drainSlots(SolarPanelBlockEntity.this.level,
                    List.<BlockPos>of(SolarPanelBlockEntity.this.worldPosition), maxExtract, simulate);
        }

        @Override
        public int getEnergyStored() {
            return SolarPanelBlockEntity.this.energy;
        }

        @Override
        public int getMaxEnergyStored() {
            return MAX_ENERGY;
        }

        @Override
        public boolean canExtract() {
            return SolarPanelBlockEntity.this.energy > 0;
        }

        @Override
        public boolean canReceive() {
            return SolarPanelBlockEntity.this.energy < MAX_ENERGY;
        }
    }

    /**
     * 对外（能力查询）返回的<b>全组共享池</b>视图。
     *
     * <p>容量 = 组员数 × {@value #MAX_ENERGY}，存量 = 组员存量之和。
     * 读全组、写全组，所以从组里任何一块下面抽电都等价。</p>
     */
    private final class GroupStorage implements IEnergyStorage {
        @Override
        public int receiveEnergy(int maxReceive, boolean simulate) {
            if (SolarPanelBlockEntity.this.level == null) {
                return 0;
            }
            return (int) fillSlots(SolarPanelBlockEntity.this.level,
                    memberPositions(), maxReceive, simulate);
        }

        @Override
        public int extractEnergy(int maxExtract, boolean simulate) {
            if (SolarPanelBlockEntity.this.level == null) {
                return 0;
            }
            return (int) drainSlots(SolarPanelBlockEntity.this.level,
                    memberPositions(), maxExtract, simulate);
        }

        @Override
        public int getEnergyStored() {
            return (int) Math.min(totalStored(), Integer.MAX_VALUE);
        }

        @Override
        public int getMaxEnergyStored() {
            long cap = (long) groupSize() * MAX_ENERGY;
            return (int) Math.min(cap, Integer.MAX_VALUE);
        }

        @Override
        public boolean canExtract() {
            return totalStored() > 0;
        }

        /**
         * {@code false}：太阳能板只发电，<b>不接受</b>外来充能（与 ZF22 的 extractOnly 一致）。
         * 但 {@link #getMaxEnergyStored()} 仍然报真实组容量 —— 那是"池子有多大"，不是"能往里灌"。
         */
        @Override
        public boolean canReceive() {
            return false;
        }

        /** 全组已存之和 —— 就是上面 {@link #getGroupStored()} 那个数。 */
        private long totalStored() {
            return SolarPanelBlockEntity.this.getGroupStored();
        }
    }

    private final IEnergyStorage groupStorage = new GroupStorage();

    /**
     * 对方块能力（Jade、别的机器的管道）暴露的接口：<b>永远是"全组共享池"这一个视图</b>。
     *
     * <p><b>为什么不能"只有控制器给池子视图、其余给本块视图"（ZF24 第一版就是这么写的，错了）：</b>
     * 玩家右键/准星指的是<b>哪一块</b>是随机的，而 Jade 是对着哪块就查哪块的能力。
     * 于是组里只有控制器那块显示 1536/1536、其余显示自己那 512/512 ——
     * 在玩家眼里就是"并联以后数不对"，正是用户反馈的「Jade 也应该显示为一个整体」。
     * 锂电池那边所有块都报同一个总容量，所以看着是一体的；这里必须一样。</p>
     *
     * <p>注意：<b>读</b>全组是安全的，但"把电推给正下方的设备"绝不能走这个视图
     * （那会从坐标最小的那块开始扣电），所以那条路显式用 {@link #localStorage}。</p>
     */
    public IEnergyStorage getEnergyStorage() {
        return this.groupStorage;
    }

    /**
     * 本块自己那 512 FE 的读写口 —— <b>只给"往正下方推电"用</b>。
     *
     * <p>名字里带 local 是要提醒：它不是对外接口，别拿它去实现能力查询。</p>
     */
    public IEnergyStorage localStorage() {
        return this.blockStorage;
    }

    // ================= 组的状态查询 =================

    /**
     * 组员坐标快照。
     *
     * <p><b>非控制器也要拿到整组的快照</b>（去问控制器要）。第一版让它们"只返回自己一个位置"，
     * 是错的：对外的池子视图正是靠这份列表算总量和摊派的，只报自己 ⇒
     * 那块板底下抽电只能抽到自己那 512 —— 也就是"并联等于没并联"。
     * 真实快照仍然只有控制器维护（它是唯一做发电机的那块），这里只是取用。</p>
     */
    public List<BlockPos> memberPositions() {
        if (isController()) {
            ensureMembers();
            return this.members;
        }
        SolarPanelBlockEntity controller = controller();
        if (controller != null && controller != this) {
            return controller.memberPositions();
        }
        return List.of(this.worldPosition);
    }

    /** 本块所属的那组的控制器；没有组（或区块没加载）时返回 null。 */
    @Nullable
    private SolarPanelBlockEntity controller() {
        if (this.level == null || this.groupController == null) {
            return null;
        }
        return this.level.getBlockEntity(this.groupController) instanceof SolarPanelBlockEntity c ? c : null;
    }

    public boolean isController() {
        return this.groupController != null && this.groupController.equals(this.worldPosition);
    }

    /**
     * 组内块数。
     *
     * <p><b>非控制器也要问到精确值</b>（不能猜）：Jade / 其他机器会对着任意一块问容量，
     * 容量 = 块数 × 512，猜成 2 就会出现"3 块并排只显示 1024"这种数不对的观感。
     * 真实快照只有控制器持有，所以这里统一去问控制器。</p>
     */
    public int groupSize() {
        if (isController()) {
            ensureMembers();
            return Math.max(1, this.members.size());
        }
        return this.groupController == null ? 1 : Math.max(2, controllerGroupSize());
    }

    /** 去问控制器"组里几块"；拿不到（区块没加载 / 还没成型）就先按 1 兜底。 */
    private int controllerGroupSize() {
        if (this.level != null && this.groupController != null
                && this.level.getBlockEntity(this.groupController) instanceof SolarPanelBlockEntity controller) {
            controller.ensureMembers();
            return Math.max(1, controller.members.size());
        }
        return 1;
    }

    /**
     * 整组的总发电量（FE/t，"共享之前"的原始和）。
     *
     * <p>非控制器<b>不返回 0，而是去问控制器</b>：速率和是"这一组的属性"，
     * 跟"谁来问"无关。Jade 对着任意一块都会问这个值，
     * 返回 0 就会表现成"并联里有些板不发电"（ZF24 第一版的第二个坑）。</p>
     */
    public int getGroupTotalRate() {
        if (isController()) {
            return this.groupTotalRate;
        }
        if (this.level != null && this.groupController != null
                && this.level.getBlockEntity(this.groupController) instanceof SolarPanelBlockEntity controller) {
            return controller.groupTotalRate;
        }
        return ownRate();
    }

    /**
     * 并联<b>平分</b>之后，本块实际拿到的速率（FE/t）。
     *
     * <p>每块都分到"总和 ÷ 块数"，所以组内每块报出来的数字<b>完全相同</b>。</p>
     */
    public int getSharedRate() {
        int size = groupSize();
        return size <= 0 ? 0 : getGroupTotalRate() / size;
    }

    public int getEnergyStored() {
        return this.energy;
    }

    /** 整组已存的总电量（共享池的"当前值"，给状态消息用）。 */
    public long getGroupStored() {
        long sum = 0L;
        for (BlockPos p : memberPositions()) {
            if (this.level != null && this.level.getBlockEntity(p) instanceof SolarPanelBlockEntity panel) {
                sum += panel.energy;
            }
        }
        return sum;
    }

    // ================= 池子读写 =================

    /**
     * 摊派用的临时缓冲（<b>懒分配、之后复用</b>）。
     *
     * <p>为什么不用 {@code long[]} 现场 new 一个：下面是<b>每 tick</b>都在跑的热路径
     * （发电、下方机器抽电都走这里），每 tick 新建数组等于给 GC 白送垃圾。
     * 只在第一次真正需要时才分配，之后一直复用 —— 代价是这份缓冲常年占着
     * {@code 组内块数 × 8} 字节（512 块封顶也就 4 KB）。</p>
     */
    private long[] slotBuffer;

    /**
     * 按顺序往组员各自的 {@value #MAX_ENERGY} 里补电，返回实际（或模拟）接收量。
     *
     * <p>{@code simulate} 时只算数、不落盘 —— 这是 {@code IEnergyStorage} 的硬性约定，
     * 自动化模组靠它做"先问后写"。<b>跨块回写别忘了 {@code setChanged()}</b>：
     * 电是记在每块自己的存档里的，漏了就会"机器上显示有电、存盘后没了"。</p>
     */
    private long fillSlots(Level level, List<BlockPos> members, int maxReceive, boolean simulate) {
        return spread(level, members, maxReceive, simulate, true);
    }

    /** 按顺序从组员各自的存量里扣电，返回实际（或模拟）抽出量。 */
    private long drainSlots(Level level, List<BlockPos> members, int maxExtract, boolean simulate) {
        return spread(level, members, maxExtract, simulate, false);
    }

    /**
     * 补/扣的公共骨架：把组员的存量<b>抄进缓冲 → 交给 {@link GroupEnergy} 纯计算 → 写回</b>。
     *
     * <p>抄进缓冲这一步是刻意的：它让"池子算法"变成对一个 {@code long[]} 的运算，
     * 于是那个算法可以被单独跑起来验算（见 {@link GroupEnergy}）。
     * 顺带也解决了"摊派过程中成员被卸载"的问题 —— 真正写回时再查一次实体，
     * 查不到就跳过（那一块的份额自然留在它的存档里，不会消失）。</p>
     */
    private long spread(Level level, List<BlockPos> members, int amount, boolean simulate, boolean filling) {
        if (members.isEmpty() || amount <= 0) {
            return 0L;
        }
        if (this.slotBuffer == null || this.slotBuffer.length < members.size()) {
            this.slotBuffer = new long[members.size()];
        }
        int n = 0;
        for (BlockPos p : members) {
            if (level.getBlockEntity(p) instanceof SolarPanelBlockEntity panel) {
                this.slotBuffer[n++] = panel.energy;
            }
        }
        if (n == 0) {
            return 0L;
        }
        long moved = filling
                ? GroupEnergy.fill(this.slotBuffer, MAX_ENERGY, amount)
                : GroupEnergy.drain(this.slotBuffer, amount);
        if (moved <= 0L || simulate) {
            return moved;
        }
        int i = 0;
        for (BlockPos p : members) {
            if (level.getBlockEntity(p) instanceof SolarPanelBlockEntity panel) {
                if (panel.energy != this.slotBuffer[i]) {
                    panel.energy = (int) this.slotBuffer[i];
                    panel.setChanged();
                }
                i++;
            }
        }
        return moved;
    }

    // ================= 发电 =================

    /**
     * 晴天基准速率表（纯函数，方便单独验算）。
     *
     * <pre>
     *   0 ~  2000 日出      60      ← ZF29 起是原来的 3 倍
     *   2000 ~  5000 上午     135
     *   5000 ~  7000 正午     180
     *   7000 ~ 10000 下午     135
     *   10000 ~ 12000 傍晚     60
     *   12000 ~ 24000 夜间      0
     * </pre>
     */
    public static int clearRate(long dayTime) {
        long t = dayTime % 24000L;
        if (t < 0L) {
            t += 24000L;
        }
        if (t >= DAY_END) {
            return 0;
        }
        if (t < DAWN_END || t >= AFTERNOON_END) {
            return RATE_DAWN_DUSK;
        }
        if (t < MORNING_END || t >= NOON_END) {
            return RATE_MORNING;
        }
        return RATE_NOON;
    }

    /** 本块正上方是否"见天"：空气，或**无色**玻璃（染色/遮光玻璃不算 —— 用户说的是"透明玻璃"）。 */
    public boolean hasClearSky() {
        if (this.level == null) {
            return false;
        }
        BlockState above = this.level.getBlockState(this.worldPosition.above());
        return above.isAir() || above.is(Tags.Blocks.GLASS_BLOCKS_COLORLESS);
    }

    /** 本块**自己**（未并联）的发电速率。 */
    public int ownRate() {
        if (this.level == null || !this.level.isLoaded(this.worldPosition)) {
            return 0;
        }
        // 下界 / 末地没有天光，晒不到太阳
        if (!this.level.dimensionType().hasSkyLight()) {
            return 0;
        }
        if (!hasClearSky()) {
            return 0;
        }
        int base = clearRate(this.level.getDayTime());
        if (base <= 0) {
            return 0;
        }
        BlockPos sky = this.worldPosition.above();
        if (this.level.isThundering() && this.level.isRainingAt(sky)) {
            return base * THUNDER_PERCENT / 100;
        }
        if (this.level.isRainingAt(sky)) {
            return base * RAIN_PERCENT / 100;
        }
        return base;
    }

    // ================= tick =================

    public static void tick(Level level, BlockPos pos, BlockState state, SolarPanelBlockEntity panel) {
        if (!level.isClientSide) {
            panel.serverTick();
        }
    }

    private void serverTick() {
        if (this.level == null) {
            return;
        }
        if (--this.groupTimer <= 0) {
            this.groupTimer = GROUP_REFRESH;
            // 每块都要重算：只有这样才能发现"自己旁边被贴了一块"或"组员被挖走了"。
            // 不是控制器的那块算完只会得到一个控制器坐标，不持有整组快照 —— 很便宜。
            recomputeGroup();
        }
        if (isController()) {
            // 只有控制器负责发电 —— 全组每 tick 只发一次，所以这里传的是"本块分到的份额"。
            //
            // ⚠ 这里曾经写错成"传整组的和"，结果并联越多总发电越大（3 块各 20 ⇒ 实际发 60）。
            // 正确语义：组的输出 = 速率和 ÷ 块数 = 每块的额定值（ZF29 起是 60/135/180，**每块**的）。
            // 3 块并联只让"阴影/天气的差异被摊平"，不产生额外电力。
            int rate = getSharedRate();
            if (rate > 0) {
                fillSlots(this.level, memberPositions(), rate, false);
            }
        }
        pushToDeviceBelow();
    }

    /**
     * 重算并联组：在<b>同一层</b>沿水平四邻 BFS，求出组内块数与组内速率之和，
     * 并推举一个控制器。
     *
     * <p>"控制器 = 坐标最小的那块"是刻意选的：它与放置/加载顺序无关，
     * 每个组员各自 BFS 都会得到<b>同一个</b>答案，不需要任何协商或额外同步。
     * 代价是"控制器"这个身份会因为旁边多出一块更靠前的板而<b>转移</b> —— 转移本身无害，
     * 因为电是记在每块自己身上的，谁当控制器只决定"谁来算总和、谁来发电"。</p>
     */
    private void recomputeGroup() {
        if (this.level == null) {
            return;
        }
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        seen.add(this.worldPosition);
        queue.add(this.worldPosition);

        List<BlockPos> found = new ArrayList<>();
        int total = 0;
        while (!queue.isEmpty() && found.size() < MAX_GROUP) {
            BlockPos p = queue.poll();
            if (!(this.level.getBlockEntity(p) instanceof SolarPanelBlockEntity panel)) {
                continue;
            }
            found.add(p);
            total += panel.ownRate();
            for (Direction dir : Direction.Plane.HORIZONTAL) {
                BlockPos n = p.relative(dir);
                if (seen.add(n) && this.level.isLoaded(n)
                        && this.level.getBlockEntity(n) instanceof SolarPanelBlockEntity) {
                    queue.add(n);
                }
            }
        }

        BlockPos best = this.worldPosition;
        for (BlockPos p : found) {
            if (comparePos(p, best) < 0) {
                best = p;
            }
        }

        this.groupController = best;
        this.groupTotalRate = total;
        this.cachedMemberCount = found.size();
        this.members.clear();
        if (best.equals(this.worldPosition)) {
            this.members.addAll(found);
            this.members.sort(SolarPanelBlockEntity::comparePos);
        }
    }

    /**
     * 水平邻居变了（旁边贴上来一块板、或者旁边那块被挖掉）时由方块调用：把快照标成待重建。
     *
     * <p>为什么需要它：{@link #ensureMembers()} 只认"块数"这一个指纹，
     * 而它平时由控制器每 {@value #GROUP_REFRESH} tick 的 BFS 刷新 ——
     * 那个刷新最坏要一秒才轮到，玩家放下第二块板时若正好有人在抽电，
     * 会先看到"抽不到"再看到"抽得到"。这里直接作废快照，下一次查询立刻重算。</p>
     */
    public void invalidateGroup() {
        this.cachedMemberCount = 0;
    }

    /**
     * 组员快照失效检测：块数变了就一定重建。
     *
     * <p>ⓘ "块数变了"这个判据<b>不完整</b>（换掉一块、块数不变的极端情况察觉不到），
     * 但那种情况只在"同时挖掉一块又补上一块"时出现，而那时两边都会调
     * {@link #invalidateGroup()}，所以漏不掉。宁可留这个已知的小缝，
     * 也不引入一个每 tick 维护的全局计数器 —— 见档案 §9 的取舍记录。</p>
     */
    private void ensureMembers() {
        if (this.cachedMemberCount == 0) {
            recomputeGroup();
        }
    }

    /** 坐标全序（x → y → z），保证"组控制器"这个名字在任何一端都指同一块。 */
    private static int comparePos(BlockPos a, BlockPos b) {
        if (a.getX() != b.getX()) {
            return Integer.compare(a.getX(), b.getX());
        }
        if (a.getY() != b.getY()) {
            return Integer.compare(a.getY(), b.getY());
        }
        return Integer.compare(a.getZ(), b.getZ());
    }

    /**
     * 把本块缓冲里的电推给<b>正下方</b>的设备（用户："直接供电给下方的设备"）。
     *
     * <p>这里<b>故意</b>用 {@link #localStorage}（本块那 512）而不是对外的池子视图：
     * 池子视图的抽取是"从坐标最小那块开始扣"，下部机器从哪块板底下抽就扣哪块，
     * 才符合"谁在供电"的直觉；用池子视图会出现"电从隔壁那块消失"。</p>
     */
    private void pushToDeviceBelow() {
        if (this.level == null || this.energy <= 0) {
            return;
        }
        BlockPos below = this.worldPosition.below();
        if (!this.level.isLoaded(below)) {
            return;
        }
        IEnergyStorage target = this.level.getCapability(
                Capabilities.EnergyStorage.BLOCK, below, Direction.UP);
        if (target == null) {
            return;
        }
        int sent = target.receiveEnergy(this.energy, false);
        if (sent > 0) {
            this.energy -= sent;
            setChanged();
        }
    }

    // ================= 状态消息 =================

    /**
     * Shift+右键时调用：把并联数量 / 总发电量 / 共享池 / 本块状态打到**聊天栏**（左下角）。
     *
     * <p>{@code displayClientMessage(..., false)} 的 {@code false} 就是"进聊天栏"；
     * 锂电池那边用的是 {@code true}（动作栏，物品栏上方），<b>两处不一样，别抄错</b>。</p>
     */
    public void sendStatus(Player player) {
        player.displayClientMessage(Component.translatable("message.potato_s_t.solar_status",
                groupSize(), getGroupTotalRate()), false);
        player.displayClientMessage(Component.translatable("message.potato_s_t.solar_self",
                getSharedRate(), stateText()), false);
        player.displayClientMessage(Component.translatable("message.potato_s_t.solar_pool",
                getGroupStored(), (long) groupSize() * MAX_ENERGY, this.energy, MAX_ENERGY), false);
    }

    /** 当前发电状态（给上面那条消息用）。 */
    private Component stateText() {
        if (this.level == null) {
            return Component.translatable("message.potato_s_t.solar.state.night");
        }
        if (!this.level.dimensionType().hasSkyLight()) {
            return Component.translatable("message.potato_s_t.solar.state.dimension");
        }
        if (!hasClearSky()) {
            return Component.translatable("message.potato_s_t.solar.state.blocked");
        }
        if (clearRate(this.level.getDayTime()) <= 0) {
            return Component.translatable("message.potato_s_t.solar.state.night");
        }
        BlockPos sky = this.worldPosition.above();
        if (this.level.isThundering() && this.level.isRainingAt(sky)) {
            return Component.translatable("message.potato_s_t.solar.state.thunder");
        }
        if (this.level.isRainingAt(sky)) {
            return Component.translatable("message.potato_s_t.solar.state.rain");
        }
        return Component.translatable("message.potato_s_t.solar.state.clear");
    }

    // ================= 持久化 =================

    /**
     * 只存"本块那 512 FE 里现在有多少"。
     *
     * <p>组信息（控制器、块数、快照）一律<b>不落盘</b>：它们全部可以由世界状态重算出来，
     * 存下来反而多一份可能对不上的副本。存档格式与单块版（ZF22）完全一致。</p>
     */
    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        this.energy = tag.getInt("energy");
        this.groupController = null;
        this.members.clear();
        this.cachedMemberCount = 0;
        this.groupTotalRate = 0;
        this.groupTimer = 1;
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putInt("energy", this.energy);
    }
}
