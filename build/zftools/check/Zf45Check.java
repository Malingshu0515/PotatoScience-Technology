package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF45 临时文件，验证完必须删）</b>：
 * 验这一批的四件事 —— 粉碎机两条新配方、高炉双输入、14 份配方 JSON、以及"消耗桶"那条的真相。
 *
 * <p><b>期望值全部照用户原话另写一遍</b>（§4.27）：下面出现的 60 / 400 / 10 / 70 / 800 / 16 / 4
 * 都是从用户那几行原文抄的，<b>不是</b>读被测常量得来的 —— 否则常量改了探针跟着改，等于没验。</p>
 */
public final class Zf45Check {

    private static final String TAG = "[ZF45] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(144, 220, 144);

    // ===== 规格（用户原话 → 数字，硬写）=====
    /** 「煤炭/木炭 3s 10fe/t产出一个碳粉」 */
    private static final int SPEC_COAL_TICKS = 3 * 20;
    private static final int SPEC_COAL_FE_T = 10;
    /** 「铁锭 20s 70fe/t 产出一个铁粉」 */
    private static final int SPEC_IRON_TICKS = 20 * 20;
    private static final int SPEC_IRON_FE_T = 70;
    /** 高炉一个槽位 10 秒、每件 800 FE（ZF43/ZF44） */
    private static final int SPEC_TICKS = 10 * 20;
    private static final int SPEC_FE_PER_ITEM = 800;

