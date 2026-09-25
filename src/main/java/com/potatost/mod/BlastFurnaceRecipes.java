package com.potatost.mod;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.tags.ItemTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

/**
 * 电力高炉的配方表（0.10 ZF39）。<b>纯查表 + 纯函数</b>，不碰世界 ⇒ 探针能脱离游戏验。
 *
 * <p>用户的三条（原话「配方暂且…」= 先这样）：
 * <ol>
 *   <li>任意<b>粗矿 → 对应锭 ×2</b>；</li>
 *   <li><b>沙子 → 硅</b>（与本项目既有的高炉配方同源，见 §6.12）；</li>
 *   <li><b>矿石方块 → 对应锭 3~6 个</b>（每个方块单独掷骰，含深板岩变体）。</li>
 * </ol>
 *
 * <p>0.10 ZF45 又加了第四条：<b>双输入配方</b>（铁粉 + 碳粉 → 高碳钢、铁粉 + 沙砾 → 磁铁），
 * 存在单独的 {@link #PAIRS} 表里 —— 前三条都是"一个输入看一个产物"，这一条要同时看两个槽。</p>
 *
 * <p><b>收录范围（用户 ZF39 拍板：「有锭的直接烧 没有的不需要新加」）：</b>
 * <ul>
 *   <li>粗铀 —— 用户点名排除；</li>
 *   <li>粗锰 / 锰矿石、粗锂 / 锂矿石 —— 本项目<b>没有锰锭、也没有锂锭</b>，
 *       而用户明确说**不为它们新增物品**，所以它们暂时没有配方。
 *       （锂的链条是 粗锂 →粉碎→ 锂矿精粉 →高炉→ 碳酸锂，本来就不走锭。）</li>
 * </ul>
 * 换句话说：本表只覆盖"**已经有对应锭**"的材料，一条都不凭空造物品。</p>
 */
public final class BlastFurnaceRecipes {

    /** 一条配方：每个输入物品产出什么、产出几个。 */
    public record Recipe(Item output, int count) {
    }

    /**
     * 一条<b>双输入</b>配方（0.10 ZF45）：两个输入槽各出 1 份，产出一份产物。
     *
     * <p>用户原话：</p>
     * <ul>
     *   <li>「检测到有1份铁和一分碳粉 自动开始熔炼 然后消耗它们两个产出1个 高碳钢」；</li>
     *   <li>「铁粉和沙砾在电力高炉中烧出一个【磁铁】」。</li>
     * </ul>
     *
     * <p><b>为什么单独一张表、不塞进 {@link #RAW}/{@link #ORE}：</b>那两张是"一个物品 →
     * 一个产物"的<b>一元</b>映射（{@code Map<Item, Recipe>}），而这两条要<b>同时看两个槽</b>。
     * 硬塞进去只能靠"把碳粉写进铁粉的产物里"之类的花招，机器那侧反而要写特例。
     * 分成两张表之后，{@link ElectricBlastFurnaceBlockEntity} 那边是"先找配对、剩下槽位再走单槽"，
     * 两条路互不干扰。</p>
     */
    public record Pair(Item a, Item b, Item output, int count) {

        /**
         * 这一对认不认这两个槽 —— <b>与左右顺序无关</b>。
         *
         * <p>用户没说"铁粉必须放左边"，而且玩家的槽位是随便摆的，所以两种顺序都算。</p>
         */
        public boolean matches(ItemStack x, ItemStack y) {
            if (x.isEmpty() || y.isEmpty()) {
                return false;
            }
            Item ix = x.getItem();
            Item iy = y.getItem();
            return (ix == this.a && iy == this.b) || (ix == this.b && iy == this.a);
        }
    }

    private static final Map<Item, Recipe> RAW = new LinkedHashMap<>();
    private static final Map<Block, Recipe> ORE = new LinkedHashMap<>();
    private static final List<Pair> PAIRS = new ArrayList<>();

    public static final int ORE_MIN = 3;
    public static final int ORE_MAX = 6;

