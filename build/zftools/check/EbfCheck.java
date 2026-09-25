package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF39 临时文件，验证完必须删）</b>：验电力高炉。
 *
 * <p>这台机器每一环都可能"看起来对" —— 结构相对坐标差一格、装配时被自己的部件格回头拆掉、
 * 原始方块没记全导致拆解吞材料、配方数量写反…… 只有真的在世界里盖一遍再拆一遍才算数。</p>
 *
 * <p><b>期望值照用户原话硬写</b>，不从被测常量里读（§4.27 的教训：探针里出现被测常量 =
 * 同义反复，注入 bug 也测不出来）。</p>
 */
public final class EbfCheck {

    private static final String TAG = "[EBF] ";
    private static boolean registered;

    // ===== 规格（用户原话），刻意不复用被测常量 =====
    private static final int SPEC_MAX_ENERGY = 320;
    private static final int SPEC_SECONDS = 3;
    private static final int SPEC_FE_PER_ITEM = 80;
    private static final int SPEC_RAW_YIELD = 2;
    private static final int SPEC_ORE_MIN = 3;
    private static final int SPEC_ORE_MAX = 6;
    private static final int SPEC_INPUT = 12;
    private static final int SPEC_OUTPUT = 32;

    private EbfCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(EbfCheck.class);
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

    /** 高空、区块已加载、测完清空 */
    private static final BlockPos C = new BlockPos(64, 220, 64);

