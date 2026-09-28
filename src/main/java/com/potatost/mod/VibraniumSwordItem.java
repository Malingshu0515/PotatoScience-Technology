package com.potatost.mod;

import java.util.List;

import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.neoforged.neoforge.event.entity.living.MobEffectEvent;

/**
 * 振金剑（0.12 ZF153）。
 *
 * <p><b>用户原话</b>：「加个振金剑材质在素材 无法破坏 拿在手里免疫凋零，缓慢，挖掘疲劳
 * 24点伤害 1.4攻击速度 1附魔权重 shift+右键猛击地面 击飞6x6除自己的所有生物
 * 并对其造成n+12点伤害 n为玩家基础伤害 和4s的失明 4s的缓慢效果 冷却6s」。</p>
 *
 * <h2>七条需求各自落在哪（逐条对账，一个都不许含糊）</h2>
 * <table border="1">
 *   <tr><th>用户的话</th><th>落在哪</th></tr>
 *   <tr><td>材质在素材</td><td>{@code build/用户素材/振金剑_001.png} ⇒ 原字节复制成
 *       {@code textures/item/vibranium_sword.png}（16x16 / 8 位 RGBA，规格本来就对）+
 *       模型 {@code models/item/vibranium_sword.json}（handheld）。身份核实：alpha 掩码与原版
 *       六档**剑**的 IoU 均为 <b>1.0000</b>，而最好的非剑（木锹）只有 0.4271</td></tr>
 *   <tr><td>无法破坏</td><td>物品属性里的 {@code DataComponents.UNBREAKABLE}
 *       —— 与振金套（ZF120）同一个做法。{@code ItemStack.isDamageableItem()} 恒 false ⇒
 *       {@code hurtAndBreak} 整个 no-op：摔落 / 岩浆 / 被砍 / 主动技能都扣不动</td></tr>
 *   <tr><td>拿在手里免疫凋零，缓慢，挖掘疲劳</td><td>{@link #onEffectApplicable}
 *       （源头拦：{@code MobEffectEvent.Applicable} ⇒ {@code DO_NOT_APPLY}）+
 *       {@link #onPlayerTick}（把**已经挂在身上**的立刻抹掉）</td></tr>
 *   <tr><td>24 点伤害</td><td>{@link ModTiers#VIBRANIUM_SWORD_DAMAGE} = 15.0
 *       ⇒ 显示 1 + (15 + 8) = 24.0</td></tr>
 *   <tr><td>1.4 攻击速度</td><td>{@link ModTiers#VIBRANIUM_SWORD_SPEED_MODIFIER} = -2.6
 *       ⇒ 4.0 - 2.6 = 1.4 次/秒</td></tr>
 *   <tr><td>1 附魔权重</td><td>{@link ModTiers#VIBRANIUM_ENCHANTMENT_VALUE} = 1
 *       （{@code TieredItem.getEnchantmentValue()} 直接取档位那一格，物品类不用覆写）</td></tr>
 *   <tr><td>shift+右键猛击地面 … 冷却 6s</td><td>{@link #use} + {@link #slam} +
 *       {@link #SLAM_COOLDOWN_TICKS}（走**原版物品冷却**：快捷栏上那圈灰罩，与斧子/剑同款）</td></tr>
 * </table>
 *
 * <h2>「免疫」为什么挂在"能不能挂上"而不是"每 tick 抹掉"</h2>
 * <p>ZF153 侦察③ 从 sources.jar 逐字读到：{@code LivingEntity.addEffect} 的**第一行**就是</p>
 * <pre>
 *   LivingEntity.java:972
 *     if (!CommonHooks.canMobEffectBeApplied(this, effectInstance, entity)) { return false; }
 * </pre>
 * <p>而这个 hook 里抛的正是 {@code MobEffectEvent.Applicable}（结果枚举是
 * {@code APPLY / DEFAULT / DO_NOT_APPLY}，不是 DENY）。<b>从源头拦</b>的好处是：
 * 凋零那 40 tick 一跳的伤害压根不会发生，而不是"挂上了、下一 tick 我再抹掉"那种
 * 每 tick 都先吃一次判定的写法。</p>
 * <p>两条路**都要**，各管一半：源头那条管"新挂上"，{@link #onPlayerTick} 那条管
 * "我已经中毒/被凋零了，此时才把剑抽出来" —— 玩家那一刻的预期是"拿在手里就该免疫"，
 * 而不是"这口毒你得先受完"。</p>
 * <p>⚠ 覆盖的是**效果**（凋零 / 缓慢 / 挖掘疲劳三条 {@code MobEffects} 条目），
 * 不是"凋灵 boss 这个生物"、也不是"任何名字里带凋零的东西"。用户点名的就是这三个效果。</p>
 *
 * <h2>「猛击地面」这一下的顺序不能换（写反就白推）</h2>
 * <p>原版 {@code LivingEntity.hurt} 自己会推一下：{@code :1253 this.knockback(0.4F, d0, d1)}
 * （侦察③ 抠出来的行号）。所以</p>
 * <pre>
 *   ① target.hurt(...)          ← 掉血；它顺手把目标推了 0.4
 *   ② setDeltaMovement(击飞)     ← **必须在这之后**，否则我的击飞会被 ① 覆盖
 *   ③ addEffect(失明 / 缓慢)     ← 最后给状态（与速度无关，放哪都行，放最后是为了可读）
 * </pre>
 * <p>击飞用 {@code set} 而不是像原版爆炸那样 {@code add}：一来"击飞"是这一下的**主效果**，
 * 不该被目标原有的移动吃掉；二来 {@code set} 的结果是**可断言**的
 * （探针直接验 {@code deltaMovement.y > 0} 与水平方向朝外），{@code add} 就得先算清目标
 * 原有的速度，验起来是一笔糊涂账。</p>
 *
 * <h2>「6x6」与「n」这两个口径</h2>
 * <ul>
 *   <li><b>6x6</b> = 水平以玩家为中心 <b>6×6 格</b>（{@link #SLAM_HALF} = 3.0），
 *       竖直方向上下各 {@link #SLAM_VERTICAL} 格 —— <b>竖直这一半用户没给</b>，
 *       取与水平同一个数（即"6×6×6"，也是原版 {@code AABB.inflate} 最自然的读法）。</li>
 *   <li><b>n</b> = 「玩家基础伤害」= 直接复用 {@link ShockwaveManager#baseAttackDamage(Player)}
 *       —— 那是 ZF133 斧子冲击波「10 + 0.5n」已经过探针的那一份（**不含手持武器/身上装备**，
 *       即属性基础值 1 + 力量之类的玩家自身加成）。空手站着的玩家 n = 1 ⇒ 这一下 **13 点**；
 *       喝了力量 II 就跟着涨。<b>没有另写一份判据</b>（两份 = 以后改一处漏一处）。</li>
 * </ul>
 *
 * <h2>刻意保留的连带后果（写在这里，免得下轮有人当 bug 修）</h2>
 * <ul>
 *   <li>被击飞的目标**落地时会吃摔落伤害**：竖直初速 {@value #SLAM_LAUNCH_UP} 会把人抬到
 *       约 3.8 格高，扣掉原版"头 3 格免伤"那一档大约再吃 1 点上下。这是"击飞"的自然结果，
 *       不是额外写的一条伤害。</li>
 *   <li>伤害走 {@code playerAttack}（与 ZF133 冲击波同一条），所以**照样吃目标的护甲与附魔**，
 *       n+12 是**税前**的数；锋利/火焰附加这类主手附魔**不参与**（没走
 *       {@code Player.attack} 那条路）。</li>
 *   <li>创造模式玩家**整只跳过**（不掉血、不被推、不给状态）：照 ZF133 冲击波那条已经过探针
 *       的口径（用户没说过要打创造模式玩家）。</li>
 *   <li>出手**不扣耐久**：物品是无法破坏的（用户第一条），扣了也没地方扣；用户也没说要代价。</li>
 * </ul>
 */
