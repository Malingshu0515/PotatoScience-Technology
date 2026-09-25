package com.potatost.mod;

import java.lang.reflect.Method;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.material.FlowingFluid;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF73). Delete after the run.
 *
 * <p>Probe for the 0.11 oil batch: crude oil fluid + liquid block + oil bucket + the two
 * whitelist cuts (gas gate / filling-machine container interface).</p>
 *
 * <p>Output is ASCII only on purpose (console codepage would mangle Chinese in the log).</p>
 */
public final class OilCheck {

    private static final String TAG = "[O73] ";
    private static boolean registered;
    private static int failed;

    private OilCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(OilCheck.class);
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
            checkFluid(level);
            checkBlock();
            checkGates();
            checkBucketItem();
            checkGasTankRejectsOil();
            checkScooping(level);
            checkFillingMachine();
            checkRecipe(level);
            checkLang();
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
    private static void checkFluid(ServerLevel level) {
        System.out.println(TAG + "(1) fluid registration / properties");
        Fluid oil = ModFluids.CRUDE_OIL.get();
        String id = BuiltInRegistries.FLUID.getKey(oil).toString();
        failed += check("crude oil fluid id = potato_s_t:crude_oil (got " + id + ")",
                id.equals("potato_s_t:crude_oil"));
        failed += check("crude oil != EMPTY", oil != Fluids.EMPTY);
        failed += check("source is a FlowingFluid", oil instanceof FlowingFluid);
        failed += check("flowing variant wired",
                oil instanceof FlowingFluid && ((FlowingFluid) oil).getFlowing() == ModFluids.FLOWING_CRUDE_OIL.get());
        failed += check("fluid type density = 800", oil.getFluidType().getDensity() == 800);
        failed += check("fluid type viscosity = 3000", oil.getFluidType().getViscosity() == 3000);
        failed += check("canHydrate = false (would wet farmland otherwise)",
                !oil.getFluidType().canHydrate(new FluidStack(oil, 1000)));
        FluidState source = oil.defaultFluidState();
        failed += check("NOT source-convertible (never infinite)",
                !oil.canConvertToSource(source, level, BlockPos.ZERO));
        failed += check("contrast: WATER IS source-convertible by default",
                Fluids.WATER.canConvertToSource(Fluids.WATER.defaultFluidState(), level, BlockPos.ZERO));
        failed += check("no bucket mapping (vanilla bucket must NOT pick it up)",
                oil.getBucket() == Items.AIR);
        // lava-like flow numbers (protected methods -> reflection)
        Integer tick = (Integer) call(oil, "getTickDelay", new Class<?>[]{net.minecraft.world.level.LevelReader.class}, level);
        Integer slope = (Integer) call(oil, "getSlopeFindDistance", new Class<?>[]{net.minecraft.world.level.LevelReader.class}, level);
        Integer drop = (Integer) call(oil, "getDropOff", new Class<?>[]{net.minecraft.world.level.LevelReader.class}, level);
        System.out.println(TAG + "    flow params: tickDelay=" + tick + " slopeFind=" + slope + " dropOff=" + drop);
        failed += check("tickDelay = 30 (lava)", tick != null && tick == 30);
        failed += check("slopeFindDistance = 2 (lava)", slope != null && slope == 2);
        failed += check("dropOff = 2 (lava)", drop != null && drop == 2);
    }

    private static void checkBlock() {
        System.out.println(TAG + "(2) liquid block");
        LiquidBlock block = ModBlocks.CRUDE_OIL.get();
        String id = BuiltInRegistries.BLOCK.getKey(block).toString();
        failed += check("block id = potato_s_t:crude_oil (got " + id + ")",
                id.equals("potato_s_t:crude_oil"));
        failed += check("block.fluid == crude oil source", block.fluid == ModFluids.CRUDE_OIL.get());
        FluidState state = block.defaultBlockState().getFluidState();
        failed += check("default state fluid = crude oil", state.getType() == ModFluids.CRUDE_OIL.get());
        failed += check("default state is a source block", state.isSource());
        failed += check("no BlockItem (cannot be placed by hand): asItem == AIR",
                block.asItem() == Items.AIR);
    }