    static {
        // ---- ① 粗矿 → 2 锭 ----
        raw(PotatoSTOres.RAW_ALUMINUM.get(), ModItems.ALUMINUM_INGOT.get());
        raw(PotatoSTOres.RAW_COBALT.get(), ModItems.COBALT_INGOT.get());
        raw(PotatoSTOres.RAW_NICKEL.get(), ModItems.NICKEL_INGOT.get());
        raw(PotatoSTOres.RAW_SILVER.get(), ModItems.SILVER_INGOT.get());
        raw(Items.RAW_IRON, Items.IRON_INGOT);
        raw(Items.RAW_COPPER, Items.COPPER_INGOT);
        raw(Items.RAW_GOLD, Items.GOLD_INGOT);

        // ---- ③ 矿石方块 → 3~6 锭 ----
        ore(PotatoSTOres.ALUMINUM_ORE.get(), ModItems.ALUMINUM_INGOT.get());
        ore(PotatoSTOres.COBALT_ORE.get(), ModItems.COBALT_INGOT.get());
        ore(PotatoSTOres.DEEPSLATE_COBALT_ORE.get(), ModItems.COBALT_INGOT.get());
        ore(PotatoSTOres.NICKEL_ORE.get(), ModItems.NICKEL_INGOT.get());
        ore(PotatoSTOres.DEEPSLATE_NICKEL_ORE.get(), ModItems.NICKEL_INGOT.get());
        ore(PotatoSTOres.SILVER_ORE.get(), ModItems.SILVER_INGOT.get());
        ore(PotatoSTOres.DEEPSLATE_SILVER_ORE.get(), ModItems.SILVER_INGOT.get());
        ore(Blocks.IRON_ORE, Items.IRON_INGOT);
        ore(Blocks.DEEPSLATE_IRON_ORE, Items.IRON_INGOT);
        ore(Blocks.COPPER_ORE, Items.COPPER_INGOT);
        ore(Blocks.DEEPSLATE_COPPER_ORE, Items.COPPER_INGOT);
        ore(Blocks.GOLD_ORE, Items.GOLD_INGOT);
        ore(Blocks.DEEPSLATE_GOLD_ORE, Items.GOLD_INGOT);
        ore(Blocks.NETHER_GOLD_ORE, Items.GOLD_INGOT);

        // ---- ④ 双输入（0.10 ZF45，用户指定）----
        //    铁粉 + 碳粉 → 高碳钢；铁粉 + 沙砾 → 磁铁。
        //    两条都只认**精确物品**：铁粉/碳粉/高碳钢/磁铁都是本项目自己的东西，
        //    沙砾按长期规则（默认只兼容矿物/粗矿/矿石/锭）也走精确 id，不挂 c:gravel。
        pair(ModItems.IRON_POWDER.get(), ModItems.CARBON.get(), ModItems.HIGH_CARBON_STEEL.get(), 1);
        pair(ModItems.IRON_POWDER.get(), Items.GRAVEL, ModItems.MAGNET.get(), 1);

        // ---- ⑤ 粉末 → 锭（0.10 ZF48，用户指定）----
        //    钛粉 → 钛锭：用户原话「钛粉再由电力高炉烧制出钛锭」。
        //    ⚠ 与"粗矿 → 2 锭"那条**不一样**，这里取 **1:1**（用户没说数量）：
        //      粉末已经是加工过的中间产物，再翻倍等于把粉碎机那 300 FE/t 白送回来。
        //      要改成 ×2 只需把下面那个 1 改掉。
        //    粗钛**不在**这张表里（也不会有原版 blasting 配方）⇒ 电力高炉烧不了粗钛，
        //    链条只能走用户指定的"先粉碎"。
        single(ModItems.TITANIUM_POWDER.get(), ModItems.TITANIUM_INGOT.get(), 1);
    }

    private BlastFurnaceRecipes() {
    }

    private static void raw(Item in, Item out) {
        RAW.put(in, new Recipe(out, 2));
    }

