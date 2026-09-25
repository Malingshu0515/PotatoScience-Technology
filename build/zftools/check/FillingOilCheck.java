package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF80). Delete after the run.
 *
 * <p>用户实测：「灌装机不往油桶灌液体」。本探针把整条链逐环验一遍，找出到底哪一环断了：</p>
 * <ol>
 *   <li>接口：油桶 / 气罐是不是都算 {@link FluidContainerItem}；</li>
 *   <li>罐子收不收原油（泵/管道路径 = {@code getFluidHandler().fill}）；</li>
 *   <li>菜单那道门（手放）收不收油桶；</li>
 *   <li>机器核心：罐里有原油 + 有电 + 槽里空油桶 ⇒ 到底灌不灌；</li>
 *   <li>反向：气体不能进油桶、液体不能进气罐（回归）。</li>
 * </ol>
 */
public final class FillingOilCheck {

    private static final String TAG = "[F80] ";
    private static final BlockPos ORIGIN = new BlockPos(360, 120, 360);
    /** 管道试验场：原油池 → 泵 → 灌装机（复刻用户的接法） */
    private static final BlockPos RIG = new BlockPos(400, 120, 400);
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf80_probe.txt";
    private static final StringBuilder REPORT = new StringBuilder();

    private static boolean registered;
    private static int passed;
    private static int failed;

    private FillingOilCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(FillingOilCheck.class);
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
            checkInterface();
            checkMenuGate(level);
            checkCoreOil(level);
            checkCoreWater(level);
            checkAllProducts(level);
            checkNoPower(level);
            checkGasIntoBucket(level);
            checkOilIntoGasTank(level);
            checkGasTankStillWorks(level);
            checkPipeFeed(level);
            checkPour(level);
            checkDiagnosis(level);
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

    /** 枚举/对象的相等断言（枚举不能传给 long 版的 eq）。 */
    private static void eqEnum(String label, Object expected, Object actual) {
        ok(label + "（期望 " + expected + "，实际 " + actual + "）",
                java.util.Objects.equals(expected, actual));
    }

    private static void eq(String label, long expected, long actual) {
        ok(label + "（期望 " + expected + "，实际 " + actual + "）", expected == actual);
    }

    // ================= ① 接口 =================

    private static void checkInterface() {
        Object bucket = ModItems.OIL_BUCKET.get();
        Object tank = ModItems.HIGH_PRESSURE_TANK.get();
        ok("油桶 implements FluidContainerItem", bucket instanceof FluidContainerItem);
        ok("气罐 implements FluidContainerItem", tank instanceof FluidContainerItem);
        ok("原油算液体（油桶肯收）", ModFluids.isLiquid(ModFluids.CRUDE_OIL.get()));
        ok("氧气算气体（油桶拒收）", ModFluids.isGas(ModFluids.OXYGEN.get()));
        ok("水算液体", ModFluids.isLiquid(net.minecraft.world.level.material.Fluids.WATER));

        // 纯物品逻辑先跑一遍（不碰世界）
        ItemStack b = new ItemStack(ModItems.OIL_BUCKET.get());
        eq("（纯物品）空桶空间 = 3000", 3000, OilBucketContents.space(b));
        eq("（纯物品）直接灌 5 mB 原油", 5,
                OilBucketContents.fill(b, new FluidStack(ModFluids.CRUDE_OIL.get(), 5), 5));
        eq("（纯物品）灌完桶里 5 mB", 5, OilBucketContents.amount(b));
        ItemStack b2 = new ItemStack(ModItems.OIL_BUCKET.get());
        eq("（纯物品）油桶拒收氧气", 0,
                OilBucketContents.fill(b2, new FluidStack(ModFluids.OXYGEN.get(), 5), 5));
    }

    // ================= ② 菜单那道门（手放） =================