    private static void checkGates() {
        System.out.println(TAG + "(3) positive whitelist (the ZF72 L1 mine)");
        failed += check("isGas(crude_oil) = false  <-- was TRUE before the fix",
                !ModFluids.isGas(ModFluids.CRUDE_OIL.get()));
        failed += check("isGas(flowing crude oil) = false",
                !ModFluids.isGas(ModFluids.FLOWING_CRUDE_OIL.get()));
        failed += check("isGas(oxygen) = true", ModFluids.isGas(ModFluids.OXYGEN.get()));
        failed += check("isGas(flowing hydrogen) = true",
                ModFluids.isGas(ModFluids.FLOWING_HYDROGEN.get()));
        failed += check("isGas(water) = false", !ModFluids.isGas(Fluids.WATER));
        failed += check("isGas(lava) = false", !ModFluids.isGas(Fluids.LAVA));
        failed += check("isLiquid(crude oil) = true", ModFluids.isLiquid(ModFluids.CRUDE_OIL.get()));
        failed += check("isLiquid(oxygen) = false", !ModFluids.isLiquid(ModFluids.OXYGEN.get()));
        failed += check("isLiquid(water) = true (decision 3: any liquid)",
                ModFluids.isLiquid(Fluids.WATER));
        failed += check("TankContents.isGas delegates (crude oil = false)",
                !TankContents.isGas(ModFluids.CRUDE_OIL.get()));
        failed += check("FillingMachine.isGasFluid delegates (crude oil = false)",
                !FillingMachineBlockEntity.isGasFluid(ModFluids.CRUDE_OIL.get()));
    }

    private static void checkBucketItem() {
        System.out.println(TAG + "(4) oil bucket item: 3000 mB, single fluid, no gas");
        ItemStack bucket = new ItemStack(ModItems.OIL_BUCKET.get());
        String id = BuiltInRegistries.ITEM.getKey(bucket.getItem()).toString();
        failed += check("item id = potato_s_t:oil_bucket (got " + id + ")",
                id.equals("potato_s_t:oil_bucket"));
        failed += check("not stackable", bucket.getMaxStackSize() == 1);
        failed += check("capacity = 3000", OilBucketContents.CAPACITY == 3000);
        failed += check("empty: amount 0 / space 3000 / isEmpty",
                OilBucketContents.amount(bucket) == 0 && OilBucketContents.space(bucket) == 3000
                        && OilBucketContents.isEmpty(bucket));

        int got = OilBucketContents.fill(bucket, new FluidStack(Fluids.WATER, 1000), 1000);
        failed += check("fill 1000 mB water -> 1000", got == 1000);
        failed += check("holds water now", OilBucketContents.fluid(bucket) == Fluids.WATER);
        failed += check("space = 2000", OilBucketContents.space(bucket) == 2000);

        int mixed = OilBucketContents.fill(bucket, new FluidStack(ModFluids.CRUDE_OIL.get(), 1000), 1000);
        failed += check("REJECT a different fluid (mixing) -> 0", mixed == 0);
        failed += check("still water, still 1000", OilBucketContents.fluid(bucket) == Fluids.WATER
                && OilBucketContents.amount(bucket) == 1000);

        ItemStack empty2 = new ItemStack(ModItems.OIL_BUCKET.get());
        int gas = OilBucketContents.fill(empty2, new FluidStack(ModFluids.OXYGEN.get(), 1000), 1000);
        failed += check("REJECT a gas (oxygen) -> 0", gas == 0);
        int gas2 = OilBucketContents.fill(empty2, new FluidStack(ModFluids.CHLORINE.get(), 500), 500);
        failed += check("REJECT chlorine -> 0", gas2 == 0);
        failed += check("empty bucket stayed empty", OilBucketContents.isEmpty(empty2));

        failed += check("fill 3000 crude oil -> 3000",
                OilBucketContents.fill(empty2, new FluidStack(ModFluids.CRUDE_OIL.get(), 3000), 3000) == 3000);
        failed += check("full: space 0", OilBucketContents.space(empty2) == 0);
        failed += check("full: further fill -> 0",
                OilBucketContents.fill(empty2, new FluidStack(ModFluids.CRUDE_OIL.get(), 100), 100) == 0);
        FluidStack drained = OilBucketContents.drain(empty2, 500);
        failed += check("drain 500 -> 500 mB of crude oil",
                drained.getAmount() == 500 && drained.getFluid() == ModFluids.CRUDE_OIL.get());
        failed += check("after drain amount = 2500", OilBucketContents.amount(empty2) == 2500);

        // white bar (same look as the gas tank)
        ItemStack bar = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketItem item = (OilBucketItem) bar.getItem();
        failed += check("bar hidden when empty", !item.isBarVisible(bar));
        OilBucketContents.fill(bar, new FluidStack(ModFluids.CRUDE_OIL.get(), 3000), 3000);
        failed += check("bar visible when filled", item.isBarVisible(bar));
        failed += check("bar width 13 at full", item.getBarWidth(bar) == 13);
        failed += check("bar colour white", item.getBarColor(bar) == 0xFFFFFF);

        // interface implementation (filling machine talks to this)
        failed += check("implements FluidContainerItem", item instanceof FluidContainerItem);
        failed += check("interface accepts(oil) = true", item.accepts(ModFluids.CRUDE_OIL.get()));
        failed += check("interface accepts(oxygen) = false", !item.accepts(ModFluids.OXYGEN.get()));
        failed += check("interface space() matches", item.space(bar) == 0);
    }

