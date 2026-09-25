package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * ⚠⚠ <b>诊断工具（ZF24 临时文件）</b>：验证"并联共享储能"的池子在真实运行时成立。
 *
 * <p>它不是一个功能，而是<b>取证手段</b>。加它的原因：关于"Jade 应该显示成一个整体"
 * 这条反馈，代码推理只能给出"我认为修好了"，而本项目一贯要求
 * <b>可证伪的证据</b>（见档案 §4.17）。这个类在专用服务器启动后自动放 3 块太阳能板，
 * 然后<b>完全按 Jade / 其他机器的方式</b>去查方块能力，把结果打成分数。</p>
 *
 * <p><b>用法</b>：交给 Gradle 的 srcDir 加进来（不进 jar），然后
 * {@code gradlew runServer} —— 日志里会出现 {@code [POOLCHECK]} 开头的行。</p>
 *
 * <p><b>为什么不做成玩家能敲的命令</b>：面向玩家的诊断命令要处理权限、补全、多语言，
 * 成本远高于"只在开发期跑一次"的价值。玩家侧的诊断入口是<b>Shift+右键</b>
 * （聊天栏那三行本来就够看）。</p>
 *
 * <p><b>验证完就删</b>：它的价值在于"跑过一次并留下了证据"，不在于长期存在。</p>
 */
public final class PoolCheck {

    private static final String TAG = "[POOLCHECK] ";
    /** 测试坐标：主世界高空，远离任何建筑 */
    private static final int TEST_Y = 200;
    private static final int BLOCKS = 3;

    private static int ticks;
    private static boolean ran;
    private static boolean registered;

    private PoolCheck() {
    }

