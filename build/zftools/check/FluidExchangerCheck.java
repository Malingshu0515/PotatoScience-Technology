package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BucketPickup;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF82). Delete after the run.
 *
 * <p>验两件（用户原话）：</p>
 * <ol>
 *   <li><b>柴油桶 / 汽油桶</b>：流体有官方桶（{@code fluid.getBucket()}）、液体方块是
 *       {@link BucketPickup}（原版空桶能舀），且原油**仍然**没有桶（ZF73 的老规矩不许被带坏）；</li>
 *   <li><b>容器换流器</b>：3 秒 / 1000 mB，把右槽空桶换成那种流体的桶；没桶形式的流体拒绝、
 *       气体拒绝、量不够拒绝、右槽不是"刚好 1 个空桶"拒绝；泵接口抽的**就是左槽那件容器**
 *       （SIMULATE 不消耗、EXECUTE 真扣），气体也能抽。</li>
 * </ol>
 */
public final class FluidExchangerCheck {

    private static final String TAG = "[F82] ";
    private static final BlockPos ORIGIN = new BlockPos(440, 120, 440);
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf82_probe.txt";
    private static final StringBuilder REPORT = new StringBuilder();

    private static boolean registered;
    private static int passed;
    private static int failed;

    private FluidExchangerCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(FluidExchangerCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            checkBuckets(level);
            checkExchange(level);
            checkPumpOut(level);
            checkRecipe(level);
        } catch (Throwable t) {
            t.printStackTrace();
            log("EXCEPTION: " + t);
            failed++;
        }
        log("==== passed=" + passed + " failed=" + failed + " ====");
        flushReport();
        event.getServer().halt(false);
    }

    // ================= 工具 =================

    private static void log(String line) {
        System.out.println(TAG + line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.Writer w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write(REPORT.toString());
        } catch (Throwable t) {
            System.out.println(TAG + "report write failed: " + t);
        }
    }

    private static void ok(String label, boolean cond) {
        if (cond) {
            passed++;
            log("  [OK]   " + label);
        } else {
            failed++;
            log("  [FAIL] " + label);
        }
    }

    private static void eq(String label, long expected, long actual) {
        ok(label + "（期望 " + expected + "，实际 " + actual + "）", expected == actual);
    }

    // ================= ① 柴油桶 / 汽油桶 =================

    private static void checkBuckets(ServerLevel level) {
        ok("柴油的官方桶 = potato_s_t:diesel_bucket",
                ModFluids.DIESEL.get().getBucket() == ModItems.DIESEL_BUCKET.get());
        ok("汽油的官方桶 = potato_s_t:gasoline_bucket",
                ModFluids.GASOLINE.get().getBucket() == ModItems.GASOLINE_BUCKET.get());
        ok("流动变体也有桶（泵抽出来的流动柴油照样能装桶）",
                ModFluids.FLOWING_DIESEL.get().getBucket() == ModItems.DIESEL_BUCKET.get()
                        && ModFluids.FLOWING_GASOLINE.get().getBucket() == ModItems.GASOLINE_BUCKET.get());
        ok("两个桶都是原版 BucketItem（放置/舀取/返空桶全走原版那一套）",
                ModItems.DIESEL_BUCKET.get() instanceof net.minecraft.world.item.BucketItem
                        && ModItems.GASOLINE_BUCKET.get() instanceof net.minecraft.world.item.BucketItem);
        ok("柴油方块 / 汽油方块都是 BucketPickup（原版空桶右键能舀起来）",
                ModBlocks.DIESEL.get() instanceof BucketPickup
                        && ModBlocks.GASOLINE.get() instanceof BucketPickup);
        ok("柴油源方块的 LEVEL = 0（pickupBlock 只在 level 0 才给桶）",
                ModBlocks.DIESEL.get().defaultBlockState()
                        .getValue(net.minecraft.world.level.block.LiquidBlock.LEVEL) == 0);
        ok("桶放出来的是本模组的柴油方块（createLegacyBlock 指向 ModBlocks.DIESEL）",
                ModFluids.DIESEL.get().defaultFluidState().createLegacyBlock()
                        .is(ModBlocks.DIESEL.get()));
        // ★ 回归：原油仍然没有桶（ZF73 的规矩：一个原版空桶 = 一整桶 3000 mB 会白送三倍）
        ok("原油**仍然没有**官方桶（ZF73 老规矩不许被带坏）",
                ModFluids.CRUDE_OIL.get().getBucket() == Items.AIR);
        ok("石脑油 / 液化石油气也仍然没有桶（用户只点了柴油与汽油）",
                ModFluids.NAPHTHA.get().getBucket() == Items.AIR
                        && ModFluids.LPG.get().getBucket() == Items.AIR);
        // 世界上真有源方块、且它是可舀的（真放一格再读状态）
        BlockPos pos = ORIGIN.offset(6, 0, 0);
        level.setBlock(pos, ModBlocks.DIESEL.get().defaultBlockState(), 3);
        ok("世界里放下的柴油是**源**流体",
                level.getFluidState(pos).isSource()
                        && level.getFluidState(pos).getType() == ModFluids.DIESEL.get());
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ② 换桶 =================

    private static FluidExchangerBlockEntity place(ServerLevel level, int dz) {
        BlockPos pos = ORIGIN.offset(0, 0, dz);
        level.setBlock(pos, ModBlocks.FLUID_EXCHANGER.get().defaultBlockState(), 3);
        return level.getBlockEntity(pos) instanceof FluidExchangerBlockEntity be ? be : null;
    }

    private static void tick(ServerLevel level, int dz) {
        BlockPos pos = ORIGIN.offset(0, 0, dz);
        BlockState state = level.getBlockState(pos);
        if (level.getBlockEntity(pos) instanceof FluidExchangerBlockEntity be) {
            FluidExchangerBlockEntity.tick(level, pos, state, be);
        }
    }

    /** 造一个装了 {@code amount} mB 某种流体的油桶。 */
    private static ItemStack oilBucketWith(net.minecraft.world.level.material.Fluid fluid, int amount) {
        ItemStack stack = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(stack, new FluidStack(fluid, amount), amount);
        return stack;
    }

    private static void checkExchange(ServerLevel level) {
        // ① 柴油：3 秒 / 1000 mB ⇒ 右槽空桶变成柴油桶
        FluidExchangerBlockEntity be = place(level, 0);
        if (be == null) {
            ok("换流器方块实体建出来了", false);
            return;
        }
        be.getInventory().setStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT,
                oilBucketWith(ModFluids.DIESEL.get(), 3000));
        be.getInventory().setStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT, new ItemStack(Items.BUCKET));
        // 逐 tick 轨迹（把"到底第几 tick 结算"钉死，免得靠猜）
        StringBuilder trace = new StringBuilder();
        int progAt59 = -1;
        int leftAt59 = -1;
        int progAt60 = -1;
        int leftAt60 = -1;
        for (int i = 0; i < 62; i++) {
            tick(level, 0);
            int left = OilBucketContents.amount(
                    be.getInventory().getStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT));
            int prog = be.getContainerData().get(FluidExchangerBlockEntity.DATA_PROGRESS);
            if (i == 58) {
                progAt59 = prog;
                leftAt59 = left;
            }
            if (i == 59) {
                progAt60 = prog;
                leftAt60 = left;
            }
            if (i < 3 || i >= 57) {
                trace.append("t").append(i + 1).append("=进度").append(prog).append("/左").append(left).append("  ");
            }
        }
        log("  诊断轨迹：" + trace);
        eq("第 59 tick：进度 59 / 60（还没到点）", 59, progAt59);
        eq("第 59 tick：左槽还是 3000 mB（一次都没扣）", 3000, leftAt59);
        eq("第 60 tick：进度归零（当 tick 结算）", 0, progAt60);
        eq("第 60 tick：一次正好扣 1000 mB（剩 2000）", 2000, leftAt60);
        ItemStack out = be.getInventory().getStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT);
        ok("第 60 tick：右槽变成柴油桶", out.is(ModItems.DIESEL_BUCKET.get()));
        eq("一次正好扣 1000 mB（剩 2000）", 2000,
                OilBucketContents.amount(be.getInventory().getStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT)));
        eq("进度归零，接着还能换下一桶", 0,
                be.getContainerData().get(FluidExchangerBlockEntity.DATA_PROGRESS));

        // ② 水 ⇒ 原版水桶
        FluidExchangerBlockEntity water = place(level, 4);
        water.getInventory().setStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT,
                oilBucketWith(Fluids.WATER, 1000));
        water.getInventory().setStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT, new ItemStack(Items.BUCKET));
        for (int i = 0; i < 60; i++) {
            tick(level, 4);
        }
        ok("水 ⇒ 原版水桶（原版流体也走同一条路）",
                water.getInventory().getStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT)
                        .is(Items.WATER_BUCKET));
        ok("水桶换完，左槽油桶空了",
                OilBucketContents.amount(water.getInventory().getStackInSlot(
                        FluidExchangerBlockEntity.LEFT_SLOT)) == 0);

        // ③ 原油：没有桶形式 ⇒ 拒绝，一滴不动（用户：「前提是流体有对应桶的形式」）
        FluidExchangerBlockEntity crude = place(level, 8);
        crude.getInventory().setStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT,
                oilBucketWith(ModFluids.CRUDE_OIL.get(), 3000));
        crude.getInventory().setStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT, new ItemStack(Items.BUCKET));
        for (int i = 0; i < 70; i++) {
            tick(level, 8);
        }
        eq("原油：状态 = 这种流体没有桶", FluidExchangerBlockEntity.STATUS_NO_BUCKET,
                crude.getContainerData().get(FluidExchangerBlockEntity.DATA_STATUS));
        eq("原油：一滴没被扣", 3000,
                OilBucketContents.amount(crude.getInventory().getStackInSlot(
                        FluidExchangerBlockEntity.LEFT_SLOT)));
        ok("原油：右槽还是那个空桶",
                crude.getInventory().getStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT).is(Items.BUCKET));

        // ④ 高压气罐（气体）⇒ 界面拒绝，请接泵（用户：「高压气罐必须接泵泵出」）
        FluidExchangerBlockEntity gas = place(level, 12);
        ItemStack tank = new ItemStack(ModItems.HIGH_PRESSURE_TANK.get());
        TankContents.fill(tank, new FluidStack(ModFluids.OXYGEN.get(), 3500), 3500);
        gas.getInventory().setStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT, tank);
        gas.getInventory().setStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT, new ItemStack(Items.BUCKET));
        for (int i = 0; i < 70; i++) {
            tick(level, 12);
        }
        eq("气罐：状态 = 左槽是气体（请接泵）", FluidExchangerBlockEntity.STATUS_GAS,
                gas.getContainerData().get(FluidExchangerBlockEntity.DATA_STATUS));
        eq("气罐：氧气一点没少", 3500,
                TankContents.total(gas.getInventory().getStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT)));

        // ⑤ 量不够 1000 mB ⇒ 等（进度保留），够了一次都不用等
        FluidExchangerBlockEntity small = place(level, 16);
        small.getInventory().setStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT,
                oilBucketWith(ModFluids.DIESEL.get(), 900));
        small.getInventory().setStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT, new ItemStack(Items.BUCKET));
        for (int i = 0; i < 70; i++) {
            tick(level, 16);
        }
        eq("只有 900 mB：状态 = 液体不够", FluidExchangerBlockEntity.STATUS_MATERIAL,
                small.getContainerData().get(FluidExchangerBlockEntity.DATA_STATUS));
        ok("只有 900 mB：右槽还是空桶",
                small.getInventory().getStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT).is(Items.BUCKET));

        // ⑥ 右槽不是"刚好 1 个空桶" ⇒ 拒绝
        FluidExchangerBlockEntity many = place(level, 20);
        many.getInventory().setStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT,
                oilBucketWith(ModFluids.DIESEL.get(), 3000));
        many.getInventory().setStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT,
                new ItemStack(Items.BUCKET, 2));
        for (int i = 0; i < 70; i++) {
            tick(level, 20);
        }
        eq("右槽 2 个空桶：状态 = 右槽不可用", FluidExchangerBlockEntity.STATUS_OUTPUT_FULL,
                many.getContainerData().get(FluidExchangerBlockEntity.DATA_STATUS));
        eq("右槽 2 个空桶：左槽一滴没扣", 3000,
                OilBucketContents.amount(many.getInventory().getStackInSlot(
                        FluidExchangerBlockEntity.LEFT_SLOT)));

        // ⑦ 左槽空 ⇒ 状态"空"
        FluidExchangerBlockEntity blank = place(level, 24);
        blank.getInventory().setStackInSlot(FluidExchangerBlockEntity.RIGHT_SLOT, new ItemStack(Items.BUCKET));
        for (int i = 0; i < 5; i++) {
            tick(level, 24);
        }
        eq("左槽空：状态 = 空", FluidExchangerBlockEntity.STATUS_EMPTY,
                blank.getContainerData().get(FluidExchangerBlockEntity.DATA_STATUS));
    }

    // ================= ③ 泵接口：直接抽左槽那件容器 =================

    private static void checkPumpOut(ServerLevel level) {
        FluidExchangerBlockEntity be = place(level, 28);
        IFluidHandler handler = be.getFluidHandler();
        be.getInventory().setStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT,
                oilBucketWith(ModFluids.GASOLINE.get(), 3000));
        eq("泵接口：罐里就是左槽那件东西里的流体（3000 mB）", 3000,
                handler.getFluidInTank(0).getAmount());
        eq("泵接口：容量报的是容器容量（油桶 3000）", 3000, handler.getTankCapacity(0));
        ok("泵接口：报的流体种类对得上",
                handler.getFluidInTank(0).getFluid() == ModFluids.GASOLINE.get());
        eq("泵接口：只出不进（fill 恒 0）", 0,
                handler.fill(new FluidStack(ModFluids.DIESEL.get(), 1000),
                        IFluidHandler.FluidAction.EXECUTE));
        FluidStack sim = handler.drain(800, IFluidHandler.FluidAction.SIMULATE);
        eq("SIMULATE：说能抽 800", 800, sim.getAmount());
        eq("SIMULATE 之后容器一点没少（还是 3000）", 3000,
                OilBucketContents.amount(be.getInventory().getStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT)));
        FluidStack real = handler.drain(800, IFluidHandler.FluidAction.EXECUTE);
        eq("EXECUTE：真抽到 800", 800, real.getAmount());
        ok("EXECUTE：抽到的是汽油", real.getFluid() == ModFluids.GASOLINE.get());
        eq("EXECUTE 之后容器少了 800（剩 2200）", 2200,
                OilBucketContents.amount(be.getInventory().getStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT)));
        // 指定流体版本的 drain：异种不抽
        eq("指名要柴油 ⇒ 一滴不抽", 0,
                handler.drain(new FluidStack(ModFluids.DIESEL.get(), 500),
                        IFluidHandler.FluidAction.EXECUTE).getAmount());
        eq("指名要汽油 ⇒ 照抽", 500,
                handler.drain(new FluidStack(ModFluids.GASOLINE.get(), 500),
                        IFluidHandler.FluidAction.EXECUTE).getAmount());

        // 气体也走泵（用户：「高压气罐必须接泵泵出」）
        FluidExchangerBlockEntity gas = place(level, 32);
        ItemStack tank = new ItemStack(ModItems.HIGH_PRESSURE_TANK.get());
        TankContents.fill(tank, new FluidStack(ModFluids.OXYGEN.get(), 2000), 2000);
        gas.getInventory().setStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT, tank);
        FluidStack got = gas.getFluidHandler().drain(1200, IFluidHandler.FluidAction.EXECUTE);
        eq("气罐走泵：抽到 1200 氧气", 1200, got.getAmount());
        ok("气罐走泵：流体种类是氧气", got.getFluid() == ModFluids.OXYGEN.get());
        eq("气罐走泵：罐里剩 800", 800,
                TankContents.total(gas.getInventory().getStackInSlot(FluidExchangerBlockEntity.LEFT_SLOT)));
        eq("左槽没容器时：泵抽不到东西", 0,
                place(level, 36).getFluidHandler().drain(100, IFluidHandler.FluidAction.EXECUTE).getAmount());
    }

    // ================= ④ 合成配方（用户给的三行） =================

    private static void checkRecipe(ServerLevel level) {
        NonNullList<ItemStack> grid = NonNullList.withSize(9, ItemStack.EMPTY);
        grid.set(1, new ItemStack(ModBlocks.COMMON_METAL_BLOCK_ITEM.get()));
        grid.set(3, new ItemStack(ModItems.IRON_PLATE.get()));
        grid.set(4, new ItemStack(ModItems.OIL_BUCKET.get()));
        grid.set(5, new ItemStack(ModItems.IRON_PLATE.get()));
        grid.set(6, new ItemStack(ModBlocks.FLUID_PIPE_ITEM.get()));
        grid.set(7, new ItemStack(ModItems.HIGH_PRESSURE_TANK.get()));
        grid.set(8, new ItemStack(ModBlocks.FLUID_PIPE_ITEM.get()));
        CraftingInput input = CraftingInput.of(3, 3, grid);
        var found = level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, level);
        ok("用户的九宫格配方认得出（【】【一般金属块】【】/【铁板】【油桶】【铁板】/【流体管道】【高压气罐】【流体管道】）",
                found.isPresent());
        if (found.isPresent()) {
            RecipeHolder<CraftingRecipe> holder = found.get();
            ItemStack result = holder.value().getResultItem(level.registryAccess());
            ok("产物 = 容器换流器",
                    result.is(ModBlocks.FLUID_EXCHANGER_ITEM.get()));
            eq("产物 1 个", 1, result.getCount());
            ok("配方 id = potato_s_t:fluid_exchanger",
                    holder.id().equals(ResourceLocation.fromNamespaceAndPath(
                            PotatoST.MODID, "fluid_exchanger")));
        }
    }
}
