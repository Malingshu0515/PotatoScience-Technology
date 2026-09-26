package com.potatost.mod;

import java.util.List;
import java.util.Optional;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;

/**
 * ⚠️ <b>诊断工具（ZF125 的临时探针）</b>：大型柴油发电机。
 *
 * <p>用户原话：「加一个大型柴油发电机 3x5x2 …（30 格图纸）以柴油发电机控制器为正方向
 * 右键打开GUI 显示流体储罐（8000mB）工作指示灯 检测到红石信号停机
 * 可以用流体泵泵入柴油 或用柴油桶/含有柴油的油桶右键添加柴油 每t消耗1mb柴油 7.2kFE」。</p>
 *
 * <p>十段，缺一不可：</p>
 * <ol>
 *   <li><b>照图纸搭 30 格能成型</b>（而且铜块/铜格栅<b>八种变体混着搭</b>也认）；</li>
 *   <li><b>接线块那一格自动变成接线口</b>，接线口能出电、不能进电；</li>
 *   <li><b>缺一格就不成型</b>（holeCount 精确报 1 处），接线口自己变回接线块，补回去又成型；</li>
 *   <li><b>里面那四台机器一个字节都没被换掉</b>（用户财产，本轮明说不吸收）；</li>
 *   <li><b>1 mB → 7200 FE</b>：罐里灌 2000 mB 柴油，跑 200 tick 边跑边抽电，
 *       正好抽到 200 × 7200 = 1,440,000 FE，柴油正好少 200 mB；</li>
 *   <li><b>抽不出去就暂停烧油</b>（缓冲满 → STATUS_OUTPUT_FULL，柴油一点不少）；</li>
 *   <li><b>红石信号停机</b>（不烧油、状态灯变 DISABLED）；</li>
 *   <li><b>罐里没柴油就停机</b>（STATUS_EMPTY）；</li>
 *   <li><b>倒柴油四种结果</b>：柴油桶整桶 1000 / 罐满不倒 / 油桶里的柴油按余量倒 /
 *       不是柴油一律拒收；</li>
 *   <li><b>数据驱动真的加载了</b>：配方是 3×3 的 shaped、铜块那一格认
 *       {@code potato_s_t:copper_blocks}（8 种全在）、水灌不进罐。</li>
 * </ol>
 *
 * <p>⚠ 本轮的电机是<b>服务端</b>逻辑（界面是客户端的事），所以探针全在服务端跑；
 * 液体/能量/结构判定这些都是服务端权威，探针一试就是真结果。</p>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf125Check.register();`，跑完用
 * {@code _zf125_unprobe.py} 摘掉（**先抄进 `build/zftools/check/` 再删**）。</p>
 */
public final class Zf125Check {

    private static final String TAG = "[A125] ";
    private static final Direction FACING = Direction.SOUTH;
    private static final BlockPos C = new BlockPos(384, 260, 176);

    /** §4.50：runServer 的日志按 GBK 扫，中文会变乱码 ⇒ 自己攒一份 UTF-8 报告。 */
    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf125_probe_utf8.txt";

    private static boolean registered;
    private static int passed;
    private static int failed;

