package com.potatost.mod;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF65 临时文件，验证完必须删）</b>：验用户实测报的那个 bug ——
 * <b>「冶炼中的合金炉被破坏，循环电机声还在响，重新建一台才好」</b>。
 *
 * <p><b>根因（读代码定的，本探针就是把它钉死）</b>：挖掉外壳任意一格（或挖接线口）走的是
 * {@code AlloySmelterPartBlock.onRemove → master.disassemble(pos) → setFormed(false)}，
 * 而控制器方块本身<b>还在</b>。ZF64 那版把 {@code running} 的清零写在 {@code craftTick()} 里，
 * 拆解完之后 {@code formed == false} ⇒ 每 tick 都走不到 {@code craftTick()} ⇒
 * {@code running} <b>永远停在 true</b>；客户端每 tick 收到"在烧" ⇒ 循环音一直响，直到重新建一台。</p>
 *
 * <p>要验的四件事：</p>
 * <ol>
 *   <li><b>正在烧的机器</b>（基线）：{@code running} 必须为真，而且连走 5 个 tick <b>保持为真</b>
 *       —— 防这次修过头，把工作中的机器也静音；</li>
 *   <li><b>挖掉一格部件格</b>（真实 {@code destroyBlock}，走真的 onRemove）⇒ <b>1 个 tick 内</b>
 *       {@code running} 变假，且更新包里也是 false（那是客户端唯一能看到的途径）；</li>
 *   <li><b>直接 {@code disassemble()}（扳手那一支）</b> ⇒ 同上；</li>
 *   <li>参数没被动过（600 tick / 800 FE/t / 储能 32768）。</li>
 * </ol>
 */
public final class AlloySoundStopCheck {

    private static final String TAG = "[SND2] ";
    private static final Direction FACING = Direction.SOUTH;
    private static final BlockPos C = new BlockPos(400, 260, 200);
    private static boolean registered;

