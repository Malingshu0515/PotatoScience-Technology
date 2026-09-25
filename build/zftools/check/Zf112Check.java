package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * ⚠⚠ <b>诊断工具（ZF112 的临时探针）</b>：锂电池构造间 + 三元锂配方改动。
 *
 * <p>用户原话：「加一个锂电池构造间 通入硫酸 放入粗锰/粗铝and 镍/粗镍 and 碳酸锂 and钴/粗钴
 * 每t消耗10mb硫酸 30s后产出一个锂电池原件 不消耗电
 * 三元锂配方里的碳酸锂改成锂电池原件 金属板统一换成纸 别的电容什么的不变」。</p>
 *
 * <p>六段：① 注册与能力（**没有**能量能力是重点）② 槽门禁（"或"）③ 缺料/断酸的分支
 * ④ 跑满一炉的账（600 tick、6000 mB 酸、四样各扣 1、出 1 个原件）⑤ 存档往返
 * ⑥ 三元锂配方（纸 + 原件 + 电容 + 一般金属块）真在配方管理器里。</p>
 *
 * <p>⚠ 期望值一律写**用户说的字面量**（10/600/6000/1/30），不从被测常量抄（§4.27）。</p>
 * <p>挂载：`PotatoST` 构造器加一行 `Zf112Check.register();`，跑完**先抄进
 * `build/zftools/check/` 再删**（ZF107 的教训）。</p>
 */
public final class Zf112Check {

    private static final String TAG = "[A112] ";
    private static final BlockPos P = new BlockPos(120, 200, 120);
    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf112_probe_utf8.txt";

    private static boolean registered;
    private static int passed;
    private static int failed;

    private Zf112Check() {
    }

    private static void say(String s) {
        System.out.println(s);
        REPORT.append(s).append('\n');
    }

    private static void check(String name, boolean ok) {
        if (ok) {
            passed++;
        } else {
            failed++;
        }
        say(TAG + (ok ? "[OK]   " : "[FAIL] ") + name);
    }

    private static void eq(String name, long want, long got) {
        check(name + "（期望 " + want + "，实际 " + got + "）", want == got);
    }