    private static void checkGasTankRejectsOil() {
        System.out.println(TAG + "(5) gas tank must refuse crude oil (user rule)");
        ItemStack tank = new ItemStack(ModItems.HIGH_PRESSURE_TANK.get());
        int moved = TankContents.fill(tank, new FluidStack(ModFluids.CRUDE_OIL.get(), 1000), 1000);
        failed += check("TankContents.fill(oil) -> 0", moved == 0);
        failed += check("tank still empty", TankContents.isEmpty(tank));
        int water = TankContents.fill(tank, new FluidStack(Fluids.WATER, 1000), 1000);
        failed += check("tank still refuses water too", water == 0);
        int oxy = TankContents.fill(tank, new FluidStack(ModFluids.OXYGEN.get(), 2000), 2000);
        failed += check("regression: oxygen still fills (2000)", oxy == 2000);
        int hyd = TankContents.fill(tank, new FluidStack(ModFluids.HYDROGEN.get(), 1000), 1000);
        failed += check("regression: mixing two gases still allowed (1000)", hyd == 1000);
        failed += check("regression: total 3000 of 3500", TankContents.total(tank) == 3000);
    }

    private static void checkScooping(ServerLevel level) {
        System.out.println(TAG + "(6) scooping from the world (1000 mB per source block)");
        BlockPos oilPos = new BlockPos(0, 120, 0);
        BlockPos waterPos = new BlockPos(4, 120, 0);
        BlockPos lavaPos = new BlockPos(8, 120, 0);
        level.setBlock(oilPos, ModBlocks.CRUDE_OIL.get().defaultBlockState(), 3);
        level.setBlock(waterPos, Blocks.WATER.defaultBlockState(), 3);
        level.setBlock(lavaPos, Blocks.LAVA.defaultBlockState(), 3);
        failed += check("placed crude oil source block",
                level.getFluidState(oilPos).getType() == ModFluids.CRUDE_OIL.get()
                        && level.getFluidState(oilPos).isSource());

        ItemStack bucket = new ItemStack(ModItems.OIL_BUCKET.get());
        int scooped = OilBucketItem.scoopAt(level, oilPos, bucket);
        failed += check("scoop oil -> 1000", scooped == 1000);
        failed += check("bucket holds crude oil 1000",
                OilBucketContents.fluid(bucket) == ModFluids.CRUDE_OIL.get()
                        && OilBucketContents.amount(bucket) == 1000);
        failed += check("source block is gone (not infinite)",
                level.getFluidState(oilPos).isEmpty());

        int again = OilBucketItem.scoopAt(level, oilPos, bucket);
        failed += check("scooping an empty spot -> 0", again == 0);

        failed += check("scooping a DIFFERENT fluid into an oil-filled bucket -> 0 (no mixing)",
                OilBucketItem.scoopAt(level, waterPos, bucket) == 0);
        failed += check("water source block STILL THERE after the refusal",
                level.getFluidState(waterPos).isSource());

        ItemStack waterBucket = new ItemStack(ModItems.OIL_BUCKET.get());
        int w = OilBucketItem.scoopAt(level, waterPos, waterBucket);
        failed += check("fresh bucket scoops water -> 1000", w == 1000);
        failed += check("bucket holds water", OilBucketContents.fluid(waterBucket) == Fluids.WATER);

        ItemStack lavaBucket = new ItemStack(ModItems.OIL_BUCKET.get());
        int l = OilBucketItem.scoopAt(level, lavaPos, lavaBucket);
        failed += check("fresh bucket scoops lava -> 1000", l == 1000);
        failed += check("bucket holds lava", OilBucketContents.fluid(lavaBucket) == Fluids.LAVA);

        // fill one bucket up to 3000 then prove the 4th scoop leaves the source alone
        ItemStack full = new ItemStack(ModItems.OIL_BUCKET.get());
        BlockPos p2 = new BlockPos(12, 120, 0);
        level.setBlock(p2, ModBlocks.CRUDE_OIL.get().defaultBlockState(), 3);
        int each = 0;
        for (int i = 0; i < 3; i++) {
            each += OilBucketItem.scoopAt(level, p2, full);
            level.setBlock(p2, ModBlocks.CRUDE_OIL.get().defaultBlockState(), 3);
        }
        failed += check("three scoops fill it (3000)", each == 3000);
        int fourth = OilBucketItem.scoopAt(level, p2, full);
        failed += check("4th scoop refused (full) -> 0", fourth == 0);
        failed += check("and the source block was NOT eaten (no free deletion)",
                level.getFluidState(p2).isSource());
    }