public class VibraniumSwordItem extends SwordItem {

    /** 猛击**水平**半宽（格）：3.0 ⇒ 6×6 格（用户给的「6x6」）。 */
    public static final double SLAM_HALF = 3.0D;

    /** 猛击**竖直**半高（格）：与水平同数 ⇒ 6×6×6（用户只给了水平那两个数）。 */
    public static final double SLAM_VERTICAL = 3.0D;

    /** 猛击的伤害加成：用户给的 {@code n + 12}。 */
    public static final double SLAM_EXTRA_DAMAGE = 12.0D;

    /** 失明 / 缓慢的时长：4 秒（用户给的）。 */
    public static final int SLAM_EFFECT_TICKS = 20 * 4;

    /** 冷却：6 秒（用户给的）—— 原版物品冷却，快捷栏上看得见那圈灰罩。 */
    public static final int SLAM_COOLDOWN_TICKS = 20 * 6;

    /** 击飞的**向上**初速（格/tick）。用户没给数；0.8 约抬到 3.8 格高，看得见"飞起来"。（见类注释） */
    public static final double SLAM_LAUNCH_UP = 0.8D;

    /** 击飞的**向外**初速（格/tick，水平，方向 = 背离玩家）。同样用户没给数。 */
    public static final double SLAM_LAUNCH_OUT = 0.7D;

