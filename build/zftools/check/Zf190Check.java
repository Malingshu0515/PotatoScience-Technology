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
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Cow;
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
 * ZF190 临时探针（0.14：黑洞召唤费 bug 修复 + 引力装置第三模式「坍缩模式-危险」）。
 *
 * <p><b>用户原话</b>：「修一下bug 黑洞正常单次召唤应该只消耗8m电力（配置改成64m之后充满一次性把全部电力
 * 都消耗完了）然后 引力装置再加一个模式【坍缩模式-危险】（红色字体）开启后无差别吸引最近所有的生物以及方块
 * （振金免疫）吸引到的掉落物会销毁 然后吸引时间越长吸引强度越高伤害也越高（召唤这个不是一次性消耗8m电力
 * 而是召唤出来消耗4m 然后黑洞每存在1tick消耗50kFE没有电力时候黑洞消失）（一个黑洞存在超过2分钟也会销毁
 * 并产生30power的爆炸）」。</p>
 *
 * <p><b>验法</b>：全部量**真行为** —— 电量差、黑洞个数、方块在不在、掉落物还在不在、牛的速度与血量差。
 * 为了便宜：坍缩模式的试验黑洞一律开在**高空**（离地 &gt; 40 格），这样"可吃的方块"只有我摆的那几块，
 * 不会把地形啃一大片、也不会把 100 块的搬运预算提前耗光（见 {@code HIGH} 的注释）。</p>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf190Check {

    private static final String TAG = "[A190] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf190_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;
    /** 试验黑洞一律开在出生点上方这么高 —— 离地 > 40 格，扫描范围够不到地形。 */
    private static final int HIGH = 100;

    private Zf190Check() {
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
        event.getServer().halt(false);
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

    /** 真开火：主手装置、副手方块（坍缩模式也仍要"引子"）、{@code releaseUsing(timeLeft=0)}。 */
    private static void fire(ServerLevel level, FakePlayer fp, BlockPos at, ItemStack stack) {
        fp.setItemInHand(InteractionHand.MAIN_HAND, stack);
        fp.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Blocks.STONE));
        fp.moveTo(at.getX() + 0.5D, at.getY(), at.getZ() + 0.5D, 0.0F, 0.0F);
        stack.getItem().releaseUsing(stack, level, fp, 0);
    }

    private static void tickMany(int n) {
        for (int i = 0; i < n; i++) {
            BlackHoleManager.tick();
        }
    }

    private static Cow cow(ServerLevel level, Vec3 at, float health) {
        Cow c = EntityType.COW.create(level);
        if (c == null) {
            return null;
        }
        c.moveTo(at.x, at.y, at.z, 0.0F, 0.0F);
        c.setHealth(health);
        level.addFreshEntity(c);
        return c;
    }

    private static double speedOf(Cow c) {
        return c == null ? -1.0D : c.getDeltaMovement().length();
    }

    // ============================================================
    //  主流程
    // ============================================================
    private static void run(ServerLevel level) {
        BlockPos spawn = level.getSharedSpawnPos();
        FakePlayer fp = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "zf190"));

        // ════════════ A 召唤费：固定 8M（用户报的 bug） ════════════
        BlockPos fireAt = spawn.offset(30, 1, 0);

        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(8_000_000);
        ItemStack full8 = device(8_000_000, GravityDeviceItem.MODE_SWALLOW);
        int before = BlackHoleManager.activeCount();
        fire(level, fp, fireAt, full8);
        check(GravityDeviceItem.getEnergy(full8) == 0 && full8.isEmpty()
                        && BlackHoleManager.activeCount() == before + 1,
                "A1 老默认（容量 8M、一次性）：满电放普通模式 ⇒ 电归 0、装置损坏、黑洞出现（老行为没变）",
                "剩 " + GravityDeviceItem.getEnergy(full8) + " FE；装置坏了=" + full8.isEmpty()
                        + "；黑洞 " + before + "→" + BlackHoleManager.activeCount());
        BlackHoleManager.clear();

        // ⚠ 量"扣了多少电"必须先把「一次性」关掉：默认开着时装置放完就**没了**，
        //   剩下的电跟着物品一起消失（读出来还是 0）—— 第一版就是这么假红的。
        PotatoSTConfig.BLACK_HOLE_ONE_SHOT.set(false);
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(64_000_000);
        ItemStack full64 = device(64_000_000, GravityDeviceItem.MODE_SWALLOW);
        int before2 = BlackHoleManager.activeCount();
        fire(level, fp, fireAt, full64);
        check(GravityDeviceItem.getEnergy(full64) == 56_000_000 && !full64.isEmpty()
                        && BlackHoleManager.activeCount() == before2 + 1,
                "A2 **用户报的 bug**：容量 64M 满电放一次 ⇒ 只扣 8M（剩 56M），不再抽干整条",
                "剩 " + GravityDeviceItem.getEnergy(full64) + " FE（旧代码这里是 0）");
        BlackHoleManager.clear();

        ItemStack short8 = device(7_999_999, GravityDeviceItem.MODE_SWALLOW);
        int before3 = BlackHoleManager.activeCount();
        fire(level, fp, fireAt, short8);
        check(GravityDeviceItem.getEnergy(short8) == 7_999_999
                        && BlackHoleManager.activeCount() == before3,
                "A3 反面自证：差 1 FE 也放不出来（闸门没被放宽成「随便放」）",
                "电 " + GravityDeviceItem.getEnergy(short8) + "；黑洞 " + BlackHoleManager.activeCount());

        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(1_000_000);
        ItemStack small = device(1_000_000, GravityDeviceItem.MODE_SWALLOW);
        int before4 = BlackHoleManager.activeCount();
        fire(level, fp, fireAt, small);
        check(GravityDeviceItem.getEnergy(small) == 0 && BlackHoleManager.activeCount() == before4 + 1,
                "A4 容量调到下限 1M 也能放（召唤费按容量封顶，否则小容量永远攒不够 8M）",
                "剩 " + GravityDeviceItem.getEnergy(small) + " FE；黑洞 +1");
        BlackHoleManager.clear();
        PotatoSTConfig.BLACK_HOLE_ONE_SHOT.set(true);
        // ⚠ 后面的坍缩模式试验都要**真 64M** 的装置（600 tick 要烧 30M）：容量停在 A4 的 1M
        //   会把装置里的电夹到 1M ⇒ 老洞跑不到一半就没电消失（B9/B10 第一版就是这么假红的）。
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(64_000_000);

        // ════════════ B 坍缩模式 ════════════
        ItemStack modeStack = device(8_000_000, GravityDeviceItem.MODE_SWALLOW);
        StringBuilder cycle = new StringBuilder();
        for (int i = 0; i < 3; i++) {
            GravityDeviceItem.toggleMode(modeStack, fp);
            cycle.append(GravityDeviceItem.getMode(modeStack)).append(i == 2 ? "" : "→");
        }
        check(cycle.toString().equals("1→2→0")
                        && GravityDeviceItem.modeKey(2).equals("message.potato_s_t.gravity.mode.collapse"),
                "B1 Shift+左键改成三档循环（吞噬→牵引→坍缩→吞噬），模式 3 用的是新语言键",
                "循环 = " + cycle + "；键 = " + GravityDeviceItem.modeKey(2));

        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(8_000_000);
        ItemStack collapse = device(8_000_000, GravityDeviceItem.MODE_COLLAPSE);
        int before5 = BlackHoleManager.activeCount();
        fire(level, fp, fireAt, collapse);
        boolean alive = !collapse.isEmpty() && collapse.getDamageValue() == 0;
        check(GravityDeviceItem.getEnergy(collapse) == 4_000_000
                        && alive && BlackHoleManager.activeCount() == before5 + 1,
                "B2 坍缩模式召唤扣 4M（不是 8M）、装置**不损坏**（它要留着每 tick 供电）",
                "剩 " + GravityDeviceItem.getEnergy(collapse) + " FE；装置完好 = " + alive);

        tickMany(10);
        check(GravityDeviceItem.getEnergy(collapse) == 3_500_000,
                "B3 每存在 1 tick 扣 50k FE（10 tick ⇒ 4M 变 3.5M）",
                "剩 " + GravityDeviceItem.getEnergy(collapse) + " FE");

        tickMany(75);   // 3.5M / 50k = 70 ⇒ 第 71 tick 交不出来
        check(BlackHoleManager.activeCount() == 0 && GravityDeviceItem.getEnergy(collapse) < 50_000,
                "B4 电耗尽 ⇒ 黑洞**当场消失**（不爆炸，用户原话「没有电力时候黑洞消失」）",
                "剩 " + GravityDeviceItem.getEnergy(collapse) + " FE；黑洞 = " + BlackHoleManager.activeCount());

        // ── 无差别吸方块 + 基岩边界 + 销毁掉落物（高空，只有我摆的东西可吃）──
        // ⚠ 这里必须把容量抬回 64M：B2 为了量"扣 4M"把容量设成了 8M，
        //   而下面这些洞要跑 200~600 tick（10M~30M 电费）⇒ 8M 的装置半路就没电、洞当场消失
        //   （B9/B10 连着两版假红就是这个原因 —— 诊断行里"老装置电量 0 / 活跃黑洞 1"是铁证）。
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(64_000_000);
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(100);
        PotatoSTConfig.BLACK_HOLE_PULL_ENTITIES.set(true);
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(false);
        Vec3 hi = new Vec3(spawn.getX() + 120.5D, spawn.getY() + HIGH, spawn.getZ() + 120.5D);
        ItemStack rich = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, rich);
        BlockPos stoneAt = BlockPos.containing(hi).offset(15, 0, 0);
        BlockPos dirtAt = BlockPos.containing(hi).offset(0, 0, 15);
        BlockPos plankAt = BlockPos.containing(hi).offset(-15, 0, 0);
        BlockPos bedrockAt = BlockPos.containing(hi).offset(0, 0, -15);
        level.setBlockAndUpdate(stoneAt, Blocks.STONE.defaultBlockState());
        level.setBlockAndUpdate(dirtAt, Blocks.DIRT.defaultBlockState());
        level.setBlockAndUpdate(plankAt, Blocks.OAK_PLANKS.defaultBlockState());
        level.setBlockAndUpdate(bedrockAt, Blocks.BEDROCK.defaultBlockState());
        ItemEntity drop = new ItemEntity(level, hi.x + 10.0D, hi.y, hi.z,
                new ItemStack(Items.DIAMOND, 3));
        level.addFreshEntity(drop);
        BlackHoleManager.spawn(level, hi, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, rich);
        tickMany(200);
        boolean stoneGone = !level.getBlockState(stoneAt).is(Blocks.STONE);
        boolean dirtGone = !level.getBlockState(dirtAt).is(Blocks.DIRT);
        boolean plankGone = !level.getBlockState(plankAt).is(Blocks.OAK_PLANKS);
        check(stoneGone && dirtGone && plankGone,
                "B5 坍缩模式**无差别**：石头 / 泥土 / 木板三种方块全被搬走（不是只吸副手那一种）",
                "石头走了=" + stoneGone + " 泥土走了=" + dirtGone + " 木板走了=" + plankGone);
        check(level.getBlockState(bedrockAt).is(Blocks.BEDROCK),
                "B6 「无差别」的边界：**基岩不动**（把地基啃穿等于坏存档）",
                "基岩还在 = " + level.getBlockState(bedrockAt).is(Blocks.BEDROCK));
        check(drop.isRemoved(),
                "B7 吸引到的**掉落物被销毁**（用户原话「吸引到的掉落物会销毁」）",
                "掉落物 isRemoved = " + drop.isRemoved());
        BlackHoleManager.clear();

        // ── 对照：普通模式只吸副手那一种 ──
        Vec3 hi2 = new Vec3(spawn.getX() - 120.5D, spawn.getY() + HIGH, spawn.getZ() + 120.5D);
        ItemStack plain = device(64_000_000, GravityDeviceItem.MODE_SWALLOW);
        fp.setItemInHand(InteractionHand.MAIN_HAND, plain);
        BlockPos stoneAt2 = BlockPos.containing(hi2).offset(15, 0, 0);
        BlockPos dirtAt2 = BlockPos.containing(hi2).offset(0, 0, 15);
        level.setBlockAndUpdate(stoneAt2, Blocks.STONE.defaultBlockState());
        level.setBlockAndUpdate(dirtAt2, Blocks.DIRT.defaultBlockState());
        BlackHoleManager.spawn(level, hi2, Blocks.STONE, fp, GravityDeviceItem.MODE_SWALLOW, plain);
        tickMany(200);
        check(!level.getBlockState(stoneAt2).is(Blocks.STONE) && level.getBlockState(dirtAt2).is(Blocks.DIRT),
                "B8 对照：**普通**模式仍然只吸副手那一种（石头走了、泥土原地不动）",
                "石头走了=" + !level.getBlockState(stoneAt2).is(Blocks.STONE)
                        + " 泥土还在=" + level.getBlockState(dirtAt2).is(Blocks.DIRT));
        BlackHoleManager.clear();

        // ── 强度/伤害随年龄涨 ──
        // ⚠ 顺序要紧：**先**开老洞跑 600 tick，**再**开新洞跑 10 tick —— 反过来的话两个洞的年龄
        //   几乎一样（600 与 610），"老的明显更猛"就无从谈起（第一版就是这么写错的）。
        // ⚠⚠ 位置也要紧：必须落在**出生点附近已加载的区块**里，否则 `getEntitiesOfClass` 根本
        //   看不到我放的那两头牛（第一版把洞开到 ±200/±260 格，B9/B10 两条全假红：速度 0、伤害 0）。
        // ⚠⚠ 位置还要**贴着出生点**：±140 格那种距离上，区块虽然是"已加载"（方块读得到、方块扫描也正常），
        //   但 `getEntitiesOfClass` 一个生物都看不到（诊断行实测「老洞可见生物 0」）⇒ 拉不动、打不到。
        //   现在两个洞都放在 ±60 格（出生点区块的实打实范围内），生物查询才有效。
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(false);
        Vec3 hFresh = new Vec3(spawn.getX() + 60.5D, spawn.getY() + HIGH, spawn.getZ() + 0.5D);
        Vec3 hOld = new Vec3(spawn.getX() - 60.5D, spawn.getY() + HIGH, spawn.getZ() + 0.5D);
        // 每个洞上方先放一块"压舱石"：把区块强行加载上（也顺便证明这一小块不会被吃掉 —— 禁采区）
        level.setBlockAndUpdate(BlockPos.containing(hFresh).offset(0, 6, 0), Blocks.DIAMOND_BLOCK.defaultBlockState());
        level.setBlockAndUpdate(BlockPos.containing(hOld).offset(0, 6, 0), Blocks.DIAMOND_BLOCK.defaultBlockState());
        ItemStack pFresh = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        ItemStack pOld = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pOld);
        BlackHoleManager.spawn(level, hOld, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pOld);
        tickMany(600);
        fp.setItemInHand(InteractionHand.MAIN_HAND, pFresh);
        BlackHoleManager.spawn(level, hFresh, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, pFresh);
        tickMany(10);

        Cow cowFresh = cow(level, hFresh.add(3.0D, 0.0D, 0.0D), 10.0F);
        Cow cowOld = cow(level, hOld.add(3.0D, 0.0D, 0.0D), 10.0F);
        if (cowFresh == null || cowOld == null) {
            check(false, "B9 生成两头牛（测强度随年龄涨）", "EntityType.COW.create 返回 null");
        } else {
            BlackHoleManager.tick();
            double freshV = speedOf(cowFresh);
            double oldV = speedOf(cowOld);
            check(oldV > freshV * 1.8D,
                    "B9 吸引强度随年龄涨：同样距离，老黑洞给牛的速度明显更大",
                    "新鲜 " + String.format("%.3f", freshV) + " ｜ 老的 " + String.format("%.3f", oldV)
                            + " ｜ 诊断：活跃黑洞 " + BlackHoleManager.activeCount()
                            + "、老洞区块已加载 " + level.isLoaded(BlockPos.containing(hOld))
                            + "、老洞牛还在 " + !cowOld.isRemoved()
                            + "、老装置电量 " + GravityDeviceItem.getEnergy(pOld)
                            + "、老洞牛距离 " + String.format("%.2f", cowOld.position().distanceTo(hOld))
                            + "、新洞牛距离 " + String.format("%.2f", cowFresh.position().distanceTo(hFresh))
                            + "、老洞可见生物 " + level.getEntitiesOfClass(
                                    net.minecraft.world.entity.LivingEntity.class,
                                    new net.minecraft.world.phys.AABB(hOld, hOld).inflate(48.0D)).size());
            cowFresh.discard();
            cowOld.discard();
            BlackHoleManager.clear();
        }

        // ── 伤害随年龄涨（虚空伤害 10 tick 一跳）── 同样是"先老后新 + 近处"
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(true);
        Vec3 hF2 = new Vec3(spawn.getX() + 0.5D, spawn.getY() + HIGH, spawn.getZ() + 60.5D);
        Vec3 hO2 = new Vec3(spawn.getX() + 0.5D, spawn.getY() + HIGH, spawn.getZ() - 60.5D);
        level.setBlockAndUpdate(BlockPos.containing(hF2).offset(0, 6, 0), Blocks.DIAMOND_BLOCK.defaultBlockState());
        level.setBlockAndUpdate(BlockPos.containing(hO2).offset(0, 6, 0), Blocks.DIAMOND_BLOCK.defaultBlockState());
        ItemStack qFresh = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        ItemStack qOld = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, qOld);
        BlackHoleManager.spawn(level, hO2, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, qOld);
        tickMany(600);
        fp.setItemInHand(InteractionHand.MAIN_HAND, qFresh);
        BlackHoleManager.spawn(level, hF2, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, qFresh);
        tickMany(10);
        Cow hurtFresh = cow(level, hF2.add(3.0D, 0.0D, 0.0D), 10.0F);
        Cow hurtOld = cow(level, hO2.add(3.0D, 0.0D, 0.0D), 10.0F);
        if (hurtFresh == null || hurtOld == null) {
            check(false, "B10 生成两头牛（测伤害随年龄涨）", "null");
        } else {
            float hpFresh0 = hurtFresh.getHealth();
            float hpOld0 = hurtOld.getHealth();
            tickMany(10);   // 两只洞的年龄差 ~600，都在 10 的倍数上 ⇒ 各挨一跳
            float dFresh = hpFresh0 - hurtFresh.getHealth();
            float dOld = hpOld0 - hurtOld.getHealth();
            check(dOld > dFresh * 1.5F && dFresh > 0.0F,
                    "B10 伤害随年龄涨：同一距离，老黑洞这一跳明显更疼",
                    "新鲜 -" + String.format("%.2f", dFresh) + " ｜ 老的 -" + String.format("%.2f", dOld));
            hurtFresh.discard();
            hurtOld.discard();
            BlackHoleManager.clear();
        }

        // ════════════ C 2 分钟硬上限 + 30 威力爆炸 ════════════
        PotatoSTConfig.BLACK_HOLE_LIFETIME_SECONDS.set(120);   // 配置上限 = 正好 2400 tick
        PotatoSTConfig.BLACK_HOLE_PULL_ENTITIES.set(false);
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(false);
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(100);
        Vec3 cap = new Vec3(spawn.getX() + 0.5D, spawn.getY() + HIGH + 40, spawn.getZ() + 0.5D);
        BlockPos capPos = BlockPos.containing(cap);
        // 121 块石头放在 **±16~26**（禁采区 12 之外）⇒ 前几 tick 就把 100 块的搬运预算用光，
        // 后面 2300 多 tick 的 pullBlocks 变成"一眼就返回"，硬上限那一跑才跑得起。
        for (int dx = 16; dx <= 26; dx++) {
            for (int dz = -5; dz <= 5; dz++) {
                level.setBlockAndUpdate(capPos.offset(dx, 0, dz), Blocks.STONE.defaultBlockState());
            }
        }
        BlockPos marker = capPos.offset(0, 5, 0);   // 禁采区内 ⇒ 黑洞自己不会吃它，只有爆炸能毁掉
        level.setBlockAndUpdate(marker, Blocks.DIAMOND_BLOCK.defaultBlockState());
        Cow blast = cow(level, cap.add(5.0D, 0.0D, 0.0D), 20.0F);
        float blastHp0 = blast == null ? 0.0F : blast.getHealth();   // ⚠ setHealth 会被夹到最大血量（牛 10）
        ItemStack longLife = device(64_000_000, GravityDeviceItem.MODE_SWALLOW);
        fp.setItemInHand(InteractionHand.MAIN_HAND, longLife);
        BlackHoleManager.spawn(level, cap, Blocks.STONE, fp, GravityDeviceItem.MODE_SWALLOW, longLife);
        long t0 = System.currentTimeMillis();
        tickMany(BlackHoleManager.HARD_CAP_TICKS);
        long ms = System.currentTimeMillis() - t0;
        check(BlackHoleManager.activeCount() == 0,
                "C1 存在满 2 分钟（2400 tick）⇒ 黑洞销毁（用户原话「超过2分钟也会销毁」）",
                "黑洞 = " + BlackHoleManager.activeCount() + "；跑了 " + ms + " ms");
        boolean markerGone = !level.getBlockState(marker).is(Blocks.DIAMOND_BLOCK);
        boolean cowHurt = blast != null && (blast.isRemoved() || blast.getHealth() < blastHp0);
        check(markerGone && cowHurt,
                "C2 那一下真是**30 威力爆炸**（不是特效）：标记方块被炸掉 + 5 格外的牛挨了伤害",
                "标记没了=" + markerGone + " ｜ 牛挨打=" + cowHurt
                        + (blast == null ? "" : "（血量 " + blastHp0 + " → " + blast.getHealth() + "）"));

        // 收尾：把配置改回出厂值
        PotatoSTConfig.BLACK_HOLE_LIFETIME_SECONDS.set(20);
        PotatoSTConfig.BLACK_HOLE_MAX_BLOCKS.set(1500);
        PotatoSTConfig.BLACK_HOLE_PULL_ENTITIES.set(true);
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(true);
        PotatoSTConfig.GRAVITY_CAPACITY_FE.set(8_000_000);
    }
}
