package com.potatost.mod;

import net.neoforged.neoforge.common.ModConfigSpec;

/**
 * PotatoS&amp;T 的配置文件（0.14 ZF186）。
 *
 * <p><b>用户原话</b>：「联动一下配置界面（做成不是必须依赖项）使本mod可以接受配置 目前我指定的配置项为
 * 黑洞是否为一次性（false则做成只消耗完电力条，不损坏）以及引力装置蓄力时长（默认30s 5-60s可调）
 * 还有单块锂电池容量（1m-20mfe）现在的值为默认值 还想加其它的你自己发挥」。</p>
 *
 * <h2>怎么落地的（三条设计决定，都是「为什么」不是「是什么」）</h2>
 * <ol>
 *   <li><b>走 NeoForge 自己的 {@link ModConfigSpec}</b>（{@code COMMON} 类型 ⇒ 生成
 *       {@code config/potato_s_t-common.toml}）。不用第三方配置库 ⇒ <b>一个依赖都不加</b>；
 *       客户端与服务端各读自己那份文件，物品条 / 界面用的那几个数两边都算得出来。</li>
 *   <li><b>配置界面用 NeoForge 自带的 {@code ConfigurationScreen}</b>（模组列表 → 配置），
 *       注册在<b>客户端专用</b>类 {@code client/PotatoSTConfigScreen} 里 —— 见那个类的注释：
 *       它读的就是这份 {@link ModConfigSpec}，所以装了 Configured / Cloth 之类界面模组也自动兼容，
 *       <b>没装也照样能改（改 TOML，或点模组列表里那个配置按钮）</b>。</li>
 *   <li><b>取值一律走 {@link #specReady()} 兜底</b>：{@code ConfigValue.get()} 在配置<b>还没加载</b>时
 *       会抛 {@code IllegalStateException}（NeoForge {@code ModConfigSpec} 第 1235 行那句
 *       {@code Preconditions.checkState}），而注册表/物品栏这些代码可能在加载前就碰到我们的取值器
 *       ⇒ 没加载时返回 {@code getDefault()}（= 出厂值）。这条是本节最容易踩的雷（档案 §4.186①）。</li>
 * </ol>
 *
 * <p>⚠ 所有默认值都<b>等于</b>落地前代码里的那个硬编码常量，除了两处用户明确改口的地方：
 * 引力装置蓄力 {@code 25s → 30s}（用户说「默认30s」）、黑洞是否一次性默认 {@code true}（= 老行为）。</p>
 */
public final class PotatoSTConfig {

    /** 配置规格；主类构造期注册为 {@code ModConfig.Type.COMMON}。 */
    public static final ModConfigSpec SPEC;

    // ============================================================
    //  黑洞（black_hole）
    // ============================================================
    /** 用户点名①：一次性（true = 用一次装置就损坏，老行为；false = 只把电力条抽干，装置不坏）。 */
    public static final ModConfigSpec.BooleanValue BLACK_HOLE_ONE_SHOT;
    /** 黑洞活多久（秒）。 */
    public static final ModConfigSpec.IntValue BLACK_HOLE_LIFETIME_SECONDS;
    /** 单次最多搬运多少方块。 */
    public static final ModConfigSpec.IntValue BLACK_HOLE_MAX_BLOCKS;
    /** 扫描半径（格）：黑洞为中心，各轴 ±N。 */
    public static final ModConfigSpec.IntValue BLACK_HOLE_SCAN_RADIUS;
    /** 是否吸引生物（含玩家）。 */
    public static final ModConfigSpec.BooleanValue BLACK_HOLE_PULL_ENTITIES;
    /** 视界内是否持续吃虚空伤害。 */
    public static final ModConfigSpec.BooleanValue BLACK_HOLE_VOID_DAMAGE;

    // ============================================================
    //  手持式引力装置（gravity_device）
    // ============================================================
    /** 用户点名②：蓄力时长（秒），默认 30、5~60 可调。 */
    public static final ModConfigSpec.IntValue GRAVITY_CHARGE_SECONDS;
    /** 引力装置储能上限（FE）。 */
    public static final ModConfigSpec.IntValue GRAVITY_CAPACITY_FE;

    // ============================================================
    //  锂电池（lithium_battery）
    // ============================================================
    /** 用户点名③：单块锂电池容量（FE），默认 = 落地前的 4M。 */
    public static final ModConfigSpec.IntValue BATTERY_PER_BLOCK_FE;
    /** 每面充放电速率上限（FE/t）。 */
    public static final ModConfigSpec.IntValue BATTERY_TRANSFER_RATE;
    /** 多方块最大块数。 */
    public static final ModConfigSpec.IntValue BATTERY_MAX_BLOCKS;

