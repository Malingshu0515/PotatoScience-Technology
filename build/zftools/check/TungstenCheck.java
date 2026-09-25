package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF46 临时文件，验证完必须删）</b>：黑钨矿 + 粗钨。
 *
 * <p>用户原话：「加入黑钨矿 和粗钨 <b>目前不可以被任何东西冶炼</b>」。
 * 所以本探针的**核心断言是"没有"**：熔炉 / 高炉 / 烟熏炉 / 营火 / 电力高炉，
 * 五个查询全都要落空 —— 并且要**在真服务端上真跑一遍电力高炉**，
 * 因为"我没写配方"和"机器确实不认"是两件事（§4.27 的口径）。</p>
 *
 * <p>期望值照用户原话与策划值硬写（§4.27/§4.30）：0 条配方、掉落粗钨、铁镐、-64~16。</p>
 */
public final class TungstenCheck {

    private static final String TAG = "[W] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(144, 220, 144);

    private TungstenCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(TungstenCheck.class);
            System.out.println(TAG + "diagnostic hook registered (game bus)");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            ServerLevel level = event.getServer().overworld();
            failed += registration();
            failed += notSmeltable(level);
            failed += ebfRefuses(level);
            failed += miningAndDrops(level);
            failed += worldgen(level);
            failed += commonTags();
            clear(level);
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

