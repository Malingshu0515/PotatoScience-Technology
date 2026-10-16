package com.potatost.mod;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.player.Player;
import com.potatost.mod.ModParticles;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * 黑洞（0.14 ZF169，手持式引力装置的大招）。
 *
 * <p><b>用户原话</b>：「储能8mFE 副手放一个方块 长按右键开始蓄力 25s后召唤出一个黑洞
 * 把3x3区块内所有副手方块 全部吸引到黑洞的位置（单次最多1200个方块）单次消耗全部8m电力并损坏
 * （黑洞还会吸引周围的生物 进入黑洞范围内会持续受到虚空伤害）黑洞特效竭尽你自己的知识储备
 * 尽你最大可能给我做的炫酷一点 不需要你省token」。</p>
 *
 * <h2>它一 tick 做什么</h2>
 * <ol>
 *   <li><b>吸方块</b>：3×3 区块里、与副手同种的方块，按离黑洞由近到远逐个"搬"过来 ——
 *       每 tick 有**预算**（{@link #BLOCKS_PER_TICK}），单次上限 {@link #maxBlocks()}（默认 1500，0.14 ZF186 起可配）。
 *       搬过来的方块**真的落在黑洞脚下**（堆成一圈塔），不是凭空消失。</li>
 *   <li><b>吸生物</b>：半径 {@link #PULL_RADIUS} 内的活物每 tick 被拉向奇点（越近越猛），
 *       进到 {@link #VOID_RADIUS} 以内的每 {@link #VOID_DAMAGE_INTERVAL} tick 吃一次<b>虚空伤害</b>
 *       （用的是原版的 {@code fellOutOfWorld} 伤害类型 —— 名字就叫"虚空"）。</li>
 *   <li><b>特效</b>（见 {@link #fx}）：三层吸积盘 + 内落流 + 事件视界光环 + 电弧 + 核心闪白，
 *       外加一套音效（生成 / 心跳 / 坍缩）。</li>
 * </ol>
 *
 * <p><b>为什么不做成实体</b>：实体要注册 + 存档 + 同步；这里只需要"服务端每 tick 算一次、
 * 客户端靠原版粒子看"，一个静态管理器就够（与 ZF153 的 {@code ShockwaveManager} 同一条路）。
 * ⚠ 代价：服务器重启后正在吸的黑洞会消失（本轮的取舍，写在这里不藏着）。</p>
 */
public final class BlackHoleManager {

    /** 单次最多搬多少方块 —— <b>0.14 ZF186 起由配置给</b>（{@code black_hole.max_blocks}，默认 1500）。 */
    public static int maxBlocks() {
        return PotatoSTConfig.blackHoleMaxBlocks();
    }

    /** 0.14 ZF172：吸方块的范围 = **5×5×5 区块的正方体** ⇒ 每轴 ±40 格（可在配置里改）。 */
    public static int half() {
        return PotatoSTConfig.blackHoleScanRadius();
    }

    /** 每轴位置数（默认 81）。 */
    public static int scanSide() {
        return half() * 2 + 1;
    }

    /** 正方体里的位置总数（默认 81³ = 531,441）。 */
    public static int scanVolume() {
        int side = scanSide();
        return side * side * side;
    }

    /**
     * 每 tick 每个黑洞最多发多少个**粒子包**（0.14 ZF173：炫技可以，TPS 不能换）。
     *
     * <p>所有特效都必须走 {@link #fx} 这个助手，它在超预算时**直接不发** ——
     * 于是"再炫"也有硬顶：一层层叠上去只会被裁掉最后几层，不会把服务器拖死。</p>
     */
    public static final int FX_BUDGET_PER_TICK = 320;
    /** 分幕：降临结束 / 前兆开始（总长 = {@link #lifetime()}）。 */
    public static final int FX_ARRIVE = 40;
    public static final int FX_OMEN = 330;
    /** 每 tick 最多**检查**多少个位置（带游标续扫；一轮 ≈ 130 tick ≈ 6.5 秒扫完 53 万）。 */
    public static final int EXAMINE_PER_TICK = 4096;
    /** 每 tick 的搬运预算（1200 个大约 2 秒搬完，不会一 tick 卡死）。 */
    public static final int BLOCKS_PER_TICK = 24;
    /** 引力半径（格）：3×3 区块的对角差不多 34，给到 48 让边界上的也吸得到。 */
    public static final double PULL_RADIUS = 48.0D;
    /** 事件视界半径：进这里就吃虚空伤害。 */
    public static final double VOID_RADIUS = 6.0D;
    /** 每多少 tick 吃一次虚空伤害。 */
    public static final int VOID_DAMAGE_INTERVAL = 10;

    /** 一次黑洞活多久 —— <b>0.14 ZF186 起由配置给</b>（{@code black_hole.lifetime_seconds}，默认 20 秒）。 */
    public static int lifetime() {
        return PotatoSTConfig.blackHoleLifetimeTicks();
    }

    /**
     * <b>0.14 ZF190：2 分钟硬上限。</b>用户原话：「一个黑洞存在超过2分钟也会销毁 并产生30power的爆炸」。
     *
     * <p>为什么需要它：坍缩模式靠装置的电费活着（50k FE/tick）⇒ 只要有人一边充一边放，
     * 它就能永远吃下去。这条硬上限是那个模式的"保险丝"，对**所有**模式生效
     * （普通模式的 {@code lifetime_seconds} 最大就是 120 秒 = 本上限，所以实际只有坍缩模式会撞到它）。</p>
     */
    public static final int HARD_CAP_TICKS = 2 * 60 * 20;
    /** 撞上硬上限那一记爆炸的威力（用户给的 30；对照：原版 TNT 是 4）。 */
    public static final float HARD_CAP_EXPLOSION_POWER = 30.0F;
    /**
     * 坍缩模式的强度/伤害**随时间递增**的斜率（用户原话「吸引时间越长吸引强度越高伤害也越高」）：
     * 倍率 = 1 + age × 本值 ⇒ 每 400 tick（20 秒）翻一倍，2 分钟时约 7 倍。
     */
    public static final double RAMP_PER_TICK = 1.0D / 400.0D;

    /** 坍缩模式这一刻的强度/伤害倍率（别的模式恒为 1）。 */
    public static double ramp(Hole hole) {
        return hole.mode == GravityDeviceItem.MODE_COLLAPSE ? 1.0D + hole.age * RAMP_PER_TICK : 1.0D;
    }

    /** 模式 2 同时在天上飞的下落方块上限（防实体爆炸）。 */
    public static final int MAX_FLYING = 48;

    /**
     * 坍缩模式（0.14 ZF194）：下落方块进到这个半径以内就算"到中心了" ⇒ **清除**（不掉落、不变回方块）。
     * 用户原话：「吸取到黑洞中心位置再清除」。
     */
    public static final double CLEAR_RADIUS = 2.5D;

    // ============================================================
    //  0.14 ZF196：坍缩模式"看得见地拆"
    //  用户原话：「没有效果啊 要像爆炸那样的 黑洞旁边的方块明显被破坏」
    // ============================================================
    /** 近场"拆除"的起始半径（格）：黑洞一落地就开始拆它旁边这一圈。 */
    public static final double DEMOLISH_START_RADIUS = 3.0D;
    /** 拆除半径的上限（格）：越吸越大，最大到这儿（不会再涨）。 */
    public static final double DEMOLISH_MAX_RADIUS = 24.0D;
    /** 拆除半径随年龄增长（格/tick）：0.08 ⇒ 每秒约 1.6 格，13 秒左右长到上限。 */
    public static final double DEMOLISH_GROWTH_PER_TICK = 0.08D;
    /**
     * 每 tick 给"近场拆除"多少次取样。
     *
     * <p>取样的半径分布用 {@code U(0, R)}（**不是**体积均匀）⇒ 体密度 ∝ 1/r²，
     * 于是"**先从紧挨着的那一圈开始拆**"，正好对上用户的「旁边的方块明显被破坏」。</p>
     */
    public static final int DEMOLISH_SAMPLES = 2048;

    /** 纯函数版：坍缩模式在第 {@code age} tick 的拆除半径（探针/门好直接验）。 */
    public static double demolishRadiusAt(int age) {
        return Math.min(DEMOLISH_MAX_RADIUS, DEMOLISH_START_RADIUS + age * DEMOLISH_GROWTH_PER_TICK);
    }

    /**
     * 这个黑洞这一刻的拆除半径：随年龄涨，但**不超过配置的扫描半径**
     * （{@code black_hole.scan_radius_blocks}）—— 配置说"只吃 8 格"，那就只吃 8 格。
     */
    public static double collapseRadius(Hole hole) {
        return Math.min(demolishRadiusAt(hole.age), (double) PotatoSTConfig.blackHoleScanRadius());
    }
    /**
     * 黑洞脚下的**禁采区半径**（0.14 ZF170c）：这一圈里的同种方块一律不再吸。
     *
     * <p>为什么必须有它：码好的方块和要吸的方块**是同一种**，而它们就在扫描范围内 ⇒
     * 黑洞会把自己刚码的又吸一遍（数字狂涨、地上什么都看不到）。半径 12 够盖住
     * {@code placeAt} 的金螺旋（1500 个的螺旋半径约 sqrt(500) ≈ 22 … 所以还要看 {@link #maxBlocks()}
     * 的量级；12 是"看得见的那一小堆"，外面那些本来也还在原地，不会被反复搬）。</p>
     */
    public static final int PILE_GUARD = 12;
    /** 奇点本身有多"重"（越小越猛）。 */
    private static final double CORE = 2.0D;

    private static final List<Hole> HOLES = new ArrayList<>();

    private BlackHoleManager() {
    }

    /** 一个正在吸的黑洞。 */
    private static final class Hole {
        final ServerLevel level;
        final Vec3 center;
        final Block block;
        final Player owner;
        /** 0 = 吞噬搬运，1 = 引力牵引（下落方块飞过去，绝不消失），2 = 坍缩模式-危险。见 GravityDeviceItem。 */
        final int mode;
        /**
         * 0.14 ZF190：坍缩模式的**电源** —— 召唤出它的那件引力装置（每 tick 扣 50k FE）。
         * 别的模式用不上（普通模式是"一次性扣 8M"）。重启之后由 {@link #resolvePowerStack} 重新找回来。
         */
        ItemStack powerStack;
        int age;
        int pulled;
        int placed;
        /** 落点不够、改成**掉落物**的数量（用户 ZF170b：「放不下的变成掉落物」）。 */
        int dropped;
        double spin;
        /** 0.14 ZF172：这一轮扫到 81³ 里的第几个（每 tick 续着扫，不许每 tick 从头全扫）。 */
        int cursor;

        Hole(ServerLevel level, Vec3 center, Block block, Player owner) {
            this(level, center, block, owner, GravityDeviceItem.MODE_SWALLOW, null);
        }

        Hole(ServerLevel level, Vec3 center, Block block, Player owner, int mode) {
            this(level, center, block, owner, mode, null);
        }

        Hole(ServerLevel level, Vec3 center, Block block, Player owner, int mode, ItemStack powerStack) {
            this.level = level;
            this.center = center;
            this.block = block;
            this.owner = owner;
            this.mode = mode;
            this.powerStack = powerStack;
        }
    }

    /** 召唤一个黑洞（由 {@link GravityDeviceItem} 在开火时调；不带电源，给老调用方与探针用）。 */
    public static void spawn(ServerLevel level, Vec3 center, Block block, Player owner, int mode) {
        spawn(level, center, block, owner, mode, null);
    }

    /**
     * 召唤一个黑洞（由 {@link GravityDeviceItem} 在开火时调）。
     *
     * @param powerStack 坍缩模式的"电源"：召唤它的那件装置（普通模式传 null）
     */
    public static void spawn(ServerLevel level, Vec3 center, Block block, Player owner, int mode,
                             ItemStack powerStack) {
        Hole hole = new Hole(level, center, block, owner, mode, powerStack);
        HOLES.add(hole);
        saveInto(level);   // 0.14 ZF169b：生成即存档（重启也还在）
        level.playSound(null, center.x, center.y, center.z, SoundEvents.END_PORTAL_SPAWN,
                SoundSource.PLAYERS, 4.0F, 0.6F);
        level.playSound(null, center.x, center.y, center.z, SoundEvents.PORTAL_TRIGGER,
                SoundSource.PLAYERS, 3.0F, 0.5F);
        // 开局一记闪白 + 一圈冲击环：让"它出现了"这件事在地图上看得见
        level.sendParticles(ParticleTypes.FLASH, center.x, center.y + 1.0D, center.z, 6, 0, 0, 0, 0);
        for (int i = 0; i < 180; i++) {
            double a = i * Math.PI / 90.0D;
            level.sendParticles(ParticleTypes.SONIC_BOOM, center.x, center.y, center.z, 1,
                    Math.cos(a) * 3.0D, 0.0D, Math.sin(a) * 3.0D, 0.0D);
        }
    }

    public static int activeCount() {
        return HOLES.size();
    }

    public static void clear() {
        // 0.14 ZF196：清场时把它那一带"还在飞的下落方块"一并收掉 —— 这些方块是**这次试验**造出来的，
        //   探针里服务端不 tick 它们不会自己走，留着会一直占着 MAX_FLYING 的上限，
        //   下一次试验就被上一轮的残留堵死（本轮真踩过：48/48 占满 ⇒ 后面几条全假红）。
        for (Hole hole : HOLES) {
            AABB box = new AABB(hole.center, hole.center).inflate(PULL_RADIUS);
            for (FallingBlockEntity fb : hole.level.getEntitiesOfClass(FallingBlockEntity.class, box)) {
                fb.discard();
            }
        }
        HOLES.clear();
        demolishedTotal = 0;   // 诊断计数跟着清场一起归零（见 demolishedTotal()）
    }

    /** 每 tick 由 {@code PotatoST} 调一次。 */
    public static void tick() {
        if (HOLES.isEmpty()) {
            return;
        }
        Iterator<Hole> it = HOLES.iterator();
        while (it.hasNext()) {
            Hole hole = it.next();
            hole.age++;
            hole.spin += 0.35D;
            fxSpent = 0;   // 0.14 ZF173：每 tick 重新给特效记账
            try {
                // ① 0.14 ZF190：坍缩模式先交这一 tick 的电费（50k FE）。交不出来 ⇒ 黑洞当场消失
                //    （用户原话「每存在1tick消耗50kFE没有电力时候黑洞消失」）
                if (hole.mode == GravityDeviceItem.MODE_COLLAPSE && !payCollapsePower(hole)) {
                    it.remove();        // ⚠ 先摘再播报：collapse() 里会 saveInto（见下面 ③ 的注释）
                    collapse(hole);
                    continue;
                }
                pullBlocks(hole);
                consumeFalling(hole);   // 0.14 ZF194：把在飞的下落方块继续拉向奇点、到中心清除
                pullEntities(hole);
                fx(hole);
                if (hole.age % 20 == 0) {
                    // "心跳"：音量随年龄涨，最后几下最重。
                    // ⚠ ZF190：坍缩模式能活到 2400 tick（寿命 400）⇒ t 必须夹住，
                    //   否则音量被算成 7 倍、低频轰鸣 10 倍，耳朵先崩。
                    float t = Math.min(2.0F, (float) hole.age / lifetime());
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 1.2F + t, 0.5F + t * 0.4F);
                    // 低频"轰鸣"：拿爆炸声压低调当鼓点用（只出声、不伤方块）
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS,
                            0.6F + 2.4F * t, 0.4F + 0.3F * t);
                }
                if (hole.age % 60 == 0) {
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS, 2.0F, 0.6F);
                }
                // 0.14 ZF173 前兆期：鼓点加密 + 音调发冷（"要坍缩了"）
                if (hole.age >= FX_OMEN && hole.age % 10 == 0) {
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), SoundSource.PLAYERS,
                            2.2F, 0.5F + (hole.age - FX_OMEN) * 0.004F);
                }
                if (hole.age % 100 == 0) {
                    saveInto(hole.level);   // 边吸边存：崩服也只丢最后 5 秒的进度
                }
            } catch (Throwable t) {
                // 一个黑洞出问题不许拖垮服务器：记账 + 丢掉它
                System.out.println("[PotatoST] 黑洞 tick 出错，已丢弃：" + t);
                it.remove();
                continue;
            }
            // ② 0.14 ZF190：**2 分钟硬上限** ⇒ 销毁 + 30 威力爆炸（用户原话见 HARD_CAP_TICKS）
            if (hole.age >= HARD_CAP_TICKS) {
                it.remove();    // ⚠ 先摘再炸：boom() 里也会 saveInto（同 ③）
                boom(hole);
                continue;
            }
            // ③ 普通模式按配置寿命自然坍缩；坍缩模式**不**看配置寿命（它由电费 + 硬上限说了算）
            //    ⚠⚠ 顺序教训（0.14 ZF190 顺手修的）：`collapse()` 里会 `saveInto()`，
            //    旧代码是「先 collapse 再 it.remove()」⇒ 刚结束的黑洞被**写回存档**，
            //    每次重启都会"复活一次再坍缩"。现在一律**先摘、后播报**。
            if (hole.mode != GravityDeviceItem.MODE_COLLAPSE && hole.age >= lifetime()) {
                it.remove();
                collapse(hole);
            }
        }
    }

    // ============================================================
    //  吸方块
    // ============================================================
    private static void pullBlocks(Hole hole) {
        // ⚠⚠ 0.14 ZF170b：上限判据原来只看 `placed` ⇒ 模式 2 那条路 `placed` 永远不涨，
        //   上限**彻底失效**（用户实测一次吸了 **16992** 块，世界被啃掉一大片）。
        //   现在改成看 **pulled**（搬走的都算），上限一到立刻停手。
        //   0.14 ZF186：这个上限本身改成配置项（默认还是 1500）。
        if (hole.pulled >= maxBlocks()) {
            return;
        }
        ServerLevel level = hole.level;
        BlockPos centerPos = BlockPos.containing(hole.center);
        // ── 0.14 ZF196：坍缩模式**完全换一套吃法**（近处优先的球内取样，见 collapseEat）──
        //    为什么必须换：原来那条**线性游标**从扫描区的一角（-40,-40,-40）往后走，
        //    要 ~65 tick 才轮到黑洞身边的东西；而默认装置（8M）只够撑 80 tick ⇒
        //    用户实测「**没有效果**」——大部分时间都花在翻远处的地皮上了。
        //    现在坍缩模式不走游标，直接"从身边一圈圈往外拆"，落地即见效。
        if (hole.mode == GravityDeviceItem.MODE_COLLAPSE) {
            collapseEat(hole);
            return;
        }
        // ── 0.14 ZF172：范围 = 5×5×5 区块的正方体（±40 格，81³ 个位置）──
        //    0.14 ZF186：半径搬进配置（{@code black_hole.scan_radius_blocks}，默认 40）。
        //    用**线性游标**扫：每 tick 只看 EXAMINE_PER_TICK 个位置，扫完一轮从头再来。
        //    这样"处处没有目标方块"时也只花固定的那点开销（否则 53 万个位置每 tick 全扫 = 服务器跪）。
        //    ⚠ 半径是**现场取**的：配置改小之后旧游标可能"越界" ⇒ 用 `cursor % volume` 兜住。
        int budget = BLOCKS_PER_TICK;
        int examined = 0;
        final int volume = scanVolume();
        final int side = scanSide();
        final int half = half();
        while (examined < EXAMINE_PER_TICK && budget > 0) {
            int idx = hole.cursor % volume;
            hole.cursor = (idx + 1) % volume;
            examined++;
            // 线性下标 → (dx, dy, dz)，每个轴都是 -half..+half
            int dx = idx % side - half;
            int dz = (idx / side) % side - half;
            int dy = idx / (side * side) - half;
            // 黑洞脚下那一圈是"禁采区"：不许把它自己码好的方块又吸一遍
            // （否则数字狂涨、地上什么都看不到 —— ZF170c 用户实测抓到的）
            if (Math.abs(dx) <= PILE_GUARD && Math.abs(dz) <= PILE_GUARD
                    && dy >= -8 && dy <= 30) {
                continue;
            }
            BlockPos p = centerPos.offset(dx, dy, dz);
            if (!level.isLoaded(p)) {
                continue;
            }
            BlockState state = level.getBlockState(p);
            if (!state.is(hole.block)) {
                continue;
            }
            // ① **先放后拆**（放不下就绝不拆）—— 修"吸走就消失"；
            // ② 落点也不够时 ⇒ **掉成掉落物**（用户点名要的兜底），仍然不消失。
            if (placeAt(hole, p, hole.block)) {
                level.removeBlock(p, false);
                hole.pulled++;
            } else {
                level.removeBlock(p, false);
                Block.popResource(level, centerPos, new ItemStack(hole.block));
                hole.pulled++;
                hole.dropped++;
            }
            // 路上撒一串粒子，让"它被拽走了"看得见
            Vec3 from = Vec3.atCenterOf(p);
            for (int s = 0; s < 8; s++) {
                double k = s / 8.0D;
                level.sendParticles(ParticleTypes.REVERSE_PORTAL,
                        Mth.lerp(k, from.x, hole.center.x),
                        Mth.lerp(k, from.y, hole.center.y),
                        Mth.lerp(k, from.z, hole.center.z), 1, 0.05D, 0.05D, 0.05D, 0.02D);
            }
            budget--;
        }
    }

    /**
     * 坍缩模式（0.14 ZF196）：**从身边一圈圈往外吃** —— 用户原话
     * 「没有效果啊 要像爆炸那样的 黑洞旁边的方块明显被破坏」。
     *
     * <p>两种吃法（都是"看不见就白干"的教训换来的）：</p>
     * <ul>
     *   <li><b>暴露在空气里的</b>（至少一面贴空气）⇒ 变成下落方块朝奇点飞（ZF194 那套，看得见地飞，
     *       到中心清除）；</li>
     *   <li><b>埋着的</b>（六面都堵）⇒ **就地拆除**：走原版"方块破坏"事件 2001（碎裂粒子 + 音效，
     *       爆炸拆方块就是这一个事件），因为它变成下落方块也**飞不出来**、卡在方块里更像"没效果"。</li>
     * </ul>
     *
     * <p>取样半径用 {@code U(0, R)}（体密度 ∝ 1/r²）⇒ 先拆紧挨着的那一圈、再往外扩；
     * R 随年龄涨（见 {@link #collapseRadius}）。每 tick 拆最多 {@link #BLOCKS_PER_TICK} 块、
     * 取样 {@link #DEMOLISH_SAMPLES} 次 —— 开销与以前那条线性扫（4096 次位置检查）同级。</p>
     */
    private static void collapseEat(Hole hole) {
        ServerLevel level = hole.level;
        BlockPos centerPos = BlockPos.containing(hole.center);
        double radius = collapseRadius(hole);
        // 天上还有几个在飞 —— **一次查好**，循环里只减计数（别逐块查实体）
        AABB flyBox = new AABB(hole.center, hole.center).inflate(PULL_RADIUS);
        int flyingLeft = Math.max(0, MAX_FLYING
                - level.getEntitiesOfClass(FallingBlockEntity.class, flyBox).size());
        int done = 0;
        for (int i = 0; i < DEMOLISH_SAMPLES && done < BLOCKS_PER_TICK && hole.pulled < maxBlocks(); i++) {
            double u = level.getRandom().nextDouble();
            double rr = radius * u;                       // ⚠ U(0,R)：近处优先，不是体积均匀
            double z = 2.0D * level.getRandom().nextDouble() - 1.0D;
            double phi = level.getRandom().nextDouble() * Math.PI * 2.0D;
            double s = Math.sqrt(Math.max(0.0D, 1.0D - z * z));
            int dx = (int) Math.round(rr * s * Math.cos(phi));
            int dy = (int) Math.round(rr * z);
            int dz = (int) Math.round(rr * s * Math.sin(phi));
            BlockPos p = centerPos.offset(dx, dy, dz);
            if (!level.isLoaded(p)) {
                continue;
            }
            BlockState state = level.getBlockState(p);
            if (!eatable(state)) {
                continue;
            }
            if (!exposed(level, p)) {
                demolish(level, hole, p, state);          // 埋着的：原地拆（像爆炸那样碎裂）
                done++;
            } else {
                // 露着的：飞进奇点，到中心清除。⚠ **天上飞满了也照样拆**（就地）——
                //   "看见了却不动手"是最糟的一种（探针里 48 个残留把上限占满时就是这样：
                //   黑洞明明盯着脚边的方块却什么都不干）。
                boolean flew = flyingLeft > 0 && launchFalling(hole, p, state);
                if (flew) {
                    hole.pulled++;
                    flyingLeft--;
                } else {
                    demolish(level, hole, p, state);
                }
                done++;
            }
        }
    }

    /**
     * 坍缩模式「无差别」的**边界**（0.14 ZF190）：空气与流体不算方块；**不可破坏**的
     * （基岩 / 屏障 / 命令方块 / 末地传送门框架…，{@code defaultDestroyTime() < 0}）一律不动。
     *
     * <p>「无差别」不等于把世界的地基啃穿 —— 把基岩吸走会让存档直接坏掉，
     * 这条边界写在这里，也是这道"危险模式"唯一的一条自我约束。</p>
     */
    private static boolean eatable(BlockState state) {
        return !state.isAir() && state.getFluidState().isEmpty()
                && state.getBlock().defaultDestroyTime() >= 0.0F;
    }

    // ============================================================
    //  0.14 ZF196：近场拆除（像爆炸那样"看得见地破坏"）
    // ============================================================

    /**
     * 原地拆掉一块：**走原版的"方块破坏"事件（2001）** —— 客户端会放该方块的碎裂粒子 + 破坏音效，
     * 爆炸拆方块用的就是这一个事件 ⇒ 「像爆炸那样」就是这么来的。
     * ⚠ 不掉落物品（坍缩模式的掉落物本来就会被销毁，见 {@code pullEntities}）。
     */
    private static void demolish(ServerLevel level, Hole hole, BlockPos p, BlockState state) {
        level.removeBlock(p, false);
        level.levelEvent(net.minecraft.world.level.block.LevelEvent.PARTICLES_DESTROY_BLOCK, p,
                Block.getId(state));
        hole.pulled++;
        demolishedTotal++;
    }

    /**
     * 诊断计数（0.14 ZF196）：累计"原地拆除"了多少块。
     *
     * <p>为什么要有它：从外面**看不出来**某一块是被"拆"的还是"飞"的（弹坑一开，原来的"埋着"
     * 就变成"露着"了）⇒ 探针/门只能用这个计数把两条路分开量。生产逻辑**不依赖**它，
     * {@link #clear()}（探针用的清场口）会把它归零。</p>
     */
    private static int demolishedTotal;

    /** 见 {@link #demolishedTotal} 的说明（只读，给探针/门用）。 */
    public static int demolishedTotal() {
        return demolishedTotal;
    }

    /** 这块方块**有没有一面贴着空气**（能不能"飞"出来）；六面都堵着的就是埋着的。 */
    private static boolean exposed(ServerLevel level, BlockPos p) {
        for (Direction d : Direction.values()) {
            if (level.getBlockState(p.relative(d)).isAir()) {
                return true;
            }
        }
        return false;
    }

    /**
     * 把方块码在黑洞周围（只往"可替换"的地方放，不砸坏别的东西）。
     *
     * <p><b>⚠ 0.14 ZF170 改成 boolean 并**不再自己拆原件****：旧版是"先拆、再调它"，
     * 而它放不下时直接 return ⇒ 方块拆了却没落地 = 用户看到的"吸过来就消失"。
     * 现在它只负责"放"，放成了返回 true，由调用方再拆原位 —— 顺序反过来了。</b></p>
     *
     * <p>0.14 ZF190：多一个参数 {@code block} —— 坍缩模式要放**原位那一种**方块（见 pullBlocks）。</p>
     */
    private static boolean placeAt(Hole hole, BlockPos from, Block block) {
        if (hole.placed >= maxBlocks()) {
            return false;
        }
        ServerLevel level = hole.level;
        BlockPos centerPos = BlockPos.containing(hole.center);
        // 模式 1：脚下金螺旋小丘；模式 2：往**黑洞正上方**码成一根塔（两种模式看着不一样，机制都安全）
        int n = hole.placed;
        double a = n * 2.399963D;
        int radius = hole.mode == GravityDeviceItem.MODE_TOW ? 1 : (int) Math.sqrt(n / 3.0D);
        int layer = hole.mode == GravityDeviceItem.MODE_TOW ? (n / 2) : (n % 3);
        BlockPos target = centerPos.offset((int) Math.round(Math.cos(a) * radius),
                hole.mode == GravityDeviceItem.MODE_TOW ? (1 + layer) : (-1 - layer),
                (int) Math.round(Math.sin(a) * radius));
        // 目标就是原位 ⇒ 什么都别做（否则"放"完再"拆"等于把这一块删了）
        if (target.equals(from)) {
            return false;
        }
        if (!level.isLoaded(target)) {
            return false;
        }
        BlockState there = level.getBlockState(target);
        if (!there.canBeReplaced()) {
            // 放不下 ⇒ 返回 false，调用方**这一块原地不动**（宁可不吸也不丢）
            return false;
        }
        level.setBlockAndUpdate(target, block.defaultBlockState());
        hole.placed++;
        level.sendParticles(ParticleTypes.SMOKE, target.getX() + 0.5D, target.getY() + 1.0D,
                target.getZ() + 0.5D, 3, 0.2D, 0.1D, 0.2D, 0.01D);
        return true;
    }

    /**
     * 坍缩模式（0.14 ZF194）：把方块变成**下落方块**（{@code FallingBlockEntity}）朝奇点飞。
     *
     * <p><b>用户原话</b>：「看不出来坍缩模式在吸取周围方块（做成把方块变成下落形式的
     * 吸取到黑洞中心位置再清除）」—— 这一段其实是 0.14 ZF170 写下来又一直没接上的旧代码
     * （{@code launchFalling} 之前是**死代码**：模式 1「引力牵引」名义上用它，实际走的是码放），
     * 本轮把它**接给坍缩模式**并按"到中心清除"改写。</p>
     *
     * <p>⚠ 天上飞的数量上限由**调用方**一次算好（{@link #pullBlocks} 的 {@code flyingLeft}），
     * 这里不再自己查实体 —— 一 tick 最多搬 {@code BLOCKS_PER_TICK} 块，逐块查实体纯属浪费。</p>
     *
     * @return true = 这一块已经变成下落方块（原位置已清空）；false = 放不出去（这一块原地不动）
     */
    private static boolean launchFalling(Hole hole, BlockPos pos, BlockState state) {
        ServerLevel level = hole.level;
        if (!level.isLoaded(pos)) {
            return false;
        }
        level.removeBlock(pos, false);
        FallingBlockEntity falling = FallingBlockEntity.fall(level, pos, state);
        // 起飞这一下朝奇点给一次速度；之后每 tick 由 {@link #consumeFalling} 续着校正（重力仍在，
        // 万一黑洞半路没了，这些方块会**正常落地变回方块**，不会永远飘着）。
        Vec3 dir = hole.center.subtract(Vec3.atCenterOf(pos));
        if (dir.lengthSqr() > 1.0E-6D) {
            falling.setDeltaMovement(dir.normalize().scale(flySpeed(dir.length())));
        }
        falling.hurtMarked = true;
        falling.setStartPos(pos);
        level.addFreshEntity(falling);
        // 起飞那一瞬撒一圈光点
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, pos.getX() + 0.5D, pos.getY() + 0.5D,
                pos.getZ() + 0.5D, 10, 0.3D, 0.3D, 0.3D, 0.05D);
        return true;
    }

    /** 下落方块朝奇点飞的速度：远一点就快一点（看起来像"被吸住加速"）。 */
    private static double flySpeed(double dist) {
        return Math.min(1.6D, 0.45D + dist * 0.02D);
    }

    /**
     * 坍缩模式（0.14 ZF194）：**把还在飞的那些下落方块继续拉向奇点**，到了
     * {@link #CLEAR_RADIUS} 以内就**清除**（不掉落、不落地）。
     *
     * <p>这就是用户要的「吸取到黑洞中心位置再清除」。⚠ 只对坍缩模式生效：
     * 模式 1「引力牵引」的语义是"**绝不消失**"（落地变回方块），将来真要接上下落方块也不能在这儿清掉。</p>
     */
    private static void consumeFalling(Hole hole) {
        if (hole.mode != GravityDeviceItem.MODE_COLLAPSE) {
            return;
        }
        ServerLevel level = hole.level;
        AABB box = new AABB(hole.center, hole.center).inflate(PULL_RADIUS);
        for (FallingBlockEntity fb : level.getEntitiesOfClass(FallingBlockEntity.class, box)) {
            Vec3 dir = hole.center.subtract(fb.position());
            double dist = dir.length();
            if (dist <= CLEAR_RADIUS) {
                // 到中心 ⇒ 清除（不掉落、不变成方块）：一记"被吞掉"的闷响 + 一团墨
                level.sendParticles(ParticleTypes.SQUID_INK, fb.getX(), fb.getY() + 0.2D, fb.getZ(),
                        10, 0.3D, 0.3D, 0.3D, 0.02D);
                fx(level, ParticleTypes.FLASH, hole.center.x, hole.center.y, hole.center.z,
                        1, 0.0D, 0.0D, 0.0D, 0.0D);
                fb.discard();
                continue;
            }
            if (dir.lengthSqr() > 1.0E-6D) {
                fb.setDeltaMovement(dir.normalize().scale(flySpeed(dist)));
                fb.hurtMarked = true;
            }
            fb.fallDistance = 0.0F;
            // 一路冒金星（隔 tick 撒，省包；走 fx() 一起受每 tick 的预算管）
            if (hole.age % 2 == 0) {
                fx(level, ParticleTypes.SCULK_SOUL, fb.getX(), fb.getY() + 0.3D, fb.getZ(),
                        1, 0.05D, 0.05D, 0.05D, 0.01D);
            }
        }
    }

    // ============================================================
    //  吸生物 + 虚空伤害
    // ============================================================
    private static void pullEntities(Hole hole) {
        // 0.14 ZF186：两个开关**互相独立**（探针 G2 就是冲着这条来的）——
        //   ①「吸引生物」只管拉不拉；②「视界虚空伤害」只管掉不掉血。
        //   ⚠ 曾经把 ② 写在 ① 的 early-return 后面 ⇒ 关掉"吸引生物"会**顺手把伤害也关掉**，
        //     那是错的（用户要的是两个独立配置项）。
        final boolean pull = PotatoSTConfig.blackHolePullsEntities();
        final boolean hurt = PotatoSTConfig.blackHoleVoidDamage();
        final boolean collapse = hole.mode == GravityDeviceItem.MODE_COLLAPSE;
        if (!pull && !hurt) {
            return;
        }
        ServerLevel level = hole.level;
        AABB box = new AABB(hole.center, hole.center).inflate(PULL_RADIUS);
        // ── 0.14 ZF190 坍缩模式：**吸引到的掉落物会销毁**（用户原话）──
        //    挂在「吸引生物」这个总开关下面：把交互整个关掉的人，掉落物也不该被吃。
        if (collapse && pull) {
            for (net.minecraft.world.entity.item.ItemEntity item
                    : level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class, box)) {
                level.sendParticles(ParticleTypes.SCULK_SOUL, item.getX(), item.getY() + 0.2D,
                        item.getZ(), 6, 0.2D, 0.2D, 0.2D, 0.02D);
                item.discard();   // 不掉落、不留痕
            }
        }
        // 0.14 ZF190：坍缩模式的强度/伤害随年龄涨（别的模式恒 1.0，行为与以前一模一样）
        final double ramp = ramp(hole);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box)) {
            // ⚠ 0.14 ZF170c（用户要的）：黑洞**也吸玩家**（包括召唤者自己）；
            //   **穿着任意一件振金装备就免疫**（吸不动 + 不掉血，只留视觉）。
            if (e instanceof Player p && wearsVibranium(p)) {
                level.sendParticles(ParticleTypes.ENCHANT, p.getX(), p.getY() + 1.0D, p.getZ(),
                        6, 0.4D, 0.6D, 0.4D, 0.02D);   // 免疫时身上泛一圈附魔光（看得见的"挡住了"）
                continue;
            }
            double dist = e.position().distanceTo(hole.center);
            if (pull) {
                // 0.14 ZF174：近处的**玩家**额外吃一层原版 DARKNESS —— 那是现成的"屏幕发暗"画效
                //   （配心跳音正合适），且完全不碰渲染管线。15 格内、每 20 tick 续一次。
                if (e instanceof Player dp && dist <= 15.0D && hole.age % 20 == 0) {
                    dp.addEffect(new net.minecraft.world.effect.MobEffectInstance(
                            net.minecraft.world.effect.MobEffects.DARKNESS, 60, 0, false, false, false));
                }
                Vec3 dir = hole.center.subtract(e.position());
                if (dir.lengthSqr() >= 1.0E-4D) {
                    // 越近越猛：1/(d/CORE + 1)；0.14 ZF190：再乘上"随着年龄涨"的倍率
                    double strength = 1.6D / (dist / CORE + 1.0D) * ramp;
                    Vec3 v = e.getDeltaMovement().add(dir.normalize().scale(strength));
                    // 切向那一分量：让生物绕着奇点转（不是直直掉进去）—— 视觉上好看得多
                    Vec3 tangent = new Vec3(-dir.z, 0.0D, dir.x).normalize().scale(strength * 0.45D);
                    e.setDeltaMovement(v.add(tangent));
                    e.hurtMarked = true;
                    e.fallDistance = 0.0F;
                }
            }
            if (hurt && dist <= VOID_RADIUS && hole.age % VOID_DAMAGE_INTERVAL == 0) {
                // 原版的"虚空"伤害类型；0.14 ZF190：伤害同样随年龄涨（用户「伤害也越高」）
                e.hurt(level.damageSources().fellOutOfWorld(), (float) (4.0D * ramp));
                level.sendParticles(ParticleTypes.SQUID_INK, e.getX(), e.getY() + 1.0D, e.getZ(),
                        12, 0.3D, 0.4D, 0.3D, 0.02D);
            }
        }
    }

    // ============================================================
    //  特效：三层吸积盘 + 内落流 + 视界光环 + 电弧 + 核心
    // ============================================================
    /** 一个黑洞当前这一 tick 已经发出去的包数（每 tick 开头清零，见 {@link #tick}）。 */
    private static int fxSpent;

    /**
     * 发一"包"粒子（唯一出口）：超预算直接丢。
     *
     * <p>{@code speed} 是**速度**不是"扩散" —— 给切向速度粒子就绕圈、给朝心速度就往里掉，
     * 这是"点阵"和"流体"的分界（旧版全靠 0 速度的静态点 ⇒ 看着像撒了一把亮片）。</p>
     */
    private static void fx(ServerLevel level, ParticleOptions type, double x, double y, double z,
                           int count, double dx, double dy, double dz, double speed) {
        if (fxSpent >= FX_BUDGET_PER_TICK) {
            return;
        }
        fxSpent++;
        level.sendParticles(type, x, y, z, count, dx, dy, dz, speed);
    }

    /** 一圈：给**切向**速度 ⇒ 粒子真的在转（不是一个个静止的点）。 */
    private static void ring(ServerLevel level, ParticleOptions type, double cx, double cy, double cz,
                             double radius, int count, double phase, double tilt, double spinSpeed) {
        for (int i = 0; i < count; i++) {
            double a = phase + i * (Math.PI * 2.0D / count);
            double x = cx + Math.cos(a) * radius;
            double z = cz + Math.sin(a) * radius;
            double y = cy + Math.sin(a) * radius * tilt;
            // 切向 = (-sin, 0, cos)；乘上 spinSpeed 就是"绕着奇点转"的速度
            fx(level, type, x, y, z, 1, -Math.sin(a) * spinSpeed, 0.0D, Math.cos(a) * spinSpeed,
                    spinSpeed);
        }
    }

    /** 一张盘：螺旋 + 倾角 + 切向速度（吸积盘就是靠这个"转"起来的）。 */
    private static void disk(ServerLevel level, ParticleOptions type, double cx, double cy, double cz,
                             double radius, int count, double phase, double tilt, double spinSpeed) {
        for (int i = 0; i < count; i++) {
            double a = phase + i * (Math.PI * 2.0D / count) + i * 0.12D;
            double r = radius * (0.75D + 0.25D * Math.sin(a * 3.0D + phase));
            double x = cx + Math.cos(a) * r;
            double z = cz + Math.sin(a) * r;
            double y = cy + Math.sin(a) * r * tilt;
            fx(level, type, x, y, z, 1, -Math.sin(a) * spinSpeed, 0.0D, Math.cos(a) * spinSpeed,
                    spinSpeed);
        }
    }

    /**
     * 特效主循环（0.14 ZF173 重写）：五幕、错峰、带速度、**有硬预算**。
     *
     * <p>跟旧版比：包数不一定更少，但**观感是流体**（切向速度）、层次分明（错峰），
     * 而且无论怎么叠都撞不破 {@link #FX_BUDGET_PER_TICK}。</p>
     */
    private static void fx(Hole hole) {
        ServerLevel level = hole.level;
        double cx = hole.center.x;
        double cy = hole.center.y + 0.6D;
        double cz = hole.center.z;
        int age = hole.age;
        boolean omen = age >= FX_OMEN;                      // 第③幕：前兆（转向反了）
        double dir = omen ? -1.0D : 1.0D;                    // 1 = 往里吸，-1 = 往外炸
        double spin = hole.spin * dir;

        // ── 第①幕：降临（0–40 tick）音爆环由小扩到大 + 闪白 + 尘土被吸起 ──
        if (age < FX_ARRIVE) {
            double k = age / (double) FX_ARRIVE;             // 0 → 1
            double shockR = 2.0D + 26.0D * k;
            ring(level, ParticleTypes.SONIC_BOOM, cx, cy, cz, shockR, 36, age * 0.4D, 0.0D, 0.0D);
            if (age % 6 == 0) {
                fx(level, ParticleTypes.FLASH, cx, cy, cz, 2, 0.4D, 0.4D, 0.4D, 0.0D);
            }
            for (int i = 0; i < 26; i++) {
                double a = i * (Math.PI * 2.0D / 26.0D) + age * 0.2D;
                double r = 1.0D + 22.0D * k;
                // 朝心速度 ⇒ 尘土"被吸起来"
                fx(level, ParticleTypes.CAMPFIRE_COSY_SMOKE, cx + Math.cos(a) * r, cy - 0.5D,
                        cz + Math.sin(a) * r, 1, -Math.cos(a) * 0.12D, 0.06D, -Math.sin(a) * 0.12D, 0.12D);
            }
        }

        // ── 事件视界**本体**（0.14 ZF174 自定义粒子）：一颗大黑盘，中间真的黑 ──
        //    它只在这里生成 ⇒ 客户端靠它反推黑洞位置（相机扭曲那点事，见 client/VoidLens）
        fx(level, ModParticles.VOID_CORE.get(), cx, cy, cz, 1, 0.0D, 0.0D, 0.0D, 0.0D);

        // ── 光子环：贴着急速旋转的亮环（每 tick、24 点、切向速度）── 黑洞的"招牌" ──
        ring(level, ModParticles.VOID_GLOW.get(), cx, cy, cz, 2.35D, 24, spin * 2.2D, 0.0D, 0.22D);

        // ── 事件视界暗盘（奇 tick）：中间要真的黑，边缘才亮 ──
        if (age % 2 == 1) {
            for (int i = 0; i < 30; i++) {
                double a = spin * 0.5D + i * (Math.PI * 2.0D / 30.0D);
                double r = 3.2D + 1.4D * Math.sin(a * 2.0D + age * 0.05D);
                fx(level, ParticleTypes.SQUID_INK, cx + Math.cos(a) * r, cy, cz + Math.sin(a) * r,
                        1, -Math.sin(a) * 0.1D, 0.0D, Math.cos(a) * 0.1D, 0.1D);
            }
            for (int i = 0; i < 18; i++) {
                double a = -spin * 0.9D + i * (Math.PI * 2.0D / 18.0D);
                fx(level, ParticleTypes.SCULK_SOUL, cx + Math.cos(a) * 2.0D, cy,
                        cz + Math.sin(a) * 2.0D, 1, -Math.sin(a) * 0.14D, 0.0D,
                        Math.cos(a) * 0.14D, 0.14D);
            }
        }

        // ── 三层反向吸积盘（偶 tick）：蓝焰 / 端杆 / 电弧，倾角各不相同 ──
        if (age % 2 == 0) {
            disk(level, ModParticles.VOID_GLOW.get(), cx, cy, cz, 4.5D, 26, spin * 0.8D, 0.22D, 0.18D);
            disk(level, ModParticles.VOID_GLOW.get(), cx, cy, cz, 6.5D, 30, -spin * 0.55D, -0.18D, 0.16D);
            disk(level, ParticleTypes.ELECTRIC_SPARK, cx, cy, cz, 8.5D, 32, spin * 0.35D, 0.30D, 0.12D);
        }

        // ── 内落粒子雨（每 tick，核心看点）：**朝心速度** ⇒ 真的往里掉 ──
        for (int i = 0; i < 12; i++) {
            double a = spin * 0.7D + i * (Math.PI * 2.0D / 12.0D);
            double r0 = 7.5D + (i % 4) * 1.5D;
            for (int s = 0; s < 4; s++) {
                double k = s / 4.0D;
                double r = r0 * (1.0D - 0.22D * k);
                double y = cy + Math.sin(a * 2.0D + k * 5.0D) * 1.6D * (1.0D - k);
                fx(level, ModParticles.VOID_STREAK.get(), cx + Math.cos(a) * r, y,
                        cz + Math.sin(a) * r, 1, -Math.cos(a) * 0.5D, -0.05D, -Math.sin(a) * 0.5D, 0.5D);
            }
        }

        // ── 引力透镜光弧（每 4 tick）：随时间收缩；前兆期急速收拢 ──
        if (age % 4 == 0) {
            double squeeze = omen
                    ? Math.max(2.6D, 10.0D - (age - FX_OMEN) * 0.28D)
                    : 10.0D - 4.0D * Math.sin(age * 0.05D);
            ring(level, ParticleTypes.END_ROD, cx, cy + 0.15D, cz, Math.max(2.6D, squeeze), 26,
                    spin * 0.25D, 0.0D, 0.05D);
            ring(level, ParticleTypes.DRAGON_BREATH, cx, cy - 0.15D, cz,
                    Math.max(2.6D, squeeze) * 0.8D, 20, -spin * 0.3D, 0.0D, 0.05D);
        }

        // ── 电弧（每 5 tick）：从奇点朝随机方向劈出去 ──
        if (age % 5 == 0) {
            for (int i = 0; i < 8; i++) {
                double a = (age * 0.37D + i * 0.9D) % (Math.PI * 2.0D);
                double up = Math.sin(age * 0.21D + i) * 0.6D;
                fx(level, ParticleTypes.ELECTRIC_SPARK, cx + Math.cos(a) * 1.2D, cy + up * 0.5D,
                        cz + Math.sin(a) * 1.2D, 1, Math.cos(a) * 0.9D, up, Math.sin(a) * 0.9D, 0.9D);
            }
        }

        // ── 核心：闪白（每 12 tick）+ 一层暗雾把"黑"压住 ──
        if (age % 12 == 0) {
            fx(level, ParticleTypes.FLASH, cx, cy, cz, 2, 0.35D, 0.35D, 0.35D, 0.0D);
        }
        fx(level, ParticleTypes.LARGE_SMOKE, cx, cy, cz, 4, 0.7D, 0.5D, 0.7D, 0.01D);

        // ── 前兆期的额外一记：音爆环 + 反向喷射（"要炸了"）──
        if (omen && age % 3 == 0) {
            // ⚠ ZF190：坍缩模式能活到 2400 tick（配置寿命才 400）⇒ k 必须夹到 [0,1]，
            //   否则 (age - FX_OMEN)/70 会把环半径算到几百格（粒子在几百格外的天上炸开）。
            double k = Mth.clamp((age - FX_OMEN) / (double) Math.max(1, lifetime() - FX_OMEN), 0.0D, 1.0D);
            ring(level, ParticleTypes.SONIC_BOOM, cx, cy, cz, 2.0D + 10.0D * k, 24, age * 0.5D,
                    0.0D, 0.0D);
        }
    }

    /**
     * 身上有没有**任意一件振金装备**（0.14 ZF170c）。
     *
     * <p>用户原话：「穿着任意一件振金装备可以免疫」。判据用**注册名**而不是写死一张物品表：
     * 本 mod 的振金系列注册名都是 {@code vibranium_*}（`ModItems` 里那一串），
     * 以后再加振金件（比如加个振金盾）不用回来改这里。</p>
     */
    public static boolean wearsVibranium(Player player) {
        for (net.minecraft.world.entity.EquipmentSlot slot : new net.minecraft.world.entity.EquipmentSlot[]{
                net.minecraft.world.entity.EquipmentSlot.HEAD,
                net.minecraft.world.entity.EquipmentSlot.CHEST,
                net.minecraft.world.entity.EquipmentSlot.LEGS,
                net.minecraft.world.entity.EquipmentSlot.FEET}) {
            ItemStack worn = player.getItemBySlot(slot);
            if (worn.isEmpty()) {
                continue;
            }
            var id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(worn.getItem());
            if ("potato_s_t".equals(id.getNamespace()) && id.getPath().startsWith("vibranium")) {
                return true;
            }
        }
        return false;
    }





    /** 坍缩：一记大爆炸 + 把吸来的方块留在原地当"遗迹"。 */
    private static void collapse(Hole hole) {
        ServerLevel level = hole.level;
        Vec3 c = hole.center;
        level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(),
                SoundSource.PLAYERS, 3.0F, 0.7F);
        // ⚠ 1.21.1 里**没有** END_CRYSTAL_DEATH 这个音效（第一版照着旧版本的名字写的）；
        //   坍缩那一声改用监守者的音爆（同样是"一记重击"，且不用额外的资源包）。
        level.playSound(null, c.x, c.y, c.z, SoundEvents.WARDEN_SONIC_BOOM,
                SoundSource.PLAYERS, 3.0F, 0.5F);
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, c.x, c.y + 1.0D, c.z, 3, 1.0D, 1.0D, 1.0D, 0.0D);
        for (int i = 0; i < 240; i++) {
            double a = i * 0.3D;
            double r = (i % 12) * 0.5D;
            level.sendParticles(ParticleTypes.SONIC_BOOM, c.x + Math.cos(a) * r,
                    c.y + 0.5D, c.z + Math.sin(a) * r, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        }
        // 说一句"收工"：三个数都报（搬走多少 / 码在地上多少 / 落不下变成掉落物多少）
        if (hole.owner instanceof ServerPlayer sp) {
            sp.sendSystemMessage(Component.translatable(
                    "message.potato_s_t.gravity_done", hole.pulled, hole.placed, hole.dropped)
                    .withStyle(net.minecraft.ChatFormatting.DARK_PURPLE));
        }
        saveInto(level);
    }

    // ============================================================
    //  0.14 ZF190：坍缩模式的电费 + 2 分钟硬上限
    // ============================================================
    /**
     * 坍缩模式这一 tick 的电费（{@link GravityDeviceItem#COLLAPSE_COST_PER_TICK} = 50k FE）。
     *
     * <p>从**召唤它的那件装置**上扣（{@link Hole#powerStack}）。装置不在了（换手 / 掉了 / 玩家离线）
     * 就现场找回一件有电的（{@link #resolvePowerStack}）；实在没有 ⇒ 返回 false，黑洞当场消失
     * （用户原话「每存在1tick消耗50kFE没有电力时候黑洞消失」）。</p>
     */
    private static boolean payCollapsePower(Hole hole) {
        ItemStack stack = hole.powerStack;
        if (stack == null || stack.isEmpty() || GravityDeviceItem.getEnergy(stack) <= 0) {
            stack = resolvePowerStack(hole);
            hole.powerStack = stack;
        }
        if (stack == null || stack.isEmpty()) {
            return false;
        }
        int now = GravityDeviceItem.getEnergy(stack);
        if (now < GravityDeviceItem.COLLAPSE_COST_PER_TICK) {
            return false;
        }
        GravityDeviceItem.setEnergy(stack, now - GravityDeviceItem.COLLAPSE_COST_PER_TICK);
        return true;
    }

    /**
     * 找回"电源"：主人**手上那件**优先，其次背包里任何一件有电的引力装置。
     *
     * <p>⚠ 玩家离线 / 死了没留装置 ⇒ 找不回来 ⇒ 黑洞消失。这条是"电费制"的必然结果，写在注释里不藏着
     * （重启之后也是走这条路：存档里只存了 owner 的 UUID，装置得现找）。</p>
     */
    private static ItemStack resolvePowerStack(Hole hole) {
        if (!(hole.owner instanceof Player p) || p.isRemoved()) {
            return null;
        }
        ItemStack main = p.getMainHandItem();
        if (main.getItem() instanceof GravityDeviceItem && GravityDeviceItem.getEnergy(main) > 0) {
            return main;
        }
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            ItemStack s = p.getInventory().getItem(i);
            if (s.getItem() instanceof GravityDeviceItem && GravityDeviceItem.getEnergy(s) > 0) {
                return s;
            }
        }
        return null;
    }

    /**
     * **2 分钟硬上限**到点：销毁黑洞 + 30 威力爆炸（用户原话
     * 「一个黑洞存在超过2分钟也会销毁 并产生30power的爆炸」）。
     *
     * <p>⚠ 用的是**原版爆炸**（{@code ExplosionInteraction.TNT}：炸方块、掉落物照常），不是纯特效：
     * 30 威力是真的会把周围犁一遍（对照：原版 TNT 是 4）。用户点名要的"危险"，这里不缩水。</p>
     */
    private static void boom(Hole hole) {
        ServerLevel level = hole.level;
        Vec3 c = hole.center;
        level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(),
                SoundSource.PLAYERS, 8.0F, 0.4F);
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, c.x, c.y + 1.0D, c.z, 16,
                3.0D, 3.0D, 3.0D, 0.0D);
        level.explode(null, c.x, c.y, c.z, HARD_CAP_EXPLOSION_POWER,
                net.minecraft.world.level.Level.ExplosionInteraction.TNT);
        if (hole.owner instanceof ServerPlayer sp) {
            sp.sendSystemMessage(Component.translatable(
                    "message.potato_s_t.gravity_done", hole.pulled, hole.placed, hole.dropped)
                    .withStyle(net.minecraft.ChatFormatting.DARK_RED));
        }
        saveInto(level);
    }

    // ============================================================
    //  存档（0.14 ZF169b：用户「黑洞做成存档的吧」）
    // ============================================================
    /**
     * 黑洞的存档：**每个黑洞一条记录**（维度 / 坐标 / 方块 / 拥有者 / 已活 tick / 吸了几个 / 码了几个）。
     *
     * <p>存在**主世界**的 {@code SavedData} 里（跨维度共用一个表，每条自带维度 id）；
     * 服务器起来时由 {@link #loadFrom} 读回来，于是"重启之后黑洞还在原地继续吸"。</p>
     *
     * <p>⚠ 只存"黑洞本身"：已经吸过来码在地上的方块是**真方块**，本来就在世界存档里 ✓；
     * 奇点附近的生物同理。要存的就是这份"还没吸完的清单"。</p>
     */
    public static class Data extends net.minecraft.world.level.saveddata.SavedData {

        public static final String NAME = "potatost_black_holes";

        public static final net.minecraft.world.level.saveddata.SavedData.Factory<Data> FACTORY =
                new net.minecraft.world.level.saveddata.SavedData.Factory<>(
                        Data::new, Data::load, null);

        final List<CompoundTag> holes = new ArrayList<>();

        static Data load(CompoundTag tag, net.minecraft.core.HolderLookup.Provider registries) {
            Data data = new Data();
            net.minecraft.nbt.ListTag list = tag.getList("holes", net.minecraft.nbt.Tag.TAG_COMPOUND);
            for (int i = 0; i < list.size(); i++) {
                data.holes.add(list.getCompound(i));
            }
            return data;
        }

        @Override
        public CompoundTag save(CompoundTag tag, net.minecraft.core.HolderLookup.Provider registries) {
            net.minecraft.nbt.ListTag list = new net.minecraft.nbt.ListTag();
            for (CompoundTag h : this.holes) {
                list.add(h.copy());
            }
            tag.put("holes", list);
            return tag;
        }
    }

    private static Data data(ServerLevel level) {
        return level.getServer().overworld().getDataStorage().computeIfAbsent(Data.FACTORY, Data.NAME);
    }

    /** 把当前活着的黑洞写进存档（每次生成 / 坍缩 / 每 100 tick 调一次）。 */
    public static void saveInto(ServerLevel level) {
        try {
            Data d = data(level);
            d.holes.clear();
            for (Hole hole : HOLES) {
                CompoundTag tag = new CompoundTag();
                tag.putString("dim", hole.level.dimension().location().toString());
                tag.putDouble("x", hole.center.x);
                tag.putDouble("y", hole.center.y);
                tag.putDouble("z", hole.center.z);
                tag.putString("block", net.minecraft.core.registries.BuiltInRegistries.BLOCK
                        .getKey(hole.block).toString());
                tag.putString("owner", hole.owner == null ? "" : hole.owner.getStringUUID());
                tag.putInt("age", hole.age);
                tag.putInt("pulled", hole.pulled);
                tag.putInt("placed", hole.placed);
                tag.putInt("mode", hole.mode);
                tag.putInt("dropped", hole.dropped);
                d.holes.add(tag);
            }
            d.setDirty();
        } catch (Throwable t) {
            System.out.println("[PotatoST] 黑洞存档写入失败：" + t);
        }
    }

    /** 服务器起来时读回（{@code PotatoST} 的 {@code ServerStartedEvent} 调）。 */
    public static void loadFrom(net.minecraft.server.MinecraftServer server) {
        HOLES.clear();
        try {
            Data d = server.overworld().getDataStorage().computeIfAbsent(Data.FACTORY, Data.NAME);
            for (CompoundTag tag : d.holes) {
                ServerLevel level = server.getLevel(net.minecraft.resources.ResourceKey.create(
                        net.minecraft.core.registries.Registries.DIMENSION,
                        net.minecraft.resources.ResourceLocation.parse(tag.getString("dim"))));
                if (level == null) {
                    continue;
                }
                Block block = net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(
                        net.minecraft.resources.ResourceLocation.parse(tag.getString("block")));
                int mode = tag.getInt("mode");
                // ⚠ 0.14 ZF192：「坍缩模式空手也能放」用 **AIR 当哨兵** ⇒ 那种洞不能在这里被丢掉；
                //   别的模式仍然是"方块没了（那个模组被卸了）⇒ 这个黑洞作废"。
                if (block == net.minecraft.world.level.block.Blocks.AIR
                        && mode != GravityDeviceItem.MODE_COLLAPSE) {
                    continue;
                }
                Player owner = null;
                String uuid = tag.getString("owner");
                if (!uuid.isEmpty()) {
                    try {
                        owner = server.getPlayerList().getPlayer(java.util.UUID.fromString(uuid));
                    } catch (IllegalArgumentException ignored) {
                        owner = null;
                    }
                }
                Hole hole = new Hole(level, new Vec3(tag.getDouble("x"), tag.getDouble("y"),
                        tag.getDouble("z")), block, owner, mode);
                hole.age = tag.getInt("age");
                hole.pulled = tag.getInt("pulled");
                hole.placed = tag.getInt("placed");
                if (hole.mode == GravityDeviceItem.MODE_COLLAPSE) {
                    // 0.14 ZF190：坍缩模式是"电费制"，存档里只有 owner 的 UUID ⇒ 装置得现找回来
                    //（找不回来就下一 tick 消失 —— 见 payCollapsePower 的注释）
                    hole.powerStack = resolvePowerStack(hole);
                }
                HOLES.add(hole);
            }
            if (!HOLES.isEmpty()) {
                System.out.println("[PotatoST] 读回 " + HOLES.size() + " 个没吸完的黑洞（ZF169b 存档）");
            }
        } catch (Throwable t) {
            System.out.println("[PotatoST] 黑洞存档读取失败：" + t);
        }
    }
}
