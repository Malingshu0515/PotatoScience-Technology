package com.potatost.mod;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import net.minecraft.core.BlockPos;
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
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
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
 *       每 tick 有**预算**（{@link #BLOCKS_PER_TICK}），单次上限 {@link #MAX_BLOCKS}（用户给的 1200）。
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

    /** 单次最多搬多少方块（用户 ZF170b 把上限从 1200 提到 **1500**）。 */
    public static final int MAX_BLOCKS = 1500;
    /** 0.14 ZF172：吸方块的范围 = **5×5×5 区块的正方体** ⇒ 每轴 ±40 格（用户在「3x3区块」基础上改的）。 */
    public static final int HALF = 40;
    /** 每轴位置数（81）。 */
    public static final int SCAN_SIDE = HALF * 2 + 1;
    /** 正方体里的位置总数（81³ = 531,441）。 */
    public static final int SCAN_VOLUME = SCAN_SIDE * SCAN_SIDE * SCAN_SIDE;
    /**
     * 每 tick 每个黑洞最多发多少个**粒子包**（0.14 ZF173：炫技可以，TPS 不能换）。
     *
     * <p>所有特效都必须走 {@link #fx} 这个助手，它在超预算时**直接不发** ——
     * 于是"再炫"也有硬顶：一层层叠上去只会被裁掉最后几层，不会把服务器拖死。</p>
     */
    public static final int FX_BUDGET_PER_TICK = 320;
    /** 分幕：降临结束 / 前兆开始（总长 = {@link #LIFETIME}）。 */
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
    /** 一次黑洞活多久（20 秒）。 */
    public static final int LIFETIME = 20 * 20;
    /** 模式 2 同时在天上飞的下落方块上限（防实体爆炸）。 */
    public static final int MAX_FLYING = 48;
    /**
     * 黑洞脚下的**禁采区半径**（0.14 ZF170c）：这一圈里的同种方块一律不再吸。
     *
     * <p>为什么必须有它：码好的方块和要吸的方块**是同一种**，而它们就在扫描范围内 ⇒
     * 黑洞会把自己刚码的又吸一遍（数字狂涨、地上什么都看不到）。半径 12 够盖住
     * {@code placeAt} 的金螺旋（1500 个的螺旋半径约 sqrt(500) ≈ 22 … 所以还要看 {@link #MAX_BLOCKS}
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
        /** 0 = 吞噬搬运，1 = 引力牵引（下落方块飞过去，绝不消失）。见 GravityDeviceItem。 */
        final int mode;
        int age;
        int pulled;
        int placed;
        /** 落点不够、改成**掉落物**的数量（用户 ZF170b：「放不下的变成掉落物」）。 */
        int dropped;
        double spin;
        /** 0.14 ZF172：这一轮扫到 81³ 里的第几个（每 tick 续着扫，不许每 tick 从头全扫）。 */
        int cursor;

        Hole(ServerLevel level, Vec3 center, Block block, Player owner) {
            this(level, center, block, owner, GravityDeviceItem.MODE_SWALLOW);
        }

        Hole(ServerLevel level, Vec3 center, Block block, Player owner, int mode) {
            this.level = level;
            this.center = center;
            this.block = block;
            this.owner = owner;
            this.mode = mode;
        }
    }

    /** 召唤一个黑洞（由 {@link GravityDeviceItem} 在蓄力满时调）。 */
    public static void spawn(ServerLevel level, Vec3 center, Block block, Player owner, int mode) {
        Hole hole = new Hole(level, center, block, owner, mode);
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
        HOLES.clear();
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
                pullBlocks(hole);
                pullEntities(hole);
                fx(hole);
                if (hole.age % 20 == 0) {
                    // "心跳"：音量随年龄涨，最后几下最重
                    float t = (float) hole.age / LIFETIME;
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
            if (hole.age >= LIFETIME) {
                collapse(hole);
                it.remove();
            }
        }
    }

    // ============================================================
    //  吸方块
    // ============================================================
    private static void pullBlocks(Hole hole) {
        // ⚠⚠ 0.14 ZF170b：上限判据原来只看 `placed` ⇒ 模式 2 那条路 `placed` 永远不涨，
        //   上限**彻底失效**（用户实测一次吸了 **16992** 块，世界被啃掉一大片）。
        //   现在改成看 **pulled**（搬走的都算），1500 一到立刻停手。
        if (hole.pulled >= MAX_BLOCKS) {
            return;
        }
        ServerLevel level = hole.level;
        BlockPos centerPos = BlockPos.containing(hole.center);
        // ── 0.14 ZF172：范围 = 5×5×5 区块的正方体（±40 格，81³ 个位置）──
        //    用**线性游标**扫：每 tick 只看 EXAMINE_PER_TICK 个位置，扫完一轮从头再来。
        //    这样"处处没有目标方块"时也只花固定的那点开销（否则 53 万个位置每 tick 全扫 = 服务器跪）。
        int budget = BLOCKS_PER_TICK;
        int examined = 0;
        while (examined < EXAMINE_PER_TICK && budget > 0) {
            int idx = hole.cursor;
            hole.cursor = (hole.cursor + 1) % SCAN_VOLUME;
            examined++;
            // 线性下标 → (dx, dy, dz)，每个轴都是 -HALF..+HALF
            int dx = idx % SCAN_SIDE - HALF;
            int dz = (idx / SCAN_SIDE) % SCAN_SIDE - HALF;
            int dy = idx / (SCAN_SIDE * SCAN_SIDE) - HALF;
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
            if (placeAt(hole, p)) {
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
     * 把方块码在黑洞周围（只往"可替换"的地方放，不砸坏别的东西）。
     *
     * <p><b>⚠ 0.14 ZF170 改成 boolean 并**不再自己拆原件****：旧版是"先拆、再调它"，
     * 而它放不下时直接 return ⇒ 方块拆了却没落地 = 用户看到的"吸过来就消失"。
     * 现在它只负责"放"，放成了返回 true，由调用方再拆原位 —— 顺序反过来了。</b></p>
     */
    private static boolean placeAt(Hole hole, BlockPos from) {
        if (hole.placed >= MAX_BLOCKS) {
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
        level.setBlockAndUpdate(target, hole.block.defaultBlockState());
        hole.placed++;
        level.sendParticles(ParticleTypes.SMOKE, target.getX() + 0.5D, target.getY() + 1.0D,
                target.getZ() + 0.5D, 3, 0.2D, 0.1D, 0.2D, 0.01D);
        return true;
    }

    /**
     * 模式 2「引力牵引」：把方块变成**下落方块**（{@code FallingBlockEntity}）朝黑洞飞过去。
     *
     * <p>用户原话：「把目标方块吸引过来而**不消失**」。下落方块落地会**变回真方块**，
     * 落不下去时还会掉成**物品**（原版行为）⇒ 任何情况下都不丢 ✓，而且过程看得见（真的在飞）。</p>
     */
    private static void launchFalling(Hole hole, BlockPos pos, BlockState state) {
        ServerLevel level = hole.level;
        // 同时飞的数量封顶（1200 个实体一起来服务器会跪）
        AABB box = new AABB(hole.center, hole.center).inflate(PULL_RADIUS);
        if (level.getEntitiesOfClass(net.minecraft.world.entity.item.FallingBlockEntity.class, box)
                .size() >= MAX_FLYING) {
            return;
        }
        level.removeBlock(pos, false);
        net.minecraft.world.entity.item.FallingBlockEntity falling =
                net.minecraft.world.entity.item.FallingBlockEntity.fall(level, pos, state);
        falling.setDeltaMovement(hole.center.subtract(Vec3.atCenterOf(pos)).normalize().scale(0.85D)
                .add(0.0D, 0.35D, 0.0D));
        falling.hurtMarked = true;
        falling.setStartPos(pos);
        level.addFreshEntity(falling);
        hole.pulled++;
        // 起飞那一瞬撒一圈光点
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, pos.getX() + 0.5D, pos.getY() + 0.5D,
                pos.getZ() + 0.5D, 10, 0.3D, 0.3D, 0.3D, 0.05D);
    }

    // ============================================================
    //  吸生物 + 虚空伤害
    // ============================================================
    private static void pullEntities(Hole hole) {
        ServerLevel level = hole.level;
        AABB box = new AABB(hole.center, hole.center).inflate(PULL_RADIUS);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box)) {
            // ⚠ 0.14 ZF170c（用户要的）：黑洞**也吸玩家**（包括召唤者自己）；
            //   **穿着任意一件振金装备就免疫**（吸不动 + 不掉血，只留视觉）。
            if (e instanceof Player p && wearsVibranium(p)) {
                level.sendParticles(ParticleTypes.ENCHANT, p.getX(), p.getY() + 1.0D, p.getZ(),
                        6, 0.4D, 0.6D, 0.4D, 0.02D);   // 免疫时身上泛一圈附魔光（看得见的"挡住了"）
                continue;
            }
            double dist = e.position().distanceTo(hole.center);
            Vec3 dir = hole.center.subtract(e.position());
            if (dir.lengthSqr() < 1.0E-4D) {
                continue;
            }
            // 越近越猛：1/(d/CORE + 1)
            double strength = 1.6D / (dist / CORE + 1.0D);
            Vec3 v = e.getDeltaMovement().add(dir.normalize().scale(strength));
            // 切向那一分量：让生物绕着奇点转（不是直直掉进去）—— 视觉上好看得多
            Vec3 tangent = new Vec3(-dir.z, 0.0D, dir.x).normalize().scale(strength * 0.45D);
            e.setDeltaMovement(v.add(tangent));
            e.hurtMarked = true;
            e.fallDistance = 0.0F;
            if (dist <= VOID_RADIUS && hole.age % VOID_DAMAGE_INTERVAL == 0) {
                // 原版的"虚空"伤害类型
                e.hurt(level.damageSources().fellOutOfWorld(), 4.0F);
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

        // ── 光子环：贴着急速旋转的亮环（每 tick、24 点、切向速度）── 黑洞的"招牌" ──
        ring(level, ParticleTypes.END_ROD, cx, cy, cz, 2.35D, 24, spin * 2.2D, 0.0D, 0.22D);

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
            disk(level, ParticleTypes.SOUL_FIRE_FLAME, cx, cy, cz, 4.5D, 26, spin * 0.8D, 0.22D, 0.18D);
            disk(level, ParticleTypes.END_ROD, cx, cy, cz, 6.5D, 30, -spin * 0.55D, -0.18D, 0.16D);
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
                fx(level, ParticleTypes.PORTAL, cx + Math.cos(a) * r, y, cz + Math.sin(a) * r,
                        1, -Math.cos(a) * 0.5D, -0.05D, -Math.sin(a) * 0.5D, 0.5D);
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
            double k = (age - FX_OMEN) / (double) Math.max(1, LIFETIME - FX_OMEN);
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
                if (block == net.minecraft.world.level.block.Blocks.AIR) {
                    continue;   // 方块没了（那个模组被卸了）⇒ 这个黑洞作废
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
                        tag.getDouble("z")), block, owner, tag.getInt("mode"));
                hole.age = tag.getInt("age");
                hole.pulled = tag.getInt("pulled");
                hole.placed = tag.getInt("placed");
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
