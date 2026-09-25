package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF78). Delete after the run.
 *
 * <p>分馏塔三件套的实测：图纸逐格、检测窗口边界、控制器推送、容量缩放、
 * 每 tick 公式、五种停机条件、存读往返、流体标签。</p>
 */
public final class DistillationCheck {

    private static final String TAG = "[F78] ";

    /** 试验场原点（离出生点不远但避开出生点，先整块清空） */
    private static final BlockPos ORIGIN = new BlockPos(200, 120, 200);

    private static boolean registered;
    private static int passed;
    private static int failed;
    /** 探针自己的 UTF-8 报告（控制台会被 JVM 按 GBK 输出成乱码，落文件才是可靠证据）
     *  ⚠ 必须用**绝对路径**：runServer 的 JVM 工作目录不是工程根（第一版写相对路径 ⇒
     *  FileNotFoundException，报告没落下来）。 */
    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf78_probe.txt";

    /** 用户图纸的逐层抄写：1=一般金属块 2=耐热金属块 3=加热装置 .=空气 */
    private static final String[][] DRAWING = {
            {"1..1", "....", "....", "1..1"},
            {"1..1", "....", "....", "1..1"},
            {"1221", "2332", "2332", "1221"},
            {"2222", "2..2", "2..2", "2222"},
            {"1221", "2332", "2332", "1221"},
            {"2222", "2..2", "2..2", "2222"},
            {"1111", "1111", "1111", "1111"},
    };

