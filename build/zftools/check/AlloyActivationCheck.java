package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF51 临时文件，验证完必须删）</b>：
 * 「主控必须先激活才能用」这条规则（用户：「类似于匠魂 他只是个控制器 需要先激活他」）。
 *
 * <p>要验的是**未激活时处处不能用、激活后处处能用**：</p>
 * <ol>
 *   <li>{@link AlloySmelterBlock#decide} 这个纯函数：未激活 ⇒ 一律 ACTIVATE（含 Shift），
 *       已激活 ⇒ 右键开界面、Shift 报状态；</li>
 *   <li>未激活：能量接口返回 null、10 个槽位一个都不收、界面标题是"主控"；</li>
 *   <li>激活后：这三样全部反过来。</li>
 * </ol>
 */
public final class AlloyActivationCheck {

    private static final String TAG = "[AK] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(176, 240, 176);
    private static final Direction FACING = Direction.SOUTH;

    private AlloyActivationCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloyActivationCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed += decideTable();
            failed += gates(event.getServer().overworld());
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

    /** ① 纯函数：右键该做什么。 */
    private static int decideTable() {
        System.out.println(TAG + "① right-click decision table");
        int failed = 0;
        failed += check("not formed + no shift  -> ACTIVATE",
                AlloySmelterBlock.decide(false, false) == AlloySmelterBlock.Action.ACTIVATE);
        failed += check("not formed + shift     -> ACTIVATE (Shift 也算激活，不开界面)",
                AlloySmelterBlock.decide(false, true) == AlloySmelterBlock.Action.ACTIVATE);
        failed += check("formed + no shift      -> OPEN_GUI",
                AlloySmelterBlock.decide(true, false) == AlloySmelterBlock.Action.OPEN_GUI);
        failed += check("formed + shift         -> STATUS",
                AlloySmelterBlock.decide(true, true) == AlloySmelterBlock.Action.STATUS);
        return failed;
    }

    /** ②③ 未激活 / 已激活 两种状态下的门禁。 */
    private static int gates(ServerLevel level) {
        System.out.println(TAG + "② gates before activation, then after");
        int failed = 0;
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
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
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return check("controller block entity exists", false);
        }
        var inv = be.getInventory();

        System.out.println(TAG + "  --- 未激活 ---");
        failed += check("isFormed() == false", !be.isFormed());
        failed += check("energy接口 = null（没激活灌不进电）", be.getEnergyStorage() == null);
        failed += check("输入槽不收铁锭", !inv.isItemValid(AlloySmelterBlockEntity.INPUT_FIRST,
                new ItemStack(Items.IRON_INGOT)));
        failed += check("输出槽不收", !inv.isItemValid(AlloySmelterBlockEntity.OUTPUT_FIRST,
                new ItemStack(Items.IRON_INGOT)));
        failed += check("消耗槽不收", !inv.isItemValid(AlloySmelterBlockEntity.CONSUME_FIRST,
                new ItemStack(Items.IRON_INGOT)));
        String notFormed = be.getDisplayName().getString();
        failed += check("界面标题 = 主控那个键（实际 \"" + notFormed + "\"）",
                be.getDisplayName().getString().equals(
                        net.minecraft.network.chat.Component.translatable("block.potato_s_t.alloy_smelter")
                                .getString()));

        // 接线口：结构没激活时也不传电（这条是 ZF49 就有的规则，这里回归一遍）
        if (level.getBlockEntity(be.portPositions().get(0)) instanceof AlloySmelterPortBlockEntity port) {
            failed += check("接线口也没电（未激活）", port.getEnergyStorage() == null);
        }

        System.out.println(TAG + "  --- 激活 ---");
        be.form();
        failed += check("isFormed() == true", be.isFormed());
        failed += check("energy接口 != null", be.getEnergyStorage() != null);
        failed += check("输入槽收铁锭", inv.isItemValid(AlloySmelterBlockEntity.INPUT_FIRST,
                new ItemStack(Items.IRON_INGOT)));
        failed += check("输入槽仍然不收红石",
                !inv.isItemValid(AlloySmelterBlockEntity.INPUT_FIRST, new ItemStack(Items.REDSTONE)));
        failed += check("消耗槽仍然锁着", !inv.isItemValid(AlloySmelterBlockEntity.CONSUME_FIRST,
                new ItemStack(Items.IRON_INGOT)));
        String formedName = be.getDisplayName().getString();
        failed += check("界面标题变成炉子那个键（实际 \"" + formedName + "\"）",
                be.getDisplayName().getString().equals(
                        net.minecraft.network.chat.Component.translatable("gui.potato_s_t.alloy_smelter.name")
                                .getString()));
        failed += check("两个标题不一样", !notFormed.equals(formedName));
        if (level.getBlockEntity(be.portPositions().get(0)) instanceof AlloySmelterPortBlockEntity port) {
            var storage = port.getEnergyStorage();
            failed += check("接线口有电了", storage != null);
            if (storage != null) {
                failed += check("能灌进 500 FE", storage.receiveEnergy(500, false) == 500
                        && be.getEnergyStored() == 500);
            }
        }
        // 再拆掉一格 ⇒ 每秒复查应当把 formed 打回 false（这里直接调 validate 验入口）
        level.setBlock(AlloySmelterStructure.offset(C, FACING, 1, 0, 0), Blocks.AIR.defaultBlockState(), 3);
        failed += check("砸掉一格后 validate() 报错", be.validateNow() != null);
        level.setBlock(AlloySmelterStructure.offset(C, FACING, 1, 0, 0),
                ModBlocks.WIRING_BLOCK.get().defaultBlockState(), 3);

        be.disassemble();
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
        return failed;
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
