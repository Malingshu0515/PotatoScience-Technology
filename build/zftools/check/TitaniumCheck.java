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
 * ⚠⚠ <b>诊断工具（ZF48 临时文件，验证完必须删）</b>：钛的整条链。
 *
 * <p>用户指定的链条是<b>唯一</b>一条：粗钛 →（粉碎机 6s/300 FE·t）→ 钛粉 →（电力高炉）→ 钛锭。
 * 所以探针要验的是**两端都不能绕**：</p>
 * <ul>
 *   <li>粗钛：熔炉 / 高炉 / 烟熏炉 / 营火 / 电力高炉 —— 全部不认（必须先去粉碎）；</li>
 *   <li>钛粉：原版冶炼也不认，**只有电力高炉**能把它变成钛锭；</li>
 *   <li>而且两台机器都要**在世界里真跑一遍**（粉碎机 120 tick / 36000 FE、高炉 200 tick / 800 FE）。</li>
 * </ul>
 *
 * <p>期望值照用户原话与算术硬写（§4.27）：6s=120 tick、300 FE/t、1:1、800 FE/件、200 tick。</p>
 */
public final class TitaniumCheck {

    private static final String TAG = "[Ti] ";
    private static boolean registered;
    private static final BlockPos EBF = new BlockPos(144, 220, 144);
    private static final BlockPos CRUSHER = new BlockPos(160, 220, 160);

