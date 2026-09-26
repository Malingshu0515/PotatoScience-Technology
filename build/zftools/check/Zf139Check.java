package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageEffects;
import net.minecraft.world.damagesource.DamageScaling;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.damagesource.DeathMessageType;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.damagesource.DamageContainer;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.entity.living.LivingFallEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/**
 * ⚠️ <b>诊断工具（ZF138 的临时探针）</b>：振金套加强的端到端取证。
 *
 * <p>用户原话：「振金套你看看能不能略微加强一下 现在地位太尴尬了 比星璨麻烦很多
 * 却大大不如晚上的星璨 简直就是个白板」，拍板「乙方案 + 一条新套装效果」：
 * 护甲值各 +1（3/8/6/3 → 4/9/7/4）、满套常驻抗性提升 I、满套免疫摔落伤害、
 * 挨打 10% 概率把这一击的伤害原样还给攻击者（被反伤打死的人文案是「踢到了铁板」）。</p>
 *
 * <p>本探针要证的六件事（每一条都在**真服务端**上跑）：</p>
 * <ol>
 *   <li><b>伤害类型真的加载了</b>：自定义的 {@code potato_s_t:vibranium_reflect} 在数据包注册表里
 *       取得到，且 msgId / scaling / exhaustion / effects 四个字段与 JSON 逐字对上；</li>
 *   <li><b>护甲值 24</b>：穿满四件后玩家属性里的 ARMOR 是 24（逐件 4/9/7/4），
 *       韧性 12、击退抗性 0.4；对照组：全套**原版下界合金**是 20（证明"比下界合金高 4"）；</li>
 *   <li><b>常驻抗性 I</b>：在真事件总线上 post 一个 {@code PlayerTickEvent.Post} ⇒ 玩家身上出现
 *       抗性提升 I、时长 320；身上已有抗性 III 时**不会被压回 I**；破套（摘一件）时**不给**；</li>
 *   <li><b>免疫摔落</b>：满套时 {@code causeFallDamage} 返回 false 且血量不变（100 点高度也一样）；
 *       破套时照常掉血（负向对照）；</li>
 *   <li><b>10% 反伤</b>：真受击 2000 次 ⇒ 反伤次数落在 [140, 260]（10% ± 4.5σ）；
 *       四条排除名单各跑 400 次 ⇒ 必须**一次都不反**（弹射物 / 爆炸 / 反伤本身 / 没掉血那一下），
 *       同时用同口径的"普通攻击"400 次跑出一个非零值当**灵敏度对照**（否则"0 次"可能是假绿）；
 *       反伤数值 = 原始伤害（裸装攻击者挨 4.0 就掉 4.0）；</li>
 *   <li><b>死亡文案</b>：被反伤打死的人，{@code CombatTracker.getDeathMessage()} 的键是
 *       {@code death.attack.potato_s_t.vibranium_reflect}，且 {@code %1$s} 解析出来是他自己的名字。</li>
 * </ol>
 *
 * <p>另外顺手钉一条**架构证据**：无敌帧里那"更轻的第二下"，{@code LivingIncomingDamageEvent}
 * 照触发、但走不到 {@code LivingDamageEvent.Post}（血量也不掉）——
 * 这正是"反伤必须挂 Post"的理由（见 {@code ModVibraniumSet} 类注释第八节）。</p>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf138Check.register();`，跑完用
 * {@code _zf138_unprobe.py} 摘掉（**先抄进 `build/zftools/check/` 再删**）。</p>
 */
public final class Zf138Check {

    private static final String TAG = "[A138] ";
    private static final String NS = "potato_s_t";

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf138_probe_utf8.txt";

    /** 概率统计的样本量与接受区间（10% ⇒ 2000 次约 200，±4.5σ ≈ ±60）。 */
    private static final int TRIALS = 2000;
    private static final int LO = 140;
    private static final int HI = 260;
    /** 排除名单的样本量：真按 10% 走，400 次里应当出现约 40 次 —— 判据是"一次都没有"。 */
    private static final int NEG_TRIALS = 400;

    private static boolean registered;
    private static int passed;
    private static int failed;

    /** 探针自己挂的两个计数器（用来证明"事件到底触发没触发"）。 */
    private static int incomingSeen;
    private static int postSeen;
    private static int playerTickSeen;
    private static int equipChangeSeen;

    /** 死亡**那一刻**抓到的文案（见 {@link #onAnyDeath} 的注释）。 */
    private static Component lastDeathMessage;

    private Zf138Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void check(String name, boolean ok) {
        if (ok) {
            passed++;
        } else {
            failed++;
        }
        say(TAG + (ok ? "[OK]   " : "[FAIL] ") + name);
    }

