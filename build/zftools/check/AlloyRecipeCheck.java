package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF62 临时探针，验证完必须删）</b>：
 * 合金冶炼炉的第一条配方 —— <b>铝锭 + 钛锭 + 银锭 → 1 轻质钛合金，30s（600 tick）、800 FE/t</b>。
 *
 * <p>要验的（每条都能单独失败）：</p>
 * <ol>
 *   <li><b>配方认得对</b>：三种锭齐了才开工（缺一样进度必须是 0，且不许白扣电）；</li>
 *   <li><b>电的账分毫不差</b>：每 tick 正好扣 <b>800</b>，跑满一轮 = 600 × 800 = <b>480,000 FE</b>，
 *       产物 1 个、三种原料各扣 1、进度归零；</li>
 *   <li><b>电不够时进度不许清</b>（停电不该把做了 29 秒的活扔掉），也不许偷偷推进；</li>
 *   <li><b>产物放不下 ⇒ 不开工、进度归零、不扣电</b>；</li>
 *   <li><b>参数守卫</b>：800 FE/t ≤ 储能 32768（ZF42 那条"单 tick 耗电不能超储能"）。</li>
 * </ol>
 *
 * <p>⚠ <b>数字一律写成字面量</b>（800 / 480000 / 600）：期望值来自<b>用户的话</b>
 * （ZF63 他把 5800 改成 800），**不从被测常量抄** —— 抄的话改坏常数探针也跟着变，等于没检查（§4.27）。</p>
 */
public final class AlloyRecipeCheck {

    private static final String TAG = "[AR] ";
    private static final Direction FACING = Direction.SOUTH;
    private static final BlockPos C = new BlockPos(352, 260, 176);
    private static boolean registered;

