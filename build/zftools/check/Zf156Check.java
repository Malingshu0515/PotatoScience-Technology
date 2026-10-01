package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

/**
 * ZF156 临时探针（0.13：① 端子连线 ② 手册只发一次 ③ 金属板跨 mod）。
 *
 * <p>三条都验**真游戏里的行为**，不是"文件写没写对"：</p>
 * <ul>
 *   <li>A 端子：真摆两个端子、真连上 FE 与动力两条线，然后**调原版那条卸载路**
 *       （{@code ServerLevel.unload(chunk)} —— {@code ChunkMap.processUnloads} 里
 *       先存盘（:544）再卸载（:546），探针走的就是 :546 那一行）。
 *       修好之后对端必须**仍然**记着这条线；负对照：真把端子挖掉时对端必须清掉。</li>
 *   <li>B 手册：真造几个 {@code ServerPlayer}，走
 *       {@code copyAttachmentsFrom(other, isDeath)} —— 那正是 NeoForge 的
 *       {@code PlayerEvent.Clone} 监听器（AttachmentInternals.java:57-59）干的事。
 *       死后(true)/换维度(false) 两条路都必须把标记带过去；
 *       负对照：0.12 的老机制（玩家持久化数据）在这两条路上都**不**搬。</li>
 *   <li>C 金属板：查**加载后的配方表**（不是 JSON 文本）：数有多少原料认自家板、
 *       铁/铜板原料是否同时认机械动力的 {@code create:iron_sheet / copper_sheet}、
 *       {@code c:plates/*} 标签里是不是两边都收着；负对照：金片不该混进我们的板原料。</li>
 * </ul>
 *
 * <p>⚠ §4.50：{@code runServer} 的 stdout 是 GBK ⇒ 自己写 UTF-8 报告，路径绝对，且在 {@code halt()} 前写。</p>
 */
public final class Zf156Check {

    private static final String TAG = "[A156] ";
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf156_probe_utf8.txt";

    /** 本 mod 7 种金属板（id 后缀 → 物品），顺序固定，报告里好读。 */
    private static final String[] METALS = {"aluminum", "cobalt", "copper", "iron", "nickel", "silver", "steel"};

    private static boolean registered;
    private static boolean done;
    private static int failed;
    private static int checks;
    private static int ticks;

    private static MinecraftServer server;
    private static ServerLevel level;

    private static final StringBuilder REPORT = new StringBuilder();
    private static final List<String> NOTES = new ArrayList<>();

    private Zf156Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void check(String name, boolean ok) {
        checks++;
        REPORT.append(ok ? "  [OK]   " : "  [FAIL] ").append(name).append('\n');
        System.out.println(TAG + (ok ? "  [OK]   " : "  [FAIL] ") + name);
        if (!ok) {
            failed++;
        }
    }