    private static void flush() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF112 探针报告（锂电池构造间 + 三元锂配方）· UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "全绿" : failed + " 条 FAIL") + "（通过 " + passed + "）\n\n");
            w.write(REPORT.toString());
        } catch (Throwable t) {
            say(TAG + "report write failed: " + t);
        }
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf112Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        passed = 0;
        try {
            run(event.getServer().overworld());
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String l : sw.toString().split("\n")) {
                say(TAG + "    " + l);
            }
            failed++;
        } finally {
            say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**")
                    + " (passed " + passed + ")");
            say(TAG + "done, halting server");
            flush();
            event.getServer().halt(false);
        }
    }

    private static void run(ServerLevel level) {
        level.setBlock(P, Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(P, ModBlocks.LITHIUM_BATTERY_PLANT.get().defaultBlockState(), 3);
        if (!(level.getBlockEntity(P) instanceof LithiumBatteryPlantBlockEntity be)) {
            check("放下方块后拿到方块实体", false);
            return;
        }
        check("放下方块后拿到方块实体", true);

        // ---------- ① 注册与能力 ----------
        say(TAG + "① registry & capabilities");
        check("方块注册名 = lithium_battery_plant",
                ModBlocks.LITHIUM_BATTERY_PLANT.getId().toString()
                        .equals("potato_s_t:lithium_battery_plant"));
        check("菜单注册名 = lithium_battery_plant",
                ModMenus.LITHIUM_BATTERY_PLANT_MENU.getId().toString()
                        .equals("potato_s_t:lithium_battery_plant"));
        check("有物品能力", level.getCapability(Capabilities.ItemHandler.BLOCK, P, null) != null);
        check("有流体能力", level.getCapability(Capabilities.FluidHandler.BLOCK, P, null) != null);
        check("**没有**能量能力（用户：不消耗电）",
                level.getCapability(Capabilities.EnergyStorage.BLOCK, P, null) == null);
        eq("槽数 = 5（4 输入 + 1 输出）", 5, be.getInventory().getSlots());
        eq("一炉 30 秒 = 600 tick", 600, LithiumBatteryPlantBlockEntity.DURATION_TICKS);
        eq("每 tick 1 mB（ZF115：原来是 10）", 1, LithiumBatteryPlantBlockEntity.ACID_PER_TICK);
        eq("一炉 600 mB（ZF115：原来是 6000）", 600, LithiumBatteryPlantBlockEntity.ACID_PER_OPERATION);
        eq("罐装得下一炉（800 ≥ 600）", 800, LithiumBatteryPlantBlockEntity.TANK_CAPACITY);

        // ---------- ② 槽门禁 ----------
        say(TAG + "② slot gate (either/or)");
        check("槽0 收粗锰", LithiumBatteryPlantBlockEntity.acceptsInput(0,
                new ItemStack(PotatoSTOres.RAW_MANGANESE.get())));
        check("槽0 收粗铝", LithiumBatteryPlantBlockEntity.acceptsInput(0,
                new ItemStack(PotatoSTOres.RAW_ALUMINUM.get())));
        check("槽0 不收镍锭", !LithiumBatteryPlantBlockEntity.acceptsInput(0,
                new ItemStack(ModItems.NICKEL_INGOT.get())));
        check("槽1 收镍锭", LithiumBatteryPlantBlockEntity.acceptsInput(1,
                new ItemStack(ModItems.NICKEL_INGOT.get())));
        check("槽1 收粗镍", LithiumBatteryPlantBlockEntity.acceptsInput(1,
                new ItemStack(PotatoSTOres.RAW_NICKEL.get())));
        check("槽2 收碳酸锂", LithiumBatteryPlantBlockEntity.acceptsInput(2,
                new ItemStack(ModItems.LITHIUM_CARBONATE.get())));
        check("槽2 不收粗锂", !LithiumBatteryPlantBlockEntity.acceptsInput(2,
                new ItemStack(PotatoSTOres.RAW_LITHIUM.get())));
        check("槽3 收钴锭", LithiumBatteryPlantBlockEntity.acceptsInput(3,
                new ItemStack(ModItems.COBALT_INGOT.get())));
        check("槽3 收粗钴", LithiumBatteryPlantBlockEntity.acceptsInput(3,
                new ItemStack(PotatoSTOres.RAW_COBALT.get())));
        check("输出槽不收东西（isItemValid=false）",
                !be.getInventory().isItemValid(LithiumBatteryPlantBlockEntity.OUTPUT_SLOT,
                        new ItemStack(ModItems.LITHIUM_BATTERY_COMPONENT.get())));

        // ---------- ③ 分支 ----------
        say(TAG + "③ missing input / dry acid");
        IFluidHandler acid = level.getCapability(Capabilities.FluidHandler.BLOCK, P, null);
        int taken = acid == null ? -1 : acid.fill(
                new FluidStack(ModFluids.SULFURIC_ACID.get(), 500), IFluidHandler.FluidAction.EXECUTE);
        eq("硫酸灌得进去 500 mB", 500, taken);
        eq("罐里 500 mB", 500, be.getTank().getFluidAmount());
        check("水灌不进去（只收硫酸）", acid != null && acid.fill(
                new FluidStack(net.minecraft.world.level.material.Fluids.WATER, 100),
                IFluidHandler.FluidAction.EXECUTE) == 0);
        check("酸抽不出来（只进不出）", acid != null && acid.drain(100,
                IFluidHandler.FluidAction.EXECUTE).isEmpty());

        be.getInventory().setStackInSlot(0, new ItemStack(PotatoSTOres.RAW_MANGANESE.get(), 2));
        be.getInventory().setStackInSlot(1, new ItemStack(ModItems.NICKEL_INGOT.get(), 2));
        be.getInventory().setStackInSlot(2, new ItemStack(ModItems.LITHIUM_CARBONATE.get(), 2));
        // 故意空着槽 3
        int acid0 = be.getTank().getFluidAmount();
        for (int i = 0; i < 5; i++) {
            be.serverTick();
        }
        eq("缺一样原料 ⇒ 进度 0", 0, be.getProgress());
        eq("缺一样原料 ⇒ 状态 18", LithiumBatteryPlantBlockEntity.STATUS_INPUTS, be.getStatus());
        eq("缺一样原料 ⇒ 一滴酸都不扣", acid0, be.getTank().getFluidAmount());

        be.getInventory().setStackInSlot(3, new ItemStack(ModItems.COBALT_INGOT.get(), 2));
        be.getTank().drain(10000, IFluidHandler.FluidAction.EXECUTE);   // 抽干（探针自己用 handler 之外的口子）
        while (be.getTank().getFluidAmount() >= 1) {
            be.getTank().drain(1, IFluidHandler.FluidAction.EXECUTE);
        }
        for (int i = 0; i < 3; i++) {
            be.serverTick();
        }
        eq("断酸 ⇒ 状态 17", LithiumBatteryPlantBlockEntity.STATUS_NO_ACID, be.getStatus());
        eq("断酸 ⇒ 进度仍是 0", 0, be.getProgress());

        // ---------- ④ 跑满一炉 ----------
        say(TAG + "④ one full batch: 600 ticks, 6000 mB acid");
        while (be.getTank().getFluidAmount() < 600) {          // 罐 8000 ⇒ 一炉装得下
            int got = acid == null ? 0 : acid.fill(new FluidStack(ModFluids.SULFURIC_ACID.get(), 1000),
                    IFluidHandler.FluidAction.EXECUTE);
            if (got <= 0) {
                break;
            }
        }
        eq("开机前罐里有 800 mB（满罐，一炉只吃 600）", 800, be.getTank().getFluidAmount());
        for (int i = 0; i < 600; i++) {
            be.serverTick();
        }
        eq("跑满 600 tick 后进度归零", 0, be.getProgress());
        ItemStack out = be.getInventory().getStackInSlot(LithiumBatteryPlantBlockEntity.OUTPUT_SLOT);
        check("输出槽 = 1 个锂电池原件（实际 " + out.getCount() + " × "
                        + out.getHoverName().getString() + "）",
                out.is(ModItems.LITHIUM_BATTERY_COMPONENT.get()) && out.getCount() == 1);
        eq("硫酸正好扣掉 600 mB（800 − 600 = 200）", 200, be.getTank().getFluidAmount());
        for (int slot = 0; slot < 4; slot++) {
            eq("输入槽 " + slot + " 从 2 扣到 1",
                    1, be.getInventory().getStackInSlot(slot).getCount());
        }
        eq("状态 = 运行中", LithiumBatteryPlantBlockEntity.STATUS_RUNNING, be.getStatus());

        // ---------- ⑤ 存档往返 ----------
        say(TAG + "⑤ save / load round trip");
        net.minecraft.nbt.CompoundTag tag = be.saveWithFullMetadata(level.registryAccess());
        LithiumBatteryPlantBlockEntity clone = new LithiumBatteryPlantBlockEntity(P, be.getBlockState());
        clone.loadWithComponents(tag, level.registryAccess());
        eq("往返后进度", be.getProgress(), clone.getProgress());
        eq("往返后罐里的酸", be.getTank().getFluidAmount(), clone.getTank().getFluidAmount());
        eq("往返后输出槽件数", out.getCount(),
                clone.getInventory().getStackInSlot(LithiumBatteryPlantBlockEntity.OUTPUT_SLOT).getCount());
        eq("往返后 0 号槽件数", 1, clone.getInventory().getStackInSlot(0).getCount());

        // ---------- ⑥ 三元锂配方 ----------
        say(TAG + "⑥ ternary battery recipe (paper + component)");
        RecipeHolder<?> r = level.getRecipeManager()
                .byKey(net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                        PotatoST.MODID, "lithium_battery")).orElse(null);
        check("lithium_battery 配方在配方管理器里", r != null);
        if (r.value() instanceof net.minecraft.world.item.crafting.ShapedRecipe sr) {
            int paper = 0;
            int comp = 0;
            int cap = 0;
            int metal = 0;
            for (net.minecraft.world.item.crafting.Ingredient ing : sr.getIngredients()) {
                for (ItemStack s : ing.getItems()) {
                    if (s.is(Items.PAPER)) {
                        paper++;
                    }
                    if (s.is(ModItems.LITHIUM_BATTERY_COMPONENT.get())) {
                        comp++;
                    }
                    if (s.is(ModItems.CAPACITOR.get())) {
                        cap++;
                    }
                    if (s.is(ModBlocks.COMMON_METAL_BLOCK_ITEM.get())) {
                        metal++;
                    }
                }
            }
            eq("配方里纸的格数 = 6（原来的 4 块铝板 + 2 块铜板）", 6, paper);
            eq("配方里锂电池原件的格数 = 1（原来那格碳酸锂）", 1, comp);
            eq("电容仍在（1 格）", 1, cap);
            eq("一般金属块仍在（1 格）", 1, metal);
            eq("九宫格一共 9 格", 9, sr.getIngredients().size());
        } else {
            check("lithium_battery 是 shaped 配方", false);
        }
        check("锂电池原件不是空气（注册成功）",
                ModItems.LITHIUM_BATTERY_COMPONENT.get() != Items.AIR);

        level.setBlock(P, Blocks.AIR.defaultBlockState(), 3);
    }
}
