# -*- coding: utf-8 -*-
u"""_zf127_java.py —— ZF127 的 Java 改动（**逐条可逆**：每条都记着 old/new，能反推出改前件）

用户原话：
「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）
  材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t」

改什么（四个文件）：
  ① `ModItems.java`：两个物品（`silver_wire` / `silver_wire_spool`，耐久 32 与铜线轴一致）
     + 创造页两行（§4.82：新物品不进创造页 = 物品栏看不见 + JEI 搜不到）；
  ② `TerminalBlockEntity.java`：连接线从 `Set<BlockPos>` 改成 `Map<BlockPos, Integer>`
     （对端 → **这条线自己的速率**）；新增 `SILVER_TRANSFER_RATE = 16134`、
     `lineRate()` / `capacity()` / `capacityFor(int)`；端子缓冲与 IO 速率随"接到的最高档线缆"伸缩；
     NBT 两种格式都认（老存档是 ListTag&lt;LongTag&gt; = 全是铜线）；
  ③ `TerminalBlock.java`：银线轴分支（与铜线轴**共用**同一个连接处理器，只有速率不同）；
  ④ `client/TerminalRenderer.java`：FE 连线**按每条线自己的速率**上色（银线 = 银白色），
     `WIRE_RADIUS` **一个字节都不改**（用户点名"像素大小一样"）。

⚠ 换行：`TerminalBlock.java` / `TerminalBlockEntity.java` / `TerminalRenderer.java` 是 **CRLF**，
  `ModItems.java` 是 **LF**（`.gitattributes` 是 `* -text`，盘上是什么仓库里就是什么）⇒
  脚本按每份文件自己的换行写回，绝不统一（§4.8）。

跑法：
    python build\\zftools\\_zf127_java.py            # 改
    python build\\zftools\\_zf127_java.py --proof    # 反推证明（改完的盘上 == 改前件）
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"E:\PotatoST"
BK = r"C:\PotatoST救援\zf127_pre"
JAVA = r"src\main\java\com\potatost\mod"

# ============================================================
#  ① ModItems.java（LF）
# ============================================================
MODITEMS_REG_OLD = u'''    public static final DeferredItem<Item> POWER_CABLE_SPOOL =
            ITEMS.register("power_cable_spool",
                    () -> new Item(new Item.Properties().durability(32)));
'''

MODITEMS_REG_NEW = MODITEMS_REG_OLD + u'''
    // ===== 银线 / 银线轴（0.11 ZF127）=====
    /**
     * 银线：银线轴的原料（2 个银锭 → 4 根，与铜线逐字对应）。
     *
     * <p><b>⚠ 贴图先不画</b>（用户点名「材质先不画」）⇒ 模型借原版<b>铁粒</b>占位
     * （见 {@code models/item/silver_wire.json}），与"电容借铁粒 / 硅借火药"同一个做法。</p>
     */
    public static final DeferredItem<Item> SILVER_WIRE =
            ITEMS.register("silver_wire", () -> new Item(new Item.Properties()));

    /**
     * 银线轴：与铜线轴<b>逐项一致</b>（32 点耐久、右键连端子、耗尽返还空线轴、连接距离 16 格、
     * 线径一样粗），只有两处不同 —— ① 线缆渲染成<b>银白色</b>；② 单线速率
     * {@link TerminalBlockEntity#SILVER_TRANSFER_RATE} = <b>16134 FE/t</b>（铜线 2048）。
     *
     * <p>用户原话：「加一个银线轴 和铜线轴一致（先搞银线 配方什么的都一致只不过铜的换成银的）
     * 材质先不画 连接线缆还是一样的像素大小 只不过变成银白色的 传输速率 16134Fe/t」。</p>
     *
     * <p><b>⚠ 贴图先不画</b>：模型借原版<b>铁锭</b>占位（见 {@code models/item/silver_wire_spool.json}）。</p>
     */
    public static final DeferredItem<Item> SILVER_WIRE_SPOOL =
            ITEMS.register("silver_wire_spool",
                    () -> new Item(new Item.Properties().durability(32)));
'''

MODITEMS_TAB_OLD = u'''                        output.accept(COPPER_WIRE_SPOOL.get());
'''

MODITEMS_TAB_NEW = u'''                        output.accept(COPPER_WIRE_SPOOL.get());
                        output.accept(SILVER_WIRE.get());            // ← 0.11 ZF127 银线
                        output.accept(SILVER_WIRE_SPOOL.get());      // ← 0.11 ZF127 银线轴
'''

# ============================================================
#  ② TerminalBlockEntity.java（CRLF）
# ============================================================
TBE_CONST_OLD = u'''    /**
     * 单个端子缓冲上限。
     * ★ 2024 调整：16384 -> 2048。端子是"过路件"，不承担储能职责。
     * 注意：端子间用"移动差额一半"的均衡规则 -> 单线稳态通过率 ≈ 本值 ÷ 2，
     * 即 2048 时约 1024 FE/t/线（与各机器单次能量 IO 上限 1024 对齐）。
     */
    public static final int MAX_ENERGY = 2048;
    /** 每根连接线每 tick 的最大传输量 */
    public static final int TRANSFER_RATE = 2048;
'''

TBE_CONST_NEW = u'''    /**
     * 单个端子缓冲上限（<b>铜线档</b>：纯铜线网络里就是最终值）。
     * ★ 2024 调整：16384 -> 2048。端子是"过路件"，不承担储能职责。
     * 注意：端子间用"移动差额一半"的均衡规则 -> 单线稳态通过率 ≈ 本值 ÷ 2，
     * 即 2048 时约 1024 FE/t/线（与各机器单次能量 IO 上限 1024 对齐）。
     *
     * <p>⚠ <b>ZF127 起这个常量是"铜线档的值"</b>：端子接上银线时，实际缓冲 =
     * {@link #capacityFor(int)}（银线 = 2 × 速率 = 32268；铜线档仍是 2048，一字不改）。
     * <b>纯铜线的端子一个字节的行为都没变</b>（2048 缓冲 / 2048 IO / 单线稳态 ~1024）。</p>
     */
    public static final int MAX_ENERGY = 2048;
    /** 每根连接线每 tick 的最大传输量（<b>铜线档</b>） */
    public static final int TRANSFER_RATE = 2048;
    /**
     * <b>银线</b>的单线速率：<b>16134 FE/t</b>（ZF127 用户点名给的数）。
     *
     * <p>铜线与银线在<b>同一个 FE 网络</b>上（同一个连接集合、同一套输入/输出模式），
     * 每条连接线各自记着自己的速率 ⇒ 混着接的时候，银线段跑银线的数、铜线段跑铜线的数。</p>
     */
    public static final int SILVER_TRANSFER_RATE = 16_134;
'''

TBE_FIELD_OLD = u'''    /** 与本端子相连的其他端子坐标（双方各存一份） */
    private final Set<BlockPos> connections = new HashSet<>();
'''

TBE_FIELD_NEW = u'''    /**
     * 与本端子相连的其他端子坐标 → <b>这条连接线自己的速率</b>（双方各存一份，值相同）。
     * ⚠ ZF127 从 {@code Set<BlockPos>} 改成 {@code Map}：铜线 2048 / 银线 16134 要能混在一条网络上。
     */
    private final Map<BlockPos, Integer> connections = new HashMap<>();
'''

TBE_STORAGE_OLD = u'''            if (mode != Mode.INPUT) return 0;
            int accepted = Math.min(Math.min(maxReceive, TRANSFER_RATE), MAX_ENERGY - energy);
'''

TBE_STORAGE_NEW = u'''            if (mode != Mode.INPUT) return 0;
            int accepted = Math.min(Math.min(maxReceive, lineRate()), capacity() - energy);
'''

TBE_EXTRACT_OLD = u'''            if (mode != Mode.OUTPUT) return 0;
            int extracted = Math.min(Math.min(maxExtract, TRANSFER_RATE), energy);
'''

TBE_EXTRACT_NEW = u'''            if (mode != Mode.OUTPUT) return 0;
            int extracted = Math.min(Math.min(maxExtract, lineRate()), energy);
'''

TBE_MAXSTORED_OLD = u'''        @Override
        public int getMaxEnergyStored() {
            return MAX_ENERGY;
        }
'''

TBE_MAXSTORED_NEW = u'''        @Override
        public int getMaxEnergyStored() {
            return capacity();
        }
'''

TBE_GETCONN_OLD = u'''    public Set<BlockPos> getConnections() {
        return this.connections;
    }
'''

TBE_GETCONN_NEW = u'''    /** 连接集合：对端坐标 → 这条线的单线速率（渲染端按这个上色，ZF127） */
    public Map<BlockPos, Integer> getConnections() {
        return this.connections;
    }

    /**
     * 本端子接到的<b>最高</b>单线速率（没接线时按铜线算 —— 空端子行为与 ZF126 一致）。
     * 端子的能力（缓冲 + 收/放速率）全部按这个值伸缩。
     */
    public int lineRate() {
        int best = TRANSFER_RATE;
        for (int rate : this.connections.values()) {
            if (rate > best) {
                best = rate;
            }
        }
        return best;
    }

    /**
     * 端子的 FE 缓冲上限：<b>铜线档 = {@value #MAX_ENERGY}</b>（一个字节的行为都不变）；
     * 接上银线 = <b>2 × {@link #lineRate()}</b>。
     *
     * <p>为什么银线要 <b>2 倍</b>：端子之间走"移动差额一半"的均衡规则，
     * 要把 rate 在一 tick 里传满，两端的电量差得有 2 × rate ⇒ 缓冲也得有 2 × rate。</p>
     */
    public int capacity() {
        return capacityFor(lineRate());
    }

    /**
     * 给定单线速率下的端子缓冲（纯函数：探针与校验器可以单独核这个式子）。
     *
     * <p>⚠ <b>探针抓到的第一版 bug</b>：原来写成 {@code Math.max(MAX_ENERGY, lineRate * 2)}，
     * 于是<b>铜线档</b>（2048）也变成 4096 —— 纯铜端子的行为被静默改掉了
     * （一 tick 从 1024 变 2048）。改成"铜线档及以下就是 {@value #MAX_ENERGY}"才对。</p>
     */
    public static int capacityFor(int lineRate) {
        return lineRate <= TRANSFER_RATE ? MAX_ENERGY : lineRate * 2;
    }

    /** 本端子记着的、通往 {@code other} 那条线的速率（对面没记就按自己这份） */
    private int rateTo(BlockPos other) {
        Integer rate = this.connections.get(other);
        return rate == null ? TRANSFER_RATE : rate;
    }
'''

TBE_ADD_OLD = u'''    /** 返回 true 表示新连接建立成功 */
    public boolean addConnection(BlockPos other) {
        if (other.equals(this.getBlockPos())) return false;
        if (this.connections.add(other)) {
            sync();
            return true;
        }
        return false;
    }
'''

TBE_ADD_NEW = u'''    /**
     * 建立连接。
     *
     * @param rate 这条线的单线速率（铜线 {@link #TRANSFER_RATE} / 银线 {@link #SILVER_TRANSFER_RATE}）
     * @return true 表示<b>新建立</b>了一条连接，或把已有连接<b>升级</b>成了更快的线（两种情况都扣耐久）
     */
    public boolean addConnection(BlockPos other, int rate) {
        if (other.equals(this.getBlockPos())) return false;
        Integer old = this.connections.get(other);
        if (old == null) {
            this.connections.put(other, rate);
            sync();
            return true;
        }
        if (rate > old) {
            // 已经有铜线了，再拿银线轴连一次 = 就地换成银线（不降级：拿铜线轴连银线仍是银线）
            this.connections.put(other, rate);
            sync();
            return true;
        }
        return false;
    }
'''

TBE_REMOVE_OLD = u'''    public void removeConnection(BlockPos other) {
        if (this.connections.remove(other)) {
            sync();
        }
    }
'''

TBE_REMOVE_NEW = u'''    public void removeConnection(BlockPos other) {
        if (this.connections.remove(other) != null) {
            sync();
        }
    }
'''

TBE_TICK_OLD = u'''        // 清理失效连接（对面端子被挖掉了）
        if (!connections.isEmpty()) {
            connections.removeIf(otherPos -> !(level.getBlockEntity(otherPos) instanceof TerminalBlockEntity));
        }

        // 与每个相连端子做能量均衡（每根线传输 = 差额一半，受 TRANSFER_RATE 封顶）
        for (BlockPos otherPos : connections) {
            if (!(level.getBlockEntity(otherPos) instanceof TerminalBlockEntity other)) continue;
            int mine = this.energy;
            int theirs = other.energy;
            if (mine > theirs) {
                int delta = Math.min(TRANSFER_RATE, (mine - theirs + 1) / 2);
                this.energy -= delta;
                other.energy += delta;
                this.setChanged();
                other.setChanged();
            } else if (theirs > mine) {
                int delta = Math.min(TRANSFER_RATE, (theirs - mine + 1) / 2);
                this.energy += delta;
                other.energy -= delta;
                this.setChanged();
                other.setChanged();
            }
        }

        // ★ 输入模式：主动从相邻能源方块抽取（应对只会"被抽"的发电机）
        if (mode == Mode.INPUT && energy < MAX_ENERGY) {
            for (Direction side : Direction.values()) {
                if (energy >= MAX_ENERGY) break;
                BlockPos neighborPos = getBlockPos().relative(side);
                // 相邻是端子就跳过（端子之间走上面的网络均衡）
                if (level.getBlockEntity(neighborPos) instanceof TerminalBlockEntity) continue;
                IEnergyStorage storage = level.getCapability(
                        Capabilities.EnergyStorage.BLOCK, neighborPos, side.getOpposite());
                if (storage == null || !storage.canExtract()) continue;
                int amount = Math.min(TRANSFER_RATE, MAX_ENERGY - energy);
                int received = storage.extractEnergy(amount, false);
                if (received > 0) {
                    this.energy += received;
                    setChanged();
                }
            }
        }

        // ★ 输出模式：主动向相邻机器输送（应对只等别人"推"的机器）
        if (mode == Mode.OUTPUT && energy > 0) {
            for (Direction side : Direction.values()) {
                if (energy <= 0) break;
                BlockPos neighborPos = getBlockPos().relative(side);
                if (level.getBlockEntity(neighborPos) instanceof TerminalBlockEntity) continue;
                IEnergyStorage storage = level.getCapability(
                        Capabilities.EnergyStorage.BLOCK, neighborPos, side.getOpposite());
                if (storage == null || !storage.canReceive()) continue;
                int amount = Math.min(TRANSFER_RATE, energy);
'''

TBE_TICK_NEW = u'''        // 清理失效连接（对面端子被挖掉了）
        if (!connections.isEmpty()) {
            connections.entrySet().removeIf(e -> !(level.getBlockEntity(e.getKey()) instanceof TerminalBlockEntity));
        }

        // ★ 银线被拆掉之后缓冲上限会缩回铜线档 ⇒ 多出来的电夹掉（不做"隔空搬运"）
        int cap = capacity();
        if (energy > cap) {
            energy = cap;
            setChanged();
        }
        int rate = lineRate();

        // 与每个相连端子做能量均衡（每根线传输 = 差额一半，受**这条线自己的速率**封顶）
        for (Map.Entry<BlockPos, Integer> entry : connections.entrySet()) {
            BlockPos otherPos = entry.getKey();
            if (!(level.getBlockEntity(otherPos) instanceof TerminalBlockEntity other)) continue;
            int line = Math.min(entry.getValue(), other.rateTo(this.getBlockPos()));
            int mine = this.energy;
            int theirs = other.energy;
            if (mine > theirs) {
                int delta = Math.min(line, (mine - theirs + 1) / 2);
                this.energy -= delta;
                other.energy += delta;
                this.setChanged();
                other.setChanged();
            } else if (theirs > mine) {
                int delta = Math.min(line, (theirs - mine + 1) / 2);
                this.energy += delta;
                other.energy -= delta;
                this.setChanged();
                other.setChanged();
            }
        }

        // ★ 输入模式：主动从相邻能源方块抽取（应对只会"被抽"的发电机）
        if (mode == Mode.INPUT && energy < cap) {
            for (Direction side : Direction.values()) {
                if (energy >= cap) break;
                BlockPos neighborPos = getBlockPos().relative(side);
                // 相邻是端子就跳过（端子之间走上面的网络均衡）
                if (level.getBlockEntity(neighborPos) instanceof TerminalBlockEntity) continue;
                IEnergyStorage storage = level.getCapability(
                        Capabilities.EnergyStorage.BLOCK, neighborPos, side.getOpposite());
                if (storage == null || !storage.canExtract()) continue;
                int amount = Math.min(rate, cap - energy);
                int received = storage.extractEnergy(amount, false);
                if (received > 0) {
                    this.energy += received;
                    setChanged();
                }
            }
        }

        // ★ 输出模式：主动向相邻机器输送（应对只等别人"推"的机器）
        if (mode == Mode.OUTPUT && energy > 0) {
            for (Direction side : Direction.values()) {
                if (energy <= 0) break;
                BlockPos neighborPos = getBlockPos().relative(side);
                if (level.getBlockEntity(neighborPos) instanceof TerminalBlockEntity) continue;
                IEnergyStorage storage = level.getCapability(
                        Capabilities.EnergyStorage.BLOCK, neighborPos, side.getOpposite());
                if (storage == null || !storage.canReceive()) continue;
                int amount = Math.min(rate, energy);
'''

TBE_LOAD_OLD = u'''        // ★ 上限 16384 -> 2048 后，老存档里可能存着超过新上限的电量：加载时夹住，
        //   否则会出现"现存电量 > 上限"的显示/逻辑异常（超出的部分丢弃）
        this.energy = Mth.clamp(tag.getInt("energy"), 0, MAX_ENERGY);

        this.connections.clear();
        ListTag list = tag.getList("connections", Tag.TAG_LONG);
        for (Tag entry : list) {
            this.connections.add(BlockPos.of(((LongTag) entry).getAsLong()));
        }
'''

TBE_LOAD_NEW = u'''        // ★ 上限 16384 -> 2048 后，老存档里可能存着超过新上限的电量：加载时夹住，
        //   否则会出现"现存电量 > 上限"的显示/逻辑异常（超出的部分丢弃）。
        //   ⚠ ZF127：夹的上限现在依赖线缆档位 ⇒ 先原样收下，等连接读完再夹（见本方法末尾）。
        this.energy = Math.max(0, tag.getInt("energy"));

        this.connections.clear();
        // ★ ZF127：新格式是 ListTag<CompoundTag>{pos, rate}；老存档（ZF126 及以前）是
        //   ListTag<LongTag>（每根都是铜线）—— 两种都认，老存档不会掉线（§4.8 存档兼容）。
        ListTag list = tag.getList("connections", Tag.TAG_COMPOUND);
        if (!list.isEmpty()) {
            for (Tag entry : list) {
                CompoundTag c = (CompoundTag) entry;
                this.connections.put(BlockPos.of(c.getLong("pos")), c.getInt("rate"));
            }
        } else {
            for (Tag entry : tag.getList("connections", Tag.TAG_LONG)) {
                this.connections.put(BlockPos.of(((LongTag) entry).getAsLong()), TRANSFER_RATE);
            }
        }
'''

TBE_LOADTAIL_OLD = u'''        ListTag powerList = tag.getList("power_connections", Tag.TAG_LONG);
        for (Tag entry : powerList) {
            this.powerConnections.add(BlockPos.of(((LongTag) entry).getAsLong()));
        }
    }
'''

TBE_LOADTAIL_NEW = u'''        ListTag powerList = tag.getList("power_connections", Tag.TAG_LONG);
        for (Tag entry : powerList) {
            this.powerConnections.add(BlockPos.of(((LongTag) entry).getAsLong()));
        }

        // 连接读完了 ⇒ 现在才知道该按哪个档位夹（银线端子 32268、纯铜线端子 2048）
        this.energy = Mth.clamp(this.energy, 0, capacity());
    }
'''

TBE_SAVE_OLD = u'''        tag.putInt("energy", this.energy);
        ListTag list = new ListTag();
        for (BlockPos pos : this.connections) {
            list.add(LongTag.valueOf(pos.asLong()));
        }
        tag.put("connections", list);
'''

TBE_SAVE_NEW = u'''        tag.putInt("energy", this.energy);
        ListTag list = new ListTag();
        for (Map.Entry<BlockPos, Integer> entry : this.connections.entrySet()) {
            CompoundTag c = new CompoundTag();
            c.putLong("pos", entry.getKey().asLong());
            c.putInt("rate", entry.getValue());
            list.add(c);
        }
        tag.put("connections", list);
'''

TBE_SETREMOVED_OLD = u'''            for (BlockPos otherPos : connections) {
                if (level.getBlockEntity(otherPos) instanceof TerminalBlockEntity other) {
                    other.removeConnection(this.getBlockPos());
                }
            }
'''

TBE_SETREMOVED_NEW = u'''            for (BlockPos otherPos : connections.keySet()) {
                if (level.getBlockEntity(otherPos) instanceof TerminalBlockEntity other) {
                    other.removeConnection(this.getBlockPos());
                }
            }
'''

TBE_IMPORT_OLD = u'''import java.util.HashSet;
import java.util.Set;
'''

TBE_IMPORT_NEW = u'''import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
'''

# ============================================================
#  ③ TerminalBlock.java（CRLF）
# ============================================================
TB_PENDING_OLD = u'''    /** 每个玩家用铜线轴选中的第一个端子 */
    private static final Map<UUID, BlockPos> PENDING_CONNECTIONS = new HashMap<>();
'''

TB_PENDING_NEW = u'''    /**
     * 每个玩家用<b>线缆轴</b>选中的第一个端子。
     * ⚠ 铜线轴与银线轴<b>共用一个待选</b>：先拿铜线轴点一下、再拿银线轴点第二个端子，
     * 这根线就按**收尾那一根线轴**的速率算（摆明了"你最后手里拿的是什么线"）。
     */
    private static final Map<UUID, BlockPos> PENDING_CONNECTIONS = new HashMap<>();
'''

TB_BRANCH_OLD = u'''        // 铜线轴右键 = 连接 / 取消连接（每次成功连接消耗 1 点耐久）
        if (stack.is(ModItems.COPPER_WIRE_SPOOL.get())) {
            if (!level.isClientSide && level instanceof ServerLevel serverLevel) {
                if (handleConnectionTool(level, pos, player)) {
                    stack.hurtAndBreak(1, serverLevel, player, item -> giveEmptySpoolBack(player));
                }
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
'''

TB_BRANCH_NEW = u'''        // 铜线轴右键 = 连接 / 取消连接（每次成功连接消耗 1 点耐久）
        if (stack.is(ModItems.COPPER_WIRE_SPOOL.get())) {
            if (!level.isClientSide && level instanceof ServerLevel serverLevel) {
                if (handleConnectionTool(level, pos, player, TerminalBlockEntity.TRANSFER_RATE)) {
                    stack.hurtAndBreak(1, serverLevel, player, item -> giveEmptySpoolBack(player));
                }
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        // 银线轴右键 = 同一条 FE 网络上的**银线**（ZF127：单线速率 16134 FE/t，线径与铜线一样粗）
        if (stack.is(ModItems.SILVER_WIRE_SPOOL.get())) {
            if (!level.isClientSide && level instanceof ServerLevel serverLevel) {
                if (handleConnectionTool(level, pos, player, TerminalBlockEntity.SILVER_TRANSFER_RATE)) {
                    stack.hurtAndBreak(1, serverLevel, player, item -> giveEmptySpoolBack(player));
                }
            }
            return ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
'''

TB_HANDLER_OLD = u'''    /** @return true 表示这次右键成功建立了一条新连接（用于扣耐久） */
    private boolean handleConnectionTool(Level level, BlockPos pos, Player player) {
'''

TB_HANDLER_NEW = u'''    /**
     * 线缆连接处理器：铜线轴与银线轴<b>共用这一套流程</b>，只有单线速率不同。
     *
     * @param rate 这条线的单线速率：铜线 {@link TerminalBlockEntity#TRANSFER_RATE} = 2048、
     *             银线 {@link TerminalBlockEntity#SILVER_TRANSFER_RATE} = 16134
     * @return true 表示这次右键成功建立（或把铜线升级成银线）了一条连接 —— 用于扣耐久
     */
    private boolean handleConnectionTool(Level level, BlockPos pos, Player player, int rate) {
'''

TB_ADD_OLD = u'''            if (self.addConnection(previous)) {
                other.addConnection(pos);
'''

TB_ADD_NEW = u'''            if (self.addConnection(previous, rate)) {
                other.addConnection(pos, rate);
'''

# ============================================================
#  ④ client/TerminalRenderer.java（CRLF）
# ============================================================
TR_COLOR_OLD = u'''    /** 紫色（动力线缆） */
    private static final float PURPLE_R = 0.58F, PURPLE_G = 0.28F, PURPLE_B = 0.92F, PURPLE_A = 0.9F;
'''

TR_COLOR_NEW = u'''    /** 紫色（动力线缆） */
    private static final float PURPLE_R = 0.58F, PURPLE_G = 0.28F, PURPLE_B = 0.92F, PURPLE_A = 0.9F;
    /** 银白色（FE 银线，ZF127；同一条网络上按**每条线自己的速率**选颜色） */
    private static final float SILVER_R = 0.88F, SILVER_G = 0.91F, SILVER_B = 0.95F, SILVER_A = 0.9F;
'''

TR_WIRE_RADIUS_OLD = u'''    private static final ResourceLocation WIRE_TEXTURE =
            ResourceLocation.parse("minecraft:textures/block/white_concrete.png");
    private static final double WIRE_RADIUS = 0.03125D;
'''

TR_WIRE_RADIUS_NEW = u'''    private static final ResourceLocation WIRE_TEXTURE =
            ResourceLocation.parse("minecraft:textures/block/white_concrete.png");
    /** ⚠ 线径（= 贴图 1 像素）：ZF127 加银线时**一个字节都没改** —— 用户点名「连接线缆还是一样的像素大小」 */
    private static final double WIRE_RADIUS = 0.03125D;
'''

TR_RENDER_OLD = u'''        // FE 铜线（古铜色）
        renderWireSet(terminal, terminal.getConnections(), BRONZE_R, BRONZE_G, BRONZE_B, BRONZE_A,
                origin, selfAnchor, poseStack, buffer, packedLight, packedOverlay);
'''

TR_RENDER_NEW = u'''        // FE 网络（铜线古铜色 / 银线银白色：一条一条按它自己的速率上色）
        renderFeWires(terminal, origin, selfAnchor, poseStack, buffer, packedLight, packedOverlay);
'''

TR_NEWMETHOD_OLD = u'''    private void renderWireSet(TerminalBlockEntity terminal, Set<BlockPos> set,
'''

TR_NEWMETHOD_NEW = u'''    /**
     * FE 网络连线：每条线按<b>它自己的速率</b>选颜色（铜线 = 古铜色，银线 = 银白色）。
     *
     * <p>⚠ 线径走的是同一个 {@link #WIRE_RADIUS}（用户点名"像素大小一样"），
     * 铜线银线只差颜色。</p>
     */
    private void renderFeWires(TerminalBlockEntity terminal, Vec3 origin, Vec3 selfAnchor,
                               PoseStack poseStack, MultiBufferSource buffer,
                               int packedLight, int packedOverlay) {
        BlockPos selfPos = terminal.getBlockPos();
        for (Map.Entry<BlockPos, Integer> entry : terminal.getConnections().entrySet()) {
            BlockPos otherPos = entry.getKey();
            if (selfPos.compareTo(otherPos) > 0) continue;   // 每根线只画一次
            BlockState otherState = terminal.getLevel().getBlockState(otherPos);
            if (!otherState.is(ModBlocks.TERMINAL.get())) continue;
            if (!(terminal.getLevel().getBlockEntity(otherPos) instanceof TerminalBlockEntity)) continue;
            Vec3 from = selfAnchor.subtract(origin);
            Vec3 to = terminalAnchor(otherPos, otherState).subtract(origin);
            boolean silver = entry.getValue() >= TerminalBlockEntity.SILVER_TRANSFER_RATE;
            renderWire(poseStack, buffer, packedLight, packedOverlay, from, to,
                    silver ? SILVER_R : BRONZE_R, silver ? SILVER_G : BRONZE_G,
                    silver ? SILVER_B : BRONZE_B, silver ? SILVER_A : BRONZE_A);
        }
    }

    private void renderWireSet(TerminalBlockEntity terminal, Set<BlockPos> set,
'''

TR_IMPORT_OLD = u'''import java.util.Set;
'''

TR_IMPORT_NEW = u'''import java.util.Map;
import java.util.Set;
'''

# ============================================================
#  文件 → 编辑清单
# ============================================================
EDITS = [
    (JAVA + r"\ModItems.java", [
        (u"物品登记", MODITEMS_REG_OLD, MODITEMS_REG_NEW),
        (u"创造页两行", MODITEMS_TAB_OLD, MODITEMS_TAB_NEW),
    ]),
    (JAVA + r"\TerminalBlockEntity.java", [
        (u"常量（银线速率 + 缓冲注释）", TBE_CONST_OLD, TBE_CONST_NEW),
        (u"连接字段 Set -> Map", TBE_FIELD_OLD, TBE_FIELD_NEW),
        (u"IO 接口收电上限", TBE_STORAGE_OLD, TBE_STORAGE_NEW),
        (u"IO 接口放电上限", TBE_EXTRACT_OLD, TBE_EXTRACT_NEW),
        (u"IO 接口容量", TBE_MAXSTORED_OLD, TBE_MAXSTORED_NEW),
        (u"getConnections + lineRate/capacity", TBE_GETCONN_OLD, TBE_GETCONN_NEW),
        (u"addConnection(rate)", TBE_ADD_OLD, TBE_ADD_NEW),
        (u"removeConnection", TBE_REMOVE_OLD, TBE_REMOVE_NEW),
        (u"serverTick（均衡/抽/推）", TBE_TICK_OLD, TBE_TICK_NEW),
        (u"读盘（两种格式）", TBE_LOAD_OLD, TBE_LOAD_NEW),
        (u"读盘末尾夹电量", TBE_LOADTAIL_OLD, TBE_LOADTAIL_NEW),
        (u"存盘（pos+rate）", TBE_SAVE_OLD, TBE_SAVE_NEW),
        (u"setRemoved（keySet）", TBE_SETREMOVED_OLD, TBE_SETREMOVED_NEW),
        (u"import HashMap/Map", TBE_IMPORT_OLD, TBE_IMPORT_NEW),
    ]),
    (JAVA + r"\TerminalBlock.java", [
        (u"待选注释", TB_PENDING_OLD, TB_PENDING_NEW),
        (u"银线轴分支", TB_BRANCH_OLD, TB_BRANCH_NEW),
        (u"连接处理器带上速率", TB_HANDLER_OLD, TB_HANDLER_NEW),
        (u"addConnection 传速率", TB_ADD_OLD, TB_ADD_NEW),
    ]),
    (JAVA + r"\client\TerminalRenderer.java", [
        (u"银白色常量", TR_COLOR_OLD, TR_COLOR_NEW),
        (u"线径注释", TR_WIRE_RADIUS_OLD, TR_WIRE_RADIUS_NEW),
        (u"render 改调 renderFeWires", TR_RENDER_OLD, TR_RENDER_NEW),
        (u"新增 renderFeWires", TR_NEWMETHOD_OLD, TR_NEWMETHOD_NEW),
        (u"import Map", TR_IMPORT_OLD, TR_IMPORT_NEW),
    ]),
]


def read(p):
    return io.open(p, encoding="utf-8", newline=u"").read()


def detect_nl(text):
    return u"\r\n" if text.count(u"\r\n") > 0 else u"\n"


def apply(notes, fails):
    # ★ 先**全部验一遍**锚点：有一条对不上就一个字节都不写（别留半成品，§4.77 同族）
    for rel, edits in EDITS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            fails.append(u"缺文件：%s" % rel)
            continue
        text = read(path)
        nl = detect_nl(text)
        for what, old, new in edits:
            o = old.replace(u"\n", nl)
            cnt = text.count(o)
            if cnt != 1:
                fails.append(u"%s / %s：锚点命中 %d 次（要正好 1 次）" % (rel, what, cnt))
    if fails:
        fails.insert(0, u"锚点没全对上 ⇒ **一个字节都没写**")
        return

    for rel, edits in EDITS:
        path = os.path.join(ROOT, rel)
        text = read(path)
        nl = detect_nl(text)
        for what, old, new in edits:
            o = old.replace(u"\n", nl)
            n = new.replace(u"\n", nl)
            cnt = text.count(o)
            if cnt != 1:
                fails.append(u"%s / %s：锚点命中 %d 次（要正好 1 次）—— 停手" % (rel, what, cnt))
                continue
            text = text.replace(o, n, 1)
            notes.append(u"%s / %s" % (os.path.basename(rel), what))
        io.open(path, "w", encoding="utf-8", newline=u"").write(text)

def proof(notes, fails):
    """反推证明：把改完的盘上文件按 new -> old 反向替换 ⇒ 必须与改前件**逐字节相同**。"""
    for rel, edits in EDITS:
        cur = read(os.path.join(ROOT, rel))
        pre_path = os.path.join(BK, rel)
        if not os.path.exists(pre_path):
            fails.append(u"改前件不在：%s" % rel)
            continue
        pre = read(pre_path)
        nl = detect_nl(cur)
        back = cur
        for what, old, new in edits:
            o = old.replace(u"\n", nl)
            n = new.replace(u"\n", nl)
            if back.count(n) < 1:
                fails.append(u"%s / %s：反推时找不到新片段" % (rel, what))
                continue
            back = back.replace(n, o, 1)
        if back == pre:
            notes.append(u"%s：反推后与改前件**逐字节相同**" % os.path.basename(rel))
        else:
            fails.append(u"%s：反推后与改前件**不同**（差 %d 字节）"
                         % (os.path.basename(rel), abs(len(back) - len(pre))))
            for i in range(min(len(back), len(pre))):
                if back[i] != pre[i]:
                    fails.append(u"    第一处差异在第 %d 字节：改前 %r / 反推 %r"
                                 % (i, pre[max(0, i - 40):i + 40], back[max(0, i - 40):i + 40]))
                    break


def main(argv):
    notes, fails = [], []
    if u"--proof" in argv:
        proof(notes, fails)
        print(u"\n".join(u"  [OK] " + n for n in notes))
        print(u"失败项 = %d" % len(fails))
        for f in fails:
            print(u"  !! " + f)
        return 1 if fails else 0

    apply(notes, fails)
    print(u"\n".join(u"  [改] " + n for n in notes))
    print(u"改了 %d 处" % len(notes))
    print(u"失败项 = %d" % len(fails))
    for f in fails:
        print(u"  !! " + f)
    return 1 if fails else 0


if __name__ == u"__main__":
    sys.exit(main(sys.argv[1:]))