    private Zf45Check() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf45Check.class);
            System.out.println(TAG + "诊断钩子已注册（game 总线）");
        } catch (Throwable t) {
            System.out.println(TAG + "注册失败：" + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            ServerLevel level = event.getServer().overworld();
            failed += crusherTable();
            failed += pairTable();
            failed += pairSmeltCases(level);
            failed += recipeFiles(level);
            failed += bucketEvidence(level);
            failed += jeiData();
            clear(level);
        } catch (Throwable t) {
            System.out.println(TAG + "验算抛异常：" + t);
            t.printStackTrace();
            failed++;
        } finally {
            System.out.println(TAG + "结论：" + (failed == 0 ? "全部成立" : "**有 " + failed + " 项不符**"));
            System.out.println(TAG + "诊断结束，请求关服");
            event.getServer().halt(false);
        }
    }

    // ================= ① 粉碎机两条新配方（纯查表） =================
    private static int crusherTable() {
        System.out.println(TAG + "① 微型粉碎机新配方");
        int failed = 0;
        int p = failed;

        MicroCrusherRecipes.Crush coal = MicroCrusherRecipes.find(new ItemStack(Items.COAL));
        failed += check("煤炭 → 碳粉 ×1，60 tick，10 FE/t（实际 "
                        + describe(coal) + "）",
                coal != null && coal.result() == ModItems.CARBON.get()
                        && coal.countMin() == 1 && coal.countMax() == 1
                        && coal.durationTicks() == SPEC_COAL_TICKS
                        && coal.energyPerTick() == SPEC_COAL_FE_T);

        MicroCrusherRecipes.Crush charcoal = MicroCrusherRecipes.find(new ItemStack(Items.CHARCOAL));
        failed += check("木炭 → 碳粉 ×1（同一条配方：" + (charcoal == coal) + "）", charcoal == coal);

        MicroCrusherRecipes.Crush iron = MicroCrusherRecipes.find(new ItemStack(Items.IRON_INGOT));
        failed += check("铁锭 → 铁粉 ×1，400 tick，70 FE/t（实际 " + describe(iron) + "）",
                iron != null && iron.result() == ModItems.IRON_POWDER.get()
                        && iron.countMin() == 1 && iron.countMax() == 1
                        && iron.durationTicks() == SPEC_IRON_TICKS
                        && iron.energyPerTick() == SPEC_IRON_FE_T);

        // 标签路径是活的：两个标签里真的有东西（否则"别的 mod 也认"是句空话）
        failed += check("标签 #minecraft:coals 里有物品（" + countTag(ItemTags.COALS) + " 个）",
                countTag(ItemTags.COALS) >= 2);
        TagKey<Item> cIron = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("c", "ingots/iron"));
        failed += check("标签 #c:ingots/iron 里有物品（" + countTag(cIron) + " 个）", countTag(cIron) >= 1);

        // 反向：粉末自己不该有粉碎配方（否则会出现自循环）
        failed += check("反向：铁粉没有粉碎配方", MicroCrusherRecipes.find(new ItemStack(ModItems.IRON_POWDER.get())) == null);
        failed += check("反向：碳粉没有粉碎配方", MicroCrusherRecipes.find(new ItemStack(ModItems.CARBON.get())) == null);

        System.out.println(TAG + "  算总账：煤 1 个 = " + (SPEC_COAL_TICKS * SPEC_COAL_FE_T) + " FE；铁 1 个 = "
                + (SPEC_IRON_TICKS * SPEC_IRON_FE_T) + " FE（= 高炉一件的 "
                + (SPEC_IRON_TICKS * SPEC_IRON_FE_T / SPEC_FE_PER_ITEM) + " 倍）");
        return failed - p;
    }

    // ================= ② 高炉双输入（纯查表） =================
    private static int pairTable() {
        System.out.println(TAG + "② 电力高炉双输入配方表");
        int failed = 0;
        int p = failed;
        ItemStack iron = new ItemStack(ModItems.IRON_POWDER.get());
        ItemStack carbon = new ItemStack(ModItems.CARBON.get());
        ItemStack gravel = new ItemStack(Items.GRAVEL);

        BlastFurnaceRecipes.Pair steel = BlastFurnaceRecipes.findPair(iron, carbon);
        failed += check("铁粉 + 碳粉 → 高碳钢 ×1（实际 " + describePair(steel) + "）",
                steel != null && steel.output() == ModItems.HIGH_CARBON_STEEL.get() && steel.count() == 1);
        failed += check("左右互换照样成立", BlastFurnaceRecipes.findPair(carbon, iron) == steel);

        BlastFurnaceRecipes.Pair magnet = BlastFurnaceRecipes.findPair(iron, gravel);
        failed += check("铁粉 + 沙砾 → 磁铁 ×1（实际 " + describePair(magnet) + "）",
                magnet != null && magnet.output() == ModItems.MAGNET.get() && magnet.count() == 1);

        failed += check("反向：碳粉 + 沙砾 不配对", BlastFurnaceRecipes.findPair(carbon, gravel) == null);
        failed += check("反向：铁粉 + 铁粉 不配对", BlastFurnaceRecipes.findPair(iron, iron) == null);
        failed += check("反向：沙砾 + 沙砾 不配对", BlastFurnaceRecipes.findPair(gravel, gravel) == null);
        failed += check("反向：空槽不配对", BlastFurnaceRecipes.findPair(iron, ItemStack.EMPTY) == null);
        failed += check("配对表正好 2 条（实际 " + BlastFurnaceRecipes.pairCount() + "）",
                BlastFurnaceRecipes.pairCount() == 2);
        return failed - p;
    }

    // ================= ③ 高炉游戏内跑一遍 =================
    private static int pairSmeltCases(ServerLevel level) {
        System.out.println(TAG + "③ 电力高炉实机（配对熔炼）");
        int failed = 0;
        int p = failed;

        // (1) 1 铁粉 + 1 碳粉 → 1 高碳钢
        failed += smelt(level, "1+1 铁粉碳粉",
                new ItemStack(ModItems.IRON_POWDER.get(), 1), new ItemStack(ModItems.CARBON.get(), 1),
                ModItems.HIGH_CARBON_STEEL.get(), 1, SPEC_FE_PER_ITEM, 0, -1);

        // (2) 64 + 64 → 64 高碳钢（满载一批）
        failed += smelt(level, "64+64 铁粉碳粉",
                new ItemStack(ModItems.IRON_POWDER.get(), 64), new ItemStack(ModItems.CARBON.get(), 64),
                ModItems.HIGH_CARBON_STEEL.get(), 64, (long) 64 * SPEC_FE_PER_ITEM, 0, -1);

        // (3) 铁粉 + 沙砾 → 磁铁
        failed += smelt(level, "2+2 铁粉沙砾",
                new ItemStack(ModItems.IRON_POWDER.get(), 2), new ItemStack(Items.GRAVEL, 2),
                ModItems.MAGNET.get(), 2, 2L * SPEC_FE_PER_ITEM, 0, -1);

        // (4) 数量不等：一批 = min(两边) ⇒ 3 个磁铁，铁粉剩 5
        failed += smelt(level, "8 铁粉 + 3 沙砾（取小）",
                new ItemStack(ModItems.IRON_POWDER.get(), 8), new ItemStack(Items.GRAVEL, 3),
                ModItems.MAGNET.get(), 3, 3L * SPEC_FE_PER_ITEM, 5, 0);

        // (5) 换料必须清零：烤 100 tick 后把碳粉换成沙砾，进度不能带走
        clear(level);
        build(level, Direction.SOUTH);
        BlastFurnaceAssembly.form(level, C, Direction.SOUTH);
        if (level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m) {
            m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                    new ItemStack(ModItems.IRON_POWDER.get(), 8));
            m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + 1,
                    new ItemStack(ModItems.CARBON.get(), 8));
            for (int i = 0; i < 100; i++) {
                setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
                ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m);
            }
            int mid = m.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST);
            failed += check("烤 100 tick 后进度 = 100（实际 " + mid + "）", mid == 100);

            m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + 1,
                    new ItemStack(Items.GRAVEL, 8));
            setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m);
            int after = m.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST);
            failed += check("把碳粉换成沙砾后进度被打回 1（实际 " + after + "；不清零会是 101）", after == 1);

            int ticks = 1;
            for (int i = 0; i < SPEC_TICKS; i++) {
                setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
                ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m);
                ticks++;
                if (!outputEmpty(m)) {
                    break;
                }
            }
            int magnets = countOutput(m, ModItems.MAGNET.get());
            int steels = countOutput(m, ModItems.HIGH_CARBON_STEEL.get());
            failed += check("换料后跑满 200 tick 出 8 个磁铁、0 个高碳钢（实际 " + magnets + " / " + steels
                            + "，共 " + ticks + " tick）",
                    magnets == 8 && steels == 0);
        } else {
            failed += check("换料用例能拿到方块实体", false);
        }
        clear(level);
        return failed - p;
    }

    /**
     * 造一台高炉、投两个槽、喂满电跑到出产物。
     *
     * @param ironLeft  跑完后第一个槽应当剩几个（-1 = 不检查）
     * @param gravelLeft 跑完后第二个槽应当剩几个（-1 = 不检查）
     */
    private static int smelt(ServerLevel level, String name, ItemStack a, ItemStack b,
                             Item expect, int expectCount, long expectFe, int ironLeft, int gravelLeft) {
        clear(level);
        build(level, Direction.SOUTH);
        BlastFurnaceAssembly.form(level, C, Direction.SOUTH);
        if (!(level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m)) {
            return check(name + "：能拿到方块实体", false);
        }
        m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST, a);
        m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + 1, b);
        long spent = 0;
        int ticks = 0;
        for (int i = 0; i < SPEC_TICKS + 100; i++) {
            setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            int before = m.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m);
            spent += Math.max(0, before - m.getEnergyStored());
            ticks++;
            if (!outputEmpty(m)) {
                break;
            }
        }
        int got = countOutput(m, expect);
        int leftA = m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST).getCount();
        int leftB = m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + 1).getCount();
        System.out.println(TAG + "  " + name + "：跑了 " + ticks + " tick，花 " + spent + " FE，出 " + got
                + " 个，剩 " + leftA + " / " + leftB);
        int failed = 0;
        failed += check(name + "：恰好 " + SPEC_TICKS + " tick 出产物（实际 " + ticks + "）", ticks == SPEC_TICKS);
        failed += check(name + "：产出 " + expectCount + " 个（实际 " + got + "）", got == expectCount);
        failed += check(name + "：总耗电 " + expectFe + " FE（实际 " + spent + "）", spent == expectFe);
        if (ironLeft >= 0) {
            failed += check(name + "：第一个槽剩 " + ironLeft + "（实际 " + leftA + "）", leftA == ironLeft);
        }
        if (gravelLeft >= 0) {
            failed += check(name + "：第二个槽剩 " + gravelLeft + "（实际 " + leftB + "）", leftB == gravelLeft);
        }
        return failed;
    }

    // ================= ④ 14 份配方 JSON 真的加载进来了 =================
    /** {文件名, 产物 id, 数量} —— 照用户那张图纸硬写。 */
    private static final String[][] EXPECT_RECIPES = {
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
    };

    private static int recipeFiles(ServerLevel level) {
        System.out.println(TAG + "④ 14 份配方 JSON 的加载与产物");
        int failed = 0;
        int p = failed;
        for (String[] row : EXPECT_RECIPES) {
            ResourceLocation id = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, row[0]);
            var holder = level.getRecipeManager().byKey(id);
            if (holder.isEmpty()) {
                failed += check(row[0] + "：配方加载成功", false);
                continue;
            }
            RecipeHolder<?> h = holder.get();
            ItemStack out = h.value().getResultItem(level.registryAccess());
            String gotId = BuiltInRegistries.ITEM.getKey(out.getItem()).toString();
            failed += check(row[0] + " → " + row[1] + " x" + row[2] + "（实际 " + gotId + " x" + out.getCount() + "）",
                    gotId.equals(row[1]) && out.getCount() == Integer.parseInt(row[2]));
        }
        return failed - p;
    }

    // ================= ⑤ "消耗桶"到底成不成立（取证） =================
    private static int bucketEvidence(ServerLevel level) {
        System.out.println(TAG + "⑤ 液压机配方里的水桶会不会被消耗");
        int failed = 0;
        var holder = level.getRecipeManager()
                .byKey(ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "hydraulic_press"));
        if (holder.isEmpty() || !(holder.get().value() instanceof CraftingRecipe recipe)) {
            return check("液压机配方能拿到", false);
        }
        List<ItemStack> cells = new ArrayList<>();
        int waterBuckets = 0;
        for (Ingredient ing : recipe.getIngredients()) {
            ItemStack[] items = ing.getItems();
            ItemStack one = items.length == 0 ? ItemStack.EMPTY : items[0].copy();
            if (one.is(Items.WATER_BUCKET)) {
                waterBuckets++;
            }
            cells.add(one);
        }
        CraftingInput input = CraftingInput.of(3, 3, cells);
        NonNullList<ItemStack> remaining = recipe.getRemainingItems(input);
        int returned = 0;
        for (ItemStack s : remaining) {
            if (s.is(Items.BUCKET)) {
                returned++;
            }
        }
        System.out.println(TAG + "  配方里放了 " + waterBuckets + " 个水桶，合成后返还了 " + returned + " 个空桶");
        // ⚠ 第一版这里写的是"3 个水桶"，跑出来 2 —— 错的是我的期望值：
        //   用户图纸第二行是【水桶】【一般金属块】【水桶】，**只有 2 个**水桶。
        //   （这就是"期望值照规格另写一遍"的价值：它会抓错，但抓到的可能是我的算术。）
        failed += check("配方里确实是 2 个水桶（实际 " + waterBuckets + "）", waterBuckets == 2);
        // 这条是**如实记录现状**，不是"应该成立"：原版 JSON 无法取消物品自带的返还。
        // 探针把它写成"确实返还 2 个空桶"，就是为了让这条偏差有取证、不靠我嘴说。
        failed += check("现状：原版机制返还 2 个空桶（用户要的『消耗桶』做不到）", returned == 2);
        return failed;
    }

    // ================= ⑥ JEI 数据层 =================
    private static int jeiData() {
        System.out.println(TAG + "⑥ JEI 数据（MachineRecipes，不含 JEI 类型）");
        int failed = 0;
        int p = failed;
        int ebf = 0;
        int pairSteel = 0;
        int pairMagnet = 0;
        int crusherCarbon = 0;
        int crusherIron = 0;
        for (MachineRecipes.Entry e : MachineRecipes.all()) {
            if (e.machineId().equals("electric_blast_furnace")) {
                ebf++;
                // ⚠ 不能只数"输入有几格"：沙子那条也是 2 格（沙子 / 红沙 = 两种**任选其一**），
                //   而配对配方那两条是"两格都要"。所以要按**具体是哪两样**来认。
                if (e.itemIn().size() == 2) {
                    boolean iron = false;
                    boolean carbon = false;
                    boolean gravel = false;
                    for (ItemStack in : e.itemIn()) {
                        iron |= in.is(ModItems.IRON_POWDER.get());
                        carbon |= in.is(ModItems.CARBON.get());
                        gravel |= in.is(Items.GRAVEL);
                    }
                    if (iron && carbon) {
                        pairSteel++;
                    }
                    if (iron && gravel) {
                        pairMagnet++;
                    }
                }
            }
            if (e.machineId().equals("micro_crusher")) {
                for (ItemStack out : e.itemOut()) {
                    if (out.is(ModItems.CARBON.get())) {
                        crusherCarbon++;
                    }
                    if (out.is(ModItems.IRON_POWDER.get())) {
                        crusherIron++;
                    }
                }
            }
        }
        // 7 粗矿 + 14 矿石 + 1 沙子 + 2 配对 = 24
        failed += check("高炉分类共 24 条（实际 " + ebf + "）", ebf == 24);
        failed += check("JEI 里有『铁粉 + 碳粉』那条（" + pairSteel + " 条）", pairSteel == 1);
        failed += check("JEI 里有『铁粉 + 沙砾』那条（" + pairMagnet + " 条）", pairMagnet == 1);
        failed += check("粉碎机分类里有碳粉配方（" + crusherCarbon + " 条）", crusherCarbon >= 1);
        failed += check("粉碎机分类里有铁粉配方（" + crusherIron + " 条）", crusherIron >= 1);
        return failed - p;
    }

    // ================= 工具 =================
    private static boolean outputEmpty(ElectricBlastFurnaceBlockEntity m) {
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            if (!m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k).isEmpty()) {
                return false;
            }
        }
        return true;
    }

    private static int countOutput(ElectricBlastFurnaceBlockEntity m, Item item) {
        int n = 0;
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            ItemStack s = m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k);
            if (s.is(item)) {
                n += s.getCount();
            }
        }
        return n;
    }

    private static int countTag(TagKey<Item> tag) {
        int n = 0;
        for (Holder<Item> ignored : BuiltInRegistries.ITEM.getTagOrEmpty(tag)) {
            n++;
        }
        return n;
    }

    private static String describe(MicroCrusherRecipes.Crush c) {
        if (c == null) {
            return "没有配方";
        }
        return BuiltInRegistries.ITEM.getKey(c.result()) + " x" + c.countMin() + "，" + c.durationTicks()
                + " tick，" + c.energyPerTick() + " FE/t";
    }

    private static String describePair(BlastFurnaceRecipes.Pair p) {
        if (p == null) {
            return "没有配方";
        }
        return BuiltInRegistries.ITEM.getKey(p.output()) + " x" + p.count();
    }

    private static void setEnergy(ElectricBlastFurnaceBlockEntity m, int v) {
        try {
            var f = ElectricBlastFurnaceBlockEntity.class.getDeclaredField("energy");
            f.setAccessible(true);
            f.setInt(m, v);
        } catch (Throwable t) {
            System.out.println(TAG + "  （写电失败：" + t + "）");
        }
    }

    private static void build(ServerLevel level, Direction facing) {
        for (int y = 0; y < 3; y++) {
            for (int j = 0; j < 3; j++) {
                for (int i = 0; i < 3; i++) {
                    level.setBlock(ElectricBlastFurnaceStructure.offset(C, facing, i, j, y),
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
