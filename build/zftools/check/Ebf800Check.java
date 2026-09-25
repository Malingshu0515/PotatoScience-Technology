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
 * ⚠⚠ <b>诊断工具（ZF44 临时文件，验证完必须删）</b>：验"每件 800 FE"。
 *
 * <p>这次的重点是**先算再跑**：每件从 80 提到 800，最坏单 tick 耗电翻十倍，
 * 储能必须跟着上去，否则又回到 ZF42 那个"塞满却一动不动"。
 * 期望值全部照用户原话与算术硬写（§4.27）。</p>
 */
public final class Ebf800Check {

    private static final String TAG = "[EBF800] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(144, 220, 144);

    // ===== 规格 / 算术（硬写）=====
    private static final int SPEC_SECONDS = 10;
    private static final int SPEC_TICKS = SPEC_SECONDS * 20;
    private static final int SPEC_FE_PER_ITEM = 800;
    private static final int SPEC_SLOTS = 12;
    private static final int SPEC_STACK = 64;
    private static final long SPEC_WORST_BATCH = (long) SPEC_SLOTS * SPEC_STACK * SPEC_FE_PER_ITEM;
    private static final long SPEC_WORST_DEMAND = (SPEC_WORST_BATCH + SPEC_TICKS - 1) / SPEC_TICKS;

    private Ebf800Check() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Ebf800Check.class);
            System.out.println(TAG + "诊断钩子已注册（game 总线）");
        } catch (Throwable t) {
            System.out.println(TAG + "注册失败：" + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed = run(event.getServer().overworld());
        } catch (Throwable t) {
            System.out.println(TAG + "验算抛异常：" + t);
            t.printStackTrace();
            failed = 1;
        } finally {
            System.out.println(TAG + "结论：" + (failed == 0 ? "全部成立" : "**有 " + failed + " 项不符**"));
            System.out.println(TAG + "诊断结束，请求关服");
            event.getServer().halt(false);
        }
    }

    private static int run(ServerLevel level) {
        int failed = 0;
        Direction facing = Direction.SOUTH;

        failed += check("ENERGY_PER_ITEM = " + SPEC_FE_PER_ITEM + "（实际 "
                        + ElectricBlastFurnaceBlockEntity.ENERGY_PER_ITEM + "）",
                ElectricBlastFurnaceBlockEntity.ENERGY_PER_ITEM == SPEC_FE_PER_ITEM);
        failed += check("DURATION_TICKS = " + SPEC_SECONDS + " 秒 = " + SPEC_TICKS + "（实际 "
                        + ElectricBlastFurnaceBlockEntity.DURATION_TICKS + "）",
                ElectricBlastFurnaceBlockEntity.DURATION_TICKS == SPEC_TICKS);
        System.out.println(TAG + "  算术：最坏 " + SPEC_SLOTS + " 槽 × " + SPEC_STACK + " 件 × "
                + SPEC_FE_PER_ITEM + " FE = " + SPEC_WORST_BATCH + " FE 整批，摊到 " + SPEC_TICKS
                + " tick = " + SPEC_WORST_DEMAND + " FE/t；储能 = "
                + ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
        // 这条是这一轮的核心：每件涨到 800 之后储能必须跟着涨，否则机器静默停摆
        failed += check("储能 " + ElectricBlastFurnaceBlockEntity.MAX_ENERGY + " ≥ 最坏单 tick 耗电 "
                        + SPEC_WORST_DEMAND + "（否则满载一动不动）",
                ElectricBlastFurnaceBlockEntity.MAX_ENERGY >= SPEC_WORST_DEMAND);

        // ---- 满载跑一遍：12 槽 × 64 件，应当恰好 200 tick ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (!(level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m)) {
            failed += check("成型后有方块实体", false);
            clear(level);
            return failed;
        }
        int items = SPEC_SLOTS * SPEC_STACK;
        for (int k = 0; k < SPEC_SLOTS; k++) {
            m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + k,
                    new ItemStack(PotatoSTOres.RAW_COBALT.get(), SPEC_STACK));
        }
        long spent = 0;
        int ticks = 0;
        for (int i = 0; i < SPEC_TICKS + 100; i++) {
            setEnergy(m, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            int before = m.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m);
            spent += Math.max(0, before - m.getEnergyStored());
            ticks++;
            if (!m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST).isEmpty()) {
                break;
            }
        }
        long expected = (long) items * SPEC_FE_PER_ITEM;
        int out = 0;
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            out += m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k).getCount();
        }
        System.out.println(TAG + "  满载：" + items + " 件，跑了 " + ticks + " tick，花掉 " + spent
                + " FE（期望约 " + expected + "），产出 " + out + " 个");
        failed += check("满载 " + items + " 件恰好 " + SPEC_TICKS + " tick 走完（实际 " + ticks + "）",
                ticks == SPEC_TICKS);
        failed += check("每件 " + SPEC_FE_PER_ITEM + " FE：总量 " + spent + " 与 " + expected
                        + " 相差 ≤ " + SPEC_TICKS, Math.abs(spent - expected) <= SPEC_TICKS);
        failed += check("产出 " + (items * 2) + " 个钴锭（实际 " + out + "）", out == items * 2);

        // ---- 反向：只放 1 件时，单 tick 耗电 = ceil(800/200) = 4 FE/t ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m2) {
            m2.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                    new ItemStack(PotatoSTOres.RAW_COBALT.get(), 1));
            setEnergy(m2, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            int before = m2.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m2);
            int used = before - m2.getEnergyStored();
            failed += check("单件时单 tick 只花 4 FE（800÷200，实际 " + used + "）", used == 4);
        }

        // ---- 反向：一点电都不给就绝对不动 ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m3) {
            m3.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                    new ItemStack(Items.DIAMOND_ORE, 8));
            setEnergy(m3, 0);
            for (int i = 0; i < 10; i++) {
                ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m3);
            }
            int p = m3.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST);
            failed += check("反向断言：不给电时进度停在 0（实际 " + p + "）", p == 0);
        }

        clear(level);
        failed += check("测完已清空测试区", level.getBlockState(C).isAir());
        return failed;
    }

    private static void setEnergy(ElectricBlastFurnaceBlockEntity m, int v) {
        try {
            var f = ElectricBlastFurnaceBlockEntity.class.getDeclaredField("energy");
            f.setAccessible(true);
            f.setInt(m, v);
        } catch (Throwable t) {
            System.out.println(TAG + "  （写电失败：" + t + "）");
        }
    }

    private static void build(ServerLevel level, Direction facing) {
        for (int y = 0; y < 3; y++) {
            for (int j = 0; j < 3; j++) {
                for (int i = 0; i < 3; i++) {
                    level.setBlock(ElectricBlastFurnaceStructure.offset(C, facing, i, j, y),
                            ElectricBlastFurnaceStructure.blockFor(
                                    ElectricBlastFurnaceStructure.kindAt(i, j, y)).defaultBlockState(), 3);
                }
            }
        }
    }

    private static void clear(ServerLevel level) {
        for (BlockPos p : ElectricBlastFurnaceStructure.positions(C, Direction.SOUTH)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
