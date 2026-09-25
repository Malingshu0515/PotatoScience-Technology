package com.potatost.mod;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.neoforge.common.Tags;

/**
 * 微型粉碎机的配方表（0.10 新增）。
 *
 * <p><b>为什么是 Java 表而不是数据包配方：</b>本机的配方是「固定加工工艺」，
 * 与电解器的化学配比同一性质，项目里同类机器（电解器 / 晒盐机）也都是代码侧判定。
 * 做成自定义 {@code RecipeType} 需要额外注册序列化器 + 每个配方一个 JSON，
 * 而收益（JEI 展示）在<b>没有 JEI 依赖</b>的前提下并不存在——
 * 无论配方存在哪，JEI 都必须靠一个 JEI 插件才能显示。
 * 若日后配方数量膨胀、或需要 KubeJS / 数据包改配方，再迁移到自定义 RecipeType。</p>
 *
 * <p><b>跟别的 mod 兼容（0.10 ZF12 追加）：</b>精确物品查不到时，再按 <b>标签</b> 查一遍，
 * 用的是 NeoForge 的 {@code c:} 公共标签（{@link Tags.Items}）。机制上很划算：
 * NeoForge 把这些标签**桥接**到了原版标签与旧的 {@code forge:} 标签，例如</p>
 * <pre>
 *   c:ores/emerald = #minecraft:emerald_ores + #forge:ores/emerald(可选)
 *   c:gems/quartz  = minecraft:quartz        + #forge:gems/quartz(可选)
 * </pre>
 * <p>所以别的 mod 无论按新约定往 {@code c:} 挂、还是沿用它自己那边的 {@code #minecraft:*_ores}，
 * 本机都能认。<b>精确条目一律保留</b>：一是快路径，二是万一标签被数据包改空，
 * 原版物品仍旧照常粉碎（纵深防御）。</p>
 *
 * <p><b>⚠ 静态初始化的雷（§4.1）：</b>本表引用了 {@code ModItems.SILICON.get()}。
 * 若把整张表写成 {@code static final} 字段，类加载时机一旦提前到注册完成之前，
 * 就会重演 0.03 那次 {@code Trying to access unbound value} 启动崩溃。
 * 所以这里是<b>懒加载</b>：第一次查询配方（也就是第一次 tick）时才建表。</p>
 */
public final class MicroCrusherRecipes {

    /** 1 秒 = 20 tick */
    private static final int SEC = 20;

    /**
     * 别的 mod 的「粗锂」标签（0.10 ZF15）。
     *
     * <p><b>为什么要自己造：</b>NeoForge 的 {@link Tags.Items} 只给铜/金/铁/下界合金预置了
     * {@code RAW_MATERIALS_*} 常量（21.1.235 实测：共 3 个），锂没有 ——
     * 写 {@code Tags.Items.RAW_MATERIALS_LITHIUM} 是<b>编译期就报错</b>，不是运行期才发现。</p>
     *
     * <p><b>安全性：</b>{@code TagKey.create} 是纯静态工厂，不读注册表、不碰 DeferredHolder，
     * 所以放 {@code static final} 不会重演 0.03 的静态初始化崩溃
     * （同理见 {@code ModItems.ANVIL_OF_THE_REPUBLIC_SONG}）。
     * 标签内容在<b>数据包</b>里（{@code data/c/tags/item/raw_materials/lithium.json}，由
     * {@code GenCommonTags.py} 生成），代码这边只是个名字。</p>
     */
    private static final TagKey<Item> RAW_MATERIALS_LITHIUM = TagKey.create(
            Registries.ITEM,
            ResourceLocation.fromNamespaceAndPath("c", "raw_materials/lithium"));

    /**
     * {@code c:ingots/copper} —— 铜锭的通用标签（含原版的 {@code minecraft:copper_ingot}）。
     *
     * <p>0.10 ZF33 加"铜锭 → 铜线"时用。理由与铜锭配方（电容）一致：<b>锭属于长期规则里
     * "默认兼容别的 mod"的那一类</b>，所以这里用标签而不是精确 id。</p>
     */
    private static final TagKey<Item> COPPER_INGOT = TagKey.create(
            Registries.ITEM,
            ResourceLocation.fromNamespaceAndPath("c", "ingots/copper"));

