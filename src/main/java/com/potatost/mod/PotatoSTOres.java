package com.potatost.mod;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public class PotatoSTOres {
    public static final DeferredRegister.Blocks ORES =
            DeferredRegister.createBlocks(PotatoST.MODID);
    public static final DeferredRegister.Items ORE_ITEMS =
            DeferredRegister.createItems(PotatoST.MODID);

    public static final List<DeferredHolder<Item, BlockItem>> ALL_ORE_ITEMS = new ArrayList<>();
    /** 粗矿物品（矿石的掉落物，必须先注册，掉落表才能引用） */
    public static final List<DeferredItem<Item>> ALL_RAW_ITEMS = new ArrayList<>();

    // ===== 16 个矿石方块 =====
    // （原来是"9 个"；ZF15 加了锂、ZF46 加了黑钨矿+深层变种、ZF48 加了钛矿+深层变种，这行注释跟着对齐。）
    public static final DeferredBlock<Block> ALUMINUM_ORE = ore("aluminum_ore", SoundType.STONE, 3.0F);
    public static final DeferredBlock<Block> COBALT_ORE = ore("cobalt_ore", SoundType.STONE, 3.0F);
    public static final DeferredBlock<Block> DEEPSLATE_COBALT_ORE = ore("deepslate_cobalt_ore", SoundType.DEEPSLATE, 4.5F);
    public static final DeferredBlock<Block> NICKEL_ORE = ore("nickel_ore", SoundType.STONE, 3.0F);
    public static final DeferredBlock<Block> DEEPSLATE_NICKEL_ORE = ore("deepslate_nickel_ore", SoundType.DEEPSLATE, 4.5F);
    public static final DeferredBlock<Block> SILVER_ORE = ore("silver_ore", SoundType.STONE, 3.0F);
    public static final DeferredBlock<Block> DEEPSLATE_SILVER_ORE = ore("deepslate_silver_ore", SoundType.DEEPSLATE, 4.5F);
    public static final DeferredBlock<Block> URANIUM_ORE = ore("uranium_ore", SoundType.STONE, 3.0F);
    public static final DeferredBlock<Block> DEEPSLATE_URANIUM_ORE = ore("deepslate_uranium_ore", SoundType.DEEPSLATE, 4.5F);
    // ===== 锰矿（数据已就位，生成暂不挂）=====
    public static final DeferredBlock<Block> MANGANESE_ORE =
            ore("manganese_ore", SoundType.STONE, 3.0F);
    public static final DeferredBlock<Block> DEEPSLATE_MANGANESE_ORE =
            ore("deepslate_manganese_ore", SoundType.DEEPSLATE, 4.5F);

    // ===== 锂矿石（0.10 ZF15）=====
    /**
     * 锂矿石：<b>「挖掘等级铁」不写在这里</b>——
     * 「必须铁镐」写在 {@code data/minecraft/tags/block/needs_iron_tool.json}，
     * 「镐可挖」写在 {@code data/minecraft/tags/block/mineable/pickaxe.json}。
     * 代码侧只有 {@link #ore} 里的 {@code requiresCorrectToolForDrops()}（= 必须用对工具才掉东西），
     * 两者是**两件不同的事**，少写一个就会出现「木镐能挖但什么都不掉」或「铁镐挖了不掉」。
     *
     * <p>只做浅层，<b>不配深层变种</b>（和铝矿石同款；钴/镍/银/铀/锰都有深层）。</p>
     */
    public static final DeferredBlock<Block> LITHIUM_ORE =
            ore("lithium_ore", SoundType.STONE, 3.0F);

    // ===== 黑钨矿（0.10 ZF46）=====
    /**
     * 黑钨矿：钨的矿石。用户原话：「加入黑钨矿 和粗钨 <b>目前不可以被任何东西冶炼</b>」。
     *
     * <p><b>所以本阶段故意一条冶炼配方都不加</b>：熔炉 / 高炉（`minecraft:smelting` / `blasting`）、
     * 电力高炉（{@link BlastFurnaceRecipes}）都**不认**粗钨 —— 探针 {@code TungstenCheck}
     * 把这三个查询都跑了一遍作为取证，不是"我没写所以应该没有"。</p>
     *
     * <p>深层变种按项目惯例配（钴/镍/银/铀/锰都有；只有铝与锂是纯浅层）：
     * 黑钨矿是深处矿，只给浅层那一份会让深板岩层完全不长。</p>
     *
     * <p>挖掘等级 = <b>铁镐</b>（写在 {@code data/minecraft/tags/block/needs_iron_tool.json}）。</p>
     */
    public static final DeferredBlock<Block> WOLFRAMITE_ORE =
            ore("wolframite_ore", SoundType.STONE, 3.0F);

    public static final DeferredBlock<Block> DEEPSLATE_WOLFRAMITE_ORE =
            ore("deepslate_wolframite_ore", SoundType.DEEPSLATE, 4.5F);

    // ===== 钛矿（0.10 ZF48）=====
    /**
     * 钛矿：用户原话「加入钛矿（<b>稀有度比黄金略高</b>）和粗钛」。
     *
     * <p>「比黄金略高」是照**原版金矿**的实际数值折算的（不是拍脑袋）——从 {@code client.jar} 读出来的金矿：
     * 每区块 {@code ore_gold} 4 簇 × 9 块 + {@code ore_gold_lower} 0~1 簇 × 9 块 ≈ <b>40 块上限</b>，
     * 且 {@code discard_chance_on_air_exposure = 0.5}（见空气的方块一半会没）。
     * 本矿取 <b>4 簇 × 8 块 = 32 块上限</b>、同样的 0.5 丢弃率、高度带收窄到 -64~16
     * ⇒ 大约**比黄金稀两成**，符合「略高」。数值都在 §9 挂着，嫌不对改两个数即可。</p>
     *
     * <p>深层变种按项目惯例配（§6.7.1 第 5 条：不写深层 target 的话深板岩层完全不生成）。</p>
     */
    public static final DeferredBlock<Block> TITANIUM_ORE =
            ore("titanium_ore", SoundType.STONE, 3.0F);

    public static final DeferredBlock<Block> DEEPSLATE_TITANIUM_ORE =
            ore("deepslate_titanium_ore", SoundType.DEEPSLATE, 4.5F);

    // ===== 9 个粗矿物品 =====
    public static final DeferredItem<Item> RAW_ALUMINUM = raw("raw_aluminum");
    public static final DeferredItem<Item> RAW_COBALT = raw("raw_cobalt");
    public static final DeferredItem<Item> RAW_LITHIUM = raw("raw_lithium");
    public static final DeferredItem<Item> RAW_NICKEL = raw("raw_nickel");
    public static final DeferredItem<Item> RAW_SILVER = raw("raw_silver");
    public static final DeferredItem<Item> RAW_URANIUM = raw("raw_uranium");
    public static final DeferredItem<Item> RAW_MANGANESE = raw("raw_manganese");
    /** 粗钨：黑钨矿的掉落物。**目前没有任何冶炼去处**（用户指定），是"先收着、以后再接线"的一环。 */
    public static final DeferredItem<Item> RAW_TUNGSTEN = raw("raw_tungsten");
    /**
     * 粗钛：钛矿的掉落物（0.10 ZF48）。
     *
     * <p>用户指定的加工链是<b>唯一</b>一条路，所以这里**故意不给它任何原版冶炼配方</b>：
     * 粗钛 →（微型粉碎机 6 秒 / 300 FE/t）→ 钛粉 →（电力高炉）→ 钛锭。
     * 探针会断言"熔炉/高炉烧不了粗钛"，同时断言"电力高炉能把钛粉烧成钛锭"。</p>
     */
    public static final DeferredItem<Item> RAW_TITANIUM = raw("raw_titanium");

    public static void register(IEventBus modEventBus) {
        ORES.register(modEventBus);
        ORE_ITEMS.register(modEventBus);
        modEventBus.addListener(PotatoSTOres::addToCreativeTab);
    }

    private static void addToCreativeTab(BuildCreativeModeTabContentsEvent event) {
        if (event.getTab() == ModItems.POTATO_ST_TAB.get()) {
            for (DeferredHolder<Item, BlockItem> holder : ALL_ORE_ITEMS) {
                event.accept(new ItemStack(holder.get()));
            }
            for (DeferredItem<Item> holder : ALL_RAW_ITEMS) {
                event.accept(new ItemStack(holder.get()));
            }
        }
    }

    private static DeferredBlock<Block> ore(String name, SoundType sound, float hardness) {
        DeferredBlock<Block> block = ORES.register(name,
                () -> new Block(BlockBehaviour.Properties.of()
                        .requiresCorrectToolForDrops()
                        .strength(hardness, 3.0F)
                        .sound(sound)));
        ALL_ORE_ITEMS.add(ORE_ITEMS.register(name,
                () -> new BlockItem(block.get(), new Item.Properties())));
        return block;
    }

    private static DeferredItem<Item> raw(String name) {
        DeferredItem<Item> item = ORE_ITEMS.register(name, () -> new Item(new Item.Properties()));
        ALL_RAW_ITEMS.add(item);
        return item;
    }
}