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
 * ⚠⚠ <b>诊断工具（ZF43 临时文件，验证完必须删）</b>：验"10 秒一组 + 所有原版高炉配方"。
 *
 * <p>期望值**照用户原话与算术硬写**，不从被测常量里读（§4.27）。</p>
 */
public final class EbfVanillaCheck {

    private static final String TAG = "[EBFVANILLA] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(128, 220, 128);

    // ===== 规格 / 算术（硬写）=====
    private static final int SPEC_SECONDS = 10;
    private static final int SPEC_TICKS = SPEC_SECONDS * 20;      // 200
    private static final int SPEC_MAX_ENERGY = 320;
    private static final int SPEC_INPUTS = 12;
    private static final int SPEC_STACK = 64;
    private static final int SPEC_FE_PER_ITEM = 80;
    /** 最坏情况单 tick 耗电（向上取整）—— 必须 ≤ 储能，否则机器永远不动 */
    private static final int WORST_DEMAND =
            (SPEC_INPUTS * SPEC_STACK * SPEC_FE_PER_ITEM + SPEC_TICKS - 1) / SPEC_TICKS;

    private EbfVanillaCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(EbfVanillaCheck.class);
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

        failed += check("DURATION_TICKS = " + SPEC_SECONDS + " 秒 × 20 = " + SPEC_TICKS
                        + "（实际 " + ElectricBlastFurnaceBlockEntity.DURATION_TICKS + "）",
                ElectricBlastFurnaceBlockEntity.DURATION_TICKS == SPEC_TICKS);
        failed += check("MAX_ENERGY = " + SPEC_MAX_ENERGY + "（实际 "
                        + ElectricBlastFurnaceBlockEntity.MAX_ENERGY + "）",
                ElectricBlastFurnaceBlockEntity.MAX_ENERGY == SPEC_MAX_ENERGY);
        System.out.println(TAG + "  算术：最坏情况 " + SPEC_INPUTS + " 槽 × " + SPEC_STACK + " 件 × "
                + SPEC_FE_PER_ITEM + " FE = " + (SPEC_INPUTS * SPEC_STACK * SPEC_FE_PER_ITEM)
                + " FE 整批，摊到 " + SPEC_TICKS + " tick = " + WORST_DEMAND + " FE/t");
        failed += check("最坏情况单 tick 耗电 " + WORST_DEMAND + " ≤ 储能 " + SPEC_MAX_ENERGY
                        + "（否则机器永远不动）", WORST_DEMAND <= SPEC_MAX_ENERGY);