    /**
     * {@code c:ingots/iron} —— 铁锭的通用标签（含原版的 {@code minecraft:iron_ingot}）。
     *
     * <p>0.10 ZF45 加"铁锭 → 铁粉"时用，理由同上：<b>锭默认兼容别的 mod</b>。</p>
     */
    private static final TagKey<Item> IRON_INGOT = TagKey.create(
            Registries.ITEM,
            ResourceLocation.fromNamespaceAndPath("c", "ingots/iron"));

    /**
     * {@code c:raw_materials/titanium} —— 别的 mod 的粗钛（0.10 ZF48）。
     *
     * <p>与 {@link #RAW_MATERIALS_LITHIUM} 同一个理由：NeoForge 的 {@code Tags.Items} 里
     * **只预置了铜/金/铁/下界合金**的粗矿常量，钛没有 ⇒ 只能自己造名字。</p>
     */
    private static final TagKey<Item> RAW_MATERIALS_TITANIUM = TagKey.create(
            Registries.ITEM,
            ResourceLocation.fromNamespaceAndPath("c", "raw_materials/titanium"));

    /**
     * 一条粉碎配方。
     *
     * @param result         产物物品
     * @param countMin       产物最少个数
     * @param countMax       产物最多个数（等于 countMin 时即固定产物）
     * @param durationTicks  粉碎一轮需要多少 tick
     * @param energyPerTick  工作时每 tick 消耗多少 FE
     */
    public record Crush(Item result, int countMin, int countMax, int durationTicks, int energyPerTick) {

        /** 随机滚一次产物（含两端）。 */
        public ItemStack createOutput(RandomSource random) {
            int count = (this.countMin >= this.countMax)
                    ? this.countMin
                    : this.countMin + random.nextInt(this.countMax - this.countMin + 1);
            return new ItemStack(this.result, count);
        }

        /** 一轮总耗电（GUI 提示用）。 */
        public int totalEnergy() {
            return this.durationTicks * this.energyPerTick;
        }
    }

    /** 标签规则：任何 mod 的物品，只要挂进了这个标签，就按这条配方粉碎。 */
    private record TagRule(TagKey<Item> tag, Crush crush) {
    }

    /** 懒加载表；null = 还没建过 */
    private static Map<Item, Crush> table;
    private static List<TagRule> tagRules;

    private MicroCrusherRecipes() {
    }

    /**
     * 查输入物品对应的配方；没有则返回 {@code null}。
     *
     * <p>顺序：先精确物品（快），再按标签（兼容别的 mod）。</p>
     */
    public static Crush find(ItemStack stack) {
        if (stack.isEmpty()) {
            return null;
        }
        Crush exact = table().get(stack.getItem());
        if (exact != null) {
            return exact;
        }
        for (TagRule rule : tagRules()) {
            if (stack.is(rule.tag())) {
                return rule.crush();
            }
        }
        return null;
    }

    private static Map<Item, Crush> table() {
        if (table == null) {
            build();
        }
        return table;
    }

    private static List<TagRule> tagRules() {
        if (tagRules == null) {
            build();
        }
        return tagRules;
    }

