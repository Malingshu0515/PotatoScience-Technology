package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.SmithingTemplateItem;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SmithingRecipe;
import net.minecraft.world.item.crafting.SmithingRecipeInput;
import net.minecraft.world.item.crafting.SmithingTransformRecipe;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * ZF155 临时探针（0.12：通用升级模板 —— 真·通用 + 有冲突就不许用）。
 *
 * <p>验的是**真游戏里的那张表**，不是文件写没写对：</p>
 * <ul>
 *   <li>A 引擎：装完之后原版 9 条下界合金升级在表里都认通用模板；本 mod 5 条本来就用它；
 *       纹饰一条都没碰；**表里的锻造配方总数不变**（原地换 id，不是加副本）。</li>
 *   <li>B 真查表 + 真 {@code assemble}：钻石装 + 下界合金锭 + 通用模板 → 下界合金装；
 *       钛合金剑 + 振金锭 + 通用模板 → **振金剑**；回归：下界合金模板照旧能用；
 *       负对照：下界合金模板**不再**能升振金（本轮真换了模板）、纹饰不吃通用模板。</li>
 *   <li>C 获取方式：八块铝锭围一圈 + 中间一张下界合金升级模板 → 通用升级模板 ×1（走真合成表）。</li>
 *   <li>D 冲突规则：喂**合成配方**给生产代码 {@code UniversalUpgradeTemplate.plan()}，
 *       同底同料不同结果的两条必须都进 {@code conflicts}、都不许加宽；
 *       只有底物重合而材料不同的第三条必须**能**加宽（判据是两个槽都重合）。</li>
 *   <li>E 幂等：再 {@code install()} 一次，表里数量不变、计划为空。</li>
 *   <li>F 真跑一次 {@code /reload}（{@code MinecraftServer.reloadResources}）：管理器实例换新、
 *       加宽必须自己回来 —— 这条验的是 {@code OnDatapackSyncEvent} 那个挂点真接上了
 *       （{@code MinecraftServer.java:1540} → {@code PlayerList.java:916} 先发事件、918 才发配方包）。</li>
 * </ul>
 *
 * <p>⚠ §4.50：{@code runServer} 的 stdout 是 GBK ⇒ 自己写 UTF-8 报告，路径绝对，且在 {@code halt()} 前写。</p>
 */
public final class Zf155Check {

    private static final String TAG = "[A155] ";
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf155_probe_utf8.txt";

    /** 原版 9 条下界合金升级（client-extra.jar 里现抠的 id）。 */
    private static final String[] NETHERITE = {"netherite_helmet_smithing", "netherite_chestplate_smithing",
            "netherite_leggings_smithing", "netherite_boots_smithing", "netherite_sword_smithing",
            "netherite_pickaxe_smithing", "netherite_axe_smithing", "netherite_shovel_smithing",
            "netherite_hoe_smithing"};

    /** 本 mod 5 条自带升级（模板槽写死就是通用模板）。 */
    private static final String[] OWN_UPGRADES = {"vibranium_helmet_smithing", "vibranium_chestplate_smithing",
            "vibranium_leggings_smithing", "vibranium_boots_smithing", "vibranium_sword_smithing"};

    private static boolean registered;
    private static int failed;
    private static int checks;
    private static final StringBuilder REPORT = new StringBuilder();
    private static final List<String> NOTES = new ArrayList<>();

    private static MinecraftServer server;
    private static ServerLevel level;
    private static int ticks;
    private static boolean phase1Done;
    private static boolean done;

    private static RecipeManager managerBefore;
    private static int smithingBefore;
    private static long reloadTriggeredAt = -1L;
    private static boolean reloadThrew;

    private Zf155Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF155 探针报告（0.12 通用升级模板：真·通用 + 冲突即禁用）× UTF-8 · §4.50\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf155Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    private static void check(String name, boolean ok) {
        checks++;
        REPORT.append(ok ? "  [OK]   " : "  [FAIL] ").append(name).append('\n');
        if (ok) {
            System.out.println(TAG + "  [OK]   " + name);
        } else {
            failed++;
            System.out.println(TAG + "  [FAIL] " + name);
        }
    }

