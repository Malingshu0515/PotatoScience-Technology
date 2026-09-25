package com.potatost.mod;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF49 临时文件，验证完必须删）</b>：合金冶炼炉多方块。
 *
 * <p>用户给的是一张<b>文字图纸</b>（4 层 × 5 排 × 4 列），本探针的核心就是
 * <b>把图纸的格数与各材料数量照着原文数一遍</b>（§4.27：期望值照规格另写，不读被测常量），
 * 再在真世界里<b>盖一遍、拆一格、成型、通电、试槽位、拆解</b>。</p>
 *
 * <p>期望值硬写：80 格 / 58 个方块 / 22 格空气；一般金属块 14、加热装置 6、耐热金属块 26、
 * 接线块 2、高炉 6、控制器 1、漏斗 1、炼药锅 1、散热装置 1；储能 32k；槽位 5+3+2。</p>
 */
public final class AlloySmelterCheck {

    private static final String TAG = "[AS] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(176, 220, 176);
    private static final Direction FACING = Direction.SOUTH;

    private AlloySmelterCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloySmelterCheck.class);
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
            failed += patternCounts();
            failed += slotsAndEnergy();
            failed += buildAndValidate(level);
            failed += formAndPower(level);
            failed += disassemble(level);
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

    // ================= ① 图纸数一遍 =================
    private static int patternCounts() {
        System.out.println(TAG + "① pattern transcription (count every material against the drawing)");
        int failed = 0;
        int[] counts = new int[AlloySmelterStructure.Kind.values().length];
        Set<BlockPos> all = new HashSet<>();
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    AlloySmelterStructure.Kind k = AlloySmelterStructure.kindAt(y, j, i);
                    failed += check("kindAt(" + y + "," + j + "," + i + ") != null", k != null);
                    if (k != null) {
                        counts[k.ordinal()]++;
                        all.add(AlloySmelterStructure.offset(BlockPos.ZERO, FACING, y, j, i));
                    }
                }
            }
        }
        int expectCommon = 14;
        int expectHeater = 6;
        int expectHr = 26;
        int expectWiring = 2;
        int expectBlast = 6;
        int expectController = 1;
        int expectHopper = 1;
        int expectCauldron = 1;
        int expectSink = 1;
        int expectAir = 22;
        int solid = expectCommon + expectHeater + expectHr + expectWiring + expectBlast
                + expectController + expectHopper + expectCauldron + expectSink;
        failed += check("80 cells total (got " + all.size() + ")", all.size() == AlloySmelterStructure.CELLS);
        failed += check("58 solid blocks (got " + solid + ")", solid == 58);
        failed += check("common_metal_block x" + expectCommon + " (got " + counts[AlloySmelterStructure.Kind.COMMON.ordinal()] + ")",
                counts[AlloySmelterStructure.Kind.COMMON.ordinal()] == expectCommon);
        failed += check("heater x" + expectHeater + " (got " + counts[AlloySmelterStructure.Kind.HEATER.ordinal()] + ")",
                counts[AlloySmelterStructure.Kind.HEATER.ordinal()] == expectHeater);
        failed += check("heat_resistant x" + expectHr + " (got " + counts[AlloySmelterStructure.Kind.HEAT_RESISTANT.ordinal()] + ")",
                counts[AlloySmelterStructure.Kind.HEAT_RESISTANT.ordinal()] == expectHr);
        failed += check("wiring_block x" + expectWiring + " (got " + counts[AlloySmelterStructure.Kind.WIRING.ordinal()] + ")",
                counts[AlloySmelterStructure.Kind.WIRING.ordinal()] == expectWiring);
        failed += check("blast_furnace x" + expectBlast + " (got " + counts[AlloySmelterStructure.Kind.BLAST_FURNACE.ordinal()] + ")",
                counts[AlloySmelterStructure.Kind.BLAST_FURNACE.ordinal()] == expectBlast);
        failed += check("controller x" + expectController + " (got " + counts[AlloySmelterStructure.Kind.CONTROLLER.ordinal()] + ")",
                counts[AlloySmelterStructure.Kind.CONTROLLER.ordinal()] == expectController);
        failed += check("hopper x" + expectHopper + ", cauldron x" + expectCauldron + ", heat_sink x" + expectSink,
                counts[AlloySmelterStructure.Kind.HOPPER.ordinal()] == expectHopper
                        && counts[AlloySmelterStructure.Kind.CAULDRON.ordinal()] == expectCauldron
                        && counts[AlloySmelterStructure.Kind.HEAT_SINK.ordinal()] == expectSink);
        failed += check("air x" + expectAir + " (got " + counts[AlloySmelterStructure.Kind.AIR.ordinal()] + ")",
                counts[AlloySmelterStructure.Kind.AIR.ordinal()] == expectAir);
        // 层 4 的"只重复耐热环"：炼药锅/散热装置各只有 1 个（若照另一种读法会出现 2 个）
        failed += check("layer 4 has no second cauldron/heat sink row",
                counts[AlloySmelterStructure.Kind.CAULDRON.ordinal()] == 1
                        && counts[AlloySmelterStructure.Kind.HEAT_SINK.ordinal()] == 1);
        failed += check("layer 4 back row has 2 air at the ends",
                AlloySmelterStructure.kindAt(3, 0, 0) == AlloySmelterStructure.Kind.AIR
                        && AlloySmelterStructure.kindAt(3, 0, 3) == AlloySmelterStructure.Kind.AIR
                        && AlloySmelterStructure.kindAt(3, 0, 1) == AlloySmelterStructure.Kind.HEAT_RESISTANT
                        && AlloySmelterStructure.kindAt(3, 0, 2) == AlloySmelterStructure.Kind.HEAT_RESISTANT);
        return failed;
    }

    // ================= ② 槽位与储能（纯对象） =================
    private static int slotsAndEnergy() {
        System.out.println(TAG + "② slots and energy constants");
        int failed = 0;
        failed += check("MAX_ENERGY = 32k (got " + AlloySmelterBlockEntity.MAX_ENERGY + ")",
                AlloySmelterBlockEntity.MAX_ENERGY == 32 * 1024);
        failed += check("5 input + 3 output + 2 consume = 10 slots (got "
                        + AlloySmelterBlockEntity.SLOT_COUNT + ")",
                AlloySmelterBlockEntity.INPUT_COUNT == 5 && AlloySmelterBlockEntity.OUTPUT_COUNT == 3
                        && AlloySmelterBlockEntity.CONSUME_COUNT == 2
                        && AlloySmelterBlockEntity.SLOT_COUNT == 10);
        return failed;
    }

    // ================= ③ 盖一遍 + 验结构 + 拆一格 =================
    private static int buildAndValidate(ServerLevel level) {
        System.out.println(TAG + "③ build it in the world, validate, then break one cell");
        int failed = 0;
        cleanup(level);
        build(level);
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return check("controller block entity exists", false);
        }
        failed += check("validate() == null on a correct build",
                AlloySmelterStructure.validate(level, C, FACING) == null);

        // 反向：抽掉一格（第 3 层 · 第 2 排 · 第 1 列 —— 那一格按图纸是**耐热金属块**）
        // ⚠ 第一版写的是 (2,1,1)，可那一格按图纸是**空气**（耐热环在 i=0 与 i=3，中间是空腔）
        //   ⇒ 往空气格摆空气当然还是"合法"，于是三条断言一起假失败。坐标要照图纸挑。
        int by = 2, bj = 1, bi = 0;
        BlockPos broken = AlloySmelterStructure.offset(C, FACING, by, bj, bi);
        level.setBlock(broken, Blocks.AIR.defaultBlockState(), 3);
        AlloySmelterStructure.Problem p = AlloySmelterStructure.validate(level, C, FACING);
        failed += check("broken cell reported as (y=" + (by + 1) + ", j=" + (bj + 1) + ", i=" + (bi + 1) + ")",
                p != null && p.y() == by && p.j() == bj && p.i() == bi);
        failed += check("problem says expected heat_resistant (got "
                        + (p == null ? "null" : p.expected().getName().getString()) + ")",
                p != null && p.expected() == ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get());
        level.setBlock(broken, ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get().defaultBlockState(), 3);
        failed += check("validate() clean again after putting it back",
                AlloySmelterStructure.validate(level, C, FACING) == null);
        return failed;
    }

    // ================= ④ 成型 + 接线口传电 =================
    private static int formAndPower(ServerLevel level) {
        System.out.println(TAG + "④ form, then feed energy through a port");
        int failed = 0;
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return check("controller block entity exists", false);
        }
        List<BlockPos> ports = be.portPositions();
        failed += check("2 port cells (got " + ports.size() + ")", ports.size() == 2);
        boolean wiringBefore = ports.stream()
                .allMatch(q -> level.getBlockState(q).is(ModBlocks.WIRING_BLOCK.get()));
        failed += check("before forming: both are plain wiring blocks", wiringBefore);

        be.form();
        boolean portsNow = ports.stream()
                .allMatch(q -> level.getBlockState(q).is(ModBlocks.ALLOY_SMELTER_PORT.get()));
        failed += check("after forming: both became alloy_smelter_port", portsNow);
        failed += check("isFormed() == true", be.isFormed());

        if (level.getBlockEntity(ports.get(0)) instanceof AlloySmelterPortBlockEntity port) {
            var storage = port.getEnergyStorage();
            failed += check("port exposes an IEnergyStorage", storage != null);
            if (storage != null) {
                int accepted = storage.receiveEnergy(1000, false);
                failed += check("port accepted 1000 FE (got " + accepted + ")", accepted == 1000);
                failed += check("controller now holds 1000 FE (got " + be.getEnergyStored() + ")",
                        be.getEnergyStored() == 1000);
                int over = storage.receiveEnergy(AlloySmelterBlockEntity.MAX_ENERGY, false);
                failed += check("buffer caps at 32k (got " + be.getEnergyStored() + " after offering 32k more)",
                        be.getEnergyStored() == AlloySmelterBlockEntity.MAX_ENERGY);
            }
        } else {
            failed += check("port block entity exists", false);
        }

        // 槽位规则
        var inv = be.getInventory();
        failed += check("input slot accepts iron ingot (c:ingots)",
                inv.isItemValid(AlloySmelterBlockEntity.INPUT_FIRST, new ItemStack(Items.IRON_INGOT)));
        failed += check("input slot accepts our own cobalt ingot",
                inv.isItemValid(AlloySmelterBlockEntity.INPUT_FIRST,
                        new ItemStack(ModItems.COBALT_INGOT.get())));
        failed += check("input slot REJECTS redstone",
                !inv.isItemValid(AlloySmelterBlockEntity.INPUT_FIRST, new ItemStack(Items.REDSTONE)));
        failed += check("input slot REJECTS raw iron (not an ingot)",
                !inv.isItemValid(AlloySmelterBlockEntity.INPUT_FIRST, new ItemStack(Items.RAW_IRON)));
        failed += check("output slot rejects everything",
                !inv.isItemValid(AlloySmelterBlockEntity.OUTPUT_FIRST, new ItemStack(Items.IRON_INGOT)));
        failed += check("consume slot is locked (user: 目前放不了东西)",
                !inv.isItemValid(AlloySmelterBlockEntity.CONSUME_FIRST, new ItemStack(Items.IRON_INGOT))
                        && !inv.isItemValid(AlloySmelterBlockEntity.CONSUME_FIRST + 1,
                        new ItemStack(Items.DIAMOND)));
        return failed;
    }

    // ================= ⑤ 拆解 =================
    private static int disassemble(ServerLevel level) {
        System.out.println(TAG + "⑤ disassemble restores the wiring blocks");
        int failed = 0;
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return check("controller block entity exists", false);
        }
        be.disassemble();
        boolean restored = be.portPositions().stream()
                .allMatch(q -> level.getBlockState(q).is(ModBlocks.WIRING_BLOCK.get()));
        failed += check("both ports are wiring blocks again", restored);
        failed += check("isFormed() == false", !be.isFormed());
        if (level.getBlockEntity(be.portPositions().get(0)) instanceof AlloySmelterPortBlockEntity gone) {
            failed += check("port no longer exposes energy after disassembly",
                    gone.getEnergyStorage() == null);
        }
        return failed;
    }

    // ================= 工具 =================
    private static void build(ServerLevel level) {
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    AlloySmelterStructure.Kind kind = AlloySmelterStructure.kindAt(y, j, i);
                    Block b = AlloySmelterStructure.blockFor(kind);
                    // ⚠ 控制器那一格必须**显式写朝向**：`defaultBlockState()` 是 NORTH，
                    //   而本探针按 SOUTH 摆图案 —— 第一版漏了这一步，于是 `be.portPositions()`
                    //   按 NORTH 算出来的两格根本不是接线块，四条断言连着假失败。
                    var state = b.defaultBlockState();
                    if (kind == AlloySmelterStructure.Kind.CONTROLLER) {
                        state = state.setValue(AlloySmelterBlock.FACING, FACING);
                    }
                    level.setBlock(AlloySmelterStructure.offset(C, FACING, y, j, i), state, 3);
                }
            }
        }
    }

    private static void cleanup(ServerLevel level) {
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
