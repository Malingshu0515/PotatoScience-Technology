package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF59 临时探针，验证完必须删）</b>：
 * 「等第四层摆完再成型」—— 顶面那 10 格也进判定（要查 58 格）。
 *
 * <p>要验的：</p>
 * <ol>
 *   <li><b>只搭前三层不许成型</b>：缺 10 格、判定不成立、连心跳那条路（{@code tryAutoForm}）也不许成型；</li>
 *   <li><b>摆完第四层才成型</b>；</li>
 *   <li><b>映射是手算的</b>：两处接线块（图纸第 2 层 j=0 的 i=0 与 i=3）在世界里必须是
 *       {@code C+(3,0,-4)} 与 {@code C+(0,0,-4)}（南向：向后 = −Z、向右 = +X）；</li>
 *   <li><b>成型账目</b>：表面 68 格里图纸有方块的 58 格 → 主控 1 + 接线口 2 + 部件格 55；
 *       顶面空着的 10 格保持空气；内部 12 格原样；</li>
 *   <li><b>成型之后再往表面空格补机器方块</b> ⇒ 会被吸收（否则和 OBJ 盒子 z-fighting）；</li>
 *   <li><b>拆解</b>：挖接线口 / 扳手满拆，方块全部还原、不留隐形格。</li>
 * </ol>
 */
public final class AlloyLayoutCheck {

    private static final String TAG = "[AL] ";
    private static final Direction FACING = Direction.SOUTH;
    private static final BlockPos C = new BlockPos(320, 260, 176);
    private static boolean registered;
    private static final java.util.List<String> DROP_LOG = new java.util.ArrayList<>();