    // ================= 配方定义 =================
    private static void build() {
        Map<Item, Crush> m = new HashMap<>();
        List<TagRule> tags = new ArrayList<>();
        Item silicon = ModItems.SILICON.get();

        // ① 紫水晶碎片 / 下界石英 → 1 硅，30s，30 FE/t
        Crush shard = new Crush(silicon, 1, 1, 30 * SEC, 30);
        m.put(Items.AMETHYST_SHARD, shard);
        m.put(Items.QUARTZ, shard);
        // 别的 mod 的紫水晶碎片 / 石英：c:gems/* 已被 NeoForge 桥接 vanilla 与旧的 forge: 标签
        tags.add(new TagRule(Tags.Items.GEMS_AMETHYST, shard));
        tags.add(new TagRule(Tags.Items.GEMS_QUARTZ, shard));

        // ② 紫水晶块 → 12~18 硅，120s，80 FE/t
        m.put(Items.AMETHYST_BLOCK, new Crush(silicon, 12, 18, 120 * SEC, 80));

        // ③ 石英建材（普通/平滑/錾制/柱/楼梯/台阶）→ 2 硅，40s，50 FE/t
        //    没有"石英建材"这种通用标签，所以只能精确匹配，别的 mod 的石英建材不进（§9 已记）
        Crush quartzBuilding = new Crush(silicon, 2, 2, 40 * SEC, 50);
        for (Item quartz : new Item[] {
                Items.QUARTZ_BLOCK, Items.SMOOTH_QUARTZ, Items.CHISELED_QUARTZ_BLOCK,
                Items.QUARTZ_PILLAR, Items.QUARTZ_STAIRS, Items.QUARTZ_SLAB }) {
            m.put(quartz, quartzBuilding);
        }

        // ④ 各类原木（含去皮的原木与原木块）→ 3~6 个对应木板，5s，1 FE/t
        //    这里**不能**改用 #minecraft:logs：产物得跟着输入变（橡木出橡木木板），
        //    标签只能给一个固定产物，所以必须逐种精确匹配。
        //    代价：别的 mod 的原木不在表内 → 不能粉碎（§9 已记为已知限制）。
        addWood(m, Items.OAK_LOG, Items.OAK_WOOD, Items.STRIPPED_OAK_LOG, Items.STRIPPED_OAK_WOOD,
                Items.OAK_PLANKS);
        addWood(m, Items.SPRUCE_LOG, Items.SPRUCE_WOOD, Items.STRIPPED_SPRUCE_LOG, Items.STRIPPED_SPRUCE_WOOD,
                Items.SPRUCE_PLANKS);
        addWood(m, Items.BIRCH_LOG, Items.BIRCH_WOOD, Items.STRIPPED_BIRCH_LOG, Items.STRIPPED_BIRCH_WOOD,
                Items.BIRCH_PLANKS);
        addWood(m, Items.JUNGLE_LOG, Items.JUNGLE_WOOD, Items.STRIPPED_JUNGLE_LOG, Items.STRIPPED_JUNGLE_WOOD,
                Items.JUNGLE_PLANKS);
        addWood(m, Items.ACACIA_LOG, Items.ACACIA_WOOD, Items.STRIPPED_ACACIA_LOG, Items.STRIPPED_ACACIA_WOOD,
                Items.ACACIA_PLANKS);
        addWood(m, Items.DARK_OAK_LOG, Items.DARK_OAK_WOOD, Items.STRIPPED_DARK_OAK_LOG, Items.STRIPPED_DARK_OAK_WOOD,
                Items.DARK_OAK_PLANKS);
        addWood(m, Items.MANGROVE_LOG, Items.MANGROVE_WOOD, Items.STRIPPED_MANGROVE_LOG, Items.STRIPPED_MANGROVE_WOOD,
                Items.MANGROVE_PLANKS);
        addWood(m, Items.CHERRY_LOG, Items.CHERRY_WOOD, Items.STRIPPED_CHERRY_LOG, Items.STRIPPED_CHERRY_WOOD,
                Items.CHERRY_PLANKS);
        addWood(m, Items.CRIMSON_STEM, Items.CRIMSON_HYPHAE, Items.STRIPPED_CRIMSON_STEM, Items.STRIPPED_CRIMSON_HYPHAE,
                Items.CRIMSON_PLANKS);
        addWood(m, Items.WARPED_STEM, Items.WARPED_HYPHAE, Items.STRIPPED_WARPED_STEM, Items.STRIPPED_WARPED_HYPHAE,
                Items.WARPED_PLANKS);

        // ⑤ 绿宝石矿石（浅层 / 深层 / 别的 mod 的）→ 15~40 绿宝石，180s，400 FE/t
        Crush emerald = new Crush(Items.EMERALD, 15, 40, 180 * SEC, 400);
        m.put(Items.EMERALD_ORE, emerald);
        m.put(Items.DEEPSLATE_EMERALD_ORE, emerald);
        tags.add(new TagRule(Tags.Items.ORES_EMERALD, emerald));

        // ⑥ 钻石矿石（浅层 / 深层 / 别的 mod 的）→ 3~12 钻石，90s，400 FE/t
        Crush diamond = new Crush(Items.DIAMOND, 3, 12, 90 * SEC, 400);
        m.put(Items.DIAMOND_ORE, diamond);
        m.put(Items.DEEPSLATE_DIAMOND_ORE, diamond);
        tags.add(new TagRule(Tags.Items.ORES_DIAMOND, diamond));

        // ⑦ 粗锂 → 2~4 锂矿精粉，12s，20 FE/t（0.10 ZF15）
        //    产物是"精粉"不是锭：粉状的下一步是进高炉烧成碳酸锂（数据包配方）。
        //    别的 mod 的粗锂按 c:raw_materials/lithium 认 —— 我们自己的 raw_lithium 也挂在这个标签里，
        //    上面先查精确条目（快路径），标签只是兜底，两条路都给同一个 Crush。
        Crush lithium = new Crush(ModItems.LITHIUM_CONCENTRATE.get(), 2, 4, 12 * SEC, 20);
        m.put(PotatoSTOres.RAW_LITHIUM.get(), lithium);
        tags.add(new TagRule(RAW_MATERIALS_LITHIUM, lithium));

        // ⑧ 铜锭 → 4 个铜线，3s，90 FE/t（0.10 ZF33，用户指定）
        //    用户原话："铜线 微型粉碎机 粉碎3s 产生4个 90Fe/t"
        //    锭在 `c:ingots/copper` 里（含原版 copper_ingot），所以别的 mod 的铜锭也能拉成线。
        //    注：**故意不做"铜线 → 铜锭"的逆向配方** —— 一锭出 4 线，逆向哪怕只给 1 锭也是 1:4 的
        //    无本套利（反复来回就白赚铜）。已记进档案 §9。
        Crush copperWire = new Crush(ModItems.COPPER_WIRE.get(), 4, 4, 3 * SEC, 90);
        m.put(Items.COPPER_INGOT, copperWire);
        tags.add(new TagRule(COPPER_INGOT, copperWire));

        // ⑨ 煤炭 / 木炭 → 1 碳粉，3s，10 FE/t（0.10 ZF45，用户指定）
        //    用户原话：「煤炭/木炭 3s 10fe/t产出一个碳粉」。
        //    用**原版标签** #minecraft:coals（= 煤炭 + 木炭）：这是原版自己就有的标签，
        //    别的 mod 的黑煤/褐煤只要挂进去也一起认 —— 比写死两个 id 更贴长期口径。
        //    两个精确条目**照样留着**（快路径 + 标签万一被数据包改空时的纵深防御）。
        Crush carbonDust = new Crush(ModItems.CARBON.get(), 1, 1, 3 * SEC, 10);
        m.put(Items.COAL, carbonDust);
        m.put(Items.CHARCOAL, carbonDust);
        tags.add(new TagRule(ItemTags.COALS, carbonDust));

        // ⑩ 铁锭 → 1 铁粉，20s，70 FE/t（0.10 ZF45，用户指定）
        //    用户原话：「铁锭 20s 70fe/t 产出一个铁粉」⇒ 一件总耗电 70×20×20 = 28000 FE。
        //    ⚠ 这个数比高炉烧一件（800 FE）贵 35 倍 —— 是照用户给的字面值实现的，
        //      没有替他"顺手调小"（数字摆在档案里，要改是一个常数）。
        //    锭属于长期规则里"默认兼容"的那类 ⇒ 走 c:ingots/iron 标签，别的 mod 的铁锭也认。
        Crush ironDust = new Crush(ModItems.IRON_POWDER.get(), 1, 1, 20 * SEC, 70);
        m.put(Items.IRON_INGOT, ironDust);
        tags.add(new TagRule(IRON_INGOT, ironDust));

        // ⑪ 粗钛 → 1 钛粉，6s，300 FE/t（0.10 ZF48，用户指定）
        //    用户原话：「粗钛需要粉碎机粉碎成钛粉 6s 300fe/t」⇒ 一件总耗电 300×6×20 = 36000 FE。
        //    ⚠ 用户**没说产出几个**，按 1:1 做（锂那条是 1→2~4）；要改就是这一行的 count。
        //    粗矿属于长期规则里"默认兼容"的那类 ⇒ 走 c:raw_materials/titanium 标签。
        Crush titaniumDust = new Crush(ModItems.TITANIUM_POWDER.get(), 1, 1, 6 * SEC, 300);
        m.put(PotatoSTOres.RAW_TITANIUM.get(), titaniumDust);
        tags.add(new TagRule(RAW_MATERIALS_TITANIUM, titaniumDust));

        table = Map.copyOf(m);
        tagRules = List.copyOf(tags);
    }