    private static void note(String text) {
        NOTES.add(text);
        System.out.println(TAG + "  [--]   " + text);
    }

    private static ItemStack stack(Item item) {
        return new ItemStack(item);
    }

    private static Ingredient ing(Item item) {
        return Ingredient.of(item);
    }

    // =========================================================== 第一阶段
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        server = event.getServer();
        level = server.overworld();
        say(TAG + "phase1 @ ServerStartedEvent，表里锻造配方 " + smithingCount() + " 条");
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        ticks++;
        try {
            if (!phase1Done && ticks >= 1) {
                phase1Done = true;
                phase1();
                triggerReload();
                return;
            }
            if (phase1Done && !done && reloadTriggeredAt > 0 && ticks - reloadTriggeredAt >= 2) {
                if (phase3()) {
                    done = true;
                    flushReport();
                    say(TAG + "done, halting");
                    server.halt(false);
                }
            }
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            for (StackTraceElement e : t.getStackTrace()) {
                say(TAG + "    at " + e);
            }
            done = true;
            flushReport();
            server.halt(false);
        }
    }

    // ---------------------------------------------------------- A/B/C/D/E
    private static void phase1() {
        ItemStack universal = stack(ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get());
        RecipeManager manager = server.getRecipeManager();
        List<RecipeHolder<?>> before = List.copyOf(manager.getRecipes());
        smithingBefore = smithingCount();

        // ---------- A 引擎 ----------
        UniversalUpgradeTemplate.Plan own =
                UniversalUpgradeTemplate.plan(before, server.registryAccess());
        boolean preInstalled = own.widened().isEmpty() && own.already().size() >= 14;
        if (preInstalled) {
            note("进 phase1 时表里已经是加宽版 ⇒ mod 自己的 ServerStartedEvent 挂点**先于**探针跑过了");
        } else {
            note("进 phase1 时表还是原样 ⇒ 未观测到 ServerStartedEvent 先跑（挂点本身另有静态校验）");
        }
        UniversalUpgradeTemplate.Plan plan = UniversalUpgradeTemplate.install(server);

        check("A1 物品已注册且是原版模板类：" + BuiltInRegistries.ITEM.getKey(
                ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get())
                + " instanceof SmithingTemplateItem="
                + (ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get() instanceof SmithingTemplateItem),
                "universal_upgrade_template".equals(BuiltInRegistries.ITEM.getKey(
                        ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get()).getPath())
                        && ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get() instanceof SmithingTemplateItem);

        List<String> widened = new ArrayList<>(own.widened().isEmpty() ? plan.widened() : own.widened());
        int netheriteHits = 0;
        for (String id : NETHERITE) {
            if (widened.contains("minecraft:" + id)) {
                netheriteHits++;
            }
        }
        check("A2 原版 9 条下界合金升级全部加宽（命中 " + netheriteHits + "）", netheriteHits == 9);

        int ownHits = 0;
        List<String> already = own.already().isEmpty() ? plan.already() : own.already();
        for (String id : OWN_UPGRADES) {
            if (already.contains("potato_s_t:" + id)) {
                ownHits++;
            }
        }
        check("A3 本 mod 5 条升级本来就是通用模板（命中 " + ownHits + "）", ownHits == 5);

        int trimSkipped = 0;
        for (String s : plan.skipped()) {
            if (s.endsWith("|trim-pattern-bound")) {
                trimSkipped++;
            }
        }
        boolean trimWidened = widened.stream().anyMatch(s -> s.contains("armor_trim"));
        check("A4 纹饰一条都没加宽（跳过 " + trimSkipped + " 条，widened 里 0 条纹饰）",
                trimSkipped >= 18 && !trimWidened);

        check("A5 真实环境下冲突数 = " + plan.conflicts().size() + "（应为 0）", plan.conflicts().isEmpty());
        if (!plan.conflicts().isEmpty()) {
            note("冲突清单：" + plan.conflicts());
        }

        // 表里那 9 条现在必须认通用模板
        int liveHits = 0;
        for (String id : NETHERITE) {
            RecipeHolder<?> holder = manager.byKey(
                    ResourceLocation.withDefaultNamespace(id)).orElse(null);
            if (holder != null && holder.value() instanceof SmithingRecipe sr
                    && sr.isTemplateIngredient(universal)) {
                liveHits++;
            }
        }
        check("A6 装完后表里 9 条都认通用模板（命中 " + liveHits + "）", liveHits == 9);

        check("A7 锻造配方总数原地不变（装前 " + smithingBefore + " / 装后 " + smithingCount() + "）",
                smithingBefore == smithingCount());

        // A8：加宽清单里**每一条**都得在表里真认通用模板（不只那 9 条原版）
        int liveAll = 0;
        for (String id : widened) {
            RecipeHolder<?> holder = manager.byKey(ResourceLocation.parse(id)).orElse(null);
            if (holder != null && holder.value() instanceof SmithingRecipe sr
                    && sr.isTemplateIngredient(universal)) {
                liveAll++;
            }
        }
        check("A8 加宽清单每一条在表里都认通用模板（" + liveAll + "/" + widened.size() + "）",
                widened.size() >= 9 && liveAll == widened.size());
        note("加宽清单（" + widened.size() + " 条）：" + widened);
        List<String> others = widened.stream().filter(s -> !s.startsWith("minecraft:")).toList();
        note("其中**别的 mod 的升级** " + others.size() + " 条：" + others);

        note("本轮非纹饰跳过项：" + plan.skipped().stream()
                .filter(s -> !s.endsWith("|trim-pattern-bound")).toList());

        // ---------- B 真查表 + 真 assemble ----------
        Object[] r;
        r = lookup(stack(Items.DIAMOND_HELMET), stack(Items.NETHERITE_INGOT), universal);
        check("B1 钻石头盔 + 下界合金锭 + 通用模板 → 下界合金头盔",
                r[0] != null && r[1] != null && r[1] == Items.NETHERITE_HELMET);
        r = lookup(stack(Items.DIAMOND_SWORD), stack(Items.NETHERITE_INGOT), universal);
        check("B2 钻石剑 + 下界合金锭 + 通用模板 → 下界合金剑",
                r[0] != null && r[1] != null && r[1] == Items.NETHERITE_SWORD);
        r = lookup(stack(Items.DIAMOND_HELMET), stack(Items.NETHERITE_INGOT),
                stack(Items.NETHERITE_UPGRADE_SMITHING_TEMPLATE));
        check("B3 回归：下界合金模板照旧能升下界合金（原版行为没被破坏）",
                r[0] != null && r[1] != null && r[1] == Items.NETHERITE_HELMET);

        r = lookup(stack(ModArmorItems.TITANIUM_ALLOY_HELMET.get()), stack(ModItems.VIBRANIUM_INGOT.get()),
                universal);
        check("B4 钛合金头盔 + 振金锭 + 通用模板 → 振金头盔",
                r[0] != null && r[1] != null && r[1] == ModArmorItems.VIBRANIUM_HELMET.get());
        r = lookup(stack(ModItems.TITANIUM_ALLOY_SWORD.get()), stack(ModItems.VIBRANIUM_INGOT.get()), universal);
        boolean swordOk = r[0] != null && r[1] != null
                && r[1] == ModItems.VIBRANIUM_SWORD.get()
                && "vibranium_sword_smithing".equals(r[2]);
        check("B5 钛合金剑 + 振金锭 + 通用模板 → 振金剑（新配方，id=" + r[2] + "）", swordOk);

        r = lookup(stack(ModArmorItems.TITANIUM_ALLOY_HELMET.get()), stack(ModItems.VIBRANIUM_INGOT.get()),
                stack(Items.NETHERITE_UPGRADE_SMITHING_TEMPLATE));
        check("B6 负对照：下界合金模板**不再**能升振金（模板真换了）", r[0] == null);
        r = lookup(stack(Items.DIAMOND_CHESTPLATE), stack(Items.GOLD_INGOT), universal);
        check("B7 负对照：钻石胸甲 + 金锭 + 通用模板 → 无配方（纹饰没被通用化）", r[0] == null);
        r = lookup(stack(Items.DIAMOND_CHESTPLATE), stack(Items.GOLD_INGOT),
                stack(Items.COAST_ARMOR_TRIM_SMITHING_TEMPLATE));
        check("B8 回归：海岸纹饰模板照旧能上纹饰", r[0] != null);
        r = lookup(stack(Items.DIAMOND_HELMET), stack(Items.COAL), universal);
        check("B9 负对照：钻石头盔 + 煤炭 + 通用模板 → 无配方（不乱配）", r[0] == null);

        // ---------- C 获取方式 ----------
        check("C1 合成：八铝锭围一圈 + 中间下界合金模板 → 通用升级模板 ×1", craftRing(true));
        check("C2 负对照：中间换成铝锭 → 不给通用模板", !craftRing(false));

        // ---------- D 冲突规则（喂合成配方给生产代码） ----------
        Ingredient template = ing(Items.NETHERITE_UPGRADE_SMITHING_TEMPLATE);
        Ingredient baseStick = ing(Items.STICK);
        RecipeHolder<SmithingTransformRecipe> x1 = new RecipeHolder<>(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "zf155/x1"),
                new SmithingTransformRecipe(template, baseStick, ing(Items.COAL), stack(Items.DIAMOND)));
        RecipeHolder<SmithingTransformRecipe> x2 = new RecipeHolder<>(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "zf155/x2"),
                new SmithingTransformRecipe(template, baseStick, ing(Items.COAL), stack(Items.EMERALD)));
        RecipeHolder<SmithingTransformRecipe> x3 = new RecipeHolder<>(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "zf155/x3"),
                new SmithingTransformRecipe(template, baseStick, ing(Items.IRON_INGOT), stack(Items.LAPIS_LAZULI)));
        UniversalUpgradeTemplate.Plan conflictPlan = UniversalUpgradeTemplate.plan(
                List.of(x1, x2, x3), server.registryAccess());
        boolean bothConflicted = conflictPlan.conflicts().size() == 1
                && conflictPlan.conflicts().get(0).contains("zf155/x1")
                && conflictPlan.conflicts().get(0).contains("zf155/x2");
        check("D1 同底同料不同结果的两条 → 判为冲突（" + conflictPlan.conflicts() + "）", bothConflicted);
        boolean neitherWidened = !conflictPlan.widened().contains("potato_s_t:zf155/x1")
                && !conflictPlan.widened().contains("potato_s_t:zf155/x2");
        check("D2 冲突的两条**都不许**加宽（widened=" + conflictPlan.widened() + "）", neitherWidened);
        check("D3 只有底物重合、材料不同的第三条**能**加宽（判据是两个槽都重合）",
                conflictPlan.widened().contains("potato_s_t:zf155/x3")
                        && conflictPlan.replacements().size() == 1);

        // ---------- E 幂等 ----------
        UniversalUpgradeTemplate.install(server);
        UniversalUpgradeTemplate.Plan again = UniversalUpgradeTemplate.plan(
                List.copyOf(manager.getRecipes()), server.registryAccess());
        check("E1 再装一次：计划为空（widened=" + again.widened().size() + "）且表里数量不变",
                again.widened().isEmpty() && smithingCount() == smithingBefore);

        // ---------- 物品 tooltip 不炸 ----------
        List<net.minecraft.network.chat.Component> lines =
                universal.getTooltipLines(Item.TooltipContext.of(level), null, TooltipFlag.Default.NORMAL);
        String joined = lines.toString();
        check("D4 通用模板 tooltip 能生成且含规则键（" + lines.size() + " 行）",
                lines.size() >= 6 && joined.contains("universal_upgrade_template.rule"));
    }

    /** 真查表 + 真 assemble：返回 {配方, 产物物品, 配方 id}。 */
    private static Object[] lookup(ItemStack base, ItemStack addition, ItemStack template) {
        RecipeManager manager = server.getRecipeManager();
        SmithingRecipeInput input = new SmithingRecipeInput(template, base, addition);
        RecipeHolder<SmithingRecipe> holder = manager
                .getRecipeFor(RecipeType.SMITHING, input, level).orElse(null);
        if (holder == null) {
            return new Object[]{null, null, "-"};
        }
        ItemStack out = holder.value().assemble(input, server.registryAccess());
        return new Object[]{holder, out.getItem(), holder.id().getPath()};
    }

    /** 3×3：八块铝锭围一圈 + 中间那张（true=下界合金模板 / false=铝锭）。 */
    private static boolean craftRing(boolean realCenter) {
        List<ItemStack> grid = new ArrayList<>();
        for (int i = 0; i < 9; i++) {
            if (i == 4) {
                grid.add(stack(realCenter ? Items.NETHERITE_UPGRADE_SMITHING_TEMPLATE : ModItems.ALUMINUM_INGOT.get()));
            } else {
                grid.add(stack(ModItems.ALUMINUM_INGOT.get()));
            }
        }
        CraftingInput input = CraftingInput.of(3, 3, grid);
        RecipeHolder<?> holder = server.getRecipeManager()
                .getRecipeFor(RecipeType.CRAFTING, input, level).orElse(null);
        return holder != null && "universal_upgrade_template".equals(holder.id().getPath());
    }

    private static int smithingCount() {
        return server.getRecipeManager().getAllRecipesFor(RecipeType.SMITHING).size();
    }

    // =========================================================== 第二阶段：真 /reload
    private static void triggerReload() {
        managerBefore = server.getRecipeManager();
        // 不用自己动手摘加宽：真 /reload 会把整张配方表**从数据包重建**（RecipeManager.apply），
        // 加宽版自然消失 ⇒ reload 之后还认通用模板，就只可能是挂点又装了一遍（F2 验的就是这个）。
        try {
            server.reloadResources(server.getPackRepository().getSelectedIds());
            reloadTriggeredAt = ticks;
            note("已触发真 /reload（MinecraftServer.reloadResources）");
        } catch (Throwable t) {
            reloadThrew = true;
            reloadTriggeredAt = ticks;
            note("真 /reload 抛了：" + t);
        }
    }

    // =========================================================== 第三阶段：验 reload
    private static boolean phase3() {
        if (ticks - reloadTriggeredAt > 200) {
            check("F1 真 /reload 完成（管理器换新）", false);
            return true;
        }
        RecipeManager now = server.getRecipeManager();
        if (now == managerBefore) {
            return false; // 还没换
        }
        check("F1 真 /reload 换掉了 RecipeManager 实例", true);
        RecipeHolder<?> helmet = now
                .byKey(ResourceLocation.withDefaultNamespace("netherite_helmet_smithing")).orElse(null);
        check("F2 /reload 之后加宽**自己回来了**（挂点生效）" + (reloadThrew ? "（⚠ 上面那步抛过）" : ""),
                !reloadThrew && helmet != null && helmet.value() instanceof SmithingRecipe sr
                        && sr.isTemplateIngredient(stack(ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get())));
        Object[] r = lookup(stack(Items.DIAMOND_HELMET), stack(Items.NETHERITE_INGOT),
                stack(ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get()));
        check("F3 /reload 之后照旧能用（钻石头盔 + 下界合金锭 + 通用模板 → 下界合金头盔）",
                r[0] != null && r[1] == Items.NETHERITE_HELMET);
        check("F4 /reload 之后纹饰仍然不吃通用模板",
                lookup(stack(Items.DIAMOND_CHESTPLATE), stack(Items.GOLD_INGOT),
                        stack(ModItems.UNIVERSAL_UPGRADE_TEMPLATE.get()))[0] == null);
        return true;
    }
}
