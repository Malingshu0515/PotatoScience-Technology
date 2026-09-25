package com.potatost.mod;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * 三套新盔甲的**盔甲材料**（钛合金 / 星璨钢 0.11 ZF103，振金 0.11 ZF120）。
 *
 * <p><b>为什么需要这个类</b>：{@code ArmorItem} 的护甲值 / 盔甲韧性 / 附魔权重 / 装备音效
 * 全都是从 {@link ArmorMaterial} 里读的（{@code ArmorItem} 构造器把
 * {@code material.getDefense(type)} 与 {@code material.toughness()} 直接写进属性修饰符）。
 * 用户给的两套数值互不相同，所以各要一份材料。</p>
 *
 * <p><b>⚠ 护甲值只能是整数 —— 这是本轮最大的实现约束</b>：
 * {@code ArmorMaterial.defense} 是 {@code Map<ArmorItem.Type, Integer>}，
 * 喂不进用户给的 {@code +2.5} / {@code +4.5} / {@code +9.5} / {@code +7.5}。
 * 所以这里的 {@code defense} <b>只作占位</b>（取用户数的向下取整），
 * **真正的护甲值/韧性由 {@link ModArmorPiece#getDefaultAttributeModifiers()} 覆盖**
 * （它接受 {@code double}，能原样表达 .5）。
 * 两边的关系：把材料里的整数改成什么都行，玩家看到的数字只由 {@code ModArmorPiece} 决定。</p>
 *
 * <p><b>贴图（用户原话「物品栏贴图先用铁套的」）</b>：{@code ArmorMaterial.Layer} 的
 * {@code assetName} 指原版 {@code minecraft:iron} ⇒ 解析成
 * {@code minecraft:textures/models/armor/iron_layer_1.png}（外层，头/胸/靴）与
 * {@code iron_layer_2.png}（内层，护腿）。
 * 1.21.1 的人形盔甲渲染**仍然走 {@code ArmorMaterial.layers()}**（见
 * {@code HumanoidArmorLayer.renderArmorPiece} 里的 {@code armormaterial.layers()} 循环），
 * 所以这两条 Layer 就是穿了以后身体上真正显示的贴图。缺省实现
 * {@code IItemExtension#getArmorTexture} 恰好把它拼成上面那两个路径（本轮已从源码核实）。
 * ⇒ <b>本工程一张盔甲贴图都不用新增</b>，等真素材来了改这两行 {@code Layer} 即可。</p>
 *
 * <p><b>⚠ 不许在本类里写会读注册表的 {@code static final}</b>（档案 §4.1）：
 * {@link #repairIngredient} 是<b>静态方法</b>而不是常量，只有真被问到（铁砧 / 修复判定）才碰
 * {@code ModItems.X.get()}。{@link #register} 收到的 {@code Supplier} 也是延迟求值的。</p>
 */
public final class ModArmorMaterials {

    /** 盔甲材料注册表：{@code potato_s_t:titanium_alloy} / {@code potato_s_t:star_steel} / {@code potato_s_t:vibranium}。 */
    public static final DeferredRegister<ArmorMaterial> ARMOR_MATERIALS =
            DeferredRegister.create(Registries.ARMOR_MATERIAL, PotatoST.MODID);

    /** 附魔权重：用户原话「钛合金套附魔权重比金高一些」，本轮拍板 25（原版金 22、下界合金 15、钻石 10）。 */
    public static final int TITANIUM_ENCHANTMENT_VALUE = 25;

    /** 附魔权重：用户没给星璨钢的数，本轮拍板 20（比金 22 略低、比下界合金 15 高）。 */
    public static final int STAR_STEEL_ENCHANTMENT_VALUE = 20;

    /**
     * 附魔权重：用户原话「附魔权重2（非常低）」。
     *
     * <p>对照原版：金 25、皮革 15、下界合金 15、锁链 12、钻石 10、海龟 9。
     * <b>2 是全游戏最低的档</b>（连木制工具的 15、石制 5 都不如）—— 这正是用户要的"非常低"：
     * 附魔台上刷出高等级附魔的**基础花费**由它决定（{@code EnchantmentHelper.java:520}），
     * 越低越贵越难出好附魔。</p>
     */
    public static final int VIBRANIUM_ENCHANTMENT_VALUE = 2;

    /**
     * 轻质钛合金套。
     *
     * <p>用户给的数（耐久 / 护甲值）：头盔 2801 / +2.5、胸甲 4096 / +8、护腿 3412 / +6、靴子 2048 / +4.5。
     * 材料里的护甲值取整（2/8/6/4）只作占位，真值在 {@link ModArmorPiece}。</p>
     */
    public static final DeferredHolder<ArmorMaterial, ArmorMaterial> TITANIUM_ALLOY =
            register("titanium_alloy", TITANIUM_ENCHANTMENT_VALUE, 0.0F,
                    2, 8, 6, 4,
                    () -> Ingredient.of(ModItems.LIGHT_TITANIUM_ALLOY.get()));

    /**
     * 星璨钢套。
     *
     * <p>用户给的数（耐久 / 护甲值 / 盔甲韧性）：头盔 2012 / +5.5 / +0.5、胸甲 3876 / +9.5 / +1、
     * 护腿 2790 / +7.5 / +0.5、靴子 1754 / +5.5 / +0.5。
     * 材料里的护甲值取整（5/9/7/5）只作占位；<b>韧性放在材料里</b>，因为四件的韧性
     * 与材料级 {@code toughness} 的语义一致（都是"每件加一点"）；
     * 但 {@link ModArmorPiece} 会自己重建整套属性，所以这里同样只是给别的调用方看的。</p>
     */
    public static final DeferredHolder<ArmorMaterial, ArmorMaterial> STAR_STEEL =
            register("star_steel", STAR_STEEL_ENCHANTMENT_VALUE, 0.5F,
                    5, 9, 7, 5,
                    () -> Ingredient.of(ModArmorItems.STAR_STEEL_INGOT.get()));

    /**
     * 振金套（0.11 ZF120）。
     *
     * <p>用户原话：「加个振金套 基础数据与下界合金一致 只不过全套都是无限耐久 附魔权重2（非常低）
     * 自带附魔纹理 贴图先用铁套」。</p>
     *
     * <h2>「与下界合金一致」抄的是哪几个数</h2>
     * 本轮从 {@code ArmorMaterials.java:70-76}（NETHERITE 那一行）逐字核实：
     * <pre>
     *   护甲值   头 3 / 胸 8 / 腿 6 / 靴 3   （材料 defense，整数）
     *   盔甲韧性 3.0
     *   击退抗性 0.1
     *   装备音效 ARMOR_EQUIP_NETHERITE
     *   耐久     407 / 592 / 555 / 481（= 部位基数 11/16/15/13 × 材料系数 37，见 ArmorItem.Type）
     * </pre>
     * 前四个数进本材料，<b>耐久写在 {@link ModArmorItems} 的物品属性里</b>
     * （材料管不到耐久）。所有数都是整数 ⇒ 不需要像 {@link ModArmorPiece} 那样覆写
     * {@code getDefaultAttributeModifiers()}（那是为了表达 .5 才不得不做的），
     * 于是振金四件由原版 {@code ArmorItem} 直接给属性，本工程只加一层
     * {@link ModVibraniumPiece}（**只为 Shift 说明**）。</p>
     *
     * <h2>贴图（用户原话「贴图先用铁套」）</h2>
     * Layer 显式指向 {@code minecraft:iron} ⇒ 渲染读
     * {@code minecraft:textures/models/armor/iron_layer_1.png}（外层：头/胸/靴）与
     * {@code iron_layer_2.png}（内层：护腿）；背包图标同样是原版铁套的
     * （见 {@code models/item/vibranium_*.json} 的 layer0）。
     * 与钛合金/星璨钢不同 —— 那两套用的是我们自己的
     * {@code potato_s_t:textures/models/armor/<材料名>_layer_*.png}，
     * 所以这里走的是**另一个** register 重载（{@link #registerBorrowingLayer}），
     * 且**显式写出 minecraft 命名空间**而不是用 {@code withDefaultNamespace}
     * 这种隐式写法（以后要换成自绘贴图时，这两处一眼能找到）。</p>
     *
     * <h2>「无限耐久」不在材料里</h2>
     * 它落在物品的 {@code UNBREAKABLE} 组件上（见 {@link ModArmorItems#VIBRANIUM_HELMET}）。</p>
     *
     * <p><b>修理材料</b>：振金锭（{@link ModItems#VIBRANIUM_INGOT}）——
     * 它自己本轮仍没有配方（ZF119 的口径），所以这条暂时只在铁砧上问得到。</p>
     */
    public static final DeferredHolder<ArmorMaterial, ArmorMaterial> VIBRANIUM =
            registerBorrowingLayer("vibranium", VIBRANIUM_ENCHANTMENT_VALUE, 3.0F, 0.1F,
                    SoundEvents.ARMOR_EQUIP_NETHERITE,
                    ResourceLocation.fromNamespaceAndPath("minecraft", "iron"),
                    3, 8, 6, 3,
                    () -> Ingredient.of(ModItems.VIBRANIUM_INGOT.get()));

    private ModArmorMaterials() {
    }

    /**
     * 判断一件装备是不是这套材料的（给 {@link ModArmorSet} 认套装用）。
     *
     * <p>用 {@code material.unwrapKey()} 而不是逐个 {@code is(...)} 比实例：
     * 前者对"以后给这套材料加第 5 件"也成立，后者每加一件都要改一处。</p>
     */
    public static boolean isMaterial(ItemStack stack, DeferredHolder<ArmorMaterial, ArmorMaterial> material) {
        if (stack.isEmpty() || !(stack.getItem() instanceof ArmorItem armor)) {
            return false;
        }
        return armor.getMaterial().unwrapKey().filter(material.getKey()::equals).isPresent();
    }

    /**
     * 盔甲的四个槽（头/胸/腿/靴）。
     *
     * <p>放在这里而不是 {@link ModArmorSet}：{@link ModArmorPiece} 也要判"满套"
     * （末地永久不掉耐久那条），而 {@code ModArmorPiece} 不认识"套装效果"那个类。</p>
     */
    private static final EquipmentSlot[] ARMOR_SLOTS = {
            EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET,
    };

    /** 四件都是**星璨钢**（套装效果与"末地不掉耐久"共用这一条）。 */
    public static boolean hasFullStarSteelSet(LivingEntity entity) {
        return hasFullSet(entity, STAR_STEEL);
    }

    /** 四件都是**振金**（0.11 ZF120 的三条套装效果共用这一条）。 */
    public static boolean hasFullVibraniumSet(LivingEntity entity) {
        return hasFullSet(entity, VIBRANIUM);
    }

    /** 四个盔甲槽是不是同一材料（{@link #hasFullStarSteelSet} / {@link #hasFullVibraniumSet} 的唯一实现）。 */
    private static boolean hasFullSet(LivingEntity entity,
                                      DeferredHolder<ArmorMaterial, ArmorMaterial> material) {
        for (EquipmentSlot slot : ARMOR_SLOTS) {
            if (!isMaterial(entity.getItemBySlot(slot), material)) {
                return false;
            }
        }
        return true;
    }

    /** 至少一件星璨钢（"每件"那档效果用）。 */
    public static boolean hasAnyStarSteelPiece(LivingEntity entity) {
        for (EquipmentSlot slot : ARMOR_SLOTS) {
            if (isMaterial(entity.getItemBySlot(slot), STAR_STEEL)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 建一份盔甲材料。
     *
     * @param name             注册名（也是 Layer 的资源名，必须 ASCII 小写，见档案 §4.24）
     * @param enchantmentValue 附魔权重
     * @param toughness        材料级盔甲韧性（每件都加这么多）
     * @param helmet           护甲值占位：头盔
     * @param chestplate       护甲值占位：胸甲
     * @param leggings         护甲值占位：护腿
     * @param boots            护甲值占位：靴子
     * @param repair           修理材料（**延迟求值**，别在这里就 {@code .get()}，见类注释）
     */
    private static DeferredHolder<ArmorMaterial, ArmorMaterial> register(
            String name,
            int enchantmentValue,
            float toughness,
            int helmet,
            int chestplate,
            int leggings,
            int boots,
            Supplier<Ingredient> repair) {
        ResourceKey<ArmorMaterial> key =
                ResourceKey.create(Registries.ARMOR_MATERIAL,
                        ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, name));
        // 外层（头/胸/靴）与内层（护腿）都指向**本模组自己的**盔甲层贴图：
        //   potato_s_t:textures/models/armor/<name>_layer_1.png（外层）
        //   potato_s_t:textures/models/armor/<name>_layer_2.png（内层）
        // 这两张由 `_zf106_armor.py` 从用户给的「套装」原图生成（去白底 + 定尺 64×32）。
        // ⚠ 万一那两张还没生成，缺图只会让玩家身上**看不见护甲**（紫黑格 / 半透明），
        //   不会崩、也不影响任何数值 —— 所以这里不写"回退到铁套"的分支（那会让缺图更难发现）。
        ArmorMaterial.Layer layer = new ArmorMaterial.Layer(
                ResourceLocation.fromNamespaceAndPath(PotatoST.MODID, name));
        return ARMOR_MATERIALS.register(name, () -> new ArmorMaterial(
                defense(helmet, chestplate, leggings, boots),
                enchantmentValue,
                SoundEvents.ARMOR_EQUIP_IRON,
                repair,
                List.of(layer),
                toughness,
                0.0F));
    }

    /**
     * 建一份**贴图借原版**的盔甲材料（振金套用，0.11 ZF120）。
     *
     * <p>与 {@link #register} 的区别只有三处，都是"这套盔甲不是自绘贴图"带来的：</p>
     * <ol>
     *   <li>图层由调用方**显式给**（振金给的是 {@code minecraft:iron}），
     *       而不是在本方法里由材料名推出来；</li>
     *   <li>所以要多收一个装备音效参数（振金要的是下界合金音效，与数值口径一致）；</li>
     *   <li>要多收一个击退抗性参数（振金 0.1 = 下界合金，前两套是 0）。</li>
     * </ol>
     *
     * <p><b>为什么不把这两个重载合成一个</b>：{@link #register} 是 ZF103 就定形、
     * 已被探针（{@code _zf103_verify.py}）与反证刀（K6/K10）按原文锚住的那一份。
     * 为了让振金多两个参数去改它，等于同时惊动三处已经绿的判据；
     * 分成两个各自说明来意的小方法更省事，也更难被误改。</p>
     *
     * @param name               注册名（必须 ASCII 小写，见档案 §4.24）
     * @param enchantmentValue   附魔权重
     * @param toughness          材料级盔甲韧性（每件都加这么多）
     * @param knockbackResistance 材料级击退抗性（每件都加这么多；0 = 不加这条修饰符）
     * @param equipSound         穿戴音效
     * @param layerTexture       盔甲图层指向（**显式**写全命名空间）
     * @param helmet             护甲值：头盔
     * @param chestplate         护甲值：胸甲
     * @param leggings           护甲值：护腿
     * @param boots              护甲值：靴子
     * @param repair             修理材料（**延迟求值**，见类注释）
     */
    private static DeferredHolder<ArmorMaterial, ArmorMaterial> registerBorrowingLayer(
            String name,
            int enchantmentValue,
            float toughness,
            float knockbackResistance,
            Holder<SoundEvent> equipSound,
            ResourceLocation layerTexture,
            int helmet,
            int chestplate,
            int leggings,
            int boots,
            Supplier<Ingredient> repair) {
        return ARMOR_MATERIALS.register(name, () -> new ArmorMaterial(
                defense(helmet, chestplate, leggings, boots),
                enchantmentValue,
                equipSound,
                repair,
                List.of(new ArmorMaterial.Layer(layerTexture)),
                toughness,
                knockbackResistance));
    }

    /** 四个部位各给一个整数护甲值（占位用，真值见 {@link ModArmorPiece}）。 */
    private static Map<ArmorItem.Type, Integer> defense(int helmet, int chestplate, int leggings, int boots) {
        Map<ArmorItem.Type, Integer> map = new EnumMap<>(ArmorItem.Type.class);
        map.put(ArmorItem.Type.HELMET, helmet);
        map.put(ArmorItem.Type.CHESTPLATE, chestplate);
        map.put(ArmorItem.Type.LEGGINGS, leggings);
        map.put(ArmorItem.Type.BOOTS, boots);
        return map;
    }
}
