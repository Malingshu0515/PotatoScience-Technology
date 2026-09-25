package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * 液压机配方表（0.10 ZF30）：<b>矿物锭 → 板材</b>。
 *
 * <p>用户原话：「加一个铜板和液压机 可以把矿物锭锻压成现有的板材」，
 * 所以是"锭进去、板出来"，一共 7 条：
 * 铜 / 铁 / 镍 / 钴 / 银 / 铝 / 钢（高碳钢）。</p>
 *
 * <p><b>锭一律走 {@code c:} 标签</b>（长期规则：矿物/粗矿/矿石/锭默认兼容别的 mod）——
 * 于是别的科技 mod 的铜锭、钢锭也能直接进来压板。
 * 铜锭自己没有物品，所以铜那一条指的是原版的 {@code minecraft:copper_ingot}，
 * 而它**确实挂在 {@code c:ingots/copper} 上**（0.10 ZF21 已解包核实，不必再猜）。</p>
 *
 * <p><b>为什么表里存"标签 + 兜底物品"两样：</b>标签是给别的 mod 开的口子，
 * 兜底物品保证"就算哪天某个标签文件出错、或者玩家只装了原版"，本模组自己的锭也照样能压。
 * 查表时**先查标签、再查兜底**，两条都命中的话前者优先（结果相同，无差别）。</p>
 *
 * <p><b>能量/时间（用户指定）：</b>400 FE/t、3 秒（{@value #DURATION_TICKS} tick）一块板
 * ⇒ 一块板共 24000 FE。</p>
 */
public final class PressRecipes {

    /** 压一块板要多久（tick）。用户："3s一个板" ⇒ 60 tick。 */
    public static final int DURATION_TICKS = 60;
    /** 压板时每 tick 耗电。用户："400FE/t" ⇒ 一块板共 24000 FE。 */
    public static final int ENERGY_PER_TICK = 400;

    /**
     * 压一个柏油块要几个沥青（0.11 ZF79，用户原话：「**12个沥青** 可以在液压机压成一个柏油块」）。
     *
     * <p>时间与耗电沿用液压机统一的 60 tick / 400 FE·t ⇒ 一块柏油块同样 <b>24000 FE</b>
     * （用户没为这条单独给数值，先用机器统一档；要改就是一个常量）。</p>
     */
    public static final int BITUMEN_PER_BLOCK = 12;

    /**
     * 一条配方：输入（通用标签 + 兜底物品 + 需要几个）→ 产物。
     *
     * <p>0.11 ZF79 改造（用户：「12 个沥青 可以在液压机压成一个柏油块」）：</p>
     * <ul>
     *   <li><b>加了 {@code inputCount}</b> —— 原先写死"一次吃 1 个"，现在 12 个沥青才能压一块柏油块；</li>
     *   <li><b>{@code inputTag} 允许为 {@code null}</b>：沥青属于"其他物品"，按长期规则**不挂 {@code c:} 标签**
     *       （只有矿物/粗矿/矿石/锭默认挂），所以这条配方只有兜底物品；</li>
     *   <li>字段顺手改成正名：{@code ingotTag} → {@code inputTag}、{@code plate} → {@code result}
     *       （表里现在不只有"锭 → 板"了）。</li>
     * </ul>
     *
     * @param inputTag   输入的通用标签；没有通用标签的物品传 {@code null}
     * @param fallback   兜底物品（本模组/原版的输入物；标签解析不到时的保证）
     * @param result     产物
     * @param inputCount 一次要消耗几个（≥1）
     */
    public record Recipe(TagKey<Item> inputTag, Item fallback, Item result, int inputCount) {

        /** {@code 1 个 → 1 个} 的常见情形（原先 7 条配方全是这样）。 */
        public Recipe(TagKey<Item> inputTag, Item fallback, Item result) {
            this(inputTag, fallback, result, 1);
        }

        /** 这个物品对不对得上（标签命中或就是兜底物品；**不看数量**）。 */
        public boolean matches(ItemStack stack) {
            if (stack.isEmpty()) {
                return false;
            }
            if (stack.is(this.fallback)) {
                return true;
            }
            return this.inputTag != null && stack.is(this.inputTag);
        }

        /** 数量够不够开工（物品对 + 手里的数量 ≥ {@link #inputCount}）。 */
        public boolean hasEnough(ItemStack stack) {
            return matches(stack) && stack.getCount() >= this.inputCount;
        }

        public ItemStack createOutput() {
            return new ItemStack(this.result);
        }
    }

    /** 铜：原版铜锭（挂在 {@code c:ingots/copper} 上，别的 mod 的铜锭同理） */
    private static final TagKey<Item> COPPER_INGOT = common("ingots/copper");
    private static final TagKey<Item> IRON_INGOT = common("ingots/iron");
    private static final TagKey<Item> NICKEL_INGOT = common("ingots/nickel");
    private static final TagKey<Item> COBALT_INGOT = common("ingots/cobalt");
    private static final TagKey<Item> SILVER_INGOT = common("ingots/silver");
    private static final TagKey<Item> ALUMINUM_INGOT = common("ingots/aluminum");
    private static final TagKey<Item> STEEL_INGOT = common("ingots/steel");

    /**
     * {@code c:} 通用标签的纯静态工厂。
     *
     * <p>⚠ 只允许这样建标签键，**绝不能在 {@code static final} 里读注册表**（§4.1 那次启动崩溃）。
     * {@code TagKey.create} 本身不碰注册表，是安全的；真正查标签是在 {@link Recipe#matches}
     * 里、"某个物品栈身上"发生的，那时注册表早就绑好了。</p>
     */
    private static TagKey<Item> common(String path) {
        return TagKey.create(Registries.ITEM, ResourceLocation.fromNamespaceAndPath("c", path));
    }

    private PressRecipes() {
    }

    /**
     * 全部 8 条配方（7 条"锭 → 板" + 1 条"12 沥青 → 柏油块"）。
     *
     * <p><b>懒加载</b>：这里要读 {@code ModItems.*.get()} / {@code ModBlocks.*.get()}，
     * 写成 {@code static final} 字段会在注册完成前触发
     * {@code Trying to access unbound value} 启动崩溃（§4.1 的血）。</p>
     */
    public static List<Recipe> all() {
        List<Recipe> out = new ArrayList<>(8);
        out.add(new Recipe(COPPER_INGOT, net.minecraft.world.item.Items.COPPER_INGOT,
                ModItems.COPPER_PLATE.get()));
        out.add(new Recipe(IRON_INGOT, net.minecraft.world.item.Items.IRON_INGOT,
                ModItems.IRON_PLATE.get()));
        out.add(new Recipe(NICKEL_INGOT, ModItems.NICKEL_INGOT.get(), ModItems.NICKEL_PLATE.get()));
        out.add(new Recipe(COBALT_INGOT, ModItems.COBALT_INGOT.get(), ModItems.COBALT_PLATE.get()));
        out.add(new Recipe(SILVER_INGOT, ModItems.SILVER_INGOT.get(), ModItems.SILVER_PLATE.get()));
        out.add(new Recipe(ALUMINUM_INGOT, ModItems.ALUMINUM_INGOT.get(), ModItems.ALUMINUM_PLATE.get()));
        out.add(new Recipe(STEEL_INGOT, ModItems.HIGH_CARBON_STEEL.get(), ModItems.STEEL_PLATE.get()));
        // 0.11 ZF79（用户原话：「12个沥青 可以在液压机压成一个柏油块（纯建筑方块）」）
        // ⚠ 沥青不挂 c: 标签（长期规则：只有矿物/粗矿/矿石/锭默认挂）⇒ inputTag 传 null
        out.add(new Recipe(null, ModItems.BITUMEN.get(), ModBlocks.ASPHALT_BLOCK_ITEM.get(),
                BITUMEN_PER_BLOCK));
        return List.copyOf(out);
    }

    /** 这个物品能不能压；不能就返回 {@code null}。 */
    public static Recipe find(ItemStack stack) {
        if (stack.isEmpty()) {
            return null;
        }
        for (Recipe recipe : all()) {
            if (recipe.matches(stack)) {
                return recipe;
            }
        }
        return null;
    }
}
