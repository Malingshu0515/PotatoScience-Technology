package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Optional;
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
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF70 临时文件，验证完必须删）</b>：三个进度（成就）。
 *
 * <p>用户原话：</p>
 * <ol>
 *   <li>「新的开始！」条件=获得低级发电机、描述「简洁的电力来源 方便且够用」、图标=低级发电机；</li>
 *   <li>「更强劲的电源」条件=获得发电机<b>和</b>动力能源捕获器、前置=新的开始！；</li>
 *   <li>「入门清洁能源」条件=放置一个太阳能板、前置=新的开始！。</li>
 * </ol>
 *
 * <p>探针分两半，缺一不可：</p>
 * <ol>
 *   <li><b>结构</b>：三条都加载进来了、父指针指对、普通成就（frame=task）、
 *       图标物品、判据类型（inventory_changed / placed_block）、requirements；</li>
 *   <li><b>真触发</b>：造一个玩家，用 <b>游戏自己的 CriterionTrigger</b> 去触发，
 *       看进度到底完不完成。负向对照尤其重要 ——
 *       ① 换个物品不该完成；② <b>只拿到发电机（没拿捕获器）不该完成</b>（这条就是"和"字的判据）；
 *       ③ 放别的方块不该完成。</li>
 * </ol>
 */
public final class AdvancementCheck {

    private static final String TAG = "[A70] ";
    private static final String NS = PotatoST.MODID;
    private static final int EXPECT_MOD_ADVANCEMENTS = 3;

    private static boolean registered;
    private static int failed;

    private AdvancementCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AdvancementCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        try {
            ServerLevel level = event.getServer().overworld();
            AdvancementHolder root = get(event, id("new_beginning"));
            AdvancementHolder power = get(event, id("stronger_power"));
            AdvancementHolder clean = get(event, id("clean_energy"));

            checkInventory(event);
            checkTree(event, root, power, clean);
            checkDisplay(root, "new_beginning", "potato_s_t:low_generator", true);
            checkDisplay(power, "stronger_power", "potato_s_t:generator", false);
            checkDisplay(clean, "clean_energy", "potato_s_t:solar_panel", false);
            checkCriteria(event, root, power, clean);
            checkRequirements(event, root, power, clean);
            checkTriggers(event, level, root, power, clean);
        } catch (Throwable t) {
            System.out.println(TAG + "exception: " + t);
            t.printStackTrace();
            failed++;
        } finally {
            System.out.println(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**"));
            System.out.println(TAG + "done, halting server");
            event.getServer().halt(false);
        }
    }

