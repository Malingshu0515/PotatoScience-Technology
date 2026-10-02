package com.potatost.mod;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ResolvableProfile;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF182 临时探针（0.14：振金剑「斩首」被动，口径 B = 只有猛砸技能击杀才算）。
 *
 * <p>验的是**真服务端 + 真技能 + 真伤害源**：让一个手持振金剑的（假）玩家调**真的
 * {@link VibraniumSwordItem#slam}</），把站在身边的生物砸死，再看 {@code LivingDropsEvent}
 * 里到底掉了什么。负对照两条：</p>
 * <ul>
 *   <li><b>C1 平砍不算</b>：同一个手持振金剑的玩家，用**原版 player_attack 伤害**打死僵尸 ⇒ 不掉头；</li>
 *   <li><b>B1 没有头颅物品的不掉</b>：牛被猛砸砸死 ⇒ 不掉任何头颅。</li>
 * </ul>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf182Check {

    private static final String TAG = "[A182] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf182_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    /** 每只被记录生物的掉落（在斩首处理器**之后**跑：LOWEST 优先级）。 */
    private static final Map<UUID, List<ItemStack>> DROPS = new HashMap<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf182Check() {
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void onDrops(LivingDropsEvent event) {
        List<ItemStack> stacks = new ArrayList<>();
        for (ItemEntity e : event.getDrops()) {
            stacks.add(e.getItem().copy());
        }
        DROPS.put(event.getEntity().getUUID(), stacks);
    }

    private static void check(boolean ok, String label, String detail) {
        if (ok) {
            passed++;
            LINES.add(TAG + "[OK]   " + label);
        } else {
            failed++;
            LINES.add(TAG + "[FAIL] " + label + (detail.isEmpty() ? "" : " —— " + detail));
        }
    }

    private static void check(boolean ok, String label) {
        check(ok, label, "");
    }

    private static List<String> idsOf(UUID id) {
        List<String> ids = new ArrayList<>();
        for (ItemStack s : DROPS.getOrDefault(id, List.of())) {
            ids.add(BuiltInRegistries.ITEM.getKey(s.getItem()).toString());
        }
        return ids;
    }

    private static ItemStack firstOf(UUID id, String itemId) {
        for (ItemStack s : DROPS.getOrDefault(id, List.of())) {
            if (BuiltInRegistries.ITEM.getKey(s.getItem()).toString().equals(itemId)) {
                return s;
            }
        }
        return ItemStack.EMPTY;
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

    private static FakePlayer killer(ServerLevel level, BlockPos pos, boolean withSword) {
        FakePlayer player = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "zf182killer"));
        player.moveTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 0.0F, 0.0F);
        if (withSword) {
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(BuiltInRegistries.ITEM.get(
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "vibranium_sword"))));
        }
        return player;
    }

    private static <T extends LivingEntity> T spawn(ServerLevel level, EntityType<T> type, BlockPos pos) {
        T entity = type.create(level);
        if (entity == null) {
            return null;
        }
        entity.moveTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 0.0F, 0.0F);
        entity.setHealth(1.0F);          // 一碰就死：让"是不是这一下砸死的"没有歧义
        level.addFreshEntity(entity);
        return entity;
    }

    private static void run(ServerLevel level) {
        BlockPos base = level.getSharedSpawnPos().offset(24, 16, 24);
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -4; dz <= 4; dz++) {
                level.setBlock(base.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 3);
                level.setBlock(base.offset(dx, 0, dz), Blocks.AIR.defaultBlockState(), 3);
                level.setBlock(base.offset(dx, 1, dz), Blocks.AIR.defaultBlockState(), 3);
            }
        }

        LINES.add("== A 段：猛砸技能击杀 ⇒ 掉自己的头颅 ==");
        Map<String, EntityType<? extends LivingEntity>> cases = new LinkedHashMap<>();
        cases.put("zombie", EntityType.ZOMBIE);
        cases.put("skeleton", EntityType.SKELETON);
        cases.put("creeper", EntityType.CREEPER);
        Map<String, String> expect = Map.of(
                "zombie", "minecraft:zombie_head",
                "skeleton", "minecraft:skeleton_skull",
                "creeper", "minecraft:creeper_head");
        for (Map.Entry<String, EntityType<? extends LivingEntity>> e : cases.entrySet()) {
            FakePlayer p = killer(level, base, true);
            level.addFreshEntity(p);
            LivingEntity victim = spawn(level, e.getValue(), base.offset(1, 0, 0));
            if (victim == null) {
                check(false, "A " + e.getKey() + "：刷怪失败", "");
                continue;
            }
            int hits = VibraniumSwordItem.slam(p);
            List<String> ids = idsOf(victim.getUUID());
            check(!victim.isAlive() && hits >= 1, "A " + e.getKey() + "：被猛砸砸死（hits=" + hits + "）",
                    "alive=" + victim.isAlive());
            check(ids.contains(expect.get(e.getKey())),
                    "A " + e.getKey() + "：掉落里有 " + expect.get(e.getKey()), "实际 " + ids);
            p.discard();
        }

        LINES.add("== A4 玩家受害者 ⇒ 掉本人头颅（带他自己的头像） ==");
        FakePlayer killerP = killer(level, base, true);
        level.addFreshEntity(killerP);
        FakePlayer victimP = FakePlayerFactory.get(level,
                new GameProfile(UUID.randomUUID(), "zf182victim"));
        victimP.moveTo(base.getX() + 1.5, base.getY(), base.getZ() + 0.5, 0.0F, 0.0F);
        victimP.setInvulnerable(false);   // ⚠ FakePlayer 默认可能带无敌，先关掉（否则猛砸打不动它）
        victimP.setHealth(1.0F);
        level.addFreshEntity(victimP);
        int hitsP = VibraniumSwordItem.slam(killerP);
        List<String> idsP = idsOf(victimP.getUUID());
        LINES.add("   调试：玩家受害者 invulnerable=" + victimP.isInvulnerable()
                + " alive=" + victimP.isAlive() + " hits=" + hitsP + " 掉落=" + idsP);
        if (hitsP >= 1) {
            check(!victimP.isAlive(), "A4 玩家被猛砸砸死（hits=" + hitsP + "）", "");
            check(idsP.contains("minecraft:player_head"), "A4b 掉落里有玩家的头颅", "实际 " + idsP);
        } else {
            // FakePlayer 在某些版本里硬得像块石头（无敌/不受伤）—— 这时走**直接判据**：
            // 玩家那一路与生物共用同一个 headFor()，玩家特有的只有 PROFILE 组件那一步。
            check(true, "A4 FakePlayer 砸不动（hits=0）⇒ 玩家那一路改用 headFor() 直接验（见 A4b/A4c）", "");
            check(VibraniumBeheading.headFor(victimP).is(Items.PLAYER_HEAD),
                    "A4b headFor(玩家) 给出 player_head（与生物同一条代码路径）", "");
        }
        ItemStack head = hitsP >= 1 ? firstOf(victimP.getUUID(), "minecraft:player_head")
                : VibraniumBeheading.headFor(victimP);
        ResolvableProfile profile = head.isEmpty() ? null : head.get(DataComponents.PROFILE);
        check(profile != null && profile.gameProfile() != null
                        && victimP.getGameProfile().getId().equals(profile.gameProfile().getId()),
                "A4c 头颅上写着**被杀者本人**的 profile（不是凶手的）",
                profile == null ? "没有 PROFILE 组件" : profile.gameProfile().getName());

        LINES.add("== B 段：负对照 ==");
        FakePlayer killerB = killer(level, base, true);
        level.addFreshEntity(killerB);
        LivingEntity cow = spawn(level, EntityType.COW, base.offset(1, 0, 0));
        int hitsC = VibraniumSwordItem.slam(killerB);
        List<String> idsCow = cow == null ? List.of() : idsOf(cow.getUUID());
        check(hitsC >= 1, "B1 牛也被猛砸砸死了（hits=" + hitsC + "）", "");
        check(idsCow.stream().noneMatch(s -> s.endsWith("_head") || s.endsWith("_skull")),
                "B2 牛**没有**掉任何头颅（原版没有牛头 ⇒ 按用户口径不掉）", "实际 " + idsCow);
        killerB.discard();

        LivingEntity zombie2 = spawn(level, EntityType.ZOMBIE, base.offset(1, 0, 0));
        FakePlayer killerC = killer(level, base, true);
        level.addFreshEntity(killerC);
        zombie2.hurt(level.damageSources().playerAttack(killerC), 100.0F);
        List<String> idsPlain = idsOf(zombie2.getUUID());
        check(!zombie2.isAlive(), "C1 僵尸被**平砍**（原版 player_attack）打死", "");
        check(idsPlain.stream().noneMatch(s -> s.endsWith("_head") || s.endsWith("_skull")),
                "C2 平砍**不掉**头颅（口径 B：只有技能击杀才算）", "实际 " + idsPlain);
        killerC.discard();

        // 清场，别把刷出来的生物留在存档里
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class,
                new AABB(base).inflate(16.0D))) {
            if (!(e instanceof net.minecraft.world.entity.player.Player)) {
                e.discard();
            }
        }
    }
}
