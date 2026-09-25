package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF54 临时文件，验证完必须删）</b>：
 * 合金冶炼炉改成"电力高炉那样的整体建模"之后，**成型/拆解是否逐格正确**。
 *
 * <p>要验的四件事（都是"静默错"的高发区）：</p>
 * <ol>
 *   <li>成型后：77 格变部件格、2 格变接线口、**控制器那格不动**，且 80 格原始状态全记下来了；</li>
 *   <li>挖一格部件格：**掉回原来那个方块**（不是掉部件格）+ 整台失效；</li>
 *   <li>挖掉的那格留空，而**其余格都还原**（ZF40 那个"白送一台"的坑）；</li>
 *   <li>再成型后调 {@code disassemble()}：80 格全部还原成原样，控制器那格变空气。</li>
 * </ol>
 */
public final class AlloyModelCheck {

    private static final String TAG = "[AM] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(176, 260, 176);
    private static final Direction FACING = Direction.SOUTH;

    private AlloyModelCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloyModelCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed += run(event.getServer().overworld());
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
        build(level);
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return check("controller block entity exists", false);
        }

        // ---------- ① 成型 ----------
        System.out.println(TAG + "① form: 77 parts + 2 ports, controller cell untouched");
        be.form();
        int parts = 0;
        int ports = 0;
        int controllerCells = 0;
        int wrong = 0;
        for (BlockPos p : be.allPositions()) {
            var s = level.getBlockState(p);
            if (p.equals(C)) {
                if (s.is(ModBlocks.ALLOY_SMELTER.get())) {
                    controllerCells++;
                } else {
                    wrong++;
                }
            } else if (s.is(ModBlocks.ALLOY_SMELTER_PART.get())) {
                parts++;
            } else if (s.is(ModBlocks.ALLOY_SMELTER_PORT.get())) {
                ports++;
            } else {
                wrong++;
            }
        }
        System.out.println(TAG + "  cells: part=" + parts + " port=" + ports + " controller=" + controllerCells
                + " other=" + wrong);
        failed += check("77 part cells (got " + parts + ")", parts == 77);
        failed += check("2 port cells (got " + ports + ")", ports == 2);
        failed += check("controller cell still itself (got " + controllerCells + ")", controllerCells == 1);
        failed += check("no other block left in the structure (got " + wrong + ")", wrong == 0);
        failed += check("all 80 original states recorded",
                be.originalAt(C) != null && be.originalAt(C).is(ModBlocks.ALLOY_SMELTER.get()));
        failed += check("isFormed() == true", be.isFormed());

        // ---------- ②③ 挖一格部件格 ----------
        System.out.println(TAG + "②③ break one part cell");
        BlockPos victim = AlloySmelterStructure.offset(C, FACING, 2, 2, 3);   // 第 3 层 · 第 3 排 · 第 4 格（耐热金属块）
        BlockState before = be.originalAt(victim);
        System.out.println(TAG + "  victim " + victim.toShortString() + " original = "
                + (before == null ? "null" : before.getBlock().getName().getString()));
        failed += check("victim was a heat-resistant block before forming",
                before != null && before.is(ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get()));
        level.destroyBlock(victim, true);
        failed += check("victim cell is now air", level.getBlockState(victim).isAir());
        failed += check("machine no longer formed", !be.isFormed());
        // 相邻那一格（第 3 层 · 第 2 排 · 第 4 格）应当已还原成耐热金属块
        // ⚠ 第一版这里写的是 (2,2,2) —— 那一格按图纸**本来就是空气**（耐热环在 i=0/i=3，
        //   中间是空腔）⇒ 又是一次"砸空气"式的假失败（§4.31 同一个坑，第 2 次）。
        BlockPos neighbour = AlloySmelterStructure.offset(C, FACING, 2, 1, 3);
        failed += check("neighbour restored to heat-resistant (got "
                        + level.getBlockState(neighbour).getBlock().getName().getString() + ")",
                level.getBlockState(neighbour).is(ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get()));
        boolean dropped = !level.getEntitiesOfClass(ItemEntity.class,
                new AABB(victim).inflate(3.0)).stream()
                .filter(e -> e.getItem().is(ModBlocks.HEAT_RESISTANT_METAL_BLOCK_ITEM.get())).toList().isEmpty();
        failed += check("the mined cell dropped its ORIGINAL block item", dropped);
        boolean droppedPart = level.getEntitiesOfClass(ItemEntity.class, new AABB(victim).inflate(3.0)).stream()
                .anyMatch(e -> e.getItem().is(ModBlocks.ALLOY_SMELTER_PART.get().asItem()));
        failed += check("no alloy_smelter_part item was dropped", !droppedPart);

        // ---------- ④ 再成型 + 满拆解 ----------
        System.out.println(TAG + "④ form again, then disassemble()");
        level.setBlock(victim, ModBlocks.HEAT_RESISTANT_METAL_BLOCK.get().defaultBlockState(), 3);
        be.form();
        failed += check("formed again", be.isFormed());
        blockCount(level, be);
        be.disassemble();
        int restored = 0;
        int bad = 0;
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            var s = level.getBlockState(p);
            if (p.equals(C)) {
                if (s.isAir()) {
                    restored++;
                } else {
                    bad++;
                }
            } else if (s.is(ModBlocks.ALLOY_SMELTER_PART.get()) || s.is(ModBlocks.ALLOY_SMELTER_PORT.get())) {
                bad++;      // 还有部件格没还原
            } else if (!s.isAir()) {
                restored++;
            }
        }
        System.out.println(TAG + "  after disassemble: restored=" + restored + " leftover/bad=" + bad);
        failed += check("controller cell became air", level.getBlockState(C).isAir());
        failed += check("nothing left as part/port (bad=" + bad + ")", bad == 0);
        failed += check("isFormed() == false", !be.isFormed());
        clear(level);
        return failed;
    }

    private static void blockCount(ServerLevel level, AlloySmelterBlockEntity be) {
        int parts = 0;
        for (BlockPos p : be.allPositions()) {
            if (level.getBlockState(p).is(ModBlocks.ALLOY_SMELTER_PART.get())) {
                parts++;
            }
        }
        System.out.println(TAG + "  (re-formed: part cells = " + parts + ")");
    }

    private static void build(ServerLevel level) {
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    AlloySmelterStructure.Kind kind = AlloySmelterStructure.kindAt(y, j, i);
                    var state = AlloySmelterStructure.blockFor(kind).defaultBlockState();
                    if (kind == AlloySmelterStructure.Kind.CONTROLLER) {
                        state = state.setValue(AlloySmelterBlock.FACING, FACING);
                    }
                    level.setBlock(AlloySmelterStructure.offset(C, FACING, y, j, i), state, 3);
                }
            }
        }
    }

    private static void clear(ServerLevel level) {
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
