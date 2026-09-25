package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.advancements.Advancement;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementNode;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.advancements.AdvancementType;
import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.advancements.DisplayInfo;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * ⚠⚠ <b>诊断工具（ZF107 的临时探针）</b>：24 条新进度（成就）+ 3 条老进度。
 *
 * <p>用户原话：「你自己发挥一下 把进度（成就）做一点 最好能引导一下玩家 全流程
 * 但也不是非得一个步骤就冒一个成就那么烦琐」。</p>
 *
 * <p>探针分四段，缺一不可：</p>
 * <ol>
 *   <li><b>账目</b>：本模组的进度一条不少（27 条全加载进来了）；</li>
 *   <li><b>树</b>：恰好一个根（新标签页）、每个节点的父指针都解析得到、从根可达；</li>
 *   <li><b>展示与判据</b>：图标物品不是空气、frame/hidden/背景图按设计、触发器在白名单内、
 *       requirements 覆盖全部判据；</li>
 *   <li><b>真触发</b>：造一个玩家，用 <b>游戏自己的 CriterionTrigger</b> 逐个点亮，
 *       负向对照同样重要 —— 无关物品不许点亮任何一条；「和」的判据只给一半不许亮；
 *       <b>空油桶不许点亮"石油"</b>（这条是本轮唯一一个用 custom_data 子谓词的判据，
 *       它到底是不是"部分匹配"只有真游戏能回答）。</li>
 * </ol>
 *
 * <p><b>⚠ 存档来历（如实说明）</b>：按本工程的老规矩，临时探针应当在<b>从 {@code src} 删掉之前</b>
 * 先抄一份到 {@code build/zftools/check/}。ZF107 这一轮我<b>先删了、没先抄</b>（我的 slip），
 * 而它也没进第一个 git 提交 ⇒ 这份存档是<b>事后按本轮会话里的原文重建</b>的。
 * 可信度靠两条外部证据兜：① 运行时输出 {@code build/zftools/_zf107_probe_utf8.txt}
 * （26918 字节，325 项 [OK]、0 FAIL）；② 重建件里每一条断言文案都能在该报告里逐条找到
 * （见 {@code _zf107_probe_archive.py} 的核对结果）。<b>下一次别再省这一步。</b></p>
 *
 * <p>挂载方式（当时）：`PotatoST` 构造器末尾加一行 `Zf107Check.register();`，跑完用
 * {@code _zf107_unprobe.py} 摘掉，并逐字节核对 `PotatoST.java` 回到改前件。</p>
 */
public final class Zf107Check {

    private static final String TAG = "[A107] ";
    private static final String NS = PotatoST.MODID;

    /** 本模组应当存在的进度：3 条老的 + 24 条新的 */
    private static final List<String> EXPECT = Arrays.asList(
            "new_beginning", "clean_energy", "stronger_power",
            "crushing", "pressing", "wiring", "first_power", "capacitor",
            "blast_furnace", "steel", "titanium", "electrolyzer", "gas_handling",
            "alloy_smelter", "light_alloy", "hard_alloy", "stable_block",
            "titanium_tools", "oil", "distillation", "fuel", "sulfur", "ammonia",
            "combustion", "acid", "music_disc_anvil", "music_disc_jasmine");

    private static final List<String> HIDDEN = Arrays.asList("music_disc_anvil", "music_disc_jasmine");

    private static final List<String> GOALS = Arrays.asList(
            "blast_furnace", "steel", "titanium", "alloy_smelter", "hard_alloy",
            "distillation", "combustion", "acid");

    /** 老两条的父链本轮改挂了 first_power */
    private static final List<String> REPARENTED = Arrays.asList("clean_energy", "stronger_power");

    private static boolean registered;
    private static int failed;

    /**
     * ⚠ §4.50：`runServer` 重定向出来的日志里，中文会被 JVM 按平台默认编码（GBK）打乱成
     * `锟斤拷` —— 上一轮就是这样丢掉一整份证据的。所以探针自己攒一份 **UTF-8 报告**，
     * 路径必须**绝对**（runServer 的工作目录不是工程根），并且要在 {@code halt()} **之前**写。
     */
    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf107_probe_utf8.txt";

