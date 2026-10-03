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
import net.minecraft.core.Direction;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF186 临时探针（0.14：配置系统 + 配置界面，配置项真的驱动行为）。
 *
 * <p><b>用户原话</b>：「联动一下配置界面（做成不是必须依赖项）使本mod可以接受配置 目前我指定的配置项为
 * 黑洞是否为一次性（false则做成只消耗完电力条，不损坏）以及引力装置蓄力时长（默认30s 5-60s可调）
 * 还有单块锂电池容量（1m-20mfe）现在的值为默认值 还想加其它的你自己发挥」。</p>
 *
 * <p><b>验法</b>：不验「取值器返回了配置里的数」（那是同义反复），验的是 ——
 * <b>把配置改了之后，真实的机器/物品/黑洞行为跟着变</b>：
 * <ul>
 *   <li>电池：真放一块锂电池，从 <b>NeoForge 能量能力</b>读容量与"一次能收多少"；</li>
 *   <li>引力装置：真拿一件装置、真调 {@code releaseUsing}（开火那条路），看装置坏没坏、黑洞有没有出来；</li>
 *   <li>黑洞：真生成黑洞 + 真调 {@code tick()}，看它到点有没有坍缩、半径外/内的方块动没动、
 *       生物挨不挨拉、掉不掉血。</li>
 * </ul>
 * 配置改动只走 {@code ConfigValue.set}（**不写盘**）⇒ 服务器退出后 {@code run/config} 里还是出厂值。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf186Check {

    private static final String TAG = "[A186] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf186_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf186Check() {
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

    private static void run(ServerLevel level) {
        // ════════════ A 配置真的加载了、文件真的生成了、默认值对得上 ════════════
        check(PotatoSTConfig.SPEC.isLoaded(), "A1 COMMON 配置已加载（SPEC.isLoaded）",
                "isLoaded=" + PotatoSTConfig.SPEC.isLoaded());

        Path cfg = FMLPaths.CONFIGDIR.get().resolve("potato_s_t-common.toml");
        String text = "";
        try {
            if (Files.isRegularFile(cfg)) {
                text = Files.readString(cfg, StandardCharsets.UTF_8);
            }
        } catch (IOException e) {
            text = "";
        }
        String[] wantKeys = {"one_shot", "lifetime_seconds", "max_blocks", "scan_radius_blocks",
                "pull_entities", "void_damage", "charge_seconds", "capacity_fe",
                "per_block_fe", "transfer_rate_fe", "max_size_blocks"};
        int found = 0;
        for (String k : wantKeys) {
            if (text.contains(k)) {
                found++;
            }
        }
        check(Files.isRegularFile(cfg) && found == wantKeys.length,
                "A2 配置文件真的生成在 config/ 下，11 个键都在",
                cfg + " ｜ 命中 " + found + "/" + wantKeys.length + " 键");

        check(PotatoSTConfig.oneShotBlackHole()
                        && PotatoSTConfig.blackHoleLifetimeTicks() == 400
                        && PotatoSTConfig.blackHoleMaxBlocks() == 1500
                        && PotatoSTConfig.blackHoleScanRadius() == 40
                        && PotatoSTConfig.blackHolePullsEntities()
                        && PotatoSTConfig.blackHoleVoidDamage()
                        && PotatoSTConfig.gravityChargeTicks() == 600
                        && PotatoSTConfig.gravityCapacity() == 8_000_000
                        && PotatoSTConfig.batteryPerBlock() == 4_000_000L
                        && PotatoSTConfig.batteryTransferRate() == 65_536
                        && PotatoSTConfig.batteryMaxBlocks() == 800,
                "A3 出厂默认值 = 落地前的老数值（蓄力 600 tick = 30 秒）",
                "oneShot/寿命/上限/半径/吸生物/虚空 = "
                        + PotatoSTConfig.oneShotBlackHole() + "/" + PotatoSTConfig.blackHoleLifetimeTicks()
                        + "/" + PotatoSTConfig.blackHoleMaxBlocks() + "/" + PotatoSTConfig.blackHoleScanRadius()
                        + "/" + PotatoSTConfig.blackHolePullsEntities() + "/" + PotatoSTConfig.blackHoleVoidDamage()
                        + "；引力 " + PotatoSTConfig.gravityChargeTicks() + " tick / "
                        + PotatoSTConfig.gravityCapacity() + " FE；电池 " + PotatoSTConfig.batteryPerBlock()
                        + " FE / " + PotatoSTConfig.batteryTransferRate() + " FE/t / "
                        + PotatoSTConfig.batteryMaxBlocks() + " 块");

        // ════════════ B 用户点名③：单块锂电池容量（真放一块电池，从能量能力读） ════════════
        BlockPos bp = level.getSharedSpawnPos().offset(20, 0, 20);
        level.setBlockAndUpdate(bp, ModBlocks.LITHIUM_BATTERY.get().defaultBlockState());
        IEnergyStorage store = level.getCapability(Capabilities.EnergyStorage.BLOCK, bp, Direction.UP);
        if (store == null && level.getBlockEntity(bp) instanceof LithiumBatteryBlockEntity be) {
            store = be.getEnergyStorage(Direction.UP);
        }
        check(store != null, "B0 单块锂电池的顶面能量能力拿得到（能力注册没坏）",
                "store=" + (store != null));
        if (store == null) {
            return;
        }
        check(store.getMaxEnergyStored() == 4_000_000,
                "B1 默认单块容量 = 4,000,000 FE", "读到 " + store.getMaxEnergyStored());

        PotatoSTConfig.BATTERY_PER_BLOCK_FE.set(12_000_000);
        int cap12 = store.getMaxEnergyStored();
        check(cap12 == 12_000_000,
                "B2 配置改成 12M ⇒ 同一块电池容量**当场**变 12,000,000（没缓存）",
                "读到 " + cap12 + "（旧的 4M 会红）");

        PotatoSTConfig.BATTERY_TRANSFER_RATE.set(4_096);
        int got = store.receiveEnergy(1_000_000, false);
        check(got == 4_096 && store.getEnergyStored() == 4_096,
                "B3 每面速率改成 4,096 ⇒ 一次只收得进 4,096 FE（要 1,000,000 也不给）",
                "收进 " + got + "，罐里 " + store.getEnergyStored());
        PotatoSTConfig.BATTERY_TRANSFER_RATE.set(65_536);
        PotatoSTConfig.BATTERY_PER_BLOCK_FE.set(4_000_000);
        level.removeBlock(bp, false);

        // ════════════ C 用户点名②：引力装置蓄力时长 ════════════
        ItemStack device = new ItemStack(ModItems.GRAVITY_DEVICE.get());
        check(device.getItem().getUseDuration(device, null) == 600,
                "C1 默认蓄力 30 秒 ⇒ 用时时长 600 tick", "读到 " + device.getItem().getUseDuration(device, null));
        PotatoSTConfig.GRAVITY_CHARGE_SECONDS.set(5);
        int d5 = device.getItem().getUseDuration(device, null);
        PotatoSTConfig.GRAVITY_CHARGE_SECONDS.set(60);
        int d60 = device.getItem().getUseDuration(device, null);
        check(d5 == 100 && d60 == 1_200,
                "C2 配置改成 5 秒 / 60 秒 ⇒ 100 / 1,200 tick（两个端点都对）",
                "5 秒→" + d5 + "，60 秒→" + d60);
        PotatoSTConfig.GRAVITY_CHARGE_SECONDS.set(30);

        // ════════════ D 用户点名①：黑洞是否一次性（走真正的开火路径） ════════════
        BlockPos fireAt = level.getSharedSpawnPos().offset(30, 1, 0);
        FakePlayer fp = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "zf186"));

        int before = BlackHoleManager.activeCount();
        ItemStack oneShot = fireDevice(level, fp, fireAt, true);
        boolean broke = oneShot.isEmpty() || oneShot.getDamageValue() >= oneShot.getMaxDamage();
        check(broke && BlackHoleManager.activeCount() == before + 1,
                "D1 默认一次性：放完装置**当场损坏**、黑洞出现",
                "装置 empty=" + oneShot.isEmpty() + " 耐久 " + oneShot.getDamageValue() + "/"
                        + oneShot.getMaxDamage() + "；黑洞 " + before + "→" + BlackHoleManager.activeCount());
        BlackHoleManager.clear();

        PotatoSTConfig.BLACK_HOLE_ONE_SHOT.set(false);
        int before2 = BlackHoleManager.activeCount();
        ItemStack reusable = fireDevice(level, fp, fireAt, true);
        check(!reusable.isEmpty() && reusable.getDamageValue() == 0
                        && GravityDeviceItem.getEnergy(reusable) == 0
                        && BlackHoleManager.activeCount() == before2 + 1,
                "D2 改成「非一次性」：装置**完好**（耐久 0）、电力条被抽干、黑洞照样出现",
                "装置 empty=" + reusable.isEmpty() + " 耐久 " + reusable.getDamageValue()
                        + " 电量 " + GravityDeviceItem.getEnergy(reusable)
                        + "；黑洞 " + before2 + "→" + BlackHoleManager.activeCount());
        BlackHoleManager.clear();

        // 没充满电时开火必须什么都不发生（闸门还在，不是"配置一改就能空放"）
        PotatoSTConfig.BLACK_HOLE_ONE_SHOT.set(true);
        ItemStack half = new ItemStack(ModItems.GRAVITY_DEVICE.get());
        GravityDeviceItem.setEnergy(half, 4_000_000);
        fp.setItemInHand(InteractionHand.MAIN_HAND, half);
        fp.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Blocks.DIAMOND_BLOCK));
        int before3 = BlackHoleManager.activeCount();
        half.getItem().releaseUsing(half, level, fp, 0);
        check(BlackHoleManager.activeCount() == before3 && !half.isEmpty(),
                "D3 反面自证：电量只有一半时开火**什么都不会发生**（闸门没有被配置绕过去）",
                "黑洞 " + before3 + "→" + BlackHoleManager.activeCount() + "；装置 empty=" + half.isEmpty());

        // ════════════ E 黑洞存活时长真的驱动坍缩 ════════════
        BlockPos holeAt = level.getSharedSpawnPos().offset(-25, 6, 25);
        PotatoSTConfig.BLACK_HOLE_LIFETIME_SECONDS.set(5);   // 100 tick
        BlackHoleManager.spawn(level, net.minecraft.world.phys.Vec3.atCenterOf(holeAt),
                Blocks.DIAMOND_BLOCK, fp, GravityDeviceItem.MODE_SWALLOW);
        for (int i = 0; i < 100; i++) {
            BlackHoleManager.tick();
        }
        check(BlackHoleManager.activeCount() == 0,
                "E1 寿命改成 5 秒 ⇒ 跑满 100 tick 后黑洞**已坍缩**",
                "活着的黑洞 = " + BlackHoleManager.activeCount());

        PotatoSTConfig.BLACK_HOLE_LIFETIME_SECONDS.set(10);   // 200 tick
        BlackHoleManager.spawn(level, net.minecraft.world.phys.Vec3.atCenterOf(holeAt),
                Blocks.DIAMOND_BLOCK, fp, GravityDeviceItem.MODE_SWALLOW);
        for (int i = 0; i < 100; i++) {
            BlackHoleManager.tick();
        }
        check(BlackHoleManager.activeCount() == 1,
                "E2 对照：寿命改成 10 秒 ⇒ 同样跑 100 tick，黑洞**还在**（说明寿命真是配置说了算）",
                "活着的黑洞 = " + BlackHoleManager.activeCount());
        BlackHoleManager.clear();

        // ════════════ F 扫描半径真的驱动"吸得到 / 吸不到" ════════════
        BlockPos center = level.getSharedSpawnPos().offset(0, 12, 40);
        BlockPos far = center.offset(15, 0, 0);          // 15 格：> 半径 8、> 禁采区 12
        PotatoSTConfig.BLACK_HOLE_SCAN_RADIUS.set(8);
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(1_500);
        level.setBlockAndUpdate(far, Blocks.DIAMOND_BLOCK.defaultBlockState());
        BlackHoleManager.spawn(level, net.minecraft.world.phys.Vec3.atCenterOf(center),
                Blocks.DIAMOND_BLOCK, fp, GravityDeviceItem.MODE_SWALLOW);
        for (int i = 0; i < 40; i++) {
            BlackHoleManager.tick();
        }
        boolean stillThere = level.getBlockState(far).is(Blocks.DIAMOND_BLOCK);
        check(stillThere, "F1 半径改成 8 ⇒ 15 格外的钻石块**一根汗毛都没动**",
                "还在 = " + stillThere);
        BlackHoleManager.clear();

        PotatoSTConfig.BLACK_HOLE_SCAN_RADIUS.set(40);
        level.setBlockAndUpdate(far, Blocks.DIAMOND_BLOCK.defaultBlockState());
        BlackHoleManager.spawn(level, net.minecraft.world.phys.Vec3.atCenterOf(center),
                Blocks.DIAMOND_BLOCK, fp, GravityDeviceItem.MODE_SWALLOW);
        for (int i = 0; i < 200; i++) {
            BlackHoleManager.tick();
        }
        boolean gone = !level.getBlockState(far).is(Blocks.DIAMOND_BLOCK);
        check(gone, "F2 对照：半径改成 40 ⇒ 同一个位置的钻石块被**搬走了**",
                "原位置已空 = " + gone);
        BlackHoleManager.clear();
        level.setBlockAndUpdate(far, Blocks.AIR.defaultBlockState());

        // ════════════ G 吸生物 / 虚空伤害两个开关 ════════════
        BlockPos cowAt = level.getSharedSpawnPos().offset(-30, 2, -30);
        Cow cow = EntityType.COW.create(level);
        if (cow == null) {
            check(false, "G0 生成一头牛（测试用）", "EntityType.COW.create 返回 null");
            return;
        }
        cow.moveTo(cowAt.getX() + 0.5D, cowAt.getY(), cowAt.getZ() + 0.5D, 0.0F, 0.0F);
        cow.setHealth(10.0F);
        level.addFreshEntity(cow);
        net.minecraft.world.phys.Vec3 holeCenter = new net.minecraft.world.phys.Vec3(
                cowAt.getX() + 3.5D, cowAt.getY(), cowAt.getZ() + 0.5D);

        PotatoSTConfig.BLACK_HOLE_PULL_ENTITIES.set(false);
        BlackHoleManager.spawn(level, holeCenter, Blocks.DIAMOND_BLOCK, fp, GravityDeviceItem.MODE_SWALLOW);
        for (int i = 0; i < 5; i++) {
            BlackHoleManager.tick();
        }
        double still = cow.getDeltaMovement().length();
        check(still == 0.0D, "G1a 关掉「吸引生物」⇒ 牛**一动不动**（速度还是 0）",
                "速度 = " + still);
        BlackHoleManager.clear();

        PotatoSTConfig.BLACK_HOLE_PULL_ENTITIES.set(true);
        BlackHoleManager.spawn(level, holeCenter, Blocks.DIAMOND_BLOCK, fp, GravityDeviceItem.MODE_SWALLOW);
        double moved = 0.0D;
        for (int i = 0; i < 5; i++) {
            BlackHoleManager.tick();
            moved = Math.max(moved, cow.getDeltaMovement().length());
        }
        check(moved > 0.5D, "G1b 打开「吸引生物」⇒ 牛被拉向奇点（速度 > 0.5）",
                "最大速度 = " + moved);
        BlackHoleManager.clear();

        float hpBefore;
        Cow cow2 = EntityType.COW.create(level);
        if (cow2 == null) {
            check(false, "G2 生成第二头牛", "null");
            return;
        }
        cow2.moveTo(cowAt.getX() + 3.5D, cowAt.getY(), cowAt.getZ() + 0.5D, 0.0F, 0.0F);
        cow2.setHealth(10.0F);
        level.addFreshEntity(cow2);
        PotatoSTConfig.BLACK_HOLE_PULL_ENTITIES.set(false);
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(false);
        BlackHoleManager.spawn(level, holeCenter, Blocks.DIAMOND_BLOCK, fp, GravityDeviceItem.MODE_SWALLOW);
        for (int i = 0; i < 10; i++) {
            BlackHoleManager.tick();
        }
        hpBefore = cow2.getHealth();
        check(hpBefore == 10.0F, "G2a 关掉「视界虚空伤害」⇒ 站在奇点边上也不掉血",
                "血量 = " + hpBefore);
        BlackHoleManager.clear();

        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(true);
        BlackHoleManager.spawn(level, holeCenter, Blocks.DIAMOND_BLOCK, fp, GravityDeviceItem.MODE_SWALLOW);
        for (int i = 0; i < 10; i++) {
            BlackHoleManager.tick();
        }
        float hpAfter = cow2.getHealth();
        check(hpAfter < hpBefore, "G2b 打开「视界虚空伤害」⇒ 同一头牛掉血（10 tick 一次 4 点）",
                "血量 " + hpBefore + " → " + hpAfter);
        BlackHoleManager.clear();

        // 收尾：把配置改回出厂值（set 不写盘，但 session 内还是改回去，方便人看日志）
        PotatoSTConfig.BLACK_HOLE_LIFETIME_SECONDS.set(20);
        PotatoSTConfig.BLACK_HOLE_SCAN_RADIUS.set(40);
        PotatoSTConfig.BLACK_HOLE_PULL_ENTITIES.set(true);
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(true);
        PotatoSTConfig.BLACK_HOLE_ONE_SHOT.set(true);
    }

    /** 真开火：满电 + 副手方块 + 主手装置，走 {@code releaseUsing}（timeLeft=0）。 */
    private static ItemStack fireDevice(ServerLevel level, FakePlayer fp, BlockPos at, boolean full) {
        ItemStack stack = new ItemStack(ModItems.GRAVITY_DEVICE.get());
        GravityDeviceItem.setEnergy(stack, full ? PotatoSTConfig.gravityCapacity() : 0);
        fp.setItemInHand(InteractionHand.MAIN_HAND, stack);
        fp.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Blocks.DIAMOND_BLOCK));
        fp.moveTo(at.getX() + 0.5D, at.getY(), at.getZ() + 0.5D, 0.0F, 0.0F);
        stack.getItem().releaseUsing(stack, level, fp, 0);
        return stack;
    }
}
