package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.PickaxeItem;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TieredItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/**
 * ⚠⚠ <b>诊断工具（ZF66 临时文件，验证完必须删）</b>：验钛合金剑 / 钛合金镐。
 *
 * <p><b>用户给的数（原话）</b>：「剑；耐久2048点 伤害6.5（附魔权重如果能改的话比金高一点就行）
 * 镐；耐久4219点 伤害4 挖掘等级下界合金（附魔权重同理）」「配方按照原版的来 锭换成轻质钛合金就行」。</p>
 *
 * <p><b>"伤害 6.5 / 4" 到底是哪个数</b>：游戏里显示的是<b>总攻击伤害</b>（原版钻石剑 7、铁剑 6 那个数）
 * ＝ 玩家基础 1 ＋ 物品加成。所以这里量的是 {@code 基础 + 物品的 ATTACK_DAMAGE 加成}，
 * 期望值写成字面量 6.5 / 4.0（§4.27：不从被测常量抄）。</p>
 *
 * <p><b>"挖掘等级下界合金"怎么量</b>：1.21 起等级就是一张"挖不动的方块"标签
 * （{@code Tier.getIncorrectBlocksForDrops()}）。所以：① 结构上必须等于
 * {@code BlockTags.INCORRECT_FOR_NETHERITE_TOOL}（且<b>不等于</b>钻石那张）；
 * ② 行为上要能挖黑曜石与古代残骸（这两样"要钻石以上"），并用铁镐当反向对照。</p>
 *
 * <p><b>配方</b>：两条都真的摆进 3×3 合成格跑 {@code matches()} + {@code assemble()}，
 * 再摆一个"少一块料"的摆法当反向断言。</p>
 */
public final class AlloyToolCheck {

    private static final String TAG = "[TOOL] ";
    private static boolean registered;

    private AlloyToolCheck() {
    }