    private AlloyRecipeCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloyRecipeCheck.class);
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
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            buildLayer(level, y);
        }
        AlloySmelterBlock.tryAutoForm(level, C);
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return check("controller block entity exists", false);
        }
        failed += check("machine formed", be.isFormed());
        failed += check("fresh buffer is empty (got " + be.getEnergyStored() + ")", be.getEnergyStored() == 0);
        be.craftTick();
        failed += check("no energy at all: progress stays 0 (got " + be.getProgress() + ")",
                be.getProgress() == 0);

        int in = AlloySmelterBlockEntity.INPUT_FIRST;
        int out = AlloySmelterBlockEntity.OUTPUT_FIRST;

        // ---------- ① 缺一样原料 ⇒ 不开工、不扣电 ----------
        System.out.println(TAG + "(1) the recipe needs all three ingots");
        be.getInventory().setStackInSlot(in, new ItemStack(ModItems.ALUMINUM_INGOT.get(), 4));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.TITANIUM_INGOT.get(), 4));
        fill(be, 40_000L);
        int e0 = be.getEnergyStored();
        for (int i = 0; i < 10; i++) {
            be.craftTick();
        }
        failed += check("aluminium + titanium only (no silver): progress stays 0 (got "
                + be.getProgress() + ")", be.getProgress() == 0);
        failed += check("...and no energy was spent (energy " + e0 + " -> " + be.getEnergyStored() + ")",
                e0 == be.getEnergyStored());

        // ---------- ② 三种齐了 ⇒ 跑满一轮，电账分毫不差 ----------
        // ⚠ 第一版这里算错了账：缓冲里本来就躺着上一段留下的电（收电接口只进不出、注入还会被
        //   储能上限截住），所以必须用**恒等式**算：花掉的 = 起始余额 + 注入 − 结束余额。
        System.out.println(TAG + "(2) all three ingots -> one full craft, exact energy accounting");
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.SILVER_INGOT.get(), 4));
        long startBalance = be.getEnergyStored();
        long injected = 0;
        int expected = 600;                                  // 30 秒，用户说的（字面量）
        for (int i = 0; i < expected; i++) {
            injected += fill(be, 800L);                      // 正好这一 tick 的耗电（字面量，不从常量抄）
            be.craftTick();
        }
        long spent = startBalance + injected - be.getEnergyStored();
        System.out.println(TAG + "  ticks=" + expected + " startBalance=" + startBalance
                + " injected=" + injected + " spent=" + spent + " buffer=" + be.getEnergyStored());
        failed += check("each tick costs exactly 800 FE (spent=" + spent + ")",
                spent == (long) expected * 800);
        failed += check("one craft = 600 x 800 = 480000 FE", spent == 480_000L);
        ItemStack result = be.getInventory().getStackInSlot(out);
        failed += check("output slot = 1 light titanium alloy (got " + result.getCount() + " x "
                        + result.getHoverName().getString() + ")",
                result.is(ModItems.LIGHT_TITANIUM_ALLOY.get()) && result.getCount() == 1);
        failed += check("aluminium 4 -> 3 (got "
                + be.getInventory().getStackInSlot(in).getCount() + ")",
                be.getInventory().getStackInSlot(in).getCount() == 3);
        failed += check("titanium 4 -> 3 (got "
                + be.getInventory().getStackInSlot(in + 1).getCount() + ")",
                be.getInventory().getStackInSlot(in + 1).getCount() == 3);
        failed += check("silver 4 -> 3 (got "
                + be.getInventory().getStackInSlot(in + 2).getCount() + ")",
                be.getInventory().getStackInSlot(in + 2).getCount() == 3);
        failed += check("progress reset to 0 (got " + be.getProgress() + ")", be.getProgress() == 0);

        // ---------- ③ 电不够：进度停住，绝不清零 ----------
        //    此刻缓冲里还剩不到 5 tick 的电（注入被储能上限截住过）⇒ 正好拿它验"跑到没电"：
        //    收电接口只进不出，探针没办法主动放电，这是最自然的"用完"方式。
        System.out.println(TAG + "(3) brownout: progress must hold, not reset");
        int progressBefore = be.getProgress();
        int runTicks = 0;
        while (be.getEnergyStored() >= AlloySmelterBlockEntity.ENERGY_PER_TICK) {
            be.craftTick();
            runTicks++;
        }
        failed += check("ran on the leftover buffer until dry (" + runTicks + " ticks, buffer now "
                        + be.getEnergyStored() + ")",
                runTicks > 0 && be.getEnergyStored() < AlloySmelterBlockEntity.ENERGY_PER_TICK);
        failed += check("progress advanced exactly by those ticks (" + progressBefore + " -> "
                        + be.getProgress() + ")",
                be.getProgress() == progressBefore + runTicks);
        int held = be.getProgress();
        be.craftTick();
        failed += check("brownout: progress HOLDS at " + held + " (got " + be.getProgress() + ")",
                be.getProgress() == held);
        be.getInventory().setStackInSlot(in, ItemStack.EMPTY);         // 原料拿走 ⇒ 这一轮作废
        be.craftTick();
        failed += check("ingredient removed: progress back to 0 (got " + be.getProgress() + ")",
                be.getProgress() == 0);

        // ---------- ④ 产物放不下 ⇒ 不开工、不扣电 ----------
        System.out.println(TAG + "(4) output blocked -> no craft, no energy spent");
        for (int slot = out; slot < out + AlloySmelterBlockEntity.OUTPUT_COUNT; slot++) {
            be.getInventory().setStackInSlot(slot, new ItemStack(Items.STONE, 64));
        }
        be.getInventory().setStackInSlot(in, new ItemStack(ModItems.ALUMINUM_INGOT.get(), 1));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.TITANIUM_INGOT.get(), 1));
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.SILVER_INGOT.get(), 1));
        fill(be, 32_000L);
        int e1 = be.getEnergyStored();
        for (int i = 0; i < 5; i++) {
            be.craftTick();
        }
        failed += check("output blocked: progress stayed 0 (got " + be.getProgress() + ")", be.getProgress() == 0);
        failed += check("output blocked: nothing spent (" + e1 + " -> " + be.getEnergyStored() + ")",
                e1 == be.getEnergyStored());

        // ---------- ⑤ 参数（期望值全是**用户说的字面量**，不从被测常量抄） ----------
        System.out.println(TAG + "(5) numbers");
        failed += check("per-tick draw is exactly 800 FE/t (got "
                        + AlloySmelterBlockEntity.ENERGY_PER_TICK + ")",
                AlloySmelterBlockEntity.ENERGY_PER_TICK == 800);
        failed += check("800 FE/t <= buffer " + AlloySmelterBlockEntity.MAX_ENERGY + " (ZF42)",
                AlloySmelterBlockEntity.ENERGY_PER_TICK <= AlloySmelterBlockEntity.MAX_ENERGY);
        failed += check("30 s = 600 ticks (got " + AlloySmelterBlockEntity.DURATION_TICKS + ")",
                AlloySmelterBlockEntity.DURATION_TICKS == 600);
        failed += check("recipe table has 1 entry (got " + AlloySmelterRecipes.all().size() + ")",
                AlloySmelterRecipes.all().size() == 1);
        failed += check("recipe total energy = 480000 FE (got "
                        + AlloySmelterRecipes.all().get(0).totalEnergy() + ")",
                AlloySmelterRecipes.all().get(0).totalEnergy() == 480_000L);
        clear(level);
        return failed;
    }

    // ==================== 工具 ====================
    /** 往缓冲里塞电，返回**真正收下**的量（收电接口只进不出，所以探针只能靠"刚好够"来控制余额）。 */
    private static long fill(AlloySmelterBlockEntity be, long amount) {
        var storage = be.getEnergyStorage();
        if (storage == null) {
            return 0;
        }
        long accepted = 0;
        while (accepted < amount) {
            int got = storage.receiveEnergy((int) Math.min(amount - accepted, 1_000_000L), false);
            if (got <= 0) {
                break;
            }
            accepted += got;
        }
        return accepted;
    }

    private static void buildLayer(ServerLevel level, int y) {
        for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
            for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                AlloySmelterStructure.Kind kind = AlloySmelterStructure.kindAt(y, j, i);
                BlockState state = kind == AlloySmelterStructure.Kind.CONTROLLER
                        ? ModBlocks.ALLOY_SMELTER.get().defaultBlockState()
                                .setValue(AlloySmelterBlock.FACING, FACING)
                        : AlloySmelterStructure.blockFor(kind).defaultBlockState();
                level.setBlock(AlloySmelterStructure.offset(C, FACING, y, j, i), state, 3);
            }
        }
    }

    private static void clear(ServerLevel level) {
        level.setBlock(C, Blocks.AIR.defaultBlockState(), 3);
        for (BlockPos p : AlloySmelterStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
