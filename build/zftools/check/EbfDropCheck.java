package com.potatost.mod;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF40 临时文件，验证完必须删）</b>：验"破坏语义"这次改动的四条。
 *
 * <p>用户报的现象：「挖掘后会掉落两个电力高炉」，并要求
 * 「一个模型是一个整体 / 任意部位右键都可以打开 gui / 被破坏后只会毁坏结构和掉落被挖掉的方块
 * 以及 gui 内部物品」。</p>
 *
 * <p>所以这里**数掉落的实体**（不是读代码猜）—— 掉两个这件事只有数出来才算数。</p>
 */
public final class EbfDropCheck {

    private static final String TAG = "[EBFDROP] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(80, 220, 80);

    private EbfDropCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(EbfDropCheck.class);
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

        // ---- 试验 A：破坏一个**部件格** ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);

        // 找一个部件格（第二层最里那排的栏杆位）
        BlockPos part = ElectricBlastFurnaceStructure.offset(C, facing, 0, 2, 1);
        BlockState originalThere = Blocks.IRON_BARS.defaultBlockState();
        failed += check("目标格确实是部件格",
                level.getBlockState(part).is(ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get()));

        // 部件格的渲染形状必须是 INVISIBLE（"一个模型是一个整体"的前提）
        failed += check("部件格 getRenderShape = INVISIBLE",
                level.getBlockState(part).getRenderShape() == RenderShape.INVISIBLE);
        failed += check("控制器的 getRenderShape = MODEL（整块 OBJ 由它画）",
                level.getBlockState(C).getRenderShape() == RenderShape.MODEL);

        dropClean(level, part);
        // 模拟玩家挖掉它：先走掉落逻辑，再移除方块（与原版 destroyBlock 的顺序一致）
        level.destroyBlock(part, true);
        List<ItemEntity> dropsA = itemsNear(level, part);
        System.out.println(TAG + "  试验A：破坏部件格后掉落 " + dropsA.size() + " 件 -> " + describe(dropsA));
        failed += check("正好掉 1 件（用户报的是掉 2 个）", dropsA.size() == 1);
        failed += check("掉的是这一格的原方块（铁栏杆），不是电力高炉",
                dropsA.size() == 1 && dropsA.get(0).getItem().is(Items.IRON_BARS));
        failed += check("被挖的那格现在应当是空气（原方块已经作为掉落物给出去了）",
                level.getBlockState(part).isAir());

        boolean othersRestored = true;
        int leftoverParts = 0;
        for (int y = 0; y < 3; y++) {
            for (int j = 0; j < 3; j++) {
                for (int i = 0; i < 3; i++) {
                    BlockPos p = ElectricBlastFurnaceStructure.offset(C, facing, i, j, y);
                    if (p.equals(part)) {
                        continue;
                    }
                    BlockState now = level.getBlockState(p);
                    if (now.is(ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get())) {
                        leftoverParts++;
                    }
                    othersRestored &= now.getBlock() ==
                            ElectricBlastFurnaceStructure.blockFor(
                                    ElectricBlastFurnaceStructure.kindAt(i, j, y)) || now.isAir();
                }
            }
        }
        failed += check("其余 26 格全部还原（残留部件格 " + leftoverParts + "）", othersRestored && leftoverParts == 0);

        // ---- 试验 B：破坏**控制器** ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        dropClean(level, C);
        level.destroyBlock(C, true);
        List<ItemEntity> dropsB = itemsNear(level, C);
        System.out.println(TAG + "  试验B：破坏控制器后掉落 " + dropsB.size() + " 件 -> " + describe(dropsB));
        failed += check("正好掉 1 件", dropsB.size() == 1);
        failed += check("掉的是控制器那一格的原方块（原版高炉），**不是**电力高炉",
                dropsB.size() == 1 && dropsB.get(0).getItem().is(Items.BLAST_FURNACE));

        // ---- 试验 C：拆解时 GUI 内容物要掉出来 ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity machine) {
            machine.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                    new ItemStack(PotatoSTOres.RAW_COBALT.get(), 7));
            machine.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.OUTPUT_FIRST,
                    new ItemStack(ModItems.COBALT_INGOT.get(), 5));
            dropClean(level, C);
            BlockPos partC = ElectricBlastFurnaceStructure.offset(C, facing, 2, 2, 2);
            level.destroyBlock(partC, true);
            List<ItemEntity> dropsC = itemsNear(level, C);
            boolean hasRaw = dropsC.stream().anyMatch(e -> e.getItem().is(PotatoSTOres.RAW_COBALT.get()));
            boolean hasIngot = dropsC.stream().anyMatch(e -> e.getItem().is(ModItems.COBALT_INGOT.get()));
            System.out.println(TAG + "  试验C：掉落 " + dropsC.size() + " 件 -> " + describe(dropsC));
            failed += check("GUI 里的粗钴掉出来了", hasRaw);
            failed += check("GUI 里的钴锭掉出来了", hasIngot);
            failed += check("没有任何一件是电力高炉本体（不许掉它）",
                    dropsC.stream().noneMatch(e -> e.getItem().is(ModBlocks.ELECTRIC_BLAST_FURNACE_ITEM.get())));
        } else {
            failed += check("成型后能找到控制器方块实体", false);
        }

        // ---- 试验 D：每个部件格周围 2 格内都找得到控制器（右键任意部位能开 GUI 的前提） ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        int reachable = 0;
        int total = 0;
        for (BlockPos p : ElectricBlastFurnaceStructure.positions(C, facing)) {
            if (p.equals(C) || level.getBlockState(p).isAir()) {
                continue;
            }
            total++;
            boolean found = false;
            for (BlockPos q : BlockPos.betweenClosed(p.offset(-2, -2, -2), p.offset(2, 2, 2))) {
                if (level.getBlockEntity(q) instanceof ElectricBlastFurnaceBlockEntity) {
                    found = true;
                    break;
                }
            }
            if (found) {
                reachable++;
            }
        }
        failed += check("全部 " + total + " 个部件格都在控制器的 2 格搜索半径内（实际 " + reachable + "）",
                reachable == total && total == 25);

        clear(level);
        failed += check("测完已清空测试区", level.getBlockState(C).isAir());
        return failed;
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

    /** 先把这一带清一遍，免得上一次试验掉的东西被数进来。 */
    private static void dropClean(ServerLevel level, BlockPos around) {
        itemsNear(level, around).forEach(ItemEntity::discard);
        itemsNear(level, C).forEach(ItemEntity::discard);
    }

    private static List<ItemEntity> itemsNear(ServerLevel level, BlockPos pos) {
        return level.getEntitiesOfClass(ItemEntity.class,
                new AABB(pos).inflate(4.0D, 3.0D, 4.0D), e -> true);
    }

    private static String describe(List<ItemEntity> list) {
        StringBuilder sb = new StringBuilder();
        for (ItemEntity e : list) {
            if (sb.length() > 0) {
                sb.append(" + ");
            }
            sb.append(e.getItem().getCount()).append("×")
                    .append(net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(e.getItem().getItem()));
        }
        return sb.length() == 0 ? "（空）" : sb.toString();
    }

    private static void clear(ServerLevel level) {
        for (BlockPos p : ElectricBlastFurnaceStructure.positions(C, Direction.SOUTH)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
        itemsNear(level, C).forEach(ItemEntity::discard);
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