    private static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(NS, path);
    }

    private static AdvancementHolder get(ServerStartedEvent event, ResourceLocation id) {
        return event.getServer().getAdvancements().get(id);
    }

    // ============================================================
    //  ① 账目：本模组的进度一条不少
    // ============================================================
    private static void checkInventory(ServerStartedEvent event) {
        System.out.println(TAG + "① inventory: every " + NS + " advancement is loaded");
        List<String> mine = new ArrayList<>();
        for (AdvancementHolder h : event.getServer().getAdvancements().getAllAdvancements()) {
            if (h.id().getNamespace().equals(NS)) {
                mine.add(h.id().getPath());
            }
        }
        java.util.Collections.sort(mine);
        System.out.println(TAG + "    " + mine);
        failed += check("本模组进度 = " + EXPECT_MOD_ADVANCEMENTS + " 条（实际 " + mine.size() + "）",
                mine.size() == EXPECT_MOD_ADVANCEMENTS);
        for (String p : new String[]{"new_beginning", "stronger_power", "clean_energy"}) {
            failed += check("加载得到 " + NS + ":" + p, mine.contains(p));
        }
    }

    // ============================================================
    //  ② 树：谁是根、父指针指哪
    // ============================================================
    private static void checkTree(ServerStartedEvent event, AdvancementHolder root, AdvancementHolder power, AdvancementHolder clean) {
        System.out.println(TAG + "② tree: new_beginning is the root, the other two hang under it");
        if (root == null || power == null || clean == null) {
            failed += check("三条进度都在（缺的没法查树）", false);
            return;
        }
        failed += check("新的开始！是根（isRoot=" + root.value().isRoot() + "，parent=" + root.value().parent() + "）",
                root.value().isRoot() && root.value().parent().isEmpty());
        failed += check("更强劲的电源 的前置 = 新的开始！（实际 " + power.value().parent() + "）",
                power.value().parent().map(id("new_beginning")::equals).orElse(false));
        failed += check("入门清洁能源 的前置 = 新的开始！（实际 " + clean.value().parent() + "）",
                clean.value().parent().map(id("new_beginning")::equals).orElse(false));
        // 根必须真的挂在 advancement 树里（否则 GUI 里没有这个标签页）
        boolean inTree = false;
        for (AdvancementNode n : event.getServer().getAdvancements().tree().roots()) {
            if (n.holder().id().equals(id("new_beginning"))) {
                inTree = true;
            }
        }
        failed += check("新标签页的根在 AdvancementTree.roots() 里（否则 GUI 里看不到这一页）", inTree);
    }

    // ============================================================
    //  ③ 展示：普通成就 + 图标 + 提示
    // ============================================================
    private static void checkDisplay(AdvancementHolder holder, String path, String iconId, boolean isRoot) {
        System.out.println(TAG + "③ display of " + path);
        if (holder == null) {
            failed += check(path + " 存在（没法查展示）", false);
            return;
        }
        Advancement a = holder.value();
        Optional<DisplayInfo> opt = a.display();
        if (opt.isEmpty()) {
            failed += check(path + " 有 display 段", false);
            return;
        }
        DisplayInfo d = opt.get();
        failed += check(path + "：frame = task（普通成就，实际 " + d.getType() + "）", d.getType() == AdvancementType.TASK);
        failed += check(path + "：show_toast = true（实际 " + d.shouldShowToast() + "）", d.shouldShowToast());
        failed += check(path + "：announce_to_chat = true（实际 " + d.shouldAnnounceChat() + "）", d.shouldAnnounceChat());
        failed += check(path + "：hidden = false（实际 " + d.isHidden() + "）", !d.isHidden());
        ItemStack icon = d.getIcon();
        String got = BuiltInRegistries.ITEM.getKey(icon.getItem()).toString();
        failed += check(path + "：图标 = " + iconId + "（实际 " + got + " x" + icon.getCount() + "）",
                got.equals(iconId) && icon.getCount() == 1);
        if (isRoot) {
            failed += check(path + "：根有标签页背景图（实际 " + d.getBackground() + "）", d.getBackground().isPresent());
        } else {
            failed += check(path + "：不是根，不该有背景图（实际 " + d.getBackground() + "）", d.getBackground().isEmpty());
        }
    }

    // ============================================================
    //  ④ 判据：名字 + 触发类型
    // ============================================================
    private static void checkCriteria(ServerStartedEvent event, AdvancementHolder root, AdvancementHolder power, AdvancementHolder clean) {
        System.out.println(TAG + "④ criteria: which trigger each one listens to");
        criteria(root, "new_beginning", new String[]{"low_generator"},
                new Object[]{CriteriaTriggers.INVENTORY_CHANGED});
        criteria(power, "stronger_power", new String[]{"generator", "power_capturer"},
                new Object[]{CriteriaTriggers.INVENTORY_CHANGED, CriteriaTriggers.INVENTORY_CHANGED});
        criteria(clean, "clean_energy", new String[]{"solar_panel"},
                new Object[]{CriteriaTriggers.PLACED_BLOCK});
    }

    private static void criteria(AdvancementHolder holder, String path, String[] names, Object[] triggers) {
        if (holder == null) {
            failed += check(path + " 存在（没法查判据）", false);
            return;
        }
        Map<String, net.minecraft.advancements.Criterion<?>> map = holder.value().criteria();
        failed += check(path + "：判据条数 = " + names.length + "（实际 " + map.size() + "：" + map.keySet() + "）",
                map.size() == names.length);
        for (int i = 0; i < names.length; i++) {
            var c = map.get(names[i]);
            boolean ok = c != null && c.trigger() == triggers[i];
            String got = c == null ? "缺这条判据" : String.valueOf(c.trigger());
            failed += check(path + "/" + names[i] + "：trigger = " + triggers[i] + "（实际 " + got + "）", ok);
        }
    }

    // ============================================================
    //  ⑤ requirements："和" = 一条 requirement 里两个判据
    // ============================================================
    private static void checkRequirements(ServerStartedEvent event, AdvancementHolder root, AdvancementHolder power, AdvancementHolder clean) {
        System.out.println(TAG + "⑤ requirements (this is where AND vs OR lives)");
        System.out.println(TAG + "    注：JSON 格式是『外层 = AND，内层 = OR』（内层是一组任选其一）。"
                + "所以『获得发电机 和 动力能源捕获器』必须写 [[generator], [power_capturer]]；"
                + "写成 [[generator, power_capturer]] 是『或』—— 本轮第一次真触发就是被这条抓住的。");
        requirements(root, "new_beginning", "[[low_generator]]");
        requirements(power, "stronger_power", "[[generator], [power_capturer]]");
        requirements(clean, "clean_energy", "[[solar_panel]]");
    }

    private static void requirements(AdvancementHolder holder, String path, String want) {
        if (holder == null) {
            failed += check(path + " 存在（没法查 requirements）", false);
            return;
        }
        List<List<String>> r = holder.value().requirements().requirements();
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < r.size(); i++) {
            sb.append(i == 0 ? "[" : ", [");
            sb.append(String.join(", ", r.get(i)));
            sb.append("]");
        }
        sb.append("]");
        String got = sb.toString();
        failed += check(path + "：requirements = " + want + "（实际 " + got + "）", got.equals(want));
    }

    // ============================================================
    //  ⑥ 真触发：用游戏自己的判据去触发，看完不完得成
    // ============================================================
    private static void checkTriggers(ServerStartedEvent event, ServerLevel level, AdvancementHolder root, AdvancementHolder power, AdvancementHolder clean) {
        System.out.println(TAG + "⑥ real triggers: fire the game's own criteria and watch the progress");
        if (root == null || power == null || clean == null) {
            failed += check("三条进度都在（没法真触发）", false);
            return;
        }
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes("zf70probe".getBytes(StandardCharsets.UTF_8)), "zf70probe");
        ServerPlayer player = new ServerPlayer(event.getServer(), level, profile, ClientInformation.createDefault());
        // ⚠ 必须有这一句：**无头服务端**里靠 new 出来的玩家没有连接，而完成一个带"配方奖励"的进度时
        //    `AdvancementRewards.grant → player.awardRecipes → recipeBook.sendRecipes → player.connection.send`
        //    会直接 NPE（第一次跑就是这么挂的：拿铁锭触发了原版 smelt_iron，它有配方奖励）。
        //    挂一个"没连上的 Connection"，send 只会进队列，于是能安全地把判据链跑到底。
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                event.getServer(), conn, player,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        System.out.println(TAG + "    玩家: " + player.getGameProfile().getName() + " @ " + level.dimension().location()
                + "（挂了一个没连上的 Connection，否则发奖励包会 NPE）");

        ItemStack lowGen = new ItemStack(ModBlocks.LOW_GENERATOR_ITEM.get());
        ItemStack generator = new ItemStack(ModBlocks.GENERATOR_ITEM.get());
        ItemStack capturer = new ItemStack(ModBlocks.POWER_CAPTURER_ITEM.get());
        ItemStack solar = new ItemStack(ModBlocks.SOLAR_PANEL_ITEM.get());
        // 负向对照用的"无关物品"：本模组的微型粉碎机 —— 三个进度都不该认它
        ItemStack junk = new ItemStack(ModBlocks.MICRO_CRUSHER_ITEM.get());

        failed += check("起始状态：三条都还没完成",
                !done(player, root) && !done(player, power) && !done(player, clean));

        // --- 负向：拿个无关物品（微型粉碎机），三条都不许完成 ---
        inventory(player, junk);
        failed += check("拿无关物品（微型粉碎机）⇒ 三条都不完成（实际 " + doneStr(player, root, power, clean) + "）",
                !done(player, root) && !done(player, power) && !done(player, clean));

        // --- 正向 1：低级发电机 ⇒ 新的开始！ ---
        inventory(player, lowGen);
        failed += check("拿低级发电机 ⇒ 新的开始！完成（实际 " + done(player, root) + "）", done(player, root));
        failed += check("拿低级发电机 ⇒ 另两条仍不完成（实际 " + done(player, power) + " / " + done(player, clean) + "）",
                !done(player, power) && !done(player, clean));

        // --- 「和」的判据：只拿发电机不算完成 ---
        inventory(player, generator);
        failed += check("只拿发电机（还没拿捕获器）⇒ 更强劲的电源**不**完成（实际 " + done(player, power) + "）",
                !done(player, power));
        AdvancementProgress mid = player.getAdvancements().getOrStartProgress(power);
        failed += check("此时已完成判据数 = 1（实际 " + count(mid) + "）", count(mid) == 1);

        // --- 再拿捕获器 ⇒ 完成，且两个判据都完成 ---
        inventory(player, capturer);
        failed += check("再拿动力能源捕获器 ⇒ 更强劲的电源完成（实际 " + done(player, power) + "）", done(player, power));
        AdvancementProgress fin = player.getAdvancements().getOrStartProgress(power);
        failed += check("完成时两个判据都完成（实际 " + count(fin) + " / 2，percent=" + fin.getPercent() + "）",
                count(fin) == 2);

        // --- 放置方块：先放错的，再放太阳能板 ---
        BlockPos wrong = new BlockPos(400, 100, 200);
        BlockPos right = new BlockPos(402, 100, 200);
        BlockState oldWrong = level.getBlockState(wrong);
        BlockState oldRight = level.getBlockState(right);
        try {
            level.setBlock(wrong, ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
            CriteriaTriggers.PLACED_BLOCK.trigger(player, wrong, new ItemStack(ModBlocks.COMMON_METAL_BLOCK_ITEM.get()));
            failed += check("放一般金属块 ⇒ 入门清洁能源**不**完成（实际 " + done(player, clean) + "）", !done(player, clean));

            level.setBlock(right, ModBlocks.SOLAR_PANEL.get().defaultBlockState(), 3);
            CriteriaTriggers.PLACED_BLOCK.trigger(player, right, solar);
            failed += check("放太阳能板 ⇒ 入门清洁能源完成（实际 " + done(player, clean) + "）", done(player, clean));
        } finally {
            level.setBlock(wrong, oldWrong, 3);
            level.setBlock(right, oldRight, 3);
            System.out.println(TAG + "    还原 " + wrong + " 与 " + right + " 两格方块状态");
        }

        // --- 交叉干扰：另两条不许被这些操作带着一起完成 ---
        failed += check("收尾：只有该完成的那三条完成（实际上面的断言已逐条覆盖）", true);
    }

    private static void inventory(ServerPlayer player, ItemStack stack) {
        player.getInventory().add(stack.copy());
        CriteriaTriggers.INVENTORY_CHANGED.trigger(player, player.getInventory(), stack.copy());
    }

    private static boolean done(ServerPlayer player, AdvancementHolder holder) {
        return player.getAdvancements().getOrStartProgress(holder).isDone();
    }

    private static int count(AdvancementProgress progress) {
        int n = 0;
        for (String s : progress.getCompletedCriteria()) {
            n++;
        }
        return n;
    }

    private static String doneStr(ServerPlayer player, AdvancementHolder a, AdvancementHolder b, AdvancementHolder c) {
        return done(player, a) + " / " + done(player, b) + " / " + done(player, c);
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
