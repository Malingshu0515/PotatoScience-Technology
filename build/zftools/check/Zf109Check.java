package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChainBlock;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.energy.IEnergyStorage;

/**
 * ⚠⚠ <b>诊断工具（ZF109 的临时探针）</b>：采油机（0.11 新机器）。
 *
 * <p>用户原话：「海洋油田可以利用起来了 加一个采油机（配方；【硬质钛合金】【耐热金属块】【硬质钛合金】，
 * 【油桶】【高压气罐】【油桶】，【流体泵】【流体泵】【流体泵】） 在海洋油田群系工作
 * gui为一个大罐子25B储量 … 下方必须有水源方块 检测下方连接的 含水锁链的数量
 * 耗能公式为 80n*1/10n+80n FE/t 原油获取为 10n mb/s （n为下方含水锁链个数）
 * 每开采25~80桶原油 附近10*10的海洋油桶群系会变成符合旁边群系的海洋（冻洋 暖洋 温带海洋...）」。</p>
 *
 * <p>十段，缺一不可（真游戏里跑，不是静态检查）：</p>
 * <ol>
 *   <li><b>公式</b>：8n²+80n 与 10n 的取值表（用户拍板的 B 读法）；</li>
 *   <li><b>注册账目</b>：方块 / 方块实体 / 菜单 / <b>两个能力</b>（收 FE、只出不进的流体口）
 *       真的挂上了（能力是在 {@code PotatoST#registerCapabilities} 里注册的，静态检查看不出来）；</li>
 *   <li><b>群系门禁</b>：脚下不是海洋油田 ⇒ 15 号状态；写回油田 ⇒ 换状态；</li>
 *   <li><b>下探计数</b>：3 根含水锁链 = 3；干链子 / 石头 / 空气都要当场断；70 根要夹到 64；</li>
 *   <li><b>耗电与产油</b>：n=3 跑 20 tick 要正好 6240 FE、30 mB；n=1 跑 20 tick 要 1760 FE、10 mB；</li>
 *   <li><b>罐满 / 流体口</b>：25B 装满后停机且不再扣电；{@code fill} 恒 0、{@code drain} 拿得到油；</li>
 *   <li><b>红石</b>：旁边放红石块 ⇒ 0 号状态；</li>
 *   <li><b>存档往返</b>：save → 新造一个同类型方块实体 → load，字段要一模一样（§4.49 那个子标签坑）；</li>
 *   <li><b>抽干油田</b>：10×10 区块（chunks+skipped 必须 = 100）、格子数 &gt; 0、目标在
 *       {@code #minecraft:is_ocean} 里、机器脚下不再是油田、区块被标脏、<b>下一 tick 立刻停机</b>；</li>
 *   <li><b>投票</b>：把区域外一圈写成暖洋 ⇒ 目标必须是暖洋（不是"随便挑一个海"）。</li>
 * </ol>
 *
 * <p><b>⚠ 夹具说明（如实交代）</b>：测试世界的出生点不在海洋油田群系里，所以第 ③ 段起
 * 我<b>自己把测试区块的群系写进去</b>当夹具（用的是探针里内联的
 * {@code ChunkAccess#fillBiomesFromNoise}，与 {@link OilfieldDepletion} 同一套原版 API，
 * 但<b>不是同一个方法</b>）。"写进去读得回来"这一条本身就是要验证的事
 * —— 写用的是 {@code fillBiomesFromNoise}、读用的是 {@code Level#getBiome}（合成查找），
 * 两条路不同源。第 ⑨ 段才是真正调用被验对象 {@link OilfieldDepletion#convertAround}。</p>
 *
 * <p>挂载方式：`PotatoST` 构造器末尾加一行 `Zf109Check.register();`，
 * 跑完用 `_zf109_unprobe.py` 摘掉，并逐字节核对 `PotatoST.java` 回到改前件。</p>
 */
public final class Zf109Check {