    private static void checkFillingMachine() {
        System.out.println(TAG + "(7) filling machine: any fluid in tanks, container decides");
        failed += check("acceptsAnyFluid(water) = true",
                FillingMachineBlockEntity.acceptsAnyFluid(new FluidStack(Fluids.WATER, 1)));
        failed += check("acceptsAnyFluid(empty) = false",
                !FillingMachineBlockEntity.acceptsAnyFluid(FluidStack.EMPTY));
        failed += check("tank count still 5", FillingMachineBlockEntity.TANK_COUNT == 5);
        failed += check("FILL_RATE still 5 / ENERGY_PER_TANK still 60",
                FillingMachineBlockEntity.FILL_RATE == 5
                        && FillingMachineBlockEntity.ENERGY_PER_TANK == 60);

        FillingMachineBlockEntity machine = new FillingMachineBlockEntity(
                BlockPos.ZERO, ModBlocks.FILLING_MACHINE.get().defaultBlockState());
        ItemStack oilBucket = new ItemStack(ModItems.OIL_BUCKET.get());
        ItemStack gasTank = new ItemStack(ModItems.HIGH_PRESSURE_TANK.get());
        failed += check("slot accepts the oil bucket",
                machine.getInventory().isItemValid(0, oilBucket));
        failed += check("slot still accepts the gas tank",
                machine.getInventory().isItemValid(0, gasTank));
        failed += check("slot refuses an unrelated item",
                !machine.getInventory().isItemValid(0, new ItemStack(Items.IRON_INGOT)));

        int tankFill = machine.getTank(2).fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 500),
                net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
        failed += check("machine tank ACCEPTS crude oil now (was gas-only) -> 500", tankFill == 500);

