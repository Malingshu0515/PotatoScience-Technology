package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * ⚠⚠ <b>诊断探针（ZF153 临时文件，验证完必须删）</b>：振金剑的端到端取证。
 *
 * <p>用户原话：「加个振金剑材质在素材 无法破坏 拿在手里免疫凋零，缓慢，挖掘疲劳 24点伤害
 * 1.4攻击速度 1附魔权重 shift+右键猛击地面 击飞6x6除自己的所有生物 并对其造成n+12点伤害
 * n为玩家基础伤害 和4s的失明 4s的缓慢效果 冷却6s」。</p>
 *
 * <h2>判据只吃"外面看得见的行为"</h2>
 * <p>一条都不碰本轮的实现细节（不去读 {@code SLAM_HALF} 之类常量、不去问管理器内部状态），
 * 全是玩家/服务端能观察到的东西：</p>
 * <ul>
 *   <li><b>数值</b>：从物品的 {@code ATTRIBUTE_MODIFIERS} **组件**里读修饰符，再把
 *       "玩家基础 1 + 修饰符"这个**显示值**算出来打出来（照 ZF133 的原话：判据盯语义、
 *       不盯魔法数字）；附魔权重读 {@code ItemStack.getEnchantmentValue()}；</li>
 *   <li><b>无法破坏</b>：{@code isDamageableItem()} + 真扣一次 500 点看耐久动不动；</li>
 *   <li><b>免疫</b>：{@code addEffect} 的**返回值**与 {@code getEffect()}。
 *       ⚠ 三条免疫**每条都配一条灵敏度对照**：空手时同样的 {@code addEffect} 必须**挂得上**
 *       （否则"挂不上"可能只是因为别的原因，比如注册表没对上）—— 这是"红基线"那一套的同源；
 *       另有两条"不该被误伤"的对照（急迫 / 速度仍要挂得上）；</li>
 *   <li><b>猛击</b>：三个范围内苦力怕…不，**三个范围内 husk** 各掉多少血（要正好 n+12）、
 *       失明/缓慢的**时长**、{@code getDeltaMovement()} 的**方向与大小**、
 *       10 tick 之后**真的离地了多高**（端到端：不是"我设了速度"，而是"它真飞起来了"）、
 *       **范围外那个一点没动**（负向对照）、**自己没掉血**、冷却中再按**被拒**。</li>
 * </ul>
 *
 * <p><b>为什么用 husk 而不是 zombie</b>：ZOMBIE 在白天会烧起来（血量自己掉），
 * 那会把"掉了多少血"这条判据搅浑；husk 是同一族的 20 血亡灵、晒不烧。</p>
 *
 * <p>跑法：{@code python build\zftools\_zf153_probe.py run}（它负责挂载、起服、收报告、摘除）。</p>
 */
public final class Zf153Check {

    private static final String TAG = "[A153] ";
    private static final String DIR = "E:\\PotatoST\\build\\zftools\\check\\";
    private static final String REPORT = DIR + "zf153_振金剑取证.log";

    /** 试验场：悬空木平台（照抄 ZF114/ZF146 —— 离地 50 多格，离天然地形远）。 */
    private static final int PX = 200;
    private static final int PY = 120;
    private static final int PZ = 200;

    private static boolean started;
    private static boolean finished;
    private static int failed;
    private static ServerLevel level;
    private static ServerPlayer player;
    private static ItemStack sword;

    private static long t0 = -1L;
    private static int phase;

    /** 四个 husk：三个在 6x6 里（含一个贴边的）、一个在范围外当负向对照。 */
    private static final List<Husk> IN = new ArrayList<>();
    private static Husk out;
    private static final double[] SPAWN_DX = {2.0D, -2.5D, 0.0D};
    private static final double[] SPAWN_DZ = {0.0D, 1.0D, 2.9D};
    private static final double OUT_DX = 4.0D;
    private static final double OUT_DZ = 0.0D;

