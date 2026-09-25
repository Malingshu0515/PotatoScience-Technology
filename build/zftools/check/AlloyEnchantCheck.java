package com.potatost.mod;

import java.util.List;
import java.util.stream.Stream;

import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.EnchantmentTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.EnchantmentInstance;
import net.minecraft.world.item.enchantment.Enchantments;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF67 临时文件，验证完必须删）</b>：验用户报的那个问题 ——
 * <b>「附魔台不给钛合金工具附魔」</b>。
 *
 * <p><b>根因（读原版代码定的）</b>：附魔台挑附魔时用的判据<b>不是</b>附魔能力，而是
 * {@code EnchantmentHelper.getAvailableEnchantmentResults()} 里那一句
 * {@code possibleEnchantments.filter(stack::isPrimaryItemFor)} —— 也就是"这个物品在不在
 * 这条附魔的 {@code primary_items} / {@code supported_items} 标签里"。原版那几张标签是
 * {@code #minecraft:swords} / {@code #minecraft:pickaxes}（再串到
 * {@code enchantable/sword}、{@code enchantable/mining}、{@code enchantable/durability} …），
 * 而 ZF66 那两把工具<b>一个都没挂</b> ⇒ 附魔能力再高也挑不出任何一条附魔。</p>
 *
 * <p>所以要验三层：① 原版功能标签挂上了；② <b>逐条附魔</b>用原版同一个判据
 * （{@code stack.isPrimaryItemFor(...)}）问得出"能附"；③ 附魔台那条路真的能给出候选
 * （花费 &gt; 0 且 30 级时候选非空），并拿<b>原版钻石剑/钻石镐当对照</b> —— 对照不过，
 * 说明是我的判据写错了，而不是物品坏了。</p>
 */
public final class AlloyEnchantCheck {

    private static final String TAG = "[ENCH] ";
    private static boolean registered;

    private AlloyEnchantCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloyEnchantCheck.class);
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
        var enchantments = event.getServer().registryAccess().lookupOrThrow(Registries.ENCHANTMENT);

        ItemStack sword = new ItemStack(ModItems.TITANIUM_ALLOY_SWORD.get());
        ItemStack pick = new ItemStack(ModItems.TITANIUM_ALLOY_PICKAXE.get());

        // ---------- ① 原版功能标签（不是 c: 兼容标签，是"能不能附魔"的硬要求）----------
        System.out.println(TAG + "(1) vanilla item tags");
        failed += check("sword in #minecraft:swords", sword.is(ItemTags.SWORDS));
        failed += check("pickaxe in #minecraft:pickaxes", pick.is(ItemTags.PICKAXES));
        failed += check("sword in #minecraft:enchantable/sword", sword.is(ItemTags.SWORD_ENCHANTABLE));
        failed += check("sword in #minecraft:enchantable/sharp_weapon", sword.is(ItemTags.SHARP_WEAPON_ENCHANTABLE));
        failed += check("sword in #minecraft:enchantable/fire_aspect", sword.is(ItemTags.FIRE_ASPECT_ENCHANTABLE));
        failed += check("pickaxe in #minecraft:enchantable/mining", pick.is(ItemTags.MINING_ENCHANTABLE));
        failed += check("pickaxe in #minecraft:enchantable/mining_loot", pick.is(ItemTags.MINING_LOOT_ENCHANTABLE));
        failed += check("both in #minecraft:enchantable/durability (unbreaking/mending)",
                sword.is(ItemTags.DURABILITY_ENCHANTABLE) && pick.is(ItemTags.DURABILITY_ENCHANTABLE));
        failed += check("both in #minecraft:enchantable/vanishing (curse of vanishing)",
                sword.is(ItemTags.VANISHING_ENCHANTABLE) && pick.is(ItemTags.VANISHING_ENCHANTABLE));

        // ---------- ② 逐条附魔：用原版同一个判据问"这个物品能不能吃到它" ----------
        System.out.println(TAG + "(2) per-enchantment support (the real criterion)");
        String[][] swordWant = {
                {"sharpness", "锋利"}, {"smite", "亡灵杀手"}, {"bane_of_arthropods", "节肢杀手"},
                {"knockback", "击退"}, {"fire_aspect", "火焰附加"}, {"looting", "抢夺"},
                {"sweeping_edge", "横扫之刃"}, {"unbreaking", "耐久"}, {"mending", "经验修补"},
                {"vanishing_curse", "消失诅咒"},
        };
        String[][] pickWant = {
                {"efficiency", "效率"}, {"fortune", "时运"}, {"silk_touch", "精准采集"},
                {"unbreaking", "耐久"}, {"mending", "经验修补"}, {"vanishing_curse", "消失诅咒"},
        };
        for (String[] e : swordWant) {
            Holder<Enchantment> h = holder(enchantments, e[0]);
            boolean sup = sword.isPrimaryItemFor(h);
            failed += check("sword can take " + e[0] + " (" + e[1] + ")", sup);
        }
        for (String[] e : pickWant) {
            Holder<Enchantment> h = holder(enchantments, e[0]);
            boolean sup = pick.isPrimaryItemFor(h);
            failed += check("pickaxe can take " + e[0] + " (" + e[1] + ")", sup);
        }
        // 反向断言：判据得真的在筛东西，不是"什么都行"
        failed += check("(reverse) sword can NOT take efficiency",
                !sword.isPrimaryItemFor(holder(enchantments, "efficiency")));
        failed += check("(reverse) pickaxe can NOT take sharpness",
                !pick.isPrimaryItemFor(holder(enchantments, "sharpness")));

        // ---------- ③ 附魔台那条路：花费 > 0 且 30 级时候选非空 ----------
        System.out.println(TAG + "(3) the enchanting table path");
        HolderSet.Named<Enchantment> inTable = enchantments.getOrThrow(EnchantmentTags.IN_ENCHANTING_TABLE);
        failed += tablePath(sword, inTable, "titanium alloy sword");
        failed += tablePath(pick, inTable, "titanium alloy pickaxe");

        // ---------- ④ 原版对照：钻石剑/镐必须表现一模一样 ----------
        System.out.println(TAG + "(4) vanilla controls (if these fail, my criterion is wrong)");
        failed += tablePath(new ItemStack(Items.DIAMOND_SWORD), inTable, "vanilla diamond sword");
        failed += tablePath(new ItemStack(Items.DIAMOND_PICKAXE), inTable, "vanilla diamond pickaxe");

        return failed;
    }

    private static int tablePath(ItemStack stack, HolderSet.Named<Enchantment> inTable, String who) {
        int failed = 0;
        RandomSource random = RandomSource.create(1234L);
        boolean enchantable = stack.isEnchantable();
        int cost = EnchantmentHelper.getEnchantmentCost(random, 2, 15, stack);
        Stream<Holder<Enchantment>> possible = inTable.stream();
        List<EnchantmentInstance> got = EnchantmentHelper.getAvailableEnchantmentResults(30, stack, possible);
        System.out.println(TAG + "  " + who + ": enchantable=" + enchantable + " enchantmentValue="
                + stack.getEnchantmentValue() + " cost(slot3,15 shelves)=" + cost
                + " candidates@30=" + got.size());
        failed += check(who + ": isEnchantable()", enchantable);
        failed += check(who + ": enchantment value > 0", stack.getEnchantmentValue() > 0);
        failed += check(who + ": the table would charge > 0 levels", cost > 0);
        failed += check(who + ": the table offers at least one enchantment", !got.isEmpty());
        return failed;
    }

    private static Holder<Enchantment> holder(net.minecraft.core.HolderLookup.RegistryLookup<Enchantment> reg, String path) {
        ResourceKey<Enchantment> key = ResourceKey.create(Registries.ENCHANTMENT,
                net.minecraft.resources.ResourceLocation.withDefaultNamespace(path));
        return reg.getOrThrow(key);
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
