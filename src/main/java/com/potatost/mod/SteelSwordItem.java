package com.potatost.mod;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.Level;

/**
 * 钢剑（0.16 ZF201 补）—— 本类<b>只做一件事：做出来自带锋利 II + 横扫之刃 III</b>。
 *
 * <p>用户原话：「钢剑做出来自带横扫3和锋利2」。</p>
 *
 * <h2>为什么走 {@link #onCraftedBy}，而不是"注册时就挂附魔组件"</h2>
 * <ul>
 *   <li><b>语义正好对上</b>：用户说的是"**做出来**自带" ⇒ 只有真的在工作台合成出来的那一把才有；
 *       创造模式物品栏拿的、{@code /give} 给的都不该白送附魔（这也是"自带"与"全局默认附魔"的分界）。</li>
 *   <li><b>注册期拿不到附魔的 Holder</b>：1.21 的 {@code Enchantments.SHARPNESS} 是
 *       {@code ResourceKey<Enchantment>}，而 {@code ItemStack.enchant(...)} 要 {@code Holder}；
 *       在模组构造期取注册表会撞上本工程 §4.1 那条"注册表还没填完"（{@code ModVibraniumPiece} 与
 *       {@code ModTiers.repair()} 的类注释里都记着同一个坑）。</li>
 *   <li><b>{@code onCraftedBy} 真的会被调</b>（不是回忆）：本轮从 1.21.1 的字节码核实
 *       {@code CraftingMenu} 里有一处 {@code invokevirtual Item.onCraftedBy(ItemStack, Level, Player)}
 *       （工作台把成品交给玩家时触发）；{@link ItemStack#onCraftedBy(Level, Player, int)} 也是转发到这里。</li>
 * </ul>
 *
 * <p>⚠ <b>只在服务端加</b>（{@code !level.isClientSide}）：{@code CraftingMenu} 是服务端菜单，
 * 但多一道判断能避免"客户端本地预测出一个带附魔的假物品"那类工具提示闪烁。</p>
 *
 * <p>两个等级是<b>用户给的固定数</b>（不是随机、不吃附魔台加成）：
 * 锋利 <b>II</b> / 横扫之刃 <b>III</b>。以后要调只改这两个常量。</p>
 *
 * <p>⚠ 别把这两个附魔写进 {@code ModTiers.STEEL_SWORD} 那一档：档位里没有"附魔"这个字段，
 * 而且档位是**三把工具共用**的语义（剑/斧/镐各一档），附魔只属于剑。</p>
 */
public class SteelSwordItem extends SwordItem {

    /** 自带的锋利等级（用户给的 II）。 */
    public static final int SHARPNESS_LEVEL = 2;

    /** 自带的横扫之刃等级（用户给的 III）。 */
    public static final int SWEEPING_EDGE_LEVEL = 3;

    public SteelSwordItem(Tier tier, Properties properties) {
        super(tier, properties);
    }

    /**
     * 工作台把成品交给玩家时触发 ⇒ 在这里把两个附魔挂到**刚做出来的那一把**上。
     *
     * <p>重复合成不会叠：{@code ItemStack.enchant} 是"把这一条设成这个等级"，
     * 不是累加（同一个附魔同名只会覆盖成一个值）。</p>
     */
    @Override
    public void onCraftedBy(ItemStack stack, Level level, Player player) {
        super.onCraftedBy(stack, level, player);
        if (level.isClientSide) {
            return;
        }
        apply(stack, level, Enchantments.SHARPNESS, SHARPNESS_LEVEL);
        apply(stack, level, Enchantments.SWEEPING_EDGE, SWEEPING_EDGE_LEVEL);
    }

    /** 从**当前世界的注册表**取 {@code Holder} 再挂上去（1.21 的附魔是数据驱动注册表）。 */
    private static void apply(ItemStack stack, Level level, ResourceKey<Enchantment> key, int enchantmentLevel) {
        Holder.Reference<Enchantment> holder = level.registryAccess()
                .registryOrThrow(Registries.ENCHANTMENT)
                .getHolderOrThrow(key);
        stack.enchant(holder, enchantmentLevel);
    }
}