    private Zf107Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF107 探针报告（成就树 + 真触发）· UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "全绿" : failed + " 条 FAIL") + "\n\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf107Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        try {
            ServerLevel level = event.getServer().overworld();
            Map<String, AdvancementHolder> mine = new java.util.LinkedHashMap<>();
            for (AdvancementHolder h : event.getServer().getAdvancements().getAllAdvancements()) {
                if (h.id().getNamespace().equals(NS)) {
                    mine.put(h.id().getPath(), h);
                }
            }
            checkInventory(mine);
            checkTree(event, mine);
            checkDisplayAndCriteria(mine);
            checkTriggers(event, level, mine);
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
        } finally {
            say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
            say(TAG + "done, halting server");
            flushReport();
            event.getServer().halt(false);
        }
    }

    private static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(NS, path);
    }

    private static ItemStack stack(String path) {
        Item item = BuiltInRegistries.ITEM.get(id(path));
        return new ItemStack(item);
    }

    // ============================================================
    //  ① 账目
    // ============================================================
    private static void checkInventory(Map<String, AdvancementHolder> mine) {
        say(TAG + "① inventory: " + EXPECT.size() + " advancements of " + NS);
        List<String> got = new ArrayList<>(new TreeSet<>(mine.keySet()));
        say(TAG + "    " + got);
        failed += check("本模组进度 = " + EXPECT.size() + " 条（实际 " + got.size() + "，多出来的："
                + extra(got, EXPECT) + "）", got.size() == EXPECT.size());
        for (String p : EXPECT) {
            failed += check("加载得到 " + NS + ":" + p, mine.containsKey(p));
        }
    }

    private static List<String> extra(List<String> got, List<String> want) {
        List<String> out = new ArrayList<>(got);
        out.removeAll(want);
        return out;
    }

    // ============================================================
    //  ② 树
    // ============================================================
    private static void checkTree(ServerStartedEvent event, Map<String, AdvancementHolder> mine) {
        say(TAG + "② tree: one root, every parent resolves, every node reachable");
        List<String> roots = new ArrayList<>();
        for (String p : mine.keySet()) {
            if (mine.get(p).value().parent().isEmpty()) {
                roots.add(p);
            }
        }
        java.util.Collections.sort(roots);
        failed += check("恰好 1 个根（实际 " + roots + "）", roots.equals(Arrays.asList("new_beginning")));
        boolean inTree = false;
        for (AdvancementNode n : event.getServer().getAdvancements().tree().roots()) {
            if (n.holder().id().equals(id("new_beginning"))) {
                inTree = true;
            }
        }
        failed += check("根在 AdvancementTree.roots() 里（否则 GUI 里没有这个标签页）", inTree);
        for (String p : EXPECT) {
            AdvancementHolder h = mine.get(p);
            if (h == null) {
                continue;
            }
            Optional<ResourceLocation> par = h.value().parent();
            if (par.isPresent()) {
                failed += check(p + " 的父 " + par.get() + " 是本模组的进度",
                        par.get().getNamespace().equals(NS) && mine.containsKey(par.get().getPath()));
            }
        }
        for (String p : REPARENTED) {
            AdvancementHolder h = mine.get(p);
            failed += check(p + " 的父链改挂 first_power（实际 "
                            + (h == null ? "缺失" : String.valueOf(h.value().parent().orElse(null))) + "）",
                    h != null && h.value().parent().map(id("first_power")::equals).orElse(false));
        }
        // 从根走一遍：能到达的节点数必须等于 27（父指针成环或有孤岛都会当场露馅）
        Set<String> seen = new HashSet<>();
        java.util.ArrayDeque<AdvancementNode> queue = new java.util.ArrayDeque<>();
        for (AdvancementNode n : event.getServer().getAdvancements().tree().roots()) {
            queue.add(n);
        }
        while (!queue.isEmpty()) {
            AdvancementNode n = queue.poll();
            if (n.holder().id().getNamespace().equals(NS)) {
                seen.add(n.holder().id().getPath());
            }
            for (AdvancementNode c : n.children()) {
                queue.add(c);
            }
        }
        List<String> unreachable = new ArrayList<>(EXPECT);
        unreachable.removeAll(seen);
        failed += check("27 条全部从根可达（够不着的：" + unreachable + "）", unreachable.isEmpty());
    }

    // ============================================================
    //  ③ 展示与判据
    // ============================================================
    private static void checkDisplayAndCriteria(Map<String, AdvancementHolder> mine) {
        say(TAG + "③ display & criteria of all " + EXPECT.size());
        int hidden = 0;
        int roots = 0;
        for (String p : EXPECT) {
            AdvancementHolder h = mine.get(p);
            if (h == null) {
                continue;
            }
            Advancement a = h.value();
            Optional<DisplayInfo> opt = a.display();
            if (opt.isEmpty()) {
                failed += check(p + " 有 display 段", false);
                continue;
            }
            DisplayInfo d = opt.get();
            AdvancementType want = HIDDEN.contains(p) ? AdvancementType.CHALLENGE
                    : (GOALS.contains(p) ? AdvancementType.GOAL : AdvancementType.TASK);
            failed += check(p + "：frame = " + want + "（实际 " + d.getType() + "）", d.getType() == want);
            failed += check(p + "：toast 与公告都开（" + d.shouldShowToast() + "/" + d.shouldAnnounceChat() + "）",
                    d.shouldShowToast() && d.shouldAnnounceChat());
            failed += check(p + "：hidden = " + HIDDEN.contains(p) + "（实际 " + d.isHidden() + "）",
                    d.isHidden() == HIDDEN.contains(p));
            if (d.isHidden()) {
                hidden++;
            }
            String icon = BuiltInRegistries.ITEM.getKey(d.getIcon().getItem()).toString();
            failed += check(p + "：图标物品不是空气（" + icon + " x" + d.getIcon().getCount() + "）",
                    d.getIcon().getItem() != Items.AIR && d.getIcon().getCount() == 1);
            failed += check(p + "：图标 id 属于本模组（" + icon + "）", icon.startsWith(NS + ":"));
            if (a.parent().isEmpty()) {
                roots++;
                failed += check(p + "：根有背景图（" + d.getBackground() + "）", d.getBackground().isPresent());
            } else {
                failed += check(p + "：不是根就不该有背景图（" + d.getBackground() + "）",
                        d.getBackground().isEmpty());
            }
            // 判据
            Set<String> names = a.criteria().keySet();
            Set<String> covered = new HashSet<>();
            for (List<String> g : a.requirements().requirements()) {
                covered.addAll(g);
            }
            failed += check(p + "：requirements 覆盖全部判据（" + names.size() + " 条）",
                    covered.equals(names) && !names.isEmpty());
            for (Map.Entry<String, net.minecraft.advancements.Criterion<?>> e : a.criteria().entrySet()) {
                boolean ok = e.getValue().trigger() == CriteriaTriggers.INVENTORY_CHANGED
                        || e.getValue().trigger() == CriteriaTriggers.PLACED_BLOCK;
                failed += check(p + "/" + e.getKey() + "：触发器在白名单内（" + e.getValue().trigger() + "）", ok);
            }
        }
        failed += check("隐藏成就正好 " + HIDDEN.size() + " 条（实际 " + hidden + "）", hidden == HIDDEN.size());
        failed += check("根节点正好 1 个（实际 " + roots + "）", roots == 1);
    }

    // ============================================================
    //  ④ 真触发
    // ============================================================
    private static void checkTriggers(ServerStartedEvent event, ServerLevel level,
                                      Map<String, AdvancementHolder> mine) {
        say(TAG + "④ real triggers: hand over items, watch the progress");
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes("zf107probe".getBytes(StandardCharsets.UTF_8)), "zf107probe");
        ServerPlayer player = new ServerPlayer(event.getServer(), level, profile, ClientInformation.createDefault());
        // ⚠ 必须有这一句（ZF70 的教训）：无头服务端里 new 出来的玩家没有连接，
        //   完成带"配方奖励"的进度时发奖励包会 NPE。挂一个没连上的 Connection，send 只会进队列。
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                event.getServer(), conn, player,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        say(TAG + "    player: " + player.getGameProfile().getName()
                + " @ " + level.dimension().location());

        Set<String> doneAtStart = doneSet(player, mine);
        failed += check("起始状态：一条都没点亮（实际 " + doneAtStart + "）", doneAtStart.isEmpty());

        // --- 负向对照①：无关物品（海盐）不许点亮任何一条 ---
        inventory(player, stack("sea_salt"));
        failed += check("拿无关物品（海盐）⇒ 一条都不亮（实际 " + doneSet(player, mine) + "）",
                doneSet(player, mine).isEmpty());

        // --- 「和」的判据：只给一半不许亮（gas_handling = 高压气罐 + 灌装机）---
        inventory(player, stack("high_pressure_tank"));
        failed += check("只给高压气罐 ⇒ 气体的存取**不**亮（实际 " + isDone(player, mine, "gas_handling") + "）",
                !isDone(player, mine, "gas_handling"));
        failed += check("此时已完成判据数 = 1（实际 " + count(player, mine, "gas_handling") + "）",
                count(player, mine, "gas_handling") == 1);
        inventory(player, stack("filling_machine"));
        failed += check("再给灌装机 ⇒ 气体的存取亮（实际 " + isDone(player, mine, "gas_handling") + "）",
                isDone(player, mine, "gas_handling"));

        // --- 老那条「和」：发电机 + 动力能源捕获器 ---
        inventory(player, stack("generator"));
        failed += check("只给发电机 ⇒ 更强劲的电源**不**亮",
                !isDone(player, mine, "stronger_power"));
        inventory(player, stack("power_capturer"));
        failed += check("再给动力能源捕获器 ⇒ 更强劲的电源亮",
                isDone(player, mine, "stronger_power"));

        // --- 单物品逐条点亮（每条都自己给自己，父链没完成也照样能亮：进度不靠父链解锁）---
        String[][] pairs = {
                {"new_beginning", "micro_crusher"},
                {"crushing", "iron_powder"},
                {"pressing", "iron_plate"},
                {"wiring", "terminal"},
                {"first_power", "low_generator"},
                {"capacitor", "capacitor"},
                {"blast_furnace", "electric_blast_furnace"},
                {"steel", "high_carbon_steel"},
                {"titanium", "titanium_ingot"},
                {"electrolyzer", "electrolyzer"},
                {"alloy_smelter", "alloy_smelter"},
                {"light_alloy", "light_titanium_alloy"},
                {"hard_alloy", "hard_titanium_alloy"},
                {"stable_block", "stable_metal_block"},
                {"titanium_tools", "titanium_alloy_pickaxe"},
                {"distillation", "distillation_controller"},
                {"fuel", "diesel_bucket"},
                {"sulfur", "sulfur"},
                {"ammonia", "ammonia_synthesis_chamber"},
                {"combustion", "combustion_chamber"},
                {"acid", "acidic_reaction_chamber"},
                {"music_disc_anvil", "music_disc_anvil_of_the_republic"},
                {"music_disc_jasmine", "music_disc_jasmine_flower"},
        };
        for (String[] pair : pairs) {
            String path = pair[0];
            String itemId = pair[1];
            ItemStack st = stack(itemId);
            if (st.getItem() == Items.AIR) {
                failed += check(path + " 的判据物品 " + itemId + " 真的注册了", false);
                continue;
            }
            inventory(player, st);
            failed += check("交给 " + itemId + " ⇒ " + path + " 点亮（实际 "
                    + isDone(player, mine, path) + "）", isDone(player, mine, path));
        }

        // --- 石油：空桶不算，装着原油才算（本轮唯一的 custom_data 子谓词）---
        AdvancementHolder oil = mine.get("oil");
        if (oil == null) {
            failed += check("石油那条进度在（没法查油桶判据）", false);
        } else {
            ItemStack empty = stack("oil_bucket");
            inventory(player, empty);
            failed += check("空油桶 ⇒ 石油**不**亮（实际 " + isDone(player, mine, "oil") + "）",
                    !isDone(player, mine, "oil"));
            ItemStack filled = stack("oil_bucket");
            int moved = OilBucketContents.fill(filled,
                    new FluidStack(ModFluids.CRUDE_OIL.get(), OilBucketContents.SOURCE_AMOUNT),
                    OilBucketContents.SOURCE_AMOUNT);
            say(TAG + "    灌了 " + moved + " mB 原油；油桶的 custom_data = "
                    + filled.get(DataComponents.CUSTOM_DATA));
            failed += check("油桶真的装进 1000 mB 原油（实际 " + moved + "）", moved == 1000);
            inventory(player, filled);
            failed += check("装着原油的油桶 ⇒ 石油亮（实际 " + isDone(player, mine, "oil") + "）",
                    isDone(player, mine, "oil"));
        }

        // --- 放置方块那条（老成就 clean_energy）---
        BlockPos wrong = new BlockPos(400, 100, 200);
        BlockPos right = new BlockPos(402, 100, 200);
        BlockState oldWrong = level.getBlockState(wrong);
        BlockState oldRight = level.getBlockState(right);
        try {
            level.setBlock(wrong, ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
            CriteriaTriggers.PLACED_BLOCK.trigger(player, wrong,
                    new ItemStack(ModBlocks.COMMON_METAL_BLOCK_ITEM.get()));
            failed += check("放一般金属块 ⇒ 入门清洁能源**不**亮",
                    !isDone(player, mine, "clean_energy"));
            level.setBlock(right, ModBlocks.SOLAR_PANEL.get().defaultBlockState(), 3);
            CriteriaTriggers.PLACED_BLOCK.trigger(player, right, stack("solar_panel"));
            failed += check("放太阳能板 ⇒ 入门清洁能源亮", isDone(player, mine, "clean_energy"));
        } finally {
            level.setBlock(wrong, oldWrong, 3);
            level.setBlock(right, oldRight, 3);
            say(TAG + "    还原 " + wrong + " 与 " + right);
        }

        // --- 收尾：27 条全亮 ---
        Set<String> done = doneSet(player, mine);
        List<String> missing = new ArrayList<>(EXPECT);
        missing.removeAll(done);
        failed += check("收尾：27 条全部点亮（没亮的：" + missing + "）", missing.isEmpty());
    }

    private static void inventory(ServerPlayer player, ItemStack stack) {
        if (stack.isEmpty()) {
            return;
        }
        player.getInventory().add(stack.copy());
        CriteriaTriggers.INVENTORY_CHANGED.trigger(player, player.getInventory(), stack.copy());
    }

    private static boolean isDone(ServerPlayer player, Map<String, AdvancementHolder> mine, String path) {
        AdvancementHolder h = mine.get(path);
        return h != null && player.getAdvancements().getOrStartProgress(h).isDone();
    }

    private static int count(ServerPlayer player, Map<String, AdvancementHolder> mine, String path) {
        AdvancementHolder h = mine.get(path);
        if (h == null) {
            return -1;
        }
        AdvancementProgress p = player.getAdvancements().getOrStartProgress(h);
        int n = 0;
        for (String s : p.getCompletedCriteria()) {
            n++;
        }
        return n;
    }

    private static Set<String> doneSet(ServerPlayer player, Map<String, AdvancementHolder> mine) {
        Set<String> out = new TreeSet<>();
        for (Map.Entry<String, AdvancementHolder> e : mine.entrySet()) {
            if (player.getAdvancements().getOrStartProgress(e.getValue()).isDone()) {
                out.add(e.getKey());
            }
        }
        return out;
    }

    private static int check(String name, boolean pass) {
        say(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