    private static int run(ServerLevel level) {
        int failed = 0;
        Direction facing = Direction.SOUTH;
        RandomSource random = RandomSource.create(20260919L);

        // ① 常量 = 规格
        failed += check("MAX_ENERGY = " + SPEC_MAX_ENERGY + "（实际 " + ElectricBlastFurnaceBlockEntity.MAX_ENERGY + "）",
                ElectricBlastFurnaceBlockEntity.MAX_ENERGY == SPEC_MAX_ENERGY);
        failed += check("DURATION_TICKS = " + SPEC_SECONDS + " 秒 × 20 = " + (SPEC_SECONDS * 20)
                        + "（实际 " + ElectricBlastFurnaceBlockEntity.DURATION_TICKS + "）",
                ElectricBlastFurnaceBlockEntity.DURATION_TICKS == SPEC_SECONDS * 20);
        failed += check("ENERGY_PER_ITEM_PER_TICK = " + SPEC_FE_PER_ITEM,
                ElectricBlastFurnaceBlockEntity.ENERGY_PER_ITEM_PER_TICK == SPEC_FE_PER_ITEM);
        failed += check("输入 " + SPEC_INPUT + " 槽 / 输出 " + SPEC_OUTPUT + " 槽",
                ElectricBlastFurnaceBlockEntity.INPUT_COUNT == SPEC_INPUT
                        && ElectricBlastFurnaceBlockEntity.OUTPUT_COUNT == SPEC_OUTPUT);

        // ② 结构相对坐标：控制器自己必须在 (i=1,j=0)
        failed += check("offset(i=1,j=0,y=0) 就是控制器本身",
                ElectricBlastFurnaceStructure.offset(C, facing, 1, 0, 0).equals(C));
        failed += check("offset(i=1,j=2,y=0) 落在控制器正后方 2 格",
                ElectricBlastFurnaceStructure.offset(C, facing, 1, 2, 0).equals(C.relative(Direction.NORTH, 2)));

        // ③ 盖一遍结构
        clear(level);
        for (int y = 0; y < 3; y++) {
            for (int j = 0; j < 3; j++) {
                for (int i = 0; i < 3; i++) {
                    BlockPos p = ElectricBlastFurnaceStructure.offset(C, facing, i, j, y);
                    level.setBlock(p, blockFor(ElectricBlastFurnaceStructure.kindAt(i, j, y)), 3);
                }
            }
        }
        failed += check("盖好的结构校验通过", ElectricBlastFurnaceStructure.validate(level, C, facing) == null);

        // ④ 成型
        BlockState before = level.getBlockState(C);
        failed += check("成型前控制器是原版高炉", before.is(Blocks.BLAST_FURNACE));
        boolean formed = BlastFurnaceAssembly.form(level, C, facing);
        failed += check("form() 返回 true", formed);
        failed += check("控制器已变成电力高炉",
                level.getBlockState(C).is(ModBlocks.ELECTRIC_BLAST_FURNACE.get()));
        int parts = 0;
        int air = 0;
        for (BlockPos p : ElectricBlastFurnaceStructure.positions(C, facing)) {
            BlockState s = level.getBlockState(p);
            if (s.is(ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get())) {
                parts++;
            } else if (s.isAir()) {
                air++;
            }
        }
        failed += check("25 格变成部件格（实际 " + parts + "）、1 格空气（实际 " + air + "）", parts == 25 && air == 1);

        if (!(level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity be)) {
            failed += check("控制器方块实体存在", false);
            clear(level);
            return failed;
        }
        failed += check("方块实体记录为已成型", be.isFormed());

        // ⑤ 拆解还原：25 格必须回到原来的建材，控制器那格留空
        be.disassemble(true);
        boolean restored = true;
        int stillPart = 0;
        for (int y = 0; y < 3; y++) {
            for (int j = 0; j < 3; j++) {
                for (int i = 0; i < 3; i++) {
                    BlockPos p = ElectricBlastFurnaceStructure.offset(C, facing, i, j, y);
                    BlockState now = level.getBlockState(p);
                    if (p.equals(C)) {
                        restored &= now.isAir();
                        continue;
                    }
                    if (now.is(ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get())) {
                        stillPart++;
                    }
                    restored &= now.getBlock() == blockFor(ElectricBlastFurnaceStructure.kindAt(i, j, y)).getBlock();
                }
            }
        }
        failed += check("拆解后 26 格全部还原（残留部件格 " + stillPart + "）", restored && stillPart == 0);

        // ⑥ 配方：粗矿 → 2，矿石 → 3~6（固定种子复现），沙子 → 硅
        ItemStack raw = new ItemStack(PotatoSTOres.RAW_COBALT.get(), 4);
        ItemStack rawOut = BlastFurnaceRecipes.produce(raw, random);
        failed += check("4 个粗钴 → " + (4 * SPEC_RAW_YIELD) + " 个钴锭（实际 "
                        + rawOut.getCount() + "）",
                rawOut.getItem() == ModItems.COBALT_INGOT.get() && rawOut.getCount() == 4 * SPEC_RAW_YIELD);

        RandomSource seeded = RandomSource.create(12345L);
        ItemStack ore = new ItemStack(PotatoSTOres.COBALT_ORE.get(), 64);
        ItemStack oreOut = BlastFurnaceRecipes.produce(ore, seeded);
        boolean inRange = oreOut.getCount() >= 64 * SPEC_ORE_MIN && oreOut.getCount() <= 64 * SPEC_ORE_MAX;
        failed += check("64 个钴矿石 → 在 " + (64 * SPEC_ORE_MIN) + ".." + (64 * SPEC_ORE_MAX)
                        + " 之间（实际 " + oreOut.getCount() + "）", inRange);
        // 反向断言：不能每次都返回同一个数。
        // ⚠ 第一版写的是"连着两次结果必须不同" —— 那是**会偶发失败**的烂断言：
        //    64 次掷骰的和标准差约 8.9，两次恰好相等有 ~3% 的概率，实测就撞上了。
        //    改成取 30 个样本看最小/最大是否相同：只有真的退化成固定值才会失败。
        RandomSource s2 = RandomSource.create(999L);
        int lo = Integer.MAX_VALUE;
        int hi = Integer.MIN_VALUE;
        for (int i = 0; i < 30; i++) {
            int v = BlastFurnaceRecipes.produce(ore, s2).getCount();
            lo = Math.min(lo, v);
            hi = Math.max(hi, v);
        }
        failed += check("30 次抽样的产出不是一个固定值（反向断言：最小 " + lo + " / 最大 " + hi + "）", lo != hi);

        ItemStack sand = BlastFurnaceRecipes.produce(new ItemStack(Items.SAND, 3), random);
        failed += check("3 个沙子 → 3 个硅（实际 " + sand.getCount() + "）",
                sand.getItem() == ModItems.SILICON.get() && sand.getCount() == 3);

        // ⑦ 排除项：粗铀、粗锰、粗锂**没有**配方（用户点名排除 / 没有对应锭）
        failed += check("粗铀没有配方（用户点名排除）",
                BlastFurnaceRecipes.find(new ItemStack(PotatoSTOres.RAW_URANIUM.get())) == null);
        failed += check("粗锰没有配方（本项目没有锰锭）",
                BlastFurnaceRecipes.find(new ItemStack(PotatoSTOres.RAW_MANGANESE.get())) == null);
        failed += check("粗锂没有配方（本项目没有锂锭）",
                BlastFurnaceRecipes.find(new ItemStack(PotatoSTOres.RAW_LITHIUM.get())) == null);

        // ⑧ 节拍与耗电：一槽 3 个粗钴 → 需求 3 × 80 = 240 FE/t，60 tick 完成
        level.setBlock(C, ModBlocks.ELECTRIC_BLAST_FURNACE.get().defaultBlockState()
                .setValue(ElectricBlastFurnaceBlock.FACING, facing), 3);
        if (level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity machine) {
            machine.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                    new ItemStack(PotatoSTOres.RAW_COBALT.get(), 3));
            // 电量给足：直接灌到满，跑 tick
            int ticks = 0;
            for (int i = 0; i < 200; i++) {
                // 每 tick 补满电，模拟"接了大电"
                refill(machine);
                ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), machine);
                ticks++;
                if (!machine.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST).isEmpty()) {
                    break;
                }
            }
            int outCount = machine.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST).getCount();
            failed += check("一槽 3 个粗钴在 " + (SPEC_SECONDS * 20) + " tick 内烧完（用了 " + ticks
                            + " tick），产出 " + (3 * SPEC_RAW_YIELD) + " 个（实际 " + outCount + "）",
                    ticks == SPEC_SECONDS * 20 && outCount == 3 * SPEC_RAW_YIELD);
            failed += check("烧完后输入槽已空",
                    machine.getInventory().getStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST).isEmpty());
        } else {
            failed += check("重新放下控制器后有方块实体", false);
        }

        // ⑨ 电不够时**不推进**（反向断言：缓冲只有 320，必须真的卡住）
        if (level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity machine) {
            machine.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                    new ItemStack(PotatoSTOres.RAW_COBALT.get(), 12));   // 需求 12×80 = 960 > 320
            int progressBefore = machine.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST);
            ElectricBlastFurnaceBlockEntity.tick(level, C, level.getBlockState(C), machine);
            int progressAfter = machine.getContainerData().get(ElectricBlastFurnaceBlockEntity.DATA_PROGRESS_FIRST);
            failed += check("12 个物品需求 960 FE/t > 缓冲 320 ⇒ 进度不动（"
                            + progressBefore + " → " + progressAfter + "）", progressAfter == progressBefore);
        }

        clear(level);
        failed += check("测完已清空测试区", level.getBlockState(C).isAir());
        return failed;
    }

    /** 把机器的电灌满（用 NBT 往返是最省事的"作弊"入口）。 */
    private static void refill(ElectricBlastFurnaceBlockEntity machine) {
        try {
            var f = ElectricBlastFurnaceBlockEntity.class.getDeclaredField("energy");
            f.setAccessible(true);
            f.setInt(machine, SPEC_MAX_ENERGY);
        } catch (Throwable t) {
            System.out.println(TAG + "  （补电失败：" + t + "）");
        }
    }

    private static BlockState blockFor(ElectricBlastFurnaceStructure.Kind kind) {
        return switch (kind) {
            case COMMON -> ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState();
            case HEATER -> ModBlocks.HEATER.get().defaultBlockState();
            case WIRING -> ModBlocks.WIRING_BLOCK.get().defaultBlockState();
            case BARS -> Blocks.IRON_BARS.defaultBlockState();
            case TRAPDOOR -> Blocks.IRON_TRAPDOOR.defaultBlockState();
            case CONTROLLER -> Blocks.BLAST_FURNACE.defaultBlockState();
            case AIR -> Blocks.AIR.defaultBlockState();
        };
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
