package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF118 的临时探针）</b>：星轨坠的合成配方。
 *
 * <p>用户原话：「星轨坠配方；中间一个下界之星 上下左右各一个星璨钢 四角放岩浆块」。</p>
 *
 * <p>只加一条配方，但该验的四件事一件都不省（§4.27/§4.30 的口径）：</p>
 * <ol>
 *   <li><b>加载进来了</b>：`byKey` 查得到、产物是 1 个星轨坠；</li>
 *   <li><b>形状真的对</b>：**照着用户那张图纸**把 9 格摆进 {@link CraftingInput}，
 *       用 {@code RecipeManager#getRecipeFor} 让它去匹配 —— 匹配不到就说明 pattern/key 抄错了。
 *       （只读 `getIngredients()` 是不够的：那只证明"有九个材料"，证明不了"哪格放哪"。）</li>
 *   <li><b>真能合成</b>：{@code assemble(...)} 出 1 个星轨坠，且没有剩余物；</li>
 *   <li><b>负向对照</b>：中心换成下界砖 / 少一格 / 四角换成岩浆膏 ⇒ **不许**匹配到这条配方。</li>
 * </ol>
 *
 * <p>外加一条**端到端**：把合成出来的星轨坠塞给一个假玩家 ⇒ ZF117 那条隐藏进度
 * `potato_s_t:starfall` 必须点亮（配方 → 物品 → 成就是一条链）。</p>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf118Check.register();`，跑完用
 * {@code _zf118_unprobe.py} 摘掉，并逐字节核对 `PotatoST.java` 回到改前件。
 * 存档先抄到 {@code build/zftools/check/} **再**从 {@code src} 删（§10.1）。</p>
 */
public final class Zf118Check {

    private static final String TAG = "[R118] ";
    private static final String NS = PotatoST.MODID;
    private static final String RECIPE = "starfall_pendant";
    private static final String RESULT = "potato_s_t:starfall_pendant";

    private static boolean registered;
    private static int failed;

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf118_probe_utf8.txt";

    private Zf118Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF118 探针报告（星轨坠配方：形状匹配 + 真合成 + 负向 + 成就联动）× UTF-8 · §4.50\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf118Check.class);
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
            checkRecipe(level);
            checkShape(level);
            checkNegative(level);
            checkAdvancement(event, level);
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

    private static Item item(String path) {
        return BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath(NS, path));
    }

    private static String idOf(ItemStack s) {
        return s.isEmpty() ? "(空)" : BuiltInRegistries.ITEM.getKey(s.getItem()).toString();
    }

    // ============================================================
    //  ① 加载 + 产物
    // ============================================================
    private static void checkRecipe(ServerLevel level) {
        say(TAG + "① recipe loads and produces the right thing");
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath(NS, RECIPE);
        Optional<RecipeHolder<?>> holder = level.getRecipeManager().byKey(id);
        failed += check("byKey(" + id + ") 找得到", holder.isPresent());
        if (holder.isEmpty()) {
            return;
        }
        failed += check("它是 CraftingRecipe（实际 " + holder.get().value().getClass().getSimpleName() + "）",
                holder.get().value() instanceof CraftingRecipe);
        ItemStack out = holder.get().value().getResultItem(level.registryAccess());
        say(TAG + "    产物 = " + idOf(out) + " x" + out.getCount());
        failed += check("产物 = " + RESULT + " x1（实际 " + idOf(out) + " x" + out.getCount() + "）",
                RESULT.equals(idOf(out)) && out.getCount() == 1);
        // 产物真的注册过（不是"配方写了但物品没有"）
        failed += check("产物物品真的注册了（不是空气）", item("starfall_pendant") != Items.AIR);
    }

    /** 用户那张图纸，**独立再写一遍**（不读 JSON、不读生成器表）。 */
    private static List<ItemStack> drawing() {
        List<ItemStack> cells = new ArrayList<>();
        String[] rows = {"MSM", "SNS", "MSM"};
        for (String row : rows) {
            for (char c : row.toCharArray()) {
                switch (c) {
                    case 'M' -> cells.add(new ItemStack(Items.MAGMA_BLOCK));
                    case 'S' -> cells.add(new ItemStack(item("star_steel_ingot")));
                    case 'N' -> cells.add(new ItemStack(Items.NETHER_STAR));
                    default -> cells.add(ItemStack.EMPTY);
                }
            }
        }
        return cells;
    }

    private static String describe(List<ItemStack> cells) {
        StringBuilder sb = new StringBuilder();
        for (int k = 0; k < cells.size(); k++) {
            if (k % 3 == 0) {
                sb.append(" / ");
            }
            ItemStack s = cells.get(k);
            String p = s.isEmpty() ? "_" : BuiltInRegistries.ITEM.getKey(s.getItem()).getPath();
            sb.append(p).append(' ');
        }
        return sb.toString();
    }

    private static Optional<RecipeHolder<CraftingRecipe>> match(ServerLevel level, List<ItemStack> cells) {
        CraftingInput input = CraftingInput.of(3, 3, cells);
        return level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, level);
    }

    // ============================================================
    //  ② 形状匹配（本轮的重点）
    // ============================================================
    private static void checkShape(ServerLevel level) {
        say(TAG + "② shape: lay the drawing out and let the recipe manager match it");
        List<ItemStack> cells = drawing();
        say(TAG + "    图纸：" + describe(cells));
        Optional<RecipeHolder<CraftingRecipe>> got = match(level, cells);
        failed += check("照着图纸摆 9 格 ⇒ getRecipeFor 匹配得到", got.isPresent());
        if (got.isEmpty()) {
            return;
        }
        say(TAG + "    匹配到：" + got.get().id());
        failed += check("匹配到的就是 " + NS + ":" + RECIPE + "（实际 " + got.get().id() + "）",
                got.get().id().equals(ResourceLocation.fromNamespaceAndPath(NS, RECIPE)));
        // 真合成
        CraftingInput input = CraftingInput.of(3, 3, cells);
        ItemStack crafted = got.get().value().assemble(input, level.registryAccess());
        say(TAG + "    assemble() = " + idOf(crafted) + " x" + crafted.getCount());
        failed += check("assemble() 出 1 个星轨坠（实际 " + idOf(crafted) + " x" + crafted.getCount() + "）",
                RESULT.equals(idOf(crafted)) && crafted.getCount() == 1);
        int leftovers = 0;
        for (ItemStack s : got.get().value().getRemainingItems(input)) {
            if (!s.isEmpty()) {
                leftovers++;
            }
        }
        failed += check("没有剩余物（实际 " + leftovers + " 件）", leftovers == 0);
        // 材料清单：4 岩浆块 + 4 星轨坠？不 —— 4 岩浆块 + 4 星璨钢锭 + 1 下界之星
        int magma = 0, steel = 0, star = 0;
        for (ItemStack s : cells) {
            if (s.is(Items.MAGMA_BLOCK)) {
                magma++;
            } else if (s.is(item("star_steel_ingot"))) {
                steel++;
            } else if (s.is(Items.NETHER_STAR)) {
                star++;
            }
        }
        failed += check("材料是 4 岩浆块 + 4 星璨钢锭 + 1 下界之星（实际 " + magma + "/" + steel + "/" + star + "）",
                magma == 4 && steel == 4 && star == 1);
    }

    // ============================================================
    //  ③ 负向对照
    // ============================================================
    private static void checkNegative(ServerLevel level) {
        say(TAG + "③ negative: these must NOT match " + RECIPE);
        // (a) 中心换成下界砖
        List<ItemStack> a = drawing();
        a.set(4, new ItemStack(Items.NETHER_BRICK));
        reportNotMatch(level, a, "中心换成下界砖");
        // (b) 右上角少一格
        List<ItemStack> b = drawing();
        b.set(2, ItemStack.EMPTY);
        reportNotMatch(level, b, "右上角留空");
        // (c) 四角换成岩浆膏
        List<ItemStack> c = drawing();
        for (int k : new int[]{0, 2, 6, 8}) {
            c.set(k, new ItemStack(Items.MAGMA_CREAM));
        }
        reportNotMatch(level, c, "四角换成岩浆膏");
        // (d) 边框和中心全换（九格岩浆块）
        List<ItemStack> d = new ArrayList<>();
        for (int k = 0; k < 9; k++) {
            d.add(new ItemStack(Items.MAGMA_BLOCK));
        }
        reportNotMatch(level, d, "九格全是岩浆块");
    }

    private static void reportNotMatch(ServerLevel level, List<ItemStack> cells, String why) {
        Optional<RecipeHolder<CraftingRecipe>> got = match(level, cells);
        boolean bad = got.isPresent()
                && got.get().id().equals(ResourceLocation.fromNamespaceAndPath(NS, RECIPE));
        say(TAG + "    " + why + " ⇒ " + (got.map(h -> h.id().toString()).orElse("(没有配方匹配)")));
        failed += check("负向：" + why + " **不许**匹配到 " + RECIPE, !bad);
    }

    // ============================================================
    //  ④ 端到端：合成出来的东西能点亮 ZF117 那条隐藏进度
    // ============================================================
    private static void checkAdvancement(ServerStartedEvent event, ServerLevel level) {
        say(TAG + "④ end to end: the crafted pendant lights potato_s_t:starfall");
        java.util.Map<String, AdvancementHolder> mine = new java.util.LinkedHashMap<>();
        for (AdvancementHolder h : event.getServer().getAdvancements().getAllAdvancements()) {
            if (h.id().getNamespace().equals(NS)) {
                mine.put(h.id().getPath(), h);
            }
        }
        AdvancementHolder node = mine.get("starfall");
        failed += check("ZF117 那条 starfall 进度在", node != null);
        if (node == null) {
            return;
        }
        GameProfile profile = new GameProfile(
                UUID.nameUUIDFromBytes("zf118probe".getBytes(StandardCharsets.UTF_8)), "zf118probe");
        ServerPlayer player = new ServerPlayer(event.getServer(), level, profile,
                ClientInformation.createDefault());
        net.minecraft.network.Connection conn = new net.minecraft.network.Connection(
                net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        player.connection = new net.minecraft.server.network.ServerGamePacketListenerImpl(
                event.getServer(), conn, player,
                net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false));
        boolean before = player.getAdvancements().getOrStartProgress(node).isDone();
        failed += check("起始状态：星轨坠那条没亮", !before);
        // 负向：岩浆块不算
        player.getInventory().add(new ItemStack(Items.MAGMA_BLOCK));
        CriteriaTriggers.INVENTORY_CHANGED.trigger(player, player.getInventory(),
                new ItemStack(Items.MAGMA_BLOCK));
        failed += check("给岩浆块 ⇒ 星轨坠**不**亮（实际 "
                        + player.getAdvancements().getOrStartProgress(node).isDone() + "）",
                !player.getAdvancements().getOrStartProgress(node).isDone());
        // 正向：合成出来的星轨坠
        List<ItemStack> cells = drawing();
        Optional<RecipeHolder<CraftingRecipe>> got = match(level, cells);
        ItemStack crafted = got.map(h -> h.value().assemble(CraftingInput.of(3, 3, cells),
                level.registryAccess())).orElse(ItemStack.EMPTY);
        failed += check("合成出来的确实是星轨坠", RESULT.equals(idOf(crafted)));
        player.getInventory().add(crafted.copy());
        CriteriaTriggers.INVENTORY_CHANGED.trigger(player, player.getInventory(), crafted.copy());
        boolean after = player.getAdvancements().getOrStartProgress(node).isDone();
        failed += check("把合成出来的星轨坠给玩家 ⇒ 进度点亮（实际 " + after + "）", after);
    }

    private static int check(String name, boolean pass) {
        say(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
