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
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ZF184 临时探针（0.14：猛砸伤害改成「玩家当前攻击伤害 + 逐目标附魔加成」）。
 *
 * <p>用户原话：「**振金剑技能伤害n改一下 改成目前玩家的伤害（之前是基础伤害 不包括手持武器）
 * 并且吃附魔例如亡灵杀手 锋利的加成**」。</p>
 *
 * <p>验法：把受害者做成一击打不死（给 MAX_HEALTH 加一个大 modifier + 回满血），
 * 用**血量差**量出这一次猛砸到底打了多少 —— 这样不用相信公式，量的是真打出来的数。</p>
 * <ul>
 *   <li><b>A</b> 手持振金剑 vs 空手：差值应当明显更大（武器那一份进来了）；</li>
 *   <li><b>B</b> 亡灵杀手 V 的振金剑打**僵尸**（亡灵）：比不带附魔更疼（吃附魔）；</li>
 *   <li><b>C</b> 同一把亡灵杀手 V 的剑打**牛**（非亡灵）：与不带附魔**一样**（逐目标、亡灵杀手只对亡灵生效）。</li>
 * </ul>
 */
@EventBusSubscriber(modid = PotatoST.MODID)
public final class Zf184Check {

    private static final String TAG = "[A184] ";
    private static final Path REPORT = Path.of("E:\\PotatoST\\build\\zftools\\_zf184_probe_utf8.txt");
    private static final List<String> LINES = new ArrayList<>();
    private static int passed = 0;
    private static int failed = 0;

