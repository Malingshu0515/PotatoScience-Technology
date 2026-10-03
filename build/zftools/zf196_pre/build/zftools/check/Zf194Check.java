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
import net.minecraft.world.entity.item.ItemEntity;
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
 * ZF194 临时探针（0.14：坍缩模式的方块改成**下落方块飞向奇点、到中心清除**）。
 *
 * <p><b>用户原话</b>：「看不出来坍缩模式在吸取周围方块（做成把方块变成下落形式的
 * 吸取到黑洞中心位置再清除）」。</p>
 *
 * <p>验五条：① 方块真的变成**下落方块**（原位清空 + 场上多了一个 FallingBlockEntity）；
 * ② 那个下落方块的速度**指向黑洞中心**；③ 到中心（{@link BlackHoleManager#CLEAR_RADIUS} 以内）
 * 就**清除**（实体没了、不留方块也不掉物品）；④ 反面自证：**普通**模式仍然"码放"（没有下落方块）；
 * ⑤ 黑洞没了之后，还在飞的方块**不会被清除**（留着等它自己落地）。</p>
 *
 * <p>⚠ 位置全在**出生点区块**里：探针跑在 {@code ServerStartedEvent}（服务端还没 tick），
 * 别的区块的实体表可能没加载 ⇒ `getEntitiesOfClass` 看不到东西（ZF192 那轮的教训，见 §4.192④）。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf194Check {

    private static final String TAG = "[A194] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf194_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;
    /** 高空（离地 &gt; 40 格）⇒ 扫描范围够不到地形；同一根区块列 = 出生点区块，实体表一定加载着。 */
    private static final int HIGH = 60;

    private Zf194Check() {
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
        System.out.println("[PotatoST] Zf194Check START");
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

    private static List<FallingBlockEntity> flying(ServerLevel level, Vec3 center) {
        return level.getEntitiesOfClass(FallingBlockEntity.class,
                new AABB(center, center).inflate(BlackHoleManager.PULL_RADIUS));
    }

    private static void run(ServerLevel level) {
        BlockPos spawn = level.getSharedSpawnPos();
        FakePlayer fp = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "zf194"));
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(100);
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(64_000_000);
        // ⚠ 洞的高度必须用**地表高度 + 60**，不能拿"出生点坐标的 y"凑：出生点在山坡上时，
        //   那里可能已经有地形落在扫描范围（±40）里 ⇒ 黑洞先吃地形、100 块的搬运预算用光，
        //   我摆的那块永远轮不到（Q4 第一版就是这么红的）。
        int surface = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX(), spawn.getZ());
        int holeY = surface + HIGH;

        // ════════ Q1/Q2/Q3 坍缩模式：方块变下落方块 → 朝中心飞 → 到中心清除 ════════
        Vec3 hA = new Vec3(spawn.getX() + 0.5D, holeY, spawn.getZ() + 0.5D);
        BlockPos marker = BlockPos.containing(hA).offset(6, 0, 0);
        level.setBlockAndUpdate(marker, Blocks.STONE.defaultBlockState());
        ItemStack pA = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pA);
        BlackHoleManager.spawn(level, hA, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pA);
        tickMany(140);   // 扫一整轮（81³ / 4096 ≈ 130 tick）才轮到那块石头

        boolean markerAir = !level.getBlockState(marker).is(Blocks.STONE);
        List<FallingBlockEntity> flyingNow = flying(level, hA);
        check(markerAir && flyingNow.size() >= 1,
                "Q1 坍缩模式把方块变成**下落方块**（原位清空 + 场上多了 FallingBlockEntity）",
                "原位已空=" + markerAir + " ｜ 在飞的下落方块 = " + flyingNow.size());

        double aim = -2.0D;
        if (!flyingNow.isEmpty()) {
            FallingBlockEntity fb = flyingNow.get(0);
            Vec3 dir = hA.subtract(fb.position());
            if (dir.lengthSqr() > 1.0E-6D && fb.getDeltaMovement().lengthSqr() > 1.0E-6D) {
                aim = dir.normalize().dot(fb.getDeltaMovement().normalize());
            }
        }
        check(aim > 0.9D,
                "Q2 它的速度**指向黑洞中心**（方向余弦 > 0.9；探针没法让它自己 tick，只能验方向）",
                "方向余弦 = " + String.format("%.3f", aim));

        boolean cleared = false, noBlock = false, noItem = false;
        if (!flyingNow.isEmpty()) {
            FallingBlockEntity fb = flyingNow.get(0);
            fb.setPos(hA);                       // 手动"飞到了"中心（没有服务端 tick，位置得自己挪）
            BlackHoleManager.tick();
            cleared = fb.isRemoved() || level.getEntities().get(fb.getId()) == null;
            noBlock = level.getBlockState(BlockPos.containing(hA)).isAir();
            noItem = level.getEntitiesOfClass(ItemEntity.class,
                    new AABB(hA, hA).inflate(4.0D)).isEmpty();
        }
        check(cleared && noBlock && noItem,
                "Q3 到中心（≤ " + BlackHoleManager.CLEAR_RADIUS + " 格）就**清除**：实体没了、不留方块、不掉物品",
                "已清除=" + cleared + " ｜ 中心还是空气=" + noBlock + " ｜ 中心没掉落物=" + noItem);
        BlackHoleManager.clear();

        // ════════ Q4 反面自证：普通模式仍然是"码放" ════════
        // ⚠ 高度也必须用 holeY（地表 + 60）：早先写成 holeY-20 时，扫描范围（±40）刚好够到地表
        //   ⇒ 普通模式先把 100 块地形搬光，我摆的那块永远轮不到（Q4 第二版就是这么红的）。
        Vec3 hB = new Vec3(spawn.getX() + 0.5D, holeY, spawn.getZ() + 8.5D);
        BlockPos marker2 = BlockPos.containing(hB).offset(15, 0, 0);
        level.setBlockAndUpdate(marker2, Blocks.STONE.defaultBlockState());
        ItemStack pB = device(64_000_000, GravityDeviceItem.MODE_SWALLOW);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pB);
        BlackHoleManager.spawn(level, hB, Blocks.STONE, fp, GravityDeviceItem.MODE_SWALLOW, pB);
        // ⚠ 判据写成"**新增**了几个下落方块"而不是"一个都没有"：别的探针（同一次跑里）也可能
        //   在附近留下还在飞的下落方块 —— 只要求"这次搬运没有产生新的"就够了（第一版就是被这个坑红的）。
        int flyBefore = flying(level, hB).size();
        tickMany(140);
        int flyAfter = flying(level, hB).size();
        boolean gone2 = !level.getBlockState(marker2).is(Blocks.STONE);
        boolean piled = level.getBlockState(BlockPos.containing(hB).below()).is(Blocks.STONE);
        boolean noFlying = flyAfter <= flyBefore;
        check(gone2 && piled && noFlying,
                "Q4 反面自证：**普通**模式仍然把方块**码在黑洞脚下**（没有下落方块参与）",
                "原位已空=" + gone2 + " ｜ 脚下码上了=" + piled + " ｜ 没有新增下落方块=" + noFlying
                        + "（" + flyBefore + "→" + flyAfter + "）");
        BlackHoleManager.clear();

        // ════════ Q5 黑洞没了之后，还在飞的方块不被清除 ════════
        Vec3 hC = new Vec3(spawn.getX() + 0.5D, holeY, spawn.getZ() + 4.5D);
        BlockPos marker3 = BlockPos.containing(hC).offset(6, 0, 0);
        level.setBlockAndUpdate(marker3, Blocks.DIRT.defaultBlockState());
        ItemStack pC = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pC);
        BlackHoleManager.spawn(level, hC, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pC);
        tickMany(140);
        List<FallingBlockEntity> inFlight = flying(level, hC);
        int before = inFlight.size();
        BlackHoleManager.clear();               // 黑洞没了（= 操作者断电/走人）
        tickMany(5);
        int after = flying(level, hC).size();
        check(before >= 1 && after == before,
                "Q5 黑洞没了之后，还在飞的方块**不会被清除**（它们会照常落地变回方块 —— 不凭空丢东西）",
                "黑洞消失前 " + before + " 个在飞 ｜ 消失后 " + after + " 个仍在");

        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(1500);
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(8_000_000);
    }
}