    private static void note(String text) {
        NOTES.add(text);
        System.out.println(TAG + "  [--]   " + text);
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF156 探针报告（0.13：① 端子连线 ② 手册只发一次 ③ 金属板跨 mod）× UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "ALL OK" : failed + " 条 FAIL") + "（共 " + checks + " 项）\n\n");
            w.write(REPORT.toString());
            if (!NOTES.isEmpty()) {
                w.write("\n---- 观 察 记 录 ----\n");
                for (String n : NOTES) {
                    w.write("  · " + n + "\n");
                }
            }
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf156Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        server = event.getServer();
        level = server.overworld();
        say(TAG + "phase1 @ ServerStartedEvent（世界已起，等 20 tick 让机器都跑起来）");
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        ticks++;
        if (done || ticks < 20) {
            return;
        }
        done = true;
        try {
            terminals();
            guide();
            plates();
        } catch (Throwable t) {
            check("phase1 全程不抛异常（" + t + "）", false);
            t.printStackTrace();
        }
        say(TAG + "判词：" + (failed == 0 ? "ALL OK" : failed + " 条 FAIL") + "（共 " + checks + " 项）");
        flushReport();
        server.halt(false);
    }

    // ============================================================ ① 端子
    private static void terminals() {
        say(TAG + "--- ① 端子连线（区块卸载 vs 真挖掉）");
        BlockState state = ModBlocks.TERMINAL.get().defaultBlockState()
                .setValue(TerminalBlock.FACING, Direction.UP);
        BlockPos aPos = new BlockPos(600, 100, 600);
        BlockPos bPos = new BlockPos(600, 100, 610);
        // ⚠ 用 UPDATE_CLIENTS（只发客户端）而不是 UPDATE_ALL：免得邻居更新把端子判成"没支撑"给拆了
        level.setBlock(aPos, state, Block.UPDATE_CLIENTS);
        level.setBlock(bPos, state, Block.UPDATE_CLIENTS);
        BlockEntity rawA = level.getBlockEntity(aPos);
        BlockEntity rawB = level.getBlockEntity(bPos);
        if (!(rawA instanceof TerminalBlockEntity a) || !(rawB instanceof TerminalBlockEntity b)) {
            check("A1 两个端子方块实体建起来了，FE 与动力两条连接都立好了", false);
            return;
        }
        a.addConnection(bPos, TerminalBlockEntity.TRANSFER_RATE);
        b.addConnection(aPos, TerminalBlockEntity.TRANSFER_RATE);
        a.addPowerConnection(bPos);
        b.addPowerConnection(aPos);
        check("A1 两个端子方块实体建起来了，FE 与动力两条连接都立好了",
                a.getConnections().containsKey(bPos) && b.getConnections().containsKey(aPos)
                        && a.getPowerConnections().contains(bPos) && b.getPowerConnections().contains(aPos));

        // ★ 区块卸载：走原版那条路（ServerLevel.unload —— ChunkMap:544 先存盘、:546 再调它）
        LevelChunk chunk = level.getChunkAt(aPos);
        level.unload(chunk);
        // ⚠ 这三条必须在**同一个 tick 回调里立刻**断言：再走一个 tick，对端那圈的
        //   "清理失效连接"会因为探测里区块没真的卸载（只清了方块实体表）而误删 —— 那是探针的假象，
        //   真世界里对端 getBlockEntity 会把卸载的区块连人带数据一起读回来（ServerChunkCache 强加载）。
        check("A2 区块卸载后，对端仍然记着这条 FE 线（用户报的『已连接的线会消失』就是这里断的）",
                b.getConnections().containsKey(aPos));
        check("A3 区块卸载后，对端仍然记着这条动力线", b.getPowerConnections().contains(aPos));
        check("A4 随区块走的那一份，自己的连接表也没被清空（区块读回来还能对上）",
                a.getConnections().containsKey(bPos) && a.getPowerConnections().contains(bPos));

        // 负对照：真挖掉（BlockBehaviour.onRemove → Level.removeBlockEntity → setRemoved）
        BlockPos cPos = new BlockPos(620, 100, 600);
        BlockPos dPos = new BlockPos(620, 100, 610);
        level.setBlock(cPos, state, Block.UPDATE_CLIENTS);
        level.setBlock(dPos, state, Block.UPDATE_CLIENTS);
        if (level.getBlockEntity(cPos) instanceof TerminalBlockEntity c
                && level.getBlockEntity(dPos) instanceof TerminalBlockEntity d) {
            c.addConnection(dPos, TerminalBlockEntity.TRANSFER_RATE);
            d.addConnection(cPos, TerminalBlockEntity.TRANSFER_RATE);
            c.addPowerConnection(dPos);
            d.addPowerConnection(cPos);
            level.removeBlock(cPos, false);
            check("A5 负对照：真把端子挖掉时，对端照样把 FE 与动力两条线都清掉（清理没被改坏）",
                    !d.getConnections().containsKey(cPos) && !d.getPowerConnections().contains(cPos));
        } else {
            check("A5 负对照：真把端子挖掉时，对端照样把两条线都清掉", false);
        }
    }

    // ============================================================ ② 手册
    private static ServerPlayer fakePlayer(String name) {
        return new ServerPlayer(server, level,
                new GameProfile(UUID.randomUUID(), name), ClientInformation.createDefault());
    }

    private static void guide() {
        say(TAG + "--- ② 手册「只发一次」（附件 vs 老的持久化数据）");
        ResourceLocation key = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "guide_given");
        check("B1 附件 potato_s_t:guide_given 真注册在 NeoForge 附件表里",
                NeoForgeRegistries.ATTACHMENT_TYPES.containsKey(key));

        ServerPlayer p1 = fakePlayer("zf156a");
        check("B2 新玩家默认没拿过（附件 false，shouldGive = true）",
                !ModAttachments.isGiven(p1) && GuideBook.shouldGive(p1));
        ModAttachments.markGiven(p1);
        check("B3 标记之后：附件 true，shouldGive 变 false",
                ModAttachments.isGiven(p1) && !GuideBook.shouldGive(p1));

        // ⚠ 这两行就是 NeoForge 的 PlayerEvent.Clone 监听器本体
        //   （AttachmentInternals.onPlayerClone → copyAttachmentsFrom(original, isWasDeath)）
        ServerPlayer p2 = fakePlayer("zf156b");
        p2.copyAttachmentsFrom(p1, true);      // 死后重生：只拷声明了 copyOnDeath 的
        check("B4 死后重生那一路（isDeath=true）把标记带过去了 —— copyOnDeath 真生效",
                ModAttachments.isGiven(p2));
        ServerPlayer p3 = fakePlayer("zf156c");
        p3.copyAttachmentsFrom(p1, false);     // 换维度：全都拷
        check("B5 换维度那一路（isDeath=false）也带过去了", ModAttachments.isGiven(p3));

        // 负对照：0.12 的老机制（ServerPlayer.restoreFrom 只搬 PERSISTED_NBT_TAG 那一把）
        ServerPlayer p4 = fakePlayer("zf156d");
        p4.getPersistentData().putBoolean("potato_s_t_guide_given", true);
        ServerPlayer p5 = fakePlayer("zf156e");
        p5.copyAttachmentsFrom(p4, false);
        check("B6 负对照：0.12 的老标记（玩家持久化数据）**不会**被搬 —— 这就是『每回进游戏都给一本』的病根",
                !p5.getPersistentData().getBoolean("potato_s_t_guide_given"));
        check("B7 老存档口径：老标记还在的玩家 shouldGive 仍是 false（不补发第二本）",
                !GuideBook.shouldGive(p4) && GuideBook.hasLegacyMark(p4));
        note("换维度与死亡两条路都走 PlayerList.respawn → ServerPlayer.restoreFrom"
                + "（ServerGamePacketListenerImpl:1669 CHANGED_DIMENSION / :1676 KILLED）"
                + "，restoreFrom 只搬 PERSISTED_NBT_TAG ⇒ 旧标记必丢；附件由 PlayerEvent.Clone 搬。");
    }

    // ============================================================ ③ 金属板
    private static Map<String, Item> ourPlates() {
        Map<String, Item> m = new LinkedHashMap<>();
        m.put("aluminum", ModItems.ALUMINUM_PLATE.get());
        m.put("cobalt", ModItems.COBALT_PLATE.get());
        m.put("copper", ModItems.COPPER_PLATE.get());
        m.put("iron", ModItems.IRON_PLATE.get());
        m.put("nickel", ModItems.NICKEL_PLATE.get());
        m.put("silver", ModItems.SILVER_PLATE.get());
        m.put("steel", ModItems.STEEL_PLATE.get());
        return m;
    }

    private static List<String> tagItems(String tagId) {
        TagKey<Item> key = TagKey.create(Registries.ITEM, ResourceLocation.parse(tagId));
        List<String> out = new ArrayList<>();
        BuiltInRegistries.ITEM.getTag(key).ifPresent(set -> set.forEach(
                h -> out.add(BuiltInRegistries.ITEM.getKey(h.value()).toString())));
        return out;
    }

    private static Item other(String id) {
        Item item = BuiltInRegistries.ITEM.get(ResourceLocation.parse(id));
        return item == null ? Items.AIR : item;
    }

    private static void plates() {
        say(TAG + "--- ③ 金属板原料改挂 #c:plates/*");
        Map<String, Item> ours = ourPlates();
        Item createIron = other("create:iron_sheet");
        Item createCopper = other("create:copper_sheet");
        Item createGold = other("create:golden_sheet");

        int plateIngs = 0;
        int ourRecipes = 0;
        boolean ironBoth = false;
        boolean copperBoth = false;
        boolean goldLeak = false;
        Set<String> filesWith = new TreeSet<>();
        // ★ C1 的口径：**按「配方 id + c:plates/<金属> 标签」去重**数 =
        //   盘上那 29 处 JSON 引用（一个合成格一份 Ingredient，同一条配方里同一个板
        //   出现在好几个格子里会重复计数 ⇒ 探针第一版按"格子数"数出 70，判据当场修正）。
        Set<String> tagPairs = new TreeSet<>();
        for (RecipeHolder<?> holder : server.getRecipeManager().getRecipes()) {
            if (!holder.id().getNamespace().equals(PotatoST.MODID)) {
                continue;
            }
            ourRecipes++;
            List<Ingredient> ings;
            try {
                ings = holder.value().getIngredients();
            } catch (Throwable t) {
                continue;
            }
            for (Ingredient ing : ings) {
                boolean oursHit = false;
                for (Item it : ours.values()) {
                    if (ing.test(new ItemStack(it))) {
                        oursHit = true;
                        break;
                    }
                }
                if (!oursHit) {
                    continue;
                }
                plateIngs++;
                filesWith.add(holder.id().getPath());
                for (Ingredient.Value v : ing.getValues()) {
                    if (v instanceof Ingredient.TagValue tv) {
                        String id = tv.tag().location().toString();
                        if (id.startsWith("c:plates/")) {
                            tagPairs.add(holder.id().getPath() + " -> " + id);
                        }
                    }
                }
                if (createIron != Items.AIR && ing.test(new ItemStack(createIron))) {
                    ironBoth = true;
                }
                if (createCopper != Items.AIR && ing.test(new ItemStack(createCopper))) {
                    copperBoth = true;
                }
                if (createGold != Items.AIR && ing.test(new ItemStack(createGold))) {
                    goldLeak = true;
                }
            }
        }
        check("C1 加载后的表里「#c:plates/<金属> 原料」= 29 处 / 21 份配方（改前是 29 处写死物品）",
                tagPairs.size() == 29 && filesWith.size() == 21);
        check("C2 铁板原料同时认 potato_s_t:iron_plate 与 create:iron_sheet（= 别的 mod 的板真能顶上）",
                ironBoth);
        check("C3 铜板原料同时认 potato_s_t:copper_plate 与 create:copper_sheet", copperBoth);

        List<String> ironTag = tagItems("c:plates/iron");
        List<String> copperTag = tagItems("c:plates/copper");
        check("C4 c:plates/iron 里同时收着我们那块铁板与机械动力的铁片（跨 mod 合并，不是顶替）",
                ironTag.contains("potato_s_t:iron_plate") && ironTag.contains("create:iron_sheet"));
        check("C5 c:plates/copper 同理", copperTag.contains("potato_s_t:copper_plate")
                && copperTag.contains("create:copper_sheet"));

        List<String> missing = new ArrayList<>();
        for (String m : METALS) {
            if (!tagItems("c:plates/" + m).contains("potato_s_t:" + m + "_plate")) {
                missing.add(m);
            }
        }
        check("C6 7 张 c:plates/<金属> 标签每张都收着自家那块板（不空 ⇒ 配方不会变死配方）",
                missing.isEmpty());

        List<String> goldTag = tagItems("c:plates/gold");
        boolean goldHasOurs = false;
        for (Item it : ours.values()) {
            String id = BuiltInRegistries.ITEM.getKey(it).toString();
            if (goldTag.contains(id)) {
                goldHasOurs = true;
            }
        }
        check("C7 负对照：金片不混进我们的板原料（c:plates/gold 收的是 create:golden_sheet，不含我们任何一块板）",
                !goldLeak && !goldHasOurs && (createGold == Items.AIR || goldTag.contains("create:golden_sheet")));

        check("C8 我们的配方总数 = 91（只把原料换成标签，不加不减）", ourRecipes == 91);
        note("本 mod 命名空间下加载到 " + ourRecipes + " 条配方；其中 " + tagPairs.size()
                + " 处是 #c:plates/<金属> 原料（" + filesWith.size() + " 份配方），"
                + "展开到合成格是 " + plateIngs + " 个（同一条配方里同一个板占多格会重复计）。");
        note("机械动力在场 ⇒ create:iron_sheet=" + createIron + " / create:copper_sheet=" + createCopper
                + " / create:golden_sheet=" + createGold);
    }
}