    public static void register() {
        if (registered) {
            return;
        }
        registered = true;
        try {
            net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(AlloyToolCheck.class);
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
        HolderLookup.Provider registries = event.getServer().registryAccess();

        Item sword = ModItems.TITANIUM_ALLOY_SWORD.get();
        Item pick = ModItems.TITANIUM_ALLOY_PICKAXE.get();
        ResourceLocation swordId = rl("titanium_alloy_sword");
        ResourceLocation pickId = rl("titanium_alloy_pickaxe");

        // ---------- ① 注册 ----------
        System.out.println(TAG + "(1) registration");
        failed += check("ITEM registry contains " + swordId, BuiltInRegistries.ITEM.containsKey(swordId));
        failed += check("ITEM registry contains " + pickId, BuiltInRegistries.ITEM.containsKey(pickId));
        failed += check("ModItems.TITANIUM_ALLOY_SWORD points at " + swordId,
                swordId.equals(BuiltInRegistries.ITEM.getKey(sword)));
        failed += check("ModItems.TITANIUM_ALLOY_PICKAXE points at " + pickId,
                pickId.equals(BuiltInRegistries.ITEM.getKey(pick)));

        // ---------- ② 耐久（用户字面量）----------
        System.out.println(TAG + "(2) durability (user's numbers)");
        failed += check("sword durability = 2048 (got " + new ItemStack(sword).getMaxDamage() + ")",
                new ItemStack(sword).getMaxDamage() == 2048);
        failed += check("pickaxe durability = 4219 (got " + new ItemStack(pick).getMaxDamage() + ")",
                new ItemStack(pick).getMaxDamage() == 4219);

        // ---------- ③ 攻击伤害 = 玩家基础 + 物品加成（显示值）----------
        System.out.println(TAG + "(3) displayed attack damage");
        double base = attackDamageBase();
        double swordDmg = totalAttackDamage(sword, base);
        double pickDmg = totalAttackDamage(pick, base);
        System.out.println(TAG + "  player base attack damage = " + base
                + "  sword total = " + swordDmg + "  pickaxe total = " + pickDmg);
        // 先用原版对照把"这套算法算的就是游戏里显示的那个数"钉死（期望值来自原版常识：钻石剑 7 / 铁剑 6 / 钻石镐 5）
        failed += check("(control) formula gives 7.0 for a vanilla diamond sword (got "
                + totalAttackDamage(Items.DIAMOND_SWORD, base) + ")",
                close(totalAttackDamage(Items.DIAMOND_SWORD, base), 7.0));
        failed += check("(control) ...6.0 for a vanilla iron sword (got "
                + totalAttackDamage(Items.IRON_SWORD, base) + ")",
                close(totalAttackDamage(Items.IRON_SWORD, base), 6.0));
        failed += check("(control) ...5.0 for a vanilla diamond pickaxe (got "
                + totalAttackDamage(Items.DIAMOND_PICKAXE, base) + ")",
                close(totalAttackDamage(Items.DIAMOND_PICKAXE, base), 5.0));
        failed += check("sword displayed attack damage = 6.5 (got " + swordDmg + ")", close(swordDmg, 6.5));
        failed += check("pickaxe displayed attack damage = 4.0 (got " + pickDmg + ")", close(pickDmg, 4.0));
        failed += check("sword attack speed modifier = -2.4 (vanilla sword) (got "
                + attackSpeed(sword) + ")", close(attackSpeed(sword), -2.4));
        failed += check("pickaxe attack speed modifier = -2.8 (vanilla pickaxe) (got "
                + attackSpeed(pick) + ")", close(attackSpeed(pick), -2.8));

        // ---------- ④ 附魔权重（比金高一点）----------
        System.out.println(TAG + "(4) enchantment value");
        int gold = Items.GOLDEN_SWORD.getEnchantmentValue();
        System.out.println(TAG + "  vanilla gold enchantment value = " + gold);
        failed += check("sword enchantment value = 25 (got " + sword.getEnchantmentValue() + ")",
                sword.getEnchantmentValue() == 25);
        failed += check("pickaxe enchantment value = 25 (got " + pick.getEnchantmentValue() + ")",
                pick.getEnchantmentValue() == 25);
        failed += check("...and it is HIGHER than gold's " + gold,
                sword.getEnchantmentValue() > gold && pick.getEnchantmentValue() > gold);
        failed += check("both tools share the same enchantment value",
                sword.getEnchantmentValue() == pick.getEnchantmentValue());

        // ---------- ⑤ 挖掘等级 = 下界合金 ----------
        System.out.println(TAG + "(5) mining level = netherite");
        Tier tier = ((TieredItem) pick).getTier();
        failed += check("tier's incorrect-for-drops tag is INCORRECT_FOR_NETHERITE_TOOL (got "
                        + tier.getIncorrectBlocksForDrops().location() + ")",
                tier.getIncorrectBlocksForDrops().equals(BlockTags.INCORRECT_FOR_NETHERITE_TOOL));
        failed += check("...and is NOT the diamond one (" + Tiers.DIAMOND.getIncorrectBlocksForDrops().location() + ")",
                !tier.getIncorrectBlocksForDrops().equals(Tiers.DIAMOND.getIncorrectBlocksForDrops()));
        failed += check("same tag as vanilla netherite tier",
                tier.getIncorrectBlocksForDrops().equals(Tiers.NETHERITE.getIncorrectBlocksForDrops()));
        failed += check("mining speed = netherite's " + Tiers.NETHERITE.getSpeed() + " (got " + tier.getSpeed() + ")",
                close(tier.getSpeed(), Tiers.NETHERITE.getSpeed()));
        ItemStack pickStack0 = new ItemStack(pick);
        failed += check("can harvest obsidian (needs diamond+)",
                pickStack0.isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));
        failed += check("can harvest ancient debris (needs diamond+)",
                pickStack0.isCorrectToolForDrops(Blocks.ANCIENT_DEBRIS.defaultBlockState()));
        failed += check("(control) vanilla iron pickaxe can NOT harvest obsidian",
                !new ItemStack(Items.IRON_PICKAXE).isCorrectToolForDrops(Blocks.OBSIDIAN.defaultBlockState()));

        // ---------- ⑥ 修理材料 = 轻质钛合金 ----------
        System.out.println(TAG + "(6) repair ingredient");
        ItemStack pickStack = new ItemStack(pick);
        failed += check("repairable with light titanium alloy",
                pick.isValidRepairItem(pickStack, new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get())));
        failed += check("(reverse) NOT repairable with an iron ingot",
                !pick.isValidRepairItem(pickStack, new ItemStack(Items.IRON_INGOT)));

        // ---------- ⑦ 没有 Shift 说明：类必须就是原版类 ----------
        System.out.println(TAG + "(7) no shift tooltip (item class must be the vanilla one)");
        failed += check("sword class is exactly SwordItem (got " + sword.getClass().getSimpleName() + ")",
                sword.getClass() == SwordItem.class);
        failed += check("pickaxe class is exactly PickaxeItem (got " + pick.getClass().getSimpleName() + ")",
                pick.getClass() == PickaxeItem.class);

        // ---------- ⑧ 两条配方：认得出、摆得出来 ----------
        System.out.println(TAG + "(8) recipes (vanilla shapes, alloy instead of the ingot)");
        failed += swordRecipe(level, registries, swordId, sword);
        failed += pickaxeRecipe(level, registries, pickId, pick);

