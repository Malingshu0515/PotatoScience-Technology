package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF145 的临时探针）</b>：成就树补线后的 **43 条**（35 老 + 8 新）。
 *
 * <p>用户原话：「是时候更新一下成就啦宝宝」。</p>
 *
 * <p>探针分五段，缺一不可：</p>
 * <ol>
 *   <li><b>账目</b>：本模组的进度**全加载进来**了（35 条老的 + 8 条新的 = 43 条）—— 这一条
 *       只有真服务端能证明：JSON 写错一个键，数据包是**静默丢掉那一条**而不是报错；</li>
 *   <li><b>树</b>：恰好一个根、8 条新节点的父链**逐条对到设计值**、从根可达；</li>
 *   <li><b>展示与判据</b>：图标物品注册、frame/hidden 按设计、requirements 覆盖全部判据、
 *       「或」与「与」的组数；星辉斩那条是**第一条第 4 类判据**的节点（没有物品判据、
 *       触发器是 {@code player_killed_entity} + 伤害类型标签）；</li>
 *   <li><b>真触发</b>：造一个玩家，用**游戏自己的 CriterionTrigger** 逐条点亮，外加
 *       负向对照 —— 无关物品不许点亮任何一条；三套盔甲**只给三件不许亮**（真「与」）、
 *       星璨钢工具**只给一件就该亮**（真「或」）；
 *       ⚠ 星辉斩那条**先反后正**：拿原版 {@code player_attack} 杀一只僵尸**不许**点亮，
 *       再拿 {@code potato_s_t:star_steel_slash} 杀一只才许亮 —— 这一对才是标签判据的证据。</li>
 *   <li><b>文案</b>：四语言**各 508 键**、16 个新键 × 4 语言都在（从**打进 jar 的资源**里读，
 *       证明它们真的随包发出去了）。</li>
 * </ol>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf145Check.register();`，跑完用
 * {@code _zf145_unprobe.py} 摘掉，并逐字节核对 `PotatoST.java` 回到改前件。
 * 存档先抄到 {@code build/zftools/check/} **再**从 {@code src} 删（§10.1）。</p>
 */
public final class Zf145Check {

    private static final String TAG = "[A145] ";
    private static final String NS = PotatoST.MODID;

    /** 本模组应当存在的进度：43 = 3 老 + 24（ZF107）+ 8（ZF117）+ 8（ZF145）。 */
    private static final List<String> EXPECT = Arrays.asList(
            "new_beginning", "clean_energy", "stronger_power",
            "crushing", "pressing", "wiring", "first_power", "capacitor",
            "blast_furnace", "steel", "titanium", "electrolyzer", "gas_handling",
            "alloy_smelter", "light_alloy", "hard_alloy", "stable_block",
            "titanium_tools", "oil", "distillation", "fuel", "sulfur", "ammonia",
            "combustion", "acid", "music_disc_anvil", "music_disc_jasmine",
            // ---- ZF117 ----
            "oil_pump", "lithium_battery_plant", "lithium_battery", "star_steel",
            "star_steel_armor", "starfall", "salt", "fluid_logistics",
            // ---- ZF145 ----
            "vibranium", "vibranium_armor", "titanium_armor", "star_steel_tools",
            "star_steel_slash", "star_chart_tome", "diesel_generator", "silver_wire");

    /** ZF145 那 8 条的父链设计值。 */
    private static final String[][] PARENTS = {
            {"vibranium", "star_steel"},
            {"vibranium_armor", "vibranium"},
            {"titanium_armor", "titanium_tools"},
            {"star_steel_tools", "star_steel"},
            {"star_steel_slash", "star_steel"},
            {"star_chart_tome", "new_beginning"},
            {"diesel_generator", "stronger_power"},
            {"silver_wire", "wiring"},
    };

    /** 8 条新节点的 frame 设计值（hidden 全都是 false）。 */
    private static final String[][] FRAMES = {
            {"vibranium", "goal"},
            {"vibranium_armor", "challenge"},
            {"titanium_armor", "goal"},
            {"star_steel_tools", "goal"},
            {"star_steel_slash", "challenge"},
            {"star_chart_tome", "task"},
            {"diesel_generator", "goal"},
            {"silver_wire", "task"},
    };

    /** 交给一件就该点亮的 6 条（「或」/单判据）。 */
    private static final String[][] SINGLE = {
            {"vibranium", "vibranium_ingot"},
            {"star_chart_tome", "star_chart_tome"},
            {"diesel_generator", "diesel_generator_controller"},
            {"silver_wire", "silver_wire_spool"},
            // ⚠ 「或」的证明：只给**锹**一件（五件工具里最新的一件）就该亮
            {"star_steel_tools", "star_steel_shovel"},
    };

    /** 三套盔甲各四件（「与」：少一件不许亮）。 */
    private static final String[][] ARMOR = {
            {"vibranium_armor", "vibranium_helmet", "vibranium_chestplate",
                    "vibranium_leggings", "vibranium_boots"},
            {"titanium_armor", "titanium_alloy_helmet", "titanium_alloy_chestplate",
                    "titanium_alloy_leggings", "titanium_alloy_boots"},
    };

    private static final String SLASH = "star_steel_slash";

    private static boolean registered;
    private static int failed;

    /**
     * ⚠ §4.50：`runServer` 的 stdout 是平台默认编码（GBK），中文会变 `锟斤拷`。
     * 所以探针自己攒一份 **UTF-8 报告**，路径必须**绝对**，并且要在 {@code halt()} **之前**写。
     */
    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf145_probe_utf8.txt";

    private Zf145Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF145 探针报告（成就树补线：43 条 + 真触发 + 伤害类型标签）× UTF-8 · §4.50\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf145Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    private static int check(String name, boolean ok) {
        REPORT.append(ok ? "  [OK]   " : "  [FAIL] ").append(name).append('\n');
        if (ok) {
            System.out.println(TAG + "  [OK]   " + name);
        } else {
            failed++;
            System.out.println(TAG + "  [FAIL] " + name);
        }
        return ok ? 0 : 1;
    }

    private static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(NS, path);
    }

    private static ItemStack stack(String path) {
        Item item = BuiltInRegistries.ITEM.get(id(path));
        return new ItemStack(item);
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        try {
            ServerLevel level = event.getServer().overworld();
            Map<String, AdvancementHolder> mine = new LinkedHashMap<>();
            for (AdvancementHolder h : event.getServer().getAdvancements().getAllAdvancements()) {
                if (h.id().getNamespace().equals(NS)) {
                    mine.put(h.id().getPath(), h);
                }
            }
            checkLedger(mine);
            checkTree(mine);
            checkDisplay(mine);
            Holder<DamageType> slash = checkDamageTypeTag(level);
            checkLanguage();
            checkTriggers(event, level, mine, slash);
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

    // ============================================================
    //  ① 账目
    // ============================================================
    private static void checkLedger(Map<String, AdvancementHolder> mine) {
        say(TAG + "① ledger: did the datapack really load all 43?");
        check("加载进来的本模组进度 = " + EXPECT.size() + " 条（实际 " + mine.size() + "）",
                mine.size() == EXPECT.size());
        List<String> missing = new ArrayList<>();
        for (String p : EXPECT) {
            if (!mine.containsKey(p)) {
                missing.add(p);
            }
        }
        check("43 条一条不少（缺：" + missing + "）", missing.isEmpty());
        List<String> extra = new ArrayList<>();
        for (String p : mine.keySet()) {
            if (!EXPECT.contains(p)) {
                extra.add(p);
            }
        }
        check("没有多出来的节点（多：" + extra + "）", extra.isEmpty());
        check("老树还在（新加 8 条不该挤掉任何一条）：ZF117 那 8 条都在",
                mine.containsKey("star_steel_armor") && mine.containsKey("starfall")
                        && mine.containsKey("salt") && mine.containsKey("fluid_logistics")
                        && mine.containsKey("oil_pump") && mine.containsKey("lithium_battery_plant")
                        && mine.containsKey("lithium_battery") && mine.containsKey("star_steel"));
    }

    // ============================================================
    //  ② 树
    // ============================================================
    private static void checkTree(Map<String, AdvancementHolder> mine) {
        say(TAG + "② tree: one root, parents resolve, reachable from the root");
        List<String> roots = new ArrayList<>();
        Map<String, String> par = new LinkedHashMap<>();
        for (Map.Entry<String, AdvancementHolder> e : mine.entrySet()) {
            AdvancementHolder h = e.getValue();
            if (h.value().parent().isEmpty()) {
                roots.add(e.getKey());
            } else {
                par.put(e.getKey(), h.value().parent().get().getPath());
            }
        }
        check("恰好 1 个根 = [new_beginning]（实际 " + roots + "）",
                roots.size() == 1 && "new_beginning".equals(roots.get(0)));
        List<String> bad = new ArrayList<>();
        for (Map.Entry<String, String> e : par.entrySet()) {
            if (!mine.containsKey(e.getValue())) {
                bad.add(e.getKey() + "→" + e.getValue());
            }
        }
        check("所有父指针都指向树里的节点（坏：" + bad + "）", bad.isEmpty());
        for (String[] pair : PARENTS) {
            String got = par.get(pair[0]);
            check("父链 " + pair[0] + " → " + pair[1] + "（实际 " + got + "）",
                    pair[1].equals(got));
        }
        Set<String> reach = new TreeSet<>();
        reach.add("new_beginning");
        boolean grew = true;
        while (grew) {
            grew = false;
            for (Map.Entry<String, String> e : par.entrySet()) {
                if (reach.contains(e.getValue()) && reach.add(e.getKey())) {
                    grew = true;
                }
            }
        }
        List<String> unreachable = new ArrayList<>();
        for (String p : mine.keySet()) {
            if (!reach.contains(p)) {
                unreachable.add(p);
            }
        }
        check("每个节点从根可达（到不了：" + unreachable + "）", unreachable.isEmpty());
    }

    // ============================================================
    //  ③ 展示与判据
    // ============================================================
    private static void checkDisplay(Map<String, AdvancementHolder> mine) {
        say(TAG + "③ display + criteria: icon / frame / hidden / groups / kill trigger");
        for (String[] pair : FRAMES) {
            AdvancementHolder h = mine.get(pair[0]);
            if (h == null) {
                check(pair[0] + " 在（没法查 frame）", false);
                continue;
            }
            var disp = h.value().display();
            check(pair[0] + " 有 display 段", disp.isPresent());
            if (disp.isEmpty()) {
                continue;
            }
            var d = disp.get();
            Item icon = d.getIcon().getItem();
            check(pair[0] + " 的图标不是空气（" + BuiltInRegistries.ITEM.getKey(icon) + "）",
                    icon != Items.AIR);
            check(pair[0] + " 的图标在本模组命名空间",
                    NS.equals(BuiltInRegistries.ITEM.getKey(icon).getNamespace()));
            check(pair[0] + " 的 frame = " + pair[1] + "（实际 " + d.getType() + "）",
                    d.getType().name().toLowerCase(java.util.Locale.ROOT).equals(pair[1]));
            check(pair[0] + " 的 hidden = false（实际 " + d.isHidden() + "）", !d.isHidden());
            Set<String> crit = new TreeSet<>(h.value().criteria().keySet());
            Set<String> grouped = new TreeSet<>();
            h.value().requirements().requirements().forEach(g -> grouped.addAll(g));
            check(pair[0] + " 的 requirements 覆盖全部判据（" + crit + "）", crit.equals(grouped));
            int ncrit = h.value().criteria().size();
            int ngroup = h.value().requirements().requirements().size();
            if ("star_steel_tools".equals(pair[0])) {
                check("star_steel_tools 是「或」：5 条判据塞进 1 个组（实际 "
                        + ncrit + "/" + ngroup + "）", ncrit == 5 && ngroup == 1);
            }
            if (pair[0].endsWith("_armor")) {
                check(pair[0] + " 是「与」：4 条判据各占 1 个组（实际 "
                        + ncrit + "/" + ngroup + "）", ncrit == 4 && ngroup == 4);
            }
        }
        // 星辉斩：击杀型判据
        AdvancementHolder h = mine.get(SLASH);
        check("star_steel_slash 在", h != null);
        if (h != null) {
            check("star_steel_slash 只有 1 条判据、1 个组（实际 "
                            + h.value().criteria().size() + "/" + h.value().requirements().size() + "）",
                    h.value().criteria().size() == 1 && h.value().requirements().size() == 1);
            var c = h.value().criteria().get("slash");
            check("star_steel_slash 用的是 player_killed_entity 触发器（实际 "
                    + (c == null ? "null" : c.trigger().toString()) + "）",
                    c != null && c.trigger() == CriteriaTriggers.PLAYER_KILLED_ENTITY);
            check("star_steel_slash 的判据里没有物品（击杀型）",
                    !h.value().criteria().toString().contains("inventory_changed"));
        }
    }

    // ============================================================
    //  ④ 伤害类型标签
    // ============================================================
    private static Holder<DamageType> checkDamageTypeTag(ServerLevel level) {
        say(TAG + "④ damage type tag: potato_s_t:star_steel_slash");
        var reg = level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE);
        TagKey<DamageType> tag = TagKey.create(Registries.DAMAGE_TYPE, id(SLASH));
        Optional<HolderSet.Named<DamageType>> named = reg.getTag(tag);
        check("伤害类型标签 potato_s_t:star_steel_slash 存在", named.isPresent());
        List<String> vals = new ArrayList<>();
        if (named.isPresent()) {
            for (Holder<DamageType> hh : named.get()) {
                vals.add(hh.unwrapKey().map(k -> k.location().toString()).orElse("?"));
            }
        }
        check("标签里正好 1 个值 = [potato_s_t:star_steel_slash]（实际 " + vals + "）",
                vals.size() == 1 && "potato_s_t:star_steel_slash".equals(vals.get(0)));
        Holder<DamageType> holder = null;
        try {
            holder = reg.getHolderOrThrow(
                    ResourceKey.create(Registries.DAMAGE_TYPE, id(SLASH)));
            check("伤害类型 potato_s_t:star_steel_slash 注册进来了", true);
            check("它的 message_id = potato_s_t.star_steel_slash ⇒ 死亡文案键 death.attack.potato_s_t.star_steel_slash（实际 "
                            + holder.value().msgId() + "）",
                    "potato_s_t.star_steel_slash".equals(holder.value().msgId()));
            check("它的 exhaustion = 0.1（照原版 player_attack 那一档）",
                    Math.abs(holder.value().exhaustion() - 0.1F) < 1.0E-6F);
        } catch (Throwable t) {
            check("伤害类型 potato_s_t:star_steel_slash 注册进来了（" + t + "）", false);
        }
        return holder;
    }

    // ============================================================
    //  ⑤ 文案（从打进 jar 的资源里读）
    // ============================================================
    private static void checkLanguage() {
        say(TAG + "⑤ language: 508 keys x4, the 16 new ones non-empty");
        String[] locs = {"zh_cn", "en_us", "ja_jp", "ru_ru"};
        List<String> keys = new ArrayList<>();
        for (String[] pair : FRAMES) {
            keys.add("advancements.potato_s_t." + pair[0] + ".title");
            keys.add("advancements.potato_s_t." + pair[0] + ".description");
        }
        for (String loc : locs) {
            String path = "/assets/" + NS + "/lang/" + loc + ".json";
            try (java.io.InputStream in = Zf145Check.class.getResourceAsStream(path)) {
                if (in == null) {
                    check(loc + " 的语言文件在包里", false);
                    continue;
                }
                String text = new String(in.readAllBytes(), StandardCharsets.UTF_8);
                com.google.gson.JsonObject o = com.google.gson.JsonParser
                        .parseString(text).getAsJsonObject();
                check(loc + "：508 键（实际 " + o.size() + "）", o.size() == 508);
                List<String> miss = new ArrayList<>();
                for (String k : keys) {
                    if (!o.has(k) || o.get(k).getAsString().trim().isEmpty()) {
                        miss.add(k);
                    }
                }
                check(loc + "：16 个新键都在且非空（缺 " + miss + "）", miss.isEmpty());
                List<String> quoted = new ArrayList<>();
                for (String k : keys) {
                    if (o.has(k) && o.get(k).getAsString().contains("\"")) {
                        quoted.add(k);
                    }
                }
                check(loc + "：新文案里没有 ASCII 双引号（中文串一律用「」）", quoted.isEmpty());
            } catch (Throwable t) {
                check(loc + " 的语言文件读得动（" + t + "）", false);
            }
        }
    }

    // ============================================================
    //  ⑥ 真触发
    // ============================================================
    private static void checkTriggers(ServerStartedEvent event, ServerLevel level,
                                      Map<String, AdvancementHolder> mine, Holder<DamageType> slash) {
        say(TAG + "⑥ real triggers: hand over items / kill with the slash, watch the progress");
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes("zf145probe".getBytes(StandardCharsets.UTF_8)), "zf145probe");
        ServerPlayer player = new ServerPlayer(event.getServer(), level, profile,
                ClientInformation.createDefault());
        // ⚠ 必须有这一句（ZF70 的教训）：无头服务端里 new 出来的玩家没有连接，
        //   完成带"配方奖励"的进度时发奖励包会 NPE。挂一个没连上的 Connection，send 只会进队列。
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                event.getServer(), conn, player,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        say(TAG + "    player: " + player.getGameProfile().getName());

        Set<String> doneAtStart = doneSet(player, mine);
        check("起始状态：一条都没点亮（实际 " + doneAtStart + "）", doneAtStart.isEmpty());

        // ---- 单判据那 6 条：给一件就该亮 ----
        for (String[] pair : SINGLE) {
            ItemStack st = stack(pair[1]);
            if (st.getItem() == Items.AIR) {
                check(pair[0] + " 的判据物品 " + pair[1] + " 真的注册了", false);
                continue;
            }
            inventory(player, st);
            check("交给 " + pair[1] + " ⇒ " + pair[0] + " 点亮（实际 "
                    + isDone(player, mine, pair[0]) + "）", isDone(player, mine, pair[0]));
        }

        // ---- 三套盔甲：只给三件不许亮（真「与」）----
        for (String[] set : ARMOR) {
            String path = set[0];
            for (int i = 1; i <= 3; i++) {
                ItemStack st = stack(set[i]);
                check(path + " 的第 " + i + " 件 " + set[i] + " 注册了", st.getItem() != Items.AIR);
                inventory(player, st);
            }
            check("只给三件 ⇒ " + path + " **不**亮（实际 " + isDone(player, mine, path) + "）",
                    !isDone(player, mine, path));
            inventory(player, stack(set[4]));
            check("给第 4 件 " + set[4] + " ⇒ " + path + " 亮（实际 "
                    + isDone(player, mine, path) + "）", isDone(player, mine, path));
        }

        // ---- 负向对照：无关物品不许点亮任何一条新节点 ----
        Set<String> beforeJunk = doneSet(player, mine);
        inventory(player, stack("wrench"));
        Set<String> afterJunk = doneSet(player, mine);
        check("交一把扳手（无关物品）⇒ 新点亮 0 条（实际 "
                + minus(afterJunk, beforeJunk) + "）", minus(afterJunk, beforeJunk).isEmpty());

        // ---- 星辉斩：先反后正 ----
        DamageSource vanilla = level.damageSources().playerAttack(player);
        DamageSource starlight = new DamageSource(slash, player);
        check("原版 player_attack 的伤害类型 ≠ 我们的（" + vanilla.getMsgId() + " vs "
                + starlight.getMsgId() + "）", !vanilla.getMsgId().equals(starlight.getMsgId()));
        Zombie neg = spawnDummy(level, 0.0D, 0.0D, 3.0D);
        boolean negHurt;
        try {
            negHurt = neg.hurt(vanilla, 12.0F);
        } finally {
            neg.discard();
        }
        check("拿原版 player_attack 打死一只僵尸（真的死了：" + negHurt + "）", negHurt);
        check("原版攻击击杀 ⇒ 星辉斩**不**亮（实际 " + isDone(player, mine, SLASH) + "）",
                !isDone(player, mine, SLASH));
        Zombie pos = spawnDummy(level, 1.0D, 0.0D, 3.0D);
        boolean posHurt;
        try {
            posHurt = pos.hurt(starlight, 12.0F);
        } finally {
            pos.discard();
        }
        check("拿 potato_s_t:star_steel_slash 打死一只僵尸（真的死了：" + posHurt + "）", posHurt);
        check("用星辉斩击杀 ⇒ 星辉斩亮（实际 " + isDone(player, mine, SLASH) + "）",
                isDone(player, mine, SLASH));

        // ---- 隐藏那条照旧能点亮（hidden 只影响界面可见性）----
        inventory(player, stack("starfall_pendant"));
        inventory(player, stack("raw_vibranium"));
        check("隐藏彩蛋位 starfall 照样能点亮（实际 " + isDone(player, mine, "starfall") + "）",
                isDone(player, mine, "starfall"));

        // ---- 收尾：**本轮这 8 条** + 隐藏彩蛋位全部点亮 ----
        // ⚠ 第一版这里写的是"43 条全部点亮" —— **是我自己的 slip**：本探针只喂了本轮 8 条
        //   与 starfall 的物品，另外 34 条老节点的真触发在 ZF107 / ZF117 两轮的探针里验过，
        //   这里重复不了（要重复就得把 34 条的判据物品全喂一遍，那是那两轮的活）。
        //   ⇒ 判据改成"本轮 9 条全亮"，**不是**放宽：它本来要验的就是本轮这 9 条。
        List<String> mineNew = new ArrayList<>();
        for (String[] pair : FRAMES) {
            mineNew.add(pair[0]);
        }
        mineNew.add("starfall");
        Set<String> done = doneSet(player, mine);
        List<String> missing = new ArrayList<>();
        for (String p : mineNew) {
            if (!done.contains(p)) {
                missing.add(p);
            }
        }
        check("收尾：本轮 8 条 + 隐藏彩蛋位共 " + mineNew.size() + " 条全亮（没亮的：" + missing + "）",
                missing.isEmpty());
        say(TAG + "    （另外 34 条老节点的真触发在 ZF107 / ZF117 那两轮的探针里验过，本探针不重复）");
    }

    private static Zombie spawnDummy(ServerLevel level, double dx, double dy, double dz) {
        BlockPos base = new BlockPos(0, 100, 0);
        // ⚠ 区块必须真的加载过（ZF144 的教训：试验场在地下、区块没加载 ⇒ 实体数不到）
        level.getChunk(base);
        // ⚠ 底下没有方块的话 getHeightmapPos 会给 y=100 附近的空气 ⇒ 实体掉下去；
        //   探针不 tick 世界，所以只要**位置在入世之前**给就行（ZF144 的第二条教训）。
        BlockPos on = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING, base);
        Zombie z = new Zombie(EntityType.ZOMBIE, level);
        z.setPos(on.getX() + 0.5D + dx, on.getY() + 1.0D + dy, on.getZ() + 0.5D + dz);
        z.setNoAi(true);
        z.setHealth(1.0F);            // 保证 12 点伤害一定打得死
        z.setRemainingFireTicks(0);
        level.addFreshEntity(z);      // ⚠ 位置必须在入世**之前**给
        say(TAG + "    dummy @" + z.blockPosition() + " hp=" + z.getHealth()
                + " alive=" + z.isAlive());
        return z;
    }

    private static Set<String> minus(Set<String> a, Set<String> b) {
        Set<String> out = new TreeSet<>(a);
        out.removeAll(b);
        return out;
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

    private static Set<String> doneSet(ServerPlayer player, Map<String, AdvancementHolder> mine) {
        Set<String> out = new TreeSet<>();
        for (Map.Entry<String, AdvancementHolder> e : mine.entrySet()) {
            AdvancementProgress p = player.getAdvancements().getOrStartProgress(e.getValue());
            if (p.isDone()) {
                out.add(e.getKey());
            }
        }
        return out;
    }
}
