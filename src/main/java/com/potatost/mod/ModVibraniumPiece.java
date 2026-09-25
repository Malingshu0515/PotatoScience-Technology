package com.potatost.mod;

import java.util.List;

import javax.annotation.Nullable;

import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

/**
 * 振金套的**单件**（0.11 ZF120）。
 *
 * <p>本类<b>只做一件事：按住 Shift 显示套装说明</b>。用户这一轮要的五件事里，
 * 其余四件都<b>不需要</b>子类 —— 这是本轮取证之后才敢下的结论，
 * 逐条记在这里，免得以后有人以为"漏写了"：</p>
 *
 * <table border="1">
 *   <caption>五个要求在代码里的落点</caption>
 *   <tr><th>要求</th><th>落点</th><th>为什么不用子类</th></tr>
 *   <tr><td>基础数据与下界合金一致</td>
 *       <td>{@link ModArmorMaterials#VIBRANIUM} 的 defense / toughness / knockbackResistance</td>
 *       <td>下界合金那四个护甲值<b>都是整数</b>（3/8/6/3），材料级 {@code defense}
 *           表达得了；原版 {@code ArmorItem} 的构造器会把
 *           {@code getDefense(type)} / {@code toughness()} / {@code knockbackResistance()}
 *           直接拼成属性修饰符（本轮从 {@code ArmorItem.java:70-94} 核实）。
 *           而 {@link ModArmorPiece} 之所以要覆写 {@code getDefaultAttributeModifiers()}，
 *           只是因为另外两套的护甲值带 .5 —— 振金没这个问题。</td></tr>
 *   <tr><td>全套无限耐久</td>
 *       <td>物品属性里的 {@code DataComponents.UNBREAKABLE}</td>
 *       <td>{@code ItemStack.isDamageableItem()} 的实现是
 *           {@code has(MAX_DAMAGE) && !has(UNBREAKABLE) && has(DAMAGE)}
 *           （本轮从 {@code ItemStack.java:440-442} 核实）⇒ 挂上 UNBREAKABLE 之后
 *           {@code hurtAndBreak} 整个 no-op（{@code ItemStack.java:465}），
 *           连"返回 0 的 damageItem"这条老路都不用走。</td></tr>
 *   <tr><td>自带附魔纹理</td>
 *       <td>物品属性里的 {@code DataComponents.ENCHANTMENT_GLINT_OVERRIDE = true}</td>
 *       <td>{@code ItemStack.hasFoil()} 先读这个组件、读不到才问 {@code Item.isFoil()}
 *           （{@code ItemStack.java:924-927}）；而背包渲染与身上渲染都走
 *           {@code hasFoil()}（身上那条见 {@code HumanoidArmorLayer.java:100}）
 *           ⇒ 一个组件同时管住"物品栏里的光"和"穿在身上发光"。</td></tr>
 *   <tr><td>贴图先用铁套</td><td>材料 Layer + 背包模型 layer0</td>
 *       <td>都是资源，不是代码。</td></tr>
 *   <tr><td>三条套装效果</td><td>{@link ModVibraniumSet}</td>
 *       <td>要听 NeoForge 事件，与"这一件是什么物品"无关。</td></tr>
 * </table>
 *
 * <p><b>为什么不直接继承 {@link ModArmorPiece}</b>：那个类里钉着星璨钢的两条规则 ——
 * 夜晚不掉耐久、末地满套永久不掉耐久。振金件套上去会**白白继承**这两条
 * （真掉耐久的时候也掉不了，而且"末地满套星璨钢"那条判的是星璨钢材料，
 * 对振金永远是 false，属于看不懂的死逻辑）。宁可各写各的。</p>
 */
public class ModVibraniumPiece extends ArmorItem {

    /** Shift 详细说明的翻译键（套装效果那段）；{@code null} = 本件不给说明。 */
    @Nullable
    private final String tooltipKey;

    public ModVibraniumPiece(Holder<ArmorMaterial> material, ArmorItem.Type type,
                             Item.Properties properties, @Nullable String tooltipKey) {
        super(material, type, properties);
        this.tooltipKey = tooltipKey;
    }

    /** Shift 看套装说明；不按 Shift 只提示"按住Shift显示详细说明"（与另外两套同一套口径）。 */
    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context,
                                List<Component> tooltipComponents, TooltipFlag tooltipFlag) {
        if (tooltipKey == null) {
            return;
        }
        if (tooltipFlag.hasShiftDown() || tooltipFlag.isAdvanced()) {
            tooltipComponents.add(Component.translatable(tooltipKey));
        } else {
            tooltipComponents.add(Component.translatable("tooltip.potato_s_t.hold_shift"));
        }
    }
}