    private static void check(String name, boolean ok, String detail) {
        if (ok) {
            passed++;
            say(TAG + "[OK]   " + name);
        } else {
            failed++;
            say(TAG + "[FAIL] " + name + "　" + detail);
        }
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF138 探针报告（振金套加强：护甲 24 / 抗性 I / 免摔落 / 10% 反伤）· UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "全绿" : failed + " 条 FAIL") + "（通过 " + passed + "）\n\n");
            w.write(REPORT.toString());
        } catch (Throwable t) {
            say(TAG + "report write failed: " + t);
        }
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            NeoForge.EVENT_BUS.register(Zf138Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    /** 探针自己的观察窗（证明事件触发与否，不参与业务）。 */
    @SubscribeEvent
    public static void onAnyIncoming(LivingIncomingDamageEvent event) {
        incomingSeen++;
    }

    @SubscribeEvent
    public static void onAnyPost(LivingDamageEvent.Post event) {
        postSeen++;
    }

    @SubscribeEvent
    public static void onAnyPlayerTick(PlayerTickEvent.Post event) {
        playerTickSeen++;
    }

    @SubscribeEvent
    public static void onAnyEquipChange(
            net.neoforged.neoforge.event.entity.living.LivingEquipmentChangeEvent event) {
        equipChangeSeen++;
    }

    /**
     * 死亡**那一刻**的死亡文案（探针用）。
     *
     * <p>⚠ 为什么非要挂这个事件、而不是事后问 {@code getCombatTracker()}：
     * {@code ServerPlayer.die} 里读文案的顺序是「先 {@code CommonHooks.onLivingDeath}
     * （就是本事件）→ 再 {@code getCombatTracker().getDeathMessage()} → 最后 {@code super.die}」，
     * 而 {@code LivingEntity.die} 里会调 {@code CombatTracker.recheckStatus()}，
     * 那一句在 {@code !mob.isAlive()} 时**把 entries 清空** ⇒
     * **死完之后再问，拿到的永远是 {@code death.attack.generic}**（探针第一版就是这么假红的）。</p>
     */
    @SubscribeEvent
    public static void onAnyDeath(
            net.neoforged.neoforge.event.entity.living.LivingDeathEvent event) {
        lastDeathMessage = event.getEntity().getCombatTracker().getDeathMessage();
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            run(event, level);
        } catch (Throwable t) {
            failed++;
            say(TAG + "[FAIL] 探针自己抛异常：" + t);
            t.printStackTrace(System.out);
        }
        say(TAG + "done, halting server");
        flushReport();
        event.getServer().halt(false);
    }

    // ============================================================
    //  工具
    // ============================================================

    private static ServerPlayer fake(ServerStartedEvent event, ServerLevel level, String name) {
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8)), name);
        ServerPlayer player = new ServerPlayer(event.getServer(), level, profile,
                ClientInformation.createDefault());
        // ⚠ 必须有这一句（ZF70 的教训）：无头服务端里 new 出来的玩家没有连接，
        //   某些路径（配方奖励 / 统计）会 NPE。
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                event.getServer(), conn, player,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        // ⚠ 生存模式：创造/旁观带 abilities.invulnerable ⇒ isInvulnerableTo 恒真 ⇒ 一点血都掉不了
        player.setGameMode(GameType.SURVIVAL);
        return player;
    }

    private static void wearVibranium(ServerPlayer p) {
        p.setItemSlot(EquipmentSlot.HEAD, new ItemStack(ModArmorItems.VIBRANIUM_HELMET.get()));
        p.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModArmorItems.VIBRANIUM_CHESTPLATE.get()));
        p.setItemSlot(EquipmentSlot.LEGS, new ItemStack(ModArmorItems.VIBRANIUM_LEGGINGS.get()));
        p.setItemSlot(EquipmentSlot.FEET, new ItemStack(ModArmorItems.VIBRANIUM_BOOTS.get()));
    }

    private static void reset(ServerPlayer wearer, ServerPlayer attacker) {
        wearer.setHealth(wearer.getMaxHealth());
        attacker.setHealth(attacker.getMaxHealth());
        wearer.invulnerableTime = 0;
        attacker.invulnerableTime = 0;
    }

    /**
     * 跑 n 次真受击，返回 {@code [反伤次数, 穿戴者真的掉血的次数]}。
     *
     * <p>第二个数是**灵敏度对照**：负向用例里"反了 0 次"只有在"这一下确实打进去了"时才有意义 ——
     * 否则（比如出生保护没烧掉、人已经死了）0 次是**假绿**。本探针第一版就吃过这个亏：
     * 13 条红里有一半是"伤害根本没进去"造成的。</p>
     */
    private static int[] countReflects(ServerPlayer wearer, ServerPlayer attacker,
                                       DamageSource src, float amount, int n) {
        int hits = 0;
        int landed = 0;
        for (int i = 0; i < n; i++) {
            reset(wearer, attacker);
            float before = attacker.getHealth();
            float wBefore = wearer.getHealth();
            wearer.hurt(src, amount);
            if (attacker.getHealth() < before) {
                hits++;
            }
            if (wearer.getHealth() < wBefore) {
                landed++;
            }
        }
        return new int[]{hits, landed};
    }

    /** 直接在总线上 post 一个 {@code LivingDamageEvent.Post}（绕过护甲/无敌帧，专门测排除名单）。 */
    private static int countReflectsOnSyntheticEvent(ServerPlayer wearer, ServerPlayer attacker,
                                                     DamageSource src, float original,
                                                     float newDamage, int n) {
        int hits = 0;
        for (int i = 0; i < n; i++) {
            reset(wearer, attacker);
            float before = attacker.getHealth();
            DamageContainer c = new DamageContainer(src, original);
            c.setNewDamage(newDamage);
            NeoForge.EVENT_BUS.post(new LivingDamageEvent.Post(wearer, c));
            if (attacker.getHealth() < before) {
                hits++;
            }
        }
        return hits;
    }

    private static String keyOf(Component c) {
        return c.getContents() instanceof net.minecraft.network.chat.contents.TranslatableContents tc
                ? tc.getKey() : "<字面量>" + c.getString();
    }

    private static String itemId(ItemStack s) {
        return net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(s.getItem()).toString();
    }

    /**
     * 真给假玩家跑一 tick 并吞掉异常。
     *
     * <p>⚠ <b>必须调 {@code doTick()}，不是 {@code tick()}</b> —— 这是本轮探针最大的一个坑，
     * 两条症状都出自它（`ServerPlayer.java:505-546` 与 `:568-572`）：</p>
     * <ul>
     *   <li>{@code ServerPlayer.tick()} **覆写了** {@code Player.tick()} 而且**不调 super.tick()**
     *       （它只做连接期的杂事：gameMode.tick / spawnInvulnerableTime-- / 容器同步 / 相机）。
     *       真正的玩家 tick 是 {@code doTick()}（由 {@code ServerGamePacketListenerImpl.tick()} 调），
     *       它第 571 行才 {@code super.tick()} ⇒ 才会触发 {@code PlayerTickEvent}、
     *       才会走到 {@code LivingEntity.tick()} 里的 {@code detectEquipmentUpdates()}。
     *       ⇒ 只调 {@code tick()} 的话：**属性修饰符永远挂不上（ARMOR 恒 0）、套装效果一帧都不跑**。</li>
     *   <li>{@code ServerPlayer} 还有一个 {@code private int spawnInvulnerableTime = 60;}
     *       （出生保护），而 {@code ServerPlayer.hurt} 第 794 行就是
     *       {@code if (!flag && this.spawnInvulnerableTime > 0 && !BYPASSES_INVULNERABILITY) return false;}
     *       —— **除了摔落**（dev 服务端 isDedicatedServer + pvp 都成立 ⇒ 那个 {@code flag} 为真）
     *       之外，任何伤害在头 3 秒里都被这一句挡掉。这就是"矩阵里只有 fall 能打进去"的原因。
     *       这个字段是 private，探针不去反射它，改用 {@link #settle} 跑满 61 帧。</li>
     * </ul>
     */
    private static void tickQuietly(ServerPlayer p, String who) {
        try {
            p.doTick();
        } catch (Throwable t) {
            failed++;
            say(TAG + "[FAIL] 给「" + who + "」跑一 tick 时抛异常：" + t);
        }
    }

    /**
     * 假玩家"入场"：跑满 61 帧，把 60 tick 的出生保护烧掉，顺手把装备属性挂上。
     *
     * <p>⚠ <b>必须把两个 tick 都跑</b>，这两个方法在 {@code ServerPlayer} 上是**分开的**：
     * {@code ServerPlayer.tick()} 覆写了 {@code Player.tick()} 而且不调 super（只做连接期杂事，
     * 其中就包括 {@code spawnInvulnerableTime--}）；真正的玩家 tick 是 {@code doTick()}
     * （{@code super.tick()} → {@code PlayerTickEvent} + {@code LivingEntity.tick()} 里的
     * {@code detectEquipmentUpdates()}）。服务端就是这么分工的：
     * {@code ServerGamePacketListenerImpl.tick()} 调 {@code doTick()}，关卡实体循环调 {@code tick()}。</p>
     *
     * <p>第一版只跑了 {@code doTick()} ⇒ 出生保护一点没减（还是 60）⇒
     * 除了摔落（dev 服务端 isDedicatedServer + pvp 都成立，那一下被 {@code flag} 放行）
     * 之外，**所有伤害都被 {@code ServerPlayer.hurt} 第 794 行挡掉**，
     * 表现为"反伤 0 次"这种看着像功能没生效的假红。</p>
     */
    private static void settle(ServerPlayer p, String who) {
        try {
            for (int i = 0; i < 61; i++) {
                p.tick();      // ServerPlayer.tick()：出生保护 -1（这一步不能少）
                p.doTick();    // 真玩家的那一 tick：事件 + 装备属性
            }
        } catch (Throwable t) {
            failed++;
            say(TAG + "[FAIL] 给「" + who + "」跑满 61 帧时抛异常：" + t);
        }
    }

    // ============================================================
    //  主体
    // ============================================================

    private static void run(ServerStartedEvent event, ServerLevel level) {
        Registry<DamageType> types = level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE);
        ResourceKey<DamageType> key = ModVibraniumSet.VIBRANIUM_REFLECT;

        ServerPlayer wearer = fake(event, level, "zf138wear");
        ServerPlayer attacker = fake(event, level, "zf138atk");
        settle(attacker, "攻击者");
        wearVibranium(wearer);
        // ⚠ 把时间钉在白天：星璨钢那套的"夜晚每件给抗性 I"走的是同一个 PlayerTickEvent.Post，
        //   本探针在 ③/⑩ 会 post 这个事件 —— 要是世界里正好是夜里，
        //   "星璨钢不会被塞抗性"那条就会假红（§4.53 的兄弟：先把自己这边的环境变量钉住）。
        level.setDayTime(6000L);
        // 入场：烧掉出生保护 + 挂上装备属性（见 tickQuietly / settle 的注释）
        settle(wearer, "振金穿戴者");

        say(TAG + "① 自定义伤害类型（数据包真的加载了）");
        Holder<DamageType> holder = null;
        try {
            holder = types.getHolderOrThrow(key);
            check("vibranium_reflect 在数据包注册表里取得到（getHolderOrThrow 没抛）", true);
        } catch (Throwable t) {
            check("vibranium_reflect 在数据包注册表里取得到（getHolderOrThrow 没抛）", false,
                    "抛了：" + t);
            return;
        }
        DamageType type = holder.value();
        check("message_id = potato_s_t.vibranium_reflect（实际 " + type.msgId() + "）",
                type.msgId().equals("potato_s_t.vibranium_reflect"));
        check("scaling = WHEN_CAUSED_BY_LIVING_NON_PLAYER（实际 " + type.scaling() + "）",
                type.scaling() == DamageScaling.WHEN_CAUSED_BY_LIVING_NON_PLAYER);
        check("exhaustion = 0.1（实际 " + type.exhaustion() + "）",
                Math.abs(type.exhaustion() - 0.1F) < 1.0E-6F);
        check("effects = THORNS（挨这一下的人听到的是「打铁板」那一声，实际 " + type.effects() + "）",
                type.effects() == DamageEffects.THORNS);
        check("death_message_type = DEFAULT（实际 " + type.deathMessageType() + "）",
                type.deathMessageType() == DeathMessageType.DEFAULT);
        DamageSource reflectSrc = new DamageSource(holder, wearer);
        check("构造出来的伤害源 is(VIBRANIUM_REFLECT) == true", reflectSrc.is(key));

        // ------------------------------------------------------------
        // ⓪ 诊断段：把「装备 → 属性」「受击 → 事件 → 反伤」两条链逐段打出来。
        //    只打印、不判分 —— 第一版探针出 13 条红之后，这一段用来一次问清楚
        //    "到底断在哪一环"，省得一轮一轮猜（每跑一次 runServer 要两分钟）。
        // ------------------------------------------------------------
        say(TAG + "⓪ 诊断（只打印，不判分）");
        wearVibranium(wearer);
        int pt0 = playerTickSeen;
        int ec0 = equipChangeSeen;
        tickQuietly(wearer, "诊断用 tick");
        say(TAG + "  装备栏：" + itemId(wearer.getItemBySlot(EquipmentSlot.HEAD)) + " / "
                + itemId(wearer.getItemBySlot(EquipmentSlot.CHEST)) + " / "
                + itemId(wearer.getItemBySlot(EquipmentSlot.LEGS)) + " / "
                + itemId(wearer.getItemBySlot(EquipmentSlot.FEET)));
        ItemStack helm = wearer.getItemBySlot(EquipmentSlot.HEAD);
        say(TAG + "  头盔的 ItemAttributeModifiers = " + helm.getAttributeModifiers().modifiers());
        var armorAttr = wearer.getAttribute(Attributes.ARMOR);
        say(TAG + "  ARMOR 属性实例 = " + (armorAttr == null ? "null" : armorAttr.getModifiers()));
        say(TAG + "  tick 期间：PlayerTickEvent.Post +" + (playerTickSeen - pt0)
                + "；LivingEquipmentChangeEvent +" + (equipChangeSeen - ec0)
                + "；ARMOR 现值 " + wearer.getArmorValue());
        DamageSource diagMelee = level.damageSources().playerAttack(attacker);
        float h0 = wearer.getHealth();
        int in0d = incomingSeen;
        int po0d = postSeen;
        boolean hr = wearer.hurt(diagMelee, 4.0F);
        say(TAG + "  wearer.hurt(playerAttack, 4.0) = " + hr
                + "；血量 " + h0 + " → " + wearer.getHealth()
                + "；incoming +" + (incomingSeen - in0d) + "；post +" + (postSeen - po0d));
        float a0 = attacker.getHealth();
        int in1d = incomingSeen;
        boolean ar = attacker.hurt(reflectSrc, 4.0F);
        say(TAG + "  attacker.hurt(reflect, 4.0) = " + ar
                + "；血量 " + a0 + " → " + attacker.getHealth()
                + "；incoming +" + (incomingSeen - in1d));
        say(TAG + "  attacker：模式 " + attacker.gameMode.getGameModeForPlayer()
                + "；abilities.invulnerable=" + attacker.getAbilities().invulnerable
                + "；isRemoved=" + attacker.isRemoved()
                + "；isDeadOrDying=" + attacker.isDeadOrDying()
                + "；难度=" + level.getDifficulty());
        say(TAG + "  wearer：模式 " + wearer.gameMode.getGameModeForPlayer()
                + "；isRemoved=" + wearer.isRemoved()
                + "；isDeadOrDying=" + wearer.isDeadOrDying());
        // 伤害源矩阵：哪一类源能进到事件、哪一类进不去 —— 一次问清楚
        DamageSource[] srcs = {level.damageSources().fall(), level.damageSources().generic(),
                level.damageSources().playerAttack(attacker), level.damageSources().mobAttack(attacker),
                level.damageSources().magic()};
        String[] snames = {"fall", "generic", "playerAttack(玩家)", "mobAttack(玩家)", "magic"};
        for (int i = 0; i < srcs.length; i++) {
            reset(wearer, attacker);
            float b = wearer.getHealth();
            int ii = incomingSeen;
            int pp = postSeen;
            boolean rr = wearer.hurt(srcs[i], 4.0F);
            say(TAG + "  源=" + snames[i] + " ⇒ hurt=" + rr
                    + "，血 " + b + "→" + wearer.getHealth()
                    + "，incoming+" + (incomingSeen - ii) + "，post+" + (postSeen - pp)
                    + "，isInvulnerableTo=" + wearer.isInvulnerableTo(srcs[i])
                    + "，scalesWithDifficulty=" + srcs[i].scalesWithDifficulty());
        }
        say(TAG + "  wearer：invulnerableTime=" + wearer.invulnerableTime
                + "；hurtTime=" + wearer.hurtTime
                + "；isInvulnerable()=" + wearer.isInvulnerable()
                + "；level.isClientSide=" + wearer.level().isClientSide
                + "；maxHealth=" + wearer.getMaxHealth()
                + "；lastHurt 不可见(protected)");
        reset(wearer, attacker);

        say(TAG + "② 护甲值：逐件 4/9/7/4，合计 24（对照组：原版下界合金 20）");
        check("穿满四件后 ARMOR 属性 = 24（实际 " + wearer.getArmorValue() + "）",
                wearer.getArmorValue() == 24);
        int[] want = {4, 9, 7, 4};
        EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                EquipmentSlot.LEGS, EquipmentSlot.FEET};
        boolean defOk = true;
        StringBuilder defGot = new StringBuilder();
        for (int i = 0; i < slots.length; i++) {
            ItemStack s = wearer.getItemBySlot(slots[i]);
            int d = (s.getItem() instanceof net.minecraft.world.item.ArmorItem a) ? a.getDefense() : -1;
            defGot.append(d).append(' ');
            defOk &= d == want[i];
        }
        check("逐件护甲值 = 4 / 9 / 7 / 4（实际 " + defGot.toString().trim() + "）", defOk);
        check("ARMOR_TOUGHNESS = 12.0（实际 " + wearer.getAttributeValue(Attributes.ARMOR_TOUGHNESS) + "）",
                Math.abs(wearer.getAttributeValue(Attributes.ARMOR_TOUGHNESS) - 12.0D) < 1.0E-6D);
        check("KNOCKBACK_RESISTANCE = 0.4（实际 " + wearer.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) + "）",
                Math.abs(wearer.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE) - 0.4D) < 1.0E-6D);
        ServerPlayer netherite = fake(event, level, "zf138net");
        netherite.setItemSlot(EquipmentSlot.HEAD, new ItemStack(Items.NETHERITE_HELMET));
        netherite.setItemSlot(EquipmentSlot.CHEST, new ItemStack(Items.NETHERITE_CHESTPLATE));
        netherite.setItemSlot(EquipmentSlot.LEGS, new ItemStack(Items.NETHERITE_LEGGINGS));
        netherite.setItemSlot(EquipmentSlot.FEET, new ItemStack(Items.NETHERITE_BOOTS));
        settle(netherite, "下界合金对照");
        check("对照：全套原版下界合金 = 20（实际 " + netherite.getArmorValue() + "）",
                netherite.getArmorValue() == 20);
        check("⇒ 振金比下界合金多 4 点护甲（" + wearer.getArmorValue() + " - "
                + netherite.getArmorValue() + " = 4）",
                wearer.getArmorValue() - netherite.getArmorValue() == 4);

        say(TAG + "③ 满套常驻抗性提升 I（真 tick 一次，走真事件总线）");
        wearer.removeAllEffects();
        tickQuietly(wearer, "振金穿戴者");
        MobEffectInstance eff = wearer.getEffect(MobEffects.DAMAGE_RESISTANCE);
        check("真 tick 一帧 ⇒ 身上出现抗性提升（PlayerTickEvent.Post 真的挂上了）", eff != null);
        if (eff != null) {
            check("等级 = I（amplifier 0，实际 " + eff.getAmplifier() + "）", eff.getAmplifier() == 0);
            check("时长 = 320 tick（16 s，实际 " + eff.getDuration() + "）", eff.getDuration() == 320);
            check("ambient = true（粒子淡）且 visible = true（图标看得见）",
                    eff.isAmbient() && eff.isVisible());
        }
        wearer.removeAllEffects();
        wearer.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 600, 2, true, true));
        tickQuietly(wearer, "振金穿戴者");
        MobEffectInstance high = wearer.getEffect(MobEffects.DAMAGE_RESISTANCE);
        check("身上已有抗性 III 时不会被压回 I（amplifier 仍是 2，实际 "
                + (high == null ? "无" : high.getAmplifier()) + "；剩余 "
                + (high == null ? "-" : high.getDuration()) + " tick）",
                // ⚠ 时长**不能写死 600**：tick 一帧就会 -1（LivingEntity.tick 会递减效果时长），
                //   第一版就是拿 `== 600` 判的 —— 一条自己造出来的假红（§4.106 的兄弟）。
                //   真正的判据是"没被换成那条 320 tick 的新实例"。
                high != null && high.getAmplifier() == 2 && high.getDuration() > 500);
        wearer.removeAllEffects();
        ItemStack kept = wearer.getItemBySlot(EquipmentSlot.CHEST);
        wearer.setItemSlot(EquipmentSlot.CHEST, ItemStack.EMPTY);
        tickQuietly(wearer, "振金穿戴者");
        check("破套（摘掉胸甲）时**不给**这个效果", wearer.getEffect(MobEffects.DAMAGE_RESISTANCE) == null);
        wearer.setItemSlot(EquipmentSlot.CHEST, kept);
        // 再补一刀（与 tick 无关的那条路）：直接在总线上 post 一个事件 —— 证明"挂载本身"没问题
        wearer.removeAllEffects();
        NeoForge.EVENT_BUS.post(new PlayerTickEvent.Post(wearer));
        check("直接在总线上 post PlayerTickEvent.Post 也补得上（挂载本身没问题）",
                wearer.getEffect(MobEffects.DAMAGE_RESISTANCE) != null);

        say(TAG + "④ 满套免疫摔落伤害");
        wearer.setHealth(wearer.getMaxHealth());
        float hpBefore = wearer.getHealth();
        boolean fell = wearer.causeFallDamage(100.0F, 1.0F, level.damageSources().fall());
        check("满套：causeFallDamage(100) 返回 false（没结算伤害，实际 " + fell + "）", !fell);
        check("满套：血量一点没掉（" + hpBefore + " → " + wearer.getHealth() + "）",
                Math.abs(wearer.getHealth() - hpBefore) < 1.0E-4F);
        LivingFallEvent fe = new LivingFallEvent(wearer, 100.0F, 1.0F);
        NeoForge.EVENT_BUS.post(fe);
        check("事件层：LivingFallEvent 被取消（这就是「连摔落音效都不放」的那条路）", fe.isCanceled());
        ItemStack keptChest = wearer.getItemBySlot(EquipmentSlot.CHEST);
        wearer.setItemSlot(EquipmentSlot.CHEST, ItemStack.EMPTY);
        tickQuietly(wearer, "破套对照");
        wearer.setHealth(wearer.getMaxHealth());
        boolean fell2 = wearer.causeFallDamage(6.0F, 1.0F, level.damageSources().fall());
        check("负向对照：破套时照常掉血（返回 true，血量 " + wearer.getHealth() + "）",
                fell2 && wearer.getHealth() < wearer.getMaxHealth());
        // ⚠ 摔落高度必须**打得死人才算数**、又必须**打不死人**：这里只要"掉了血"。
        //   第一版用的是 100 点 —— 穿戴者当场摔死，于是后面 ⑤~⑨ 全部静默失效
        //   （死人 hurt 恒返回 false）⇒ "反伤 0 次"看起来像功能没生效。
        //   这条断言就是那次教训的看门狗。
        check("负向对照没把穿戴者摔死（否则后面的反伤统计全是假红）", !wearer.isDeadOrDying());
        wearer.setItemSlot(EquipmentSlot.CHEST, keptChest);
        tickQuietly(wearer, "穿戴者复原");

        say(TAG + "⑤ 10% 反伤：真好血路径 2000 次");
        DamageSource melee = level.damageSources().playerAttack(attacker);
        int[] r5 = countReflects(wearer, attacker, melee, 4.0F, TRIALS);
        int hits = r5[0];
        check("**这一下真的打得进去**（" + TRIALS + " 次里穿戴者掉血 " + r5[1] + " 次 —— 0 就说明前面全白测）",
                r5[1] == TRIALS);
        check("真受击 " + TRIALS + " 次 ⇒ 反伤 " + hits + " 次，落在 [" + LO + ", " + HI + "]（≈10%）",
                hits >= LO && hits <= HI);

        say(TAG + "⑥ 反伤数值 = 这一击的原始伤害（裸装攻击者挨 4.0 就掉 4.0）");
        reset(wearer, attacker);
        float atkBefore = attacker.getHealth();
        wearer.hurt(melee, 4.0F);
        // 10% 才触发 ⇒ 可能这一下没反；循环到反一次为止（上限 200 次）
        for (int i = 0; i < 200 && attacker.getHealth() >= atkBefore; i++) {
            reset(wearer, attacker);
            wearer.hurt(melee, 4.0F);
        }
        float lost = atkBefore - attacker.getHealth();
        check("攻击者掉了 4.0 血（裸装无减免，实际 " + lost + "）", Math.abs(lost - 4.0F) < 1.0E-4F);

        say(TAG + "⑦ 排除名单：四条各 400 次，一次都不许反");
        DamageSource arrow = new DamageSource(types.getHolderOrThrow(DamageTypes.ARROW), attacker);
        DamageSource boom = new DamageSource(types.getHolderOrThrow(DamageTypes.PLAYER_EXPLOSION), attacker);
        DamageSource back = new DamageSource(holder, attacker);
        check("弹射物源真的带 is_projectile 标签", arrow.is(net.minecraft.tags.DamageTypeTags.IS_PROJECTILE));
        check("爆炸源真的带 is_explosion 标签", boom.is(net.minecraft.tags.DamageTypeTags.IS_EXPLOSION));
        int nArrow = countReflectsOnSyntheticEvent(wearer, attacker, arrow, 4.0F, 0.5F, NEG_TRIALS);
        int nBoom = countReflectsOnSyntheticEvent(wearer, attacker, boom, 4.0F, 0.5F, NEG_TRIALS);
        int nBack = countReflectsOnSyntheticEvent(wearer, attacker, back, 4.0F, 0.5F, NEG_TRIALS);
        int nZero = countReflectsOnSyntheticEvent(wearer, attacker, melee, 4.0F, 0.0F, NEG_TRIALS);
        // 灵敏度对照：同一个口子、同样 400 次，换个"没被排除"的来源 ⇒ 必须反出非零值
        int nCtrl = countReflectsOnSyntheticEvent(wearer, attacker, melee, 4.0F, 0.5F, NEG_TRIALS);
        check("弹射物来源：" + NEG_TRIALS + " 次反 " + nArrow + " 次（必须 0）", nArrow == 0);
        check("爆炸来源：" + NEG_TRIALS + " 次反 " + nBoom + " 次（必须 0）", nBoom == 0);
        check("反伤本身（递归保护）：" + NEG_TRIALS + " 次反 " + nBack + " 次（必须 0）", nBack == 0);
        check("没掉血那一下（盾牌/吸收全吃）：" + NEG_TRIALS + " 次反 " + nZero + " 次（必须 0）",
                nZero == 0);
        check("**灵敏度对照**：同口径的普通攻击 " + NEG_TRIALS + " 次反了 " + nCtrl
                + " 次（非零 ⇒ 上面那四个 0 不是假绿）", nCtrl > 0);
        ItemStack keptForNeg = wearer.getItemBySlot(EquipmentSlot.CHEST);
        wearer.setItemSlot(EquipmentSlot.CHEST, ItemStack.EMPTY);
        tickQuietly(wearer, "破套对照");
        int[] rNoSet = countReflects(wearer, attacker, melee, 4.0F, NEG_TRIALS);
        check("负向对照：破套时真受击 " + NEG_TRIALS + " 次反 " + rNoSet[0] + " 次（必须 0）",
                rNoSet[0] == 0);
        check("  └ 同一个负向对照里，这 " + NEG_TRIALS + " 下确实打进去了（掉血 " + rNoSet[1]
                + " 次）—— 否则上面那个 0 是假绿", rNoSet[1] == NEG_TRIALS);
        wearer.setItemSlot(EquipmentSlot.CHEST, keptForNeg);
        ServerPlayer plain = fake(event, level, "zf138plain");
        settle(plain, "裸装对照");
        int[] rPlain = countReflects(plain, attacker, level.damageSources().playerAttack(attacker),
                4.0F, NEG_TRIALS);
        check("负向对照：完全没穿振金的玩家受击 " + NEG_TRIALS + " 次反 " + rPlain[0] + " 次（必须 0）",
                rPlain[0] == 0);
        check("  └ 同一个负向对照里，这 " + NEG_TRIALS + " 下确实打进去了（掉血 " + rPlain[1]
                + " 次，裸装每下 4.0）", rPlain[1] == NEG_TRIALS);

        say(TAG + "⑧ 架构证据：无敌帧里那一下 —— 事件照触发，但走不到 Post");
        reset(wearer, attacker);
        wearer.hurt(melee, 4.0F);                     // 第一下：真掉血，lastHurt 记为 4.0
        int in0 = incomingSeen;
        int po0 = postSeen;
        float hp0 = wearer.getHealth();
        wearer.invulnerableTime = 20;                  // 无敌帧内
        wearer.hurt(melee, 3.0F);                      // 更轻 ⇒ hurt 提前 return
        check("无敌帧里的第二下：LivingIncomingDamageEvent 照触发（+" + (incomingSeen - in0) + "）",
                incomingSeen > in0);
        check("但它走不到 LivingDamageEvent.Post（+" + (postSeen - po0) + "）", postSeen == po0);
        check("血量也没掉（" + hp0 + " → " + wearer.getHealth() + "）",
                Math.abs(wearer.getHealth() - hp0) < 1.0E-4F);

        say(TAG + "⑨ 死亡文案：「踢到了铁板」");
        reset(wearer, attacker);
        Component msg = reflectSrc.getLocalizedDeathMessage(attacker);
        check("getLocalizedDeathMessage 的键 = death.attack.potato_s_t.vibranium_reflect（实际 "
                + keyOf(msg) + "）",
                keyOf(msg).equals("death.attack.potato_s_t.vibranium_reflect"));
        check("%1$s 解析出来是**攻击者自己的名字**（" + msg.getString() + "）",
                msg.getString().contains(attacker.getName().getString()));
        reset(wearer, attacker);
        attacker.setHealth(0.5F);
        attacker.hurt(reflectSrc, 100.0F);
        check("真把攻击者反伤致死（isDeadOrDying = " + attacker.isDeadOrDying() + "）",
                attacker.isDeadOrDying());
        // ⚠ 必须在**死亡那一刻**抓（见 onAnyDeath 的注释）：死完再问 CombatTracker，
        //   entries 已经被 recheckStatus() 清空 ⇒ 永远拿到 death.attack.generic。
        check("死亡那一刻的 CombatTracker.getDeathMessage 键 = 那一条（实际 "
                + (lastDeathMessage == null ? "没抓到" : keyOf(lastDeathMessage)) + "）",
                lastDeathMessage != null
                        && keyOf(lastDeathMessage).equals("death.attack.potato_s_t.vibranium_reflect"));
        check("死亡文案里出现的是攻击者的名字、不是穿戴者的（"
                + (lastDeathMessage == null ? "没抓到" : lastDeathMessage.getString()) + "）",
                lastDeathMessage != null
                        && lastDeathMessage.getString().contains(attacker.getName().getString())
                        && !lastDeathMessage.getString().contains(wearer.getName().getString()));

        say(TAG + "⑩ 无关面：别的套装没被带上");
        ServerPlayer star = fake(event, level, "zf138star");
        star.setItemSlot(EquipmentSlot.HEAD, new ItemStack(ModArmorItems.STAR_STEEL_HELMET.get()));
        star.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ModArmorItems.STAR_STEEL_CHESTPLATE.get()));
        star.setItemSlot(EquipmentSlot.LEGS, new ItemStack(ModArmorItems.STAR_STEEL_LEGGINGS.get()));
        star.setItemSlot(EquipmentSlot.FEET, new ItemStack(ModArmorItems.STAR_STEEL_BOOTS.get()));
        settle(star, "星璨钢对照");
        int[] rStar = countReflects(star, attacker,
                level.damageSources().playerAttack(attacker), 4.0F, NEG_TRIALS);
        check("满套星璨钢受击 " + NEG_TRIALS + " 次反 " + rStar[0] + " 次（必须 0 —— 反伤只属于振金）",
                rStar[0] == 0);
        check("  └ 同一组里这 " + NEG_TRIALS + " 下确实打进去了（星璨钢掉血 " + rStar[1] + " 次）",
                rStar[1] == NEG_TRIALS);
        star.removeAllEffects();
        tickQuietly(star, "星璨钢对照");
        check("满套星璨钢**不会**被塞常驻抗性 I（那是振金专属；星璨的抗性是夜晚「每件」给的）",
                star.getEffect(MobEffects.DAMAGE_RESISTANCE) == null);
        check("检查一下护甲没被顺手改：星璨钢满套 ARMOR = 28（实际 " + star.getArmorValue() + "）",
                star.getArmorValue() == 28);
        check("振金四件的物品 id 没变（头盔 = " + itemId(wearer.getItemBySlot(EquipmentSlot.HEAD)) + "）",
                itemId(wearer.getItemBySlot(EquipmentSlot.HEAD)).equals(NS + ":vibranium_helmet"));
    }
}
