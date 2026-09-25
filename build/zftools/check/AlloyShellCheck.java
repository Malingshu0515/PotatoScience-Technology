package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF55 临时探针）</b>：判定改成"围起来就能激活 + 自动激活"之后，逐条验它。
 *
 * <p>⚠ <b>本文件的来历</b>：ZF55 收尾时先把 src 里那份删了、忘了先抄一份到本目录，
 * 所以这是**事后按归档日志逐条重建的版本**（日志见 `build/zftools/_zf55_probe.txt`）。
 * 重建后重跑过一次，输出的 52 行与归档日志**逐字一致** ⇒ 行为等价，可以当原件用。
 * <b>下次的规矩：探针先抄进 `build/zftools/check/`，再从 src 删。</b></p>
 *
 * <p>要验的：</p>
 * <ol>
 *   <li><b>判定</b>：底面 + 三层墙（48 格）围满就成立、缺口会被点名、
 *       <b>内部塞金块不影响</b>、<b>顶面敲个洞也不影响</b>、外壳一个接线块都没有 ⇒ 不成立；</li>
 *   <li><b>随便搭也能成型</b>：80 格全用"一般金属块"（没有高炉/加热装置/漏斗/炼药锅/散热装置）
 *       ⇒ 照样成立（这是 ZF55 改判定的全部意义）；</li>
 *   <li><b>自动激活</b>：摆下控制器（onPlace）、补上控制器旁边的缺口（neighborChanged）、
 *       以及 tick 那条入口（tryAutoForm）—— 三条路都要能自己成型；</li>
 *   <li><b>成型账目</b>：只换"表面上的机器方块"，控制器不动、内部 12 格原样、空着的顶面不留隐形格；</li>
 *   <li><b>挖接线口 / 挖部件格</b>：掉回各自原来的方块、其余格全部还原（ZF54 遗留的
 *       "挖了接线口留下几十格隐形方块"必须不再复现）。掉落用 {@code EntityJoinLevelEvent}
 *       记账验证 —— 这个阶段（{@code ServerStartedEvent}）查不到刚 {@code addFreshEntity} 的实体，
 *       探针里的金丝雀实测 {@code addFreshEntity=true}、实体没被 discard，但查询数到 0 个；</li>
 *   <li><b>脏状态防护</b>：对着一台已经成型的机器再调一次 form()，原始方块<b>不能</b>被记成部件格
 *       （否则拆解会还出一片隐形方块）。</li>
 * </ol>
 */
public final class AlloyShellCheck {

    private static final String TAG = "[AS] ";
    private static final Direction FACING = Direction.SOUTH;
    private static boolean registered;

    /** 掉落账本：所有新进世界的物品实体都记一笔（光靠世界查询在这个阶段查不到，见类注释）。 */
    private static final java.util.List<String> DROP_LOG = new java.util.ArrayList<>();

    /** 5 个互不干扰的试验场（x 隔 24 格，结构只有 ±5 格）。 */
    private static final BlockPos A = new BlockPos(176, 260, 176);   // 纯判定（不放控制器）
    private static final BlockPos B = new BlockPos(200, 260, 176);   // 图纸 + 内部塞金块
    private static final BlockPos C = new BlockPos(224, 260, 176);   // 全用一般金属块 + 顶面漏风
    private static final BlockPos D = new BlockPos(248, 260, 176);   // 自动激活三条路
    private static final BlockPos E = new BlockPos(272, 260, 176);   // 脏状态 / 重复成型

    private AlloyShellCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloyShellCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onEntityJoin(net.neoforged.neoforge.event.entity.EntityJoinLevelEvent event) {
        if (event.getEntity() instanceof ItemEntity item) {
            DROP_LOG.add(item.getItem().getCount() + " x " + item.getItem().getItem().getDescriptionId()
                    + " @ " + item.blockPosition().toShortString());
        }
    }

