package com.potatost.mod;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF69 临时文件，验证完必须删）</b>：散热装置配方（加热装置围一圈青金石）。
 *
 * <p>用户原话只有一句：「给散热装置加一个配方 加热装置围一圈青金石」。</p>
 *
 * <p>与 ZF47 那次 {@code RecipeProbe} 最大的区别 —— <b>不许再从配方自己的 {@code getIngredients()}
 * 反推摆法</b>。那样是循环论证：配方写反了，摆出来的材料也跟着反，于是照样"通过"。
 * 这里改成<b>照用户原话硬摆</b>（外圈 8 个青金石 + 中心 1 个加热装置），
 * 再拿游戏自己的 {@code RecipeManager} 去匹配；外圈/中心那 9 条断言也各自
 * "必须接受对的、且必须不接受错的"。</p>
 *
 * <p>负向对照 5 条（错摆法一律不许出散热装置）—— 正向过不代表认得出错的。</p>
 */
public final class HeatSinkRecipeCheck {

    private static final String TAG = "[R69] ";
    private static final ResourceLocation HEAT_SINK =
            ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "heat_sink");
    /** 照文件数硬写：recipe/ 下 34 份 JSON，其中 6 份是 smelting/blasting ⇒ 合成 28 条 */
    private static final int EXPECT_CRAFTING = 28;

    private static boolean registered;
    private static int failed;

    private HeatSinkRecipeCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(HeatSinkRecipeCheck.class);
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
            checkRegistration();
            checkRecipeLoaded(level);
            checkIngredientGrid(level);
            checkRealCrafting(level);
            checkNegativeControls(level);
            checkInventory(event);
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

    // ============================================================
    //  ① 物品本身
    // ============================================================
    private static void checkRegistration() {
        System.out.println(TAG + "① the block item exists");
        ItemStack sink = new ItemStack(ModBlocks.HEAT_SINK_ITEM.get());
        String id = BuiltInRegistries.ITEM.getKey(sink.getItem()).toString();
        failed += check("散热装置的物品 id = potato_s_t:heat_sink (got " + id + ")", id.equals("potato_s_t:heat_sink"));
        ItemStack heater = new ItemStack(ModBlocks.HEATER_ITEM.get());
        String hid = BuiltInRegistries.ITEM.getKey(heater.getItem()).toString();
        failed += check("加热装置的物品 id = potato_s_t:heater (got " + hid + ")", hid.equals("potato_s_t:heater"));
    }

    // ============================================================
    //  ② 配方加载 + 产物
    // ============================================================
    private static void checkRecipeLoaded(ServerLevel level) {
        System.out.println(TAG + "② recipe loads: shaped, 3x3, result = 1 heat sink");
        Optional<RecipeHolder<?>> holder = level.getRecipeManager().byKey(HEAT_SINK);
        if (holder.isEmpty()) {
            failed += check("potato_s_t:heat_sink 加载得到", false);
            return;
        }
        failed += check("potato_s_t:heat_sink 加载得到", true);
        if (!(holder.get().value() instanceof ShapedRecipe shaped)) {
            failed += check("是定形（ShapedRecipe）配方（实际 " + holder.get().value().getClass().getSimpleName() + "）", false);
            return;
        }
        failed += check("是定形（ShapedRecipe）配方", true);
        failed += check("3x3（实际 " + shaped.getWidth() + "x" + shaped.getHeight() + "）",
                shaped.getWidth() == 3 && shaped.getHeight() == 3);
        failed += check("不是特殊配方（isSpecial=false，配方书/JEI 才画得出来）", !shaped.isSpecial());

        ItemStack out = shaped.getResultItem(level.registryAccess());
        String oid = BuiltInRegistries.ITEM.getKey(out.getItem()).toString();
        failed += check("产物 = 1 个散热装置（实际 " + oid + " x" + out.getCount() + "）",
                out.is(ModBlocks.HEAT_SINK_ITEM.get()) && out.getCount() == 1);
    }

    // ============================================================
    //  ③ 九格成分：中心必须是加热装置、外圈 8 格必须是青金石
    // ============================================================
    private static void checkIngredientGrid(ServerLevel level) {
        System.out.println(TAG + "③ ingredient grid: lapis ring + heater in the middle");
        Optional<RecipeHolder<?>> holder = level.getRecipeManager().byKey(HEAT_SINK);
        if (holder.isEmpty() || !(holder.get().value() instanceof ShapedRecipe shaped)) {
            failed += check("九格成分（配方没加载，跳过）", false);
            return;
        }
        NonNullList<Ingredient> ings = shaped.getIngredients();
        if (ings.size() != 9) {
            failed += check("九格成分：getIngredients().size()=9（实际 " + ings.size() + "）", false);
            return;
        }
        ItemStack lapis = new ItemStack(Items.LAPIS_LAZULI);
        ItemStack heater = new ItemStack(ModBlocks.HEATER_ITEM.get());
        for (int i = 0; i < 9; i++) {
            boolean center = (i == 4);
            Ingredient ing = ings.get(i);
            boolean accLapis = ing.test(lapis);
            boolean accHeater = ing.test(heater);
            boolean pass = center ? (accHeater && !accLapis) : (accLapis && !accHeater);
            failed += check(String.format("第 %d 行第 %d 列（%s）应接受 %s（实测 lapis=%s heater=%s）",
                    i / 3 + 1, i % 3 + 1, center ? "中心" : "外圈", center ? "加热装置" : "青金石", accLapis, accHeater), pass);
        }
    }

    // ============================================================
    //  ④ 真摆一遍（材料照用户原话硬摆，不从配方里读）
    // ============================================================
    private static void checkRealCrafting(ServerLevel level) {
        System.out.println(TAG + "④ actually craft it with the drawing from the user (8 lapis + 1 heater)");
        List<ItemStack> cells = ringDrawing();
        System.out.println(TAG + "  摆法: " + describe(cells));
        CraftingInput input = CraftingInput.of(3, 3, cells);

        Optional<RecipeHolder<CraftingRecipe>> found =
                level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, level);
        if (found.isEmpty()) {
            failed += check("合成台路径 getRecipeFor(...) 命中一条配方", false);
            return;
        }
        failed += check("合成台路径 getRecipeFor(...) 命中一条配方", true);
        failed += check("命中的就是 potato_s_t:heat_sink（实际 " + found.get().id() + "）",
                found.get().id().equals(HEAT_SINK));

        ItemStack crafted = found.get().value().assemble(input, level.registryAccess());
        String cid = BuiltInRegistries.ITEM.getKey(crafted.getItem()).toString();
        failed += check("assemble() = 1 个散热装置（实际 " + cid + " x" + crafted.getCount() + "）",
                crafted.is(ModBlocks.HEAT_SINK_ITEM.get()) && crafted.getCount() == 1);

        NonNullList<ItemStack> remaining = found.get().value().getRemainingItems(input);
        int leftovers = 0;
        for (ItemStack s : remaining) {
            if (!s.isEmpty()) {
                leftovers++;
            }
        }
        failed += check("没有返还物（实际 " + leftovers + " 个）", leftovers == 0);

        // 同一个摆法能命中几条"出散热装置"的配方 —— 重复配方 = JEI 里两条一模一样的
        int producing = 0;
        for (RecipeHolder<CraftingRecipe> h : level.getRecipeManager().getRecipesFor(RecipeType.CRAFTING, input, level)) {
            if (h.value().getResultItem(level.registryAccess()).is(ModBlocks.HEAT_SINK_ITEM.get())) {
                producing++;
            }
        }
        failed += check("这个摆法只命中 1 条出散热装置的配方（实际 " + producing + "）", producing == 1);
    }

    // ============================================================
    //  ⑤ 负向对照：错摆法一个都不许出散热装置
    // ============================================================
    private static void checkNegativeControls(ServerLevel level) {
        System.out.println(TAG + "⑤ negative controls: wrong layouts must NOT give a heat sink");

        List<ItemStack> swapped = ringDrawing();
        swapped.set(0, new ItemStack(ModBlocks.HEATER_ITEM.get()));
        swapped.set(4, new ItemStack(Items.LAPIS_LAZULI));
        expectNoHeatSink(level, "中心放青金石、外圈一角放加热装置", swapped);

        List<ItemStack> hole = ringDrawing();
        hole.set(8, ItemStack.EMPTY);
        expectNoHeatSink(level, "外圈少一个角（7 青金石 + 中心加热装置）", hole);

        List<ItemStack> hollow = ringDrawing();
        hollow.set(4, ItemStack.EMPTY);
        expectNoHeatSink(level, "中心空着（外圈 8 青金石）", hollow);

        List<ItemStack> allLapis = new ArrayList<>();
        for (int i = 0; i < 9; i++) {
            allLapis.add(new ItemStack(Items.LAPIS_LAZULI));
        }
        expectNoHeatSink(level, "9 个青金石", allLapis);

        List<ItemStack> allHeater = new ArrayList<>();
        for (int i = 0; i < 9; i++) {
            allHeater.add(new ItemStack(ModBlocks.HEATER_ITEM.get()));
        }
        expectNoHeatSink(level, "9 个加热装置", allHeater);
    }

    private static void expectNoHeatSink(ServerLevel level, String name, List<ItemStack> cells) {
        CraftingInput input = CraftingInput.of(3, 3, cells);
        Optional<RecipeHolder<CraftingRecipe>> found =
                level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, level);
        if (found.isEmpty()) {
            failed += check(name + " ⇒ 无配方匹配", true);
            return;
        }
        ItemStack out = found.get().value().assemble(input, level.registryAccess());
        String oid = BuiltInRegistries.ITEM.getKey(out.getItem()).toString();
        boolean notHeatSink = !out.is(ModBlocks.HEAT_SINK_ITEM.get());
        failed += check(name + " ⇒ 不许出散热装置（实际命中 " + found.get().id() + " -> " + oid + " x" + out.getCount() + "）",
                notHeatSink);
    }

    // ============================================================
    //  ⑥ 账目：本模组合成配方必须一条不少地加载
    // ============================================================
    private static void checkInventory(ServerStartedEvent event) {
        System.out.println(TAG + "⑥ inventory: every potato_s_t crafting recipe is loaded");
        List<String> ids = new ArrayList<>();
        for (RecipeHolder<?> h : event.getServer().getRecipeManager().getRecipes()) {
            if (h.id().getNamespace().equals(PotatoST.MODID) && h.value().getType() == RecipeType.CRAFTING) {
                ids.add(h.id().getPath());
            }
        }
        Collections.sort(ids);
        for (String s : ids) {
            System.out.println(TAG + "    " + s);
        }
        failed += check("本模组合成配方 = " + EXPECT_CRAFTING + " 条（实际 " + ids.size() + "）", ids.size() == EXPECT_CRAFTING);
        failed += check("散热装置在名单里", ids.contains("heat_sink"));

        int adv = 0;
        for (AdvancementHolder h : event.getServer().getAdvancements().getAllAdvancements()) {
            if (h.id().getNamespace().equals(PotatoST.MODID)) {
                adv++;
            }
        }
        System.out.println(TAG + "[INFO] 本模组 advancement = " + adv
                + " ⇒ 配方书不会自动解锁（JEI 看得到、工作台手摆也能合 —— 与另外 27 条配方同状态）");
    }

    // ============================================================
    //  工具
    // ============================================================
    /** 照用户原话硬摆：外圈 8 个青金石 + 中心 1 个加热装置。 */
    private static List<ItemStack> ringDrawing() {
        List<ItemStack> cells = new ArrayList<>();
        for (int i = 0; i < 9; i++) {
            cells.add(i == 4 ? new ItemStack(ModBlocks.HEATER_ITEM.get()) : new ItemStack(Items.LAPIS_LAZULI));
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
            sb.append(s.isEmpty() ? "_" : BuiltInRegistries.ITEM.getKey(s.getItem()).getPath());
            sb.append(' ');
        }
        return sb.toString();
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
