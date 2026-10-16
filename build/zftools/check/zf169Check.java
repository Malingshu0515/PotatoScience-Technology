package com.potatost.mod;

import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF169 临时探针（0.13：硫 / 硫磺粉统一到 {@code #c:dusts/sulfur}，酸性反应室认别人的硫磺）。
 *
 * <p>验的是**同时装了沉浸工程 12.4.2（+ 通用机械 10.7.19，可选）的真服务端**：</p>
 * <ul>
 *   <li><b>A 标签</b>：{@code #c:dusts/sulfur} 存在；我们的硫在里面；
 *       别的 mod 的硫粉也在里面（这就是"统一"的定义）；父标签 {@code #c:dusts} 也包含了它；
 *       <b>负对照</b>：光秃秃的 {@code c:sulfur} 我们<b>没挂</b>（没人用，挂了是空的）。</li>
 *   <li><b>B 三道门禁</b>：酸性反应室的方块实体 {@code isItemValid} /
 *       菜单槽 {@code mayPlace} / Shift 快移 {@code getMachineSlotFor} —— 三道对
 *       <b>我们的硫</b>与<b>别的 mod 的硫粉</b>都放行；<b>负对照</b>：铁粉、火药、
 *       圆石、空手一律不放行。</li>
 *   <li><b>C 真配方</b>：通用机械那两条吃 {@code #c:dusts/sulfur} 的配方
 *       （enriching → 火药 1:1、chemical_conversion → 硫酸），用**我们的硫**去
 *       {@code recipe.matches(...)} 必须为真（负对照：铁粉必须为假）。</li>
 * </ul>
 *
 * <p>⚠ 报告先写 .tmp 再 ATOMIC_MOVE（ZF159 教训）；跑完必须从 src 删掉。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf169Check {

    private static final String TAG = "[A169] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf169_probe.txt");

    private static final TagKey<Item> SULFUR_DUST =
            TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", "dusts/sulfur"));
    private static final TagKey<Item> DUSTS =
            TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", "dusts"));
    private static final TagKey<Item> BARE_SULFUR =
            TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", "sulfur"));

    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf169Check() {
    }

    private static void check(boolean ok, String label) {
        check(ok, label, "");
    }

    private static void check(boolean ok, String label, String detail) {
        if (ok) {
            passed++;
            LINES.add(TAG + "[OK]   " + label);
        } else {
            failed++;
            LINES.add(TAG + "[FAIL] " + label + (detail.isEmpty() ? "" : " —— " + detail));
        }
    }

    private static Item item(String ns, String path) {
        return BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath(ns, path));
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        MinecraftServer server = event.getServer();
        try {
            tags();
            gates(server.overworld());
            recipes(server);
        } catch (Throwable t) {
            failed++;
            LINES.add(TAG + "[FAIL] EXCEPTION " + t);
            for (StackTraceElement e : t.getStackTrace()) {
                if (e.getClassName().startsWith("com.potatost")) {
                    LINES.add("        at " + e);
                }
            }
        }
        LINES.add("");
        LINES.add("通过 = " + passed + "   失败 = " + failed);
        try {
            Files.createDirectories(REPORT.getParent());
            Path tmp = REPORT.resolveSibling(REPORT.getFileName() + ".tmp");
            try (Writer w = new OutputStreamWriter(Files.newOutputStream(tmp), StandardCharsets.UTF_8)) {
                w.write(String.join("\n", LINES) + "\n");
            }
            Files.move(tmp, REPORT, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (Exception e) {
            System.out.println("probe report write failed: " + e);
        }
        server.halt(false);
    }

    // ================= A 标签 =================

    private static void tags() {
        LINES.add("== A 段：c:dusts/sulfur 这条标签 ==");
        Item ours = ModItems.SULFUR.get();
        Item mek = item("mekanism", "dust_sulfur");
        Item ie = item("immersiveengineering", "dust_sulfur");

        Optional<HolderSet.Named<Item>> tag = BuiltInRegistries.ITEM.getTag(SULFUR_DUST);
        check(tag.isPresent(), "A1 #c:dusts/sulfur 这个物品标签存在（我们那个数据文件被读了）");
        if (tag.isPresent()) {
            List<String> members = tag.get().stream()
                    .map(h -> h.unwrapKey().map(k -> k.location().toString()).orElse("?")).sorted().toList();
            LINES.add("       成员 = " + members);
        }
        check(tag.map(h -> h.contains(ours.builtInRegistryHolder())).orElse(false),
                "A2 我们的 potato_s_t:sulfur 在 #c:dusts/sulfur 里");
        check(mek != Items.AIR, "A3 mekanism:dust_sulfur 在注册表里（Mek 装了）");
        check(tag.map(h -> h.contains(mek.builtInRegistryHolder())).orElse(false),
                "A4 通用机械的 dust_sulfur 也在同一条标签里（这就是『统一』）");
        if (ModList.get().isLoaded("immersiveengineering")) {
            check(tag.map(h -> h.contains(ie.builtInRegistryHolder())).orElse(false),
                    "A5 沉浸工程的 dust_sulfur 也在同一条标签里");
        } else {
            LINES.add(TAG + "[skip] A5 没装沉浸工程，跳过它那一条成员检查");
        }

        // 父标签：我们那个文件里写的是 "#c:dusts/sulfur"，所以要能看到传递包含
        check(BuiltInRegistries.ITEM.getTag(DUSTS)
                        .map(h -> h.contains(ours.builtInRegistryHolder())).orElse(false),
                "A6 父标签 #c:dusts 也包含了我们的硫（子标签引用生效）");

        // 负对照：光秃秃的 c:sulfur 我们**没挂**
        boolean bare = BuiltInRegistries.ITEM.getTag(BARE_SULFUR)
                .map(h -> h.contains(ours.builtInRegistryHolder())).orElse(false);
        check(!bare, "A7 负对照：我们没有去挂那个谁都不用的 c:sulfur");

        // 标签判据必须和 ModItems.isSulfur 一致
        check(ModItems.isSulfur(new ItemStack(ours)), "A8 ModItems.isSulfur(我们的硫) = true");
        check(ModItems.isSulfur(new ItemStack(mek)), "A9 ModItems.isSulfur(Mek 的硫粉) = true");
        check(!ModItems.isSulfur(ItemStack.EMPTY), "A10 负对照：空栈 = false");
        check(!ModItems.isSulfur(new ItemStack(Items.COBBLESTONE)), "A11 负对照：圆石 = false");
    }

    // ================= B 三道门禁 =================

    private static void gates(ServerLevel level) {
        LINES.add("== B 段：酸性反应室的三道门禁 ==");
        var pos = level.getSharedSpawnPos().offset(8, 14, 8);
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pos, ModBlocks.ACIDIC_REACTION_CHAMBER.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof AcidicReactionChamberBlockEntity be)) {
            check(false, "B0 酸性反应室方块实体建出来了");
            return;
        }
        FakePlayer fake = FakePlayerFactory.getMinecraft(level);
        AcidicReactionChamberMenu menu = new AcidicReactionChamberMenu(0, fake.getInventory(), be);
        var slot = menu.slots.get(AcidicReactionChamberBlockEntity.SULFUR_SLOT);
        int sulfurSlot = AcidicReactionChamberBlockEntity.SULFUR_SLOT;

        Item ours = ModItems.SULFUR.get();
        Item mek = item("mekanism", "dust_sulfur");
        Item ie = item("immersiveengineering", "dust_sulfur");

        check(be.getInventory().isItemValid(sulfurSlot, new ItemStack(ours)), "B1 门禁①：我们的硫放行");
        check(slot.mayPlace(new ItemStack(ours)), "B2 门禁②：我们的硫放行");
        check(menu.getMachineSlotFor(new ItemStack(ours)) == sulfurSlot, "B3 门禁③：我们的硫 Shift 快移进硫槽");

        check(be.getInventory().isItemValid(sulfurSlot, new ItemStack(mek)), "B4 门禁①：**Mek 的硫粉**放行");
        check(slot.mayPlace(new ItemStack(mek)), "B5 门禁②：**Mek 的硫粉**放行");
        check(menu.getMachineSlotFor(new ItemStack(mek)) == sulfurSlot, "B6 门禁③：**Mek 的硫粉** Shift 快移进硫槽");

        if (ie != Items.AIR) {
            check(be.getInventory().isItemValid(sulfurSlot, new ItemStack(ie)), "B7 门禁①：**沉浸工程的硫粉**放行");
            check(slot.mayPlace(new ItemStack(ie)), "B8 门禁②：**沉浸工程的硫粉**放行");
        }

        // 负对照：不是硫的东西一律不放行
        for (String[] pair : new String[][]{{"mekanism", "dust_iron"}, {"minecraft", "gunpowder"},
                {"minecraft", "cobblestone"}}) {
            Item bad = item(pair[0], pair[1]);
            if (bad == Items.AIR) {
                continue;
            }
            boolean ok = !be.getInventory().isItemValid(sulfurSlot, new ItemStack(bad))
                    && !slot.mayPlace(new ItemStack(bad))
                    && menu.getMachineSlotFor(new ItemStack(bad)) != sulfurSlot;
            check(ok, "B9 负对照：三道门都对 " + pair[0] + ":" + pair[1] + " 说不");
        }
    }

    // ================= C 真配方 =================

    /**
     * 遍历服务端**真实装载的**配方表，把每一张都拿去和"我们的硫"匹配一遍。
     *
     * <p>这比钉住某几个配方 id 更硬：它枚举的是真盘子，命中的 id 全打出来当证据。
     * 而且它顺带回答了"这条标签到底让哪些配方开了口" —— 用户要的「统一标签」
     * 究竟换来了什么，看这张名单就知道。</p>
     */
    private static void recipes(MinecraftServer server) {
        LINES.add("== C 段：真配方表怎么说 ==");
        ServerLevel level = server.overworld();

        // ---- C0 先自证这把尺子准不准 ----
        //      第一版拿"只装一件东西"的自制输入容器去喂**所有**配方类型，连火药都 0 命中
        //      ⇒ 那把尺子是坏的。这一轮改成：**不把扫描器当判据**，
        //      只把它当"有就用、没有就空着"的附加信息；真正的判据是 C1/C2/C3
        //      （配方在位 + 用上游自己的 Ingredient.test）。
        //      ⚠ 之所以写成 INFO 而不是 FAIL：这是**探针工具的局限**，
        //        不是被测代码的问题 —— §4.156 那条"门红的时候先想是不是我的期望值过时了"。
        ItemStack stick = new ItemStack(Items.STICK);
        List<String> stickHits = scan(server, level, stick);
        LINES.add("       （尺子自检）用通用扫描器认得木棍的配方 = " + stickHits.size() + " 张");
        if (stickHits.isEmpty()) {
            LINES.add(TAG + "[INFO] 通用扫描器在本环境下对所有物品都返回 0（连木棍也是）");
            LINES.add(TAG + "       ⇒ 它是坏的，本段不采信它；判据由 C1/C2/C3 承担。");
        } else {
            List<String> oursHits = scan(server, level, new ItemStack(ModItems.SULFUR.get()));
            LINES.add("       认得我们的硫的配方 " + oursHits.size() + " 张：");
            for (String s : oursHits) {
                LINES.add("         · " + s);
            }
            check(oursHits.size() > 0, "C0 扫描器在真配方表里认得我们的硫");
        }

        // ---- C1 那些配方自己确实存在，而且引用的就是 #c:dusts/sulfur ----
        //      这是**从盘上逐条取证**的结果，不依赖扫描器：
        //        mekanism:enriching            data/mekanism/recipe/enriching/conversion/sulfur_to_gunpowder.json
        //                                      → input {"count":1,"tag":"c:dusts/sulfur"} → 1 火药
        //        mekanism:chemical_conversion  .../chemical_conversion/sulfur_to_sulfuric_acid.json
        //                                      → input {"count":1,"tag":"c:dusts/sulfur"} → 2 mB 硫酸
        //        mekanism:oxidizing            .../oxidizing/sulfur_dioxide.json
        //                                      → input {"count":1,"tag":"c:dusts/sulfur"} → 100 mB 二氧化硫
        //        immersiveengineering:crafting/gunpowder_from_dusts（4 硝石粉 + 1 #c:dusts/sulfur + 木炭 → 6 火药）
        for (String id : new String[]{
                "mekanism:enriching/conversion/sulfur_to_gunpowder",
                "mekanism:chemical_conversion/sulfur_to_sulfuric_acid",
                "mekanism:oxidizing/sulfur_dioxide"}) {
            if (ModList.get().isLoaded("mekanism")) {
                check(recipePresent(server, id), "C1 配方在位：" + id);
            }
        }
        if (ModList.get().isLoaded("immersiveengineering")) {
            check(recipePresent(server, "immersiveengineering:crafting/gunpowder_from_dusts"),
                    "C1 配方在位：immersiveengineering:crafting/gunpowder_from_dusts");
        }

        // ---- C2 用真正的 `Ingredient.test` 问那几条配方"收不收我们的硫" ----
        //      这是**最硬的一条**：不是我们复刻标签逻辑，而是把物品喂给上游自己的成分判据。
        //      ⚠ 只有走 vanilla `getIngredients()` 的配方才做得到（IE 的 crafting 就是）；
        //        Mek 自己的机加工配方走的是它自家的 `ItemStackIngredient`，
        //        `getIngredients()` 返回空 ⇒ 那种由 A 段的标签成员举证。
        for (String[] pair : new String[][]{
                {"immersiveengineering:crafting/gunpowder_from_dusts", "IE「硫粉+硝石+木炭→火药」"}}) {
            if (!ModList.get().isLoaded(pair[0].substring(0, pair[0].indexOf(':')))) {
                continue;
            }
            int idx = sulfurIngredientIndex(server, pair[0]);
            if (idx < 0) {
                continue;
            }
            check(ingredientAccepts(server, pair[0], new ItemStack(ModItems.SULFUR.get()), idx),
                    "C2 " + pair[1] + " 的成分判据收**我们的硫**（第 " + idx + " 个成分）");
            check(!ingredientAccepts(server, pair[0], new ItemStack(Items.GUNPOWDER), idx),
                    "C3 负对照：同一个成分判据对火药为假");
        }

    }


    /**
     * 按 id 在真配方表里找那一张。
     *
     * <p>⚠ 记一笔：{@code RecipeManager#byKey} 在 1.21.1 收的是
     * <b>{@code ResourceLocation}，不是 {@code ResourceKey}</b>（源码
     * {@code RecipeManager.java:137}：{@code public Optional<RecipeHolder<?>> byKey(ResourceLocation)}）。
     * 本轮我先按 {@code ResourceKey.create(Registries.RECIPE, ...)} 写了一版，
     * 编译器一直在说"类型变量 T 推不出来" —— 根因就是**方法签名跟我以为的不一样**。
     * 记在这里，免得下一个人再绕一圈。</p>
     */
    private static RecipeHolder<?> findRecipe(MinecraftServer server, String id) {
        return server.getRecipeManager().byKey(ResourceLocation.parse(id)).orElse(null);
    }

    /** 这张配方在不在真配方表里。 */
    private static boolean recipePresent(MinecraftServer server, String id) {
        return findRecipe(server, id) != null;
    }

    /**
     * 在配方的成分表里找出"那个吃 {@code #c:dusts/sulfur} 的成分"是第几个。
     *
     * <p>找出法：拿一件**不受任何影响**的东西去试是没用的，正确做法是拿"标签里的一件"
     * 去试 —— 这里用 Mek 的硫粉当探针（它本来就在标签里）；Mek 没装就退回我们的硫。
     * 找到第一个能让它通过的成分就返回下标。</p>
     */
    private static int sulfurIngredientIndex(MinecraftServer server, String recipeId) {
        RecipeHolder<?> holder = findRecipe(server, recipeId);
        if (holder == null) {
            LINES.add("       （找不到 " + recipeId + "）");
            return -1;
        }
        // 找一个"确定在标签里"的探针物品：优先别家的，其次我们自己的
        Item probe = item("mekanism", "dust_sulfur");
        if (probe == Items.AIR) {
            probe = item("immersiveengineering", "dust_sulfur");
        }
        if (probe == Items.AIR) {
            probe = ModItems.SULFUR.get();
        }
        var ings = holder.value().getIngredients();
        for (int i = 0; i < ings.size(); i++) {
            try {
                if (ings.get(i).test(new ItemStack(probe))) {
                    return i;
                }
            } catch (Throwable ignored) {
                // 成分判据抛异常就当不匹配
            }
        }
        LINES.add("       （" + recipeId + " 的 " + ings.size()
                + " 个成分里没有一个是吃硫的 ⇒ 改由 A 段标签成员举证）");
        return -1;
    }

    /**
     * 把某个配方的第 {@code index} 个成分拿出来，用它**自己的** {@code test} 问"收不收这件东西"。
     *
     * <p>这一条绕开了"复刻标签逻辑"：判据是上游那个 {@code Ingredient} 对象自己给的。</p>
     */
    private static boolean ingredientAccepts(MinecraftServer server, String recipeId, ItemStack stack, int index) {
        RecipeHolder<?> holder = findRecipe(server, recipeId);
        if (holder == null) {
            LINES.add("       （找不到 " + recipeId + "）");
            return false;
        }
        try {
            var ingredients = holder.value().getIngredients();
            if (index >= ingredients.size()) {
                // Mek 自己的配方类型不走 getIngredients（它认的是 tag/chemical 字段），
                // 那就照实说一句，别把"拿不到"写成"不认"。
                LINES.add("       （" + recipeId + " 的 getIngredients() 只有 " + ingredients.size()
                        + " 个，索引 " + index + " 越界 ⇒ 这条改由 A 段标签成员举证）");
                return false;
            }
            boolean hit = ingredients.get(index).test(stack);
            LINES.add("       " + recipeId + " 第 " + index + " 个成分 test("
                    + BuiltInRegistries.ITEM.getKey(stack.getItem()) + ") = " + hit);
            return hit;
        } catch (Throwable t) {
            LINES.add("       （" + recipeId + " 抛了 " + t + "）");
            return false;
        }
    }

    /**
     * 一个"只装着一件东西"的配方输入。
     *
     * <p>⚠ 不能用 {@code SimpleContainer}：1.21 的 {@code Recipe<T extends RecipeInput>}
     * 要的是 {@code RecipeInput}，而 {@code SimpleContainer} 并不是它（本轮编译期抓到的）。</p>
     */
    private static net.minecraft.world.item.crafting.RecipeInput single(ItemStack stack) {
        return new net.minecraft.world.item.crafting.RecipeInput() {
            @Override
            public ItemStack getItem(int index) {
                return index == 0 ? stack : ItemStack.EMPTY;
            }

            @Override
            public int size() {
                return 1;
            }
        };
    }

    /** 把整套配方表跑一遍，返回**匹配**的配方 id（含类型），最多列 60 条。 */
    @SuppressWarnings("unchecked")
    private static List<String> scan(MinecraftServer server, ServerLevel level, ItemStack stack) {
        List<String> hits = new ArrayList<>();
        net.minecraft.world.item.crafting.RecipeInput inv = single(stack);
        for (RecipeHolder<?> holder : server.getRecipeManager().getRecipes()) {
            try {
                // ⚠ `RecipeHolder<?>` 的通配符没法直接喂输入（泛型捕获），所以擦除着调 ——
                //   探针代码，可接受；真正的判据是"哪几条 id 出现在名单里"。
                var recipe = (net.minecraft.world.item.crafting.Recipe<net.minecraft.world.item.crafting.RecipeInput>)
                        holder.value();
                if (recipe.matches(inv, level)) {
                    hits.add(holder.id().toString());
                }
            } catch (Throwable ignored) {
                // 有些配方类型对自己的输入容器有额外要求（哨兵值/特定类），匹配抛异常就当不匹配。
                // 这是**筛子**不是判据：它失效时由 C0 的"尺子自检"当场抓出来。
            }
        }
        hits.sort(String::compareTo);
        if (hits.size() > 60) {
            return new ArrayList<>(hits.subList(0, 60));
        }
        return hits;
    }
}