    /** 账本里有没有"某物品掉在某一格"的记录。 */
    private static boolean droppedAt(BlockPos pos, String itemName) {
        String where = "@ " + pos.toShortString();
        for (String entry : DROP_LOG) {
            if (entry.endsWith(where) && entry.contains(itemName)) {
                return true;
            }
        }
        return false;
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        ServerLevel level = event.getServer().overworld();
        try {
            failed += judge(level);
            failed += blueprintWithGoldInside(level);
            failed += uniformShell(level);
            failed += autoActivate(level);
            failed += dirtyState(level);
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

    // ==================== ① 纯判定（这一区**不放控制器**，所以不会有自动激活来捣乱） ====================
    private static int judge(ServerLevel level) {
        System.out.println(TAG + "(1) rules: 48-cell body + wiring, holes named, inside & roof ignored");
        int failed = 0;
        clear(level, A);
        buildBlueprint(level, A, false);          // 控制器那一格留空气 ⇒ 没有任何方块实体
        // 没有控制器 ⇒ 那一格按图纸是控制器，先用一般金属块顶上（判定只看"是不是机器方块"）
        level.setBlock(offset(A, 1, 4, 0), ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);

        AlloySmelterStructure.Report r1 = AlloySmelterStructure.inspect(level, A, FACING, 16);
        failed += check("blueprint shell is ok (holes=" + r1.holeCount() + " wiring=" + r1.wiring() + ")",
                r1.ok() && r1.holeCount() == 0 && r1.wiring() == 2);

        // 挖掉一个底面角 ⇒ 正好一处缺口，而且坐标要报对
        level.setBlock(offset(A, 0, 0, 0), Blocks.AIR.defaultBlockState(), 3);
        AlloySmelterStructure.Report r2 = AlloySmelterStructure.inspect(level, A, FACING, 16);
        boolean named = r2.holeCount() == 1 && r2.holes().size() == 1
                && r2.holes().get(0).y() == 0 && r2.holes().get(0).j() == 0 && r2.holes().get(0).i() == 0
                && r2.holes().get(0).found() == Blocks.AIR;
        failed += check("one missing floor cell -> exactly 1 hole at (1,1,1) naming air (got "
                + r2.holeCount() + ")", named && !r2.ok());
        level.setBlock(offset(A, 0, 0, 0), ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);

        // 内部挖一格 ⇒ 判定必须**毫无反应**
        level.setBlock(offset(A, 1, 2, 1), Blocks.AIR.defaultBlockState(), 3);
        AlloySmelterStructure.Report r3 = AlloySmelterStructure.inspect(level, A, FACING, 16);
        failed += check("hole INSIDE the box is ignored (holes=" + r3.holeCount() + ")", r3.ok());

        // 顶面挖一格 ⇒ 也必须有反应（图纸的顶面本来就漏风）
        level.setBlock(offset(A, 3, 2, 2), Blocks.AIR.defaultBlockState(), 3);
        AlloySmelterStructure.Report r3b = AlloySmelterStructure.inspect(level, A, FACING, 16);
        failed += check("hole in the ROOF is ignored too (holes=" + r3b.holeCount() + ")",
                r3b.ok() && r3b.holeCount() == 0);

        // 两处接线块都换成一般金属块 ⇒ 外壳完好但没地方进电
        level.setBlock(offset(A, 1, 0, 0), ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
        level.setBlock(offset(A, 1, 0, 3), ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
        AlloySmelterStructure.Report r4 = AlloySmelterStructure.inspect(level, A, FACING, 16);
        failed += check("shell without any wiring block is NOT ok (wiring=" + r4.wiring() + ")",
                !r4.ok() && r4.holeCount() == 0 && r4.wiring() == 0);
        return failed;
    }

    // ==================== ② 图纸 + 内部塞金块 ⇒ 自动成型，内部不许被动 ====================
    private static int blueprintWithGoldInside(ServerLevel level) {
        System.out.println(TAG + "(2) blueprint + gold blocks inside: auto-form on placement, inside untouched");
        int failed = 0;
        clear(level, B);
        buildBlueprint(level, B, false);          // 控制器那一格先留空（否则一放就成型，测不到"内部"）
        for (int y = 1; y <= 2; y++) {
            for (int j = 1; j <= 3; j++) {
                for (int i = 1; i <= 2; i++) {
                    level.setBlock(offset(B, y, j, i), Blocks.GOLD_BLOCK.defaultBlockState(), 3);
                }
            }
        }
        AlloySmelterStructure.Report before = AlloySmelterStructure.inspect(level, B, FACING, 16);
        // 此时唯一该报的缺口就是"控制器那一格还空着"——里面那 12 块金块不算缺口
        failed += check("only the empty controller slot is a hole, gold inside is ignored (holes="
                        + before.holeCount() + ")",
                before.holeCount() == 1 && !before.holes().isEmpty()
                        && before.holes().get(0).j() == 4 && before.holes().get(0).i() == 0
                        && before.holes().get(0).found() == Blocks.AIR);

        // 控制器最后放 ⇒ onPlace 那条自动激活路径
        level.setBlock(B, controllerState(), 3);
        if (!(level.getBlockEntity(B) instanceof AlloySmelterBlockEntity be)) {
            return failed + check("controller block entity exists", false);
        }
        failed += check("auto-formed just by placing the controller (onPlace)", be.isFormed());
        if (!be.isFormed()) {
            be.form();                             // 万一 onPlace 没触发，后面几条也要能验
        }

        int parts = 0;
        int ports = 0;
        int gold = 0;
        int airRoof = 0;
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    if (!AlloySmelterStructure.isHull(y, j, i)) {
                        continue;
                    }
                    BlockState s = level.getBlockState(offset(B, y, j, i));
                    if (s.is(ModBlocks.ALLOY_SMELTER_PART.get())) {
                        parts++;
                    } else if (s.is(ModBlocks.ALLOY_SMELTER_PORT.get())) {
                        ports++;
                    } else if (s.isAir()) {
                        airRoof++;
                    }
                }
            }
        }
        for (int y = 1; y <= 2; y++) {
            for (int j = 1; j <= 3; j++) {
                for (int i = 1; i <= 2; i++) {
                    if (level.getBlockState(offset(B, y, j, i)).is(Blocks.GOLD_BLOCK)) {
                        gold++;
                    }
                }
            }
        }
        System.out.println(TAG + "  hull: part=" + parts + " port=" + ports + " leftAir=" + airRoof);
        // 表面 68 = 控制器 1 + 接线口 2 + 部件格 55 + 图纸本来就空着的顶面 10
        failed += check("55 part cells (got " + parts + ")", parts == 55);
        failed += check("2 port cells (got " + ports + ")", ports == 2);
        failed += check("the 10 empty roof cells stay air, no invisible part (got " + airRoof + ")",
                airRoof == 10);
        failed += check("the 12 inner cells are untouched gold (got " + gold + ")", gold == 12);
        failed += check("controller cell still the controller",
                level.getBlockState(B).is(ModBlocks.ALLOY_SMELTER.get()));
        failed += check("original of a floor cell is its blueprint block",
                be.originalAt(offset(B, 0, 0, 0)) != null
                        && be.originalAt(offset(B, 0, 0, 0)).is(ModBlocks.COMMON_METAL_BLOCK.get()));

        // 挖掉一个接线口：掉回接线块 + 其余格全部还原（ZF54 那个"留下隐形方块"的坑）
        BlockPos port = offset(B, 1, 0, 0);
        System.out.println(TAG + "  break the port " + port.toShortString()
                + " (block there = " + level.getBlockState(port).getBlock().getName().getString() + ")");
        level.destroyBlock(port, true);
        int leftover = 0;
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    BlockState s = level.getBlockState(offset(B, y, j, i));
                    if (s.is(ModBlocks.ALLOY_SMELTER_PART.get()) || s.is(ModBlocks.ALLOY_SMELTER_PORT.get())) {
                        leftover++;
                    }
                }
            }
        }
        failed += check("mined port cell is air", level.getBlockState(port).isAir());
        failed += check("no part/port cell left anywhere (leftover=" + leftover + ")", leftover == 0);
        failed += check("machine no longer formed", !be.isFormed());

        // 金丝雀：这个阶段"加实体能成、查实体查不到"，先把这条环境事实钉在日志里
        ItemEntity canary = new ItemEntity(level, port.getX() + 0.5, port.getY() + 0.5, port.getZ() + 0.5,
                new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.DIAMOND));
        boolean added = level.addFreshEntity(canary);
        int seen = level.getEntitiesOfClass(ItemEntity.class, new AABB(port).inflate(4.0)).size();
        System.out.println(TAG + "  canary: addFreshEntity=" + added + " alive=" + !canary.isRemoved()
                + " but getEntitiesOfClass=" + seen + "  <- fresh entities are invisible in this phase");
        failed += check("canary: the level DOES accept a fresh entity here", added && !canary.isRemoved());
        canary.discard();

        // ⚠ 掉落改用账本验（EntityJoinLevelEvent）——上面那条金丝雀说明了为什么不能查世界
        failed += check("the mined port dropped a WIRING BLOCK item (ledger)",
                droppedAt(port, "potato_s_t.wiring_block"));
        failed += check("no alloy_smelter_part item was dropped",
                DROP_LOG.stream().noneMatch(s -> s.contains("alloy_smelter_part")));

        // ---------- 对照组：补回接线口 → 再成型 → 挖一格普通部件格（应当掉回它原来的加热装置） ----------
        level.setBlock(port, ModBlocks.WIRING_BLOCK.get().defaultBlockState(), 3);
        AlloySmelterBlock.tryAutoForm(level, B);
        if (level.getBlockEntity(B) instanceof AlloySmelterBlockEntity be2 && !be2.isFormed()) {
            be2.form();
        }
        BlockPos victim = offset(B, 0, 2, 1);      // 图纸上是一台加热装置（成型后是部件格）
        System.out.println(TAG + "  control: break a plain part cell " + victim.toShortString()
                + " (block there = " + level.getBlockState(victim).getBlock().getName().getString() + ")");
        level.destroyBlock(victim, true);
        failed += check("control: mining a part cell drops its ORIGINAL block (Heater) (ledger)",
                droppedAt(victim, "potato_s_t.heater"));
        System.out.println(TAG + "  drop ledger (" + DROP_LOG.size() + "):");
        for (String entry : DROP_LOG) {
            System.out.println(TAG + "    " + entry);
        }
        return failed;
    }

    // ==================== ③ 全用一般金属块 + 顶面漏风（ZF55 的全部意义） ====================
    private static int uniformShell(ServerLevel level) {
        System.out.println(TAG + "(3) a shell made of nothing but common metal blocks, open roof");
        int failed = 0;
        clear(level, C);
        fillUniform(level, C, true);
        BlockPos roof = offset(C, 3, 2, 1);
        level.setBlock(roof, Blocks.AIR.defaultBlockState(), 3);        // 顶面敲个洞（图纸本来就没封顶）
        AlloySmelterStructure.Report report = AlloySmelterStructure.inspect(level, C, FACING, 16);
        failed += check("roof hole is not a hole at all (holes=" + report.holeCount()
                + " wiring=" + report.wiring() + ")", report.ok() && report.holeCount() == 0);
        level.setBlock(roof, ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);

        level.setBlock(C, controllerState(), 3);
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            return failed + check("controller block entity exists", false);
        }
        failed += check("plain metal shell auto-forms", be.isFormed());
        if (!be.isFormed()) {
            be.form();
        }
        int parts = 0;
        int metal = 0;
        int wiringLeft = 0;
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    BlockState s = level.getBlockState(offset(C, y, j, i));
                    if (AlloySmelterStructure.isHull(y, j, i)) {
                        if (s.is(ModBlocks.ALLOY_SMELTER_PART.get())) {
                            parts++;
                        } else if (s.is(ModBlocks.WIRING_BLOCK.get())) {
                            wiringLeft++;
                        }
                    } else if (s.is(ModBlocks.COMMON_METAL_BLOCK.get())) {
                        metal++;
                    }
                }
            }
        }
        failed += check("65 part cells (got " + parts + ")", parts == 65);
        failed += check("inner cells still plain metal, not touched (got " + metal + ")", metal == 12);
        failed += check("wiring cells became ports (wiring left=" + wiringLeft + ")", wiringLeft == 0);
        return failed;
    }

    // ==================== ④ 自动激活的三条路 ====================
    private static int autoActivate(ServerLevel level) {
        System.out.println(TAG + "(4) auto activation: onPlace / neighborChanged / tryAutoForm");
        int failed = 0;

        // 4a onPlace：外壳先围好，控制器最后摆下
        clear(level, D);
        fillUniform(level, D, true);
        level.setBlock(D, Blocks.AIR.defaultBlockState(), 3);       // 控制器那一格留空
        level.setBlock(D, controllerState(), 3);
        boolean a = level.getBlockEntity(D) instanceof AlloySmelterBlockEntity beA && beA.isFormed();
        failed += check("onPlace path: placing the controller into a finished shell forms it", a);

        // 4b neighborChanged：先在控制器旁边留个洞 ⇒ 摆下控制器不成型；补上那一格 ⇒ 立刻成型
        clear(level, D);
        fillUniform(level, D, true);
        level.setBlock(offset(D, 1, 4, 1), Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(D, controllerState(), 3);
        boolean before = level.getBlockEntity(D) instanceof AlloySmelterBlockEntity beB && beB.isFormed();
        failed += check("shell with a hole next to the controller does NOT form", !before);
        level.setBlock(offset(D, 1, 4, 1), ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
        boolean after = level.getBlockEntity(D) instanceof AlloySmelterBlockEntity beC && beC.isFormed();
        failed += check("patched the last neighbour cell -> formed at once (neighborChanged)", after);

        // 4c tick 那条入口：洞补在**离控制器很远**的角 ⇒ neighborChanged 不会响，只能靠 tryAutoForm
        clear(level, D);
        fillUniform(level, D, true);
        level.setBlock(offset(D, 2, 0, 1), Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(D, controllerState(), 3);
        boolean quiet = level.getBlockEntity(D) instanceof AlloySmelterBlockEntity beD && beD.isFormed();
        failed += check("far-away hole: nothing forms yet", !quiet);
        level.setBlock(offset(D, 2, 0, 1), ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState(), 3);
        boolean stillQuiet = level.getBlockEntity(D) instanceof AlloySmelterBlockEntity beE && beE.isFormed();
        failed += check("far-away patch does NOT notify the controller (still unformed)", !stillQuiet);
        AlloySmelterBlock.tryAutoForm(level, D);
        boolean ticked = level.getBlockEntity(D) instanceof AlloySmelterBlockEntity beF && beF.isFormed();
        failed += check("tryAutoForm (the tick path) forms it", ticked);

        // 4d 外壳围好了但一个接线块都没有 ⇒ 永远不成型
        clear(level, D);
        fillUniform(level, D, false);
        level.setBlock(D, controllerState(), 3);
        AlloySmelterBlock.tryAutoForm(level, D);
        boolean noWire = level.getBlockEntity(D) instanceof AlloySmelterBlockEntity beG && beG.isFormed();
        failed += check("no wiring block anywhere -> never forms", !noWire);
        return failed;
    }

    // ==================== ⑤ 脏状态：对着已成型的外壳再 form() 一次 ====================
    private static int dirtyState(ServerLevel level) {
        System.out.println(TAG + "(5) calling form() again over leftover part blocks must not record them");
        int failed = 0;
        clear(level, E);
        fillUniform(level, E, true);
        level.setBlock(E, controllerState(), 3);
        var raw = level.getBlockEntity(E);
        if (!(raw instanceof AlloySmelterBlockEntity be)) {
            return failed + check("controller block entity exists", false);
        }
        if (!be.isFormed()) {
            be.form();
        }
        BlockPos probe = offset(E, 2, 4, 2);      // 表面的一格（成型后是部件格）
        BlockState first = be.originalAt(probe);
        failed += check("first round recorded a plain metal block (got "
                        + (first == null ? "null" : first.getBlock().getName().getString()) + ")",
                first != null && first.is(ModBlocks.COMMON_METAL_BLOCK.get()));
        failed += check("that cell is a part block right now",
                level.getBlockState(probe).is(ModBlocks.ALLOY_SMELTER_PART.get()));

        be.form();                                // 再成型一次（表面整片都是部件格/接线口）
        BlockState second = be.originalAt(probe);
        failed += check("second round still records the metal block, NOT the part block (got "
                        + (second == null ? "null" : second.getBlock().getName().getString()) + ")",
                second != null && second.is(ModBlocks.COMMON_METAL_BLOCK.get()));

        be.disassemble();
        failed += check("after disassemble that cell is a plain metal block again (got "
                        + level.getBlockState(probe).getBlock().getName().getString() + ")",
                level.getBlockState(probe).is(ModBlocks.COMMON_METAL_BLOCK.get()));
        return failed;
    }

    // ==================== 工具 ====================
    private static BlockState controllerState() {
        return ModBlocks.ALLOY_SMELTER.get().defaultBlockState()
                .setValue(AlloySmelterBlock.FACING, FACING);
    }

    /** 80 格全填一般金属块；{@code withWiring} 时把图纸里那两格换成接线块（控制器那格留空）。 */
    private static void fillUniform(ServerLevel level, BlockPos c, boolean withWiring) {
        BlockState metal = ModBlocks.COMMON_METAL_BLOCK.get().defaultBlockState();
        for (BlockPos p : AlloySmelterStructure.positions(c, FACING)) {
            level.setBlock(p, metal, 3);
        }
        if (withWiring) {
            BlockState wire = ModBlocks.WIRING_BLOCK.get().defaultBlockState();
            level.setBlock(offset(c, 1, 0, 0), wire, 3);
            level.setBlock(offset(c, 1, 0, 3), wire, 3);
        }
    }

    /** 按图纸摆（{@code withController=false} 时控制器那一格留空气）。 */
    private static void buildBlueprint(ServerLevel level, BlockPos c, boolean withController) {
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    AlloySmelterStructure.Kind kind = AlloySmelterStructure.kindAt(y, j, i);
                    BlockState state;
                    if (kind == AlloySmelterStructure.Kind.CONTROLLER) {
                        state = withController ? controllerState() : Blocks.AIR.defaultBlockState();
                    } else {
                        state = AlloySmelterStructure.blockFor(kind).defaultBlockState();
                    }
                    level.setBlock(offset(c, y, j, i), state, 3);
                }
            }
        }
    }

    private static BlockPos offset(BlockPos c, int y, int j, int i) {
        return AlloySmelterStructure.offset(c, FACING, y, j, i);
    }

    private static void clear(ServerLevel level, BlockPos c) {
        // ⚠ 必须先干掉控制器：它一没，表面那些部件格的 onRemove 就找不到控制器，
        //   也不会一边拆一边把别的格"还原"回来（否则 clear 出来一片金属块，试验场不干净）
        level.setBlock(c, Blocks.AIR.defaultBlockState(), 3);
        for (BlockPos p : AlloySmelterStructure.positions(c, FACING)) {
            level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
        }
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
