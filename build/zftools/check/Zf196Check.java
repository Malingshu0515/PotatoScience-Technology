package com.potatost.mod;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF196 临时探针（0.14：坍缩模式**看得见地拆** —— 近处优先 + 像爆炸那样的碎裂）。
 *
 * <p><b>用户原话</b>：「没有效果啊 要像爆炸那样的 黑洞旁边的方块明显被破坏」。</p>
 *
 * <p>验五条：① 黑洞**旁边**（3 格）的方块很快被拆掉；② 拆除半径**随年龄涨**（同一个洞里，
 * 20 格外那块早期不动、跑够 400 tick 之后被拆）；③ **埋着的**（六面堵死）就地拆、不产生"飞不出来"的
 * 下落方块；④ **露着的**（空气里）仍然变成下落方块飞进中心（ZF194 那套没丢）；
 * ⑤ 拆除与搬运都算进 `max_blocks` 上限（一个封闭石方块堆里最多被拆掉那么多）。</p>
 *
 * <p>⚠ 位置全在**出生点区块**里（探针跑在 {@code ServerStartedEvent}，服务端还没 tick，
 * 别的区块的实体表可能没加载 —— §4.192④）。方块类判据（①②③⑤）不受这条影响。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf196Check {

    private static final String TAG = "[A196] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf196_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;
    private static final int HIGH = 60;

    private Zf196Check() {
    }

    private static void check(boolean ok, String label, String detail) {
        if (ok) {
            passed++;
            LINES.add(TAG + "[OK]   " + label + (detail.isEmpty() ? "" : " ｜ " + detail));
        } else {
            failed++;
            LINES.add(TAG + "[FAIL] " + label + (detail.isEmpty() ? "" : " —— " + detail));
        }
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        System.out.println("[PotatoST] Zf196Check START");
        MinecraftServer server = event.getServer();
        try {
            run(server.overworld());
        } catch (Throwable t) {
            failed++;
            LINES.add(TAG + "[FAIL] EXCEPTION " + t);
            for (StackTraceElement e : t.getStackTrace()) {
                if (e.getClassName().startsWith("com.potatost")) {
                    LINES.add("        at " + e);
                }
            }
        }
        LINES.add("");
        LINES.add("通过 = " + passed + "   失败 = " + failed);
        try {
            Files.createDirectories(REPORT.getParent());
            try (Writer w = new OutputStreamWriter(Files.newOutputStream(REPORT), StandardCharsets.UTF_8)) {
                w.write(String.join("\n", LINES) + "\n");
            }
        } catch (IOException e) {
            System.out.println("probe report write failed: " + e);
        }
        server.halt(false);
    }

    private static ItemStack device(int energy, int mode) {
        ItemStack stack = new ItemStack(ModItems.GRAVITY_DEVICE.get());
        GravityDeviceItem.setMode(stack, mode);
        GravityDeviceItem.setEnergy(stack, energy);
        return stack;
    }

    private static void tickMany(int n) {
        for (int i = 0; i < n; i++) {
            BlackHoleManager.tick();
        }
    }

    private static int flying(ServerLevel level, Vec3 center) {
        return level.getEntitiesOfClass(FallingBlockEntity.class,
                new AABB(center, center).inflate(BlackHoleManager.PULL_RADIUS)).size();
    }

    private static void run(ServerLevel level) {
        BlockPos spawn = level.getSharedSpawnPos();
        FakePlayer fp = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "zf196"));
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(1500);
        PotatoSTConfig.BLACK_HOLE_SCAN_RADIUS.set(40);
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(64_000_000);
        int surface = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX(), spawn.getZ());
        int holeY = surface + HIGH;

        // ════════ S1 身边（3 格）的方块很快被拆 ════════
        Vec3 hA = new Vec3(spawn.getX() + 0.5D, holeY, spawn.getZ() + 0.5D);
        BlockPos near = BlockPos.containing(hA).offset(3, 0, 0);
        level.setBlockAndUpdate(near, Blocks.STONE.defaultBlockState());
        ItemStack pA = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pA);
        BlackHoleManager.spawn(level, hA, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pA);
        tickMany(20);
        check(level.getBlockState(near).isAir(),
                "S1 黑洞**旁边**（3 格）的方块 20 tick 内就被拆掉了（近处优先，不是满世界乱翻）",
                "3 格那块已空 = " + level.getBlockState(near).isAir());
        BlackHoleManager.clear();

        // ════════ S2 拆除半径随年龄涨（同一个洞，20 格外那块）════════
        Vec3 hB = new Vec3(spawn.getX() + 0.5D, holeY, spawn.getZ() + 0.5D);
        BlockPos far = BlockPos.containing(hB).offset(20, 0, 0);
        level.setBlockAndUpdate(far, Blocks.DIRT.defaultBlockState());
        ItemStack pB = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pB);
        BlackHoleManager.spawn(level, hB, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pB);
        tickMany(20);   // 半径 ≈ 3 + 1.6 = 4.6 ⇒ 20 格外不该动
        boolean early = level.getBlockState(far).is(Blocks.DIRT);
        tickMany(400);  // 半径 ≈ 3 + 33 ⇒ 封顶 24 ⇒ 20 格外该被拆
        boolean late = level.getBlockState(far).isAir();
        check(early && late,
                "S2 拆除半径**随年龄涨**：同一个洞，20 格外那块早期不动（半径 4.6）、跑够 400 tick 就被拆（半径封顶 24）",
                "早期还在 = " + early + " ｜ 后期被拆 = " + late
                        + " ｜ 半径函数 r(20)=" + String.format("%.1f", BlackHoleManager.demolishRadiusAt(20))
                        + "、r(400)=" + String.format("%.1f", BlackHoleManager.demolishRadiusAt(400)));
        BlackHoleManager.clear();

        // ════════ S3 埋着的就地拆（不产生"飞不出来"的下落方块）════════
        // ⚠ 必须开到**地下**去验：那里一切都被石头包着（露在外面的只有地表那一层，而它离得远），
        //   所以"露着的飞、埋着的拆"这条分岔才分得清；开在半空中是验不出来的。
        Vec3 hC = new Vec3(spawn.getX() + 0.5D, surface - 30, spawn.getZ() + 0.5D);
        BlockPos buried = BlockPos.containing(hC).offset(8, 0, 0);
        level.setBlockAndUpdate(buried, Blocks.DIAMOND_BLOCK.defaultBlockState());   // 埋在地下 8 格处
        ItemStack pC = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pC);
        BlackHoleManager.spawn(level, hC, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pC);
        tickMany(200);
        boolean buriedGone = !level.getBlockState(buried).is(Blocks.DIAMOND_BLOCK);
        int flyingC = flying(level, hC);
        int demolishedC = BlackHoleManager.demolishedTotal();
        // ⚠ 判据为什么是"两条路都走到"而不是"一个下落方块都没有"：弹坑一开，原来的"埋着"
        //   立刻就变成"露着"了 ⇒ **从外面看不出来**某一块是被拆的还是飞的。所以用诊断计数
        //   （`demolishedTotal`）证明"原地拆"这条路真的走到了，用实体数证明"飞"那条也在走。
        check(buriedGone && demolishedC > 0 && flyingC > 0,
                "S3 两条吃法都在干活：地下的方块被**原地拆**（诊断计数 > 0），露出来的照旧**飞**（在飞 > 0）",
                "地下那块已空=" + buriedGone + " ｜ 累计原地拆 = " + demolishedC + " ｜ 在飞 = " + flyingC);
        BlackHoleManager.clear();

        // ════════ S4 露着的仍然变成下落方块飞进中心 ════════
        Vec3 hD = new Vec3(spawn.getX() + 0.5D, holeY, spawn.getZ() + 12.5D);
        BlockPos open = BlockPos.containing(hD).offset(8, 0, 0);   // 空气里 = 露着
        level.setBlockAndUpdate(open, Blocks.OAK_PLANKS.defaultBlockState());
        ItemStack pD = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pD);
        BlackHoleManager.spawn(level, hD, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pD);
        tickMany(120);   // 半径 r(120)=12.6 ⇒ 8 格那块才进圈（r(60) 只有 7.8，差一点）
        boolean openGone = level.getBlockState(open).isAir();
        int flyingD = flying(level, hD);
        check(openGone && flyingD >= 1,
                "S4 **露着的**（空气里）方块仍然变成下落方块飞进奇点（ZF194 那套没丢）",
                "原位已空=" + openGone + " ｜ 在飞的下落方块 = " + flyingD);
        BlackHoleManager.clear();

        // ════════ S5 拆除也算进搬运上限 ════════
        Vec3 hE = new Vec3(spawn.getX() + 0.5D, holeY, spawn.getZ() - 12.5D);
        BlockPos cE = BlockPos.containing(hE);
        // 一个 9×9×9 的实心石头方堆（内外都是石头）⇒ 拆掉多少一眼可数
        for (int dx = -4; dx <= 4; dx++) {
            for (int dy = -4; dy <= 4; dy++) {
                for (int dz = -4; dz <= 4; dz++) {
                    level.setBlockAndUpdate(cE.offset(dx, dy, dz), Blocks.STONE.defaultBlockState());
                }
            }
        }
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(30);
        ItemStack pE = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pE);
        BlackHoleManager.spawn(level, hE, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pE);
        tickMany(200);
        int removed = 0;
        for (int dx = -4; dx <= 4; dx++) {
            for (int dy = -4; dy <= 4; dy++) {
                for (int dz = -4; dz <= 4; dz++) {
                    if (level.getBlockState(cE.offset(dx, dy, dz)).isAir()) {
                        removed++;
                    }
                }
            }
        }
        check(removed >= 28 && removed <= 32,
                "S5 拆除与搬运都算进 `max_blocks`：上限设 30 ⇒ 9³ 石堆里正好被拆掉 30 块左右",
                "被拆掉 = " + removed + "（上限 30）");
        BlackHoleManager.clear();

        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(1500);
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(8_000_000);
    }
}