    /**
     * 注册诊断钩子。放在 {@code PotatoST} 构造器里调用，<b>整段 try/catch 包住</b> ——
     * 诊断代码绝不能把正式版搞崩（这是"临时文件"该有的自我修养）。
     *
     * <p>⚠ 必须挂 <b>game 总线</b>（{@code NeoForge.EVENT_BUS}），不是构造器拿到的 mod 总线。
     * 第一版挂错了，NeoForge 当场报
     * {@code @SubscribeEvent ... takes an argument that is not valid for this bus}
     * —— 崩是没崩（try/catch 兜住了，这正是把诊断代码包起来的意义），但什么都没跑。</p>
     */
    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(PoolCheck.class);
            System.out.println(TAG + "诊断钩子已注册（game 总线）");
        } catch (Throwable t) {
            System.out.println(TAG + "注册失败（不影响正式功能）：" + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        try {
            Level level = event.getServer().overworld();
            int x = 0;
            int z = 0;
            for (int i = 0; i < BLOCKS; i++) {
                BlockPos p = new BlockPos(x + i, TEST_Y, z);
                level.setBlock(p, ModBlocks.SOLAR_PANEL.get().defaultBlockState(), 3);
            }
            System.out.println(TAG + "已放置 " + BLOCKS + " 块太阳能板 @ y=" + TEST_Y + "，等它们 tick");
            ticks = 0;
            ran = false;
        } catch (Throwable t) {
            System.out.println(TAG + "放置失败：" + t);
        }
    }

    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (ran || ticks < 0) {
            return;
        }
        if (++ticks < 40) {          // 40 tick = 2 秒，足够完成 BFS 与发电
            return;
        }
        ran = true;
        try {
            verify(event.getServer().overworld());
        } catch (Throwable t) {
            System.out.println(TAG + "验证抛异常：" + t);
            t.printStackTrace();
        } finally {
            System.out.println(TAG + "诊断结束，请求关服");
            event.getServer().halt(false);
        }
    }

    private static void verify(Level level) {
        List<BlockPos> row = new ArrayList<>();
        for (int i = 0; i < BLOCKS; i++) {
            row.add(new BlockPos(i, TEST_Y, 0));
        }

        int ok = 0;
        int bad = 0;

        // ---- 像 Jade / 别的机器那样查能力：逐块问，看是否同一个池子 ----
        int expectCap = SolarPanelBlockEntity.MAX_ENERGY * BLOCKS;
        for (BlockPos p : row) {
            IEnergyStorage st = level.getCapability(
                    net.neoforged.neoforge.capabilities.Capabilities.EnergyStorage.BLOCK, p, null);
            SolarPanelBlockEntity be = level.getBlockEntity(p) instanceof SolarPanelBlockEntity b ? b : null;
            String line = String.format("pos=%s 能力=%s 存量=%s 容量=%s | 组=%d 控制器=%s 速率和=%d",
                    p.toShortString(),
                    st == null ? "null" : "ok",
                    st == null ? "-" : st.getEnergyStored(),
                    st == null ? "-" : st.getMaxEnergyStored(),
                    be == null ? -1 : be.groupSize(),
                    be == null ? "-" : (be.isController() ? "本块" : "别的块"),
                    be == null ? -1 : be.getGroupTotalRate());
            System.out.println(TAG + line);
            if (st != null && st.getMaxEnergyStored() == expectCap) {
                ok++;
            } else {
                bad++;
            }
        }

        // ---- 池子是不是"一个"：三块报的存量必须完全相同 ----
        int first = -1;
        boolean same = true;
        for (BlockPos p : row) {
            IEnergyStorage st = level.getCapability(
                    net.neoforged.neoforge.capabilities.Capabilities.EnergyStorage.BLOCK, p, null);
            int got = st == null ? -1 : st.getEnergyStored();
            if (first < 0) {
                first = got;
            } else if (got != first) {
                same = false;
            }
        }
        System.out.println(TAG + "① 三块报同一存量 = " + same + "（值 " + first + "）"
                + "  ⇒ " + (same ? "通过（是一整个池子）" : "失败（各自为政）"));
        System.out.println(TAG + "② 容量 = 块数×512 = " + expectCap + " ⇒ 通过 " + ok + " / 失败 " + bad);
        System.out.println(TAG + "③ 这 2 秒池子涨了 " + first + " FE（正午晴：3 块合计应约 "
                + (SolarPanelBlockEntity.RATE_NOON / BLOCKS * 40) + " FE）");

        // ---- 速率和与分摊 ----
        SolarPanelBlockEntity any = level.getBlockEntity(row.get(0)) instanceof SolarPanelBlockEntity b ? b : null;
        long dayTime = level.getDayTime() % 24000L;
        int base = SolarPanelBlockEntity.clearRate(level.getDayTime());
        System.out.println(TAG + "时刻 dayTime=" + dayTime + " ⇒ 晴天基准 " + base + " FE/t"
                + "，维度有天光=" + level.dimensionType().hasSkyLight()
                + "，天气 雨=" + level.isRaining() + " 雷=" + level.isThundering());
        if (any != null) {
            // ⚠ 期望值必须**按当前时刻算**，不能硬编码正午 60：
            // 第一版写死"3 块 × 60 = 180"，而测试跑在 dayTime=13450（下午档 45），
            // 于是检查报"失败"而代码其实是对的 —— 期望值错了和代码错了长得一模一样，
            // 这正是 §4.17 说的"检查本身也会骗人"，所以下面全部改成"由当前速率推算"。
            int expectedTotal = base * BLOCKS;
            int expectedShared = expectedTotal / BLOCKS;
            System.out.println(TAG + "④ 速率和 = " + any.getGroupTotalRate()
                    + " FE/t（按当前时刻应为 " + expectedTotal + "）"
                    + (any.getGroupTotalRate() == expectedTotal ? " ⇒ 通过" : " ⇒ 失败"));
            System.out.println(TAG + "⑤ 每块分到 " + any.getSharedRate()
                    + " FE/t（应为 " + expectedShared + "，也就是每块自己的额定值）"
                    + (any.getSharedRate() == expectedShared ? " ⇒ 通过" : " ⇒ 失败"));
        }
        System.out.println(TAG + "结论：" + (same && bad == 0 && first > 0 ? "池子成立（三块同一个池子）" : "有失败，见上"));
    }
}