        // ---- ① 满载跑一遍：12 槽 × 64 件，应当恰好 200 tick ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (!(level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m1)) {
            failed += check("成型后有方块实体", false);
            clear(level);
            return failed;
        }
        int items = SPEC_INPUTS * SPEC_STACK;
        for (int k = 0; k < SPEC_INPUTS; k++) {
            m1.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST + k,
                    new ItemStack(PotatoSTOres.RAW_COBALT.get(), SPEC_STACK));
        }
        long spent = 0;
        int ticks = 0;
        for (int i = 0; i < SPEC_TICKS + 100; i++) {
            refill(m1);
            int before = m1.getEnergyStored();
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m1);
            spent += Math.max(0, before - m1.getEnergyStored());
            ticks++;
            if (!m1.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST).isEmpty()) {
                break;
            }
        }
        long expected = (long) items * SPEC_FE_PER_ITEM;
        System.out.println(TAG + "  满载：" + items + " 件，跑了 " + ticks + " tick，花掉 " + spent
                + " FE（期望约 " + expected + "）");
        failed += check("满载 " + items + " 件恰好 " + SPEC_TICKS + " tick 走完（实际 " + ticks + "）",
                ticks == SPEC_TICKS);
        failed += check("每件 80 FE，总量 " + spent + " 与 " + expected + " 相差 ≤ " + SPEC_TICKS,
                Math.abs(spent - expected) <= SPEC_TICKS);

        // ---- ② 原版高炉配方（用户：「加上所有的原版高炉配方」）----
        // 挑四种有代表性的：矿石出宝石/矿物、下界合金碎片、工具烧成粒、石英
        failed += oneShot(level, facing, new ItemStack(Items.DIAMOND_ORE, 4), Items.DIAMOND, 4,
                "钻石矿石 ×4 → 4 个钻石");
        failed += oneShot(level, facing, new ItemStack(Items.ANCIENT_DEBRIS, 2), Items.NETHERITE_SCRAP, 2,
                "远古残骸 ×2 → 2 个下界合金碎片");
        failed += oneShot(level, facing, new ItemStack(Items.IRON_PICKAXE, 1), Items.IRON_NUGGET, 1,
                "铁镐 ×1 → 1 个铁粒（原版「工具烧成粒」）");
        failed += oneShot(level, facing, new ItemStack(Items.NETHER_QUARTZ_ORE, 3), Items.QUARTZ, 3,
                "下界石英矿石 ×3 → 3 个石英");
        failed += oneShot(level, facing, new ItemStack(Items.REDSTONE_ORE, 1), Items.REDSTONE, 1,
                "红石矿石 ×1 → 1 个红石");
        failed += oneShot(level, facing, new ItemStack(Items.LAPIS_ORE, 2), Items.LAPIS_LAZULI, 2,
                "青金石矿石 ×2 → 2 个青金石");
        failed += oneShot(level, facing, new ItemStack(Items.COAL_ORE, 1), Items.COAL, 1,
                "煤矿石 ×1 → 1 个煤炭");
        failed += oneShot(level, facing, new ItemStack(Items.EMERALD_ORE, 1), Items.EMERALD, 1,
                "绿宝石矿石 ×1 → 1 个绿宝石");

        // ---- ③ 反向：本模组自己的表**优先**，不能被原版的 1 锭盖掉 ----
        failed += oneShot(level, facing, new ItemStack(PotatoSTOres.RAW_COBALT.get(), 3),
                ModItems.COBALT_INGOT.get(), 6, "粗钴 ×3 → 6 个钴锭（本模组的表优先，不是 3）");

        // ---- ④ 反向：原版高炉烧不了的应当不加工 ----
        failed += oneShot(level, facing, new ItemStack(Items.DIRT, 4), Items.DIRT, 0,
                "泥土 ×4 → 什么都不出（反向断言）");

        clear(level);
        failed += check("测完已清空测试区", level.getBlockState(C).isAir());
        return failed;
    }

    /** 把一种物品放进 0 号输入槽跑到底，看产出。 */
    private static int oneShot(ServerLevel level, Direction facing, ItemStack input,
                               net.minecraft.world.item.Item expectedItem, int expectedCount, String label) {
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (!(level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m)) {
            return check("[" + label + "] 成型后有方块实体", false);
        }
        m.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST, input);
        for (int i = 0; i < SPEC_TICKS + 40; i++) {
            refill(m);
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), m);
            if (m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST).getItem()
                    == expectedItem && expectedCount > 0) {
                break;
            }
            if (expectedCount == 0 && i > 20) {
                break;   // 反向断言：给足时间也不该出东西
            }
        }
        int total = 0;
        boolean sameItem = true;
        for (int k = 0; k < ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT; k++) {
            ItemStack s = m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST + k);
            if (s.isEmpty()) {
                continue;
            }
            total += s.getCount();
            sameItem &= s.getItem() == expectedItem;
        }
        boolean inputConsumed = m.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST).isEmpty();
        return check("[" + label + "] 实际出 " + total + " 个（输入" + (inputConsumed ? "已消耗" : "未消耗") + "）",
                total == expectedCount && sameItem && (expectedCount == 0 || inputConsumed));
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

    private static void refill(ElectricBlastFurnaceBlockEntity m) {
        setEnergy(m, SPEC_MAX_ENERGY);
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