    private static float playerHpBefore;
    private static final List<Float> hpBefore = new ArrayList<>();
    private static float outHpBefore;
    private static double outYBefore;
    private static double groupYBefore;
    private static float expectedDamage;

    private static final StringBuilder report = new StringBuilder();

    private Zf153Check() {
    }

    public static void register() {
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf153Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    // ============================================================
    //  开场：搭台 + 造人 + A/B 两组判据
    // ============================================================
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (started) {
            return;
        }
        started = true;
        try {
            level = event.getServer().overworld();
            buildArena();

            GameProfile profile = new GameProfile(
                    UUID.nameUUIDFromBytes("zf153probe".getBytes(StandardCharsets.UTF_8)), "zf153probe");
            player = new ServerPlayer(event.getServer(), level, profile, ClientInformation.createDefault());
            // ⚠ 无头服务端里 new 出来的玩家没有连接，发任何包都会 NPE（档案 §4.43）；
            //   1.21.1 还要给 Connection 塞一个 EmbeddedChannel（ZF114/ZF146 同款）
            net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                    net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
            try {
                java.lang.reflect.Field channelField =
                        net.minecraft.network.Connection.class.getDeclaredField("channel");
                channelField.setAccessible(true);
                channelField.set(conn, new io.netty.channel.embedded.EmbeddedChannel());
            } catch (Throwable t) {
                say(TAG + "EmbeddedChannel 注入失败（后面发消息会 NPE）：" + t);
            }
            player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                    event.getServer(), conn, player,
                    net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
            player.moveTo(PX + 0.5D, PY + 1, PZ + 0.5D, 0.0F, 0.0F);

            sword = new ItemStack(ModItems.VIBRANIUM_SWORD.get());
            player.getInventory().setItem(0, sword);
            player.getInventory().selected = 0;

            sectionA();
            sectionB();
            t0 = level.getGameTime();
            say(TAG + "① 试验场就绪，世界时间 = " + t0 + "（接下来在第 +20 / +30 / +40 tick 三批取证）");
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
            finish(event.getServer());
        }
    }

