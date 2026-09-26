package com.potatost.mod;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ProjectileDeflection;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.ProjectileImpactEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.entity.living.LivingFallEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.living.LivingKnockBackEvent;
import net.neoforged.neoforge.event.level.ExplosionKnockbackEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/**
 * 振金套的**套装效果**（0.11 ZF120 立起三条；0.11 ZF136 又加了三条）。
 *
 * <h2>一、最初的三条（ZF120，用户原话逐条落地）</h2>
 *
 * <p>三条都属于"穿满四件才有"那一档，与星璨钢同一口径「效果须满套装」：</p>
 *
 * <table border="1">
 *   <caption>ZF120 的三条效果与落点</caption>
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
 * <h2>二、ZF136 加的三条（用户原话「振金套你看看能不能略微加强一下 现在地位太尴尬了
 *     比星璨麻烦很多 却大大不如晚上的星璨 简直就是个白板」，拍板「乙方案 + 一条新套装效果」）</h2>
 *
 * <p><b>为什么"白板"这个评价是准的</b>（本轮按原版公式逐格算过，`_zf136_calc.py`）：
 * 振金原来的 20 护甲 / 12 韧性就是**原版下界合金那一行**，10 点伤害吃 2.80；
 * 而星璨钢**白天**（28 护甲）只吃 2.00、**夜晚主世界**（再叠抗性提升 II）只吃 1.20。
 * 也就是说振金连白天的星璨都不如，而它比星璨贵得多（12 金锭 + 8 热力金属 + 3 银锭 +
 * 2 高碳钢 + 1 硬质钛合金，再各加 1 粗振金 + 2 下界合金碎片，14500 FE/t）。</p>
 *
 * <table border="1">
 *   <caption>ZF136 的三条效果与落点</caption>
 *   <tr><th>内容</th><th>监听的事件</th><th>做什么</th></tr>
 *   <tr><td>满套常驻**抗性提升 I**（不分昼夜、不分维度）</td>
 *       <td>{@link PlayerTickEvent.Post}</td>
 *       <td>不满足就补一条 16 s 的 {@code DAMAGE_RESISTANCE}（{@link #RESISTANCE_TICKS}），
 *           到点前 2 s 续上 ⇒ 穿着期间**永不断档**；图标一直亮（这就是"不是白板"最直观的一处）</td></tr>
 *   <tr><td>满套**免疫摔落伤害**</td><td>{@link LivingFallEvent}</td>
 *       <td>取消 ⇒ {@code causeFallDamage} 直接 return false：不结算伤害、**连摔落音效都不放**</td></tr>
 *   <tr><td>满套：**10% 概率把 100% 的伤害返还给攻击者**，被反伤而死的人文案是「踢到了铁板」</td>
 *       <td>{@link LivingDamageEvent.Post}</td>
 *       <td>用**这一击的原始伤害**（进护甲前）给对方来一下，
 *           伤害类型是自定义的 {@code potato_s_t:vibranium_reflect} ⇒ 死亡文案走它自己的键</td></tr>
 * </table>
 *
 * <h2>三、为什么"反弹"用 {@code Projectile.deflect} 而不是自己改速度</h2>
 * <p>因为原版本来就有这套机制（ZF120 从源码核实）：{@code Projectile.java:177-203} 的
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
 * <h2>四、"免疫"为什么要两处判</h2>
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
 * <h2>五、"免疫任何击退"为什么要两个事件</h2>
 * <p>游戏里"击退"有两条互不相干的通道（ZF120 从源码核实）：</p>
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
 * <h2>六、常驻抗性 I：为什么是 {@code PlayerTickEvent.Post}</h2>
 * <p><b>先说一处与另外三条的不一致，以及它为什么可以接受</b>：振金另外三条效果判的都是
 * "**穿戴者**"（{@link ModArmorMaterials#hasFullVibraniumSet} 接受任意 {@link LivingEntity}），
 * 因为它们的判据本来就发生在带实体的事件里 —— 多判一个怪物不花任何额外代价。
 * 这一条不一样：它必须**主动每 tick 去看**，而"每个活体每 tick"这件事在本版 NeoForge 里
 * 没有现成的钩子（`LivingEvent.LivingTickEvent` 只在文档里被 `PlayerTickEvent` 引用，
 * 盘上并不存在这个类；能用的只有 `EntityTickEvent`，那是**每个实体**、连掉落物都算）。
 * 为了一个"怪物穿满振金"的假想场面去挂一条每实体每 tick 的钩子，不划算；
 * 而星璨钢那套的夜晚抗性走的就是 {@link PlayerTickEvent.Post} —— 两套盔甲的"持续型效果"
 * 落在同一个口子上，本身也更好讲。**代价写在脸上**：怪物穿满振金不会得到这一条
 * （另外三条照样有效），而怪物穿满振金的概率约等于零。</p>
 * <p><b>为什么不用 {@code EntityTickEvent.Post}</b>：它每 tick 对**每个**实体触发一次
 * （`ServerLevel.tickNonPassenger` 与 `Entity.rideTick` 两处，见 {@code ServerLevel.java:776}
 * 与 {@code Entity.java:2050-2052}），而且客户端也响。收益是"怪物也有"，成本是全场实体。
 * 这笔账不划算。</p>
 * <p><b>三条补充判据与星璨钢那套的 {@code ModArmorSet.ensure} 完全同口径</b>：
 * ① 已有更高等级 ⇒ 不覆盖（身上有抗性 III 时不会被压回 I）；
 * ② 剩余时长还大于 {@link #RESISTANCE_REFRESH}（2 s）⇒ 不续；
 * ③ 否则补一条 {@link #RESISTANCE_TICKS}（16 s）的新实例。
 * {@code ambient = true} ⇒ 粒子更淡（套装给的效果不该像药水那样糊住屏幕）；
 * {@code visible = true} ⇒ 图标照常显示 —— 这一条正是用户要的"别像个白板"。</p>
 *
 * <h2>七、免疫摔落：为什么是 {@code LivingFallEvent} 而不是"按伤害标签取消"</h2>
 * <p>本工程已有的写法是"挂 {@link LivingIncomingDamageEvent}、按伤害标签取消"（弹射物那条），
 * 但摔落有**更靠前**的钩子：{@code Entity.checkFallDamage}（{@code Entity.java:1192-1210}）
 * 在落地那一帧调 {@code state.getBlock().fallOn(...)} ⇒
 * {@code LivingEntity.causeFallDamage}（{@code LivingEntity.java:1646-1662}），
 * 而它第一句就是 {@code CommonHooks.onLivingFall(...)}：事件被取消 ⇒ 返回 {@code null} ⇒
 * 直接 {@code return false}。**在伤害事件之前就结束了**，于是</p>
 * <ul>
 *   <li>不结算伤害；</li>
 *   <li>连 {@code playSound(getFallDamageSound(...))} 与 {@code playBlockFallSound()} 都不会执行
 *       （那两句在事件之后）⇒ 重甲落地不再"砰"一声，听感上也对得上"振金吸掉了这一下"；</li>
 *   <li>坠落距离照旧被 {@code resetFallDistance()} 清掉（那一句在 {@code checkFallDamage} 里，
 *       与本事件无关）⇒ 没有"这次免了、下次一起算"的隐患。</li>
 * </ul>
 * <p>换成"按 {@code #minecraft:is_fall} 取消伤害"当然也能免伤，但会留下音效与粒子 —— 那就是
 * "听起来还是摔了个结实"。所以这一条走 {@link LivingFallEvent}。</p>
 *
 * <h2>八、反伤：为什么挂在"伤害之后"，反的又是哪个数</h2>
 * <p><b>为什么不是"伤害之前"那个事件</b>（{@link LivingIncomingDamageEvent}）：
 * 它比**无敌帧判定**更早 —— {@code LivingEntity.hurt} 的顺序是
 * ① 建 {@code DamageContainer} → ② 触发 {@code LivingIncomingDamageEvent}
 * （{@code LivingEntity.java:1152-1153}）→ … → ⑧
 * {@code if (this.invulnerableTime > 10 && !source.is(BYPASSES_COOLDOWN))}
 * （{@code LivingEntity.java:1190-1199}）。也就是说**挨完一下之后的 0.5 秒里再挨一下，
 * 事件照样触发、但那一下根本不掉血**。挂在那里掷骰子，会出现"我明明没掉血，攻击者却被反伤"。
 * 挂在 {@link LivingDamageEvent.Post}（在 {@code actuallyHurt} 末尾、{@code LivingEntity.java:1805}）
 * 就只在**这一下真的走过结算**之后才轮到我们。</p>
 * <p><b>反伤的数值 = 这一击的原始伤害</b>（{@code event.getOriginalDamage()}，
 * 即进护甲之前、{@code hurt} 收到的那一个数）。用户说的是"返还 **100% 的伤害**"，
 * 而振金穿戴者自己只吃下其中一小截（20% 上下）—— 要是按"我掉的血"去反，
 * 攻击者挨的还不到他自己出手的零头，"踢到铁板"就不成立了。
 * ⚠ 一个已知的口径细节：无敌帧里"只结算差额"那种情况下（{@code LivingEntity.java:1197}
 * 传的是 {@code amount - lastHurt}），我们反的**仍是整击的原始伤害**而不是差额 ——
 * 差额那点事不值得再多一条分支，而且它只在那 10 tick 的窗口内、且后一下更重时才出现。</p>
 * <p><b>为什么要求 {@code getNewDamage() > 0}</b>：{@code actuallyHurt} 末尾那句
 * {@code onLivingDamagePost(...)} 是**无条件**执行的（{@code LivingEntity.java:1805} 在
 * {@code if (f1 != 0.0F)} 那个块**外面**）⇒ 被盾牌全额挡下、或被伤害吸收全额吃掉的那一下
 * 也会走到本事件。那种情况按"没挨到"处理：不掷骰、不反伤。</p>
 * <p><b>排除的三类来源</b>：</p>
 * <ul>
 *   <li>{@code potato_s_t:vibranium_reflect} **本身** ⇒ 两个人都穿满振金时不会你反我、我反你
 *       （这条是**递归保护**，不是平衡）。</li>
 *   <li>带 {@code #minecraft:is_projectile} 的 ⇒ 那类伤害已经被上面第一条整条免疫掉了，
 *       再反一次等于"既弹回去又掉血"两开花。</li>
 *   <li>带 {@code #minecraft:is_explosion} 的 ⇒ 已经减半了，而且那一下的"攻击者"往往是
 *       苦力怕自己或者点了 TNT 的人，"踢到铁板"讲的不是这个。</li>
 * </ul>
 * <p><b>死亡文案</b>走自定义伤害类型：{@code data/potato_s_t/damage_type/vibranium_reflect.json}
 * 的 {@code message_id = "potato_s_t.vibranium_reflect"}
 * ⇒ 文案键 {@code death.attack.potato_s_t.vibranium_reflect}，值是
 * {@code %1$s踢到了铁板}。`%1$s` 正是**死掉的那个人**（原攻击者）——
 * 这一点是查过 {@code DamageSource.getLocalizedDeathMessage}
 * （{@code DamageSource.java:78-92}）才敢写的：带实体来源时它拼的是
 * {@code Translatable(s, livingEntity.getDisplayName(), component)}，
 * 第一个参数是**受害者**、第二个才是造成伤害的人。反伤这一下的"受害者"就是先动手的那位，
 * 所以文案里出现的名字天然是攻击者，不需要我们再拼字符串。</p>
 *
 * <h2>九、没做的两件事（记着，免得下次当漏项）</h2>
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

    /**
     * 反伤概率（0.11 ZF136）：用户原话「10%概率返还100%的伤害给攻击者」⇒ 0.1。
     *
     * <p>掷骰用的是**穿戴者自己的** {@code RandomSource}（{@code wearer.getRandom()}）——
     * 不新开 {@code Random}、不用 {@code Math.random()}：前者不随存档走，
     * 后者在多线程的服务端 tick 里没有可复现性，探针也就没法验。</p>
     */
    public static final float REFLECT_CHANCE = 0.1F;

    /**
     * 反伤用的伤害类型（0.11 ZF136）——
     * {@code data/potato_s_t/damage_type/vibranium_reflect.json} 就是它的数据包定义。
     *
     * <p>本工程**第一个**自定义伤害类型（此前所有伤害都用原版的）。只有自定义了，
     * 死亡文案才能是「踢到了铁板」而不是原版那几句
     * （{@code DamageSource.java:79} 那句 {@code "death.attack." + this.type().msgId()}）。</p>
     *
     * <p>⚠ 这一类**不是** {@code DeferredRegister} 的东西：伤害类型是**数据包注册表**
     * （{@code Registries.DAMAGE_TYPE}），运行时从 {@code level.registryAccess()} 取
     * —— 见 {@link #reflectSource}。</p>
     */
    public static final ResourceKey<DamageType> VIBRANIUM_REFLECT =
            ResourceKey.create(Registries.DAMAGE_TYPE,
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "vibranium_reflect"));

    /** 抗性提升 I 的 amplifier（0 = I 级）。 */
    private static final int RESISTANCE_I = 0;

    /** 常驻抗性的单次时长（tick）：320 = 16 s，与星璨钢那套的"夜晚持续型"同一个数。 */
    private static final int RESISTANCE_TICKS = 320;

    /** 剩余时长低于这个值就补（tick）：40 = 2 s ⇒ 穿着期间断不了档。 */
    private static final int RESISTANCE_REFRESH = 40;

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

    // ============================================================
    //  ③ ZF136：满套常驻抗性提升 I
    // ============================================================

    /**
     * 穿满振金的玩家每 tick 查一次：身上没有抗性提升 I（或快断档、或等级不够）就补一条。
     *
     * <p>为什么是玩家、为什么不是"每个活体每 tick"，见类注释第六节。</p>
     *
     * <p>⚠ 只在服务端补：{@code addEffect} 在客户端只会催生一个本地效果实例，
     * 下一帧就被服务端同步覆盖（与 ZF103 那套同一个道理）—— 而
     * {@link PlayerTickEvent.Post} 本来就在两侧都会触发。</p>
     */
    @SubscribeEvent
    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        if (!ModArmorMaterials.hasFullVibraniumSet(player)) {
            return;
        }
        MobEffectInstance current = player.getEffect(MobEffects.DAMAGE_RESISTANCE);
        if (current != null && current.getAmplifier() >= RESISTANCE_I
                && current.getDuration() > RESISTANCE_REFRESH) {
            return;
        }
        player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE,
                RESISTANCE_TICKS, RESISTANCE_I, true, true));
    }

    // ============================================================
    //  ④ ZF136：满套免疫摔落伤害
    // ============================================================

    /**
     * 穿满振金的活体落地：直接取消这次摔落。
     *
     * <p>见类注释第七节：取消 {@link LivingFallEvent} 之后，
     * {@code LivingEntity.causeFallDamage} 连摔落音效都不会播
     * （那两句在事件之后，{@code LivingEntity.java:1652-1661}）。</p>
     *
     * <p>不区分维度、不区分是否骑乘 —— "振金吸掉了这一下"没有例外条款。</p>
     */
    @SubscribeEvent
    public static void onFall(LivingFallEvent event) {
        if (ModArmorMaterials.hasFullVibraniumSet(event.getEntity())) {
            event.setCanceled(true);
        }
    }

    // ============================================================
    //  ⑤ ZF136：10% 反伤（含「踢到了铁板」死亡文案）
    // ============================================================

    /**
     * 穿满振金的生物**真的被打掉血**之后：10% 概率把这一击的原始伤害还给攻击者。
     *
     * <p>判据顺序与理由见类注释第八节，这里只重复三条最容易写错的：</p>
     * <ul>
     *   <li>挂 {@code Post}（不是 {@code Incoming}）—— 后者比无敌帧判定更早，
     *       会在"根本没掉血"的那一下掷骰子；</li>
     *   <li>{@code getNewDamage() > 0} —— {@code Post} 是**无条件**触发的，
     *       被盾牌/伤害吸收全吃掉的那一下也在里面；</li>
     *   <li>反的是 {@code getOriginalDamage()}（进护甲前），不是"我掉了多少血"。</li>
     * </ul>
     *
     * <p>⚠ 反伤这一下**会不会被对方的振金再反回来**：不会 ——
     * {@link #VIBRANIUM_REFLECT} 在排除名单里，而它正是我们自己发出去的那个类型
     * （双方都穿满振金时，A 反给 B 的那一下在 B 身上不会触发第二条反伤）。</p>
     */
    @SubscribeEvent
    public static void onDamagePost(LivingDamageEvent.Post event) {
        LivingEntity wearer = event.getEntity();
        if (!ModArmorMaterials.hasFullVibraniumSet(wearer)) {
            return;
        }
        // 真的掉血了才算这一下"打到了铁板"（盾牌全挡 / 伤害吸收全吃 => 不掷骰）
        if (event.getNewDamage() <= 0.0F) {
            return;
        }
        DamageSource source = event.getSource();
        if (source.is(VIBRANIUM_REFLECT)
                || source.is(DamageTypeTags.IS_PROJECTILE)
                || source.is(DamageTypeTags.IS_EXPLOSION)) {
            return;
        }
        if (!(source.getEntity() instanceof LivingEntity attacker)
                || attacker == wearer || !attacker.isAlive()) {
            return;
        }
        if (wearer.getRandom().nextFloat() >= REFLECT_CHANCE) {
            return;
        }
        float amount = event.getOriginalDamage();
        if (amount <= 0.0F) {
            return;
        }
        attacker.hurt(reflectSource(wearer), amount);
    }

    /**
     * 反伤那一击的伤害源：类型是 {@link #VIBRANIUM_REFLECT}，**实体是穿戴者自己**。
     *
     * <p>为什么实体（{@code causingEntity} 与 {@code directEntity} 都）填穿戴者：
     * ① 击杀归属 —— {@code DamageSource.getEntity()} 就是原版认"谁杀的"那一个
     * （{@code LivingEntity.getKillCredit}、玩家击杀统计、掉落物归属都看它）；
     * ② 死亡文案 —— {@code getLocalizedDeathMessage} 的第一个参数永远是**受害者**，
     * 所以把穿戴者填成来源，文案里的名字才会是"先动手的那位"。</p>
     *
     * <p>⚠ {@code getHolderOrThrow} 在"数据包缺了这个伤害类型"时会抛 ——
     * 那正是我们要的行为：宁可当场炸出来，也不要静默退回一个通用文案。
     * 本轮真服务端探针专门跑过一次完整的"被反伤打死 ⇒ 读死亡文案"，就是为了钉住这条链。</p>
     */
    private static DamageSource reflectSource(LivingEntity wearer) {
        Holder<DamageType> type = wearer.level().registryAccess()
                .registryOrThrow(Registries.DAMAGE_TYPE)
                .getHolderOrThrow(VIBRANIUM_REFLECT);
        return new DamageSource(type, wearer);
    }
}