        int syncId = machine.getContainerData().get(FillingMachineBlockEntity.DATA_TANK_FLUID_0 + 2);
        failed += check("GUI sync id = fluid registry id (NOT 0, which used to mean 'empty') -> "
                        + syncId, syncId == BuiltInRegistries.FLUID.getId(ModFluids.CRUDE_OIL.get()));
        failed += check("client side can resolve it back (menu does exactly this)",
                BuiltInRegistries.FLUID.byId(syncId) == ModFluids.CRUDE_OIL.get());

        // slot 2 with an oil bucket + energy -> the machine's real fill path
        machine.getInventory().setStackInSlot(2, oilBucket);
        machine.getEnergyStorage().receiveEnergy(1000, false);
        boolean moved = (Boolean) callInstance(machine, "tryFillSlot",
                new Class<?>[]{int.class}, 2);
        ItemStack after = machine.getInventory().getStackInSlot(2);
        failed += check("tryFillSlot(oil bucket) actually moved fluid", moved);
        failed += check("bucket now holds 5 mB of crude oil",
                OilBucketContents.fluid(after) == ModFluids.CRUDE_OIL.get()
                        && OilBucketContents.amount(after) == 5);
        failed += check("tank drained to 495", machine.getTank(2).getFluidAmount() == 495);
        failed += check("energy charged 60 FE (940 left)",
                machine.getEnergyStorage().getEnergyStored() == 940);

