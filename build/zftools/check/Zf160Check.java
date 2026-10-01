package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.levelgen.feature.ConfiguredFeature;
import net.minecraft.world.level.levelgen.feature.configurations.OreConfiguration;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.levelgen.placement.PlacementModifier;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * ZF160 临时探针（0.13：银矿矿脉调大 / 铝的权重调小）。
 *
 * <p>验的是**服务端真加载进来的那两张注册表**（不是盘上的 JSON 写没写对）：
 * {@code Registries.CONFIGURED_FEATURE} 里的 `potato_s_t:ore_*` 取 {@link OreConfiguration#size}，
 * {@code Registries.PLACED_FEATURE} 里的 {@code potato_s_t:ore_*_placed} 把每一步
 * {@link PlacementModifier} 用**官方编解码器**（{@link PlacementModifier#CODEC}）编回 NBT 再读字段 ——
 * {@code CountPlacement.count} 是 private，但走编码器就不用反射（本工程对反射零容忍）。</p>
 *
 * <p>七条：银 size=10 / 银 count=12 / 银 targets 没动 / 铝 count=10（size 仍 11）/
 * 另外 7 种矿 size+count 逐条没动 / 9 条矿脉的高度区间逐条没动 / 负对照（读到的不是旧值）。</p>
 *
 * <p><b>⚠ 本轮不走"改 `PotatoST.java` 挂探针"那条老路</b>：那一刻盘上正挂着另一条线的
 * `Zf159Check`，汇合点不能叠罗汉（§4.7）。改成给本类加
 * {@code @EventBusSubscriber(modid = PotatoST.MODID)} 自动注册（默认就是 game 总线，
 * 与 `GuideBook` 同一个写法）⇒ **只拷一个文件进来、跑完删掉**，`PotatoST.java` 一个字节都不用动。
 * 卸载脚本因此简化成"删文件 + 核对 `PotatoST.java` 的 sha1 没变"。</p>
 *
 * <p>⚠ §4.50：{@code runServer} 的 stdout 是 GBK ⇒ 自己写 UTF-8 报告，路径绝对，且在 {@code halt()} 前写。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf160Check {

    private static final String TAG = "[A160] ";
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf160_probe_utf8.txt";

    /** 改后应有值：矿名 → {size, count}。 */
    private static final Map<String, int[]> EXPECT = new LinkedHashMap<>();
    /** 改前值（只给银/铝用来说明"确实变了"）。 */
    private static final Map<String, int[]> BEFORE = new LinkedHashMap<>();
    /** 高度区间（改前改后一致）：矿名 → 文本。 */
    private static final Map<String, String> HEIGHT = new LinkedHashMap<>();

    static {
        EXPECT.put("aluminum", new int[]{11, 10});
        EXPECT.put("cobalt", new int[]{4, 6});
        EXPECT.put("nickel", new int[]{6, 8});
        EXPECT.put("silver", new int[]{10, 12});
        EXPECT.put("uranium", new int[]{10, 10});
        EXPECT.put("manganese", new int[]{12, 8});
        EXPECT.put("lithium", new int[]{8, 7});
        EXPECT.put("wolframite", new int[]{4, 6});
        EXPECT.put("titanium", new int[]{8, 4});
        BEFORE.put("silver", new int[]{3, 9});
        BEFORE.put("aluminum", new int[]{11, 12});
        HEIGHT.put("aluminum", "16..80");
        HEIGHT.put("cobalt", "-64..32");
        HEIGHT.put("nickel", "-56..76");
        HEIGHT.put("silver", "-48..32");
        HEIGHT.put("uranium", "-64..16");
        HEIGHT.put("manganese", "-64..48");
        HEIGHT.put("lithium", "-16..64");
        HEIGHT.put("wolframite", "-64..16");
        HEIGHT.put("titanium", "-64..16");
    }

    private static boolean done;
    private static int failed;
    private static int checks;
    private static int ticks;
    private static MinecraftServer server;

    private static final StringBuilder REPORT = new StringBuilder();
    private static final List<String> NOTES = new ArrayList<>();

    private Zf160Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void check(String name, boolean ok, String detail) {
        checks++;
        String line = (ok ? "  [OK]   " : "  [FAIL] ") + name + (detail.isEmpty() ? "" : "  <- " + detail);
        REPORT.append(line).append('\n');
        System.out.println(TAG + line);
        if (!ok) {
            failed++;
        }
    }

    private static void note(String text) {
        NOTES.add(text);
        System.out.println(TAG + "  [--]   " + text);
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF160 探针报告（0.13：银矿脉调大 / 铝权重调小）× UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "ALL OK" : failed + " 条 FAIL") + "（共 " + checks + " 项）\n\n");
            w.write(REPORT.toString());
            if (!NOTES.isEmpty()) {
                w.write("\n---- 观 察 记 录 ----\n");
                for (String n : NOTES) {
                    w.write("  · " + n + "\n");
                }
            }
        } catch (Throwable t) {
            say(TAG + "report write failed: " + t);
        }
    }

    /**
     * ⚠ 本探针**不等 tick**：`ServerStartedEvent` 那一刻 configure/placed feature 两个注册表已经装好
     * （`UniversalUpgradeTemplate` 就是在这儿读配方的），直接验、写完报告就 halt。
     *
     * <p>为什么不等 20 tick（第一版吃了亏）：那一刻盘上还挂着另一条线的 `Zf159Check`，
     * 它在启动期就 `halt` ⇒ 服务器**一个 tick 都没跑**（日志里 "Done" 之后紧跟着 "Stopping server"），
     * 于是"等 20 tick 再验"的版本永远等不到 —— 报告一个字都没写。</p>
     */
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (done) {
            return;
        }
        done = true;
        server = event.getServer();
        say(TAG + "phase1 @ ServerStartedEvent（注册表已装好，立即验，不等 tick）");
        try {
            phase1();
        } catch (Throwable t) {
            check("phase1 全程不抛异常（" + t + "）", false, "");
            t.printStackTrace();
        }
        say(TAG + "判词：" + (failed == 0 ? "ALL OK" : failed + " 条 FAIL") + "（共 " + checks + " 项）");
        flushReport();
        server.halt(false);
    }

    // ============================================================ 正式检查
    private static void phase1() {
        Registry<ConfiguredFeature<?, ?>> cf = server.registryAccess().registryOrThrow(Registries.CONFIGURED_FEATURE);
        Registry<PlacedFeature> pf = server.registryAccess().registryOrThrow(Registries.PLACED_FEATURE);

        int silverSize = oreSize(cf, "silver");
        int silverCount = placedCount(pf, "silver");

        check("A1 银矿脉 size = 10（原版铜小脉同值；改前 3）", silverSize == 10, "实际 " + silverSize);
        check("A2 银矿每区块 12 次（改前 9；原版铜 16）", silverCount == 12, "实际 " + silverCount);
        check("A3 银矿的两个 replace 目标没被顺手改坏（silver_ore + deepslate_silver_ore）",
                targetsOk(cf, "silver"), targetsOf(cf, "silver"));

        int alumSize = oreSize(cf, "aluminum");
        int alumCount = placedCount(pf, "aluminum");
        check("A4 铝每区块 10 次（改前 12，取了「调小 1~2」的 2）+ size 仍 11",
                alumCount == 10 && alumSize == 11, "实际 size=" + alumSize + " count=" + alumCount);

        List<String> bad = new ArrayList<>();
        for (Map.Entry<String, int[]> e : EXPECT.entrySet()) {
            int s = oreSize(cf, e.getKey());
            int c = placedCount(pf, e.getKey());
            if (s != e.getValue()[0] || c != e.getValue()[1]) {
                bad.add(e.getKey() + "(size=" + s + ",count=" + c + " 应为 " + e.getValue()[0] + "," + e.getValue()[1] + ")");
            }
        }
        check("A5 九种矿的 size / count 逐条对上改后表（其余 7 种一个没动）", bad.isEmpty(), String.join(" ", bad));

        List<String> hbad = new ArrayList<>();
        for (Map.Entry<String, String> e : HEIGHT.entrySet()) {
            String h = placedHeight(pf, e.getKey());
            if (!h.equals(e.getValue())) {
                hbad.add(e.getKey() + "=" + h + "(应 " + e.getValue() + ")");
            }
        }
        check("A6 九条矿脉的高度区间逐条没动（只动了要动的那三个数）", hbad.isEmpty(), String.join(" ", hbad));

        check("A7 负对照：读到的确实是**新值**（银 size≠3、铝 count≠12）",
                silverSize != BEFORE.get("silver")[0] && alumCount != BEFORE.get("aluminum")[1],
                "silver.size=" + silverSize + " alum.count=" + alumCount);

        note("读法是「注册表现查 + 官方编解码器把 placement 编回 NBT」（CountPlacement.count 是 private，零反射）。");
        note("银：size " + BEFORE.get("silver")[0] + "→" + silverSize
                + "、count " + BEFORE.get("silver")[1] + "→" + silverCount
                + "；铝：count " + BEFORE.get("aluminum")[1] + "→" + alumCount + "。");
    }

    private static OreConfiguration oreConfig(Registry<ConfiguredFeature<?, ?>> cf, String ore) {
        Holder<ConfiguredFeature<?, ?>> h = cf.getHolder(ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "ore_" + ore)).orElse(null);
        if (h == null || !(h.value().config() instanceof OreConfiguration ore0)) {
            return null;
        }
        return ore0;
    }

    private static int oreSize(Registry<ConfiguredFeature<?, ?>> cf, String ore) {
        OreConfiguration c = oreConfig(cf, ore);
        return c == null ? -1 : c.size;
    }

    private static String targetsOf(Registry<ConfiguredFeature<?, ?>> cf, String ore) {
        OreConfiguration c = oreConfig(cf, ore);
        if (c == null) {
            return "(取不到)";
        }
        List<String> out = new ArrayList<>();
        for (OreConfiguration.TargetBlockState t : c.targetStates) {
            out.add(String.valueOf(t.state.getBlock()));
        }
        return String.join("+", out);
    }

    private static boolean targetsOk(Registry<ConfiguredFeature<?, ?>> cf, String ore) {
        String s = targetsOf(cf, ore);
        return s.contains("silver_ore") && s.contains("deepslate_silver_ore") && s.split("\\+").length == 2;
    }

    /** 把 placed feature 的每一步编回 NBT，读 count / 高度；全用官方编解码器，零反射。 */
    private static CompoundTag placedAsTag(Registry<PlacedFeature> pf, String ore) {
        PlacedFeature p = pf.get(ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "ore_" + ore + "_placed"));
        if (p == null) {
            return null;
        }
        CompoundTag out = new CompoundTag();
        List<PlacementModifier> mods = p.placement();
        for (int i = 0; i < mods.size(); i++) {
            Tag t = PlacementModifier.CODEC.encodeStart(NbtOps.INSTANCE, mods.get(i)).getOrThrow();
            if (t instanceof CompoundTag c) {
                out.put(String.valueOf(i), c);
            }
        }
        return out;
    }

    private static int placedCount(Registry<PlacedFeature> pf, String ore) {
        CompoundTag steps = placedAsTag(pf, ore);
        if (steps == null) {
            return -1;
        }
        for (String k : steps.getAllKeys()) {
            CompoundTag c = steps.getCompound(k);
            if ("minecraft:count".equals(c.getString("type"))) {
                return c.getInt("count");
            }
        }
        return -1;
    }

    private static String placedHeight(Registry<PlacedFeature> pf, String ore) {
        CompoundTag steps = placedAsTag(pf, ore);
        if (steps == null) {
            return "(取不到)";
        }
        for (String k : steps.getAllKeys()) {
            CompoundTag c = steps.getCompound(k);
            if ("minecraft:height_range".equals(c.getString("type"))) {
                CompoundTag h = c.getCompound("height");
                int lo = h.getCompound("min_inclusive").getInt("absolute");
                int hi = h.getCompound("max_inclusive").getInt("absolute");
                return lo + ".." + hi;
            }
        }
        return "(没有高度步)";
    }
}
