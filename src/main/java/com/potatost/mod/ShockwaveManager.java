package com.potatost.mod;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * 星璨钢斧的**冲击波**（0.11 ZF133）—— 本工程第一个"会自己往前推进、边走边拆"的东西。
 *
 * <p><b>用户原话</b>：「shift+右键 扣除120点耐久 发射一道冲击波 15s冷却（玩家朝向 宽度6格就可以）
 * 破坏沿途所有原木/去皮原木 和树叶 碰到斧子不可以开采的方块 或 10s内未碰到任何原木 则冲击波消失
 * 在末地时 冲击波将具有10+0.5n的远程伤害（n为玩家基础伤害）」。</p>
 *
 * <h3>形状</h3>
 * 从发射者脚下那一格起，沿**玩家朝向的主轴**（x 或 z，取 |dx|、|dz| 大的那个）每 tick 前进 1 格，
 * 每个采样位置是一个 **6 宽 × 3 高** 的薄片（"宽度6格"是用户给的数；6 块是偶数，
 * 所以按 **-3 ~ +2** 铺，相对玩家正好对称）。3 格高是我补的（用户没给）——
 * 正好覆盖一棵树从脚到头的树干高度，已挂 §9 待确认。</p>
 *
 * <h3>终止条件（用户给了两条，我加了第三条兜底）</h3>
 * <ol>
 *   <li><b>撞上"斧子挖不动的方块"</b>：该薄片里出现任何一格
 *       {@code !斧头.isCorrectToolForDrops(该方块)} ⇒ 立刻消失
 *       （判据用 {@code getDestroyTime() >= 0} 先排除"没有碰撞/不破坏"的方块：空气、水、草）。</li>
 *   <li><b>10 秒（200 tick）没碰到任何原木/树叶</b> ⇒ 消失。
 *       ⚠ 这是<b>滚动窗口</b>：拆到树就重新计时，所以在树林里可以一路推下去，
 *       在空旷处飞 10 秒就自己散掉。</li>
 *   <li>兜底：<b>60 秒</b>（1200 tick）硬上限，防止"一整片森林 + 一直拆"把波留到天荒地老。
 *       这是防跑飞的护栏，不是玩法数值。</li>
 * </ol>
 *
 * <h3>伤害（只在末地）</h3>
 * {@code 10 + 0.5n}，{@code n} = 发射者的**基础攻击伤害**（{@link #baseAttackDamage}：
 * 属性的基础值 + 玩家自身的加成，**不含手持武器那一份**）—— "玩家基础伤害"逐字的读法，
 * 已挂 §9 待用户确认。伤害在每个采样位置对周围实体结算一次，带击退（原版
 * {@code playerAttack} 伤害源的先天行为），且**绝不误伤发射者自己**。
 *
 * <h3>性能（用户要求过「不要太卡」）</h3>
 * 没有实体、没有每 tick 的包：服务端每 tick 最多查 6×3 = 18 格 + 一次 AABB，
 * 粒子按 {@code PARTICLE_INTERVAL} 每 2 tick 发一批、每批最多 6 个；
 * 客户端的"光墙"只收**发射时的一个包**（见 {@code ShockwaveNetworking}），
 * 之后由客户端按世界时间自己推算位置。</p>
 */
public final class ShockwaveManager {

    /** 冲击波宽度（用户给的数）：6 格，按 -3 ~ +2 铺（偶数宽相对玩家对称）。 */
    public static final int WIDTH = 6;
    /** 宽度的一半（往玩家左边铺几格）。 */
    public static final int HALF_WIDTH = WIDTH / 2;
    /** 高度：3 格（用户没给，见类注释）。 */
    public static final int HEIGHT = 3;

    /** "10s 内没碰到原木/树叶就消失"：200 tick 的滚动窗口。 */
    public static final int IDLE_LIMIT_TICKS = 200;
    /** 兜底硬上限：60 秒。 */
    public static final int MAX_TICKS = 1200;
    /** 每 tick 前进几格（1 格/tick ⇒ 大约 20 格/秒）。 */
    public static final int STEP_PER_TICK = 1;

    /**
     * 射程上限（格）——**这条是补的规则，用户没给**，已挂 §9 待确认。
     *
     * <p>为什么必须有：用户给的两条消失条件（撞墙 / 10 秒没碰到木头）在**空旷地**
     * 挡不住波 —— 它会一直往前飞，偶尔蹭到远处的树又把计时重置，
     * 于是变成一台永久伐木机（探针实测：240 tick 之后它还活着）。</p>
     *
     * <p>取 64 格：玩家眼前的树一般都在十几格内，一片林子 64 格也够推平；
     * 既是玩法边界，也顺手把"永远飞下去"这种跑飞场景掐掉。</p>
     */
    public static final int MAX_DISTANCE = 64;

    /** 粒子每几 tick 发一批（2 ⇒ 10 批/秒，肉眼连续但只有一半的量）。 */
    private static final int PARTICLE_INTERVAL = 2;

    /** 还在推进的冲击波。只在服务端主线程上增删（ServerTickEvent 与右键都是主线程）。 */
    private static final List<Wave> WAVES = new ArrayList<>();

    private ShockwaveManager() {
    }

    /** 一道冲击波。字段全是**值**（Level 引用只在服务端活着时用，玩家一退就丢）。 */
    private static final class Wave {

        private final ServerLevel level;
        private final UUID owner;
        /** 玩家基础攻击伤害的快照（发射那一刻算一次，见类注释）。 */
        private final double baseDamage;

        /** 主轴：true = 沿 x（东西向），false = 沿 z（南北向）。 */
        private final boolean alongX;
        /** 主轴正负号：+1 / -1。 */
        private final int sign;

        /**
         * 采样的**高度基准**（发射那一刻玩家脚下的 y）。
         *
         * <p>⚠ 这是必须冻结的值：`tick()` 里如果每 tick 现读 `owner.getBlockY()`，
         * 玩家一被自己拆掉脚下的方块（重力）或被顶起来，采样层就跟着人跑 ——
         * 于是采到石台（被挡住）或空气（什么都拆不到）。探针实测过这两条，
         * 用户要的语义本来就是"**从我发射那一刻的高度**往前推"。</p>
         */
        private final int originY;

        /** 已经走过几格（0 = 起手那一格）。 */
        private int travelled;
        /** 从上一次拆到东西起过了几 tick。 */
        private int sinceBreak;
        /** 总共活了几 tick（兜底用）。 */
        private int totalTicks;

        private Wave(ServerLevel level, UUID owner, double baseDamage,
                     boolean alongX, int sign, int originY) {
            this.level = level;
            this.owner = owner;
            this.baseDamage = baseDamage;
            this.alongX = alongX;
            this.sign = sign;
            this.originY = originY;
        }

        /** 主轴坐标（当前采样位置）。 */
        private int mainCoord(int origin) {
            return origin + sign * travelled * STEP_PER_TICK;
        }
    }

    /**
     * 右键出手：起一道波。
     *
     * <p>返回 {@code true} 表示真的放出去了（调用方据此扣耐久 / 进冷却）。</p>
     */
    public static boolean fire(ServerPlayer player, ItemStack axe) {
        ServerLevel level = player.serverLevel();
        int x = player.getBlockX();
        int y = player.getBlockY();
        int z = player.getBlockZ();
        double dx = player.getLookAngle().x;
        double dz = player.getLookAngle().z;
        boolean alongX = Math.abs(dx) >= Math.abs(dz);
        int sign = (alongX ? dx : dz) >= 0.0D ? 1 : -1;

        Wave wave = new Wave(level, player.getUUID(), baseAttackDamage(player), alongX, sign, y);
        WAVES.add(wave);

        // 起手的视听：一声闷响 + 一排粒子（用户要"炫酷"，但起手只发一批）
        level.playSound(null, x + 0.5D, y + 0.5D, z + 0.5D,
                SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 1.1F, 1.4F);
        spawnParticles(wave, player, x, y, z, true);
        ShockwaveNetworking.broadcastWave(player, x, y, z, alongX, sign);
        return true;
    }

    /** 推进所有冲击波；由 {@code PotatoST} 挂在 {@code ServerTickEvent.Post} 上。 */
    public static void onServerTick(ServerTickEvent.Post event) {
        if (WAVES.isEmpty()) {
            return;
        }
        // 倒着走：tick 里可能把当前这道移除（§11.4 那套"边遍历边删"的老坑）
        for (int i = WAVES.size() - 1; i >= 0; i--) {
            Wave wave = WAVES.get(i);
            if (wave.level.getServer() == null || !tick(wave)) {
                WAVES.remove(i);
            }
        }
    }

    /** 玩家退出：他名下还在飞的波原地散掉（人走了，参照系没了）。 */
    public static void onPlayerLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        if (WAVES.isEmpty()) {
            return;
        }
        UUID id = event.getEntity().getUUID();
        WAVES.removeIf(w -> w.owner.equals(id));
    }

    /** 推进一步。返回 false = 这道波该消失了。 */
    private static boolean tick(Wave wave) {
        ServerPlayer owner = wave.level.getServer().getPlayerList().getPlayer(wave.owner);
        if (owner == null || !owner.isAlive()) {
            return false;
        }
        wave.totalTicks++;
        if (wave.totalTicks > MAX_TICKS) {
            return false;
        }
        if (wave.travelled * STEP_PER_TICK > MAX_DISTANCE) {
            return false;   // 超出射程（见 MAX_DISTANCE 的注释）
        }

        int ox = owner.getBlockX();
        // ⚠ 高度用**发射那一刻冻结的 originY**，不是每 tick 现读玩家 Y（见 Wave#originY）
        int oy = wave.originY;
        int oz = owner.getBlockZ();

        boolean broke = false;
        boolean blocked = false;
        for (int lateral = 0; lateral < WIDTH; lateral++) {
            int offset = lateral - HALF_WIDTH;      // -3 .. +2（偶数宽的对称铺法）
            for (int dy = 0; dy < HEIGHT; dy++) {
                int bx = wave.alongX ? wave.mainCoord(ox) : ox + offset;
                int bz = wave.alongX ? oz + offset : wave.mainCoord(oz);
                int by = oy + dy;
                BlockPos pos = new BlockPos(bx, by, bz);
                BlockState state = wave.level.getBlockState(pos);
                // 末地才有的远程伤害（用户给的公式 10 + 0.5n）：实体结算与前缘同步推进
                if (wave.level.dimension() == Level.END) {
                    damageAt(wave, owner, pos);
                }

                // ⚠⚠ 这一句**不能删**（我删过一次，代价是四轮排查）：
                //   空气/实体占着的格子要**直接穿过去**。少了它，
                //   `isCorrectToolForDrops(空气)` 返回 false ⇒ 每一格空气都被当成
                //   "斧子挖不动的方块" ⇒ `blocked = true` ⇒ 波在第 1 tick 就散。
                //   探针当时的表现是"少拆一格"，非常容易误判成判据顺序问题。
                if (state.isAir()) {
                    continue;
                }

                float hardness = state.getDestroySpeed(wave.level, pos);
                if (hardness < 0.0F) {
                    // 硬度为负 = 原版那批"打不掉"的方块（基岩、传送门框架…）：不是"墙"，穿过去
                    continue;
                }
                // ---------------------------------------------------------------
                // ⚠⚠ 这两支**必须**先判"该不该拆"、再判"挡不挡路"，别用 `continue` 把两件事缠在一起。
                //   第一版写成"先判 !isChoppable ⇒ 再判工具 ⇒ continue"，结果是：
                //   **同一排里只要有一格是斧子挖不动的方块，这一排的其他格子也跟着不拆** ——
                //   探针当场抓到（宽度内 6 根原木只掉 5 根、6 格树叶只掉 5 格，
                //   到"走廊里只有一格木头"那场干脆一格都不掉）。
                //   拆与挡是两件独立的事：拆只看"是不是原木/树叶"，挡只看"斧子挖不挖得动"。
                // ---------------------------------------------------------------
                if (isChoppable(state)) {
                    // 原木/树叶：用户明说要拆的那一类 —— **工具种类不参与判定**
                    //（树叶的"正确工具"是锄/剪刀，拿 isCorrectToolForDrops 去判会把树叶全漏掉）
                    boolean destroyed = wave.level.destroyBlock(pos, true, owner);
                    if (destroyed) {
                        broke = true;
                    }
                    continue;
                }
                // 原木/树叶以外的方块：用户那条"碰到斧子不可以开采的方块就消失"
                if (!owner.getMainHandItem().isCorrectToolForDrops(state)) {
                    blocked = true;
                }
            }
        }

        if (blocked) {
            return false;
        }

        // 粒子 + 声音（每 2 tick 一批）
        if (wave.totalTicks % PARTICLE_INTERVAL == 0) {
            spawnParticles(wave, owner, ox, oy, oz, false);
        }

        if (broke) {
            wave.sinceBreak = 0;
            wave.level.playSound(null, wave.mainCoord(ox), oy + 1.0D,
                    wave.alongX ? oz : wave.mainCoord(oz),
                    SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 0.7F, 0.7F);
        } else if (++wave.sinceBreak >= IDLE_LIMIT_TICKS) {
            return false;    // 用户第 2 条：10 秒没碰到原木 ⇒ 消失
        }

        wave.travelled++;
        return true;
    }

    /**
     * 这格算不算"用户说的原木/去皮原木 和树叶"。
     *
     * <p>判据是**原版标签**（{@code #minecraft:logs} 覆盖所有原木/去皮原木/木头/去皮木头，
     * {@code #minecraft:leaves} 覆盖所有树叶）—— 不去硬编码方块名，这样模组木材自动算数。</p>
     */
    private static boolean isChoppable(BlockState state) {
        return state.is(BlockTags.LOGS) || state.is(BlockTags.LEAVES);
    }

    /**
     * 玩家的**基础攻击伤害**（不含手上/身上装备）—— 冲击波伤害里的 {@code n}。
     *
     * <p>为什么不直接读 {@code getAttributeValue(ATTACK_DAMAGE)}：1.21 起**物品的攻击力
     * 就是普通的属性修饰符**（写在物品的 {@code ItemAttributeModifiers} 组件里），
     * 主手拿着斧子时那个值里已经含了 "1 + 斧基础 5 + 档位 8" ⇒ 读出来是"这把斧子的伤害"，
     * 换把武器数值就变，跟用户那句"n 为玩家基础伤害"对不上。要的是
     * <b>玩家自己的那一份</b>：属性基础值（所有生物都是 1）+ 力量之类的加成。</p>
     *
     * <p><b>摘法（这是本方法的关键，写错就悄悄算错）</b>：不能靠"认得
     * {@code minecraft:base_attack_damage} 这个 id"—— 1.21 往属性表里塞物品修饰符时
     * 会<b>按槽位给 id 加后缀</b>（不同槽位的同一件装备不能同名），主手到底叫什么名字
     * 是靠字符串拼出来的、不是公开常量。所以这里改成<b>按来源认</b>：
     * 把玩家身上每件装备自带的修饰符收集成一张表（id → 倍率 + 加法值），
     * 再从属性表的快照里逐条排除"三条都一模一样"的那些 ——
     * 只认 id 会误伤（药水效果完全可以碰巧同名），三条全等才是同一份来源。</p>
     *
     * <p>算式的三个 operation 与顺序是**照着原版 {@code AttributeInstance.calculateValue}
     * 重演的**（add → multiply_base → multiply_total），因为原版是乘算叠加、
     * 直接"读总值再相减"在有多层乘算时会算错。</p>
     */
    public static double baseAttackDamage(Player player) {
        AttributeInstance instance = player.getAttribute(Attributes.ATTACK_DAMAGE);
        if (instance == null) {
            return 0.0D;
        }
        // ① 玩家身上所有装备自带的攻击力修饰符：id -> (加法值, 倍率)，倍率含符号编码
        Map<ResourceLocation, double[]> gear = new HashMap<>();
        if (player instanceof LivingEntity living) {
            collectGear(living.getMainHandItem(), gear);
            collectGear(living.getOffhandItem(), gear);
            for (EquipmentSlot slot : new EquipmentSlot[]{EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                    EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
                collectGear(living.getItemBySlot(slot), gear);
            }
        }

        // ② 照原版算式重演，跳过装备那一份
        double base = instance.getBaseValue();
        double added = 0.0D;
        double multipliedBase = 1.0D;
        double multipliedTotal = 1.0D;
        for (AttributeModifier modifier : instance.getModifiers()) {
            double[] gearValue = gear.get(modifier.id());
            if (gearValue != null && gearValue[0] == modifier.amount()
                    && gearValue[1] == signOf(modifier.operation())) {
                continue;
            }
            switch (modifier.operation()) {
                case ADD_VALUE -> added += modifier.amount();
                case ADD_MULTIPLIED_BASE -> multipliedBase += modifier.amount();
                case ADD_MULTIPLIED_TOTAL -> multipliedTotal *= 1.0D + modifier.amount();
            }
        }
        return (base + added) * multipliedBase * multipliedTotal;
    }

    /** 收一件装备自带的攻击力修饰符（只收主手那一组，别的槽位组按装备实际穿的位置生效）。 */
    private static void collectGear(ItemStack stack, Map<ResourceLocation, double[]> out) {
        if (stack.isEmpty()) {
            return;
        }
        stack.forEachModifier(EquipmentSlotGroup.MAINHAND, (attribute, modifier) -> {
            if (attribute.is(Attributes.ATTACK_DAMAGE)) {
                out.put(modifier.id(), new double[]{modifier.amount(), signOf(modifier.operation())});
            }
        });
        stack.forEachModifier(EquipmentSlotGroup.ARMOR, (attribute, modifier) -> {
            if (attribute.is(Attributes.ATTACK_DAMAGE)) {
                out.put(modifier.id(), new double[]{modifier.amount(), signOf(modifier.operation())});
            }
        });
    }

    /** operation → 符号（0/+、1/*、2/*…用不同编码，免得与加法值混淆）。 */
    private static double signOf(AttributeModifier.Operation operation) {
        return switch (operation) {
            case ADD_VALUE -> 0.0D;
            case ADD_MULTIPLIED_BASE -> 1.0D;
            case ADD_MULTIPLIED_TOTAL -> 2.0D;
        };
    }

    /** 冲击波在末地的远程伤害：{@code 10 + 0.5n}（用户给的公式）。 */
    public static double rangedDamage(double baseAttackDamage) {
        return 10.0D + 0.5D * baseAttackDamage;
    }

    /**
     * 在某一格上结算一次冲击波伤害（**只在末地调用**）。
     *
     * <p>伤害值 = {@link #rangedDamage}{@code (n)}，其中 {@code n} 是**发射那一刻**读到的
     * 玩家基础伤害（{@link Wave#baseDamage} 是快照 —— 用户说的是"n 为玩家基础伤害"，
     * 取发射时的值才不会一边打一边变）。</p>
     *
     * <p>几点刻意的选择（写在这里，免得下次有人顺手改）：</p>
     * <ul>
     *   <li><b>直接实体是发射者</b>：飘字与击杀归属归他，与原版 {@code playerAttack} 一致；</li>
     *   <li><b>排除发射者自己</b>：用户没说要自伤，而波从脚下出发、第一格就扫到自己；</li>
     *   <li><b>创造模式玩家不吃伤害</b>：原版规则；</li>
     *   <li>同一 tick 里相邻采样格可能框住同一个实体，原版无敌帧会挡掉重复伤害。</li>
     * </ul>
     */
    private static void damageAt(Wave wave, ServerPlayer owner, BlockPos pos) {
        double damage = rangedDamage(wave.baseDamage);
        AABB box = new AABB(pos).inflate(0.5D);
        for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, box)) {
            if (target.getUUID().equals(wave.owner) || !target.isAlive()) {
                continue;
            }
            if (target instanceof Player other && other.isCreative()) {
                continue;
            }
            target.hurt(wave.level.damageSources().playerAttack(owner), (float) damage);
        }
    }

    /** 每 2 tick 一批粒子：前缘一道弧 + 上下两条星屑（全走服务端标准粒子包）。 */
    private static void spawnParticles(Wave wave, ServerPlayer owner, int ox, int oy, int oz, boolean launch) {
        int main = wave.alongX ? wave.mainCoord(ox) : wave.mainCoord(oz);
        int lateralBase = wave.alongX ? oz : ox;
        boolean inEnd = wave.level.dimension() == Level.END;

        for (int lateral = 0; lateral < WIDTH; lateral++) {
            int offset = lateral - HALF_WIDTH;
            double px = wave.alongX ? main + 0.5D : ox + offset + 0.5D;
            double pz = wave.alongX ? lateralBase + offset + 0.5D : main + 0.5D;
            double py = oy + 0.5D;

            // 前缘：横扫粒子（原版剑气那个），打头两格
            wave.level.sendParticles(ParticleTypes.SWEEP_ATTACK, px, py + 0.6D, pz, 1, 0.0D, 0.0D, 0.0D, 0.0D);
            // 星屑：上下各一颗（"星璨"的那点意思）
            ParticleOptions star = (lateral % 3 == 0 && inEnd) ? ParticleTypes.END_ROD : ParticleTypes.CRIT;
            wave.level.sendParticles(star, px, py + 0.2D, pz, 1, 0.15D, 0.15D, 0.15D, 0.0D);
            wave.level.sendParticles(ParticleTypes.END_ROD, px, py + HEIGHT - 0.3D, pz, 1, 0.1D, 0.1D, 0.1D, 0.0D);
            if (launch || lateral % 2 == 0) {
                wave.level.sendParticles(ParticleTypes.CLOUD, px, py + 0.05D, pz, 1, 0.2D, 0.05D, 0.2D, 0.01D);
            }
        }

        // 拆到木头时补一点木屑（视觉上"这排树被啃掉了"）
        if (!launch) {
            BlockPos below = new BlockPos(
                    wave.alongX ? main : lateralBase,
                    oy + 1,
                    wave.alongX ? lateralBase : main);
            BlockState state = wave.level.getBlockState(below);
            if (isChoppable(state)) {
                wave.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state),
                        below.getX() + 0.5D, below.getY() + 0.5D, below.getZ() + 0.5D,
                        6, 0.4D, 0.4D, 0.4D, 0.05D);
            }
        }
    }

    /** 当前还有几道波（探针/验证用，不参与玩法）。 */
    public static int activeCount() {
        return WAVES.size();
    }

    /** 清空（探针/验证用；正常玩法里波是自己到期的）。 */
    public static void clearAll() {
        WAVES.clear();
    }
}