    static {
        ModConfigSpec.Builder b = new ModConfigSpec.Builder();

        // ── 黑洞 ──────────────────────────────────────────────
        b.comment("黑洞（手持式引力装置的产物）。",
                  "The black hole spawned by the gravity device.")
                .translation("potato_s_t.configuration.section.black_hole")
                .push("black_hole");
        BLACK_HOLE_ONE_SHOT = b
                .comment("一次性：true = 放完黑洞装置当场损坏（老行为）；false = 只把电力条抽干，装置不损坏。",
                         "One shot: true leaves the device broken after firing,",
                         "false only drains the energy bar and keeps the device intact.")
                .translation("potato_s_t.configuration.black_hole.one_shot")
                .define("one_shot", true);
        BLACK_HOLE_LIFETIME_SECONDS = b
                .comment("黑洞存活时长（秒）。越长吸得越多，也越吃性能。",
                         "How long a black hole lives, in seconds.")
                .translation("potato_s_t.configuration.black_hole.lifetime_seconds")
                .defineInRange("lifetime_seconds", 20, 5, 120);
        BLACK_HOLE_MAX_BLOCKS = b
                .comment("单次最多搬运多少方块（搬走 + 码放都算这个数）。",
                         "Maximum blocks a single black hole may move.")
                .translation("potato_s_t.configuration.black_hole.max_blocks")
                .defineInRange("max_blocks", 1500, 100, 5000);
        BLACK_HOLE_SCAN_RADIUS = b
                .comment("扫描半径（格）：黑洞为中心各轴 ±N。默认 40 = 5x5x5 区块；",
                         "半径每加一格，扫描体积是三次方地涨 —— 调大之前先想想 TPS。",
                         "Scan radius in blocks (each axis is +/- N around the hole).")
                .translation("potato_s_t.configuration.black_hole.scan_radius_blocks")
                .defineInRange("scan_radius_blocks", 40, 8, 80);
        BLACK_HOLE_PULL_ENTITIES = b
                .comment("是否吸引生物（含玩家）。关掉只吸方块。",
                         "Whether the black hole pulls living entities (players included).")
                .translation("potato_s_t.configuration.black_hole.pull_entities")
                .define("pull_entities", true);
        BLACK_HOLE_VOID_DAMAGE = b
                .comment("视界内是否持续吃虚空伤害。关掉只是「拉过来」，不掉血。",
                         "Whether entities inside the event horizon take void damage.")
                .translation("potato_s_t.configuration.black_hole.void_damage")
                .define("void_damage", true);
        b.pop();

        // ── 引力装置 ──────────────────────────────────────────
        b.comment("手持式引力装置（副手放方块、长按右键蓄力、放黑洞那件）。",
                  "The hand-held gravity device.")
                .translation("potato_s_t.configuration.section.gravity_device")
                .push("gravity_device");
        GRAVITY_CHARGE_SECONDS = b
                .comment("蓄力时长（秒）。默认 30、可调 5~60。",
                         "Charge-up time in seconds (default 30, 5-60).")
                .translation("potato_s_t.configuration.gravity_device.charge_seconds")
                .defineInRange("charge_seconds", 30, 5, 60);
        GRAVITY_CAPACITY_FE = b
                .comment("储能上限（FE）。老数值是 8M；改小之后已经充进去的电按新上限算。",
                         "Energy buffer in FE (the original value was 8M).")
                .translation("potato_s_t.configuration.gravity_device.capacity_fe")
                .defineInRange("capacity_fe", 8_000_000, 1_000_000, 64_000_000);
        b.pop();

        // ── 锂电池 ────────────────────────────────────────────
        b.comment("三元聚合物锂电池（多方块储能）。",
                  "The lithium battery multiblock.")
                .translation("potato_s_t.configuration.section.lithium_battery")
                .push("lithium_battery");
        BATTERY_PER_BLOCK_FE = b
                .comment("单块容量（FE）。默认 4M（= 落地前的老数值）；多方块总容量 = 块数 x 本值。",
                         "Capacity per block in FE (default 4M, the original value).")
                .translation("potato_s_t.configuration.lithium_battery.per_block_fe")
                .defineInRange("per_block_fe", 4_000_000, 1_000_000, 20_000_000);
        BATTERY_TRANSFER_RATE = b
                .comment("每 tick 每面的充放电上限（FE/t）。",
                         "Transfer rate per side in FE/t.")
                .translation("potato_s_t.configuration.lithium_battery.transfer_rate_fe")
                .defineInRange("transfer_rate_fe", 65_536, 1_024, 1_048_576);
        BATTERY_MAX_BLOCKS = b
                .comment("一个多方块最多几块（决定「能堆多高」的上限）。",
                         "Maximum blocks in one battery multiblock.")
                .translation("potato_s_t.configuration.lithium_battery.max_size_blocks")
                .defineInRange("max_size_blocks", 800, 27, 800);
        b.pop();

        SPEC = b.build();
    }

    private PotatoSTConfig() {
    }

