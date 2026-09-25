package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF41 临时文件，验证完必须删）</b>：验这一轮的三件事。
 *
 * <ol>
 *   <li><b>接电</b>：用户报「原来接线块的地方也不传电」。这台机器之前**压根没注册能量能力**，
 *       而且"只有接线块的位置能传电"这条规则要求**逐格**判定 —— 两条都要量；</li>
 *   <li><b>扳手</b>：拆解改成"手持扳手 Shift 右键"，逻辑抽到了
 *       {@link ElectricBlastFurnaceWrench}，这里直接调它验还原；</li>
 *   <li><b>Jade 名字</b>：部件格必须有 lang（否则显示一大串 id）。</li>
 * </ol>
 */
public final class EbfPowerCheck {

    private static final String TAG = "[EBFPOWER] ";
    private static boolean registered;
    private static final BlockPos C = new BlockPos(96, 220, 96);

    private EbfPowerCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(EbfPowerCheck.class);
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

        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);

        if (!(level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity master)) {
            failed += check("成型后控制器方块实体存在", false);
            clear(level);
            return failed;
        }

        // ---- ① 控制器本身要能收电 ----
        IEnergyStorage fromMaster = level.getCapability(Capabilities.EnergyStorage.BLOCK, C, Direction.UP);
        failed += check("控制器暴露了能量能力（之前压根没注册）", fromMaster != null);
        if (fromMaster != null) {
            // 先用扳手那条路把它清空，免得残留
            int accepted = fromMaster.receiveEnergy(9999, false);
            failed += check("能收电且收满到上限 320（收了 " + accepted + "）",
                    accepted == ElectricBlastFurnaceBlockEntity.MAX_ENERGY);
            failed += check("存进去的就是 320", master.getEnergyStored() == 320);
            failed += check("反向断言：不能从它抽电（canExtract 应为 false）", !fromMaster.canExtract());
            failed += check("反向断言：满电后再收是 0", fromMaster.receiveEnergy(100, false) == 0);
        }

        // ---- ② 只有"原本是接线块"的部件格才是接电口 ----
        // 第二层中间那排的两端就是接线块位（i=0/2, j=1, y=1）
        BlockPos portA = ElectricBlastFurnaceStructure.offset(C, facing, 0, 1, 1);
        BlockPos portB = ElectricBlastFurnaceStructure.offset(C, facing, 2, 1, 1);
        // 拿一个明显不是接线块的：第一层最里排的角（一般金属块位）
        BlockPos notPort = ElectricBlastFurnaceStructure.offset(C, facing, 0, 2, 0);

        failed += check("接线块位现在是部件格",
                level.getBlockState(portA).is(ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get()));
        failed += check("接线块位有方块实体（能力只能挂在方块实体上）",
                level.getBlockEntity(portA) instanceof ElectricBlastFurnacePartBlockEntity);
        if (level.getBlockEntity(portA) instanceof ElectricBlastFurnacePartBlockEntity port) {
            failed += check("接线块位判定为接电口（isPowerPort）", port.isPowerPort());
        }
        IEnergyStorage atPort = level.getCapability(Capabilities.EnergyStorage.BLOCK, portA, Direction.NORTH);
        failed += check("接线块位对外暴露了能量能力", atPort != null);
        if (atPort != null) {
            // ⚠ 第一版这里写错了：先想用 fromMaster.extractEnergy 把电腾空，可控制器是**只收不放**的，
            //    抽取恒返回 0 ⇒ 缓冲还停在 320（满的），于是 receiveEnergy 当然收 0，白白报了一个假 FAIL。
            //    改成直接把 energy 字段清零（反射），再从这个口灌电，才是真正的端到端。
            drain(master);
            int before = master.getEnergyStored();
            int got = atPort.receiveEnergy(320, false);
            failed += check("从接线块位灌电，控制器存量 " + before + " → " + master.getEnergyStored()
                            + "（实收 " + got + "）", got == 320 && master.getEnergyStored() == 320);
            failed += check("这个口报的容量就是控制器的容量（320）", atPort.getMaxEnergyStored() == 320);
        }
        failed += check("两个接线块位都算接电口",
                level.getCapability(Capabilities.EnergyStorage.BLOCK, portB, Direction.NORTH) != null);

        IEnergyStorage atNotPort = level.getCapability(Capabilities.EnergyStorage.BLOCK, notPort, Direction.UP);
        failed += check("**非**接线块位不给电（用户定的规则：只有接线块的位置能传电）", atNotPort == null);
        if (level.getBlockEntity(notPort) instanceof ElectricBlastFurnacePartBlockEntity other) {
            failed += check("非接线块位的 isPowerPort 为假（反向断言）", !other.isPowerPort());
        }

        // ---- ③ 扳手拆解 ----
        clear(level);
        build(level, facing);
        BlastFurnaceAssembly.form(level, C, facing);
        if (level.getBlockEntity(C) instanceof ElectricBlastFurnaceBlockEntity m2) {
            m2.getInventory().setStackInSlot(ElectricBlastFurnaceBlockEntity.INPUT_FIRST,
                    new ItemStack(PotatoSTOres.RAW_SILVER.get(), 3));
            var items = level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,
                    new net.minecraft.world.phys.AABB(C).inflate(4, 3, 4));
            items.forEach(net.minecraft.world.entity.item.ItemEntity::discard);

            ElectricBlastFurnaceWrench.disassembleByWrench(level, m2, portA);

            int restored = 0;
            int leftover = 0;
            for (int y = 0; y < 3; y++) {
                for (int j = 0; j < 3; j++) {
                    for (int i = 0; i < 3; i++) {
                        BlockPos p = ElectricBlastFurnaceStructure.offset(C, facing, i, j, y);
                        BlockState now = level.getBlockState(p);
                        if (now.is(ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get())) {
                            leftover++;
                        }
                        if (now.getBlock() == ElectricBlastFurnaceStructure.blockFor(
                                ElectricBlastFurnaceStructure.kindAt(i, j, y))) {
                            restored++;
                        }
                    }
                }
            }
            failed += check("扳手拆解后 26 格全部还原（还原 " + restored + "，残留部件格 " + leftover + "）",
                    leftover == 0 && restored == 26);
            failed += check("控制器那一格变成空气（原方块已作为掉落物给出）", level.getBlockState(C).isAir());
            var after = level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,
                    new net.minecraft.world.phys.AABB(C).inflate(4, 3, 4));
            boolean hasFurnace = after.stream().anyMatch(e -> e.getItem().is(net.minecraft.world.item.Items.BLAST_FURNACE));
            boolean hasRaw = after.stream().anyMatch(e -> e.getItem().is(PotatoSTOres.RAW_SILVER.get()));
            failed += check("掉出了原版高炉（控制器那格的原方块）", hasFurnace);
            failed += check("掉出了 GUI 里的粗银", hasRaw);
            failed += check("**没有**掉电力高炉本体（用户要求破坏/拆解不给这个物品）",
                    after.stream().noneMatch(e -> e.getItem().is(ModBlocks.ELECTRIC_BLAST_FURNACE_ITEM.get())));
        }

        // ---- ④ 部件格的显示名（Jade 读的就是它）----
        // ⚠ 第一版这里也写错了：去世界里取 (0,1,1) 那格的方块 —— 可上面第 ③ 段已经把结构拆掉了，
        //    那一格早变回铁栏杆了，于是判了个假 FAIL。这里直接问方块本身，不碰世界。
        String key = ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get().getDescriptionId();
        failed += check("部件格的 descriptionId = block.potato_s_t.electric_blast_furnace_part（实际 " + key + "）",
                "block.potato_s_t.electric_blast_furnace_part".equals(key));
        String shown = ModBlocks.ELECTRIC_BLAST_FURNACE_PART.get().getName().getString();
        failed += check("部件格的名字解析成了人话（实际 \"" + shown + "\"）—— 不再是原始 id",
                !shown.startsWith("block.") && shown.length() > 0);

        clear(level);
        failed += check("测完已清空测试区", level.getBlockState(C).isAir());
        return failed;
    }

    /** 把控制器的电清零（反射）—— 它只收不放，没有别的办法腾空。 */
    private static void drain(ElectricBlastFurnaceBlockEntity master) {
        try {
            var f = ElectricBlastFurnaceBlockEntity.class.getDeclaredField("energy");
            f.setAccessible(true);
            f.setInt(master, 0);
        } catch (Throwable t) {
            System.out.println(TAG + "  （清零失败：" + t + "）");
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
        level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,
                new net.minecraft.world.phys.AABB(C).inflate(4, 3, 4))
                .forEach(net.minecraft.world.entity.item.ItemEntity::discard);
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