        // and the gas tank in the same slot must NOT take oil
        FillingMachineBlockEntity m2 = new FillingMachineBlockEntity(
                BlockPos.ZERO, ModBlocks.FILLING_MACHINE.get().defaultBlockState());
        m2.getTank(0).fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 500),
                net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction.EXECUTE);
        m2.getInventory().setStackInSlot(0, new ItemStack(ModItems.HIGH_PRESSURE_TANK.get()));
        m2.getEnergyStorage().receiveEnergy(1000, false);
        boolean moved2 = (Boolean) callInstance(m2, "tryFillSlot", new Class<?>[]{int.class}, 0);
        failed += check("tryFillSlot(gas tank) refuses crude oil", !moved2);
        failed += check("tank kept its 500 mB", m2.getTank(0).getFluidAmount() == 500);
        failed += check("no energy was charged for the refused move",
                m2.getEnergyStorage().getEnergyStored() == 1000);
    }

    private static void checkRecipe(ServerLevel level) {
        System.out.println(TAG + "(8) recipe (2 iron buckets in, 1 oil bucket out)");
        ResourceLocation rid = ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "oil_bucket");
        failed += check("recipe exists in the manager",
                level.getRecipeManager().byKey(rid).isPresent());

        CraftingInput input = CraftingInput.of(3, 3, NonNullList.of(ItemStack.EMPTY,
                new ItemStack(Items.COPPER_INGOT), new ItemStack(Items.BUCKET), new ItemStack(Items.COPPER_INGOT),
                new ItemStack(ModItems.STEEL_PLATE.get()), new ItemStack(Items.BUCKET), new ItemStack(ModItems.STEEL_PLATE.get()),
                new ItemStack(ModItems.IRON_PLATE.get()), new ItemStack(ModItems.ALUMINUM_INGOT.get()), new ItemStack(ModItems.IRON_PLATE.get())));
        java.util.Optional<RecipeHolder<CraftingRecipe>> found =
                level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, level);
        failed += check("laid out exactly as the user wrote it -> a recipe matches", found.isPresent());
        if (found.isPresent()) {
            ItemStack out = found.get().value().assemble(input, level.registryAccess());
            String oid = BuiltInRegistries.ITEM.getKey(out.getItem()).toString();
            failed += check("output = 1 x potato_s_t:oil_bucket (got " + out.getCount() + " x " + oid + ")",
                    out.getCount() == 1 && oid.equals("potato_s_t:oil_bucket"));
        }
        // negative control: swap the aluminium ingot away
        CraftingInput bad = CraftingInput.of(3, 3, NonNullList.of(ItemStack.EMPTY,
                new ItemStack(Items.COPPER_INGOT), new ItemStack(Items.BUCKET), new ItemStack(Items.COPPER_INGOT),
                new ItemStack(ModItems.STEEL_PLATE.get()), new ItemStack(Items.BUCKET), new ItemStack(ModItems.STEEL_PLATE.get()),
                new ItemStack(ModItems.IRON_PLATE.get()), new ItemStack(Items.IRON_INGOT), new ItemStack(ModItems.IRON_PLATE.get())));
        java.util.Optional<RecipeHolder<CraftingRecipe>> badHit =
                level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, bad, level);
        boolean badGivesOil = badHit.isPresent() && badHit.get().value().assemble(bad, level.registryAccess())
                .getItem() == ModItems.OIL_BUCKET.get();
        failed += check("negative control: iron ingot instead of aluminium -> no oil bucket", !badGivesOil);

        // only one bucket is consumed per craft: the recipe really needs TWO buckets in the grid
        CraftingInput oneBucket = CraftingInput.of(3, 3, NonNullList.of(ItemStack.EMPTY,
                new ItemStack(Items.COPPER_INGOT), ItemStack.EMPTY, new ItemStack(Items.COPPER_INGOT),
                new ItemStack(ModItems.STEEL_PLATE.get()), new ItemStack(Items.BUCKET), new ItemStack(ModItems.STEEL_PLATE.get()),
                new ItemStack(ModItems.IRON_PLATE.get()), new ItemStack(ModItems.ALUMINUM_INGOT.get()), new ItemStack(ModItems.IRON_PLATE.get())));
        java.util.Optional<RecipeHolder<CraftingRecipe>> oneHit =
                level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, oneBucket, level);
        boolean oneGivesOil = oneHit.isPresent() && oneHit.get().value().assemble(oneBucket, level.registryAccess())
                .getItem() == ModItems.OIL_BUCKET.get();
        failed += check("negative control: only ONE bucket in the grid -> no oil bucket", !oneGivesOil);
    }

    private static void checkLang() {
        System.out.println(TAG + "(9) lang keys resolve (server side = en_us)");
        String[][] keys = {
                {"item.potato_s_t.oil_bucket", "Oil Bucket"},
                {"fluid_type.potato_s_t.crude_oil", "Crude Oil"},
                {"block.potato_s_t.crude_oil", "Crude Oil"},
        };
        for (String[] pair : keys) {
            String got = Component.translatable(pair[0]).getString();
            failed += check(pair[0] + " -> " + got, got.equals(pair[1]));
        }
        String rule = Component.translatable("tooltip.potato_s_t.oil_bucket.rule").getString();
        failed += check("tooltip rule key resolves (got: " + rule + ")",
                !rule.equals("tooltip.potato_s_t.oil_bucket.rule"));
    }

    // ============================================================
    private static Object call(Object target, String name, Class<?>[] types, Object... args) {
        try {
            Method m = target.getClass().getMethod(name, types);
            return m.invoke(target, args);
        } catch (NoSuchMethodException e) {
            return callDeclared(target, name, types, args);
        } catch (Throwable t) {
            System.out.println(TAG + "call " + name + " failed: " + t);
            return null;
        }
    }

    private static Object callDeclared(Object target, String name, Class<?>[] types, Object... args) {
        Class<?> c = target.getClass();
        while (c != null) {
            try {
                Method m = c.getDeclaredMethod(name, types);
                m.setAccessible(true);
                return m.invoke(target, args);
            } catch (NoSuchMethodException e) {
                c = c.getSuperclass();
            } catch (Throwable t) {
                System.out.println(TAG + "declared call " + name + " failed: " + t);
                return null;
            }
        }
        System.out.println(TAG + "method not found: " + name);
        return null;
    }

    private static Object callInstance(Object target, String name, Class<?>[] types, Object... args) {
        return callDeclared(target, name, types, args);
    }

    private static int check(String what, boolean ok) {
        System.out.println(TAG + (ok ? "[OK]   " : "[FAIL] ") + what);
        return ok ? 0 : 1;
    }
}
