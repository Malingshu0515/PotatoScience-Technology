package com.potatost.mod;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF188 临时探针（0.14：配置界面归属 —— 装了「配置界面」Configured 就让位给它）。
 *
 * <p><b>用户拍板</b>（选项 A）：「让『配置界面』接管；没装就用 NeoForge 自带的」。</p>
 *
 * <p><b>验什么、为什么这么验</b>：这台机器上跑不了真客户端 GUI（没有可用的图形会话），
 * 但那条「让不让位」的**策略**被抽成了纯函数
 * {@link PotatoSTConfig#shouldRegisterOwnConfigScreen(boolean)} ⇒ 真值表可以在真服务端验；
 * 再加一条「这台服务器上 Configured 确实不在场」的**现场事实**，两下一拼就覆盖了实际分支。</p>
 *
 * <p>⚠ 客户端那一半（Configured 打完日志 {@code Registering config factory for mod potato_s_t}）
 * 只能由用户在客户端日志里看 —— 探针**不谎称**验过 GUI，这条写进报告里。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf188Check {

    private static final String TAG = "[A188] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf188_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf188Check() {
    }

    private static void check(boolean ok, String label, String detail) {
        if (ok) {
            passed++;
            LINES.add(TAG + "[OK]   " + label + (detail.isEmpty() ? "" : " ｜ " + detail));
        } else {
            failed++;
            LINES.add(TAG + "[FAIL] " + label + (detail.isEmpty() ? "" : " —— " + detail));
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        try {
            run();
        } catch (Throwable t) {
            failed++;
            LINES.add(TAG + "[FAIL] EXCEPTION " + t);
            for (StackTraceElement e : t.getStackTrace()) {
                if (e.getClassName().startsWith("com.potatost")) {
                    LINES.add("        at " + e);
                }
            }
        }
        LINES.add("");
        LINES.add("通过 = " + passed + "   失败 = " + failed);
        LINES.add("（客户端日志判据：装 Configured 时应出现 "
                + "Registering config factory for mod potato_s_t —— 由用户实测，探针没验 GUI）");
        try {
            Files.createDirectories(REPORT.getParent());
            try (Writer w = new OutputStreamWriter(Files.newOutputStream(REPORT), StandardCharsets.UTF_8)) {
                w.write(String.join("\n", LINES) + "\n");
            }
        } catch (IOException e) {
            System.out.println("probe report write failed: " + e);
        }
        // ⚠ 本轮同时挂了上一轮的 Zf186Check（当回归探针）：两个 handler 都在这一拍里跑完，
        //   各自的报告在各自 handler 内写完 ⇒ 这里再 halt 一次不影响（halt 幂等）。
        event.getServer().halt(false);
    }

    private static void run() {
        // ── H1/H2 策略真值表 ──
        boolean none = PotatoSTConfig.shouldRegisterOwnConfigScreen(false);
        boolean with = PotatoSTConfig.shouldRegisterOwnConfigScreen(true);
        check(none, "H1 没装 Configured ⇒ **我们自己注册** NeoForge 自带配置界面", "返回 " + none);
        check(!with, "H2 装了 Configured ⇒ **让位**（我们不注册，交给它接管那个按钮）", "返回 " + with);

        // ── H3 现场事实：这台服务器上 Configured 不在场；策略落到"自己注册"这一支 ──
        boolean loaded = ModList.get().isLoaded("configured");
        boolean decided = PotatoSTConfig.shouldRegisterOwnConfigScreen(loaded);
        check(!loaded && decided,
                "H3 现场：本服务器 mods 里没有 configured ⇒ 走「自己注册」这一支（策略与真实查询接得上）",
                "isLoaded(configured)=" + loaded + " ⇒ 自己注册=" + decided);

        // ── H4 回归：ZF186 那 11 项的出厂值没被这次重构碰坏 ──
        check(PotatoSTConfig.oneShotBlackHole()
                        && PotatoSTConfig.blackHoleLifetimeTicks() == 400
                        && PotatoSTConfig.blackHoleMaxBlocks() == 1500
                        && PotatoSTConfig.blackHoleScanRadius() == 40
                        && PotatoSTConfig.blackHolePullsEntities()
                        && PotatoSTConfig.blackHoleVoidDamage()
                        && PotatoSTConfig.gravityChargeTicks() == 600
                        && PotatoSTConfig.gravityCapacity() == 8_000_000
                        && PotatoSTConfig.batteryPerBlock() == 4_000_000L
                        && PotatoSTConfig.batteryTransferRate() == 65_536
                        && PotatoSTConfig.batteryMaxBlocks() == 800,
                "H4 回归：11 项出厂值一字未变（重构只多了「让位」这一条策略）",
                "引力 " + PotatoSTConfig.gravityChargeTicks() + " tick / "
                        + PotatoSTConfig.gravityCapacity() + " FE；电池 " + PotatoSTConfig.batteryPerBlock()
                        + " FE / " + PotatoSTConfig.batteryMaxBlocks() + " 块");
    }
}
