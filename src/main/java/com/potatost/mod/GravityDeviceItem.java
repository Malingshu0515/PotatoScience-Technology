package com.potatost.mod;

import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * 手持式引力装置（0.14 ZF169）：副手放方块 ⇒ 长按右键蓄力 ⇒ 放一个黑洞。
 *
 * <p><b>用户原话</b>：「储能8mFE 副手放一个方块 长按右键开始蓄力 25s后召唤出一个黑洞
 * 把3x3区块内所有副手方块 全部吸引到黑洞的位置（单次最多1200个方块）单次消耗全部8m电力并损坏
 * （黑洞还会吸引周围的生物 进入黑洞范围内会持续受到虚空伤害）」。</p>
 *
 * <h2>怎么用</h2>
 * <ol>
 *   <li>把要吸的那种**方块**放进<b>副手</b>（主手拿本装置）；</li>
 *   <li>把储能充到满（{@link PotatoSTConfig#gravityCapacity()} = 默认 8,000,000 FE，用充电站/别的模组的
 *       充电器都行 —— 本装置实现了 NeoForge 的物品能量能力）；</li>
 *   <li><b>按住右键蓄力</b>（{@link PotatoSTConfig#gravityChargeTicks()}，默认 30 秒）不动：
 *       手会像拉弓一样收着，脚下有粒子往身上卷、每 10 tick 报一次百分比；</li>
 *   <li>蓄满 ⇒ 扣掉这一次的**召唤费**，在原地召唤黑洞（见 {@link BlackHoleManager}）。
 *       <b>0.14 ZF190 修的那个 bug</b>：以前是「扣光整条电力条」，容量调到 64M 时一次就扣 64M ——
 *       现在扣的是**固定费用** {@link #summonCost(int)}：普通模式 {@link #SUMMON_COST}（8M）、
 *       坍缩模式 {@link #COLLAPSE_SUMMON_COST}（4M，之后每 tick 再扣 50k）。</li>
 *   <li><b>装置坏不坏由配置说了算</b>（{@link PotatoSTConfig#oneShotBlackHole()}）：true（默认）
 *       时装置当场损坏（耐久打空），false 时留着下次再用。<b>坍缩模式永远不损坏</b> ——
 *       它靠装置每 tick 供电，装置坏了就没电可扣（黑洞会立刻消失）。中途松手 = 作废重来。</li>
 * </ol>
 *
 * <h2>三个模式（Shift + 左键循环切换）</h2>
 * <ol>
 *   <li>{@link #MODE_SWALLOW} 吞噬搬运：只吸副手那种方块，搬过来码在黑洞脚下；</li>
 *   <li>{@link #MODE_TOW} 引力牵引：同上，但方块变成**下落方块**飞过去；</li>
 *   <li>{@link #MODE_COLLAPSE} <b>坍缩模式-危险</b>（0.14 ZF190，用户原话
 *       「开启后无差别吸引最近所有的生物以及方块（振金免疫）吸引到的掉落物会销毁
 *       然后吸引时间越长吸引强度越高伤害也越高」）：<b>无差别</b>吸一切可破坏方块与生物、
 *       销毁掉落物、强度与伤害随存活时间递增；副手方块仍要放一个（当"引子"，它不决定吸什么）。
 *       费用口径见上面第 4 条。</li>
 * </ol>
 *
 * <p>⚠ 蓄力过程中副手方块被拿走 ⇒ 立刻中断（不许「空手放大招」）。
 * 储能与探测器一样写在物品自己的 {@code CustomData} 里（不动注册表）。</p>
 *
 * <p><b>⚠ 0.14 ZF186：{@code CAPACITY} / {@code CHARGE_TICKS} 两个常量已经删掉</b>，
 * 改成每次现取 {@link PotatoSTConfig}。为什么不缓存进 static final：配置**可以在游戏里改**
 * （配置界面的值改完立刻生效，NeoForge 的 {@code ConfigValue.set} 在 restartType=NONE 时会刷缓存）
 * —— 缓存下来就会出现「界面改了、物品条不动」这种假生效。</p>
 */
public class GravityDeviceItem extends Item {

    /** 每多少 tick 报一次进度（顺带一声「充能」）。 */
    public static final int FEEDBACK_INTERVAL = 10;

    private static final String ENERGY_KEY = "potatost:energy";
    private static final String MODE_KEY = "potatost:mode";

    /** 模式 1「吞噬搬运」：方块直接搬到黑洞脚下码起来（原位置变空）。 */
    public static final int MODE_SWALLOW = 0;
    /** 模式 2「引力牵引」：方块变成**下落方块**飞过去 —— 落地还会变回方块，落不下就掉成物品，**绝不消失**。 */
    public static final int MODE_TOW = 1;
    /**
     * 模式 3「坍缩模式-危险」（0.14 ZF190，用户原话见类注释）：无差别吸引 + 销毁掉落物 +
     * 强度/伤害随年龄递增；电费按 tick 算（{@link #COLLAPSE_COST_PER_TICK}）。
     */
    public static final int MODE_COLLAPSE = 2;

    /**
     * 普通模式（吞噬 / 牵引）的**固定**召唤费。
     *
     * <p><b>0.14 ZF190 用户报的 bug</b>：「黑洞正常单次召唤应该只消耗8m电力（配置改成64m之后
     * 充满一次性把全部电力都消耗完了）」—— 旧代码是 {@code setEnergy(stack, 0)}（抽干整条），
     * 所以容量一调大就"一次吃掉 64M"。现在扣的就是这个数（用户最早给的口径「单次消耗全部8m电力」）。</p>
     */
    public static final int SUMMON_COST = 8_000_000;
    /** 坍缩模式的召唤费（用户原话「召唤出来消耗4m」）。 */
    public static final int COLLAPSE_SUMMON_COST = 4_000_000;
    /** 坍缩模式每存在 1 tick 的电费（用户原话「每存在1tick消耗50kFE没有电力时候黑洞消失」）。 */
    public static final int COLLAPSE_COST_PER_TICK = 50_000;

    /**
     * 这一次召唤要扣多少电：按模式取费用，**再按当前容量封顶**。
     *
     * <p>为什么要封顶：配置允许把容量调到 1M，而召唤费是 8M ⇒ 不封顶的话那种配置下**永远放不出来**
     * （电永远攒不够）。封顶之后"小容量也能用，只是每次放完就精光"，这条写在这里不藏着。</p>
     */
    public static int summonCost(int mode) {
        int want = mode == MODE_COLLAPSE ? COLLAPSE_SUMMON_COST : SUMMON_COST;
        return Math.min(want, PotatoSTConfig.gravityCapacity());
    }

    public GravityDeviceItem(Properties properties) {
        super(properties);
    }

    /** 模式名对应的 lang 键（三个模式一套，切换时显示的就是它）。 */
    public static String modeKey(int mode) {
        return switch (mode) {
            case MODE_TOW -> "message.potato_s_t.gravity.mode.tow";
            case MODE_COLLAPSE -> "message.potato_s_t.gravity.mode.collapse";
            default -> "message.potato_s_t.gravity.mode.swallow";
        };
    }

    // ============================================================
    //  模式（0.14 ZF170：Shift+左键切换；0.14 ZF190：三个模式循环）
    // ============================================================
    public static int getMode(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        return tag.getInt(MODE_KEY);
    }

    public static void setMode(ItemStack stack, int mode) {
        int m = (mode == MODE_TOW || mode == MODE_COLLAPSE) ? mode : MODE_SWALLOW;
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        tag.putInt(MODE_KEY, m);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        // 附魔光效：非"吞噬"模式都亮（危险模式也得一眼看出来）—— 用原版那个"强制光效"组件，
        // 不用自己写 isFoil（1.21 起光效就是 DataComponents.ENCHANTMENT_GLINT_OVERRIDE 说了算）。
        if (m == MODE_SWALLOW) {
            stack.remove(DataComponents.ENCHANTMENT_GLINT_OVERRIDE);
        } else {
            stack.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, Boolean.TRUE);
        }
    }

    /**
     * Shift+左键：**循环**切换模式（由 {@code PotatoST} 里的 LeftClickBlock 监听调）。
     *
     * <p>0.14 ZF190：从两档变三档（吞噬 → 牵引 → 坍缩 → 吞噬）；<b>坍缩模式那行字按用户要求用红色</b>
     * （{@code ChatFormatting.RED}，只动颜色、不加语言键）。</p>
     */
    public static void toggleMode(ItemStack stack, Player player) {
        int next = switch (getMode(stack)) {
            case MODE_SWALLOW -> MODE_TOW;
            case MODE_TOW -> MODE_COLLAPSE;
            default -> MODE_SWALLOW;
        };
        setMode(stack, next);
        // ⚠ 这里必须是 MutableComponent：`withStyle` 在 MutableComponent 上（Component 接口没有）
        net.minecraft.network.chat.MutableComponent msg = Component.translatable(modeKey(next));
        if (next == MODE_COLLAPSE) {
            msg = msg.withStyle(net.minecraft.ChatFormatting.RED);
        }
        player.displayClientMessage(msg, true);
        player.level().playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.LEVER_CLICK, SoundSource.PLAYERS, 0.6F,
                next == MODE_SWALLOW ? 0.8F : (next == MODE_TOW ? 1.4F : 0.5F));
    }

    // ============================================================
    //  能量
    // ============================================================
    public static int getEnergy(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        // ZF186：容量可以在游戏里调小 ⇒ 存着的电可能"超容"，对外一律按当前容量封顶（不偷偷扣掉玩家的电）
        return Math.min(tag.getInt(ENERGY_KEY), PotatoSTConfig.gravityCapacity());
    }

    public static void setEnergy(ItemStack stack, int value) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        tag.putInt(ENERGY_KEY, Math.max(0, Math.min(PotatoSTConfig.gravityCapacity(), value)));
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    public static IEnergyStorage energyStorage(ItemStack stack) {
        return new IEnergyStorage() {
            @Override
            public int receiveEnergy(int toReceive, boolean simulate) {
                int now = getEnergy(stack);
                int taken = Math.min(PotatoSTConfig.gravityCapacity() - now, Math.max(0, toReceive));
                if (!simulate && taken > 0) {
                    setEnergy(stack, now + taken);
                }
                return taken;
            }

            @Override
            public int extractEnergy(int toExtract, boolean simulate) {
                int now = getEnergy(stack);
                int given = Math.min(now, Math.max(0, toExtract));
                if (!simulate && given > 0) {
                    setEnergy(stack, now - given);
                }
                return given;
            }

            @Override
            public int getEnergyStored() {
                return getEnergy(stack);
            }

            @Override
            public int getMaxEnergyStored() {
                return PotatoSTConfig.gravityCapacity();
            }

            @Override
            public boolean canExtract() {
                return true;
            }

            @Override
            public boolean canReceive() {
                return true;
            }
        };
    }

    // ============================================================
    //  物品条（蓄能 = 黄，满 = 紫，一眼看出能不能放）
    // ============================================================
    @Override
    public boolean isBarVisible(ItemStack stack) {
        return true;
    }

    @Override
    public int getBarWidth(ItemStack stack) {
        return Math.round(13.0F * getEnergy(stack) / PotatoSTConfig.gravityCapacity());
    }

    @Override
    public int getBarColor(ItemStack stack) {
        return getEnergy(stack) >= PotatoSTConfig.gravityCapacity() ? 0xFF9B30FF : 0xFFE0C040;
    }

    /**
     * 动态 tooltip（0.14 ZF186）：容量 / 蓄力时长 / 一次性都能在配置里改，
     * 静态 lang 里写死的数字迟早对不上 ⇒ 这里按**当前配置**现算一行。
     * （静态那行的文案也顺手改成了「默认 x，可在配置里改」的口径。）
     */
    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context,
                                java.util.List<Component> tooltip, net.minecraft.world.item.TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.potato_s_t.gravity_device.stats",
                String.format("%,d", PotatoSTConfig.gravityCapacity()),
                PotatoSTConfig.gravityChargeTicks() / 20));
        tooltip.add(Component.translatable(PotatoSTConfig.oneShotBlackHole()
                ? "tooltip.potato_s_t.gravity_device.one_shot.on"
                : "tooltip.potato_s_t.gravity_device.one_shot.off"));
    }

    // ============================================================
    //  蓄力
    // ============================================================
    @Override
    public int getUseDuration(ItemStack stack, LivingEntity entity) {
        return PotatoSTConfig.gravityChargeTicks();
    }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) {
        return UseAnim.BOW;
    }

    /** 副手那种方块（没有就 null）。 */
    public static Block offhandBlock(Player player) {
        ItemStack off = player.getOffhandItem();
        return off.getItem() instanceof BlockItem bi ? bi.getBlock() : null;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        int mode = getMode(stack);
        // 0.14 ZF192：**坍缩模式副手可以空着** —— 它无差别吸一切，"引子"对它没有意义。
        //   另外两个模式仍然要求先在副手放好要吸的那种方块。
        if (offhandBlock(player) == null && mode != MODE_COLLAPSE) {
            if (!level.isClientSide) {
                player.displayClientMessage(
                        Component.translatable("message.potato_s_t.gravity.need_offhand"), true);
            }
            return InteractionResultHolder.fail(stack);
        }
        // 0.14 ZF190：闸门从「必须充满」改成「**至少够这一次的召唤费**」——
        //   容量调大之后（比如 64M）没道理要求先充到 64M 才肯放一个只花 8M 的洞。
        int cost = summonCost(mode);
        if (getEnergy(stack) < cost) {
            if (!level.isClientSide) {
                player.displayClientMessage(Component.translatable(
                        "message.potato_s_t.gravity.not_full", getEnergy(stack), cost), true);
            }
            return InteractionResultHolder.fail(stack);
        }
        player.startUsingItem(hand);
        if (!level.isClientSide) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.0F, 0.6F);
        }
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public void onUseTick(Level level, LivingEntity living, ItemStack stack, int remaining) {
        if (!(living instanceof Player player)) {
            return;
        }
        // ZF186：蓄力总长现取配置（默认 30 秒）。⚠ 蓄力**途中**配置被改小的话 `remaining` 可能比总长还大
        // ⇒ charged 会是负数，所以这里先夹到 0，别让百分比/粒子半径算出鬼来。
        int total = PotatoSTConfig.gravityChargeTicks();
        int charged = Math.max(0, total - remaining);
        if (offhandBlock(player) == null && getMode(stack) != MODE_COLLAPSE) {
            // 副手方块被拿走了 ⇒ 立刻中断（并说清为什么）。
            // ⚠ 0.14 ZF192：坍缩模式本来就不需要副手方块 ⇒ 它的蓄力不该被这条打断。
            if (!level.isClientSide) {
                player.displayClientMessage(
                        Component.translatable("message.potato_s_t.gravity.cancel_offhand"), true);
                player.stopUsingItem();
            }
            return;
        }
        if (level.isClientSide) {
            return;
        }
        if (charged % FEEDBACK_INTERVAL == 0) {
            int percent = charged * 100 / total;
            player.displayClientMessage(Component.translatable(
                    "message.potato_s_t.gravity.charging", percent), true);
            // 音调随进度升高：听得出"快好了"
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS,
                    0.6F + 1.4F * charged / total, 0.8F + 1.2F * charged / total);
        }
        // 粒子：脚下的方块碎屑 + 一圈往身上卷的传送门粒子（半径随蓄力收小 = "吸进来了"）
        if (level instanceof ServerLevel serverLevel) {
            double t = (double) charged / total;
            double radius = 3.0D - 2.0D * t;
            int count = 8 + (int) (t * 16);
            for (int i = 0; i < count; i++) {
                double a = i * (Math.PI * 2.0D / count) + charged * 0.25D;
                serverLevel.sendParticles(net.minecraft.core.particles.ParticleTypes.REVERSE_PORTAL,
                        player.getX() + Math.cos(a) * radius, player.getY() + 0.2D + t * 1.2D,
                        player.getZ() + Math.sin(a) * radius, 1, 0.0D, 0.02D, 0.0D, 0.0D);
            }
            if (charged % 5 == 0) {
                serverLevel.sendParticles(net.minecraft.core.particles.ParticleTypes.ELECTRIC_SPARK,
                        player.getX(), player.getY() + 1.0D, player.getZ(), 3, 0.5D, 0.8D, 0.5D, 0.05D);
            }
        }
    }

    @Override
    public boolean useOnRelease(ItemStack stack) {
        // ⚠⚠ 0.14 ZF169b **用户实测抓出来的真 bug**：「可以正常蓄力但是没结果（蓄力完能量都不消耗）」。
        //   根因：`Item.useOnRelease()` 默认 **false** ⇒ 蓄力**满**的时候原版走的是
        //   `completeUsingItem()` → `finishUsingItem()`，**根本不调 `releaseUsing`**；
        //   `releaseUsing` 只在**提前松手/换手/被打断**时来，而且那时 `timeLeft > 0`
        //   ⇒ 我那段"满了就开火"的分支永远进不去（`timeLeft == 0` 那半边是死代码）。
        //   返回 true ⇒ 满蓄力也走 `releaseUsing`（弓、三叉戟都是这条路）。
        return true;
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity living) {
        // 双保险：万一还有别的路径走到 finishUsingItem，也让它开火。
        // `fire()` 里用"电量是否满"当闸门 ⇒ 两条路都来也只会开一次（不会扣两次电）。
        if (living instanceof ServerPlayer player && level instanceof ServerLevel serverLevel) {
            fire(serverLevel, player, stack);
        }
        return stack;
    }

    /**
     * 开火（唯一入口）：扣掉**这一次的召唤费** + （按配置）装置损坏 + 召唤黑洞。
     * 电量不够这一次的费用 = 什么都不做（也顺带挡住"同一次操作扣两次电"）。
     *
     * <p><b>0.14 ZF190 修的真 bug</b>（用户原话：「黑洞正常单次召唤应该只消耗8m电力
     * （配置改成64m之后充满一次性把全部电力都消耗完了）」）：旧代码是 {@code setEnergy(stack, 0)}，
     * 把整条电力条抽干 —— 容量一调大就变成"一次 64M"。现在扣 {@link #summonCost(int)}。</p>
     *
     * <p><b>一次性</b>（{@link PotatoSTConfig#oneShotBlackHole()}）只对**普通模式**生效：
     * 坍缩模式靠装置**每 tick 供电**，装置要是当场坏了就没电可扣、黑洞立刻消失 ⇒ 它豁免。</p>
     */
    private void fire(ServerLevel serverLevel, ServerPlayer player, ItemStack stack) {
        int mode = getMode(stack);
        int cost = summonCost(mode);
        if (getEnergy(stack) < cost) {
            return;   // 闸门：电不够这一次（或已经放过了 —— 费用已经扣走）
        }
        Block block = offhandBlock(player);
        // 0.14 ZF192：坍缩模式**副手可以空着**（用户：「坍缩模式空手也能放」）⇒ 只有别的模式才拦。
        if (block == null && mode != MODE_COLLAPSE) {
            player.displayClientMessage(
                    Component.translatable("message.potato_s_t.gravity.cancel_offhand"), true);
            return;
        }
        boolean seeded = block != null;
        setEnergy(stack, getEnergy(stack) - cost);
        if (PotatoSTConfig.oneShotBlackHole() && mode != MODE_COLLAPSE) {
            stack.hurtAndBreak(stack.getMaxDamage(), player, EquipmentSlot.MAINHAND);
        }
        serverLevel.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 2.0F, 0.5F);
        // ⚠ 第六个参数把**装置本身**交给黑洞：坍缩模式每 tick 从这件装置上扣 50k FE
        // ⚠ 空手放时"种子方块"用 AIR 当哨兵：坍缩模式根本不用它（吸什么由 eatable 决定），
        //   只有存档那一个字段会记成 minecraft:air（loadFrom 对坍缩模式**不**把它当"方块没了"）。
        BlackHoleManager.spawn(serverLevel, player.position().add(0.0D, 1.0D, 0.0D),
                seeded ? block : Blocks.AIR, player, mode, stack);
        player.displayClientMessage(seeded
                ? Component.translatable("message.potato_s_t.gravity.fired", block.getName())
                : Component.translatable("message.potato_s_t.gravity.fired.everything"), true);
    }

    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity living, int timeLeft) {
        if (level.isClientSide || !(living instanceof ServerPlayer player)
                || !(level instanceof ServerLevel serverLevel)) {
            return;
        }
        if (timeLeft > 0) {
            // 没蓄满就松手 —— 作废（不扣电、不损坏）
            serverLevel.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 1.0F, 0.6F);
            player.displayClientMessage(
                    Component.translatable("message.potato_s_t.gravity.interrupted"), true);
            return;
        }
        fire(serverLevel, player, stack);
    }
}