    /**
     * 拿在手里免疫的三个效果（用户点名的三个）。
     *
     * <p>写成一张表而不是三个 {@code if}：探针要按这张表逐个验（三条都要"挂不上"，
     * 还要有"空手就挂得上"的灵敏度对照），说明文案也按它写。</p>
     */
    public static final List<Holder<MobEffect>> IMMUNE_EFFECTS =
            List.of(MobEffects.WITHER, MobEffects.MOVEMENT_SLOWDOWN, MobEffects.DIG_SLOWDOWN);

    /** Shift 说明的行数（三行：数值 / 免疫 / 招式）。 */
    private static final int TOOLTIP_LINES = 3;

    /** 说明键前缀（与星璨钢那几把分开，各自一组）。 */
    private static final String TOOLTIP_PREFIX = "tooltip.potato_s_t.vibranium_sword.";

    public VibraniumSwordItem(Item.Properties properties) {
        super(ModTiers.VIBRANIUM_TOOL, properties);
    }

    /**
     * Shift + 右键：猛击地面。
     *
     * <p>三个"不出手"的情形都不进冷却：客户端、没按 Shift、冷却中。写法与斧子 ZF133 /
     * 星璨钢剑 ZF142 的 {@code use} 逐条对齐（那两份都过了真服务端探针）——
     * 客户端只把"用过了"回给动画系统，一切判定都在服务端。</p>
     *
     * <p>⚠ 与斧子/剑那两处**故意不同**的一处：<b>没有耐久检查、也不扣耐久</b> ——
     * 这把剑是无法破坏的（用户第一条），{@code hurtAndBreak} 本来就是个 no-op，
     * 再写一遍"耐久够不够"只会让读的人以为它会坏。</p>
     */
    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) {
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        if (!player.isShiftKeyDown()) {
            return InteractionResultHolder.pass(stack);
        }
        if (player.getCooldowns().isOnCooldown(this)) {
            return InteractionResultHolder.pass(stack);
        }
        if (player instanceof ServerPlayer serverPlayer) {
            slam(serverPlayer);
            player.getCooldowns().addCooldown(this, SLAM_COOLDOWN_TICKS);
            player.swing(hand, true);
        }
        return InteractionResultHolder.sidedSuccess(stack, false);
    }

    /**
     * 猛击一次，返回**被这一下打着几个**（探针拿这个数当判据；正常游戏里没人读它）。
     *
     * <p>顺序见类注释（hurt → 击飞 → 状态）。目标集合 = 以玩家为中心
     * {@code 6×6×6} 的盒子里所有活着的 {@link LivingEntity}，**除自己**（{@code target == player}
     * 直接跳）与创造模式玩家（照 ZF133）。</p>
     *
     * <p>注意 {@code getEntitiesOfClass} 用的是**包围盒相交**：站在你旁边那格、
     * 或者正好在头顶两格的怪都算数 —— 这正是"猛击地面"该有的范围，
     * 而不是"以脚下那一格为圆心画个圆"（那样贴着你的怪反而打不到）。</p>
     */
    public static int slam(ServerPlayer player) {
        ServerLevel level = player.serverLevel();
        AABB box = new AABB(
                player.getX() - SLAM_HALF, player.getY() - SLAM_VERTICAL, player.getZ() - SLAM_HALF,
                player.getX() + SLAM_HALF, player.getY() + SLAM_VERTICAL, player.getZ() + SLAM_HALF);

        // n = 玩家**基础**伤害（不含手持武器）—— 复用 ZF133 已过探针的那一份，不另写
        double n = ShockwaveManager.baseAttackDamage(player);
        float damage = (float) (n + SLAM_EXTRA_DAMAGE);
        DamageSource source = level.damageSources().playerAttack(player);

        int hits = 0;
        for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, box)) {
            if (target == player || !target.isAlive()) {
                continue;
            }
            if (target instanceof Player other && (other.isCreative() || other.isSpectator())) {
                continue;
            }
            if (launch(player, target, source, damage)) {
                hits++;
            }
        }
        render(level, player);
        return hits;
    }

    /**
     * 对**一个**目标结算这一下：掉血 → 击飞 → 失明 + 缓慢。
     *
     * <p>拆成一个方法是为了让探针能"只对一个目标"验（也为了 {@link #slam} 读起来是一段话）。</p>
     *
     * @return 这一次 {@code hurt} 是否真的扣了血（有无敌帧 / 已死 / 免疫时是 false）
     */
    public static boolean launch(ServerPlayer player, LivingEntity target,
                                 DamageSource source, float damage) {
        boolean hurt = target.hurt(source, damage);

        // 击飞：背离玩家的水平方向 + 向上。set 而不是 add（理由见类注释）
        double dx = target.getX() - player.getX();
        double dz = target.getZ() - player.getZ();
        double len = Math.sqrt(dx * dx + dz * dz);
        if (len < 1.0E-4D) {
            // 目标正上/正下方：水平方向退化成零向量 ⇒ 用玩家朝向兜底（与剑气 ZF142 同源）
            double yaw = Math.toRadians(player.getYRot());
            dx = -Math.sin(yaw);
            dz = Math.cos(yaw);
            len = 1.0D;
        }
        dx /= len;
        dz /= len;
        target.setDeltaMovement(dx * SLAM_LAUNCH_OUT, SLAM_LAUNCH_UP, dz * SLAM_LAUNCH_OUT);
        // 这两个字段是"把新速度同步给客户端"的原版开关：hasImpulse 是原版 knockback 用的那个，
        // hurtMarked 是原版挨打/爆炸用的那个（ZF153 侦察③ 从 Entity.java 核实的字段名）
        target.hasImpulse = true;
        target.hurtMarked = true;

        // 失明 + 缓慢各 4 秒（用户给的）。粒子照原版给（visible = true），图标也照原版显示
        target.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, SLAM_EFFECT_TICKS,
                0, false, true, true));
        target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, SLAM_EFFECT_TICKS,
                0, false, true, true));
        return hurt;
    }

    /**
     * 猛击的样子：脚下一圈尘土 + 中心一记闷响 + 一把碎星。
     *
     * <p>全在**服务端**发（{@code ServerLevel.sendParticles} / {@code playSound}）⇒
     * 本工程**不需要**任何客户端代码、不需要自己的数据包与渲染器
     * （与星璨钢剑的剑气同一个便宜）。音效取 **1.21 重锤砸地那一声**
     * （{@code MACE_SMASH_GROUND_HEAVY}，ZF153 侦察③ 核实过常量名与类型是 {@code SoundEvent}）。</p>
     *
     * <p>粒子数是**一次性**的（24 + 1 + 30），不是每 tick 一批 —— 用户在前面几轮反复说过
     * 「不要太卡」。</p>
     */
    private static void render(ServerLevel level, ServerPlayer player) {
        double x = player.getX();
        double y = player.getY();
        double z = player.getZ();
        int ring = 24;
        for (int i = 0; i < ring; i++) {
            double angle = Math.PI * 2.0D * i / ring;
            level.sendParticles(ParticleTypes.CLOUD,
                    x + Math.cos(angle) * SLAM_HALF * 0.9D, y + 0.15D,
                    z + Math.sin(angle) * SLAM_HALF * 0.9D,
                    1, 0.0D, 0.0D, 0.0D, 0.02D);
        }
        level.sendParticles(ParticleTypes.EXPLOSION, x, y + 0.3D, z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        level.sendParticles(ParticleTypes.CRIT, x, y + 0.5D, z, 30,
                SLAM_HALF, 0.4D, SLAM_HALF, 0.35D);
        level.playSound(null, x, y, z, SoundEvents.MACE_SMASH_GROUND_HEAVY,
                SoundSource.PLAYERS, 1.0F, 1.0F);
    }

    /** 手上（主手**或**副手）有没有振金剑 —— "拿在手里"逐字的读法。 */
    public static boolean isHolding(Player player) {
        return player.getMainHandItem().getItem() instanceof VibraniumSwordItem
                || player.getOffhandItem().getItem() instanceof VibraniumSwordItem;
    }

    /**
     * 免疫的**源头**那一半：这三种效果根本挂不上（由 {@code PotatoST} 挂在 game 总线）。
     *
     * <p>客户端也会收到这个事件（效果同步走 {@code forceAddEffect} → 同一个 hook），
     * 而这里只读"手里拿着什么" ⇒ **不区分端**，两端行为天然一致（不会出现"客户端图标闪一下
     * 又消失"）。</p>
     */
    public static void onEffectApplicable(MobEffectEvent.Applicable event) {
        if (!(event.getEntity() instanceof Player player) || !isHolding(player)) {
            return;
        }
        MobEffectInstance effect = event.getEffectInstance();
        for (Holder<MobEffect> immune : IMMUNE_EFFECTS) {
            if (effect.is(immune)) {
                event.setResult(MobEffectEvent.Applicable.Result.DO_NOT_APPLY);
                return;
            }
        }
    }

    /**
     * 免疫的**清理**那一半：拿着剑时，身上已经有的那三种立刻掉（由 {@code PotatoST} 挂在
     * {@code PlayerTickEvent.Post} 上）。
     *
     * <p>{@code isClientSide} 早退与斧子 ZF133 的"手持急迫"同源：只在服务端改，
     * 靠原版的效果同步把结果送给客户端（两端各改一遍只会互相打架）。</p>
     */
    public static void onPlayerTick(Player player) {
        if (player.level().isClientSide()) {
            return;
        }
        if (!isHolding(player)) {
            return;
        }
        for (Holder<MobEffect> immune : IMMUNE_EFFECTS) {
            if (player.hasEffect(immune)) {
                player.removeEffect(immune);
            }
        }
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip,
                                TooltipFlag flag) {
        StarSteelTools.appendHoverText(tooltip, flag, TOOLTIP_PREFIX, TOOLTIP_LINES);
    }
}
