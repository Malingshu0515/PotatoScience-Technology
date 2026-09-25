package com.potatost.mod;

import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Item;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * 两套新盔甲 + 星璨钢锭的注册（0.11 ZF103）。
 *
 * <p>单独开一个文件而不是塞进 {@link ModItems}：那个文件已经 533 行，
 * 而本轮的 9 个物品每个都要一段数值说明。注册表实例仍是 {@link ModItems#ITEMS}
 * （同一个 {@code DeferredRegister} 可以跨类写，{@code PotatoSTOres} 就是先例），
 * 所以语言键、创造页、审计口径全都跟其他物品一致：{@code item.potato_s_t.&lt;注册名&gt;}。</p>
 *
 * <h2>用户给的数（原话逐条抄下来，单位就是游戏里的显示值）</h2>
 * <pre>
 * 钛合金套（附魔权重比金高一些 ⇒ {@link ModArmorMaterials#TITANIUM_ENCHANTMENT_VALUE} = 25）
 *   头盔   耐久 2801  护甲值 +2.5
 *   胸甲   耐久 4096  护甲值 +8
 *   护腿   耐久 3412  护甲值 +6
 *   靴子   耐久 2048  护甲值 +4.5
 *
 * 星璨钢套（附魔权重用户没给 ⇒ {@link ModArmorMaterials#STAR_STEEL_ENCHANTMENT_VALUE} = 20）
 *   头盔   耐久 2012  护甲值 +5.5  盔甲韧性 +0.5
 *   胸甲   耐久 3876  护甲值 +9.5  盔甲韧性 +1
 *   护腿   耐久 2790  护甲值 +7.5  盔甲韧性 +0.5
 *   靴子   耐久 1754  护甲值 +5.5  盔甲韧性 +0.5
 * </pre>
 *
 * <p><b>耐久走 {@code properties.durability(n)} 直接写死</b>，不用
 * {@code ArmorItem.Type.getDurability(factor)} —— 后者是"档位系数 × 部位基数"，
 * 表达不出用户这四组精确值（2801/4096/3412/2048 和 2012/3876/2790/1754）。</p>
 *
 * <p><b>修理材料</b>（用户本轮拍板）：钛合金套用<b>轻质钛合金</b>、
 * 星璨钢套用<b>星璨钢锭</b>，写在 {@link ModArmorMaterials} 的 {@code repairIngredient} 里。</p>
 *
 * <p><b>星璨钢锭本轮没有配方</b>（用户原话「星璨钢这个金属的配方先不做」），
 * 也没有作为材料的下游 —— 只做"盔甲修理材料"这一件事。
 * 它的贴图按用户给的路径读 {@code assets/potato_s_t/textures/item/star_steel_ingot.png}。</p>
 */
public final class ModArmorItems {

    // ========== 星璨钢锭 ==========
    /**
     * 星璨钢锭：本轮只有"修理星璨钢套"一个用途（用户明确先不做配方）。
     *
     * <p>贴图是用户放进 {@code textures/item} 的那张：{@code star_steel_ingot.png}
     * （见 {@code models/item/star_steel_ingot.json} 的 layer0）。</p>
     */
    public static final DeferredItem<Item> STAR_STEEL_INGOT =
            ModItems.ITEMS.register("star_steel_ingot", () -> new Item(new Item.Properties()));

    // ========== 钛合金套 ==========
    /** 钛合金头盔：耐久 2801、护甲值 +2.5。 */
    public static final DeferredItem<Item> TITANIUM_ALLOY_HELMET =
            register("titanium_alloy_helmet", ModArmorMaterials.TITANIUM_ALLOY, ArmorItem.Type.HELMET,
                    2801, 2.5, 0.0, "tooltip.potato_s_t.titanium_alloy_set");

    /** 钛合金胸甲：耐久 4096、护甲值 +8。 */
    public static final DeferredItem<Item> TITANIUM_ALLOY_CHESTPLATE =
            register("titanium_alloy_chestplate", ModArmorMaterials.TITANIUM_ALLOY, ArmorItem.Type.CHESTPLATE,
                    4096, 8.0, 0.0, "tooltip.potato_s_t.titanium_alloy_set");

    /** 钛合金护腿：耐久 3412、护甲值 +6。 */
    public static final DeferredItem<Item> TITANIUM_ALLOY_LEGGINGS =
            register("titanium_alloy_leggings", ModArmorMaterials.TITANIUM_ALLOY, ArmorItem.Type.LEGGINGS,
                    3412, 6.0, 0.0, "tooltip.potato_s_t.titanium_alloy_set");

    /** 钛合金靴子：耐久 2048、护甲值 +4.5。 */
    public static final DeferredItem<Item> TITANIUM_ALLOY_BOOTS =
            register("titanium_alloy_boots", ModArmorMaterials.TITANIUM_ALLOY, ArmorItem.Type.BOOTS,
                    2048, 4.5, 0.0, "tooltip.potato_s_t.titanium_alloy_set");

    // ========== 星璨钢套 ==========
    /** 星璨钢头盔：耐久 2012、护甲值 +5.5、韧性 +0.5。 */
    public static final DeferredItem<Item> STAR_STEEL_HELMET =
            register("star_steel_helmet", ModArmorMaterials.STAR_STEEL, ArmorItem.Type.HELMET,
                    2012, 5.5, 0.5, "tooltip.potato_s_t.star_steel_set");

    /** 星璨钢胸甲：耐久 3876、护甲值 +9.5、韧性 +1。 */
    public static final DeferredItem<Item> STAR_STEEL_CHESTPLATE =
            register("star_steel_chestplate", ModArmorMaterials.STAR_STEEL, ArmorItem.Type.CHESTPLATE,
                    3876, 9.5, 1.0, "tooltip.potato_s_t.star_steel_set");

    /** 星璨钢护腿：耐久 2790、护甲值 +7.5、韧性 +0.5。 */
    public static final DeferredItem<Item> STAR_STEEL_LEGGINGS =
            register("star_steel_leggings", ModArmorMaterials.STAR_STEEL, ArmorItem.Type.LEGGINGS,
                    2790, 7.5, 0.5, "tooltip.potato_s_t.star_steel_set");

    /** 星璨钢靴子：耐久 1754、护甲值 +5.5、韧性 +0.5。 */
    public static final DeferredItem<Item> STAR_STEEL_BOOTS =
            register("star_steel_boots", ModArmorMaterials.STAR_STEEL, ArmorItem.Type.BOOTS,
                    1754, 5.5, 0.5, "tooltip.potato_s_t.star_steel_set");

    private ModArmorItems() {
    }

    /**
     * **只为"在模组构造期把本类初始化掉"而存在**（0.11 ZF105）。方法体故意是空的。
     *
     * <p><b>为什么必须有它</b>：本类的静态字段**直接调 {@code ModItems.ITEMS.register(...)}**，
     * 而 {@code DeferredRegister} 只在 {@code RegisterEvent} 之前收新条目。
     * 如果没人在这之前碰过本类，静态初始化会被拖到"第一次真正访问它"才发生 ——
     * 而第一次访问来自<b>创造模式标签页</b>（{@code ModItems} 里那串
     * {@code output.accept(ModArmorItems.XXX.get())}），那已经是<b>开物品栏</b>的时候了，
     * 注册窗口早关了 ⇒
     * {@code IllegalStateException: Cannot register new entries to DeferredRegister after RegisterEvent has been fired}
     * ⇒ {@code ExceptionInInitializerError} ⇒ 类初始化失败 ⇒ 之后**开物品栏必崩**
     * （而且崩点报在 {@code ModItems} 里，跟真正的错隔一层）。
     * 这正是 2026-09-25 18:40:17 那次客户端崩溃的根因（崩溃报告第 217 / 259 / 327 行）。</p>
     *
     * <p><b>为什么 {@code PotatoSTOres} 没踩</b>：它的注册方法
     * {@code PotatoSTOres.register(modEventBus)} 在构造器里被调用 ——
     * 光这一下就会触发该类的静态初始化，所以它的 {@code ORES.register(...)} 发生在窗口还开着的时候。
     * 本轮 {@code ModArmorItems} 缺的正是"被碰一下"这件事。</p>
     *
     * <p><b>约束（别顺手改）</b>：本方法必须留在类的<b>尾部</b> —— 挪到静态字段前面，
     * 它就会在字段初始化之前被调用（那时类还在初始化中，等于没起作用）。</p>
     */
    public static void touch() {
        // 这一行不是装饰：它是"类初始化真的发生在注册窗口内"的**日志证据**。
        // 崩溃那次这里没有任何输出（因为那时根本没有 touch()）；
        // 现在只要日志里出现这句话，就证明上面那 9 个 register 是在构造期跑的。
        // ⚠ 文案用英文：Audit 的 E 项会把开发者日志一起拦（见档案 §4.29）。
        LOGGER.debug("ModArmorItems initialized during mod construction (armor/star-steel registration window open)");
    }

    /** 本类的日志器（只为上面那行证据；用 Mojang 的 LogUtils，与工程其它处一致）。 */
    private static final org.slf4j.Logger LOGGER =
            com.mojang.logging.LogUtils.getLogger();

    /**
     * 注册一件盔甲。
     *
     * @param id         注册名（必须 ASCII 小写，见档案 §4.24）
     * @param material   盔甲材料（决定附魔权重 / 装备音效 / 修理材料 / 借用的贴图）
     * @param type       部位
     * @param durability 耐久（用户逐个给的数 ⇒ 直接写死）
     * @param armor      护甲值（可带 .5）
     * @param toughness  盔甲韧性（钛合金套为 0，此时不挂 KNOCKBACK 之外的多余修饰符）
     * @param tooltipKey Shift 说明的翻译键
     */
    private static DeferredItem<Item> register(String id,
                                               DeferredHolder<ArmorMaterial, ArmorMaterial> material,
                                               ArmorItem.Type type,
                                               int durability,
                                               double armor,
                                               double toughness,
                                               String tooltipKey) {
        return ModItems.ITEMS.register(id, () -> new ModArmorPiece(material, type,
                new Item.Properties().durability(durability), armor, toughness, tooltipKey));
    }
}
