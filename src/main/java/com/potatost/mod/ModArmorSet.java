package com.potatost.mod;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/**
 * 星璨钢套的**套装效果**（0.11 ZF103）。
 *
 * <p>用户原话逐条落地（判定口径本轮已向用户确认：<b>效果须满套装</b>、
 * <b>耐久夜晚不消耗</b>、<b>虚空优先找方块、找不到就换位</b>）：</p>
 *
 * <table border="1">
 *   <caption>数值表</caption>
 *   <tr><th>条件</th><th>效果</th></tr>
 *   <tr><td>每件（不要求满套）</td><td>夜晚获得抗性提升 I —— 多件同时生效也只有 I（见下面的"不可叠加"）</td></tr>
 *   <tr><td>每件（不要求满套）</td><td>夜晚装备耐久不消耗（落在 {@link ModArmorPiece#damageItem}）</td></tr>
 *   <tr><td><b>只头盔</b>（ZF135 加的那条）</td><td>夜视 I，每次 4 s、穿着就一直续（不分昼夜与维度）</td></tr>
 *   <tr><td>满套 · 主世界 · 夜晚</td><td>力量 I、抗性提升 II；每 45 s 给一次 10 s 的伤害吸收 III</td></tr>
 *   <tr><td>满套 · 末地</td><td>生命恢复 I、抗性提升 III、力量 II；每 15 s 给一次 12 s 的伤害吸收 VI</td></tr>
 *   <tr><td>满套 · 受到虚空伤害</td><td>传送到 20×20（Y 轴不限）内最近的实心方块上；找不到就与最近的生物交换位置</td></tr>
 * </table>
 *
 * <p><b>「不可叠加」怎么落地的</b>：不是"多件就升到 II"，而是
 * <b>只在身上没有该效果（或它快过期）时才补一次</b>。四件同时触发也只会补出 I；
 * 补的时候也<b>不覆盖更高级别</b>（身上已有抗性 III 时不会被压回 I，
 * 判据是 {@code getAmplifier() >= 目标等级}）。</p>
 *
 * <p><b>「每 45 s」/「每 15 s」怎么落地的</b>：不自己存计时器（存档要序列化、多人要分表，
 * 都是新雷）。做法是"效果没了就再给一次"，把周期交给效果自身的持续时间：
 * 主世界给 {@code 10 s 时长 + 35 s 冷却} ⇒ 从第一次给上开始每 45 s 一次；
 * 末地给 {@code 12 s 时长 + 3 s 冷却} ⇒ 每 15 s 一次。数字都写在常量里，改平衡只动常量。</p>
 *
 * <p><b>「装备耐久不消耗」为什么不在这里判</b>：耐久是在 {@code ItemStack.hurtAndBreak} 里扣的，
 * 那边只认 {@code Item.damageItem(...)}，所以规则落在 {@link ModArmorPiece}；
 * 本类只管效果与传送。</p>
 *
 * <p><b>虚空那一刀为什么挂在「伤害之后」</b>：结算分两段 ——
 * 第一段判无敌帧/免疫，第二段才真正结算（护甲、附魔、吸收）。
 * 挂在 {@link LivingDamageEvent.Post} 上意味着"这一下确实落到身上了"才救，
 * 被无敌帧挡下的那一下不会白传送；挂在"伤害之前"那个事件上则连"其实没打中"也会触发。</p>
 *
 * <p><b>⚠ 本轮唯一由我定死、用户没给的一处</b>：虚空伤害的<b>触发判定</b>用
 * {@code DamageTypes.FELL_OUT_OF_WORLD}（{@code minecraft:out_of_world}）——
 * 这就是原版虚空伤害的类型 id（本轮从 {@code DamageTypes.java:22} 核实）。
 * 用户原话里的三种处理按<b>顺序</b>读：先找方块，找不到换位；
 * 第三种「每件装备消耗 999 点耐久」本轮<b>故意不实现</b>（用户已明确"耐久夜晚不消耗"，
 * 且本轮确认口径为"优先找方块、找不到就换位"），理由记在
 * {@code docs/开发档案.md} 的 ZF103 条目里。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class ModArmorSet {

    /** 抗性提升 I / II / III 的 amplifier（0 / 1 / 2）。 */
    private static final int RESISTANCE_I = 0;
    private static final int RESISTANCE_II = 1;
    private static final int RESISTANCE_III = 2;

    /** 夜晚持续类效果的补充时长（tick）：320 = 16 s，够撑到"自然结束前 2 s"再补。 */
    private static final int NIGHT_EFFECT_TICKS = 320;

    /**
     * 星璨钢**头盔**给的夜视时长（tick）：80 = **4 s**（用户原话「星璨钢头盔穿戴加个夜视效果 1级 4s」）。
     *
     * <p>口径与上面那些"持续型"效果完全一样：**给短时长、到点再续**，而不是给一个很长的时长。
     * 好处是"摘下头盔"不需要写任何清理代码 —— 最后一次给的那 4 s 到点自己就没了
     * （所以摘头盔后最多再亮 4 s，这与用户给的"4s"同时是**单次时长**和**退场时间**）。</p>
     *
     * <p>补充余量用 {@link #KNOCKBACK_MARGIN}（2 s）：80 tick 的效果在剩 40 tick 时被续上，
     * ⇒ 穿着期间**永远不会断**（效果一旦断一帧，客户端就会闪一下黑，那是夜视最刺眼的毛病）。</p>
     */
    private static final int HELMET_NIGHT_VISION_TICKS = 80;

    /** 夜视 I 的 amplifier（0 = I 级）。 */
    private static final int NIGHT_VISION_I = 0;

    /** 主世界：伤害吸收 III，每次 10 s（用户给的数 ⇒ 200 tick）。 */
    private static final int OVERWORLD_ABSORPTION_TICKS = 200;
    private static final int OVERWORLD_ABSORPTION_AMPLIFIER = 2;

    /** 末地：伤害吸收 VI，每次 12 s（用户给的数 ⇒ 240 tick）。 */
    private static final int END_ABSORPTION_TICKS = 240;
    private static final int END_ABSORPTION_AMPLIFIER = 5;

    /** 剩余时长低于这个值就视为"该补了"（tick）：40 = 2 s。 */
    private static final int REFRESH_MARGIN = 40;

    /**
     * **持续型**效果（抗性/力量/恢复）的补充阈值（tick）：40 = 2 s。
     *
     * <p>提前 2 s 续上 ⇒ 玩家**察觉不到断档**（这些效果没有"会用完"的量，连续才合理）。</p>
     */
    private static final int KNOCKBACK_MARGIN = REFRESH_MARGIN;

    /**
     * **伤害吸收**的补充阈值（tick）：**0 ⇒ 必须等它彻底结束才给下一次**。
     *
     * <p>用户原话：「没有伤害吸收效果不需要立即重置 末地15s给12伤害吸收 晚上45秒才给10s是为了平衡
     * 护盾不要立马就恢复」。</p>
     *
     * <p>原先用的是 {@link #KNOCKBACK_MARGIN}（剩余 &lt; 2 s 就续）⇒ 护盾**还没扣完就被补满**，
     * 等于"永久满护盾"，把那 3 s / 35 s 的空窗全吃掉了 —— 而那段空窗**就是平衡点本身**
     * （末地 15 s 给 12 s、主世界 45 s 给 10 s）。改成 0 之后，效果一到期立刻给下一条，
     * 周期恢复成用户要的 15 s / 45 s，护盾该破的时候就会破。</p>
     */
    private static final int ABSORPTION_REFRESH = 0;

    /** 虚空传送的搜索半径：用户原话「20x20」⇒ ±10 格。 */
    private static final int SEARCH_RADIUS = 10;

    /** 找落点时，方块上方要留出的净空高度（玩家 1.8 格高 ⇒ 2 格）。 */
    private static final int CLEARANCE = 2;

    /** 与最近的生物交换位置时，搜索半径（格）。 */
    private static final int SWAP_RADIUS = 16;

    /**
     * 虚空传送前给的缓降时长（tick）：940 = 47 s。
     *
     * <p>够从世界顶落到世界底（约 384 格，缓降速度下约 28 s），到期时人早已落地。</p>
     */
    private static final int SLOW_FALLING_TICKS = 940;


    private ModArmorSet() {
    }

    // ============================================================
    //  ① 玩家每 tick：夜晚抗性 I（每件）+ 套装效果
    // ============================================================

    /**
     * 服务端玩家每 tick 结算一次效果。
     *
     * <p>只挂 {@code PlayerTickEvent.Post}：效果不需要抢在别的逻辑之前算。</p>
     */
    @SubscribeEvent
    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        ServerLevel level = player.serverLevel();

        // ---- 每件：夜晚抗性提升 I（不叠加）----
        if (level.isNight() && ModArmorMaterials.hasAnyStarSteelPiece(player)) {
            ensure(player, MobEffects.DAMAGE_RESISTANCE, RESISTANCE_I, NIGHT_EFFECT_TICKS, KNOCKBACK_MARGIN);
        }

        // ---- 只头盔：夜视 I（4 s，穿着就一直续）----
        // ⚠ 这一条**不挑昼夜、不挑维度**：用户说的是"穿戴就有"，没提夜晚 ——
        //   上面那条抗性才是"夜晚限定"。别顺手给它加 `level.isNight()` 的门（那会把白天的地洞变黑）。
        if (ModArmorMaterials.hasStarSteelHelmet(player)) {
            ensure(player, MobEffects.NIGHT_VISION, NIGHT_VISION_I, HELMET_NIGHT_VISION_TICKS,
                    KNOCKBACK_MARGIN);
        }

        // ---- 满套 ----
        if (!ModArmorMaterials.hasFullStarSteelSet(player)) {
            return;
        }
        if (level.dimension() == Level.END) {
            // 末地：恢复 I + 抗性 III + 力量 II 持续；吸收 VI **每 15 s 给一次、每次 12 s**
            ensure(player, MobEffects.REGENERATION, 0, NIGHT_EFFECT_TICKS, KNOCKBACK_MARGIN);
            ensure(player, MobEffects.DAMAGE_RESISTANCE, RESISTANCE_III, NIGHT_EFFECT_TICKS, KNOCKBACK_MARGIN);
            ensure(player, MobEffects.DAMAGE_BOOST, 1, NIGHT_EFFECT_TICKS, KNOCKBACK_MARGIN);
            ensure(player, MobEffects.ABSORPTION, END_ABSORPTION_AMPLIFIER, END_ABSORPTION_TICKS,
                    ABSORPTION_REFRESH);
        } else if (level.dimension() == Level.OVERWORLD && level.isNight()) {
            // 主世界·夜晚：力量 I + 抗性 II 持续；吸收 III **每 45 s 给一次、每次 10 s**
            ensure(player, MobEffects.DAMAGE_BOOST, 0, NIGHT_EFFECT_TICKS, KNOCKBACK_MARGIN);
            ensure(player, MobEffects.DAMAGE_RESISTANCE, RESISTANCE_II, NIGHT_EFFECT_TICKS, KNOCKBACK_MARGIN);
            ensure(player, MobEffects.ABSORPTION, OVERWORLD_ABSORPTION_AMPLIFIER, OVERWORLD_ABSORPTION_TICKS,
                    ABSORPTION_REFRESH);
        }
    }

    /**
     * 夜间默认补一次效果：身上没有、或快过期、或等级不够时才补。
     *
     * <p>{@code ambient = true} ⇒ 粒子更淡（套装给的效果不该像药水那样糊住屏幕）；
     * {@code visible = true} ⇒ 图标照常显示，玩家看得见身上有什么。</p>
     *
     * @param refreshMargin 剩余时长低于这个值就视为"该补了"（tick）。
     *                      见 {@link #KNOCKBACK_MARGIN} 与 {@link #ABSORPTION_REFRESH} 的区别。
     */
    private static void ensure(ServerPlayer player, Holder<MobEffect> effect,
                               int amplifier, int durationTicks, int refreshMargin) {
        MobEffectInstance current = player.getEffect(effect);
        if (current != null && current.getAmplifier() >= amplifier
                && current.getDuration() > refreshMargin) {
            return;
        }
        player.addEffect(new MobEffectInstance(effect, durationTicks, amplifier, true, true));
    }

    // 「四件都是星璨钢 / 至少一件 / 判材料」这三个判据已搬去
    // {@link ModArmorMaterials#hasFullStarSteelSet} —— 因为 {@link ModArmorPiece} 也要用
    // （末地永久不掉耐久那条），而它不该认识"套装效果"这个类。这里只留调用。

    // ============================================================
    //  ② 受到虚空伤害：先找方块，找不到就与最近的生物换位
    // ============================================================

    /**
     * 虚空伤害落地之后：满套才有救。
     *
     * <p>这里不改伤害值 —— 该吃的伤害照吃，救的是"接下来掉进虚空"这件事。</p>
     */
    @SubscribeEvent
    public static void onLivingDamaged(LivingDamageEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        if (!event.getSource().is(DamageTypes.FELL_OUT_OF_WORLD)) {
            return;
        }
        if (!ModArmorMaterials.hasFullStarSteelSet(player)) {
            return;
        }
        rescueFromVoid(player);
    }

    /**
     * 虚空救援：20×20、Y 轴不限，找最近的实心方块传送；找不到就与最近的生物交换位置。
     *
     * <p>两个出口都会留下可观察的结果（传送音 + 物品栏上方的提示），
     * 不会出现"悄悄地什么都没发生"。</p>
     */
    private static void rescueFromVoid(ServerPlayer player) {
        BlockPos landing = findLanding(player);
        if (landing != null) {
            // ⚠ **先给缓降、再传送**（用户原话：「传送之前加个缓降还是什么免除一下摔落伤害
            //    要不然就摔死了」）。落点可能是世界顶附近（Y 轴不限 ⇒ 往上 320 格也可能中选），
            //    没有缓降就是 300+ 格自由落体 ⇒ 必死。所以这一句必须在 teleportTo 之前。
            preventFallDamage(player);
            player.teleportTo(player.serverLevel(), landing.getX() + 0.5, landing.getY(), landing.getZ() + 0.5,
                    Set.of(), player.getYRot(), player.getXRot());
            player.serverLevel().playSound(null, landing, SoundEvents.ENDERMAN_TELEPORT,
                    SoundSource.PLAYERS, 0.7F, 1.4F);
            player.displayClientMessage(Component.translatable("message.potato_s_t.star_steel_void_block"), true);
            return;
        }
        if (swapWithNearestEntity(player)) {
            player.displayClientMessage(Component.translatable("message.potato_s_t.star_steel_void_swap"), true);
        } else {
            player.displayClientMessage(Component.translatable("message.potato_s_t.star_steel_void_failed"), true);
        }
    }

    /**
     * 免除摔落伤害：**清空已累积的坠落距离** + 给一段缓降。
     *
     * <p>两条一起做，因为它们各挡一半：</p>
     * <ul>
     *   <li>{@link LivingEntity#resetFallDistance()}（⇒ {@code fallDistance = 0}）——
     *       挡的是"掉进虚空时**已经攒下**的那段坠落距离"。玩家是掉到 Y&lt;-64 才吃虚空伤害的，
     *       那时 {@code fallDistance} 早就很大了，不归零的话传送到落点一落地照样结算一大笔。</li>
     *   <li>{@link MobEffects#SLOW_FALLING}（缓降）—— 挡的是"传送到高处之后**接下来**的坠落"。
     *       缓降让 `checkFallDamage` 里那个 `if (this.fallDistance > 0)` 分支
     *       （见 {@code LivingEntity.checkFallDamage}）永远不成立 ⇒ 落地也不结算。</li>
     * </ul>
     *
     * <p>时长 {@link #SLOW_FALLING_TICKS} = 940 tick（47 s）：从世界顶落到世界底
     * （约 384 格）按缓降速度要 ~28 s，留足余量。效果到期时人早就落地了 ——
     * 所以**不需要**手动移除（少一处状态要清，就少一个能出 bug 的地方）。</p>
     */
    private static void preventFallDamage(ServerPlayer player) {
        player.resetFallDistance();
        player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING,
                SLOW_FALLING_TICKS, 0, false, false));
    }

    /**
     * 找落点：以玩家为中心 ±{@link #SEARCH_RADIUS} 格、Y 轴从世界底扫到世界顶，
     * 取"最近的实心方块、且它上方有净空"的那一格。
     *
     * <p>排序口径：先按 Y 的高度差（近的优先），同高再按水平距离。</p>
     *
     * <p><b>两个易错点</b>：① 用 {@code immutable()} 存下来 —— 可变 {@code BlockPos}
     * 在循环里被复用，直接收集会得到一堆"同一个坐标"（档案 §4.59 同款雷）；
     * ② 未加载的区块读出来全是空气，会把它误判成"脚下没方块"，所以先问 {@code isLoaded}。</p>
     *
     * @return 可站立位置（脚所在格）的坐标；一处都没有则 {@code null}
     */
    private static BlockPos findLanding(ServerPlayer player) {
        ServerLevel level = player.serverLevel();
        BlockPos origin = player.blockPosition();
        List<BlockPos> candidates = new ArrayList<>();
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int dx = -SEARCH_RADIUS; dx <= SEARCH_RADIUS; dx++) {
            for (int dz = -SEARCH_RADIUS; dz <= SEARCH_RADIUS; dz++) {
                int x = origin.getX() + dx;
                int z = origin.getZ() + dz;
                for (int y = level.getMinBuildHeight(); y < level.getMaxBuildHeight() - CLEARANCE; y++) {
                    cursor.set(x, y, z);
                    if (!level.isLoaded(cursor)) {
                        continue;
                    }
                    if (isStandable(level, cursor)) {
                        candidates.add(cursor.immutable());
                        break;
                    }
                }
            }
        }
        if (candidates.isEmpty()) {
            return null;
        }
        return candidates.stream().min(Comparator
                .comparingInt((BlockPos pos) -> Math.abs(pos.getY() - origin.getY()))
                .thenComparingInt(pos -> pos.distManhattan(origin))).orElse(null);
    }

    /** 这一格能不能站：脚下是实心、脚与头两格无碰撞。 */
    private static boolean isStandable(ServerLevel level, BlockPos pos) {
        BlockPos below = pos.below();
        BlockState state = level.getBlockState(below);
        if (state.isAir() || !state.isFaceSturdy(level, below, Direction.UP)) {
            return false;
        }
        return level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()
                && level.getBlockState(pos.above()).getCollisionShape(level, pos.above()).isEmpty();
    }

    /**
     * 与最近的生物交换位置。
     *
     * <p>交换，不是"单方面传过去"：两边都换位置才算"交换位置"。
     * 两边都用 {@code randomTeleport(..., broadcastTeleport = true)} ——
     * 它自己会往下找地面、查碰撞与液体，失败就退回原位并返回 {@code false}，
     * 比手写一套"先落地再传送"稳。
     * 因此<b>顺序很重要</b>：先把生物挪到玩家原位（这时玩家还在原位，生物的落点一定安全），
     * 再把玩家挪到生物原位。</p>
     *
     * <p>排除项：玩家自己、已被骑乘的实体（挪了会把骑手一起带走）、
     * 已经死掉/被移除的实体。不排除敌对生物 —— 用户的"附近的一个生物"没有敌我限定。</p>
     */
    private static boolean swapWithNearestEntity(ServerPlayer player) {
        AABB box = player.getBoundingBox().inflate(SWAP_RADIUS);
        List<LivingEntity> nearby = player.serverLevel().getEntitiesOfClass(LivingEntity.class, box,
                e -> e != player && !e.isPassenger() && !e.isRemoved() && e.isAlive());
        LivingEntity nearest = nearby.stream()
                .min(Comparator.comparingDouble(player::distanceToSqr)).orElse(null);
        if (nearest == null) {
            return false;
        }
        double fromX = player.getX();
        double fromY = player.getY();
        double fromZ = player.getZ();
        double toX = nearest.getX();
        double toY = nearest.getY();
        double toZ = nearest.getZ();
        if (!nearest.randomTeleport(fromX, fromY, fromZ, true)) {
            return false;
        }
        boolean moved = player.randomTeleport(toX, toY, toZ, true);
        player.serverLevel().playSound(null, player.blockPosition(), SoundEvents.ENDERMAN_TELEPORT,
                SoundSource.PLAYERS, 0.7F, 0.8F);
        return moved;
    }
}