    private Zf184Check() {
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

    private static FakePlayer player(ServerLevel level, BlockPos pos, ItemStack hand) {
        FakePlayer p = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "zf184"));
        p.moveTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 0.0F, 0.0F);
        p.setItemInHand(InteractionHand.MAIN_HAND, hand);
        level.addFreshEntity(p);
        return p;
    }

    /** 刷一只血厚的受害者（一击打不死，好用血量差量伤害）。 */
    private static <T extends LivingEntity> T tank(ServerLevel level, EntityType<T> type, BlockPos pos) {
        T e = type.create(level);
        if (e == null) {
            return null;
        }
        e.moveTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 0.0F, 0.0F);
        AttributeInstance max = e.getAttribute(Attributes.MAX_HEALTH);
        if (max != null) {
            max.addTransientModifier(new AttributeModifier(
                    ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "zf184_tank"),
                    500.0D, AttributeModifier.Operation.ADD_VALUE));
            e.setHealth(e.getMaxHealth());
        }
        level.addFreshEntity(e);
        return e;
    }

    private static double slamDamage(ServerLevel level, BlockPos base, ItemStack hand,
                                     EntityType<? extends LivingEntity> type) {
        return slamDamage(level, base, hand, type, 0.0D);
    }

    /**
     * @param attackBonus 给凶手额外加的攻击力 —— 用来验「猛砸吃的是**玩家当前攻击伤害**」这条判据本身。
     *                    ⚠ 为什么不用「手持武器」来验：凶手是 {@code FakePlayer}，**它不 tick**，
     *                    而原版把武器的属性修饰符挂进属性表那一步在
     *                    {@code LivingEntity.detectEquipmentUpdates()}（**private**，探针调不到）里、由 tick 触发
     *                    ⇒ 假玩家手里拿着剑，属性表里也没有那 +9。真实玩家身上这份由原版装备逻辑给，
     *                    所以这里手动加等价的一份，验的是「伤害基数 = 属性值里的当前攻击伤害」。
     */
    private static double slamDamage(ServerLevel level, BlockPos base, ItemStack hand,
                                     EntityType<? extends LivingEntity> type, double attackBonus) {
        FakePlayer p = player(level, base, hand);
        if (attackBonus != 0.0D) {
            AttributeInstance atk = p.getAttribute(Attributes.ATTACK_DAMAGE);
            if (atk != null) {
                atk.addTransientModifier(new AttributeModifier(
                        ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "zf184_bonus"),
                        attackBonus, AttributeModifier.Operation.ADD_VALUE));
            }
        }
        LivingEntity victim = tank(level, type, base.offset(1, 0, 0));
        if (victim == null) {
            return -1.0D;
        }
        float before = victim.getHealth();
        int hits = VibraniumSwordItem.slam(p);
        float after = victim.getHealth();
        p.discard();
        victim.discard();
        return hits >= 1 ? (before - after) : -1.0D;
    }

    private static ItemStack sword(ServerLevel level, String enchant, int lvl) {
        ItemStack stack = new ItemStack(net.minecraft.core.registries.BuiltInRegistries.ITEM.get(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, "vibranium_sword")));
        if (enchant != null) {
            Holder<Enchantment> holder = level.registryAccess().registryOrThrow(Registries.ENCHANTMENT)
                    .getHolderOrThrow(net.minecraft.resources.ResourceKey.create(Registries.ENCHANTMENT,
                            ResourceLocation.withDefaultNamespace(enchant)));
            stack.enchant(holder, lvl);
        }
        return stack;
    }

    private static void run(ServerLevel level) {
        BlockPos base = level.getSharedSpawnPos().offset(30, 16, 30);
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                level.setBlock(base.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 3);
                level.setBlock(base.offset(dx, 0, dz), Blocks.AIR.defaultBlockState(), 3);
                level.setBlock(base.offset(dx, 1, dz), Blocks.AIR.defaultBlockState(), 3);
            }
        }

        double bare = slamDamage(level, base, ItemStack.EMPTY, EntityType.ZOMBIE);
        double plain = slamDamage(level, base, sword(level, null, 0), EntityType.ZOMBIE);
        double smite = slamDamage(level, base, sword(level, "smite", 5), EntityType.ZOMBIE);
        double smiteCow = slamDamage(level, base, sword(level, "smite", 5), EntityType.COW);
        double plainCow = slamDamage(level, base, sword(level, null, 0), EntityType.COW);
        double sharpCow = slamDamage(level, base, sword(level, "sharpness", 5), EntityType.COW);
        // A1 用「攻击力 +9」来验判据本身（见 slamDamage 的 attackBonus 注释：假玩家不 tick，
        // 手里拿剑也不会把武器那份挂进属性表）
        double plus9 = slamDamage(level, base, ItemStack.EMPTY, EntityType.ZOMBIE, 9.0D);
        LINES.add("   实测伤害：空手=" + bare + "（僵尸）｜空手+9攻击力=" + plus9 + "（僵尸）｜振金剑="
                + plain + "（僵尸）｜亡灵杀手V=" + smite
                + "（僵尸）｜亡灵杀手V=" + smiteCow + "（牛）｜无附魔=" + plainCow + "（牛）｜锋利V="
                + sharpCow + "（牛）");

        check(bare > 0 && plus9 > 0, "A0 两次猛砸都真的打中了（血量差能量出来）",
                "空手=" + bare + " 空手+9=" + plus9);
        check(plus9 > bare + 8.0D,
                "A1 攻击力 +9 ⇒ 猛砸伤害跟着 +9 ⇒ 基数吃的是**玩家当前攻击伤害**"
                        + "（真实玩家身上这一份 = 基础 + 玩家加成 + **手持武器**）",
                "空手=" + bare + " 空手+9=" + plus9);
        check(plain == bare, "A2 佐证：假玩家手里拿剑但属性表没变 ⇒ 伤害与空手相同"
                + "（说明武器那份**只走属性表**，不走别的隐式通道）",
                "空手=" + bare + " 剑=" + plain);
        check(smite > plain + 3.0D, "B1 亡灵杀手 V 打**僵尸**（亡灵）明显更疼 ⇒ 技能吃附魔",
                "无附魔=" + plain + " 亡灵杀手V=" + smite);
        check(Math.abs(smiteCow - plainCow) < 0.01D,
                "C1 同一把亡灵杀手 V 打**牛**（非亡灵）伤害**不变** ⇒ 加成是按目标逐个算的",
                "牛：无附魔=" + plainCow + " 亡灵杀手V=" + smiteCow);
        check(sharpCow > plainCow + 1.0D, "C2 锋利 V 打牛更疼 ⇒ 通吃的附魔也生效（逐目标那一步没写反）",
                "牛：无附魔=" + plainCow + " 锋利V=" + sharpCow);

        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class,
                new net.minecraft.world.phys.AABB(base).inflate(24.0D))) {
            if (!(e instanceof net.minecraft.world.entity.player.Player)) {
                e.discard();
            }
        }
    }
}
