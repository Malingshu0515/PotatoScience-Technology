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
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF192 临时探针（0.14：**坍缩模式空手也能放**）。
 *
 * <p><b>用户原话</b>：「坍缩模式空手也能放」。</p>
 *
 * <p>验六条：① 空手（副手空）能放坍缩模式且只扣 4M、装置不坏；② 那个洞照样无差别吸方块 + 销毁掉落物；
 * ③ 反面自证：普通模式空手**放不出来**；④ 坍缩模式蓄力时副手空着**不会被取消**；
 * ⑤ 反面自证：普通模式蓄力时副手空着立刻取消；⑥ 空手那面"种子方块 = AIR"的哨兵**过得了存档/读档**
 * （而普通模式的 AIR 假洞仍然被丢掉）。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf192Check {

    private static final String TAG = "[A192] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf192_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf192Check() {
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
        System.out.println("[PotatoST] Zf192Check START");   // 诊断：探针跑的顺序
        MinecraftServer server = event.getServer();
        try {
            run(server, server.overworld());
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

    // ============================================================
    //  小工具
    // ============================================================

    private static ItemStack device(int energy, int mode) {
        ItemStack stack = new ItemStack(ModItems.GRAVITY_DEVICE.get());
        GravityDeviceItem.setMode(stack, mode);
        GravityDeviceItem.setEnergy(stack, energy);
        return stack;
    }

    /** 开火：主手装置、副手**可选**（withSeed=false 就是"空手"），{@code releaseUsing(timeLeft=0)}。 */
    private static void fire(ServerLevel level, FakePlayer fp, BlockPos at, ItemStack stack, boolean withSeed) {
        fp.setItemInHand(InteractionHand.MAIN_HAND, stack);
        fp.setItemInHand(InteractionHand.OFF_HAND,
                withSeed ? new ItemStack(Blocks.STONE) : ItemStack.EMPTY);
        fp.moveTo(at.getX() + 0.5D, at.getY(), at.getZ() + 0.5D, 0.0F, 0.0F);
        stack.getItem().releaseUsing(stack, level, fp, 0);
    }

    private static void tickMany(int n) {
        for (int i = 0; i < n; i++) {
            BlackHoleManager.tick();
        }
    }

    /**
     * 把中心所在区块**强制加载**到 entity-ticking 档（0.14 ZF192 补的判据修法）。
     *
     * <p>⚠ 探针跑在 {@code ServerStartedEvent} 里，服务端还没 tick 过 ⇒ 光靠
     * {@code setBlockAndUpdate}/{@code isLoaded()} 只能保证"方块读得到"，
     * {@code getEntitiesOfClass()} 可能一个生物/掉落物都看不到（Zf190 那边实测"可见生物 0"）。
     * {@code setChunkForced} 挂 FORCED 票（等级 = ENTITY_TICKING）才稳定。</p>
     */
    private static void forceChunk(ServerLevel level, Vec3 center) {
        BlockPos p = BlockPos.containing(center);
        level.setChunkForced(p.getX() >> 4, p.getZ() >> 4, true);
    }

    private static void unforceChunk(ServerLevel level, Vec3 center) {
        BlockPos p = BlockPos.containing(center);
        level.setChunkForced(p.getX() >> 4, p.getZ() >> 4, false);
    }

    private static void run(MinecraftServer server, ServerLevel level) {
        BlockPos spawn = level.getSharedSpawnPos();
        FakePlayer fp = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "zf192"));

        // ════════ P1 空手放坍缩模式 ════════
        // 高空（离地 > 40 格）⇒ 只有我摆的东西可吃，不会被地形干扰
        BlockPos fireAt = spawn.offset(40, 100, 40);
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(8_000_000);
        ItemStack bare = device(8_000_000, GravityDeviceItem.MODE_COLLAPSE);
        int before = BlackHoleManager.activeCount();
        fire(level, fp, fireAt, bare, false);
        check(GravityDeviceItem.getEnergy(bare) == 4_000_000 && !bare.isEmpty()
                        && BlackHoleManager.activeCount() == before + 1,
                "P1 **空手**（副手空）放坍缩模式：扣 4M、装置完好、黑洞出现",
                "剩 " + GravityDeviceItem.getEnergy(bare) + " FE；装置 empty=" + bare.isEmpty()
                        + "；黑洞 " + before + "→" + BlackHoleManager.activeCount());

        // ════════ P2 那个空手的洞照样干活（无差别吸方块 + 销毁掉落物）════════
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(100);
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(64_000_000);
        GravityDeviceItem.setEnergy(bare, 64_000_000);   // 给它续电，撑住 200 tick
        Vec3 center = new Vec3(fireAt.getX() + 0.5D, fireAt.getY() + 1.0D, fireAt.getZ() + 0.5D);
        forceChunk(level, center);   // 掉落物/方块的实体查询要这一档才稳
        BlockPos stoneAt = BlockPos.containing(center).offset(15, 0, 0);
        level.setBlockAndUpdate(stoneAt, Blocks.STONE.defaultBlockState());
        ItemEntity drop = new ItemEntity(level, center.x + 10.0D, center.y, center.z,
                new ItemStack(Items.DIAMOND, 2));
        level.addFreshEntity(drop);
        tickMany(200);
        boolean stoneGone = !level.getBlockState(stoneAt).is(Blocks.STONE);
        check(stoneGone && drop.isRemoved(),
                "P2 空手放的洞照样「无差别吸方块 + 销毁掉落物」（种子方块 = AIR 不影响它吸什么）",
                "石头走了=" + stoneGone + " ｜ 掉落物没了=" + drop.isRemoved());
        unforceChunk(level, center);
        BlackHoleManager.clear();

        // ════════ P3 反面自证：普通模式空手放不出来 ════════
        ItemStack plain = device(8_000_000, GravityDeviceItem.MODE_SWALLOW);
        int before3 = BlackHoleManager.activeCount();
        fire(level, fp, fireAt, plain, false);
        check(GravityDeviceItem.getEnergy(plain) == 8_000_000
                        && BlackHoleManager.activeCount() == before3,
                "P3 反面自证：**普通**模式空手**放不出来**（电不掉、黑洞不出现）",
                "电 " + GravityDeviceItem.getEnergy(plain) + "；黑洞 " + BlackHoleManager.activeCount());

        // ════════ P4/P5 蓄力时副手空着：坍缩模式不取消、普通模式取消 ════════
        ItemStack chargeCollapse = device(8_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, chargeCollapse);
        fp.setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY);
        fp.startUsingItem(InteractionHand.MAIN_HAND);
        chargeCollapse.getItem().onUseTick(level, fp, chargeCollapse,
                PotatoSTConfig.gravityChargeTicks() - 5);
        check(fp.isUsingItem(),
                "P4 坍缩模式蓄力时副手空着 ⇒ **不会**被中途取消（isUsingItem 仍为 true）",
                "还在蓄力 = " + fp.isUsingItem());
        fp.stopUsingItem();

        ItemStack chargePlain = device(8_000_000, GravityDeviceItem.MODE_SWALLOW);
        fp.setItemInHand(InteractionHand.MAIN_HAND, chargePlain);
        fp.setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY);
        fp.startUsingItem(InteractionHand.MAIN_HAND);
        chargePlain.getItem().onUseTick(level, fp, chargePlain,
                PotatoSTConfig.gravityChargeTicks() - 5);
        check(!fp.isUsingItem(),
                "P5 反面自证：普通模式蓄力时副手空着 ⇒ **立刻取消**",
                "还在蓄力 = " + fp.isUsingItem());
        fp.stopUsingItem();

        // ════════ P6 AIR 哨兵过得了存档/读档；普通模式的 AIR 假洞仍然被丢掉 ════════
        BlackHoleManager.Data data = level.getDataStorage()
                .computeIfAbsent(BlackHoleManager.Data.FACTORY, BlackHoleManager.Data.NAME);
        data.holes.clear();          // 先把前几轮探针留下的存档清干净，避免计数被它们搅乱
        BlackHoleManager.clear();
        BlackHoleManager.spawn(level, new Vec3(spawn.getX() + 80.5D, spawn.getY() + 100, spawn.getZ() + 0.5D),
                Blocks.AIR, fp, GravityDeviceItem.MODE_COLLAPSE, null);   // 空手坍缩洞
        BlackHoleManager.spawn(level, new Vec3(spawn.getX() - 80.5D, spawn.getY() + 100, spawn.getZ() + 0.5D),
                Blocks.AIR, fp, GravityDeviceItem.MODE_SWALLOW, null);    // 普通模式 + AIR = "方块没了"
        BlackHoleManager.saveInto(level);
        int saved = data.holes.size();
        BlackHoleManager.clear();
        BlackHoleManager.loadFrom(server);
        check(saved == 2 && BlackHoleManager.activeCount() == 1,
                "P6 存档：空手的坍缩洞（AIR 哨兵）**读得回来**，普通模式的 AIR 假洞仍然被丢掉",
                "存档里 " + saved + " 条 ⇒ 读回 " + BlackHoleManager.activeCount() + " 个（要 1 个）");
        BlackHoleManager.clear();

        // 收尾
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(8_000_000);
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(1500);
    }
}
