package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF56 临时探针，验证完必须删）</b>：
 * 「主控 ≠ 大盒子」—— 模型必须跟着成型状态走。
 *
 * <p>用户原话：「不是主控变成4x5x4是合金炉！合金炉成型后模型！」</p>
 *
 * <p>要验的（每条都能单独失败）：</p>
 * <ol>
 *   <li>刚放下的主控：{@code isFormed()=false}、方块状态 {@code formed=false}（= 小方块）；</li>
 *   <li>成型后：{@code formed=true}（= 整台 4×5×4），而且<b>方块实体没被换掉</b>
 *       （槽位里塞的东西还在 —— 换状态要是把 BE 重建了，物品就没了）；</li>
 *   <li>挖掉一格 ⇒ 模型退回小方块、方块全部还原、控制器本体还在；</li>
 *   <li><b>扳手那条路</b>：成型状态下调 {@code disassemble()}（此刻控制器还在、外壳刚被还原成"完整"）
 *       ⇒ <b>绝不能当场自己重新成型</b>（这是 ZF56 最容易踩的坑）；</li>
 *   <li>把控制器那格挖成空气 ⇒ 那格必须**真的是空气**（切状态那次 setBlock 不许把控制器复活）。</li>
 * </ol>
 */
public final class AlloyFormedCheck {

    private static final String TAG = "[AF] ";
    private static final Direction FACING = Direction.SOUTH;
    private static boolean registered;
    private static final BlockPos F = new BlockPos(296, 260, 176);

    private AlloyFormedCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloyFormedCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
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

        // ---------- ① 刚放下的主控 ----------
        fillUniform(level);
        level.setBlock(offset(1, 4, 1), Blocks.AIR.defaultBlockState(), 3);   // 先留个洞，别让它自动成型
        level.setBlock(F, controllerState(), 3);
        if (!(level.getBlockEntity(F) instanceof AlloySmelterBlockEntity be)) {
            return check("controller block entity exists", false);
        }
        System.out.println(TAG + "(1) a freshly placed controller looks like the small block");
        failed += check("not formed yet", !be.isFormed());
        failed += check("blockstate formed=false (small cube)",
                !level.getBlockState(F).getValue(AlloySmelterBlock.FORMED));
        failed += check("the block exposes a formed property, default false",
                ModBlocks.ALLOY_SMELTER.get().defaultBlockState().hasProperty(AlloySmelterBlock.FORMED)
                        && !ModBlocks.ALLOY_SMELTER.get().defaultBlockState()
                                .getValue(AlloySmelterBlock.FORMED));

        // ---------- ② 补上缺口 ⇒ 自动成型，模型切成大盒子 ----------
        System.out.println(TAG + "(2) closing the shell -> formed=true (the 4x5x4 furnace)");
        be.getInventory().setStackInSlot(0, new ItemStack(net.minecraft.world.item.Items.IRON_INGOT, 7));
        level.setBlock(offset(1, 4, 1), ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
        failed += check("auto-formed", be.isFormed());
        failed += check("blockstate formed=true (the whole furnace)",
                level.getBlockState(F).getValue(AlloySmelterBlock.FORMED));
        failed += check("controller cell is still the controller block",
                level.getBlockState(F).is(ModBlocks.ALLOY_SMELTER.get()));
        failed += check("same block entity instance (not recreated by the state change)",
                level.getBlockEntity(F) == be);
        failed += check("the stack in slot 0 survived (7 iron ingots)",
                level.getBlockEntity(F) instanceof AlloySmelterBlockEntity b2
                        && b2.getInventory().getStackInSlot(0).getCount() == 7);

        // ---------- ③ 挖一格部件格 ⇒ 退回小方块 ----------
        System.out.println(TAG + "(3) mining one part cell -> back to the small block");
        BlockPos victim = offset(0, 2, 1);
        level.destroyBlock(victim, true);
        failed += check("de-formed", !be.isFormed());
        failed += check("blockstate back to formed=false",
                !level.getBlockState(F).getValue(AlloySmelterBlock.FORMED));
        failed += check("controller block itself is still there (not destroyed with the shell)",
                level.getBlockState(F).is(ModBlocks.ALLOY_SMELTER.get()));
        failed += check("no part/port cell left (got " + leftovers(level) + ")", leftovers(level) == 0);

        // ---------- ④ 扳手那条路：外壳刚还原成"完整"，不许自己重新成型 ----------
        System.out.println(TAG + "(4) wrench path: disassemble() must not re-form itself");
        level.setBlock(victim, Blocks.GOLD_BLOCK.defaultBlockState(), 3);   // 放个别的东西先占着
        level.setBlock(victim, ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
        AlloySmelterBlock.tryAutoForm(level, F);
        failed += check("re-formed for the wrench test", be.isFormed());
        failed += check("blockstate formed=true again",
                level.getBlockState(F).getValue(AlloySmelterBlock.FORMED));
        be.disassemble();
        failed += check("disassemble() did NOT re-form itself", !be.isFormed());
        failed += check("blockstate formed=false after disassemble",
                !level.getBlockState(F).getValue(AlloySmelterBlock.FORMED));
        failed += check("shell really restored, nothing left (got " + leftovers(level) + ")",
                leftovers(level) == 0);
        failed += check("controller survived the disassembly",
                level.getBlockState(F).is(ModBlocks.ALLOY_SMELTER.get()));

        // ---------- ⑤ 挖掉控制器那格：切状态不许把方块复活 ----------
        System.out.println(TAG + "(5) mining the controller itself: the cell must stay air");
        level.setBlock(F, Blocks.AIR.defaultBlockState(), 3);
        failed += check("controller cell is air, not resurrected by applyFormedState()",
                level.getBlockState(F).isAir());
        clear(level);
        return failed;
    }

    // ==================== 工具 ====================
    private static BlockState controllerState() {
        return ModBlocks.ALLOY_SMELTER.get().defaultBlockState()
                .setValue(AlloySmelterBlock.FACING, FACING);
    }

    /** 80 格全填一般金属块，两处接线块照图纸摆（控制器那格留空）。 */
    private static void fillUniform(ServerLevel level) {
        BlockState metal = ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState();
        for (BlockPos p : AlloySmelterStructure.positions(F, FACING)) {
            level.setBlock(p, metal, 3);
        }
        BlockState wire = ModBlocks.WIRING_BLOCK.get().defaultBlockState();
        level.setBlock(offset(1, 0, 0), wire, 3);
        level.setBlock(offset(1, 0, 3), wire, 3);
    }

    private static int leftovers(ServerLevel level) {
        int count = 0;
        for (BlockPos p : AlloySmelterStructure.positions(F, FACING)) {
            BlockState s = level.getBlockState(p);
            if (s.is(ModBlocks.ALLOY_SMELTER_PART.get()) || s.is(ModBlocks.ALLOY_SMELTER_PORT.get())) {
                count++;
            }
        }
        return count;
    }

    private static BlockPos offset(int y, int j, int i) {
        return AlloySmelterStructure.offset(F, FACING, y, j, i);
    }

    private static void clear(ServerLevel level) {
        // 先干掉控制器：它一没，部件格的 onRemove 就找不到控制器，不会边拆边还原
        level.setBlock(F, Blocks.AIR.defaultBlockState(), 3);
        for (BlockPos p : AlloySmelterStructure.positions(F, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