    // ============================================================
    //  A 物品事实（数值 / 无法破坏 / 附魔权重 / 创造页）
    // ============================================================
    private static void sectionA() {
        say(TAG + "======== A 物品事实 ========");
        Item item = sword.getItem();
        ResourceLocation id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(item);
        failed += check("A1 注册名 = potato_s_t:vibranium_sword", "potato_s_t:vibranium_sword".equals(id.toString()),
                String.valueOf(id));

        // 名字念得出（en_us 里真有这个键）
        String descId = sword.getDescriptionId();
        String name = net.minecraft.locale.Language.getInstance().getOrDefault(descId, descId);
        failed += check("A2 名字在语言表里念得出（键 " + descId + "）", !name.equals(descId), name);

        // 属性：从**组件**里读，再算显示值
        Object comp = sword.get(DataComponents.ATTRIBUTE_MODIFIERS);
        failed += check("A3 带 ATTRIBUTE_MODIFIERS 组件", comp != null);
        double dmgMod = 0.0D;
        double spdMod = 0.0D;
        boolean sawSpeed = false;
        if (comp instanceof ItemAttributeModifiers mods) {
            for (ItemAttributeModifiers.Entry e : mods.modifiers()) {
                if (e.attribute().is(Attributes.ATTACK_DAMAGE)) {
                    dmgMod = e.modifier().amount();
                } else if (e.attribute().is(Attributes.ATTACK_SPEED)) {
                    spdMod = e.modifier().amount();
                    sawSpeed = true;
                }
            }
        }
        double bonus = ModTiers.VIBRANIUM_TOOL.getAttackDamageBonus();
        say(TAG + "      组件里的攻击力修饰符 = " + dmgMod + "（= 参数 + 档位加成 " + bonus + "）");
        failed += check("A4 修饰符 == 剑的参数 + 档位加成" + "（" + dmgMod + " == "
                        + ModTiers.VIBRANIUM_SWORD_DAMAGE + " + " + bonus + "）",
                Math.abs(dmgMod - (ModTiers.VIBRANIUM_SWORD_DAMAGE + bonus)) < 1.0E-6D);
        double shown = 1.0D + dmgMod;
        say(TAG + "      ⇒ 显示的总伤害 = 1 + " + dmgMod + " = " + shown + "（用户要的 24）");
        failed += check("A5 显示总伤害 = 24.0", Math.abs(shown - 24.0D) < 1.0E-6D, String.valueOf(shown));
        failed += check("A6 带攻速修饰符", sawSpeed);
        double aps = 4.0D + spdMod;
        say(TAG + "      ⇒ 攻速 = 4.0 + " + spdMod + " = " + aps + " 次/秒（用户要的 1.4）");
        failed += check("A7 攻速 = 1.4", Math.abs(aps - 1.4D) < 1.0E-6D, String.valueOf(aps));

        int ench = sword.getEnchantmentValue();
        failed += check("A8 附魔权重 = 1（用户要的）", ench == 1, String.valueOf(ench));

        failed += check("A9 组件里有 UNBREAKABLE",
                sword.has(DataComponents.UNBREAKABLE));
        failed += check("A10 isDamageableItem() == false（于是 hurtAndBreak 是空操作）",
                !sword.isDamageableItem());
        int maxDmg = sword.getMaxDamage();
        say(TAG + "      看不见的那个耐久 = " + maxDmg + "（下界合金剑同款；挂着 UNBREAKABLE 玩家看不到）");
        int dmgBefore = sword.getDamageValue();
        sword.hurtAndBreak(500, player, EquipmentSlot.MAINHAND);
        int dmgAfter = sword.getDamageValue();
        failed += check("A11 真扣 500 点之后耐久一点没动（" + dmgBefore + " → " + dmgAfter + "）",
                dmgAfter == dmgBefore);
        failed += check("A12 物品还在（没被扣爆）", !sword.isEmpty());

        // 创造页（无头服务端里内容可能还没构建 ⇒ 照 ZF119 的口径：构建过就必须有）
        try {
            CreativeModeTab tab = net.minecraft.core.registries.BuiltInRegistries.CREATIVE_MODE_TAB.get(
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "potato_s_t_tab"));
            failed += check("A13 注册表里有本模组的创造页", tab != null);
            if (tab != null) {
                Collection<ItemStack> items = tab.getDisplayItems();
                if (items.isEmpty()) {
                    say(TAG + "      （创造页内容在无头服务端里还没构建 ⇒ 这条留给静态检查 "
                            + "_zf153_verify.py 的 B 组）");
                } else {
                    boolean has = items.stream().anyMatch(s -> s.is(item));
                    failed += check("A14 创造页里有它（该页共 " + items.size() + " 项）", has);
                }
            }
        } catch (Throwable t) {
            say(TAG + "      创造页检查抛了（不当判据）：" + t);
        }
    }

    // ============================================================
    //  B 免疫三种效果（每条都配灵敏度对照）
    // ============================================================
    private static void sectionB() {
        say(TAG + "======== B 拿在手里免疫凋零 / 缓慢 / 挖掘疲劳 ========");
        ItemStack saved = player.getInventory().getItem(0);

        // ---- B1 灵敏度对照：空手时三条都**挂得上** ----
        player.getInventory().setItem(0, ItemStack.EMPTY);
        failed += check("B1 前置：空手（getMainHandItem 为空）", player.getMainHandItem().isEmpty());
        for (Holder<MobEffect> e : VibraniumSwordItem.IMMUNE_EFFECTS) {
            player.removeAllEffects();
            boolean added = player.addEffect(new MobEffectInstance(e, 200, 0));
            failed += check("B2 空手时 " + effectName(e) + " 挂得上（灵敏度对照）",
                    added && player.hasEffect(e));
        }
        player.removeAllEffects();

        // ---- B3 拿剑时三条都**挂不上** ----
        player.getInventory().setItem(0, saved);
        failed += check("B3 前置：手里拿着振金剑", VibraniumSwordItem.isHolding(player));
        for (Holder<MobEffect> e : VibraniumSwordItem.IMMUNE_EFFECTS) {
            player.removeAllEffects();
            boolean added = player.addEffect(new MobEffectInstance(e, 200, 0));
            failed += check("B4 拿着剑时 " + effectName(e) + " 挂不上（addEffect 返回 false、身上也没有）",
                    !added && !player.hasEffect(e));
        }

        // ---- B5/B6 两条"不该被误伤"的对照 ----
        for (Holder<MobEffect> e : List.of(MobEffects.DIG_SPEED, MobEffects.MOVEMENT_SPEED)) {
            player.removeAllEffects();
            boolean added = player.addEffect(new MobEffectInstance(e, 200, 0));
            failed += check("B5 拿着剑时 " + effectName(e) + " 仍然挂得上（没有一刀切）",
                    added && player.hasEffect(e));
        }

        // ---- B7 清理那一半：先空手挂上凋零，再拿起剑 ----
        player.removeAllEffects();
        player.getInventory().setItem(0, ItemStack.EMPTY);
        boolean seeded = player.addEffect(new MobEffectInstance(MobEffects.WITHER, 200, 0));
        boolean had = player.hasEffect(MobEffects.WITHER);
        player.getInventory().setItem(0, saved);
        VibraniumSwordItem.onPlayerTick(player);
        failed += check("B7 空手挂上的凋零（" + seeded + "/" + had + "）⇒ 一拿起剑就被清掉",
                seeded && had && !player.hasEffect(MobEffects.WITHER));
        player.removeAllEffects();
    }

    // ============================================================
    //  C 猛击：范围 / 伤害 / 击飞 / 状态 / 冷却
    // ============================================================
    private static void phaseSlam() {
        say(TAG + "======== C 猛击地面（Shift + 右键）=======");
        // 三个范围内的 husk + 一个范围外的
        for (int i = 0; i < SPAWN_DX.length; i++) {
            Husk h = spawnHusk(PX + 0.5D + SPAWN_DX[i], PZ + 0.5D + SPAWN_DZ[i]);
            if (h != null) {
                IN.add(h);
            }
        }
        out = spawnHusk(PX + 0.5D + OUT_DX, PZ + 0.5D + OUT_DZ);
        failed += check("C1 三个范围内 husk + 一个范围外 husk 都造出来了（" + IN.size() + " + "
                + (out != null ? 1 : 0) + "）", IN.size() == 3 && out != null);

        hpBefore.clear();
        for (Husk h : IN) {
            hpBefore.add(h.getHealth());
        }
        outHpBefore = out.getHealth();
        outYBefore = out.getY();
        groupYBefore = IN.get(0).getY();
        playerHpBefore = player.getHealth();

        double n = ShockwaveManager.baseAttackDamage(player);
        expectedDamage = (float) (n + 12.0D);
        say(TAG + "      n（玩家基础伤害，不含手持装备）= " + n + " ⇒ 这一下应当各掉 "
                + expectedDamage + " 点");
        say(TAG + "      （参考：拿剑时 getAttributeValue(ATTACK_DAMAGE) = "
                + player.getAttributeValue(Attributes.ATTACK_DAMAGE) + "，那个值含武器、不当判据）");

        player.setShiftKeyDown(true);
        InteractionResultHolder<ItemStack> r = sword.getItem().use(level, player, InteractionHand.MAIN_HAND);
        player.setShiftKeyDown(false);
        say(TAG + "      右键结果 = " + r.getResult());
        // ⚠ 服务端这一侧的正确期望是 **CONSUME**，不是 SUCCESS：
        //   `InteractionResultHolder.sidedSuccess(stack, false)` = 客户端 SUCCESS / **服务端 CONSUME**
        //   （原版那条"客户端预演成功、服务端只认领"的写法，斧子/剑那两处用的也是它）。
        //   第一版探针写成 SUCCESS ⇒ 假红。冷却中被拒那一支仍然是 PASS，两者刚好区分得开。
        failed += check("C2 出手成功（服务端结果是 CONSUME）", r.getResult() == InteractionResult.CONSUME,
                String.valueOf(r.getResult()));

        // ① 冷却
        failed += check("C3 进了冷却（原版物品冷却）", player.getCooldowns().isOnCooldown(sword.getItem()));
        float pct = player.getCooldowns().getCooldownPercent(sword.getItem(), 0.0F);
        say(TAG + "      冷却进度 = " + pct + "（6 秒 = 120 tick，刚出手应当接近 1.0）");
        failed += check("C4 冷却进度 > 0.9（说明是刚上的 6 秒）", pct > 0.9F, String.valueOf(pct));

        // ② 伤害 / 状态 / 速度
        for (int i = 0; i < IN.size(); i++) {
            Husk h = IN.get(i);
            float lost = hpBefore.get(i) - h.getHealth();
            // ⚠ 掉血要过**原版护甲算式**再比：husk 自带 2 点护甲（僵尸那一族的基值），
            //   13 点"税前"伤害实测掉 **12.792**（= 13 × 0.984，正是原版
            //   `CombatRules.getDamageAfterAbsorb` 在 2 点护甲下的结果）。
            //   第一版直接拿 13.0 比 ⇒ 假红。这里**不自己重写公式**，直接调原版那一个方法。
            net.minecraft.world.damagesource.DamageSource src =
                    level.damageSources().playerAttack(player);
            float after = net.minecraft.world.damagesource.CombatRules.getDamageAfterAbsorb(
                    h, expectedDamage, src, h.getArmorValue(),
                    (float) h.getAttributeValue(Attributes.ARMOR_TOUGHNESS));
            say(TAG + "      husk#" + (i + 1) + " 税前 " + expectedDamage + " → 过护甲（"
                    + h.getArmorValue() + " 点）后应当掉 " + after + "，实测掉 " + lost);
            failed += check("C5." + (i + 1) + " 范围内 husk#" + (i + 1) + " 掉血 = " + after
                    + "（税前 n+12 = " + expectedDamage + "）", Math.abs(lost - after) < 1.0E-4F);
            MobEffectInstance blind = h.getEffect(MobEffects.BLINDNESS);
            MobEffectInstance slow = h.getEffect(MobEffects.MOVEMENT_SLOWDOWN);
            failed += check("C6." + (i + 1) + " 失明挂上了（时长 " + dur(blind) + " tick，要 80）",
                    blind != null && blind.getDuration() == 80);
            failed += check("C7." + (i + 1) + " 缓慢挂上了（时长 " + dur(slow) + " tick，要 80）",
                    slow != null && slow.getDuration() == 80);
            Vec3 v = h.getDeltaMovement();
            double awayX = h.getX() - player.getX();
            double awayZ = h.getZ() - player.getZ();
            double dot = v.x * awayX + v.z * awayZ;
            say(TAG + "      husk#" + (i + 1) + " 速度 = (" + round(v.x) + ", " + round(v.y) + ", "
                    + round(v.z) + ")，朝外点积 = " + round(dot));
            failed += check("C8." + (i + 1) + " 被向上击飞（速度 y > 0.3）", v.y > 0.3D,
                    String.valueOf(round(v.y)));
            failed += check("C9." + (i + 1) + " 水平方向是背离玩家的（点积 > 0）", dot > 0.0D,
                    String.valueOf(round(dot)));
        }

        // ③ 负向对照：范围外那个一点没动
        failed += check("C10 范围外 husk 血没掉（" + outHpBefore + " → " + out.getHealth() + "）",
                Math.abs(out.getHealth() - outHpBefore) < 1.0E-4F);
        failed += check("C11 范围外 husk 没有失明", !out.hasEffect(MobEffects.BLINDNESS));
        failed += check("C12 范围外 husk 没有缓慢", !out.hasEffect(MobEffects.MOVEMENT_SLOWDOWN));
        failed += check("C13 范围外 husk 没被向上击飞（速度 y < 0.3）",
                out.getDeltaMovement().y < 0.3D, String.valueOf(round(out.getDeltaMovement().y)));

        // ④ 自己
        failed += check("C14 自己没掉血（" + playerHpBefore + " → " + player.getHealth() + "）",
                Math.abs(player.getHealth() - playerHpBefore) < 1.0E-4F);
        failed += check("C15 自己身上没有被这一下带上来的失明/缓慢",
                !player.hasEffect(MobEffects.BLINDNESS)
                        && !player.hasEffect(MobEffects.MOVEMENT_SLOWDOWN));
    }

    /** 出手后 10 tick：验"真的离地了"（端到端，而不是"我设了速度"）。 */
    private static void phaseFlight() {
        double rise = IN.get(0).getY() - groupYBefore;
        say(TAG + "======== C 猛击：10 tick 之后的位移 ========");
        say(TAG + "      范围内 husk#1 起飞高度 = " + round(rise) + " 格");
        failed += check("C16 10 tick 之后它真的离地了（> 1.5 格）", rise > 1.5D, String.valueOf(round(rise)));
        double outMove = Math.abs(out.getY() - outYBefore);
        failed += check("C17 范围外那个原地不动（竖直位移 " + round(outMove) + " 格）", outMove < 0.5D);
    }

    /** 冷却中再按一次：必须被拒。 */
    private static void phaseCooldown() {
        say(TAG + "======== C 猛击：冷却中再按一次 ========");
        float before = IN.get(0).getHealth();
        player.setShiftKeyDown(true);
        InteractionResultHolder<ItemStack> r = sword.getItem().use(level, player, InteractionHand.MAIN_HAND);
        player.setShiftKeyDown(false);
        say(TAG + "      右键结果 = " + r.getResult() + "（冷却中应当是 PASS）");
        failed += check("C18 冷却中被拒（结果 = PASS）", r.getResult() == InteractionResult.PASS);
        failed += check("C19 冷却中目标没再掉血（" + before + " → " + IN.get(0).getHealth() + "）",
                Math.abs(IN.get(0).getHealth() - before) < 1.0E-4F);
        // 冷却清掉之后还能再用（证明"拒"是冷却造成的，不是坏了）
        // ⚠ 换一个**满血的新 husk** 来量这一下：原来那三个已经被打过两轮，
        //   第一个只剩 7.2 血，再挨一下会**直接死** ⇒ 掉血量只有 7.208 而不是 13（第一版假红）。
        Husk fresh = spawnHusk(PX + 0.5D + 2.0D, PZ + 0.5D - 2.0D);
        float hp0 = fresh == null ? -1.0F : fresh.getHealth();
        player.getCooldowns().removeCooldown(sword.getItem());
        float hp2 = IN.get(0).getHealth();
        player.setShiftKeyDown(true);
        InteractionResultHolder<ItemStack> r2 = sword.getItem().use(level, player, InteractionHand.MAIN_HAND);
        player.setShiftKeyDown(false);
        float lost = hp2 - IN.get(0).getHealth();
        float freshLost = fresh == null ? -1.0F : hp0 - fresh.getHealth();
        say(TAG + "      新目标：" + hp0 + " → " + (fresh == null ? -1.0F : fresh.getHealth())
                + "（掉 " + freshLost + "）");
        failed += check("C20 冷却清掉后立刻又能用（新目标掉 " + freshLost + "，结果 "
                        + r2.getResult() + "）",
                r2.getResult() == InteractionResult.CONSUME && freshLost > 0.0F);
        say(TAG + "      （参考：原来那三个又挨了一下，第一个掉了 " + lost + "）");
    }

    // ============================================================
    //  节拍
    // ============================================================
    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (!started || finished || t0 < 0L) {
            return;
        }
        long dt = level.getGameTime() - t0;
        try {
            if (phase == 0 && dt >= 20L) {
                phase = 1;
                phaseSlam();
            } else if (phase == 1 && dt >= 30L) {
                phase = 2;
                phaseFlight();
            } else if (phase == 2 && dt >= 40L) {
                phase = 3;
                phaseCooldown();
                finish(event.getServer());
            }
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
            finish(event.getServer());
        }
    }

    // ============================================================
    //  工具
    // ============================================================
    private static Husk spawnHusk(double x, double z) {
        Husk h = EntityType.HUSK.create(level);
        if (h == null) {
            return null;
        }
        h.moveTo(x, PY + 1, z, 0.0F, 0.0F);
        // ⚠⚠ **不能**用 setNoAi(true)：
        //   `Mob.isEffectiveAi()` 在 NoAI 时是 false（`return super.isEffectiveAi() && !this.isNoAi()`），
        //   而 `LivingEntity.travel()` 的第一行是 `if (this.isControlledByLocalInstance())` ——
        //   于是 NoAI 的生物**根本不物理位移**：我在它身上设的速度一个 tick 都不会生效。
        //   第一版探针就是栽在这儿：C8（速度 y = 0.8 设上了）过了，C16（10 tick 后真离地）却是 0.0。
        //   改成"把移动速度与攻击力按 0 钉住"：它走不动、打不动人，但重力与击飞照常算。
        if (h.getAttribute(Attributes.MOVEMENT_SPEED) != null) {
            h.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(0.0D);
        }
        if (h.getAttribute(Attributes.ATTACK_DAMAGE) != null) {
            h.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(0.0D);
        }
        h.setTarget(null);
        h.setPersistenceRequired();
        level.addFreshEntity(h);
        return h;
    }

    private static void buildArena() {
        level.getChunkAt(new BlockPos(PX, PY, PZ));
        int cx = PX >> 4;
        int cz = PZ >> 4;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                level.setChunkForced(cx + dx, cz + dz, true);
            }
        }
        for (int dx = -7; dx <= 7; dx++) {
            for (int dz = -7; dz <= 7; dz++) {
                level.setBlockAndUpdate(new BlockPos(PX + dx, PY, PZ + dz),
                        Blocks.OAK_PLANKS.defaultBlockState());
                for (int dy = 1; dy <= 5; dy++) {
                    level.setBlockAndUpdate(new BlockPos(PX + dx, PY + dy, PZ + dz),
                            Blocks.AIR.defaultBlockState());
                }
            }
        }
        say(TAG + "试验场：悬空木平台 " + new BlockPos(PX, PY, PZ) + "（15×15，起跳净空 5 格）");
    }

    private static String effectName(Holder<MobEffect> e) {
        return e.unwrapKey().map(k -> k.location().getPath()).orElse("?");
    }

    private static int dur(MobEffectInstance i) {
        return i == null ? -1 : i.getDuration();
    }

    private static double round(double v) {
        return Math.round(v * 1000.0D) / 1000.0D;
    }

    private static int check(String name, boolean ok) {
        say(TAG + (ok ? "  [OK]   " : "  [FAIL] ") + name);
        return ok ? 0 : 1;
    }

    private static int check(String name, boolean ok, String detail) {
        say(TAG + (ok ? "  [OK]   " : "  [FAIL] ") + name + "   实测：" + detail);
        return ok ? 0 : 1;
    }

    private static void say(String line) {
        System.out.println(line);
        report.append(line).append('\n');
    }

    private static void flush() {
        try {
            Files.write(Paths.get(REPORT), report.toString().getBytes(StandardCharsets.UTF_8));
        } catch (Throwable t) {
            System.out.println(TAG + "report write failed: " + t);
        }
    }

    /** 收尾：写报告 + 正常退出服务器（报告必须在 halt 之前落盘）。 */
    private static void finish(net.minecraft.server.MinecraftServer server) {
        if (finished) {
            return;
        }
        finished = true;
        say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
        flush();
        say(TAG + "report: " + REPORT);
        say(TAG + "done, halting server");
        server.halt(false);
    }
}
