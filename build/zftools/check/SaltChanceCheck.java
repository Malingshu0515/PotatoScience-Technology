package com.potatost.mod;

import net.minecraft.util.RandomSource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF32 临时文件）</b>：验算盐分解构器的概率。
 *
 * <p>为什么要它：概率是"最像对的"那种东西 —— {@code nextInt(1000) < 60} 也能编译、也能跑，
 * 但实际只有 6%。读代码看不出错，所以拿<b>真实分布</b>去量。</p>
 *
 * <p><b>用法</b>：临时放进 {@code com.potatost.mod}、在 {@code PotatoST} 构造器里
 * {@code SaltChanceCheck.register()}，然后 {@code gradlew runServer} ——
 * 日志里出现 {@code [SALTCHECK]} 若干行后自动关服。<b>验证完必须连同注册行一起删掉。</b></p>
 *
 * <p>注：它只用 {@link SaltDecomposerRecipes#roll}（纯函数 + {@code RandomSource}），
 * <b>不碰任何注册表</b>，所以不依赖物品是否已绑定。</p>
 */
public final class SaltChanceCheck {

    private static final String TAG = "[SALTCHECK] ";
    private static boolean registered;

    private SaltChanceCheck() {
    }

    /** 挂 game 总线（{@code ServerStartedEvent} 是 game 事件，挂 mod 总线会静默失败 —— 见档案 §4.20）。 */
    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(SaltChanceCheck.class);
            System.out.println(TAG + "诊断钩子已注册（game 总线）");
        } catch (Throwable t) {
            System.out.println(TAG + "注册失败（不影响正式功能）：" + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed = run();
        } catch (Throwable t) {
            System.out.println(TAG + "验算抛异常：" + t);
            t.printStackTrace();
            failed = 1;
        } finally {
            System.out.println(TAG + "结论：" + (failed == 0 ? "概率全部符合预期" : "**有 " + failed + " 项不符**"));
            System.out.println(TAG + "诊断结束，请求关服");
            event.getServer().halt(false);
        }
    }

    private static int run() {
        int n = 200_000;
        RandomSource random = RandomSource.create(20260919L);   // 固定种子 ⇒ 可复现
        int salt = 0;
        int ore = 0;
        for (int i = 0; i < n; i++) {
            SaltDecomposerRecipes.Rolls r = SaltDecomposerRecipes.roll(random);
            if (r.saltReturned()) {
                salt++;
            }
            if (r.rawOre()) {
                ore++;
            }
        }
        double saltPct = 100.0 * salt / n;
        double orePct = 100.0 * ore / n;
        int failed = 0;
        System.out.println(TAG + "抽样 " + n + " 次：海盐返还 " + fmt(saltPct) + "%（期望 "
                + SaltDecomposerRecipes.SALT_RETURN_PERCENT + "%）、粗矿 " + fmt(orePct) + "%（期望 "
                + SaltDecomposerRecipes.RAW_ORE_PERCENT + "%）");

        failed += check("海盐返还率 ≈ 60%（±1%）",
                Math.abs(saltPct - SaltDecomposerRecipes.SALT_RETURN_PERCENT) <= 1.0);
        failed += check("粗矿产出率 ≈ 5%（±1%）",
                Math.abs(orePct - SaltDecomposerRecipes.RAW_ORE_PERCENT) <= 1.0);
        // 反向断言：写成 nextInt(1000) 会让命中率掉一个数量级
        failed += check("粗矿率没被写小一个数量级（> 4%）", orePct > 4.0);
        failed += check("海盐率没被写小一个数量级（> 50%）", saltPct > 50.0);

        double theory = SaltDecomposerRecipes.SALT_INPUT
                * SaltDecomposerRecipes.SALT_RETURN_PERCENT / 100.0;
        double actual = (double) salt * SaltDecomposerRecipes.SALT_INPUT / n;
        System.out.println(TAG + "每轮期望返还海盐：理论 " + fmt(theory) + "，实测 " + fmt(actual));
        failed += check("期望返还量与 64×60% 一致（±0.5）", Math.abs(theory - actual) <= 0.5);
        return failed;
    }

    private static String fmt(double v) {
        return String.format("%.2f", v);
    }

    private static int check(String name, boolean ok) {
        System.out.println(TAG + (ok ? "  [OK]   " : "  [FAIL] ") + name);
        return ok ? 0 : 1;
    }
}
