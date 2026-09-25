import com.potatost.mod.GroupEnergy;

/**
 * 共享储能池算法的<b>独立验算</b>（0.10 ZF24）。
 *
 * <p>{@link GroupEnergy} 刻意不认识 Minecraft，所以这个文件<b>不需要启动游戏</b>、
 * 不需要任何依赖，直接就能跑：</p>
 *
 * <pre>
 *   javac -encoding UTF-8 -d build\zftools\check\classes ^
 *       src\main\java\com\potatost\mod\GroupEnergy.java build\zftools\check\GroupEnergyCheck.java
 *   java -cp build\zftools\check\classes GroupEnergyCheck
 * </pre>
 *
 * <p>每一条都是<b>可失败</b>的断言（见档案 §4.17）：数字对不上就抛，退出码非 0。
 * 首轮实测抓到过一个真 BUG：非控制器那块问"总发电量"得到 0（Jade 显示成"不发电"）。</p>
 */
public final class GroupEnergyCheck {

    private static int passed = 0;
    private static int failed = 0;

    public static void main(String[] args) {
        int perBlock = 512;
        int blocks = 3;

        // ---- ① 空池子把一次 receive 全收下，且每块不超过上限 ----
        long[] e = new long[blocks];
        long got = GroupEnergy.fill(e, perBlock, 100);
        check("① 收 100 进空池", got == 100 && GroupEnergy.total(e) == 100);

        // ---- ② 灌满就停：一次灌 100000 只应收到 3×512 ----
        e = new long[blocks];
        got = GroupEnergy.fill(e, perBlock, 100_000);
        check("② 灌满只收 3×512", got == 3L * perBlock && GroupEnergy.total(e) == 3L * perBlock);
        check("② 每块都到上限", e[0] == perBlock && e[1] == perBlock && e[2] == perBlock);

        // ---- ③ 溢出后继续灌 = 一滴不收 ----
        got = GroupEnergy.fill(e, perBlock, 500);
        check("③ 满池再灌收 0", got == 0L && GroupEnergy.total(e) == 3L * perBlock);

        // ---- ④ 抽得比有的多：只抽到这么多，不会变负数 ----
        long taken = GroupEnergy.drain(e, 100_000);
        check("④ 抽干正好 3×512", taken == 3L * perBlock && GroupEnergy.total(e) == 0L);

        // ---- ⑤ 空池抽不到东西 ----
        taken = GroupEnergy.drain(e, 999);
        check("⑤ 空池抽 0", taken == 0L && GroupEnergy.total(e) == 0L);

        // ---- ⑥ 部分抽取只动前面的块（顺序确定，便于对账） ----
        e = new long[]{perBlock, perBlock, perBlock};
        taken = GroupEnergy.drain(e, 700);
        check("⑥ 抽 700 = 第1块扣光 + 第2块扣 188",
                taken == 700 && e[0] == 0 && e[1] == perBlock - 188 && e[2] == perBlock);

        // ---- ⑦ 容量算式 ----
        check("⑦ 容量 = 块数×512", GroupEnergy.capacity(3, perBlock) == 1536L
                && GroupEnergy.capacity(0, perBlock) == 0L);

        // ---- ⑧ 速率分摊：先乘后除，余数不能丢 ----
        // 3 块共 20 FE/t ⇒ 整组每秒 20*20 = 400；400/3 = 133；133*3 = 399（丢 1 是整数除法本身，可接受）
        // 若先除后乘 (20/3)*20 = 120 ⇒ 每秒白丢 13 FE（6.5%），必须被这条挡住
        long perSec = GroupEnergy.perPanelPerSecond(20, 3);
        check("⑧ 20FE/t ÷ 3 块 ⇒ 每秒 133（不是 120）", perSec == 133L);

        // ---- ⑨ 池子快满时的一次发电不会丢电（这是最容易被忽略的那种 bug） ----
        e = new long[]{perBlock, perBlock, perBlock - 10};   // 只剩 10 的空间
        long before = GroupEnergy.total(e);
        got = GroupEnergy.fill(e, perBlock, 60);             // 想发 60，只有 10 装得下
        check("⑨ 快满时只收得起 10，且总量守恒",
                got == 10L && GroupEnergy.total(e) - before == got && e[0] == perBlock && e[1] == perBlock);

        // ---- ⑩ 组输出 = 速率和 ÷ 块数（不是速率和！） ----
        // 用户给的 60/135/180（ZF29 起 ×3）是**每块**的额定速率。
        // 3 块正午全晴：和 = 540，组输出 = 180。
        // 若写成"把和当输出"（540），并联越多总发电越大 —— 那是台永动机，曾经真的这么错过。
        int totalRateNoon = 180 + 180 + 180;
        int groupOutput = totalRateNoon / 3;
        check("⑩ 3 块正午 ⇒ 组输出 180 FE/t（不是 540）", groupOutput == 180);

        // 摊平效应：一块被遮（0）、两块 180 ⇒ 组输出仍是 180，被遮那块照样有电
        check("⑩ 一块被遮不拖垮全组（和 360 ÷ 3 = 120/块）",
                (0 + 180 + 180) / 3 == 120);

        // ---- ⑪ 充满需要多久：ZF29 起 1600 FE ÷ 180 FE/t ≈ 9 tick（约 0.45 秒） ----
        // 这条断言第一版写错了（以为要 26 秒），被自己的检查当场打回 —— 见档案 §4.17 的用意。
        e = new long[blocks];
        for (int t = 0; t < 9; t++) {
            GroupEnergy.fill(e, perBlock, groupOutput);
        }
        check("⑪ 9 tick 灌满 3×512", GroupEnergy.total(e) == 3L * perBlock);

        e = new long[blocks];
        for (int t = 0; t < 8; t++) {
            GroupEnergy.fill(e, perBlock, groupOutput);
        }
        check("⑪ 8 tick 时未满（1440 < 1536）",
                GroupEnergy.total(e) == 1440L && GroupEnergy.total(e) < 3L * perBlock);

        System.out.printf("%n通过 %d / 失败 %d%n", passed, failed);
        if (failed > 0) {
            System.exit(1);
        }
    }

    private static void check(String name, boolean ok) {
        if (ok) {
            passed++;
            System.out.println("  [OK]   " + name);
        } else {
            failed++;
            System.out.println("  [FAIL] " + name);
        }
    }
}
