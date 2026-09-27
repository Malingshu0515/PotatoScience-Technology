package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * ⚠⚠ <b>诊断探针（ZF146 临时文件，验证完必须删）</b>：星轨坠
 * <b>「中途退出游戏 → 再进来」</b>的端到端取证（用户转述的别人反馈：
 * 「星轨坠 中途退出游戏就不会落下 再次进入就不能使用了」）。
 *
 * <p><b>这个探针的判据全部只吃"外面看得见的行为"</b>，一条都不碰本轮的实现细节，
 * 所以<b>同一份源码在改前 / 改后都能编译、都能跑</b>——改前跑出红、改后跑出绿，这才叫对照。
 * 具体地：</p>
 * <ul>
 *   <li><b>起手成没成</b>：只看<b>物品耐久</b>（{@code hurtAndBreak} 只在 STARTED 那一支被调），
 *       不看管理器里的任何表；</li>
 *   <li><b>陨石落没落 / 什么时候落</b>：只看实体表里有没有 {@link StarfallMeteorEntity}
 *       （{@code EntityJoinLevelEvent} 记账）+ 落点平台少没少方块；</li>
 *   <li><b>倒计时是不是"接着走"</b>：拿"陨石生成时刻"去比第一次开服时记下的
 *       {@code 起手时刻 + 600} —— 重头再数会差 +600、原地立刻落会差 -600，只有接着走才对得上；</li>
 *   <li><b>还能不能再用</b>：仪式还没落地时右键应当被拒（耐久不动）、落地之后再右键应当重新起手
 *       （耐久 0 → 1）。</li>
 * </ul>
 *
 * <p><b>两次开服怎么串起来</b>：第一次开服在第 {@link #HALT_AT} tick（已过 10 秒取消窗口，
 * 正是用户描述的那个时刻）把服务器<b>正常停掉</b>（{@code halt(false)} ⇒ 走完整存档流程），
 * 并把"起手时刻 / 预期落地时刻"写进 {@link #PHASE} 文件；第二次开服读这个文件接着验。</p>
 *
 * <p><b>⚠ 这个探针能证到哪、证不到哪</b>：它证的是"<b>服务端重启之后</b>倒计时还在不在"
 * （专用服务端重启、单机关掉游戏再开，都是这一类）。而用户报的"再次进入就不能使用了"那一半，
 * 出在<b>单机退回标题界面</b>那种"JVM 还活着、世界换了一茬"的场景 —— 那个场景在这个工程里
 * 自动化跑不起来（见档案 §4.150），靠的是"静态字段跨世界存活"的推理 + 本轮的结构性判据。</p>
 *
 * <p>跑法：{@code python build\zftools\_zf146_probe.py --before|--after}
 * （它负责挂载、两次开服、收报告）。</p>
 */
public final class Zf146Check {

    private static final String TAG = "[A146] ";
    private static final String DIR = "E:\\PotatoST\\build\\zftools\\check\\";
    private static final String REPORT = DIR + "zf146_星轨坠重启取证.log";
    private static final String PHASE = DIR + "_zf146_phase.txt";
    /** ⚠ 这里写字符串、**不引用** {@code StarfallRitualManager.DATA_ID}：
     *  那个常量是本轮新加的，引用它这份探针就没法在**改前**那版上编译了 ——
     *  而"同一份探针在改前跑出红、改后跑出绿"正是这一轮唯一的对照手段。 */
    private static final String DATA_NAME = "potato_s_t_starfall";

    /** 试验场：悬空木平台（照抄 ZF114 —— 离地 50 多格，爆炸够不到天然地形）。 */
    private static final int PX = 200;
    private static final int PY = 120;
    private static final int PZ = 200;

    /** 第一次开服：第几 tick 退出（> 200 ⇒ 已过可取消窗口，锁定期退出才是用户报的那个场景）。 */
    private static final int HALT_AT = 300;
    /**
     * 第二次开服：预期落地时刻之后再等这么多 tick 还没落地就认输。
     *
     * <p>⚠ 这个数必须**小于**一次新起手的 600 tick：第二次开服进来时那次"被拒"的右键，
     * 在<b>改前</b>那版会因为"表是空的"而真的起一场新仪式（600 tick 后才落），
     * 宽限期要是 ≥600，那场新仪式的陨石会被当成"上一次的陨石落下来了" ⇒ 假绿。</p>
     */
    private static final int GRACE = 250;

    private static boolean started;
    private static boolean isRun2;
    private static boolean finished;
    private static int failed;
    private static ServerLevel level;
    private static ServerPlayer player;
    private static BlockPos target;
    private static final StringBuilder report = new StringBuilder();

    private static UUID playerId;
    private static long phaseUseTick;       // 第一次开服：右键那一刻的世界时间
    private static long phaseEndTick;       // 第一次开服：预期落地时刻（起手 + 600）
    private static long meteorTick = -1L;   // 第二次开服：陨石生成的时刻
    private static int meteorPower = -1;
    private static boolean impactSeen;
    private static boolean deadlineHit;

    private Zf146Check() {
    }

    public static void register() {
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf146Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    // ============================================================
    //  开场
    // ============================================================
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (started) {
            return;
        }
        started = true;
        try {
            level = event.getServer().overworld();
            playerId = UUID.nameUUIDFromBytes("zf146probe".getBytes(StandardCharsets.UTF_8));
            String worldName = event.getServer().getWorldData().getLevelName();
            Path dataFile = event.getServer().getWorldPath(LevelResource.ROOT)
                    .resolve("data").resolve(DATA_NAME + ".dat");
            isRun2 = Files.exists(Paths.get(PHASE));
            say(TAG + "世界 = " + worldName + "，本次是第 " + (isRun2 ? "2" : "1") + " 次开服");
            say(TAG + "存档数据文件 = " + dataFile + "（存在 " + Files.exists(dataFile) + "）");

            buildArena();

            GameProfile profile = new GameProfile(playerId, "zf146probe");
            player = new ServerPlayer(event.getServer(), level, profile, ClientInformation.createDefault());
            // ⚠ 无头服务端里 new 出来的玩家没有连接，发任何包都会 NPE（档案 §4.43）；
            //   1.21.1 还要给 Connection 塞一个 EmbeddedChannel，否则 channel() 为 null 会炸
            //   （ZF114 踩过：系统聊天包就会踩）。照抄 ZF114 那一段。
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
            player.getInventory().setItem(0, new ItemStack(ModItems.STARFALL_PENDANT.get()));
            player.getInventory().selected = 0;

            if (isRun2) {
                run2Start(event, dataFile);
            } else {
                run1Start();
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

    /** 第一次开服：起手 + 记下"预期落地时刻"。 */
    private static void run1Start() {
        say(TAG + "① 起手（右键一次）");
        int before = player.getMainHandItem().getDamageValue();
        usePendant();
        int after = player.getMainHandItem().getDamageValue();
        failed += check("起手成功（耐久 " + before + " → " + after + "，只有 STARTED 那一支才扣）", after == before + 1);
        phaseUseTick = level.getGameTime();
        phaseEndTick = phaseUseTick + StarfallRitualManager.TOTAL_TICKS;
        writePhase();
        say(TAG + "    起手时刻 = " + phaseUseTick + "，预期落地时刻 = " + phaseEndTick
                + "（这次开服将在第 " + HALT_AT + " tick 正常退出）");
    }

    /** 第二次开服：读回上次记下的时刻，验"接着走"。 */
    private static void run2Start(ServerStartedEvent event, Path dataFile) {
        readPhase();
        long entryTick = level.getGameTime();
        long remain = phaseEndTick - entryTick;
        say(TAG + "① 回到世界：世界时间 = " + entryTick + "（上次退出在 " + (phaseUseTick + HALT_AT) + "）");
        say(TAG + "    预期落地时刻 = " + phaseEndTick + " ⇒ 现在应当还剩 " + remain + " tick");

        failed += check("世界时间跨重启继续、没有归零", entryTick >= phaseUseTick + HALT_AT);
        failed += check("存档里留下了仪式数据（" + DATA_NAME + ".dat）", Files.exists(dataFile));

        // 进世界就右键一次：上一次的仪式还锁着 ⇒ 必须被拒、耐久不许动。
        // ⚠ 改前那版会在这一下**真的起一场新仪式**（因为它的表是空的、旧仪式已经丢了）——
        //   这正是「再次进入就不能使用了」的反面：不是"永远锁死"，而是"上一场凭空消失"。
        say(TAG + "② 仪式未落地时右键（应当被拒）");
        int d0 = player.getMainHandItem().getDamageValue();
        usePendant();
        int d1 = player.getMainHandItem().getDamageValue();
        failed += check("被拒且耐久不动（" + d0 + " → " + d1 + "）—— 说明上一场的倒计时还在",
                d1 == d0);

        // 通报数：读回通报进度之后，这里**不该**立刻补发"还剩 20 秒 / 15 秒"两条过时通报
        int announced = StarfallRitualManager.debugAnnouncements;
        failed += check("进世界不补发过时的通报（实际 " + announced + " 条）", announced == 0);
    }

    // ============================================================
    //  时间线
    // ============================================================
    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (!started || finished || level == null) {
            return;
        }
        try {
            if (!isRun2) {
                if (level.getGameTime() - phaseUseTick >= HALT_AT) {
                    say(TAG + "② 正常退出服务器（走完整存档流程）");
                    say(TAG + "verdict: RUN1 DONE");
                    flush();
                    finished = true;
                    event.getServer().halt(false);
                }
                return;
            }

            long now = level.getGameTime();
            if (meteorTick < 0 && now > phaseEndTick + 40) {
                // 兜底轮询（万一 EntityJoinLevelEvent 没赶上，也不许把"没落"记成"落了"）
                List<StarfallMeteorEntity> meteors = level.getEntitiesOfClass(StarfallMeteorEntity.class,
                        new AABB(target).inflate(8.0D, 300.0D, 8.0D));
                if (!meteors.isEmpty()) {
                    meteorTick = now;
                    meteorPower = meteors.get(0).getPower();
                    say(TAG + "②' 兜底轮询才看到陨石：世界时间 = " + now);
                }
            }

            if (meteorTick > 0 && !impactSeen && now > meteorTick + 5) {
                List<StarfallMeteorEntity> meteors = level.getEntitiesOfClass(StarfallMeteorEntity.class,
                        new AABB(target).inflate(64.0D, 320.0D, 64.0D));
                if (meteors.isEmpty()) {
                    impactSeen = true;
                    checkImpact(event.getServer());
                    return;
                }
            }

            if (!deadlineHit && now > phaseEndTick + GRACE) {
                deadlineHit = true;
                failed += check("倒计时走完、把陨石叫下来（等到预期落地后 " + (now - phaseEndTick)
                        + " tick 也没等到）", false);
                finish(event.getServer());
            }
        } catch (Throwable t) {
            say(TAG + "tick exception: " + t);
            failed++;
            finish(event.getServer());
        }
    }

    /** 陨石一生成就记账（这是"倒计时接着走"的唯一硬证据）。 */
    @SubscribeEvent
    public static void onEntityJoin(EntityJoinLevelEvent event) {
        if (!isRun2 || meteorTick > 0 || !(event.getEntity() instanceof StarfallMeteorEntity meteor)) {
            return;
        }
        if (meteor.level() != level) {
            return;
        }
        meteorTick = level.getGameTime();
        meteorPower = meteor.getPower();
        say(TAG + "② 陨石生成：世界时间 = " + meteorTick + "（预期 " + phaseEndTick + "，差 "
                + (meteorTick - phaseEndTick) + " tick）、威力 = " + meteorPower
                + "、y = " + String.format("%.1f", meteor.getY()));
        failed += check("倒计时在**退出前剩下的**时间里走完（差 " + (meteorTick - phaseEndTick)
                + " tick，允许 ±5）", Math.abs(meteorTick - phaseEndTick) <= 5);
        failed += check("陨石从 y=200 下来（实际 y=" + String.format("%.1f", meteor.getY()) + "）",
                meteor.getY() > 150.0D);
        failed += check("威力落在 7~20（实际 " + meteorPower + "）",
                meteorPower >= StarfallRitualManager.MIN_POWER && meteorPower <= StarfallRitualManager.MAX_POWER);
        failed += check("重启后倒计时确实跑过（通报 ≥1 条，实际 " + StarfallRitualManager.debugAnnouncements + "）",
                StarfallRitualManager.debugAnnouncements >= 1);
    }

    private static void checkImpact(net.minecraft.server.MinecraftServer server) {
        say(TAG + "③ 落地结算（威力 " + meteorPower + "）");
        int destroyed = 0;
        for (int dx = -5; dx <= 5; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                if (!level.getBlockState(target.offset(dx, -1, dz)).is(Blocks.OAK_PLANKS)) {
                    destroyed++;
                }
            }
        }
        failed += check("爆炸真的发生了（落点平台少了 " + destroyed + " 格）", destroyed >= 3);

        say(TAG + "④ 落地之后再右键一次（应当能重新起手）");
        int before = player.getMainHandItem().getDamageValue();
        usePendant();
        int after = player.getMainHandItem().getDamageValue();
        failed += check("星轨坠又能用了（耐久 " + before + " → " + after + "）", after == before + 1);
        finish(server);
    }

    // ============================================================
    //  工具
    // ============================================================
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
                for (int dy = 1; dy <= 4; dy++) {
                    level.setBlockAndUpdate(new BlockPos(PX + dx, PY + dy, PZ + dz),
                            Blocks.AIR.defaultBlockState());
                }
            }
        }
        target = new BlockPos(PX, PY + 1, PZ);
        say(TAG + "试验场：悬空木平台 " + target + "（15×15）");
    }

    private static void usePendant() {
        ItemStack stack = player.getMainHandItem();
        InteractionResultHolder<ItemStack> result = stack.getItem().use(level, player, InteractionHand.MAIN_HAND);
        say(TAG + "      右键结果 = " + result.getResult());
    }

    private static void writePhase() {
        try {
            Files.write(Paths.get(PHASE), ("run=1\nuuid=" + playerId + "\nuseTick=" + phaseUseTick
                    + "\nendTick=" + phaseEndTick + "\n").getBytes(StandardCharsets.UTF_8));
        } catch (Throwable t) {
            say(TAG + "phase write failed: " + t);
            failed++;
        }
    }

    private static void readPhase() {
        try {
            for (String line : Files.readAllLines(Paths.get(PHASE), StandardCharsets.UTF_8)) {
                int eq = line.indexOf('=');
                if (eq <= 0) {
                    continue;
                }
                String k = line.substring(0, eq).trim();
                String v = line.substring(eq + 1).trim();
                if (k.equals("useTick")) {
                    phaseUseTick = Long.parseLong(v);
                } else if (k.equals("endTick")) {
                    phaseEndTick = Long.parseLong(v);
                }
            }
        } catch (Throwable t) {
            say(TAG + "phase read failed: " + t);
            failed++;
        }
    }

    private static int check(String name, boolean ok) {
        say(TAG + (ok ? "  [OK]   " : "  [FAIL] ") + name);
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