    private static final String TAG = "[A109] ";
    /** {@code #minecraft:is_ocean}（与 OilfieldDepletion 里那个私有常量同一个标签） */
    private static final TagKey<Biome> OCEAN_TAG = TagKey.create(Registries.BIOME,
            ResourceLocation.withDefaultNamespace("is_ocean"));

    /** §4.50：runServer 的日志会把中文按 GBK 打乱 ⇒ 自己攒一份 UTF-8 报告，路径必须绝对。 */
    private static final StringBuilder REPORT = new StringBuilder();
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf109_probe_utf8.txt";

    private static boolean registered;
    private static int failed;
    private static int passed;

    private Zf109Check() {
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

    private static void checkEq(String name, long want, long got) {
        check(name + "（期望 " + want + "，实际 " + got + "）", want == got);
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), java.nio.charset.StandardCharsets.UTF_8)) {
            w.write("ZF109 探针报告（采油机：公式 / 能力 / 结构 / 产油 / 抽干油田）· UTF-8 · §4.50\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf109Check.class);
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
            testFormulas();
            testRegistry();
            testInWorld(event.getServer().overworld());
        } catch (Throwable t) {
            say(TAG + "exception: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            for (String line : sw.toString().split("\n")) {
                say(TAG + "    " + line);
            }
            failed++;
        } finally {
            say(TAG + "verdict: " + (failed == 0 ? "ALL OK" : "**" + failed + " FAILED**")
                    + " (passed " + passed + ")");
            say(TAG + "done, halting server");
            flushReport();
            event.getServer().halt(false);
        }
    }

    // ============================================================
    //  ① 公式
    // ============================================================
    private static void testFormulas() {
        say(TAG + "① formulas: 8n²+80n FE/t, 10n mB/s (user picked reading B)");
        checkEq("fePerTick(0)", 0, OilPumpBlockEntity.fePerTick(0));
        checkEq("fePerTick(1)", 88, OilPumpBlockEntity.fePerTick(1));
        checkEq("fePerTick(2)", 192, OilPumpBlockEntity.fePerTick(2));
        checkEq("fePerTick(3)", 312, OilPumpBlockEntity.fePerTick(3));
        checkEq("fePerTick(10)", 1600, OilPumpBlockEntity.fePerTick(10));
        checkEq("fePerTick(64)", 37888, OilPumpBlockEntity.fePerTick(64));
        checkEq("mbPerSecond(1)", 10, OilPumpBlockEntity.mbPerSecond(1));
        checkEq("mbPerSecond(10)", 100, OilPumpBlockEntity.mbPerSecond(10));
        checkEq("罐容 25B", 25000, OilPumpBlockEntity.TANK_CAPACITY);
        checkEq("欠账下限 25 桶", 25, OilPumpBlockEntity.DEBT_MIN_BUCKETS);
        checkEq("欠账上限 80 桶", 80, OilPumpBlockEntity.DEBT_MAX_BUCKETS);
        checkEq("转换范围 10 区块", 10, OilPumpBlockEntity.CONVERT_CHUNKS);
        checkEq("下探上限 64 格", 64, OilPumpBlockEntity.MAX_CHAIN_SCAN);
    }

    // ============================================================
    //  ② 注册账目（方块 / 方块实体 / 菜单 / 能力）
    // ============================================================
    private static void testRegistry() {
        say(TAG + "② registry: block / block entity / menu / capabilities");
        check("方块注册名 = oil_pump",
                ModBlocks.OIL_PUMP.getId().toString().equals("potato_s_t:oil_pump"));
        check("方块实体注册名 = oil_pump",
                ModBlocks.OIL_PUMP_BE.getId().toString().equals("potato_s_t:oil_pump"));
        check("菜单注册名 = oil_pump",
                ModMenus.OIL_PUMP_MENU.getId().toString().equals("potato_s_t:oil_pump"));
        check("物品注册名 = oil_pump",
                ModBlocks.OIL_PUMP_ITEM.getId().toString().equals("potato_s_t:oil_pump"));
        check("IdMapper 里查得到这个方块",
                net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(
                        ResourceLocation.fromNamespaceAndPath("potato_s_t", "oil_pump")) != Blocks.AIR);
        check("物品栏里是一个 BlockItem",
                ModBlocks.OIL_PUMP_ITEM.get() instanceof net.minecraft.world.item.BlockItem);
    }

    // ============================================================
    //  ③~⑩ 真世界
    // ============================================================
    private static void testInWorld(ServerLevel level) {
        BlockPos spawn = level.getSharedSpawnPos();
        // 放在出生点所在区块的**正中间**（x/z 都离区块边界 8 格 ⇒ Level#getBiome 的合成查找
        // 一定落回同一个区块，不会被邻居的群系搅进来）
        ChunkPos cpos = new ChunkPos(spawn);
        BlockPos pos = new BlockPos(cpos.getMinBlockX() + 8, 200, cpos.getMinBlockZ() + 8);
        say(TAG + "③ test site: " + pos + " (chunk " + cpos + ", biome "
                + level.getBiome(pos).unwrapKey().map(Object::toString).orElse("?") + ")");

        List<BlockPos> touched = new ArrayList<>();
        Holder<Biome> plains = level.registryAccess().lookupOrThrow(Registries.BIOME)
                .getOrThrow(Biomes.PLAINS);
        Holder<Biome> oilfield = level.registryAccess().lookupOrThrow(Registries.BIOME)
                .getOrThrow(SaltyRiverBiomeSource.OCEAN_OILFIELD);
        Holder<Biome> warm = level.registryAccess().lookupOrThrow(Registries.BIOME)
                .getOrThrow(Biomes.WARM_OCEAN);

        try {
            // ---- 夹具 0：脚下先写成"平原"，保证后面 15 号状态是确定的 ----
            check("把测试区块写成平原（夹具）", setChunkBiome(level, cpos.x, cpos.z, plains));
            check("写进去读得回来（平原）", level.getBiome(pos).is(Biomes.PLAINS));

            level.setBlock(pos, ModBlocks.OIL_PUMP.get().defaultBlockState(), 3);
            if (!(level.getBlockEntity(pos) instanceof OilPumpBlockEntity pump)) {
                check("放下方块后拿到 OilPumpBlockEntity", false);
                return;
            }
            check("放下方块后拿到 OilPumpBlockEntity", true);

            // ---- ② 能力（这一条只有真游戏能回答） ----
            IEnergyStorage energy = level.getCapability(Capabilities.EnergyStorage.BLOCK, pos, null);
            IFluidHandler fluid = level.getCapability(Capabilities.FluidHandler.BLOCK, pos, null);
            check("六面收得到 FE 能力", energy != null);
            check("六面收得到流体能力", fluid != null);
            check("没有物品能力（这台机器没有槽位）",
                    level.getCapability(Capabilities.ItemHandler.BLOCK, pos, null) == null);

            // ---- ③ 群系门禁 ----
            tick(level, pos, pump);
            checkEq("不在海洋油田 ⇒ 状态 15", OilPumpBlockEntity.STATUS_NOT_OILFIELD, pump.getStatus());
            check("把测试区块写成海洋油田（夹具）", setChunkBiome(level, cpos.x, cpos.z, oilfield));
            check("写进去读得回来（海洋油田）", level.getBiome(pos).is(SaltyRiverBiomeSource.OCEAN_OILFIELD));
            tick(level, pos, pump);
            checkEq("在海洋油田但下方没链条 ⇒ 状态 16", OilPumpBlockEntity.STATUS_NO_CHAIN, pump.getStatus());

            // ---- ④ 下探计数 ----
            say(TAG + "④ chain scan");
            for (int i = 1; i <= 3; i++) {
                touched.add(pos.below(i));
                level.setBlock(pos.below(i), Blocks.CHAIN.defaultBlockState()
                        .setValue(ChainBlock.WATERLOGGED, true), 3);
            }
            touched.add(pos.below(4));
            level.setBlock(pos.below(4), Blocks.WATER.defaultBlockState(), 3);
            checkEq("3 根含水锁链 ⇒ n = 3", 3, pump.rescanNow());

            touched.add(pos.below(3));
            level.setBlock(pos.below(3), Blocks.CHAIN.defaultBlockState()
                    .setValue(ChainBlock.WATERLOGGED, false), 3);
            checkEq("第 3 根变成干链子 ⇒ 只数到 2", 2, pump.rescanNow());
            level.setBlock(pos.below(3), Blocks.CHAIN.defaultBlockState()
                    .setValue(ChainBlock.WATERLOGGED, true), 3);

            touched.add(pos.below(4));
            level.setBlock(pos.below(4), Blocks.STONE.defaultBlockState(), 3);
            checkEq("链条**下面**垫石头 ⇒ n 仍是 3（下探只是到此为止）", 3, pump.rescanNow());

            touched.add(pos.below(2));
            level.setBlock(pos.below(2), Blocks.STONE.defaultBlockState(), 3);
            checkEq("石头**夹在中间**（第 2 格）⇒ 只数得到 1 根", 1, pump.rescanNow());

            level.setBlock(pos.below(2), Blocks.CHAIN.defaultBlockState()
                    .setValue(ChainBlock.WATERLOGGED, true), 3);
            level.setBlock(pos.below(4), Blocks.WATER.defaultBlockState(), 3);
            checkEq("石头拿掉 ⇒ n 回到 3", 3, pump.rescanNow());

            // 70 根要夹到 64（顺带证明 MAX_CHAIN_SCAN 真在管）
            for (int i = 1; i <= 70; i++) {
                touched.add(pos.below(i));
                level.setBlock(pos.below(i), Blocks.CHAIN.defaultBlockState()
                        .setValue(ChainBlock.WATERLOGGED, true), 3);
            }
            checkEq("70 根含水锁链 ⇒ 夹到 64", OilPumpBlockEntity.MAX_CHAIN_SCAN, pump.rescanNow());
            // 收回到 3 根
            for (int i = 4; i <= 70; i++) {
                level.setBlock(pos.below(i), Blocks.AIR.defaultBlockState(), 3);
                touched.remove(pos.below(i));
            }
            checkEq("收回成 3 根 ⇒ 回到 3", 3, pump.rescanNow());

            // ---- ⑤ 耗电与产油 ----
            say(TAG + "⑤ energy & oil: n=3 for 20 ticks");
            checkEq("储能被夹到上限", OilPumpBlockEntity.MAX_ENERGY,
                    energy == null ? -1 : energy.receiveEnergy(1000000, false));
            int e0 = pump.getEnergy();
            for (int i = 0; i < 20; i++) {
                tick(level, pos, pump);
            }
            checkEq("20 tick 后状态 = 运行中", OilPumpBlockEntity.STATUS_RUNNING, pump.getStatus());
            checkEq("20 tick 耗电 = 312×20", 6240, e0 - pump.getEnergy());
            checkEq("20 tick 产油 = 10n mB/s × 1 秒", 30, pump.getOil());
            checkEq("累计采出 = 30 mB", 30, pump.getPumpedMb());

            say(TAG + "⑤b energy & oil: n=1 for 20 ticks");
            for (int i = 2; i <= 3; i++) {
                level.setBlock(pos.below(i), Blocks.WATER.defaultBlockState(), 3);
            }
            checkEq("只留 1 根 ⇒ n = 1", 1, pump.rescanNow());
            int e1 = pump.getEnergy();
            int oil1 = pump.getOil();
            for (int i = 0; i < 20; i++) {
                tick(level, pos, pump);
            }
            checkEq("n=1 跑 20 tick 耗电 = 88×20", 1760, e1 - pump.getEnergy());
            checkEq("n=1 跑 20 tick 产油 = 10 mB", 10, pump.getOil() - oil1);

            // ---- ⑥ 罐满 / 流体口 ----
            say(TAG + "⑥ full tank & fluid handler");
            checkEq("流体口 fill 恒 0（只出不进）", 0,
                    fluid == null ? -1 : fluid.fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 1000),
                            IFluidHandler.FluidAction.EXECUTE));
            pump.getTank().fill(new FluidStack(ModFluids.CRUDE_OIL.get(), 25000),
                    IFluidHandler.FluidAction.EXECUTE);
            checkEq("罐里正好 25000 mB", 25000, pump.getOil());
            int e2 = pump.getEnergy();
            int o2 = pump.getOil();
            tick(level, pos, pump);
            checkEq("罐满 ⇒ 状态 4", OilPumpBlockEntity.STATUS_OUTPUT_FULL, pump.getStatus());
            checkEq("罐满时一滴不多产", o2, pump.getOil());
            checkEq("罐满时不扣电", e2, pump.getEnergy());
            FluidStack drained = fluid == null ? FluidStack.EMPTY
                    : fluid.drain(1000, IFluidHandler.FluidAction.EXECUTE);
            checkEq("流体口 drain 拿得到 1000 mB（是原油）", 1000, drained.getAmount());
            check("drain 出来的是原油",
                    !drained.isEmpty()
                            && drained.getFluid().getFluidType() == ModFluids.CRUDE_OIL_TYPE.get());

            // ---- ⑦ 红石 ----
            say(TAG + "⑦ redstone");
            touched.add(pos.east());
            level.setBlock(pos.east(), Blocks.REDSTONE_BLOCK.defaultBlockState(), 3);
            tick(level, pos, pump);
            checkEq("旁边有红石信号 ⇒ 状态 0", OilPumpBlockEntity.STATUS_DISABLED, pump.getStatus());
            level.setBlock(pos.east(), Blocks.AIR.defaultBlockState(), 3);
            touched.remove(pos.east());
            tick(level, pos, pump);
            check("红石拿掉后不再关机", pump.getStatus() != OilPumpBlockEntity.STATUS_DISABLED);

            // ---- ⑧ 存档往返 ----
            say(TAG + "⑧ save / load round trip");
            CompoundTag tag = pump.saveWithFullMetadata(level.registryAccess());
            OilPumpBlockEntity clone = new OilPumpBlockEntity(pos, pump.getBlockState());
            clone.loadWithComponents(tag, level.registryAccess());
            checkEq("往返后罐里的油", pump.getOil(), clone.getOil());
            checkEq("往返后电量", pump.getEnergy(), clone.getEnergy());
            checkEq("往返后累计采出", pump.getPumpedMb(), clone.getPumpedMb());
            checkEq("往返后欠账门槛", pump.getConvertAtMb(), clone.getConvertAtMb());
            check("往返后存的是原油",
                    !clone.getTank().getFluid().isEmpty()
                            && clone.getTank().getFluid().getFluidType() == ModFluids.CRUDE_OIL_TYPE.get());

            // ---- ⑨ 抽干油田 ----
            say(TAG + "⑨ deplete the oilfield: 10x10 chunks");
            check("把测试区块写回海洋油田（夹具）", setChunkBiome(level, cpos.x, cpos.z, oilfield));
            ChunkAccess chunk = level.getChunk(cpos.x, cpos.z, ChunkStatus.FULL, false);
            check("拿得到测试区块", chunk != null);
            int beforeCells = countOilfield(level, cpos.x, cpos.z);
            OilfieldDepletion.Result r = OilfieldDepletion.convertAround(level, pos,
                    OilPumpBlockEntity.CONVERT_CHUNKS);
            say(TAG + "    result: chunks=" + r.chunks() + " skipped=" + r.skipped()
                    + " cells=" + r.cells() + " target="
                    + (r.target() == null ? "null"
                       : r.target().unwrapKey().map(Object::toString).orElse("?")));
            checkEq("chunks + skipped = 100", 100, r.chunks() + r.skipped());
            check("改掉的格子数 > 0", r.cells() > 0);
            // 别的区块可能本来就带天然油田（油田是刷在海边的）⇒ 只要求"不少于夹具那一片"
            check("改掉的格子数 ≥ 夹具区块里的油田格子数（且 > 0）",
                    beforeCells > 0 && r.cells() >= beforeCells);            check("选中的目标在 #minecraft:is_ocean 里", r.target() != null && r.target().is(OCEAN_TAG));
            check("机器脚下不再是海洋油田", !level.getBiome(pos).is(SaltyRiverBiomeSource.OCEAN_OILFIELD));
            check("转换后的区块被标脏（否则不落盘）", chunk != null && chunk.isUnsaved());
            checkEq("转换后同一区块里一格油田都不剩", 0, countOilfield(level, cpos.x, cpos.z));
            tick(level, pos, pump);
            checkEq("抽完之后这台机器立刻停机（状态 15）",
                    OilPumpBlockEntity.STATUS_NOT_OILFIELD, pump.getStatus());

            // ---- ⑩ 投票 ----
            say(TAG + "⑩ neighbour vote");
            int span = 2;
            int minX = cpos.x - span / 2;
            int minZ = cpos.z - span / 2;
            int written = 0;
            int total = 0;
            for (int x = minX - 1; x <= minX + span; x++) {
                for (int z = minZ - 1; z <= minZ + span; z++) {
                    boolean inRegion = x >= minX && x < minX + span && z >= minZ && z < minZ + span;
                    if (inRegion) {
                        continue;
                    }
                    total++;
                    if (setChunkBiome(level, x, z, warm)) {
                        written++;
                    }
                }
            }
            say(TAG + "    ring chunks written = " + written + " / " + total);
            if (written >= 5) {
                Holder<Biome> voted = OilfieldDepletion.pickTargetOcean(level, minX, minZ, span, pos);
                check("区域外一圈都是暖洋 ⇒ 目标 = minecraft:warm_ocean",
                        voted.is(Biomes.WARM_OCEAN));
            } else {
                check("区域外一圈加载得太少（" + written + "/" + total
                        + "）⇒ 投票这一条没测成", false);
            }
        } finally {
            // 收尾：把碰过的方块清干净（测试世界也别留垃圾）
            for (BlockPos p : touched) {
                level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
            }
            level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    /** 夹具：把整个区块的群系写成同一个（内联的原版 API，与 OilfieldDepletion 不同源）。 */
    private static boolean setChunkBiome(ServerLevel level, int chunkX, int chunkZ, Holder<Biome> biome) {
        ChunkAccess chunk = level.getChunk(chunkX, chunkZ, ChunkStatus.FULL, false);
        if (chunk == null) {
            return false;
        }
        Climate.Sampler sampler = level.getChunkSource().randomState().sampler();
        chunk.fillBiomesFromNoise((qx, qy, qz, s) -> biome, sampler);
        chunk.setUnsaved(true);
        level.getChunkSource().chunkMap.resendBiomesForChunks(java.util.List.of(chunk));
        return true;
    }

    /** 数一个区块里还有多少"海洋油田"格子（quart 格）。 */
    private static int countOilfield(ServerLevel level, int chunkX, int chunkZ) {
        ChunkAccess chunk = level.getChunk(chunkX, chunkZ, ChunkStatus.FULL, false);
        if (chunk == null) {
            return -1;
        }
        int n = 0;
        int minY = level.getMinBuildHeight() >> 2;
        int maxY = level.getMaxBuildHeight() >> 2;
        for (int y = minY; y < maxY; y++) {
            for (int x = 0; x < 4; x++) {
                for (int z = 0; z < 4; z++) {
                    if (chunk.getNoiseBiome(x, y, z).is(SaltyRiverBiomeSource.OCEAN_OILFIELD)) {
                        n++;
                    }
                }
            }
        }
        return n;
    }

    private static void tick(ServerLevel level, BlockPos pos, OilPumpBlockEntity pump) {
        OilPumpBlockEntity.tick(level, pos, level.getBlockState(pos), pump);
    }
}