    // ================= ① 注册 =================
    private static int registration() {
        System.out.println(TAG + "① registration");
        int failed = 0;
        for (String id : new String[] {"wolframite_ore", "deepslate_wolframite_ore"}) {
            ResourceLocation rl = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, id);
            failed += check(id + " in BLOCK registry", BuiltInRegistries.BLOCK.containsKey(rl));
            failed += check(id + " in ITEM registry as BlockItem", BuiltInRegistries.ITEM.containsKey(rl)
                    && BuiltInRegistries.ITEM.get(rl) instanceof net.minecraft.world.item.BlockItem);
        }
        failed += check("raw_tungsten in ITEM registry",
                BuiltInRegistries.ITEM.containsKey(
                        ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "raw_tungsten")));
        return failed;
    }

    // ================= ② 不能被任何东西冶炼 =================
    private static int notSmeltable(ServerLevel level) {
        System.out.println(TAG + "② not smeltable by anything");
        int failed = 0;
        ItemStack raw = new ItemStack(PotatoSTOres.RAW_TUNGSTEN.get());
        SingleRecipeInput in = new SingleRecipeInput(raw);

        failed += check("furnace (minecraft:smelting) has no recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.SMELTING, in, level).isEmpty());
        failed += check("blast furnace (minecraft:blasting) has no recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.BLASTING, in, level).isEmpty());
        failed += check("smoker (minecraft:smoking) has no recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.SMOKING, in, level).isEmpty());
        failed += check("campfire (minecraft:campfire_cooking) has no recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.CAMPFIRE_COOKING, in, level).isEmpty());
        failed += check("electric blast furnace table has no single recipe",
                BlastFurnaceRecipes.find(raw) == null);
        failed += check("electric blast furnace table has no pair recipe either",
                BlastFurnaceRecipes.findPair(raw, new ItemStack(ModItems.CARBON.get())) == null
                        && BlastFurnaceRecipes.findPair(raw, new ItemStack(ModItems.IRON_POWDER.get())) == null
                        && BlastFurnaceRecipes.findPair(new ItemStack(Items.GRAVEL), raw) == null);
        // 顺手：连粉碎机也不认（用户只说"冶炼"，这条是额外情报 —— 若不成立也不该算失败，
        // 但当前设计与"先收着、以后再接线"一致，所以照样断言，让读数明确。）
        failed += check("(extra) micro crusher has no recipe either",
                MicroCrusherRecipes.find(raw) == null);
        // 反向对照：粗铁**有**配方 ⇒ 证明上面那几条不是因为"查询本身坏了"
        failed += check("control: raw iron DOES have a vanilla blasting recipe (query works)",
                !level.getRecipeManager()
                        .getRecipeFor(RecipeType.BLASTING, new SingleRecipeInput(new ItemStack(Items.RAW_IRON)), level)
                        .isEmpty());
        return failed;
    }

    // ================= ③ 电力高炉实机：喂粗钨它也不动 =================
    private static int ebfRefuses(ServerLevel level) {
        System.out.println(TAG + "③ electric blast furnace in-world");
        int failed = 0;
        clear(level);
        build(level);
        BlastFurnaceAssembly.form(level, C, Direction.SOUTH);
        if (!(level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m)) {
            return check("got the controller block entity", false);
        }
        m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                new ItemStack(PotatoSTOres.RAW_TUNGSTEN.get(), 64));
        m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + 1,
                new ItemStack(PotatoSTOres.WOLFRAMITE_ORE.get(), 64));
        long spent = 0;
        for (int i = 0; i < 400; i++) {
            setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            int before = m.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m);
            spent += Math.max(0, before - m.getEnergyStored());
        }
        int progressRaw = m.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST);
        int progressOre = m.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST + 1);
        int out = 0;
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            out += m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k).getCount();
        }
        System.out.println(TAG + "  400 ticks with full power: progress=" + progressRaw + "/" + progressOre
                + ", energy spent=" + spent + ", output=" + out);
        failed += check("raw tungsten slot progress stays 0 after 400 ticks", progressRaw == 0);
        failed += check("wolframite ore slot progress stays 0", progressOre == 0);
        failed += check("no energy consumed at all (spent=" + spent + ")", spent == 0);
        failed += check("no output produced (out=" + out + ")", out == 0);
        failed += check("inputs untouched",
                m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST).getCount() == 64
                        && m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + 1).getCount() == 64);
        clear(level);
        return failed;
    }

    // ================= ④ 挖掘等级与掉落 =================
    private static int miningAndDrops(ServerLevel level) {
        System.out.println(TAG + "④ mining tier and drops");
        int failed = 0;
        ItemStack diamond = new ItemStack(Items.DIAMOND_PICKAXE);
        ItemStack ironPick = new ItemStack(Items.IRON_PICKAXE);
        ItemStack stonePick = new ItemStack(Items.STONE_PICKAXE);
        BlockPos pos = new BlockPos(200, 220, 200);

        for (Block block : new Block[] {PotatoSTOres.WOLFRAMITE_ORE.get(),
                PotatoSTOres.DEEPSLATE_WOLFRAMITE_ORE.get()}) {
            BlockState state = block.defaultBlockState();
            String name = BuiltInRegistries.BLOCK.getKey(block).getPath();
            failed += check(name + ": requiresCorrectToolForDrops", state.requiresCorrectToolForDrops());
            failed += check(name + ": in #minecraft:mineable/pickaxe", state.is(BlockTags.MINEABLE_WITH_PICKAXE));
            failed += check(name + ": in #minecraft:needs_iron_tool", state.is(BlockTags.NEEDS_IRON_TOOL));

            level.setBlock(pos, state, 3);
            List<ItemStack> got = Block.getDrops(state, level, pos, null, null, diamond);
            boolean dropsRaw = got.size() == 1 && got.get(0).getCount() == 1
                    && got.get(0).getItem() == PotatoSTOres.RAW_TUNGSTEN.get();
            failed += check(name + ": drops 1 raw_tungsten (actually " + describe(got) + ")", dropsRaw);
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);

            failed += check(name + ": diamond pickaxe is a correct tool", hasCorrectTool(state, diamond));
            failed += check(name + ": iron pickaxe is a correct tool", hasCorrectTool(state, ironPick));
            failed += check(name + ": stone pickaxe is NOT (needs_iron_tool works)",
                    !hasCorrectTool(state, stonePick));
            failed += check(name + ": empty hand is NOT", !hasCorrectTool(state, ItemStack.EMPTY));
        }
        return failed;
    }

    // ================= ⑤ 世界生成接线 =================
    private static int worldgen(ServerLevel level) {
        System.out.println(TAG + "⑤ worldgen wiring");
        int failed = 0;
        ResourceLocation cfgId = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "ore_wolframite");
        ResourceLocation placedId = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "ore_wolframite_placed");
        var cfgReg = level.registryAccess().registryOrThrow(Registries.CONFIGURED_FEATURE);
        var placedReg = level.registryAccess().registryOrThrow(Registries.PLACED_FEATURE);
        failed += check("configured_feature ore_wolframite loaded", cfgReg.containsKey(cfgId));
        failed += check("placed_feature ore_wolframite_placed loaded", placedReg.containsKey(placedId));
        if (!placedReg.containsKey(placedId)) {
            return failed;
        }
        Holder<PlacedFeature> target = placedReg.getHolderOrThrow(
                ResourceKey.create(Registries.PLACED_FEATURE, placedId));
        Holder<Biome> biome = level.getBiome(C);
        var features = biome.value().getGenerationSettings().features();
        int step = GenerationStep.Decoration.UNDERGROUND_ORES.ordinal();
        boolean inBiome = step < features.size() && features.get(step).contains(target);
        failed += check("biome at test pos (" + biome.unwrapKey().map(k -> k.location().toString()).orElse("?")
                + ") has it in UNDERGROUND_ORES", inBiome);
        return failed;
    }

    // ================= ⑥ c: 通用标签 =================
    private static int commonTags() {
        System.out.println(TAG + "⑥ c: common tags");
        int failed = 0;
        TagKey<Item> ores = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "ores/tungsten"));
        TagKey<Item> rawMaterials = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "raw_materials/tungsten"));
        TagKey<Item> anyOres = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "ores"));
        failed += check("#c:ores/tungsten has " + countTag(ores) + " entries (expect 2)", countTag(ores) == 2);
        failed += check("#c:raw_materials/tungsten has " + countTag(rawMaterials) + " (expect 1)",
                countTag(rawMaterials) == 1);
        failed += check("both ore items reachable through parent #c:ores",
                new ItemStack(PotatoSTOres.WOLFRAMITE_ORE.get()).is(anyOres)
                        && new ItemStack(PotatoSTOres.DEEPSLATE_WOLFRAMITE_ORE.get()).is(anyOres));
        failed += check("raw_tungsten is in #c:raw_materials/tungsten",
                new ItemStack(PotatoSTOres.RAW_TUNGSTEN.get()).is(rawMaterials));
        failed += check("(sanity) ore blocks are NOT in #minecraft:logs", !new ItemStack(
                PotatoSTOres.WOLFRAMITE_ORE.get()).is(ItemTags.LOGS));
        return failed;
    }

    // ================= 工具 =================
    private static boolean hasCorrectTool(BlockState state, ItemStack tool) {
        return !state.requiresCorrectToolForDrops() || tool.isCorrectToolForDrops(state);
    }

    private static String describe(List<ItemStack> stacks) {
        if (stacks.isEmpty()) {
            return "empty";
        }
        StringBuilder sb = new StringBuilder();
        for (ItemStack s : stacks) {
            if (sb.length() > 0) {
                sb.append(", ");
            }
            sb.append(BuiltInRegistries.ITEM.getKey(s.getItem())).append(" x").append(s.getCount());
        }
        return sb.toString();
    }

    private static int countTag(TagKey<Item> tag) {
        int n = 0;
        for (Holder<Item> ignored : BuiltInRegistries.ITEM.getTagOrEmpty(tag)) {
            n++;
        }
        return n;
    }

    private static void setEnergy(ElectricBlastFurnaceBlockEntity m, int v) {
        try {
            var f = ElectricBlastFurnaceBlockEntity.class.getDeclaredField("energy");
            f.setAccessible(true);
            f.setInt(m, v);
        } catch (Throwable t) {
            System.out.println(TAG + "  (setEnergy failed: " + t + ")");
        }
    }

    private static void build(ServerLevel level) {
        for (int y = 0; y < 3; y++) {
            for (int j = 0; j < 3; j++) {
                for (int i = 0; i < 3; i++) {
                    level.setBlock(ElectricBlastFurnaceStructure.offset(C, Direction.SOUTH, i, j, y),
                            ElectricBlastFurnaceStructure.blockFor(
                                    ElectricBlastFurnaceStructure.kindAt(i, j, y)).defaultBlockState(), 3);
                }
            }
        }
    }

    private static void clear(ServerLevel level) {
        for (BlockPos p : ElectricBlastFurnaceStructure.positions(C, Direction.SOUTH)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
