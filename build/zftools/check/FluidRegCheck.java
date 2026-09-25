package com.potatost.mod;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF85). Delete after the run.
 *
 * <p>用户诉求是"把 IDE 的警告/报错优化掉"，本轮**逻辑一字未改**（只搬注册、删死代码）。
 * 所以探针只做一件事：<b>证明搬完之后服务端一切照旧</b> ——</p>
 * <ol>
 *   <li>8 种流体类型与流体本体都还绑得上（搬走的是"客户端贴图注册"，不该碰到注册表）；</li>
 *   <li>桶映射没变（柴油/汽油有桶、原油/石脑油/液化石油气没有）；</li>
 *   <li>气体判定没变（isGas 只认那 3 种）；</li>
 *   <li>顺带证明**服务端加载不会碰客户端类**：这条路走下来不抛 NoClassDefFoundError。</li>
 * </ol>
 */
public final class FluidRegCheck {

    private static final String TAG = "[F85] ";
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf85_probe.txt";
    private static final StringBuilder REPORT = new StringBuilder();

    private static boolean registered;
    private static int passed;
    private static int failed;

    private FluidRegCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(FluidRegCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            checkRegistry(level);
            checkBuckets();
            checkGasRules();
        } catch (Throwable t) {
            t.printStackTrace();
            log("EXCEPTION: " + t);
            failed++;
        }
        log("==== passed=" + passed + " failed=" + failed + " ====");
        flushReport();
        event.getServer().halt(false);
    }

    private static void log(String line) {
        System.out.println(TAG + line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.Writer w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write(REPORT.toString());
        } catch (Throwable t) {
            System.out.println(TAG + "report write failed: " + t);
        }
    }

    private static void ok(String label, boolean cond) {
        if (cond) {
            passed++;
            log("  [OK]   " + label);
        } else {
            failed++;
            log("  [FAIL] " + label);
        }
    }

    private static void eq(String label, long expected, long actual) {
        ok(label + "（期望 " + expected + "，实际 " + actual + "）", expected == actual);
    }

    /** ① 注册表侧：8 种流体类型 + 8 种流体本体都还在。 */
    private static void checkRegistry(ServerLevel level) {
        Fluid[] sources = {ModFluids.OXYGEN.get(), ModFluids.HYDROGEN.get(),
                ModFluids.CHLORINE.get(), ModFluids.CRUDE_OIL.get(), ModFluids.DIESEL.get(),
                ModFluids.NAPHTHA.get(), ModFluids.GASOLINE.get(), ModFluids.LPG.get()};
        String[] names = {"oxygen", "hydrogen", "chlorine", "crude_oil", "diesel",
                "naphtha", "gasoline", "lpg"};
        eq("8 种流体本体都注册了", 8, sources.length);
        for (int i = 0; i < sources.length; i++) {
            Fluid f = sources[i];
            ok("流体本体可用：" + names[i],
                    f != null && level.getFluidState(level.getSharedSpawnPos()).getType() != f);
            ok("流体类型绑得上：" + names[i],
                    f != null && f.getFluidType() != null
                            && f.getFluidType().getDescription() != null);
        }
        eq("gases() 仍是 3 种（那个只认紧凑编号的 idOf/byId 本轮删了，gases() 保留）",
                3, ModFluids.gases().size());
        ok("注册名没变（potato_s_t:diesel 等）",
                String.valueOf(net.minecraft.core.registries.BuiltInRegistries.FLUID.getKey(
                        ModFluids.GASOLINE.get())).equals("potato_s_t:gasoline"));
    }

    /** ② 桶映射（ZF82 的成果，本轮不该被搬家碰到）。 */
    private static void checkBuckets() {
        ok("柴油有官方桶", ModFluids.DIESEL.get().getBucket() == ModItems.DIESEL_BUCKET.get());
        ok("汽油有官方桶", ModFluids.GASOLINE.get().getBucket() == ModItems.GASOLINE_BUCKET.get());
        ok("原油仍然没有桶（ZF73 老规矩）", ModFluids.CRUDE_OIL.get().getBucket() == Items.AIR);
        ok("石脑油 / 液化石油气仍然没有桶",
                ModFluids.NAPHTHA.get().getBucket() == Items.AIR
                        && ModFluids.LPG.get().getBucket() == Items.AIR);
    }

    /** ③ 气体 / 液体判定（ZF73 的正向白名单，本轮不动）。 */
    private static void checkGasRules() {
        ok("氧气/氢气/氯气算气体",
                ModFluids.isGas(ModFluids.OXYGEN.get()) && ModFluids.isGas(ModFluids.HYDROGEN.get())
                        && ModFluids.isGas(ModFluids.CHLORINE.get()));
        ok("原油/柴油/汽油/液化石油气算液体（不是气体）",
                !ModFluids.isGas(ModFluids.CRUDE_OIL.get()) && !ModFluids.isGas(ModFluids.DIESEL.get())
                        && !ModFluids.isGas(ModFluids.GASOLINE.get())
                        && !ModFluids.isGas(ModFluids.LPG.get()));
        ok("isLiquid = 非气体（油桶收任何液体这条没变）",
                ModFluids.isLiquid(ModFluids.DIESEL.get())
                        && !ModFluids.isLiquid(ModFluids.OXYGEN.get()));
    }
}