    private DistillationCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(DistillationCheck.class);
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
            clearArea(level);
            checkIds();
            checkDrawing();
            checkDetection(level);
            checkControllerPush(level);
            checkCapacity(level);
            checkProcessing(level);
            checkPour(level);
            checkDiagnose(level);
            checkSaveLoad(level);
            checkTags(level);
        } catch (Throwable t) {
            t.printStackTrace();
            failed++;
        }
        System.out.println(TAG + "==== passed=" + passed + " failed=" + failed + " ====");
        REPORT.append("==== passed=").append(passed).append(" failed=").append(failed)
                .append(" ====\n");
        flushReport();
        event.getServer().halt(false);
    }

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

    // ================= 工具 =================

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

    private static void clearArea(ServerLevel level) {
        BlockPos min = ORIGIN.offset(-24, -4, -24);
        BlockPos max = ORIGIN.offset(36, 16, 36);
        for (BlockPos p : BlockPos.betweenClosed(min, max)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 2);
        }
        System.out.println(TAG + "试验场已清空 " + min.toShortString() + " .. " + max.toShortString());
    }

    private static void buildTower(ServerLevel level, BlockPos base) {
        for (int y = 0; y < DistillationTowerStructure.HEIGHT; y++) {
            for (int z = 0; z < DistillationTowerStructure.SIZE; z++) {
                for (int x = 0; x < DistillationTowerStructure.SIZE; x++) {
                    DistillationTowerStructure.Kind kind = DistillationTowerStructure.kindAt(x, z, y);
                    level.setBlock(base.offset(x, y, z), kind == DistillationTowerStructure.Kind.AIR
                            ? Blocks.AIR.defaultBlockState()
                            : DistillationTowerStructure.blockFor(kind).defaultBlockState(), 3);
                }
            }
        }
    }

    private static void tickController(ServerLevel level, BlockPos pos) {
        if (level.getBlockEntity(pos) instanceof DistillationControllerBlockEntity be) {
            DistillationControllerBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
    }

    private static void tickOperator(ServerLevel level, BlockPos pos) {
        if (level.getBlockEntity(pos) instanceof DistillationOperatorBlockEntity be) {
            DistillationOperatorBlockEntity.tick(level, pos, level.getBlockState(pos), be);
        }
    }

    private static FluidStack crude(int mb) {
        return new FluidStack(ModFluids.CRUDE_OIL.get(), mb);
    }

    private static FluidStack product(Fluid fluid, int mb) {
        return new FluidStack(fluid, mb);
    }

    // ================= ① 注册名 / 图纸 =================

    private static void checkIds() {
        ok("方块 id = potato_s_t:distillation_controller",
                "potato_s_t:distillation_controller".equals(
                        String.valueOf(BuiltInRegistries.BLOCK.getKey(ModBlocks.DISTILLATION_CONTROLLER.get()))));
        ok("方块 id = potato_s_t:distillation_operator",
                "potato_s_t:distillation_operator".equals(
                        String.valueOf(BuiltInRegistries.BLOCK.getKey(ModBlocks.DISTILLATION_OPERATOR.get()))));
        ok("两个方块实体类型都已注册",
                ModBlocks.DISTILLATION_CONTROLLER_BE.get() != null
                        && ModBlocks.DISTILLATION_OPERATOR_BE.get() != null);
        ok("沥青物品 id = potato_s_t:bitumen",
                "potato_s_t:bitumen".equals(
                        String.valueOf(BuiltInRegistries.ITEM.getKey(ModItems.BITUMEN.get()))));
        ok("操作器菜单类型已注册", ModMenus.DISTILLATION_OPERATOR_MENU.get() != null);
        ok("四个产品流体 id 正确",
                "potato_s_t:diesel".equals(String.valueOf(BuiltInRegistries.FLUID.getKey(ModFluids.DIESEL.get())))
                        && "potato_s_t:naphtha".equals(String.valueOf(BuiltInRegistries.FLUID.getKey(ModFluids.NAPHTHA.get())))
                        && "potato_s_t:gasoline".equals(String.valueOf(BuiltInRegistries.FLUID.getKey(ModFluids.GASOLINE.get())))
                        && "potato_s_t:lpg".equals(String.valueOf(BuiltInRegistries.FLUID.getKey(ModFluids.LPG.get()))));
    }

    private static void checkDrawing() {
        int bad = 0;
        for (int y = 0; y < DRAWING.length; y++) {
            for (int z = 0; z < DistillationTowerStructure.SIZE; z++) {
                for (int x = 0; x < DistillationTowerStructure.SIZE; x++) {
                    DistillationTowerStructure.Kind want = switch (DRAWING[y][z].charAt(x)) {
                        case '1' -> DistillationTowerStructure.Kind.COMMON;
                        case '2' -> DistillationTowerStructure.Kind.HEAT;
                        case '3' -> DistillationTowerStructure.Kind.HEATER;
                        default -> DistillationTowerStructure.Kind.AIR;
                    };
                    if (DistillationTowerStructure.kindAt(x, z, y) != want) {
                        bad++;
                    }
                }
            }
        }
        ok("图纸 7 层 × 16 格逐格一致（不符 " + bad + " 格）", bad == 0);

        int common = 0;
        int heat = 0;
        int heater = 0;
        int air = 0;
        for (int y = 0; y < DistillationTowerStructure.HEIGHT; y++) {
            for (int z = 0; z < DistillationTowerStructure.SIZE; z++) {
                for (int x = 0; x < DistillationTowerStructure.SIZE; x++) {
                    switch (DistillationTowerStructure.kindAt(x, z, y)) {
                        case COMMON -> common++;
                        case HEAT -> heat++;
                        case HEATER -> heater++;
                        case AIR -> air++;
                    }
                }
            }
        }
        eq("一般金属块 32 格", 32, common);
        eq("耐热金属块 40 格", 40, heat);
        eq("加热装置 8 格", 8, heater);
        eq("空格（必须是空气）32 格", 32, air);
        eq("总计 112 格", 112, common + heat + heater + air);
    }

    // ================= ② 检测与窗口边界 =================

    private static void checkDetection(ServerLevel level) {
        BlockPos base = ORIGIN;
        // ⚠ 控制器放在塔的东北侧（+6,+6）：第一版放在西北角，第二座塔（+6 格）离它 14 格，
        //    塔身伸出 32×32 窗口 ⇒ 数不到。这是**探针**摆位错，不是检测错。
        BlockPos ctrl = base.offset(6, 0, 6);
        buildTower(level, base);
        ok("isValidTower(塔底)", DistillationTowerStructure.isValidTower(level, base));
        eq("1 座塔 -> 数到 1", 1, DistillationTowerStructure.countTowers(level, ctrl));

        level.setBlock(base.offset(1, 0, 1), Blocks.STONE.defaultBlockState(), 3);
        eq("空腔里塞石头 -> 0", 0, DistillationTowerStructure.countTowers(level, ctrl));
        level.setBlock(base.offset(1, 0, 1), Blocks.AIR.defaultBlockState(), 3);

        level.setBlock(base.offset(0, 0, 0), Blocks.AIR.defaultBlockState(), 3);
        eq("抽掉一根立柱 -> 0", 0, DistillationTowerStructure.countTowers(level, ctrl));
        level.setBlock(base.offset(0, 0, 0),
                ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);

        level.setBlock(base.offset(2, 6, 2),
                ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get().defaultBlockState(), 3);
        eq("顶盖换成耐热金属块 -> 0", 0, DistillationTowerStructure.countTowers(level, ctrl));
        level.setBlock(base.offset(2, 6, 2),
                ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);

        level.setBlock(base.offset(1, 2, 1),
                ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
        eq("加热装置位置换成一般金属块 -> 0", 0, DistillationTowerStructure.countTowers(level, ctrl));
        level.setBlock(base.offset(1, 2, 1), ModBlocks.HEATER.get().defaultBlockState(), 3);
        eq("复原 -> 又是 1", 1, DistillationTowerStructure.countTowers(level, ctrl));

        // 两座（相距 6 格，包围盒不相交）
        BlockPos second = base.offset(0, 0, 6);
        buildTower(level, second);
        eq("2 座（相距 6）-> 2", 2, DistillationTowerStructure.countTowers(level, ctrl));
        List<BlockPos> found = DistillationTowerStructure.findTowers(level, ctrl);
        boolean disjoint = true;
        for (int i = 0; i < found.size(); i++) {
            for (int j = i + 1; j < found.size(); j++) {
                BlockPos a = found.get(i);
                BlockPos b = found.get(j);
                if (Math.abs(a.getX() - b.getX()) < 4 && Math.abs(a.getY() - b.getY()) < 7
                        && Math.abs(a.getZ() - b.getZ()) < 4) {
                    disjoint = false;
                }
            }
        }
        ok("返回的塔互相不重叠（去重不变式）", disjoint);

        // 一片实心金属不该被误判成塔（⚠ 控制器要放在只看得见这块铁的位置：
        //   第一版放在它西北角，结果把远处那座**真塔**数进来了，白报一次 FAIL）
        BlockPos slab = ORIGIN.offset(20, 0, 0);
        for (int y = 0; y < 7; y++) {
            for (int z = 0; z < 4; z++) {
                for (int x = 0; x < 4; x++) {
                    level.setBlock(slab.offset(x, y, z),
                            ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
                }
            }
        }
        eq("4×4×7 实心一般金属块 -> 0（不算塔）", 0,
                DistillationTowerStructure.countTowers(level, slab.offset(0, 0, 6)));

        // 窗口边界（水平 ±16、竖直 -3..+6，整座塔必须落在里面）
        removeTower(level, second);
        removeTower(level, slab);
        eq("回到 1 座", 1, DistillationTowerStructure.countTowers(level, ctrl));
        buildTower(level, ctrl.offset(12, 0, 0));
        eq("塔底贴到 +12（窗口内最远）-> 2", 2, DistillationTowerStructure.countTowers(level, ctrl));
        removeTower(level, ctrl.offset(12, 0, 0));
        buildTower(level, ctrl.offset(13, 0, 0));
        eq("塔底 +13（塔身伸出 32 格窗口）-> 仍 1", 1, DistillationTowerStructure.countTowers(level, ctrl));
        removeTower(level, ctrl.offset(13, 0, 0));
        buildTower(level, ctrl.offset(0, -3, 0));
        eq("塔底 -3 层（窗口下沿）-> 2", 2, DistillationTowerStructure.countTowers(level, ctrl));
        removeTower(level, ctrl.offset(0, -3, 0));
        buildTower(level, ctrl.offset(0, -4, 0));
        eq("塔底 -4 层（超出竖直窗口）-> 仍 1", 1, DistillationTowerStructure.countTowers(level, ctrl));
        removeTower(level, ctrl.offset(0, -4, 0));
        buildTower(level, ctrl.offset(0, 1, 0));
        eq("塔底 +1 层（塔顶伸出窗口）-> 仍 1", 1, DistillationTowerStructure.countTowers(level, ctrl));
        removeTower(level, ctrl.offset(0, 1, 0));
    }

    private static void removeTower(ServerLevel level, BlockPos base) {
        for (int y = 0; y < DistillationTowerStructure.HEIGHT; y++) {
            for (int z = 0; z < DistillationTowerStructure.SIZE; z++) {
                for (int x = 0; x < DistillationTowerStructure.SIZE; x++) {
                    level.setBlock(base.offset(x, y, z), Blocks.AIR.defaultBlockState(), 3);
                }
            }
        }
    }

    // ================= ③ 控制器 -> 操作器 =================

    private static void checkControllerPush(ServerLevel level) {
        removeTower(level, ORIGIN);
        BlockPos ctrl = ORIGIN.offset(0, 0, 20);
        BlockPos oper = ctrl.offset(1, 0, 0);
        level.setBlock(ctrl, ModBlocks.DISTILLATION_CONTROLLER.get().defaultBlockState(), 3);
        level.setBlock(oper, ModBlocks.DISTILLATION_OPERATOR.get().defaultBlockState(), 3);
        ok("控制器 / 操作器的方块实体都建出来了",
                level.getBlockEntity(ctrl) instanceof DistillationControllerBlockEntity
                        && level.getBlockEntity(oper) instanceof DistillationOperatorBlockEntity);
        DistillationControllerBlockEntity cbe = (DistillationControllerBlockEntity) level.getBlockEntity(ctrl);
        DistillationOperatorBlockEntity obe = (DistillationOperatorBlockEntity) level.getBlockEntity(oper);
        if (cbe == null || obe == null) {
            return;
        }

        buildTower(level, ctrl.offset(-8, 0, -8));
        cbe.requestRescan();
        tickController(level, ctrl);
        eq("控制器数到 1 座", 1, cbe.getTowerCount());
        eq("数量推给了相邻操作器", 1, obe.getTowerCount());

        // 5 座塔 -> 控制器报 5，操作器夹到 4
        removeTower(level, ctrl.offset(-8, 0, -8));
        for (int k = 0; k < 5; k++) {
            buildTower(level, ctrl.offset(-16 + k * 5, 0, -8));
        }
        cbe.requestRescan();
        tickController(level, ctrl);
        eq("5 座塔 -> 控制器报 5", 5, cbe.getTowerCount());
        eq("操作器最多认 4 座", 4, obe.getTowerCount());

        for (int k = 0; k < 5; k++) {
            removeTower(level, ctrl.offset(-16 + k * 5, 0, -8));
        }
        cbe.requestRescan();
        tickController(level, ctrl);
        eq("全拆掉 -> 控制器报 0", 0, cbe.getTowerCount());
        eq("操作器塔数归 0", 0, obe.getTowerCount());

        // 拆掉控制器：操作器应当在 1 秒内自己发现（不复核的话它会一直分馏下去）
        level.setBlock(ctrl, Blocks.AIR.defaultBlockState(), 3);
        for (int i = 0; i < DistillationOperatorBlockEntity.CONTROLLER_CHECK_INTERVAL + 1; i++) {
            tickOperator(level, oper);
        }
        eq("拆掉控制器后塔数归 0", 0, obe.getTowerCount());
        eq("状态 = 未连接控制器", DistillationOperatorBlockEntity.STATUS_NO_CONTROLLER, obe.getStatus());
        level.setBlock(ctrl, ModBlocks.DISTILLATION_CONTROLLER.get().defaultBlockState(), 3);
    }

    // ================= ④ 容量缩放 =================

    private static void checkCapacity(ServerLevel level) {
        BlockPos oper = ORIGIN.offset(1, 0, 20);
        DistillationOperatorBlockEntity obe = (DistillationOperatorBlockEntity) level.getBlockEntity(oper);
        if (obe == null) {
            ok("操作器方块实体存在", false);
            return;
        }
        obe.setTowerCount(2);
        eq("2 塔：石油罐容量 24000", 24000, obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).getCapacity());
        eq("2 塔：产品罐容量 5000", 5000, obe.getTank(DistillationOperatorBlockEntity.TANK_DIESEL).getCapacity());
        eq("2 塔：能量上限 = 8096×2", 16192, obe.maxEnergy());
        eq("2 塔：能量能力上限也是 8096×2", 16192,
                obe.getEnergyStorage().getMaxEnergyStored());
        eq("2 塔：能量能力收满 8096×2", 16192, obe.getEnergyStorage().receiveEnergy(999999, false));

        eq("石油罐收 1000 mB 原油", 1000,
                obe.getFluidHandler().fill(crude(1000), IFluidHandler.FluidAction.EXECUTE));
        eq("产品罐拒收（灌柴油 = 0）", 0,
                obe.getFluidHandler().fill(product(ModFluids.DIESEL.get(), 1000),
                        IFluidHandler.FluidAction.EXECUTE));
        eq("石油罐拒收柴油", 0,
                obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(
                        product(ModFluids.DIESEL.get(), 1000), IFluidHandler.FluidAction.EXECUTE));
        eq("石油罐拒收水（只认原油）", 0,
                obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(
                        new FluidStack(net.minecraft.world.level.material.Fluids.WATER, 1000),
                        IFluidHandler.FluidAction.EXECUTE));

        obe.setTowerCount(0);
        eq("0 塔：石油罐容量 0", 0, obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).getCapacity());
        eq("0 塔：装满的罐不再收料", 0,
                obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(crude(1000),
                        IFluidHandler.FluidAction.EXECUTE));
        eq("0 塔：已有流体不被销毁", 1000, obe.oilAmount());
        obe.setTowerCount(4);
        eq("4 塔：石油罐容量 48000", 48000, obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).getCapacity());
    }

    // ================= ⑤ 每 tick 公式与五种停机 =================

    private static void checkProcessing(ServerLevel level) {
        BlockPos oper = ORIGIN.offset(1, 0, 20);
        DistillationOperatorBlockEntity obe = (DistillationOperatorBlockEntity) level.getBlockEntity(oper);
        if (obe == null) {
            ok("操作器方块实体存在", false);
            return;
        }
        // 清干净：罐清空、沥青槽清空、能量清零、拆掉红石
        for (int i = 0; i < DistillationOperatorBlockEntity.TANK_COUNT; i++) {
            obe.getTank(i).drain(1000000, IFluidHandler.FluidAction.EXECUTE);
        }
        obe.getInventory().setStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT, ItemStack.EMPTY);

        // 无红石：有塔也不炼
        obe.setTowerCount(1);
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(crude(8000), IFluidHandler.FluidAction.EXECUTE);
        fillEnergy(obe);
        tickOperator(level, oper);
        eq("无红石信号：不消耗石油", 8000, obe.oilAmount());
        eq("状态 = 无红石信号", DistillationOperatorBlockEntity.STATUS_NO_REDSTONE, obe.getStatus());

        // 给红石：开始分馏
        level.setBlock(oper.above(), Blocks.REDSTONE_BLOCK.defaultBlockState(), 3);
        int oil0 = obe.oilAmount();
        int energy0 = obe.getEnergy();
        tickOperator(level, oper);
        int diesel = obe.getTank(DistillationOperatorBlockEntity.TANK_DIESEL).getFluidAmount();
        int naphtha = obe.getTank(DistillationOperatorBlockEntity.TANK_NAPHTHA).getFluidAmount();
        int gasoline = obe.getTank(DistillationOperatorBlockEntity.TANK_GASOLINE).getFluidAmount();
        int lpg = obe.getTank(DistillationOperatorBlockEntity.TANK_LPG).getFluidAmount();
        eq("1 tick：石油 -8", oil0 - 8, obe.oilAmount());
        eq("1 tick：能量 -8096", energy0 - 8096, obe.getEnergy());
        eq("1 tick：柴油 +3", 3, diesel);
        eq("1 tick：石脑油 +2", 2, naphtha);
        eq("1 tick：汽油 +2", 2, gasoline);
        eq("1 tick：液化石油气 +1", 1, lpg);
        eq("进 8 mB 出 8 mB（物料平衡）", oil0 - obe.oilAmount(), diesel + naphtha + gasoline + lpg);
        eq("1 tick：沥青进度 1/5", 1, obe.getProgress());
        eq("状态 = 分馏中", DistillationOperatorBlockEntity.STATUS_RUNNING, obe.getStatus());

        // 再 4 tick -> 出 1 块沥青、进度归零
        for (int i = 0; i < 4; i++) {
            fillEnergy(obe);
            tickOperator(level, oper);
        }
        eq("5 tick：沥青 1 块", 1, obe.getInventory()
                .getStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT).getCount());
        eq("5 tick：进度归零", 0, obe.getProgress());

        // 沥青满 64 -> 停机，一滴油都不炼
        obe.getInventory().setStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT,
                new ItemStack(ModItems.BITUMEN.get(), 64));
        fillEnergy(obe);
        int oilBefore = obe.oilAmount();
        tickOperator(level, oper);
        eq("沥青满 64：不消耗石油", oilBefore, obe.oilAmount());
        eq("状态 = 沥青已满", DistillationOperatorBlockEntity.STATUS_BITUMEN_FULL, obe.getStatus());

        // 沥青 62 + 4 塔：只出装得下的 2 块，一块都不销毁
        obe.setTowerCount(4);
        obe.getInventory().setStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT,
                new ItemStack(ModItems.BITUMEN.get(), 62));
        for (int i = 0; i < 5; i++) {
            fillEnergy(obe);
            obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(crude(500),
                    IFluidHandler.FluidAction.EXECUTE);
            tickOperator(level, oper);
        }
        eq("沥青 62 + 4 塔：出满 64（不销毁、不超出）", 64, obe.getInventory()
                .getStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT).getCount());
        // ⚠ 状态是"这一 tick 开始时"算出来的：出满 64 的那一 tick 状态还是"运行中"，
        //   要再 tick 一次才报"沥青已满"（探针第一版在这里就断言，白报一次 FAIL）
        tickOperator(level, oper);
        eq("接着就停机", DistillationOperatorBlockEntity.STATUS_BITUMEN_FULL, obe.getStatus());
        obe.getInventory().setStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT, ItemStack.EMPTY);
        obe.setTowerCount(1);

        // 产品罐满 -> 停机
        for (int i = 0; i < DistillationOperatorBlockEntity.TANK_COUNT; i++) {
            obe.getTank(i).drain(1000000, IFluidHandler.FluidAction.EXECUTE);
        }
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(crude(8000), IFluidHandler.FluidAction.EXECUTE);
        obe.getTank(DistillationOperatorBlockEntity.TANK_DIESEL).fill(
                product(ModFluids.DIESEL.get(), 2500), IFluidHandler.FluidAction.EXECUTE);
        fillEnergy(obe);
        int oilFull = obe.oilAmount();
        tickOperator(level, oper);
        eq("柴油罐满：不消耗石油", oilFull, obe.oilAmount());
        eq("状态 = 产品罐满", DistillationOperatorBlockEntity.STATUS_PRODUCT_FULL, obe.getStatus());
        obe.getTank(DistillationOperatorBlockEntity.TANK_DIESEL).drain(10, IFluidHandler.FluidAction.EXECUTE);

        // 没油 / 没电
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).drain(1000000, IFluidHandler.FluidAction.EXECUTE);
        fillEnergy(obe);
        tickOperator(level, oper);
        eq("没油：状态 = 石油不足", DistillationOperatorBlockEntity.STATUS_NO_OIL, obe.getStatus());
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(crude(8000), IFluidHandler.FluidAction.EXECUTE);
        // 能量上限恰好等于每 tick 的消耗（8096 = 8096×1）⇒ 灌满后跑一 tick 就正好见底
        fillEnergy(obe);
        tickOperator(level, oper);
        eq("灌满后跑 1 tick：能量见底", 0, obe.getEnergy());
        tickOperator(level, oper);
        eq("没电：状态 = 电力不足", DistillationOperatorBlockEntity.STATUS_NO_POWER, obe.getStatus());

        // 没塔（控制器在、塔被拆光）
        fillEnergy(obe);
        obe.setTowerCount(0);
        tickOperator(level, oper);
        eq("没塔：状态 = 未检测到分馏塔", DistillationOperatorBlockEntity.STATUS_NO_TOWER, obe.getStatus());
        level.setBlock(oper.above(), Blocks.AIR.defaultBlockState(), 3);
    }

    private static void fillEnergy(DistillationOperatorBlockEntity obe) {
        obe.getEnergyStorage().receiveEnergy(Integer.MAX_VALUE, false);
    }

    // ================= ⑤b 右键倒流体（2026-09-24 用户点名要的功能）=================

    /**
     * 倒油桶 / 气罐的四种结果。
     *
     * <p>用的是 {@code DistillationOperatorBlock.pourFrom}（纯逻辑、不需要玩家对象）——
     * 本工程 §4.43 记过"假玩家 NPE"那一课，能不碰玩家就不碰。</p>
     */
    private static void checkPour(ServerLevel level) {
        BlockPos oper = ORIGIN.offset(1, 0, 20);
        DistillationOperatorBlockEntity obe = (DistillationOperatorBlockEntity) level.getBlockEntity(oper);
        if (obe == null) {
            ok("操作器方块实体存在", false);
            return;
        }
        DistillationOperatorBlock block = (DistillationOperatorBlock) ModBlocks.DISTILLATION_OPERATOR.get();
        for (int i = 0; i < DistillationOperatorBlockEntity.TANK_COUNT; i++) {
            obe.getTank(i).drain(1000000, IFluidHandler.FluidAction.EXECUTE);
        }
        obe.setTowerCount(1);

        // ① 不是流体容器 ⇒ 放行
        ItemStack dirt = new ItemStack(net.minecraft.world.item.Items.DIRT);
        ok("普通物品 ⇒ NO_CONTAINER（放行走原逻辑）",
                DistillationOperatorBlock.pourFrom(dirt, level, oper)
                        == DistillationOperatorBlock.PourResult.NO_CONTAINER);

        // ② 空油桶 ⇒ EMPTY
        ItemStack emptyBucket = new ItemStack(ModItems.OIL_BUCKET.get());
        ok("空油桶 ⇒ EMPTY（提示「容器是空的」）",
                DistillationOperatorBlock.pourFrom(emptyBucket, level, oper)
                        == DistillationOperatorBlock.PourResult.EMPTY);
        eq("空油桶倒完石油罐还是 0", 0, obe.oilAmount());

        // ③ 满油桶（3000）倒进空罐 ⇒ 一次 1000
        ItemStack oil = new ItemStack(ModItems.OIL_BUCKET.get());
        int preFilled = OilBucketContents.fill(oil,
                new FluidStack(ModFluids.CRUDE_OIL.get(), OilBucketContents.CAPACITY),
                OilBucketContents.CAPACITY);
        eq("（准备）油桶装了 3000 mB", OilBucketContents.CAPACITY, preFilled);
        ok("满油桶 ⇒ POURED",
                DistillationOperatorBlock.pourFrom(oil, level, oper)
                        == DistillationOperatorBlock.PourResult.POURED);
        eq("罐里 +1000（一次一格）", 1000, obe.oilAmount());
        eq("桶里剩 2000", 2000, OilBucketContents.total(oil));
        ok("再倒两次 ⇒ 桶空、罐 3000",
                DistillationOperatorBlock.pourFrom(oil, level, oper)
                        == DistillationOperatorBlock.PourResult.POURED
                        && DistillationOperatorBlock.pourFrom(oil, level, oper)
                        == DistillationOperatorBlock.PourResult.POURED
                        && OilBucketContents.isEmpty(oil) && obe.oilAmount() == 3000);

        // ④ 气罐（氧气）⇒ REJECTED，两边都不动
        ItemStack gas = new ItemStack(ModItems.HIGH_PRESSURE_TANK.get());
        TankContents.fill(gas, new FluidStack(ModFluids.OXYGEN.get(), 1000), 1000);
        int gasBefore = TankContents.total(gas);
        ok("气罐 ⇒ REJECTED（石油罐只收原油）",
                DistillationOperatorBlock.pourFrom(gas, level, oper)
                        == DistillationOperatorBlock.PourResult.REJECTED);
        eq("被拒后罐里还是 3000", 3000, obe.oilAmount());
        eq("被拒后气罐一滴没少", gasBefore, TankContents.total(gas));

        // ⑤ 罐满了 ⇒ REJECTED，油桶一滴没少
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(
                new FluidStack(ModFluids.CRUDE_OIL.get(), 100000), IFluidHandler.FluidAction.EXECUTE);
        ItemStack oil2 = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(oil2, new FluidStack(ModFluids.CRUDE_OIL.get(), 1000), 1000);
        ok("罐满 ⇒ REJECTED",
                DistillationOperatorBlock.pourFrom(oil2, level, oper)
                        == DistillationOperatorBlock.PourResult.REJECTED);
        eq("被拒后油桶仍是 1000", 1000, OilBucketContents.total(oil2));

        // ⑥ 罐里只剩 300 空间 ⇒ 只倒 300（允许倒半格），桶里剩 700
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).drain(1000000,
                IFluidHandler.FluidAction.EXECUTE);
        obe.setTowerCount(1);
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(
                new FluidStack(ModFluids.CRUDE_OIL.get(), 12000 - 300),
                IFluidHandler.FluidAction.EXECUTE);
        ok("罐只剩 300 空间 ⇒ 倒得进 300（不倒半格也受理）",
                DistillationOperatorBlock.pourFrom(oil2, level, oper)
                        == DistillationOperatorBlock.PourResult.POURED);
        eq("桶里剩 700", 700, OilBucketContents.total(oil2));
        eq("罐满到 12000", 12000, obe.oilAmount());
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).drain(1000000,
                IFluidHandler.FluidAction.EXECUTE);
    }

    // ================= ⑤c 控制器的排查显示（右击给的那句话）=================

    private static void checkDiagnose(ServerLevel level) {
        // 在试验场另一角搭一座"只差一格"的塔，诊断必须精确指到那一格
        BlockPos base = ORIGIN.offset(24, 0, -20);
        removeTower(level, base);
        buildTower(level, base);
        BlockPos ctrl = base.offset(6, 0, 6);
        level.setBlock(ctrl, ModBlocks.DISTILLATION_CONTROLLER.get().defaultBlockState(), 3);

        DistillationTowerStructure.Diagnosis good = DistillationTowerStructure.diagnose(level, ctrl);
        ok("完整塔 ⇒ 诊断 0 格不符", good != null && good.wrong() == 0);

        // 第 4 层（layer=3）第 2 排（z=1）第 1 列（x=0）本该是耐热金属块 ⇒ 换成空气
        BlockPos broken = base.offset(0, 3, 1);
        level.setBlock(broken, Blocks.AIR.defaultBlockState(), 3);
        DistillationTowerStructure.Diagnosis one = DistillationTowerStructure.diagnose(level, ctrl);
        ok("拆掉一格 ⇒ 诊断 1 格不符", one != null && one.wrong() == 1);
        if (one != null) {
            eq("指到 x", 0, one.x());
            eq("指到 z", 1, one.z());
            eq("指到层（0 基）", 3, one.y());
            ok("期望的是耐热金属块",
                    one.expected() == DistillationTowerStructure.Kind.HEAT);
            ok("实际读到空气", one.found() != null && one.found().isAir());
            ok("锚点就是塔底（" + one.base().toShortString() + "）", base.equals(one.base()));
        }
        eq("同时确认塔数已经归 0", 0, DistillationTowerStructure.countTowers(level, ctrl));

        // 再拆一格 ⇒ 2 格不符，第一处仍报靠前的那一格
        // ⚠ 第一版这里拆的是 base.offset(1,3,1) —— 那格按图纸（第 4 层是 `2222/2..2/2..2/2222`）
        //   本来就是**空腔**，设成空气等于什么都没干 ⇒ 探针自己假 FAIL。
        //   要拆就拆环上的：第 4 层第 1 排第 2 列（z=0, x=1）是耐热金属块。
        level.setBlock(base.offset(1, 3, 0), Blocks.AIR.defaultBlockState(), 3);
        DistillationTowerStructure.Diagnosis two = DistillationTowerStructure.diagnose(level, ctrl);
        ok("再拆一格（这次拆的是环上的格子）⇒ 诊断 2 格不符（实际 "
                + (two == null ? "null" : two.wrong()) + "）", two != null && two.wrong() == 2);

        removeTower(level, base);
        level.setBlock(ctrl, Blocks.AIR.defaultBlockState(), 3);
    }

    // ================= ⑥ 存读往返 =================

    private static void checkSaveLoad(ServerLevel level) {
        BlockPos oper = ORIGIN.offset(1, 0, 20);
        DistillationOperatorBlockEntity obe = (DistillationOperatorBlockEntity) level.getBlockEntity(oper);
        if (obe == null) {
            ok("操作器方块实体存在", false);
            return;
        }
        for (int i = 0; i < DistillationOperatorBlockEntity.TANK_COUNT; i++) {
            obe.getTank(i).drain(1000000, IFluidHandler.FluidAction.EXECUTE);
        }
        obe.getInventory().setStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT, ItemStack.EMPTY);
        obe.setTowerCount(3);
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(crude(1234), IFluidHandler.FluidAction.EXECUTE);
        obe.getTank(DistillationOperatorBlockEntity.TANK_LPG).fill(
                product(ModFluids.LPG.get(), 77), IFluidHandler.FluidAction.EXECUTE);
        obe.getInventory().setStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT,
                new ItemStack(ModItems.BITUMEN.get(), 5));
        fillEnergy(obe);
        int energy = obe.getEnergy();
        int progress = obe.getProgress();

        CompoundTag tag = obe.saveWithoutMetadata(level.registryAccess());
        DistillationOperatorBlockEntity copy =
                new DistillationOperatorBlockEntity(oper, level.getBlockState(oper));
        copy.loadWithComponents(tag, level.registryAccess());
        eq("存读：石油量", 1234, copy.oilAmount());
        eq("存读：液化石油气", 77, copy.getTank(DistillationOperatorBlockEntity.TANK_LPG).getFluidAmount());
        eq("存读：沥青 5 块", 5, copy.getInventory()
                .getStackInSlot(DistillationOperatorBlockEntity.BITUMEN_SLOT).getCount());
        eq("存读：能量", energy, copy.getEnergy());
        eq("存读：进度", progress, copy.getProgress());

        // 石油 48000 超出短整型 ⇒ 界面上必须分两片传、拼回来一样
        obe.setTowerCount(4);
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).drain(1000000, IFluidHandler.FluidAction.EXECUTE);
        obe.getTank(DistillationOperatorBlockEntity.TANK_OIL).fill(crude(48000), IFluidHandler.FluidAction.EXECUTE);
        int low = obe.getContainerData().get(DistillationOperatorBlockEntity.DATA_OIL_LOW) & 0x7FFF;
        int high = obe.getContainerData().get(DistillationOperatorBlockEntity.DATA_OIL_HIGH) & 0x7FFF;
        eq("石油 48000：两片拼回来一致", 48000, low | (high << 15));
        ok("两片都落在短整型范围内（low=" + low + " high=" + high + "）", low <= 32767 && high <= 32767);
        // 4 塔的能量上限 = 8096×4 = 32384，也还在短整型里（不用分片）
        fillEnergy(obe);
        eq("4 塔能量灌满 = 32384", 32384, obe.getEnergy());
        ok("能量一个槽位就够传（" + obe.getContainerData().get(DistillationOperatorBlockEntity.DATA_ENERGY)
                + " ≤ 32767）",
                obe.getContainerData().get(DistillationOperatorBlockEntity.DATA_ENERGY) <= 32767);
        obe.setTowerCount(0);
    }

    // ================= ⑦ 流体标签 =================

    private static void checkTags(ServerLevel level) {
        Fluid[] sources = {ModFluids.DIESEL.get(), ModFluids.NAPHTHA.get(), ModFluids.GASOLINE.get(),
                ModFluids.LPG.get()};
        Fluid[] flowing = {ModFluids.FLOWING_DIESEL.get(), ModFluids.FLOWING_NAPHTHA.get(),
                ModFluids.FLOWING_GASOLINE.get(), ModFluids.FLOWING_LPG.get()};
        String[] names = {"diesel", "naphtha", "gasoline", "lpg"};
        for (int i = 0; i < sources.length; i++) {
            ok(names[i] + " 判为液体（不是气体）", ModFluids.isLiquid(sources[i]) && !ModFluids.isGas(sources[i]));
            ok(names[i] + " 不在 #c:gaseous 里", !sources[i].defaultFluidState().is(Tags.Fluids.GASEOUS));
            ok("source 在 #c:" + names[i] + " 里", inTag(level, sources[i], names[i]));
            ok("flowing 在 #c:" + names[i] + " 里", inTag(level, flowing[i], names[i]));
        }
        ok("原油仍在 #c:crude_oil 里", inTag(level, ModFluids.CRUDE_OIL.get(), "crude_oil"));
    }

    private static boolean inTag(ServerLevel level, Fluid fluid, String path) {
        ResourceLocation id = BuiltInRegistries.FLUID.getKey(fluid);
        if (id == null) {
            return false;
        }
        TagKey<Fluid> key = TagKey.create(Registries.FLUID,
                ResourceLocation.fromNamespaceAndPath("c", path));
        return level.registryAccess().registryOrThrow(Registries.FLUID)
                .getHolder(ResourceKey.create(Registries.FLUID, id))
                .map(holder -> holder.is(key))
                .orElse(false);
    }
}
