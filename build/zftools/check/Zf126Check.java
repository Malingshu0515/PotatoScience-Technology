package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * ⚠️ <b>诊断工具（ZF126 的临时探针）</b>：大型柴油发电机的 <b>18000 FE 缓冲</b>。
 *
 * <p>用户原话（附游戏内截图）：「这个加个fe缓存 18k的fe」。</p>
 *
 * <p>要证的是"18k 这个数真的按 18k 在跑"，而不是只改了个常量：</p>
 * <ol>
 *   <li>常量就是 18000（读的就是方块实体那个 public static final）；</li>
 *   <li>照图纸搭 30 格成型（不重复 ZF125 的全套，只搭到能开工）；</li>
 *   <li><b>缓冲空着连跑 3 tick</b>：7200 → 14400 → <b>第 3 tick 暂停</b>（只剩 3600 的空间，
 *       装不下整整一 tick 的 7200）⇒ 电量停 14400、状态 OUTPUT_FULL、柴油只烧了 2 mB；</li>
 *   <li><b>抽走 7200 之后能接着跑</b>（抽一 tick 的量 ⇒ 又发一 tick，柴油 98 → 97）；</li>
 *   <li>全程<b>峰值不超过 18000</b>（多出来的电一分都不许凭空冒出来）；</li>
 *   <li>一次最多只能抽走缓冲里真实存在的那些（抽 999999 拿到多少就是多少，不会多）。</li>
 * </ol>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf126Check.register();`，跑完用
 * {@code _zf126_unprobe.py} 摘掉（**先抄进 `build/zftools/check/` 再删**）。</p>
 */
public final class Zf126Check {

    private static final String TAG = "[A126] ";
    private static final Direction FACING = Direction.SOUTH;
    private static final BlockPos C = new BlockPos(384, 300, 176);   // 换个高度，别踩 ZF125 的现场

    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf126_probe_utf8.txt";

    private static boolean registered;
    private static int passed;
    private static int failed;

    private Zf126Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void check(String name, boolean ok) {
        if (ok) {
            passed++;
        } else {
            failed++;
        }
        say(TAG + (ok ? "[OK]   " : "[FAIL] ") + name);
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF126 探针报告（大型柴油发电机的 18000 FE 缓冲）· UTF-8 · §4.50\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf126Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            clear(level);
            run(level);
            clear(level);
        } catch (Throwable t) {
            failed++;
            say(TAG + "[FAIL] 探针自己抛异常：" + t);
            t.printStackTrace(System.out);
        }
        say(TAG + "done, halting server");
        flushReport();
        event.getServer().halt(false);
    }

    private static void run(ServerLevel level) {
        say(TAG + "① 常量与成型");
        check("MAX_ENERGY == 18000（用户原话「18k的fe」）",
                DieselGeneratorBlockEntity.MAX_ENERGY == 18_000);
        check("ENERGY_PER_TICK == 7200（产量没被顺手改掉）",
                DieselGeneratorBlockEntity.ENERGY_PER_TICK == 7200);
        check("两个数**不是**同一个常量（解耦了）",
                DieselGeneratorBlockEntity.MAX_ENERGY != DieselGeneratorBlockEntity.ENERGY_PER_TICK);

        build(level, FACING);
        tick(level, 12);                       // 12 tick 足够让结构复查（周期 10）跑一遍
        DieselGeneratorBlockEntity be = controller(level);
        check("控制器方块实体建起来了", be != null);
        if (be == null) {
            return;
        }
        check("30 格摆齐 ⇒ 成型", be.isFormed());

        be.getTank().drain(100000, IFluidHandler.FluidAction.EXECUTE);
        be.getFluidHandler().fill(new FluidStack(ModFluids.DIESEL.get(), 100),
                IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().extractEnergy(1_000_000, false);

        say(TAG + "② 缓冲空着连跑 3 tick（不抽电）");
        int peak = 0;
        int[] after = new int[3];
        for (int n = 0; n < 3; n++) {
            tick(level, 1);
            after[n] = be.getEnergyStored();
            peak = Math.max(peak, after[n]);
        }
        check("第 1 tick 后 = 7200（实际 " + after[0] + "）", after[0] == 7200);
        check("第 2 tick 后 = 14400（实际 " + after[1] + "）", after[1] == 14400);
        check("第 3 tick **暂停**：电量仍是 14400（实际 " + after[2] + "）", after[2] == 14400);
        check("第 3 tick 的状态是 OUTPUT_FULL（缓冲装不下整整一 tick）",
                be.getStatus() == DieselGeneratorBlockEntity.STATUS_OUTPUT_FULL);
        check("这 3 tick 只烧了 2 mB 柴油（实剩 " + be.dieselAmount() + " mB）",
                be.dieselAmount() == 98);
        check("峰值没超过 18000（实际 " + peak + "）", peak <= 18_000);

        say(TAG + "③ 抽走一 tick 的量之后能接着跑");
        int got = be.getEnergyStorage().extractEnergy(7200, false);
        check("一次抽走 7200（实际 " + got + "）", got == 7200);
        tick(level, 1);
        check("抽出后一 tick 又发满：14400（实际 " + be.getEnergyStored() + "）",
                be.getEnergyStored() == 14400);
        check("柴油跟着少 1 mB（98 → " + be.dieselAmount() + "）", be.dieselAmount() == 97);
        check("状态回到 RUNNING", be.getStatus() == DieselGeneratorBlockEntity.STATUS_RUNNING);

        say(TAG + "④ 抽不出来的东西抽不出来");
        int all = be.getEnergyStorage().extractEnergy(999_999, false);
        check("抽 999999 只拿到缓冲里真实存在的 14400（实际 " + all + "）", all == 14400);
        check("抽干之后缓冲是 0（实际 " + be.getEnergyStored() + "）", be.getEnergyStored() == 0);
        int again = be.getEnergyStorage().extractEnergy(999_999, false);
        check("再抽一次是 0（不会凭空多出来）", again == 0);
        check("缓冲是「只出不进」：receiveEnergy 恒 0",
                be.getEnergyStorage().receiveEnergy(1000, false) == 0);
    }

    // ================= 工具（照 ZF125 探针那套）=================

    private static DieselGeneratorBlockEntity controller(ServerLevel level) {
        return level.getBlockEntity(C) instanceof DieselGeneratorBlockEntity be ? be : null;
    }

    private static void tick(ServerLevel level, int n) {
        for (int i = 0; i < n; i++) {
            BlockState state = level.getBlockState(C);
            if (level.getBlockEntity(C) instanceof DieselGeneratorBlockEntity be) {
                DieselGeneratorBlockEntity.tick(level, C, state, be);
            }
        }
    }

    private static void build(ServerLevel level, Direction facing) {
        for (int y = 0; y < DieselGeneratorStructure.HEIGHT; y++) {
            for (int j = 0; j < DieselGeneratorStructure.DEPTH; j++) {
                for (int i = 0; i < DieselGeneratorStructure.WIDTH; i++) {
                    DieselGeneratorStructure.Kind kind = DieselGeneratorStructure.kindAt(y, j, i);
                    BlockPos p = DieselGeneratorStructure.offset(C, facing, y, j, i);
                    if (kind == DieselGeneratorStructure.Kind.CONTROLLER) {
                        level.setBlock(p, ModBlocks.DIESEL_GENERATOR.get().defaultBlockState()
                                .setValue(DieselGeneratorBlock.FACING, facing), 3);
                    } else {
                        level.setBlock(p, DieselGeneratorStructure.blockFor(kind).defaultBlockState(), 3);
                    }
                }
            }
        }
    }

    private static void clear(ServerLevel level) {
        level.setBlock(C.relative(FACING), Blocks.AIR.defaultBlockState(), 3);
        for (BlockPos p : DieselGeneratorStructure.positions(C, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
        level.setBlock(C, Blocks.AIR.defaultBlockState(), 3);
    }
}