    private TitaniumCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(TitaniumCheck.class);
            System.out.println(TAG + "hook registered");
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
            failed += recipeWiring(level);
            failed += crusherInWorld(level);
            failed += ebfInWorld(level);
            failed += miningAndDrops(level);
            failed += worldgenAndTags(level);
            cleanup(level);
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
        for (String id : new String[] {"titanium_ore", "deepslate_titanium_ore"}) {
            ResourceLocation rl = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, id);
            failed += check(id + " block + BlockItem", BuiltInRegistries.BLOCK.containsKey(rl)
                    && BuiltInRegistries.ITEM.get(rl) instanceof net.minecraft.world.item.BlockItem);
        }
        for (String id : new String[] {"raw_titanium", "titanium_powder", "titanium_ingot"}) {
            failed += check(id + " item registered", BuiltInRegistries.ITEM.containsKey(
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, id)));
        }
        return failed;
    }

    // ================= ② 配方接线 =================
    private static int recipeWiring(ServerLevel level) {
        System.out.println(TAG + "② recipe wiring (the chain must be the only way)");
        int failed = 0;
        ItemStack raw = new ItemStack(PotatoSTOres.RAW_TITANIUM.get());
        ItemStack powder = new ItemStack(ModItems.TITANIUM_POWDER.get());
        ItemStack ingot = new ItemStack(ModItems.TITANIUM_INGOT.get());

        // ⚠ 这里**不写循环**：`getRecipeFor` 的签名是 <C extends RecipeInput, T extends Recipe<C>>，
        //    用通配符 RecipeType<?> 去 cast 会在编译期报"类型参数不在范围内"（第一版就栽在这）。
        //    四条各写一遍，类型推断自然就对。
        SingleRecipeInput rawIn = new SingleRecipeInput(raw);
        failed += check("raw titanium: furnace has NO recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.SMELTING, rawIn, level).isEmpty());
        failed += check("raw titanium: blast furnace has NO recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.BLASTING, rawIn, level).isEmpty());
        failed += check("raw titanium: smoker has NO recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.SMOKING, rawIn, level).isEmpty());
        failed += check("raw titanium: campfire has NO recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.CAMPFIRE_COOKING, rawIn, level).isEmpty());
        failed += check("raw titanium: not in the electric blast furnace table",
                BlastFurnaceRecipes.find(raw) == null);
        failed += check("raw titanium: no pair recipe either",
                BlastFurnaceRecipes.findPair(raw, new ItemStack(ModItems.CARBON.get())) == null);
        failed += check("raw titanium: the crusher DOES have it (6s / 300 FE/t)",
                MicroCrusherRecipes.find(raw) != null
                        && MicroCrusherRecipes.find(raw).durationTicks() == 120
                        && MicroCrusherRecipes.find(raw).energyPerTick() == 300
                        && MicroCrusherRecipes.find(raw).result() == ModItems.TITANIUM_POWDER.get());

        failed += check("titanium powder: furnace has NO recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.SMELTING, new SingleRecipeInput(powder), level).isEmpty());
        failed += check("titanium powder: blast furnace has NO recipe",
                level.getRecipeManager().getRecipeFor(RecipeType.BLASTING, new SingleRecipeInput(powder), level).isEmpty());
        BlastFurnaceRecipes.Recipe eb = BlastFurnaceRecipes.find(powder);
        failed += check("titanium powder: electric blast furnace DOES smelt it into 1 ingot (1:1)",
                eb != null && eb.output() == ModItems.TITANIUM_INGOT.get() && eb.count() == 1);
        failed += check("titanium ingot itself is not a recipe input anywhere",
                BlastFurnaceRecipes.find(ingot) == null && MicroCrusherRecipes.find(ingot) == null
                        && level.getRecipeManager().getRecipeFor(RecipeType.SMELTING,
                        new SingleRecipeInput(ingot), level).isEmpty());
        // 对照：粗铁**有**原版高炉配方 ⇒ 证明上面那些"没有"不是查询坏了
        failed += check("control: raw iron DOES have a vanilla blasting recipe",
                !level.getRecipeManager().getRecipeFor(RecipeType.BLASTING,
                        new SingleRecipeInput(new ItemStack(Items.RAW_IRON)), level).isEmpty());
        return failed;
    }

    // ================= ③ 粉碎机实机 =================
    private static int crusherInWorld(ServerLevel level) {
        System.out.println(TAG + "③ micro crusher in-world (raw titanium -> powder)");
        int failed = 0;
        level.setBlock(CRUSHER, ModBlocks.MICRO_CRUSHER.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(CRUSHER) instanceof MicroCrusherBlockEntity c)) {
            return check("got the crusher block entity", false);
        }
        c.getInventory().setStackInSlot(MicroCrusherBlockEntity.INPUT_SLOT,
                new ItemStack(PotatoSTOres.RAW_TITANIUM.get(), 1));
        long spent = 0;
        int ticks = 0;
        for (int i = 0; i < 400; i++) {
            setEnergy(c, MicroCrusherBlockEntity.MAX_ENERGY);
            int before = c.getContainerData().get(MicroCrusherBlockEntity.DATA_ENERGY);
            MicroCrusherBlockEntity.tick(level, CRUSHER, level.getBlockState(CRUSHER), c);
            spent += Math.max(0, before - c.getContainerData().get(MicroCrusherBlockEntity.DATA_ENERGY));
            ticks++;
            if (!c.getInventory().getStackInSlot(MicroCrusherBlockEntity.OUTPUT_FIRST).isEmpty()) {
                break;
            }
        }
        int out = 0;
        ItemStack got = ItemStack.EMPTY;
        for (int k = 0; k < MicroCrusherBlockEntity.OUTPUT_COUNT; k++) {
            ItemStack s = c.getInventory().getStackInSlot(MicroCrusherBlockEntity.OUTPUT_FIRST + k);
            if (!s.isEmpty()) {
                got = s;
                out += s.getCount();
            }
        }
        int progressMax = c.getContainerData().get(MicroCrusherBlockEntity.DATA_PROGRESS_MAX);
        System.out.println(TAG + "  120-tick run: ticks=" + ticks + ", spent=" + spent + " FE, out="
                + BuiltInRegistries.ITEM.getKey(got.getItem()) + " x" + out + ", progressMax=" + progressMax);
        failed += check("recipe duration = 120 ticks (6s)", progressMax == 120);
        failed += check("finished in exactly 120 ticks (got " + ticks + ")", ticks == 120);
        failed += check("total energy = 36000 FE = 300 FE/t x 120 (got " + spent + ")", spent == 36000);
        failed += check("output = 1 titanium_powder (got "
                + BuiltInRegistries.ITEM.getKey(got.getItem()) + " x" + out + ")",
                out == 1 && got.getItem() == ModItems.TITANIUM_POWDER.get());
        failed += check("input slot is now empty",
                c.getInventory().getStackInSlot(MicroCrusherBlockEntity.INPUT_SLOT).isEmpty());
        return failed;
    }

    // ================= ④ 电力高炉实机 =================
    private static int ebfInWorld(ServerLevel level) {
        System.out.println(TAG + "④ electric blast furnace in-world (powder -> ingot)");
        int failed = 0;

        // (1) 粗钛丢进去：一动不动（必须先去粉碎）
        build(level);
        BlastFurnaceAssembly.form(level, EBF, Direction.SOUTH);
        if (!(level.getBlockEntity(EBF) instanceof ElectricBlastFurnaceBlockEntity m)) {
            return check("got the EBF block entity", false);
        }
        m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                new ItemStack(PotatoSTOres.RAW_TITANIUM.get(), 8));
        long spentRaw = 0;
        for (int i = 0; i < 50; i++) {
            setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            int before = m.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, EBF, level.getBlockState(EBF), m);
            spentRaw += Math.max(0, before - m.getEnergyStored());
        }
        int prog = m.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST);
        failed += check("raw titanium in the EBF: progress stays 0 after 50 ticks (got " + prog + ")", prog == 0);
        failed += check("raw titanium in the EBF: no energy spent (got " + spentRaw + ")", spentRaw == 0);

        // (2) 钛粉丢进去：200 tick 出 1 个钛锭，800 FE
        clear(level);
        build(level);
        BlastFurnaceAssembly.form(level, EBF, Direction.SOUTH);
        m = (ElectricBlastFurnaceBlockEntity) level.getBlockEntity(EBF);
        m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                new ItemStack(ModItems.TITANIUM_POWDER.get(), 1));
        long spent = 0;
        int ticks = 0;
        for (int i = 0; i < 400; i++) {
            setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            int before = m.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, EBF, level.getBlockState(EBF), m);
            spent += Math.max(0, before - m.getEnergyStored());
            ticks++;
            if (!m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST).isEmpty()) {
                break;
            }
        }
        int ingots = 0;
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            ItemStack s = m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k);
            if (s.is(ModItems.TITANIUM_INGOT.get())) {
                ingots += s.getCount();
            }
        }
        System.out.println(TAG + "  1 powder -> " + ingots + " ingot in " + ticks + " ticks, " + spent + " FE");
        failed += check("powder smelts in exactly 200 ticks (got " + ticks + ")", ticks == 200);
        failed += check("total energy 800 FE (got " + spent + ")", spent == 800);
        failed += check("output = 1 titanium_ingot (got " + ingots + ")", ingots == 1);

        // (3) 满载：64 个钛粉 → 64 个钛锭（200 tick、51200 FE）
        clear(level);
        build(level);
        BlastFurnaceAssembly.form(level, EBF, Direction.SOUTH);
        m = (ElectricBlastFurnaceBlockEntity) level.getBlockEntity(EBF);
        m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                new ItemStack(ModItems.TITANIUM_POWDER.get(), 64));
        long spentFull = 0;
        int ticksFull = 0;
        for (int i = 0; i < 400; i++) {
            setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            int before = m.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, EBF, level.getBlockState(EBF), m);
            spentFull += Math.max(0, before - m.getEnergyStored());
            ticksFull++;
            if (!m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST).isEmpty()) {
                break;
            }
        }
        int full = 0;
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            ItemStack s = m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k);
            if (s.is(ModItems.TITANIUM_INGOT.get())) {
                full += s.getCount();
            }
        }
        System.out.println(TAG + "  64 powder -> " + full + " ingots in " + ticksFull + " ticks, " + spentFull + " FE");
        failed += check("64 powder -> 64 ingots in 200 ticks (got " + full + " / " + ticksFull + ")",
                full == 64 && ticksFull == 200);
        failed += check("64 powder costs 51200 FE (got " + spentFull + ")", spentFull == 51200);
        clear(level);
        return failed;
    }

    // ================= ⑤ 挖掘与掉落 =================
    private static int miningAndDrops(ServerLevel level) {
        System.out.println(TAG + "⑤ mining tier and drops");
        int failed = 0;
        ItemStack diamond = new ItemStack(Items.DIAMOND_PICKAXE);
        ItemStack ironPick = new ItemStack(Items.IRON_PICKAXE);
        ItemStack stonePick = new ItemStack(Items.STONE_PICKAXE);
        BlockPos pos = new BlockPos(200, 220, 200);
        for (Block block : new Block[] {PotatoSTOres.TITANIUM_ORE.get(),
                PotatoSTOres.DEEPSLATE_TITANIUM_ORE.get()}) {
            BlockState state = block.defaultBlockState();
            String name = BuiltInRegistries.BLOCK.getKey(block).getPath();
            failed += check(name + ": in #minecraft:mineable/pickaxe", state.is(BlockTags.MINEABLE_WITH_PICKAXE));
            failed += check(name + ": in #minecraft:needs_iron_tool", state.is(BlockTags.NEEDS_IRON_TOOL));
            level.setBlock(pos, state, 3);
            List<ItemStack> got = Block.getDrops(state, level, pos, null, null, diamond);
            boolean dropsRaw = got.size() == 1 && got.get(0).getCount() == 1
                    && got.get(0).getItem() == PotatoSTOres.RAW_TITANIUM.get();
            failed += check(name + ": drops 1 raw_titanium (got " + describe(got) + ")", dropsRaw);
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
            failed += check(name + ": diamond/iron pickaxe OK, stone pickaxe NOT",
                    hasCorrectTool(state, diamond) && hasCorrectTool(state, ironPick)
                            && !hasCorrectTool(state, stonePick) && !hasCorrectTool(state, ItemStack.EMPTY));
        }
        return failed;
    }

    // ================= ⑥ 世界生成与标签 =================
    private static int worldgenAndTags(ServerLevel level) {
        System.out.println(TAG + "⑥ worldgen wiring and c: tags");
        int failed = 0;
        ResourceLocation placedId = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "ore_titanium_placed");
        var placedReg = level.registryAccess().registryOrThrow(Registries.PLACED_FEATURE);
        failed += check("configured+placed features loaded",
                level.registryAccess().registryOrThrow(Registries.CONFIGURED_FEATURE)
                        .containsKey(ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "ore_titanium"))
                        && placedReg.containsKey(placedId));
        if (placedReg.containsKey(placedId)) {
            Holder<PlacedFeature> target = placedReg.getHolderOrThrow(
                    ResourceKey.create(Registries.PLACED_FEATURE, placedId));
            Holder<Biome> biome = level.getBiome(EBF);
            var features = biome.value().getGenerationSettings().features();
            int step = GenerationStep.Decoration.UNDERGROUND_ORES.ordinal();
            failed += check("biome " + biome.unwrapKey().map(k -> k.location().toString()).orElse("?")
                            + " has it in UNDERGROUND_ORES", step < features.size() && features.get(step).contains(target));
        }
        TagKey<Item> ores = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "ores/titanium"));
        TagKey<Item> rawTag = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "raw_materials/titanium"));
        TagKey<Item> ingotTag = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "ingots/titanium"));
        failed += check("#c:ores/titanium has 2 entries (got " + countTag(ores) + ")", countTag(ores) == 2);
        failed += check("#c:raw_materials/titanium has 1 (got " + countTag(rawTag) + ")", countTag(rawTag) == 1);
        failed += check("#c:ingots/titanium has 1 (got " + countTag(ingotTag) + ")", countTag(ingotTag) == 1);
        failed += check("our raw titanium is in the tag",
                new ItemStack(PotatoSTOres.RAW_TITANIUM.get()).is(rawTag));
        failed += check("our titanium ingot is in the tag",
                new ItemStack(ModItems.TITANIUM_INGOT.get()).is(ingotTag));
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

    private static void setEnergy(Object be, int v) {
        try {
            var f = be.getClass().getDeclaredField("energy");
            f.setAccessible(true);
            f.setInt(be, v);
        } catch (Throwable t) {
            System.out.println(TAG + "  (setEnergy failed: " + t + ")");
        }
    }

    private static void build(ServerLevel level) {
        for (int y = 0; y < 3; y++) {
            for (int j = 0; j < 3; j++) {
                for (int i = 0; i < 3; i++) {
                    level.setBlock(ElectricBlastFurnaceStructure.offset(EBF, Direction.SOUTH, i, j, y),
                            ElectricBlastFurnaceStructure.blockFor(
                                    ElectricBlastFurnaceStructure.kindAt(i, j, y)).defaultBlockState(), 3);
                }
            }
        }
    }

    private static void clear(ServerLevel level) {
        for (BlockPos p : ElectricBlastFurnaceStructure.positions(EBF, Direction.SOUTH)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static void cleanup(ServerLevel level) {
        clear(level);
        level.setBlock(CRUSHER, Blocks.AIR.defaultBlockState(), 3);
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
