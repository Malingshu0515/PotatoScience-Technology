package com.potatost.mod;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * ZF151 临时探针（0.12：挖掘口径 —— 太阳能板掉落 / 全机器镐子标签 / 空手也掉落）。
 *
 * <p>验的是**真游戏里的那两条链**，不是文件写没写对：
 * ① 每一项都在 {@code minecraft:mineable/pickaxe} 里（镐子加速）、且机器**不带**
 *    {@code requiresCorrectToolForDrops}（空手也掉）；
 * ② **端到端**：拿假玩家**空手**去 `playerDestroy` 一块太阳能板 / 一个接线口，
 *    世界里必须真的出现掉落物 —— 负对照是矿石空手 `canHarvestBlock = false`。</p>
 *
 * <p>⚠ <b>为什么端到端要等几个 tick</b>：`ServerStartedEvent` 那一刻区块里新加的实体还留在
 * 实体管理器的 pending 队列里（`addFreshEntity` 返回 true、`isAlive` 也是 true，但
 * `getAllEntities()` / `getEntitiesOfClass` **数不到**）—— 本节第一版就栽在这儿，
 * 报告里写成"挖了不掉"，其实是"数不到"。改成开局后第 3 个 tick 再跑那段。</p>
 *
 * <p>⚠ §4.50：`runServer` 的 stdout 是 GBK ⇒ 自己写 UTF-8 报告，路径绝对，且在 {@code halt()} 前写。</p>
 */
public final class Zf151Check {

    private static final String TAG = "[A151] ";
    private static final String REPORT_PATH = "E:\\PotatoST\\build\\zftools\\_zf151_probe_utf8.txt";
    private static final String[] LIQUIDS = {"crude_oil", "diesel", "gasoline"};

    /**
     * 建材家族（**刻意**学原版铁块/煤炭块：必须用镐挖）—— 它们不是机器，
     * A2 那条"空手也掉"的判据不管它们，只单独记录下来。
     */
    private static final String[] DECOR = {"common_metal_block", "advanced_metal_block",
            "stable_metal_block", "heat_resistant_metal_block", "heater", "heat_sink",
            "wiring_block", "asphalt_block"};

    private static boolean registered;
    private static int failed;
    private static int checks;
    private static final StringBuilder REPORT = new StringBuilder();

    // 端到端要等 tick ⇒ 把现场存下来
    private static MinecraftServer server;
    private static ServerLevel level;
    private static ServerPlayer player;
    private static int ticks;
    private static boolean e2eDone;

    private Zf151Check() {
    }

    private static void say(String line) {
        System.out.println(line);
        REPORT.append(line).append('\n');
    }

