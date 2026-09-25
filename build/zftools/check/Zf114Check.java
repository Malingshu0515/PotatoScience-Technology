package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * ⚠⚠ <b>诊断探针（ZF114 临时文件，验证完必须删）</b>：星轨坠的端到端取证。
 *
 * <p>静态校验（{@code _zf114_verify.py}）只能证明"代码长对了"，
 * 下面这些**只有真服务端 + 真 tick 才能回答**：</p>
 * <ol>
 *   <li><b>起手</b>：右键扣 1 点耐久（4→3）、仪式进了表、截止时刻 = 现在 + 600；</li>
 *   <li><b>可取消窗口</b>：第 40 tick 再右键 ⇒ 取消、**不再扣耐久**、通报数为 0；</li>
 *   <li><b>锁定</b>：第 300 tick（已过 10 秒）再右键 ⇒ 拒绝，仪式仍在；通报已发；</li>
 *   <li><b>落点固定</b>：第 560 tick 把玩家传送到 30 格外 ⇒ 陨石仍然砸**原来那一格**
 *       （用户拍板的语义：定在右键那一刻的位置）；</li>
 *   <li><b>陨石</b>：y=200 生成、威力落在 7~20；</li>
 *   <li><b>落地</b>：爆炸**破坏地形**（木平台被炸掉若干格）+ **有火**（平台上出现火方块）；</li>
 *   <li><b>掉落档位</b>：喷出的粗矿逐件核对 —— 7~12 只许铁/铜；13 以上全部来自
 *       {@code #c:raw_materials}；15 以上**恰好**多 3 个粗振金。件数 = 6 + min(6, (威力-7)/2)。</li>
 * </ol>
 *
 * <p>物品是通过 {@link EntityJoinLevelEvent} 记账的 —— **不能在 ServerStartedEvent 里用
 * getEntitiesOfClass 数刚 addFreshEntity 的实体**（档案 §4.32 第三条：那个阶段查不到，
 * 会让"喷射了 0 个"这种假通过溜过去）。</p>
 */
public final class Zf114Check {

    private static final String TAG = "[A114] ";
    private static final String REPORT = "E:\\PotatoST\\build\\zftools\\check\\zf114_星轨坠取证.log";
    private static final TagKey<Item> RAW_MATERIALS =
            TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", "raw_materials"));

    // 时间线（tick，相对第一次起手）
    private static final int T_CANCEL = 40;      // 窗口内再右键
    private static final int T_RESTART = 60;     // 重新起手
    private static final int T_LOCKED = 300;     // 过了 10 秒再右键 ⇒ 必须被拒
    private static final int T_MOVE_AWAY = 560;  // 玩家跑开 30 格
    private static final int T_DEADLINE = 760;   // 无论如何在这里收工

    private static boolean registered;
    private static boolean started;
    private static int failed;
    private static long t0;
    private static BlockPos target;
    private static ServerLevel level;
    private static ServerPlayer player;
    private static final List<ItemStack> sprayed = new ArrayList<>();
    private static final StringBuilder report = new StringBuilder();
    /** 玩家跑开之后、陨石落地之前，新位置脚下 5×5 的地面快照（用来证明落点没跟着人跑）。 */
    private static List<BlockState> awayBefore;
    /** 只有仪式真的起了手才开始记"喷出来的矿"（防止旧掉落物混进来）。 */
    private static boolean counting;
    private static int sawMeteor = -1;
    private static boolean impactSeen;

    private Zf114Check() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf114Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    // ============================================================
    //  开场：建假玩家 + 木平台 + 第一次起手
    // ============================================================
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (started) {
            return;
        }
        started = true;
        failed = 0;
        try {
            level = event.getServer().overworld();
            // ⚠ 试验场必须**悬空**（y=120 的木平台，离地 50 多格）：
            //   · 第四次跑踩到"区块没加载 ⇒ 高度图给 y=-63 ⇒ 平台被埋进深层石头"；
            //   · 第五次跑踩到"平台铺在地面上 ⇒ 爆炸把地下的天然矿石炸出来，
            //     被我的记账当成'喷出来的矿'（17 件 vs 8 件）"，火也被地面环境吃掉。
            //   悬空平台一次解决三条：爆炸够不到任何天然方块、木板掉落物不是矿（会被过滤掉）、
            //   木板可燃所以"带火"这条终于有确定的观测对象。
            int px = 200;
            int pz = 200;
            int py = 120;
            BlockPos probeColumn = new BlockPos(px, py, pz);
            level.getChunkAt(probeColumn);
            int cx = px >> 4;
            int cz = pz >> 4;
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 1; dz++) {
                    level.setChunkForced(cx + dx, cz + dz, true);
                }
            }

            BlockState planks = Blocks.OAK_PLANKS.defaultBlockState();
            int placed = 0;
            for (int dx = -7; dx <= 7; dx++) {
                for (int dz = -7; dz <= 7; dz++) {
                    level.setBlockAndUpdate(new BlockPos(px + dx, py, pz + dz), planks);
                    placed++;
                    for (int dy = 1; dy <= 4; dy++) {
                        level.setBlockAndUpdate(new BlockPos(px + dx, py + dy, pz + dz),
                                Blocks.AIR.defaultBlockState());
                    }
                }
            }
            target = new BlockPos(px, py + 1, pz);
            failed += check("悬空木平台铺好了（" + placed + " 格，实际应在 225）", placed == 225);

            // ⚠ 清场：同一个存档反复跑探针时，**前几次喷出来的矿还躺在原地**，
            //   区块一加载它们就会被 EntityJoinLevelEvent 收进来 ⇒ 第七次跑报出 16 件（本次 9 件 + 旧 7 件）。
            //   每次开跑先把落点周围 48 格内的掉落物清干净，试验场才是可复现的。
            int cleared = 0;
            for (ItemEntity old : level.getEntitiesOfClass(ItemEntity.class,
                    new AABB(target).inflate(48.0D))) {
                old.discard();
                cleared++;
            }
            say(TAG + "清场：丢掉 " + cleared + " 件旧掉落物");

            GameProfile profile = new GameProfile(
                    UUID.nameUUIDFromBytes("zf114probe".getBytes(StandardCharsets.UTF_8)), "zf114probe");
            player = new ServerPlayer(event.getServer(), level, profile, ClientInformation.createDefault());
            // ⚠ 无头服务端里 new 出来的玩家没有连接，发任何包都会 NPE（档案 §4.43）
            // ⚠⚠ ZF114 的新发现：光 `new Connection(SERVERBOUND)` **还不够** ——
            //    1.21.1 的某些 send 路径会解引用 `connection.channel()`（channel 为 null 时抛
            //    "Cannot invoke io.netty.channel.Channel.attr(...) because Connection.channel() is null"）。
            //    实测：系统聊天包（displayClientMessage 走的那个）就会踩。
            //    修法是给连接塞一个 netty 的 EmbeddedChannel（本地通道，不进网络、写进去只是入队）。
            //    ⇒ 以后写探针要发消息的，照抄这一段，别只挂 Connection。
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
            player.moveTo(target.getX() + 0.5D, target.getY(), target.getZ() + 0.5D, 0.0F, 0.0F);
            player.getInventory().setItem(0, new ItemStack(ModItems.STARFALL_PENDANT.get()));
            player.getInventory().selected = 0;      // 1.21.1 只有公有字段 selected，没有 setSelectedSlot

            say(TAG + "① 物品属性");
            ItemStack stack = player.getMainHandItem();
            failed += check("手上拿的确实是星轨坠", stack.is(ModItems.STARFALL_PENDANT.get()));
            failed += check("耐久上限 = 4（实际 " + stack.getMaxDamage() + "）", stack.getMaxDamage() == 4);
            failed += check("不可附魔（isEnchantable = false）", !stack.isEnchantable());
            failed += check("附魔价值 = 0（实际 " + stack.getItem().getEnchantmentValue() + "）",
                    stack.getItem().getEnchantmentValue() == 0);
            failed += check("粗振金挂进了 c:raw_materials",
                    inRawTag(ModItems.RAW_VIBRANIUM.get()));

            say(TAG + "② 第一次起手");
            StarfallRitualManager.resetForTest();
            usePendant();
            failed += check("仪式已建立", StarfallRitualManager.isActive(player.getUUID()));
            failed += check("耐久 4 → 3（实际 " + (4 - stack.getDamageValue()) + " 点剩余）",
                    stack.getDamageValue() == 1);
            long end = StarfallRitualManager.endTickOf(player.getUUID());
            failed += check("截止时刻 = 现在 + 600 tick（实际 " + (end - level.getGameTime()) + "）",
                    end - level.getGameTime() == 600);
            t0 = level.getGameTime();
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
        }
    }

    // ============================================================
    //  时间线
    // ============================================================
    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (player == null || level == null) {
            return;
        }
        try {
            long t = level.getGameTime() - t0;

            if (t == T_CANCEL) {
                say(TAG + "③ 窗口内再右键（应当取消）");
                ItemStack stack = player.getMainHandItem();
                int dmgBefore = stack.getDamageValue();
                usePendant();
                failed += check("仪式被取消", !StarfallRitualManager.isActive(player.getUUID()));
                failed += check("取消不额外扣耐久（" + dmgBefore + " → " + stack.getDamageValue() + "）",
                        stack.getDamageValue() == dmgBefore);
                failed += check("取消阶段一条通报都不该发（实际 " + StarfallRitualManager.debugAnnouncements + "）",
                        StarfallRitualManager.debugAnnouncements == 0);
            }

            if (t == T_RESTART) {
                say(TAG + "④ 重新起手");
                usePendant();
                failed += check("第二次仪式已建立", StarfallRitualManager.isActive(player.getUUID()));
                failed += check("耐久 3 → 2（实际 " + (4 - player.getMainHandItem().getDamageValue()) + " 点剩余）",
                        player.getMainHandItem().getDamageValue() == 2);
                failed += check("落点 = 玩家当时所在格（" + target + "）",
                        Math.abs(player.getX() - (target.getX() + 0.5D)) < 1.5D);
                counting = true;   // 从这一刻起才记"喷出来的矿"（之前的一律不算）
            }

            if (t == T_LOCKED) {
                say(TAG + "⑤ 过了 10 秒再右键（应当被拒）");
                usePendant();
                failed += check("仪式仍未被取消", StarfallRitualManager.isActive(player.getUUID()));
                failed += check("已经通报过（实际 " + StarfallRitualManager.debugAnnouncements + " 条）",
                        StarfallRitualManager.debugAnnouncements >= 1);
            }

            if (t == T_MOVE_AWAY) {
                say(TAG + "⑥ 玩家跑开 30 格（落点必须不动）");
                player.moveTo(target.getX() + 30.5D, target.getY(), target.getZ() + 0.5D, 0.0F, 0.0F);
            }

            // 跑开之后、陨石落地之前，把"新位置脚下"的地面拍一张快照。
            // ⚠ 第一版是拿"是不是木板"去比新位置 —— 那 25 格本来就不是木板（平台只铺在落点），
            //   `!is(OAK_PLANKS)` 恒真 ⇒ 假 FAIL。判据要能失败，但不能恒失败。
            if (t == T_MOVE_AWAY + 20) {
                awayBefore = new ArrayList<>();
                BlockPos away = BlockPos.containing(player.getX(), player.getY(), player.getZ());
                for (int dx = -2; dx <= 2; dx++) {
                    for (int dz = -2; dz <= 2; dz++) {
                        awayBefore.add(level.getBlockState(away.offset(dx, -1, dz)));
                    }
                }
                failed += check("跑开处的地面快照取到了 25 格（实际 " + awayBefore.size() + "）",
                        awayBefore.size() == 25);
            }

            // 陨石出现时记下它的威力
            if (sawMeteor < 0 && t > 600) {
                List<StarfallMeteorEntity> meteors = level.getEntitiesOfClass(StarfallMeteorEntity.class,
                        new AABB(target).inflate(6.0D, 260.0D, 6.0D));
                if (!meteors.isEmpty()) {
                    StarfallMeteorEntity meteor = meteors.get(0);
                    sawMeteor = meteor.getPower();
                    failed += check("陨石从 y=200 附近下来（实际 y=" + String.format("%.1f", meteor.getY()) + "）",
                            meteor.getY() > 60.0D);
                    failed += check("威力落在 7~20（实际 " + sawMeteor + "）",
                            sawMeteor >= 7 && sawMeteor <= 20);
                    failed += check("通报数 = 6 个节点 + 最后警告 + 天火降临 = 8（实际 "
                            + StarfallRitualManager.debugAnnouncements + "）",
                            StarfallRitualManager.debugAnnouncements == 8);
                }
            }

            // 落地结算：陨石没了就算落完了
            if (sawMeteor > 0 && !impactSeen && t > 620) {
                List<StarfallMeteorEntity> meteors = level.getEntitiesOfClass(StarfallMeteorEntity.class,
                        new AABB(target).inflate(64.0D, 300.0D, 64.0D));
                if (meteors.isEmpty()) {
                    impactSeen = true;
                    say(TAG + "⑦ 落地结算（威力 " + sawMeteor + "）");
                    checkImpact();
                    finish(event);
                }
            }

            if (t > T_DEADLINE && !impactSeen) {
                failed += check("陨石必须在 760 tick 内落地（没落地）", false);
                finish(event);
            }
        } catch (Throwable t) {
            say(TAG + "tick exception: " + t);
            failed++;
            finish(event);
        }
    }

    /** 记下所有新生成的**矿物**物品实体。
     *
     * <p>⚠ ZF114 第一版这里把"落点附近的一切物品实体"都记了进来 ⇒ 爆炸炸碎的木板掉落物
     * 被当成"喷出来的矿"，报出 8 件（实际 6 件矿物 + 2 摞木板）两条**假 FAIL**。
     * 记账的判据要和被测对象对齐：星轨坠只管喷矿，所以这里只收矿物。</p>
     */
    @SubscribeEvent
    public static void onEntityJoin(EntityJoinLevelEvent event) {
        if (target == null || !counting || !(event.getEntity() instanceof ItemEntity item)) {
            return;
        }
        if (item.level() != level) {
            return;
        }
        if (!item.blockPosition().closerThan(target, 40.0D)) {
            return;
        }
        ItemStack stack = item.getItem();
        if (isOre(stack)) {
            sprayed.add(stack.copy());
        }
    }

    /** 什么算"矿"：原版粗铁/粗铜，或者挂在 {@code #c:raw_materials} 上的东西。 */
    private static boolean isOre(ItemStack stack) {
        return stack.is(Items.RAW_IRON) || stack.is(Items.RAW_COPPER) || inRawTag(stack.getItem());
    }

    // ============================================================
    //  落地断言
    // ============================================================
    private static void checkImpact() {
        // ① 地形被破坏：平台中心 11×11 必须少掉若干格（这一条量的是"平台自己的脚印"）
        int destroyed = 0;
        for (int dx = -5; dx <= 5; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                BlockPos p = target.offset(dx, -1, dz);
                if (!level.getBlockState(p).is(Blocks.OAK_PLANKS)) {
                    destroyed++;
                }
            }
        }
        failed += check("爆炸破坏了地形（木平台少了 " + destroyed + " 格）", destroyed >= 10);

        // 带火：爆炸带火时会把火点在"实心方块上方的空气"里。
        // ⚠ 扫描范围必须盖住**整条爆坑**：上一版只扫中心 11×11，而中心被整个蒸发掉、
        //   火恰好点在被炸剩的边缘木板上 ⇒ 报 0 格（假 FAIL）。判据的范围要和现象的范围对齐。
        int fire = 0;
        for (int dx = -14; dx <= 14; dx++) {
            for (int dz = -14; dz <= 14; dz++) {
                for (int dy = -1; dy <= 3; dy++) {
                    if (level.getBlockState(target.offset(dx, dy, dz)).is(Blocks.FIRE)) {
                        fire++;
                    }
                }
            }
        }
        failed += check("带火：爆坑范围内出现火方块（" + fire + " 格）", fire >= 1);

        // ② 落点在"右键那一刻"的位置，而不是玩家跑开后的位置：
        //    拿"跑开处落地前的地面快照"逐格比 —— 变了就说明陨石追着玩家跑了
        BlockPos away = BlockPos.containing(player.getX(), player.getY(), player.getZ());
        int changedAway = -1;
        if (awayBefore != null && awayBefore.size() == 25) {
            changedAway = 0;
            int index = 0;
            for (int dx = -2; dx <= 2; dx++) {
                for (int dz = -2; dz <= 2; dz++) {
                    if (!level.getBlockState(away.offset(dx, -1, dz)).equals(awayBefore.get(index))) {
                        changedAway++;
                    }
                    index++;
                }
            }
        }
        failed += check("玩家跑开后原地毫发无伤（新位置脚下地面变了 " + changedAway + " 格，应当 0）",
                changedAway == 0);

        // ③ 掉落档位
        int power = sawMeteor;
        int wantCount = 6 + Math.min(6, Math.max(0, power - 7) / 2);
        int vibranium = 0;
        int offTier = 0;
        for (ItemStack s : sprayed) {
            if (s.is(ModItems.RAW_VIBRANIUM.get())) {
                vibranium++;
            } else if (power <= 12) {
                if (!s.is(Items.RAW_IRON) && !s.is(Items.RAW_COPPER)) {
                    offTier++;
                }
            } else if (!inRawTag(s.getItem())) {
                offTier++;
            }
        }
        int expectedVibranium = power >= 15 ? 3 : 0;
        say(TAG + "   喷出 " + sprayed.size() + " 件：" + summary());
        failed += check("喷射件数 = " + wantCount + "（实际 " + (sprayed.size() - vibranium) + " 件普通粗矿）",
                sprayed.size() - vibranium == wantCount);
        failed += check("档位外的矿物 = 0 件（实际 " + offTier + "）", offTier == 0);
        failed += check("粗振金 = " + expectedVibranium + " 个（实际 " + vibranium + "）",
                vibranium == expectedVibranium);

        // ④ 落地后 HUD 收尾：仪式表里不该再留着这一条
        failed += check("落地后仪式已出表", !StarfallRitualManager.isActive(player.getUUID()));
    }

    private static String summary() {
        StringBuilder sb = new StringBuilder();
        for (ItemStack s : sprayed) {
            sb.append(s.getHoverName().getString()).append("×").append(s.getCount()).append(" ");
        }
        return sb.toString().trim();
    }

    private static boolean inRawTag(Item item) {
        HolderSet.Named<Item> tag = BuiltInRegistries.ITEM.getTag(RAW_MATERIALS).orElse(null);
        return tag != null && tag.stream().anyMatch(h -> h.value() == item);
    }

    private static void usePendant() {
        ItemStack stack = player.getMainHandItem();
        InteractionResultHolder<ItemStack> result = stack.getItem().use(level, player, InteractionHand.MAIN_HAND);
        say(TAG + "      右键结果 = " + result.getResult());
    }

    private static int check(String name, boolean ok) {
        say(TAG + (ok ? "  [OK]   " : "  [FAIL] ") + name);
        return ok ? 0 : 1;
    }

    private static void say(String line) {
        System.out.println(line);
        report.append(line).append('\n');
    }

    private static void finish(ServerTickEvent.Post event) {
        say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
        try {
            Files.write(Paths.get(REPORT), report.toString().getBytes(StandardCharsets.UTF_8));
            say(TAG + "report: " + REPORT);
        } catch (Throwable t) {
            say(TAG + "report write failed: " + t);
        }
        say(TAG + "done, halting server");
        event.getServer().halt(false);
    }
}