    private static void ore(Block in, Item out) {
        ORE.put(in, new Recipe(out, ORE_MIN));
    }

    /** 单输入 + 指定数量（钛粉 → 1 钛锭这种"不翻倍"的条目用它，别去改 {@link #raw} 的语义）。 */
    private static void single(Item in, Item out, int count) {
        RAW.put(in, new Recipe(out, count));
    }

    private static void pair(Item a, Item b, Item out, int count) {
        PAIRS.add(new Pair(a, b, out, count));
    }

    /**
     * 找出同时认这两个槽的配对配方；没有就返回 {@code null}。
     *
     * <p>顺序无关（见 {@link Pair#matches}）。表很小（目前 2 条），线性扫足够。</p>
     */
    public static Pair findPair(ItemStack x, ItemStack y) {
        for (Pair p : PAIRS) {
            if (p.matches(x, y)) {
                return p;
            }
        }
        return null;
    }

    /** 全部配对配方（JEI 展示用，只读）。 */
    public static List<Pair> pairs() {
        return List.copyOf(PAIRS);
    }

    /**
     * 查一个输入物品能烧出什么（只看种类，不看数量）。
     *
     * <p>沙子走<b>标签</b> {@code #minecraft:sand}（含红沙）—— 与 §6.12 既有的高炉配方一致；
     * 否则同一个"沙子"在高炉里能烧、在电力高炉里不能，玩家会以为坏了。</p>
     */
    public static Recipe find(ItemStack stack) {
        if (stack.isEmpty()) {
            return null;
        }
        Recipe r = RAW.get(stack.getItem());
        if (r != null) {
            return r;
        }
        if (stack.is(ItemTags.SAND)) {
            return new Recipe(ModItems.SILICON.get(), 1);
        }
        return ORE.get(Block.byItem(stack.getItem()));
    }

    /** 是不是"矿石方块"那一类 —— 产出数量**逐个随机**。 */
    public static boolean isOre(ItemStack stack) {
        return !stack.isEmpty() && ORE.containsKey(Block.byItem(stack.getItem()));
    }

    /**
     * 把<b>一整槽</b>的产物算出来（电力高炉一个槽位无论几个物品都是 3 秒烧完，见 §12.4）。
     *
     * <p>矿石那类**每个方块单独掷骰**（用户原话：「一个烧制成 3-6 个」），
     * 所以一摞 64 个矿石的总产出是 64 次独立掷骰的和。传 {@link RandomSource} 进来是为了
     * 探针能用固定种子复现（与 {@code SaltDecomposerRecipes.roll} 同一套做法）。</p>
     */
    public static ItemStack produce(ItemStack input, RandomSource random) {
        Recipe r = find(input);
        if (r == null || input.isEmpty()) {
            return ItemStack.EMPTY;
        }
        long total = 0;
        if (isOre(input)) {
            for (int i = 0; i < input.getCount(); i++) {
                total += ORE_MIN + random.nextInt(ORE_MAX - ORE_MIN + 1);
            }
        } else {
            total = (long) r.count() * input.getCount();
        }
        return new ItemStack(r.output(), (int) Math.min(total, Integer.MAX_VALUE));
    }

    public static int rawRecipeCount() {
        return RAW.size();
    }

    public static int oreRecipeCount() {
        return ORE.size();
    }

    /** 双输入配方条数（探针用：这张表加一条就该变一次）。 */
    public static int pairCount() {
        return PAIRS.size();
    }

    /**
     * 粗矿那类的只读视图（JEI 展示用）。
     *
     * <p>用 {@code unmodifiableMap(new LinkedHashMap<>(...))} 而不是 {@code Map.copyOf}：
     * 后者会打乱顺序，JEI 里的排列就会每次重启都换位置（与 {@code displayGroups} 同一个坑）。</p>
     */
    public static Map<Item, Recipe> rawRecipes() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(RAW));
    }

    /** 矿石方块那类的只读视图（JEI 展示用，顺序同上）。 */
    public static Map<Block, Recipe> oreRecipes() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(ORE));
    }
}