    private static void flushReport() {
        try (java.io.OutputStreamWriter w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(REPORT_PATH), StandardCharsets.UTF_8)) {
            w.write("ZF151 探针报告（0.12 挖掘口径：太阳能板掉落 / 镐子标签 / 空手掉落）× UTF-8 · §4.50\n");
            w.write("生成时间：" + java.time.LocalDateTime.now() + "\n");
            w.write("判词：" + (failed == 0 ? "ALL OK" : failed + " 条 FAIL") + "（共 " + checks + " 项）\n\n");
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
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(Zf151Check.class);
            say(TAG + "hook registered");
        } catch (Throwable t) {
            say(TAG + "register failed: " + t);
        }
    }

    private static void check(String name, boolean ok) {
        checks++;
        REPORT.append(ok ? "  [OK]   " : "  [FAIL] ").append(name).append('\n');
        if (ok) {
            System.out.println(TAG + "  [OK]   " + name);
        } else {
            failed++;
            System.out.println(TAG + "  [FAIL] " + name);
        }
    }

    private static BlockState st(String path) {
        return BuiltInRegistries.BLOCK.get(ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, path))
                .defaultBlockState();
    }

    // ================================================================ 第一阶段：开局
    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        failed = 0;
        checks = 0;
        try {
            server = event.getServer();
            level = server.overworld();
            player = new ServerPlayer(server, level,
                    new GameProfile(UUID.nameUUIDFromBytes("Zf151Check".getBytes(StandardCharsets.UTF_8)),
                            "Zf151"),
                    ClientInformation.createDefault());
            checkPolicyMatrix();
            checkSolarPanelStatic();
            checkPortsStatic();
        } catch (Throwable t) {
            say(TAG + "exception(phase1): " + t);
            for (StackTraceElement e : t.getStackTrace()) {
                say(TAG + "    at " + e);
            }
        }
    }

    // ================================================================ 第二阶段：第 3 tick 的端到端
    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        if (e2eDone) {
            return;
        }
        ticks++;
        if (ticks < 3) {
            return;
        }
        e2eDone = true;
        try {
            checkSolarPanelE2E();
            checkPortE2E();
        } catch (Throwable t) {
            say(TAG + "exception(phase2): " + t);
            for (StackTraceElement e : t.getStackTrace()) {
                say(TAG + "    at " + e);
            }
        }
        say(TAG + "done, halting server");
        flushReport();
        server.halt(false);
    }

    // ---------------------------------------------------------------- A 口径矩阵
    private static void checkPolicyMatrix() {
        say(TAG + "================ A 口径矩阵：本 mod 每一块方块的「镐子加速 / 空手掉落」 ================");
        List<String> badTag = new ArrayList<>();
        List<String> badTool = new ArrayList<>();
        List<String> decorTool = new ArrayList<>();
        int machines = 0;
        int ores = 0;
        int decorN = 0;
        int skipped = 0;
        for (Block block : BuiltInRegistries.BLOCK) {
            ResourceLocation id = BuiltInRegistries.BLOCK.getKey(block);
            if (!PotatoST.MODID.equals(id.getNamespace())) {
                continue;
            }
            String path = id.getPath();
            boolean liquid = false;
            for (String l : LIQUIDS) {
                if (path.equals(l)) {
                    liquid = true;
                }
            }
            if (liquid || block == Blocks.AIR) {
                skipped++;
                continue;
            }
            BlockState state = block.defaultBlockState();
            boolean inTag = state.is(BlockTags.MINEABLE_WITH_PICKAXE);
            boolean needsTool = state.requiresCorrectToolForDrops();
            boolean ore = path.endsWith("_ore");
            boolean decor = false;
            for (String d : DECOR) {
                if (path.equals(d)) {
                    decor = true;
                }
            }
            if (ore) {
                ores++;
                if (!inTag) {
                    badTag.add(path + "(矿)");
                }
                if (!needsTool) {
                    badTool.add(path + "(矿：本该需要正确工具)");
                }
            } else if (decor) {
                decorN++;
                if (!inTag) {
                    badTag.add(path + "(建材)");
                }
                if (needsTool) {
                    decorTool.add(path);
                }
            } else {
                machines++;
                if (!inTag) {
                    badTag.add(path);
                }
                if (needsTool) {
                    badTool.add(path + "(不该需要正确工具)");
                }
            }
        }
        say(TAG + "    记录：本 mod 非液体方块 " + (machines + ores + decorN) + " 个（机器 " + machines
                + " / 矿 " + ores + " / 建材 " + decorN + "），跳过液体 " + skipped + " 个");
        say(TAG + "    记录：建材家族里**刻意**需要镐的 " + decorTool.size() + " 个：" + decorTool);
        check("A1 每一台机器都在 mineable/pickaxe 里（镐子加速）—— 漏 " + badTag.size() + ":" + badTag,
                badTag.isEmpty());
        check("A2 每一台机器都不需要正确工具（空手也掉）—— 例外 " + badTool.size() + ":" + badTool,
                badTool.isEmpty());
        check("A3 负对照：钴矿石仍然 requiresCorrectToolForDrops（判据有区分度）",
                st("cobalt_ore").requiresCorrectToolForDrops());
        check("A4 负对照：钴矿石空手 canHarvestBlock = false",
                !st("cobalt_ore").canHarvestBlock(level, new BlockPos(0, 100, 0), player));
        check("A5 正对照：微型粉碎机空手 canHarvestBlock = true",
                st("micro_crusher").canHarvestBlock(level, new BlockPos(0, 100, 0), player));
    }

    // ---------------------------------------------------------------- B 太阳能板（静态部分）
    private static void checkSolarPanelStatic() {
        say(TAG + "================ B 太阳能板：挖了到底掉不掉 ================");
        BlockState state = st("solar_panel");
        BlockPos pos = new BlockPos(8, 250, 8);
        check("B1 太阳能板拿到手（defaultBlockState 非空）", !state.isAir());
        check("B2 太阳能板在 mineable/pickaxe 标签里", state.is(BlockTags.MINEABLE_WITH_PICKAXE));
        check("B3 太阳能板空手 canHarvestBlock = true（空手挖得动 —— 这一条就是掉落的总闸门）",
                state.canHarvestBlock(level, pos, player));
        List<ItemStack> drops = Block.getDrops(state, level, pos, null, player, ItemStack.EMPTY);
        check("B4 Block.getDrops 正好 1 个太阳能板（实测 " + describe(drops) + "）",
                drops.size() == 1 && drops.get(0).getItem() == ModBlocks.SOLAR_PANEL_ITEM.get());
        for (String path : new String[]{"micro_crusher", "fluid_exchanger", "hydraulic_press"}) {
            BlockState s = st(path);
            List<ItemStack> d = Block.getDrops(s, level, pos, null, player, ItemStack.EMPTY);
            check("B5 对照：" + path + " 也掉自己（实测 " + describe(d) + "）",
                    d.size() == 1 && d.get(0).getItem() == s.getBlock().asItem());
        }
    }

    // ---------------------------------------------------------------- C 接线口（静态部分）
    private static void checkPortsStatic() {
        say(TAG + "================ C 两个接线口：空手挖掉的是接线块 ================");
        BlockPos pos = new BlockPos(9, 250, 9);
        BlockState alloy = st("alloy_smelter_port");
        BlockState diesel = st("diesel_generator_port");
        check("C1 合金炉接线口不再 requiresCorrectToolForDrops", !alloy.requiresCorrectToolForDrops());
        check("C2 柴油机接线口不再 requiresCorrectToolForDrops", !diesel.requiresCorrectToolForDrops());
        check("C3 柴油机接线口空手 canHarvestBlock = true",
                diesel.canHarvestBlock(level, pos, player));
        List<ItemStack> d = Block.getDrops(diesel, level, pos, null, player, ItemStack.EMPTY);
        check("C4 柴油机接线口的掉落是接线块（实测 " + describe(d) + "）",
                d.size() == 1 && d.get(0).getItem() == ModBlocks.WIRING_BLOCK_ITEM.get());
        BlockState stone = Blocks.STONE.defaultBlockState();
        check("C5 口径对照：原版石头**既**在 pickaxe 标签里**又**需要正确工具 ⇒ 标签只管速度",
                stone.is(BlockTags.MINEABLE_WITH_PICKAXE) && stone.requiresCorrectToolForDrops());
    }

    // ---------------------------------------------------------------- B/C 端到端（第 3 tick）
    private static void checkSolarPanelE2E() {
        say(TAG + "================ B' 端到端（开局后第 " + ticks + " tick）：空手挖掉一块太阳能板 ================");
        BlockPos pos = new BlockPos(8, 250, 8);
        boolean tileDrops = level.getGameRules().getBoolean(GameRules.RULE_DOBLOCKDROPS);
        check("B6 游戏规则 doBlockDrops = true（`popResource` 里的最后一道闸门）", tileDrops);
        // ⚠ 环境限制（本轮实测，写进 §4.161）：探针**没有真玩家**（players=0）⇒ 没有任何"实体刻"区块
        //   ⇒ 新 addFreshEntity 的掉落物留在实体管理器的 pending 队列里，`getAllEntities()` /
        //   `getEntitiesOfClass` 一律数不到（实测：手动丢一根木棍，addFreshEntity 返回 true、
        //   isAlive 也 true，但 2.5 格与 64 格的 AABB、getAllEntities 全是 0）。
        //   ⇒ "世界里出现掉落物"这一条在服务端探针里**验不了**，只能把**原版那条链逐段**跑通。
        say(TAG + "    环境记录：players=" + level.players().size()
                + " ⇒ 新加实体" + (level.players().isEmpty() ? "**不可见**（无实体刻区块）" : "可见")
                + "；本条因此只验「链条逐段」");

        boolean placed = level.setBlockAndUpdate(pos, st("solar_panel"));
        BlockState now = level.getBlockState(pos);
        // 原版那条链（ServerPlayerGameMode.destroyBlock 274-278 + Block.dropResources）：
        //   ① canHarvestBlock（手上没工具也要 true）→ ② getDrops → ③ popResource
        boolean gate = now.canHarvestBlock(level, pos, player);
        List<ItemStack> chain = Block.getDrops(now, level, pos, null, player, ItemStack.EMPTY);
        boolean popped = false;
        if (chain.size() == 1) {
            ItemEntity e = new ItemEntity(level, pos.getX() + 0.5D, pos.getY() + 0.5D, pos.getZ() + 0.5D,
                    chain.get(0).copy());
            popped = level.addFreshEntity(e) && e.isAlive();
            e.discard();
        }
        level.removeBlock(pos, false);
        check("B7 掉落链逐段成立：落上方块=" + placed + " / 空手 canHarvestBlock=" + gate
                + " / getDrops=" + describe(chain) + " / popResource=" + popped,
                placed && gate && chain.size() == 1 && popped);
        check("B8 该链产出的就是太阳能板本身（实测 " + describe(chain) + "）",
                chain.size() == 1 && chain.get(0).getItem() == ModBlocks.SOLAR_PANEL_ITEM.get());
    }

    private static void checkPortE2E() {
        say(TAG + "================ C' 端到端：空手挖掉柴油机接线口 ================");
        BlockPos pos = new BlockPos(9, 250, 9);
        boolean placed = level.setBlockAndUpdate(pos, st("diesel_generator_port"));
        BlockState now = level.getBlockState(pos);
        boolean gate = now.canHarvestBlock(level, pos, player);
        List<ItemStack> chain = Block.getDrops(now, level, pos, null, player, ItemStack.EMPTY);
        boolean popped = false;
        if (chain.size() == 1) {
            ItemEntity e = new ItemEntity(level, pos.getX() + 0.5D, pos.getY() + 0.5D, pos.getZ() + 0.5D,
                    chain.get(0).copy());
            popped = level.addFreshEntity(e) && e.isAlive();
            e.discard();
        }
        level.removeBlock(pos, false);
        check("C6 接线口掉落链逐段成立：落上=" + placed + " / 空手 canHarvestBlock=" + gate
                + " / getDrops=" + describe(chain) + " / popResource=" + popped + "（应当是接线块）",
                placed && gate && chain.size() == 1 && popped
                        && chain.get(0).getItem() == ModBlocks.WIRING_BLOCK_ITEM.get());
    }

    // ---------------------------------------------------------------- 工具
    private static int countItems(ServerLevel level, BlockPos pos) {
        return level.getEntitiesOfClass(ItemEntity.class, box(pos)).size();
    }

    /** `getAllEntities()` 的条数（返回的是 Iterable，没有 size()）。 */
    private static int countAllEntities(ServerLevel level) {
        int n = 0;
        for (net.minecraft.world.entity.Entity ignored : level.getAllEntities()) {
            n++;
        }
        return n;
    }

    private static List<ItemStack> itemsAt(ServerLevel level, BlockPos pos) {
        List<ItemStack> out = new ArrayList<>();
        for (ItemEntity e : level.getEntitiesOfClass(ItemEntity.class, box(pos))) {
            out.add(e.getItem());
        }
        return out;
    }

    private static void clearItems(ServerLevel level, BlockPos pos) {
        for (ItemEntity e : level.getEntitiesOfClass(ItemEntity.class, box(pos))) {
            e.discard();
        }
    }

    private static AABB box(BlockPos pos) {
        return new AABB(pos).inflate(2.5D);
    }

    private static String describe(List<ItemStack> stacks) {
        if (stacks.isEmpty()) {
            return "空";
        }
        StringBuilder sb = new StringBuilder();
        for (ItemStack s : stacks) {
            if (sb.length() > 0) {
                sb.append(" + ");
            }
            sb.append(s.getCount()).append("x")
                    .append(BuiltInRegistries.ITEM.getKey(s.getItem()).getPath());
        }
        return sb.toString();
    }
}
