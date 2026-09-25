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
 * ⚠⚠ <b>诊断工具（ZF42 临时文件，验证完必须删）</b>：验"塞满也能跑"。
 *
 * <p>用户报「貌似不工作」：界面里 12 个输入槽塞满 64 一摞的矿石、能量条满格、产物一个没有。
 * 根因是 <b>单 tick 耗电 &gt; 储能上限 ⇒ 永远凑不齐</b>。这里按用户那天的真实负载
 * （11 槽 × 64 = 704 件）跑一遍，量**总耗电**与**耗时**。</p>
 */
public final class EbfLoadCheck {

    private static final String TAG = "[EBFLOAD] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(112, 220, 112);

    private EbfLoadCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(EbfLoadCheck.class);
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

        // 常量按**现在实现的口径**核对：一件物品总耗电 80、储能够扛最坏情况
        failed += check("ENERGY_PER_ITEM = 80", ElectricBlastFurnaceBlockEntity.ENERGY_PER_ITEM == 80);
        failed += check("MAX_ENERGY (" + ElectricBlastFurnaceBlockEntity.MAX_ENERGY
                        + ") ≥ 12 槽塞满时的单 tick 耗电 ("
                        + (12 * 64 * 80 / ElectricBlastFurnaceBlockEntity.DURATION_TICKS) + ")",
                ElectricBlastFurnaceBlockEntity.MAX_ENERGY
                        >= 12 * 64 * 80 / ElectricBlastFurnaceBlockEntity.DURATION_TICKS);

        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (!(level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity machine)) {
            failed += check("成型后有方块实体", false);
            clear(level);
            return failed;
        }

        // 用户那天的真实负载：**11 个槽各塞 64 个粗钴**
        int slots = 11;
        int per = 64;
        int items = slots * per;
        for (int k = 0; k < slots; k++) {
            machine.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + k,
                    new ItemStack(PotatoSTOres.RAW_COBALT.get(), per));
        }

        // 每 tick 先把电灌满（模拟"接了足够大的电"），再跑，记录实际花掉多少
        long spent = 0;
        int ticks = 0;
        for (int i = 0; i < 200; i++) {
            refill(machine);
            int before = machine.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), machine);
            int after = machine.getEnergyStored();
            spent += Math.max(0, before - after);
            ticks++;
            if (!machine.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST).isEmpty()) {
                break;
            }
        }
        // ⚠ 第一版这里只看了**第一个**输出槽：64 个粗钴 → 128 个锭，一个槽最多装 64，
        //    所以有一半溢到了第二个槽，断言于是判了个假 FAIL。要**把所有输出槽加起来**。
        int outCount = 0;
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            outCount += machine.getInventory()
                    .getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k).getCount();
        }
        long expected = (long) items * 80;

        System.out.println(TAG + "  负载：" + slots + " 槽 × " + per + " = " + items + " 件；跑了 " + ticks
                + " tick，花掉 " + spent + " FE（期望约 " + expected + "），首槽产出 " + outCount);
        failed += check("塞满 " + items + " 件时**机器真的会动**（用了 " + ticks + " tick，不是卡死）",
                ticks <= ElectricBlastFurnaceBlockEntity.DURATION_TICKS + 1);
        failed += check("一槽 3 秒烧完（" + ticks + " tick = 期望 "
                        + ElectricBlastFurnaceBlockEntity.DURATION_TICKS + "）",
                ticks == ElectricBlastFurnaceBlockEntity.DURATION_TICKS);
        failed += check("每件物品耗电 80 FE，总量 " + spent + " 与 " + expected
                        + " 相差不超过 60（逐 tick 向上取整的零头）",
                Math.abs(spent - expected) <= ElectricBlastFurnaceBlockEntity.DURATION_TICKS);
        failed += check("11 槽 64 个粗钴共出 " + (items * 2) + " 个钴锭（实际 " + outCount + "，跨多个输出槽）",
                outCount == items * 2);
        failed += check("烧完的输入槽已空",
                machine.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST).isEmpty());

        // 反向断言：**不给电就绝对不动**（这条才说明"接大电"是真的）
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m2) {
            m2.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                    new ItemStack(PotatoSTOres.RAW_COBALT.get(), 64));
            drain(m2);
            for (int i = 0; i < 10; i++) {
                ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m2);
            }
            int p = m2.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST);
            failed += check("反向断言：一点电都不给时进度停在 0（实际 " + p + "）", p == 0);
        }

        clear(level);
        failed += check("测完已清空测试区", level.getBlockState(C).isAir());
        return failed;
    }

    private static void setEnergy(ElectricBlastFurnaceBlockEntity machine, int value) {
        try {
            var f = ElectricBlastFurnaceBlockEntity.class.getDeclaredField("energy");
            f.setAccessible(true);
            f.setInt(machine, value);
        } catch (Throwable t) {
            System.out.println(TAG + "  （写电失败：" + t + "）");
        }
    }

    private static void refill(ElectricBlastFurnaceBlockEntity machine) {
        setEnergy(machine, ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
    }

    private static void drain(ElectricBlastFurnaceBlockEntity machine) {
        setEnergy(machine, 0);
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