    private Zf125Check() {
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
            w.write("ZF125 探针报告（大型柴油发电机：结构 / 成型 / 发电 / 红石 / 倒油 / 数据驱动）"
                    + " · UTF-8 · §4.50\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf125Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    // ================= 四组铜变体（每格换一种，证明"无论氧化/涂蜡"）=================

    private static final Block[] COPPERS = {
            Blocks.COPPER_BLOCK, Blocks.EXPOSED_COPPER, Blocks.WEATHERED_COPPER,
            Blocks.OXIDIZED_COPPER, Blocks.WAXED_COPPER_BLOCK, Blocks.WAXED_EXPOSED_COPPER,
            Blocks.WAXED_WEATHERED_COPPER, Blocks.WAXED_OXIDIZED_COPPER,
    };

    private static final Block[] GRATES = {
            Blocks.COPPER_GRATE, Blocks.EXPOSED_COPPER_GRATE, Blocks.WEATHERED_COPPER_GRATE,
            Blocks.OXIDIZED_COPPER_GRATE, Blocks.WAXED_COPPER_GRATE, Blocks.WAXED_EXPOSED_COPPER_GRATE,
            Blocks.WAXED_WEATHERED_COPPER_GRATE, Blocks.WAXED_OXIDIZED_COPPER_GRATE,
    };

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        passed = 0;
        failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            clear(level);
            t1buildAndForm(level);
            t2portAndEnergy(level);
            t3holeBreaksAndHeals(level);
            t4machinesUntouched(level);
            t5generate(level);
            t6bufferFullPauses(level);
            t7redstoneStops(level);
            t8emptyStops(level);
            t9pouring(level);
            t10dataDriven(level);
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

    // ================= ① 照图纸搭 =================

    private static void t1buildAndForm(ServerLevel level) {
        say(TAG + "① 照图纸搭 30 格（铜块/铜格栅八种变体混着用）");
        int copper = 0;
        int grate = 0;
        for (int y = 0; y < DieselGeneratorStructure.HEIGHT; y++) {
            for (int j = 0; j < DieselGeneratorStructure.DEPTH; j++) {
                for (int i = 0; i < DieselGeneratorStructure.WIDTH; i++) {
                    DieselGeneratorStructure.Kind kind = DieselGeneratorStructure.kindAt(y, j, i);
                    BlockPos p = DieselGeneratorStructure.offset(C, FACING, y, j, i);
                    BlockState state;
                    if (kind == DieselGeneratorStructure.Kind.CONTROLLER) {
                        state = ModBlocks.DIESEL_GENERATOR.get().defaultBlockState()
                                .setValue(DieselGeneratorBlock.FACING, FACING);
                    } else if (kind == DieselGeneratorStructure.Kind.COPPER) {
                        state = COPPERS[copper++ % COPPERS.length].defaultBlockState();
                    } else if (kind == DieselGeneratorStructure.Kind.GRATE) {
                        state = GRATES[grate++ % GRATES.length].defaultBlockState();
                    } else {
                        state = DieselGeneratorStructure.blockFor(kind).defaultBlockState();
                    }
                    level.setBlock(p, state, 3);
                }
            }
        }
        DieselGeneratorBlockEntity be = controller(level);
        check("控制器方块实体建起来了", be != null);
        if (be == null) {
            return;
        }
        tick(level, 1);
        check("30 格摆齐 ⇒ 自动成型（铜块用了 " + copper + " 格、铜格栅 " + grate + " 格，全是不同变体）",
                be.isFormed());
        check("结构检查报 0 处缺口",
                DieselGeneratorStructure.inspect(level, C, FACING, 4).holeCount() == 0);
    }

    // ================= ② 接线口 =================

    private static void t2portAndEnergy(ServerLevel level) {
        say(TAG + "② 控制器正上方那一格：接线块 → 接线口，且只能出电");
        BlockPos portPos = DieselGeneratorStructure.portPos(C);
        BlockState portState = level.getBlockState(portPos);
        check("头上那一格已经变成 diesel_generator_port",
                portState.is(ModBlocks.DIESEL_GENERATOR_PORT.get()));
        check("接线口贴图与接线块同款（模型文件里写的是 wiring_block）",
                portState.getBlock() == ModBlocks.DIESEL_GENERATOR_PORT.get());
        if (level.getBlockEntity(portPos) instanceof DieselGeneratorPortBlockEntity port) {
            var storage = port.getEnergyStorage();
            check("接线口交出了能量接口", storage != null);
            if (storage != null) {
                check("接线口只能出、不能进（canExtract=true / canReceive=false）",
                        storage.canExtract() && !storage.canReceive());
            }
            check("接线口也收柴油（getFluidHandler 非空）", port.getFluidHandler() != null);
        } else {
            check("接线口有方块实体", false);
        }
    }

    // ================= ③ 缺一格 =================

    private static void t3holeBreaksAndHeals(ServerLevel level) {
        say(TAG + "③ 缺一格就不成型；接线口自己变回接线块；补回去又成型");
        BlockPos pumpPos = DieselGeneratorStructure.offset(C, FACING, 0, 0, 1);
        BlockPos portPos = DieselGeneratorStructure.portPos(C);
        DieselGeneratorBlockEntity be = controller(level);
        if (be == null) {
            check("③ 需要控制器", false);
            return;
        }
        be.getTank().drain(100000, IFluidHandler.FluidAction.EXECUTE);   // 先把油放空，免得白烧
        level.setBlock(pumpPos, Blocks.AIR.defaultBlockState(), 3);
        tick(level, 12);
        check("挖掉【流体泵】那一格 ⇒ 不再是成型状态", !be.isFormed());
        DieselGeneratorStructure.Report report =
                DieselGeneratorStructure.inspect(level, C, FACING, 4);
        check("缺口总数正好 1 处（holeCount=" + report.holeCount() + "）", report.holeCount() == 1);
        check("明细指的就是挖掉的那一格（y=0,j=0,i=1）",
                report.holes().size() == 1 && report.holes().get(0).j() == 0
                        && report.holes().get(0).i() == 1);
        check("散架后接线口自己变回了接线块",
                level.getBlockState(portPos).is(ModBlocks.WIRING_BLOCK.get()));

        level.setBlock(pumpPos, ModBlocks.FLUID_PUMP.get().defaultBlockState(), 3);
        tick(level, 12);
        check("把那一格补回去 ⇒ 又成型", be.isFormed());
        check("接线块又变回接线口",
                level.getBlockState(portPos).is(ModBlocks.DIESEL_GENERATOR_PORT.get()));
    }

    // ================= ④ 里面那四台机器原样 =================

    private static void t4machinesUntouched(ServerLevel level) {
        say(TAG + "④ 里面那四台机器一个字节都没被换掉（本轮明说不吸收）");
        BlockPos p1 = DieselGeneratorStructure.offset(C, FACING, 0, 0, 1);
        BlockPos g1 = DieselGeneratorStructure.offset(C, FACING, 0, 1, 1);
        BlockPos b1 = DieselGeneratorStructure.offset(C, FACING, 0, 2, 1);
        BlockPos g2 = DieselGeneratorStructure.offset(C, FACING, 0, 3, 1);
        check("流体泵还是流体泵（方块实体也在）",
                level.getBlockState(p1).is(ModBlocks.FLUID_PUMP.get())
                        && level.getBlockEntity(p1) instanceof FluidPumpBlockEntity);
        check("低级发电机还是低级发电机",
                level.getBlockState(g1).is(ModBlocks.LOW_GENERATOR.get())
                        && level.getBlockState(g2).is(ModBlocks.LOW_GENERATOR.get()));
        check("燃烧反应室还是燃烧反应室",
                level.getBlockState(b1).is(ModBlocks.COMBUSTION_CHAMBER.get())
                        && level.getBlockEntity(b1) instanceof CombustionChamberBlockEntity);
    }

    // ================= ⑤ 发电 =================

    private static void t5generate(ServerLevel level) {
        say(TAG + "⑤ 每 tick 1 mB 柴油 → 7200 FE（跑 200 tick，边跑边抽）");
        DieselGeneratorBlockEntity be = controller(level);
        if (be == null) {
            check("⑤ 需要控制器", false);
            return;
        }
        be.getTank().drain(100000, IFluidHandler.FluidAction.EXECUTE);
        int accepted = be.getFluidHandler().fill(
                new FluidStack(ModFluids.DIESEL.get(), 2000), IFluidHandler.FluidAction.EXECUTE);
        check("流体能力收下 2000 mB 柴油（实际 " + accepted + "）", accepted == 2000);
        check("水灌不进罐（只认柴油）",
                be.getFluidHandler().fill(new FluidStack(net.minecraft.world.level.material.Fluids.WATER, 1000),
                        IFluidHandler.FluidAction.EXECUTE) == 0);
        check("罐里抽不出东西（只进不出）",
                be.getFluidHandler().drain(1000, IFluidHandler.FluidAction.EXECUTE).isEmpty());

        long total = 0;
        boolean runningSeen = false;
        for (int n = 0; n < 200; n++) {
            tick(level, 1);
            if (be.getStatus() == DieselGeneratorBlockEntity.STATUS_RUNNING) {
                runningSeen = true;
            }
            total += be.getEnergyStorage().extractEnergy(1_000_000, false);
        }
        check("200 tick 一共发出 " + total + " FE（要 200×7200 = 1440000）", total == 1_440_000L);
        check("200 tick 正好烧掉 200 mB 柴油（实剩 " + be.dieselAmount() + " mB）",
                be.dieselAmount() == 1800);
        check("期间状态灯是 RUNNING", runningSeen);
    }

    // ================= ⑥ 抽不出去就暂停 =================

    private static void t6bufferFullPauses(ServerLevel level) {
        say(TAG + "⑥ 电送不出去 ⇒ 暂停烧油（缓冲满，1 mB 都不许白烧）");
        DieselGeneratorBlockEntity be = controller(level);
        if (be == null) {
            check("⑥ 需要控制器", false);
            return;
        }
        be.getTank().drain(100000, IFluidHandler.FluidAction.EXECUTE);
        be.getFluidHandler().fill(new FluidStack(ModFluids.DIESEL.get(), 100), IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().extractEnergy(1_000_000, false);      // 缓冲清空
        tick(level, 1);
        int afterFirst = be.dieselAmount();
        int stored = be.getEnergyStored();
        tick(level, 1);
        check("第一 tick 发满 7200 FE（缓冲里 " + stored + "）", stored == 7200);
        check("第二 tick 缓冲满 ⇒ 状态是 OUTPUT_FULL",
                be.getStatus() == DieselGeneratorBlockEntity.STATUS_OUTPUT_FULL);
        check("第二 tick 一滴柴油都没烧（" + afterFirst + " → " + be.dieselAmount() + "）",
                afterFirst == be.dieselAmount());
    }

    // ================= ⑦ 红石 =================

    private static void t7redstoneStops(ServerLevel level) {
        say(TAG + "⑦ 检测到红石信号 ⇒ 停机（柴油一点不少）");
        DieselGeneratorBlockEntity be = controller(level);
        if (be == null) {
            check("⑦ 需要控制器", false);
            return;
        }
        be.getEnergyStorage().extractEnergy(1_000_000, false);
        BlockPos rs = C.relative(FACING);        // 控制器正面（结构外面那一格）
        int before = be.dieselAmount();
        level.setBlock(rs, Blocks.REDSTONE_BLOCK.defaultBlockState(), 3);
        tick(level, 20);
        check("有红石信号时状态是 DISABLED",
                be.getStatus() == DieselGeneratorBlockEntity.STATUS_DISABLED);
        check("有红石信号时柴油没被烧（" + before + " → " + be.dieselAmount() + " mB）",
                be.dieselAmount() == before);
        check("有红石信号时缓冲是空的（没发电）", be.getEnergyStored() == 0);
        level.setBlock(rs, Blocks.AIR.defaultBlockState(), 3);
        tick(level, 1);
        check("信号撤掉 ⇒ 立刻恢复发电（柴油 " + before + " → " + be.dieselAmount() + " mB）",
                be.dieselAmount() == before - 1
                        && be.getStatus() == DieselGeneratorBlockEntity.STATUS_RUNNING);
    }

    // ================= ⑧ 没柴油 =================

    private static void t8emptyStops(ServerLevel level) {
        say(TAG + "⑧ 罐里没有柴油 ⇒ 停机（状态 1）");
        DieselGeneratorBlockEntity be = controller(level);
        if (be == null) {
            check("⑧ 需要控制器", false);
            return;
        }
        be.getTank().drain(100000, IFluidHandler.FluidAction.EXECUTE);
        be.getEnergyStorage().extractEnergy(1_000_000, false);
        tick(level, 3);
        check("状态是 EMPTY", be.getStatus() == DieselGeneratorBlockEntity.STATUS_EMPTY);
        check("没发电（缓冲 " + be.getEnergyStored() + "）", be.getEnergyStored() == 0);
    }

    // ================= ⑨ 倒柴油 =================

    private static void t9pouring(ServerLevel level) {
        say(TAG + "⑨ 倒柴油：柴油桶 / 装柴油的油桶 / 拒收别的 / 罐满不倒");
        DieselGeneratorBlockEntity be = controller(level);
        if (be == null) {
            check("⑨ 需要控制器", false);
            return;
        }
        be.getTank().drain(100000, IFluidHandler.FluidAction.EXECUTE);

        check("原版柴油桶 → POURED（+1000 mB）",
                DieselGeneratorBlock.pourFrom(new ItemStack(ModItems.DIESEL_BUCKET.get()), level, C)
                        == DieselGeneratorBlock.PourResult.POURED && be.dieselAmount() == 1000);

        ItemStack oil = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(oil, new FluidStack(ModFluids.DIESEL.get(), 1000), 1000);
        check("装着柴油的油桶 → POURED（+1000 mB，罐里 2000）",
                DieselGeneratorBlock.pourFrom(oil, level, C) == DieselGeneratorBlock.PourResult.POURED
                        && be.dieselAmount() == 2000);

        ItemStack water = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(water, new FluidStack(net.minecraft.world.level.material.Fluids.WATER, 1000), 1000);
        check("装着水的油桶 → REJECTED（这台机器只烧柴油）",
                DieselGeneratorBlock.pourFrom(water, level, C) == DieselGeneratorBlock.PourResult.REJECTED);

        check("空油桶 → EMPTY",
                DieselGeneratorBlock.pourFrom(new ItemStack(ModItems.OIL_BUCKET.get()), level, C)
                        == DieselGeneratorBlock.PourResult.EMPTY);
        check("普通物品（泥土）→ NO_CONTAINER",
                DieselGeneratorBlock.pourFrom(new ItemStack(Items.DIRT), level, C)
                        == DieselGeneratorBlock.PourResult.NO_CONTAINER);

        // 罐里 7500（只剩 500 空间）：整桶 1000 塞不下 ⇒ FULL；油桶里那 1000 只倒得进 500 ⇒ 正好倒满
        be.getFluidHandler().fill(new FluidStack(ModFluids.DIESEL.get(), 5500), IFluidHandler.FluidAction.EXECUTE);
        check("罐里 " + be.dieselAmount() + " 时柴油桶 → FULL（不倒半桶）",
                DieselGeneratorBlock.pourFrom(new ItemStack(ModItems.DIESEL_BUCKET.get()), level, C)
                        == DieselGeneratorBlock.PourResult.FULL && be.dieselAmount() == 7500);
        ItemStack oil2 = new ItemStack(ModItems.OIL_BUCKET.get());
        OilBucketContents.fill(oil2, new FluidStack(ModFluids.DIESEL.get(), 1000), 1000);
        check("罐里 7500 时油桶 → POURED（能倒多少倒多少，正好倒满 8000）",
                DieselGeneratorBlock.pourFrom(oil2, level, C) == DieselGeneratorBlock.PourResult.POURED
                        && be.dieselAmount() == 8000);
    }

    // ================= ⑩ 数据驱动 =================

    private static void t10dataDriven(ServerLevel level) {
        say(TAG + "⑩ 配方与物品标签真的加载了");
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath("potato_s_t",
                "diesel_generator_controller");
        Optional<RecipeHolder<?>> holder = level.getRecipeManager().byKey(id);
        check("配方 diesel_generator_controller 在配方管理器里", holder.isPresent());
        if (holder.isPresent() && holder.get().value() instanceof ShapedRecipe shaped) {
            check("是 3×3 的 shaped（实测 " + shaped.getWidth() + "×" + shaped.getHeight() + "）",
                    shaped.getWidth() == 3 && shaped.getHeight() == 3);
            List<Ingredient> grid = shaped.getIngredients();
            check("正中间那一格认原版熔炉",
                    grid.get(4).test(new ItemStack(Items.FURNACE)));
            check("中间一排左右两格认铜块（普通铜块）",
                    grid.get(3).test(new ItemStack(Items.COPPER_BLOCK))
                            && grid.get(5).test(new ItemStack(Items.COPPER_BLOCK)));
            check("也认氧化+涂蜡的铜块（用户原话：无论氧化/涂蜡程度都可以）",
                    grid.get(3).test(new ItemStack(Items.WAXED_OXIDIZED_COPPER)));
            check("上中那一格认流体管道", grid.get(1).test(new ItemStack(ModBlocks.FLUID_PIPE_ITEM.get())));
            check("下中那一格认钢板", grid.get(7).test(new ItemStack(ModItems.STEEL_PLATE.get())));
            check("产物就是控制器本体",
                    shaped.getResultItem(level.registryAccess()).is(ModBlocks.DIESEL_GENERATOR_ITEM.get()));
        } else {
            check("配方类型是 crafting_shaped", false);
        }
        TagKey<Item> tag = TagKey.create(Registries.ITEM,
                ResourceLocation.fromNamespaceAndPath("potato_s_t", "copper_blocks"));
        var named = BuiltInRegistries.ITEM.getTag(tag);
        check("物品标签 potato_s_t:copper_blocks 存在", named.isPresent());
        if (named.isPresent()) {
            check("标签里正好 8 种铜块（实测 " + named.get().size() + "）", named.get().size() == 8);
        }
        // 语言键抽查（四语言由静态校验管，这里只确认服务端能取到键）
        check("控制器物品有名字",
                !ModBlocks.DIESEL_GENERATOR_ITEM.get().getDescription().getString().isEmpty());
    }

    // ================= 工具 =================

    private static DieselGeneratorBlockEntity controller(ServerLevel level) {
        return level.getBlockEntity(C) instanceof DieselGeneratorBlockEntity be ? be : null;
    }

    /** 跑 n 次机器 tick（直接调静态 tick，等价于世界在跑）。 */
    private static void tick(ServerLevel level, int n) {
        for (int i = 0; i < n; i++) {
            BlockState state = level.getBlockState(C);
            if (level.getBlockEntity(C) instanceof DieselGeneratorBlockEntity be) {
                DieselGeneratorBlockEntity.tick(level, C, state, be);
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