    private AlloySoundStopCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloySoundStopCheck.class);
            System.out.println(TAG + "hook registered");
        } catch (Throwable t) {
            System.out.println(TAG + "register failed: " + t);
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        int failed = 0;
        try {
            failed = run(event);
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

    private static int run(ServerStartedEvent event) {
        int failed = 0;
        ServerLevel level = event.getServer().overworld();
        var registries = event.getServer().registryAccess();

        // ---------- ① 基线：真在烧的机器不许被静音 ----------
        System.out.println(TAG + "(1) a machine that is really smelting must stay 'running'");
        AlloySmelterBlockEntity be = buildRunning(level);
        failed += check("machine formed", be.isFormed());
        failed += check("baseline: 'running' is true right after a crafted tick", be.isRunning());
        for (int i = 0; i < 5; i++) {
            fill(be, 800L);
            AlloySmelterBlockEntity.tick(level, C, level.getBlockState(C), be);
        }
        failed += check("still smelting after 5 real ticks: 'running' is STILL true (got " + be.isRunning() + ")",
                be.isRunning());
        failed += check("...and the update tag says true as well (client keeps the loop)",
                be.getUpdateTag(registries).getBoolean("running"));

        // ---------- ② 挖掉一格部件格（真实 onRemove 那条路）----------
        System.out.println(TAG + "(2) mining one hull cell (the path the user hit)");
        BlockPos part = findPart(level);
        failed += check("found a hull part cell" + (part == null ? "" : " at " + part), part != null);
        if (part != null) {
            boolean destroyed = level.destroyBlock(part, false);
            failed += check("destroyBlock(hull cell) returned true", destroyed);
            failed += check("that cell is now air", level.getBlockState(part).isAir());
        }
        failed += check("machine is no longer formed", !be.isFormed());
        AlloySmelterBlockEntity.tick(level, C, level.getBlockState(C), be);      // 真实 ticker 走一 tick
        failed += check("**ONE tick later 'running' is false** (got " + be.isRunning()
                + ") -- this is the bug the user reported", !be.isRunning());
        CompoundTag tag = be.getUpdateTag(registries);
        failed += check("update tag carries running=false => the client stops the loop",
                tag.contains("running") && !tag.getBoolean("running"));

        // ---------- ③ 直接 disassemble()（扳手那一支：满还原）----------
        System.out.println(TAG + "(3) full disassemble() (the wrench path)");
        AlloySmelterBlockEntity be2 = buildRunning(level);
        failed += check("second machine formed and running", be2.isFormed() && be2.isRunning());
        be2.disassemble();
        failed += check("after disassemble(): no longer formed", !be2.isFormed());
        AlloySmelterBlockEntity.tick(level, C, level.getBlockState(C), be2);
        failed += check("**ONE tick later 'running' is false** (got " + be2.isRunning() + ")", !be2.isRunning());
        failed += check("...and the update tag says false as well",
                !be2.getUpdateTag(registries).getBoolean("running"));

        // ---------- ④ 参数没被动过（用户给的数，字面量）----------
        System.out.println(TAG + "(4) numbers untouched");
        failed += check("600 ticks (30 s)", AlloySmelterBlockEntity.DURATION_TICKS == 600);
        failed += check("800 FE/t", AlloySmelterBlockEntity.ENERGY_PER_TICK == 800);
        failed += check("buffer 32768 FE", AlloySmelterBlockEntity.MAX_ENERGY == 32768);
        failed += check("sound event still registered",
                BuiltInRegistries.SOUND_EVENT.containsKey(
                        net.minecraft.resources.ResourceLocation.fromNamespaceAndPath(
                                PotatoST.MODID, "alloy_smelter_running")));

        clear(level);
        return failed;
    }

    // ==================== 工具 ====================
    /** 造一台成型 + 正在烧的机器（三种锭各 1 + 满电），并让它真的走一个 tick。 */
    private static AlloySmelterBlockEntity buildRunning(ServerLevel level) {
        clear(level);
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            buildLayer(level, y);
        }
        AlloySmelterBlock.tryAutoForm(level, C);
        if (!(level.getBlockEntity(C) instanceof AlloySmelterBlockEntity be)) {
            throw new IllegalStateException("controller block entity missing at " + C);
        }
        int in = AlloySmelterBlockEntity.INPUT_FIRST;
        be.getInventory().setStackInSlot(in, new ItemStack(ModItems.ALUMINUM_INGOT.get(), 4));
        be.getInventory().setStackInSlot(in + 1, new ItemStack(ModItems.TITANIUM_INGOT.get(), 4));
        be.getInventory().setStackInSlot(in + 2, new ItemStack(ModItems.SILVER_INGOT.get(), 4));
        fill(be, 40_000L);
        AlloySmelterBlockEntity.tick(level, C, level.getBlockState(C), be);
        return be;
    }

    /** 表面那 68 格里随便找一格"部件格"（不碰控制器、不碰接线口）。 */
    private static BlockPos findPart(ServerLevel level) {
        for (int y = 0; y < AlloySmelterStructure.HEIGHT; y++) {
            for (int j = 0; j < AlloySmelterStructure.DEPTH; j++) {
                for (int i = 0; i < AlloySmelterStructure.WIDTH; i++) {
                    if (!AlloySmelterStructure.isHull(y, j, i)) {
                        continue;
                    }
                    BlockPos p = AlloySmelterStructure.offset(C, FACING, y, j, i);
                    if (level.getBlockState(p).is(ModBlocks.ALLOY_SMELTER_PART.get())) {
                        return p;
                    }
                }
            }
        }
        return null;
    }

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
                BlockState st = kind == AlloySmelterStructure.Kind.CONTROLLER
                        ? ModBlocks.ALLOY_SMELTER.get().defaultBlockState()
                                .setValue(AlloySmelterBlock.FACING, FACING)
                        : AlloySmelterStructure.blockFor(kind).defaultBlockState();
                level.setBlock(AlloySmelterStructure.offset(C, FACING, y, j, i), st, 3);
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
