package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * WARNING - TEMPORARY DIAGNOSTIC (ZF79). Delete after the run.
 *
 * <p>验两件：① **12 个沥青 → 1 个柏油块**（含数量不够时的新状态、以及 1:1 老配方没被改坏）；
 * ② 柏油块本体（注册名 / 挖掘标签 / 没有合成台配方由常驻校验管）。</p>
 */
public final class AsphaltCheck {

    private static final String TAG = "[F79] ";
    private static final BlockPos ORIGIN = new BlockPos(320, 120, 320);

    private static boolean registered;
    private static int passed;
    private static int failed;

    private AsphaltCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AsphaltCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            checkRegistration(level);
            checkRecipes();
            checkPress(level);
        } catch (Throwable t) {
            t.printStackTrace();
            failed++;
        }
        System.out.println(TAG + "==== passed=" + passed + " failed=" + failed + " ====");
        event.getServer().halt(false);
    }

    // ================= 工具 =================

    private static void ok(String label, boolean cond) {
        if (cond) {
            passed++;
            System.out.println(TAG + "  [OK]   " + label);
        } else {
            failed++;
            System.out.println(TAG + "  [FAIL] " + label);
        }
    }

    private static void eq(String label, long expected, long actual) {
        ok(label + "（期望 " + expected + "，实际 " + actual + "）", expected == actual);
    }

    // ================= ① 注册与标签 =================

    private static void checkRegistration(ServerLevel level) {
        ok("柏油块 id = potato_s_t:asphalt_block",
                "potato_s_t:asphalt_block".equals(
                        String.valueOf(BuiltInRegistries.BLOCK.getKey(ModBlocks.ASPHALT_BLOCK.get()))));
        ok("柏油块物品 id = potato_s_t:asphalt_block",
                "potato_s_t:asphalt_block".equals(
                        String.valueOf(BuiltInRegistries.ITEM.getKey(
                                ModBlocks.ASPHALT_BLOCK_ITEM.get()))));
        ok("柏油块是 requiresCorrectToolForDrops（挖了会掉）",
                ModBlocks.ASPHALT_BLOCK.get().defaultBlockState().requiresCorrectToolForDrops());
        TagKey<net.minecraft.world.level.block.Block> pickaxe = TagKey.create(
                net.minecraft.core.registries.Registries.BLOCK,
                ResourceLocation.withDefaultNamespace("mineable/pickaxe"));
        ok("柏油块挂在 #minecraft:mineable/pickaxe 上（§4.25：不挂就挖不出东西）",
                ModBlocks.ASPHALT_BLOCK.get().defaultBlockState().is(pickaxe));
        ok("柏油块没有方块实体（纯装饰）",
                ModBlocks.ASPHALT_BLOCK.get().getClass() == net.minecraft.world.level.block.Block.class);
    }

    // ================= ② 配方表 =================

    private static void checkRecipes() {
        int n = PressRecipes.all().size();
        eq("液压机配方 8 条（7 锭→板 + 1 沥青→柏油块）", 8, n);

        PressRecipes.Recipe bitumen = PressRecipes.find(new ItemStack(ModItems.BITUMEN.get()));
        ok("沥青能匹配到配方", bitumen != null);
        if (bitumen != null) {
            eq("这条配方要 12 个沥青", PressRecipes.BITUMEN_PER_BLOCK, bitumen.inputCount());
            eq("一次要 12 个", 12, bitumen.inputCount());
            ok("产物是柏油块",
                    bitumen.createOutput().is(ModBlocks.ASPHALT_BLOCK_ITEM.get()));
            ok("没有通用标签（沥青按长期规则不挂 c:）", bitumen.inputTag() == null);
            ok("11 个沥青：物品对但数量不够", bitumen.matches(new ItemStack(ModItems.BITUMEN.get(), 11))
                    && !bitumen.hasEnough(new ItemStack(ModItems.BITUMEN.get(), 11)));
            ok("12 个沥青：够", bitumen.hasEnough(new ItemStack(ModItems.BITUMEN.get(), 12)));
        }

        // 回归：7 条老配方必须还是"1 个进、1 个出、标签优先"
        PressRecipes.Recipe iron = PressRecipes.find(
                new ItemStack(net.minecraft.world.item.Items.IRON_INGOT));
        ok("铁锭仍能匹配", iron != null);
        if (iron != null) {
            eq("老配方还是吃 1 个", 1, iron.inputCount());
            ok("产物还是铁板", iron.createOutput().is(ModItems.IRON_PLATE.get()));
            ok("铁锭走 c:ingots/iron 标签（别的 mod 的铁锭也能用）",
                    iron.inputTag() != null && iron.matches(new ItemStack(
                            net.minecraft.world.item.Items.IRON_INGOT)));
        }
        ok("不可压的东西仍然匹配不到（泥土）",
                PressRecipes.find(new ItemStack(net.minecraft.world.item.Items.DIRT)) == null);
    }

    // ================= ③ 真跑一遍液压机 =================

    private static void checkPress(ServerLevel level) {
        BlockPos pos = ORIGIN;
        level.setBlock(pos, ModBlocks.HYDRAULIC_PRESS.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(pos) instanceof HydraulicPressBlockEntity press)) {
            ok("液压机方块实体建出来了", false);
            return;
        }
        // ⚠ 只用**公开口子**：inventory / containerData / energyStorage —— 生产代码里不留任何探针钩子
        var inv = press.getInventory();
        var data = press.getContainerData();
        IEnergyStorage energy = press.getEnergyStorage();
        int inSlot = HydraulicPressBlockEntity.INPUT_SLOT;
        int outSlot = HydraulicPressBlockEntity.OUTPUT_SLOT;

        // ① 11 个沥青：不开工、状态"材料不够"、一个都不吃
        inv.setStackInSlot(inSlot, new ItemStack(ModItems.BITUMEN.get(), 11));
        inv.setStackInSlot(outSlot, ItemStack.EMPTY);
        energy.receiveEnergy(Integer.MAX_VALUE, false);
        tick(level, pos);
        eq("11 个沥青：状态 = 材料不够",
                HydraulicPressBlockEntity.STATUS_MATERIAL,
                data.get(HydraulicPressBlockEntity.DATA_STATUS));
        eq("11 个沥青：进度没动", 0, data.get(HydraulicPressBlockEntity.DATA_PROGRESS));
        eq("11 个沥青：一个都没被吃掉", 11, inv.getStackInSlot(inSlot).getCount());

        // ② 12 个沥青：**只灌一次电**（缓冲正好 = 一块板的 24000 FE）⇒ 60 tick 出一块、电正好见底
        //    ⚠ 第一版在每 tick 前都灌满，结束时还剩 23600 ⇒ 断言写错位置（探针自己的锅）
        inv.setStackInSlot(inSlot, new ItemStack(ModItems.BITUMEN.get(), 12));
        inv.setStackInSlot(outSlot, ItemStack.EMPTY);
        energy.receiveEnergy(Integer.MAX_VALUE, false);
        eq("（准备）缓冲正好一块板的电（60 × 400）", 24000,
                data.get(HydraulicPressBlockEntity.DATA_ENERGY));
        for (int i = 0; i < 60; i++) {
            tick(level, pos);
        }
        eq("12 个沥青：跑完 60 tick 出 1 个柏油块", 1, inv.getStackInSlot(outSlot).getCount());
        ok("产物就是柏油块", inv.getStackInSlot(outSlot).is(ModBlocks.ASPHALT_BLOCK_ITEM.get()));
        eq("12 个沥青正好被吃光", 0, inv.getStackInSlot(inSlot).getCount());
        eq("电正好扣光（60 tick × 400 FE）", 0, data.get(HydraulicPressBlockEntity.DATA_ENERGY));

        // ③ 24 个沥青：连跑两轮 ⇒ 2 块
        inv.setStackInSlot(outSlot, ItemStack.EMPTY);
        inv.setStackInSlot(inSlot, new ItemStack(ModItems.BITUMEN.get(), 24));
        runTicks(level, pos, press, 120);
        eq("24 个沥青 ⇒ 2 块柏油块", 2, inv.getStackInSlot(outSlot).getCount());
        eq("24 个沥青正好被吃光", 0, inv.getStackInSlot(inSlot).getCount());

        // ④ 回归：铁锭还是 1 个进 1 个出
        inv.setStackInSlot(outSlot, ItemStack.EMPTY);
        inv.setStackInSlot(inSlot, new ItemStack(net.minecraft.world.item.Items.IRON_INGOT, 3));
        runTicks(level, pos, press, 60);
        eq("铁锭：出 1 个铁板", 1, inv.getStackInSlot(outSlot).getCount());
        ok("产物是铁板", inv.getStackInSlot(outSlot).is(ModItems.IRON_PLATE.get()));
        eq("铁锭：只吃掉 1 个（剩 2）", 2, inv.getStackInSlot(inSlot).getCount());

        // ⑤ 输出槽放不下 ⇒ 卡在满进度等位置、不吃料
        inv.setStackInSlot(outSlot, new ItemStack(ModBlocks.ASPHALT_BLOCK_ITEM.get(), 64));
        inv.setStackInSlot(inSlot, new ItemStack(ModItems.BITUMEN.get(), 12));
        runTicks(level, pos, press, 61);
        eq("输出满：状态 = 输出槽放不下",
                HydraulicPressBlockEntity.STATUS_OUTPUT_FULL,
                data.get(HydraulicPressBlockEntity.DATA_STATUS));
        eq("输出满：12 个沥青一个都不吃", 12, inv.getStackInSlot(inSlot).getCount());

        level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
    }

    /** 连跑 n tick，每 tick 先把电灌满（模拟"持续供电"）。 */
    private static void runTicks(ServerLevel level, BlockPos pos, HydraulicPressBlockEntity press, int n) {
        for (int i = 0; i < n; i++) {
            press.getEnergyStorage().receiveEnergy(Integer.MAX_VALUE, false);
            tick(level, pos);
        }
    }

    private static void tick(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (level.getBlockEntity(pos) instanceof HydraulicPressBlockEntity press) {
            HydraulicPressBlockEntity.tick(level, pos, state, press);
        }
    }
}
