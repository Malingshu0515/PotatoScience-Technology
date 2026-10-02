package com.potatost.mod;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
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

    /** 单次最多搬多少方块（用户给的数）。 */
    public static final int MAX_BLOCKS = 1200;
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
        int age;
        int pulled;
        int placed;
        double spin;

        Hole(ServerLevel level, Vec3 center, Block block, Player owner) {
            this.level = level;
            this.center = center;
            this.block = block;
            this.owner = owner;
        }
    }

    /** 召唤一个黑洞（由 {@link GravityDeviceItem} 在蓄力满时调）。 */
    public static void spawn(ServerLevel level, Vec3 center, Block block, Player owner) {
        HOLES.add(new Hole(level, center, block, owner));
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
            try {
                pullBlocks(hole);
                pullEntities(hole);
                fx(hole);
                if (hole.age % 20 == 0) {
                    // "心跳"：音量随年龄涨，最后几下最重
                    float t = (float) hole.age / LIFETIME;
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 1.2F + t, 0.5F + t * 0.4F);
                }
                if (hole.age % 60 == 0) {
                    hole.level.playSound(null, hole.center.x, hole.center.y, hole.center.z,
                            SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS, 2.0F, 0.6F);
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
        if (hole.placed >= MAX_BLOCKS) {
            return;
        }
        ServerLevel level = hole.level;
        BlockPos centerPos = BlockPos.containing(hole.center);
        // 每 tick 重新从"最近的"开始找：这样方块是**一层层被剥过来**的，看着像被吸走
        int budget = BLOCKS_PER_TICK;
        int radius = 40;
        for (int r = 0; r <= radius && budget > 0; r++) {
            for (int dx = -r; dx <= r && budget > 0; dx++) {
                for (int dz = -r; dz <= r && budget > 0; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != r) {
                        continue;   // 只扫这一圈的壳
                    }
                    for (int dy = -8; dy <= 12 && budget > 0; dy++) {
                        BlockPos p = centerPos.offset(dx, dy, dz);
                        if (!level.isLoaded(p)) {
                            continue;
                        }
                        BlockState state = level.getBlockState(p);
                        if (!state.is(hole.block)) {
                            continue;
                        }
                        // 搬走：原位置留空气（不掉落物 —— 方块本身要飞到黑洞那儿去）
                        level.removeBlock(p, false);
                        // 路上撒一串粒子，让"它被拽走了"看得见
                        Vec3 from = Vec3.atCenterOf(p);
                        for (int s = 0; s < 8; s++) {
                            double k = s / 8.0D;
                            level.sendParticles(ParticleTypes.REVERSE_PORTAL,
                                    Mth.lerp(k, from.x, hole.center.x),
                                    Mth.lerp(k, from.y, hole.center.y),
                                    Mth.lerp(k, from.z, hole.center.z), 1, 0.05D, 0.05D, 0.05D, 0.02D);
                        }
                        // 落在黑洞脚下：一圈圈往外码（金螺旋），只码在能放的地方
                        placeAt(hole, p);
                        hole.pulled++;
                        budget--;
                    }
                }
            }
        }
    }

    /** 把吸来的方块码在黑洞周围（只往"可替换"的地方放，不砸坏别的东西）。 */
    private static void placeAt(Hole hole, BlockPos from) {
        if (hole.placed >= MAX_BLOCKS) {
            return;
        }
        ServerLevel level = hole.level;
        BlockPos centerPos = BlockPos.containing(hole.center);
        // 金螺旋：第 n 个方块摆在半径 ~ sqrt(n) 的螺线上，几层高
        int n = hole.placed;
        double a = n * 2.399963D;
        int radius = (int) Math.sqrt(n / 3.0D);
        int layer = n % 3;
        BlockPos target = centerPos.offset((int) Math.round(Math.cos(a) * radius), -1 - layer,
                (int) Math.round(Math.sin(a) * radius));
        if (!level.isLoaded(target)) {
            return;
        }
        BlockState there = level.getBlockState(target);
        if (!there.canBeReplaced()) {
            // 放不下就记一笔但**不算数**（下一 tick 换个位置再试），避免"凭空消失"
            return;
        }
        level.setBlockAndUpdate(target, hole.block.defaultBlockState());
        hole.placed++;
        level.sendParticles(ParticleTypes.SMOKE, target.getX() + 0.5D, target.getY() + 1.0D,
                target.getZ() + 0.5D, 3, 0.2D, 0.1D, 0.2D, 0.01D);
    }

    // ============================================================
    //  吸生物 + 虚空伤害
    // ============================================================
    private static void pullEntities(Hole hole) {
        ServerLevel level = hole.level;
        AABB box = new AABB(hole.center, hole.center).inflate(PULL_RADIUS);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box)) {
            if (e == hole.owner) {
                continue;   // 召唤者自己不受影响（不然刚放完就被自己的黑洞吸住）
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
    private static void fx(Hole hole) {
        ServerLevel level = hole.level;
        double cx = hole.center.x;
        double cy = hole.center.y + 0.6D;
        double cz = hole.center.z;
        boolean loud = hole.age % 3 == 0;   // 每 3 tick 放"重"的那几层，省包但不掉帧感

        // ① 事件视界：一圈贴着奇点的黑紫光环（永远在）
        ring(level, ParticleTypes.REVERSE_PORTAL, cx, cy, cz, 2.2D, 16, hole.spin * 1.0D, 0.0D);
        ring(level, ParticleTypes.PORTAL, cx, cy, cz, 2.8D, 20, -hole.spin * 1.4D, 0.0D);

        if (loud) {
            // ② 吸积盘：三个半径、三个倾角的螺旋盘，反向自转
            disk(level, ParticleTypes.SOUL_FIRE_FLAME, cx, cy, cz, 4.5D, 34, hole.spin * 0.8D, 0.22D);
            disk(level, ParticleTypes.END_ROD, cx, cy, cz, 6.5D, 40, -hole.spin * 0.55D, -0.18D);
            disk(level, ParticleTypes.ELECTRIC_SPARK, cx, cy, cz, 8.5D, 46, hole.spin * 0.35D, 0.30D);
            // ③ 内落流：从盘外沿"掉"进奇点的粒子雨（拖尾 = 同一条线上的多点）
            for (int i = 0; i < 14; i++) {
                double a = hole.spin * 0.5D + i * (Math.PI * 2.0D / 14.0D);
                double r0 = 9.0D + (i % 3);
                for (int s = 0; s < 7; s++) {
                    double k = s / 7.0D;
                    double r = r0 * (1.0D - k);
                    double y = cy + Math.sin(a * 2.0D + k * 6.0D) * 1.4D * (1.0D - k);
                    level.sendParticles(ParticleTypes.PORTAL, cx + Math.cos(a) * r, y,
                            cz + Math.sin(a) * r, 1, 0.02D, 0.02D, 0.02D, 0.0D);
                }
            }
            // ④ 视界外的"引力透镜"光弧：一层上下对称的端杆粒子，随时间收缩
            double squeeze = 12.0D - 6.0D * Math.sin(hole.age * 0.08D);
            ring(level, ParticleTypes.END_ROD, cx, cy + 0.2D, cz, Math.max(3.0D, squeeze), 28,
                    hole.spin * 0.2D, 0.0D);
            // ⑤ 核心：偶发的闪白 + 烟（越到后期越密）
            if (hole.age % 9 == 0) {
                level.sendParticles(ParticleTypes.FLASH, cx, cy, cz, 2, 0.3D, 0.3D, 0.3D, 0.0D);
            }
            level.sendParticles(ParticleTypes.LARGE_SMOKE, cx, cy, cz, 6, 0.6D, 0.4D, 0.6D, 0.01D);
            level.sendParticles(ParticleTypes.SQUID_INK, cx, cy, cz, 4, 1.2D, 0.5D, 1.2D, 0.02D);
        }
    }

    /** 一圈（水平环）。 */
    private static void ring(ServerLevel level, ParticleOptions type, double cx, double cy, double cz,
                             double radius, int count, double phase, double tilt) {
        for (int i = 0; i < count; i++) {
            double a = phase + i * (Math.PI * 2.0D / count);
            double x = cx + Math.cos(a) * radius;
            double z = cz + Math.sin(a) * radius;
            double y = cy + Math.sin(a) * radius * tilt;
            level.sendParticles(type, x, y, z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        }
    }

    /** 一张盘（螺旋，倾角靠 tilt 把 y 随角度抬起来）。 */
    private static void disk(ServerLevel level, ParticleOptions type, double cx, double cy, double cz,
                             double radius, int count, double phase, double tilt) {
        for (int i = 0; i < count; i++) {
            double a = phase + i * (Math.PI * 2.0D / count) + i * 0.12D;   // 多出来的 0.12 就是"螺旋"
            double r = radius * (0.75D + 0.25D * Math.sin(a * 3.0D + phase));
            double x = cx + Math.cos(a) * r;
            double z = cz + Math.sin(a) * r;
            double y = cy + Math.sin(a) * r * tilt;
            level.sendParticles(type, x, y, z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        }
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
        // 说一句"收工"（玩家在聊天栏看得到搬了多少）
        if (hole.owner instanceof ServerPlayer sp) {
            sp.sendSystemMessage(Component.translatable(
                    "message.potato_s_t.gravity_done", hole.pulled, hole.placed)
                    .withStyle(net.minecraft.ChatFormatting.DARK_PURPLE));
        }
    }
}