        return failed;
    }

    // ==================== 配方 ====================
    /** {@code RecipeHolder<?>} 里那个捕获类型没法直接喂 CraftingInput，这里统一转一下（合成配方本来就是 CraftingInput）。 */
    @SuppressWarnings("unchecked")
    private static Recipe<CraftingInput> craftingRecipe(RecipeHolder<?> holder) {
        return (Recipe<CraftingInput>) holder.value();
    }

    private static int swordRecipe(ServerLevel level, HolderLookup.Provider registries,
                                   ResourceLocation id, Item expected) {
        int failed = 0;
        RecipeHolder<?> holder = level.getRecipeManager().byKey(id).orElse(null);
        failed += check("recipe " + id + " exists", holder != null);
        if (holder == null) {
            return failed;
        }
        Recipe<CraftingInput> recipe = craftingRecipe(holder);
        List<ItemStack> grid = new ArrayList<>();
        for (int i = 0; i < 9; i++) {
            grid.add(ItemStack.EMPTY);
        }
        grid.set(0, new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get()));
        grid.set(3, new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get()));
        grid.set(6, new ItemStack(Items.STICK));
        CraftingInput input = CraftingInput.of(3, 3, grid);
        failed += check("2 alloy + 1 stick in a column matches", recipe.matches(input, level));
        ItemStack out = recipe.assemble(input, registries);
        failed += check("outputs 1 titanium alloy sword (got " + out.getCount() + ")",
                out.is(expected) && out.getCount() == 1);

        List<ItemStack> bad = new ArrayList<>(grid);
        bad.set(6, ItemStack.EMPTY);
        failed += check("(reverse) without the stick it does NOT match",
                !recipe.matches(CraftingInput.of(3, 3, bad), level));
        return failed;
    }

    private static int pickaxeRecipe(ServerLevel level, HolderLookup.Provider registries,
                                     ResourceLocation id, Item expected) {
        int failed = 0;
        RecipeHolder<?> holder = level.getRecipeManager().byKey(id).orElse(null);
        failed += check("recipe " + id + " exists", holder != null);
        if (holder == null) {
            return failed;
        }
        Recipe<CraftingInput> recipe = craftingRecipe(holder);
        List<ItemStack> grid = new ArrayList<>();
        for (int i = 0; i < 9; i++) {
            grid.add(ItemStack.EMPTY);
        }
        grid.set(0, new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get()));
        grid.set(1, new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get()));
        grid.set(2, new ItemStack(ModItems.LIGHT_TITANIUM_ALLOY.get()));
        grid.set(4, new ItemStack(Items.STICK));
        grid.set(7, new ItemStack(Items.STICK));
        CraftingInput input = CraftingInput.of(3, 3, grid);
        failed += check("3 alloy on top + 2 sticks down the middle matches", recipe.matches(input, level));
        ItemStack out = recipe.assemble(input, registries);
        failed += check("outputs 1 titanium alloy pickaxe (got " + out.getCount() + ")",
                out.is(expected) && out.getCount() == 1);

        List<ItemStack> bad = new ArrayList<>(grid);
        bad.set(2, ItemStack.EMPTY);
        failed += check("(reverse) with only 2 alloy it does NOT match",
                !recipe.matches(CraftingInput.of(3, 3, bad), level));
        return failed;
    }

    // ==================== 属性读数 ====================
    /**
     * 玩家基础攻击伤害 —— 原版 {@code Player.createAttributes()} 里写的是 <b>1.0</b>。
     *
     * <p>⚠ <b>别拿 {@code Attributes.ATTACK_DAMAGE.value().getDefaultValue()}（= 2.0）</b>：
     * 那是"通用生物"的默认值，玩家不是那个数。用错就会把"显示伤害"整体算高 1 点
     * （第一版探针就是这么错的：钻石剑算成 8，可游戏里明明是 7）。</p>
     */
    private static double attackDamageBase() {
        return net.minecraft.world.entity.player.Player.createAttributes().build()
                .getBaseValue(Attributes.ATTACK_DAMAGE);
    }

    /** 显示总伤害 = 基础 + 物品的 ATTACK_DAMAGE 加成。 */
    private static double totalAttackDamage(Item item, double base) {
        return base + modifierAmount(item, Attributes.ATTACK_DAMAGE);
    }

    private static double attackSpeed(Item item) {
        return modifierAmount(item, Attributes.ATTACK_SPEED);
    }

    private static double modifierAmount(Item item, net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute) {
        ItemAttributeModifiers mods = new ItemStack(item).get(DataComponents.ATTRIBUTE_MODIFIERS);
        if (mods == null) {
            return 0.0D;
        }
        for (ItemAttributeModifiers.Entry entry : mods.modifiers()) {
            AttributeModifier modifier = entry.modifier();
            if (entry.attribute().value() == attribute.value()) {
                return modifier.amount();
            }
        }
        return 0.0D;
    }

    private static boolean close(double a, double b) {
        return Math.abs(a - b) < 1.0E-6;
    }

    private static ResourceLocation rl(String path) {
        return ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, path);
    }

    private static int check(String name, boolean pass) {
        System.out.println(TAG + (pass ? "  [OK]   " : "  [FAIL] ") + name);
        return pass ? 0 : 1;
    }
}