    // ============================================================
    //  取值器（唯一入口 —— 别在别处直接 .get()）
    // ============================================================

    /** 配置加载了没有。没加载时 {@code ConfigValue.get()} 会抛异常（见类注释③）。 */
    private static boolean specReady() {
        return SPEC != null && SPEC.isLoaded();
    }

    private static boolean b(ModConfigSpec.BooleanValue v) {
        return specReady() ? v.get() : v.getDefault();
    }

    private static int i(ModConfigSpec.IntValue v) {
        return specReady() ? v.get() : v.getDefault();
    }

    /** 用户点名①：放完黑洞装置会不会坏。 */
    public static boolean oneShotBlackHole() {
        return b(BLACK_HOLE_ONE_SHOT);
    }

    /** 黑洞存活 tick 数（秒 x 20）。 */
    public static int blackHoleLifetimeTicks() {
        return i(BLACK_HOLE_LIFETIME_SECONDS) * 20;
    }

    /** 单次最多搬运方块数。 */
    public static int blackHoleMaxBlocks() {
        return i(BLACK_HOLE_MAX_BLOCKS);
    }

    /** 扫描半径（格）。 */
    public static int blackHoleScanRadius() {
        return i(BLACK_HOLE_SCAN_RADIUS);
    }

    /** 黑洞吸不吸生物。 */
    public static boolean blackHolePullsEntities() {
        return b(BLACK_HOLE_PULL_ENTITIES);
    }

    /** 视界里掉不掉血。 */
    public static boolean blackHoleVoidDamage() {
        return b(BLACK_HOLE_VOID_DAMAGE);
    }

    /** 用户点名②：蓄力 tick 数（秒 x 20）。 */
    public static int gravityChargeTicks() {
        return i(GRAVITY_CHARGE_SECONDS) * 20;
    }

    /** 引力装置储能上限（FE）。 */
    public static int gravityCapacity() {
        return i(GRAVITY_CAPACITY_FE);
    }

    /** 用户点名③：单块锂电池容量（FE）。 */
    public static long batteryPerBlock() {
        return (long) i(BATTERY_PER_BLOCK_FE);
    }

    /** 锂电池每面速率上限（FE/t）。 */
    public static int batteryTransferRate() {
        return i(BATTERY_TRANSFER_RATE);
    }

    /** 锂电池多方块最大块数。 */
    public static int batteryMaxBlocks() {
        return i(BATTERY_MAX_BLOCKS);
    }

    // ============================================================
    //  配置界面归属（0.14 ZF188）
    // ============================================================

    /**
     * 本模组**要不要自己注册配置界面**（0.14 ZF188）。
     *
     * <p><b>用户拍板的口径</b>：「让『配置界面』(Configured) 接管；没装就用 NeoForge 自带的」。</p>
     *
     * <h2>为什么这个口径正好对得上 Configured 的实现</h2>
     * <p>反编译本机那份 {@code [配置界面] configured-neoforge-1.21.1-2.6.3.jar} 的
     * {@code com.mrcrayfish.configured.client.ClientConfigured.generateConfigFactories}
     * （它遍历 {@code ModList.forEachModContainer}，每个模组跑一段 lambda）：</p>
     * <pre>
     *   if (container.getCustomExtension(IConfigScreenFactory.class).isPresent()
     *           &amp;&amp; !Config.isForceConfiguredMenu()) return;      // 模组自带界面 ⇒ 它让位
     *   Map&lt;ConfigType, ?&gt; map = ClientHandler.createConfigMap(new ModContext(modId));
     *   if (map.isEmpty()) return;                                // 没有任何配置的模组它也不管
     *   LOG.info("Registering config factory for mod {}. Found {} config(s)", modId, count);
     *   container.registerExtensionPoint(IConfigScreenFactory.class, ...);   // ← 接管那个按钮
     * </pre>
     * <p>⇒ 只要**我们不注册**、而本模组确实有配置（一个 {@code COMMON}），Configured 就会接管
     * 模组列表里的「配置」按钮，并在客户端日志里留下
     * {@code Registering config factory for mod potato_s_t. Found 1 config(s)}
     * —— <b>那一行就是「它真的接管了」的判据</b>（要你实测时看的就是它）。</p>
     *
     * <p>⚠ 这是个**策略**，所以单独抽成一个**纯函数**（入参就是「configured 装没装」）：
     * 这台机器上跑不了真客户端 GUI，但策略的真值表可以在真服务端探针里验（见 {@code Zf188Check}）。</p>
     *
     * @param configuredModPresent {@code ModList.get().isLoaded("configured")}
     * @return true = 我们自己注册 NeoForge 自带的 {@code ConfigurationScreen}；false = 让给 Configured
     */
    public static boolean shouldRegisterOwnConfigScreen(boolean configuredModPresent) {
        return !configuredModPresent;
    }
}