    private static void checkMenuGate(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(0, 0, 8);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了", false);
            return;
        }
        FillingMachineMenu menu;
        try {
            menu = new FillingMachineMenu(0, new Inventory(null), be);
        } catch (Throwable t) {
            log("  [SKIP] 菜单构造失败（不能在无玩家环境建菜单）: " + t);
            return;
        }
        ok("菜单槽位0 收油桶（手放那道门）",
                menu.slots.get(0).mayPlace(new ItemStack(ModItems.OIL_BUCKET.get())));
        ok("菜单槽位0 收气罐", menu.slots.get(0).mayPlace(new ItemStack(ModItems.HIGH_PRESSURE_TANK.get())));
        ok("菜单槽位0 不收泥土", !menu.slots.get(0).mayPlace(new ItemStack(Items.DIRT)));
        eq("方块实体侧也给油桶放行（Shift 快移口径）", 1,
                be.getInventory().isItemValid(0, new ItemStack(ModItems.OIL_BUCKET.get())) ? 1 : 0);
    }

    // ================= ③ 核心：原油 → 油桶 =================

    private static void checkCoreOil(ServerLevel level) {
        BlockPos pos = ORIGIN;
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了", false);
            return;
        }
        var inv = be.getInventory();
        var data = be.getContainerData();
        IFluidHandler handler = be.getFluidHandler();
        IEnergyStorage energy = be.getEnergyStorage();

        int accepted = handler.fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        eq("泵/管道往罐0灌原油：5000 全收", 5000, accepted);
        eq("罐0 里就是 5000 原油", 5000, be.getTank(0).getFluidAmount());
        ok("罐0 里那种流体是原油", be.getTank(0).getFluid().getFluid() == ModFluids.CRUDE_OIL.get());
        eq("界面数据槽里的流体 id = 原油注册表 id",
                net.minecraft.core.registries.BuiltInRegistries.FLUID.getId(ModFluids.CRUDE_OIL.get()),
                data.get(FillingMachineBlockEntity.DATA_TANK_FLUID_0));

        energy.receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        eq("（准备）电灌满 3000", 3000, data.get(FillingMachineBlockEntity.DATA_ENERGY));

        inv.setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
        tick(level, pos);
        int after1 = OilBucketContents.amount(inv.getStackInSlot(0));
        log("  诊断：1 tick 后桶里 = " + after1 + " mB，罐0 = "
                + be.getTank(0).getFluidAmount() + " mB，电 = "
                + data.get(FillingMachineBlockEntity.DATA_ENERGY));
        eq("1 tick 灌进 5 mB（FILL_RATE）", FillingMachineBlockEntity.FILL_RATE, after1);
        eq("罐0 相应少 5 mB", 4995, be.getTank(0).getFluidAmount());
        eq("扣 60 FE（ENERGY_PER_TANK）", 2940, data.get(FillingMachineBlockEntity.DATA_ENERGY));

        // 连跑到桶满：桶 3000 = 600 tick；之后罐里应剩 2000
        for (int i = 0; i < 599; i++) {
            energy.receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
            tick(level, pos);
        }
        eq("跑满 600 tick：桶满 3000", 3000, OilBucketContents.amount(inv.getStackInSlot(0)));
        eq("罐0 剩 2000", 2000, be.getTank(0).getFluidAmount());
        ok("桶里那种流体还是原油",
                OilBucketContents.fluid(inv.getStackInSlot(0)) == ModFluids.CRUDE_OIL.get());

        // 桶满了：一滴不动
        energy.receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        tick(level, pos);
        eq("桶满后再 tick：罐0 不动（仍 2000）", 2000, be.getTank(0).getFluidAmount());

        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ③-b 没电：一滴不动（单独一台新机器，缓冲真的是 0） =================

    private static void checkNoPower(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(0, 0, 24);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了（没电的场景）", false);
            return;
        }
        be.getFluidHandler().fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
        eq("（准备）这台机器的电是 0", 0,
                be.getContainerData().get(FillingMachineBlockEntity.DATA_ENERGY));
        for (int i = 0; i < 5; i++) {
            tick(level, pos);
        }
        eq("没电：罐里 5000 一滴没少", 5000, be.getTank(0).getFluidAmount());
        eq("没电：桶还是空的", 0, OilBucketContents.amount(be.getInventory().getStackInSlot(0)));
        // 只补 59 FE（差 1 FE）：仍然不动 —— 判据是 <ENERGY_PER_TANK 就停
        be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.ENERGY_PER_TANK - 1, false);
        tick(level, pos);
        eq("电只有 59 FE（差 1）也不灌", 0,
                OilBucketContents.amount(be.getInventory().getStackInSlot(0)));
        // 补到 60：立刻动
        be.getEnergyStorage().receiveEnergy(1, false);
        tick(level, pos);
        eq("凑够 60 FE：立刻灌 5 mB", 5,
                OilBucketContents.amount(be.getInventory().getStackInSlot(0)));
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ③-c 四种石油产品也要能灌进油桶 =================

    private static void checkAllProducts(ServerLevel level) {
        java.util.List<net.minecraft.world.level.material.Fluid> products = java.util.List.of(
                ModFluids.DIESEL.get(), ModFluids.NAPHTHA.get(),
                ModFluids.GASOLINE.get(), ModFluids.LPG.get());
        int z = 0;
        for (net.minecraft.world.level.material.Fluid product : products) {
            BlockPos pos = ORIGIN.offset(0, 0, 28 + z * 4);
            z++;
            level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
            if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
                ok("灌装机方块实体建出来了（产品场景）", false);
                continue;
            }
            ok("产品算液体：" + product.builtInRegistryHolder().key().location(),
                    ModFluids.isLiquid(product));
            be.getFluidHandler().fill(new FluidStack(product, 5000), IFluidHandler.FluidAction.EXECUTE);
            be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
            be.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
            tick(level, pos);
            ItemStack bucket = be.getInventory().getStackInSlot(0);
            eq("产品能灌进油桶（5 mB）：" + product.builtInRegistryHolder().key().location(),
                    5, OilBucketContents.amount(bucket));
            ok("桶里那种流体对得上：" + product.builtInRegistryHolder().key().location(),
                    OilBucketContents.fluid(bucket) == product);
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    // ================= ⑧ 用户的真实接法：原油池 → 泵 → 灌装机 =================

    private static void checkPipeFeed(ServerLevel level) {
        Direction front = Direction.NORTH;
        BlockPos pumpPos = RIG.relative(Direction.SOUTH, 2);
        BlockPos machinePos = RIG.relative(Direction.SOUTH, 3);
        BlockPos oilCenter = RIG;

        // 池底与围墙（免得原油到处流）：池 = x399..401 / z399..401，围墙在 z398 与 x398/402，
        // 泵两侧再堵两块石头 —— 墙必须在源方块之前放，否则会被源方块覆盖掉
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 3; dz++) {
                level.setBlock(oilCenter.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
            }
        }
        for (int dx = -2; dx <= 2; dx++) {
            level.setBlock(oilCenter.offset(dx, 0, -2), Blocks.STONE.defaultBlockState(), 2);
        }
        for (int dz = -2; dz <= 2; dz++) {
            level.setBlock(oilCenter.offset(-2, 0, dz), Blocks.STONE.defaultBlockState(), 2);
            level.setBlock(oilCenter.offset(2, 0, dz), Blocks.STONE.defaultBlockState(), 2);
        }
        level.setBlock(oilCenter.offset(-1, 0, 2), Blocks.STONE.defaultBlockState(), 2);
        level.setBlock(oilCenter.offset(1, 0, 2), Blocks.STONE.defaultBlockState(), 2);

        // 3x3 原油源方块
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                level.setBlock(oilCenter.offset(dx, 0, dz),
                        ModBlocks.CRUDE_OIL.get().defaultBlockState(), 3);
            }
        }
        // 泵：正面（输入）朝北贴着原油池，背面（输出）朝南贴灌装机
        level.setBlock(pumpPos, ModBlocks.FLUID_PUMP.get().defaultBlockState()
                .setValue(FluidPumpBlock.FACING, front), 3);
        level.setBlock(machinePos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);

        ok("泵正面那格确实是原油源方块",
                level.getFluidState(pumpPos.relative(front)).isSource()
                        && level.getFluidState(pumpPos.relative(front)).getType() == ModFluids.CRUDE_OIL.get());

        if (!(level.getBlockEntity(pumpPos) instanceof FluidPumpBlockEntity pump)
                || !(level.getBlockEntity(machinePos) instanceof FillingMachineBlockEntity machine)) {
            ok("泵 / 灌装机方块实体建出来了", false);
            return;
        }
        pump.setRate(100);
        eq("泵 100% ⇒ 每 tick 1000 mB", 1000, FluidPumpBlockEntity.mbPerTick(100));
        eq("泵 100% ⇒ 每 tick 400 FE", 400, FluidPumpBlockEntity.fePerTick(100));
        for (int i = 0; i < 20; i++) {
            pump.getEnergyStorage().receiveEnergy(Integer.MAX_VALUE, false);
            tickPump(level, pumpPos);
            tick(level, machinePos);
        }
        int inMachine = machine.getTank(0).getFluidAmount() + machine.getTank(1).getFluidAmount()
                + machine.getTank(2).getFluidAmount() + machine.getTank(3).getFluidAmount()
                + machine.getTank(4).getFluidAmount();
        log("  诊断：泵跑 20 tick 后，灌装机五个罐合计 = " + inMachine + " mB");
        ok("泵真的把原油送进了灌装机（>0）", inMachine > 0);
        ok("送进来的那种流体是原油",
                machine.getTank(0).getFluidAmount() > 0
                        && machine.getTank(0).getFluid().getFluid() == ModFluids.CRUDE_OIL.get());

        // 再放空油桶 ⇒ 应该开始灌
        machine.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
        for (int i = 0; i < 10; i++) {
            machine.getEnergyStorage().receiveEnergy(Integer.MAX_VALUE, false);
            tick(level, machinePos);
        }
        eq("管道供油 + 空油桶 ⇒ 桶里 50 mB（10 tick × 5）", 50,
                OilBucketContents.amount(machine.getInventory().getStackInSlot(0)));
        level.setBlock(machinePos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pumpPos, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ⑨ ZF80 新功能：手倒进罐 =================

    private static void checkPour(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(8, 0, 0);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了（手倒场景）", false);
            return;
        }
        // ① 空桶：倒不出东西
        ItemStack empty = new ItemStack(ModItems.OIL_BUCKET.get());
        eqEnum("空桶：结果是 EMPTY",
                FillingMachineBlockEntity.PourResult.EMPTY, be.pourFrom(empty).result());

        // ② 满油桶 3000 mB ⇒ 一次倒 1000 mB 进 1 号罐
        ItemStack full = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(full, new FluidStack(ModFluids.CRUDE_OIL.get(), 3000), 3000);
        eq("（准备）桶里有 3000 mB 原油", 3000, OilBucketContents.amount(full));
        var out1 = be.pourFrom(full);
        eqEnum("满油桶：结果是 POURED", FillingMachineBlockEntity.PourResult.POURED, out1.result());
        eq("倒进了 1 号罐", 0, out1.tank());
        eq("一次倒 1000 mB（POUR_PER_CLICK）", 1000, out1.amount());
        eq("桶里剩 2000 mB", 2000, OilBucketContents.amount(full));
        eq("罐里 1000 mB", 1000, be.getTank(0).getFluidAmount());

        // ③ 再倒两次 ⇒ 桶空、罐 3000（接着同种流体倒，不乱开新罐）
        be.pourFrom(full);
        be.pourFrom(full);
        eq("倒三次：桶空", 0, OilBucketContents.amount(full));
        eq("倒三次：还是 1 号罐在收（3000 mB）", 3000, be.getTank(0).getFluidAmount());
        eq("2 号罐没被开出来", 0, be.getTank(1).getFluidAmount());
        eqEnum("空桶再倒：EMPTY",
                FillingMachineBlockEntity.PourResult.EMPTY, be.pourFrom(full).result());

        // ④ 异种流体 ⇒ 找下一个空罐（不是混进 1 号罐）
        ItemStack diesel = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(diesel, new FluidStack(ModFluids.DIESEL.get(), 500), 500);
        var out2 = be.pourFrom(diesel);
        eq("柴油倒进 2 号罐（异种不混装）", 1, out2.tank());
        ok("2 号罐里是柴油", be.getTank(1).getFluid().getFluid() == ModFluids.DIESEL.get());

        // ⑤ 五个罐都满了 ⇒ NO_ROOM
        for (int i = 2; i < FillingMachineBlockEntity.TANK_COUNT; i++) {
            be.getTank(i).fill(new FluidStack(ModFluids.NAPHTHA.get(), 5000),
                    IFluidHandler.FluidAction.EXECUTE);
        }
        be.getTank(0).fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        be.getTank(1).fill(new FluidStack(ModFluids.DIESEL.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        ItemStack again = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(again, new FluidStack(ModFluids.CRUDE_OIL.get(), 1000), 1000);
        eqEnum("五个罐全满：NO_ROOM",
                FillingMachineBlockEntity.PourResult.NO_ROOM, be.pourFrom(again).result());
        eq("倒不进去时桶里一滴不少", 1000, OilBucketContents.amount(again));

        // ⑥ 不是容器：NO_CONTAINER
        eqEnum("手里拿泥土：NO_CONTAINER",
                FillingMachineBlockEntity.PourResult.NO_CONTAINER,
                be.pourFrom(new ItemStack(Items.DIRT)).result());

        // ⑦ 手倒进去的油，机器接着就能灌进空桶（闭环）
        BlockPos pos2 = ORIGIN.offset(8, 0, 4);
        level.setBlock(pos2, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (level.getBlockEntity(pos2) instanceof FillingMachineBlockEntity fresh) {
            ItemStack src = new ItemStack(ModItems.OIL_BUCKET.get());
            OilBucketContents.fill(src, new FluidStack(ModFluids.CRUDE_OIL.get(), 1000), 1000);
            fresh.pourFrom(src);
            eq("（闭环）手倒后罐里 1000 mB", 1000, fresh.getTank(0).getFluidAmount());
            fresh.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
            fresh.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
            tick(level, pos2);
            eq("（闭环）机器立刻灌进空桶 5 mB", 5,
                    OilBucketContents.amount(fresh.getInventory().getStackInSlot(0)));
        } else {
            ok("闭环用的第二台机器建出来了", false);
        }
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(pos2, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ⑩ ZF80 新功能：逐槽诊断的状态码 =================

    private static void checkDiagnosis(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(8, 0, 8);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了（诊断场景）", false);
            return;
        }
        // ① 罐空
        eqEnum("罐空 ⇒ TANK_EMPTY", FillingMachineBlockEntity.SlotState.TANK_EMPTY, be.stateOf(0));
        // ② 有油没容器
        be.getTank(0).fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        eqEnum("有油没容器 ⇒ SLOT_EMPTY", FillingMachineBlockEntity.SlotState.SLOT_EMPTY, be.stateOf(0));
        // ③ 有容器没电
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
        eqEnum("有容器没电 ⇒ NO_POWER", FillingMachineBlockEntity.SlotState.NO_POWER, be.stateOf(0));
        // ④ 有电 ⇒ 正在灌
        be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        eqEnum("电够了 ⇒ FILLING", FillingMachineBlockEntity.SlotState.FILLING, be.stateOf(0));
        // ⑤ 容器满了
        ItemStack fullBucket = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(fullBucket, new FluidStack(ModFluids.CRUDE_OIL.get(), 3000), 3000);
        be.getInventory().setStackInSlot(0, fullBucket);
        eqEnum("容器满 ⇒ FULL", FillingMachineBlockEntity.SlotState.FULL, be.stateOf(0));
        // ⑥ 容器不收这种流体：罐里是氧气、槽里是油桶
        be.getTank(0).drain(5000, IFluidHandler.FluidAction.EXECUTE);
        be.getTank(0).fill(new FluidStack(ModFluids.OXYGEN.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
        eqEnum("氧气 + 油桶 ⇒ REJECTED", FillingMachineBlockEntity.SlotState.REJECTED, be.stateOf(0));
        // ⑦ 诊断与真实行为一致：REJECTED 的槽 tick 之后一滴不动
        int before = be.getTank(0).getFluidAmount();
        tick(level, pos);
        eq("REJECTED 的槽 tick 之后氧气没少", before, be.getTank(0).getFluidAmount());
        eq("REJECTED 的槽 tick 之后桶还是空的", 0,
                OilBucketContents.amount(be.getInventory().getStackInSlot(0)));
        // ⑧ 诊断用读数
        eq("诊断读数：罐里氧气 5000", 5000, be.fluidOf(0).getAmount());
        eq("诊断读数：空桶还能装 3000", 3000, be.spaceOf(0));
        eq("诊断读数：没容器时 spaceOf = −1", -1, be.spaceOf(4));
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    private static void tickPump(ServerLevel level, BlockPos pos) {        BlockState state = level.getBlockState(pos);
        if (level.getBlockEntity(pos) instanceof FluidPumpBlockEntity pump) {
            FluidPumpBlockEntity.tick(level, pos, state, pump);
        }
    }

    // ================= ④ 水 → 油桶（说明"液体"这条规则本身没问题） =================

    private static void checkCoreWater(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(0, 0, 4);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了（水的场景）", false);
            return;
        }
        be.getFluidHandler().fill(
                new FluidStack(net.minecraft.world.level.material.Fluids.WATER, 1000),
                IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
        tick(level, pos);
        eq("水也能灌进油桶（5 mB/t）", 5,
                OilBucketContents.amount(be.getInventory().getStackInSlot(0)));
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ⑤ 气体不能进油桶（用户规则，回归） =================

    private static void checkGasIntoBucket(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(0, 0, 12);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了（气体的场景）", false);
            return;
        }
        be.getFluidHandler().fill(new FluidStack(ModFluids.OXYGEN.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.OIL_BUCKET.get()));
        for (int i = 0; i < 20; i++) {
            be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
            tick(level, pos);
        }
        eq("氧气一滴都进不了油桶（用户规则：不可以罐装气体）", 0,
                OilBucketContents.amount(be.getInventory().getStackInSlot(0)));
        eq("罐里的氧气没被抽走", 5000, be.getTank(0).getFluidAmount());
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ⑥ 液体不能进气罐（回归） =================

    private static void checkOilIntoGasTank(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(0, 0, 16);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了（气罐的场景）", false);
            return;
        }
        be.getFluidHandler().fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.HIGH_PRESSURE_TANK.get()));
        for (int i = 0; i < 20; i++) {
            be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
            tick(level, pos);
        }
        eq("原油进不了高压气罐", 0, TankContents.total(be.getInventory().getStackInSlot(0)));
        eq("罐里的原油没被抽走", 5000, be.getTank(0).getFluidAmount());
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ⑦ 气罐照旧能灌气（回归） =================

    private static void checkGasTankStillWorks(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(0, 0, 20);
        level.setBlock(pos, ModBlocks.FILLING_MACHINE.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be)) {
            ok("灌装机方块实体建出来了（气罐回归的场景）", false);
            return;
        }
        be.getFluidHandler().fill(new FluidStack(ModFluids.OXYGEN.get(), 5000),
                IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
        be.getInventory().setStackInSlot(0, new ItemStack(ModItems.HIGH_PRESSURE_TANK.get()));
        for (int i = 0; i < 10; i++) {
            be.getEnergyStorage().receiveEnergy(FillingMachineBlockEntity.MAX_ENERGY, false);
            tick(level, pos);
        }
        eq("气罐照旧能灌氧气（10 tick = 50 mB）", 50,
                TankContents.total(be.getInventory().getStackInSlot(0)));
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    private static void tick(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (level.getBlockEntity(pos) instanceof FillingMachineBlockEntity be) {
            FillingMachineBlockEntity.tick(level, pos, state, be);
        }
    }
}
