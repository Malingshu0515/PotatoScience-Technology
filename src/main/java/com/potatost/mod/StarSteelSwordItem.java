package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * 星璨钢剑（0.11 ZF141 建、ZF142 加第二个技能）。
 *
 * <p><b>用户原话</b>：ZF141「还有几个星璨钢的工具你自己写一下呗（耐久 挖掘等级 技能...）
 * 剑和斧子差不多强度 其他的略低（要不要技能都无所谓）你参考一下斧子和星璨钢套」；
 * ZF142「剑你看看能不能再加个特殊技能」。</p>
 *
 * <h2>数值（与斧子摆在一起看）</h2>
 * <pre>
 *   斧（ZF133，一个字没动）  17.0 伤害 @ 0.9 次/秒 = 15.3 DPS  + 冲击波 / 急迫 / 夜晚免耐久
 *   剑（ZF141/142）          16.0 伤害 @ 1.6 次/秒 = 25.6 DPS  + 星辉斩 / 夜晚免耐久
 *   锹（ZF142）              13.5 伤害 @ 1.0 次/秒 = 13.5 DPS
 *   镐（ZF141）              13.0 伤害 @ 1.2 次/秒 = 15.6 DPS
 *   锄（ZF141）              12.0 伤害 @ 1.0 次/秒 = 12.0 DPS
 * </pre>
 * <p>「剑和斧子差不多强度」落在**每击只差 1 点**上；算式 {@code 1 + (参数 + 档位加成 8)}
 * ⇒ {@link ModTiers#STAR_STEEL_SWORD_DAMAGE} = 7.0 得 16.0。</p>
 *
 * <h2>技能①「与夜同频」（ZF141）</h2>
 * <p>夜晚（主世界 13000~23000）**采掘与攻击都不消耗耐久**。剑这两个入口都真的会磨：
 * 攻击每击 1 点（{@code SwordItem.postHurtEnemy}）、采掘每方块 2 点（剑的
 * {@code damagePerBlock = 2}）—— 源码依据见 {@link StarSteelTools} 的类注释。</p>
 *
 * <h2>技能②「星辉斩」（ZF142，Shift + 右键）</h2>
 * <p>朝面部斩出一道**星辉剑气**：长约 {@value #SLASH_RANGE} 格、宽 {@value #SLASH_HALF_WIDTH}
 * 格、高 {@value #SLASH_HALF_HEIGHT} 格（都是**半**宽/半高，即中心线两侧各这么远），
 * 贯穿沿途**所有**敌人，各受 {@value #SLASH_DAMAGE} 点伤害并被星辉照亮
 * {@value #SLASH_GLOW_TICKS} tick（5 秒）。出手代价 {@value #SLASH_COST} 点耐久、
 * 冷却 {@code 15} 秒 —— 与斧子的冲击波同一套节奏（斧子扣 120，剑轻一些扣 100）。</p>
 *
 * <p><b>为什么"剑气"直接扫一次、而不是像斧子那样每 tick 推进的波</b>：斧子那道波要**拆方块**
 * （沿途砍树），所以必须一格一格推进、要处理"撞墙即停"与"10 秒没碰到木头就散"；
 * 剑气只是**一瞬间**打一条走廊，扫一次就够了 —— 少一整套状态机、少一个每 tick 的监听、
 * 也少一份"退场清理"的账。**这不是省事，是两道技能本来就该长得不一样。**</p>
 *
 * <p><b>几何判据用"走廊坐标"而不是"逐格采样"</b>：把目标位置投影到
 * 「朝向（{@code dx,dz}）+ 它的法线（{@code nx,nz}）」这组基上，
 * 沿线距离落在 {@code [0.5, 8]}、横向 |偏移| ≤ 1.5、纵向 |Δy| ≤ 1.5 就算命中。
 * 不遍历格子就不会"同一个目标被数两次"，也不用管"斜着放"（法线一算就是任意角度，
 * 与斧子 ZF134 把冲击波从"正东南西北"改成任意角度同一条账）。</p>
 *
 * <p><b>隔着墙打不到</b>：每个候选目标都从**眼睛**到它**身体中段**做一次原版
 * {@code level.clip(...)} 射线；被方块挡住就跳过。这条用的是原版自己的射线，
 * 不手写几何（手写的那份最容易与"我以为的"不一致 —— §4.135 的同族）。</p>
 *
 * <p><b>伤害类型是本工程第二个自定义的</b>（{@code potato_s_t:star_steel_slash}）：
 * 死在这一下的人，文案是「%1$s被星光贯穿」（{@code %1$s} 按原版规则是**受害者**）。
 * 拿在手里的这 12 点**不是**通用伤害 —— 它走自己的数据包条目，所以以后要给"剑气"加规则
 * （比如无视护甲）只要改那一个 JSON 与这里的一行。</p>
 */
public class StarSteelSwordItem extends SwordItem {

    /** 星辉斩的出手代价（耐久）。斧子的冲击波是 120，剑轻一些。 */
    public static final int SLASH_COST = 100;

    /** 星辉斩的冷却：15 秒（与斧子同一个节奏）。用原版物品冷却（快捷栏上那圈灰罩）。 */
    public static final int SLASH_COOLDOWN_TICKS = 20 * 15;

    /** 剑气对每个命中者造成的伤害（点）。 */
    public static final float SLASH_DAMAGE = 12.0F;

    /** 剑气的长度（格，沿朝向）。 */
    public static final double SLASH_RANGE = 8.0D;

    /** 剑气的**半**宽（格，中心线两侧各这么远 ⇒ 实际宽 3 格）。 */
    public static final double SLASH_HALF_WIDTH = 1.5D;

    /** 剑气的**半**高（格 ⇒ 实际高 3 格）。 */
    public static final double SLASH_HALF_HEIGHT = 1.5D;

    /**
     * 目标必须落在朝向的**正前方多远之外**才算命中（0.5 格）。
     *
     * <p>没有这条的话，"站在你身上/身后的怪"也会被算进走廊 —— 而"身后的敌人被前方的斩击打到"
     * 是玩家一眼就能看出来的错。探针里有专门的负向对照（同一个目标放到身后 ⇒ 必须 0 伤害）。</p>
     */
    public static final double SLASH_MIN_ALONG = 0.5D;

    /** 命中后给目标的发光时长（tick）：100 = 5 秒。 */
    public static final int SLASH_GLOW_TICKS = 100;

    /** Shift 说明的行数（三行：与夜同频 / 怎么放 / 打什么）。 */
    private static final int TOOLTIP_LINES = 3;

    /** 剑自己的说明键前缀（与锹/镐/锄共用的那句分开了 —— 它有第二个技能）。 */
    private static final String TOOLTIP_PREFIX = "tooltip.potato_s_t.star_steel_sword.";

    /**
     * 剑气用的伤害类型（数据包注册表 {@code Registries.DAMAGE_TYPE}，**不是**
     * {@code DeferredRegister} 的东西）—— 与振金反伤同一个做法，
     * 运行时从 {@code level.registryAccess()} 取，见 {@link #slashSource}。
     */
    public static final ResourceKey<DamageType> STAR_STEEL_SLASH =
            ResourceKey.create(Registries.DAMAGE_TYPE,
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "star_steel_slash"));

    public StarSteelSwordItem(Item.Properties properties) {
        super(ModTiers.STAR_STEEL_TOOL, properties);
    }

    /** 夜晚采掘不磨损；白天**原样**走原版（含 damagePerBlock = 2 那条）。 */
    @Override
    public boolean mineBlock(ItemStack stack, Level level, BlockState state, BlockPos pos, LivingEntity entity) {
        if (StarSteelTools.isNightWearFree(level)) {
            return StarSteelTools.nightMineBlockResult(stack);
        }
        return super.mineBlock(stack, level, state, pos, entity);
    }

    /** 夜晚攻击不磨损；白天**原样**走原版（每击 1 点）。 */
    @Override
    public void postHurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
        if (StarSteelTools.isNightWearFree(attacker.level())) {
            return;
        }
        super.postHurtEnemy(stack, target, attacker);
    }

    /**
     * Shift + 右键：星辉斩。
     *
     * <p>四个"不出手"的情形都不扣耐久、不进冷却：客户端、没按 Shift、冷却中、耐久不够一次
     * {@value #SLASH_COST}。出手那一下扣满耐久（{@code hurtAndBreak} 与原版一样吃耐久附魔、
     * 扣穿了会正常爆掉并走 {@code onBroken}），然后交给 {@link #slash}。</p>
     *
     * <p>⚠ 写着法与斧子 ZF133 的 {@code use} 逐条对齐（那是已经过探针的那一份）：
     * 客户端只把"用过了"回给动画系统，一切判定都在服务端。</p>
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
        if (stack.getMaxDamage() - stack.getDamageValue() < SLASH_COST) {
            return InteractionResultHolder.fail(stack);
        }
        if (player instanceof ServerPlayer serverPlayer) {
            EquipmentSlot slot = hand == InteractionHand.MAIN_HAND
                    ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND;
            stack.hurtAndBreak(SLASH_COST, serverPlayer, slot);
            slash(serverPlayer);
            player.getCooldowns().addCooldown(this, SLASH_COOLDOWN_TICKS);
            player.swing(hand, true);
        }
        return InteractionResultHolder.sidedSuccess(stack, false);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        StarSteelTools.appendHoverText(tooltip, flag, TOOLTIP_PREFIX, TOOLTIP_LINES);
    }

    /**
     * 放一次星辉斩，返回**打到几个**（探针拿这个数当判据；正常游戏里没人读它）。
     *
     * <p>朝向取 {@code getLookAngle()} 的**水平投影**并归一化；视线完全垂直（俯视/仰视）时
     * 水平投影退化成零向量 ⇒ 用 yaw 兜底（与斧子 ZF134 那条同源）。</p>
     */
    public static int slash(ServerPlayer player) {
        ServerLevel level = player.serverLevel();
        Vec3 look = player.getLookAngle();
        double dx = look.x;
        double dz = look.z;
        double len = Math.sqrt(dx * dx + dz * dz);
        if (len < 1.0E-4D) {
            double yaw = Math.toRadians(player.getYRot());
            dx = -Math.sin(yaw);
            dz = Math.cos(yaw);
            len = 1.0D;
        }
        dx /= len;
        dz /= len;
        double nx = -dz;
        double nz = dx;

        DamageSource source = slashSource(player);
        int hits = 0;
        for (Entity entity : level.getEntities(player, player.getBoundingBox().inflate(SLASH_RANGE))) {
            if (!(entity instanceof LivingEntity target) || !target.isAlive()) {
                continue;
            }
            Vec3 delta = target.position().subtract(player.position());
            double along = delta.x * dx + delta.z * dz;
            double lateral = delta.x * nx + delta.z * nz;
            if (along < SLASH_MIN_ALONG || along > SLASH_RANGE) {
                continue;
            }
            if (Math.abs(lateral) > SLASH_HALF_WIDTH || Math.abs(delta.y) > SLASH_HALF_HEIGHT) {
                continue;
            }
            if (isBehindWall(level, player, target)) {
                continue;
            }
            if (target.hurt(source, SLASH_DAMAGE)) {
                target.addEffect(new MobEffectInstance(MobEffects.GLOWING, SLASH_GLOW_TICKS,
                        0, false, false, true));
                hits++;
            }
        }
        render(level, player, dx, dz, nx, nz);
        return hits;
    }

    /** 从眼睛到目标身体中段的原版射线：被方块挡住就够不着。 */
    private static boolean isBehindWall(ServerLevel level, ServerPlayer player, LivingEntity target) {
        Vec3 from = player.getEyePosition();
        Vec3 to = target.position().add(0.0D, target.getBbHeight() * 0.5D, 0.0D);
        BlockHitResult hit = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, player));
        return hit.getType() != HitResult.Type.MISS;
    }

    /**
     * 剑气的样子：沿走廊撒 {@code END_ROD} 粒子 + 一声三叉戟投掷。
     *
     * <p>全在**服务端**发（{@code ServerLevel.sendParticles} / {@code playSound}）⇒
     * 本工程**不需要**任何客户端代码，也不需要自己的数据包与渲染器 ——
     * 这正是"扫一次"这个设计带来的便宜。粒子每格发一次（共 8 次），
     * 不是每 tick 发（斧子那条是每 2 tick 一批，因为它要活 200 tick）。</p>
     */
    private static void render(ServerLevel level, ServerPlayer player,
                               double dx, double dz, double nx, double nz) {
        for (int step = 1; step <= (int) SLASH_RANGE; step++) {
            level.sendParticles(ParticleTypes.END_ROD,
                    player.getX() + dx * step, player.getY() + 1.0D, player.getZ() + dz * step,
                    3, nx * SLASH_HALF_WIDTH, 0.4D, nz * SLASH_HALF_WIDTH, 0.0D);
        }
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.TRIDENT_THROW.value(), SoundSource.PLAYERS);
    }

    /**
     * 剑气伤害来源：**以玩家为来源实体** ⇒ 击杀照常算玩家的（掉落 / 经验 / 进度都走原版那条路），
     * 但伤害类型是我们自己的数据包条目（换文案、以后也好加规则）。
     *
     * <p>⚠ {@code getHolderOrThrow} 在"数据包缺了这个伤害类型"时会抛 —— 那正是要的行为：
     * 宁可当场炸出来，也不要静默退回一个通用文案（与振金反伤同一条口径）。</p>
     */
    private static DamageSource slashSource(ServerPlayer player) {
        Holder<DamageType> type = player.level().registryAccess()
                .registryOrThrow(Registries.DAMAGE_TYPE)
                .getHolderOrThrow(STAR_STEEL_SLASH);
        return new DamageSource(type, player);
    }
}