    /** 一种木材的 4 个「原木/木头/去皮原木/去皮木头」都产出同种木板（5s，1 FE/t，3~6 个）。 */
    private static void addWood(Map<Item, Crush> m, Item log, Item wood, Item strippedLog, Item strippedWood,
                                Item planks) {
        Crush crush = new Crush(planks, 3, 6, 5 * SEC, 1);
        m.put(log, crush);
        m.put(wood, crush);
        m.put(strippedLog, crush);
        m.put(strippedWood, crush);
    }

    // ================= 展示用（JEI / 文档，0.10 ZF19 追加） =================
    /** 一条展示分组 = 一条配方 + 这条配方认的全部输入物品。 */
    public record DisplayGroup(Crush crush, List<ItemStack> inputs) {
    }

    /**
     * 把配方整理成"一条配方一条记录"，给 {@link MachineRecipes} 与 JEI 用。
     *
     * <p>精确条目按 {@link Crush} 合并 —— 比如 6 种石英建材共用一个配方，JEI 里只出 1 条、输入是那 6 个物品；
     * 标签规则则把<b>标签里当前所有的物品</b>展开成输入（别的 mod 往 {@code c:} 里挂什么就显示什么，
     * 所以我们自己也不用维护"兼容列表"）。</p>
     *
     * <p><b>这是只读视图，不参与 {@link #find}，机器行为一个字都没变。</b>
     * 排序按"产物注册名 → 耗时 → 最少产出"，与 {@code Map.copyOf} 的遍历顺序无关，
     * 所以 JEI 里的排列是稳定的（不会每次重启换位置）。</p>
     */
    public static List<DisplayGroup> displayGroups() {
        Map<Crush, LinkedHashSet<Item>> groups = new LinkedHashMap<>();
        table().forEach((item, crush) -> groups.computeIfAbsent(crush, k -> new LinkedHashSet<>()).add(item));
        for (TagRule rule : tagRules()) {
            LinkedHashSet<Item> set = groups.computeIfAbsent(rule.crush(), k -> new LinkedHashSet<>());
            BuiltInRegistries.ITEM.getTag(rule.tag()).ifPresent(holders -> holders.forEach(h -> set.add(h.value())));
        }
        List<DisplayGroup> out = new ArrayList<>();
        for (Map.Entry<Crush, LinkedHashSet<Item>> entry : groups.entrySet()) {
            List<ItemStack> inputs = new ArrayList<>();
            for (Item item : entry.getValue()) {
                inputs.add(new ItemStack(item));
            }
            out.add(new DisplayGroup(entry.getKey(), List.copyOf(inputs)));
        }
        out.sort(Comparator
                .comparing((DisplayGroup g) -> BuiltInRegistries.ITEM.getKey(g.crush().result()).toString())
                .thenComparingInt(g -> g.crush().durationTicks())
                .thenComparingInt(g -> g.crush().countMin()));
        return List.copyOf(out);
    }
}
