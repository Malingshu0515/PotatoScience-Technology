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
 * <p><b>0.14 ZF192 的两处判据修法</b>（都是"探针环境"的坑，不是被测代码的坑）：</p>
 * <ol>
 *   <li><b>凡是要"看到实体"的判据，洞必须开在**出生点区块**里</b>（出生点那几块是 START 票，
 *       实体表一定是加载好的）。探针跑在 {@code ServerStartedEvent} 里，**服务端一 tick 都没跑**，
 *       别的区块可能只加载到"方块读得到"那一档 ⇒ {@code addFreshEntity} 明明返回 true，
 *       实体却还在 pending 里（诊断实测「老牛在实体表 false、新牛在实体表 true」）
 *       ⇒ 黑洞看不到牛 = 速度/伤害恒 0 = 假红。</li>
 *   <li><b>强度/伤害随年龄涨，用**同一个洞量两次**</b>（先在新鲜时量、跑 600 tick 再量），
 *       不要"一老一新两个洞"—— 两个洞就要求两块区块的实体表都可用，稳定性差一倍。</li>
 * </ol>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf190Check {

    private static final String TAG = "[A190] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf190_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;
    /** 方块类试验开这么高（离地 &gt; 40 格 ⇒ 扫描范围够不到地形，只有我摆的东西可吃）。 */
    private static final int HIGH = 100;
    /** 实体类试验的高度：出生点正上方 60 格（同一根区块列 ⇒ 实体表一定加载着，且够不到地形）。 */
    private static final int ENTITY_HIGH = 60;

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
        System.out.println("[PotatoST] Zf190Check START");
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

        // ── 方块类：无差别吸 + 基岩边界（高空，只有我摆的东西可吃）──
        // ⚠ 这一片只放**方块**判据；"掉落物销毁"与"强度/伤害随年龄涨"要看到实体 ⇒ 挪到出生点区块（见 ENTITY_HIGH）。
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
        BlackHoleManager.clear();

        // ── 对照：普通模式只吸副手那一种（纯方块判据）──
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

        // ── B7 + B9/B10：**同一个洞、出生点正上方**（实体表一定加载着）──
        Vec3 h1 = new Vec3(spawn.getX() + 0.5D, spawn.getY() + ENTITY_HIGH, spawn.getZ() + 0.5D);
        ItemStack p1 = device(64_000_000, GravityDeviceItem.MODE_COLLAPSE);
        fp.setItemInHand(InteractionHand.MAIN_HAND, p1);
        BlackHoleManager.spawn(level, h1, Blocks.STONE, fp, GravityDeviceItem.MODE_COLLAPSE, p1);

        ItemEntity drop = new ItemEntity(level, h1.x + 10.0D, h1.y, h1.z, new ItemStack(Items.DIAMOND, 3));
        level.addFreshEntity(drop);
        tickMany(3);
        check(drop.isRemoved(),
                "B7 吸引到的**掉落物被销毁**（用户原话「吸引到的掉落物会销毁」；在出生点区块里量）",
                "掉落物 isRemoved = " + drop.isRemoved());

        // 新鲜组：先量速度（关伤害，牛别死），再量一跳伤害
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(false);
        tickMany(7);                                   // 洞年龄 ≈ 10
        Cow vFresh = cow(level, h1.add(3.0D, 0.0D, 0.0D), 10.0F);
        BlackHoleManager.tick();
        double freshV = speedOf(vFresh);
        if (vFresh != null) {
            vFresh.discard();
        }
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(true);
        Cow dFresh = cow(level, h1.add(3.0D, 0.0D, 0.0D), 10.0F);
        float hpFresh0 = dFresh == null ? 0.0F : dFresh.getHealth();
        tickMany(10);                                  // 年龄 20 那一下挨一跳
        float dmgFresh = hpFresh0 - (dFresh == null ? 0.0F : dFresh.getHealth());
        if (dFresh != null) {
            dFresh.discard();
        }

        // 变老：600 tick（电费 30M，装置 64M 够用）
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(false);
        tickMany(600);
        Cow vOld = cow(level, h1.add(3.0D, 0.0D, 0.0D), 10.0F);
        BlackHoleManager.tick();
        double oldV = speedOf(vOld);
        if (vOld != null) {
            vOld.discard();
        }
        PotatoSTConfig.BLACK_HOLE_VOID_DAMAGE.set(true);
        Cow dOld = cow(level, h1.add(3.0D, 0.0D, 0.0D), 10.0F);
        float hpOld0 = dOld == null ? 0.0F : dOld.getHealth();
        tickMany(10);                                  // 年龄 630 那一下挨一跳
        float dmgOld = hpOld0 - (dOld == null ? 0.0F : dOld.getHealth());
        if (dOld != null) {
            dOld.discard();
        }

        check(oldV > freshV * 1.8D,
                "B9 吸引强度随年龄涨（**同一个洞**：新鲜 vs 600 tick 后，同距离）",
                "新鲜 " + String.format("%.3f", freshV) + " ｜ 老的 " + String.format("%.3f", oldV)
                        + " ｜ 装置电量 " + GravityDeviceItem.getEnergy(p1));
        check(dmgOld > dmgFresh * 1.5F && dmgFresh > 0.0F,
                "B10 伤害随年龄涨（同一个洞：年龄 20 一跳 vs 年龄 630 一跳）",
                "新鲜 -" + String.format("%.2f", dmgFresh) + " ｜ 老的 -" + String.format("%.2f", dmgOld));
        BlackHoleManager.clear();

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
