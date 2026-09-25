package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * 星轨坠召唤的陨石（0.11 ZF114，本工程第一个自定义实体）。
 *
 * <p>行为很单一：从 {@code y=200} 以恒定速度往下砸，一路拖粒子与呼啸声，撞到第一块非空气方块
 * 就地引爆（把爆炸与掉落全部交给 {@link StarfallRitualManager#impact}），然后自毁。</p>
 *
 * <p><b>为什么用恒定速度而不是自由落体</b>：自由落体要 9~10 秒，而且速度取决于掉落高度 ——
 * 玩家站在山顶还是海平面上，"最后 1 秒报坐标"这句警告的提前量会差好几秒。
 * 恒定 {@code 1.8 格/tick} ⇒ 从 200 到海平面约 <b>3.8 秒</b>，高度差不多的世界里手感一致。</p>
 *
 * <p><b>为什么自己扫方块而不是走原版物理</b>：本实体 {@code noPhysics = true}、位置由
 * {@link #tick()} 直接写，不去碰碰撞箱那套东西 —— 陨石不该被栅栏、告示牌、蛛网之类的东西挡下来，
 * 也不该把沿途的实体挤开。碰到"第一个非空气方块"（含水面）才算落地。</p>
 *
 * <p><b>粒子在服务端发</b>（档案 §4.67 那条规矩）：{@code Level#addParticle} 在服务端是空操作，
 * 必须走 {@link ServerLevel#sendParticles}，原版自带距离裁剪，远处的玩家不会收到包。</p>
 *
 * <p><b>数量按"不太卡"调过</b>：每 tick 8 颗火焰 + 3 团浓烟，熔岩与末地烛按 {@code %3} / {@code %5}
 * 抽稀。一颗陨石从 200 落到地面约 76 tick ⇒ 全程约 900 颗粒子，分摊到 3.8 秒里，
 * 比一台机器每秒 12 颗的量级还低。</p>
 */
public class StarfallMeteorEntity extends Entity {

    /** 下落速度（格/tick）。与渲染缩放 1.6 无关，改速度只影响"多久落地"。 */
    public static final double FALL_SPEED = 1.8D;

    /** 坠落的起始高度（用户原话「从 y=200 砸下来」）。 */
    public static final double SPAWN_Y = 200.0D;

    /** 兜底寿命：20 秒还没落地就自毁，免得留下一个永远在天上的实体。 */
    private static final int MAX_LIFE_TICKS = 400;

    /** 落点威力 7~20，由召唤时 roll 好带下来（决定爆炸威力**和**掉落档位）。 */
    private int power = 7;

    /** 谁叫来的（落地时给他发一条"HUD 收尾"的同步包）。没人认领时是 null —— 探针就吃这条路径。 */
    private java.util.UUID ownerId;

    public StarfallMeteorEntity(EntityType<?> type, Level level) {
        super(type, level);
        this.noPhysics = true;
    }

    public void setPower(int power) {
        this.power = power;
    }

    public int getPower() {
        return this.power;
    }

    public void setOwnerId(java.util.UUID ownerId) {
        this.ownerId = ownerId;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        // 没有需要同步给客户端的字段：位置由原版的实体追踪包负责，
        // 威力只在服务端用于结算（客户端不参与爆炸与掉落）。
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        this.power = tag.getInt("Power");
        if (tag.hasUUID("Owner")) {
            this.ownerId = tag.getUUID("Owner");
        }
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putInt("Power", this.power);
        if (this.ownerId != null) {
            tag.putUUID("Owner", this.ownerId);
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (!(this.level() instanceof ServerLevel server)) {
            return;                     // 客户端不做任何判定（位置由服务端同步）
        }
        this.trail(server);
        if (this.tickCount > MAX_LIFE_TICKS) {
            this.discard();
            return;
        }
        double nextY = this.getY() - FALL_SPEED;
        BlockPos landing = BlockPos.containing(this.getX(), nextY, this.getZ());
        if (nextY <= this.level().getMinBuildHeight() || this.blocked(server, landing)) {
            StarfallRitualManager.impact(server, this.position(), this.power, this, this.ownerId);
            this.discard();
            return;
        }
        this.setPos(this.getX(), nextY, this.getZ());
    }

    /** 目标格是不是"挡住了"：会挡路的方块，或者任何流体（海里就在水面炸）。 */
    private boolean blocked(ServerLevel level, BlockPos pos) {
        if (!level.isLoaded(pos)) {
            return false;
        }
        BlockState state = level.getBlockState(pos);
        return state.blocksMotion() || !state.getFluidState().isEmpty();
    }

    /** 尾迹：火焰 + 浓烟每 tick，熔岩与末地烛抽稀；外加一段音调上扬的呼啸。 */
    private void trail(ServerLevel level) {
        double x = this.getX();
        double y = this.getY() + 0.8D;
        double z = this.getZ();
        level.sendParticles(ParticleTypes.FLAME, x, y, z, 8, 0.45D, 0.6D, 0.45D, 0.02D);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, x, y + 0.6D, z, 3, 0.6D, 0.8D, 0.6D, 0.01D);
        if (this.tickCount % 3 == 0) {
            level.sendParticles(ParticleTypes.LAVA, x, y, z, 2, 0.5D, 0.4D, 0.5D, 0.0D);
        }
        if (this.tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.END_ROD, x, y, z, 4, 0.6D, 0.9D, 0.6D, 0.02D);
            // 呼啸：用原版烟花爆裂声当"哨音"，音调随下坠升高（1.0 → 1.8）
            float pitch = Math.min(1.8F, 1.0F + this.tickCount * 0.012F);
            level.playSound(null, x, y, z, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.WEATHER, 0.8F, pitch);
        }
    }
}
