package com.potatost.mod;

import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ProjectileDeflection;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.ProjectileImpactEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.living.LivingKnockBackEvent;
import net.neoforged.neoforge.event.level.ExplosionKnockbackEvent;

/**
 * 振金套的**套装效果**（0.11 ZF120）。
 *
 * <p>用户原话逐条落地（三条都属于"穿满四件才有"那一档，与星璨钢同一口径
 * 「效果须满套装」）：</p>
 *
 * <table border="1">
 *   <caption>三条效果与落点</caption>
 *   <tr><th>用户原话</th><th>监听的事件</th><th>做什么</th></tr>
 *   <tr><td>免疫弹射物攻击并反弹任何弹射物（如果可以反弹的话）</td>
 *       <td>{@link ProjectileImpactEvent}（主打）+ {@link LivingIncomingDamageEvent}（兜底）</td>
 *       <td>命中**取消**（这一下不算命中 ⇒ 不结算伤害、不插在身上），
 *           然后按原版 {@code Projectile.deflect} 把弹射物打回去</td></tr>
 *   <tr><td>降低爆炸伤害 50%</td><td>{@link LivingIncomingDamageEvent}</td>
 *       <td>伤害源带 {@code #minecraft:is_explosion} ⇒ 待结算伤害 × {@link #EXPLOSION_DAMAGE_MULTIPLIER}</td></tr>
 *   <tr><td>免疫任何击退</td><td>{@link LivingKnockBackEvent} + {@link ExplosionKnockbackEvent}</td>
 *       <td>前者取消，后者把击退速度置零</td></tr>
 * </table>
 *
 * <h2>一、为什么"反弹"用 {@code Projectile.deflect} 而不是自己改速度</h2>
 * <p>因为原版本来就有这套机制（本轮从源码核实）：{@code Projectile.java:177-203} 的
 * {@code hitTargetOrDeflectSelf} 会先问被撞的实体
 * {@code entity.deflection(projectile)}，拿到非 {@code NONE} 的结果就
 * <b>不结算伤害</b>、只调用 {@code deflect(...)} 改速度。原版 {@code ProjectileDeflection}
 * 提供四种现成行为，其中</p>
 * <ul>
 *   <li>{@code REVERSE}：{@code setDeltaMovement(getDeltaMovement().scale(-0.5))} +
 *       偏航 170°~190° —— <b>字面意义的"沿原路弹回去，速度减半"</b>，正是"反弹"。
 *       原版拿它给旋风人（{@code EntityTypeTags.DEFLECTS_PROJECTILES}）用。</li>
 *   <li>{@code AIM_DEFLECT}：改成沿**被撞者视线**飞出去（原版拿它给"玩家空手打火球"用，
 *       {@code Player.java:1235}）。那是"打飞"不是"反弹"，所以本轮不选它。</li>
 * </ul>
 * <p>用现成机制的三个好处：速度/朝向/后续判定全走原版逻辑（不会出现"打回去了但箭还认识你"
 * 这类怪事）；{@code deflect} 里那句 {@code setOwner(owner)} 把**击杀归属**一起给了玩家
 * （骷髅射你的箭被弹回去射死它自己，算你的）；{@code AbstractArrow.setOwner} 还会顺手把
 * "骷髅射出的、玩家捡不起来的箭"改成可拾取（{@code AbstractArrow.java:589-598}）。</p>
 *
 * <h2>二、"免疫"为什么要两处判</h2>
 * <p>{@link ProjectileImpactEvent} 是**主流路径**：原版所有弹射物在
 * {@code onHit} 之前都会问这个事件，取消掉就根本走不到扣血
 * （箭在 {@code AbstractArrow.java:236-244}、火球在
 * {@code AbstractHurtingProjectile.java:83-86}，取消后是 {@code break}）。</p>
 * <p>但它不是**唯一**路径 —— 有些伤害虽然带 {@code #minecraft:is_projectile} 标签，
 * 却不是"弹射物撞到人"那个流程（自定义弹射物、别的 mod 的投射物、命令造成的同源伤害）。
 * 所以再挂一道 {@link LivingIncomingDamageEvent}，按**伤害源标签**判：
 * 只要带 {@code is_projectile} 就免疫。两处的关系是"主路径顺手把东西打回去，
 * 兜底那道负责不漏"。</p>
 *
 * <h2>三、"免疫任何击退"为什么要两个事件</h2>
 * <p>游戏里"击退"有两条互不相干的通道（本轮从源码核实）：</p>
 * <ul>
 *   <li><b>受击击退</b>：{@code LivingEntity.hurt} 末尾的 {@code this.knockback(0.4F, dx, dz)}
 *       （{@code LivingEntity.java:953} 附近）以及 {@code Player.attack} /
 *       {@code Mob.doHurtTarget} 那一类 —— 全部经过
 *       {@code LivingEntity.knockback}，而它第一句就是
 *       {@code if (event.isCanceled()) return;}（{@code LivingEntity.java:1529-1531}）
 *       ⇒ 取消 {@link LivingKnockBackEvent} 就彻底不动。</li>
 *   <li><b>爆炸击退</b>：{@code Explosion.explode} **不**走上面那条，
 *       它直接 {@code entity.setDeltaMovement(entity.getDeltaMovement().add(vec31))}
 *       （{@code Explosion.java:302-304}，那一行本来只受
 *       {@code EXPLOSION_KNOCKBACK_RESISTANCE} 属性影响）⇒ 取消受击击退也拦不住它。
 *       对应的钩子是 {@link ExplosionKnockbackEvent}（NeoForge 的，
 *       在 {@code Explosion.java:303} 那一行前触发）。它**不可取消**，
 *       但给了 {@code setKnockbackVelocity} ⇒ 置零即可。</li>
 * </ul>
 * <p>两条都堵上，才配得上用户那句"免疫**任何**击退"。仍然不覆盖的是"被别人挤开"
 * （{@code Entity.push} 那一类碰撞推挤）—— 那不是击退，没有事件，也不该免疫。</p>
 *
 * <h2>四、没做的两件事（记着，免得下次当漏项）</h2>
 * <ul>
 *   <li><b>爆炸不减弹射物伤害</b>：火球打在身上的那一下属于 {@code is_projectile}
 *       ⇒ 直接免疫（连爆炸都不会发生，因为 {@code onHit} 被取消了）；
 *       只有在旁边炸开时才算 {@code is_explosion} ⇒ 减半。两条规则不重叠。</li>
 *   <li><b>不区分"谁的弹射物"</b>：自己射出去的箭落回自己头上也照样免疫+弹开。
 *       用户说的是"免疫弹射物攻击"，加一条"自己射的不算"会多出一个玩家看不见的分支；
 *       而且真加了，兜底那道按伤害源判的免疫又不会跟着分 —— 两处口径会打架。</li>
 * </ul>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class ModVibraniumSet {

    /** 爆炸伤害的倍率：用户原话「降低爆炸伤害50%」⇒ 0.5。 */
    public static final float EXPLOSION_DAMAGE_MULTIPLIER = 0.5F;

    private ModVibraniumSet() {
    }

    // ============================================================
    //  ① 弹射物：免疫 + 反弹
    // ============================================================

    /**
     * 弹射物撞到穿满振金的生物：取消这次命中，并把它打回去。
     *
     * <p>只认 {@link EntityHitResult}（打在方块上不关我们的事）。</p>
     *
     * <p><b>客户端也取消</b>：这是在客户端跑还是服务端跑，取决于实体在哪一侧 tick ——
     * 两边都会走到这里。要是不在客户端取消，客户端会自己把箭"插"在玩家身上，
     * 下一帧再被服务端的位置同步硬拽回去（一帧的视觉抖动）。所以取消两边都做，
     * 而**动实体**（{@code deflect}）只在服务端做 —— {@code Projectile.deflect}
     * 内部本来就有 {@code if (!this.level().isClientSide)}，这里再挡一道是为了让意图写在脸上。</p>
     */
    @SubscribeEvent
    public static void onProjectileImpact(ProjectileImpactEvent event) {
        if (!(event.getRayTraceResult() instanceof EntityHitResult hit)) {
            return;
        }
        if (!(hit.getEntity() instanceof LivingEntity wearer)) {
            return;
        }
        if (!ModArmorMaterials.hasFullVibraniumSet(wearer)) {
            return;
        }
        Projectile projectile = event.getProjectile();

        // 这一下不算命中：不结算伤害、不插在身上、不触发 onHit 的任何副作用。
        event.setCanceled(true);
        if (wearer.level().isClientSide) {
            return;
        }

        // ⚠ 第二帧的保护：近距离被打回去之后，弹射物可能**还**嵌在穿戴者身体里，
        //   于是下一 tick 又"命中"一次。这时若再翻转一次速度，它会在身上来回抖
        //   （每次速度减半、方向来回翻）。判据：速度已经朝外（与"穿戴者→弹射物"同向）
        //   就只取消命中，不再翻转。
        Vec3 outward = projectile.position().subtract(wearer.position());
        if (projectile.getDeltaMovement().dot(outward) <= 0.0) {
            projectile.deflect(ProjectileDeflection.REVERSE, wearer, wearer, true);
        }
    }

    /**
     * 兜底：伤害源带 {@code #minecraft:is_projectile} 就整条抹掉。
     *
     * <p>正常路径上根本轮不到它（上一条已经把命中取消了）；它挡的是
     * "没走 {@link ProjectileImpactEvent} 却仍然算弹射物伤害"的那些来源。</p>
     *
     * <p>取消 = {@code LivingEntity.hurt} 直接 {@code return false}
     * （{@code LivingEntity.java:1152-1153}）⇒ 后面的护甲结算、无敌帧、
     * 受击音效、受击击退**全都不发生**，这正是"免疫"。</p>
     */
    @SubscribeEvent
    public static void onIncomingDamage(LivingIncomingDamageEvent event) {
        LivingEntity wearer = event.getEntity();
        if (!ModArmorMaterials.hasFullVibraniumSet(wearer)) {
            return;
        }
        DamageSource source = event.getSource();
        if (source.is(DamageTypeTags.IS_PROJECTILE)) {
            event.setCanceled(true);
            return;
        }
        if (source.is(DamageTypeTags.IS_EXPLOSION)) {
            // 「降低爆炸伤害50%」：直接把"待结算的伤害"减半。
            // 位置选在**最早**的那一步（护甲/附魔/吸收都还没算），
            // 与抗性提升药水同层 —— 玩家看到的是"这一炸只掉一半血"。
            event.setAmount(event.getAmount() * EXPLOSION_DAMAGE_MULTIPLIER);
        }
    }

    // ============================================================
    //  ② 免疫击退（两条通道）
    // ============================================================

    /** 受击击退（近战/弹射物/爆炸伤害附带的那个 0.4 强度）：整体取消。 */
    @SubscribeEvent
    public static void onKnockback(LivingKnockBackEvent event) {
        if (ModArmorMaterials.hasFullVibraniumSet(event.getEntity())) {
            event.setCanceled(true);
        }
    }

    /**
     * 爆炸自带的那一份击退：置零。
     *
     * <p>{@code ExplosionKnockbackEvent} **不可取消**，只能改速度
     * （{@code Explosion.java:303-304} 会把这里给的值直接加到实体速度上）。</p>
     *
     * <p>只对穿满振金的生物置零；其余实体原样返回，不影响别的 mod 改这一笔。</p>
     */
    @SubscribeEvent
    public static void onExplosionKnockback(ExplosionKnockbackEvent event) {
        Entity affected = event.getAffectedEntity();
        if (affected instanceof LivingEntity wearer
                && ModArmorMaterials.hasFullVibraniumSet(wearer)) {
            event.setKnockbackVelocity(Vec3.ZERO);
        }
    }
}
