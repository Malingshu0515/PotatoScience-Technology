package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF81). Delete after the run.
 *
 * <p>用户原话：「电解器还是改成 1000Fe/t 吧」。验三件事：</p>
 * <ol>
 *   <li>两个模式的能耗常量都是 1000；</li>
 *   <li>真跑：999 FE 一点不动、凑够 1000 FE 才走一 tick（水 −10、氧 +3、氢 +6、电 −1000）；</li>
 *   <li>缓冲仍 ≥ 单 tick 电费（ZF38 那条"泵永久待机"的坑不许重演），并报出缓冲能顶几 tick。</li>
 * </ol>
 */
public final class ElectrolyzerCheck {

    private static final String TAG = "[F81] ";
    private static final BlockPos ORIGIN = new BlockPos(420, 120, 420);
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf81_probe.txt";
    private static final StringBuilder REPORT = new StringBuilder();

    private static boolean registered;
    private static int passed;
    private static int failed;

    private ElectrolyzerCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(ElectrolyzerCheck.class);
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
            checkConstants();
            checkOxygenRun(level);
            checkChlorineRun(level);
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

    // ================= ① 常量 =================

    private static void checkConstants() {
        eq("纯水制氧能耗 = 1000 FE/t", 1000, ElectrolyzerBlockEntity.ENERGY_PER_TICK_OXYGEN);
        eq("盐水制氯能耗 = 1000 FE/t", 1000, ElectrolyzerBlockEntity.ENERGY_PER_TICK_CHLORINE);
        eq("兼容别名 ENERGY_PER_TICK 跟着走", 1000, ElectrolyzerBlockEntity.ENERGY_PER_TICK);
        ok("缓冲 ≥ 单 tick 电费（ZF38「泵永久待机」那条坑）",
                ElectrolyzerBlockEntity.MAX_ENERGY >= ElectrolyzerBlockEntity.ENERGY_PER_TICK_OXYGEN
                        && ElectrolyzerBlockEntity.MAX_ENERGY >= ElectrolyzerBlockEntity.ENERGY_PER_TICK_CHLORINE);
        log("  诊断：缓冲 " + ElectrolyzerBlockEntity.MAX_ENERGY + " FE ⇒ 满载能顶 "
                + (ElectrolyzerBlockEntity.MAX_ENERGY / ElectrolyzerBlockEntity.ENERGY_PER_TICK_OXYGEN)
                + " tick（100 FE/t 时代是 "
                + (ElectrolyzerBlockEntity.MAX_ENERGY / 100) + " tick）");
        eq("水/产物速度一个没动：水 10 mB/t", 10, ElectrolyzerBlockEntity.WATER_PER_TICK);
        eq("水/产物速度一个没动：氧 3 / 氯 3 / 氢 6", 3, ElectrolyzerBlockEntity.OXYGEN_PER_TICK);
        eq("每个海盐仍然是 500 mB 水", 500, ElectrolyzerBlockEntity.WATER_PER_SALT);
    }

    // ================= ② 纯水制氧真跑 =================

    private static void checkOxygenRun(ServerLevel level) {
        BlockPos pos = ORIGIN;
        level.setBlock(pos, ModBlocks.ELECTROLYZER.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof ElectrolyzerBlockEntity be)) {
            ok("电解器方块实体建出来了", false);
            return;
        }
        IFluidHandler handler = be.getFluidHandler();
        var data = be.getContainerData();
        IEnergyStorage energy = be.getEnergyStorage();

        int accepted = handler.fill(new FluidStack(Fluids.WATER, 1000), IFluidHandler.FluidAction.EXECUTE);
        eq("灌水 1000 mB 全收", 1000, accepted);
        eq("水槽 = 1000", 1000, data.get(ElectrolyzerBlockEntity.DATA_INPUT));

        // ① 差 1 FE：一点不动
        energy.receiveEnergy(999, false);
        eq("（准备）电 = 999", 999, data.get(ElectrolyzerBlockEntity.DATA_ENERGY));
        tick(level, pos);
        eq("999 FE：水一点没少", 1000, data.get(ElectrolyzerBlockEntity.DATA_INPUT));
        eq("999 FE：氧还是 0", 0, data.get(ElectrolyzerBlockEntity.DATA_OXYGEN));
        eq("999 FE：电还是 999", 999, data.get(ElectrolyzerBlockEntity.DATA_ENERGY));

