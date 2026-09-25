package com.potatost.mod;

import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.component.Unbreakable;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * 三套新盔甲 + 星璨钢锭的注册（钛合金/星璨钢 0.11 ZF103，振金 0.11 ZF120）。
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
 *
 * 振金套（0.11 ZF120；用户原话「基础数据与下界合金一致 只不过全套都是无限耐久 附魔权重2（非常低）
 *        自带附魔纹理 贴图先用铁套」）
 *   头盔   耐久 407（= 11 × 37，下界合金同款）  护甲值 +3  盔甲韧性 +3  击退抗性 +0.1
 *   胸甲   耐久 592（= 16 × 37）                护甲值 +8  盔甲韧性 +3  击退抗性 +0.1
 *   护腿   耐久 555（= 15 × 37）                护甲值 +6  盔甲韧性 +3  击退抗性 +0.1
 *   靴子   耐久 481（= 13 × 37）                护甲值 +3  盔甲韧性 +3  击退抗性 +0.1
 *   ⚠ 这四个耐久数字**玩家永远看不到**：UNBREAKABLE 组件让 isDamageableItem() 恒 false
 *     ⇒ 耐久条不显示、也永远扣不动。写死它们是为了两件事：
 *     ① 以后要把 UNBREAKABLE 摘掉时，数值立刻回到"与下界合金一致"；
 *     ② {@code Item.isEnchantable(stack)} 要求物品带 MAX_DAMAGE
 *        （{@code Item.java:355-357}）—— 没有它，附魔权重 2 这条要求**根本没机会生效**
 *        （附魔台会把物品当成不可附魔）。这是本轮最容易踩空的一处，记在这里。
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

    // ========== 振金套（0.11 ZF120）==========
    // 四件的**数值全部来自材料**（下界合金口径），这里只给"耐久"和"贴图/图标"。
    // 无限耐久 + 附魔光效写在 vibraniumProperties(...) 里，四件共用一份说明。
    /** 振金头盔：下界合金的 407 耐久，但永不消耗（UNBREAKABLE）；护甲值 +3、韧性 +3、击退抗性 +0.1。 */
    public static final DeferredItem<Item> VIBRANIUM_HELMET =
            registerVibranium("vibranium_helmet", ArmorItem.Type.HELMET, 407);

    /** 振金胸甲：下界合金的 592 耐久，但永不消耗；护甲值 +8、韧性 +3、击退抗性 +0.1。 */
    public static final DeferredItem<Item> VIBRANIUM_CHESTPLATE =
            registerVibranium("vibranium_chestplate", ArmorItem.Type.CHESTPLATE, 592);

    /** 振金护腿：下界合金的 555 耐久，但永不消耗；护甲值 +6、韧性 +3、击退抗性 +0.1。 */
    public static final DeferredItem<Item> VIBRANIUM_LEGGINGS =
            registerVibranium("vibranium_leggings", ArmorItem.Type.LEGGINGS, 555);

    /** 振金靴子：下界合金的 481 耐久，但永不消耗；护甲值 +3、韧性 +3、击退抗性 +0.1。 */
    public static final DeferredItem<Item> VIBRANIUM_BOOTS =
            registerVibranium("vibranium_boots", ArmorItem.Type.BOOTS, 481);

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

    /**
     * 注册一件**振金**盔甲（0.11 ZF120）。
     *
     * <p>与前两套的区别：护甲值/韧性/击退抗性<b>不在这个参数表里</b> ——
     * 它们是下界合金的整数，全部由 {@link ModArmorMaterials#VIBRANIUM} 给出
     * （原版 {@code ArmorItem} 自己会读材料拼属性）。所以这里只剩两件事要传：
     * 部位，以及那个"看得见但永远扣不动"的耐久。</p>
     *
     * @param id         注册名（必须 ASCII 小写，见档案 §4.24）
     * @param type       部位
     * @param durability 耐久（**下界合金同款**；挂上 UNBREAKABLE 后玩家看不到也扣不动，
     *                   写死它是为了让"摘掉 UNBREAKABLE 就退回下界合金"这件事只改一行，
     *                   并且让物品保持"可附魔"—— 见类注释里的 ②）
     */
    private static DeferredItem<Item> registerVibranium(String id, ArmorItem.Type type, int durability) {
        return ModItems.ITEMS.register(id, () -> new ModVibraniumPiece(
                ModArmorMaterials.VIBRANIUM, type, vibraniumProperties(durability),
                "tooltip.potato_s_t.vibranium_set"));
    }

    /**
     * 振金套四件共用的物品属性：**无限耐久 + 自带附魔光效**。
     *
     * <p>用户原话「全套都是无限耐久 … 自带附魔纹理」。</p>
     *
     * <ul>
     *   <li>{@code UNBREAKABLE}（{@code new Unbreakable(true)}）：让
     *       {@code ItemStack.isDamageableItem()} 恒为 false（本轮从
     *       {@code ItemStack.java:440-442} 核实），于是 {@code hurtAndBreak} 整个 no-op
     *       —— 摔落/岩浆/被砍/被炸，一律扣不动。参数 true = 保留原版那行蓝色的
     *       "Unbreakable" 说明（玩家看得见"这东西不会坏"）。
     *       这条**比** {@link ModArmorPiece#damageItem} 那条路更彻底：
     *       那条是"每次问我要扣多少、我答 0"，这条是"根本不来问"。</li>
     *   <li>{@code ENCHANTMENT_GLINT_OVERRIDE = true}：附魔光效。
     *       {@code ItemStack.hasFoil()} 先读它、读不到才问 {@code Item.isFoil()}
     *       （{@code ItemStack.java:924-927}）。背包里和穿在身上发光走的是同一个
     *       {@code hasFoil()}（身上那条在 {@code HumanoidArmorLayer.java:100}）
     *       ⇒ 一个组件管两处，不必覆写 {@code isFoil}。</li>
     * </ul>
     *
     * <p><b>为什么还留着 {@code durability(n)}</b>：见 {@link #VIBRANIUM_HELMET} 那段
     * 与类注释里的 ② —— 主要是为了"物品仍然可附魔"（附魔权重 2 才有意义）。</p>
     */
    private static Item.Properties vibraniumProperties(int durability) {
        return new Item.Properties()
                .durability(durability)
                .component(DataComponents.UNBREAKABLE, new Unbreakable(true))
                .component(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, Boolean.TRUE);
    }
}