    private AlloyLayoutCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloyLayoutCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onEntityJoin(net.neoforged.neoforge.event.entity.EntityJoinLevelEvent event) {
        if (event.getEntity() instanceof ItemEntity item) {
            DROP_LOG.add(item.getItem().getItem().getDescriptionId() + " @ "
                    + item.blockPosition().toShortString());
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            failed += run(level);
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

    private static int run(ServerLevel level) {
        int failed = 0;
        clear(level);

        // ---------- ① 只搭前三层 ⇒ 不许成型（ZF59 的核心） ----------
        System.out.println(TAG + "(1) three layers only -> must NOT form");
        buildLayer(level, 0);
        buildLayer(level, 1);
        buildLayer(level, 2);
        AlloySmelterStructure.Report missingRoof = AlloySmelterStructure.inspect(level, C, FACING, 16);
        failed += check("three layers: the 10 roof cells are missing (holes=" + missingRoof.holeCount() + ")",
                missingRoof.holeCount() == 10 && !missingRoof.ok());
        AlloySmelterBlock.tryAutoForm(level, C);              // 心跳那条路也不许成型
        boolean early = level.getBlockEntity(C) instanceof AlloySmelterBlockEntity e0 && e0.isFormed();
        failed += check("three layers only: NOT formed (even via tryAutoForm)", !early);
        failed += check("blockstate still formed=false",
                !level.getBlockState(C).getValue(AlloySmelterBlock.FORMED));

        // ---------- ② 摆完第四层 ⇒ 才成型 ----------
        System.out.println(TAG + "(2) finishing the roof -> now it forms");
        buildLayer(level, 3);
        AlloySmelterBlock.tryAutoForm(level, C);
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return failed + check("controller block entity exists", false);
        }
        failed += check("roof finished: auto-formed", be.isFormed());
        AlloySmelterStructure.Report full = AlloySmelterStructure.inspect(level, C, FACING, 16);
        failed += check("full drawing is ok (holes=" + full.holeCount() + " wiring=" + full.wiring() + ")",
                full.ok() && full.holeCount() == 0 && full.wiring() == 2);

        // ---------- ③ 手算的世界坐标 ----------
        System.out.println(TAG + "(3) hand-derived world positions (NOT copied from offset())");
        BlockPos wire1 = C.offset(3, 0, -4);      // 图纸第2层 j=0 的 i=0（最远那一角）
        BlockPos wire2 = C.offset(0, 0, -4);      // 图纸第2层 j=0 的 i=3（主控正后方）
        failed += check("wiring cell (1,0,0) is at C+(3,0,-4) (got "
                + level.getBlockState(wire1).getBlock().getName().getString() + ")",
                AlloySmelterStructure.isWiring(level.getBlockState(wire1)));
        failed += check("wiring cell (1,0,3) is at C+(0,0,-4) (got "
                + level.getBlockState(wire2).getBlock().getName().getString() + ")",
                AlloySmelterStructure.isWiring(level.getBlockState(wire2)));
        failed += check("both of them are POWER PORTS now",
                level.getBlockState(wire1).is(ModBlocks.ALLOY_SMELTER_PORT.get())
                        && level.getBlockState(wire2).is(ModBlocks.ALLOY_SMELTER_PORT.get()));
        failed += check("main block is in the right-hand column (CTRL_I=3)",
                AlloySmelterStructure.CTRL_I == 3);

        // ---------- ④ 成型账目 ----------
        System.out.println(TAG + "(4) forming tallies");
        for (int y = 1; y <= 2; y++) {
            for (int j = 1; j <= 3; j++) {
                for (int i = 1; i <= 2; i++) {
                    level.setBlock(AlloySmelterStructure.offset(C, FACING, y, j, i),
                            Blocks.GOLD_BLOCK.defaultBlockState(), 3);
                }
            }
        }
        int parts = 0;
        int ports = 0;
        int roofAir = 0;
        int gold = 0;
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    if (!AlloySmelterStructure.isHull(y, j, i)) {
                        continue;
                    }
                    BlockState s = level.getBlockState(AlloySmelterStructure.offset(C, FACING, y, j, i));
                    if (s.is(ModBlocks.ALLOY_SMELTER_PART.get())) {
                        parts++;
                    } else if (s.is(ModBlocks.ALLOY_SMELTER_PORT.get())) {
                        ports++;
                    } else if (s.isAir()) {
                        roofAir++;
                    }
                }
            }
        }
        for (int y = 1; y <= 2; y++) {
            for (int j = 1; j <= 3; j++) {
                for (int i = 1; i <= 2; i++) {
                    if (level.getBlockState(AlloySmelterStructure.offset(C, FACING, y, j, i))
                            .is(Blocks.GOLD_BLOCK)) {
                        gold++;
                    }
                }
            }
        }
        System.out.println(TAG + "  hull: part=" + parts + " port=" + ports + " roofAir=" + roofAir);
        failed += check("55 part cells (58 filled - 1 controller - 2 ports) (got " + parts + ")", parts == 55);
        failed += check("2 port cells (got " + ports + ")", ports == 2);
        failed += check("10 empty roof cells stay air (got " + roofAir + ")", roofAir == 10);
        failed += check("the 12 inner cells are untouched gold (got " + gold + ")", gold == 12);
        failed += check("blockstate formed=true (whole furnace)",
                level.getBlockState(C).getValue(AlloySmelterBlock.FORMED));
        List<BlockPos> portPositions = be.portPositions();
        failed += check("portPositions() = exactly the two wiring cells (got " + portPositions.size() + ")",
                portPositions.size() == 2 && portPositions.contains(wire1) && portPositions.contains(wire2));

        // ---------- ⑤ 成型后再往表面空格补一块 ⇒ 吸收 ----------
        System.out.println(TAG + "(5) a block placed into an empty hull cell AFTER forming gets absorbed");
        BlockPos extra = AlloySmelterStructure.offset(C, FACING, 3, 4, 0);   // 图纸里是空的（顶面第一列）
        failed += check("that cell is air before the test", level.getBlockState(extra).isAir());
        level.setBlock(extra, ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get().defaultBlockState(), 3);
        failed += check("it is a visible block right now",
                level.getBlockState(extra).is(ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get()));
        be.absorbNewHullBlocks();
        failed += check("absorb: it became a part cell",
                level.getBlockState(extra).is(ModBlocks.ALLOY_SMELTER_PART.get()));
        failed += check("absorb: its original was recorded (heat-resistant block)",
                be.originalAt(extra) != null
                        && be.originalAt(extra).is(ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get()));
        failed += check("absorb: still formed", be.isFormed());

        // ---------- ⑥ 挖接线口 + 扳手拆解 ----------
        System.out.println(TAG + "(6) mine a port, then the wrench path");
        level.destroyBlock(wire1, true);
        failed += check("mining a port drops a WIRING BLOCK (ledger)",
                DROP_LOG.stream().anyMatch(s -> s.contains("potato_s_t.wiring_block")));
        failed += check("no part/port left after the break", leftovers(level) == 0);
        failed += check("de-formed, controller alive",
                !be.isFormed() && level.getBlockState(C).is(ModBlocks.ALLOY_SMELTER.get()));
        level.setBlock(wire1, ModBlocks.WIRING_BLOCK.get().defaultBlockState(), 3);
        AlloySmelterBlock.tryAutoForm(level, C);
        failed += check("re-formed for the wrench test", be.isFormed());
        be.disassemble();
        failed += check("disassemble() did not re-form itself", !be.isFormed() && leftovers(level) == 0);
        failed += check("blockstate back to formed=false",
                !level.getBlockState(C).getValue(AlloySmelterBlock.FORMED));
        clear(level);
        return failed;
    }

    /** 按图纸摆某一层（空气格也照摆，等于清干净）。 */
    private static void buildLayer(ServerLevel level, int y) {
        for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
            for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                AlloySmelterStructure.Kind kind = AlloySmelterStructure.kindAt(y, j, i);
                BlockState state = kind == AlloySmelterStructure.Kind.CONTROLLER
                        ? ModBlocks.ALLOY_SMELTER.get().defaultBlockState()
                                .setValue(AlloySmelterBlock.FACING, FACING)
                        : AlloySmelterStructure.blockFor(kind).defaultBlockState();
                level.setBlock(AlloySmelterStructure.offset(C, FACING, y, j, i), state, 3);
            }
        }
    }

    private static int leftovers(ServerLevel level) {
        int count = 0;
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            BlockState s = level.getBlockState(p);
            if (s.is(ModBlocks.ALLOY_SMELTER_PART.get()) || s.is(ModBlocks.ALLOY_SMELTER_PORT.get())) {
                count++;
            }
        }
        return count;
    }

    private static void clear(ServerLevel level) {
        level.setBlock(C, Blocks.AIR.defaultBlockState(), 3);
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
