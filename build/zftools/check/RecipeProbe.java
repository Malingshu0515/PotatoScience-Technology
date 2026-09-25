package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF47 临时文件，验证完必须删）</b>：耐热金属块的新配方。
 *
 * <p>只加一条配方，但该验的两件事一件都不能省（§4.27/§4.30 的口径）：</p>
 * <ol>
 *   <li><b>加载进来了</b>：31 份 JSON 逐条 {@code byKey} 查得到、产物与数量对（照图纸硬写）；</li>
 *   <li><b>真能合成</b>：照着配方的 {@code getIngredients()} 把材料摆进 {@link CraftingInput}，
 *       调 {@code assemble(...)} —— 产物必须是 1 个耐热金属块。
 *       只读 {@code getResultItem()} 是"配方说自己出什么"，{@code assemble} 才是"合成台真出什么"。</li>
 * </ol>
 */
public final class RecipeProbe {

    private static final String TAG = "[R47] ";
    private static boolean registered;

    private RecipeProbe() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(RecipeProbe.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed += allRecipesLoad(event.getServer().overworld());
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

    /** {配方文件名, 产物 id, 数量} —— 本项目全部**合成**配方（照图纸硬写，不读文件）。 */
    private static final String[][] EXPECT = {
            // ZF45 那批（14 条）
            {"micro_crusher", "potato_s_t:micro_crusher", "1"},
            {"hydraulic_press", "potato_s_t:hydraulic_press", "1"},
            {"filling_machine", "potato_s_t:filling_machine", "1"},
            {"salt_dryer", "potato_s_t:salt_dryer", "1"},
            {"generator", "potato_s_t:generator", "1"},
            {"fluid_pipe", "potato_s_t:fluid_pipe", "16"},
            {"fluid_pump", "potato_s_t:fluid_pump", "1"},
            {"salt_decomposer", "potato_s_t:salt_decomposer", "1"},
            {"photovoltaic_component", "potato_s_t:photovoltaic_component", "1"},
            {"solar_panel", "potato_s_t:solar_panel", "1"},
            {"thermal_metal", "potato_s_t:thermal_metal", "1"},
            {"heater", "potato_s_t:heater", "1"},
            {"empty_spool", "potato_s_t:empty_spool", "1"},
            {"copper_wire", "potato_s_t:copper_wire", "4"},
            // ZF47
            {"heat_resistant_metal_block", "potato_s_t:heat_resistant_metal_block", "1"},
    };

    private static int allRecipesLoad(ServerLevel level) {
        System.out.println(TAG + "① all crafting recipes load and produce what the drawing says");
        int failed = 0;
        for (String[] row : EXPECT) {
            ResourceLocation id = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, row[0]);
            var holder = level.getRecipeManager().byKey(id);
            if (holder.isEmpty()) {
                failed += check(row[0] + ": loaded", false);
                continue;
            }
            RecipeHolder<?> h = holder.get();
            ItemStack out = h.value().getResultItem(level.registryAccess());
            String gotId = BuiltInRegistries.ITEM.getKey(out.getItem()).toString();
            failed += check(row[0] + " -> " + row[1] + " x" + row[2]
                            + " (got " + gotId + " x" + out.getCount() + ")",
                    gotId.equals(row[1]) && out.getCount() == Integer.parseInt(row[2]));
        }

        // ② 真摆一遍再合成
        System.out.println(TAG + "② actually craft the new one");
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "heat_resistant_metal_block");
        var holder = level.getRecipeManager().byKey(id);
        if (holder.isEmpty() || !(holder.get().value() instanceof CraftingRecipe recipe)) {
            failed += check("new recipe is a CraftingRecipe", false);
            return failed;
        }
        List<ItemStack> cells = new ArrayList<>();
        for (Ingredient ing : recipe.getIngredients()) {
            ItemStack[] items = ing.getItems();
            cells.add(items.length == 0 ? ItemStack.EMPTY : items[0].copy());
        }
        System.out.println(TAG + "  drawing: " + describe(cells));
        CraftingInput input = CraftingInput.of(3, 3, cells);
        ItemStack crafted = recipe.assemble(input, level.registryAccess());
        String craftedId = BuiltInRegistries.ITEM.getKey(crafted.getItem()).toString();
        failed += check("assemble() -> potato_s_t:heat_resistant_metal_block x1 (got "
                        + craftedId + " x" + crafted.getCount() + ")",
                craftedId.equals("potato_s_t:heat_resistant_metal_block") && crafted.getCount() == 1);
        NonNullList<ItemStack> remaining = recipe.getRemainingItems(input);
        int leftovers = 0;
        for (ItemStack s : remaining) {
            if (!s.isEmpty()) {
                leftovers++;
            }
        }
        failed += check("no leftover items returned (got " + leftovers + ")", leftovers == 0);
        return failed;
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
