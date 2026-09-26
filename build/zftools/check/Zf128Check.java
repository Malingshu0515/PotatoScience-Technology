package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
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
import net.minecraft.advancements.AdvancementType;
import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.advancements.DisplayInfo;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠️ <b>诊断工具（ZF128 的临时探针）</b>：成就页签的图标 = <b>毒马铃薯</b>。
 *
 * <p>用户原话：「成就栏换成毒马铃薯 但是成就还是粉碎机可以嘛」。</p>
 *
 * <p>先说清楚为什么"页签换、根节点不换"做不到（本探针把这件事也验了）——
 * 查的是本工程编译用的那份源码（`build/neoForm/…/sources.jar`）：</p>
 * <ul>
 *   <li>`AdvancementTab.java:51` {@code this.icon = display.getIcon();}</li>
 *   <li>`AdvancementTab.java:53` {@code this.root = new AdvancementWidget(this, minecraft, rootNode, display);}
 *       —— 根节点 widget 拿的是<b>同一个 display</b></li>
 *   <li>`AdvancementWidget.java:162` {@code guiGraphics.renderFakeItem(this.display.getIcon(), …)}</li>
 * </ul>
 * <p>⇒ 页签图标与树里那个小方块是同一个字段，改了**一起变**；但**判据**（成就内容）是另一回事。</p>
 *
 * <p>要证的三件事：</p>
 * <ol>
 *   <li><b>图标真的换了</b>：根成就的 {@code display.getIcon()} == {@code minecraft:poisonous_potato}，
 *       而且是**原版**命名空间（我们自己的物品一律带 {@code potato_s_t:} —— 这一处是用户点名的例外）；</li>
 *   <li><b>别的都没动</b>：标题/描述仍是 translate 键、背景图、frame、hidden、toast；
 *       树里仍恰好 1 个根、本模组成就仍是 35 条、没有第二条成就在用毒马铃薯；</li>
 *   <li><b>「成就还是粉碎机」</b>：真交一个**微型粉碎机**给玩家 ⇒ 这条成就**点亮**；
 *       先交一个**毒马铃薯** ⇒ <b>不亮</b>（负向对照：图标换了，判据没换）。</li>
 * </ol>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf128Check.register();`，跑完用
 * {@code _zf128_unprobe.py} 摘掉（**先抄进 `build/zftools/check/` 再删**；
 * 挂载/卸载这次是**严格互逆**的 —— ZF127 那次吃过"吃掉一个空行"的亏，§4.108）。</p>
 */
public final class Zf128Check {

    private static final String TAG = "[A128] ";
    private static final String NS = "potato_s_t";
    private static final int EXPECT_NODES = 35;

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf128_probe_utf8.txt";

    private static boolean registered;
    private static int passed;
    private static int failed;

    private Zf128Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void check(String name, boolean ok) {
        if (ok) {
            passed++;
        } else {
            failed++;
        }
        say(TAG + (ok ? "[OK]   " : "[FAIL] ") + name);
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF128 探针报告（成就页签图标 = 毒马铃薯；判据仍是微型粉碎机）· UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "全绿" : failed + " 条 FAIL") + "（通过 " + passed + "）\n\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf128Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            run(event, level);
        } catch (Throwable t) {
            failed++;
            say(TAG + "[FAIL] 探针自己抛异常：" + t);
            t.printStackTrace(System.out);
        }
        say(TAG + "done, halting server");
        flushReport();
        event.getServer().halt(false);
    }

    private static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(NS, path);
    }

    private static void run(ServerStartedEvent event, ServerLevel level) {
        Map<String, AdvancementHolder> mine = new java.util.LinkedHashMap<>();
        for (AdvancementHolder h : event.getServer().getAdvancements().getAllAdvancements()) {
            if (h.id().getNamespace().equals(NS)) {
                mine.put(h.id().getPath(), h);
            }
        }

        say(TAG + "① 根成就的 display（页签与根节点画的就是它）");
        AdvancementHolder root = mine.get("new_beginning");
        check("根成就 new_beginning 加载得到", root != null);
        if (root == null) {
            return;
        }
        Advancement adv = root.value();
        Optional<DisplayInfo> opt = adv.display();
        check("根成就有 display 段", opt.isPresent());
        if (opt.isEmpty()) {
            return;
        }
        DisplayInfo d = opt.get();
        String icon = BuiltInRegistries.ITEM.getKey(d.getIcon().getItem()).toString();
        check("**图标 = minecraft:poisonous_potato**（实际 " + icon + "）",
                icon.equals("minecraft:poisonous_potato"));
        check("图标**不再是** potato_s_t:micro_crusher（真的换了）",
                !icon.equals(NS + ":micro_crusher"));
        check("图标不是空气、数量 1（" + d.getIcon().getCount() + "）",
                d.getIcon().getItem() != Items.AIR && d.getIcon().getCount() == 1);
        check("图标是**原版**命名空间（我们自己的物品一律 potato_s_t: —— 这一处是用户点名的例外）",
                icon.startsWith("minecraft:"));
        String titleKey = keyOf(d.getTitle());
        String descKey = keyOf(d.getDescription());
        check("标题仍是 translate 键 advancements.potato_s_t.new_beginning.title（页签名字的来源没动）",
                titleKey.equals("advancements.potato_s_t.new_beginning.title"));
        check("描述仍是 translate 键 advancements.potato_s_t.new_beginning.description",
                descKey.equals("advancements.potato_s_t.new_beginning.description"));
        check("背景图没动（" + d.getBackground().map(ResourceLocation::toString).orElse("无") + "）",
                d.getBackground().map(r -> r.toString()
                        .equals(NS + ":textures/block/common_metal_block.png")).orElse(false));
        check("frame = TASK（实际 " + d.getType() + "）", d.getType() == AdvancementType.TASK);
        check("hidden = false、toast 与 announce 都开",
                !d.isHidden() && d.shouldShowToast() && d.shouldAnnounceChat());
        check("判据仍只有 1 条、名字叫 got（实际 " + adv.criteria().keySet() + "）",
                adv.criteria().keySet().equals(Set.of("got")));
        check("触发器仍是 minecraft:inventory_changed",
                adv.criteria().get("got").trigger() == CriteriaTriggers.INVENTORY_CHANGED);

        say(TAG + "② 树与全模组成就（没被顺手改坏）");
        List<String> roots = new ArrayList<>();
        for (String p : mine.keySet()) {
            if (mine.get(p).value().parent().isEmpty()) {
                roots.add(p);
            }
        }
        java.util.Collections.sort(roots);
        check("本模组恰好 1 个根、还是 new_beginning（实际 " + roots + "）",
                roots.equals(List.of("new_beginning")));
        boolean inTree = false;
        for (AdvancementNode n : event.getServer().getAdvancements().tree().roots()) {
            if (n.holder().id().equals(id("new_beginning"))) {
                inTree = true;
            }
        }
        check("根挂在 AdvancementTree.roots() 里（否则 GUI 里没有这一页）", inTree);
        check("本模组成就仍是 " + EXPECT_NODES + " 条（实际 " + mine.size() + "）",
                mine.size() == EXPECT_NODES);
        List<String> potatoUsers = new ArrayList<>();
        List<String> notOurs = new ArrayList<>();
        for (Map.Entry<String, AdvancementHolder> e : mine.entrySet()) {
            Optional<DisplayInfo> o = e.getValue().value().display();
            if (o.isEmpty()) {
                continue;
            }
            String ic = BuiltInRegistries.ITEM.getKey(o.get().getIcon().getItem()).toString();
            if (ic.equals("minecraft:poisonous_potato")) {
                potatoUsers.add(e.getKey());
            }
            if (!ic.startsWith(NS + ":") && !e.getKey().equals("new_beginning")) {
                notOurs.add(e.getKey() + "=" + ic);
            }
        }
        check("只有根那条用毒马铃薯（实际 " + new TreeSet<>(potatoUsers) + "）",
                potatoUsers.equals(List.of("new_beginning")));
        check("别的成就的图标全是我们自己的物品（没有第二处被改成原版物品：" + notOurs + "）",
                notOurs.isEmpty());

        say(TAG + "③ 真交物品：「成就还是粉碎机」");
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes("zf128probe".getBytes(StandardCharsets.UTF_8)), "zf128probe");
        ServerPlayer player = new ServerPlayer(event.getServer(), level, profile,
                net.minecraft.server.level.ClientInformation.createDefault());
        // ⚠ 必须有这一句（ZF70 的教训）：无头服务端里 new 出来的玩家没有连接，
        //   完成带"配方奖励"的进度时发奖励包会 NPE。
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                event.getServer(), conn, player,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));

        check("起始状态：根成就没点亮", !isDone(player, mine, "new_beginning"));
        inventory(player, new ItemStack(Items.POISONOUS_POTATO));
        check("**交一个毒马铃薯 ⇒ 根成就仍然不亮**（图标 ≠ 判据，负向对照）",
                !isDone(player, mine, "new_beginning"));
        inventory(player, new ItemStack(ModBlocks.MICRO_CRUSHER_ITEM.get()));
        check("**交一个微型粉碎机 ⇒ 根成就点亮**（「成就还是粉碎机」）",
                isDone(player, mine, "new_beginning"));
    }

    /**
     * 取组件的 translate 键。
     * ⚠ 第一版去 `Component.toString()` 里正则找 `translate=` ⇒ 两条假 FAIL（那个格式不是那样）。
     *   正路是问组件自己的 contents（`TranslatableContents.getKey()`）。
     */
    private static String keyOf(Component c) {
        return c.getContents() instanceof net.minecraft.network.chat.contents.TranslatableContents tc
                ? tc.getKey() : "<字面量>" + c.getString();
    }

    /** 照 ZF107 探针那套（唯一在无头服务端上真能点亮 inventory_changed 的写法） */
    private static void inventory(ServerPlayer player, ItemStack stack) {
        if (stack.isEmpty()) {
            return;
        }
        player.getInventory().add(stack.copy());
        CriteriaTriggers.INVENTORY_CHANGED.trigger(player, player.getInventory(), stack.copy());
    }

    private static boolean isDone(ServerPlayer player, Map<String, AdvancementHolder> mine,
                                  String path) {
        AdvancementHolder h = mine.get(path);
        return h != null && player.getAdvancements().getOrStartProgress(h).isDone();
    }
}