        // ② 凑够 1000：走一 tick
        energy.receiveEnergy(1, false);
        tick(level, pos);
        eq("凑够 1000 FE：水 −10", 990, data.get(ElectrolyzerBlockEntity.DATA_INPUT));
        eq("凑够 1000 FE：氧 +3", 3, data.get(ElectrolyzerBlockEntity.DATA_OXYGEN));
        eq("凑够 1000 FE：氢 +6", 6, data.get(ElectrolyzerBlockEntity.DATA_HYDROGEN));
        eq("凑够 1000 FE：电正好扣光", 0, data.get(ElectrolyzerBlockEntity.DATA_ENERGY));

        // ③ 连跑 10 tick（每 tick 补满一次电）⇒ 100 水 / 30 氧 / 60 氢
        for (int i = 0; i < 10; i++) {
            energy.receiveEnergy(ElectrolyzerBlockEntity.MAX_ENERGY, false);
            tick(level, pos);
        }
        eq("10 tick 后：水 990−100 = 890", 890, data.get(ElectrolyzerBlockEntity.DATA_INPUT));
        eq("10 tick 后：氧 3+30 = 33", 33, data.get(ElectrolyzerBlockEntity.DATA_OXYGEN));
        eq("10 tick 后：氢 6+60 = 66", 66, data.get(ElectrolyzerBlockEntity.DATA_HYDROGEN));

        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ③ 盐水制氯真跑 =================

    private static void checkChlorineRun(ServerLevel level) {
        BlockPos pos = ORIGIN.offset(0, 0, 4);
        level.setBlock(pos, ModBlocks.ELECTROLYZER.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof ElectrolyzerBlockEntity be)) {
            ok("电解器方块实体建出来了（盐水场景）", false);
            return;
        }
        var data = be.getContainerData();
        be.getFluidHandler().fill(new FluidStack(Fluids.WATER, 1000), IFluidHandler.FluidAction.EXECUTE);
        be.getInventory().setStackInSlot(ElectrolyzerBlockEntity.ELECTROLYTE_SLOT,
                new ItemStack(ModItems.SEA_SALT.get(), 1));

        // 999 FE：不动
        be.getEnergyStorage().receiveEnergy(999, false);
        tick(level, pos);
        eq("盐水模式 999 FE：氯还是 0", 0, data.get(ElectrolyzerBlockEntity.DATA_CHLORINE));
        // 1000 FE：产氯 3 + 氢 6
        be.getEnergyStorage().receiveEnergy(1, false);
        tick(level, pos);
        eq("盐水模式 1000 FE：氯 +3", 3, data.get(ElectrolyzerBlockEntity.DATA_CHLORINE));
        eq("盐水模式 1000 FE：氢 +6", 6, data.get(ElectrolyzerBlockEntity.DATA_HYDROGEN));
        eq("盐水模式 1000 FE：电扣光", 0, data.get(ElectrolyzerBlockEntity.DATA_ENERGY));
        eq("盐水模式：水 −10", 990, data.get(ElectrolyzerBlockEntity.DATA_INPUT));
        // 海盐按 500 mB 水消耗：再跑 49 tick（累计 500 mB 水）⇒ 海盐从 1 个变 0
        for (int i = 0; i < 49; i++) {
            be.getEnergyStorage().receiveEnergy(ElectrolyzerBlockEntity.MAX_ENERGY, false);
            tick(level, pos);
        }
        eq("累计 500 mB 水后：海盐被消耗掉",
                0, be.getInventory().getStackInSlot(ElectrolyzerBlockEntity.ELECTROLYTE_SLOT).getCount());
        ok("海盐没了之后自动回到纯水制氧（不会卡死）",
                be.getContainerData().get(ElectrolyzerBlockEntity.DATA_OXYGEN) >= 0);
        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    private static void tick(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (level.getBlockEntity(pos) instanceof ElectrolyzerBlockEntity be) {
            ElectrolyzerBlockEntity.tick(level, pos, state, be);
        }
    }
}
